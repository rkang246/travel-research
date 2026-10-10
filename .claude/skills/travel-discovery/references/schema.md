# `data.json` schema

`trips/<slug>/data.json` is the **single source of truth** for a trip. The HTML
report, CSVs, and KML are all generated from it by `scripts/build.py`, so the
catalog, master database, map, and neighborhood view can never disagree with
each other. Edit `data.json`; never hand-edit generated files.

## Top level

```json
{
  "meta": { ... },
  "theme": { ... },
  "category_info": { "food": { ... } },
  "lenses": [ { "id": "...", "label": "...", "hint": "..." } ],
  "overview": [ { "heading": "...", "text": "..." } ],
  "items": [ { ... } ],
  "clusters": [ { "name": "...", "summary": "...", "ids": ["..."] } ],
  "practical": [ { "heading": "...", "items": ["..."] } ]
}
```

## `meta`

| Field | Type | Notes |
|---|---|---|
| `destination` | string, required | "Tokyo" |
| `country` | string, required | "Japan" |
| `slug` | string, required | Same as the folder name: `YYYY-MM-city`, e.g. `2026-11-tokyo` |
| `arrive`, `depart` | `YYYY-MM-DD`, required | |
| `generated` | `YYYY-MM-DD`, required | Date the research was done. Freshness depends on it. |
| `local_language` | string | "Japanese" |
| `local_title` | string | Big local-script title at the top of the report, e.g. `"香港清單"`, `"東京図鑑"`. Omit for destinations whose language uses Latin script, unless a local word adds character. |
| `regions` | string[] | Display order for the coarse **region** filter, e.g. `["HK Island", "Kowloon", "New Territories", "Islands"]`. 3–6 regions that a visitor would think in. |
| `traveler` | object | `base` (accommodation, **neighborhood only**: the report may be public), `interests`, `budget`, `pace`, `transport`. Omit unknown keys. |
| `assumptions` | string[] | Every preference you assumed rather than were told. |
| `coverage` | `{category, note}[]` | Honest gaps, e.g. `{"category": "events", "note": "Few English listings for late Nov; local-language calendars only partly checked."}` |

## `items[]`: one record per discovery

| Field | Type | Notes |
|---|---|---|
| `id` | string, required, unique | See **IDs** below. |
| `name` | string, required | English or commonly used name. |
| `local_name` | string | Local script / language name, when one exists. |
| `kind` | enum, required | `place` (a venue or site with an address) · `area` (neighborhood, street, park, district) · `dish` · `product` · `event` · `daytrip` |
| `categories` | string[], required | First entry is the **primary** category (where the full card is shown); others cross-list it. Values: `food`, `restaurants`, `products`, `neighborhoods`, `shopping`, `photography`, `attractions`, `experiences`, `nature`, `nightlife`, `events`, `daytrips` |
| `subcategory` | string | Free text, used to group cards inside a category ("Street food", "Michelin", "Vintage", "Sunset viewpoints"). Keep the wording consistent within a category. |
| `region` | string | Coarse area, one of `meta.regions`. Fill it for every geographically identifiable item, including day trips. |
| `neighborhood` | string | Use one consistent spelling per neighborhood across all items. |
| `lenses` | string[] | IDs from top-level `lenses` that apply, e.g. `["retro", "trending"]`. |
| `address` | string | Full street address for `place`; a representative point/description for `area`. Omit for dishes/products. |
| `lat`, `lng` | number | **Only** if they come from a source you actually read (official site, Wikipedia, OSM) or from `build.py --geocode`. Never estimate. |
| `coord_source` | string | `source` · `nominatim` · `manual`. Set automatically when geocoding. |
| `maps_url` | string | Optional. A real Google Maps URL you saw. Otherwise leave it out: the build generates a Maps *search* link from name + address, which is safe because it can't point to the wrong pin. |
| `website` | string | Official site. |
| `description` | string, required | 1–3 sentences: what it is. Paraphrase sources, don't copy them. |
| `why` | string, required | Why it's distinctive *here*: the local connection. |
| `tier` | enum, required | `iconic` · `strong` · `niche` (interest-dependent, not "worse") |
| `cost` | enum | `free` · `$` · `$$` · `$$$` · `$$$$` (relative to local prices) |
| `duration` | string | "30–60 min", "2–3 h", "half day" |
| `best_time` | string | Time of day / day of week / lighting. |
| `setting` | enum | `indoor` · `outdoor` · `mixed` |
| `booking` | enum | `none` · `recommended` · `required` |
| `seasonal` | string | How the trip dates affect it ("persimmon season peaks in Nov", "closed Mondays + Nov 23 holiday"). |
| `dates` | object | Events only: `{"start": "YYYY-MM-DD", "end": "YYYY-MM-DD", "note": "evenings only"}` |
| `status` | enum, required | `verified`: operating status/details confirmed from an official or recent source. `reputation`: real and well-regarded but current details not re-checked. `unconfirmed`: couldn't confirm it's operating / happening. `possibly-closed`: signals of closure, moving, or renovation. |
| `verification` | string | What you checked and when, or what's uncertain. |
| `sources` | `{title, url}[]` | URLs you actually read. Events **must** have at least one. |
| `where` | string[] | For `dish` / `product`: IDs of venue items where to find it. Each target must exist as its own item. |
| `where_note` | string | Free-text guidance when no specific venue fits ("any depachika food hall"). |
| `details` | object | Category-specific key→string pairs (see `categories.md`), e.g. `{"Light": "Blue hour", "Angles": "...", "Restrictions": "No tripods"}`. |

### Example

```json
{
  "id": "food-monjayaki",
  "name": "Monjayaki",
  "local_name": "もんじゃ焼き",
  "kind": "dish",
  "categories": ["food"],
  "subcategory": "Regional specialties",
  "description": "A runny, griddle-cooked batter of dashi, cabbage and fillings scraped up with tiny spatulas as it crisps.",
  "why": "A Tokyo-born shitamachi dish closely tied to Tsukishima's Monja Street; rarely done well outside the city.",
  "tier": "strong",
  "cost": "$$",
  "where": ["rest-tsukishima-monja-street"],
  "where_note": "Most shops on Tsukishima's Nishi-Naka-dori; expect queues on weekend evenings.",
  "status": "reputation",
  "sources": [{"title": "GO TOKYO: Monja Street", "url": "https://..."}]
}
```

## `theme`: the destination's visual identity

The report should look like it belongs to the place. The Hong Kong prototype
used the MTR map: each category is a "line" in a real MTR line colour, and
condensed type evokes station signage. Pick a motif with a similar local root:
a transit map's line colours (Tokyo Metro, London Underground), street-sign or
tile palettes (Lisbon azulejo blues), a flag, or a landmark material. Record it
in `motif` so it's clear why the colours were chosen.

```json
"theme": {
  "motif": "MTR map: each category is a line in a real MTR line colour",
  "fonts": { "display": "Barlow Condensed", "body": "Barlow", "local": "Noto Sans HK" },
  "google_fonts": "family=Barlow:wght@400;500;600;700&family=Barlow+Condensed:wght@500;600;700&family=Noto+Sans+HK:wght@500;700;900",
  "colors": { "food": "#e2231a", "attractions": "#0075c2", "nature": "#00a04a", "accent": "#0075c2" },
  "colors_dark": { "attractions": "#2c95e0" }
}
```

| Field | Notes |
|---|---|
| `fonts` | Roles `display` (titles and signs; a condensed or characterful face), `body` (readable text), `local` (a font that covers the local script, such as Noto Sans JP/KR/TC/HK/SC/Thai). Plain family names only. |
| `google_fonts` | The query string for `https://fonts.googleapis.com/css2?…`, covering every family above, with **weights that family actually offers** (check fonts.google.com). The build warns if the request fails. Omit it to use system fonts. |
| `colors` | `#rrggbb` per category key, plus optional `accent` (links). Category colours sit behind **white** sign text, so each needs ≥ 3:1 contrast with white. The build warns when one doesn't, so darken it rather than ignore the warning. Unlisted categories keep the defaults. |
| `colors_dark` | Optional overrides for dark mode, for colours that turn muddy on a near-black background. |

## `category_info`: per-category signage and notes

```json
"category_info": {
  "food":   { "local": "食", "tagline": "Dim sum to dai pai dong", "note": "Price key: $ under ~HK$100/head … Recently closed: …" },
  "nature": { "label": "Hikes", "local": "行山", "tagline": "December is peak hiking season" }
}
```

| Field | Notes |
|---|---|
| `local` | Short local-script label shown in the category sign (1–3 characters works best). |
| `label` | Optional override of the English category name, when the destination calls for it ("Hikes" instead of "Nature & Outdoors"). |
| `tagline` | One short line under the category name. |
| `note` | A 1–3 sentence callout under the sign. Use it for context that applies to the whole category: price key, notable recent closures to skip, how trailheads are reached, seasonal notes. |

## `lenses[]`: cross-category interest toggles

Lenses are toggle chips that cut across categories, like the Hong Kong
prototype's "Retro HK" toggle. Derive them from the traveler's interests and
from the destination's personality, e.g. `retro`, `design`, `rainy-day`,
`late-night`, `free`. Always include `trending` when social research turned up
items (see SKILL.md).

```json
"lenses": [
  { "id": "retro", "label": "Retro HK", "hint": "Bing sutts, tong lau, last-of-their-trade craftsmen" },
  { "id": "trending", "label": "Trending", "hint": "Currently popular on Instagram / TikTok / RedNote" }
]
```

`label` is shown both on the toggle and as the tag on each item, so make it a
short noun phrase. 2–6 lenses is the sweet spot.

## IDs

`<prefix>-<slug-of-name>`: lowercase ASCII, hyphens only, stable across re-runs
so that a user's shortlist still matches after the research is refreshed.

| Primary category | Prefix |
|---|---|
| food | `food` |
| restaurants | `rest` |
| products | `prod` |
| neighborhoods | `hood` |
| shopping | `shop` |
| photography | `photo` |
| attractions | `sight` |
| experiences | `exp` |
| nature | `nat` |
| nightlife | `night` |
| events | `event` |
| daytrips | `trip` |

Add a disambiguating suffix on collision (`rest-ichiran-shibuya`).

## `clusters[]`

The neighborhood-oriented summary (output section E). One per meaningful
geographic cluster: `name`, a 1–2 sentence `summary` of what's there, and
`ids` of the member items. Only group things that are genuinely in the same
area, and don't state walking times you didn't verify.

## `practical[]`

Free-form notes for output section F, as `{heading, items[]}` blocks
(transit passes, holiday closures, payment norms, weather). The report
**automatically** derives booking-required, booking-recommended, event-date,
and unverified lists from the item fields, so don't repeat those here.
