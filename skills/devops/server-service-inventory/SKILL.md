---
name: server-service-inventory
description: "List/access URLs and creds for self-hosted services."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [server, docker, inventory, services, access, credentials, healthcheck, ops]
---

# Server Service Inventory & Access

Use when the user asks how to access/URL the apps on a server ("what's X's URL",
"how do I reach Y", "is Z online", "what's X's password", "list running services").

## Steps

1. **List services + ports:**
   ```
   docker ps --format "table {{.Names}}\t{{.Ports}}\t{{.Status}}"
   ```
   Note binds: `127.0.0.1:P->C` means localhost-only (not reachable from LAN); `0.0.0.0:P` means exposed.

2. **Get host IPs to build URLs** (apps with `0.0.0.0` binds are reachable on any):
   ```
   ip -4 addr show | grep -E "inet " | grep -v 127.0.0.1
   ```
   Offer the most useful reachable IPs (Tailscale if present = works offsite; LAN IP for local).

3. **Health-check an endpoint:**
   ```
   curl -s -o /dev/null -w "HTTP %{http_code} | time: %{time_total}s\n" --max-time 10 http://HOST:PORT/
   ```
   Cross-check container state: `docker ps --filter "name=<svc>" --format "{{.Names}}: {{.Status}}"`.

4. **Recover credentials from container env** (many docker images provision their superuser/login via env vars):
   ```
   docker inspect <container> --format '{{range .Config.Env}}{{println .}}{{end}}' | grep -iE "^SUPERUSER_|POSTGRES|^[A-Z_]*PASSWORD|^[A-Z_]*TOKEN"
   ```
   netbox-docker key vars: `SUPERUSER_NAME`, `SUPERUSER_PASSWORD`, `SUPERUSER_EMAIL`.

## Pitfalls

- **Present redacted when probing broadly** (`sed -E` masking values) so secrets don't dump into chat/logs; reveal the exact value only when the user is the authorized owner/operator asking for their own access.
- **Don't guess/store a password** for apps that use a separate API token (e.g. Zammad MCP) — the token is for automation, not GUI login; point the user to the reset flow instead.
- **localhost-only binds** (127.0.0.1) can't be reached from the user's machine — suggest an SSH tunnel: `ssh -L PORT:localhost:PORT <server>`.
- Remind on **default provisioned passwords** (e.g. docker netbox `adminpassword`) that they're known to anyone who deployed it → rotate after first login.

## References

- `references/rm1-dev-inventory.md` — actual service/URL/credential map for the RM1-dev server.