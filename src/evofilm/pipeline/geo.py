"""Map data for history/geography frames — Natural Earth (public domain) as a JS data file.

  evofilm geo --project <dir> [--layers countries,coastline,rivers,lakes] [--scale 110m|50m]

Writes <project>/assets/geo/<layer>-<scale>.js, each defining
  window.EF_GEO["<layer>"] = <GeoJSON FeatureCollection>
Coordinates are rounded to 2 decimals (≈1 km) to keep files small. Downloads are cached in
~/.evofilm/geo-cache/. Load in a frame with a classic script tag BEFORE the frame script:
  <script src="assets/geo/countries-110m.js"></script>
and project it with d3-geo (see references/history.md → Maps).

Historical borders are NOT in Natural Earth (it is present-day). Draw historical territories as
your own lon/lat polygons from a cited source and say they are approximate.
"""

import argparse
import json
import urllib.request
from pathlib import Path

from evofilm import paths
BASE = "https://raw.githubusercontent.com/nvkelso/natural-earth-vector/master/geojson"
LAYERS = {
    "countries": "ne_{s}_admin_0_countries.geojson",
    "coastline": "ne_{s}_coastline.geojson",
    "rivers": "ne_{s}_rivers_lake_centerlines.geojson",
    "lakes": "ne_{s}_lakes.geojson",
    "land": "ne_{s}_land.geojson",
    "places": "ne_{s}_populated_places_simple.geojson",
}
KEEP_PROPS = {"NAME", "NAME_ZH", "NAME_EN", "ADMIN", "ISO_A3", "CONTINENT", "name", "name_zh", "scalerank", "featurecla"}


def rnd(c):
    if isinstance(c, (int, float)):
        return round(c, 2)
    return [rnd(x) for x in c]


def fetch(layer, scale):
    CACHE = paths.geo_cache()
    CACHE.mkdir(parents=True, exist_ok=True)
    name = LAYERS[layer].format(s=scale)
    path = CACHE / name
    if not path.exists():
        with urllib.request.urlopen(f"{BASE}/{name}", timeout=120) as r:
            path.write_bytes(r.read())
    return json.loads(path.read_text("utf-8"))


def slim(fc):
    feats = []
    for f in fc["features"]:
        props = {k: v for k, v in (f.get("properties") or {}).items() if k in KEEP_PROPS}
        geom = f["geometry"]
        if geom is None:
            continue
        feats.append({"type": "Feature", "properties": props,
                      "geometry": {"type": geom["type"], "coordinates": rnd(geom["coordinates"])}})
    return {"type": "FeatureCollection", "features": feats}


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--project", default=".")
    ap.add_argument("--layers", default="countries,coastline,rivers")
    ap.add_argument("--scale", default="110m", choices=["110m", "50m"])
    a = ap.parse_args(argv)
    out = Path(a.project) / "assets" / "geo"
    out.mkdir(parents=True, exist_ok=True)
    for layer in a.layers.split(","):
        layer = layer.strip()
        fc = slim(fetch(layer, a.scale))
        js = f'window.EF_GEO = window.EF_GEO || {{}};\nwindow.EF_GEO["{layer}"] = {json.dumps(fc, ensure_ascii=False, separators=(",", ":"))};\n'
        p = out / f"{layer}-{a.scale}.js"
        p.write_text(js, "utf-8")
        print(f"  {p.name}: {len(fc['features'])} features · {p.stat().st_size / 1024:.0f} KB")
    print("✓ geo data → assets/geo/ (Natural Earth, public domain)")


if __name__ == "__main__":
    main()
