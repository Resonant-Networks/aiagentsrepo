---
name: fnt-elid-fetcher
description: Fetch random real ELIDs from live FNT Command database across Cable, Rack, and Equipment/ODF modules for testing, scanning verification, and infrastructure lookups.
---

# FNT Random ELID Fetcher Skill

Use this skill whenever you or the user need random, valid ELIDs from FNT Command (`https://100.80.103.95/app/command`) across different datacenter modules: **Cable**, **Rack**, and **Equipment (including ODFs)**.

## When to Activate

- User asks for "a random ELID to test", "sample barcode for ODF", "rack barcode", or "cable ELID".
- Testing the Cable Scanner PWA (`/scanner` or `/scanner/test-qrcodes`).
- Verifying FNT API connectivity and entity lookups.

## Execution Recipes

### 1. Fetch Random ELIDs Across All Modules
```bash
python3 /home/ubuntu/.gemini/config/skills/fnt-elid-fetcher/scripts/get_random_elid.py
```

### 2. Fetch for a Specific Module
```bash
# Only Racks (e.g. 42U switch cabinets)
python3 /home/ubuntu/.gemini/config/skills/fnt-elid-fetcher/scripts/get_random_elid.py --module rack --count 3

# Only Equipment / ODFs (junctionBox, chassis, switches)
python3 /home/ubuntu/.gemini/config/skills/fnt-elid-fetcher/scripts/get_random_elid.py --module equipment --count 3

# Only Cables (fiber data cables, power cables, master trunks)
python3 /home/ubuntu/.gemini/config/skills/fnt-elid-fetcher/scripts/get_random_elid.py --module cable --count 3
```

### 3. Programmatic Output (JSON)
```bash
python3 /home/ubuntu/.gemini/config/skills/fnt-elid-fetcher/scripts/get_random_elid.py --json
```

## How It Works

1. **Authentication**: Reads the active `FNT_SESSION_ID` and `FNT_BASE_URL` automatically from `/home/ubuntu/cable-scanner-fnt/.env`.
2. **Entity Queries**: Calls the FNT REST API (`POST /api/rest/entity/{entityType}/query?sessionId=...`):
   - **Rack**: `switchCabinet` (1,420+ racks)
   - **Equipment / ODF**: `junctionBox` (ODF fiber cassettes) & `chassis` (switches/routers)
   - **Cable**: `dataCable`, `cableMaster`, `powerCable` (26,000+ cables)
3. **Random Sampling**: Randomly samples items so each run provides fresh test data with both 14-character alphanumeric ELIDs and human-readable Barcode/Visible IDs.
