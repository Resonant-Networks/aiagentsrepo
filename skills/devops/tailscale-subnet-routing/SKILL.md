---
name: tailscale-subnet-routing
description: "Advertise/inspect Tailscale subnet routes on a node."
version: 1.0.0
author: Hermes Agent
license: MIT
platforms: [linux]
metadata:
  hermes:
    tags: [tailscale, networking, subnet, routes, vpn]
---

# Tailscale Subnet Routing (node side)

## When to Use

Use when the user asks to advertise/remove a LAN subnet through Tailscale, or to
list which subnets are being advertised right now ("what subnet is tailscale
advertising", "advertise 10.x.y.0/24", "is 172.16.0.0/16 routed").

Applies to this host as a tailnet node (`tailscale` CLI + `tailscaled`).

## Inspect what subnets are advertised / routable now

```bash
tailscale status --json | python3 -c "import json,sys; d=json.load(sys.stdin); s=d['Self']; print('Self.AdvertisedRoutes:', s.get('AdvertisedRoutes')); print('Self.AllowedIPs:', s.get('AllowedIPs'))"
```

- `Self.AdvertisedRoutes` — what THIS node advertises (see approval caveat below).
- `Self.AllowedIPs` — only `self /32` + IPv6 `/128` unless it advertises subnets AND they're accepted.
- Peers that advertise subnets expose them under `Peer[*].AllowedIPs` as extra CIDRs beyond their `/32` (e.g. `..., '10.90.39.0/24']`).
- Peer-sourcing this way is authoritative for "what subnet X advertises".
- `tailscale status` tabular output for a human-readable list of nodes.

## Advertise a subnet on this node

```bash
# REQUIRED: must run as root, otherwise:
#   "Access denied: checkprefs access denied"
sudo tailscale set --advertise-routes=10.10.10.0/24
```

To avoid sudo for `tailscale *` going forward, run once (as root):
```bash
sudo tailscale set --operator=$USER
```

## Verify the change actually committed

`tailscale status --json` `.Self.AdvertisedRoutes` is UNRELIABLE immediately after
`set` — it can stay `None` even when the route was written (netmap lags / only
reflects approved routes). The authoritative confirm is the stored prefs:

```bash
sudo tailscale debug prefs | python3 -c "import json,sys; p=json.load(sys.stdin); print('AdvertiseRoutes:', p.get('AdvertiseRoutes'))"
```

And the tailscaled log proves the write + router reconfig:
```bash
sudo journalctl -u tailscaled --no-pager -n 200 | grep -iE "EditPrefs|AdvertiseRoutes|Reconfig"
# expect:  EditPrefs: MaskedPrefs{AdvertiseRoutes=[10.10.10.0/24]}  &&  wgengine: Reconfig: configuring router
```

## Approval requirement (the common gotcha)

Advertised-but-unapproved subnet routes:
- Prefs are committed locally (`debug prefs` shows them).
- But `Self.AdvertisedRoutes` in `status --json` reads `None` and remote peers will
  NOT install the route until it's approved.

**Approve in the admin console** → https://login.tailscale.com/admin/machines →
select the node → Approve/Edit route for the CIDR. Until approved, the route is
staged, not acting. Subnet routes are NEVER usable by peers until approved (unless
the tailnet has auto-approval enabled).

Also note `RouteAll` default is `false` — a peer needs "Use Tailscale subnets
(accept routes)" enabled on its end to install/route to your advertised subnet.

## Undo

```bash
sudo tailscale set --advertise-routes=""   # clear all advertised routes on this node
```

## Pitfalls

- **Always prefix with `sudo`** — token auth / access `checkprefs access denied` otherwise.
- **Don't report "advertised" from `status --json` alone right after set** — cross-check `debug prefs`. Distinguish "committed locally" from "approved + active".
- **Don't fabricate** that a route is live for clients before admin-console approval; be explicit it is pending.
- `tailscale set --advertise-routes` is a local prefs edit + router reconfig, not a disruption of the existing tunnel — no need to `tailscale up` to apply it.