---
name: fnt-session-fetch
description: Fetch a fresh active FNT Command session ID via headless Playwright login and refresh the .env session token.
version: 1.0.0
author: hermes-curator
license: MIT
metadata:
  hermes:
    tags: [fnt, session, token-refresh, cable-scanner, playwright, automation]
    related_skills: [fnt-command-automation, fnt-elid-fetcher]
---

# FNT Session Fetch

## When to Use

- User asks to "fetch / refresh / renew the FNT session ID".
- FNT REST API returns `401 Unauthorized` / `Invalid session` (errorCode 102) and the cable-scanner needs a fresh token.
- Keeping `FNT_SESSION_ID` in the cable-scanner `.env` up to date (usually via the 4-hour cron).

## Execution Recipe

Run the headless-browser session extractor from the cable-scanner working dir:

```bash
node /home/ubuntu/.hermes/skills/devops/fnt-session-fetch/scripts/fnt_session_extractor.js
```

Invoke from `/home/ubuntu/cable-scanner-fnt` (or pass `cd` first) so the script updates the correct `.env`:

```bash
cd /home/ubuntu/cable-scanner-fnt && node /home/ubuntu/.hermes/skills/devops/fnt-session-fetch/scripts/fnt_session_extractor.js
```

## What It Does

1. Launches headless Chromium (Playwright via the scratch node_modules path, `ignoreHTTPSErrors: true`).
2. Logs into `https://100.80.103.95/app/command` using credentials from env (`FNT_USERNAME`/`FNT_PASSWORD`, default `command`/`command`).
3. Handles Mandant selection (`/html/command/mandant`).
4. Opens Session Admin Search (`/html/administration/search/session`) and clicks **Search**.
5. Extracts the active `sessionid` cookie / table token.
6. Rewrites `FNT_SESSION_ID` (+ base url/username/password) into the cable-scanner `.env` files.

## Targets written

- `/home/ubuntu/cable-scanner-fnt/.env` (source of truth)
- `/home/ubuntu/remix-of-cable-scan/.env`
- `$(pwd)/.env` (whichever cwd is active)

## Cron (every 4 hours)

A system cron (see `fnt_session_refresh` wrapper) runs the extractor every 4 hours. Verify active cron with:

```bash
crontab -l | grep -i fnt
```

## Pitfalls

- FNT sessions expire; a stale token yields `{"status":{"errorCode":102,"message":"Invalid session","success":false}}`. Re-run this skill to refresh.
- Playwright is NOT in the current npm resolution path — the script falls back to the scratch module dir under `~/.gemini/antigravity-cli/...`. Do not overwrite that require path.
- The old `GET /rest/<entity>/search` endpoints 404 with a valid session — always use the `/api/rest/entity/<type>/query` POST API afterward.