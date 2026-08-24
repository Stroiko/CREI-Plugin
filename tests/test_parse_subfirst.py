"""Subdivision-first legal parser tests (NewVision style). Legal strings are
real Polk values from the live 2026-08-24 pull (legals identify parcels, not
people)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "plugins" / "crei" / "skills" / "county-records" / "scripts"))

from parse_legal import parse_legal_subfirst, ReviewRecord


def ok(legal):
    r = parse_legal_subfirst(legal)
    assert not isinstance(r, ReviewRecord), f"unexpectedly routed to review: {r}"
    return r


def review(legal):
    r = parse_legal_subfirst(legal)
    assert isinstance(r, ReviewRecord), f"expected review, parsed: {r}"
    return r


def test_sub_then_lot():
    p = ok("HAMMOCK RESERVE PHASE 1 LT 142")
    assert p.subdivision == "HAMMOCK RESERVE PHASE 1"
    assert p.lot == "142" and p.block is None


def test_sub_block_lot():
    p = ok("ALTURUS BLK 5 LT 1 & 2 BK 13102 PG 0522")
    assert p.subdivision == "ALTURUS"
    assert p.block == "5" and p.lot == "1"


def test_double_spaces_tolerated():
    p = ok("PRESTWICK VILLAGE  LT 21")
    assert p.subdivision == "PRESTWICK VILLAGE" and p.lot == "21"


def test_interior_block_and_lot_tokens_in_sub_name():
    p = ok("REPL POINCIANA PT OF NEIGH 1 VIL 3 BLK 47 LT 4")
    assert p.block == "47" and p.lot == "4"
    assert p.subdivision == "REPL POINCIANA PT OF NEIGH 1 VIL 3"


def test_no_lot_reviews():
    assert review("SOME ACREAGE DESC BK 100 PG 5").reason == "missing_fields"


def test_empty_reviews():
    assert review("").reason == "empty"


def test_condo_unit_parses_for_owner_lookup():
    p = ok("BAHAMA BAY PHASE 35 UN 35302")
    assert p.lot == "35302" and p.subdivision == "BAHAMA BAY PHASE 35"
    p2 = ok("KIMBERLEA CONDO III UN 4 BK 1736 PG 511 THRU 538")
    assert p2.lot == "4" and p2.subdivision == "KIMBERLEA CONDO III"


def test_metes_still_reviews():
    assert review("BGN NW COR NE 1/4 SW 1/4 24-29-04").reason == "missing_fields"
