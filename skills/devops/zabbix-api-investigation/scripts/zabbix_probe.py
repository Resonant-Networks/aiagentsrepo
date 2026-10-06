#!/usr/bin/env python3
"""Zabbix API forensic probe (READ-ONLY).

Usage:
  python3 zabbix_probe.py --event 15559 [--event 15560] \
      [--url http://172.17.0.1:8083/api_jsonrpc.php] \
      [--user Admin] [--pass zabbix] [--hours 8]

Prints per event: clock/status/severity/name, trigger expression, resolved item
ids, item last/prev values, a value history around the event clock, and other
active problems on the host. Never calls a mutating API method.

Validated against Zabbix 6.4.21 (see SKILL.md "Zabbix 6.4 API quirks").
"""
import argparse
import json
import urllib.request
from datetime import datetime, timezone


def call(url, method, params, auth=None):
    payload = {"jsonrpc": "2.0", "method": method, "params": params, "id": 1}
    if auth:
        payload["auth"] = auth
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json-rpc"},
    )
    r = json.loads(urllib.request.urlopen(req, timeout=10).read())
    if "error" in r:
        raise RuntimeError(r["error"])
    return r["result"]


def utc(ts):
    return datetime.fromtimestamp(int(ts), timezone.utc).strftime("%Y-%m-%d %H:%M:%S")


def main():
    ap = argparse.ArgumentParser(description="Zabbix read-only alert forensics")
    ap.add_argument("--event", action="append", required=True, help="event id (repeatable)")
    ap.add_argument("--url", default="http://172.17.0.1:8083/api_jsonrpc.php")
    ap.add_argument("--user", default="Admin")
    ap.add_argument("--pass", dest="pw", default="zabbix")
    ap.add_argument("--hours", type=int, default=8, help="history window before/after event")
    a = ap.parse_args()

    auth = call(a.url, "user.login", {"username": a.user, "password": a.pw})
    # apiinfo.version must NOT receive the auth token (6.4 quirk)
    print("Zabbix API:", call(a.url, "apiinfo.version", {}))

    evs = call(
        a.url,
        "event.get",
        {
            "eventids": a.event,
            "output": ["eventid", "clock", "value", "severity", "name"],
            "selectHosts": ["host"],
            "selectRelatedObject": ["triggerid", "description", "expression"],
        },
        auth,
    )
    for e in evs:
        t0 = int(e["clock"])
        print("\n== EVENT", e["eventid"], "|", utc(t0), "|",
              "PROBLEM" if e["value"] == "1" else "RESOLVED")
        print("  ", e["name"], "| hosts:", [h["host"] for h in e.get("hosts", [])])
        robj = e.get("relatedObject", {})
        print("   trigger:", robj.get("description"))
        trig = call(
            a.url,
            "trigger.get",
            {"triggerids": [robj["triggerid"]],
             "output": ["description", "expression"], "selectFunctions": "extend"},
            auth,
        )[0]
        print("   expr:", trig["expression"])
        for f in trig.get("functions", []):
            iid = f["itemid"]
            it = call(
                a.url,
                "item.get",
                {"itemids": [iid],
                 "output": ["itemid", "key_", "name", "value_type", "lastvalue",
                            "lastclock", "prevvalue", "units"]},
                auth,
            )
            if not it:
                print(f"   (item {iid} not found)")
                continue
            x = it[0]
            print(f"   -> item {x['itemid']} {x['key_']} | {x['name']}"
                  f" | last: {x['lastvalue']} {x['units']} at {utc(x['lastclock'])}"
                  f" | prev: {x.get('prevvalue')}")
            htype = {0: 0, 3: 3}.get(int(x.get("value_type", 0)), 0)  # float/int
            hist = call(
                a.url,
                "history.get",
                {"history": htype, "itemids": [iid], "output": ["clock", "value"],
                 "time_from": t0 - a.hours * 3600,
                 "time_till": t0 + a.hours * 3600 // 2,
                 "sortfield": "clock", "sortorder": "ASC"},
                auth,
            )
            for h in hist:
                print(f"      {utc(h['clock'])} -> {h['value']}")
        hosts = [h["host"] for h in e.get("hosts", [])]
        if hosts:
            probs = call(
                a.url,
                "problem.get",
                {"host": hosts[0], "output": ["eventid", "clock", "name", "severity"]},
                auth,
            )
            if probs:
                print("   active problems on", hosts[0], ":")
                for p in probs:
                    print(f"      #{p['eventid']} [{p['severity']}] {p['name']} since {utc(p['clock'])}")


if __name__ == "__main__":
    main()
