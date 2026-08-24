"""Landmark structured-row parsing tests. Field shapes mirror the real Palm
Beach export (converted CSV); values synthetic."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "plugins" / "crei" / "skills" / "county-records" / "scripts"))

from run_pipeline import landmark_fields


def row(**over):
    base = {
        "Status": "V",
        "Direct Name": "SOME HOA INC",
        "Reverse Name": "DOE JOHN\nDOE JANE",
        "Record Date Search": "08/14/2026",
        "Location": "01,47,41,",
        "Doc Type": "LIS PENDENS",
        "Instrument #": "20260295425",
        "Legal": "Case Number: \nCase Number: 502026CC014026XXXAMB\nL: 64 SUB: SOME LAKES PARCEL K PCN: : 20260225058 O 36603 / 140\n",
        "Lot": "64", "Building": "", "Block": "", "Unit": "",
        "Subdivision": "SOME LAKES PARCEL K",
        "Section": "01", "Township": "47", "Range": "41",
    }
    base.update(over)
    return base


def test_standard_lot_row():
    f = landmark_fields(row())
    assert f["lot"] == "64" and f["block"] is None
    assert f["subdivision"] == "SOME LAKES PARCEL K"
    assert f["section"] == "01" and f["township"] == "47" and f["range"] == "41"
    assert f["case_number"] == "502026CC014026XXXAMB"
    assert f["review"] is None


def test_case_number_extracted_from_legal_text():
    f = landmark_fields(row(Legal="Case Number: 502026CA010101XXXXMB\nL: 5 SUB: X"))
    assert f["case_number"] == "502026CA010101XXXXMB"


def test_unit_condo_still_parses_for_owner_lookup():
    f = landmark_fields(row(Lot="", Unit="204", Subdivision="SOME TOWER CONDO"))
    assert f["review"] is None
    assert f["lot"] == "204" and f["is_unit"] is True


def test_block_carried():
    f = landmark_fields(row(Block="H"))
    assert f["block"] == "H"


def test_no_identifiers_reviews():
    f = landmark_fields(row(Lot="", Unit="", Subdivision=""))
    assert f["review"] == "missing_fields"


def test_provisional_from_status():
    assert landmark_fields(row(Status="R"))["provisional"] is True
    assert landmark_fields(row(Status="V"))["provisional"] is False


def test_primary_defendant_is_first_line():
    f = landmark_fields(row())
    assert f["indirect_name"] == "DOE JOHN"
    assert f["all_defendants"] == ["DOE JOHN", "DOE JANE"]
