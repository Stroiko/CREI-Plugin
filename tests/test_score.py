"""Scoring tests: config-driven, explainable, contributions sum to the total."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "plugins" / "crei" / "skills" / "county-records" / "scripts"))

from score import score_lead

CFG = {
    "signals": {
        "lis_pendens": {"weight": 40, "recencyMultipliers": [
            {"maxAgeDays": 7, "multiplier": 1.0},
            {"maxAgeDays": 30, "multiplier": 0.8},
            {"maxAgeDays": 99999, "multiplier": 0.3}]},
        "cc_case": {"weight": 20},
        "association_plaintiff": {"weight": 10},
        "absentee_owner": {"weight": 15},
        "out_of_state_owner": {"weight": 10},
        "entity_owned": {"weight": 5},
        "long_tenure": {"weight": 10, "minYears": 10},
    }
}


def lead(**over):
    base = {
        "case_number": "05-2026-CA-044764-XXCA-BC",
        "direct_name": "BIG BANK NA",
        "record_age_days": 5,
        "signals": {
            "absentee_owner": False, "out_of_state_owner": False,
            "entity_owned": False, "tenure_years": 2.0,
            "vacant_land_flag": False, "enriched": True,
        },
    }
    base.update(over)
    return base


def test_fresh_lis_pendens_full_weight():
    r = score_lead(lead(), CFG)
    assert r["contributions"]["lis_pendens"] == 40.0


def test_stale_lis_pendens_reduced():
    r = score_lead(lead(record_age_days=60), CFG)
    assert r["contributions"]["lis_pendens"] == 40 * 0.3


def test_cc_case_and_association_stack():
    l = lead(case_number="05-2025-CC-059041-XXCC-BC",
             direct_name="HICKORY GREEN HOMEOWNERS ASSN INC")
    r = score_lead(l, CFG)
    assert r["contributions"]["cc_case"] == 20
    assert r["contributions"]["association_plaintiff"] == 10


def test_ca_case_no_cc_contribution():
    r = score_lead(lead(), CFG)
    assert "cc_case" not in r["contributions"]


def test_contributions_sum_to_score():
    l = lead(case_number="05-2025-CC-059041-XXCC-BC",
             direct_name="SUNSET SHORES CONDOMINIUM ASSOCIATION")
    l["signals"].update(absentee_owner=True, out_of_state_owner=True,
                        entity_owned=True, tenure_years=22.0)
    r = score_lead(l, CFG)
    assert abs(sum(r["contributions"].values()) - r["score"]) < 1e-9
    assert r["contributions"]["long_tenure"] == 10


def test_weights_come_from_config_not_code():
    doubled = {"signals": {**CFG["signals"],
                           "absentee_owner": {"weight": 30}}}
    l = lead()
    l["signals"]["absentee_owner"] = True
    assert score_lead(l, doubled)["contributions"]["absentee_owner"] == 30
