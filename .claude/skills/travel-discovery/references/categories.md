# Research categories

Twelve categories. For each: what to look for, what each item must convey, and
the suggested `details` keys (see `schema.md`). The targets are for a large
city. They are coverage targets, not quotas: scale them to the destination and
the evidence, and never pad with weak entries to hit a number.

## Contents
1. [food](#1-food--signature-foods--drinks) · 2. [restaurants](#2-restaurants--restaurants--culinary-destinations) · 3. [products](#3-products--local-products-brands--things-to-buy) · 4. [neighborhoods](#4-neighborhoods--neighborhoods-streets--walking-areas) · 5. [shopping](#5-shopping--shopping-districts-markets--malls) · 6. [photography](#6-photography--photography--aesthetic-locations) · 7. [attractions](#7-attractions--landmarks-history-architecture--culture) · 8. [experiences](#8-experiences--unique-experiences--activities) · 9. [nature](#9-nature--nature--outdoors) · 10. [nightlife](#10-nightlife--cafés-nightlife--social-culture) · 11. [events](#11-events--seasonal-events--temporary-experiences) · 12. [daytrips](#12-daytrips--day-trips--excursions)

---

## 1. `food`: Signature Foods & Drinks
**Target 15–25 · kind `dish`**

*What* to eat and drink, independent of the restaurant. Cover famous regional
specialties, historically important dishes, street food and snacks, sweets and
baked goods, local beverages (including alcohol, coffee and tea traditions),
lesser-known but culturally meaningful foods, modern specialties with strong
local followings, and foods that are only good or only available during the trip
dates.

Each item: local-language name, what it is, why it matters here, and its flavor
profile when that helps. Fill `where` with venue IDs (and add those venues
under `restaurants`, `shopping`, etc.) or `where_note` when anywhere decent
will do. **Say explicitly** in `why` whether it's a nationwide dish or one
especially tied to this city or region.

`details`: `Flavor`, `Season` (if seasonal), `Etiquette` (if there's a way to eat it).

## 2. `restaurants`: Restaurants & Culinary Destinations
**Target 20–35 · kind `place`**

Spread across: fine dining and Michelin/guide-recognized; famous local
institutions; neighborhood favorites; small family-run places; street-food
vendors and market stalls; single-dish specialists; casual high-value spots;
unusual dining formats; bakeries and dessert shops with real local significance.

Don't over-index on fine dining, social-media popularity, or places mostly full
of tourists. In `description` name the cuisine and signature dishes. In `why`
say whether it's iconic, locally beloved, niche, or unusual. Set `cost` and
`booking` carefully because they matter more here than anywhere else. Link back
to `food` dishes by ID rather than re-explaining them.

`details`: `Signature`, `Format` (counter, standing, tasting menu…), `Queue` (typical wait if known).

## 3. `products`: Local Products, Brands & Things to Buy
**Target 10–20 · kind `product`**

Goods, brands, and design objects tied to the place, like Acne Studios ↔
Stockholm or TWEMCO flip clocks ↔ Hong Kong. Look for brands founded or
headquartered here, things designed or made in the region, craft traditions,
local skincare and cosmetics, packaged specialty foods, stationery, household
items, electronics, design objects, independent fashion labels, and important
vintage scenes. Prioritize things that are hard to buy elsewhere or are
region-exclusive.

Each item: what it is, its connection to the place, why it's desirable, and
where to buy it locally (`where` → shop IDs). Only claim a buying advantage
(price, exclusives, tax refund) if you verified it. Skip generic souvenirs
unless they have genuine regional importance.

`details`: `Founded`, `Buy at`, `Price range`, `Local advantage`.

## 4. `neighborhoods`: Neighborhoods, Streets & Walking Areas
**Target 10–20 · kind `area`**

Places where wandering *is* the experience: historic districts, beautiful
residential streets, artistic or cultural quarters, walkable shopping or
architecture streets, trendy or emerging areas, waterfronts, people-watching
hubs, pedestrian corridors. Together they should show different sides of the
city's identity. Judge each one on how good the walk is, not on how many
attractions it has.

Each item: atmosphere and character, why to go, good starting streets or
landmarks, and a few discoveries inside it (preferably as IDs of other items:
put them in `details.Inside` as names, and make sure the `neighborhood` field
of those items matches).

`details`: `Start at`, `Inside`, `Best time`, `Wander time`.

## 5. `shopping`: Shopping Districts, Markets & Malls
**Target 10–20 · kind `place` or `area`**

Treat shopping as cultural exploration: famous shopping streets, luxury
districts and department stores, independent fashion and design districts,
vintage and secondhand, flea and antique markets, night and food markets,
architecturally interesting malls, bookstores, record shops, stationery,
niche retailers, concept stores.

Each item: type of shopping, what's locally distinctive about it, specific
stores or products to seek out, and whether it's worth visiting for someone not
planning to buy anything.

`details`: `Look for`, `Non-shopper value`, `Market days` (for markets).

## 6. `photography`: Photography & Aesthetic Locations
**Target 15–25 · kind `place` or `area`**

Scout like an enthusiast photographer would. Look for street-photography
neighborhoods, architecture, visually distinctive streets, viewpoints and
skylines, geometry, symmetry and leading lines, water reflections, landscapes,
neon and atmospheric night streets, markets and candid scenes, historic
alleys, photogenic cafés, shops and interiors, and sunrise, sunset, blue-hour
or night spots. Prefer a distinctive aesthetic over Instagram popularity.

Each item: exact shooting position or area, the main visual appeal, when the
light is best (check actual sunrise and sunset times for the trip dates), and
what to shoot and from where.

`details`: `Light`, `Subjects & angles`, `Restrictions` (tripods, drones, interiors, fees).

## 7. `attractions`: Landmarks, History, Architecture & Culture
**Target 15–25 · kind `place` or `area`**

Iconic landmarks, monuments, religious and spiritual sites, museums and
galleries, architectural highlights, palaces and castles, cultural
institutions, public art, civic spaces, unusual or niche museums, places with
especially interesting history.

Each item: what makes it worth it and **who would appreciate it most** (put that
in `why`). Note closures, renovations, and timed-entry tickets in `seasonal` and
`booking`.

`details`: `For`, `Tickets`, `Closed`.

## 8. `experiences`: Unique Experiences & Activities
**Target 10–20 · kind `place`, `area`, or `event`**

Things to *do*: craft workshops, cultural performances, cooking and food
experiences, interesting guided tours, distinctive local transport, specialty
tastings, hands-on art, recreation tied to the area, and unusual
culturally rooted experiences. Prioritize what's hard to replicate elsewhere.

Fill `duration`, `cost`, and `booking`. State whether it's available on the
trip dates (in `seasonal`).

`details`: `Book via`, `Languages`, `Availability`.

## 9. `nature`: Nature & Outdoors
**Target 10–20 · kind `area` or `place`**

Major parks, botanical gardens, coast and beaches, scenic walks, hikes and
nearby trails, waterfronts, urban green spaces, natural viewpoints,
distinctive regional landscapes, and seasonal phenomena such as foliage,
blossoms, migrations, or bioluminescence, checked against the trip dates.

Each item: accessibility (how you get there), time commitment, and weather
dependence (`seasonal`).

`details`: `Access`, `Difficulty`, `Weather`.

## 10. `nightlife`: Cafés, Nightlife & Social Culture
**Target 10–20 · kind `place` or `area`**

Specialty coffee and roasters, tea houses, exceptional bakeries and dessert
cafés, cocktail bars, historic or culturally important bars, local drinking
traditions, jazz and live-music venues, nightlife districts, independent
venues, creative-community hangouts.

Set `subcategory` so the report separates places worth visiting **for the
product** (e.g. "Coffee: for the cup") from places worth visiting **for the
setting or social scene** (e.g. "Bars: for the room").

`details`: `Go for`, `Hours`, `Cover`.

## 11. `events`: Seasonal Events & Temporary Experiences
**Every worthwhile, verifiable event overlapping the dates · kind `event`**

Festivals, concerts and performances, sporting events, art exhibitions,
cultural celebrations, seasonal markets, food festivals, pop-ups,
limited-time experiences, and public holidays and what they bring (including
closures). Search local-language listings, venue calendars, and official
tourism event pages for the exact date range.

Each event needs real `dates`, a location, and at least one `source`. Don't
include expired events, and don't present an annual event as scheduled unless
this year's dates are published. If the dates aren't out yet, use
`status: "unconfirmed"` and say so in `verification`.

`details`: `Tickets`, `Venue`, `Typical crowd`.

## 12. `daytrips`: Day Trips & Excursions
**Target 5–15 · kind `daytrip`**

Historic towns, nearby cities, scenic natural areas, cultural sites, coast,
villages and rural areas, unique regional activities.

Each item: why it's worthwhile, what to do there, approximate one-way travel
time, transport considerations, and whether it's a half-day, full-day, or
overnight trip. Be explicit about how long anything far away really takes.

`details`: `One-way`, `Transport`, `Trip length`, `Do there`.
