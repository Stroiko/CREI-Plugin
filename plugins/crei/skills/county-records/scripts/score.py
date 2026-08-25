"""Config-driven, explainable two-axis lead scoring.

score_lead(lead, cfg) returns:
  motivation          0-100 call-order priority (always present)
  equity              0-100 deal-margin PROXY, or None when unenriched
  equity_confidence   HIGH | MED | LOW | NONE
  tier                A | A_UNVERIFIED | B | C | D
  motivation_contrib  {name: points} explaining the motivation score
  equity_contrib      {name: points} explaining the equity proxy

Weights live in config/scoring.json only - nothing is hardcoded here. Every
input comes from lead["signals"] (enrich.derive_signals + the plaintiff/family
classifiers) and lead["record_age_days"].
"""


def _recency_multiplier(brackets, age_days) -> float:
    if not brackets or age_days is None:
        return 1.0
    for b in sorted(brackets, key=lambda b: b["maxAgeDays"]):
        if age_days <= b["maxAgeDays"]:
            return b["multiplier"]
    return brackets[-1]["multiplier"]


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def _motivation(sig, age_days, cfg):
    contrib = {}
    # Institutional owners have no seller motivation, whatever else fires.
    if sig.get("owner_profile") == "INSTITUTIONAL":
        floor = float(cfg.get("institutionalFloor", 0))
        contrib["institutional_floor"] = floor
        return floor, contrib

    # A HIGH-confidence family match promotes the distress type to FAMILY;
    # a MED match keeps the individual base and adds a nudge (uncertain).
    ptype = sig.get("plaintiff_type", "UNKNOWN")
    fam = (sig.get("family_matter") or {}).get("confidence", "NONE")
    distress = "FAMILY" if fam == "HIGH" else ptype
    pt = cfg["plaintiffType"]
    base = pt.get(distress, pt.get("UNKNOWN", 20))
    recency = _recency_multiplier(cfg.get("recencyMultipliers"), age_days)
    contrib[f"distress:{distress}"] = round(base * recency, 1)

    if fam == "MED":
        nudge = cfg.get("familyMedNudge", 0)
        if nudge:
            contrib["family:MED"] = nudge

    occ = cfg.get("ownerOccupancy", {})
    if sig.get("owner_occupant"):
        contrib["owner_occupant"] = occ.get("OCCUPANT", 0)
    elif sig.get("absentee_owner") and sig.get("owner_profile") == "SMALL_INVESTOR":
        contrib["absentee_small_investor"] = occ.get("ABSENTEE_SMALL_INVESTOR", 0)

    if sig.get("out_of_state_owner"):
        contrib["out_of_state"] = cfg.get("outOfStateAddon", 0)

    lt = cfg.get("longTenure", {})
    tenure = sig.get("tenure_years")
    if tenure is not None and tenure >= lt.get("minYears", 10):
        contrib["long_tenure"] = lt.get("points", 0)

    total = _clamp(sum(contrib.values()), 0, cfg.get("cap", 100))
    return total, contrib


def _equity(sig, cfg):
    if not sig.get("enriched"):
        return None, "NONE", {}

    market = sig.get("market_value_num")
    gap = sig.get("assessed_gap")
    appr = sig.get("appreciation")
    tenure = sig.get("tenure_years")
    w = cfg.get("weights", {})
    contrib, comps = {}, []

    if market and gap is not None:
        v = min(1.0, max(0.0, gap / market) / cfg.get("capGapFullAtRatio", 0.35))
        comps.append((w.get("capGap", 0), v))
        contrib["cap_gap"] = round(w.get("capGap", 0) * v, 1)
    if market and appr is not None:
        v = min(1.0, max(0.0, appr / market) / cfg.get("appreciationFullAtRatio", 0.5))
        comps.append((w.get("appreciation", 0), v))
        contrib["appreciation"] = round(w.get("appreciation", 0) * v, 1)
    if tenure is not None:
        v = min(1.0, tenure / cfg.get("tenureFullAtYears", 25))
        comps.append((w.get("tenure", 0), v))
        contrib["tenure"] = round(w.get("tenure", 0) * v, 1)

    weight_sum = sum(wt for wt, _ in comps)
    if weight_sum == 0:
        return None, "NONE", {}

    base = sum(wt * v for wt, v in comps) / weight_sum * 100.0

    ptype = sig.get("plaintiff_type", "UNKNOWN")
    fam = (sig.get("family_matter") or {}).get("confidence", "NONE")
    prior_key = "FAMILY" if fam == "HIGH" else ptype
    prior = cfg.get("plaintiffPrior", {}).get(prior_key, 0)
    if prior:
        contrib[f"plaintiff_prior:{prior_key}"] = prior

    equity = _clamp(base + prior, 0, cfg.get("cap", 100))

    has_gap, has_appr = "cap_gap" in contrib, "appreciation" in contrib
    conf = "HIGH" if (has_gap and has_appr) else "MED" if (has_gap or has_appr) else "LOW"
    return equity, conf, contrib


def _tier(motivation, equity, owner_profile, cfg):
    if owner_profile == "INSTITUTIONAL" or motivation < cfg.get("motivationMed", 40):
        return "D"
    high_m = motivation >= cfg.get("motivationHigh", 60)
    if equity is None:
        return "A_UNVERIFIED" if high_m else "C"
    high_e = equity >= cfg.get("equityHigh", 55)
    if high_m and high_e:
        return "A"
    if high_m or high_e:
        return "B"
    return "C"


def score_lead(lead: dict, scoring_cfg: dict) -> dict:
    sig = lead.get("signals", {})
    motivation, m_contrib = _motivation(sig, lead.get("record_age_days"),
                                         scoring_cfg["motivation"])
    equity, e_conf, e_contrib = _equity(sig, scoring_cfg["equity"])
    tier = _tier(motivation, equity, sig.get("owner_profile"), scoring_cfg["tiers"])

    return {
        "motivation": round(motivation, 1),
        "equity": None if equity is None else round(equity, 1),
        "equity_confidence": e_conf,
        "tier": tier,
        "motivation_contrib": m_contrib,
        "equity_contrib": e_contrib,
        # legacy aliases so older readers of `score`/`contributions` still work
        "score": round(motivation, 1),
        "contributions": m_contrib,
    }
