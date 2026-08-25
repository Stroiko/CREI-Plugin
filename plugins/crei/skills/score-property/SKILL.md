---
name: score-property
description: >
  Score a single property by address on a multi-lens DEAL scorecard — cash flow,
  built-in equity margin, and seller motivation — with an overall A/B/C/D tier.
  Composes the zillow, hud-fmr, and rental-cashflow skills. Use when the user
  asks "is <address> a good deal", "score this property", "grade this deal",
  "deal scorecard for <address>", "should I buy <address>", "rate this
  property", or wants a single-property investment verdict. NOT for a county
  lead list (that is county-records) — this scores ONE known property.
compatibility: >
  Requires a Python 3 code-execution environment for the scorer (stdlib only,
  no pip installs). Gathers inputs via the zillow and hud-fmr skills (browser)
  and the rental-cashflow skill (Python); each lens degrades gracefully with a
  confidence flag when its data is unavailable.
---

# Score Property Skill

## What this does and does not do

**Does:** given one address, gather listing/value (zillow), Section 8 rent
(hud-fmr), and cash-flow/DSCR (rental-cashflow), then emit a **deal scorecard** —
three independent 0-100 lenses, each with a confidence flag, plus an overall
**A/B/C/D tier**:

| Lens | Question | Built from |
|---|---|---|
| **CASHFLOW** | Does it pencil as a rental? | rental-cashflow's DSCR + monthly cash flow |
| **MARGIN** | Is there built-in equity? | list price vs value (ARV, else Zestimate) |
| **MOTIVATION** | Is the seller likely to deal? | Zillow listing signals; upgraded to the two-axis distress engine when a lis pendens + CAD data exist |

**Does not:** give investment advice, promise a value, or invent a number. A
lens with no data reports `NONE` confidence and a `—`, never a fabricated score.
A missing lens never buries the tier. For a whole county's distressed leads, use
**county-records**, not this.

## Pipeline at a glance

1. **Listing** — invoke the **zillow skill**; capture price, Zestimate, rent, status, days-on-market.
2. **Rent benchmark** — invoke the **hud-fmr skill** (ZIP + beds).
3. **Cash flow** — invoke the **rental-cashflow skill** (`cashflow.py analyze`); read back DSCR + cash flow.
4. **Motivation** — listing signals from step 1; *opportunistically* upgrade with distress/CAD data.
5. **Score** — write one `facts.json`, run `score_property.py score`.
6. **Present** — show `scorecard.md`; lead with the tier and the three lens rows.

---

## Stage 1 — Listing & value (zillow)

Invoke the **zillow skill** with the address (do not duplicate its scraping).
Capture `price`, `zestimate` (**null on foreclosure/auction listings — expected,
never treat as $0**), `rent_zestimate`, `status`, `days_on_zillow`, `beds`,
`year_built`, `home_type`. Zillow blocked → `listing.available = false`; MARGIN
and the listing-signal MOTIVATION baseline go `NONE`, CASHFLOW can still run on a
user-supplied rent/price.

## Stage 2 — Rent benchmark (hud-fmr)

Invoke the **hud-fmr skill** with the ZIP + bedroom count for the Section 8
scenario. Missing → drop that rent scenario, note it.

## Stage 3 — Cash flow (rental-cashflow — never hand-computed)

Invoke the **rental-cashflow skill**: assemble its input JSON (Zillow price +
rent scenarios: `zillow_rent_zestimate`, `hud_fmr`, `user_estimate`), run
`cashflow.py analyze`, and read `analysis.json`. Per scenario, take
`modes.self_managed.dscr` and `.cash_flow`. **Financing** (down payment, rate)
comes from the user or rental-cashflow's defaults — if defaulted, set
`financing_is_default: true` so CASHFLOW confidence drops to `LOW` and the
assumption is surfaced.

## Stage 4 — Motivation signals (layered)

- **Baseline (universal, from Stage 1):** `days_on_market`, `status`
  (FORECLOSURE / PRE_FORECLOSURE / AUCTION), and FSBO if known. These feed
  `motivation.listing_signals`.
- **Upgrade (opportunistic):** ONLY when you actually have a distress filing +
  appraiser data for this exact property — i.e. it came **from a county-records
  lead**, or the user handed you the lis pendens. There is **no address → lis
  pendens lookup**; do not fabricate one. When present, fill
  `motivation.distress` (plaintiff/defendant names, doc_type, record_age_days,
  owner, use_desc, market_value, homestead, absentee, tenure_years) — the scorer
  runs the two-axis motivation engine and flags it HIGH confidence.

## Stage 5 — Score

Write all gathered facts to `facts.json` (schema below) and run:

```
python ${CLAUDE_PLUGIN_ROOT}/skills/score-property/scripts/score_property.py score \
    --input output/work/facts.json --out output/work/
```

Writes `scorecard.json` + `scorecard.md`. Weights, thresholds, the cash-flow rent
anchor priority, and tier cutoffs live in `config/scoring.json` — the user may
edit them; never hardcode.

### `facts.json` schema

```json
{
  "address": "1603 Rio Cove Ct, Orlando FL 32825",
  "cashflow": {
    "available": true,
    "rent_grounded": true, "tax_is_estimate": false, "financing_is_default": false,
    "scenarios": {
      "user_estimate":        {"dscr": 1.34, "cash_flow": 210},
      "zillow_rent_zestimate":{"dscr": 1.21, "cash_flow": 60},
      "hud_fmr":              {"dscr": 1.05, "cash_flow": -80}
    }
  },
  "listing":   {"available": true, "price": 499000, "zestimate": 512000, "status": "FOR_SALE"},
  "valuation": {"arv": null},
  "motivation": {
    "listing_signals": {"available": true, "days_on_market": 62, "status": "FOR_SALE", "fsbo": false},
    "distress": {"available": false}
  }
}
```

Every lens block carries an `available` flag; when false, that lens is scored
`NONE`. `cashflow.scenarios` are keyed by label; the scorer picks the anchor per
`config` (`anchorPriority`, default `user_estimate → zillow_rent_zestimate →
hud_fmr`). Set only the `distress` keys you actually have.

## Stage 6 — Present

Show `scorecard.md` — the tier line, the three lens rows (score, confidence,
why), and the lens-detail bullets. Always keep the disclaimer. State plainly
which lenses were `NONE` and what data would fill them (e.g. "supply an ARV to
score MARGIN on this foreclosure").

## Partial-data handling

| Situation | Effect |
|---|---|
| Zillow blocked / no listing | MARGIN + listing-MOTIVATION → `NONE`; CASHFLOW still runs on user numbers |
| Zestimate suppressed (foreclosure/auction) | MARGIN → `NONE` unless the user supplies an ARV/comp — never score null as $0 |
| No HUD FMR for the ZIP | Drop that rent scenario; anchor falls to the next in priority |
| No rent source at all | CASHFLOW → `NONE`; ask the user for a rent estimate |
| Financing assumed (defaults) | CASHFLOW confidence → `LOW`; print the assumed rate/down payment |
| No distress filing for the address | MOTIVATION runs on listing signals only (the normal case for a cold address) |
| Every lens unavailable | Tier `NR` (not rated); say what's missing |

## Honesty caveats

- **The distress-motivation upgrade is opportunistic, not guaranteed.** There is
  no "address → its lis pendens" path; the two-axis layer fires for leads that
  came *from* county-records or a user-supplied filing. Cold addresses get
  listing-signal motivation only — that is expected, not a failure.
- **Zestimate is suppressed on exactly the distressed listings** a deal-finder
  wants; MARGIN needs an ARV/comp there. The don't-bury tier rule keeps those
  properties scoreable on their other lenses.
- **Cash flow is only as good as the financing assumptions** — surface them.
- The tier is a screen, not a buy signal or a lender decision.

## What NOT to do

- Never invent a value, rent, ARV, or distress filing to fill a lens — a `NONE`
  is the honest answer.
- Never hand-compute cash flow — invoke rental-cashflow; it is the tested path.
- Never treat a suppressed (null) Zestimate as a $0 value (would fake a 100% margin).
- Never commit `facts.json` with a real address to the repo (`output/` is gitignored).
- Never use this to build outreach or contact lists — it scores a property, full stop.
