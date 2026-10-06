# Infra-Alert Downstream Diagnostics

When Zabbix fires an infrastructure-level alert (BGP down, interface down, high latency), the alert tells you *what* is wrong but not *why*. Correct root cause analysis requires verifying at the device level whether the issue is a link fault, a configuration gap, a routing protocol problem, or a monitoring misconfiguration.

## Workflow: Alert → Device Forensics

### 1. Read the Alert Carefully

The Zabbix alert payload usually names:
- The **host** (device name — may be a containerlab node, VM, or physical device)
- The **interface** (e.g. `ethernet-1/1`)
- The **peer** (e.g. `10.0.0.1` for BGP, or a remote IP)
- The **condition** (e.g. "packet loss 100%", "session DOWN", "interface DOWN")

⚠️ **Do not assume a BGP "DOWN" alert means the session ever existed.** The alert only reports the probe's current state.

### 2. Check Interface Layer First

```bash
# Is the interface physically up?
docker exec <node> sr_cli show interface <name> detail
```

Key indicators:
- **Oper state: up** → physical layer is fine. Move to config/routing checks.
- **Oper state: down** → physical issue (cable, optics, remote device down).
- **Last change** + **flaps count** → link bouncing? Check recent history.
- **Traffic counters** → 0 unicast packets on both directions = no data-plane traffic (suggests no IP configured on the link).

### 3. Check IP Configuration

```bash
# Are there subinterfaces with IP addresses?
docker exec <node> sr_cli show interface <name> detail
# Look for the subinterface section — if absent, no IP is configured.
```

SR Linux interfaces can be "up" at L1 with **no L3 configuration** — the interface has `admin-state: enable` in config.json but no `subinterface` section with IPv4/IPv6 addresses.

### 4. Check Routing Protocol Configuration

```bash
# Is BGP configured at all?
docker exec <node> sr_cli show network-instance <name> protocols bgp neighbor

# BGP summary
docker exec <node> sr_cli show network-instance <name> protocols bgp summary
```

**Critical distinction — different output shapes mean different things:**

| Output | Meaning |
|--------|---------|
| `show bgp neighbor` returns **empty** (no output at all) | BGP is **not configured** on this network-instance. No groups, no peers. |
| `show bgp neighbor` returns a neighbor **with state `idle`/`active`/`connect`** | BGP is configured but the session cannot establish (remote unreachable, auth mismatch, passive mode) |
| `show bgp neighbor` returns a neighbor **with state `established`** | Session is up — the alert may be stale or monitoring probe is misconfigured |

### 5. Check Which Network-Instance Exists

SR Linux separates routing domains via network-instances:

```bash
# List all network-instances
docker exec <node> sr_cli show network-instance
```

A vanilla containerlab topology may only have the `mgmt` network-instance. If the alert references a routing protocol but no `default` routing-instance exists, the root cause is **configuration deficit**, not a service outage.

### 6. Check the Peer Device

Always verify both sides of the link:

```bash
docker exec <peer-node> sr_cli show interface <name> detail
docker exec <peer-node> sr_cli show network-instance <name> protocols bgp neighbor
```

The issue may be on the remote side (interface down, BGP not configured, passive mode).

### 7. Check the Topology Context

Containerlab nodes carry labels revealing the lab topology:

```bash
docker inspect <node> --format '{{json .Config.Env}}' | jq -r '.[] | select(startswith("CLAB_LABEL"))'
```

Look for:
- `CLAB_LABEL_CLAB_TOPO_FILE` — the topology YAML that defines links
- `CLAB_LABEL_CLAB_NODE_TYPE` — hardware type (e.g., `ixr-d2l`)
- `CLAB_LABEL_CLAB_NODE_LONGNAME` — full node name

The topology file shows which interfaces connect to which nodes:
```yaml
links:
  - endpoints: [ "leaf1:e1-1", "spine1:e1-1" ]
```

## Real Example: BGP Peer "DOWN" Alert — Root Cause Was Config Gap

**Alert:** "Interface ethernet-1/1 BGP session to 10.0.0.1 is DOWN. Packet loss 100%."

**Device inspection revealed:**
1. leaf1 ethernet-1/1 → **up** (L1 fine)
2. No subinterface/IP configured on ethernet-1/1
3. `show network-instance default protocols bgp neighbor` → **empty** (BGP never configured)
4. Only `mgmt` network-instance existed
5. spine1 (peer) had the same condition
6. Topology file confirmed leaf1⇔spine1 link exists at L1, but no config on top

**Root cause:** BGP was never configured on this lab topology. The monitoring probe was set up to expect a BGP session that the lab environment never provisioned. This is a **configuration deficit** — not a link failure, not a BGP flapping issue, not a routing outage.

**Action recommended:** Configure IP addressing + BGP on the intended link, or adjust the monitoring probe if the session is not supposed to exist yet.

## When to Escalate vs. When to Flag Config Issues

| Finding | Assessment |
|---------|------------|
| Interface DOWN | **Real service issue** — L1 fault. Escalate to network team. |
| Interface UP, no IP configured | **Configuration gap** — likely intentional (lab/DEV), or provisioning failure. Flag to engineer. |
| Interface UP, IP present, BGP empty | **BGP config missing** — provisioning gap or config drift. Engineer should define BGP group/neighbor. |
| BGP neighbor present but idle/active | **Reachability issue** — check ACLs, passwords, remote BGP config, routing to peer IP. |
| BGP neighbor established | **Alert probe misconfiguration** — stale alert or wrong trigger expression. Update Zabbix. |

## Scripted Probe

For reproducible diagnostics, see `scripts/zabbix_probe.py` — extend with a `--device-check` mode that SSHes or docker-execs into the alerted device and runs the interface/BGP checks above, returning a structured assessment.