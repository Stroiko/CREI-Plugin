"""GA Landmark (DeKalb) legals are labeled tokens embedding a direct Parcel ID.
Most records join directly via parcelExtract (a search in run_pipeline); the
parse_legal_ga_landmark fallback extracts SUB/LOT/BLK for the rare no-parcel
record. Legal strings are real DeKalb values from the live 2026-08-24 pull."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "plugins" / "crei" / "skills" / "county-records" / "scripts"))

from parse_legal import parse_legal_ga_landmark, ParsedNameLegal, ReviewRecord

# Mirrors dekalb-ga config parcelId.parcelExtract (a re.search).
PARCEL_EXTRACT = r"Parcel:\s*(\d\d \d\d\d \d\d \d\d\d)"

R1 = ("DIS:15 LAND:122 LOT:5 SUB:RENAISSANCE LAKES Parcel: 15 122 02 012 "
      "Tax District: 04 STREETNUM:3245 STREET:DAVINCI SUFF:CT CITY:DECATUR STATE:GA ZIP:30034")
R2 = ("DIS:15 LAND:131 LOT:102 BLK:D UNI:V SUB:EMERALD ESTATES Parcel: 15 131 08 026 "
      "Tax District: 04 STREETNUM:4100 STREET:EMERALD LAKE SUFF:DR CITY:DECATUR STATE:GA ZIP:30035")
NO_PARCEL = ("DIS:16 LAND:050 LOT:12 BLK:A SUB:SOME PLACE Tax District: 04 "
             "STREETNUM:100 STREET:MAIN SUFF:ST CITY:DECATUR")


def test_parcel_extract_direct():
    m = re.search(PARCEL_EXTRACT, R1)
    assert m and m.group(1) == "15 122 02 012"


def test_parcel_extract_not_confused_by_tax_district():
    # 'Tax District: 04' must not be mistaken for the parcel.
    m = re.search(PARCEL_EXTRACT, R2)
    assert m and m.group(1) == "15 131 08 026"


def test_fallback_extracts_sub_lot_block():
    p = parse_legal_ga_landmark(NO_PARCEL)
    assert isinstance(p, ParsedNameLegal)
    assert p.subdivision == "SOME PLACE" and p.lot == "12" and p.block == "A"


def test_fallback_multiword_subdivision():
    p = parse_legal_ga_landmark(R1)
    assert isinstance(p, ParsedNameLegal)
    assert p.subdivision == "RENAISSANCE LAKES" and p.lot == "5"


def test_fallback_empty_reviews():
    assert parse_legal_ga_landmark("").reason == "empty"
