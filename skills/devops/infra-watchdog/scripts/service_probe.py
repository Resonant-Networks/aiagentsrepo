#!/usr/bin/env python3
"""
Generic service-health probe for an infra-watchdog.

Reads an endpoint list (JSON: [{name,url,kind,note}]) and probes each:
  - kind "http"/"https": curl, capture HTTP code + latency
  - kind "tcp": raw socket connect
Prints ONLY state transitions vs a baseline JSON (new/up/down/status-class/latency).
Advances baseline each run so each change is reported exactly once.

Usage:
  python3 service_probe.py --init --endpoints endpoints.json --baseline svc_baseline.json
  python3 service_probe.py --endpoints endpoints.json --baseline svc_baseline.json
"""
import argparse
import json
import os
import socket
import subprocess
import sys
import datetime

DEFAULT_ENDPOINTS = "endpoints.json"
DEFAULT_BASELINE = "svc_baseline.json"
TIMEOUT = 6


def probe(ep):
    url = ep["url"]
    if url.startswith("tcp://"):
        host, port = url[6:].split(":")
        s = socket.socket()
        s.settimeout(TIMEOUT)
        try:
            s.connect((host, int(port)))
            return {"ok": True, "code": 0, "ms": 1, "tcp": True}
        except Exception as e:
            return {"ok": False, "code": 0, "ms": None, "err": f"tcp:{e}"}
        finally:
            s.close()
    insecure = ["-k"] if url.startswith("https") else []
    cmd = ["curl", "-s", "-o", "/dev/null", "-w", "%{http_code} %{time_total}",
           "--max-time", str(TIMEOUT)] + insecure + [url]
    try:
        out = subprocess.run(cmd, capture_output=True, text=True, timeout=TIMEOUT + 2)
        text = out.stdout.strip()
        if " " in text:
            code_s, t_s = text.split()
            return {"ok": True, "code": int(code_s), "ms": round(float(t_s) * 1000)}
        return {"ok": False, "code": 0, "ms": None, "err": "no-output"}
    except subprocess.TimeoutExpired:
        return {"ok": False, "code": 0, "ms": None, "err": "timeout"}
    except Exception as e:
        return {"ok": False, "code": 0, "ms": None, "err": str(e)[:40]}


def snap(endpoints):
    return {ep["name"]: {"url": ep["url"], "state": probe(ep)} for ep in endpoints}


def load(path):
    if os.path.exists(path):
        try:
            with open(path) as fh:
                return json.load(fh)
        except Exception:
            return None
    return None


def save(path, s):
    with open(path, "w") as fh:
        json.dump(s, fh, indent=2, sort_keys=True)


def code_class(c):
    return "down" if c == 0 else f"{c // 100}xx"


def diff(prev, cur):
    lines = []
    for name, info in cur.items():
        st = info["state"]
        ps = prev.get(name, {}).get("state") if prev else None
        if ps is None:
            lines.append(f"  - {name}: NEW + {'UP' if st['ok'] else 'DOWN (' + str(st.get('err')) + ')'}")
            continue
        if st["ok"] and not ps.get("ok"):
            lines.append(f"  - {name}: RECOVERED (HTTP {st['code']}, {st['ms']}ms)")
        elif not st["ok"] and ps.get("ok"):
            lines.append(f"  - {name}: WENT DOWN ({st.get('err')}) was HTTP {ps.get('code')}")
        elif st["ok"] and ps.get("ok"):
            if code_class(st["code"]) != code_class(ps.get("code")):
                lines.append(f"  - {name}: status class {ps.get('code')} -> {st['code']}")
            elif st["ms"] and ps.get("ms") and st["ms"] >= max(5000, ps["ms"] * 2):
                lines.append(f"  - {name}: latency spike {ps['ms']}ms -> {st['ms']}ms")
    return lines


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--endpoints", default=DEFAULT_ENDPOINTS)
    ap.add_argument("--baseline", default=DEFAULT_BASELINE)
    ap.add_argument("--init", action="store_true")
    args = ap.parse_args()

    with open(args.endpoints) as fh:
        endpoints = json.load(fh)
    cur = snap(endpoints)
    if args.init:
        save(args.baseline, cur)
        print("=== service health :: baseline ===")
        for ep in endpoints:
            st = cur[ep["name"]]["state"]
            status = f"UP HTTP {st['code']} {st['ms']}ms" if st["ok"] else f"DOWN ({st.get('err')})"
            print(f"  - {ep['name']:14s} {status}")
        print(f"\n[baseline -> {args.baseline}]")
        return
    prev = load(args.baseline)
    if prev is None:
        save(args.baseline, cur)
        print("[no baseline — created one]")
        return
    changes = diff(prev, cur)
    save(args.baseline, cur)
    if changes:
        ts = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{ts}] service changes:\n" + "\n".join(changes))


if __name__ == "__main__":
    main()
