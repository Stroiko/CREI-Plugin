"""Aumentum (Alachua FL) reuses the name-based-subfirst parser plus a
directPattern/directFormat for 'PIN {digits}' legals. Legal strings are real
Alachua values from the live 2026-08-24 pull."""
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "plugins" / "crei" / "skills" / "county-records" / "scripts"))

from parse_legal import parse_legal_subfirst, ParsedNameLegal, ReviewRecord

# Mirrors config: alachua-fl parcelId.directPattern / directFormat + the
# run_pipeline "(+)" strip.
DIRECT = re.compile(r"PIN (\d{5})(\d{3})(\d{3})")
DFMT = "{0}-{1}-{2}"


def strip_plus(legal):
    return re.sub(r"\s*\(\+\)\s*$", "", legal)


def test_pin_direct_reformats():
    m = re.fullmatch(DIRECT, strip_plus("PIN 18812010002 (+)"))
    assert m and DFMT.format(*m.groups()) == "18812-010-002"


def test_named_subfirst_lot_block():
    p = parse_legal_subfirst("CAROL ESTATES LT 12 BLK B PLAT BOOK E PAGE 13")
    assert isinstance(p, ParsedNameLegal)
    assert p.subdivision == "CAROL ESTATES" and p.lot == "12" and p.block == "B"


def test_named_multilot_takes_first():
    p = parse_legal_subfirst("LINCOLN ESTATES LT 91 92 PLAT BOOK F PAGE 19")
    assert isinstance(p, ParsedNameLegal)
    assert p.subdivision == "LINCOLN ESTATES" and p.lot == "91"


def test_unit_in_name_not_mistaken_for_lot():
    p = parse_legal_subfirst("CEDAR GROVE UNIT ONE LT 22 PLAT BOOK H PAGE 3")
    assert isinstance(p, ParsedNameLegal)
    assert p.subdivision == "CEDAR GROVE UNIT ONE" and p.lot == "22"


def test_metes_and_bounds_reviews():
    r = parse_legal_subfirst("SEC 26 TWNSHP 10 S RNG 22 E")
    assert isinstance(r, ReviewRecord) and r.reason == "missing_fields"


def test_non_pin_is_not_a_direct():
    assert re.fullmatch(DIRECT, strip_plus("CAROL ESTATES LT 12 BLK B")) is None
