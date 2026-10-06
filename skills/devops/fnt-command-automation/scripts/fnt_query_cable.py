#!/usr/bin/env python3
"""
fnt_query_cable.py — Query FNT Command assets (cables OR racks) by ELID.

Uses the REAL FNT REST entity API:
    POST {base}/api/rest/entity/<entityType>/query?sessionId=<SID>
The session is a QUERY PARAM (not cookie/header). The live session ID is
auto-read from /home/ubuntu/cable-scanner-fnt/.env (FNT_SESSION_ID).
"""
import sys
import os
import argparse
import requests
import urllib3

urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

FNT_BASE_URL = os.getenv("FNT_BASE_URL", "https://100.80.103.95/app/command").rstrip("/")

# Entity type groups
CABLE_ENTITIES = ["cableMaster", "powerCable", "dataCable"]
RACK_ENTITIES = ["switchCabinet"]  # a rack IS a switchCabinet

def load_live_session():
    """Read FNT_SESSION_ID from the cable-scanner .env (source of truth)."""
    for env_path in ["/home/ubuntu/cable-scanner-fnt/.env", os.path.join(os.getcwd(), ".env")]:
        try:
            with open(env_path) as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        k, _, v = line.partition("=")
                        if k.strip() == "FNT_SESSION_ID" and v.strip():
                            return v.strip()
        except OSError:
            continue
    return os.getenv("FNT_SESSION_ID", "")


def query_entity(base, session, entity_type, elid=None):
    url = f"{base}/api/rest/entity/{entity_type}/query?sessionId={session}"
    res = requests.post(url, headers={"content-type": "application/json"},
                        data="{}", verify=False, timeout=20)
    if res.status_code != 200:
        return None, f"HTTP {res.status_code}"
    try:
        data = res.json()
    except ValueError:
        return None, "non-JSON response"
    if not data.get("status", {}).get("success", False):
        return None, data.get("status", {}).get("errorMessage", "status failed")
    records = data.get("returnData", [])
    if not elid:
        return records, None
    key = elid.strip().upper()
    for rec in records:
        for field in ("elid", "visibleId", "id"):
            v = str(rec.get(field, "")).strip().upper()
            if v == key or (v and (v.endswith(key) or key.endswith(v))):
                return rec, None
    return None, "ELID not found in entity"


def main():
    p = argparse.ArgumentParser(description="Query FNT command asset (cable or rack) by ELID")
    p.add_argument("--elid", required=True, help="ELID / visibleId / id to look up")
    p.add_argument("--entity", choices=["cable", "rack", "all"], default="all",
                   help="Which entity group to search (default: all)")
    args = p.parse_args()

    base = FNT_BASE_URL
    SID = load_live_session()
    if not SID:
        print("No FNT_SESSION_ID found in cable-scanner .env — run the session extractor first.")
        sys.exit(1)

    types = []
    if args.entity in ("all", "rack"):
        types += RACK_ENTITIES
    if args.entity in ("all", "cable"):
        types += CABLE_ENTITIES

    found = False
    for t in types:
        rec, err = query_entity(base, SID, t, args.elid)
        if rec is not None:
            print(f"Found in {t}:")
            print(rec)
            found = True
            break
        # don't print routine misses for 'all' runs
    if not found:
        print(f"Nothing found for {args.elid} in {types}")


if __name__ == "__main__":
    main()