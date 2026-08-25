"""Two-axis scoring tests: motivation + equity + tier, explainable, config-driven.

The model separates seller MOTIVATION (call-order priority, always computable
from the filing + owner profile) from an EQUITY deal-margin proxy (measured from
CAD enrichment, null when the join refuses). Institutional owners are floored;
tiers come from the motivation x equity matrix.
"""
import json
import sys
from pathlib import Path

_SCRIPTS = (Path(__file__).resolve().parents[1]
            / "plugins" / "crei" / "skills" / "county-records" / "scripts")
sys.path.insert(0, str(_SCRIPTS))

from classify import (classify_owner_profile, classify_plaintiff,
                      detect_family_matter, resolve_parties, parse_money)
from enrich import derive_signals
from score import score_lead

SCORING = json.loads((_SCRIPTS.parent / "config" / "scoring.json")
                     .read_text(encoding="utf-8"))
AS_OF = "2026-08-24"


# --- fixtures ---------------------------------------------------------------

def occupant_account(**over):
    """Homesteaded owner-occupant: long tenure, big Save-Our-Homes gap, strong
    appreciation. Site uses a directional SUFFIX and long-form 'SOUTH' that the
    mailing address abbreviates/reorders - the normalizer must not flag it."""
    acct = {
        "parcelID": "00-00-00-00-*-1",
        "owner": "PARRISH, JOHN A",
        "siteAddress": "1925 COTTONWOOD VALLEY CIR S DALLAS TX 75201",
        "mailingAddress": {"addr1": "1925 S COTTONWOOD VALLEY CIR",
                           "state": "TX", "isForeign": False},
        "propertyUse": {"description": "SINGLE FAMILY RESIDENCE"},
        "marketValue": "$1,940,000",
        "saleInfo": "03/14/2004 $520,000 Improved",
        "exemptions": [{"code": "HEX1", "description": "HOMESTEAD FIRST"}],
        "valueSummary": [{"marketVal": 1940000, "assessedVal": 1100000,
                          "homesteadEx": 25000}],
        "salesHistory": [{"salePrice": 520000, "saleDate": "2004-03-14T00:00:00"}],
    }
    acct.update(over)
    return acct


def reit_account(**over):
    acct = {
        "parcelID": "00-00-00-00-*-2",
        "owner": "PROLOGIS INDUSTRIAL REIT LLC",
        "siteAddress": "500 LOGISTICS PKWY DALLAS TX 75212",
        "mailingAddress": {"addr1": "1800 WYNKOOP ST STE 500", "state": "CO",
                           "isForeign": False},
        "propertyUse": {"description": "INDUSTRIAL WAREHOUSE"},
        "marketValue": "$28,400,000",
        "saleInfo": "06/01/2009 $9,000,000 Improved",
        "valueSummary": [{"marketVal": 28400000, "assessedVal": 28400000}],
    }
    acct.update(over)
    return acct


def score(defendant, account, plaintiff, doc_type="LIS PENDENS",
          state="TX", age_days=5, party_roles=None):
    plaintiff_name, lead_name = resolve_parties(plaintiff, defendant, party_roles)
    sig = derive_signals(lead_name, account, state, AS_OF)
    sig["plaintiff_type"] = classify_plaintiff(plaintiff_name)
    sig["family_matter"] = detect_family_matter(plaintiff_name, lead_name,
                                                doc_type, None, party_roles)
    return score_lead({"record_age_days": age_days, "signals": sig}, SCORING)


# --- owner profile ----------------------------------------------------------

def test_person_is_individual():
    assert classify_owner_profile("PARRISH, JOHN A", "SINGLE FAMILY RESIDENCE",
                                  300000) == "INDIVIDUAL"


def test_small_llc_on_sfr_is_small_investor():
    assert classify_owner_profile("BOSSIN LLC", "SINGLE FAMILY RESIDENCE",
                                  173000) == "SMALL_INVESTOR"


def test_reit_is_institutional():
    assert classify_owner_profile("PROLOGIS INDUSTRIAL REIT LLC",
                                  "INDUSTRIAL WAREHOUSE", 28400000) == "INSTITUTIONAL"


def test_commercial_use_forces_institutional():
    assert classify_owner_profile("SMITH, JOE", "COMMERCIAL OFFICE",
                                  400000) == "INSTITUTIONAL"


def test_high_value_llc_is_institutional():
    assert classify_owner_profile("SUNRISE LLC", "SINGLE FAMILY RESIDENCE",
                                  2_000_000) == "INSTITUTIONAL"


def test_high_value_person_stays_individual():
    assert classify_owner_profile("PARRISH, JOHN A", "SINGLE FAMILY RESIDENCE",
                                  1_940_000) == "INDIVIDUAL"


# --- plaintiff type ---------------------------------------------------------

def test_credit_union_is_lender():
    assert classify_plaintiff("SPACE COAST CREDIT UNION") == "LENDER"


def test_hoa_is_association():
    assert classify_plaintiff("OAK RUN HOMEOWNERS ASSOCIATION INC") == "ASSOCIATION"


def test_government_is_government():
    assert classify_plaintiff("COUNTY OF DALLAS") == "GOVERNMENT"


def test_individual_plaintiff():
    assert classify_plaintiff("PARRISH, MARY L") == "INDIVIDUAL"


def test_trustee_bank_national_assn_is_lender_not_association():
    # 'NATIONAL ASSN' is a bank designation, not an HOA.
    assert classify_plaintiff("US BANK TRUST NATIONAL ASSN TR") == "LENDER"


def test_servicer_brand_is_lender():
    assert classify_plaintiff("NEWREZ LLC") == "LENDER"
    assert classify_plaintiff("PENNYMAC LOAN SERVICES LLC") == "LENDER"


# --- family detector --------------------------------------------------------

def test_shared_surname_individuals_is_high():
    assert detect_family_matter("PARRISH, MARY", "PARRISH, JOHN A") == \
        {"value": True, "confidence": "HIGH"}


def test_explicit_family_doctype_is_high():
    assert detect_family_matter("SMITH, A", "JONES, B",
                                doc_type="LIS PENDENS FAMILY")["confidence"] == "HIGH"


def test_different_surname_individuals_is_med():
    assert detect_family_matter("JONES, ANN", "PARRISH, BOB")["confidence"] == "MED"


def test_bank_plaintiff_is_not_family():
    assert detect_family_matter("SEACOAST NATIONAL BANK",
                                "PARRISH, JOHN")["confidence"] == "NONE"


def test_entity_defendant_is_not_family():
    assert detect_family_matter("SMITH, A", "ACME HOLDINGS LLC")["confidence"] == "NONE"


def test_undifferentiated_parties_is_not_family():
    assert detect_family_matter("SMITH, JOHN", "SMITH, JOHN",
                                party_roles={"lead": "undifferentiated"}
                                )["confidence"] == "NONE"


# --- party resolution -------------------------------------------------------

def test_standard_party_orientation():
    assert resolve_parties("BANK NA", "OWNER, JOE") == ("BANK NA", "OWNER, JOE")


def test_bexar_party_inversion():
    # lead = grantor = DirectName; plaintiff = grantee = IndirectName
    assert resolve_parties("OWNER, JOE", "HOA ASSN",
                           party_roles={"lead": "grantor"}) == ("HOA ASSN", "OWNER, JOE")


# --- address normalizer + double-count fix ----------------------------------

def test_directional_reorder_not_absentee():
    sig = derive_signals("PARRISH, JOHN A", occupant_account(), "TX", AS_OF)
    assert not sig["absentee_owner"]
    assert sig["owner_occupant"]


def test_genuinely_different_address_is_absentee():
    acct = occupant_account(
        siteAddress="111 BLUFF TER MELBOURNE FL 32901",
        mailingAddress={"addr1": "952 HAYES CT", "state": "FL", "isForeign": False},
        exemptions=[])
    assert derive_signals("BOSSIN LLC", acct, "FL", AS_OF)["absentee_owner"]


def test_out_of_state_does_not_force_absentee():
    # Same street but out-of-state mailing: absentee is decided by the address
    # alone now, so this is NOT absentee (the old code force-set it True).
    acct = occupant_account(
        siteAddress="1925 S COTTONWOOD VALLEY CIR DALLAS TX 75201",
        mailingAddress={"addr1": "1925 S COTTONWOOD VALLEY CIR", "state": "CA",
                        "isForeign": False},
        exemptions=[])
    sig = derive_signals("PARRISH, JOHN A", acct, "TX", AS_OF)
    assert sig["out_of_state_owner"]
    assert not sig["absentee_owner"]


# --- equity evidence --------------------------------------------------------

def test_equity_evidence_extracted():
    sig = derive_signals("PARRISH, JOHN A", occupant_account(), "TX", AS_OF)
    assert sig["market_value_num"] == 1940000
    assert sig["last_sale_price"] == 520000
    assert sig["assessed_value"] == 1100000
    assert sig["assessed_gap"] == 840000
    assert sig["appreciation"] == 1420000


def test_parse_money():
    assert parse_money("$1,940,000") == 1940000
    assert parse_money(323690) == 323690
    assert parse_money(None) is None
    assert parse_money("") is None


# --- two-axis scoring + tiers ----------------------------------------------

def test_divorce_homestead_is_tier_A():
    r = score("PARRISH, JOHN A", occupant_account(), "PARRISH, MARY L")
    assert r["tier"] == "A"
    assert r["motivation"] >= 60
    assert r["equity"] is not None


def test_institutional_reit_is_tier_D_motivation_zero():
    r = score("PROLOGIS INDUSTRIAL REIT LLC", reit_account(), "SOME BANK NA")
    assert r["tier"] == "D"
    assert r["motivation"] == 0


def test_homestead_beats_reit():
    reit = score("PROLOGIS INDUSTRIAL REIT LLC", reit_account(), "BANK NA")
    divorce = score("PARRISH, JOHN A", occupant_account(), "PARRISH, MARY L")
    assert divorce["motivation"] > reit["motivation"]


def test_unenriched_hot_lead_is_A_unverified():
    r = score("PARRISH, JOHN A", None, "PARRISH, MARY L")
    assert r["tier"] == "A_UNVERIFIED"
    assert r["equity"] is None


def test_recent_absentee_llc_bank_foreclosure_is_low_tier():
    acct = occupant_account(
        owner="BOSSIN LLC", siteAddress="111 BLUFF TER MELBOURNE FL 32901",
        mailingAddress={"addr1": "952 HAYES CT", "state": "FL", "isForeign": False},
        marketValue="$173,130", saleInfo="05/03/2024 $170,000 Improved",
        exemptions=[], valueSummary=[{"marketVal": 173130, "assessedVal": 172000}],
        salesHistory=[{"salePrice": 170000}])
    r = score("BOSSIN LLC", acct, "SEACOAST NATIONAL BANK", state="FL")
    assert r["tier"] in {"C", "D"}
    assert r["motivation"] < 60


def test_no_cc_case_signal_anywhere():
    r = score("PARRISH, JOHN A", occupant_account(), "PARRISH, MARY L")
    assert "cc_case" not in json.dumps(r)


def test_scores_are_explainable():
    r = score("PARRISH, JOHN A", occupant_account(), "PARRISH, MARY L")
    assert r["motivation_contrib"]
    assert r["equity_contrib"]


def test_weights_come_from_config_not_code():
    boosted = json.loads(json.dumps(SCORING))
    boosted["motivation"]["ownerOccupancy"]["OCCUPANT"] = 40
    base = score_lead({"record_age_days": 5, "signals": {
        "enriched": True, "owner_profile": "INDIVIDUAL", "owner_occupant": True,
        "plaintiff_type": "LENDER", "family_matter": {"value": False, "confidence": "NONE"}}},
        boosted)
    assert base["motivation_contrib"]["owner_occupant"] == 40
