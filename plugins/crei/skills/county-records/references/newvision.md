# NewVision BrowserView handler — verified reference

Verified live on Polk County FL (2026-08-24, full flow + 3/3 parcel joins) and
Osceola County FL (identical app, doc types enumerated). All steps are
user-level browser actions; no CAPTCHA anywhere in the flow (unlike Landmark).

**Do NOT confuse with NewVision "SearchNG"** (`nvweb.` hosts, e.g. Marion) —
that launches a ClickOnce Windows desktop app and cannot be browser-automated.

## Fingerprint

AngularJS single-page app; banner "**Verified as of MM/DD/YYYY**" under the
clerk's name; footer "© 2018 NewVision Systems Corporation. All rights
reserved"; top tabs **Search | Results | Document** with search sub-tabs
**Party | Document Type | File Number | Book/Page**; URL path `/browserview*`.

## The flow (Document Type sub-tab) — verified Polk

1. Load the landing page (no disclaimer, no gate).
2. Click the **Document Type** sub-tab. **Each sub-tab is its own independent
   form** — selections made on the Party tab do not carry over.
3. In "Search Document Types", type `LIS` to filter, then **check every
   lis pendens code** — counties differ: Polk has `LP` **and** `L PEN` (both
   labeled LIS PENDENS); Osceola has `LP` and `LPCT` (LIS PENDENS COURT).
   Ignore `A L PEN` (amended) and `L PEN DIS` (discharge) unless asked.
4. Date Range: type into the From/To boxes (`MM/DD/YYYY`; 7/30/90-day
   shortcut links exist). Keep the range at or before the "Verified as of"
   banner date.
5. Click **Search**. The app switches to the **Results** tab.
6. Results grid: one row **per party per document** — the same File# appears
   several times. A `*` in the first column marks the **From/plaintiff**
   party; unmarked rows are the **To/defendant** parties (the leads).
   Columns: Name, Date, Type, Book, Page, **Legal** (truncated in-grid),
   File#, **Status** (V/B = verified; R = replaced; C = correction; others =
   not yet verified → provisional), Flag. Footer shows "Retrieved records 1
   through N of MAX (N total)" — 1000-row cap; narrow the window if hit.
7. **Ingest via "Print Results"**: click it — a new tab renders ALL rows as a
   plain tab-delimited table with FULL untruncated legals and the `*`
   markers. Save that page's text to the working directory (e.g.
   `work/print.tsv`). There is no CSV/XLSX export in this app.

## Layer B

```
python ${CLAUDE_SKILL_DIR}/scripts/newvision_tsv_to_csv.py work/print.tsv work/raw.csv
python ${CLAUDE_SKILL_DIR}/scripts/run_pipeline.py parse --csv work/raw.csv --county polk-fl --out work/
```

The converter merges party rows into one row per document (DirectName = first
`*` party, IndirectName = first defendant, AllDefendants = the rest) and maps
Status→provisional. Parsing uses `legalStyle: name-based-subfirst`:
`{SUBDIVISION NAME} [BLK b] (LT|UN) n [trailing book/page refs]` — e.g.
`HAMMOCK RESERVE PHASE 1 LT 142`, `ALTURUS BLK 5 LT 1 & 2 BK 13102 PG 0522`,
condos `BAHAMA BAY PHASE 35 UN 35302`. Some legals ARE the parcel ID
(`23-28-23-100500-001180`) — config `directPattern` turns those into instant
joins. Live Polk result: 74/79 documents parsed (4 direct parcels; reviews
were metes-and-bounds + one county typo).

**Note:** the grid carries NO case numbers. Distress type is read from the
plaintiff NAME (the plaintiff-type classifier — association / lender /
government / individual), so the missing case number costs no scoring signal.

## Join (Polk — verified 3/3)

`joinStrategy: owner-lookup` against the Polk Property Appraiser — **domain
moved to `polkflpa.gov`** (old polkpa.org shows a redirect notice). Owner
search box `#searchRE_name` on `/CamaSearch.aspx`; result rows link to
`/CamaDisplay.aspx?...&ParcelID=<id>`. Cross-check the detail page's
**Subdivision** field + lot (the parcel tail encodes lot×10 — e.g.
`...001420` = LT 142). Owners with multiple parcels (verified case: an LLC
with 2) are disambiguated by the lot tail. Detail page carries Subdivision,
Mailing Address, Sales History → normalized parcel contract, keyed by
InstrumentNumber; direct-parcel records can be fetched by parcel ID straight
into the contract.

## Verifying a new BrowserView county

Standard procedure (references/acclaim.md § Verifying a new county), plus:
enumerate the county's lis pendens codes (they differ), confirm the Print
Results view renders (it's the only export), and record the appraiser's
owner-search URL and cross-check anchors in `counties.json`.
