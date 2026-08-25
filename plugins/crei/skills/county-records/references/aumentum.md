# Aumentum Recorder — Public Access handler — verified reference

Verified live on Alachua County FL (2026-08-24, full flow + 3/3 parcel joins on
ACPA/qPublic). One ASP.NET product (Harris, "Version 2023.1.2") also runs Travis
TX (`tccsearch.org`) and Fort Bend TX (`ccweb.co.fort-bend.tx.us`) — byte-identical
UI, but those are TX and unverified (their legal format and appraisers differ).
All steps are user-level browser actions; no CAPTCHA in the verified flow.

## Fingerprint

Footer `Aumentum Recorder - Public Access Web UI, Version 20xx.x.x Copyright ©
2001 - 20xx Harris Recording Solutions`; paths under `/RealEstate/`
(`SearchEntry.aspx`, `SearchResults.aspx`). Some deployments front the search
with a disclaimer "I Accept" link; Alachua's `SearchEntry.aspx` **is** the open
search form (no gate). "Permanent Index From … to MM/DD/YYYY" banner = the
released-through date; cap the search window at it.

## The flow (SearchEntry) — verified Alachua

1. Load `…/RealEstate/SearchEntry.aspx`. If a disclaimer link appears, accept it.
2. Document Type is a **long checkbox list** (not a picker). Check every lis
   pendens variant — Alachua has `LIS PENDENS` (`LP`) and `LIS PENDENS FAMILY`
   (`LPFAM`). Skip release/amended types.
3. Type `Date Filed From` / `To` (mm/dd/yyyy) capped at the Permanent Index
   date, then click **Search** (either the floating Search button or the one at
   the form foot).
4. Results grid columns: `#`, Image, Instrument #/Book-Page, Date Filed, Date
   Recorded, Document Type, **Party Name / Reverse Party Name**, Legal
   Description, Status. All rows render on one page for small windows (18 rows
   in the verified pull); a page selector + First/Prev/Next handle larger sets.
5. **Party tags: `[R]` = plaintiff (lender/HOA), `[E]` = defendant/owner = the
   lead.** Standard orientation. A `(+)` suffix on a party or legal means more
   parties/legals exist on the document.
6. **Ingest by reading the grid** (the legals render full and untruncated). The
   "Get a Free Copy → Results List → Get Item(s) Now" option prints a report,
   but the grid already has everything. Transcribe to `work/raw.csv` with
   headers `InstrumentNumber,RecordDate,DocTypeDescription,DirectName,
   IndirectName,DocLegalDescription`: Date Filed → RecordDate, `[R]` party →
   DirectName, `[E]` party → IndirectName, Legal → DocLegalDescription.
   **Strip the trailing `(+)` from every field.** No CSV export, no case numbers.

Politeness rules apply (serial requests, 2–3s between actions).

## Layer B

```
python ${CLAUDE_SKILL_DIR}/scripts/run_pipeline.py parse --csv work/raw.csv --county alachua-fl --out work/
```

`legalStyle: name-based-subfirst` (reused from NewVision) parses the
subdivision-first legals: `{SUBDIVISION} LT n [BLK b] [PLAT/DEED BOOK x PAGE y]`
— e.g. `CAROL ESTATES LT 12 BLK B PLAT BOOK E PAGE 13`, `LINCOLN ESTATES LT 91
92 PLAT BOOK F PAGE 19`. Trailing plat/deed-book refs are ignored. Two special
cases handled by config:
- **`PIN {11 digits}` legals ARE the parcel** — `parcelId.directPattern`
  `PIN (\d{5})(\d{3})(\d{3})` + `directFormat` `{0}-{1}-{2}` reformats
  `PIN 18812010002` → `18812-010-002` for an instant join.
- **Bare `SEC n TWNSHP n RNG n`** (no lot) → review (metes-and-bounds).

Live Alachua result: 16/18 joinable (3 direct PIN + 13 named), 2 review.

## Join (Alachua — verified 3/3)

`joinStrategy: owner-lookup` against **ACPA on qPublic/Schneider**
(`qpublic.schneidercorp.com`, AppID 1081). Accept the Terms modal once.

- **Direct PIN records**: "Search by Parcel Number" (`00000-000-000`) → the
  reformatted PIN lands on the parcel report. Verified: PIN 18812010002 → owner
  QUESADA MAURILIO PINO (the LP defendant).
- **Named records**: "Search by Owner Name" (Last First) with the `[E]`
  defendant — a unique name jumps straight to the report; otherwise a results
  list. **Cross-check the report's Legal Description** (`CAROL ESTATES PB E-13
  LOT 12 BK B`) against the record's lot + block + plat book/page. Owner search
  matches loosely (auto-jumped to a different YEADON's STERLING PLACE parcel in
  the verified run — the legal mismatch correctly refused it). Accept only on
  lot/block agreement; HOA-defendant records whose title sits under a different
  name ship unenriched.

The report page carries Owner, Subdivision, Legal, Property Use, mailing
address, and Sales History → normalized parcel contract.

## Verifying a new Aumentum county

Standard procedure (references/acclaim.md § Verifying a new county), plus:
accept the disclaimer if present; enumerate the county's lis pendens checkboxes
and record the URL codes from the criteria string; **check the legal template**
— FL Aumentum is subdivision-first STR-style (this handler); **TX deployments
(Travis, Fort Bend) likely use lot/block/subdivision or abstract legals and may
need a different `legalStyle`** — confirm before trusting `name-based-subfirst`;
map the county appraiser's owner + parcel search and record the cross-check
anchors in `counties.json`. Fort Bend has a 500-result search cap — keep windows
short.
