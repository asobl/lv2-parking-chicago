"""
fetch_street_geojson_retry.py -- Retry fetching missing OSM streets.

Loads existing internal/zone-streets.geojson, identifies which streets are
missing, and re-fetches them using kumi.systems mirror with longer delays.

Run from project root:
  python3 scripts/fetch_street_geojson_retry.py
"""

import json, time, urllib.request, urllib.parse, ssl, random

# Mirror servers to rotate through
MIRRORS = [
    "https://overpass.kumi.systems/api/interpreter",
    "https://overpass-api.de/api/interpreter",
]

GEOJSON_PATH = "internal/zone-streets.geojson"

S, W, N, E = 41.938, -87.690, 41.968, -87.638

STREETS = [
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
    ("North Broadway",           "BROADWAY",     "#e83",    "diag"),
    ("North Clark Street",       "CLARK",        "#e83",    "diag"),
    ("North Lincoln Avenue",     "LINCOLN",      "#e83",    "diag"),
]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE


def fetch_street(osm_name, server):
    query = f"""[out:json][timeout:30];
way["name"="{osm_name}"]({S},{W},{N},{E});
out geom;"""
    data = urllib.parse.urlencode({"data": query}).encode()
    req = urllib.request.Request(server, data=data,
                                 headers={"User-Agent": "lv2park-zone-map/1.0"})
    with urllib.request.urlopen(req, context=ctx, timeout=35) as resp:
        return json.loads(resp.read())


def ways_to_features(osm_result, label, color, layer):
    features = []
    for elem in osm_result.get("elements", []):
        if elem["type"] != "way" or "geometry" not in elem:
            continue
        coords = [[pt["lon"], pt["lat"]] for pt in elem["geometry"]]
        if len(coords) < 2:
            continue
        features.append({
            "type": "Feature",
            "properties": {"name": label, "color": color, "layer": layer, "osm_id": elem["id"]},
            "geometry": {"type": "LineString", "coordinates": coords}
        })
    return features


def main():
    # Load existing GeoJSON
    try:
        with open(GEOJSON_PATH) as f:
            existing = json.load(f)
        all_features = existing.get("features", [])
        already_have = set(f["properties"]["name"] for f in all_features)
        print(f"Loaded {len(all_features)} existing segments covering: {', '.join(sorted(already_have))}")
    except FileNotFoundError:
        all_features = []
        already_have = set()
        print("No existing file, starting fresh.")

    # Find streets to fetch
    to_fetch = [(osm_name, label, color, layer)
                for osm_name, label, color, layer in STREETS
                if label not in already_have]
    print(f"Need to fetch {len(to_fetch)} streets.")

    failed = []
    mirror_idx = 0

    for i, (osm_name, label, color, layer) in enumerate(to_fetch):
        server = MIRRORS[mirror_idx % len(MIRRORS)]
        print(f"  [{i+1:2d}/{len(to_fetch)}] {osm_name} via {server.split('/')[2]}...", end=" ", flush=True)

        success = False
        for attempt in range(3):
            try:
                result = fetch_street(osm_name, server)
                feats = ways_to_features(result, label, color, layer)
                all_features.extend(feats)
                n_ways = len(result.get("elements", []))
                print(f"OK ({n_ways} ways, {len(feats)} segments)")
                success = True
                break
            except Exception as ex:
                code = str(ex)
                if "429" in code or "Too Many" in code:
                    wait = 10 + attempt * 5
                    print(f"\n    429 rate limit, waiting {wait}s...", end=" ", flush=True)
                    time.sleep(wait)
                    mirror_idx += 1  # switch mirror
                elif "504" in code or "Timeout" in code or "timeout" in code:
                    wait = 5
                    print(f"\n    504 timeout, retry {attempt+1}/3 in {wait}s...", end=" ", flush=True)
                    time.sleep(wait)
                else:
                    print(f"\n    Error: {ex}")
                    break

        if not success:
            print(f"FAILED after 3 attempts")
            failed.append(osm_name)

        # Save progress after every street
        geojson = {"type": "FeatureCollection", "features": all_features}
        with open(GEOJSON_PATH, "w") as f:
            json.dump(geojson, f, separators=(",", ":"))

        # Delay between requests
        if i < len(to_fetch) - 1:
            delay = 4 + random.random() * 2
            time.sleep(delay)
        mirror_idx += 1  # rotate mirrors

    already_have2 = set(f["properties"]["name"] for f in all_features)
    print(f"\nDone. {len(all_features)} total segments, {len(already_have2)} streets covered.")
    if failed:
        print(f"Still failed ({len(failed)}): {', '.join(failed)}")
        print("Run again to retry.")
    else:
        print("All streets fetched successfully!")


if __name__ == "__main__":
    main()
