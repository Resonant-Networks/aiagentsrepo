# Docker / Portainer sibling detection

Scenario: the user pastes a Portainer container list but your Hermes agent runs
inside a *different* container. You may still be on the SAME Docker host.

## Detect it (no docker CLI needed)
- `hostname -i` → if it returns an IP on `172.17.0.0/16`, you're on the default
  bridge. Cross-check the user's pasted list: if one container's IP equals
  `hostname -i`, THAT container is you. (In one session, `hostname -i` returned
  `172.17.0.5` and the pasted list showed `hermes-27027ceb` at `172.17.0.5`.)
- `.dockerenv` exists in your container (`ls -la /.dockerenv`) — confirms you are
  a container, but says nothing about siblings.

## Reach sibling services
- The host publishes ports on the bridge gateway, usually `172.17.0.1`.
  Probe from your container: `curl -s -o /dev/null -w '%{http_code}' http://172.17.0.1:PORT/`
- Internal bridge IPs of OTHER stacks (e.g. `172.21.0.2`, `172.26.0.2`) are
  generally UNREACHABLE from your container — use the host-published port.
- Raw TCP check (no curl): `python3 -c "import socket;s=socket.socket();s.settimeout(4);s.connect(('172.17.0.1',10051));print('open')"`

## Portainer API (limited, no auth)
- `GET https://172.17.0.1:9443/api/status` → returns version JSON, NO token
  needed (useful liveness check: `{"Version":"2.39.3",...}`).
- `GET /api/endpoints` → **requires Bearer token**. Without it you get
  `{"message":"A valid authorization token is missing"}`. So full container
  inventory (running/health/exit state) needs a Portainer admin token. Ask the
  user for one if you need per-container monitoring beyond port probes.

## Watchdog implications
- You can run a silent-unless-change service probe against `172.17.0.1:<port>`
  for every published service even without docker/Portainer API access.
- A container marked "healthy" in Portainer can still be unreachable on its
  published port from your container (seen with Vaultwarden :8080 returning
  connection-refused). Record that as baseline DOWN and flag the discrepancy.
