"""Pure cashflow math - no I/O, no network. Everything here is unit-tested.

Every computed line item carries a human-readable `basis` explaining where the
number came from (which default, tier, or override), matching the explainable
ethos of the county-records scoring pipeline.
"""


def normalize_rate(rate):
    """Accept 6.5 or 0.065; values > 1 are percents."""
    rate = float(rate)
    return rate / 100.0 if rate > 1 else rate


def parse_down_payment(value, purchase_price):
    """Accept '20%' or a dollar amount; return dollars."""
    if isinstance(value, str) and value.strip().endswith("%"):
        return float(value.strip().rstrip("%")) / 100.0 * purchase_price
    return float(value)


def monthly_pi(loan_amount, annual_rate, term_years, interest_only=False):
    """Standard amortization payment; interest-only and 0%-rate handled."""
    if loan_amount <= 0:
        return 0.0
    r = annual_rate / 12.0
    n = term_years * 12
    if interest_only:
        return loan_amount * r
    if r == 0:
        return loan_amount / n
    return loan_amount * r * (1 + r) ** n / ((1 + r) ** n - 1)


def pct_tier(age_years, tiers):
    """Select a pct from age bands. Unknown age -> most conservative tier."""
    if age_years is None:
        pct = tiers[-1]["pct"]
        return pct, "age unknown -> conservative oldest tier ({:.1%})".format(pct)
    for tier in tiers:
        if age_years <= tier["maxAgeYears"]:
            label = "<={}y".format(tier["maxAgeYears"]) \
                if tier["maxAgeYears"] < 9999 else "{}+y".format(
                    tiers[-2]["maxAgeYears"] + 1 if len(tiers) > 1 else 0)
            return tier["pct"], "age {}y -> {} tier ({:.1%})".format(
                age_years, label, tier["pct"])
    pct = tiers[-1]["pct"]
    return pct, "age {}y -> oldest tier ({:.1%})".format(age_years, pct)


def dscr(noi_annual, debt_service_annual):
    """DSCR = NOI / annual debt service. None when there is no debt."""
    if debt_service_annual <= 0:
        return None
    return noi_annual / debt_service_annual


def _pct_basis(pct, source):
    return "{:.1%} of gross rent ({})".format(pct, source)


def _resolve_pct(overrides, key, default_value, default_basis):
    """Overrides beat defaults; basis says which won."""
    val = (overrides or {}).get(key)
    if val is not None:
        return float(val), "override"
    return default_value, default_basis


def analyze(inp, defaults):
    """Full analysis: every rent scenario x {self_managed, managed}.

    Returns {"assumptions": {...}, "scenarios": [{label, rent, modes: {...}}]}.
    Line items are rounded to cents; cash flow is the sum of the rounded lines
    so the printed column always foots exactly. DSCR uses unrounded values.
    """
    prop = inp["property"]
    fin = inp["financing"]
    overrides = inp.get("overrides") or {}
    as_of_year = inp.get("as_of_year")

    price = float(prop["purchase_price"])
    down = parse_down_payment(fin["down_payment"], price)
    rate = normalize_rate(fin["interest_rate"])
    term = int(fin.get("term_years") or defaults["loan"]["term_years"])
    interest_only = bool(fin.get("interest_only"))
    loan = price - down

    pi_raw = monthly_pi(loan, rate, term, interest_only)
    pi_basis = "${:,.0f} loan @ {:.3g}%/{}yr {}".format(
        loan, rate * 100, term,
        "interest-only" if interest_only else "amortized")

    year_built = prop.get("year_built")
    age = (as_of_year - year_built) if (as_of_year and year_built) else None

    vacancy_pct, vac_src = _resolve_pct(
        overrides, "vacancy_pct", defaults["vacancy_pct"], "default")
    managed_pct, mgmt_src = _resolve_pct(
        overrides, "management_pct",
        defaults["management"]["managed_pct"], "default")

    maint_override = overrides.get("maintenance_pct")
    if maint_override is not None:
        maint_pct, maint_src = float(maint_override), "override"
    else:
        maint_pct, maint_src = pct_tier(age, defaults["maintenance_pct_by_age"])
    capex_override = overrides.get("capex_pct")
    if capex_override is not None:
        capex_pct, capex_src = float(capex_override), "override"
    else:
        capex_pct, capex_src = pct_tier(age, defaults["capex_pct_by_age"])

    insurance_monthly = prop.get("insurance_monthly")
    tax_monthly = prop.get("property_tax_monthly")
    hoa_monthly = prop.get("hoa_monthly")

    dscr_cfg = defaults["dscr"]
    dscr_method = dscr_cfg.get("method", "noi")

    assumptions = {
        "purchase_price": price,
        "down_payment": round(down, 2),
        "loan_amount": round(loan, 2),
        "interest_rate": rate,
        "term_years": term,
        "interest_only": interest_only,
        "vacancy_pct": {"value": vacancy_pct, "source": vac_src},
        "management_pct_when_managed": {"value": managed_pct, "source": mgmt_src},
        "maintenance_pct": {"value": maint_pct, "source": maint_src},
        "capex_pct": {"value": capex_pct, "source": capex_src},
        "insurance": ("${}/mo provided".format(insurance_monthly)
                      if insurance_monthly is not None
                      else "{:.1%} of gross rent (default - no quote given)".format(
                          defaults["insurance"]["pct_of_rent"])),
        "property_tax": ("${}/mo provided".format(tax_monthly)
                         if tax_monthly is not None
                         else "ESTIMATE: {:.2%}/yr of price (no real figure given)".format(
                             defaults["property_tax"]["fallback_annual_pct_of_price"])),
        "hoa_monthly": hoa_monthly if hoa_monthly is not None else "not provided -> $0",
        "year_built": year_built or "unknown",
        "home_age_years": age if age is not None else "unknown",
        "dscr": {"method": dscr_method,
                 "include_capex_in_noi": dscr_cfg.get("include_capex_in_noi", False),
                 "pass_threshold": dscr_cfg["pass_threshold"]},
    }

    scenarios = []
    for scen in inp["rent_scenarios"]:
        rent = float(scen["rent"])

        vacancy_raw = rent * vacancy_pct
        if insurance_monthly is not None:
            ins_raw = float(insurance_monthly)
            ins_basis = "provided quote"
        else:
            ins_raw = rent * defaults["insurance"]["pct_of_rent"]
            ins_basis = _pct_basis(defaults["insurance"]["pct_of_rent"],
                                   "default - no quote given")
        if tax_monthly is not None:
            tax_raw = float(tax_monthly)
            tax_basis = "provided figure"
        else:
            tax_raw = price * defaults["property_tax"]["fallback_annual_pct_of_price"] / 12.0
            tax_basis = "fallback estimate: {:.2%}/yr of price - get the real county figure".format(
                defaults["property_tax"]["fallback_annual_pct_of_price"])
        hoa_raw = float(hoa_monthly) if hoa_monthly is not None else 0.0
        hoa_basis = ("provided figure" if hoa_monthly is not None
                     else "not provided -> $0")
        maint_raw = rent * maint_pct
        capex_raw = rent * capex_pct

        modes = {}
        for mode_name, mgmt_pct in (
                ("self_managed", defaults["management"]["self_managed_pct"]),
                ("managed", managed_pct)):
            mgmt_raw = rent * mgmt_pct
            mgmt_basis = (_pct_basis(mgmt_pct, mgmt_src) if mgmt_pct > 0
                          else "self-managed (0%)")

            gross = round(rent, 2)
            vac = round(vacancy_raw, 2)
            pi = round(pi_raw, 2)
            mgmt = round(mgmt_raw, 2)
            ins = round(ins_raw, 2)
            tax = round(tax_raw, 2)
            maint = round(maint_raw, 2)
            capex = round(capex_raw, 2)
            hoa = round(hoa_raw, 2)
            effective = round(gross - vac, 2)
            cash_flow = round(effective - pi - mgmt - ins - tax
                              - maint - capex - hoa, 2)

            lines = [
                {"item": "gross_rent", "sign": "+", "amount": gross,
                 "basis": scen["label"]},
                {"item": "vacancy", "sign": "-", "amount": vac,
                 "basis": _pct_basis(vacancy_pct, vac_src)},
                {"item": "effective_rent", "sign": "=", "amount": effective,
                 "basis": "gross rent - vacancy"},
                {"item": "mortgage_pi", "sign": "-", "amount": pi,
                 "basis": pi_basis},
                {"item": "management", "sign": "-", "amount": mgmt,
                 "basis": mgmt_basis},
                {"item": "insurance", "sign": "-", "amount": ins,
                 "basis": ins_basis},
                {"item": "property_tax", "sign": "-", "amount": tax,
                 "basis": tax_basis},
                {"item": "maintenance", "sign": "-", "amount": maint,
                 "basis": "{:.1%} of gross rent ({})".format(maint_pct, maint_src)},
                {"item": "capex", "sign": "-", "amount": capex,
                 "basis": "{:.1%} of gross rent ({})".format(capex_pct, capex_src)},
                {"item": "hoa", "sign": "-", "amount": hoa, "basis": hoa_basis},
                {"item": "cash_flow", "sign": "=", "amount": cash_flow,
                 "basis": "effective rent - all expenses"},
            ]

            # DSCR from unrounded values
            debt_service_annual = pi_raw * 12
            if dscr_method == "rent_over_pitia":
                pitia_monthly = pi_raw + tax_raw + ins_raw + hoa_raw
                ratio = (rent / pitia_monthly) if pitia_monthly > 0 else None
            else:
                noi_monthly = (rent - vacancy_raw - mgmt_raw - ins_raw
                               - tax_raw - maint_raw - hoa_raw)
                if dscr_cfg.get("include_capex_in_noi", False):
                    noi_monthly -= capex_raw
                ratio = dscr(noi_monthly * 12, debt_service_annual)

            if ratio is None:
                verdict = "N/A (no debt)"
            else:
                verdict = ("PASS" if ratio >= dscr_cfg["pass_threshold"]
                           else "FAIL")

            modes[mode_name] = {
                "lines": lines,
                "cash_flow": cash_flow,
                "dscr": ratio,
                "dscr_verdict": verdict,
            }

        scenarios.append({"label": scen["label"], "rent": rent, "modes": modes})

    return {"assumptions": assumptions, "scenarios": scenarios}
