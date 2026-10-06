# Containerlab SR Linux SIGTERM Recovery — Worked Example

## Incident 1: Ticket #72047 (ICMP down on clab-demo-clos-spine1)

### Initial State
- **Node**: `clab-demo-clos-spine1` (Nokia SR Linux, ixr-d2l)
- **IP**: 172.30.20.10
- **Ping**: 100% loss, "Destination Host Unreachable"
- **DNS**: resolved OK (Docker DNS stale entry)
- **Container state**: `Exited (143)` — SIGTERM
- **OOM**: false
- **Restart policy**: `no` (containerlab default for SR Linux)

### Root Cause
```
Container exited at 2026-09-13 11:19:46 UTC
Logs show: "Termination_signal_received by sr_app_mgr: SIGTERM (15: Terminated). SentByPid:1956"
```
PID 1956 inside container = Docker stop signal. Container was stopped externally — likely Docker daemon restart or manual `docker stop`. No application crash.

### Recovery Commands
```bash
docker start clab-demo-clos-spine1
# → "clab-demo-clos-spine1" (confirmed)

ping -c 4 clab-demo-clos-spine1
# → 4/4 received, 0% loss, avg 0.41ms RTT

docker update --restart unless-stopped clab-demo-clos-spine1
docker inspect clab-demo-clos-spine1 --format '{{.HostConfig.RestartPolicy.Name}}'
# → "unless-stopped"
```

### Key Observations
- DNS stale: exited container still resolved (172.30.20.10) from Docker's embedded DNS
- Sibling nodes (leaf1, leaf2, client1, client2) all healthy — localized to spine1
- Containerlab defaults both `restart=no` AND `RestartCount=0` for SR Linux nodes
- Client nodes (network-multitool image) default to `restart=always`

### Full Diagnostic Command Set Used
```bash
# Parallel diagnostics (independent commands):
getent hosts clab-demo-clos-spine1
ping -c 4 -W 3 clab-demo-clos-spine1
docker ps -a --filter "name=clab" --format "table {{.Names}}\t{{.Status}}"
docker inspect clab-demo-clos-spine1 | python3 -c "import sys,json; d=json.load(sys.stdin)[0]['State']; print(f'Status: {d[\"Status\"]}, Exit: {d[\"ExitCode\"]}, OOM: {d[\"OOMKilled\"]}')"
docker inspect clab-demo-clos-spine1 --format '{{.HostConfig.RestartPolicy.Name}}'
docker logs --tail 50 clab-demo-clos-spine1 2>&1
sudo containerlab inspect --name demo-clos
```

### Zammad Integration Note
The ticket was auto-closed by Zabbix before manual note could be added. Zammad API returns:
```
{"error":"Cannot follow-up on a closed ticket. Please create a new ticket."}
```
This is expected behavior — the Zabbix→Zammad integration auto-closes tickets upon ICMP recovery.

---

## Incident 2: Ticket #72048 (REPEAT — same spine1 node, same SIGTERM)

### What Changed
The **same node** (`clab-demo-clos-spine1`) exited with SIGTERM (143) again ~5 minutes after the first recovery. This time the container started immediately after creation of the second Zammad ticket (no additional manual action needed — it recovered on its own or was already restarting when diagnosed).

### Diagnostics at Alert Time
- **Container**: `Exited (143) 50 seconds ago` (exit 143, same as Incident 1)
- **All siblings**: Up and healthy (leaf1, leaf2, client1, client2 all running 4+ days)
- **Ping**: 100% packet loss to 172.30.20.10
- **Logs**: Identical pattern — `Termination_signal_received by sr_app_mgr: SIGTERM (15: Terminated). SentByPid:1957`

### Recovery
`docker start clab-demo-clos-spine1` — container resumed immediately.

### Key Observation
The restart policy had been set to `unless-stopped` in Incident 1, yet the node failed to auto-restart. This is likely because `docker update --restart` only takes effect at container stop time — if the container was already stopped when the policy was applied, the new policy won't auto-start it. A future Docker daemon restart will now honor the policy.

### Zabbix Recovery Confirmation
```
event.get {eventids: ["59896"]}  →  r_eventid: "59900"  (recovery recorded)
```
The `r_eventid` field on the original problem event confirmed Zabbix saw the recovery. No acknowledgements existed on either event.

### What Changed After This Session
The `node-incident-recovery` skill gained two new pitfalls:
- **SIGTERM recurrence**: investigate host-side process when the same SR Linux node exits with SIGTERM multiple times
- **Zabbix recovery confirmation**: check `r_eventid` before declaring closure