"""
Fetch real road geometry for LV2 hot streets from OpenStreetMap Overpass API.
Outputs data/lv2-streets.geojson — loaded by the map in app.js.

Run: python3 scripts/fetch_streets.py
"""

import json, urllib.request, urllib.parse, time, os, ssl

# macOS ships without default CA bundle for Python — skip verify for public OSM data
_ctx = ssl._create_unverified_context()

OVERPASS_URL = 'https://overpass.kumi.systems/api/interpreter'

# Bounding box covering the full LV2 zone (south, west, north, east)
BBOX = '41.9420,-87.6760,41.9545,-87.6540'

# Streets to fetch with their FOIA ticket counts
# OSM uses full directional names in Chicago
STREETS = [
    { 'osm_name': 'North Sheffield Avenue', 'display': 'Sheffield Ave', 'tickets': 2100 },
    { 'osm_name': 'North Clark Street',     'display': 'Clark St',      'tickets': 1800 },
    { 'osm_name': 'West Addison Street',    'display': 'Addison St',    'tickets': 1400 },
    { 'osm_name': 'West Waveland Avenue',   'display': 'Waveland Ave',  'tickets': 1200 },
    { 'osm_name': 'North Seminary Avenue',  'display': 'Seminary Ave',  'tickets':  900 },
    { 'osm_name': 'North Kenmore Avenue',   'display': 'Kenmore Ave',   'tickets':  700 },
    { 'osm_name': 'North Racine Avenue',    'display': 'Racine Ave',    'tickets':  600 },
    { 'osm_name': 'West Roscoe Street',     'display': 'Roscoe St',     'tickets':  500 },
    { 'osm_name': 'West Irving Park Road',  'display': 'Irving Park Rd','tickets':  400 },
]

def fetch_all_streets(names):
    """Fetch all streets in one Overpass query."""
    union = '\n'.join(f'  way["name"="{n}"]["highway"]({BBOX});' for n in names)
    query = f'[out:json][timeout:30];\n(\n{union}\n);\nout geom;\n'
    data = urllib.parse.urlencode({'data': query}).encode()
    req = urllib.request.Request(OVERPASS_URL, data=data,
                                  headers={'User-Agent': 'lv2park.com/1.0'})
    with urllib.request.urlopen(req, timeout=60, context=_ctx) as resp:
        return json.loads(resp.read())

def ways_to_linestrings(elements):
    """Convert OSM way elements to GeoJSON LineString coordinates."""
    lines = []
    for el in elements:
        if el.get('type') != 'way' or 'geometry' not in el:
            continue
        coords = [[pt['lon'], pt['lat']] for pt in el['geometry']]
        lines.append(coords)
    return lines

def merge_lines(lines):
    """Merge touching line segments into one continuous LineString."""
    if not lines:
        return []
    if len(lines) == 1:
        return lines[0]

    # Build a flat list, try to chain segments end-to-end
    result = list(lines[0])
    used = {0}
    for _ in range(len(lines)):
        best = None
        for i, seg in enumerate(lines):
            if i in used:
                continue
            if seg[0] == result[-1]:
                best = (i, seg, False)
                break
            if seg[-1] == result[-1]:
                best = (i, seg, True)
                break
        if best is None:
            break
        idx, seg, rev = best
        used.add(idx)
        result += (list(reversed(seg)) if rev else seg)[1:]

    return result

def main():
    # Build name -> street info lookup
    by_name = {s['osm_name']: s for s in STREETS}
    names = list(by_name.keys())

    print(f'Fetching {len(names)} streets in one query...', flush=True)
    try:
        result = fetch_all_streets(names)
    except Exception as e:
        print(f'Error: {e}')
        return

    # Group elements by their OSM name tag
    from collections import defaultdict
    by_osm_name = defaultdict(list)
    for el in result.get('elements', []):
        name = el.get('tags', {}).get('name', '')
        if name in by_name:
            by_osm_name[name].append(el)

    features = []
    for osm_name, s in by_name.items():
        elements = by_osm_name.get(osm_name, [])
        lines = ways_to_linestrings(elements)
        if not lines:
            print(f'  {s["display"]}: no results')
            continue
        coords = merge_lines(lines)
        features.append({
            'type': 'Feature',
            'properties': {
                'street': s['display'],
                'tickets': s['tickets']
            },
            'geometry': {
                'type': 'LineString',
                'coordinates': coords
            }
        })
        print(f'  {s["display"]}: ok ({len(coords)} nodes)')

    geojson = {'type': 'FeatureCollection', 'features': features}

    out_path = os.path.join(os.path.dirname(__file__), '..', 'data', 'lv2-streets.geojson')
    out_path = os.path.normpath(out_path)
    with open(out_path, 'w') as f:
        json.dump(geojson, f)
    print(f"\nWrote {len(features)} streets to {out_path}")

if __name__ == '__main__':
    main()
