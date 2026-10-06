# Worked example: "Number of installed packages has been changed" (2026-08-12, RM1-dev)

Real case that validated this recipe end-to-end.

## Question
Why did event **15559** ("Linux: Number of installed packages has been changed",
Warning, host `ubuntu-rm1dev`, 02:09:10 UTC) fire?

## Findings (all via read-only API)
- `event.get 15559` → clock 02:09:10, trigger 23778, expr `{33941}<>0`.
- `trigger.get 23778 selectFunctions` → function `change`, itemid **47350**
  (`{33941}` is a FUNCTION id — `item.get` by 33941 returns `[]`).
- `item.get 47350` (`system.sw.packages.get`): prevvalue **1005** → lastvalue **1006**
  = exactly ONE package added.
- Correlation: item 47417 `vfs.fs.dependent.size[/,pused]` history (`history=0`,
  float) showed `/` usage **78.7% → 81.2%** (~2.4 GB of 95.1 GB) between 01:58 and
  02:16 UTC, crossing the 80% warn → companion event **15560** fired 02:18:41
  (trigger uses `min(15m) > 80%`, stays PROBLEM while >80%).
- Same trigger had fired + auto-resolved earlier (event 15340, resolved Aug 11
  16:09) → recurring routine, not a one-off.

## Diagnosis
02:00–02:16 UTC + one new package + ~2.4 GB = **unattended-upgrades /
apt-daily-upgrade.timer** (Ubuntu nightly ~02:00 with random delay); a kernel
security update (new `linux-image` + headers + firmware) is the classic
"+1 package, ~2 GB" case.

## Boundary honored
Exact package name NOT in Zabbix — requires host-side:
```bash
grep -E " (install|remove|upgrade) " /var/log/dpkg.log | tail -15
tail -40 /var/log/apt/history.log
```

## Trigger semantics notes
- `change()` triggers auto-recover at the next poll (hourly item → ~03:09 UTC here),
  which explains "still active" for event 15559.
- Threshold triggers with `min()` stay PROBLEM until the condition clears —
  event 15560 remained active while `/` stayed above 80%.
