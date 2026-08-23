"""Signal derivation tests. Account JSON shape mirrors the live BCPAO
/api/v1/account response (verified 2026-08-23); names/addresses synthetic."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "plugins" / "crei" / "skills" / "county-records" / "scripts"))

from enrich import derive_signals


def account(**over):
    base = {
        "account": "1234567",
        "parcelID": "29-37-33-GT-1138-22",
        "siteAddress": "1478 SUMMER ST SE PALM BAY FL 32909",
        "owner": "DOE, JOHN",
        "mailingAddress": {
            "addr1": "1478 SUMMER ST SE", "addr2": "", "city": "PALM BAY",
            "state": "FL", "zip": "32909", "country": "", "isForeign": False,
        },
        "saleInfo": "02/21/2015 $35,000 Improved",
        "propertyUse": {"code": "0110", "description": "SINGLE FAMILY RESIDENCE"},
        "marketValue": "$310,000",
    }
    base.update(over)
    return base


AS_OF = "2026-08-23"


def test_owner_occupied_not_absentee():
    s = derive_signals("DOE, JOHN", account(), "FL", AS_OF)
    assert not s["absentee_owner"] and not s["out_of_state_owner"]


def test_absentee_in_state():
    a = account(mailingAddress={"addr1": "5307 AMERSHAM LN", "addr2": "",
                                "city": "SAINT CLOUD", "state": "FL",
                                "zip": "34771", "country": "", "isForeign": False})
    s = derive_signals("DOE, JOHN", a, "FL", AS_OF)
    assert s["absentee_owner"] and not s["out_of_state_owner"]


def test_out_of_state_is_also_absentee():
    a = account(mailingAddress={"addr1": "9 PINE RD", "addr2": "", "city": "DAYTON",
                                "state": "OH", "zip": "45402", "country": "",
                                "isForeign": False})
    s = derive_signals("DOE, JOHN", a, "FL", AS_OF)
    assert s["absentee_owner"] and s["out_of_state_owner"]


def test_entity_owner_detected_from_defendant_name():
    s = derive_signals("3ELEVEN LLC", account(owner="3ELEVEN LLC"), "FL", AS_OF)
    assert s["entity_owned"]


def test_individual_owner_not_entity():
    s = derive_signals("DOE, JOHN", account(), "FL", AS_OF)
    assert not s["entity_owned"]


def test_long_tenure():
    s = derive_signals("DOE, JOHN", account(saleInfo="02/21/2015 $35,000 Improved"), "FL", AS_OF)
    assert s["tenure_years"] is not None and s["tenure_years"] > 10
    a = account(saleInfo="02/21/2024 $35,000 Improved")
    s2 = derive_signals("DOE, JOHN", a, "FL", AS_OF)
    assert s2["tenure_years"] is not None and s2["tenure_years"] < 3


def test_vacant_flag():
    a = account(propertyUse={"code": "0010",
                             "description": "VACANT RESIDENTIAL LAND (SINGLE FAMILY, PLATTED)"})
    s = derive_signals("DOE, JOHN", a, "FL", AS_OF)
    assert s["vacant_land_flag"]


def test_null_account_yields_unenriched():
    s = derive_signals("DOE, JOHN", None, "FL", AS_OF)
    assert s["enriched"] is False
    assert not s["absentee_owner"] and s["tenure_years"] is None
