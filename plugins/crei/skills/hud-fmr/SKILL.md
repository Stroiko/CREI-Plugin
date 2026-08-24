---
name: hud-fmr
description: >
  Look up HUD Fair Market Rents (Section 8 / voucher rents) for a ZIP code or
  county from huduser.gov. Use whenever the user or another skill needs Section
  8 rent, FMR, Small Area FMR (SAFMR), voucher payment levels, or "what would
  HUD pay" for a property. Trigger on: "Section 8 rent", "fair market rent",
  "FMR for <zip/county>", "HUD rent", "voucher rent", "SAFMR", or any rental
  analysis needing a government rent benchmark.
compatibility: >
  Requires a browser driven by Claude (Claude in Chrome, Playwright MCP, or
  equivalent). huduser.gov is a public government site with no login, no
  CAPTCHA, and no anti-bot layer observed. No API token needed.
---

# HUD Fair Market Rent (FMR) Lookup Skill

## What this skill does and does not do

**Does:** navigate the huduser.gov FMR documentation system in a browser,
resolve a county (or metro area) to its FMR table, and extract rents by
bedroom count — including ZIP-level Small Area FMRs where they exist.

**Does not:** decide what a local housing authority will actually pay. PHAs
set payment standards at 90–110% of FMR (SAFMR areas can differ more). FMR is
the federal baseline, not a guaranteed Section 8 contract rent.

## Key facts (verified live on huduser.gov, Aug 2026)

- Current data year: **FY 2026** (FMRs are federal-fiscal-year, effective Oct 1
  of the prior calendar year).
- FMR is keyed by **bedroom count only** — Efficiency (0BR), 1BR, 2BR, 3BR,
  4BR. Baths never factor. For 5+ bedrooms HUD's convention is the 4BR rent
  + 15% per extra bedroom; report the 4BR value and note the convention.
- Two kinds of result areas:
  - **SAFMR metro** (e.g. Palm Bay-Melbourne-Titusville, FL MSA): one table of
    per-ZIP rows. Heading contains "Small Area FY 20XX Fair Market Rents".
  - **Plain FMR area** (e.g. Sebring, FL MSA via Highlands County): a single
    "FY 20XX & Final FY 20XX-1 FMRs By Unit Bedrooms" table with one row per
    fiscal year — the county-wide rent applies to every ZIP in the area.

---

## The fast path: constructible summary URL (VERIFIED)

When you know the property's **county**, skip all clicking. Build the entity id
as `{5-digit county FIPS}` + `"99999"` and GET:

```
https://www.huduser.gov/portal/datasets/fmr/fmrs/FY2026_code/2026summary.odn?fips={FIPS}99999&selection_type=county&year=2026&data=2026
```

Verified: `fips=1200999999` (Brevard County, FL = FIPS 12009) loads the Palm
Bay-Melbourne-Titusville, FL MSA Small Area FMR page directly, and
`fips=1205599999` (Highlands County, FL = 12055) loads the Sebring, FL MSA
plain FMR page. For a different fiscal year, substitute the year in all three
places (`FY2025_code/2025summary.odn?...year=2025&data=2025`).

You generally know the county from the property's city/state (the county
appraiser data or the county-records skill also carries it). If unsure of the
county FIPS, use the interactive path below instead of guessing.

## The interactive path: geography select

Entry point:

```
https://www.huduser.gov/portal/datasets/fmr/fmrs/FY2026_code/select_Geography.odn
```

(The bare page title shows a literal `$fmrtype$` placeholder — cosmetic, not an
error.) Three controls, all verified:

| Control | Name/id | Values | Submit |
|---|---|---|---|
| State listbox | `STATES` | state FIPS as float (`"12.0"` = FL) | reloads page with county list populated |
| County listbox | `fips` / `#countyselect` | 10-digit entity id, `{countyFIPS}99999` (Brevard = `1200999999`) | "Next Screen..." button → POST `2026summary.odn` |
| Metro dropdown | `cbsasub` / `#inputname` | `METRO{cbsa}M{cbsa}` (MSA) or `METRO{cbsa}N{fips}` (HMFA part) | "Select HUD FMR Area" button → POST `2026summary.odn` |

Flow: click the state option → wait for reload → select the county in
`#countyselect` → click "Next Screen...". Or pick the metro by visible name in
`#inputname` and click "Select HUD FMR Area".

## Reading the result page

Read the tables from the DOM (server-rendered HTML; no embedded JSON, no JS
required).

**SAFMR metro** — one table, header row
`ZIP Code | Efficiency | One-Bedroom | Two-Bedroom | Three-Bedroom | Four-Bedroom`,
~45 ZIP rows. Find the row whose first cell equals the target ZIP. Verified:
ZIP 32905 in Palm Bay MSA → `$1,210 / $1,410 / $1,630 / $2,220 / $2,520`.

**Plain FMR area** — table titled "FY 2026 & Final FY 2025 FMRs By Unit
Bedrooms"; use the `FY 2026 FMR` row (ignore the prior-year row). Verified:
Sebring, FL MSA → `$876 / $1,006 / $1,271 / $1,538 / $2,017`. The rest of the
page is calculation methodology — ignore it for rent lookup.

**ZIP membership check (REQUIRED in SAFMR metros):** if the target ZIP is not
in the table, you are in the wrong metro or the ZIP is unassigned (~2–3% of
ZIPs have no FMR area). Re-resolve the county before reporting anything.

## Output format

Compact JSON, zillow-skill style — no nulls, no prose:

```json
{"zip":"32905","year":2026,"area_name":"Palm Bay-Melbourne-Titusville, FL MSA",
 "source":"safmr_zip","entity_fips":"1200999999",
 "bedroom_rents":{"0":1210,"1":1410,"2":1630,"3":2220,"4":2520},
 "bedrooms":3,"selected_rent":2220}
```

`source` is one of: `safmr_zip` (ZIP row in a SAFMR metro), `county_fmr`
(plain FMR area — county-wide value used for the ZIP). `selected_rent` is
`bedroom_rents[min(bedrooms, 4)]`; when bedrooms > 4 add
`"note":"5+BR convention: 4BR + 15% per extra bedroom"`.

## Error handling

| Situation | Action |
|---|---|
| ZIP not in the SAFMR table | Wrong metro or unassigned ZIP — re-resolve county via interactive path; if still absent, report `{"error":"zip_not_in_fmr_area","zip":"..."}` |
| County not in state list | New England areas are town-based; select the metro by name from `#inputname` instead |
| Summary page shows methodology but no FMR table | Retry once; then report `{"error":"page_not_loaded"}` |
| `$fmrtype$` in page title | Cosmetic placeholder — not an error |
| FY year rolled over (new fiscal year) | Update the three year tokens in the URL; the entry page always links the current system from huduser.gov/portal/datasets/fmr.html |

## What NOT to do

- Do not present an FMR as "what Section 8 will pay" — it is the baseline for
  PHA payment standards (90–110%), not a contract rent.
- Do not use the prior-year FMR row when the current-year row is present.
- Do not guess a county FIPS — if unsure, use the interactive path.
- Do not scrape the methodology tables — only the rent tables matter here.
- Do not use bathrooms to pick the rent — FMR is bedroom-count only.
