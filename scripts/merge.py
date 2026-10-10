#!/usr/bin/env python3
"""Assemble trips/<slug>/data.json from research work files, deterministically.

    python3 scripts/merge.py trips/<slug>                 # merge + compact summary
    python3 scripts/merge.py trips/<slug> --list          # ...plus one line per item
    python3 scripts/merge.py trips/<slug> --list food,restaurants
    python3 scripts/merge.py --check trips/<slug>/work/eat.jsonl   # validate one work file

Inputs, all in trips/<slug>/work/:
  synthesis.json    top-level sections written by the orchestrator: meta, theme,
                    category_info, lenses, overview, clusters, practical, rejected
  *.jsonl           item records from research agents, one JSON object per line
  *.json            the same as a JSON array (except synthesis.json)
  *.patch.jsonl     partial records {"id": ..., <fields>} applied to existing items
                    (verification updates); "sources" are appended, other fields replace

Existing data.json items are merged first, so their IDs survive refreshes.
Duplicates (same id, or same normalized name/local name in the same neighborhood)
are merged; items matching the rejected list are dropped. The point is that the
orchestrating model never has to read or rewrite the full record set itself.
Standard library only.
"""
import argparse
import difflib
import json
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build import CATEGORIES, validate  # noqa: E402
from find import norm  # noqa: E402

TARGETS = {
    "food": (15, 25), "restaurants": (20, 35), "products": (10, 20), "neighborhoods": (10, 20),
    "shopping": (10, 20), "photography": (15, 25), "attractions": (15, 25), "experiences": (10, 20),
    "nature": (10, 20), "nightlife": (10, 20), "events": (0, 0), "daytrips": (5, 15),
}
STATUS_RANK = {"possibly-closed": 0, "verified": 1, "reputation": 2, "unconfirmed": 3}
LIST_FIELDS = ("lenses", "where")
LONGER_WINS = ("description", "why", "where_note", "seasonal")


def read_records(path):
    """Return (records, errors) from a .jsonl or .json file."""
    text = path.read_text(encoding="utf-8")
    if path.suffix == ".json":
        try:
            data = json.loads(text)
        except ValueError as exc:
            return [], ["%s: invalid JSON (%s)" % (path.name, exc)]
        return (data if isinstance(data, list) else [data]), []
    records, errors = [], []
    for n, line in enumerate(text.splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except ValueError as exc:
            errors.append("%s line %d: invalid JSON (%s)" % (path.name, n, exc))
    return records, errors


def same_place(a, b):
    if a.get("id") == b.get("id"):
        return True
    names_a = {norm(a.get("name")), norm(a.get("local_name"))} - {""}
    names_b = {norm(b.get("name")), norm(b.get("local_name"))} - {""}
    if not names_a & names_b:
        return False
    if a.get("kind") in ("dish", "product") or b.get("kind") in ("dish", "product"):
        return a.get("kind") == b.get("kind")
    ha, hb = norm(a.get("neighborhood")), norm(b.get("neighborhood"))
    return not ha or not hb or ha == hb


def merge_into(a, b, override=False):
    """Merge record b into record a (a keeps its id).

    override=True (same id: a corrected or refreshed record) lets b's non-empty
    scalar fields replace a's; otherwise b only fills gaps."""
    for c in b.get("categories") or []:
        if c not in a.setdefault("categories", []):
            a["categories"].append(c)
    urls = {s.get("url") for s in a.get("sources") or []}
    for s in b.get("sources") or []:
        if s.get("url") not in urls:
            a.setdefault("sources", []).append(s)
            urls.add(s.get("url"))
    for f in LIST_FIELDS:
        for v in b.get(f) or []:
            if v not in a.setdefault(f, []):
                a[f].append(v)
    for k, v in (b.get("details") or {}).items():
        a.setdefault("details", {}).setdefault(k, v)
    for f in LONGER_WINS:
        if len(str(b.get(f) or "")) > len(str(a.get(f) or "")):
            a[f] = b[f]
    if STATUS_RANK.get(b.get("status"), 9) < STATUS_RANK.get(a.get("status"), 9):
        a["status"] = b["status"]
        if b.get("verification"):
            a["verification"] = b["verification"]
    for k, v in b.items():
        if k in ("id", "categories", "sources", "details") + LIST_FIELDS:
            continue
        if k not in a or a[k] in ("", None, [], {}) or (override and v not in ("", None, [], {})):
            a[k] = v


def is_rejected(it, rejected):
    names = {norm(it.get("name")), norm(it.get("local_name"))} - {""}
    for r in rejected:
        rnames = {norm(r.get("name")), norm(r.get("local_name"))} - {""}
        for x in names:
            for y in rnames:
                if x == y or difflib.SequenceMatcher(None, x, y).ratio() >= 0.92:
                    return r
    return None


def check_file(path):
    records, errors = read_records(path)
    data = {"meta": {"destination": "x", "country": "x", "slug": "x", "arrive": "2000-01-01",
                     "depart": "2000-01-01", "generated": "2000-01-01"}, "items": records}
    errs, warns = validate(data)
    # where/lens references may point into other agents' files or synthesis.json; checked at merge time
    errs = [e for e in errs if "where -> unknown id" not in e and "is not defined in top-level lenses" not in e]
    for e in errors + errs:
        print("ERROR: " + e)
    print("%s: %d records, %d error(s), %d warning(s)" % (path.name, len(records), len(errors) + len(errs), len(warns)))
    sys.exit(1 if errors or errs else 0)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("trip_dir", nargs="?")
    ap.add_argument("--list", nargs="?", const="all", help="print one line per item (optionally: comma-separated categories)")
    ap.add_argument("--warnings", action="store_true", help="print every validation warning")
    ap.add_argument("--check", metavar="FILE", help="validate a single work file and exit")
    args = ap.parse_args()
    if args.check:
        check_file(Path(args.check))
    if not args.trip_dir:
        ap.error("trip_dir is required")

    trip = Path(args.trip_dir)
    work = trip / "work"
    data_path = trip / "data.json"
    data = json.loads(data_path.read_text(encoding="utf-8")) if data_path.exists() else {}
    existing = data.pop("items", [])
    synth_path = work / "synthesis.json"
    if synth_path.exists():
        data.update(json.loads(synth_path.read_text(encoding="utf-8")))
    rejected = data.get("rejected") or []

    problems, item_files, patch_files = [], [], []
    for p in sorted(work.glob("*.json*")) if work.exists() else []:
        if p.name == "synthesis.json":
            continue
        (patch_files if p.name.endswith(".patch.jsonl") else item_files).append(p)

    incoming = []
    for p in item_files:
        recs, errs = read_records(p)
        problems += errs
        incoming += [(p.name, r) for r in recs]

    items, remap, merged_n, dropped = [], {}, 0, []
    for src, rec in [("data.json", r) for r in existing] + incoming:
        if not isinstance(rec, dict) or not rec.get("id") or not rec.get("name"):
            problems.append("%s: record without id/name skipped: %s" % (src, str(rec)[:80]))
            continue
        hit = is_rejected(rec, rejected)
        if hit:
            dropped.append("%s (rejected: %s)" % (rec["name"], hit.get("reason", "")))
            continue
        match = next((it for it in items if same_place(it, rec)), None)
        if match:
            if match["id"] != rec["id"]:
                remap[rec["id"]] = match["id"]
            merge_into(match, rec, override=match["id"] == rec["id"])
            merged_n += 1
            continue
        if any(it["id"] == rec["id"] for it in items):  # same id, different place
            base, n = rec["id"], 2
            while any(it["id"] == "%s-%d" % (base, n) for it in items):
                n += 1
            rec["id"] = "%s-%d" % (base, n)
            problems.append("id collision: %r renamed to %r (%s)" % (base, rec["id"], rec["name"]))
        items.append(rec)

    by_id = {it["id"]: it for it in items}
    for p in patch_files:
        recs, errs = read_records(p)
        problems += errs
        for patch in recs:
            target = by_id.get(remap.get(patch.get("id"), patch.get("id")))
            if not target:
                problems.append("%s: patch for unknown id %r" % (p.name, patch.get("id")))
                continue
            for k, v in patch.items():
                if k == "id":
                    continue
                if k == "sources":
                    merge_into(target, {"sources": v})
                else:
                    target[k] = v

    for it in items:
        if it.get("where"):
            it["where"] = list(dict.fromkeys(remap.get(w, w) for w in it["where"]))
    for cl in data.get("clusters") or []:
        cl["ids"] = list(dict.fromkeys(remap.get(i, i) for i in cl.get("ids", [])))

    possible = []
    for i, a in enumerate(items):
        for b in items[i + 1:]:
            if difflib.SequenceMatcher(None, norm(a["name"]), norm(b["name"])).ratio() >= 0.88:
                possible.append("%s ~ %s" % (a["id"], b["id"]))

    data["items"] = items
    data_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

    # ---- compact report (this is what the orchestrator reads, not the records)
    print("merged %d record(s) from %d file(s) into %d items (%d duplicates folded, %d patch file(s))"
          % (len(existing) + len(incoming), len(item_files) + (1 if existing else 0), len(items), merged_n, len(patch_files)))
    prim = Counter(it["categories"][0] for it in items if it.get("categories"))
    print("\ncategory          count  target")
    for k, label in CATEGORIES:
        lo, hi = TARGETS[k]
        flag = "" if k == "events" else ("  LOW" if prim[k] < lo else "")
        print("  %-15s %5d  %s%s" % (k, prim[k], "-" if k == "events" else "%d-%d" % (lo, hi), flag))
    print("\ntier:   " + ", ".join("%s %d" % kv for kv in Counter(it.get("tier") for it in items).most_common()))
    print("status: " + ", ".join("%s %d" % kv for kv in Counter(it.get("status") for it in items).most_common()))
    print("region: " + ", ".join("%s %d" % kv for kv in Counter(it.get("region") or "(none)" for it in items).most_common()))
    hoods = Counter(it.get("neighborhood") for it in items if it.get("neighborhood"))
    print("top neighborhoods: " + ", ".join("%s %d" % kv for kv in hoods.most_common(12)))
    lenses = Counter(l for it in items for l in it.get("lenses") or [])
    if lenses:
        print("lenses: " + ", ".join("%s %d" % kv for kv in lenses.most_common()))
    no_src = [it["id"] for it in items if not it.get("sources")]
    if no_src:
        print("no sources (%d): %s" % (len(no_src), ", ".join(no_src[:15]) + (" …" if len(no_src) > 15 else "")))
    for label, rows in (("dropped (rejected list)", dropped), ("possible duplicates, not merged", possible), ("problems", problems)):
        if rows:
            print("\n%s:" % label)
            for r in rows[:40]:
                print("  - " + r)

    errs, warns = validate(data)
    print("\nvalidation: %d error(s), %d warning(s)%s" % (len(errs), len(warns), "" if args.warnings or not warns else " (--warnings to show)"))
    for e in errs:
        print("  ERROR: " + e)
    if args.warnings:
        for w in warns:
            print("  warning: " + w)

    if args.list:
        cats = None if args.list == "all" else set(args.list.split(","))
        print("\nid | name | local | categories | subcategory | neighborhood | tier | status | booking | lenses")
        order = {k: n for n, (k, _) in enumerate(CATEGORIES)}
        for it in sorted(items, key=lambda i: (order.get(i["categories"][0], 99), i.get("subcategory") or "", i["name"])):
            if cats and not cats & set(it["categories"]):
                continue
            print(" | ".join([it["id"], it["name"], it.get("local_name", ""), "+".join(it["categories"]),
                              it.get("subcategory", ""), it.get("neighborhood", ""), it.get("tier", ""),
                              it.get("status", ""), it.get("booking", ""), ",".join(it.get("lenses") or [])]))


if __name__ == "__main__":
    main()
