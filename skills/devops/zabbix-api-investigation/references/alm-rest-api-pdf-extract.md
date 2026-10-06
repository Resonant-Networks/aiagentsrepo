# Adtran ALM Programming Guide — Chapter 4: REST Interface (Extract)

Source: Adtran ALM R7.1 Programming Guide (Issue A), Chapter 4 "REST Interface"
PDF file: "ALM REST API.pdf" (available in Slack #alm-rest-api-docs)

## Architecture

The REST interface is **GET-only (read-only)**. All endpoints retrieve existing data from
the ALM unit. There are **no POST/PUT/PATCH/DELETE endpoints** to trigger actions, start
measurements, or modify configuration. This is a fundamental device constraint.

Authentication: HTTP Basic Auth (credentials: admin/chgme.1a). Self-signed HTTPS certs accepted.

## Endpoint Reference

### Retrieving Latest Traces

| Resource | Endpoint | Returns |
|---|---|---|
| Latest Fingerprint | `GET /trace/<port>/fp/<type>` | CSV (2 traces) or SOR (1 trace) |
| Latest Manual FA | `GET /trace/<port>/fa/<type>` | CSV (4 traces) or SOR |
| Latest Auto FA | `GET /trace/<port>/af/<type>` | CSV (4 traces) or SOR |
| Latest Manual OTDR | `GET /trace/<port>/om/<type>` | CSV or SOR |

`<type>` values:
- `f` — filtered, CSV (default)
- `r` — raw, CSV
- `d` — debug, CSV
- `sf1` — filtered, small pulse, SOR
- `sf2` — filtered, big pulse, SOR (fp/fa/af only)
- `sr1` — raw, small pulse, SOR
- `sr2` — raw, big pulse, SOR (fp/fa/af only)

### Listing Available Traces

| Resource | Endpoint | Response Format |
|---|---|---|
| Fingerprints | `GET /trace/<port>/fp/list` | JSON (id, port, type, pulsewidth, timestamp, remark) |
| Manual FA | `GET /trace/<port>/fa/list` | JSON (faultpos, faultposcorrected, lat, lon, deprecated) |
| Auto FA | `GET /trace/<port>/af/list` | JSON (faultpos, faultposcorrected, lat, lon, deprecated) |
| Manual OTDR | `GET /trace/<port>/om/list` | JSON (fiberlength, faultpos, laserpower, pulsewidth, meastime) |

### Full Trace Data (no type suffix)

`GET /trace/<port>/af` returns TSV with metadata headers and per-event details:

```
FP_EVENT_1:  0.0    -62.7  1.2     ""
FP_EVENT_2:  7.3    -56.6  n.c.    ""
FP_EVENT_3:  516.8  -45.0  1.0     ""
FA_EVENT_1:  0.0    -55.4  >12.4
```

Event format: `<name>: <distance> <loss> <reflection_type> "<remark>"`
- FP events = fingerprint trace events (baseline)
- FA events = fault analysis trace events (difference from baseline)
- n.c. = not calculated; > = loss exceeds range

This is richer than the JSON `af/list` summary — the JSON may show `faultpos: "0.0"` (no
fault flagged) while the full trace still contains fiber events at non-zero distances.

### Route Endpoints

| Endpoint | Returns |
|---|---|
| `GET /trace/route/<port>` | KML file with `<coordinates>lon,lat,0 lon,lat,0...</coordinates>` |
| `GET /trace/route/list` | JSON list (port, route_length, type, name, remark) |

## Key Learnings

1. **No write endpoints exist** — the REST interface cannot trigger manual OTDR
   measurements. Must use ALM WebGUI (https://10.10.10.3/alm.php5) for that.
2. **`faultpos: "0.0"` vs events** — the JSON summary may say 0.0 (no fault) while
   the full trace TSV shows fiber events. Always fetch the full trace for verification.
3. **Manual OTDR measurements** — listed via `/trace/<port>/om/list`. If an engineer ran
   one via WebGUI, it appears here. Retrieve via `/trace/<port>/om/f`.
4. **Documentation-first approach** — before probing for unknown API endpoints, consult
   the vendor programming guide PDF. It documents all available endpoints.
