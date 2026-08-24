---
name: rental-cashflow
description: >
  Compute monthly cash flow, expense breakdown, and DSCR for a rental property
  under multiple rent scenarios (Zillow Rent Zestimate, HUD Section 8 FMR, and
  the user's own rent estimate). Use whenever the user asks "does this deal
  cash flow", "what's the cash flow on <address>", "rental analysis", "run the
  numbers", "would this rent for enough", "DSCR", "is this a good rental", or
  wants PITI / operating-expense math on an investment property.
compatibility: >
  Requires a Python 3 code-execution environment for the bundled scripts
  (stdlib only, no pip installs). Rent scenarios optionally use the zillow
  skill (browser) and the hud-fmr skill (browser); the calculator itself works
  offline with user-supplied numbers.
---

# Rental Cashflow Skill

## What this skill does and does not do

**Does:** build a line-item monthly cash flow statement (PITI + operating
expenses) for each available rent scenario, always showing BOTH self-managed
and property-managed cases, plus a DSCR estimate. Every number carries its
basis — which default, tier, or override produced it.

**Does not:** give lending or investment advice. The DSCR verdict is a screen
against a configurable threshold (default 1.20), not a lender decision. All
defaults are estimates for screening; real quotes (insurance, tax, HOA) always
beat them.

## Pipeline at a glance

1. **Gather property facts** — from the zillow skill, county records, or the user.
2. **Build rent scenarios** — Zillow Rent Zestimate + HUD Section 8 FMR + user's own estimate.
3. **Compute** — write one input JSON, run `cashflow.py analyze` once.
4. **Present** — side-by-side tables + assumptions, always.

---

## Stage 1 — Gather property facts

If the user gives an address or Zillow URL, invoke the **zillow skill** (do
not duplicate its scraping logic). It returns `price`, `beds`, `baths`,
`year_built`, `rent_zestimate`, and the ZIP.

Facts Zillow can NOT provide — get these from the user or county records:

| Fact | Source | If missing |
|---|---|---|
| Property tax ($/mo) | County appraiser / tax roll (county-records skill enrichment carries it) | Fallback estimate: 1.1%/yr of price — **say so loudly**, it is the least reliable default |
| HOA ($/mo) | User / listing | $0, flagged "not provided" |
| Insurance ($/mo) | User's real quote | 5% of gross rent (mirrors Kevin's analysis app) |

Financing inputs: purchase price (or offer), down payment (`"20%"` or dollars),
interest rate, interest-only toggle, term (default 30yr).

## Stage 2 — Build rent scenarios

Assemble up to three; **a missing source is skipped with a note, never blocks**:

1. `zillow_rent_zestimate` — from Stage 1's zillow output.
2. `hud_fmr_{beds}br` — invoke the **hud-fmr skill** with the property's ZIP
   and bedroom count. Record the FY year and whether the value was a ZIP-level
   SAFMR or a county-wide FMR.
3. `user_estimate` — any rent the user supplies (their own AIRV/comp figure).

## Stage 3 — Compute

Write the input JSON (schema below) to a work dir (`output/` is gitignored),
then run the calculator ONCE — it computes every scenario × both management
modes internally:

```
python ${CLAUDE_PLUGIN_ROOT}/skills/rental-cashflow/scripts/cashflow.py analyze \
    --input output/work/property.json --out output/work/
```

Input schema (see `tests/fixtures/cashflow_property.json` for a live example):

```json
{
  "property": {"address": "...", "zip": "32905", "bedrooms": 3,
               "year_built": 1980, "purchase_price": 89500,
               "hoa_monthly": null, "property_tax_monthly": 200,
               "insurance_monthly": null},
  "financing": {"down_payment": "20%", "interest_rate": 6.5,
                "interest_only": false, "term_years": 30},
  "rent_scenarios": [{"label": "user_estimate", "rent": 1551}],
  "overrides": {}
}
```

- `down_payment`: `"20%"` or a dollar number. `interest_rate`: `6.5` or
  `0.065` (values > 1 are percents).
- `overrides` accepts `vacancy_pct`, `management_pct`, `maintenance_pct`,
  `capex_pct` (decimals). Null/absent = use `config/defaults.json`.
- Outputs: `analysis.json` (full breakdown + every assumption echoed) and
  `summary.md` (ready-to-show tables).

### The expense model (all defaults in `config/defaults.json`)

| Line | Default basis |
|---|---|
| Vacancy | 5% of gross rent |
| Management | 0% self-managed AND 10% managed — both always computed (typical range 8–10%) |
| Mortgage P&I | standard amortization; interest-only supported |
| Insurance | real quote, else 5% of gross rent |
| Property tax | real figure, else 1.1%/yr of price (flagged) |
| Maintenance | age-tiered: 0–10yrs → 5%, 11–30 → 7.5%, 31+ → 10% of gross rent |
| CapEx | same age tiers as maintenance |
| HOA | provided figure, else $0 |

Unknown `year_built` → conservative oldest tier, flagged in the basis.

DSCR: default method `noi` = (effective rent − mgmt − insurance − tax −
maintenance − HOA) × 12 ÷ annual debt service; CapEx excluded (toggle
`dscr.include_capex_in_noi`). Alternative `dscr.method: "rent_over_pitia"` =
gross rent ÷ (P&I + tax + insurance + HOA) — the DSCR-lender convention
Kevin's app displays (its 2.12 figure). Pass threshold 1.20, configurable.

## Stage 4 — Present

Show `summary.md` as-is or reformat, but ALWAYS include:

- Both management modes (self-managed and managed) for every scenario.
- The FMR year and source (`safmr_zip` vs `county_fmr`) next to the HUD scenario.
- The assumptions list — every default used, every override, every fallback.
- The disclaimer line (already in summary.md).

## Error handling

| Situation | Action |
|---|---|
| Zillow blocked / no rent_zestimate | Drop that scenario with a note; continue |
| hud-fmr ZIP not in an FMR area | Drop that scenario with a note; continue |
| No rent source at all | Ask the user for a rent estimate — the calculator needs at least one scenario |
| No property tax figure | Compute with the fallback AND tell the user the tax line is an estimate |
| `cashflow.py` non-zero exit | Report the stderr; do not hand-compute a replacement |

## What NOT to do

- Never present a cash flow number without its assumptions.
- Never show only one management mode — exposing both is the point.
- Never treat the DSCR verdict as lender approval.
- Never hand-compute the breakdown in chat — run the script; it is the tested
  path and its lines always foot.
- Never commit work-dir JSON with a real owner's address to the repo
  (`output/` is gitignored for a reason).
