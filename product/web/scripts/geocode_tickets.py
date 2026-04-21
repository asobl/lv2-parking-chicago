"""
geocode_tickets.py — Convert FOIA LV2 ticket data to geocoded map points.

Reads the FOIA Excel file, groups tickets by address, applies Chicago
street grid math to approximate lat/lng, and outputs ticket-map-data.json.

Run from project root:
  python3 scripts/geocode_tickets.py

Output: data/ticket-map-data.json
"""

import openpyxl, re, json
from collections import Counter

# ---------- PATHS ----------
FOIA_PATH = os.environ.get('FOIA_PATH', '')
OUT_PATH  = "data/ticket-map-data.json"

# ---------- CHICAGO GRID MATH ----------
# Chicago address grid:
#   800 address units = 1 mile (N-S or E-W)
#   State St = 0 E/W  (longitude baseline)
#   Madison St = 0 N/S (latitude baseline)
LAT_MADISON  = 41.881890   # Madison St latitude
LNG_STATE    = -87.627960  # State St longitude
LAT_PER_100  = 0.001810    # degrees latitude per 100 address units N (calibrated to LV2 zone)
LNG_PER_100  = -0.002550   # degrees longitude per 100 address units W (calibrated to LV2 zone)

def addr_to_lat(north_num):
    return LAT_MADISON + (north_num / 100) * LAT_PER_100

def addr_to_lng(west_num):
    return LNG_STATE + (west_num / 100) * LNG_PER_100


# ---------- STREET LOOKUP TABLES ----------

# N-S streets: their W (or E) address number
# (i.e., how far west of State St they run)
NS_STREET_W = {
    # Streets west of Halsted (800 W), the LV2 area
    'RAVENSWOOD AVE': 1800, 'RAVENSWOOD': 1800,
    'HERMITAGE AVE':  1734, 'HERMITAGE':  1734,
    'WOLCOTT AVE':    1732, 'WOLCOTT':    1732,
    'PAULINA ST':     1700, 'PAULINA':    1700,
    'WOOD ST':        1700, 'WOOD':       1700,
    'MARSHFIELD AVE': 1634, 'MARSHFIELD': 1634,
    'HONORE ST':      1632, 'HONORE':     1632,
    'LEAVITT ST':     2200, 'LEAVITT':    2200,
    'OAKLEY AVE':     2300, 'OAKLEY':     2300,
    'ASHLAND AVE':    1600, 'ASHLAND':    1600,
    'SOUTHPORT AVE':  1400, 'SOUTHPORT':  1400,
    'GREENVIEW AVE':  1500, 'GREENVIEW':  1500,
    # Streets east of Halsted
    'HALSTED ST':      800, 'HALSTED':     800,
    'RACINE AVE':     1200, 'RACINE':     1200,
    'SEMINARY AVE':   1134, 'SEMINARY':   1134,
    'MAGNOLIA AVE':   1134, 'MAGNOLIA':   1134,
    'WAYNE AVE':      1232, 'WAYNE':      1232,
    'KENMORE AVE':    1040, 'KENMORE':    1040,
    'SHEFFIELD AVE':  1000, 'SHEFFIELD':  1000,
    'CLIFTON AVE':     840, 'CLIFTON':     840,
    # CLARK ST and LINCOLN AVE omitted -- both diagonal, grid formula places dots ~0.75mi off
    # Additional streets that may appear in data
    'HAMILTON AVE':   2100, 'HAMILTON':   2100,
    'DAMEN AVE':      2000, 'DAMEN':      2000,
    'SEELEY AVE':     2132, 'SEELEY':     2132,
    'BELL AVE':       2232, 'BELL':       2232,
    'CLAREMONT AVE':  2332, 'CLAREMONT':  2332,
}

# E-W streets: their N (or S) address number
EW_STREET_N = {
    # Streets in the LV2 area (3200–5000 N)
    'BELMONT AVE':     3200, 'BELMONT':     3200,
    'SCHOOL ST':       3300, 'SCHOOL':      3300,
    'ROSCOE ST':       3400, 'ROSCOE':      3400,
    'HENDERSON ST':    3458, 'HENDERSON':   3458,
    'NEWPORT AVE':     3542, 'NEWPORT':     3542,
    'BROMPTON AVE':    3554, 'BROMPTON':    3554,
    'EDDY ST':         3525, 'EDDY':        3525,
    'ADDISON ST':      3600, 'ADDISON':     3600,
    'CORNELIA AVE':    3500, 'CORNELIA':    3500,
    'WAVELAND AVE':    3632, 'WAVELAND':    3632,
    'GRACE ST':        3800, 'GRACE':       3800,
    'BYRON ST':        3500, 'BYRON':       3500,
    'BERTEAU AVE':     3700, 'BERTEAU':     3700,
    'BELLE PLAINE AVE':3800, 'BELLE PLAINE':3800,
    'IRVING PARK RD':  4000, 'IRVING PARK': 4000,
    'CUYLER AVE':      4700, 'CUYLER':      4700,
    'PENSACOLA AVE':   4580, 'PENSACOLA':   4580,
    'CULLOM AVE':      4458, 'CULLOM':      4458,
    'MONTROSE AVE':    4400, 'MONTROSE':    4400,
    'HUTCHINSON ST':   4234, 'HUTCHINSON':  4234,
    'SUNNYSIDE AVE':   4500, 'SUNNYSIDE':   4500,
    'WARNER AVE':      4658, 'WARNER':      4658,
    'WILSON AVE':      4600, 'WILSON':      4600,
    'AINSLIE ST':      4900, 'AINSLIE':     4900,
    'LELAND AVE':      4700, 'LELAND':      4700,
    'PATTERSON AVE':   3942, 'PATTERSON':   3942,
    'DAKIN ST':        3464, 'DAKIN':       3464,
    'MELROSE ST':      3358, 'MELROSE':     3358,
    'ALDINE AVE':      3244, 'ALDINE':      3244,
}


# ---------- PARSE ADDRESS ----------

def parse_address(raw):
    """
    Parse a Chicago address like '3406 N MARSHFIELD AVE' or '1616 W ROSCOE ST'.
    Returns (lat, lng) or None if the street is not in our lookup.
    """
    m = re.match(r'^(\d+)\s+([NSEW])\s+(.+)$', raw.strip().upper())
    if not m:
        return None
    num    = int(m.group(1))
    dirn   = m.group(2)
    street = m.group(3).strip()

    # LV2 zone bounds: Belmont (3200N) to Irving Park (4000N), Broadway to Ashland
    # Allow small buffer: ~3100N–4100N in lat, ~700W–2400W in lng
    LAT_MIN = addr_to_lat(3100)   # 41.9381
    LAT_MAX = addr_to_lat(4100)   # 41.9562
    LNG_MIN = addr_to_lng(2400)   # westernmost
    LNG_MAX = addr_to_lng(700)    # easternmost

    if dirn == 'N':
        lat = addr_to_lat(num)
        if not (LAT_MIN <= lat <= LAT_MAX):
            return None
        w_addr = NS_STREET_W.get(street)
        if w_addr is None:
            return None
        lng = addr_to_lng(w_addr)
        return (lat, lng)

    elif dirn == 'W':
        lng = addr_to_lng(num)
        if not (LNG_MAX >= lng >= LNG_MIN):
            return None
        n_addr = EW_STREET_N.get(street)
        if n_addr is None:
            return None
        lat = addr_to_lat(n_addr)
        if not (LAT_MIN <= lat <= LAT_MAX):
            return None
        return (lat, lng)

    # S and E addresses are outside our zone — ignore
    return None


# ---------- MAIN ----------

def main():
    print("Reading FOIA data...")
    wb = openpyxl.load_workbook(FOIA_PATH, read_only=True)
    ws = wb.active
    raw_counts = Counter()
    for row in ws.iter_rows(min_row=2, values_only=True):
        loc = row[5]
        if loc:
            raw_counts[str(loc).strip().upper()] += 1
    wb.close()
    print(f"  {sum(raw_counts.values())} tickets across {len(raw_counts)} unique addresses")

    # Geocode each unique address
    points = []
    skipped = 0
    for addr, count in raw_counts.items():
        coords = parse_address(addr)
        if coords:
            lat, lng = coords
            points.append({
                "lat":   round(lat, 6),
                "lng":   round(lng, 6),
                "count": count,
                "addr":  addr.title()
            })
        else:
            skipped += 1

    # Sort descending by count
    points.sort(key=lambda x: -x["count"])
    total_mapped = sum(p["count"] for p in points)
    total_all    = sum(raw_counts.values())

    print(f"  Geocoded: {len(points)} addresses ({total_mapped} tickets = {total_mapped/total_all*100:.1f}% of all tickets)")
    print(f"  Skipped:  {skipped} addresses")

    # Write output
    out = {
        "total_tickets":  total_all,
        "mapped_tickets": total_mapped,
        "points":         points,
        "color_scale": {
            "red":    {"min": 15, "color": "#e84040", "label": "15+ tickets"},
            "orange": {"min": 8,  "color": "#f0a030", "label": "8–14 tickets"},
            "yellow": {"min": 4,  "color": "#f5c020", "label": "4–7 tickets"},
            "dim":    {"min": 1,  "color": "#8898aa", "label": "1–3 tickets"},
        }
    }
    with open(OUT_PATH, "w") as f:
        json.dump(out, f, separators=(",", ":"))
    print(f"  Wrote {OUT_PATH} ({len(points)} points)")

    # Quick stats
    red_pts    = [p for p in points if p["count"] >= 15]
    orange_pts = [p for p in points if 8 <= p["count"] < 15]
    yellow_pts = [p for p in points if 4 <= p["count"] < 8]
    dim_pts    = [p for p in points if p["count"] < 4]
    print(f"\nColor breakdown:")
    print(f"  Red (15+):    {len(red_pts):4d} addresses — top 3: {[p['addr'] for p in red_pts[:3]]}")
    print(f"  Orange (8-14):{len(orange_pts):4d} addresses")
    print(f"  Yellow (4-7): {len(yellow_pts):4d} addresses")
    print(f"  Dim (1-3):    {len(dim_pts):4d} addresses")

if __name__ == "__main__":
    main()
