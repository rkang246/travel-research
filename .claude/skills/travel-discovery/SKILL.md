---
name: travel-discovery
description: In-depth destination research that builds a large, filterable discovery catalog for a trip covering signature foods, restaurants, local brands and products, neighborhoods, shopping, photo spots, landmarks, experiences, nature, cafés and nightlife, events on the exact travel dates, and day trips. It saves everything to the travel-discovery repo as data.json, an HTML field guide with a map and shortlist, and Google My Maps CSVs. Use this whenever the user names a destination they're visiting (with or without dates) and wants to know what to eat, see, buy, photograph, or do there, asks to "research" a city or trip, or wants a travel brainstorm, field guide, or map of places, even if they never say "discovery". Not for day-by-day itineraries or route optimization from an existing shortlist; that's a separate later phase.
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

Repo: `/Users/robertkang/Desktop/Code/travel-discovery` (GitHub: `rkang246/travel-discovery`)

```
trips/<YYYY-MM>-<city-slug>/        e.g. trips/2026-11-tokyo/
  data.json        ← the ONLY file you write by hand (schema: references/schema.md)
  index.html       ← generated field guide (catalog, map, neighborhoods, table, practical)
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
   reputation, and paraphrase sources rather than copying review text.
4. **Current and date-aware.** Use the actual dates to check seasonal foods,
   weather-dependent experiences, events, public holidays and closures, places
   that closed or moved, seasonal hours, renovations, and required
   reservations, tickets, or permits. Record what you confirmed and what you
   didn't in each item's `status` and `verification`.
5. **No premature itinerary.** No "Day 1 / Day 2". Make everything filterable
   instead, through the item fields (category, subcategory, neighborhood, tier,
   cost, duration, setting, booking, seasonal), which the report turns into
   filters.

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
the best local-language publications and event calendars. Write these notes
to `work/orientation.md`. They brief the research agents.

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
the path to `work/orientation.md`, its sections of
`references/categories.md`, `references/schema.md`, the research principles
above, and the quality standards below. Tell it to write a JSON array of items
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
- how to shortlist: star items in the report, then **Export shortlist** →
  save as `trips/<slug>/selections.json` for the itinerary phase

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
