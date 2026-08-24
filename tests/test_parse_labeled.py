"""Labeled-token legal parser tests (Tyler Self-Service style). Legal strings
are real Orange County values from the live 2026-08-24 pull."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "plugins" / "crei" / "skills" / "county-records" / "scripts"))

from parse_legal import parse_legal_labeled, ReviewRecord


def ok(legal):
    r = parse_legal_labeled(legal)
    assert not isinstance(r, ReviewRecord), f"unexpectedly routed to review: {r}"
    return r


def review(legal):
    r = parse_legal_labeled(legal)
    assert isinstance(r, ReviewRecord), f"expected review, parsed: {r}"
    return r


def test_lot_only():
    p = ok("Lot: 76    HUNTER S CREEK TRACT 550")
    assert p.lot == "76" and p.block is None
    assert p.subdivision == "HUNTER S CREEK TRACT 550"


def test_lot_block():
    p = ok("Lot: 8 Block: C    RI MAR RIDGE")
    assert p.lot == "8" and p.block == "C"
    assert p.subdivision == "RI MAR RIDGE"


def test_unit_condo_parses():
    p = ok("Unit: 2427    GROVE RESORT AND SPA HOTEL CONDOMINIUM II")
    assert p.lot == "2427"
    assert p.subdivision == "GROVE RESORT AND SPA HOTEL CONDOMINIUM II"


def test_str_only_reviews_as_metes():
    assert review(" Section: 22 Township: 22 Range: 30   ").reason == "metes_and_bounds"


def test_empty_reviews():
    assert review("").reason == "empty"


def test_no_identifiers_reviews():
    assert review("SOME FREEFORM TEXT").reason == "missing_fields"


def test_timeshare_reviews_as_condo_unit():
    r = review("TS: GRANDE VISTA CONDOMINIUM")
    assert r.reason == "condo_unit" and r.detail == "timeshare"
