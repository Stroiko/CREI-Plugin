# GovOS Cloud Search handler — verified reference

Verified live on Dallas County TX (2026-08-24, full flow + 3/3 parcel joins on
DCAD). One uniform SPA covers Dallas, Tarrant, Bexar, Collin, Denton, Hidalgo,
and Cameron TX — all open anonymous. All steps are user-level browser actions
(clicks, typing, URL navigation); no CAPTCHA anywhere in the verified flow.

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

## Verifying a new GovOS county

Standard procedure (references/acclaim.md § Verifying a new county), plus:
enumerate the county's lis pendens doc types in the Advanced Search picker and
record the URL codes from the results URL; confirm the grid shows the same
labeled-token legal format (the parser is format-strict — a county with a
different legal template will send everything to review, which the >30%
warning will catch); map the county's appraisal-district owner search
(Texas: every county has a CAD — Tarrant `tad.org`, Bexar `bcad.org`, Collin
`collincad.org`, Denton `dentoncad.com`, Hidalgo `hidalgoad.org`, Cameron
`cameroncad.org`) and record its search URL + cross-check anchors in
`counties.json`.
