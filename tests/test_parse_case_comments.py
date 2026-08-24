"""Case-comments legal parser tests (Highlands style: 'CASE # x/LEGAL' with
abbreviated tokens). Fixtures are real Comments values, 2026-08-23."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "plugins" / "crei" / "skills" / "county-records" / "scripts"))

from parse_legal import parse_legal_case_comments, ReviewRecord


def ok(text):
    r = parse_legal_case_comments(text)
    assert not isinstance(r, ReviewRecord), f"unexpectedly routed to review: {r}"
    return r


def review(text):
    r = parse_legal_case_comments(text)
    assert isinstance(r, ReviewRecord), f"expected review, parsed: {r}"
    return r


def test_standard():
    p = ok("CASE # 26-413-GCAXMX/L8 PT L9 BLK 180 WOODLAWN TERRACE")
    assert p.case_number == "26-413-GCAXMX"
    assert p.lot == "8" and p.block == "180"
    assert p.subdivision == "WOODLAWN TERRACE"


def test_lot_only():
    p = ok("CASE # 26-416-GCAXMX/L115 LINCOLN HEIGHTS SUB")
    assert p.lot == "115" and p.block is None
    assert p.subdivision == "LINCOLN HEIGHTS SUB"


def test_cc_case_number_extracted():
    p = ok("CASE # 26-771-CCAXMX/L14 BLK 253 SUN'N LAKES EST SEB UNIT 12")
    assert p.case_number == "26-771-CCAXMX"
    assert p.lot == "14" and p.block == "253"


def test_alnum_lot():
    p = ok("CASE # 26-420-GCAXMX/L84A CORMORANT POINT SUB UNIT II REPLAT")
    assert p.lot == "84A"


def test_multi_lot_takes_first():
    assert ok("CASE # 26-424-GCAXMX/L8/9 BLK A MORNINGSIDE SUB").lot == "8"
    assert ok("CASE # 26-429-GCAXMX/L137-139 LAKESIDE HEIGHTS").lot == "137"


def test_parcel_token_as_lot():
    p = ok("CASE # 26-415-GCAXMX/PARCEL 45 HIGHLANDS HOMES SUB")
    assert p.lot == "45" and p.subdivision == "HIGHLANDS HOMES SUB"


def test_part_block_only_reviews():
    assert review("CASE # 26-054-GCAXMX/PT BLK 4 SUNSET BEACH SUB").reason == "missing_fields"


def test_section_only_reviews():
    assert review("CASE # 26-54-GCAXMX/PT SEC 32-34-29").reason == "metes_and_bounds"


def test_see_instrument_reviews():
    assert review("CASE # 26-449-GCAXMX/SEE INSTRUMENT").reason == "missing_fields"
