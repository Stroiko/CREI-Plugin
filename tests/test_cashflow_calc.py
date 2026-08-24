"""Cashflow calculator tests: amortization, age tiers, DSCR, explainable line items.

The screenshot case mirrors Kevin's rental-analysis app: $89,500 purchase,
20% down, 6.5%/30yr, rent $1,551, tax $200/mo, insurance 5%, maintenance 10%,
management 10% -> P&I $452.56, cash flow $433.14.
"""
import json
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "plugins" / "crei" / "skills" / "rental-cashflow" / "scripts"))

from calc import (
    analyze,
    dscr,
    monthly_pi,
    normalize_rate,
    parse_down_payment,
    pct_tier,
)

DEFAULTS_PATH = (Path(__file__).resolve().parents[1]
                 / "plugins" / "crei" / "skills" / "rental-cashflow"
                 / "config" / "defaults.json")


def load_defaults():
    return json.loads(DEFAULTS_PATH.read_text())


TIERS = [
    {"maxAgeYears": 10, "pct": 0.05},
    {"maxAgeYears": 30, "pct": 0.075},
    {"maxAgeYears": 9999, "pct": 0.10},
]


def screenshot_input(**over):
    base = {
        "property": {
            "address": "123 Example St, Palm Bay, FL 32905",
            "zip": "32905",
            "bedrooms": 3,
            "year_built": 1980,
            "purchase_price": 89500,
            "hoa_monthly": None,
            "property_tax_monthly": 200,
            "insurance_monthly": None,
        },
        "financing": {
            "down_payment": "20%",
            "interest_rate": 6.5,
            "interest_only": False,
            "term_years": 30,
        },
        "rent_scenarios": [{"label": "user_airv", "rent": 1551}],
        "overrides": {"capex_pct": 0.0},
        "as_of_year": 2026,
    }
    base.update(over)
    return base


# ---------------------------------------------------------------- amortization

def test_monthly_pi_known_good():
    assert monthly_pi(200000, 0.07, 30) == pytest.approx(1330.60, abs=0.05)


def test_monthly_pi_screenshot():
    assert monthly_pi(71600, 0.065, 30) == pytest.approx(452.56, abs=0.02)


def test_monthly_pi_interest_only():
    assert monthly_pi(200000, 0.07, 30, interest_only=True) == pytest.approx(1166.67, abs=0.01)


def test_monthly_pi_zero_rate():
    assert monthly_pi(180000, 0.0, 30) == pytest.approx(500.0)


def test_monthly_pi_15yr_term():
    assert monthly_pi(200000, 0.07, 15) == pytest.approx(1797.66, abs=0.05)


# ------------------------------------------------------------- input parsing

def test_normalize_rate_percent_and_decimal():
    assert normalize_rate(6.5) == pytest.approx(0.065)
    assert normalize_rate(0.065) == pytest.approx(0.065)


def test_parse_down_payment_percent_vs_dollars():
    assert parse_down_payment("20%", 89500) == pytest.approx(17900)
    assert parse_down_payment(17900, 89500) == pytest.approx(17900)


# ----------------------------------------------------------------- age tiers

def test_pct_tier_boundaries():
    assert pct_tier(10, TIERS)[0] == 0.05
    assert pct_tier(11, TIERS)[0] == 0.075
    assert pct_tier(30, TIERS)[0] == 0.075
    assert pct_tier(31, TIERS)[0] == 0.10


def test_pct_tier_unknown_age_is_conservative_and_flagged():
    pct, basis = pct_tier(None, TIERS)
    assert pct == 0.10
    assert "unknown" in basis.lower()


# --------------------------------------------------------------------- DSCR

def test_dscr_value():
    assert dscr(12000, 10000) == pytest.approx(1.2)


def test_dscr_no_debt():
    assert dscr(12000, 0) is None


# ------------------------------------------------------------------ analyze

def modes(result, scenario=0):
    return result["scenarios"][scenario]["modes"]


def lines_by_item(mode):
    return {l["item"]: l for l in mode["lines"]}


def test_analyze_matches_app_screenshot():
    result = analyze(screenshot_input(), load_defaults())
    managed = modes(result)["managed"]
    li = lines_by_item(managed)
    assert li["mortgage_pi"]["amount"] == pytest.approx(452.56, abs=0.01)
    assert li["vacancy"]["amount"] == pytest.approx(77.55, abs=0.01)
    assert li["management"]["amount"] == pytest.approx(155.10, abs=0.01)
    assert li["insurance"]["amount"] == pytest.approx(77.55, abs=0.01)
    assert li["property_tax"]["amount"] == pytest.approx(200.00, abs=0.01)
    assert li["maintenance"]["amount"] == pytest.approx(155.10, abs=0.01)
    assert li["hoa"]["amount"] == 0.0
    assert li["cash_flow"]["amount"] == pytest.approx(433.14, abs=0.01)


def test_analyze_self_managed_differs_by_management_fee():
    result = analyze(screenshot_input(), load_defaults())
    m = modes(result)
    managed_cf = lines_by_item(m["managed"])["cash_flow"]["amount"]
    self_cf = lines_by_item(m["self_managed"])["cash_flow"]["amount"]
    assert lines_by_item(m["self_managed"])["management"]["amount"] == 0.0
    assert self_cf - managed_cf == pytest.approx(155.10, abs=0.01)


def test_analyze_lines_foot_exactly():
    inp = screenshot_input()
    inp["rent_scenarios"] = [{"label": "odd", "rent": 1234.56}]
    inp["overrides"] = {}
    result = analyze(inp, load_defaults())
    for mode in modes(result).values():
        li = lines_by_item(mode)
        expenses = ["mortgage_pi", "management", "insurance", "property_tax",
                    "maintenance", "capex", "hoa"]
        total = round(li["gross_rent"]["amount"] - li["vacancy"]["amount"]
                      - sum(li[e]["amount"] for e in expenses), 2)
        assert li["cash_flow"]["amount"] == pytest.approx(total, abs=0.001)
        assert li["effective_rent"]["amount"] == pytest.approx(
            round(li["gross_rent"]["amount"] - li["vacancy"]["amount"], 2), abs=0.001)


def test_analyze_dscr_noi_convention():
    # NOI (managed) = effective rent - mgmt - ins - tax - maintenance - hoa,
    # capex excluded. 885.70*12 / (452.56...*12) ~= 1.957
    result = analyze(screenshot_input(), load_defaults())
    managed = modes(result)["managed"]
    assert managed["dscr"] == pytest.approx(1.957, abs=0.01)
    assert managed["dscr_verdict"] == "PASS"


def test_analyze_dscr_rent_over_pitia_matches_app():
    # Kevin's app shows 2.12 = gross rent / (P&I + tax + insurance + HOA)
    defaults = load_defaults()
    defaults["dscr"]["method"] = "rent_over_pitia"
    result = analyze(screenshot_input(), defaults)
    assert modes(result)["managed"]["dscr"] == pytest.approx(2.12, abs=0.01)


def test_analyze_dscr_include_capex_toggle():
    defaults = load_defaults()
    defaults["dscr"]["include_capex_in_noi"] = True
    inp = screenshot_input()
    inp["overrides"] = {}  # real capex tier applies (31+ -> 10% = 155.10)
    with_capex = modes(analyze(inp, defaults))["managed"]["dscr"]
    without = modes(analyze(inp, load_defaults()))["managed"]["dscr"]
    assert with_capex < without


def test_analyze_dscr_pass_boundary():
    assert dscr(12000, 10000) == pytest.approx(1.2)
    result = analyze(screenshot_input(), load_defaults())
    assert modes(result)["managed"]["dscr_verdict"] in ("PASS", "FAIL")
    # verdict is PASS at exactly the threshold
    defaults = load_defaults()
    defaults["dscr"]["pass_threshold"] = modes(result)["managed"]["dscr"]
    again = analyze(screenshot_input(), defaults)
    assert modes(again)["managed"]["dscr_verdict"] == "PASS"


def test_analyze_no_debt_dscr_na():
    inp = screenshot_input()
    inp["financing"]["down_payment"] = "100%"
    result = analyze(inp, load_defaults())
    managed = modes(result)["managed"]
    assert lines_by_item(managed)["mortgage_pi"]["amount"] == 0.0
    assert managed["dscr"] is None
    assert "N/A" in managed["dscr_verdict"]


def test_analyze_hoa_absent_flagged():
    result = analyze(screenshot_input(), load_defaults())
    hoa = lines_by_item(modes(result)["managed"])["hoa"]
    assert hoa["amount"] == 0.0
    assert "not provided" in hoa["basis"].lower()


def test_analyze_overrides_beat_defaults():
    inp = screenshot_input()
    inp["overrides"] = {"vacancy_pct": 0.08, "capex_pct": 0.0}
    result = analyze(inp, load_defaults())
    vac = lines_by_item(modes(result)["managed"])["vacancy"]
    assert vac["amount"] == pytest.approx(round(1551 * 0.08, 2), abs=0.001)
    assert "override" in vac["basis"].lower()


def test_analyze_tax_fallback_when_missing():
    inp = screenshot_input()
    inp["property"]["property_tax_monthly"] = None
    result = analyze(inp, load_defaults())
    tax = lines_by_item(modes(result)["managed"])["property_tax"]
    # 1.1%/yr of 89500 / 12 = 82.04
    assert tax["amount"] == pytest.approx(82.04, abs=0.01)
    assert "estimate" in tax["basis"].lower() or "fallback" in tax["basis"].lower()


def test_analyze_maintenance_tier_from_year_built():
    inp = screenshot_input()
    inp["property"]["year_built"] = 2020  # age 6 -> 5% tier
    inp["overrides"] = {}
    result = analyze(inp, load_defaults())
    maint = lines_by_item(modes(result)["managed"])["maintenance"]
    assert maint["amount"] == pytest.approx(round(1551 * 0.05, 2), abs=0.001)


def test_analyze_multiple_scenarios():
    inp = screenshot_input()
    inp["rent_scenarios"] = [
        {"label": "zillow_rent_zestimate", "rent": 1600},
        {"label": "hud_fmr_3br", "rent": 1450},
    ]
    result = analyze(inp, load_defaults())
    assert [s["label"] for s in result["scenarios"]] == [
        "zillow_rent_zestimate", "hud_fmr_3br"]
    assert result["assumptions"]  # every run echoes its assumptions
