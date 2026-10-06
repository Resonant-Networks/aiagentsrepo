---
name: zabbix-api-investigation
description: Investigate & manage Zabbix alarms via the JSON-RPC API — read-only forensics + active alert ops (acknowledge, notes).
version: 1.1.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [zabbix, monitoring, alert-forensics, rca, api]
    related_skills: [infra-watchdog, systematic-debugging]
---

# Zabbix API Investigation (read-only alert forensics)

## When to Use

- "Why did this Zabbix alarm fire?" — RCA on a specific event id or alert text.
- Need item history / old-vs-new values not visible in the alert payload.
- Correlating multiple events on one host (e.g. package change + disk spike).
- Any read-only Zabbix forensics against a live server.

All API calls below are read-only (`event.get` / `trigger.get` / `item.get` / `history.get` / `problem.get`) — never call mutating methods.

## Quick start
- Endpoint: `http://<host>:<port>/api_jsonrpc.php` — the Zabbix **web UI** port (e.g. 8083).
- Login: `user.login`; `Admin/zabbix` default creds are common on dev stacks. Treat access as read-only and flag the default password for rotation.
- Ready-made probe: `python3 scripts/zabbix_probe.py --event <ID> [--event <ID> ...]` (params `--url --user --pass --hours`). Prints event detail, trigger expression, resolved item IDs, last/prev values, value history around the event clock, and other active problems on the host.

## Active Alert Management (mutating ops)

Use these when you need to acknowledge, comment on, or close events — complementary to read-only forensics above.

### Authenticate (same as read-only)
```python
url = "http://<host>:<port>/api_jsonrpc.php"
auth_data = {"jsonrpc": "2.0", "method": "user.login",
             "params": {"username": "Admin", "password": "zabbix"}, "id": 1}
# Returns temporary auth token; or use API token:
# {"jsonrpc": "2.0", "method": "user.login", "params": {"token": "<api-token>"}, "id": 1}
```

### Acknowledge event with notes
```python
event.acknowledge {
    eventids: ["<event_id>"],
    action: 4,              # 4 = acknowledge + add message
    message: "Your notes here"
}
```
Returns `{"eventids": [<id>]}` on success. Verify by re-fetching `event.get {eventids, selectAcknowledges}`.

### Change event severity
Not directly supported via `event.acknowledge` on its own — use `action` flags:
- `1` = acknowledge
- `2` = close (if problem auto-resolved)
- `4` = acknowledge + add message
- `8` = add message without acknowledge
- `10` = acknowledge + close
- `12` = acknowledge + close + message
- `32` = suppress until (add `suppress_until` timestamp)

## Core recipe
1. **Event detail** — `event.get {eventids: [...], selectRelatedObject, selectHosts}` → clock, PROBLEM/RESOLVED, severity, name, trigger description + expression.
2. **Resolve trigger → item** — `trigger.get {triggerids, selectFunctions: extend}` → `functions[].itemid` is the REAL item id.
3. **Item state** — `item.get {itemids}` → `prevvalue` / `lastvalue` / `lastclock`. Note `prevvalue` only reflects the last change; use history for a real series.
4. **History** — `history.get {history: <type>, itemids, time_from, time_till, sortfield: clock}`. Map item `value_type`:
   - 0 (float) → `history=0` (e.g. `vfs.fs.size` pused)
   - 1 (character) → `history=1`
   - 2 (log) → `history=2` (e.g. log file monitoring items like `log[/var/log/foo.log]`)
   - 3 (unsigned int) → `history=3` (e.g. `system.sw.packages.get`)
   - 4 (text) → `history=4`
   For log-type items (`history=2`), the `value` field contains the raw log line including timestamp. Filter in Python with list comprehension after fetching.
5. **Correlate** — pull history of *other* items on the same host around the event clock. Example: a package-count change coinciding with a ~2 GB disk burst at ~02:00 UTC is the classic **unattended-upgrades / kernel-update** signature.
6. **Context** — `problem.get {host}` lists other active problems; `event.get {host, time_from}` shows recurrence (same trigger firing repeatedly = routine maintenance, not anomaly).

7. **Host inventory / location data** — `host.get {search: {name: "...", output: "extend", selectInventory: "extend"}` returns lat/long, site address, location name, hardware model, site notes. Useful for ALM/fiber-monitoring probes and physical infrastructure tracking.
8. **Find items by key pattern** — `item.get {search: {key_: "log[/var/log/..."}}` or `search: {name: "syslog"}` to locate monitoring items when you know the data source but not the item ID. Pair with `selectHosts` to show which host each item belongs to.

## Authentication methods
- **User/password** (default for dev stacks): `user.login {username, password}` — returns a temporary session token. Default creds `Admin/zabbix` are common; flag for rotation.
- **API token** (more secure): generate in Zabbix UI → Administration → API tokens, then `user.login {token: "<api-token>"}` — no password sent over wire.

## Zabbix 6.4 API quirks (the traps)
- **Expression `{N}` is a FUNCTION id, NOT an item id.** `item.get {itemids: [33941]}` returns `[]` even when the expression reads `{33941}<>0`. Always resolve through `trigger.get selectFunctions`.
- **`apiinfo.version` must be called WITHOUT the auth parameter** — passing it returns `Invalid params`.
- **`trends.get` was removed in 6.4** → use `history.get` with `history=4`. Its output fields are limited to `itemid/clock/value/ns` (no `value_min/max/num` — requesting them errors).
- **Trigger semantics explain "still active":** `change()` triggers fire on any value change and auto-recover at the next poll (an hourly item recovers ~1 h later); threshold triggers (`min() > X`) stay PROBLEM while the condition holds.
- **`change()` fires on install AND removal** — "packages changed" Warning is informational audit, not a fault.

## Boundary: what Zabbix cannot tell you
Zabbix gives the WHAT (item, old→new value, exact timestamp) and WHEN. It does NOT say *which* package changed — that requires host-side logs (`/var/log/dpkg.log`, `/var/log/apt/history.log`). State the boundary and hand the user the exact host commands instead of guessing.

## Worked example
`references/example-package-change-investigation.md` — real end-to-end case: package count 1005→1006 correlated with an 80%-disk-crossing event, diagnosis, and the host commands that close the loop.

## Domain references (alarm-type-specific guides)
- `references/alm-fiber-monitoring.md` — Adtran/ADVA FSP 3000 optical fiber probe: syslog formats, Zabbix event naming, SNMP-based fault analysis via direct device walk (OID mappings for Auto FA table, GIS route check, GPS-unmapped fallback). Use this when investigating ALM optical-fiber port faults where REST API credentials are unknown — SNMP community `public` works.
- `references/alm-rest-api-pdf-extract.md` — Condensed extract from Adtran ALM Programming Guide Ch.4 (REST Interface). Documents all GET-only endpoints, full trace data format, and the `faultpos: "0.0"` vs trace events nuance. Consult before probing for undocumented endpoints — the REST API has no write/trigger endpoints.
