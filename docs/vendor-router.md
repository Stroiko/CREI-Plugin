# Vendor router — fingerprints, regimes, and branch logic

All entries verified live 2026-08-23 unless noted. The router's job: given a
county, tell the user upfront whether the pipeline can run there.

## Step 1 — fingerprint the vendor

| Vendor | Fingerprint | Seen at |
|---|---|---|
| Acclaim classic | Footer "Acclaim, is a registered trademark of Harris Recording Solutions"; disclaimer gate; search tiles | Brevard, Pinellas, Broward |
| Acclaim v2 | "Welcome, Guest" header; "Copyright 1999–2026. Harris Recording Solutions"; Kendo widgets; no disclaimer gate | Highlands, St. Lucie |
| Tyler Eagle | `countygovernmentrecords.com` domains; Tyler footer | (prior recon) **login-gated** |
| Custom in-house | anything else — e.g. Manatee's "Public Records Hub" (MCCCC) | Manatee |

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
