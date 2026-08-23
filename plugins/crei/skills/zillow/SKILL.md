---
name: zillow-scraper
description: >
  Fetch property listing and Zestimate data from Zillow. Use this skill any time
  the user or agent needs Zillow property data, pricing, Zestimates, listing
  details, or search results by location. Trigger on: "look up on Zillow",
  "get Zillow data", "what's the Zestimate", "pull the listing", "check Zillow
  for", "find foreclosures on Zillow", "FSBO listings", or any request involving
  a real estate location or address and Zillow as the source.
compatibility: >
  Requires a real Chrome browser driven over CDP (claude-in-chrome or equivalent)
  on a residential connection. Datacenter IPs are blocked by Zillow's anti-bot
  layer. This skill does NOT bypass CAPTCHAs — if a challenge appears, it stops.
---

# Zillow Scraper Skill

## What this skill does and does not do

**Does:** construct Zillow search URLs deterministically from filters, load them
in a real browser, and extract structured listing data from the embedded JSON.

**Does not:** solve CAPTCHAs, rotate proxies, or evade bot detection. If Zillow
presents a press-and-hold challenge or "press & hold to confirm" wall, STOP and
report it to the user. Do not attempt to defeat it.

## Why URL construction matters

Zillow encodes all search filters in a single URL parameter, `searchQueryState`,
which is a URL-encoded JSON object. Because filters live in the URL, searches are
**constructible** — you build the URL from the user's criteria rather than
clicking filter menus. This is faster, uses fewer requests (which matters for
staying under Zillow's rate limits), and is reproducible.

**Critical reason to always pass filters explicitly:** Zillow holds filter state
in the session. Navigating to a bare path like `/32819/` after a previous FSBO
search returns FSBO results for that ZIP — the old filter silently carries over.
Always pass a complete `searchQueryState` so each query is self-contained. Never
rely on path slugs alone for anything beyond a single one-shot lookup.

---

## Search URL structure

```
https://www.zillow.com/{location-slug}/?searchQueryState={URL-encoded JSON}
```

**Location slug formats (verified):**
- `orlando-fl` — city-state
- `32819` — ZIP (use bare, no state)

**searchQueryState skeleton (before URL-encoding):**
```json
{
  "isMapVisible": true,
  "isListVisible": true,
  "filterState": {
    ...filters go here...
  }
}
```

URL-encode the whole JSON object and append as `?searchQueryState=`. Verified:
a hand-built object with price + beds + sort applied correctly on first load
(Orlando dropped to 853 results with the pills updating to match).

---

## Filter reference (verified against live Zillow, Aug 2026)

### Listing-type toggles — each is `{"value": true|false}`

| Key | Listing type |
|---|---|
| `fsba` | For sale by agent |
| `fsbo` | For sale by owner |
| `fore` | Foreclosures |
| `auc` | Auctions |
| `nc` | New construction |
| `cmsn` | Coming soon |

**To isolate one listing type, set it true and all others false.** Verified:
`fore:true` + all others `false` returned only foreclosure-labeled listings.

### Value filters

| Key | Meaning | Value shape |
|---|---|---|
| `price` | List price | `{"min":N,"max":N}` |
| `mp` | Monthly payment | `{"min":N,"max":N}` |
| `beds` | Bedrooms | `{"min":N,"max":N}` |
| `baths` | Bathrooms | `{"min":N}` |
| `sqft` | Square feet | `{"min":N,"max":N}` |
| `lot` | Lot size (sqft) | `{"min":N,"max":N}` |
| `built` | Year built | `{"min":N,"max":N}` |
| `doz` | Days on Zillow | `{"value":"7"}` |
| `sort` | Result order | `{"value":"days"}` |

`doz` accepted values: `1`, `7`, `14`, `30`, `90`, `6m`, `12m`, `24m`, `36m`.
`sort` accepted values: `days` (newest), `price` (high→low), `pricea` (low→high),
`beds`, `lot`, `size`, `paymenta`, `paymentd`.

`min`/`max` are omittable independently — `{"min":200000}` with no max is valid.

---

## Common recipes

### New foreclosures in the last 7 days (deal-finder core)
```json
{"isMapVisible":true,"isListVisible":true,"filterState":{
  "fore":{"value":true},"fsba":{"value":false},"fsbo":{"value":false},
  "nc":{"value":false},"cmsn":{"value":false},"auc":{"value":false},
  "doz":{"value":"7"},"sort":{"value":"days"}}}
```
Verified: returned 3 fresh foreclosure listings in Orlando.

### FSBO under $300k, 3+ beds
```json
{"isMapVisible":true,"isListVisible":true,"filterState":{
  "fsbo":{"value":true},"fsba":{"value":false},"nc":{"value":false},
  "cmsn":{"value":false},"auc":{"value":false},"fore":{"value":false},
  "price":{"max":300000},"beds":{"min":3}}}
```

### Newest listings, any type, last 24 hours
```json
{"isMapVisible":true,"isListVisible":true,"filterState":{
  "doz":{"value":"1"},"sort":{"value":"days"}}}
```

---

## Reading result counts — AVOID THIS TRAP

The result count appears in two places that DISAGREE:

- **Page header** (e.g. "853 results", "3 results") — strict matches. **USE THIS.**
- **Browser tab title** (e.g. "21 Homes") — includes nearby/similar results. IGNORE.

Observed live: Orlando FSBO header said 54, tab title said 46. ZIP 32819 header
said 2, tab title said 21. Always read the header count from the page, never the
tab title, or you will over-report.

**Also:** the map badge shows "504 of 4,246 homes" — Zillow caps results per map
viewport at ~500. To get all results in a dense area, you must tile the map into
sub-regions. For most queries the 500 cap is not reached; check whether the
"X of Y" numbers differ before assuming you have everything.

---

## Extracting listing data

All listing data is embedded in the page as JSON — do not scrape the rendered
DOM. Two sources:

1. **Search results:** the page's `__NEXT_DATA__` script tag, or the
   `cat1/searchResults` object in the page state, holds the list of results with
   price, beds, baths, sqft, address, and zpid for each.
2. **Single property detail:** navigate to the detail page and read
   `__NEXT_DATA__`. Path (VERIFIED live Aug 2026):
   `props.pageProps.componentProps.gdpClientCache` — this is a **stringified**
   JSON string, so parse it a second time. Then find the cache key and read
   `.property` from it.

### Cache key — CHANGED, verify at runtime

The `gdpClientCache` is an object keyed by GraphQL query names. **The key name
has changed and will change again** — do not hardcode it.

- **Old (broken):** `ForSaleShopperPlatformFullRenderQuery{...}`
- **Current (Aug 2026):** `ForSalePriorityQuery{...}`

**Robust approach:** don't match a fixed prefix. Iterate the cache keys and pick
the one whose value has a `.property` object:
```js
const cache = JSON.parse(componentProps.gdpClientCache);
const key = Object.keys(cache).find(k => cache[k] && cache[k].property);
const property = cache[key].property;
```
This survives the next rename. There is also a `zpid` directly on
`componentProps` if you just need the ID.

### Field extraction map (VERIFIED live Aug 2026)

Fields are split between the top-level `property` object and its nested
`property.resoFacts` object. Several fields moved into `resoFacts` — check both.

| Output key | Source path | Notes |
|---|---|---|
| `address` | `property.streetAddress` + `.city` + `.state` + `.zipcode` | ✓ all present |
| `price` | `property.price` | ✓ |
| `zestimate` | `property.zestimate` | often **null on foreclosures/auctions** — expected |
| `rent_zestimate` | `property.rentZestimate` | ✓ present even when zestimate is suppressed |
| `beds` | `property.bedrooms` | ✓ |
| `baths` | `property.bathrooms` | ✓ |
| `sqft` | `property.livingAreaValue` (or `.livingArea`) | ✓ both worked; prefer `livingAreaValue` |
| `lot_sqft` | `property.lotSize` | ✓ now in **square feet** (e.g. 20652) |
| `lot_acres` | `property.lotAreaValue` | acres (e.g. 0.474) |
| `year_built` | `property.resoFacts.yearBuilt` | **MOVED** — null at top level |
| `price_per_sqft` | `property.resoFacts.pricePerSquareFoot` | **MOVED** — null at top level |
| `home_type` | `property.homeType` | ✓ e.g. SINGLE_FAMILY |
| `status` | `property.homeStatus` | ✓ FOR_SALE, SOLD, PENDING |
| `days_on_zillow` | `property.daysOnZillow` | ✓ |
| `listing_url` | `property.hdpUrl` (prepend `https://www.zillow.com`) | ✓ |
| `zpid` | `property.zpid` | ✓ |
| `foreclosure_types` | `property.foreclosureTypes` | present on distressed listings |

### Fields NO LONGER on the detail query — require a second request

`taxHistory` and `priceHistory` are **absent** from the `ForSalePriorityQuery`
property object (both `undefined` when tested). Zillow now loads them via a
separate lazy GraphQL call. Do not map them from the detail page — they will
always be null.

**Implication for deal-scoring:** price-cut history and tax records are exactly
the distress signals a lead scorer wants, and they are no longer free on the
detail page. Prefer authoritative sources instead — the county tax roll (bulk
download) for tax history, and `priceHistory` via search-result deltas or a
dedicated request if truly needed. Do not build scoring on Zillow tax/price
history.

### Property detail URL — the ZPID problem (VERIFIED)

Canonical detail URLs are `/homedetails/{address-slug}/{zpid}_zpid/`. The **zpid
is an internal ID you cannot derive from an address.**

**Two slugs, only one works from an address — tested live Aug 2026:**

- `/homedetails/{address}` WITHOUT a trailing `_zpid` → **FAILS.** Zillow bounces
  it to the generic `/homes/` search page. The address slug in a `/homedetails/`
  URL is cosmetic — Zillow keys entirely off the numeric zpid and ignores the
  address text.
- `/homes/{address}_rb/` → **RESOLVES.** Zillow looks up the address, redirects
  to the canonical `/homedetails/{address}/{zpid}_zpid/`, and fills in the zpid
  itself. Verified: `/homes/1603-Rio-Cove-Court-Orlando-FL-32825_rb/` redirected
  to `/homedetails/1603-Rio-Cove-Ct-Orlando-FL-32825/46235532_zpid/` and rendered
  the full detail page.

**So `_rb/` doubles as your address→zpid lookup.** Hit `_rb/`, follow the
redirect, and read the zpid out of the final URL. This removes the earlier
limitation that you needed a search result to get a zpid.

**Ambiguity check after redirect — REQUIRED:**
- Final URL contains `_zpid/` → it's a detail page. Read the property JSON.
- Final URL is still `/homes/` or a city search → the address was ambiguous
  (missing ZIP, street exists in multiple cities). Fall back to a
  `searchQueryState` query and disambiguate from results.

**Preferred path when you already have search results:** each result includes its
`zpid` directly — build the canonical detail URL from it and skip `_rb/`
entirely. Only use `_rb/` when starting from a bare address.

**Note on distressed listings:** foreclosures and auctions frequently have the
Zestimate suppressed ("$-- Zestimate" on the live page, `zestimate: null` in
JSON). This is expected on exactly the properties a deal-finder targets — do not
treat a null Zestimate as an error, and prefer comps (e.g. HomeHarvest) for
valuation on distressed inventory.

### Field extraction map (from the `property` object)

See the verified extraction table above. Key reminders: `year_built` and
`price_per_sqft` live under `property.resoFacts`, not the top level; `taxHistory`
and `priceHistory` are no longer present on the detail query; the cache key is
discovered at runtime, not hardcoded.

---

## Output format

Compact JSON, one object per property, no null keys, no prose, no markdown fences.

```json
[
  {"address":"1603 Rio Cove Court, Orlando, FL 32825","status":"FOR_SALE",
   "price":499000,"beds":5,"baths":4,"sqft":3373,"home_type":"SINGLE_FAMILY",
   "days_on_zillow":1,"listing_url":"https://www.zillow.com/homedetails/...",
   "zpid":"12345678"}
]
```

---

## Error handling

| Situation | Action |
|---|---|
| Press-and-hold / CAPTCHA wall | STOP. Report to user. Do not attempt to bypass. |
| `__NEXT_DATA__` not found | Retry once. If still missing, report `{"error":"page_not_loaded"}` |
| 404 / property not found | Report `{"error":"listing_not_found","url":"..."}` |
| Empty results | Legitimate — widen filters. Not an error. |
| Header count ≪ tab-title count | Normal; header is correct. Not an error. |
| `X of Y` map badge differ | Result set exceeds viewport cap; tile the map if completeness matters |

---

## What NOT to do

- Do not attempt to bypass any CAPTCHA or bot-detection challenge.
- Do not rely on path slugs (`/fsbo/`, `/foreclosures/`) alone — session filter
  state leaks between navigations. Always pass a full `searchQueryState`.
- Do not read the tab-title result count — use the page header.
- Do not scrape the rendered DOM — read the embedded JSON.
- Do not include null/missing fields in output.
- Do not run high-volume sequential requests — Zillow's anti-bot layer triggers
  on rate and repetition, not on the first request. Space requests out.
