---
name: fnt-session-extractor
description: Automate FNT Command browser login, Mandant selection, session search, and active token extraction via Playwright.
---

# FNT Command Session Extractor Skill

Use this skill when you need to fetch, refresh, or extract a fresh active `sessionid` token from FNT Command (`https://100.80.103.95/app/command`).

## When to Activate

- User asks to "fetch FNT session ID", "extract session token from browser", or "login to FNT Command to get session".
- FNT REST API returns `401 Unauthorized` or `503 Session Expired` and needs session refresh.
- Setting up or updating `.env` credentials for the Cable Scanner PWA.

## Execution Recipe

Run the headless browser extraction script:
```bash
node /home/ubuntu/.gemini/config/skills/fnt-session-extractor/scripts/fnt_session_extractor.js
```

## What the Automation Does

1. **Launches Headless Browser** (Chromium via Playwright with `ignoreHTTPSErrors: true`).
2. **Logs In**: Navigates to `https://100.80.103.95/app/command`, fills credentials (`command` / `command`), and clicks **OK**.
3. **Mandant Selection**: Navigates to `/html/command/mandant` and confirms Mandant selection.
4. **Session Administration Search**: Navigates to `/html/administration/search/session` and clicks **Search**.
5. **Token Extraction**: Extracts the active `sessionid` cookie & table row.
6. **Environment Sync**: Automatically updates `FNT_SESSION_ID` across `.env` files in the workspace.
