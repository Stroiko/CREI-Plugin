---
name: county-records
description: >
  Use when the user wants motivated-seller or distressed-property leads,
  pre-foreclosure records, lis pendens filings, HOA/condo lien cases, tax
  deeds, county official-records searches, or a scored/ranked lead list for a
  county. Trigger on: "find motivated sellers", "pull pre-foreclosures",
  "lis pendens in <county>", "distressed leads", "who's getting foreclosed",
  "HOA lien cases", "score these leads".
compatibility: >
  Requires (1) a real Chrome browser driven by Claude (Claude in Chrome or
  equivalent) on a residential connection — county portals and appraiser sites
  may block datacenter IPs; and (2) a Python 3 code-execution environment for
  the bundled scripts (stdlib only, no pip installs).
---

# County Records — Motivated-Seller Lead Pipeline

## What this does

Pulls fresh distress filings (lis pendens and similar) from a county's official
records portal, parses each record's legal description into a parcel ID, joins
county appraiser ownership data, and produces a **ranked, explainable lead
list**. Every score is a sum of named signal contributions from
`config/scoring.json` — "why did this score 87?" always has an exact answer.

**Hard boundaries — never violate:**
- Produce the list and STOP. Never contact, skip-trace, or solicit property
  owners, and never build output designed for automated outreach.
- Never create accounts, log in with stored credentials, or enter payment on
  any county site. If a portal requires login, tell the user and stop.
- Records name individuals in financial distress. Keep all pulled files in the
  working session; never commit them to a repo or paste them into chat beyond
  the summary the user asked for.

## Pipeline at a glance

| Stage | Where | What |
|---|---|---|
| 0. Route | — | Find the county in `config/counties.json`; unknown → vendor router |
| 1. Pull | Browser | Acclaim portal → doc-type search → CSV export |
| 2. Parse | Python | `run_pipeline.py parse` → parcel IDs (or lookup list) + review file |
| 2b. Lookup | Browser+Python | `joinStrategy: subdivision-lookup` counties only: appraiser sub search → `run_pipeline.py match` |
| 3. Enrich | Browser | Fetch each parcel's appraiser record → normalized contract |
| 4. Score | Python | `run_pipeline.py score` → ranked CSV/JSON + summary |

The county's `joinStrategy` decides how a record becomes a parcel ID:
**`construct`** (e.g. Brevard) builds the ID from the legal description string;
**`subdivision-lookup`** (e.g. Pinellas) searches the appraiser by subdivision
NAME and matches block/lot; **`owner-lookup`** (e.g. Highlands) searches the
appraiser by the DEFENDANT'S NAME and accepts a parcel only when its legal
description cross-checks against the recorded lot/block/subdivision. All three
are live-verified; the county entry says which applies.

Scripts live at `${CLAUDE_SKILL_DIR}/scripts/`, configs at
`${CLAUDE_SKILL_DIR}/config/`. Work in a scratch directory; suggested layout:
`work/raw.csv`, `work/parsed.json`, `work/review.csv`, `work/parcels.json`,
`work/leads.csv`.

## Stage 0 — Route the county

Look up the county in `config/counties.json`.

- **Found, `"verified": true`** → follow its entry (base URL, doc-type codes,
  parcel ID format). Proceed to Stage 1.
- **Found, `"verified": false`** → the portal flow works but the parcel-ID
  join is unverified there. Tell the user leads will ship without appraiser
  enrichment unless you verify 2–3 parcel constructions first (see
  `references/acclaim.md` § Verifying a new county).
- **Not found** → run the vendor router below, then offer to proceed (Acclaim
  open) or explain the limitation (gated/unknown vendor).

### Vendor router

Load the county's official records search page (find it via the county clerk's
website) and fingerprint:

| Vendor | Fingerprint | Automatable? |
|---|---|---|
| Acclaim (Harris) | Footer: "Acclaim, is a registered trademark of Harris Recording Solutions" | Yes, if open — this skill |
| Tyler Eagle | `countygovernmentrecords.com` or Tyler footer | No — login-gated; user must register themselves |
| Kofile / Catalis / i3 Verticals | vendor branding | Not supported yet |

Then detect the **access regime** (per deployment, not per vendor): if
accepting the disclaimer reaches a search form anonymously, it's open. If the
entry path bounces to a mandatory login, it's gated — say so upfront and stop;
at most drive the search after the user logs in themselves.

## Stage 1 — Pull the records (Acclaim, browser)

Follow `references/acclaim.md` for the verified step-by-step flow, endpoints,
and known gotchas. Summary:

1. Load the county's landing page; **discover the base path** from where the
   search tiles link (`/AcclaimWeb/...` on some counties, domain root on
   others — never hardcode).
2. Accept the disclaimer ("I accept the conditions above.").
3. Read the **released-through date** from the banner. Cap the search range at
   it — querying past it returns silently empty results.
4. Open Document Type search. Enumerate lis pendens codes by typing `LIS` into
   the autocomplete and reading the options (e.g. Brevard: `LP`, `LP1`).
   **The autocomplete REPLACES the selection instead of adding** — verify the
   input shows exactly what you intend; run multiple codes as separate
   searches if needed.
5. Set the date range **by typing into the date fields** (setting values via
   JavaScript does not register with the widget), then Search.
6. Confirm results loaded, then click the **Export to CSV** button on the
   results grid (equivalently: navigate to `Search/ExportCsv` relative to the
   base path in the same session — the browser downloads the file). Judge
   success by the downloaded file's content, not by HTTP status or error
   noise. Zero results with codes-you-verified is legitimate (try a wider
   window), not an error.
7. Get the CSV into the working directory. In Cowork the download lands in the
   user's Downloads folder — ask the user to attach it to the session if you
   cannot read it directly. Do not proceed on a partial grid scrape when the
   export exists.

**Politeness rules (county government servers):** serial requests only, 2–3s
between actions, never re-pull data you already have this session, stop and
report rather than retry-loop on repeated errors.

## Stage 2 — Parse legal descriptions

```
python ${CLAUDE_SKILL_DIR}/scripts/run_pipeline.py parse \
    --csv work/raw.csv --county brevard-fl --out work/
```

Writes `work/parsed.json`, `work/review.csv` (records that could not be
parsed — condo/timeshare units, metes-and-bounds, unexpected tokens), and the
Stage-3 worklist: `parcel_ids.txt` for construct counties, `lookups.txt`
(subdivision names) for lookup counties. **Review rows are never dropped**;
mention their count and reasons to the user. Condo-heavy counties legitimately
send many rows to review; the script only warns when >30% fail for
*unexpected* reasons — if it warns, stop and investigate.

### Stage 2b — subdivision lookup (lookup counties only)

For each name in `lookups.txt`, run the appraiser's subdivision/sub-condo
search in the browser (Pinellas: Quick Search → "Sub/Condo" mode). **Recorded
names may be word-reordered vs the appraiser's names** ("EDGEWATER SECTION OF
SHORE ACRES" is filed as "SHORE ACRES EDGEWATER SEC") — if a name returns
nothing, try reordered/shortened variants; that judgment is yours. Save all
result rows as `work/subdivisions.json`:
`{ "<name as it appears in lookups.txt>": [{"pid": "...", "legal": "..."}] }`
— then:

```
python ${CLAUDE_SKILL_DIR}/scripts/run_pipeline.py match \
    --parsed work/parsed.json --subdivisions work/subdivisions.json --out work/
```

Matching is strict (exact lot token + block agreement + exactly one
candidate); unmatched records ship unenriched rather than mis-joined.

### Stage 2c — owner lookup (owner-lookup counties only)

For each name in `work/owners.txt`, search the appraiser by the defendant's
name (Highlands: `https://www.hcpao.org/Search?id=<name>`). For each candidate
parcel, open its detail page and **cross-check the legal description** against
the record's lot/block/subdivision (names may be abbreviated differently —
"SUN'N LAKES EST SEB UNIT 12" vs "SUN N LAKE EST OF SEBRING UNIT 12" — the
LOT and BLK numbers are the reliable anchors). Accept only a match where lot
and block agree; zero or ambiguous candidates ship unenriched. Because you're
already on the accepted parcel's detail page, record its normalized parcel
contract (Stage 3) immediately, keyed by the record's **InstrumentNumber** in
`work/parcels.json` — owner-lookup records have no parcel ID until this step.

## Stage 3 — Enrich from the appraiser (browser)

For each parcel ID in `work/parcel_ids.txt`, fetch the county appraiser
record per the `appraiser` entry in `counties.json` and record it in the
**normalized parcel contract** — the shape `enrich.py` consumes for every
county:

```json
{"siteAddress": "…", "owner": "…",
 "mailingAddress": {"addr1": "…", "city": "…", "state": "…", "isForeign": false},
 "saleInfo": "MM/DD/YYYY …", "propertyUse": {"description": "…"},
 "marketValue": "…"}
```

- **Brevard (JSON API):** navigate to
  `https://www.bcpao.us/api/v1/search?parcel=<id>` (read the account number),
  then `https://www.bcpao.us/api/v1/account/<account>` — the response already
  IS the contract shape (a superset).
- **Pinellas (page-read):** open
  `https://www.pcpao.gov/property-details?s=<strap>` — the strap is the
  parcel ID with its first three segments REVERSED, then concatenated without
  dashes (verified: `28-30-16-71496-001-0040` → `163028714960010040`); the
  subdivision search results also link each parcel's details page directly.
  Read Owner Name,
  Site Address, Mailing Address, most recent sale date, and Property Use off
  the page into the contract yourself.

Serial navigation, ~1–2s apart.

Collect results into `work/parcels.json` as `{ "<parcelID>": <account JSON> }`.
**Only an exact single match (`totalCount: 1`) counts.** Zero matches OR
multiple matches (e.g. a subdivided lot — `…-85` matching 85, 85.01, 85.02…,
common when the legal description has a `BEG @`/`FROM` partial-lot fragment)
go in as `null` — the scorer ships those leads unenriched and flagged rather
than risking a wrong join.

## Stage 4 — Score

```
python ${CLAUDE_SKILL_DIR}/scripts/run_pipeline.py score \
    --parsed work/parsed.json --parcels work/parcels.json \
    --county brevard-fl --out work/
```

Writes `work/leads.csv` + `work/leads.json` (ranked, one row per lead, with
per-signal contribution columns) and `work/summary.md`. Signals and weights
come from `config/scoring.json` — the user may edit weights; never hardcode
them. Present the summary and the top leads; offer the CSV as the deliverable.

## Error handling

| Situation | Action |
|---|---|
| Portal bounces to login | Gated deployment — tell the user, stop. Never register or pay. |
| CAPTCHA / bot challenge | Stop, report. Do not attempt to bypass. |
| Doc-type autocomplete shows no lis pendens option | Enumerate what IS offered; ask the user which distress doc types to pull. |
| Zero results in window | Legitimate — released-through lag or quiet week. Widen the window within the banner date. |
| Export returns error page instead of CSV | Retry once after 3s; then fall back to paging `Search/GridResults` (see references). |
| >30% of rows in review file | Stop; county format likely differs — re-verify before shipping leads. |
| Appraiser API unreachable / blocked | Ship leads unenriched (distress signals only) and say so. |
