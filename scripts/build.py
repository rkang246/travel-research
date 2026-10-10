#!/usr/bin/env python3
"""Build a trip's generated files from its data.json.

    python3 scripts/build.py trips/<slug> [--geocode]
    python3 scripts/build.py --index-only

Generates, inside the trip folder:
    index.html        field guide (catalog, map, neighborhoods, table, practical)
    locations.csv     master location database (mappable items only)
    locations.kml     items with coordinates, one folder per category group
    mymaps/*.csv      one CSV per Google My Maps layer
and refreshes the repo-root index.html and the trip table in README.md.

Standard library only (Python 3.9+).
"""
import argparse
import csv
import html
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).resolve().parent / "report_template.html"

CATEGORIES = [
    ("food", "Signature Foods & Drinks"),
    ("restaurants", "Restaurants & Culinary"),
    ("products", "Local Products & Brands"),
    ("neighborhoods", "Neighborhoods & Walks"),
    ("shopping", "Shopping & Markets"),
    ("photography", "Photography & Aesthetics"),
    ("attractions", "Landmarks & Culture"),
    ("experiences", "Experiences & Activities"),
    ("nature", "Nature & Outdoors"),
    ("nightlife", "Cafés, Nightlife & Social"),
    ("events", "Events During Your Dates"),
    ("daytrips", "Day Trips & Excursions"),
]
CAT_KEYS = [c[0] for c in CATEGORIES]
CAT_LABEL = dict(CATEGORIES)

# Google My Maps allows at most 10 layers per map, so the 12 categories are
# folded into 9 layer groups (by primary category).
LAYERS = [
    ("01-food-drink", "Food & Drink", {"food", "restaurants"}),
    ("02-cafes-nightlife", "Cafés & Nightlife", {"nightlife"}),
    ("03-shopping", "Shopping & Products", {"products", "shopping"}),
    ("04-neighborhoods", "Neighborhoods & Walks", {"neighborhoods"}),
    ("05-photography", "Photography", {"photography"}),
    ("06-sights", "Landmarks & Culture", {"attractions"}),
    ("07-experiences-events", "Experiences & Events", {"experiences", "events"}),
    ("08-nature", "Nature & Outdoors", {"nature"}),
    ("09-day-trips", "Day Trips", {"daytrips"}),
]

ENUMS = {
    "kind": {"place", "area", "dish", "product", "event", "daytrip"},
    "tier": {"iconic", "strong", "niche"},
    "cost": {"free", "$", "$$", "$$$", "$$$$"},
    "setting": {"indoor", "outdoor", "mixed"},
    "booking": {"none", "recommended", "required"},
    "status": {"verified", "reputation", "unconfirmed", "possibly-closed"},
}
REQUIRED_ITEM = ["id", "name", "kind", "categories", "description", "why", "tier", "status"]
MAPPABLE_KINDS = {"place", "area", "event", "daytrip"}
ID_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")
DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")


# ---------------------------------------------------------------- validation

def validate(data):
    errors, warnings = [], []
    meta = data.get("meta", {})
    for key in ("destination", "country", "slug", "arrive", "depart", "generated"):
        if not meta.get(key):
            errors.append("meta.%s is required" % key)
    for key in ("arrive", "depart", "generated"):
        if meta.get(key) and not DATE_RE.match(meta[key]):
            errors.append("meta.%s must be YYYY-MM-DD" % key)

    items = data.get("items", [])
    ids = set()
    for n, it in enumerate(items):
        label = it.get("id") or "items[%d]" % n
        for key in REQUIRED_ITEM:
            if not it.get(key):
                errors.append("%s: missing %s" % (label, key))
        iid = it.get("id", "")
        if iid:
            if iid in ids:
                errors.append("%s: duplicate id" % iid)
            ids.add(iid)
            if not ID_RE.match(iid):
                errors.append("%s: id must be lowercase-hyphenated ascii" % iid)
        for key, allowed in ENUMS.items():
            if it.get(key) and it[key] not in allowed:
                errors.append("%s: %s=%r not in %s" % (label, key, it[key], sorted(allowed)))
        cats = it.get("categories") or []
        for c in cats:
            if c not in CAT_KEYS:
                errors.append("%s: unknown category %r" % (label, c))
        if ("lat" in it) != ("lng" in it):
            errors.append("%s: lat and lng must be set together" % label)
        if it.get("kind") == "event":
            d = it.get("dates") or {}
            if not d.get("start"):
                errors.append("%s: events need dates.start" % label)
            if not it.get("sources"):
                errors.append("%s: events need at least one source" % label)
        if not it.get("sources"):
            warnings.append("%s: no sources" % label)
        if it.get("kind") in MAPPABLE_KINDS and not it.get("address") and "lat" not in it:
            warnings.append("%s: mappable kind but no address or coordinates" % label)

    for it in items:
        for ref in it.get("where") or []:
            if ref not in ids:
                errors.append("%s: where -> unknown id %r" % (it.get("id"), ref))
    for cl in data.get("clusters", []):
        for ref in cl.get("ids", []):
            if ref not in ids:
                errors.append("cluster %r -> unknown id %r" % (cl.get("name"), ref))
    return errors, warnings


# ---------------------------------------------------------------- geocoding

def geocode(data, trip_dir):
    cache_path = trip_dir / "geocode-cache.json"
    cache = json.loads(cache_path.read_text()) if cache_path.exists() else {}
    meta = data["meta"]
    changed = 0
    for it in data["items"]:
        if it.get("kind") not in MAPPABLE_KINDS or "lat" in it or not it.get("address"):
            continue
        query = location_query(it, meta)
        if query not in cache:
            url = "https://nominatim.openstreetmap.org/search?" + urllib.parse.urlencode(
                {"q": query, "format": "jsonv2", "limit": 1})
            req = urllib.request.Request(url, headers={"User-Agent": "travel-discovery/1.0 (personal trip research)"})
            try:
                with urllib.request.urlopen(req, timeout=20) as resp:
                    res = json.loads(resp.read().decode("utf-8"))
                cache[query] = res[0] if res else None
            except Exception as exc:  # network trouble: skip, retry next build
                print("  geocode failed for %s: %s" % (it["id"], exc))
                continue
            time.sleep(1.1)  # Nominatim usage policy: max 1 request/second
        hit = cache.get(query)
        if hit:
            it["lat"] = round(float(hit["lat"]), 6)
            it["lng"] = round(float(hit["lon"]), 6)
            it["coord_source"] = "nominatim"
            changed += 1
        else:
            print("  no geocode match: %s (%s)" % (it["id"], query))
    cache_path.write_text(json.dumps(cache, ensure_ascii=False, indent=1))
    print("geocoded %d item(s)" % changed)
    return changed


# ---------------------------------------------------------------- helpers

def location_query(it, meta):
    addr = it.get("address", "")
    parts = [addr] if addr else [it["name"], it.get("neighborhood", "")]
    joined = ", ".join(p for p in parts if p)
    for extra in (meta["destination"], meta["country"]):
        if extra.lower() not in joined.lower():
            joined += ", " + extra
    return joined


def maps_url(it, meta):
    if it.get("maps_url"):
        return it["maps_url"]
    query = "%s, %s" % (it["name"], location_query(it, meta))
    return "https://www.google.com/maps/search/?api=1&query=" + urllib.parse.quote(query)


def is_mappable(it):
    return it.get("kind") in MAPPABLE_KINDS and (it.get("address") or "lat" in it)


def layer_for(it):
    primary = it["categories"][0]
    for slug, label, cats in LAYERS:
        if primary in cats:
            return slug, label
    return LAYERS[0][0], LAYERS[0][1]


def fmt_dates(it):
    d = it.get("dates") or {}
    if not d.get("start"):
        return ""
    out = d["start"] if not d.get("end") or d["end"] == d["start"] else "%s to %s" % (d["start"], d["end"])
    return out + (" (%s)" % d["note"] if d.get("note") else "")


def sources_text(it):
    return " | ".join(s.get("url", "") for s in it.get("sources") or [])


# ---------------------------------------------------------------- outputs

def write_locations_csv(data, trip_dir):
    meta = data["meta"]
    cols = ["ID", "Name", "Local name", "Kind", "Category", "Other categories", "Subcategory",
            "Neighborhood", "Address", "Latitude", "Longitude", "Coord source", "Google Maps",
            "Website", "Description", "Why distinctive", "Tier", "Cost", "Duration", "Best time",
            "Setting", "Booking", "Seasonal", "Dates", "Status", "Verification", "Sources"]
    rows = []
    for it in data["items"]:
        if not is_mappable(it):
            continue
        rows.append([
            it["id"], it["name"], it.get("local_name", ""), it["kind"],
            CAT_LABEL[it["categories"][0]],
            "; ".join(CAT_LABEL[c] for c in it["categories"][1:]),
            it.get("subcategory", ""), it.get("neighborhood", ""), it.get("address", ""),
            it.get("lat", ""), it.get("lng", ""), it.get("coord_source", ""),
            maps_url(it, meta), it.get("website", ""), it["description"], it["why"],
            it["tier"], it.get("cost", ""), it.get("duration", ""), it.get("best_time", ""),
            it.get("setting", ""), it.get("booking", ""), it.get("seasonal", ""), fmt_dates(it),
            it["status"], it.get("verification", ""), sources_text(it),
        ])
    with open(trip_dir / "locations.csv", "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f)
        w.writerow(cols)
        w.writerows(rows)
    return len(rows)


def write_mymaps(data, trip_dir):
    meta = data["meta"]
    out_dir = trip_dir / "mymaps"
    out_dir.mkdir(exist_ok=True)
    for old in out_dir.glob("*.csv"):
        old.unlink()
    cols = ["Name", "Location", "Latitude", "Longitude", "Category", "Tier", "Neighborhood",
            "Description", "Google Maps", "ID"]
    groups = {}
    for it in data["items"]:
        if is_mappable(it):
            groups.setdefault(layer_for(it)[0], []).append(it)
    counts = {}
    for slug, label, _ in LAYERS:
        members = groups.get(slug)
        if not members:
            continue
        with open(out_dir / ("%s.csv" % slug), "w", newline="", encoding="utf-8") as f:
            w = csv.writer(f)
            w.writerow(cols)
            for it in members:
                desc = it["description"]
                if it.get("why"):
                    desc += " Why: " + it["why"]
                w.writerow([it["name"], location_query(it, meta), it.get("lat", ""), it.get("lng", ""),
                            CAT_LABEL[it["categories"][0]], it["tier"], it.get("neighborhood", ""),
                            desc, maps_url(it, meta), it["id"]])
        counts[label] = len(members)
    return counts


def write_kml(data, trip_dir):
    meta = data["meta"]
    e = lambda s: html.escape(str(s), quote=True)
    folders = {}
    skipped = 0
    for it in data["items"]:
        if not is_mappable(it):
            continue
        if "lat" not in it:
            skipped += 1
            continue
        folders.setdefault(layer_for(it)[1], []).append(it)
    parts = ['<?xml version="1.0" encoding="UTF-8"?>',
             '<kml xmlns="http://www.opengis.net/kml/2.2"><Document>',
             "<name>%s discovery (%s to %s)</name>" % (e(meta["destination"]), meta["arrive"], meta["depart"])]
    for _, label, _ in LAYERS:
        members = folders.get(label)
        if not members:
            continue
        parts.append("<Folder><name>%s</name>" % e(label))
        for it in members:
            desc = "<p>%s</p><p><b>Why:</b> %s</p><p>%s · %s</p><p><a href=\"%s\">Google Maps</a></p>" % (
                e(it["description"]), e(it["why"]), e(it["tier"]), e(it.get("neighborhood", "")),
                e(maps_url(it, meta)))
            parts.append("<Placemark><name>%s</name><description><![CDATA[%s]]></description>"
                         "<Point><coordinates>%s,%s,0</coordinates></Point></Placemark>"
                         % (e(it["name"]), desc, it["lng"], it["lat"]))
        parts.append("</Folder>")
    parts.append("</Document></kml>")
    (trip_dir / "locations.kml").write_text("\n".join(parts), encoding="utf-8")
    return skipped


def write_report(data, trip_dir):
    meta = data["meta"]
    payload = dict(data)
    payload["items"] = []
    for it in data["items"]:
        it = dict(it)
        if is_mappable(it):
            it["maps_url"] = maps_url(it, meta)
        payload["items"].append(it)
    payload["categories"] = CATEGORIES
    blob = json.dumps(payload, ensure_ascii=False).replace("</", "<\\/")
    title = "%s Discovery Guide" % meta["destination"]
    page = TEMPLATE.read_text(encoding="utf-8")
    page = page.replace("__TITLE__", html.escape(title)).replace("__DATA__", blob)
    (trip_dir / "index.html").write_text(page, encoding="utf-8")


# ---------------------------------------------------------------- repo index

def load_trips():
    trips = []
    for path in sorted((ROOT / "trips").glob("*/data.json"), reverse=True):
        try:
            d = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print("  skipping %s: %s" % (path, exc))
            continue
        m = d.get("meta", {})
        trips.append({
            "dir": path.parent.name,
            "destination": m.get("destination", path.parent.name),
            "country": m.get("country", ""),
            "arrive": m.get("arrive", ""),
            "depart": m.get("depart", ""),
            "generated": m.get("generated", ""),
            "count": len(d.get("items", [])),
        })
    return trips


def write_root_index(trips):
    site = json.loads((ROOT / "site.json").read_text()) if (ROOT / "site.json").exists() else {}
    base = site.get("pages_base", "").rstrip("/")

    # README trip table (between markers)
    readme = ROOT / "README.md"
    if readme.exists():
        lines = ["| Trip | Dates | Items | Report | Data |", "|---|---|---|---|---|"]
        for t in trips:
            report = "[open](%s/trips/%s/)" % (base, t["dir"]) if base else "-"
            lines.append("| %s, %s | %s → %s | %d | %s | [folder](trips/%s/) |" % (
                t["destination"], t["country"], t["arrive"], t["depart"], t["count"], report, t["dir"]))
        if not trips:
            lines.append("| _no trips yet_ | | | | |")
        text = readme.read_text(encoding="utf-8")
        new = re.sub(r"(<!-- TRIPS:START -->\n).*?(\n<!-- TRIPS:END -->)",
                     lambda m: m.group(1) + "\n".join(lines) + m.group(2), text, flags=re.S)
        readme.write_text(new, encoding="utf-8")

    # Root landing page for GitHub Pages
    e = html.escape
    cards = "\n".join(
        '<a class="trip" href="trips/%s/"><h2>%s</h2><p>%s</p><p class="m">%s → %s · %d discoveries · researched %s</p></a>'
        % (e(t["dir"]), e(t["destination"]), e(t["country"]), e(t["arrive"]), e(t["depart"]), t["count"], e(t["generated"]))
        for t in trips) or '<p class="m">No trips yet.</p>'
    page = """<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>Travel Discovery</title>
<style>
:root{--bg:#f6f5f2;--panel:#fff;--text:#1d1d1f;--muted:#6b6b70;--line:#e3e1dc;--accent:#2b6cb0}
@media (prefers-color-scheme:dark){:root{--bg:#111318;--panel:#1a1d24;--text:#e8e9ed;--muted:#9aa0ab;--line:#2b2f39;--accent:#7fb2ff}}
*{box-sizing:border-box}body{margin:0;background:var(--bg);color:var(--text);font:16px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,sans-serif}
main{max-width:860px;margin:0 auto;padding:40px 16px}h1{margin:0 0 4px}.m{color:var(--muted);font-size:.9rem;margin:0}
.grid{display:grid;gap:12px;margin-top:24px}.trip{display:block;background:var(--panel);border:1px solid var(--line);border-radius:12px;padding:16px 18px;color:inherit;text-decoration:none}
.trip:hover{border-color:var(--accent)}.trip h2{margin:0;font-size:1.2rem}.trip p{margin:2px 0}
</style></head><body><main>
<h1>Travel Discovery</h1><p class="m">Destination research catalogs. Discovery first, itineraries later.</p>
<div class="grid">
%s
</div></main></body></html>
""" % cards
    (ROOT / "index.html").write_text(page, encoding="utf-8")


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("trip_dir", nargs="?", help="trips/<slug>")
    ap.add_argument("--geocode", action="store_true", help="fill missing coordinates via OSM Nominatim")
    ap.add_argument("--index-only", action="store_true", help="only refresh root index.html and README")
    args = ap.parse_args()

    if not args.index_only:
        if not args.trip_dir:
            ap.error("trip_dir is required unless --index-only")
        trip_dir = Path(args.trip_dir).resolve()
        data_path = trip_dir / "data.json"
        data = json.loads(data_path.read_text(encoding="utf-8"))
        data.setdefault("items", [])

        errors, warnings = validate(data)
        for w in warnings:
            print("warning: " + w)
        if errors:
            for err in errors:
                print("ERROR: " + err)
            print("\n%d error(s); nothing written." % len(errors))
            sys.exit(1)

        if args.geocode and geocode(data, trip_dir):
            data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        write_report(data, trip_dir)
        n_loc = write_locations_csv(data, trip_dir)
        layers = write_mymaps(data, trip_dir)
        skipped = write_kml(data, trip_dir)

        items = data["items"]
        print("\n%s: %d items" % (data["meta"]["destination"], len(items)))
        for key, label in CATEGORIES:
            primary = sum(1 for i in items if i["categories"][0] == key)
            cross = sum(1 for i in items if key in i["categories"][1:])
            print("  %-28s %3d%s" % (label, primary, ("  (+%d cross-listed)" % cross) if cross else ""))
        with_coords = sum(1 for i in items if is_mappable(i) and "lat" in i)
        print("locations.csv: %d mappable · %d with coordinates · %d not in KML (no coords)" % (n_loc, with_coords, skipped))
        print("My Maps layers: " + ", ".join("%s (%d)" % kv for kv in layers.items()))

    write_root_index(load_trips())
    print("refreshed root index.html and README")


if __name__ == "__main__":
    main()
