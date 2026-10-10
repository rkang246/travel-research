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

Repo: `/Users/robertkang/Desktop/Code/travel-discovery` (GitHub: `rkang246/travel-research`)

```
trips/<YYYY-MM>-<city-slug>/        e.g. trips/2026-11-tokyo/
  data.json        ← the ONLY file you write by hand (schema: references/schema.md)
  index.html       ← generated field guide (list, map, neighborhoods, table, practical)
  locations.csv    ← generated master location database
  locations.kml    ← generated, for Google Earth / My Maps
  mymaps/*.csv     ← generated, one CSV per My Maps layer (≤10 layers)
  work/            ← scratch output from research agents (gitignored)
```

`scripts/build.py` generates everything else from `data.json` and refreshes the
repo's root `index.html` and README trip list. Because the catalog, master
database, map, and neighborhood view are all rendered from the same records,
items are deduplicated by construction: a place that's both a photo spot and a
café is **one** record with `categories: ["photography", "nightlife"]`.

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

### 1. Set up
Create `trips/<YYYY-MM>-<city-slug>/` (month of arrival). If it already exists,
you're refreshing an earlier trip, so read the existing `data.json` and
**keep its IDs** for items that persist, because the user's shortlist refers to them.

### 2. Orientation pass (do this yourself)
Spend a few searches building context that every later step needs: what the
destination is known for, its food identity, main neighborhoods and their
character, design and shopping culture, local language and script, public
holidays and seasonal conditions for the dates, sunrise and sunset times, and
the best local-language publications and event calendars, and **which social
platforms locals and regional travelers actually use** there (see below). Write
these notes to `work/orientation.md`. They brief the research agents.

Also decide the things every agent must use consistently, and put them in
`orientation.md`:
- **Regions**: 3–6 coarse areas a visitor thinks in (`meta.regions`).
- **Lenses**: 2–6 cross-category interest toggles drawn from the traveler's
  interests and the city's personality (e.g. `retro`, `design`, `rainy-day`),
  plus `trending`.
- **Theme**: the report's visual identity, rooted in the place (`theme`,
  `meta.local_title`, and the `local`/`tagline` fields of `category_info`).
  See the `theme` section of `references/schema.md`. The Hong Kong prototype's
  MTR-map look, with line colours, station-sign headers, and 香港清單 as its title, is
  the bar to meet. A generic palette is a missed opportunity.

### 3. Category research (fan out)
Full coverage is ~200–300 researched items, too much for one context to do
well. If you have a subagent tool, run these **six groups in parallel**, one
agent each:

| Group | Categories |
|---|---|
| eat | `food`, `restaurants` |
| buy | `products`, `shopping` |
| walk-and-see | `neighborhoods`, `photography` |
| culture | `attractions`, `experiences` |
| outdoors | `nature`, `daytrips` |
| social-and-dated | `nightlife`, `events` |

Brief each agent with: destination, dates, traveler profile and assumptions,
the path to `work/orientation.md` (including the regions, lenses, and social
platforms chosen there), its sections of `references/categories.md`,
`references/schema.md`, the research principles above, the *Social & trending
research* section, and the quality standards below. Tell it to write a JSON array of items
to `trips/<slug>/work/<group>.json` and reply with only a short summary
(counts, gaps, anything surprising). It shouldn't return the items inline,
because the file is the hand-off. Agents should use their own category prefixes
for IDs, and when they need a venue outside their categories (for example, the
eat agent needing the department-store food hall where a sweet is sold), add it
with the right primary category anyway. You'll dedupe in the merge.

Without subagents, work through the same groups one at a time, writing each
group's file before moving on so that context stays manageable.

### 4. Merge
Combine `work/*.json` into `data.json`:
- **Dedupe** records that are the same place (same name or address). Merge their
  `categories` (keep the strongest-fit category first), union `sources`, and keep
  the richer text.
- **Cross-link**: every `where` ID on a dish or product must exist. Fix
  dangling links or turn them into `where_note`.
- **Normalize** neighborhood spellings and subcategory labels.
- **Respect earlier decisions**: on a refresh, drop anything that matches the
  trip's `rejected` list (check with `scripts/find.py`), unless its situation has
  clearly changed. In that case flag it to the user rather than silently re-adding it.
- **Balance**: scan for gaps (a category with only famous names, no local-language
  finds, everything in two neighborhoods) and do targeted extra research.

### 5. Verification pass
Prioritize checks where being wrong costs the user the most: anything
`iconic`, everything with `booking: required`, all `events`, and anything you
saw closure, move, or renovation hints for. Check official sites and recent
sources, and update `status`, `verification`, and `seasonal`.

### 6. Synthesis
- `overview`: a short orientation covering what the place is known for, its
  defining food traditions, the most interesting neighborhoods, shopping and design
  culture, what makes it different, and the seasonal notes for these dates. Keep it
  brief, since the catalog is the product.
- `clusters`: geographic groupings for the neighborhood view (e.g. "Kuramae: two
  stationery shops, a coffee roaster, a riverside photo spot"). Only group
  things that really are near each other, and don't invent walking times.
- `category_info`: for each category, a local-script `local` label, a short
  `tagline`, and a `note` wherever there's category-wide context worth a
  callout. Examples: a price key, famous places that recently closed (so
  the user stops looking for them), how trailheads are reached, seasonal
  caveats. Add a `label` override when the destination suggests a better name.
- `practical`: transit, payment, holiday closures, weather, access notes. Lists of
  booking-required, unverified, and event items are derived automatically.
- `meta.coverage`: disclose any category with thin or incomplete coverage.

### 7. Build and check
```bash
python3 scripts/build.py trips/<slug> --geocode
```
`--geocode` fills missing coordinates through OpenStreetMap Nominatim (≈1
request/sec, cached in `geocode-cache.json`) and writes them back to
`data.json` with `coord_source: "nominatim"`. Read the build output: fix every
**error**, review the warnings (missing sources, ungeocoded places, IDs that
don't resolve), and rebuild. Spot-check a few geocoded pins that look out of
place in the report's Map tab. Nominatim sometimes matches a same-named
place elsewhere, so correct or delete those coordinates.

### 8. Commit and report
Commit the trip folder and the regenerated root files locally. **Don't push**
unless the user says so, because pushing publishes to GitHub. Then tell the user:
- item counts per category and any coverage gaps
- the handful of most time-sensitive things (bookings to make now, events on their dates)
- the local path to `index.html` and, once pushed, the Pages URL
  (`pages_base` in `site.json` + `/trips/<slug>/`)
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
  because the report may be published on GitHub Pages.

## Google Maps

There's no API for native Google Maps saved lists, so the default deliverable is
the My Maps import set (`mymaps/*.csv`, one per layer, staying under My Maps'
10-layer limit). Import steps are in the repo README. If the user later wants
their *shortlist* saved to a native Maps list and a browser with their Google
session is available, offer to do it for the shortlisted items only, and get
explicit approval first, because it changes their account. Never say a map or list
was created unless you actually created it.
