"""
build_lv2_geojson.py -- Build LV2 zone street GeoJSON from OSM data.

Reads internal/zone-streets.geojson (717 OSM segments), filters to only
LV2 streets, clips to the LV2 North and LV2 West bounding boxes, and
outputs data/lv2-zone-streets.geojson.

Three streets missing from the OSM fetch (Byron, Wood, Ravenswood) are
added with manual coordinates from the verified 2013 map data.

Run from collected-ideas/lv2park/:
  python3 scripts/build_lv2_geojson.py
"""

import json
from pathlib import Path

INPUT_PATH = "internal/zone-streets.geojson"
OUTPUT_PATH = "data/lv2-zone-streets.geojson"

# LV2 North bounding box: Irving Park to Montrose, EAST of Ashland
# Per 2013 map, all north section streets are east of Ashland
LV2_NORTH = {
    "lat_min": 41.9549,  # Irving Park Road, nothing south of it
    "lat_max": 41.9650,  # Wilson Ave
    "lon_min": -87.6695,  # just west of Ashland (~-87.6690), east side only
    "lon_max": -87.6635,  # just east of Southport (~-87.6641)
}

# LV2 West bounding box for N-S streets: includes Wolcott
LV2_WEST_NS = {
    "lat_min": 41.9430,
    "lat_max": 41.9542,  # Irving Park Road
    "lon_min": -87.6770,  # wide enough to include Wolcott (~-87.6762)
    "lon_max": -87.6690,
}

# LV2 West bounding box for E-W streets: Hermitage to Ravenswood
# Per 2013 map, E-W streets span Hermitage to Ravenswood/Ashland area
LV2_WEST_EW = {
    "lat_min": 41.9430,
    "lat_max": 41.9542,  # Irving Park Road
    "lon_min": -87.6740,  # west to Ravenswood (~-87.6736)
    "lon_max": -87.6692,  # stop at Ashland (~-87.6690), don't cross into Zone 383
}

# Streets verified against the 2013 official LV2 Parking Areas map.
# Only streets with visible magenta lines on the 2013 map are included.
# Ashland, Damen, Honore (north) are NOT posted LV2 streets.
LV2_STREETS = {
    # N-S streets in north section: east of Ashland only (per 2013 map)
    "GREENVIEW":  {"direction": "ns", "sections": ["north"]},
    "SOUTHPORT":  {"direction": "ns", "sections": ["north"]},
    # N-S streets in west section only
    "HERMITAGE":  {"direction": "ns", "sections": ["west"]},
    "PAULINA":    {"direction": "ns", "sections": ["west"]},
    "MARSHFIELD": {"direction": "ns", "sections": ["west"]},
    # E-W streets in north section (east of Ashland)
    "CUYLER":       {"direction": "ew", "sections": ["north"]},
    "BELLE PLAINE": {"direction": "ew", "sections": ["north"]},
    "WARNER":       {"direction": "ew", "sections": ["north"]},
    "CULLOM":       {"direction": "ew", "sections": ["north"]},
    "PENSACOLA":    {"direction": "ew", "sections": ["north"]},
    "BERTEAU":      {"direction": "ew", "sections": ["north"]},
    # E-W streets in west section (Hermitage to Ravenswood)
    "EDDY":      {"direction": "ew", "sections": ["west"]},
    "GRACE":     {"direction": "ew", "sections": ["west"]},
    "WAVELAND":  {"direction": "ew", "sections": ["west"]},
    "ADDISON":   {"direction": "ew", "sections": ["west"]},
    "CORNELIA":  {"direction": "ew", "sections": ["west"]},
    "NEWPORT":   {"direction": "ew", "sections": ["west"]},
    "ROSCOE":    {"direction": "ew", "sections": ["west"]},
}

# Streets missing from OSM data, added with manual coordinates
# from the verified 2013 map / existing hardcoded map data
MANUAL_STREETS = [
    {
        "name": "BYRON",
        "direction": "ew",
        "section": "west",
        # Hermitage to Marshfield
        "coordinates": [[-87.672540, 41.952200], [-87.669252, 41.952200]],
    },
    {
        "name": "EDDY",
        "direction": "ew",
        "section": "west",
        # Wolcott to Ravenswood (per 2013 map)
        "coordinates": [[-87.676200, 41.946000], [-87.673550, 41.946000]],
    },
    {
        "name": "SUNNYSIDE",
        "direction": "ew",
        "section": "north",
        # Ashland to Clark (per 2013 map)
        "coordinates": [[-87.669000, 41.963400], [-87.666600, 41.963400]],
    },
    {
        "name": "RAVENSWOOD",
        "direction": "ns",
        "section": "west",
        # West section only: Roscoe to Irving Park (west of Ashland)
        "coordinates": [[-87.673550, 41.943423], [-87.673550, 41.9542]],
    },
]


def point_in_box(lat, lon, box):
    return (box["lat_min"] <= lat <= box["lat_max"] and
            box["lon_min"] <= lon <= box["lon_max"])


def interpolate(p1, p2, boundary_val, axis):
    """Interpolate between two [lon, lat] points at a boundary value.
    axis=0 for lon boundary, axis=1 for lat boundary."""
    if abs(p2[axis] - p1[axis]) < 1e-10:
        return list(p1)
    t = (boundary_val - p1[axis]) / (p2[axis] - p1[axis])
    return [
        p1[0] + t * (p2[0] - p1[0]),
        p1[1] + t * (p2[1] - p1[1]),
    ]


def clip_line_to_box(coords, box):
    """Clip a LineString's coordinates to a bounding box.
    Returns list of coordinate lists (may produce multiple segments
    if the line exits and re-enters the box)."""
    if len(coords) < 2:
        return []

    segments = []
    current = []

    for i, coord in enumerate(coords):
        lon, lat = coord[0], coord[1]
        inside = point_in_box(lat, lon, box)

        if inside:
            if not current and i > 0:
                # Entering the box: interpolate entry point
                prev = coords[i - 1]
                entry = clip_entry_point(prev, coord, box)
                if entry:
                    current.append(entry)
            current.append(coord)
        else:
            if current:
                # Exiting the box: interpolate exit point
                exit_pt = clip_entry_point(coord, coords[i - 1], box)
                if exit_pt:
                    current.append(exit_pt)
                if len(current) >= 2:
                    segments.append(current)
                current = []

    if len(current) >= 2:
        segments.append(current)

    return segments


def clip_entry_point(outside, inside, box):
    """Find the point where the line from outside to inside crosses the box boundary."""
    ox, oy = outside[0], outside[1]  # lon, lat
    ix, iy = inside[0], inside[1]

    best_t = 2.0  # start beyond valid range
    best_pt = None

    # Check all 4 boundaries
    boundaries = [
        (1, box["lat_min"]),  # bottom (lat)
        (1, box["lat_max"]),  # top (lat)
        (0, box["lon_min"]),  # left (lon)
        (0, box["lon_max"]),  # right (lon)
    ]

    for axis, val in boundaries:
        denom = ix - ox if axis == 0 else iy - oy
        if abs(denom) < 1e-12:
            continue
        num = val - (ox if axis == 0 else oy)
        t = num / denom
        if 0 <= t <= 1:
            pt = [ox + t * (ix - ox), oy + t * (iy - oy)]
            if point_in_box(pt[1], pt[0], box):
                if t < best_t:
                    best_t = t
                    best_pt = pt

    return best_pt


def determine_section(coords, direction):
    """Determine which LV2 section(s) a clipped segment belongs to."""
    sections = []
    west_box = LV2_WEST_NS if direction == "ns" else LV2_WEST_EW
    for coord in coords:
        lon, lat = coord[0], coord[1]
        if point_in_box(lat, lon, LV2_NORTH):
            if "north" not in sections:
                sections.append("north")
        if point_in_box(lat, lon, west_box):
            if "west" not in sections:
                sections.append("west")
    return sections[0] if sections else "unknown"


def main():
    # Load OSM data
    with open(INPUT_PATH) as f:
        osm_data = json.load(f)

    output_features = []
    stats = {"osm_matched": 0, "osm_clipped": 0, "manual": 0}

    # Process OSM features
    for feat in osm_data["features"]:
        name = feat["properties"]["name"]
        if name not in LV2_STREETS:
            continue

        stats["osm_matched"] += 1
        info = LV2_STREETS[name]
        coords = feat["geometry"]["coordinates"]

        # Try clipping to each section this street belongs to
        for section in info["sections"]:
            if section == "north":
                box = LV2_NORTH
            elif info["direction"] == "ns":
                box = LV2_WEST_NS
            else:
                box = LV2_WEST_EW
            clipped_segments = clip_line_to_box(coords, box)

            for seg_coords in clipped_segments:
                output_features.append({
                    "type": "Feature",
                    "properties": {
                        "street": name.title().replace("Belle Plaine", "Belle Plaine"),
                        "section": section,
                    },
                    "geometry": {
                        "type": "LineString",
                        "coordinates": seg_coords,
                    },
                })
                stats["osm_clipped"] += 1

    # Add manual streets (Byron, Wood, Ravenswood)
    for manual in MANUAL_STREETS:
        output_features.append({
            "type": "Feature",
            "properties": {
                "street": manual["name"].title(),
                "section": manual["section"],
            },
            "geometry": {
                "type": "LineString",
                "coordinates": manual["coordinates"],
            },
        })
        stats["manual"] += 1

    # Write output
    output = {
        "type": "FeatureCollection",
        "features": output_features,
    }

    Path(OUTPUT_PATH).parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w") as f:
        json.dump(output, f, separators=(",", ":"))

    print(f"Wrote {OUTPUT_PATH}")
    print(f"  OSM segments matched: {stats['osm_matched']}")
    print(f"  Clipped segments output: {stats['osm_clipped']}")
    print(f"  Manual streets added: {stats['manual']}")
    print(f"  Total features: {len(output_features)}")

    # Print street summary
    streets_seen = {}
    for feat in output_features:
        key = feat["properties"]["street"]
        streets_seen[key] = streets_seen.get(key, 0) + 1
    print(f"\n  Streets ({len(streets_seen)}):")
    for name in sorted(streets_seen):
        print(f"    {name}: {streets_seen[name]} segments")


if __name__ == "__main__":
    main()
