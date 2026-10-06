---
name: fnt-command-automation
description: Automate FNT Command login, session extraction, mandant selection, and cable/asset REST lookups.
version: 1.0.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [fnt, fnt-command, session-extraction, cable-scanner, asset-management, automation, playwright]
    related_skills: [infra-watchdog, zabbix-api-investigation]
---

# FNT Command Automation & Session Extraction

## When to Use

- "Get FNT session ID" / "Extract active FNT session token" — Simulates browser login and extracts session credentials.
- "Query FNT cable by ELID" — Look up cable info from FNT Command REST API.
- Setting up or refreshing credentials for the Cable Scanner PWA middleware.
- Interacting with FNT Command SOAP or REST API endpoints.

## Core Capabilities

1. **Browser-Simulated Session Extraction**: Automates browser login at `https://100.80.103.95/app/command`, selects Mandant, navigates to Session Search (`/html/administration/search/session`), and extracts active Session IDs.
2. **Automated `.env` Updating**: Automatically updates `.env` in the OWUI Cable Scanner workspace with fresh session keys.
3. **Cable Asset Lookups**: Queries `cableMaster`, `powerCable`, and `dataCable` entities by ELID.

## Quick Start

### 1. Extract Fresh Session ID
Run the automated session extractor script:
```bash
node /home/ubuntu/.hermes/skills/devops/fnt-command-automation/scripts/fnt_session_extractor.js
```
This script will:
- Launch headless Chromium via Playwright (ignoring SSL warnings).
- Log into `https://100.80.103.95/app/command` using credentials (`command` / `command`).
- Confirm Mandant selection (`/html/command/mandant`).
- Open Session Search (`/html/administration/search/session`) and click **Search**.
- Extract active `sessionid` cookies & table rows.
- Automatically write `FNT_SESSION_ID` to the OWUI Cable Scanner `.env` file.

### 2. Query Cable / Rack Information by ELID
Run the Python lookup utility (auto-reads the live `FNT_SESSION_ID` from the cable-scanner `.env`):
```bash
python3 /home/ubuntu/.hermes/skills/devops/fnt-command-automation/scripts/fnt_query_cable.py --elid <CABLE_OR_RACK_ELID>
```
Add `--entity rack` to query the `switchCabinet` (rack) entity explicitly; add `--entity cable` for cableMaster/powerCable/dataCable.

## FNT Command API Reference

- **Base URL**: `https://100.80.103.95/app/command`
- **Default Credentials**: `command` / `command`
- **Current live session**: read `FNT_SESSION_ID` from `/home/ubuntu/cable-scanner-fnt/.env` (prefer over re-running the Playwright extractor; only re-login via SOAP if it expires).
- **Auth**: session is passed as a **query param** `?sessionId=<SID>` on every request. (Cookie/`X-FNT-Session-Id` header are NOT used by the REST entity API.)

### Correct REST entity API (POST, body `{}`)
- **Query entity list**: `POST {base}/api/rest/entity/<entityType>/query?sessionId=<SID>` — body `{}`, content-type `application/json`. Returns `{"status":{...},"returnData":[{...}]}`.
- **Extended query** (switchCabinet/junctionBox/chassis): try `queryExtended` first, fall back to `query`.
- **Rack sub-devices**: `POST {base}/api/rest/entity/switchCabinet/<elid>/SubDevices?sessionId=<SID>` — body `{}`.

### Entity types (tokens)
- Cables: `cableMaster`, `powerCable`, `dataCable`
- **Racks: `switchCabinet`** (a rack IS a switchCabinet — `id`/`visibleId` e.g. `Rack-B02`, `elid` e.g. `8IO2TTSSVG985G`)
- Infra: `junctionBox`, `chassis`
- Locations: `building`, `room`, `floor`, `campus`

### Pitfalls (learned in the field)
- The old skill endpoints `GET /rest/<entity>/search?q=` **return 404 even with a valid session** — the real API is `/api/rest/entity/<entityType>/query`. Do not use them.
- `switchCabinet/query` returns ~1,400+ racks (1 MB+); filter/select in code, don't dump.
- The `.env` session is the source of truth; the script default session in `fnt_query_cable.py` is stale — the script now reads the .env automatically.

See `references/fnt-api-cheatsheet.md` for full endpoint schemas and Blowfish SOAP auth details.
