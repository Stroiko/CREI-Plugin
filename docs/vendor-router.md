# Vendor router — fingerprints, regimes, and branch logic

> The canonical, user-shipped copy of this logic lives INSIDE the skill at
> [`plugins/crei/skills/county-records/references/vendor-router.md`](../plugins/crei/skills/county-records/references/vendor-router.md)
> — that's what installed users' Claude reads. This file is the repo-side
> record with the verification evidence. Keep them in sync.

All entries verified live 2026-08-23 unless noted. The router's job: given a
county, tell the user upfront whether the pipeline can run there.

## Step 1 — fingerprint the vendor

| Vendor | Fingerprint | Seen at |
|---|---|---|
| Acclaim classic | Footer "Acclaim, is a registered trademark of Harris Recording Solutions"; disclaimer gate; search tiles | Brevard, Pinellas, Broward |
| Acclaim v2 | "Welcome, Guest" header; "Copyright 1999–2026. Harris Recording Solutions"; Kendo widgets; no disclaimer gate | Highlands, St. Lucie |
| Tyler Eagle | `countygovernmentrecords.com` domains; Tyler footer | (prior recon) **login-gated** |
| GovOS Cloud Search (Kofile→GovOS→Neumo) | Host `{county}.{st}.publicsearch.us`; title "Official Record Search - Quick Search - …"; "Powered By Neumo" footer; "Certified through" banner; Quick/Advanced tabs, OCR full-text option, "Property Alert" | Dallas, Tarrant, Bexar, Collin, Denton, Hidalgo, Cameron — all TX, all open (2026-08-24). **Handler shipped** (`references/govos.md`) |
| Aumentum Recorder – Public Access (Harris) | Footer "Aumentum Recorder - Public Access Web UI, Version 20xx.x.x … Harris Recording Solutions"; disclaimer + accept; `/RealEstate/SearchEntry.aspx` paths | Alachua FL; Travis TX (`tccsearch.org`), Fort Bend TX (`ccweb.co.fort-bend.tx.us`) — all Version 2023.1.2, open (2026-08-24). **Handler shipped** (`references/aumentum.md`) — Alachua verified 3/3 |
| GSCCCA (GA statewide consortium) | `search.gsccca.org`, classic ASP paths, © GSCCCA footer, 159-county picker; forms anonymous but search execution → `apps.gsccca.org/login.asp` | Fulton, Gwinnett, Clayton, Chatham, Hall GA (only online route; **Gated/Paid** $5/4hr — login wall hit live 2026-08-24). User-assisted only |
| Cott Systems eSearch | "eSearch \| Name Search" title, Guest User header, © Cott Systems footer; `cotthosting.com` variants gated | Forsyth GA (open as guest, 2026-08-24); Henry GA legacy (gated). **No handler yet** |
| Tyler "RE Search" (MicroPact) | "RE Search" title, `/RESearch/RESearch` path, © Tyler Technologies v1.x footer, per-class Good-Thru dates | Henry GA (open, free; 2026-08-24). **No handler yet** |
| Custom in-house | anything else — e.g. Manatee's "Public Records Hub" (MCCCC); Harris Co. TX "Web Inquiry" (`cclerk.hctx.net`); El Paso TX (`apps.epcountytx.gov/publicrecords`) | Manatee; Harris TX, El Paso TX (open, 2026-08-24) |

## Step 2 — access regime (per deployment)

Open = anonymous search reachable (after disclaimer on classic). Gated =
bounced to login. Never auto-register or enter payment on gated sites.

## Step 3 — data capability (per deployment — vendor is NOT enough)

Even on open Acclaim, check what the export actually contains before promising
leads. Verified capability matrix:

| County | Pull | Legal in CSV | Join strategy | Status |
|---|---|---|---|---|
| Brevard, FL | ✓ (24 rows) | ✓ STR+SUBID style | construct `{T}-{R}-{S}-{SUBID}-{BLK|*}-{LOT}` | **Fully verified (6/6)** |
| Pinellas, FL | ✓ (23 rows) | ✓ name-based, in `Comments` | subdivision-lookup on PCPAO | **Verified (3/3)**; condos → review |
| Highlands, FL | ✓ (25 rows) | ✓ `CASE #/abbrev` in `Comments` | owner-lookup + legal cross-check on HCPAO | **Verified (3/3)** |
| Palm Beach, FL | ✓ (93 rows/wk, XLSX export; reCAPTCHA = 1 human click per search) | ✓ **pre-parsed columns** (Lot/Sub/S-T-R) | owner-lookup on PAPA, cross-check lot+STR | **Verified (3/3)** — 2026-08-24 |
| Polk, FL | ✓ (79 docs/wk via Print Results TSV; no CAPTCHA) | ✓ sub-first name-based; some legals ARE parcel IDs | owner-lookup on polkflpa.gov + legal cross-check | **Verified (3/3)** — 2026-08-24; no case numbers in data |
| Orange, FL | ✓ (44 docs/wk, native CSV export; reCAPTCHA at entry = 1 human click/session) | ✓ labeled tokens (Lot:/Block:/Unit:); TS: timeshares → review | owner-lookup on OCPA (try ALL defendants) + subdivision fallback; parcel constructible once sub code known | **Verified (3/3)** — 2026-08-24. Vendor = **Tyler Self-Service** (NOT Aumentum as first reported); no case numbers |
| Dallas, TX | ✓ (16 docs/wk via grid transcription; native export login-gated; no CAPTCHA; results URL is a constructible GET) | ✓ labeled tokens incl. **city** (Subdivision - Name:/Lot:/Block:/Township:); Survey legals → review | owner-lookup on DCAD (dallascad.org) + lot/block cross-check, city narrows candidates | **Verified (3/3)** — 2026-08-24. Vendor = **GovOS Cloud Search**; no case numbers; family-matter LPs often unjoinable |
| Tarrant, TX | ✓ (8/wk; grid transcription; URL code LP) | ✓ **comma template** (`{CITY}, Subdivision: X, Lot: n, Block: b`) | **legal-search URL on TAD** (`searchType=LegalDescription&query={SUB} BLOCK {b} LOT {l}`) — name-drift-immune | **Verified (3/3)** — 2026-08-24 |
| Bexar, TX | ✓ (40/wk, HOA-heavy; URL code `LIS PEN`) | ✗ legal string empty — but grid has **Lot/Block/NCB/CountyBlock/Address columns** | **address search on BCAD** (Harris Govern portal, phrase mode) + lot/block/CB cross-check | **Verified (3/3)** — 2026-08-24. **PARTIES INVERTED: grantor = owner/lead** |
| Denton, TX | ✓ (4/wk; grid has Lot/Block; subdivision on detail pages) | dash template on `/doc/{id}` | owner-surname compound search on Denton CAD (True Prodigy); GEO ID encodes blk+lot | **Verified (3/3)** — 2026-08-24 |
| Collin, TX | ✓ (~10/wk) but legals AND role-split only via detail pages; **every party indexed as both grantor and grantee** | dash template on `/doc/{id}` | esearch.collincad.org owner search (invisible reCAPTCHA present) | Pull-verified; join unverified — parties undifferentiated, ship flagged |
| Hidalgo, TX | ✓ (~2/wk; 14 LIS type variants, URL codes are FULL NAMES) | dash template on `/doc/{id}`; Spanish land-grant legals → review | hidalgoad.org unmapped | Pull-verified; join unverified |
| Cameron, TX | **✗ ZERO lis pendens in the OR index over a full year** (type exists in picker) — likely district-clerk filings only | n/a | n/a | **No LP supply** — say so plainly |
| Alachua, FL | ✓ (18/wk LP+LPFAM; grid transcription, no CSV export) | ✓ subdivision-first (`{SUB} LT n [BLK b]`); some legals are `PIN {id}` directs; SEC/TWP/RNG → review | owner-lookup on ACPA qPublic + legal cross-check; PIN directs via directFormat | **Verified (3/3)** — 2026-08-24. Vendor = **Aumentum** (Harris); no case numbers |
| Travis/Fort Bend, TX | Aumentum identical UI (Version 2023.1.2) | TX legal format differs (not FL STR) — unverified | expected owner-lookup on county CAD | Candidates (verify next); Fort Bend has 500-result cap |
| Osceola, FL | BrowserView identical to Polk; codes LP+LPCT | expected same | expected owner-lookup | Candidate (verify next) |
| Lee, FL | Landmark confirmed; **Akamai interstitial** before search | expected same as PB | expected owner-lookup (leepa.org) | Blocked pending user-assisted run |
| St. Johns, FL | Landmark, structure identical to PB | not yet pulled | unmapped | Candidate (verify next) |
| Broward, FL | ✓ (43 rows) | ✗ empty on LP (0/43) | none from CSV | **Pull-only** — names/cases without parcels |
| St. Lucie, FL | portal reachable (v2) | unmapped | unmapped | Candidate |
| Manatee, FL | non-Acclaim (MCCCC), open, has Subdivision search | unmapped | unmapped | Candidate, different handler needed |

## What to tell the user

- Verified county → run the pipeline.
- Open Acclaim, unverified → offer to pull records now and verify the join
  first (the per-county verification procedure is in the skill's
  `references/acclaim.md`).
- Pull-only (Broward pattern) → pulls names/cases, no ownership enrichment;
  say exactly that.
- Gated/Tyler → "your county requires an account; we won't automate that."
- Unknown vendor → not supported yet; note the fingerprint for future work.
