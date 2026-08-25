# Landmark Web handler — verified reference

Verified live on Palm Beach County FL (2026-08-24, full flow incl. export and
3/3 parcel joins), St. Johns County FL (structure identical), and **DeKalb
County GA (2026-08-24, 3/3 direct-parcel joins — see § Georgia below)**. Lee
County confirmed Landmark but sits behind an extra Akamai challenge.

**Regime and legals are per-deployment.** FL Landmark (Palm Beach) has an
on-form **reCAPTCHA** (one human click) and **pre-parsed lot/block/sub
columns**. GA Landmark (DeKalb) has **NO reCAPTCHA** (fully open after the
disclaimer) and **labeled legals that embed a direct parcel ID**. Read the
county's `counties.json` entry; the two flows diverge at steps 7 and the join.

## Fingerprint

Page title "Landmark Web Official Records Search" / "Landmark Web Home Page";
nav Home/Search/Support (+ optional "Subscriber Log On"); search tiles whose
links call `LaunchDisclaimer('searchCriteria…')`; "Property Fraud Alert" link.
Base path varies: `/LandmarkWeb` (Lee), `/Landmark` (St. Johns), domain root
(Palm Beach) — read it from the landing page, never hardcode.

## The flow (Document Type search) — verified Palm Beach

1. Landing page → click the **Document Search** tile → a **Disclaimer modal**
   appears (once per session) → click **Accept**. You land on
   `<base>/search/index?section=searchCriteriaDocuments`.
2. **Possible Akamai interstitial** (per-deployment; Lee has it, Palm Beach
   and St. Johns don't): a "Challenge Validation" page with an "I'm not a
   robot" box "Powered … by Akamai". STOP and ask the user to complete it —
   never click it yourself. If it loops or escalates, mark the county
   user-assisted-only.
3. Read the **"Instrument Number verified through <date>"** banner (right
   panel) — Landmark's released-through equivalent. Keep the date range at or
   before it.
4. **Document Type — use the picker, never type in the field.** Click
   **"select document type"** next to the Document Type field (label wording
   may vary; it's the control adjacent to the field), check **LIS PENDENS**
   in the list, click **Select**. The field then shows the code (Palm Beach:
   `LP`) and hidden id fields are set.

   **GOTCHA (verified):** typing into the field directly corrupts it
   ("LIS PENDENS,LP" → "Please select or enter a valid document type") and
   your submit will burn the CAPTCHA token on a validation error.
5. Dates: type into **Begin Date** / **End Date** (`#beginDate-DocumentType`,
   `#endDate-DocumentType`; "Last 7/30/90 Days" shortcuts also exist).
6. Result cap: the "Show first N records" dropdown defaults to 200 — raise it
   (700/3000) for wide windows in big counties; Palm Beach produced 93 lis
   pendens rows in one week.
7. **reCAPTCHA (the human step).** A "I'm not a robot" checkbox sits on the
   form. Tell the user exactly this: "Please click the I'm-not-a-robot box in
   the browser — I'll submit the moment you're done." Then click **Submit**
   immediately.

   **GOTCHAS (verified):** the token is SINGLE-USE and short-lived (~2 min).
   Make sure the form is fully valid BEFORE the user clicks; any failed
   submit consumes the token and shows "Invalid Captcha" with the box reset —
   the user must click again. Never fetch search endpoints directly; the
   token must ride the normal form submit.
8. Results grid appears (35 rows/page). Columns include **Status** (V =
   verified, R/I = provisional — keep provisional rows, flagged), Direct
   Name (plaintiff), **Reverse Name (defendant = the lead; multiple names
   stacked in one cell)**, Record Date, Location (`SS,TT,RR,`), Doc Type,
   Book/Page, Instrument #, Legal, and **pre-parsed legal columns: Lot,
   Building, Block, Unit, Subdivision, Section, Township, Range**.
9. Click **Export** → downloads an **XLSX** (`_ExportResults_<timestamp>.xlsx`,
   via `POST <base>/Search/GetSearchResultsExport`, session-stateful). Get the
   file into the working directory (Downloads folder → attach if needed).

## Layer B for Landmark counties

```
python ${CLAUDE_SKILL_DIR}/scripts/xlsx_to_csv.py work/export.xlsx work/raw.csv
python ${CLAUDE_SKILL_DIR}/scripts/run_pipeline.py parse --csv work/raw.csv --county palm-beach-fl --out work/
```

The converter handles Landmark's duplicate headers (two Location/DocLinks
columns → `_2` suffix) and strips the `legalfield_` prefixes. The parse stage
uses `legalStyle: landmark-columns` — no legal-string parsing needed; the
county pre-parsed it. The case number is extracted from the Legal text
(`Case Number: 502026CC014026XXXAMB` — `CC`/`CA` classify the case). Palm
Beach live result: 92/93 rows parsed, 88 unique defendants.

## Join (Palm Beach — verified 3/3)

`joinStrategy: owner-lookup` against PAPA (`pbcpao.gov`): type the defendant
name from Reverse Name (already LAST-FIRST order) into the quick search; a
unique match lands directly on `/Property/Details?parcelId=<PCN>`.
**Cross-check on LOT + SECTION/TOWNSHIP/RANGE, not subdivision spelling** —
names drift between clerk and appraiser ("VILLAGE AT BOCA RIO PHASE # 03" is
PAPA's "VILLAGE AT BOCA RIO PH-2"). The PCN itself decodes as
`county(00)-RR-TT-SS-sub-BBB-(lot×10)`, which makes the lot/STR check
instant from the URL alone. Detail page carries legal description, mailing
address, and sales history → normalized parcel contract, keyed by
InstrumentNumber (owner-lookup convention).

Condo units (Unit column instead of Lot) still parse and join — owner search
doesn't depend on lot/block; cross-check unit + subdivision instead.

## Georgia Landmark (DeKalb — verified 3/3)

GA Superior Court Clerks run the same Landmark app, but the deployment differs:

- **Open, no reCAPTCHA.** Flow is: Document Search tile → **Accept** disclaimer
  modal → doc-type **checkbox list** (check LIS PENDENS, click **Select**) →
  Begin/End dates → **Submit**. No human CAPTCHA step. "Clerk File Number
  verified through <date>" banner is the released-through date.
- **Ingest**: the grid shows Grantor/Grantee/Filing Date/Doc Type/Book/Page/
  Cross-References but NOT the legal. Click a row's doc-type cell for the
  detail, or use **Export** (XLSX) / **"Show all legal fields"**. Grantee =
  defendant/owner = lead. No case numbers.
- **Legals are labeled tokens with a DIRECT parcel** — the strongest join:
  `DIS:15 LAND:122 LOT:5 SUB:RENAISSANCE LAKES Parcel: 15 122 02 012 Tax
  District:04 STREETNUM:3245 STREET:DAVINCI SUFF:CT CITY:DECATUR ...`.
  `legalStyle: ga-landmark`; config `parcelId.parcelExtract` pulls the Parcel
  for a direct join, and `parse_legal_ga_landmark` extracts SUB/LOT/BLK as the
  fallback for the rare record with no Parcel.
- **Join = direct-parcel** on the county tax/appraiser site. DeKalb: DeKalb Tax
  Commissioner (`publicaccess.dekalbtaxga.gov`, iasWorld), Parcel ID field
  format `12 123 12 123` (with spaces). Verified 3/3: 15 122 02 012 → HOWARD
  KIMBERLY NICOLE (defendant is current owner), 15 131 08 026 → FALL BRIDGET,
  18 275 13 015 → 3230 OSBORNE RD (owner transferred post-filing — parcel +
  address still verify; the owner change is useful distress signal).
- **Cobb + Cherokee** are the same app (candidates in `counties.json`) but
  their parcel format and appraiser differ — set each county's `parcelExtract`
  and verify before trusting.

## Verifying a new Landmark county

Same procedure as Acclaim (references/acclaim.md § Verifying a new county):
pull a small window, then resolve 3+ records to single exact parcels on that
county's appraiser before setting `"verified": true`. Landmark-specific
additions: note the base path, whether an Akamai interstitial fires, the
doc-type code for lis pendens (via the picker), and whether the export's
structured legal columns are populated (Palm Beach: yes, 92/93).
