# Travel Discovery

In-depth destination research catalogs. Each trip has a large, filterable field
guide covering foods, restaurants, local brands, neighborhoods, shopping, photo spots,
landmarks, experiences, nature, cafés and nightlife, events on the exact dates,
and day trips. Each one also has a Google My Maps import set.

**Discovery first, itinerary later.** The research doesn't prune anything to fit
a schedule. You star favorites in the report, export the shortlist, and an
itinerary step works from that.

## Trips

<!-- TRIPS:START -->
| Trip | Dates | Items | Report | Data |
|---|---|---|---|---|
| _no trips yet_ | | | | |
<!-- TRIPS:END -->

The **Report** links open the rendered page on GitHub Pages. If you click an
`index.html` inside GitHub's file browser instead, you'll only see its source code.

## Running a research pass

Open Claude Code in this repo and run:

```
/travel-discovery Tokyo 2026-11-20 2026-11-27 staying in Kuramae; into coffee, stationery, street photography
```

Only the destination and dates are required. Anything else is assumed and listed
under *Assumptions* in the report. The skill lives in
[`.claude/skills/travel-discovery/`](.claude/skills/travel-discovery/SKILL.md).

## Layout

```
trips/<YYYY-MM>-<city>/
  data.json        source of truth (all research records)
  index.html       field guide: Overview · Catalog · Map · Neighborhoods · Table · Practical
  locations.csv    master location database
  locations.kml    pinned locations, foldered by category
  mymaps/*.csv     one file per Google My Maps layer
  selections.json  (you add this) your exported shortlist
scripts/build.py   regenerates everything from data.json
```

Rebuild after editing a trip's data:

```bash
python3 scripts/build.py trips/2026-11-tokyo --geocode
```

## Viewing reports on GitHub Pages

One-time setup, after the first push: in the repo on GitHub, go to **Settings →
Pages → Build and deployment**, choose **Deploy from a branch**, then select `main` / `/ (root)`.
Because `rkang246.github.io` uses the custom domain `robertqkang.com`, reports
are served at `https://robertqkang.com/travel-discovery/trips/<slug>/`. That
base URL is set in [`site.json`](site.json).

> **Privacy:** Pages sites from a public repo are public, and so are the trip
> dates in them. Reports only record your base neighborhood, never a hotel. To
> keep a repo private and still use Pages, you need GitHub Pro. Otherwise, open
> `index.html` locally.

## Importing into Google My Maps

1. Go to [mymaps.google.com](https://www.google.com/mymaps) → **Create a new map**.
2. For each file in `trips/<slug>/mymaps/` (there are up to 9 of them, which fits My Maps' 10-layer limit):
   **Add layer** → **Import** → upload the CSV.
3. When asked for placemark positions, pick **Latitude / Longitude** if every row
   has them. Otherwise pick **Location**, which is the address. Use **Name** as the title.
4. Style each layer by color, or use *Style by data column → Tier* to separate
   iconic, strong, and niche items.

`locations.kml` also opens directly in Google Earth.

## Shortlist → itinerary hand-off

In a report, star (☆) the items you want, then click **Export shortlist**.
Save the downloaded file as `trips/<slug>/selections.json`. It contains
the item IDs, which match `data.json`, so an itinerary step can read
`data.json` and `selections.json` together and plan routes, opening hours, and
travel time. Stars are saved in your browser per trip. IDs stay stable when a
trip's research is refreshed.
