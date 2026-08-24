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
| **Tyler "RE Search"** (MicroPact platform) | Tyler Technologies (acquired MicroPact 2019) — third Tyler recorder product after Eagle and Self-Service | Title `RE Search`; path `/RESearch/RESearch`; footer `© 20xx Tyler Technologies v1.x.x.x`; host often `micropact.{county domain}`; "Good Thru Date" per record class (Deeds/Liens/Plats); search-by nav Name / Book-Page / Land Description / Instrument Type / Cross-Reference / Image; optional free account for fraud notifications only | VERIFIED (Henry GA — **open**, disclaimer states "no charge") |
| **NewVision BrowserView / SearchNG** | NewVision Systems Corporation, New Canaan CT (independent; [newvisionsystems.com](https://webhost01.newvisionsystems.com/officialrecords.aspx)) | BrowserView: URL path `/browserview*`, footer `© 2018 NewVision Systems Corporation. All rights reserved`, banner "Verified as of MM/DD/YYYY", tabs Search/Results/Document, sub-tabs Party / Document Type / File Number / Book-Page. SearchNG (legacy): `nvweb.` host, launches a **ClickOnce Windows app** — not browser-automatable | VERIFIED (Polk, Osceola = BrowserView; Marion = SearchNG) |
| **Aumentum Recorder — Public Access** | Harris Computer since 18-Nov-2019; formerly Thomson Reuters Aumentum, originally Manatron ([pitchbook](https://pitchbook.com/profiles/company/436305-52), [Harris announcement](https://www.harrisfrontline.com/post/harris-announces-aumentum)) | ASP.NET variant: path `/RealEstate/SearchEntry.aspx`, footer `Aumentum Recorder - Public Access Web UI, Version 20xx.x.x Copyright © 2001 - 20xx`. JSP variant: path `/recorder/web/`, "Version: 20xx.1.xx" banner, disclaimer + "I Accept", help at `web/help.jsp` with `$ ? + - *` wildcard-operator help text | VERIFIED (Alachua FL, Travis TX, Fort Bend TX = ASP.NET, all on Version 2023.1.2) |
| **OnCore** (Aptitude Solutions) | Harris (same Aptitude lineage as Acclaim). Legacy product; deployments migrating to Acclaim (Duval's `oncore.duvalclerk.com` now 301s to an Acclaim portal — VERIFIED) | ASP.NET `.aspx` pages (`ORWelcome.aspx`, `OfficialRecords.aspx`); header shows `User Name - Anonymous / Group - Public Access` | VERIFIED portal (Sarasota); vendor ID from UI pattern = REPORTED |
| **Kofile → GovOS → Neumo** — **GovOS Cloud Search** (live OR index; internally "Vanguard Search" — NOT Tyler's "Vanguard CI") + "QuickLink" (historic books) | Audax PE bought Kofile Technologies 2020; software arm became **GovOS** (Austin, TX), **spun out of Kofile 2023**; Audax sold GovOS to **Neumo** Aug 2025 ("700+ government agencies") ([Audax/LinkedIn](https://www.linkedin.com/posts/audax-private-equity_were-thrilled-to-announce-the-sale-of-govos-activity-7361439161477660673-6JjF), [press PDF](https://sheaco.com/wp-content/uploads/2025/08/Audax-Private-Equity-Completes-Exit-of-GovOS.pdf)). Kofile itself continues as records preservation/digitization services | **Cloud Search**: host `{county}.{st}.publicsearch.us`; title `Official Record Search - Quick Search - {County}, {State} {office}`; footer "Powered By **Neumo**" logo; "Certified through MM/DD/YYYY" banner; workspace-tab SPA with Quick/Advanced search, department picker, Index-vs-Full-Text-(OCR) radio, "Property Alert" fraud alert, Cart/Register (optional). **QuickLink**: `kofilequicklinks.com/{county}{st}/Default.aspx`, title "QuickLink - {County}"; table-layout ASP.NET, "Search Index Books" / "Search for a Document" panels — **historical index books only**, not the live OR index; often cross-links its county's Cloud Search | VERIFIED — Cloud Search (Cameron, Dallas, Tarrant, Bexar, Collin, Denton, Hidalgo — all TX); QuickLink (Polk FL, Cameron TX historic books) |
| **Fidlar Technologies** — Laredo / Tapestry | Independent (Davenport, IA — [fidlar.com](https://www.fidlar.com/CompanyInfo.aspx)) | Tapestry: `tapestry.fidlar.com/TapestryEON/...` central multi-county site, **pay-per-search**; Laredo: installed/subscription client, per-county. County sites say "search in all Fidlar counties" ([example: Lyon Co. KS](https://www.lyoncountyks.gov/246/Register-of-Deeds-Records-Search)) | VERIFIED (vendor + county pages); Midwest (MN, WI, IL, IN, MI, KS...) — no FL seen |
| **Cott Systems** — Resolution³ / eSearch | Independent (Columbus, OH; 135+ yrs) | **eSearch (live)**: title `eSearch \| Name Search`; path `/External/LandRecords/protected/SrchQuickName.aspx`; "Guest User" header with optional "Log in as named user"; footer `© 2007 - 20xx Cott Systems, Inc. Version 1.x.x.x`; hosted on county subdomain (`resolution.{county}.com`) or `cotthosting.com/{st}{county}` (the cotthosting deployments land on `User/Login.aspx` = gated). Vendor claim "**over 300 local offices across 21 states**" ([cottsystems.com](https://cottsystems.com/)) | VERIFIED live (Forsyth GA — open as guest); cotthosting variant seen gated (Henry GA legacy) |
| **DuProcess®** (Alliance) | Alliance ([courtalliance.com/software](https://courtalliance.com/software)) — small FL/MS vendor | Title `DuProcess® Official Records Online`; path `/DuProcessWebInquiry/` | VERIFIED (Seminole FL; MS chancery clerks) |
| **i3 Verticals** — Land Records / TitleSearcher (ex-BIS) | i3 Verticals (public co., Nashville); land records line from Business Information Systems (BIS) | `titlesearcher.com` multi-county search, footer `©1999-2026 Business Information Systems`; states AR, TN, KY, VA, NC, SC; **membership/paid** | VERIFIED landing |
| **US Land Records** network | Historically ACS/Xerox-lineage hosted network; landing says "Welcome LandAccess.com users" (LandAccess was Manatron/Aumentum's), current operator not named on site | `uslandrecords.com/uslr/UslrApp/index.jsp`; state picker (CT, DE, MA, ME, MI, NJ, NY, OH, OK, PA, RI, SC, TX, VT, VA); per-state subdomains (`sclandrecords.com`, `i2e.uslandrecords.com/...`) | VERIFIED landing; ownership REPORTED/unclear — no FL |
| **Vanguard CI** | Site title "Home \| Tyler Technologies \| Vanguard CI" — Tyler-affiliated recorder-office product line. **Name collision:** GovOS internally calls its Cloud Search "Vanguard Search" (seen in QuickLink nav) — unrelated product | Niche; "Recording Access" public request module | REPORTED only — not seen in FL |
| **Granicus govRecords** | Granicus | Marketing page only ([granicus.com](https://granicus.com/)) — no live portal fingerprinted | REPORTED only |
| **GSCCCA** — Georgia Superior Court Clerks' Cooperative Authority | State-created cooperative of all 159 GA clerks (statute O.C.G.A. 15-6-97/98) — **new category: statewide consortium**, not a commercial vendor. First seen 2026-08-24 (GA sweep) | Host `search.gsccca.org`; classic ASP paths (`/RealEstate/namesearch.asp`, `/Lien/lienindex.asp`, `/plat/...`, `/pt61/...`); footer `Copyright © 1995 - 20xx Georgia Superior Court Clerks' Cooperative Authority`; statewide county picker (all 159 + All Counties + neighboring-county option); instrument types incl. LIEN, DEED - FORECLOSURE, TAX SALE DEED; "PREMIUM"-labeled searches. **Search forms load anonymously but executing ANY search bounces to `apps.gsccca.org/login.asp`** — account + payment required ($5/4hr day pass per county references; subscriptions) | VERIFIED (login wall hit live on Fulton name search, 2026-08-24) — **Gated/Paid** |
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

## 3. Texas county-by-vendor (top 10 by population + Cameron)

All VERIFIED live in browser 2026-08-24 (landing/search page only; no logins, no
registrations, no gates bypassed — disclaimer clicks at most). Every portal
below is **Open** (anonymous search). Cameron was the random spot-check that
started the TX sweep; the rest are the top 10 by 2020 census population.

| # | County | Vendor | URL | Evidence / notes |
|---|---|---|---|---|
| 1 | Harris | Custom in-house | `cclerk.hctx.net/applications/websearch/RP.aspx` | Title "Web Inquiry"; ASP.NET (`__doPostBack`), © Harris County Clerk's Office footer, no vendor branding. Rich anonymous search form: grantor/grantee/trustee, subdivision/description, instrument type, lot/block/section/unit. Login exists but optional |
| 2 | Dallas | **GovOS Cloud Search (Neumo)** | `dallas.tx.publicsearch.us` | Title + Neumo footer match; "Certified through 08/20/2026"; announcement banner links `kofilequicklinks.com/Dallas/` for historic books |
| 3 | Tarrant | **GovOS Cloud Search (Neumo)** | `tarrant.tx.publicsearch.us` | Title + Neumo footer match |
| 4 | Bexar | **GovOS Cloud Search (Neumo)** | `bexar.tx.publicsearch.us` | Title + Neumo footer match |
| 5 | Travis | **Aumentum Recorder Public Access** (ASP.NET variant) | `tccsearch.org` | Footer verbatim "Aumentum Recorder - Public Access Web UI, Version 2023.1.2 Copyright © 2001 - 2026 Harris Recording Solutions" — byte-identical to Alachua FL. Disclaimer + accept link. NOTE: `travis.tx.publicsearch.us` is Google-indexed but NXDOMAIN as of 2026-08-24 — possible migration to GovOS in flight; re-check |
| 6 | Collin | **GovOS Cloud Search (Neumo)** | `collin.tx.publicsearch.us` | Title + Neumo footer match |
| 7 | Denton | **GovOS Cloud Search (Neumo)** | `denton.tx.publicsearch.us` | Title + Neumo footer match |
| 8 | Hidalgo | **GovOS Cloud Search (Neumo)** | `hidalgo.tx.publicsearch.us` | Title + Neumo footer match |
| 9 | El Paso | Custom in-house | `apps.epcountytx.gov/publicrecords/OfficialPublicRecords` | © El Paso County footer, no vendor branding; open form with doc-type dropdown incl. **LIP - LIS PENDENS**; 10-docs-per-search view cap; QuickLink (`kofilequicklinks.com/ElPaso/`) for 1874–1963 historic books |
| 10 | Fort Bend | **Aumentum Recorder Public Access** (ASP.NET variant) | `ccweb.co.fort-bend.tx.us` | Same verbatim Aumentum/HRS footer, Version 2023.1.2; "Welcome Visitor", optional login; `/RealEstate/Map/SearchEntry.aspx` path visible (matches Alachua's `/RealEstate/` pattern); 500-result search cap |
| ~13 | Cameron | **GovOS Cloud Search (Neumo)** | `cameron.tx.publicsearch.us` | The original spot-check (2026-08-24): title + Neumo footer, "Certified through 08/19/2026"; QuickLink sister `kofilequicklinks.com/cameroncc/` (historic books 1830–1968, links back as "Vanguard Search") |

**TX tally (11 counties established):** GovOS Cloud Search 7 (Dallas, Tarrant,
Bexar, Collin, Denton, Hidalgo, Cameron) · Aumentum 2 (Travis, Fort Bend) ·
Custom in-house 2 (Harris, El Paso) · **Unknown vendors: 0 — every county
matched an existing roster row.**

**GovOS Cloud Search is to Texas what Acclaim+Landmark are to Florida: one
uniform SPA covering 6 of the top 10 (plus Cameron), all open anonymous, with a
guessable URL pattern (`{county}.tx.publicsearch.us`) that resolves before you
even search.** The FL§1 fingerprints classified all 11 TX counties with zero
new vendor rows needed.

## 4. Georgia county-by-vendor (top 10 by population)

All VERIFIED live 2026-08-24 (same standard as FL/TX; one search-execution test
on GSCCCA to resolve conflicting regime evidence — stopped at the login wall,
nothing entered). GA structural difference: deeds/liens are recorded with the
**Clerk of Superior Court**, and the state runs a mandatory statewide index
(GSCCCA). Counties without their own portal route the public there.

| # | County | Vendor | URL | Evidence / notes |
|---|---|---|---|---|
| 1 | Fulton | **GSCCCA** (statewide) | via `search.gsccca.org` | County site routes to GSCCCA ("$5 fee for 4 hours of access"); county eServices is filing-oriented. **Gated/Paid** |
| 2 | Gwinnett | **GSCCCA** (statewide) | via `search.gsccca.org` | County deeds FAQ routes to gsccca.org; no county-run OR portal found. Gated/Paid |
| 3 | Cobb | **Landmark Web** | `superiorcourtclerk.cobbcounty.gov/landmark` | Title "Landmark Web Home Page" — exact fingerprint; path-mounted variant. Legacy "Web Public Inquiry" at `research.cobbsuperiorcourtclerk.com` frozen at 10/01/2024 (Landmark migration). Open |
| 4 | DeKalb | **Landmark Web** | `deeds.dekalbcountyga.gov/LandmarkWeb` | Title "Landmark Web Official Records Search" — exact fingerprint. Open |
| 5 | Clayton | **GSCCCA** (statewide) | via `gsccca.org/search` | County Real Estate Division page: "Real Estate Document Search 1985 – Current" links to gsccca.org/search. Gated/Paid |
| 6 | Chatham | **GSCCCA** (statewide) | via `gsccca.org` | Superior Court Clerk Real Estate pages route to gsccca.org; in-person terminals otherwise. Gated/Paid |
| 7 | Cherokee | **Landmark Web** | `deeds.cherokeega.com/LandmarkWeb` | Title match — exact fingerprint; confirms the 2022 Catalis GA-expansion note (§5). Open |
| 8 | Forsyth | **Cott Systems eSearch** | `resolution.forsythco.com` | First live Cott: title "eSearch \| Name Search", footer "© 2007 - 2026 Cott Systems, Inc. Version 1.7.29.15", "Guest User" + optional named-user login. **Open as guest** — contradicts Cott's registration-typical rep. County disclaimer page at forsythclerk.com links in |
| 9 | Henry | **Tyler "RE Search"** (MicroPact) | `micropact.co.henry.ga.us/RESearch/RESearch` | Footer "© 2026 Tyler Technologies v1.1.7.0"; disclaimer: "no charge for this access"; Good-Thru dates Deeds 08/18 / Liens 08/19/2026. **Open.** Legacy gated Cott portal at `cotthosting.com/gahenry/User/Login.aspx` still resolves |
| 10 | Hall | **GSCCCA** (statewide) | via `gsccca.org/search` | hallclerk.com Real Estate pages route to gsccca.org (account required). Gated/Paid |

**GA tally (10 counties established):** GSCCCA statewide 5 (Fulton, Gwinnett,
Clayton, Chatham, Hall — all Gated/Paid) · Landmark Web 3 (Cobb, DeKalb,
Cherokee — all open) · Cott eSearch 1 (Forsyth — open) · Tyler RE Search 1
(Henry — open) · Unknown vendors: 0, but **GSCCCA is a new system category**
(statewide consortium) and Cott + Tyler RE Search are first live fingerprints
for previously reported-only products.

**Georgia's trend twist: half the top 10 has NO open county portal — the
statewide GSCCCA consortium is the only online route, and it's paywalled.
The other half is business as usual: Landmark (shipped handler!) took the
big suburban counties, and every county-run portal we touched is open.**

## 5. National footprint (vendor claims — treat as marketing numbers)

| Rank (approx.) | Vendor | Claimed footprint | Source |
|---|---|---|---|
| 1 | Tyler Technologies (Eagle / Records Public Access) | Largest govtech vendor overall; Eagle recorder concentrated in the West/Southwest; hosted search network covers NM, PA, TX, WA | [countygovernmentrecords.com](https://www.countygovernmentrecords.com/) (VERIFIED landing); [tylertech.com](https://www.tylertech.com/solutions/public-administration/land-official-records/records-management) |
| 2 | GovOS (ex-Kofile software) → Neumo | "More than 700 government agencies" (all products, not just land records). **TX dominance confirmed by our sweep**: 7 of 11 established TX counties on Cloud Search | [Audax exit press, Aug 2025](https://sheaco.com/wp-content/uploads/2025/08/Audax-Private-Equity-Completes-Exit-of-GovOS.pdf); §3 sweep 2026-08-24 |
| 3 | Fidlar (Laredo/Tapestry) | Multi-state Midwest network; "all Fidlar counties" searchable from one Tapestry site (MN, WI, IL, IN, MI, KS seen); no exact count published on fidlar.com | [fidlar.com](https://www.fidlar.com/); [Lyon Co. KS](https://www.lyoncountyks.gov/246/Register-of-Deeds-Records-Search) |
| 4 | Cott Systems | "over 300 local offices across 21 states"; first live deployment fingerprinted 2026-08-24 (Forsyth GA eSearch) | [cottsystems.com](https://cottsystems.com/); §4 sweep |
| 5 | Catalis (Pioneer Landmark + Benchmark + more) | 30+ companies rolled up; Landmark dominant in FL, expanding (Cherokee Co. GA, Adams Co. CO, Seattle WA wins) | [govtech.com](https://www.govtech.com/biz/after-30-acquisitions-government-brands-rebrands-as-catalis); [ptghome.com](https://www.ptghome.com/) (→ catalisgov.com) |
| 6 | Harris (HRS Acclaim + Aumentum + OnCore legacy) | FL-dominant on Acclaim; Aumentum adds large-county recorder deployments nationally (ex-Thomson Reuters book) | [PRWeb](https://www.prweb.com/releases/harris_recording_solutions_announces_acclaim_upgrade/prweb11929075.htm); [pitchbook](https://pitchbook.com/profiles/company/436305-52) |
| 7 | i3 Verticals / BIS (TitleSearcher) | AR, TN, KY, VA, NC, SC counties | [titlesearcher.com](https://www.titlesearcher.com/) |
| 8 | US Land Records network | 15 states (Northeast-heavy) | [uslandrecords.com](https://www.uslandrecords.com/) |
| — | NewVision Systems | Small (CT + a few FL counties) but holds 3 FL counties incl. Polk | [newvisionsystems.com](https://webhost01.newvisionsystems.com/officialrecords.aspx) |

No independent, current per-county census exists; these are the best sourced
claims as of 2026-08-24.

## 6. Access regime + export capability per vendor

Never auto-register or enter payment anywhere (router rule). Regime is
**per-deployment** — vendor is a prior, not a guarantee.

| Vendor | Regime (norm) | Export / bulk | Automation outlook |
|---|---|---|---|
| Acclaim (classic & v2) | **Open** — anonymous after disclaimer (classic) or straight in (v2) | `Search/ExportCsv` returns full result set in one GET (GT, Brevard). Legal-description column population varies by county (Broward empty) | Best-in-class; handler shipped |
| Landmark Web | **Open** — anonymous search tiles; "Subscriber Log On" exists but is optional for index search (all 6 FL deployments landed on open tiles) | XLSX export verified (Palm Beach, 93 rows/wk; reCAPTCHA = 1 human click per search); legals ride in pre-parsed columns | **Handler shipped** (Palm Beach 3/3) |
| NewVision BrowserView | **Open** — anonymous | Print Results TSV verified (Polk, 79 docs/wk, no CAPTCHA); has "Verified as of" freshness banner | **Handler shipped** (Polk 3/3); Osceola on identical app |
| NewVision SearchNG | Open in theory, but **ClickOnce desktop app** | n/a | Do not attempt browser automation (Marion) |
| Aumentum Public Access | **Open** — disclaimer then anonymous search (both UI variants) | Unknown; ASP.NET grid | Moderate; covers Orange (if confirmed) + Alachua |
| OnCore (legacy) | **Open** — "Anonymous / Public Access" group | Unknown | Low priority; shrinking install base (migrations to Acclaim) |
| GovOS Cloud Search (Neumo) | **Open** — anonymous; Register/Sign In optional (needed only for purchases/cart). **Export button IS login-gated** | Grid transcription (full labeled-token legals incl. city render in-grid, untruncated); results URL is a constructible GET; doc images viewable anonymously; no case numbers | **Handler shipped** (Dallas 3/3, 2026-08-24) — 7 TX counties incl. 6 of top 10, one uniform app |
| Custom FL portals | All **open** in our sample (Miami-Dade, Hillsborough, Volusia, Pasco, Leon, Collier, Manatee, Charlotte) | Pasco/Leon/Volusia are plain server-rendered forms (easy scrape, no export button); SPAs (Miami-Dade, Hillsborough, Collier) have JSON backends worth sniffing | Per-county one-offs |
| Custom TX portals | Both **open** (Harris "Web Inquiry" form; El Paso plain form with LIS PENDENS doc type) | Harris: server-rendered ASP.NET, rich criteria; El Paso: 10-docs-per-view cap | Harris is the #3 US county by population — worth a one-off |
| Tyler Eagle | **Gated** — document search requires account (GT prior recon); Tyler markets subscription "Records Public Access" | n/a for us | Skip (also: no FL) |
| Fidlar Laredo / Tapestry | **Paid** — Laredo subscription; Tapestry pay-per-search with account | n/a for us | Skip (also: no FL) |
| i3/BIS TitleSearcher | **Paid** membership | n/a | Skip |
| Cott eSearch | **Open as guest** at Forsyth GA (named-user login optional); `cotthosting.com` deployments seen gated (Henry GA legacy) — regime per-deployment | Unknown; ASP.NET postback UI, results untested | Single GA top-10 county so far; revisit if more Cott counties appear |
| Tyler RE Search (MicroPact) | **Open** — "no charge" per county disclaimer; free account only for fraud alerts | Unknown; has per-class Good-Thru dates | Single county (Henry GA) so far |
| GSCCCA (GA statewide) | **Gated/Paid** — forms load anonymously, search execution bounces to login; $5/4hr day pass or subscription | n/a for us (never pay/register) | Covers ALL 159 GA counties incl. 5 of top 10 with no county alternative. User-assisted route only: user logs into their own GSCCCA account, we drive the search after |
| Kofile/GovOS QuickLink | **Open** (Polk) | Index-book images only — not a lead source | Not useful for pipeline |
| US Land Records | Free index search typical, paid images | Unknown | No FL; revisit for Northeast expansion |

## 7. Recommended handler build order (re-ranked 2026-08-24 with TX + GA sweeps)

Shipped so far: **Acclaim** (Brevard pipeline), **Landmark Web** (Palm Beach
verified 3/3), **NewVision BrowserView** (Polk verified 3/3), **Tyler
Self-Service** (Orange verified 3/3), **GovOS Cloud Search** (Dallas verified
3/3, 2026-08-24 — grid-transcription ingest, native export login-gated; six
sister TX counties are unverified candidates in `counties.json`) — see
vendor-router capability matrix.

1. **Aumentum Public Access** — strengthened by TX: Alachua FL + Travis TX +
   Fort Bend TX, all on the identical ASP.NET variant (Version 2023.1.2), open.
   One handler now covers 3 counties across 2 states; the JSP variant can wait.
2. **Remaining GovOS counties** — DONE 2026-08-24: Tarrant, Bexar, Denton
   verified 3/3 (see vendor-router capability matrix); Collin + Hidalgo
   pull-verified with documented caveats (detail-page legals; Collin parties
   undifferentiated); **Cameron has zero LP supply in the OR index** (full-year
   search empty — district-clerk filings suspected). GovOS now = 4 verified +
   2 partial of 7 counties.
3. **High-value custom one-offs, easiest first** — FL: Pasco (#12, classic ASP —
   trivial), Leon (#22), Volusia (#11). TX: **Harris (#1 TX / #3 US)** — open
   server-rendered ASP.NET "Web Inquiry" with rich criteria; El Paso (plain
   form, has LIS PENDENS type, 10-doc view cap). Then the SPA heavyweights via
   backend-API sniffing: Miami-Dade, Hillsborough, Collier. Sarasota
   (OnCore-style) fits here too.
4. **Remaining Landmark/NewVision counties** — extend shipped handlers'
   capability rows: Lee (Akamai interstitial — user-assisted), St. Johns, Clay,
   Hernando, Escambia; Osceola (BrowserView, expected identical to Polk);
   **GA: Cobb (#3), DeKalb (#4), Cherokee (#7)** — the shipped Landmark handler's
   cheapest new-state expansion (verify per-county capability rows, GA legals are
   land-lot/district style so join strategies need GA appraiser mapping).
5. **DuProcess (Seminole)** — single FL county, JS app; do when Seminole matters.
6. **Skip for now:** GSCCCA (gated/paid — the only route for 5 of GA's top 10;
   revisit as a **user-assisted** flow where the user logs into their own
   account first), Tyler Eagle (gated; TX presence is small-county via
   `countygovernmentrecords.com`), Fidlar (paid), TitleSearcher (paid),
   US Land Records / Vanguard CI / Granicus (no footprint in our states).
   Cott eSearch (Forsyth GA) + Tyler RE Search (Henry GA): open but one county
   each — build when those counties matter. Charlotte FL's unidentified portal:
   fingerprint again when a handler pass reaches it. QuickLink historic books:
   not a lead source.

With GovOS shipped (Dallas verified; 6 sister counties pending per-county
verification), adding Aumentum would take vendor-level coverage to **17 of
FL's 30 established counties (incl. 8 of top 10) and 9 of TX's 11 (incl. 8 of
top 10)**.
