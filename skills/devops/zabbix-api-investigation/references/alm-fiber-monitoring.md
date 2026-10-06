# ALM (Active Line Monitoring) — Optical Fiber Probe

## Device
- **Vendor:** Adtran / ADVA FSP 3000
- **Host in Zabbix:** `Cyberjaya ALM (10.10.10.3)`
- **Location:** CoPlace 2, 2300 Jalan Perdana, Cyberjaya
- **Coordinates:** 2.925867, 101.662949 (stored in Zabbix host inventory `location_lat` / `location_lon`)
- **Site notes:** "Adtran ALM Fiber Monitoring Probe"

## Syslog source
- **Item key:** `log[/var/log/alm-optical.log]`
- **Collector host:** `ubuntu-rm1dev` (has live syslog)
- **Item name:** "ALM Optical Syslog Ingestion"

## Syslog message format
```
2026-09-13T07:41:10.006449+00:00 ALM almlogger[1690]: Port 6 Operational State changed from "abnormal" to "unavailable"
```

Key fields in each line:
- ISO timestamp
- Source "ALM"
- Process `almlogger[PID]`
- Port number (1–16 typically)
- Message type: `Operational State`, `Admin State`, or `Alarm`

## Known syslog message types

### State transitions
- `Port N Operational State changed from "X" to "Y"` — fiber link state
- `Port N Admin State changed from "X" to "Y"` — administrative control

### Alarm events
- `Port N Alarm: "Fingerprint Missing"` — optical signature not detected (primary fault signal)
- `Port N Alarm: "Fingerprint Missing" has been cleared` — fault cleared
- `Port N Alarm: OOS Disabled` — port taken out of service
- `Port N Alarm: "Link Not Monitored"` — monitoring suspended
- `Port N Alarm: "Link Not Monitored" has been cleared`

### State values seen
- **Operational:** `normal`, `abnormal`, `unavailable`
- **Admin:** `In Service`, `Disabled`

## Zabbix event naming conventions
- `ALM: Port N Monitoring Inactive` — trigger fires when fingerprint is missing
- Opdata: `Port N (MCH-1-N) is Inactive / Missing Fingerprint`
- Tags: `port: Port N`, `domain: optical-monitoring`
- Security: `🔒 [SECURITY] ALM: Unauthorized Access / Authentication Failure in Syslog` — auth failures on the ALM device itself

## Investigation workflow
1. Query `event.get {search: {name: "ALM"}}` for recent events
2. Get the host inventory for lat/long via `host.get {name search, selectInventory}`
3. Pull syslog history via `history.get {itemids, history=2, time_from}` on the syslog collector item
4. Filter entries by port number in Python
5. Acknowledge with notes via `event.acknowledge {eventids, action: 4, message}`

## REST API — Auto FA Data + KML Route Retrieval

The ALM device exposes a REST API with HTTP Basic Auth (credentials `admin:chgme.1a`).

### Auto FA Data

```bash
curl -sk -u 'admin:chgme.1a' 'https://10.10.10.3/trace/<PORT>/af/list'
```

Returns JSON with `data[0]` being the most recent FA entry. Key fields:
- `faultpos` — distance in meters (string; `null` = no fault, `"0.0"` = at ALM itself)
- `port_string` — e.g. `"MCH-1-1"` — **required for the route endpoint** (see below)
- `fault_latitude` / `fault_longitude` — pre-computed GPS if route is mapped and device calculated it
- `fptype` — e.g. `"P2P w/o Refl."` (Point-to-Point without Reflection)

### KML Route (critical: use port_string, not numeric port)

The route endpoint **requires the full port string** (e.g. `MCH-1-1`) from the FA data's `port_string` field, NOT the numeric port number:

```bash
# ✓ WORKS — returns KML with coordinates
curl -sk -u 'admin:chgme.1a' 'https://10.10.10.3/trace/route/MCH-1-1'

# ✗ FAILS — returns {"status":"Not Found"} even when route exists
curl -sk -u 'admin:chgme.1a' 'https://10.10.10.3/trace/route/1'
```

**Response format tells you the problem:**
- JSON `{"status":"Not Found"}` = wrong endpoint path / identifier. Retry with `port_string`
- Empty body or HTML 404 page = route genuinely does not exist for this port
- Valid KML = `<kml><Document><Placemark><LineString><coordinates>lon,lat,0  lon,lat,0...</coordinates>`

Save the KML for records:
```bash
curl -sk -u 'admin:chgme.1a' 'https://10.10.10.3/trace/route/MCH-1-1' \
  -o /home/ubuntu/port<N>_route.kml
```

### GPS Triangulation from KML

Once you have the KML waypoints and the fault distance, interpolate along the route:

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

Usage:
```python
fault_lat, fault_lon = triangulate_fault(waypoints, 515.1)
gmaps_url = f"https://www.google.com/maps?q={fault_lat},{fault_lon}"
```

### REST-to-SNMP cross-verification

When the REST route endpoint returns `{"status":"Not Found"}` and you've already tried the port_string, verify via SNMP whether the route actually exists before reporting "no route":

- `1.3.6.1.4.1.2544.1.14.2.2.1.9.<port>` → `2` means route IS configured (`1` = no route)
- `1.3.6.1.4.1.2544.1.14.5.1.1.0` → route ID string (e.g. `60101_202311141349`)

If SNMP shows `portGisConfigured=2` but REST still can't return the KML, the REST path is wrong (try different path prefix like `/kml/` or the route ID directly) — the data exists on device.

Also cross-verify fault distance via SNMP:
- `1.3.6.1.4.1.2544.1.14.3.11.1.4.1.<port>` → INTEGER × 0.1 m (5151 = 515.1 m; -1 = no fault)
- `1.3.6.1.4.1.2544.1.14.3.11.1.3.1.<port>` → INTEGER × 0.1 dB (1000 = 100 dB = full break)

### Multi-step fallback order
1. REST Auto FA → extract `port_string` + `faultpos`
2. REST KML route using `port_string` → if `{"status":"Not Found"}`, try numeric port
3. SNMP `portGisConfigured` → if `2`, route EXISTS but REST path is wrong — investigate
4. If no route at all → report ALM unit GPS + distance as search radius

## Direct SNMP fault analysis (when REST API creds are unknown)
SNMPv2c with community `public` (or `private`) works and exposes the same Auto Fault Analysis table that Zabbix mirrors — use it to read fault data directly without REST credentials.

### Auto FA table OIDs (index suffix = port number, e.g. `...1.1` = port 1)
| OID (suffix `.1.<port>`) | Field | Notes |
|---|---|---|
| `1.3.6.1.4.1.2544.1.14.3.11.1.2` | Ref ID | INTEGER |
| `1.3.6.1.4.1.2544.1.14.3.11.1.3` | Link Loss | INTEGER, ×0.1 dB (1000 = 100 dB = full break) |
| `1.3.6.1.4.1.2544.1.14.3.11.1.4` | Fault Position | INTEGER, ×0.1 m (5151 = 515.1 m; -1 = no fault) |
| `1.3.6.1.4.1.2544.1.14.3.11.1.6` | Timestamp | Hex-STRING DateAndTime (`07 EA 09 0E...` = year 0x07EA) |
| `1.3.6.1.4.1.2544.1.14.3.11.1.8` | Fault Lat | DisplayString — **empty `""` when unmapped** |
| `1.3.6.1.4.1.2544.1.14.3.11.1.9` | Fault Lon | DisplayString — **empty `""` when unmapped** |

Walk commands:
```bash
snmpwalk -v2c -c public -t 3 10.10.10.3 1.3.6.1.4.1.2544.1.14.3.11 | head -30
# Key rows are the .1.2/.1.3/.1.4/.1.6/.1.8/.1.9 columns at index ...1.<port>
snmpget -v2c -c public 10.10.10.3 1.3.6.1.4.1.2544.1.14.3.11.1.4.1.1   # fault pos port 1
```

### GIS route mapping checks
- `portGisConfigured`: `1.3.6.1.4.1.2544.1.14.2.2.1.9.<port>` → `1=no` (no route), `2=yes` (route present)
- Route table: `1.3.6.1.4.1.2544.1.14.5.1.1.0` → route ID string (e.g. `60101_202311141349`)
- Even with `portGisConfigured=yes`, fault lat/lon can still be `""` — the route must also have coordinates mapped.
- Port-level setting is per-port: port 1 may be `2 (yes)` while port 2 is `1 (no)`; always check the specific port.

### GPS answer when unmapped
If fault lat/lon OIDs are empty, the honest answer is: **GPS not mapped — fault is distance-only** (e.g. "fiber break at 515.1 m from ALM unit"). Provide:
1. The ALM unit's own coordinates (from Zabbix inventory: lat 2.925867, lon 101.662949, CoPlace 2 Cyberjaya), and
2. The fiber distance from there (515.1 m) as the search radius.

Exact fault GPS requires GIS route coordinates configured on the ALM unit or a physical duct survey at that distance. Do NOT fabricate coordinates by dead-reckoning a bearing — the route's geometry is not exposed via SNMP.