"""Lookup-join matcher tests. Candidate rows mirror the live PCPAO
GetBySubdivision legal strings (verified 2026-08-23)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "plugins" / "crei" / "skills" / "county-records" / "scripts"))

from match_lookup import match_parcel

PINELLE = [
    {"pid": "28-30-16-71496-001-0010", "legal": "PINELLE PARTIAL REPLAT BLK A, LOT 1"},
    {"pid": "28-30-16-71496-001-0040", "legal": "PINELLE PARTIAL REPLAT BLK A, LOT 4"},
    {"pid": "28-30-16-71496-002-0080", "legal": "PINELLE PARTIAL REPLAT BLK B, LOT 8"},
    {"pid": "28-30-16-71496-001-0070", "legal": "PINELLE PARTIAL REPLAT BLK A, W 60FT LOT 7"},
    {"pid": "28-30-16-71496-002-0100", "legal": "PINELLE PARTIAL REPLAT BLK B, LOTS 10 AND 11"},
]


def test_exact_lot_block_match():
    assert match_parcel("4", "A", PINELLE) == "28-30-16-71496-001-0040"


def test_block_disambiguates():
    rows = [
        {"pid": "08-31-16-57852-001-0100", "legal": "MILES PINES BLK A, LOT 10"},
        {"pid": "08-31-16-57852-008-0100", "legal": "MILES PINES BLK H, LOT 10"},
    ]
    assert match_parcel("10", "H", rows) == "08-31-16-57852-008-0100"


def test_no_block_matches_blockless_legal():
    rows = [
        {"pid": "20-30-16-12345-000-0760", "legal": "BLUE JAY WOODLANDS PH 3 LOT 76"},
        {"pid": "20-30-16-12345-000-0770", "legal": "BLUE JAY WOODLANDS PH 3 LOT 77"},
    ]
    assert match_parcel("76", None, rows) == "20-30-16-12345-000-0760"


def test_lot_1_does_not_match_lot_10():
    rows = [
        {"pid": "x-10", "legal": "SOME SUB BLK A, LOT 10"},
        {"pid": "x-1", "legal": "SOME SUB BLK A, LOT 1"},
    ]
    assert match_parcel("1", "A", rows) == "x-1"


def test_multi_lot_legal_still_matches_listed_lot():
    assert match_parcel("10", "B", PINELLE) == "28-30-16-71496-002-0100"


def test_ambiguous_returns_none():
    rows = [
        {"pid": "a", "legal": "SUB BLK A, LOT 5"},
        {"pid": "b", "legal": "SUB REPLAT BLK A, LOT 5"},
    ]
    assert match_parcel("5", "A", rows) is None


def test_no_candidates_returns_none():
    assert match_parcel("99", "Z", PINELLE) is None
