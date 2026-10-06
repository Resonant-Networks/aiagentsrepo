#!/usr/bin/env python3
"""
Generic host change-detector for an infra-watchdog.

Snapshots: listening ports, user processes, file inventory of watched dirs,
cron job store, git repos, and health thresholds. Prints ONLY the diff vs a
baseline JSON. Advances baseline each run so each change is reported once.

Process/port noise from the agent's own infra is filtered; tune NOISE_COMM /
HERMES_CMD_RE and EXCLUDE_RE to the host.

Usage:
  python3 host_monitor.py --init --baseline host_baseline.json --dirs /root,/srv,/workspace
  python3 host_monitor.py --baseline host_baseline.json --dirs /root,/srv,/workspace
"""
import argparse
import json
import os
import re
import subprocess
import sys
import datetime

DEFAULT_BASELINE = "host_baseline.json"
MONITORED_DIRS = ["/root", "/srv", "/workspace"]
EXCLUDE_RE = re.compile(r"(^|/)\.hermes(/|$)")  # ignore agent's own churn
NOISE_COMM = {"ps", "head", "sleep", "docker-init", "bash", "sh", "ss"}
HERMES_CMD_RE = re.compile(r"hermes-snap|hermes[ /]|cronjob|host_monitor|service_probe")
DISK_WARN_PCT = 85
MEM_AVAIL_WARN_PCT = 10


def run(cmd):
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return out.stdout
    except Exception:
        return ""


def snap_ports():
    ports = set()
    for flag in ("-tlnpH", "-ulnpH"):
        out = run(["ss", flag])
        for line in out.splitlines():
            parts = line.split()
            if len(parts) < 4:
                continue
            local = parts[4] if len(parts) > 4 else parts[3]
            m = re.search(r":(\d+)$", local)
            if not m:
                continue
            proto = "tcp" if flag.startswith("-t") else "udp"
            proc = parts[-1] if len(parts) >= 5 else ""
            ports.add(f"{proto}:{m.group(1)} {proc}")
    return sorted(ports)


def snap_processes():
    procs = []
    out = run(["ps", "-eo", "pid,user,etimes,comm,args", "--no-headers"])
    self_pid = os.getpid()
    for line in out.splitlines():
        f = line.split(None, 4)
        if len(f) < 5:
            continue
        pid, user, etimes, comm, args = f
        if int(pid) == self_pid or int(pid) == 1:
            continue
        if comm in NOISE_COMM or HERMES_CMD_RE.search(args):
            continue
        procs.append(f"{comm} pid={pid} user={user} t+{etimes}s :: {args[:120]}")
    return sorted(procs)


def snap_files(dirs):
    inv = {}
    for d in dirs:
        if not os.path.isdir(d):
            continue
        for root, ds, files in os.walk(d):
            ds[:] = [x for x in ds if not EXCLUDE_RE.search(os.path.join(root, x))]
            for fn in files:
                p = os.path.join(root, fn)
                if EXCLUDE_RE.search(p) or not os.path.isfile(p):
                    continue
                try:
                    st = os.lstat(p)
                    inv[p] = [st.st_size, int(st.st_mtime)]
                except OSError:
                    continue
    return inv


def snap_cron():
    store = "/root/.hermes/cron"
    jobs = set()
    if os.path.isdir(store):
        for f in os.listdir(store):
            if f.endswith((".json", ".yaml", ".yml")):
                jobs.add(f)
    return sorted(jobs)


def snap_git():
    repos = {}
    for d in ["/root", "/srv", "/workspace", "/home"]:
        if not os.path.isdir(d):
            continue
        out = run(["find", d, "-maxdepth", "5", "-name", ".git", "-type", "d"])
        for line in out.splitlines():
            line = line.strip()
            if line:
                repo = os.path.dirname(line)
                head = run(["git", "-C", repo, "rev-parse", "HEAD"]).strip()
                dirty = bool(run(["git", "-C", repo, "status", "--porcelain"]).strip())
                repos[repo] = {"head": head[:12], "dirty": dirty}
    return repos


def snap_health():
    h = {}
    df = run(["df", "-h", "/"]).splitlines()
    if len(df) >= 2:
        h["disk_used_pct"] = df[1].split()[4].rstrip("%")
    try:
        with open("/proc/meminfo") as fh:
            mi = fh.read()
        avail = re.search(r"MemAvailable:\s+(\d+)", mi)
        total = re.search(r"MemTotal:\s+(\d+)", mi)
        if avail and total:
            h["mem_avail_pct"] = round(int(avail.group(1)) / int(total.group(1)) * 100)
    except Exception:
        pass
    load = run(["cat", "/proc/loadavg"]).split()
    if load:
        h["load1"] = load[0]
    return h


def build_snapshot(dirs):
    return {
        "ports": snap_ports(),
        "processes": snap_processes(),
        "files": snap_files(dirs),
        "cron": snap_cron(),
        "git": snap_git(),
        "health": snap_health(),
    }


def load_baseline(path):
    if os.path.exists(path):
        try:
            with open(path) as fh:
                return json.load(fh)
        except Exception:
            return None
    return None


def save_baseline(path, snap):
    with open(path, "w") as fh:
        json.dump(snap, fh, indent=2, sort_keys=True)


def fmt(title, items, limit=60):
    if not items:
        return ""
    out = [f"\n## {title} ({len(items)})"]
    out += [f"  - {it}" for it in items[:limit]]
    if len(items) > limit:
        out.append(f"  ... +{len(items) - limit} more")
    return "\n".join(out)


def diff_report(prev, cur):
    lines = []
    p_add = sorted(set(cur["ports"]) - set(prev["ports"]))
    p_del = sorted(set(prev["ports"]) - set(cur["ports"]))
    if p_add:
        lines.append(fmt("NEW listening ports", p_add))
    if p_del:
        lines.append(fmt("CLOSED ports", p_del))
    pr_add = sorted(set(cur["processes"]) - set(prev["processes"]))
    pr_del = sorted(set(prev["processes"]) - set(cur["processes"]))
    if pr_add:
        lines.append(fmt("NEW processes", pr_add))
    if pr_del:
        lines.append(fmt("STOPPED processes", pr_del))
    cf, pf = cur["files"], prev["files"]
    added = sorted(k for k in cf if k not in pf)
    removed = sorted(k for k in pf if k not in cf)
    changed = sorted(k for k in cf if k in pf and cf[k] != pf[k])
    if added:
        lines.append(fmt("NEW files", added))
    if removed:
        lines.append(fmt("REMOVED files", removed))
    if changed:
        lines.append(fmt("MODIFIED files", changed))
    c_add = sorted(set(cur["cron"]) - set(prev["cron"]))
    c_del = sorted(set(prev["cron"]) - set(cur["cron"]))
    if c_add:
        lines.append(fmt("NEW scheduled jobs", c_add))
    if c_del:
        lines.append(fmt("REMOVED scheduled jobs", c_del))
    g_add = sorted(k for k in cur["git"] if k not in prev["git"])
    g_head = sorted(k for k in cur["git"] if k in prev["git"] and cur["git"][k]["head"] != prev["git"][k]["head"])
    if g_add:
        lines.append(fmt("NEW git repos", [f"{r} @ {cur['git'][r]['head']}" for r in g_add]))
    if g_head:
        lines.append(fmt("NEW commits", [f"{r} -> {cur['git'][r]['head']}" for r in g_head]))
    h = cur["health"]
    disk = int(str(h.get("disk_used_pct", "0")).rstrip("%") or 0)
    mem = int(h.get("mem_avail_pct", 100) or 100)
    if disk >= DISK_WARN_PCT:
        lines.append(f"\n## HEALTH: disk used {disk}% (>= {DISK_WARN_PCT}%)")
    if mem <= MEM_AVAIL_WARN_PCT:
        lines.append(f"\n## HEALTH: memory available {mem}% (<= {MEM_AVAIL_WARN_PCT}%)")
    return "\n".join(lines)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", default=DEFAULT_BASELINE)
    ap.add_argument("--dirs", default=",".join(MONITORED_DIRS))
    ap.add_argument("--init", action="store_true")
    args = ap.parse_args()
    dirs = [d for d in args.dirs.split(",") if d]

    cur = build_snapshot(dirs)
    if args.init:
        save_baseline(args.baseline, cur)
        print("=== host state :: baseline ===")
        print(f"ports={len(cur['ports'])} procs={len(cur['processes'])} files={len(cur['files'])} cron={len(cur['cron'])} git={len(cur['git'])}")
        print(f"health disk={cur['health'].get('disk_used_pct')} mem_avail={cur['health'].get('mem_avail_pct')}% load1={cur['health'].get('load1')}")
        print(f"\n[baseline -> {args.baseline}]")
        return
    prev = load_baseline(args.baseline)
    if prev is None:
        save_baseline(args.baseline, cur)
        print("[no baseline — created one]")
        return
    report = diff_report(prev, cur)
    save_baseline(args.baseline, cur)
    if report.strip():
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] host changes:{report}")


if __name__ == "__main__":
    main()
