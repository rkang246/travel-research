#!/usr/bin/env python3
"""Check whether places/things are already in a trip's research.

    python3 scripts/find.py trips/<slug> "Mido Cafe" "美都餐室" "egg waffle"

For each query, prints:
  - matching items (by name / local name, tolerant of accents, punctuation, typos)
  - items that merely *mention* it (in descriptions, where_note, details)
  - earlier rejections from data.json's "rejected" list, with the reason
Standard library only.
"""
import difflib
import json
import re
import sys
import unicodedata
from pathlib import Path


def norm(s):
    s = unicodedata.normalize("NFKD", str(s or ""))
    s = "".join(c for c in s if not unicodedata.combining(c)).lower()
    s = re.sub(r"[^\w\s]", " ", s)          # keeps CJK characters (they are \w)
    return re.sub(r"\s+", " ", s).strip()


def name_score(q, name):
    n = norm(name)
    if not n or not q:
        return 0.0
    if q == n:
        return 1.0
    if q in n or n in q:
        return 0.9
    qt, nt = set(q.split()), set(n.split())
    overlap = len(qt & nt) / max(len(qt), 1)
    return max(difflib.SequenceMatcher(None, q, n).ratio(), overlap * 0.85)


def mention_text(it):
    parts = [it.get(k, "") for k in ("description", "why", "where_note", "seasonal", "address", "verification")]
    parts += [str(v) for v in (it.get("details") or {}).values()]
    return norm(" ".join(parts))


def describe(it):
    bits = [it["categories"][0], it.get("tier", ""), it.get("status", "")]
    if it.get("neighborhood"):
        bits.append(it["neighborhood"])
    return "%s  [%s]" % (it["id"], " · ".join(b for b in bits if b))


def main():
    if len(sys.argv) < 3:
        print(__doc__)
        sys.exit(2)
    data = json.loads((Path(sys.argv[1]) / "data.json").read_text(encoding="utf-8"))
    items = data.get("items", [])
    rejected = data.get("rejected", [])
    for raw in sys.argv[2:]:
        q = norm(raw)
        print("\n=== %s" % raw)
        scored = []
        for it in items:
            s = max(name_score(q, it.get("name")), name_score(q, it.get("local_name")))
            if s >= 0.6:
                scored.append((s, it))
        scored.sort(key=lambda x: -x[0])
        if scored:
            for s, it in scored[:6]:
                label = "MATCH" if s >= 0.9 else "maybe"
                print("  %-5s %.2f  %s — %s" % (label, s, it["name"], describe(it)))
        else:
            print("  no item with a similar name")
        matched_ids = {it["id"] for _, it in scored}
        mentions = [it for it in items if it["id"] not in matched_ids and q and q in mention_text(it)]
        for it in mentions[:6]:
            print("  mentioned in: %s — %s" % (it["name"], describe(it)))
        for r in rejected:
            s = name_score(q, r.get("name"))
            if s >= 0.6:
                print("  REJECTED %s (%.2f): %s — %s" % (r.get("date", ""), s, r.get("name"), r.get("reason", "")))


if __name__ == "__main__":
    main()
