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
| 2. Parse | Python | `run_pipeline.py parse` → parcel IDs + review file |
| 3. Enrich | Browser | Fetch each parcel's appraiser record (JSON API) |
| 4. Score | Python | `run_pipeline.py score` → ranked CSV/JSON + summary |

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

Writes `work/parsed.json` (records with constructed parcel IDs), and
`work/review.csv` (records that could not be parsed or constructed — condo/
timeshare units, metes-and-bounds, unexpected tokens). **Review rows are never
dropped**; mention their count to the user. If more than ~30% of rows land in
review, stop and investigate before continuing — the county's format may
differ from its config.

## Stage 3 — Enrich from the appraiser (browser)

For each parcel ID in `parsed.json`, fetch the county appraiser record using
the `appraiser` entry in `counties.json`. These are plain GET URLs, so
**navigate the browser to each URL and read the JSON shown on the page** —
no scripting required (Brevard: exact lookup
`https://www.bcpao.us/api/v1/search?parcel=<id>` to get the account number,
then `https://www.bcpao.us/api/v1/account/<account>` for the full record with
mailing address and sales history). Serial navigation, ~1–2s apart.

Collect results into `work/parcels.json` as `{ "<parcelID>": <account JSON> }`.
A parcel that returns 0 matches goes in with value `null` — the scorer flags
it for review instead of dropping it.

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
