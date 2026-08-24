# Tyler Self-Service handler — verified reference

Verified live on Orange County FL (2026-08-24, full flow + 3/3 parcel joins).
Tyler's CURRENT records product ("ssweb") — counties on legacy Tyler EagleWeb
are migrating to it (Orange's old `/recorder/eagleweb/` now redirects here;
its legacy site was discontinued 9/1/25). This is the vendor to expect when a
Tyler county turns out to be OPEN — Tyler ≠ automatically gated; regime is
per-deployment.

## Fingerprint

Footer "© Copyright 2014-20xx **Tyler Technologies** | Version 20xx.x.x";
URL path `/ssweb/`; entry disclaimer page at `/ssweb/user/disclaimer` whose
"I Accept" button is **gated behind a reCAPTCHA**; home page tiles ("Basic
Official Records Search", "Advanced Official Records Searching", "Property
Fraud Alert"). NOTE: the version banner alone (`Version 2025.x.x`) is NOT
distinctive — earlier research mistook it for Aumentum. Fingerprint on the
Tyler copyright + `/ssweb` path.

## The flow (Advanced Document Search) — verified Orange

1. Land on `/ssweb/user/disclaimer`. **reCAPTCHA before entry** — the user
   clicks "I'm not a robot", THEN click **I Accept** (button stays disabled
   until the box is checked). One human click per session.
2. Home → **Advanced Official Records Searching** → **Advanced Document
   Search** ("all available search fields including legal fields, parcel
   number, case number"). Note the caveat on the page: advanced fields only
   cover documents recorded **after 6/1/2008**.
3. The form has stable field IDs: `#field_selfservice_documentTypes` (type
   `LIS`, click the "Lis Pendens" autocomplete option),
   `#field_RecordingDateID_DOT_StartDate` / `..._EndDate` (MM/DD/YYYY), plus
   grantor/grantee, parcel ID, case number, and platted-legal fields if ever
   needed. Click `#searchButton`.
4. Results render as one **card per document**: Document #, type,
   recorded-at timestamp, **Grantor(s)** (plaintiffs), **Grantee(s)**
   (defendants — the leads; junior lienholders like HUD/banks appear in the
   list too), and a labeled **Legal** ("Lot: 8 Block: C    RI MAR RIDGE").
   Facet panel shows the per-type counts.
5. **Export**: click the printer-settings icon titled "Export Search
   Results" (top right of results) → "Print Options" menu → **Export as
   CSV** → downloads `SearchResults.CSV`.

## Layer B

```
python ${CLAUDE_SKILL_DIR}/scripts/tylerss_csv_to_csv.py SearchResults.CSV work/raw.csv
python ${CLAUDE_SKILL_DIR}/scripts/run_pipeline.py parse --csv work/raw.csv --county orange-fl --out work/
```

CSV layout: line 1 is a search-description preamble; line 2 is the header
(`Document #, Description, Recording Date, Grantor, Grantee, Legal`); parties
are comma-joined lists in one cell. The converter emits standard pipeline
columns (first grantee = primary defendant, rest in AllDefendants).

`legalStyle: labeled-tokens` parses `Lot:/Block:/Unit:/Tract:` labels with
the subdivision name as the trailing free text. `TS:` records are timeshares
(Disney-heavy in Orange) → review, not leads. STR-only legals
(`Section: 22 Township: 22 Range: 30`) → review as metes-and-bounds. No case
numbers and no verification flags in the export. Live Orange result: 36/44
parsed (8 review: 6 timeshares, 2 STR-only).

## Join (Orange — verified 3/3)

`joinStrategy: owner-lookup` against OCPA (`ocpaweb.ocpafl.org/parcelsearch`):

- `#OwnerName` search — a UNIQUE match jumps straight to the property card;
  the legal lives under the **PROPERTY FEATURES** tab as "Property
  Description" (e.g. `RI MAR RIDGE W/27 LOT 8 BLK C`). Card shows owner
  names, mailing address; SALES tab has history.
- **Try ALL defendants, not just the first.** Verified case: the first-named
  person owned a *different* property (cross-check refused it — working as
  designed); the entity co-defendant (an LLC) was the actual owner.
- `#Subdivision` search returns every parcel in a subdivision (paged, WITH
  an Excel export) — the fallback when owner names are ambiguous.
- Parcel format `SS-TT-RR-SSSS-BB-LLL`: block letters map to numbers
  (C → 03), lot is ×10 zero-padded (LOT 8 → 080). Once the 4-digit
  subdivision code is known (from any parcel in the sub), the ID is
  constructible — verified: NORTH PINE HILLS LOT 2 BLK C →
  `06-22-29-5978-03-020`.

## Verifying a new Tyler Self-Service county

Standard procedure (references/acclaim.md § Verifying a new county), plus:
confirm the deployment is anonymous (some Tyler counties still require
accounts — never register), note the doc-type label for lis pendens, check
the export's column set, and map that county's appraiser search + parcel
format for the cross-check.
