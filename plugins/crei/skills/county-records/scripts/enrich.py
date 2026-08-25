"""Derive ownership + equity-evidence signals for a lead from its appraiser account.

The account dict mirrors the county appraiser JSON (Brevard/BCPAO shape:
siteAddress, mailingAddress{addr1,city,state,isForeign}, saleInfo, salesHistory,
exemptions, valueSummary, propertyUse). Other vendors save a looser shape, so
every field is read defensively - a missing field lowers equity confidence,
never crashes. A None account means enrichment was unavailable; signals stay
conservative (False/None), never guessed.
"""
import re
from datetime import date

from classify import classify_owner_profile, is_entity, parse_money

_SALE_DATE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")
_SALE_PRICE = re.compile(r"\$([\d,]+)")

# Address canonicalization so a directional reorder or a SOUTH/S spelling
# difference is not mistaken for a different (absentee) address.
_DIRECTIONALS = {
    "NORTH": "N", "SOUTH": "S", "EAST": "E", "WEST": "W",
    "NORTHEAST": "NE", "NORTHWEST": "NW", "SOUTHEAST": "SE", "SOUTHWEST": "SW",
}
_SUFFIXES = {
    "STREET": "ST", "AVENUE": "AVE", "DRIVE": "DR", "ROAD": "RD", "LANE": "LN",
    "BOULEVARD": "BLVD", "COURT": "CT", "PLACE": "PL", "CIRCLE": "CIR",
    "TERRACE": "TER", "PARKWAY": "PKWY", "HIGHWAY": "HWY", "TRAIL": "TRL",
    "SQUARE": "SQ", "CROSSING": "XING", "POINT": "PT", "HEIGHTS": "HTS",
}
_UNIT_NOISE = {"APT", "UNIT", "STE", "SUITE", "BLDG", "RM", "ROOM", "FLR", "#"}


def _canon_token(tok: str) -> str:
    tok = re.sub(r"[.,#]", "", tok.upper())
    tok = _DIRECTIONALS.get(tok, tok)
    return _SUFFIXES.get(tok, tok)


def _addr_tokens(s) -> set:
    return {t for raw in (s or "").split()
            if (t := _canon_token(raw)) and t not in _UNIT_NOISE}


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").upper()).strip()


def _is_homestead(account) -> bool:
    for e in account.get("exemptions") or []:
        if (e.get("code") or "").upper().startswith("HEX") \
           or "HOMESTEAD" in (e.get("description") or "").upper():
            return True
    vs = account.get("valueSummary") or []
    return bool(vs and (vs[0] or {}).get("homesteadEx"))


def _equity_evidence(account) -> dict:
    """Market value, last sale price, assessed value and the two derived gaps.
    Any missing input yields None for the dependent field (honest, not zero)."""
    vs0 = (account.get("valueSummary") or [{}])[0] or {}
    market = parse_money(account.get("marketValue")) or vs0.get("marketVal")
    assessed = vs0.get("assessedVal")

    last_sale = None
    sales = account.get("salesHistory") or []
    if sales:
        last_sale = sales[0].get("salePrice")
    if last_sale is None:
        m = _SALE_PRICE.search(account.get("saleInfo") or "")
        if m:
            last_sale = int(m.group(1).replace(",", ""))

    gap = (market - assessed) if (market and assessed is not None) else None
    appreciation = (market - last_sale) if (market and last_sale is not None) else None
    return {
        "market_value_num": market,
        "assessed_value": assessed,
        "last_sale_price": last_sale,
        "assessed_gap": gap,
        "appreciation": appreciation,
    }


def derive_signals(defendant_name, account, property_state, as_of: str) -> dict:
    signals = {
        "enriched": account is not None,
        "owner_profile": "INDIVIDUAL" if not is_entity(defendant_name) else "SMALL_INVESTOR",
        "absentee_owner": False,
        "out_of_state_owner": False,
        "owner_occupant": False,
        "homestead": False,
        "tenure_years": None,
        "vacant_land_flag": False,
        "market_value_num": None,
        "assessed_value": None,
        "last_sale_price": None,
        "assessed_gap": None,
        "appreciation": None,
    }
    if account is None:
        return signals

    owner = account.get("owner")
    use_desc = (account.get("propertyUse") or {}).get("description")
    equity = _equity_evidence(account)
    signals.update(equity)
    signals["owner_profile"] = classify_owner_profile(
        owner or defendant_name, use_desc, equity["market_value_num"])

    # Absentee: is the mailing street a subset of the site address (owner lives
    # there)? Token-set + canonical directionals/suffixes tolerate SOUTH/S and
    # directional reordering that a naive startswith() mis-flags as absentee.
    site_tokens = _addr_tokens(account.get("siteAddress"))
    mail = account.get("mailingAddress") or {}
    mail_tokens = _addr_tokens(mail.get("addr1"))
    if site_tokens and mail_tokens:
        signals["absentee_owner"] = not mail_tokens.issubset(site_tokens)

    # Out-of-state is a SEPARATE weak signal - it no longer force-sets absentee
    # (that double-counted an out-of-state owner as both absentee and OOS).
    mail_state = _norm(mail.get("state"))
    if mail.get("isForeign") or (mail_state and mail_state != _norm(property_state)):
        signals["out_of_state_owner"] = True

    signals["homestead"] = _is_homestead(account)
    signals["owner_occupant"] = (
        signals["homestead"]
        or (not signals["absentee_owner"] and signals["owner_profile"] == "INDIVIDUAL"))

    m = _SALE_DATE.search(account.get("saleInfo") or "")
    if m:
        mm, dd, yyyy = (int(g) for g in m.groups())
        y, mo, d = (int(p) for p in as_of.split("-"))
        try:
            days = (date(y, mo, d) - date(yyyy, mm, dd)).days
            signals["tenure_years"] = round(days / 365.25, 1)
        except ValueError:
            pass

    signals["vacant_land_flag"] = "VACANT" in (use_desc or "").upper()
    return signals
