"""Parser tests. Every fixture below is a real DocLegalDescription pulled live
from Brevard's Acclaim portal on 2026-08-23 (legal descriptions identify
parcels, not people - no PII)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "plugins" / "crei" / "skills" / "county-records" / "scripts"))

from parse_legal import parse_legal, ReviewRecord


def ok(legal):
    result = parse_legal(legal)
    assert not isinstance(result, ReviewRecord), f"unexpectedly routed to review: {result}"
    return result


def review(legal):
    result = parse_legal(legal)
    assert isinstance(result, ReviewRecord), f"expected review, parsed: {result}"
    return result


def test_standard_lot_block():
    p = ok("LT 82 BLK 10 PB 28 PG 67  HOLIDAY SPRINGS AT SUNTREE S 02 T 26 R 36 SUBID MM")
    assert p.lot == "82" and p.block == "10"
    assert p.section == "02" and p.township == "26" and p.range == "36"
    assert p.subid == "MM"
    assert p.plat_book == "28" and p.plat_page == "67"
    assert p.subdivision == "HOLIDAY SPRINGS AT SUNTREE"


def test_alpha_block():
    p = ok("LT 15 BLK S PB 9 PG 78  NATIONAL POLICE HOME FOUNDATION INC S 11 T 28 R 36 SUBID 01")
    assert p.block == "S" and p.lot == "15" and p.subid == "01"


def test_township_letter_suffix():
    p = ok("LT 1 BLK 2 PB 16 PG 62  ROSEDALE MANORS S 20 T 20G R 35 SUBID 04")
    assert p.township == "20G" and p.section == "20"


def test_no_block():
    p = ok("LT 88 PB 48 PG 95  HICKORY GREEN UNIT THREE S 20 T 22 R 35 SUBID 55")
    assert p.block is None and p.lot == "88"


def test_section_fragment_noise():
    # "S 1/2 OF S 32" - the section is 32, not 1/2
    p = ok("LT 35 PB 10 PG 38  COCOA PALMS SUBD  S 1/2 OF S 32 T 24 R 36 SUBID 50")
    assert p.section == "32" and p.township == "24" and p.range == "36"
    assert p.block is None and p.lot == "35"


def test_alphanumeric_lot():
    p = ok("LT 75H PB 55 PG 37  WATERSTONE PLAT ONE P.U.D. S 04 T 30 R 37 SUBID UT")
    assert p.lot == "75H" and p.block is None and p.subid == "UT"


def test_subdivision_with_interior_keywords():
    # UNIT/PARCELS/PHASE inside the subdivision name must not break parsing
    p = ok("LT 59 BLK A PB 44 PG 52  VIERA CENTRAL PUD TRACT 12 UNIT 1 PARCELS 1-3, PHASE 3 S 15 T 26 R 36 SUBID RI")
    assert p.lot == "59" and p.block == "A" and p.subid == "RI"


def test_condo_unit_routes_to_review():
    r = review("U A228 UW 48  OCEAN LANDINGS CONDO RESORT & RACQUET CLUB")
    assert r.reason == "condo_unit"


def test_condo_with_orb_routes_to_review():
    r = review("PB 9 PG 27 U A228 UW 48  SEACREST BEACH, REPLAT OF  OCEAN LANDINGS RES & RAC CLB I TIME SHARE ORB 2224/1002 S 10 T 25 R 37 SUBID CZ")
    assert r.reason == "condo_unit"


def test_block_unit_condo_routes_to_review():
    r = review("BLK 501.1 U 101  INDIAN HARBOUR BEACH CLUB CONDO ORB 2499/1618 S 12 T 27 R 37 SUBID 00")
    assert r.reason == "condo_unit"


def test_lot_block_with_unit_and_orb_routes_to_review():
    # Has LT+BLK+STR+SUBID but also "U 19" and an ORB ref - ambiguous, do not guess
    r = review("LT 3.08 BLK 2 PB 21 PG 9 U 19  COCOA ISLES COUNTRY CLUB SEC PH 1 REPT OF PT SEC & COCOA ISLES  THE MASTER'S CONDO PH II ORB 2910/957 S 09 T 25 R 37 SUBID 51")
    assert r.reason == "condo_unit"


def test_metes_and_bounds_routes_to_review():
    r = review("FROM INTERSEC OF CENTER LINE OF SOUTH ST & ROCK PIT RD GO NLY S 4 T 22 R 35")
    assert r.reason == "metes_and_bounds"


def test_missing_subid_routes_to_review():
    r = review("LT 5 BLK 4 PB 26 PG 72  VERNON HEIGHTS S 33 T 21 R 35")
    assert r.reason == "missing_fields"


def test_empty_routes_to_review():
    r = review("")
    assert r.reason in ("empty", "missing_fields")
