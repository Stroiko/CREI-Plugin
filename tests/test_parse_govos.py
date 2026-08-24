"""GovOS Cloud Search legal parser tests. Legal strings are real Dallas County
values from the live 2026-08-24 pull."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "plugins" / "crei" / "skills" / "county-records" / "scripts"))

from parse_legal import parse_legal_govos, ReviewRecord


def ok(legal):
    r = parse_legal_govos(legal)
    assert not isinstance(r, ReviewRecord), f"unexpectedly routed to review: {r}"
    return r


def review(legal):
    r = parse_legal_govos(legal)
    assert isinstance(r, ReviewRecord), f"expected review, parsed: {r}"
    return r


def test_sub_lot_township():
    p = ok("Subdivision - Name: WO SMITH Lot: 11 Township: LANCASTER")
    assert p.subdivision == "WO SMITH" and p.lot == "11"
    assert p.block is None and p.city == "LANCASTER"


def test_full_tokens_with_reference():
    p = ok("Subdivision - Name: LUNA BUSINESS PARK Lot: 1R Block: C "
           "Township: CARROLLTON Reference - 202600116366/")
    assert p.subdivision == "LUNA BUSINESS PARK"
    assert p.lot == "1R" and p.block == "C" and p.city == "CARROLLTON"


def test_multiword_subdivision_and_reference_excluded():
    p = ok("Subdivision - Name: COTTONWOOD VALLEY PHASE II INSTALLMENT IV "
           "Lot: 34 Block: 7 Township: IRVING Reference - 85182/3683")
    assert p.subdivision == "COTTONWOOD VALLEY PHASE II INSTALLMENT IV"
    assert p.lot == "34" and p.block == "7"


def test_ampersand_name_no_lot_reviews():
    r = review("Subdivision - Name: HUGHES&SLAUGHTER TRACT Block: 5 "
               "Township: DALLAS Reference - 2/196")
    assert r.reason == "missing_fields" and "lot" in r.detail


def test_survey_reviews_as_metes():
    r = review("Survey - Name: JJ METCALF SUR Survey: 885 Acres: 26.1")
    assert r.reason == "metes_and_bounds"


def test_alnum_lot_kept_verbatim():
    p = ok("Subdivision - Name: CEDAR BEND Lot: 31R Block: 2 Township: CEDAR HILL")
    assert p.lot == "31R" and p.block == "2" and p.city == "CEDAR HILL"


def test_empty_reviews():
    assert review("").reason == "empty"


def test_freeform_reviews():
    assert review("SOME FREEFORM TEXT").reason == "missing_fields"


def test_first_subdivision_segment_wins_over_survey():
    p = ok("Subdivision - Name: NUSSBAUMERS Lot: 10 Block: 1 Township: DALLAS "
           "Survey - Name: SOME SUR Survey: 12")
    assert p.subdivision == "NUSSBAUMERS" and p.lot == "10"
