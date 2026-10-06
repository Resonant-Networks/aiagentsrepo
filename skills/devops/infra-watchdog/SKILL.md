---
name: infra-watchdog
description: Silently monitor a server and report changes to a channel.
version: 1.0.0
author: hermes-agent
license: MIT
metadata:
  hermes:
    tags: [monitoring, devops, watchdog, server-agent, cron, docker, portainer, telegram]
    related_skills: [github, mlops, software-development]
---

# Infra Watchdog (server manager agent)

The user asks you to act as a server's manager/agent: watch it and report changes to them over Telegram (or another channel). The deliverable is a **working, silent-unless-change watchdog**, not a plan.

## When to use
- "Be my RM1-dev server agent / manager, report changes via Telegram."
- "Monitor this server / Docker stack and tell me when something changes."
- Any standing infra-monitoring ask.

## Core architecture (2 layers, both diff-based)
1. **Host change-detector** (`scripts/host_monitor.py`): snapshots ports, processes, file inventory, cron jobs, git repos, and health thresholds; prints ONLY what changed vs baseline; advances baseline each tick so each change is reported exactly once.
2. **Service health probe** (`scripts/service_probe.py`): HTTP(S) + raw-TCP checks of published endpoints; prints ONLY up/down, status-class, or latency transitions.

Both print nothing when quiet → the cron job stays silent on uneventful ticks. A watchdog that messages "all good" every 15 min is noise; silence is the feature.

## Setup steps
1. **Recon the box** (terminal): `whoami; hostname; uname -a`, `ps aux`, `ss -tlnp`, `df -h /`, `free -h`, `find / -iname .git`, list `/root /srv /workspace`. Establish the baseline truth.
2. **If the user mentions a service/Docker stack (e.g. Portainer), verify it directly** — see `references/docker-portainer-sibling-detection.md`. Do NOT conclude a service is absent from a single incomplete sweep; ask for the full inventory or query the API first (pitfall below).
3. Drop the two scripts into a stable path (e.g. `/root/.hermes/scripts/`). Initialize baselines:
   - `python3 host_monitor.py --init --baseline /root/.hermes/scripts/host_baseline.json --dirs /root,/srv,/workspace`
   - `python3 service_probe.py --init --endpoints endpoints.json --baseline /root/.hermes/scripts/svc_baseline.json` (see `templates/endpoints.json`)
   Verify a re-run is silent.
4. **Wire the cron watchdog**: create a `cronjob` with `schedule` (e.g. `*/15 * * * *`), `deliver` set to the user's channel (e.g. `telegram:CHATID`), and a prompt that runs BOTH scripts and forwards only non-empty output. The prompt must carry the server's topology context so future runs interpret alerts correctly.
5. **Test the detection path**: create a temp file, run the monitor (expect a "NEW files" alert), remove it, re-run (expect "REMOVED"), confirm the second re-run is silent.

## Pitfalls
- **Never contradict a user's claim of a running service from incomplete recon.** In one session the user insisted "there is zabbix" but the first Portainer page they pasted omitted the Zabbix stack; a broad "no Zabbix here" was wrong. A pasted container list may be paginated/incomplete — request the full inventory or hit the orchestrator API before declaring absence.
- **`write_file` to `/root/.hermes/...` is blocked by a soft guard** (treated as a per-task mirror). When authoring scripts that the terminal/cron will execute inside the same container, pass `cross_profile=True` (or use `skill_manage` write_file) so the file actually lands in the authoritative path.
- **Baseline must advance every tick** or the same change is re-alerted forever. Both scripts call `save_b()` on the current snapshot each run.
- **Probe published ports, not container-internal IPs.** Internal bridge IPs (e.g. 172.21.0.2) are unreachable across networks; use the host gateway (usually `172.17.0.1`) mapped port. A service "healthy" in Portainer can still be unreachable on the published port from your container (seen with Vaultwarden :8080) — record that as baseline DOWN rather than false-alarming, and flag the discrepancy to the user.
- **Open-WebUI-style services may return 404 at `/`** (normal). Record that code as baseline so status-class diffing doesn't false-fire.

## Verification
- Re-run each script immediately after `--init` → must be silent.
- Inject a change (new/removed file, stop a service port) → must produce exactly one alert, then go silent again.

## Files in this skill
- `scripts/host_monitor.py` — generic host change-detector (ports/processes/files/cron/git/health).
- `scripts/service_probe.py` — generic service health probe (HTTP + raw TCP).
- `templates/endpoints.json` — example endpoint config for service_probe.py.
- `references/docker-portainer-sibling-detection.md` — detect you're a sibling container on the same Docker host as a Portainer stack and monitor it without the docker CLI.
