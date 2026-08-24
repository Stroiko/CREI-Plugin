# Vendor router — classify the county's record system, then route

Run this whenever the county is not in `config/counties.json`, or a known
county's portal doesn't look like its config says it should (counties migrate
vendors). Classify in three steps: VENDOR → REGIME → DATA CAPABILITY. Never
assume; each step is observable in under a minute.

## Step 1 — find the portal

Search for "<county> county clerk official records search" and follow the
county clerk's own link to their records search. Ignore third-party
aggregators (searchsystems, myfloridacounty, etc.) — go to the county's
system itself.

## Step 2 — classify the VENDOR (fingerprints, all verified live)

| Vendor | You will see | Route |
|---|---|---|
| **Acclaim classic** | Disclaimer page with an "I accept the conditions above." button; search tiles (Name, Book/Page, Document Type…); footer "Acclaim, is a registered trademark of Harris Recording Solutions" | This skill, classic flow (`references/acclaim.md`) |
| **Acclaim v2** | "Welcome, Guest" header, NO disclaimer gate; tile menu; footer "Copyright 1999–20xx. Harris Recording Solutions"; Kendo widgets (DocTypes multi-select "Select DocTypes...", `#FromDatePicker`/`#ToDatePicker`) | This skill, v2 flow (`references/acclaim.md`) — same `Search/ExportCsv` backend |
| **Landmark Web** (Pioneer/Catalis) | Page title "Landmark Web …"; search tiles calling `LaunchDisclaimer(…)`; "Property Fraud Alert" link; "Subscriber Log On"; base path `/LandmarkWeb`, `/Landmark`, or domain root | This skill (`references/landmark.md`) — open, but a **reCAPTCHA on the search form** means one human click per search; possible Akamai interstitial (Lee) |
| **NewVision BrowserView** | Angular SPA at `/browserview*`; banner "Verified as of MM/DD/YYYY"; footer "© 2018 NewVision Systems Corporation"; tabs Search/Results/Document with Party/Document Type sub-tabs | This skill (`references/newvision.md`) — open, no CAPTCHA; ingest via Print Results page. **`nvweb.` SearchNG variant = ClickOnce desktop app, unautomatable** |
| **Tyler Self-Service** | Footer "© Tyler Technologies \| Version 20xx.x.x"; URL path `/ssweb/`; disclaimer page whose "I Accept" is gated by reCAPTCHA | This skill (`references/tyler-selfservice.md`) — verified OPEN on Orange FL; one human CAPTCHA click per session. Legacy `/recorder/eagleweb/` URLs often redirect here |
| **Tyler Eagle (legacy/gated)** | `countygovernmentrecords.com` or state-branded Tyler domains; "You must register to conduct document searches" | If it bounces to login: STOP, tell the user their county requires a personal account; never register for them. If it redirects to `/ssweb`, use the Tyler Self-Service handler |
| **GovOS Cloud Search** (Kofile→GovOS→Neumo) | Host `{county}.{st}.publicsearch.us`; title "Official Record Search - Quick Search - …"; footer "Powered By Neumo"; "Certified through MM/DD/YYYY" banner; Quick/Advanced search tabs, department picker, Index vs Full-Text (OCR) radio, "Property Alert" link | **Recognized, no handler yet.** Open anonymous search (Register/Sign In only for purchases) — dominant in Texas (Dallas, Tarrant, Bexar, Collin, Denton, Hidalgo, Cameron). Tell the user their county's system is recognized and open but automation isn't built yet. Sister site `kofilequicklinks.com/...` = historic index books only, never a lead source |
| **Aumentum Recorder – Public Access** (Harris) | Footer "Aumentum Recorder - Public Access Web UI, Version 20xx.x.x Copyright © 2001 - 20xx Harris Recording Solutions"; disclaimer page with accept link; paths under `/RealEstate/` (e.g. `SearchEntry.aspx`) | **Recognized, no handler yet.** Open after disclaimer (Alachua FL, Travis TX via tccsearch.org, Fort Bend TX). Same message as GovOS |
| **GSCCCA** (Georgia statewide) | `search.gsccca.org`; classic ASP paths (`/RealEstate/namesearch.asp`); footer "© 1995 - 20xx Georgia Superior Court Clerks' Cooperative Authority"; all-159-county picker | **Gated/Paid** — forms load anonymously but running any search bounces to `apps.gsccca.org/login.asp` ($5/4hr pass or subscription). This is the ONLY online route for many GA counties. Never register or pay. Offer the user-assisted route: the user logs into their own GSCCCA account, then you drive the search |
| **Cott Systems eSearch** | Title "eSearch \| Name Search"; "Guest User" header, optional "Log in as named user"; footer "© 2007 - 20xx Cott Systems, Inc. Version 1.x.x.x"; `cotthosting.com/{st}{county}` variants land on a Login page (gated) | **Recognized, no handler yet.** Guest-open at some deployments (Forsyth GA), gated at others — regime is per-deployment, check which you got |
| **Tyler "RE Search"** (MicroPact) | Title "RE Search"; path `/RESearch/RESearch`; footer "© 20xx Tyler Technologies v1.x.x.x"; Good-Thru dates per Deeds/Liens/Plats | **Recognized, no handler yet.** Open, free (account only for fraud alerts). Third Tyler product — do NOT confuse with Eagle (gated) or Self-Service (`/ssweb/`, has handler) |
| **Custom / other** (Catalis, i3 Verticals, in-house systems like Manatee's "Public Records Hub" / MCCCC, Harris County TX "Web Inquiry") | Anything without the marks above | Not supported for automation yet. Tell the user plainly, note the vendor name for future support, and offer the Zillow skill as the available alternative |

A county could theoretically run Acclaim behind a mandatory login — regime is
per-deployment, so always confirm Step 3.

## Step 3 — classify the ACCESS REGIME

- **Open**: you reach a search form anonymously (after the disclaimer on
  classic). → proceed.
- **Gated**: any path bounces to a login. → tell the user upfront; at most
  drive the search after they log in themselves. Never create accounts or
  enter payment.

## Step 4 — classify the DATA CAPABILITY (from the CSV itself)

Same vendor ≠ same data. Pull a small recent lis pendens window (2–3 days)
and read the export — the CSV content tells you exactly which pipeline route
applies:

| What the legal field contains | Classification | Route |
|---|---|---|
| `LT 22 BLK 1138 PB 16 PG 19 … S 33 T 29 R 37 SUBID GT` (STR + SUBID codes) | `str-subid` | `construct` strategy — but the ID format must be verified per county before use |
| `LOT 4 BLOCK A PINELLE PARTIAL REPLAT` (plain-English name) | `name-based` | `subdivision-lookup` strategy via the county appraiser's subdivision search |
| `CASE # 26-413-GCAXMX/L8 PT L9 BLK 180 WOODLAWN TERRACE` (case + abbreviated legal packed together) | `case-comments` | `owner-lookup` strategy via the appraiser's owner search + legal cross-check |
| Empty on every lis pendens row | pull-only | Deliver names/dates/cases honestly; say ownership enrichment isn't possible from this county's index (Broward pattern) |

Also note WHICH column carries the legal (`DocLegalDescription` vs
`Comments`) and whether `U`/`CaseNumber` columns exist — the column layout is
per-deployment configuration, not a vendor constant. Four live variants are
documented in `references/acclaim.md`.

## Step 5 — write it down, then verify before trusting joins

Add what you classified to `config/counties.json` (vendor, regime, landing
URL, base path, doc-type codes, `csvColumns`, `legalStyle`, `joinStrategy`)
with `"verified": false`. Records can be PULLED immediately; **joins may not
be trusted until the per-county verification procedure passes** (3+ real
records resolved to single exact parcels — see `references/acclaim.md`
§ Verifying a new county). Until then, leads ship unenriched with a clear
note to the user.

## What to tell the user, by outcome

- Verified county → run the pipeline.
- Open Acclaim, unverified → "I can pull the filings now; give me a few extra
  minutes to verify the property-matching for your county before I trust it."
- Pull-only → "Your county doesn't publish property identifiers on these
  filings; you'll get names, dates and case numbers only."
- Gated / Tyler → "Your county requires a personal account; I can't automate
  that, but I can walk you through searching manually."
- Recognized vendor, no handler (GovOS Cloud Search, Aumentum, Cott eSearch,
  Tyler RE Search) → "Your county runs <vendor>, which is open for anonymous
  search, but automation for it isn't built yet" — then offer to walk the
  search manually.
- Statewide gated system (GSCCCA in Georgia) → "Your state routes record
  searches through <system>, which requires a paid account; if you have (or
  open) one and log in yourself, I can drive the search from there."
- Unknown vendor → "Not supported yet" + record the fingerprint.
