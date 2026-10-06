---
name: alm-fault-analysis
description: ALM fiber fault GPS via REST API + route triangulation.
version: 1.0.0
author: hermes-curator
metadata:
  hermes:
    tags: [ALM, fiber, OTDR, fault-analysis, GPS, NOC]
    related_skills: [zabbix-api-investigation, slack-incident]
---

# ALM Fiber Fault Analysis — REST API + GPS Triangulation

## When to Use

- An ALM incident arrives: "Fiber Cut", "Fast Loss Deviation", "Port N Monitoring Inactive", or "New OTDR Fault Analysis Run Completed"
- You need the **exact GPS coordinates** of a fiber fault by combining the auto FA distance with the KML route geometry
- You need a Google Maps link to dispatch the field team

## Prerequisites

- ALM REST API credentials: **`admin:chgme.1a`**
- ALM device reachable at `10.10.10.3` (HTTPS)
- The ALM unit's own location: **Lat 2.925867, Lon 101.662949** (CoPlace 2, Cyberjaya)

## Recommended Method: Standalone CLI

Whenever asked to perform or redo fault triangulation, use the pre-built CLI tool which queries the ALM REST API (inspecting both Automatic and Manual Fault Analysis traces and picking the freshest), computes route Haversine coordinates, and formats the output cleanly:

```bash
python3 ~/.hermes/skills/slack-incident/scripts/triangulate_alm.py --port <PORT> [--source both|auto|manual]
```

If responding in an active Slack incident channel thread, post the formatted card directly to the thread:

```bash
python3 ~/.hermes/skills/slack-incident/scripts/triangulate_alm.py --port <PORT> --channel <CHANNEL_ID> --thread-ts <THREAD_TS>
```

---

## Workflow

### 1. Extract the Port Number from the Incident

Extract via regex: `r'Port\s+(\d+)'` or `r'port\s+(\d+)'` (case-insensitive) from the alert title.

### 2. Fetch Latest Fault Analysis Data (Check Both Auto and Manual FA)

The ALM stores fault traces in two distinct REST endpoints:
- **Automatic FA (`/af/list`)**: Traces triggered automatically by alarms/loss deviations.
- **Manual FA (`/fa/list`)**: Traces triggered manually by engineers from the ALM WebGUI.

When asked to redo or refresh triangulation, **query both endpoints and select the one with the freshest timestamp**:

```bash
# Check Automatic FA:
curl -sk --max-time 10 -u 'admin:chgme.1a' \
  'https://10.10.10.3/trace/<PORT>/af/list'

# Check Manual FA:
curl -sk --max-time 10 -u 'admin:chgme.1a' \
  'https://10.10.10.3/trace/<PORT>/fa/list'
```

Compare `timestamp` (`YYYY-MM-DD HH:MM:SS`) between the first entry of `/af/list` and `/fa/list`. Use the trace with the most recent timestamp.

Key checks on `faultpos`:
- If `faultpos` is `null` or `-1` → **no fault detected** (link normal)
- If `faultpos` is `"0.0"` or `0` → **fault at origin / ALM port itself** (patch cord removed, connector disconnected, or cut directly at ODF / ALM transceiver). Fault distance is **0.0m**.
- If `faultpos` is a positive number → fault distance in **meters** from start of fiber route
- Clearly label whether the measurement is **Automatic FA** or **Manual FA**.

### 3. Fetch KML Route (REST API)

```bash
curl -sk --max-time 10 -u 'admin:chgme.1a' \
  'https://10.10.10.3/trace/route/<PORT>'
```

Response is a KML file with `<coordinates>lon,lat,0  lon,lat,0...</coordinates>`.

Edge cases:
- **HTTP 404**: port has no route → fall back to ALM unit coordinates + distance
- **Empty KML / no coordinates**: same fallback
- **Only 1 coordinate pair**: a straight line — usable but less precise

### 4. Triangulate GPS (Haversine Interpolation)

```python
from math import radians, cos, sin, sqrt, atan2

R = 6371000

def haversine(lon1, lat1, lon2, lat2):
    dlat = radians(lat2 - lat1)
    dlon = radians(lon2 - lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1)) * cos(radians(lat2)) * sin(dlon/2)**2
    c = 2 * atan2(sqrt(a), sqrt(1-a))
    return R * c

def triangulate_fault(waypoints, fault_distance_m):
    """waypoints: list of (lon, lat) tuples. Returns (lat, lon) or None."""
    if not waypoints:
        return None
    if fault_distance_m <= 0:
        # Origin / ODF fault: return Waypoint 0
        return (waypoints[0][1], waypoints[0][0])

    cumulative = [0.0]
    for i in range(1, len(waypoints)):
        d = haversine(waypoints[i-1][0], waypoints[i-1][1],
                      waypoints[i][0], waypoints[i][1])
        cumulative.append(cumulative[-1] + d)

    if fault_distance_m >= cumulative[-1]:
        return None  # fault beyond route end

    for i in range(1, len(waypoints)):
        if cumulative[i] >= fault_distance_m:
            seg_start = cumulative[i-1]
            seg_end = cumulative[i]
            frac = (fault_distance_m - seg_start) / (seg_end - seg_start) if seg_end > seg_start else 0
            interp_lon = waypoints[i-1][0] + (waypoints[i][0] - waypoints[i-1][0]) * frac
            interp_lat = waypoints[i-1][1] + (waypoints[i][1] - waypoints[i-1][1]) * frac
            return (interp_lat, interp_lon)
    return None
```

### 5. Generate Google Maps Link

```python
gmaps_url = f"https://www.google.com/maps?q={fault_lat},{fault_lon}"
```

### 6. Deliver to Engineer

```
FAULT GPS: {lat}, {lon}
Google Maps: {gmaps_url}
Distance: {fault_distance}m along route
Route total: {route_length:.0f}m
```

Also save the KML:

```bash
curl -sk --max-time 10 -u 'admin:chgme.1a' \
  'https://10.10.10.3/trace/route/<PORT>' \
  -o /home/ubuntu/port<N>_route.kml
```

## Edge Cases & Fallbacks

| Condition | Action |
|---|---|
| `faultpos` is null, -1, or empty | Report "No fault detected / Link healthy" |
| `faultpos` is "0.0" or 0 | Report "Fault at origin / ALM port / ODF (0.0m)". Use Waypoint 0 GPS |
| KML returns 404 / has <2 waypoints | Report ALM unit coords (2.925867, 101.662949) + distance only |
| Fault distance > route total length | Report fault lies beyond mapped route at {dist}m. Show route end GPS |
| REST API returns 401 | Fall back to SNMP method (see `alm-fiber-monitoring.md` reference) |
| `fault_latitude`/`fault_longitude` are non-null | Use them directly — no triangulation needed |
| Port number > 16 | Invalid — ALM has ports 1-16 |

## Full Implementation Snippet

```python
from hermes_tools import terminal
from math import radians, cos, sin, sqrt, atan2
import json, re

PORT = extract_port_number(alert_title)
REST_USER = "admin"
REST_PASS = "chgme.1a"
BASE_URL = f"https://10.10.10.3/trace/{PORT}"

# Fetch both Automatic and Manual FA, picking the freshest timestamp
candidates = []
for ep in ["af", "fa"]:
    r = terminal(f"curl -sk --max-time 10 -u '{REST_USER}:{REST_PASS}' '{BASE_URL}/{ep}/list'")
    try:
        items = json.loads(r['output']).get('data', [])
        if items:
            candidates.append(items[0])
    except Exception:
        pass

if not candidates:
    return "No fault analysis trace found on ALM"

latest = max(candidates, key=lambda x: x.get('timestamp') or '')
faultpos = latest.get('faultpos')
if faultpos is None or float(faultpos) < 0:
    return f"No fault detected (Latest: {latest.get('type')})"

fault_distance = float(faultpos)
trace_type = latest.get('type')
trace_ts = latest.get('timestamp')

r = terminal(f"curl -sk --max-time 10 -u '{REST_USER}:{REST_PASS}' '{BASE_URL}/route'")
match = re.search(r'<coordinates>(.*?)</coordinates>', r['output'], re.DOTALL)
if not match:
    return f"No KML route for port {PORT}. Fault at {fault_distance}m from ALM (2.925867, 101.662949)"

waypoints = []
for point in match.group(1).strip().split():
    parts = point.split(',')
    if len(parts) >= 2:
        waypoints.append((float(parts[0]), float(parts[1])))

if len(waypoints) < 2:
    return f"Route too short for triangulation. Fault at {fault_distance}m"

R = 6371000
def h(lon1, lat1, lon2, lat2):
    dlat, dlon = radians(lat2-lat1), radians(lon2-lon1)
    a = sin(dlat/2)**2 + cos(radians(lat1))*cos(radians(lat2))*sin(dlon/2)**2
    return 2 * R * atan2(sqrt(a), sqrt(1-a))

cum = [0.0]
for i in range(1, len(waypoints)):
    cum.append(cum[-1] + h(waypoints[i-1][0], waypoints[i-1][1], waypoints[i][0], waypoints[i][1]))

if fault_distance <= 0:
    lat, lon = waypoints[0][1], waypoints[0][0]
    print(f"FAULT GPS: {lat}, {lon}")
    print(f"Google Maps: https://www.google.com/maps?q={lat},{lon}")
    print(f"Distance: 0.0m (Local Origin / ODF / Transceiver Disconnect) | Route: {cum[-1]:.0f}m")
elif fault_distance > cum[-1]:
    return f"Fault at {fault_distance}m exceeds route length {cum[-1]:.0f}m"
else:
    for i in range(1, len(waypoints)):
        if cum[i] >= fault_distance:
            frac = (fault_distance - cum[i-1]) / (cum[i] - cum[i-1])
            lon = waypoints[i-1][0] + (waypoints[i][0] - waypoints[i-1][0]) * frac
            lat = waypoints[i-1][1] + (waypoints[i][1] - waypoints[i-1][1]) * frac
            print(f"FAULT GPS: {lat}, {lon}")
            print(f"Google Maps: https://www.google.com/maps?q={lat},{lon}")
            print(f"Distance: {fault_distance}m | Route: {cum[-1]:.0f}m")
            break
```

## References

- `zabbix-api-investigation` → `references/alm-fiber-monitoring.md` — SNMP fallback, syslog format, Zabbix event mapping
- `slack-incident` — incident channel creation and management