# Data sources

Every source the plugin touches: what it provides, how it's accessed, and what was
verified live. Dates are verification dates.

## 1. County recorded documents — Acclaim portals (PRIMARY)

**Provides:** lis pendens (pre-foreclosure), tax deeds, judgments — the core
distress signal, before anything appears on consumer sites.

**Access:** browser (Layer A) on a residential IP. Anonymous after accepting the
disclaimer on Open deployments. CSV export returns the full result set in one
request.

### Brevard County, FL — VERIFIED 2026-08-23

- Landing: `https://vaclmweb1.brevardclerk.us/AcclaimWeb/` (base path `/AcclaimWeb`)
- Disclaimer → "I accept the conditions above." → search tiles
- Doc Type search: `search/SearchTypeDocType`; autocomplete input `#DocTypesDisplay-input`
- Lis pendens codes: `LP` (active — all 23 rows in test window), `LP1` (legacy, 0 rows;
  still enumerate both)
- **Autocomplete selections REPLACE, not add** — selecting a second doc type drops the
  first. Verify the input shows what you intend before searching; run codes separately
  if needed.
- Search POST body (form-encoded): `DocTypes=<internalId>&DocTypesDisplay-input=<label>&DocTypesDisplay=<internalId>&DateRangeList=%20&RecordDateFrom=M/D/YYYY&RecordDateTo=M/D/YYYY`
  (LP1's internal id observed as `100`; ids are per-county — never hardcode)
- Completion poll: `Search/HasResults` returns literal `True`/`False`
- Export: `GET Search/ExportCsv` (same session) — schema exactly as documented:
  `U, DirectName, IndirectName, RecordDate, DocTypeDescription, BookType, BookPage,
  InstrumentNumber, Consideration, DocLegalDescription, Comments, CaseNumber`
- Released-through banner present (`Released through date: 08/19/2026 | Released
  through Clerk File Number: ... | As of ...`) — lag was 4 days at verification.
  Never query beyond it.

## 2. Parcel / ownership data — county property appraiser (JOIN TARGET)

### Brevard (BCPAO) — VERIFIED 2026-08-23 — has a clean JSON API

Base: `https://www.bcpao.us/api/v1/` (same-origin from bcpao.us; works from a
browser on a residential IP; datacenter access untested — treat as Layer A).

- `GET /api/v1/search?parcel=<parcelID>` — exact match returns `totalCount: 1`;
  a **prefix** (e.g. `24-36-32-50`) returns all parcels under it (used to discover
  formats). Other filters exist (`?parcelid=` is NOT it — returns everything).
- `GET /api/v1/account/<account>` — full record: `parcelID` **plus parsed
  components** (`parcelTownship`, `parcelRange`, `parcelSection`,
  `parcelSubdivision`, `parcelBlock`, `parcelLot`), `siteAddress`, `owner`,
  `ownerNames[]`, **`mailingAddress`** (absentee/out-of-state detection),
  `saleInfo` + sales history (tenure/equity proxy), `marketValue`, `propertyUse`,
  `platBookPage`, `legalDescription`, `subdivisionName`.
- Data refresh: nightly (page shows "Data Updated <date> @ 4:20 AM EST").

**Brevard parcel-ID construction — VERIFIED on 6/6 live lis pendens rows:**

```
{T}-{R}-{S}-{SUBID}-{BLOCK or *}-{LOT}
```

- Township may carry a letter suffix (`20G`) — normal, not an anomaly.
- Section keeps its two-digit form from the legal description (`S 02` → `02`).
- Block/lot are NOT zero-padded (`1138`, not `01138`).
- **No `BLK` in the legal description → block segment is `*`** (e.g. `24-36-32-50-*-35`).
- Alphanumeric lots pass through (`LT 75H` → `75H`; `LT 3.08` → `3.08` untested).

| Variant | Legal (abridged) | Constructed | Result |
|---|---|---|---|
| Standard | LT 22 BLK 1138 … S 33 T 29 R 37 SUBID GT | 29-37-33-GT-1138-22 | ✓ exact |
| Standard | LT 82 BLK 10 … S 02 T 26 R 36 SUBID MM | 26-36-02-MM-10-82 | ✓ exact |
| Alpha block | LT 15 BLK S … S 11 T 28 R 36 SUBID 01 | 28-36-11-01-S-15 | ✓ exact |
| Township suffix | LT 1 BLK 2 … S 20 T 20G R 35 SUBID 04 | 20G-35-20-04-2-1 | ✓ exact |
| No block | LT 35 … S 32 T 24 R 36 SUBID 50 | 24-36-32-50-*-35 | ✓ exact |
| No block + alnum lot | LT 75H … S 04 T 30 R 37 SUBID UT | 30-37-04-UT-*-75H | ✓ exact |

**Not yet constructible (→ review file):** condo/timeshare units (`U D411 UW40 …
ORB 2224/1002`, often `SUBID 00` or missing S/T/R) and metes-and-bounds
(`FROM INTERSEC OF …`). Both appeared in the live sample; route to review, never
guess.

### Pinellas (PCPAO) — VERIFIED 2026-08-23 — subdivision-lookup join

- Quick Search "Sub/Condo" mode at `pcpao.gov/quick-search?qu=1`; backend POST
  `pcpao.gov/dal/quicksearch/searchProperty` (`input=<name>&searchsort=subcondo`,
  DataTables-style) → rows with parcel ID + legal + owner + site address.
- Join: subdivision NAME search, then strict block/lot match on the returned
  legal. Verified 3/3. Recorded names may be word-reordered vs PCPAO names.
- Detail page `pcpao.gov/property-details?s=<strap>` (strap = parcel ID with
  first three segments reversed, no dashes) shows mailing address + sales
  history for the parcel contract.
- Condo units NOT joinable in v1 — PCPAO condo naming diverges from recorded
  names; routed to review.

### Highlands (HCPAO) — VERIFIED 2026-08-23 — owner-lookup join

- `hcpao.org/Search?id=<owner name>` → result rows (parcel ID, owner, site
  address) linking to detail pages with full legal description, mailing
  address, sales history.
- Join: search the DEFENDANT name, cross-check the parcel's legal against the
  recorded lot/block/subdivision. Verified 3/3 (single exact matches).

### Palm Beach (PAPA) — VERIFIED 2026-08-24 — owner-lookup join (Landmark county)

- Clerk portal is **Landmark Web** (`erec.mypalmbeachclerk.com`) — full flow
  verified incl. XLSX export (93 lis pendens in one week; 92/93 parsed via the
  export's pre-parsed legal columns). One reCAPTCHA click by the user per search.
- Appraiser: PAPA (`pbcpao.gov`) — quick search `#realsrchVal` by owner name
  (last-first, matching the export's Reverse Name), address, or PCN; unique
  match lands on `/Property/Details?parcelId=<PCN>` with legal description,
  mailing address, sales history.
- Join verified 3/3 via owner search + cross-check on **lot + S/T/R** (sub
  names drift: clerk "VILLAGE AT BOCA RIO PHASE # 03" = PAPA "PH-2").
- PCN decodes as `county(00)-RR-TT-SS-sub-BBB-(lot×10)` — instant cross-check
  from the URL.

### Polk (polkflpa.gov) — VERIFIED 2026-08-24 — owner-lookup join (NewVision county)

- Clerk portal is **NewVision BrowserView** (`apps.polkcountyclerk.net/browserviewor/`) —
  no CAPTCHA; ingest via the Print Results page (tab-delimited, full legals,
  `*` = plaintiff row). 79 unique documents in one week; 74/79 parsed
  (4 were direct parcel IDs — instant joins); lis pendens codes `LP` + `L PEN`.
- Appraiser **moved domains: polkpa.org → polkflpa.gov**. Owner search
  `#searchRE_name` on `/CamaSearch.aspx`; details at
  `/CamaDisplay.aspx?...&ParcelID=<id>` with Subdivision, Mailing Address,
  Sales History.
- Join verified 3/3 (incl. a two-parcel LLC disambiguated by the lot tail —
  parcel tail encodes lot×10).
- No case numbers in the clerk grid — distress type comes from the plaintiff
  name (plaintiff-type classifier), so no scoring signal is lost.

### Orange (OCPA) — VERIFIED 2026-08-24 — owner-lookup join (Tyler Self-Service county)

- Clerk portal is **Tyler Self-Service** (`selfservice.or.occompt.com/ssweb`) —
  anonymous, but the entry disclaimer's "I Accept" is reCAPTCHA-gated (one
  user click per session). Advanced Document Search covers records after
  6/1/2008 only. Native **Export as CSV** (44 lis pendens in the test week;
  36/44 parsed — reviews were 6 Disney-area timeshares + 2 STR-only).
- Correction: earlier research classified Orange as "Aumentum JSP variant"
  from its version banner — wrong; fingerprint on the Tyler copyright +
  `/ssweb` path.
- Appraiser OCPA (`ocpaweb.ocpafl.org/parcelsearch`): owner search jumps
  straight to the property card on a unique hit; legal under PROPERTY
  FEATURES; subdivision search has an Excel export. Join verified 3/3 —
  including a case where the first-named defendant owned a different
  property (cross-check refused it) and the entity co-defendant was the true
  owner. Parcel format `SS-TT-RR-SSSS-BB-LLL` (C→03, lot×10) is
  constructible once the subdivision code is known.

### Broward — PULL-ONLY (verified 2026-08-23)

Acclaim export works (43 rows) but 0/43 lis pendens carried a legal
description — Broward does not index legals on LP docs. No CSV-based join;
leads would be names/cases only.

## 3. Zillow (current listings + rent estimate)

See `plugins/crei/skills/zillow/SKILL.md` — fully verified Aug 2026. Browser-only
(Layer A), residential IP. Not a pre-foreclosure source; used for listing-status
and rent enrichment.

## 4. HomeHarvest (comps/ARV) — DEFERRED

`pip install homeharvest` conflicts with the no-install Cowork goal; needs an
environment with realtor.com network access. Revisit post-v1.

## Out of scope

FSBO scraping, social scraping, paid/gated sources (Tyler subscriptions, Florida
BECA probate), contacting/skip-tracing/soliciting owners.
