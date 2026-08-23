"""Derive ownership signals for a lead from its appraiser account record.

The account dict mirrors the county appraiser JSON (Brevard/BCPAO shape:
siteAddress, mailingAddress{addr1,city,state,...}, saleInfo, propertyUse).
A None account means enrichment was unavailable - signals stay conservative
(False/None), never guessed.
"""
import re
from datetime import date

_ENTITY = re.compile(
    r"\b(LLC|PLLC|INC|CORP|CORPORATION|TRUST|TRUSTEE|ASSN|ASSOCIATION|COMPANY"
    r"|LTD|PARTNERSHIP|HOLDINGS|PROPERTIES|INVESTMENTS|FOUNDATION|CHURCH|BANK|PLC)\b")
_SALE_DATE = re.compile(r"(\d{1,2})/(\d{1,2})/(\d{4})")


def _is_entity(*names) -> bool:
    return any(name and _ENTITY.search(name.upper()) for name in names)


def _norm(s: str) -> str:
    return re.sub(r"\s+", " ", (s or "").upper()).strip()


def derive_signals(defendant_name, account, property_state, as_of: str) -> dict:
    signals = {
        "enriched": account is not None,
        "absentee_owner": False,
        "out_of_state_owner": False,
        "entity_owned": _is_entity(defendant_name),
        "tenure_years": None,
        "vacant_land_flag": False,
    }
    if account is None:
        return signals

    signals["entity_owned"] = _is_entity(defendant_name, account.get("owner"))

    site = _norm(account.get("siteAddress"))
    mail = account.get("mailingAddress") or {}
    mail_street = _norm(mail.get("addr1"))
    if site and mail_street:
        signals["absentee_owner"] = not site.startswith(mail_street)
    mail_state = _norm(mail.get("state"))
    if mail.get("isForeign") or (mail_state and mail_state != _norm(property_state)):
        signals["out_of_state_owner"] = True
        signals["absentee_owner"] = True

    m = _SALE_DATE.search(account.get("saleInfo") or "")
    if m:
        mm, dd, yyyy = (int(g) for g in m.groups())
        y, mo, d = (int(p) for p in as_of.split("-"))
        try:
            days = (date(y, mo, d) - date(yyyy, mm, dd)).days
            signals["tenure_years"] = round(days / 365.25, 1)
        except ValueError:
            pass

    use = ((account.get("propertyUse") or {}).get("description") or "").upper()
    signals["vacant_land_flag"] = "VACANT" in use
    return signals
