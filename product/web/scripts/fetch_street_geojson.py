"""
fetch_street_geojson.py -- Fetch actual OSM street geometries via Overpass API.

Queries streets one at a time (to avoid timeouts) and saves as GeoJSON.
Run from project root:
  python3 scripts/fetch_street_geojson.py

Output: internal/zone-streets.geojson
"""

import json, time, urllib.request, urllib.parse, ssl

OVERPASS_URL = "https://overpass-api.de/api/interpreter"
OUT_PATH = "internal/zone-streets.geojson"

# Bounding box: Belmont to Wilson, Broadway to Oakley (with buffer)
BBOX = "41.938,  -87.690, 41.968, -87.638"
# south, west, north, east
S, W, N, E = 41.938, -87.690, 41.968, -87.638

# Streets to fetch with their display metadata
# Format: (osm_name, display_label, color, layer)
STREETS = [
    # E-W streets (horizontal)
    ("West Belmont Avenue",      "BELMONT",      "#FF6B35", "ew"),
    ("West School Street",       "SCHOOL",       "#FF6B35", "ew"),
    ("West Melrose Street",      "MELROSE",      "#888",    "ew"),
    ("West Roscoe Street",       "ROSCOE",       "#FF6B35", "ew"),
    ("West Henderson Street",    "HENDERSON",    "#888",    "ew"),
    ("West Dakin Street",        "DAKIN",        "#888",    "ew"),
    ("West Newport Avenue",      "NEWPORT",      "#888",    "ew"),
    ("West Brompton Avenue",     "BROMPTON",     "#888",    "ew"),
    ("West Cornelia Avenue",     "CORNELIA",     "#888",    "ew"),
    ("West Eddy Street",         "EDDY",         "#888",    "ew"),
    ("West Addison Street",      "ADDISON",      "#FF6B35", "ew"),
    ("West Waveland Avenue",     "WAVELAND",     "#888",    "ew"),
    ("West Berteau Avenue",      "BERTEAU",      "#888",    "ew"),
    ("West Grace Street",        "GRACE",        "#888",    "ew"),
    ("West Belle Plaine Avenue", "BELLE PLAINE", "#888",    "ew"),
    ("West Patterson Avenue",    "PATTERSON",    "#888",    "ew"),
    ("West Irving Park Road",    "IRVING PARK",  "#FF6B35", "ew"),
    ("West Cuyler Avenue",       "CUYLER",       "#888",    "ew"),
    ("West Warner Avenue",       "WARNER",       "#888",    "ew"),
    ("West Hutchinson Street",   "HUTCHINSON",   "#888",    "ew"),
    ("West Cullom Avenue",       "CULLOM",       "#888",    "ew"),
    ("West Pensacola Avenue",    "PENSACOLA",    "#888",    "ew"),
    ("West Montrose Avenue",     "MONTROSE",     "#FF6B35", "ew"),
    ("West Sunnyside Avenue",    "SUNNYSIDE",    "#888",    "ew"),
    ("West Wilson Avenue",       "WILSON",       "#FF6B35", "ew"),
    # N-S streets (vertical)
    ("North Halsted Street",     "HALSTED",      "#4a90d9", "ns"),
    ("North Clifton Avenue",     "CLIFTON",      "#888",    "ns"),
    ("North Sheffield Avenue",   "SHEFFIELD",    "#4a90d9", "ns"),
    ("North Kenmore Avenue",     "KENMORE",      "#888",    "ns"),
    ("North Seminary Avenue",    "SEMINARY",     "#888",    "ns"),
    ("North Racine Avenue",      "RACINE",       "#4a90d9", "ns"),
    ("North Wayne Avenue",       "WAYNE",        "#888",    "ns"),
    ("North Southport Avenue",   "SOUTHPORT",    "#4a90d9", "ns"),
    ("North Greenview Avenue",   "GREENVIEW",    "#888",    "ns"),
    ("North Ashland Avenue",     "ASHLAND",      "#4a90d9", "ns"),
    ("North Marshfield Avenue",  "MARSHFIELD",   "#888",    "ns"),
    ("North Honore Street",      "HONORE",       "#888",    "ns"),
    ("North Paulina Street",     "PAULINA",      "#888",    "ns"),
    ("North Wood Street",        "WOOD",         "#888",    "ns"),
    ("North Hermitage Avenue",   "HERMITAGE",    "#888",    "ns"),
    ("North Wolcott Avenue",     "WOLCOTT",      "#888",    "ns"),
    ("North Damen Avenue",       "DAMEN",        "#888",    "ns"),
    ("North Leavitt Street",     "LEAVITT",      "#888",    "ns"),
    ("North Oakley Avenue",      "OAKLEY",       "#888",    "ns"),
    # Diagonals
    ("North Broadway",           "BROADWAY",     "#e83",    "diag"),
    ("North Clark Street",       "CLARK",        "#e83",    "diag"),
    ("North Lincoln Avenue",     "LINCOLN",      "#e83",    "diag"),
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def fetch_street(osm_name):
    """Fetch all way segments for a street within the bounding box."""
    query = f"""[out:json][timeout:30];
way["name"="{osm_name}"]({S},{W},{N},{E});
out geom;"""
    data = urllib.parse.urlencode({"data": query}).encode()
    req = urllib.request.Request(OVERPASS_URL, data=data,
                                 headers={"User-Agent": "lv2park-zone-map/1.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=35) as resp:
        return json.loads(resp.read())


def ways_to_geojson_features(osm_result, label, color, layer):
    """Convert Overpass way results to GeoJSON LineString features."""
    features = []
    for elem in osm_result.get("elements", []):
        if elem["type"] != "way" or "geometry" not in elem:
            continue
        coords = [[pt["lon"], pt["lat"]] for pt in elem["geometry"]]
        if len(coords) < 2:
            continue
        features.append({
            "type": "Feature",
            "properties": {
                "name": label,
                "color": color,
                "layer": layer,
                "osm_id": elem["id"]
            },
            "geometry": {
                "type": "LineString",
                "coordinates": coords
            }
        })
    return features


def main():
    all_features = []
    failed = []

    for i, (osm_name, label, color, layer) in enumerate(STREETS):
        print(f"  [{i+1:2d}/{len(STREETS)}] {osm_name}...", end=" ", flush=True)
        try:
            result = fetch_street(osm_name)
            feats = ways_to_geojson_features(result, label, color, layer)
            all_features.extend(feats)
            n_ways = len(result.get("elements", []))
            print(f"OK ({n_ways} ways, {len(feats)} segments)")
        except Exception as ex:
            print(f"FAILED: {ex}")
            failed.append(osm_name)

        # Polite delay between requests (Overpass policy: 1 req/sec)
        if i < len(STREETS) - 1:
            time.sleep(1.5)

    geojson = {
        "type": "FeatureCollection",
        "features": all_features
    }

    with open(OUT_PATH, "w") as f:
        json.dump(geojson, f, separators=(",", ":"))

    print(f"\nWrote {OUT_PATH}")
    print(f"  {len(all_features)} total segments from {len(STREETS) - len(failed)} streets")
    if failed:
        print(f"  FAILED ({len(failed)}): {', '.join(failed)}")
        print("  Re-run to retry failed streets (they'll be fetched again).")


if __name__ == "__main__":
    main()
