# Acclaim portal handler — verified reference

Verified live on Brevard County FL (2026-08-23, this repo) and Pinellas County
FL (prior recon). Everything below was observed, not assumed. All browser
steps are plain user-level actions (click, type, navigate, read the page) —
do not rely on script injection or network-tab inspection; Claude in Chrome
does not have them.

## Fingerprint

Footer text: "Acclaim, is a registered trademark of Harris Recording
Solutions". Landing page shows search tiles (Name, Book/Page, Document Type,
Record Date, Case Number, …).

## Per-county variation — discover at runtime, never hardcode

1. **Base path.** Brevard serves the app under `/AcclaimWeb/...`; Pinellas
   serves it from the domain root. Read where the search tiles link on the
   landing page. (Hardcoding `/AcclaimWeb/` produced an Acclaim error page on
   Pinellas — confirmed failure mode.)
2. **Document-type codes.** Brevard has two lis pendens codes (`LP` active,
   `LP1` legacy); Pinellas has one (`LIS PENDENS`). Enumerate by typing `LIS`
   into the Doc Type autocomplete and reading the dropdown.

## The flow (Document Type search)

1. Landing page → disclaimer panel → click **"I accept the conditions
   above."** (button text verified identical on both counties).
2. Read the banner: `Released through date: <date> | Released through Clerk
   File Number: <n> | As of <timestamp>`. The date is the query high-water
   mark; observed lag ~4 days behind today. Searching past it silently
   returns nothing.
3. Navigate to the Document Type search (tile link, e.g.
   `<base>/search/SearchTypeDocType`).
4. Type `LIS` into the Document Type autocomplete; click the desired option
   in the dropdown.

   **GOTCHA (verified):** picking a second option REPLACES the first — the
   widget looks multi-select but is not. After selecting, read the input text
   and confirm it shows exactly the code you want. To cover multiple codes
   (`LP` and `LP1`), run one search per code and merge the CSVs, deduping on
   `InstrumentNumber`.
5. Set From/To Record Date **by typing into the date textboxes**.

   **GOTCHA (verified):** setting the field values programmatically (JS) does
   not register with the widget's internal state — the search runs with stale
   criteria. Type like a user.
6. Click **Search**. Results appear in a paged grid; an export control
   appears above it.
7. Click **Export to CSV** (or navigate to `<base>/Search/ExportCsv` in the
   same session). The full result set arrives as one file — 23 rows verified
   Brevard, 64 Pinellas (prior recon).

   **GOTCHA (verified, Brevard prior recon):** a 503 was once logged while
   the file still downloaded fine. Judge success by the file's content.

## CSV schema (identical across verified counties)

```
U, DirectName, IndirectName, RecordDate, DocTypeDescription, BookType,
BookPage, InstrumentNumber, Consideration, DocLegalDescription, Comments, CaseNumber
```

| Field | Meaning |
|---|---|
| `U` | blank = released; `U` = recorded but not yet released → keep, flag provisional |
| `DirectName` | plaintiff (bank/HOA/individual). NOT the lead. |
| `IndirectName` | defendant / property owner. **The lead.** |
| `InstrumentNumber` | unique per document — the dedupe key |
| `Consideration` | always `0.0000` on lis pendens; ignore |
| `DocLegalDescription` | the only property identifier (no address, no parcel ID) |
| `CaseNumber` | e.g. `05-2026-CA-042960-XXCA-BC`; case-type token classifies the lead |

Case-type token: **`-CA-` = Circuit Civil = mortgage foreclosure;
`-CC-` = County Civil = HOA/condo lien (small-dollar, high-equity owner,
low competition — prioritized by the scorer).**

## Internals (fallback only)

The search fires: `POST <base>/search/SearchTypeDocType?Length=6` (form
fields: `DocTypes=<internal id>`, `DocTypesDisplay-input=<label>`,
`DocTypesDisplay=<internal id>`, `DateRangeList= `, `RecordDateFrom`,
`RecordDateTo`) → `GET Search/PartialGrid` → `GET Search/HasResults`
(returns literal `True`/`False`). The grid data endpoint
`POST Search/GridResults` is stateful (Telerik-style paging) — use it only if
`ExportCsv` fails twice.

Internal doc-type ids are per-county (Brevard `LP1` = `100`) — never reuse
across counties.

## Verifying a new county (required before its leads ship enriched)

1. Fingerprint + regime check (see SKILL.md Stage 0).
2. Run the flow above; pull a small recent window of lis pendens.
3. Parse 3+ legal descriptions covering different variants; construct parcel
   IDs per the county's format hypothesis.
4. Look each one up on that county's appraiser site/API and confirm an exact
   single match whose legal/subdivision matches the recorded document.
5. Only then set `"verified": true` for the county in `config/counties.json`,
   including the appraiser lookup pattern that worked.

Brevard's verified construction (6/6 exact): `{T}-{R}-{S}-{SUBID}-{BLK|*}-{LOT}`
— township may carry a letter suffix (`20G`); block segment is `*` when the
legal description has no `BLK`; nothing is zero-padded. Condo/timeshare units
and metes-and-bounds are NOT constructible → review file.
