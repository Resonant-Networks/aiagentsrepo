# ALM Trace Sequence Interpretation & Change-Polling (live incident playbook)

Context: ALM box at 10.10.10.3 (Cyberjaya, CoPlace 2), REST creds `admin:chgme.1a`.
Endpoints: `GET /trace/<PORT>/af/list` (auto-FA list, FIRST entry = newest, `faultpos` in meters or `null`),
`GET /trace/route/<PORT>` (KML route for triangulation).
CLI: `python3 ~/.hermes/skills/slack-incident/scripts/triangulate_alm.py --port <PORT>`.

## Rule 1 — during an active incident, read the FULL list, not just entry 0

Compare against the previously reported reading. A single snapshot cannot show a *change*;
the change itself is the signal.

## Rule 2 — interpret the fault-distance SEQUENCE (field-observed pattern)

Observed live: `515.1 m → null → 0.0 m` across ~24 h on Port 1 (MCH-1-1).

- `null` between two faults → the link was momentarily UP (re-splice / reconnect happened),
  then a new fault appeared. Not an artifact — real state.
- Old distance (515.1 m) followed by `0.0` → the active fault has MOVED TO THE ORIGIN:
  patch cord pulled, connector disconnected, or cut at the ODF / ALM transceiver end —
  i.e. someone is physically working at the ODF right now.
  → The previously triangulated dispatch point (515 m mark) is STALE. Say so explicitly.
    Recommend a confirmatory manual trace (or wait for the next auto-FA cycle) before
    dispatching to the old mark.
- `faultpos: 0.0` = origin fault (per alm-fault-analysis edge table: Waypoint 0 GPS /
  ALM unit location, e.g. 2.908965, 99.540296 for Port 1 route start).
- Same trace id on a re-query → no new auto-FA cycle; report "unchanged since <timestamp>",
  don't re-report identical numbers.

## Rule 3 — poll with cron monitor-mode (change-detection watch), not repeated manual curls

Verified working pattern (2026-09-15, incident #72100):

1. Write a STABLE-output script, e.g. `~/.hermes/scripts/alm_port1_watch.py`:
   - emits exactly ONE line per run, e.g.
     `PORT1: trace_id=421 ts=2026-09-15 13:23:08 fault=0.0`
   - **no timestamps of its own, no random ordering** — the cron monitor hashes stdout;
     unchanged output = silent tick (no LLM, no delivery).
2. Create the job: `cronjob action=create`, `schedule='every 5m'`,
   `monitor_script='alm_port1_watch.py'`, `deliver='origin'`. Prompt tells the run-agent to
   read the injected MONITOR CHANGE DETECTED block (diff + new output), report in NOC
   log style, and NEVER claim resolution / close anything (read-only).
3. Quirk (verified): bare `5m` parses as a ONE-SHOT "once in 5m". Use `every 5m`, then
   `cronjob action=update repeat=0` — otherwise `repeat` stays `once` and the poller dies
   after a single run.
4. First tick always runs the agent (baseline). Later ticks are silent unless the output
   hash changes (new trace id / faultpos change).
5. Remove when incident closes: `cronjob action=list` → `remove <job_id>`.
   The monitor script lives at `~/.hermes/scripts/` and is reusable for any port.