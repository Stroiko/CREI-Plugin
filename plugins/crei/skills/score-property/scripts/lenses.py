"""Pure, config-driven lens functions for the property deal scorecard.

Three lenses, each 0-100 = a sum of named contributions clamped to `cap`
(mirroring county-records score.py). CONFIDENCE reflects which inputs fired,
never the score value. A missing input yields score None + confidence NONE - a
number is never invented. `overall_tier` reads the available lenses; a missing
lens is skipped, never scored 0, and never buries the tier.
"""
from classify import (classify_owner_profile, classify_plaintiff,
                      detect_family_matter, is_entity)

_CONF = {"NONE": 0, "LOW": 1, "MED": 2, "HIGH": 3}


def _clamp(x, lo, hi):
    return max(lo, min(hi, x))


def _lower(a, b):
    """The weaker of two confidence labels."""
    return a if _CONF[a] <= _CONF[b] else b


def _none_lens(basis):
    return {"score": None, "confidence": "NONE", "contrib": {}, "basis": basis}


# --- CASHFLOW ---------------------------------------------------------------

def _dscr_component(dscr, cfg):
    """Piecewise 0..1: floor->0, pass->passFraction, strong->1.0."""
    floor, pass_, strong = cfg["dscrFloor"], cfg["dscrPass"], cfg["dscrStrong"]
    pf = cfg.get("dscrPassFraction", 0.6)
    if dscr <= floor:
        return 0.0
    if dscr < pass_:
        return pf * (dscr - floor) / (pass_ - floor)
    if dscr < strong:
        return pf + (1 - pf) * (dscr - pass_) / (strong - pass_)
    return 1.0


def cashflow_lens(facts, cfg):
    """facts: {available, scenarios:{label:{dscr, cash_flow}}, anchor?,
    rent_grounded?, tax_is_estimate?, financing_is_default?}."""
    if not facts or not facts.get("available"):
        return _none_lens("no cash-flow analysis (rental-cashflow not run)")

    scenarios = facts.get("scenarios") or {}
    anchor = None
    for label in cfg["anchorPriority"]:
        if label in scenarios and scenarios[label] is not None:
            anchor = label
            break
    if anchor is None:
        return _none_lens("no rent scenario available to anchor cash flow")

    s = scenarios[anchor]
    dscr, cf = s.get("dscr"), s.get("cash_flow")
    contrib = {}

    cf_v = None
    if cf is not None:
        cf_v = _clamp((cf - cfg["cashflowFloorMonthly"])
                      / (cfg["cashflowFullAtMonthly"] - cfg["cashflowFloorMonthly"]),
                      0.0, 1.0)

    if dscr is not None and cf_v is not None:
        dv = _dscr_component(dscr, cfg)
        contrib["dscr"] = round(cfg["dscrWeight"] * dv, 1)
        contrib["cash_flow"] = round(cfg["cashflowWeight"] * cf_v, 1)
    elif dscr is None and cf_v is not None:
        # Cash purchase (no debt): score on cash flow alone, scaled to 100.
        contrib["cash_flow"] = round(100 * cf_v, 1)
    elif dscr is not None:
        dv = _dscr_component(dscr, cfg)
        contrib["dscr"] = round(100 * dv, 1)
    else:
        return _none_lens(f"anchor scenario '{anchor}' has no DSCR or cash flow")

    score = _clamp(sum(contrib.values()), 0, cfg["cap"])

    conf = "HIGH"
    if anchor == "zillow_rent_zestimate":
        conf = _lower(conf, "MED")          # optimistic estimate, not a real rent
    if not facts.get("rent_grounded", True):
        conf = _lower(conf, "MED")
    if facts.get("tax_is_estimate"):
        conf = _lower(conf, "MED")
    if facts.get("financing_is_default"):
        conf = _lower(conf, "LOW")          # assumed rate/down payment dominates

    return {"score": round(score, 1), "confidence": conf, "contrib": contrib,
            "anchor": anchor,
            "basis": f"anchored on {anchor}: DSCR {dscr}, cash flow {cf}/mo"}


# --- MARGIN -----------------------------------------------------------------

def margin_lens(listing, valuation, cfg):
    """listing: {available, price, zestimate, status}. valuation: {arv}."""
    listing = listing or {}
    valuation = valuation or {}
    if not listing.get("available"):
        return _none_lens("no listing data (Zillow not reached)")

    price = listing.get("price")
    arv = valuation.get("arv")
    zest = listing.get("zestimate")
    status = (listing.get("status") or "").upper()
    suppressed = status in cfg.get("suppressionStatuses", [])

    value, value_src = None, None
    for src in cfg["valuePriority"]:
        v = arv if src == "arv" else zest
        if v:
            value, value_src = v, src
            break

    if value is None:
        if suppressed:
            return _none_lens("Zestimate suppressed on distressed listing; "
                              "supply an ARV/comp to score margin")
        return _none_lens("no value (ARV or Zestimate) available")
    if not price:
        return _none_lens("no list price available")

    ratio = (value - price) / value
    floor, full = cfg["marginFloorRatio"], cfg["marginFullRatio"]
    score = _clamp(100 * (ratio - floor) / (full - floor), 0, cfg["cap"])

    if value_src == "arv":
        conf = "HIGH"
    elif suppressed:
        conf = "LOW"                        # distressed listing: Zestimate is shaky
    else:
        conf = "MED"

    return {"score": round(score, 1), "confidence": conf,
            "contrib": {"price_vs_value": round(score, 1)},
            "basis": f"{ratio:+.0%} equity vs {value_src} ${value:,.0f} "
                     f"(price ${price:,.0f})"}


# --- MOTIVATION (layered) ---------------------------------------------------

def _recency(brackets, age_days):
    if not brackets or age_days is None:
        return 1.0
    for b in sorted(brackets, key=lambda b: b["maxAgeDays"]):
        if age_days <= b["maxAgeDays"]:
            return b["multiplier"]
    return brackets[-1]["multiplier"]


def _distress_motivation(d, cfg):
    """Layer 2: reuse the two-axis motivation formula on supplied filing + CAD."""
    contrib = {}
    owner_profile = classify_owner_profile(
        d.get("owner"), d.get("use_desc"), d.get("market_value"))
    if owner_profile == "INSTITUTIONAL":
        contrib["institutional_floor"] = float(cfg.get("institutionalFloor", 0))
        return contrib, owner_profile

    plaintiff, defendant = d.get("plaintiff_name"), d.get("defendant_name")
    ptype = classify_plaintiff(plaintiff)
    fam = detect_family_matter(plaintiff, defendant, d.get("doc_type")).get("confidence")
    distress = "FAMILY" if fam == "HIGH" else ptype
    pt = cfg["plaintiffType"]
    base = pt.get(distress, pt.get("UNKNOWN", 30))
    contrib[f"distress:{distress}"] = round(
        base * _recency(cfg.get("recencyMultipliers"), d.get("record_age_days")), 1)
    if fam == "MED":
        nudge = cfg.get("familyMedNudge", 0)
        if nudge:
            contrib["family:MED"] = nudge

    absentee = bool(d.get("absentee"))
    occupant = bool(d.get("homestead")) or (not absentee and owner_profile == "INDIVIDUAL")
    occ = cfg.get("ownerOccupancy", {})
    if occupant:
        contrib["owner_occupant"] = occ.get("OCCUPANT", 0)
    elif absentee and owner_profile == "SMALL_INVESTOR":
        contrib["absentee_small_investor"] = occ.get("ABSENTEE_SMALL_INVESTOR", 0)
    if d.get("out_of_state"):
        contrib["out_of_state"] = cfg.get("outOfStateAddon", 0)
    lt = cfg.get("longTenure", {})
    tenure = d.get("tenure_years")
    if tenure is not None and tenure >= lt.get("minYears", 10):
        contrib["long_tenure"] = lt.get("points", 0)
    return contrib, owner_profile


def _listing_motivation(ls, cfg):
    """Layer 1: universal Zillow listing signals."""
    contrib = {}
    dom = ls.get("days_on_market")
    if dom is not None:
        for br in sorted(cfg["daysOnMarket"], key=lambda b: -b["minDays"]):
            if dom >= br["minDays"]:
                contrib["days_on_market"] = br["points"]
                break
    status = (ls.get("status") or "").upper()
    sp = cfg.get("statusPoints", {}).get(status)
    if sp:
        contrib[f"status:{status}"] = sp
    if ls.get("fsbo"):
        contrib["fsbo"] = cfg.get("fsboPoints", 0)
    if ls.get("price_cut"):
        contrib["price_cut"] = cfg.get("priceCutPoints", 0)
    return contrib


def motivation_lens(facts, cfg):
    """facts: {distress:{available, ...}, listing_signals:{available, ...}}."""
    facts = facts or {}
    distress = facts.get("distress") or {}
    listing = facts.get("listing_signals") or {}

    if distress.get("available"):
        contrib, owner_profile = _distress_motivation(distress, cfg["distress"])
        score = _clamp(sum(contrib.values()), 0, cfg["cap"])
        return {"score": round(score, 1), "confidence": "HIGH", "contrib": contrib,
                "layer": "distress", "owner_profile": owner_profile,
                "basis": "distress filing + CAD (two-axis motivation)"}

    if listing.get("available"):
        contrib = _listing_motivation(listing, cfg["listingSignals"])
        score = _clamp(sum(contrib.values()), 0, cfg["cap"])
        strong = any(k.startswith("status:") for k in contrib) \
            or contrib.get("days_on_market", 0) >= 15 or "fsbo" in contrib
        conf = "MED" if strong else "LOW"
        return {"score": round(score, 1), "confidence": conf, "contrib": contrib,
                "layer": "listing",
                "basis": "Zillow listing signals (DOM / status / FSBO)"}

    return {"score": None, "confidence": "NONE", "contrib": {}, "layer": "none",
            "basis": "no listing signals and no distress filing"}


# --- OVERALL TIER -----------------------------------------------------------

def overall_tier(cashflow, margin, motivation, cfg):
    strong_band = cfg["strongBand"]
    fail_band = cfg["failBand"]
    lenses = {"cashflow": cashflow, "margin": margin, "motivation": motivation}
    available = {k: v for k, v in lenses.items() if v.get("score") is not None}

    if not available:
        return {"tier": "NR", "basis": "no lens could be scored", "lenses_available": 0}

    strong = [k for k, v in available.items() if v["score"] >= strong_band.get(k, 101)]
    # Only cashflow/margin can DISQUALIFY; weak motivation never buries a deal.
    disqualifying = [k for k in ("cashflow", "margin")
                     if k in available and available[k]["score"] < fail_band.get(k, -1)]

    if len(strong) >= 2:
        tier = "A"
    elif len(strong) == 1:
        tier = "B"
    elif disqualifying:
        tier = "D"
    else:
        tier = "C"

    parts = [f"{k} {available[k]['score']:g}" for k in
             ("cashflow", "margin", "motivation") if k in available]
    strong_note = f"; strong: {', '.join(strong)}" if strong else ""
    fail_note = f"; disqualifying: {', '.join(disqualifying)}" if disqualifying else ""
    single = " (single-lens, capped at B)" if len(available) == 1 else ""
    return {"tier": tier, "lenses_available": len(available),
            "basis": f"{', '.join(parts)}{strong_note}{fail_note}{single}"}


def score_property(facts, cfg):
    """Compose the three lenses + overall tier into a full scorecard dict."""
    cashflow = cashflow_lens(facts.get("cashflow"), cfg["cashflow"])
    margin = margin_lens(facts.get("listing"), facts.get("valuation"), cfg["margin"])
    motivation = motivation_lens(facts.get("motivation"), cfg["motivation"])
    overall = overall_tier(cashflow, margin, motivation, cfg["tiers"])
    return {
        "address": facts.get("address"),
        "tier": overall["tier"],
        "tier_basis": overall["basis"],
        "lenses_available": overall["lenses_available"],
        "lenses": {"cashflow": cashflow, "margin": margin, "motivation": motivation},
    }
