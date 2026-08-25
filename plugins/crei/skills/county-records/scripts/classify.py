"""Portable, vendor-agnostic classifiers for two-axis lead scoring.

Pure functions, no I/O. These work off names + property use, so they fire on
every vendor - including GovOS (Texas) where no case number exists and the old
`cc_case` signal was dead.

  classify_owner_profile(owner, use_desc, market_value) -> INDIVIDUAL | SMALL_INVESTOR | INSTITUTIONAL
  classify_plaintiff(name)                              -> ASSOCIATION | LENDER | GOVERNMENT | INDIVIDUAL
  detect_family_matter(plaintiff, defendant, ...)       -> {"value": bool, "confidence": HIGH|MED|NONE}

Party orientation (who is plaintiff vs defendant) varies by county - Bexar
inverts grantor/grantee, Collin lists every party under both roles. Callers
resolve the plaintiff/defendant names via `resolve_parties` BEFORE calling
these, so the classifiers stay county-agnostic.
"""
import re

# --- name-shape helpers -----------------------------------------------------

# Generic entity markers: something that is not a natural person.
_ENTITY = re.compile(
    r"\b(LLC|PLLC|L\.?L\.?C|INC|CORP|CORPORATION|CO|COMPANY|LTD|LP|LLP|LLLP"
    r"|TRUST|TRUSTEE|ASSN|ASSOCIATION|PARTNERSHIP|PARTNERS|HOLDINGS|PROPERTIES"
    r"|INVESTMENTS|ENTERPRISES|VENTURES|GROUP|FOUNDATION|CHURCH|MINISTRIES"
    r"|BANK|CREDIT UNION|MORTGAGE|CAPITAL|FUND|REIT|PLC|NA|N\.A\.)\b")

# Strong institutional markers: a fund / bank / builder / commercial operator,
# never a mom-and-pop owner. Presence forces INSTITUTIONAL regardless of value.
_INSTITUTIONAL = re.compile(
    r"\b(REIT|FUND|FUNDS|CAPITAL|PARTNERS|HOLDINGS|BANK|MORTGAGE|FINANCIAL"
    r"|LENDING|SERVICING|SAVINGS|ADVISORS|DEVELOPMENT|REALTY TRUST|EQUITY"
    r"|ACQUISITIONS|VENTURES|MANAGEMENT|NATIONAL ASSOCIATION|N\.A\.|FSB"
    r"|INDUSTRIAL|LOGISTICS|MULTIFAMILY|APARTMENTS|COMMERCIAL)\b")

# High-value threshold above which even a plain LLC reads as institutional.
_INSTITUTIONAL_VALUE = 1_500_000

_ASSOCIATION = re.compile(
    r"\b(ASSN|ASSOCIATION|HOA|CONDOMINIUM|CONDO|HOMEOWNERS|OWNERS ASSN"
    r"|PROPERTY OWNERS|COMMUNITY ASSOCIATION|MASTER ASSOCIATION|TOWNHOMES"
    r"|TOWNHOUSE ASSOCIATION|VILLAS)\b")

_LENDER = re.compile(
    r"\b(BANK|MORTGAGE|LOAN|LOANS|LENDING|CREDIT UNION|FINANCIAL|FUNDING"
    r"|SERVICING|SAVINGS|FSB|BANCORP|CAPITAL ONE|WELLS FARGO|BANCORP"
    r"|NATIONAL ASSOCIATION|NATIONAL ASSN|N\.A\.|FEDERAL SAVINGS|HOME LOANS)\b")

# Foreclosure-plaintiff brand names that carry no generic lender keyword. These
# dominate the plaintiff column; without them they fall through to UNKNOWN.
_LENDER_BRANDS = re.compile(
    r"\b(NEWREZ|PENNYMAC|CALIBER|CARRINGTON|SHELLPOINT|RUSHMORE|NATIONSTAR"
    r"|MR COOPER|LOANDEPOT|FLAGSTAR|OCWEN|SELENE|DITECH|GREENTREE|CENLAR"
    r"|FANNIE MAE|FREDDIE MAC|GINNIE MAE|CITIMORTGAGE|SN SERVICING|PHH)\b")

_GOVERNMENT = re.compile(
    r"\b(COUNTY OF|CITY OF|STATE OF|TOWN OF|VILLAGE OF|TAX|TAXES|IRS"
    r"|INTERNAL REVENUE|UNITED STATES|U\.?S\.?A|APPRAISAL DISTRICT|TREASURER"
    r"|COMPTROLLER|DEPARTMENT OF|MUNICIPAL|TAX COLLECTOR|COMMISSIONER"
    r"|SCHOOL DISTRICT|DRAINAGE DISTRICT|WATER DISTRICT)\b")

_COMMERCIAL_USE = re.compile(
    r"\b(COMMERCIAL|INDUSTRIAL|WAREHOUSE|OFFICE|RETAIL|STORE|SHOPPING|HOTEL"
    r"|MOTEL|RESTAURANT|MANUFACTURING|STORAGE|BANK|GAS STATION|MEDICAL"
    r"|PROFESSIONAL|MIXED USE|PARKING|MARINA)\b")
_VACANT_USE = re.compile(r"\bVACANT\b")


def _norm(s) -> str:
    return re.sub(r"\s+", " ", (s or "").upper()).strip()


def is_entity(name) -> bool:
    return bool(name and _ENTITY.search(_norm(name)))


def surname(name):
    """Last name for a person record. County name strings are 'LAST,FIRST' or
    'LAST, FIRST MIDDLE'. Returns None for entities / unparseable names."""
    n = _norm(name)
    if not n or is_entity(name):
        return None
    if "," in n:
        return n.split(",", 1)[0].strip() or None
    parts = n.split()
    return parts[-1] if len(parts) >= 2 else None


def classify_owner_profile(owner, use_desc=None, market_value=None) -> str:
    """INDIVIDUAL (natural person), SMALL_INVESTOR (single LLC/trust on an
    ordinary residential parcel - the tired-landlord path), or INSTITUTIONAL
    (fund/REIT/bank/builder, or any commercial/industrial or high-value parcel).
    """
    use = _norm(use_desc)
    if _COMMERCIAL_USE.search(use):
        return "INSTITUTIONAL"
    if not is_entity(owner):
        return "INDIVIDUAL"
    # Owner is an entity. Decide small vs institutional.
    if _INSTITUTIONAL.search(_norm(owner)):
        return "INSTITUTIONAL"
    if market_value is not None and market_value >= _INSTITUTIONAL_VALUE:
        return "INSTITUTIONAL"
    return "SMALL_INVESTOR"


def classify_plaintiff(name) -> str:
    """Distress type from the plaintiff (creditor) name.

    Banks style themselves '... NATIONAL ASSOCIATION / N.A.' - that is a lender,
    NOT an HOA - so a lender match suppresses the association check even though
    'ASSN' appears in the name."""
    n = _norm(name)
    if not n:
        return "UNKNOWN"
    is_lender = bool(_LENDER.search(n) or _LENDER_BRANDS.search(n))
    if _ASSOCIATION.search(n) and not is_lender:
        return "ASSOCIATION"
    if _GOVERNMENT.search(n):
        return "GOVERNMENT"
    if is_lender:
        return "LENDER"
    if is_entity(name):
        return "UNKNOWN"          # some other entity (e.g. contractor lien)
    return "INDIVIDUAL"


def detect_family_matter(plaintiff, defendant, doc_type=None, case_class=None,
                         party_roles=None) -> dict:
    """Confidence-graded divorce / partition / heirship detector.

    HIGH: county labels it (doc_type/case_class), OR plaintiff & defendant are
          both individuals sharing a surname with no institutional plaintiff.
    MED : both parties individuals, plaintiff individual, no surname match
          (heirship/partition among differently-named parties).
    NONE: institutional/lender/HOA/government plaintiff, or undifferentiated
          parties we can't trust.
    """
    none = {"value": False, "confidence": "NONE"}
    dt, cc = _norm(doc_type), _norm(case_class)
    if "FAMILY" in dt or "DIVORCE" in dt or "DISSOLUTION" in dt:
        return {"value": True, "confidence": "HIGH"}
    if cc in {"FAM", "FAMILY", "DR", "DIV"}:
        return {"value": True, "confidence": "HIGH"}

    # Undifferentiated party lists (Collin): can't trust who's who.
    if (party_roles or {}).get("lead") == "undifferentiated":
        return none

    ptype = classify_plaintiff(plaintiff)
    if ptype != "INDIVIDUAL":            # a bank/HOA/gov plaintiff is not family
        return none
    if is_entity(defendant):             # entity defendant is not a family matter
        return none

    ps, ds = surname(plaintiff), surname(defendant)
    if ps and ds and ps == ds:
        return {"value": True, "confidence": "HIGH"}
    if ps and ds:                        # both individuals, different surnames
        return {"value": True, "confidence": "MED"}
    return none


def resolve_parties(direct_name, indirect_name, party_roles=None):
    """Return (plaintiff, defendant/lead) honoring the county's party semantics.

    Standard (default): DirectName = grantor = plaintiff, IndirectName =
    grantee = defendant/lead. Bexar inverts (lead = grantor = DirectName).
    Collin lists parties under both roles - lead defaults to IndirectName and
    the plaintiff is treated as unknown by the family detector.
    """
    lead_role = (party_roles or {}).get("lead", "grantee")
    if lead_role == "grantor":
        return indirect_name, direct_name          # inverted (Bexar)
    return direct_name, indirect_name              # standard / undifferentiated


def parse_money(s):
    """'$323,690' or 323690 -> 323690 (int). None/blank -> None."""
    if s is None:
        return None
    if isinstance(s, (int, float)):
        return int(s)
    m = re.search(r"[\d,]+", str(s).replace(" ", ""))
    if not m:
        return None
    try:
        return int(m.group(0).replace(",", ""))
    except ValueError:
        return None
