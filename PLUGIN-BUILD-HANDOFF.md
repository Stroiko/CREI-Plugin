# Real Estate Motivated-Seller Plugin — Build Handoff

Hand this to Claude Code to develop the repository. It captures the target
architecture, the runtime constraints, the verified findings from live recon,
and a build order. A companion file, `zillow-SKILL.md`, is a standalone skill
referenced here and delivered alongside this doc.

---

## 1. What this is

A plugin that finds motivated-seller / distressed-property leads by pulling
public records and listing data, joining them to parcel/ownership data, scoring
each property, and producing a ranked lead list.

**Primary distribution target: Claude Cowork users (non-technical).** The plugin
must work for someone who installs it and runs it in Cowork — ideally with no
manual dependency installation. Build in Claude Code for speed; ship to Cowork.

**The differentiator is signal stacking, not any single data source.** Single-
signal lists (just foreclosures, just tax-delinquent) are commodities sold by
PropStream/DealMachine. The value here is cross-referencing heterogeneous public
datasets — a lis pendens on a property that is *also* absentee-owned, *also* long-
held (high equity), *also* an HOA-lien case — into a scored, explainable lead.
No generic AI-automation channel can do this because it requires domain knowledge
(what a lis pendens is, what `-CC-` vs `-CA-` means). Keep the moat there.

---

## 2. Runtime architecture — READ FIRST, it shapes everything

Cowork's execution model is split, and this plugin straddles the split:

- **Cloud sandbox:** Cowork runs code/reasoning in an isolated environment on
  Anthropic's servers. It **cannot reach the user's home network or residential
  IP.** It CAN run Python on files it already has.
- **Local browser:** When a task needs the browser, Claude drives the user's
  local Chrome via **Claude in Chrome**, through the Claude Desktop app. This is
  the only path that reaches county sites and Zillow on a residential IP.

### The two-layer design that follows from this

**Layer A — Browser (local, Claude in Chrome).** All web interaction:
- Driving county record portals (Acclaim, etc.) through their gates
- Triggering the CSV export and receiving the file
- Running Zillow searches and reading listing JSON

This MUST run locally because:
1. County sites and Zillow block datacenter IPs; only the user's residential
   Chrome gets answered.
2. There is no API/script that replaces it for these sources.

**Layer B — Data (deterministic code, runs on already-clean inputs).** Parsing,
joining, scoring:
- Parse legal descriptions → construct parcel IDs
- Join records to parcel/ownership data
- Weighted, explainable lead scoring
- Emit ranked CSV/JSON + summary

Layer B runs on the structured CSV that Layer A produced. Because Acclaim exports
a clean CSV, Layer A hands Layer B tidy data — Layer B never has to parse a
rendered web grid. In Cowork, Layer B executes in the cloud sandbox on that file.

### Hard prerequisites for the user (put these in the setup guide, not footnotes)

1. **Claude Desktop app installed AND open.** Browser automation as part of a
   task requires the desktop app. Web-only Cowork can read the current tab but
   cannot drive the browser through a full task. If a user is web-only, Layer A
   silently fails.
2. **Claude in Chrome enabled.** This is the extension that performs Layer A.
3. **Plan tier:** Chrome-side-panel Cowork is on Max/Team, rolling out to Pro.
   Verify tier availability at launch; it changes frequently.

### Privacy disclosure (required in user-facing docs)

Cowork processes work — including local files opened through the desktop app — on
Anthropic's servers. This plugin handles records of named individuals in
financial distress. Disclose that data is processed in Cowork's cloud
environment, and keep pulled record files gitignored and out of any screen
recording. Do NOT design a feature that contacts, skip-traces, or solicits
property owners — the plugin produces a list and stops.

---

## 3. Data source strategy

### Design principle: check for a download/API before scraping
Most of this data is a file or an API. Scraping is the last resort. Before
writing browser automation against any source, confirm there is no bulk download,
no export button, no documented API.

### Sources, in priority order

**A. County recorded documents (the core distress signal).**
Pre-foreclosure filings (lis pendens), tax deeds, judgments. These are
recorded documents in the county's Official Records — the highest-intent signal,
and not yet listed on any consumer site. This is the primary source. See §4 for
the fully-verified Acclaim handler.

**B. Parcel / ownership data (the join target + more signals).**
County property appraiser / assessor. Provides owner mailing address vs site
address (→ absentee owner), out-of-state owners, tenure (→ equity proxy), entity
vs individual ownership. Usually available as **bulk download or ArcGIS REST
API** — do not scrape. This is also what record legal-descriptions join against.

**C. Zillow (current-listing data + rent estimate).**
Use the standalone `zillow-SKILL.md`. Good for: current for-sale/FSBO/foreclosure
listings, rent estimates (survive even when the sale Zestimate is suppressed on
distressed listings). NOT a pre-foreclosure source — Zillow "foreclosures" are
already-listed/auction properties, a weaker and more competitive signal than
county lis pendens. Note: tax history and price history were REMOVED from the
Zillow detail query (see the skill) — get those from source B instead.

**D. HomeHarvest (comps / ARV) — OPTIONAL, deferred.**
Python library (`pip install homeharvest`) scraping Realtor.com; has a
`foreclosure` parameter. Excellent for bulk sold comps for ARV. Deferred because
it needs a pip install and a code-execution environment, which complicates the
no-install Cowork goal. Revisit once the core plugin works. If used, it belongs
in Layer B (bulk structured query, no browser). NOTE: it will fail from any
sandbox without realtor.com network access — it must run where the user's
environment can reach realtor.com.

### Explicitly out of scope
- FSBO scraping (covered by the user's separate existing product)
- Facebook / social scraping
- Any source requiring paid subscription or signed user agreement
- Contacting/skip-tracing/soliciting owners

---

## 4. County records — the vendor router (VERIFIED LIVE)

County record portals run on a small number of vendor platforms. Detect the
vendor, detect the access regime, then branch. This was validated against live
sites, not assumed.

### Step 1 — Detect the vendor (reliable, instant)

| Vendor | Fingerprint | Notes |
|---|---|---|
| **Acclaim** (Harris Recording Solutions) | Footer: "Acclaim, is a registered trademark of Harris Recording Solutions"; "OnCore Acclaim" logo | Many FL counties + beyond. FULLY MAPPED below. |
| **Tyler Eagle** | `countygovernmentrecords.com` / state subdomains; Tyler footer | Largest national footprint. **Login-gated.** |
| Kofile, Catalis, i3 Verticals | vendor branding | Not yet mapped. |

### Step 2 — Detect the access regime (per-deployment, not per-vendor)

Load the landing/disclaimer page and determine:
- **Open:** accepting the disclaimer reaches a search form. Full automation
  possible. (Acclaim/Brevard and Acclaim/Pinellas both verified open.)
- **Gated:** the entry path bounces to a mandatory login. (Tyler verified gated —
  "You must register to conduct document searches," plus per-county paid image
  subscriptions.)

A given Acclaim county *could* be configured to require login, so this check is
per-deployment.

### Step 3 — Branch
- **Open** → run the automated handler (Layer A drives it end to end).
- **Gated** → tell the user upfront that their own login is required. **Never
  auto-create accounts or enter payment** (credential/payment boundary). At most,
  drive the search after the user has logged in themselves.

### The Acclaim handler — one handler, many counties (VERIFIED on 2 counties)

Ran the identical flow against Brevard AND Pinellas (opposite coasts, different
clerks). Every step worked unchanged. This is the highest-value, fully-
automatable, portable piece — build it first.

**Verified-identical across counties:**
- Disclaimer "I accept the conditions above" gate
- Anonymous search (no login)
- Document Type autocomplete search
- Single-day / date-range Record Date search
- Results grid schema
- **Export to CSV button** (same position, same behavior)
- Header banner showing "Released through date" (recording lag ~3–5 days)

**The ONLY two things that vary per county — discover at runtime, never hardcode:**

1. **Base path.** Brevard: app under `/AcclaimWeb/...`. Pinellas: domain root
   `/...` (e.g. `/search/SearchTypeDocType`). Discover by loading the landing
   page and reading where the search tiles link. (Hardcoding `/AcclaimWeb/`
   produced an Acclaim error page on Pinellas — confirmed failure mode.)
2. **Document-type codes.** Brevard: two lis pendens codes (`LP`, `LP1`).
   Pinellas: one (`LIS PENDENS`). Enumerate per county by typing a fragment into
   the Doc Type autocomplete and reading the options — never assume another
   county's codes.

**Verified Acclaim internals (from Brevard recon):**

Search fires four requests:
| # | Method | Endpoint (relative to base path) | Role |
|---|---|---|---|
| 1 | POST | `search/SearchTypeDocType?Length=6` | submits criteria, sets server-side search state |
| 2 | GET | `Search/PartialGrid` | grid shell |
| 3 | POST | `Search/GridResults` | data endpoint (stateful — pages the held result set; likely Telerik Kendo: `{take,skip,page,pageSize,sort,filter}` → `{Data,Total}`) |
| 4 | GET | `Search/HasResults` | completion poll |

**Preferred ingest: the CSV export.** `GET Search/ExportCsv` returns the full
result set in one call (74 rows verified on Brevard, 64 on Pinellas). This is
simpler and more durable than paging `GridResults`. Note: on Brevard a 503 was
logged concurrently but the file still downloaded — verify by checking for the
file, not the HTTP status. Keep `GridResults` as a fallback.

**Verified CSV schema:**
```
U, DirectName, IndirectName, RecordDate, DocTypeDescription, BookType,
BookPage, InstrumentNumber, Consideration, DocLegalDescription, Comments, CaseNumber
```

Field semantics:
- `U` — freshness flag; blank = released, `U` = recorded but not yet released
  (postdates the released-through banner). Keep, flag as provisional, re-check.
- `DirectName` — plaintiff (bank/HOA/individual). NOT the lead.
- `IndirectName` — defendant / property owner. **This is the lead.**
- `InstrumentNumber` — unique per doc; primary dedupe key.
- `Consideration` — always `0.0000` on lis pendens; ignore.
- `DocLegalDescription` — the only property identifier (no parcel ID, no street
  address). See §5 for parsing.
- `CaseNumber` — e.g. `05-2026-CA-042960-XXCA-BC`. Case-type token classifies the
  lead for free: **`-CA-` = Circuit Civil = mortgage foreclosure; `-CC-` = County
  Civil = HOA/condo lien, small-dollar.** Prioritize `-CC-` and association
  plaintiffs (small liens against high-equity owners, less competition).

**Behavior constraints (county government servers):**
- Serial requests only, no concurrency.
- Deliberate delay between requests (start 2–3s).
- Parse the released-through banner each run; use it as the high-water mark. Do
  not query beyond it (silent empty results).
- Cache; never re-fetch a document already pulled.
- Descriptive User-Agent; respect robots.txt.

**Note on probate:** probate is a court case type, often behind a separate gated
system (e.g. Florida BECA requires a signed subscriber agreement + paid tier).
Do NOT build against it. One bounded check only: see if `NOTICE OF ADMINISTRATION`
appears as a recorded doc type in Official Records; if not, out of scope.

---

## 5. Layer B — parsing, join, scoring (the deterministic core)

### 5a. Legal-description parser (the hardest part — build and test carefully)

Grammar (from real Brevard + Pinellas samples):
```
LT {lot} BLK {block} PB {platbook} PG {platpage}  {SUBDIVISION NAME}  S {section} T {township} R {range} SUBID {subid}
```

**Key hypothesis to verify FIRST:** Brevard tax account numbers are structured
`TT-RR-SS-SUBID-BLOCK-LOT`. If parcel IDs are constructible from the legal
description, there is no fuzzy address matching:
```
LT 22 BLK 1138 PB 16 PG 19  PORT MALABAR UNIT 23  S 33 T 29 R 37 SUBID GT
                                   ↓
                        29-37-33-GT-01138-22
```
**Verify against 2–3 known parcels on the county appraiser site before building
the rest.** Confirm the county's parcel dataset exposes matching fields
(subdivision, plat book/page, lot, block, section/township/range). This
construction format is county-specific — re-verify per county.

Variants the parser must handle (all seen in real data):
- **Condos/units:** `U {unit}` with an ORB book/page ref, often `SUBID 00`
  (e.g. `PB 9 PG 27 U AA109 UW 37 SEACREST BEACH...`)
- **Fractional lots:** `LT 2.25`, `LT 3.08`
- **Alpha blocks:** `BLK D`, `BLK H`
- **Metes-and-bounds (no lot/block):** e.g. `FROM INTERSEC OF CENTER LINE OF
  SOUTH ST & ROCK PIT RD GO NLY...` — **route to a review file, do not parse.**
- **Anomalous tokens:** a township appeared as `T 20G`. Fail loudly on unexpected
  tokens rather than guessing.

Any record that fails to parse or match goes to a review file. Never silently
drop.

### 5b. Enrich from parcel data
Attach: absentee owner (mail ≠ site address), out-of-state owner, entity vs
individual, tenure (equity proxy).

### 5c. Scoring — transparent, weighted, config-driven
Not a hardcoded formula, not an LLM judgment call. A weighted rule set where
every score is explainable (which signals fired, each contribution). "Why did
this score 87?" must be answerable on camera.

Starting signals (weights in a config file):
- Lis pendens recorded (recency-weighted)
- Absentee owner
- Out-of-state owner
- Entity-owned vs individual
- Long tenure
- `-CC-` / association case (equity-rich, low-competition)
- Tax deed / foreclosure listing
- [later] MLS distress via HomeHarvest: price cuts, high DOM, expired/relisted,
  keywords ("as-is", "cash only", "handyman special", "estate sale", "must sell")

---

## 6. Deliverables & repo layout

```
docs/
  data-sources.md        # every source: URL, format, refresh cadence, access
  vendor-router.md       # fingerprints + regime detection + branch logic
config/
  scoring.yaml           # weights, exposed and editable
  counties.yaml          # per-county: vendor, base path, doc-type codes, parcel-ID format
skills/
  zillow/                # the standalone Zillow skill (see zillow-SKILL.md)
  county-records/        # the Acclaim handler + router
src/
  browser/               # Layer A — Claude in Chrome interaction
  data/                  # Layer B — parser, join, scoring
data/                    # GITIGNORED — pulled records (PII)
output/                  # ranked leads + summary
README.md                # setup for a non-technical Cowork user; hard prereqs up top
```

`README.md` is a real deliverable — write it for a non-technical user, with the
§2 hard prerequisites (desktop app open, Claude in Chrome on, plan tier) at the
very top, and the privacy disclosure stated plainly.

---

## 7. Build order (each step ships something usable)

1. **Acclaim handler, single county (Brevard), single doc type (lis pendens).**
   Layer A: base-path discovery → disclaimer → doc-type enumeration → search →
   CSV export → hand off file. Ships: "pulls the distress CSV from Brevard."
2. **Legal-description parser + parcel-ID construction.** Verify the parcel-ID
   hypothesis against real parcels FIRST. Ships: CSV rows → parcel IDs.
3. **Parcel-data join + enrichment.** Ships: leads with ownership signals.
4. **Scoring.** Ships: ranked, explainable lead list — the actual product.
5. **Generalize the handler across Acclaim counties** (base-path + doc-code
   discovery already designed in from step 1). Ships: works in any open Acclaim
   county.
6. **Vendor router** (detect Acclaim vs Tyler vs others; regime branch). Ships:
   "tell the user upfront whether we can automate their county."
7. **Zillow skill integration** (already built — see zillow-SKILL.md) for
   current-listing/rent enrichment.
8. **[Deferred] HomeHarvest** for comps/ARV, once the no-install story is settled.

Ship after step 4 if needed — a scored lead list for one county is a real product.
Steps 5–6 are what make it a *plugin* rather than a one-county script.

---

## 8. Working notes for the developer
- Report blockers immediately; a blocker that turns out interesting is useful
  signal (and video material).
- Log what didn't work and why — dead ends are teaching content for the
  companion YouTube tutorial.
- Build one signal end-to-end before adding sources. A narrow working pipeline
  beats a broad broken one.
- Keep anything county-specific in `config/counties.yaml`, never in code. The
  portability across counties is the single most valuable property — do not
  compromise it.
