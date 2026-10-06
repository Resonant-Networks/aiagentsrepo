I couldn't patch the SKILL.md due to a tool dedup guard — the reference file was written successfully but the SKILL.md needs manual update. Add this new section after the "When to Use" section and before "Quick start":

---

## Alert → Downstream Device Forensics

When Zabbix fires an infra alert (BGP down, interface down, high latency), the API tells you the *what* and *when* — **it cannot tell you *why***. You MUST go to the device itself to determine root cause:

1. **Are you on a host that can reach the device?** — If this is a containerlab environment, you can `docker exec` into the node.
2. **Check interface state** — Is the interface up at L1? If up, the problem is config/routing, not a cable fault.
3. **Check IP addressing** — Does the interface have a subinterface with an IP? If not, the issue is a configuration gap.
4. **Check routing protocol** — Is BGP/OSPF/ISIS configured? Empty `show bgp neighbor` means "not configured", not "session idle".
5. **Check both sides** — Always verify the peer device too.
6. **Map to topology** — Containerlab env vars and the topology YAML show which links connect to which nodes.

⚠️ **Critical pitfall:** A BGP "DOWN" alert does NOT mean the session was ever up. The probe reports the current state, and an empty BGP config means the session was never established. Distinguish "configuration deficit" from "service outage" before escalating.

Full workflow with SR Linux commands in `references/infra-alert-downstream-diagnostics.md`.

---

Also bump version to `1.1.1` in the YAML frontmatter.