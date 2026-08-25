# Appraiser bootstrap — mapping the join for a new county

The clerk portal gives you a distress record (defendant + legal). The **join**
turns that into a parcel with owner, address, and value on the county
appraiser/tax site. The clerk handler is chosen by vendor fingerprint; the
join is per-county craft. This checklist distills what verifying ~12 counties
taught, so a new county's join can be mapped and verified unattended.

The bar never changes: **3 real records resolved to single exact parcels**,
recorded in `counties.json` with date + samples, before `"verified": true`.
Until then, leads ship unenriched with a clear note.

## Step 1 — find the appraiser and recognize its platform

Search "<county> <state> property appraiser" (FL) / "tax assessor" or
"tax commissioner" (GA/TX). Ignore aggregators. Most sites are one of a few
platforms — recognizing it tells you the search modes and URL shape:

| Platform | Tells | Search by | Seen |
|---|---|---|---|
| **qPublic / Schneider** | `qpublic.schneidercorp.com/Application.aspx?AppID=…`; "Agree" terms modal | Owner, Parcel, Address | Alachua ACPA, Cherokee (GA) |
| **iasWorld** | `…/search/commonsearch.aspx?mode=realprop`; parcel format hint on the field | Parcel, Owner, Address | DeKalb Tax Commissioner |
| **Harris Govern** | `hgo.harrisgovern.com/{county}/property/search`; "Refine search for phrases" toggle | one compound box (address/owner/id) | Bexar BCAD |
| **True Prodigy** | `{county}.prodigycad.com/property-search`; "Compound Text Search" + Advanced | compound + subdivision picker | Tarrant TAD (new), Denton CAD |
| **BIS eSearch** | `esearch.{county}cad.org`; By Owner/Address/ID/Advanced tabs; reCAPTCHA badge | Owner, Address, ID | Collin CAD |
| **Custom JSON API** | `/api/v1/search?parcel=…` returns JSON | parcel / address | Brevard BCPA |
| **Legacy .aspx / page-read** | server-rendered result page | owner / strap | Pinellas PCPAO, Highlands HCPAO, Polk PA |

Accept any terms/disclaimer modal once. Note whether a reCAPTCHA gates search
(Collin) — if so, flag the county user-assisted for the join too.

## Step 2 — pick the join strategy from what the record carries

Read the record's legal (post-parse). The strongest available path wins:

1. **direct-parcel** — the record already contains a parcel ID (GovOS `PIN`,
   Aumentum `PIN`, GA Landmark `Parcel:`). Look it up by parcel. Deterministic;
   the only risks are format and existence. **Prefer this whenever present.**
2. **legal-search** — the appraiser accepts a subdivision+lot query and returns
   the exact parcel (Tarrant TAD's constructible URL
   `…searchType=LegalDescription&query={SUB} BLOCK {b} LOT {l}`). Immune to
   owner-name drift.
3. **address-search** — the record/grid carries a street address (Bexar). Use
   the appraiser's address search; cross-check lot/block in the returned legal.
4. **subdivision-lookup** — search by subdivision NAME, match block/lot
   (Pinellas). Names drift — try reordered/shortened variants.
5. **owner-lookup** — search by the DEFENDANT name, cross-check the legal
   (most counties). The default when nothing better is present.
6. **construct** — build the parcel ID string from the legal's coded parts
   (Brevard STR+SUBID). County-specific; verify the format before trusting.

Record the choice as `joinStrategy` (+ `parcelExtract`/`directPattern`/
`directFormat` for direct-parcel, `appraiser.type` + `searchUrl` for the rest).

## Step 3 — cross-check discipline (this is where joins go wrong)

- **Lot and block are the reliable anchors. Subdivision names drift** between
  clerk and appraiser ("VILLAGE AT BOCA RIO PHASE # 03" ↔ "PH-2"; "Davis Ranch"
  ↔ "McCRARY TRACT"; "WO SMITH" ↔ "W O SMITH"). Cross-check on lot/block (and
  section/township/range where present), not spelling.
- **Owner search matches loosely and will auto-jump to the wrong parcel.** A
  "YEADON JAMES" search landed on a different Yeadon's STERLING PLACE parcel;
  the legal cross-check (ROBINLANE ≠ STERLING PLACE) correctly refused it.
  **Accept only on lot/block agreement; a mismatch means refuse → ship
  unenriched.** Never force a join to hit 3/3.
- **Disambiguators when a name/legal is ambiguous:** the record's city
  (GovOS "Township:" token) narrows same-name owners; account-number encoding
  often embeds block/lot (DeKalb GEO `18 275 13 015`, Denton `SD4456A-…-0011`,
  Bexar `05752-328-0390`) for a free confirmation.
- **Try ALL parties.** The lead may be an entity co-defendant, not the first
  person named (Orange); and for family/HOA suits the title may sit with a
  spouse or a since-transferred owner. A parcel+address match still verifies
  the join even when the current owner ≠ the defendant (the transfer is useful
  distress signal).
- **Party orientation is per-vendor** — usually grantor=plaintiff,
  grantee=defendant=lead, but Bexar inverts it and Collin can't split roles
  from the index. Confirm from 3–4 rows (the HOAs/lenders/taxing units are the
  plaintiff side) and set `partyRoles` if non-standard.

## Step 4 — capture the normalized parcel contract

From the accepted parcel's detail page, record the shape `enrich.py` consumes:

```json
{"siteAddress": "…", "owner": "…",
 "mailingAddress": {"addr1": "…", "city": "…", "state": "…", "isForeign": false},
 "saleInfo": "MM/DD/YYYY …", "propertyUse": {"description": "…"},
 "marketValue": "…"}
```

Mailing ≠ site address is the absentee-owner signal; a homestead/exemption flag
is the owner-occupied signal; recent sale/deed date dates the ownership. Key
owner-lookup contracts by the record's InstrumentNumber (no parcel ID until the
lookup); direct-parcel contracts by parcel ID.

## Step 5 — record and gate

Write `appraiser` (name, type, searchUrl, parcelUrl if applicable, notes with
the exact field IDs and cross-check anchors) and `parcelId` (format, extract
pattern, `verified`, `verifiedDate`, `verifiedSamples`, and a notes line naming
the 3 verified records) to `counties.json`. Only then flip `"verified": true`.
Anything under 3/3, or any strategy that had to guess, ships unenriched and
says so.
