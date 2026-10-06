# FNT Command API Reference Cheatsheet

## Overview
FNT Command supports two integration methods:
1. **SOAP Web Service (Legacy Auth)**: Used for initial user login with Blowfish password encryption.
2. **REST API (Data Query)**: Used for entity queries (`cableMaster`, `powerCable`, `dataCable`, etc.) using session tokens.

---

## 1. SOAP Login & Mandant Selection

### SOAP Endpoint
`POST https://100.80.103.95/app/command/soap/v1/auth`

### Login Request Envelope
```xml
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/" xmlns:auth="http://www.fnt.de/command/soap/auth">
   <soapenv:Header/>
   <soapenv:Body>
      <auth:login>
         <auth:user>command</auth:user>
         <auth:encryptedPassword>ENCRYPTED_BLOWFISH_STRING</auth:encryptedPassword>
      </auth:login>
   </soapenv:Body>
</soapenv:Envelope>
```

---

## 2. REST API Queries

### Authentication
- Every request passes the session as a **query param**: `?sessionId=<SESSION_ID>`.
- The live session ID lives in `/home/ubuntu/cable-scanner-fnt/.env` as `FNT_SESSION_ID`. Read it from there; re-login (SOAP below) only if it expires.
- (Header `Cookie: sessionid=` / `X-FNT-Session-Id:` are NOT used by the entity API.)

### Endpoints (POST, `content-type: application/json`, body `{}`)
- **Query entities**: `POST {base}/api/rest/entity/<entityType>/query?sessionId=<SID>`
  - `entityType` tokens: `cableMaster`, `powerCable`, `dataCable` (cables); **`switchCabinet` (rack)**; `junctionBox`, `chassis`; `building`, `room`, `floor`, `campus`.
  - For rich attributes (switchCabinet/junctionBox/chassis): use `queryExtended` first, fall back to `query`.
- **Rack sub-devices**: `POST {base}/api/rest/entity/switchCabinet/<elid>/SubDevices?sessionId=<SID>`
- **Session Check**: `GET /app/command/html/administration/search/session`

### Pitfall (IMPORTANT)
The previously-documented `GET /rest/<entity>/search?q=<ELID>` endpoints return **HTTP 404** even with a valid session. Use the `/api/rest/entity/<entityType>/query` POST API above.

---

## 3. Playwright Automation Shortcut

To retrieve a fresh `sessionid` automatically without manual browser interaction:
```bash
node /home/ubuntu/.hermes/skills/devops/fnt-command-automation/scripts/fnt_session_extractor.js
```
