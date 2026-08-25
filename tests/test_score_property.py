"""Multi-lens deal-scorecard tests: three lenses (cashflow/margin/motivation),
each 0-100 + confidence, plus a best-available tier. Config-driven, explainable,
honest about missing data (a missing input -> None + NONE confidence, never a
fabricated number; a missing lens never buries the tier).
"""
import copy
import json
import sys
from pathlib import Path

_SCRIPTS = (Path(__file__).resolve().parents[1]
            / "plugins" / "crei" / "skills" / "score-property" / "scripts")
sys.path.insert(0, str(_SCRIPTS))

from lenses import (cashflow_lens, margin_lens, motivation_lens, overall_tier,
                    score_property)

CFG = json.loads((_SCRIPTS.parent / "config" / "scoring.json").read_text(encoding="utf-8"))
FIX = Path(__file__).resolve().parent / "fixtures"


def fixture(name):
    return json.loads((FIX / name).read_text(encoding="utf-8"))


# --- archetypes -------------------------------------------------------------

def test_strong_cashflow_low_margin_is_B():
    card = score_property(fixture("sp_strong_cashflow_low_margin.json"), CFG)
    assert card["lenses"]["cashflow"]["score"] >= 65
    assert card["lenses"]["cashflow"]["confidence"] == "HIGH"
    assert card["lenses"]["margin"]["score"] < 60
    assert card["tier"] == "B"          # one strong lens


def test_high_margin_flip_is_B():
    card = score_property(fixture("sp_high_margin_flip.json"), CFG)
    assert card["lenses"]["margin"]["score"] >= 99
    assert card["lenses"]["margin"]["confidence"] == "HIGH"     # ARV-based
    assert card["lenses"]["cashflow"]["score"] < 25            # negative cash flow
    assert card["tier"] == "B"          # strong margin offsets weak cashflow


def test_distressed_motivated_not_buried():
    card = score_property(fixture("sp_distressed_motivated.json"), CFG)
    mot = card["lenses"]["motivation"]
    assert mot["layer"] == "distress"
    assert mot["confidence"] == "HIGH"
    assert card["lenses"]["margin"]["confidence"] == "NONE"     # Zestimate suppressed
    assert card["lenses"]["margin"]["score"] is None
    assert card["tier"] != "D"          # don't-bury rule (tiers on motivation alone)


# --- cashflow lens ----------------------------------------------------------

def test_cashflow_anchor_follows_priority():
    facts = {"available": True, "scenarios": {
        "user_estimate": {"dscr": 1.3, "cash_flow": 100},
        "zillow_rent_zestimate": {"dscr": 2.0, "cash_flow": 900}}}
    assert cashflow_lens(facts, CFG["cashflow"])["anchor"] == "user_estimate"


def test_cashflow_zillow_anchor_downgrades_confidence():
    facts = {"available": True, "scenarios": {
        "zillow_rent_zestimate": {"dscr": 1.6, "cash_flow": 500}}}
    assert cashflow_lens(facts, CFG["cashflow"])["confidence"] == "MED"


def test_dscr_below_floor_scores_zero():
    facts = {"available": True, "rent_grounded": True,
             "scenarios": {"user_estimate": {"dscr": 0.85, "cash_flow": -100}}}
    assert cashflow_lens(facts, CFG["cashflow"])["score"] == 0


def test_dscr_strong_and_cashflow_full_scores_100():
    facts = {"available": True, "rent_grounded": True,
             "scenarios": {"user_estimate": {"dscr": 1.6, "cash_flow": 400}}}
    assert cashflow_lens(facts, CFG["cashflow"])["score"] == 100


def test_financing_default_downgrades_to_low():
    facts = {"available": True, "financing_is_default": True,
             "scenarios": {"user_estimate": {"dscr": 1.6, "cash_flow": 500}}}
    assert cashflow_lens(facts, CFG["cashflow"])["confidence"] == "LOW"


# --- margin lens ------------------------------------------------------------

def test_margin_zestimate_suppression_yields_none():
    listing = {"available": True, "price": 480000, "zestimate": None,
               "status": "FORECLOSURE"}
    r = margin_lens(listing, {}, CFG["margin"])
    assert r["score"] is None and r["confidence"] == "NONE"


def test_margin_uses_arv_over_zestimate():
    listing = {"available": True, "price": 300000, "zestimate": 350000,
               "status": "FOR_SALE"}
    r = margin_lens(listing, {"arv": 400000}, CFG["margin"])
    assert r["score"] == 100 and r["confidence"] == "HIGH"     # 25% equity on ARV
    assert "arv" in r["basis"]


def test_margin_never_treats_null_value_as_zero():
    # No value at all -> None, not a 100% "free" margin.
    listing = {"available": True, "price": 200000, "zestimate": None,
               "status": "FOR_SALE"}
    assert margin_lens(listing, {}, CFG["margin"])["score"] is None


# --- motivation lens (layered) ----------------------------------------------

def test_motivation_listing_baseline_fires_on_stale_fsbo():
    facts = {"listing_signals": {"available": True, "days_on_market": 100,
                                 "status": "FOR_SALE", "fsbo": True}}
    r = motivation_lens(facts, CFG["motivation"])
    assert r["layer"] == "listing"
    assert r["score"] == 40            # DOM>=90 (+25) + FSBO (+15)
    assert r["confidence"] == "MED"


def test_motivation_upgrades_to_distress():
    facts = {"listing_signals": {"available": True, "days_on_market": 5,
                                 "status": "FOR_SALE"},
             "distress": {"available": True, "plaintiff_name": "PARRISH, MARY",
                          "defendant_name": "PARRISH, JOHN", "doc_type": "LIS PENDENS",
                          "record_age_days": 5, "owner": "PARRISH, JOHN",
                          "use_desc": "SINGLE FAMILY RESIDENCE", "homestead": True,
                          "tenure_years": 20}}
    r = motivation_lens(facts, CFG["motivation"])
    assert r["layer"] == "distress" and r["confidence"] == "HIGH"
    assert r["score"] >= 55            # FAMILY base + occupant + tenure


def test_motivation_institutional_owner_floored():
    facts = {"distress": {"available": True, "plaintiff_name": "SOME BANK NA",
                          "defendant_name": "PROLOGIS INDUSTRIAL REIT LLC",
                          "doc_type": "LIS PENDENS", "record_age_days": 5,
                          "owner": "PROLOGIS INDUSTRIAL REIT LLC",
                          "use_desc": "INDUSTRIAL WAREHOUSE", "market_value": 28000000}}
    r = motivation_lens(facts, CFG["motivation"])
    assert r["score"] == 0 and r["layer"] == "distress"


def test_motivation_none_when_no_signals():
    r = motivation_lens({}, CFG["motivation"])
    assert r["score"] is None and r["confidence"] == "NONE"


# --- overall tier -----------------------------------------------------------

def _lens(score):
    return {"score": score, "confidence": "HIGH", "contrib": {}, "basis": ""}


def test_two_strong_lenses_is_A():
    t = overall_tier(_lens(80), _lens(70), _lens(30), CFG["tiers"])
    assert t["tier"] == "A"


def test_missing_motivation_does_not_bury_tier():
    # strong cashflow, mid margin, motivation unavailable -> B, not buried.
    t = overall_tier(_lens(80), _lens(40),
                     {"score": None, "confidence": "NONE", "contrib": {}}, CFG["tiers"])
    assert t["tier"] == "B"


def test_single_available_lens_capped_at_B():
    none = {"score": None, "confidence": "NONE", "contrib": {}}
    t = overall_tier(_lens(95), none, none, CFG["tiers"])
    assert t["tier"] == "B" and t["lenses_available"] == 1


def test_disqualifying_cashflow_with_no_strong_is_D():
    # negative cash flow (below fail band), nothing strong -> D.
    t = overall_tier(_lens(10), _lens(40), _lens(20), CFG["tiers"])
    assert t["tier"] == "D"


def test_weak_motivation_alone_never_causes_D():
    # mid cashflow + mid margin + failing motivation -> C, not D.
    t = overall_tier(_lens(40), _lens(40), _lens(5), CFG["tiers"])
    assert t["tier"] == "C"


def test_all_unavailable_is_NR():
    none = {"score": None, "confidence": "NONE", "contrib": {}}
    assert overall_tier(none, none, none, CFG["tiers"])["tier"] == "NR"


# --- explainability + config-driven -----------------------------------------

def test_scores_are_explainable():
    card = score_property(fixture("sp_strong_cashflow_low_margin.json"), CFG)
    assert card["lenses"]["cashflow"]["contrib"]
    assert card["lenses"]["margin"]["contrib"]


def test_weights_come_from_config_not_code():
    facts = fixture("sp_strong_cashflow_low_margin.json")
    assert score_property(facts, CFG)["tier"] == "B"      # cashflow strong
    bumped = copy.deepcopy(CFG)
    bumped["tiers"]["strongBand"]["cashflow"] = 200       # nothing can be "strong"
    assert score_property(facts, bumped)["tier"] == "C"   # config moved the result


def test_no_number_invented_when_unavailable():
    facts = {"address": "x", "cashflow": {"available": False},
             "listing": {"available": False}, "valuation": {}, "motivation": {}}
    card = score_property(facts, CFG)
    assert all(card["lenses"][k]["score"] is None for k in card["lenses"])
    assert card["tier"] == "NR"
