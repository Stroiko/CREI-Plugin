"""Config-driven, explainable lead scoring.

score_lead returns {"score", "contributions"} where contributions maps each
FIRED signal to the points it added; they always sum to the score. Weights
live in config/scoring.json only - nothing is hardcoded here.
"""
import re

_ASSOCIATION = re.compile(r"\b(ASSN|ASSOCIATION|HOA|CONDOMINIUM|HOMEOWNERS)\b")


def _recency_multiplier(cfg: dict, age_days) -> float:
    brackets = cfg.get("recencyMultipliers")
    if not brackets or age_days is None:
        return 1.0
    for bracket in sorted(brackets, key=lambda b: b["maxAgeDays"]):
        if age_days <= bracket["maxAgeDays"]:
            return bracket["multiplier"]
    return brackets[-1]["multiplier"]


def score_lead(lead: dict, scoring_cfg: dict) -> dict:
    cfg = scoring_cfg["signals"]
    sig = lead.get("signals", {})
    contributions = {}

    def fire(name, condition, multiplier=1.0):
        entry = cfg.get(name)
        if entry and condition and entry.get("weight", 0) != 0:
            contributions[name] = entry["weight"] * multiplier

    fire("lis_pendens", True,
         _recency_multiplier(cfg.get("lis_pendens", {}), lead.get("record_age_days")))
    fire("cc_case", lead.get("case_class") == "CC"
         or "-CC-" in (lead.get("case_number") or ""))
    fire("association_plaintiff",
         bool(_ASSOCIATION.search((lead.get("direct_name") or "").upper())))
    fire("absentee_owner", sig.get("absentee_owner"))
    fire("out_of_state_owner", sig.get("out_of_state_owner"))
    fire("entity_owned", sig.get("entity_owned"))
    tenure = sig.get("tenure_years")
    min_years = cfg.get("long_tenure", {}).get("minYears", 10)
    fire("long_tenure", tenure is not None and tenure >= min_years)
    fire("vacant_land_flag", sig.get("vacant_land_flag"))
    fire("provisional_record", lead.get("provisional"))

    return {"score": round(sum(contributions.values()), 2),
            "contributions": contributions}
