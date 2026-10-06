---
name: node-incident-recovery
description: "NOC node down? Diagnose and recover container nodes."
author: "Hermes Agent (Nous Research)"
license: CC0-1.0
version: 1.1.0
platforms: [linux]
metadata:
  hermes:
    tags: [NOC, Incident, Recovery, Docker, Containerlab, SRE]
---

# Node Incident Recovery

Use this skill when a NOC ticket arrives reporting a network node (Docker container, containerlab device) as unreachable or down. Covers the full lifecycle: Slack channel creation → diagnostics → recovery → hardening → documentation.

## When to Use

- A Zammad ticket fires with "Unavailable by ICMP ping" or similar node-down alert
- A containerlab node (especially Nokia SR Linux) shows Exited state
- You need a repeatable workflow: alert → Slack channel → diagnose → fix → harden → report
- You are responding to ICMP health alerts in a containerlab network topology

## Workflow

### 1. Create Incident Channel
Create a dedicated Slack channel for this incident:

```bash
python3 ~/.hermes/skills/slack-incident/scripts/slack_incident.py create \
  --ticket-id "<TICKET_ID>" \
  --topic "<TICKET_TITLE>" \
  --users "U04A3PR9294"
```

Save the returned `channel_id` (e.g. `C0C2BA7BD5E`) — you'll need it for all subsequent steps.

### 2. Diagnose the Node

Run these diagnostics in parallel to build a full picture:

```bash
# DNS resolution + ICMP reachability
getent hosts <NODE_HOSTNAME>
ping -c 4 -W 3 <NODE_HOSTNAME>

# Container status (all states)
docker ps -a --filter "name=<NODE_NAME>" --format "table {{.Names}}\t{{.Status}}\t{{.State}}"

# Container details: exit code, OOM, restart policy
docker inspect <NODE_NAME> | python3 -c "import sys,json; d=json.load(sys.stdin)[0]['State']; print(f'Status: {d[\"Status\"]}, Exit: {d[\"ExitCode\"]}, OOM: {d[\"OOMKilled\"]}, Error: {d[\"Error\"]}')"
docker inspect <NODE_NAME> --format '{{.HostConfig.RestartPolicy.Name}}'

# Container logs (last 50 lines)
docker logs --tail 50 <NODE_NAME> 2>&1

# For containerlab environments: full topology status
sudo containerlab inspect --name <LAB_NAME>
```

**Exit code cheat sheet for containers:**
| Code | Signal | Meaning |
|------|--------|---------|
| 0 | — | Clean exit / success |
| 137 | SIGKILL (9) | OOM killer or force kill |
| 139 | SIGSEGV (11) | Segmentation fault / crash |
| 143 | SIGTERM (15) | Clean Docker stop (expected shutdown) |
| 1 | — | Application error / crash |

### 3. Interpret Diagnostics

- **Sibling nodes**: Check if other nodes in the same topology are healthy — isolates the issue
- **DNS staleness**: An exited container still resolves via Docker DNS; verify actual container state
- **Restart policy**: Containerlab defaults SR Linux nodes to `restart=no` — no auto-recovery on any stop
- **Logs**: SIGTERM (code 143) with clean `"Termination_signal_received by sr_app_mgr: SIGTERM"` is a Docker stop, not an application crash

### 4. Recover the Node

```bash
docker start <NODE_NAME>
```

Verify recovery:
```bash
ping -c 4 <NODE_HOSTNAME>    # expect 0% loss, sub-1ms RTT
docker ps --filter "name=<NODE_NAME>" --format "{{.Names}} {{.Status}}"
```

### 5. Harden: Fix Restart Policy

Containerlab SR Linux nodes default to `restart=no`. Set to auto-recover:

```bash
docker update --restart unless-stopped <NODE_NAME>
docker inspect <NODE_NAME> --format '{{.HostConfig.RestartPolicy.Name}}'  # verify
```

### 6. Post Report to Incident Channel

```bash
python3 ~/.hermes/skills/slack-incident/scripts/slack_incident.py post \
  --channel "<CHANNEL_ID>" \
  --message "<REPORT>"
```

Report should cover:
- **Diagnosis**: exit code, log findings, DNS/ping state
- **Recovery action**: docker start, restart-policy change
- **Post-recovery**: ping verification, current container state
- **Recommendations**: restart-policy fix, root cause investigation

### 7. Archive Channel
When the ticket is resolved:

```bash
python3 ~/.hermes/skills/slack-incident/scripts/slack_incident.py archive \
  --channel "<CHANNEL_ID>" \
  --summary "Incident <ID> resolved. RC: <ROOT_CAUSE>. Archiving channel."
```

## Pitfalls

- **Zammad MCP may return "Not authorized"**: verify token via direct curl against the API before assuming MCP is down.
- **Zammad tickets may auto-close**: Zabbix integration can close tickets upon ICMP recovery. Adding articles to closed tickets returns `"Cannot follow-up on a closed ticket"`.
- **DNS staleness**: An exited container still resolves in Docker DNS. `ping` alone is not sufficient — always check `docker ps -a` for actual container state.
- **`containerlab inspect` output format**: requires `table`, `json`, or `csv` when not using `--details`. Custom Go templates need `--details` flag.
- **SR Linux nodes** do not auto-restart by design in containerlab. Always set `unless-stopped` after recovery.
- **SIGTERM recurrence**: If the same SR Linux node exits with SIGTERM (143) multiple times, investigate the host-side process rather than treating each as isolated. Check `docker events --filter container=<NAME>` and host journal for the PID that sent the SIGTERM. Containerlab defaults to `restart=no`, so a Docker daemon restart or resource pressure can silently kill SR Linux nodes without auto-recovery.
- **Zabbix recovery confirmation**: After restarting a node, verify Zabbix has registered the recovery. Query `event.get {eventids: [<EVENT_ID>]}` for the `r_eventid` field — a non-zero value points to the recovery event. Do not assume recovery from container uptime alone.

## Related

- `zabbix-api-investigation` — upstream Zabbix alarm diagnostics
- `slack-incident` — Slack channel creation and management
- `infra-watchdog` — proactive server monitoring

## References

See `references/containerlab-sigterm-recovery.md` for a worked example of recovering an SR Linux spine node that exited with SIGTERM (exit code 143).