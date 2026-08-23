"""Name-based legal parser tests (Pinellas style). Fixtures are real Comments
values from the Pinellas Acclaim export, 2026-08-23."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "plugins" / "crei" / "skills" / "county-records" / "scripts"))

from parse_legal import parse_legal_namebased, ReviewRecord


def ok(legal):
    r = parse_legal_namebased(legal)
    assert not isinstance(r, ReviewRecord), f"unexpectedly routed to review: {r}"
    return r


def review(legal):
    r = parse_legal_namebased(legal)
    assert isinstance(r, ReviewRecord), f"expected review, parsed: {r}"
    return r


def test_lot_only():
    p = ok("LOT 76 BLUE JAY WOODLANDS PHASE 3")
    assert p.lot == "76" and p.block is None
    assert p.subdivision == "BLUE JAY WOODLANDS PHASE 3"


def test_lot_block():
    p = ok("LOT 4 BLOCK A PINELLE PARTIAL REPLAT")
    assert p.lot == "4" and p.block == "A" and p.subdivision == "PINELLE PARTIAL REPLAT"


def test_numeric_block():
    p = ok("LOT 11 BLOCK 5 EDGEWATER SECTION OF SHORE ACRES")
    assert p.lot == "11" and p.block == "5"
    assert p.subdivision == "EDGEWATER SECTION OF SHORE ACRES"


def test_of_prefix_stripped():
    p = ok("LOT 6 BLOCK 9 OF GANBRIDGE HUB SUBDIVISION")
    assert p.subdivision == "GANBRIDGE HUB SUBDIVISION"


def test_lots_plural():
    p = ok("LOTS 91 TARA CAY SOUND SOUTH VILLAGE PHASE 1")
    assert p.lot == "91"


def test_condo_unit_reviews():
    assert review("UNIT NO 204 OF CHATEAU TOWER CONDOMINIUM").reason == "condo_unit"
    assert review("UNIT 232 OF WINSTON PARK NORTHEAST 900 CONDOMINIUM").reason == "condo_unit"
    assert review("APARTMENT NO 302 D OF TYRONE GARDENS APARTMENTS UNIT II CONDOMINIUM").reason == "condo_unit"


def test_multi_lot_takes_first():
    p = ok("LOT 23 AND THE NORTH 1/2 OF LOT 22 BLOCK A OF SUMMIT PARK")
    assert p.lot == "23" and p.block == "A" and p.subdivision == "SUMMIT PARK"


def test_no_lot_reviews():
    assert review("TRACT A COMMON AREA SOMEWHERE").reason == "missing_fields"
