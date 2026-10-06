#!/usr/bin/env python3
"""
FNT Random ELID Fetcher
Queries live FNT Command REST API for random valid ELIDs across Cable, Rack, and Equipment/ODF modules.
"""

import argparse
import json
import os
import random
import ssl
import sys
import urllib.parse
import urllib.request

DEFAULT_ENV_PATHS = [
    "/home/ubuntu/cable-scanner-fnt/.env",
    "/home/ubuntu/.env",
]

ENTITY_MAP = {
    "rack": [("switchCabinet", "Datacenter Rack / Cabinet")],
    "equipment": [
        ("junctionBox", "ODF / Distribution Box"),
        ("chassis", "Network Switch / Chassis"),
    ],
    "cable": [
        ("dataCable", "Data Cable"),
        ("cableMaster", "Fiber Trunk / Master"),
        ("powerCable", "Power Cable"),
    ],
}


def load_env(custom_path=None):
    paths = [custom_path] if custom_path else DEFAULT_ENV_PATHS
    env = {}
    for p in paths:
        if p and os.path.exists(p):
            with open(p, "r", encoding="utf-8") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        env[k.strip()] = v.strip().strip("\"'")
            if env.get("FNT_SESSION_ID"):
                break
    return env


def query_fnt_entities(base_url, session_id, entity_type):
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    url = f"{base_url.rstrip('/')}/api/rest/entity/{entity_type}/query?sessionId={urllib.parse.quote(session_id)}"
    req = urllib.request.Request(
        url,
        data=b"{}",
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )

    try:
        with urllib.request.urlopen(req, context=ctx, timeout=15) as resp:
            data = json.loads(resp.read().decode("utf-8"))
            return data.get("returnData", [])
    except Exception as e:
        print(f"[Warning] Failed querying {entity_type}: {e}", file=sys.stderr)
        return []


def get_random_elids(module="all", count_per_type=1, custom_env=None):
    env = load_env(custom_env)
    base_url = env.get("FNT_BASE_URL", "https://100.80.103.95/app/command")
    session_id = env.get("FNT_SESSION_ID")

    if not session_id:
        print("Error: No FNT_SESSION_ID found in environment or .env files.", file=sys.stderr)
        sys.exit(1)

    targets = []
    if module == "all":
        for mod, ent_list in ENTITY_MAP.items():
            for ent, label in ent_list:
                targets.append((mod, ent, label))
    elif module in ENTITY_MAP:
        for ent, label in ENTITY_MAP[module]:
            targets.append((module, ent, label))
    else:
        print(f"Error: Unknown module '{module}'. Use 'cable', 'rack', 'equipment', or 'all'.", file=sys.stderr)
        sys.exit(1)

    results = []
    for mod, ent, label in targets:
        items = query_fnt_entities(base_url, session_id, ent)
        if not items:
            continue

        sample_size = min(count_per_type, len(items))
        sampled = random.sample(items, sample_size)

        for item in sampled:
            elid = item.get("elid")
            vis_id = item.get("visibleId") or item.get("id") or "N/A"
            name = item.get("name") or vis_id
            explanation = item.get("explanation") or item.get("type") or ""
            building = item.get("building") or ""
            room = item.get("room") or ""
            location_str = f"{building} / {room}".strip(" /") or "N/A"

            results.append({
                "module": mod,
                "category": label,
                "entityType": ent,
                "elid": elid,
                "visibleId": vis_id,
                "name": name,
                "details": explanation,
                "location": location_str,
            })

    return results


def main():
    parser = argparse.ArgumentParser(description="Fetch random real ELIDs from FNT Command across modules.")
    parser.add_argument(
        "--module", "-m",
        choices=["all", "cable", "rack", "equipment"],
        default="all",
        help="Target datacenter module (default: all)",
    )
    parser.add_argument(
        "--count", "-c",
        type=int,
        default=1,
        help="Number of random items per entity type (default: 1)",
    )
    parser.add_argument(
        "--json", "-j",
        action="store_true",
        help="Output raw JSON array instead of formatted markdown table",
    )
    parser.add_argument(
        "--env",
        type=str,
        default=None,
        help="Custom path to .env containing FNT_SESSION_ID",
    )

    args = parser.parse_args()
    results = get_random_elids(module=args.module, count_per_type=args.count, custom_env=args.env)

    if args.json:
        print(json.dumps(results, indent=2))
        return

    if not results:
        print("No entities found.")
        return

    print("\n### 🎲 Random FNT Datacenter ELIDs\n")
    print(f"| Module | Category | ELID | Barcode / Visible ID | Name / Model | Location |")
    print(f"| :--- | :--- | :--- | :--- | :--- | :--- |")
    for r in results:
        mod_icon = "🔌" if r["module"] == "cable" else "🖥️" if r["module"] == "rack" else "🎛️"
        print(f"| {mod_icon} **{r['module'].title()}** | {r['category']} | `{r['elid']}` | **{r['visibleId']}** | {r['name']} | {r['location']} |")
    print("")


if __name__ == "__main__":
    main()
