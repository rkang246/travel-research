---
name: travel-discovery
description: In-depth destination research that builds a large, filterable discovery catalog for a trip covering signature foods, restaurants, local brands and products, neighborhoods, shopping, photo spots, landmarks, experiences, nature, cafés and nightlife, events on the exact travel dates, and day trips, including places trending on Instagram, TikTok, and RedNote. It saves everything to the travel-discovery repo as data.json, a destination-themed HTML field guide with a map and shortlist, and Google My Maps CSVs. Use this whenever the user names a destination they're visiting (with or without dates) and wants to know what to eat, see, buy, photograph, or do there, asks to "research" a city or trip, or wants a travel brainstorm, field guide, or map of places, even if they never say "discovery". Also use it when the user follows up about a trip that has already been researched with a place, dish, shop, or event they heard about ("is X in my Tokyo list?", "a friend recommended Y", "saw Z on TikTok"), to check whether it's already covered and evaluate adding it. Not for day-by-day itineraries or route optimization from an existing shortlist; that's a separate later phase.
argument-hint: <destination> <arrive> <depart> [notes on base, interests, budget, pace]
---

# Travel Discovery

Act as a thorough travel researcher and discovery engine. The deliverable is a
**destination discovery database and researched field guide**, a large menu of
well-researched options the user picks from. It is **not** an itinerary.

Research and selection are deliberately separate phases. Optimizing early
(fitting things into days, pruning by distance or opening hours) quietly drops
the most interesting discoveries before the user ever sees them. So here,
breadth wins. Trip length affects how *relevant* things are, never how much
gets researched. A 3-day trip still gets the full catalog. The user shortlists
in the report, and a separate itinerary step works from that shortlist.

## Inputs

- **Required:** destination; arrival and departure dates. If the dates are
  missing, ask once, because events, seasonality, and closures all depend on them.
- **Optional:** accommodation area, interests, budget, pace, transport
  constraints. Don't ask about these. Assume sensible defaults (curious about
  food, culture, shopping, photography, and exploration; mid-range budget;
  public transit and walking) and record every assumption in
  `meta.assumptions`.

## Where the output goes

Repo: the git checkout containing this skill (GitHub: `rkang246/travel-research`).
Find its root from this skill's base directory, following symlinks:
`cd "$(dirname "$(readlink -f <skill-base>/SKILL.md)")/../../.." && pwd`.
Usual locations: `~/Desktop/Code/travel-discovery` on the Mac and
`~/work/travel-research` on the OpenClaw server. Run every command below from
that root, and give agents **absolute** paths under it.

```
trips/<YYYY-MM>-<city-slug>/        e.g. trips/2026-11-tokyo/
  data.json        ← source of truth (schema: references/schema.md), assembled by
                     scripts/merge.py during research, edited directly afterwards
  index.html       ← generated field guide (list, map, neighborhoods, table, practical)
  locations.csv    ← generated master location database
  locations.kml    ← generated, for Google Earth / My Maps
  mymaps/*.csv     ← generated, one CSV per My Maps layer (≤10 layers)
  work/            ← research scratch (gitignored): orientation.md, synthesis.json,
                     agents' *.jsonl, *.patch.jsonl
```

`scripts/build.py` generates the report and exports from `data.json` and
refreshes the repo's root `index.html` and README trip list. Because the list,
master database, map, and neighborhood view are all rendered from the same
records, items are deduplicated by construction: a place that's both a photo
spot and a café is **one** record with `categories: ["photography", "nightlife"]`.

## Research principles

1. **Breadth over curation.** Cover every category substantially, with concise
   but concrete entries. The targets in `references/categories.md` are
   coverage goals, not quotas. Scale them to the destination, and never invent
   or pad to hit a number.
2. **Local distinctiveness.** Keep asking: what is this place famous for? What
   is hard to replicate elsewhere? What do locals associate with its identity?
   What do knowledgeable repeat visitors recommend? What would someone into
   food, culture, shopping, photography, and exploration regret missing? Which
   neighborhoods are emerging, and which niche scenes are underrated? Balance
   world-famous landmarks with real local discoveries, but don't mistake
   obscurity for quality, and don't manufacture "hidden gem" status.
3. **Diverse sources.** Combine official tourism and cultural institutions,
   reputable local food and travel publications, **local-language sources** (search
   in the local language; they often surface venues English SEO lists miss),
   specialty fashion, design, architecture, photography, and food press, local
   blogs and forums, official business sites and event calendars, and map
   listings. Corroborate the strongest recommendations independently. Don't lean
   on generic listicles that all repeat each other. Separate verified facts from
   reputation, and paraphrase sources rather than copying review text. Include
   **social and trending signals** too (see *Social & trending research*), since
   they surface new and visually striking places long before guidebooks do.
4. **Current and date-aware.** Use the actual dates to check seasonal foods,
   weather-dependent experiences, events, public holidays and closures, places
   that closed or moved, seasonal hours, renovations, and required
   reservations, tickets, or permits. Record what you confirmed and what you
   didn't in each item's `status` and `verification`.
5. **No premature itinerary.** No "Day 1 / Day 2". Make everything filterable
   instead, through the item fields (category, subcategory, region,
   neighborhood, lenses, tier, cost, duration, setting, booking, seasonal),
   which the report turns into filters.

## Workflow

### Who does what

Full coverage means ~200–300 researched items and hundreds of searches. That
volume shouldn't run on the most expensive model, and it shouldn't pass through
your context. Split the work by what each stage needs:

| Stage | Who | Why |
|---|---|---|
| Orientation, review, synthesis | **you** (session model) | Judgment: what matters here, what's missing, how to present it |
| Category research, gap-fill, verification | **`travel-researcher` agents** (Sonnet, defined in `.claude/agents/travel-researcher.md`) | Volume: searching and reading pages |
| Merge, dedupe, validation, rendering | **scripts** (`merge.py`, `build.py`) | Mechanical: exact, repeatable, free |

Cost rules. These matter: an unconstrained run can exhaust a session's usage
limit before one city is done.
- Spawn research **only** as `subagent_type: "travel-researcher"`, and also pass
  `model: "sonnet"` on the call, so the worker can't inherit your model.
  Don't use general-purpose agents for research, and don't do the bulk
  category research yourself.
- **At most 5 agent runs per trip:** 4 category agents, then 1 follow-up agent.
- **Don't read work files or the full `data.json`.** Your view of the research is
  `merge.py`'s summary and `--list` output (one line per item). When a decision
  needs detail, grep or `find.py` the specific records.
- Write your own contributions (meta, theme, lenses, overview, clusters,
  category_info, practical, coverage) to `work/synthesis.json`, and fix records
  through patch files. `merge.py` assembles `data.json`, so you never rewrite it.

### 1. Set up
Create `trips/<YYYY-MM>-<city-slug>/work/` (month of arrival). On a refresh,
`merge.py` folds the existing `data.json` in first, so IDs that persist are kept
automatically. If `work/` still holds files from an earlier run, move them into
`work/archive-<date>/` first.

### 2. Orientation (you, ~10–15 searches)
Build the context every later step needs:
- what the destination is known for, its food identity, and its main neighborhoods and their character
- design and shopping culture
- local language and script
- public holidays and seasonal conditions for the dates, and sunrise and sunset times
- the best local-language publications and event calendars
- **which social platforms locals and regional travelers actually use** (see *Social & trending research*)

Then decide what every agent must use consistently:
- **Regions**: 3–6 coarse areas a visitor thinks in (`meta.regions`), plus
  canonical spellings for the main neighborhoods.
- **Lenses**: 2–6 cross-category interest toggles drawn from the traveler's
  interests and the city's personality (e.g. `retro`, `design`, `rainy-day`),
  plus `trending`.
- **Theme**: the report's visual identity, rooted in the place (`theme`,
  `meta.local_title`, and the `local`/`tagline` fields of `category_info`).
  See the `theme` section of `references/schema.md`. The Hong Kong prototype's
  MTR-map look, with line colours, station-sign headers, and 香港清單 as its title, is
  the bar to meet. A generic palette is a missed opportunity.

Write the notes, regions, lenses, neighborhood spellings, and per-group source
tips to `work/orientation.md`. Write `meta`, `lenses`, `theme`, and the first
pass of `category_info` to `work/synthesis.json`.

### 3. Research: 4 `travel-researcher` agents in parallel

| Brief | Categories | Output file |
|---|---|---|
| eat-drink | `food`, `restaurants`, `nightlife` | `work/eat-drink.jsonl` |
| shop-walk | `products`, `shopping`, `neighborhoods` | `work/shop-walk.jsonl` |
| see-shoot | `attractions`, `photography`, `nature` | `work/see-shoot.jsonl` |
| do-go | `experiences`, `events`, `daytrips` | `work/do-go.jsonl` |

Keep each brief compact: point to files by **absolute path** instead of pasting
them. Include:
- destination, dates, slug, traveler profile and assumptions
- the paths to `work/orientation.md`, `references/categories.md` (name the
  sections), `references/schema.md`, and this SKILL.md (sections *Research
  principles*, *Social & trending research*, *Quality standards*)
- the absolute output path
- any group-specific tips from orientation (sources, platforms, seasonal angles)

The agent definition already covers search budgets, batch appending,
validation, and the short reply.

If an agent stops early at its turn limit, its records are already on disk.
Leave the gaps for the follow-up pass rather than resuming it.

Without a subagent tool, research the same groups yourself, one at a time,
appending to the same files.

### 4. Merge and review (you)
```bash
python3 scripts/merge.py trips/<slug> --list
```
The script dedupes across agents (same place found twice becomes one record with both
categories), applies patches, drops anything on the `rejected` list, validates,
and prints coverage against targets plus one line per item. Review that output
for:
- **Gaps**: categories below target; few local-language, regional, or niche finds;
  everything clustered in two neighborhoods; thin `trending` coverage.
- **Problems**: possible duplicates it didn't merge, dangling `where` links,
  inconsistent neighborhood names, a wrong primary category.
- **Risk** (what needs verification): `iconic` items, `booking: required`,
  events, `possibly-closed` / `unconfirmed`, and social-only finds.

Fix problems that need no research with your own patch file
(`work/orchestrator.patch.jsonl`, one `{"id": ..., <fields>}` per line).

### 5. One follow-up agent: gap-fill and verification
Spawn one more `travel-researcher` (Sonnet) with two concrete lists:
- **Gaps → `work/gapfill.jsonl`**: specific asks, such as "8 more photography spots,
  especially night and neon", "3 local-language dessert finds", or "nature in the New
  Territories".
- **Checks → `work/verify.patch.jsonl`**: item IDs, each with what to check.

Verify in proportion to risk, not uniformly:

| Finding | Treatment |
|---|---|
| Famous landmark with reliable sources | No extra check |
| Established local restaurant with good sources | No extra check |
| Obscure place with thin evidence, or social-only | Confirm it exists and is open |
| Event on the trip dates | Confirm on the official schedule |
| Conflicting hours, status, or booking info | Resolve with the official source |
| Product with uncertain local origin | Confirm provenance before claiming it |

Then re-run `merge.py`.

### 6. Synthesis (you)
Add to `work/synthesis.json`, working from `--list` and targeted lookups:
- `overview`: a short orientation covering what the place is known for, its
  defining food traditions, the most interesting neighborhoods, shopping and design
  culture, what makes it different, and the seasonal notes for these dates. Keep it
  brief, since the catalog is the product.
- `clusters`: geographic groupings for the neighborhood view (e.g. "Kuramae: two
  stationery shops, a coffee roaster, a riverside photo spot"). Only group
  things that really are near each other, and don't invent walking times.
- `category_info` notes: category-wide context worth a callout, such as a price key,
  famous places that recently closed (so the user stops looking for them), how
  trailheads are reached, or seasonal caveats. Add a `label` override when the destination
  suggests a better name.
- `practical`: transit, payment, holiday closures, weather, access notes. Lists of
  booking-required, unverified, and event items are derived automatically.
- `meta.coverage`: disclose any category with thin or incomplete coverage.

Re-run `merge.py` to fold it in.

### 7. Build and check
```bash
python3 scripts/build.py trips/<slug> --geocode
```
`--geocode` fills missing coordinates through OpenStreetMap Nominatim (≈1
request/sec, cached in `geocode-cache.json`) and writes them back to
`data.json` with `coord_source: "nominatim"`. Fix every **error** (through a patch
file and `merge.py`, or by editing `synthesis.json`), review the warnings, and
rebuild. Spot-check a few geocoded pins that look out of place in the report's Map tab.
Nominatim sometimes matches a same-named place elsewhere, so correct or delete those coordinates.

### 8. Archive, commit, and report
Move `work/*.json*` into `work/archive-<date>/`. From now on `data.json` is
edited directly (ad hoc additions), and stale work files must not be merged over
those edits. Commit the trip folder and the regenerated root files locally.
**Don't push** unless the user says so, because pushing publishes to GitHub.
Then tell the user:
- item counts per category and any coverage gaps
- the handful of most time-sensitive things (bookings to make now, events on their dates)
- the local path to `index.html` and, once pushed, the **preview link**:
  `preview_base` from `site.json` + `/trips/<slug>/index.html`. Never suggest
  GitHub Pages; it's deliberately off because it would publish under the user's
  personal domain.
- how to shortlist: tap ★ on items in the report. **Copy shortlist** gives
  readable text for a trip sheet. **Export** downloads `selections.json`, which
  goes in `trips/<slug>/` for the itinerary phase.

## Ad hoc additions (follow-ups after the research)

After the main research the user will often bring individual tips: "a friend
said to try X", "is Y on my list?", "saw this café on TikTok". The goal is to
check, then **evaluate together**. Don't add anything until the user agrees.

1. **Find the trip.** Use the folder under `trips/` that matches the destination.
   If more than one could match, ask which one.
2. **Check what's already there:**
   ```bash
   python3 scripts/find.py trips/<slug> "<name>" "<local-script name>" "<alternate spelling>"
   ```
   Pass every variant you know of, including the local-script name, romanization, and
   the English name. The script reports matches, near matches, items that only
   *mention* it (e.g. a bakery named in a dish's "find it" note), and earlier
   rejections.
   - **Already in:** show the user the entry (category, tier, status, the
     key line of `why`) and stop there unless something looks stale. If its
     verification is old or its status is shaky, offer to re-check it.
   - **Only mentioned, or rejected before:** say so, quote the earlier reason, and ask
     whether they want to reconsider.
3. **If it's new, research it the same way** as the main pass, but just this one
   thing: confirm it exists and is operating (an independent source, not only
   the social post it came from), what it is, why it's distinctive here,
   cost, booking, hours or seasonality against the trip dates, and its location.
4. **Present an evaluation and wait.** Keep it short:
   - what it is and the local connection
   - status and anything time-sensitive for these dates
   - **how it compares to what's already in the catalog**: the 1–3 closest items
     (same subcategory or neighborhood), and whether it adds something they
     don't or overlaps
   - proposed category, subcategory, tier, lenses, and region/neighborhood
   - your recommendation (add, add as niche, or skip) with a one-line reason
   When the user sends several tips at once, give a compact table with one row per tip.
5. **Apply the decision:**
   - **Add:** append a full record to `data.json` with a new ID. Don't touch
     existing IDs. If research shows it's the same as an existing item under
     another name, merge into that item instead (add the alternate name to
     `local_name` or `details`). Add it to a matching `clusters` entry if one fits,
     run `build.py`, and commit.
   - **Skip:** add it to `rejected` with the reason and today's date (and
     `local_name` if known), then commit, so it isn't proposed again.

## Social & trending research

Instagram, Reels, TikTok, and regional platforms surface new, visually striking,
trend-driven places (cafés, desserts, photo spots, pop-ups, shops) months before
guides and listicles do. Use them, but with care. Most of their content is
video, much of it is behind login walls, and virality isn't quality: trending
places open and close fast, and some are photo ops with nothing behind them.

**Where to look, in order:**
1. **Search-indexed social.** Run web searches such as
   `site:tiktok.com <city> <topic>` (TikTok's public `/discover/` pages carry
   text summaries of top videos), `site:instagram.com <city> <topic>`
   (captions and location tags of public posts and reels appear in results), and
   phrasings like `<city> viral cafe 2026` or `<city> tiktok famous dessert`.
   Use the local language too.
2. **Regional platforms**, which are often richer than Instagram or TikTok for that market:
   Xiaohongshu/RedNote (小红书) for Greater China, Japan, Korea, and Southeast Asia
   (search the city's Chinese name with 小红书, 打卡, 必去, or 探店), OpenRice (HK),
   Dianping (mainland China), Tabelog and Retty (Japan), Naver Blog and Map (Korea),
   Dcard/PTT (Taiwan), Wongnai (Thailand). Pick the relevant ones in the
   orientation pass.
3. **Secondary coverage**: local media and Time Out-style pieces about what's
   viral, and Reddit or forum threads that mention places people found on social.
4. **Logged-in browser pass (opt-in only).** If a browser with the user's own
   Instagram or TikTok session is available, *ask first*. With approval, browse
   hashtag, location, and search pages for the most visual categories (cafés, desserts,
   photography, shopping, nightlife) and read captions, location tags, and
   comments. Stay read-only: never like, follow, comment, save, or post. Keep it
   light, because it's slow and platforms rate-limit.

**How to record what you find:**
- **Corroborate before including.** A trending place still needs an independent,
  non-social signal that it exists at that address and is operating: an official
  account or site, a map listing, or press. Social-only finds go in as
  `status: "unconfirmed"` at most.
- Tag the item with the `trending` lens, and in `why` say *what* is trending and
  *when* ("viral since spring 2026 for its soufflé pancakes"). Base `tier` on
  substance, not view counts.
- Add social URLs to `sources` with descriptive titles ("TikTok: @handle, 2.1M
  views", "RedNote post").
- Note practical realities in `seasonal` or `details`: queues, "photo spot
  only", timed slots, and crowds at peak hours.

## Quality standards

- Never fabricate restaurants, attractions, products, events, hours,
  coordinates, or map links. If you can't confirm something exists, leave it out;
  if it exists but current details are unknown, include it with an honest `status`.
- Prefer official sources for operational facts (hours, closures, tickets, dates).
- Separate local institutions from international chains that just have a branch here.
- Don't repeat a discovery across categories. Use one record with multiple categories.
- If research access was limited (blocked sites, few local-language results),
  say which categories are incomplete in `meta.coverage` instead of presenting
  the research as comprehensive.
- `meta.traveler.base` holds a neighborhood, not a hotel name or address,
  because the repo is public.

## Google Maps

There's no API for native Google Maps saved lists, so the default deliverable is
the My Maps import set (`mymaps/*.csv`, one per layer, staying under My Maps'
10-layer limit). Import steps are in the repo README. If the user later wants
their *shortlist* saved to a native Maps list and a browser with their Google
session is available, offer to do it for the shortlisted items only, and get
explicit approval first, because it changes their account. Never say a map or list
was created unless you actually created it.
