# RM1-dev Service Inventory

Server: RM1-dev. Hermes container is on the Docker bridge `172.17.0.0/16` sharing the host's `docker0` (gateway `172.17.0.1`).

## Reachable host IPs
Apps with a `0.0.0.0` publish are reachable on any of these:
- Tailscale: `100.80.103.95` (works offsite)
- LAN: `192.168.0.9` (ens18)
- Secondary: `10.90.39.104` (ens20)

## Web apps (pick an IP above; swap `100.80.103.95` for your LAN IP when local)

| App | Port | URL |
|-----|------|-----|
| Zabbix | 8083 | `http://IP:8083` |
| Zabbix (TLS) | 8444 | `https://IP:8444` |
| Zammad | 8084 | `http://IP:8084` |
| Open WebUI | 8085 | `http://IP:8085` |
| Open Terminal | 8086 | `http://IP:8086` |
| Portainer | 9443 | `https://IP:9443` |
| EdgeShark | 5001 | `http://IP:5001` |
| NetBox | 8087 | **localhost only** — `127.0.0.1:8087`; tunnel: `ssh -L 8087:localhost:8087 <server>` |

## Internal / non-browser
- Zabbix relay webhook: `:9099` (alerts relay, not a UI)
- Zabbix server/traps: `:10051` / `:162` (agent protocol)

## Known credentials (owner-managed infra)
- **NetBox superuser** (default provisioned, ROTATE after first login):
  - Username: `admin` / Password: `adminpassword` / Email: `admin@example.com`
  - Source: `netbox-docker-netbox-1` container env `SUPERUSER_*`.
- **Zabbix API** (container): `http://172.17.0.1:8083/api_jsonrpc.php`, Admin/zabbix (default — rotate).
- **Zammad**: automation account `hafiz@resonantnetworks.com` (user_id 3) authenticated via API token (MCP), no GUI password on hand — use the forgot-password flow.

## Health-check quickstart
```
curl -s -o /dev/null -w "HTTP %{http_code}\n" --max-time 10 http://IP:PORT/
docker ps --format "table {{.Names}}\t{{.Status}}" | grep -E "zabbix|zammad|netbox|open|portainer|edgeshark"
```