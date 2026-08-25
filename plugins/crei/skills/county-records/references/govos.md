# GovOS Cloud Search handler — verified reference

Verified live 2026-08-24 with 3/3 parcel joins on **Dallas (DCAD), Tarrant
(TAD), Bexar (BCAD), and Denton (Denton CAD)**; Collin and Hidalgo pull-verified
(joins pending); Cameron has NO lis pendens supply in the OR index. One uniform
SPA — all open anonymous, no CAPTCHA anywhere in the verified flows. All steps
are user-level browser actions (clicks, typing, URL navigation).

**The app is uniform; the DATA is not.** Counties differ in: legal template
(dash vs comma), whether legals render in-grid or only on doc detail pages,
extra pre-parsed grid columns, party-role semantics, and doc-type URL codes.
`counties.json` records each county's answers — read its entry first.

## Fingerprint

Host `{county}.{st}.publicsearch.us`; title "Official Record Search - …";
footer "Powered By Neumo"; "Certified through MM/DD/YYYY" banner (this is the
released-through date — never search past it); Quick/Advanced search tabs;
"Property Alert" link. Sister site `kofilequicklinks.com/...` is historic
index books only — never a lead source.

## The flow (Advanced Search) — verified Dallas

1. Load `https://{county}.{st}.publicsearch.us/search/advanced`. No disclaimer
   gate, no login needed. Note the **"Certified through"** date next to the
   Recorded Date Range.
2. In **Document Types**, type `LIS` — the picker filters live. Check every
   lis pendens variant the county offers (Dallas: `LIS PENDENS` and
   `LIS PENDENS (NOTICE OF)`). Skip release/partial-release types unless
   asked. Selected types appear as removable chips.
3. Type the **Recorded Date Range** (MM/DD/YYYY) capped at the certified-through
   date, and click **Search**.
4. The results page URL is a clean GET — e.g.
   `/results?department=RP&docTypes=LPS%2CLP&recordedDateRange=20260813%2C20260820&searchType=advancedSearch`
   — so subsequent pulls can navigate straight to it (URL doc-type codes are
   per-county; record them in `counties.json` after the first search).
5. Results grid columns: Grantor, Grantee, Doc Type, Recorded Date, Doc
   Number, Book/Volume/Page, Town, **Legal Description (full text in-grid,
   labeled tokens, not truncated)**. Footer shows "1-N of N results".
   **Party semantics: Grantor = plaintiff/filer, Grantee = defendant = the
   lead** (IndirectName). Set "Results Per Page" to the maximum and use the
   pager for larger sets.
6. **Ingest by reading the grid** — transcribe every row into `work/raw.csv`
   with headers `InstrumentNumber,RecordDate,DocTypeDescription,DirectName,
   IndirectName,Town,DocLegalDescription` (Doc Number → InstrumentNumber,
   Grantor → DirectName, Grantee → IndirectName, Legal Description →
   DocLegalDescription, verbatim).
   **The "Export all Results" button is LOGIN-GATED — never register.** The
   grid is the export.
7. Optional per-record detail at `/doc/{internalId}` (click the row): all
   parties with GRANTOR/GRANTEE labels, instrument date, page count, and the
   **document image viewable anonymously** page-by-page — useful for manual
   review of survey/metes-and-bounds records. **No case numbers anywhere** in
   the index, so the `cc_case` scoring signal cannot fire in GovOS counties.

Politeness rules apply (serial requests, 2–3s between actions).

## Layer B

```
python ${CLAUDE_SKILL_DIR}/scripts/run_pipeline.py parse --csv work/raw.csv --county dallas-tx --out work/
```

`legalStyle: govos-labeled` parses the segment-structured legals:
`Subdivision - Name: {SUB} [Lot: n] [Block: b] [Township: CITY] [Reference - vol/page]`.
The parser also captures the **city** (GovOS "Township:" = municipality) —
used to disambiguate appraiser owner matches. `Survey - Name: …` legals are
metes-and-bounds equivalents → review; subdivision legals without a Lot →
review. Live Dallas result: 14/16 parsed, both reviews legitimate.

## Join (Dallas — verified 3/3)

`joinStrategy: owner-lookup` against DCAD (`dallascad.org`):

1. Owner search `https://www.dallascad.org/SearchOwner.aspx`, box
   `#txtOwnerName`, button `#cmdSubmit`. Format: full last name + at least two
   letters of the first name, "Last First" order — **the grid's Grantee is
   already in that order**. `%` is a wildcard.
2. Result rows link to `AcctDetailRes.aspx?ID={account}` (residential) or
   `AcctDetailCom.aspx?ID={account}` (commercial — entity owners often land
   here). The 17-char account often visibly encodes block/lot (e.g.
   `160065700231R0000` ↔ LT 31R) but is NOT constructible.
3. **Cross-check required** on the detail page's "Legal Desc" block: line 1 =
   subdivision name, line 2 = `BLK b LT n`. Names drift between clerk and DCAD
   ("BONNIE VIEW GARDENS NO 1" ↔ "BONNIE VIEW GARDENS #1 REPLAT", "WO SMITH" ↔
   "W O SMITH") — **lot and block are the reliable anchors**; use the record's
   city vs the result row's city column to narrow candidates first.
4. Accept only lot+block agreement; try ALL parties if the grantee misses.
   Verified cases: WO SMITH LT 11 (owner match, city narrowed 4 candidates),
   CEDAR BEND BLK 2 LT 31R (same owner's second filing), BONNIE VIEW GARDENS
   BLK F LOT 7A (entity grantee, single hit, commercial detail page). Two
   correct REFUSALS: candidates whose legals didn't match the filed lot/block
   (defendant owned a different property) shipped unenriched — never force a
   join.
5. The accepted detail page carries the full normalized-parcel-contract
   material: owner + **mailing address** (absentee signal when ≠ site
   address), market value, deed transfer date + last-deed instrument
   reference, exemptions (homestead = owner-occupied signal).

**Known join gap:** family-matter lis pendens (divorce/heirship styles) often
name parties who hold title under a different name form — those legitimately
ship unenriched after the cross-check refuses.

## Per-county variation matrix (all verified live 2026-08-24)

| County | LP types (URL codes) | Legal in grid? | Template | Extra grid columns | Parties | ~Vol/wk |
|---|---|---|---|---|---|---|
| Dallas | LIS PENDENS (`LP`), LIS PENDENS (NOTICE OF) (`LPS`) | ✓ full | dash | Town | grantor=plaintiff, grantee=lead | 16 |
| Tarrant | LIS PENDENS (`LP`) | ✓ full | **comma** (`{CITY}, Subdivision: X, Lot: n, Block: b`) | — | grantor=plaintiff (family cases: title may sit with either party) | 8 |
| Bexar | LIS PENDENS (`LIS PEN`) | ✗ (string empty) | — | **Lot, Block, NCB, County Block, Property Address** | **INVERTED: grantor=owner/lead**, grantee=plaintiff | 40 |
| Collin | LIS PENDENS (`LP`) | ✗ | dash (detail page only) | — | **undifferentiated** (every party listed as both) | ~10 |
| Denton | LIS PENDENS (NOTICE OF) (`LP`) | ✗ (Lot/Block only) | dash (detail page only) | Lot, Block | grantor=plaintiff | 4 |
| Hidalgo | LIS PENDENS + NOTICE OF LIS PENDEN (URL codes = FULL NAMES) | ✗ | dash (detail page only) | — | standard | ~2 |
| Cameron | type exists, **0 docs/year** | — | — | — | — | 0 |

Rules that fall out of the matrix:
- **Check the county's `counties.json` entry for `partyRoles`** — Bexar's lead
  is the GRANTOR; Collin's parties can't be role-split from the index at all
  (ship all parties, flagged).
- Counties with legals only on detail pages (Collin, Denton, Hidalgo): open
  each result row (`/doc/{id}`) and transcribe the Legal Description line —
  volumes are small enough that this stays cheap. Denton's grid Lot/Block
  columns allow the column-fallback without detail visits when speed matters.
- Bexar: transcribe the extra columns verbatim as CSV headers
  `Lot,Block,NCB,CountyBlock,PropertyAddress` — the parser's column fallback
  makes address+lot/block rows joinable without a legal string.
- Doc-type URL codes are per-county and inconsistent (short codes, full names,
  or truncated names) — never guess; select via the picker once and read the
  produced results URL.

## Join playbook per verified county

- **Dallas — DCAD** (`dallascad.org/SearchOwner.aspx`): owner search, then
  legal cross-check on the detail page (see § Join above).
- **Tarrant — TAD**: constructible legal-search URL
  `tad.org/search-results?searchType=LegalDescription&filter=R&query={SUB} BLOCK {b} LOT {l}`
  → exact parcel row; immune to owner-name drift. GEO ID = `{sub}-{block}-{lot}`.
- **Bexar — BCAD** (`hgo.harrisgovern.com/bexar/property/search`): phrase-refined
  ADDRESS search with the grid's Property Address column; cross-check
  lot/block/CB in the returned legal. GEO ID = `{CB}-{blk}-{lot×10}`.
- **Denton — Denton CAD** (`denton.prodigycad.com/property-search`): compound
  text search on the defendant surname; cross-check the GEO ID
  (`S{sub}-{block}-…-{lot}-…`) against the grid's Lot/Block.

## Verifying a new GovOS county

Standard procedure (references/acclaim.md § Verifying a new county), plus:
enumerate the county's lis pendens doc types in the Advanced Search picker and
record the URL codes from the results URL; determine which legal template the
county uses (dash vs comma — the parser handles both; anything else sends rows
to review, which the >30% warning will catch), whether legals render in-grid
or only on detail pages, and any extra pre-parsed grid columns; **verify the
party-role semantics** by reading 3–4 rows (who are the HOAs/lenders/taxing
units? that side is the plaintiff) and record `partyRoles` if inverted or
undifferentiated; map the county's appraisal-district owner search
(Texas: every county has a CAD — Tarrant `tad.org`, Bexar `bcad.org`, Collin
`collincad.org`, Denton `dentoncad.com`, Hidalgo `hidalgoad.org`, Cameron
`cameroncad.org`) and record its search URL + cross-check anchors in
`counties.json`.
