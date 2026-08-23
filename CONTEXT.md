# CONTEXT

Glossary for the CREI (Claude Real Estate Investing) plugin. Terms here are canonical — use them exactly.

## Terms

- **Lead** — the property owner named as `IndirectName` (defendant) on a recorded distress document, joined to a parcel. The plaintiff (`DirectName`) is never the lead.
- **Layer A** — browser work run locally through Claude in Chrome (county record portals, Zillow). Ships as SKILL.md instructions, not code.
- **Layer B** — deterministic parse/join/score code run in the Cowork sandbox on the CSV Layer A produced. Ships as bundled Python scripts.
- **Vendor** — the software platform a county's record portal runs on (Acclaim, Tyler Eagle, Kofile, …). Detected by fingerprint, never assumed.
- **Access regime** — whether a specific county deployment is **Open** (anonymous search reachable after accepting a disclaimer) or **Gated** (mandatory login). Per-deployment, not per-vendor. Open → automate; Gated → the user logs in themselves; never auto-create accounts or enter payment.
- **Signal stacking** — scoring a property on multiple co-occurring distress signals (lis pendens + absentee owner + long tenure + …). The product's differentiator; every score must be explainable from `scoring.yaml`.
- **Released-through date** — the high-water mark shown in the Acclaim results banner. Records past it exist but are not yet released; never query beyond it.
- **Provisional record** — a CSV row flagged `U` (recorded but not yet released). Kept and flagged, re-checked later.
- **Review file** — the destination for any record that fails to parse or join (e.g. metes-and-bounds legal descriptions). Records are never silently dropped.
- **Parcel ID construction** — building a county parcel/tax account ID directly from a parsed legal description (e.g. Brevard `TT-RR-SS-SUBID-BLOCK-LOT`). County-specific; verified per county before use.
- **Case-type token** — the classifier inside `CaseNumber` (`-CA-` = Circuit Civil = mortgage foreclosure; `-CC-` = County Civil = HOA/condo lien). `-CC-` cases are prioritized (small liens, high-equity owners, low competition).

## Boundaries

- The plugin produces a ranked lead list and stops. No contacting, skip-tracing, or soliciting owners — ever.
- Pulled records name individuals in financial distress (PII): they live only in gitignored `data/` and `output/` directories.
