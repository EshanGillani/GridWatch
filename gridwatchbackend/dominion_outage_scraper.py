#!/usr/bin/env python3
"""
Dominion Energy Real-Time Outage Scraper
=========================================
Fetches live outage data from KUBRA StormCenter including location coordinates.
Outputs to console, CSV, JSON, and an interactive HTML map.

Usage:
    py dominion_outage_scraper.py                        # run once, console output
    py dominion_outage_scraper.py --loop 60              # poll every 60 seconds
    py dominion_outage_scraper.py --csv outages.csv      # save to CSV
    py dominion_outage_scraper.py --map outages_map.html # save interactive map
    py dominion_outage_scraper.py --loop 300 --csv outages.csv --map map.html
"""

import argparse
import csv
import json
import math
import sys
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import datetime, timezone
from pathlib import Path

import requests

# Base directory = folder where this script lives
SCRIPT_DIR = Path(__file__).parent.resolve()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

KUBRA_CURRENT_STATE_URL = (
    "https://kubra.io/stormcenter/api/v1/stormcenters/"
    "9c691bb6-767e-4532-b00e-286ac9adc223/views/"
    "38b5394c-8bca-4dfd-ac59-b321615446bd/currentState?preview=false"
)
KUBRA_DATA_BASE = "https://kubra.io"

# All zoom-7 quadkeys covering Dominion Energy's VA/NC service territory
# (lat 36-40, lon -84 to -75)
TERRITORY_TILES = [
    '0320010', '0320011', '0320012', '0320013',
    '0320030', '0320031', '0320100', '0320101',
    '0320102', '0320103', '0320120', '0320121',
]

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Chrome/122.0.0.0 Safari/537.36",
    "Accept": "application/json, */*",
    "Referer": "https://outagemap.dominionenergy.com/",
}
SESSION = requests.Session()
SESSION.headers.update(HEADERS)

# ---------------------------------------------------------------------------
# Geo helpers
# ---------------------------------------------------------------------------

def decode_polyline(encoded: str) -> list[tuple[float, float]]:
    """Decode a Google Encoded Polyline string into (lat, lng) pairs."""
    coords = []
    index, lat, lng = 0, 0, 0
    while index < len(encoded):
        for is_lng in [False, True]:
            shift, result = 0, 0
            while True:
                b = ord(encoded[index]) - 63
                index += 1
                result |= (b & 0x1f) << shift
                shift += 5
                if b < 0x20:
                    break
            val = ~(result >> 1) if (result & 1) else (result >> 1)
            if is_lng:
                lng += val
            else:
                lat += val
        coords.append((round(lat / 1e5, 6), round(lng / 1e5, 6)))
    return coords


def polygon_centroid(coords: list[tuple[float,float]]) -> tuple[float,float]:
    """Return the centroid of a polygon."""
    if not coords:
        return (0.0, 0.0)
    lat = sum(c[0] for c in coords) / len(coords)
    lng = sum(c[1] for c in coords) / len(coords)
    return (round(lat, 6), round(lng, 6))

# ---------------------------------------------------------------------------
# HTTP helpers
# ---------------------------------------------------------------------------

def fetch_json(url, timeout=15):
    try:
        r = SESSION.get(url, timeout=timeout)
        r.raise_for_status()
        return r.json()
    except requests.exceptions.HTTPError as e:
        if e.response.status_code != 404:
            print(f"  [WARN] {url} -> {e}", file=sys.stderr)
        return None
    except Exception as e:
        print(f"  [WARN] {url} -> {e}", file=sys.stderr)
        return None

# ---------------------------------------------------------------------------
# KUBRA data fetchers
# ---------------------------------------------------------------------------

def get_state():
    state = fetch_json(KUBRA_CURRENT_STATE_URL)
    if not state:
        return None, None
    try:
        data_prefix    = state["data"]["interval_generation_data"]
        cluster_prefix = state["data"]["cluster_interval_generation_data"]
        print(f"  [INFO] Data prefix   : {data_prefix}")
        return data_prefix, cluster_prefix
    except (KeyError, TypeError) as e:
        print(f"  [WARN] State parse error: {e}", file=sys.stderr)
        return None, None


def fetch_summary(data_prefix):
    for sub in ["summary-2", "summary-1", "summary-3"]:
        url  = f"{KUBRA_DATA_BASE}/{data_prefix}/public/{sub}/data.json"
        data = fetch_json(url)
        if not data:
            continue
        try:
            sfd         = data.get("summaryFileData") or data.get("file_data") or data
            totals_list = sfd.get("totals") or []
            totals      = totals_list[0] if totals_list else {}
            return {
                "report_date"     : sfd.get("date_generated", "Unknown"),
                "customers_out"   : (totals.get("total_cust_a") or {}).get("val", 0),
                "total_customers" : totals.get("total_cust_s", 0),
                "pct_out"         : (totals.get("total_percent_cust_a") or {}).get("val", 0),
                "total_outages"   : totals.get("total_outages", 0),
            }
        except Exception as e:
            print(f"  [WARN] Summary parse error: {e}", file=sys.stderr)
    return None


def fetch_tile(url):
    """Fetch one cluster tile; return list of outage event dicts with coordinates."""
    data = fetch_json(url)
    if not data:
        return []
    events = []
    try:
        items = data.get("file_data") or []
        if isinstance(items, dict):
            items = [items]
        for item in items:
            desc = item.get("desc") or {}
            if not desc or desc.get("cluster"):
                continue  # skip cluster aggregates

            # --- decode geometry ---
            geom       = item.get("geom") or {}
            point_enc  = (geom.get("p") or [""])[0]
            area_enc   = (geom.get("a") or [""])[0]

            point_coords = decode_polyline(point_enc) if point_enc else []
            area_coords  = decode_polyline(area_enc)  if area_enc  else []

            if point_coords:
                lat, lng = point_coords[0]
            elif area_coords:
                lat, lng = polygon_centroid(area_coords)
            else:
                lat, lng = None, None

            events.append({
                "outage_id"     : item.get("id", ""),
                "incident_id"   : desc.get("inc_id", ""),
                "customers_out" : (desc.get("cust_a") or {}).get("val", 0),
                "cause"         : (desc.get("cause") or {}).get("EN-US", "Unknown"),
                "crew_status"   : (desc.get("crew_status") or {}).get("EN-US", "Unknown"),
                "etr"           : desc.get("etr", ""),
                "etr_range"     : desc.get("etrRange", ""),
                "start_time"    : desc.get("start_time", ""),
                "lat"           : lat,
                "lng"           : lng,
                "area_polygon"  : area_coords,
            })
    except Exception as e:
        print(f"  [WARN] Tile parse error {url}: {e}", file=sys.stderr)
    return events


def fetch_all_outages(cluster_prefix):
    """Fetch all territory tiles in parallel and return outage events."""
    base = cluster_prefix.replace("{qkh}", "XXX")
    urls = []
    for tile in TERRITORY_TILES:
        qkh = tile[-1] + tile[-2] + tile[-3]  # reversed last 3 digits
        url = f"{KUBRA_DATA_BASE}/{base.replace('XXX', qkh)}/public/cluster-1/{tile}.json"
        urls.append(url)

    print(f"  [INFO] Scanning {len(urls)} territory tiles ...")
    all_events = []
    with ThreadPoolExecutor(max_workers=12) as ex:
        futures = {ex.submit(fetch_tile, url): url for url in urls}
        for future in as_completed(futures):
            all_events.extend(future.result())

    all_events.sort(key=lambda x: int(x["customers_out"] or 0), reverse=True)
    return all_events

# ---------------------------------------------------------------------------
# Map generation
# ---------------------------------------------------------------------------

def generate_map(events, summary, pulled_at, output_path, browser_refresh=60):
    """Generate a self-contained Leaflet HTML map of all outage events."""

    def severity_color(n):
        if n >= 500:  return "#d32f2f"
        if n >= 100:  return "#f57c00"
        if n >= 25:   return "#fbc02d"
        return "#388e3c"

    def severity_label(n):
        if n >= 500:  return "Critical (500+)"
        if n >= 100:  return "Major (100-499)"
        if n >= 25:   return "Moderate (25-99)"
        return "Minor (<25)"

    markers_js = []
    polygons_js = []

    for e in events:
        if e["lat"] is None:
            continue

        color  = severity_color(e["customers_out"])
        radius = max(8, min(40, int(e["customers_out"] ** 0.5) * 3))
        popup  = (
            f"<b>Outage #{e['incident_id']}</b><br>"
            f"<b>Customers Out:</b> {e['customers_out']:,}<br>"
            f"<b>Cause:</b> {e['cause']}<br>"
            f"<b>Crew Status:</b> {e['crew_status']}<br>"
            f"<b>ETR:</b> {e['etr_range'] or e['etr']}<br>"
            f"<b>Started:</b> {e['start_time'] or 'Unknown'}"
        )
        markers_js.append(
            f'L.circleMarker([{e["lat"]},{e["lng"]}], '
            f'{{radius:{radius},color:"{color}",fillColor:"{color}",'
            f'fillOpacity:0.7,weight:2}}).bindPopup("{popup}").addTo(map);'
        )

        # Draw affected area polygon if available
        if e["area_polygon"] and len(e["area_polygon"]) > 2:
            poly_coords = str([[c[0], c[1]] for c in e["area_polygon"]])
            polygons_js.append(
                f'L.polygon({poly_coords}, '
                f'{{color:"{color}",fillOpacity:0.15,weight:1}}).addTo(map);'
            )

    co = summary["customers_out"] if summary else "?"
    tc = summary["total_customers"] if summary else "?"
    pct = summary["pct_out"] if summary else "?"
    n_evt = summary["total_outages"] if summary else len(events)
    rdate = summary["report_date"] if summary else pulled_at

    html = f"""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8"/>
<meta http-equiv="refresh" content="{browser_refresh}"/>
<title>Dominion Energy Outages</title>
<meta name="viewport" content="width=device-width,initial-scale=1"/>
<link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css"/>
<script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
<style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif; background:#1a1a2e; color:#eee; }}
  #header {{ padding:12px 20px; background:#16213e; border-bottom:2px solid #0f3460; display:flex; align-items:center; gap:20px; flex-wrap:wrap; }}
  #header h1 {{ font-size:1.2rem; color:#e94560; }}
  .stat {{ background:#0f3460; border-radius:6px; padding:6px 14px; text-align:center; }}
  .stat .val {{ font-size:1.4rem; font-weight:700; color:#e94560; }}
  .stat .lbl {{ font-size:0.7rem; color:#aaa; text-transform:uppercase; letter-spacing:1px; }}
  #map {{ height: calc(100vh - 70px); }}
  #legend {{ position:absolute; bottom:30px; right:10px; z-index:1000; background:rgba(22,33,62,0.95);
             padding:12px; border-radius:8px; font-size:0.8rem; border:1px solid #0f3460; }}
  #legend h4 {{ margin-bottom:6px; color:#aaa; font-size:0.75rem; text-transform:uppercase; }}
  .leg-item {{ display:flex; align-items:center; gap:8px; margin:4px 0; }}
  .leg-dot {{ width:14px; height:14px; border-radius:50%; flex-shrink:0; }}
  #timestamp {{ font-size:0.7rem; color:#888; margin-left:auto; }}
</style>
</head>
<body>
<div id="header">
  <h1>⚡ Dominion Energy Live Outages</h1>
  <div class="stat"><div class="val">{co:,}</div><div class="lbl">Customers Out</div></div>
  <div class="stat"><div class="val">{n_evt}</div><div class="lbl">Active Outages</div></div>
  <div class="stat"><div class="val">{pct}%</div><div class="lbl">% Affected</div></div>
  <div class="stat"><div class="val">{tc:,}</div><div class="lbl">Total Customers</div></div>
  <div id="timestamp">Updated: {rdate}<br>Scraped: {pulled_at}</div>
</div>
<div id="map"></div>
<div id="legend">
  <h4>Severity</h4>
  <div class="leg-item"><div class="leg-dot" style="background:#d32f2f"></div>Critical (500+)</div>
  <div class="leg-item"><div class="leg-dot" style="background:#f57c00"></div>Major (100–499)</div>
  <div class="leg-item"><div class="leg-dot" style="background:#fbc02d"></div>Moderate (25–99)</div>
  <div class="leg-item"><div class="leg-dot" style="background:#388e3c"></div>Minor (&lt;25)</div>
  <div style="margin-top:8px;font-size:0.7rem;color:#888">Circle size = customers affected<br>Click outage for details</div>
</div>
<script>
var map = L.map('map').setView([37.5, -79.5], 7);
L.tileLayer('https://{{s}}.basemaps.cartocdn.com/dark_all/{{z}}/{{x}}/{{y}}{{r}}.png', {{
  attribution: '&copy; OpenStreetMap &copy; CARTO',
  maxZoom: 19
}}).addTo(map);
{''.join(polygons_js)}
{''.join(markers_js)}
</script>
</body>
</html>"""

    out = Path(output_path) if Path(output_path).is_absolute() else SCRIPT_DIR / output_path
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html, encoding="utf-8")
    print(f"  [MAP] Saved interactive map -> {output_path}")

# ---------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------

def collect_outage_data():
    pulled_at = datetime.now(timezone.utc).isoformat()
    print(f"\n{'='*60}")
    print(f"  Dominion Energy Outage Scraper  --  {pulled_at}")
    print(f"{'='*60}")
    result = {"pulled_at_utc": pulled_at, "summary": None, "outage_events": []}

    print("\n[1/3] Resolving live data paths ...")
    data_prefix, cluster_prefix = get_state()
    if not data_prefix:
        print("      [!] Could not resolve data prefix.")
        return result

    print("\n[2/3] Fetching outage summary ...")
    summary = fetch_summary(data_prefix)
    if summary:
        result["summary"] = summary
        co, tc = summary["customers_out"], summary["total_customers"]
        print(f"      Report date      : {summary['report_date']}")
        print(f"      Customers out    : {co:,}")
        print(f"      Total customers  : {tc:,}")
        print(f"      % affected       : {summary['pct_out']}%")
        print(f"      Active outages   : {summary['total_outages']}")

    print("\n[3/3] Fetching individual outage events + locations ...")
    events = fetch_all_outages(cluster_prefix)
    result["outage_events"] = events

    if events:
        located = sum(1 for e in events if e["lat"] is not None)
        total_cust = sum(int(e["customers_out"] or 0) for e in events)
        print(f"      {len(events)} events found  |  {located} with GPS  |  {total_cust:,} customers affected\n")
        fmt = "      {:<8} {:>9}  {:<24}  {:<20}  {}"
        print(fmt.format("INC_ID", "Cust.Out", "Cause", "Crew", "ETR"))
        print("      " + "-" * 85)
        for e in events:
            loc_str = f"({e['lat']},{e['lng']})" if e['lat'] else "no coords"
            print(fmt.format(
                str(e["incident_id"])[:8],
                str(e["customers_out"]),
                str(e["cause"])[:23],
                str(e["crew_status"])[:19],
                str(e["etr_range"] or e["etr"])[:35],
            ))
    else:
        print("      [!] No outage events found.")

    return result

# ---------------------------------------------------------------------------
# Output helpers
# ---------------------------------------------------------------------------

def append_csv(data, csv_path):
    rows = data.get("outage_events") or []
    if not rows:
        print("  [CSV] No rows to write.")
        return
    # Flatten — exclude area_polygon (too large for CSV)
    flat_rows = []
    for r in rows:
        flat = {k: v for k, v in r.items() if k != "area_polygon"}
        flat_rows.append(flat)
    path = Path(csv_path) if Path(csv_path).is_absolute() else SCRIPT_DIR / csv_path
    path.parent.mkdir(parents=True, exist_ok=True)
    write_header = not path.exists()
    
    with open(path, "a", newline="", encoding="utf-8") as f:
        fieldnames = ["pulled_at_utc"] + list(flat_rows[0].keys())
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        if write_header:
            writer.writeheader()
        for row in flat_rows:
            writer.writerow({"pulled_at_utc": data["pulled_at_utc"], **row})
    print(f"  [CSV] Appended {len(flat_rows)} rows -> {csv_path}")

# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Dominion Energy real-time outage scraper")
    parser.add_argument("--loop", type=int, metavar="SECONDS", default=0)
    parser.add_argument("--csv",  metavar="FILE", default="")
    parser.add_argument("--map",  metavar="FILE", default="outages_map.html",
                        help="Output HTML map file (default: outages_map.html)")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--refresh", type=int, metavar="SECONDS", default=60,
                        help="How often the browser auto-refreshes the map (default: 60)")
    parser.add_argument("--no-map", action="store_true", help="Skip map generation")
    args = parser.parse_args()

    try:
        while True:
            if args.json:
                sys.stdout = sys.stderr   # send debug prints to stderr so they don't corrupt JSON output
            data = collect_outage_data()
            if args.json:
                sys.stdout = sys.__stdout__  # restore stdout for JSON output
            if args.json:
                clean = json.loads(json.dumps(data, default=str))
                for e in clean.get("outage_events", []):
                    e.pop("area_polygon", None)
                output = {
                    "pulled_at_utc": clean["pulled_at_utc"],
                    "summary": clean.get("summary"),
                    "outages": [
                        {
                            "lat":         e["lat"],
                            "lng":         e["lng"],
                            "customers":   e["customers_out"],
                            "cause":       e["cause"],
                            "crew_status": e["crew_status"],
                            "etr":         e["etr_range"] or e["etr"],
                            "incident_id": e["incident_id"],
                            "provider":    "Dominion Energy",
                        }
                        for e in clean.get("outage_events", []) if e.get("lat")
                    ]
                }
                print(json.dumps(output, indent=2))
            if args.csv:
                append_csv(data, args.csv)
            if not args.no_map:
                generate_map(
                    data["outage_events"],
                    data["summary"],
                    data["pulled_at_utc"],
                    args.map,
                    browser_refresh=args.refresh,
                )
            if args.loop <= 0:
                break
            print(f"\n  Sleeping {args.loop}s ... (Ctrl-C to stop)\n")
            time.sleep(args.loop)
    except KeyboardInterrupt:
        print("\n\nStopped by user.")

if __name__ == "__main__":
    main()
