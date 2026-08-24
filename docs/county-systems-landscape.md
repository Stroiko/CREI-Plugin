# County official-records systems — vendor landscape

Survey of the vendors behind US county recorder / clerk **online search** portals
(the public web search over deeds, liens, lis pendens — not case management or
e-filing, except where one portal serves both). Feeds the
[vendor router](vendor-router.md) and sets the handler build order.

All **VERIFIED** entries were loaded live in a browser on **2026-08-24** (only the
landing/search page — no logins, no registrations, no gates bypassed). **REPORTED**
= vendor claim or secondary source; each carries its source URL. Ground-truth (GT)
entries were verified earlier by us (2026-08-23, see `data-sources.md` /
`vendor-router.md`).

## 1. Vendor roster with fingerprints

| Vendor / product | Owner (lineage) | Fingerprint — classify in seconds | Status |
|---|---|---|---|
| **Acclaim classic** (Harris Recording Solutions) | Harris Computer (Constellation). Acclaim built by Aptitude Solutions (Maitland, FL); Harris acquired Aptitude + Delta Computer Systems' recording products and formed HRS in 2014 ([flexjobs company profile](https://www.flexjobs.com/remote-jobs/company/harris_computer_systems-harris_recording_solutions), [PRWeb 2014](https://www.prweb.com/releases/harris_recording_solutions_announces_acclaim_upgrade/prweb11929075.htm)) | Footer `Copyright 20xx © Acclaim, is a registered trademark of HARRIS RECORDING SOLUTIONS`; disclaimer gate with button "I accept the conditions above."; search-tile paths `/search/SearchType{DocType,Name,RecordDate,...}`; often (not always) `/AcclaimWeb` base path | VERIFIED (Duval, Lake + GT Brevard, Pinellas, Broward) |
| **Acclaim v2** (guest UI) | same | "Welcome, Guest" header, Kendo widgets, no disclaimer gate, `Copyright 1999–20xx Harris Recording Solutions` | GT (Highlands, St. Lucie) |
| **Landmark Web** (Pioneer Technology Group) | **Catalis** (formerly Government Brands LLC — PE rollup of 30+ govtech cos., rebranded Aug 2022 ([govtech.com](https://www.govtech.com/biz/after-30-acquisitions-government-brands-rebrands-as-catalis)); ptghome.com now redirects to catalisgov.com/courts-land-records/ — VERIFIED 2026-08-24). PTG HQ Sanford, FL; sister product Benchmark (courts) | Page title `Landmark Web Official Records Search` or `Landmark Web Home Page`; URL path `/LandmarkWeb` (also `/Landmark`, case-insensitive `/LandMarkWeb`); nav: Home/Search/Support + "Subscriber Log On"; tiles: Name, Document, Case Number, Book Page, Consideration, Record Date, Clerk File Number, Legal; "Property Fraud Alert" at `/LandmarkWeb/FraudAlert` | VERIFIED (Lee, Palm Beach, Escambia, St. Johns, Clay, Hernando) |
| **Tyler Eagle** recorder | Tyler Technologies (acquired Eagle Computer Systems) | `countygovernmentrecords.com` hosted network (footer "© Tyler Technologies Inc.") — hosts NM, PA, TX, WA only (VERIFIED 2026-08-24); standalone deployments use `/recorder/eagleweb/` JSP paths; public product now "[Records Public Access](https://www.tylertech.com/solutions/public-administration/land-official-records/records-management)" | VERIFIED (network landing) — **login-gated** for doc search (GT prior recon) |
| **NewVision BrowserView / SearchNG** | NewVision Systems Corporation, New Canaan CT (independent; [newvisionsystems.com](https://webhost01.newvisionsystems.com/officialrecords.aspx)) | BrowserView: URL path `/browserview*`, footer `© 2018 NewVision Systems Corporation. All rights reserved`, banner "Verified as of MM/DD/YYYY", tabs Search/Results/Document, sub-tabs Party / Document Type / File Number / Book-Page. SearchNG (legacy): `nvweb.` host, launches a **ClickOnce Windows app** — not browser-automatable | VERIFIED (Polk, Osceola = BrowserView; Marion = SearchNG) |
| **Aumentum Recorder — Public Access** | Harris Computer since 18-Nov-2019; formerly Thomson Reuters Aumentum, originally Manatron ([pitchbook](https://pitchbook.com/profiles/company/436305-52), [Harris announcement](https://www.harrisfrontline.com/post/harris-announces-aumentum)) | ASP.NET variant: path `/RealEstate/SearchEntry.aspx`, footer `Aumentum Recorder - Public Access Web UI, Version 20xx.x.x Copyright © 2001 - 20xx`. JSP variant: path `/recorder/web/`, "Version: 20xx.1.xx" banner, disclaimer + "I Accept", help at `web/help.jsp` with `$ ? + - *` wildcard-operator help text | VERIFIED (Alachua = ASP.NET; Orange = JSP variant, vendor string not exposed — see §2) |
| **OnCore** (Aptitude Solutions) | Harris (same Aptitude lineage as Acclaim). Legacy product; deployments migrating to Acclaim (Duval's `oncore.duvalclerk.com` now 301s to an Acclaim portal — VERIFIED) | ASP.NET `.aspx` pages (`ORWelcome.aspx`, `OfficialRecords.aspx`); header shows `User Name - Anonymous / Group - Public Access` | VERIFIED portal (Sarasota); vendor ID from UI pattern = REPORTED |
| **Kofile → GovOS → Neumo** ("QuickLink", GovOS Cloud Search) | Audax PE bought Kofile Technologies 2020; software arm became **GovOS** (Austin, TX), **spun out of Kofile 2023**; Audax sold GovOS to **Neumo** Aug 2025 ("700+ government agencies") ([Audax/LinkedIn](https://www.linkedin.com/posts/audax-private-equity_were-thrilled-to-announce-the-sale-of-govos-activity-7361439161477660673-6JjF), [press PDF](https://sheaco.com/wp-content/uploads/2025/08/Audax-Private-Equity-Completes-Exit-of-GovOS.pdf)). Kofile itself continues as records preservation/digitization services | `kofilequicklinks.com/{county}{st}/Default.aspx`, title "QuickLink - {County}"; table-layout ASP.NET, "Search Index Books" / "Search for a Document" panels. Mostly **historical index books**, not the live OR index | VERIFIED (Polk historic books) |
| **Fidlar Technologies** — Laredo / Tapestry | Independent (Davenport, IA — [fidlar.com](https://www.fidlar.com/CompanyInfo.aspx)) | Tapestry: `tapestry.fidlar.com/TapestryEON/...` central multi-county site, **pay-per-search**; Laredo: installed/subscription client, per-county. County sites say "search in all Fidlar counties" ([example: Lyon Co. KS](https://www.lyoncountyks.gov/246/Register-of-Deeds-Records-Search)) | VERIFIED (vendor + county pages); Midwest (MN, WI, IL, IN, MI, KS...) — no FL seen |
| **Cott Systems** — Resolution³ / records online | Independent (Columbus, OH; 135+ yrs) | Hosted per-county portals (`cotthosting.com` etc.); vendor claim "**over 300 local offices across 21 states**" ([cottsystems.com](https://cottsystems.com/), VERIFIED claim 2026-08-24) | REPORTED footprint; no FL deployment seen |
| **DuProcess®** (Alliance) | Alliance ([courtalliance.com/software](https://courtalliance.com/software)) — small FL/MS vendor | Title `DuProcess® Official Records Online`; path `/DuProcessWebInquiry/` | VERIFIED (Seminole FL; MS chancery clerks) |
| **i3 Verticals** — Land Records / TitleSearcher (ex-BIS) | i3 Verticals (public co., Nashville); land records line from Business Information Systems (BIS) | `titlesearcher.com` multi-county search, footer `©1999-2026 Business Information Systems`; states AR, TN, KY, VA, NC, SC; **membership/paid** | VERIFIED landing |
| **US Land Records** network | Historically ACS/Xerox-lineage hosted network; landing says "Welcome LandAccess.com users" (LandAccess was Manatron/Aumentum's), current operator not named on site | `uslandrecords.com/uslr/UslrApp/index.jsp`; state picker (CT, DE, MA, ME, MI, NJ, NY, OH, OK, PA, RI, SC, TX, VT, VA); per-state subdomains (`sclandrecords.com`, `i2e.uslandrecords.com/...`) | VERIFIED landing; ownership REPORTED/unclear — no FL |
| **Vanguard CI** | Site title "Home \| Tyler Technologies \| Vanguard CI" — Tyler-affiliated recorder-office product line | Niche; "Recording Access" public request module | REPORTED only — not seen in FL |
| **Granicus govRecords** | Granicus | Marketing page only ([granicus.com](https://granicus.com/)) — no live portal fingerprinted | REPORTED only |
| **Custom in-house** | per county | Anything else. FL examples: Miami-Dade SPA, Hillsborough "ORI Public Access" SPA, Volusia legacy `.aspx` "Document Inquiry", Pasco classic `.asp` forms, Leon `lforms` form, Collier "COR Access" SPA, Manatee "Public Records Hub" (GT) | VERIFIED (each below) |

## 2. Florida county-by-vendor (top 25+ by population)

All VERIFIED 2026-08-24 unless marked GT (ground truth 2026-08-23) or REPORTED.
"Open" = anonymous search reachable from the landing page (disclaimer clicks at
most); nothing here required login.

| # | County | Vendor | URL | Evidence / notes |
|---|---|---|---|---|
| 1 | Miami-Dade | Custom in-house | `onlineservices.miamidadeclerk.gov/officialrecords/` | SPA ("Loading…", toast container); no vendor branding. Open |
| 2 | Broward | Acclaim classic | `officialrecords.broward.org/AcclaimWeb` | GT. Open; CSV pull-only (no legals) |
| 3 | Palm Beach | **Landmark Web** | `erec.mypalmbeachclerk.com/` | Title "Landmark Web Home Page". Open |
| 4 | Hillsborough | Custom SPA ("ORI Public Access") | `publicaccess.hillsclerk.com/oripublicaccess/` | Linked from hillsclerk.com as "Search Official Records Online". Client-rendered SPA, no vendor branding on landing; vendor undetermined. (HOVER = court records only.) |
| 5 | Orange | **Tyler Self-Service** (CORRECTED 2026-08-24 — earlier "Aumentum JSP variant" guess was wrong) | `selfservice.or.occompt.com/ssweb/` | Footer "© 2014-2025 Tyler Technologies \| Version 2025.1.32". Legacy `/recorder/eagleweb/` redirects here; legacy site discontinued 9/1/25. **Open** (anonymous) with reCAPTCHA-gated entry disclaimer. Fully verified incl. CSV export + 3/3 OCPA joins — see vendor-router.md |
| 6 | Pinellas | Acclaim classic | `officialrecords.mypinellasclerk.gov` | GT. Open, CSV verified |
| 7 | Duval | Acclaim classic | `or.duvalclerk.com/` | Harris footer verbatim; `oncore.duvalclerk.com` 301s here (migrated from OnCore). Open |
| 8 | Lee | **Landmark Web** | `or.leeclerk.org/LandmarkWeb` | Title + full tile set + "Subscriber Log On". Open |
| 9 | Polk | NewVision BrowserView | `apps.polkcountyclerk.net/browserviewor/` | `© 2018 NewVision Systems Corporation`; "Verified as of 08/20/2026". Open. (Kofile QuickLink at `kofilequicklinks.com/polkfl/` = historic index books only; PRO = court cases only) |
| 10 | Brevard | Acclaim classic | `vaclmweb1.brevardclerk.us/AcclaimWeb/` | GT. Fully verified pipeline |
| 11 | Volusia | Custom in-house (legacy ASP.NET) | `app02.clerk.org/or_m/` | "Document Inquiry", disclaimer + Accept, "requires Internet Explorer 10" note. Open |
| 12 | Pasco | Custom in-house (classic ASP) | `app.pascoclerk.com/appdot-public-online-services-forms-or-search.asp` | Server-rendered forms; has LIS PENDENS doc-type filter. Open, very simple |
| 13 | Seminole | DuProcess (Alliance) | `recording.seminoleclerk.org/DuProcessWebInquiry/` | Title "DuProcess® Official Records Online" (JS app, empty a11y tree). Open |
| 14 | Sarasota | OnCore-style (Aptitude/Harris — REPORTED vendor ID) | `secure.sarasotaclerk.com/ORWelcome.aspx` | "User Name - Anonymous / Group - Public Access" header. Open |
| 15 | Manatee | Custom ("Public Records Hub", MCCCC) | `records.manateeclerk.com` | GT. Open, has Subdivision search |
| 16 | Collier | Custom SPA ("COR Access") | `cor.collierclerk.com/coraccess/` | Linked from collierclerk.com "Search Official Records"; SPA, no vendor branding |
| 17 | Marion | NewVision **SearchNG** | `nvweb.marioncountyclerk.org/searchng_SSL/` | Launches a **ClickOnce Windows app** (Edge/Chrome extensions required, Safari unsupported) — not browser-automatable |
| 18 | Osceola | NewVision BrowserView | `officialrecords.osceolaclerk.org/browserview/` | Same footer + "Verified as of" banner as Polk. Open |
| 19 | Lake | Acclaim classic | `officialrecords.lakecountyclerk.org/` | Harris footer verbatim; "I accept the conditions above." — note: **no `/AcclaimWeb` path** (root-mounted) |
| 20 | Escambia | **Landmark Web** | `dory.escambiaclerk.com/LandmarkWeb` | Title match. Open |
| 21 | St. Lucie | Acclaim v2 | `acclaimweb.stlucieclerk.gov` | GT. Open |
| 22 | Leon | Custom in-house | `lforms.leonclerk.com/official_records/` | Single-page form (Book Type / Instrument Code / date), "validated … through 08/20/2026" banner, © Leon Clerk. Open |
| 23 | Alachua | **Aumentum Recorder Public Access** | `isol.alachuaclerk.org/RealEstate/SearchEntry.aspx` | Footer "Aumentum Recorder - Public Access Web UI, Version 2023.1.2 Copyright © 2001 - 2026". Open (disclaimer page on county site links in) |
| 24 | St. Johns | **Landmark Web** | `apps.stjohnsclerk.com/Landmark` | Title match. Open |
| 25 | Clay | **Landmark Web** | `landmark.clayclerk.com/LandmarkWeb` | Title match. Open |
| — | Highlands | Acclaim v2 | `acclaim.highlandsclerkfl.gov/AcclaimWeb` | GT. Open |
| — | Hernando | **Landmark Web** | `or.hernandoclerk.com/LandmarkWeb/` | Title match. Open |
| — | Charlotte | Unidentified modern portal | `recording.charlotteclerk.com/` | Open, anonymous; "Verified Through 8/17/2026" banner, Agent Login link, combined single-page search. No vendor branding — fingerprint doesn't match Acclaim/Landmark/NewVision; classify later |
| — | Citrus | Landmark (REPORTED) | — | [PRWeb 2014: "Landmark Official Records System is now live in Citrus County"](https://www.prweb.com/releases/pioneer_technology_group_announces_landmark_official_records_system_is_now_live_in_citrus_county/prweb12178561.htm) — not re-verified live |

**FL tally (30 counties established):** Acclaim 7 (Brevard, Pinellas, Broward,
Duval, Lake, Highlands, St. Lucie) · Landmark 6 verified + 1 reported (Palm Beach,
Lee, Escambia, St. Johns, Clay, Hernando; Citrus) · Custom in-house 7 (Miami-Dade,
Hillsborough, Volusia, Pasco, Manatee, Collier, Leon) · NewVision 3 (Polk, Osceola,
Marion) · Aumentum 1 verified + 1 probable (Alachua; Orange) · DuProcess 1
(Seminole) · OnCore-style 1 (Sarasota) · Unidentified 1 (Charlotte).

**Two vendors — Acclaim (Harris) and Landmark (Catalis/Pioneer) — cover ~half of
the top-25 FL counties, and every one of their deployments we touched is open
anonymous search.**

## 3. National footprint (vendor claims — treat as marketing numbers)

| Rank (approx.) | Vendor | Claimed footprint | Source |
|---|---|---|---|
| 1 | Tyler Technologies (Eagle / Records Public Access) | Largest govtech vendor overall; Eagle recorder concentrated in the West/Southwest; hosted search network covers NM, PA, TX, WA | [countygovernmentrecords.com](https://www.countygovernmentrecords.com/) (VERIFIED landing); [tylertech.com](https://www.tylertech.com/solutions/public-administration/land-official-records/records-management) |
| 2 | GovOS (ex-Kofile software) → Neumo | "More than 700 government agencies" (all products, not just land records) | [Audax exit press, Aug 2025](https://sheaco.com/wp-content/uploads/2025/08/Audax-Private-Equity-Completes-Exit-of-GovOS.pdf) |
| 3 | Fidlar (Laredo/Tapestry) | Multi-state Midwest network; "all Fidlar counties" searchable from one Tapestry site (MN, WI, IL, IN, MI, KS seen); no exact count published on fidlar.com | [fidlar.com](https://www.fidlar.com/); [Lyon Co. KS](https://www.lyoncountyks.gov/246/Register-of-Deeds-Records-Search) |
| 4 | Cott Systems | "over 300 local offices across 21 states" | [cottsystems.com](https://cottsystems.com/) |
| 5 | Catalis (Pioneer Landmark + Benchmark + more) | 30+ companies rolled up; Landmark dominant in FL, expanding (Cherokee Co. GA, Adams Co. CO, Seattle WA wins) | [govtech.com](https://www.govtech.com/biz/after-30-acquisitions-government-brands-rebrands-as-catalis); [ptghome.com](https://www.ptghome.com/) (→ catalisgov.com) |
| 6 | Harris (HRS Acclaim + Aumentum + OnCore legacy) | FL-dominant on Acclaim; Aumentum adds large-county recorder deployments nationally (ex-Thomson Reuters book) | [PRWeb](https://www.prweb.com/releases/harris_recording_solutions_announces_acclaim_upgrade/prweb11929075.htm); [pitchbook](https://pitchbook.com/profiles/company/436305-52) |
| 7 | i3 Verticals / BIS (TitleSearcher) | AR, TN, KY, VA, NC, SC counties | [titlesearcher.com](https://www.titlesearcher.com/) |
| 8 | US Land Records network | 15 states (Northeast-heavy) | [uslandrecords.com](https://www.uslandrecords.com/) |
| — | NewVision Systems | Small (CT + a few FL counties) but holds 3 FL counties incl. Polk | [newvisionsystems.com](https://webhost01.newvisionsystems.com/officialrecords.aspx) |

No independent, current per-county census exists; these are the best sourced
claims as of 2026-08-24.

## 4. Access regime + export capability per vendor

Never auto-register or enter payment anywhere (router rule). Regime is
**per-deployment** — vendor is a prior, not a guarantee.

| Vendor | Regime (norm) | Export / bulk | Automation outlook |
|---|---|---|---|
| Acclaim (classic & v2) | **Open** — anonymous after disclaimer (classic) or straight in (v2) | `Search/ExportCsv` returns full result set in one GET (GT, Brevard). Legal-description column population varies by county (Broward empty) | Best-in-class; handler shipped |
| Landmark Web | **Open** — anonymous search tiles; "Subscriber Log On" exists but is optional for index search (all 6 FL deployments landed on open tiles) | Results grid print/download exists; **CSV export not yet verified** — first task of handler work | High priority; one MVC app pattern across many counties |
| NewVision BrowserView | **Open** — anonymous | Unknown; results table in-page; has "Verified as of" freshness banner | Moderate; two FL top-10 counties on identical app |
| NewVision SearchNG | Open in theory, but **ClickOnce desktop app** | n/a | Do not attempt browser automation (Marion) |
| Aumentum Public Access | **Open** — disclaimer then anonymous search (both UI variants) | Unknown; ASP.NET grid | Moderate; covers Orange (if confirmed) + Alachua |
| OnCore (legacy) | **Open** — "Anonymous / Public Access" group | Unknown | Low priority; shrinking install base (migrations to Acclaim) |
| Custom FL portals | All **open** in our sample (Miami-Dade, Hillsborough, Volusia, Pasco, Leon, Collier, Manatee, Charlotte) | Pasco/Leon/Volusia are plain server-rendered forms (easy scrape, no export button); SPAs (Miami-Dade, Hillsborough, Collier) have JSON backends worth sniffing | Per-county one-offs |
| Tyler Eagle | **Gated** — document search requires account (GT prior recon); Tyler markets subscription "Records Public Access" | n/a for us | Skip (also: no FL) |
| Fidlar Laredo / Tapestry | **Paid** — Laredo subscription; Tapestry pay-per-search with account | n/a for us | Skip (also: no FL) |
| i3/BIS TitleSearcher | **Paid** membership | n/a | Skip |
| Cott | Mixed; typically registration, some paid images | Unknown | Skip until a target county appears |
| Kofile/GovOS QuickLink | **Open** (Polk) | Index-book images only — not a lead source | Not useful for pipeline |
| US Land Records | Free index search typical, paid images | Unknown | No FL; revisit for Northeast expansion |

## 5. Recommended handler build order

1. **Landmark Web (Catalis/Pioneer)** — highest ROI. 6 verified FL counties
   (Palm Beach #3, Lee #8, Escambia, St. Johns, Clay, Hernando; Citrus reported),
   uniform `/LandmarkWeb` MVC app, open anonymous, same tile/search structure as a
   pattern (Doc-Type + date-range search exists). First step: verify whether the
   results grid exposes CSV/export and whether legals ride along — mirrors the
   Acclaim capability-matrix exercise. Expected effort: moderate (one handler,
   per-county capability rows).
2. **NewVision BrowserView** — Polk (#9) and Osceola (#18) on the byte-identical
   app; open; freshness banner built in. Effort: moderate. (Explicitly exclude
   SearchNG/Marion — ClickOnce.)
3. **Aumentum Public Access** — Alachua verified; **confirm Orange (#5) by
   fingerprint match** (accept disclaimer → compare search form to Alachua's).
   Orange alone justifies the handler. Two UI variants (JSP vs `.aspx`) may mean
   1.5 handlers. Effort: moderate-high.
4. **High-value custom one-offs, easiest first** — Pasco (#12, classic ASP form —
   trivial), Leon (#22, plain form), Volusia (#11, legacy .aspx). Then the SPA
   heavyweights via backend-API sniffing: Miami-Dade (#1), Hillsborough (#4),
   Collier (#16). Sarasota (OnCore-style, open) fits here too. Effort: low each
   for forms; high per SPA.
5. **DuProcess (Seminole)** — single FL county, JS app; do when Seminole matters.
6. **Skip for now:** Tyler Eagle (gated, no FL), Fidlar (paid, no FL),
   TitleSearcher (paid), Cott / US Land Records / Vanguard / Granicus (no FL
   footprint observed). Charlotte's unidentified portal: fingerprint again when a
   handler pass reaches it.

Combined with the shipped Acclaim handler, tiers 1–3 would give vendor-level
coverage of **17 of Florida's 30 established counties**, including 8 of the top 10.
