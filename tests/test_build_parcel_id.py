"""Parcel-ID construction tests. Expected IDs were each confirmed live against
the BCPAO API on 2026-08-23 (totalCount == 1, subdivision matched)."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]
                       / "plugins" / "crei" / "skills" / "county-records" / "scripts"))

from parse_legal import parse_legal
from build_parcel_id import build_parcel_id

BREVARD_CFG = {
    "format": "{T}-{R}-{S}-{SUBID}-{BLK}-{LOT}",
    "noBlockToken": "*",
    "zeroPad": False,
    "verified": True,
}

CONFIRMED = [
    ("LT 22 BLK 1138 PB 16 PG 19  PORT MALABAR UNIT 23  S 33 T 29 R 37 SUBID GT", "29-37-33-GT-1138-22"),
    ("LT 82 BLK 10 PB 28 PG 67  HOLIDAY SPRINGS AT SUNTREE S 02 T 26 R 36 SUBID MM", "26-36-02-MM-10-82"),
    ("LT 15 BLK S PB 9 PG 78  NATIONAL POLICE HOME FOUNDATION INC S 11 T 28 R 36 SUBID 01", "28-36-11-01-S-15"),
    ("LT 1 BLK 2 PB 16 PG 62  ROSEDALE MANORS S 20 T 20G R 35 SUBID 04", "20G-35-20-04-2-1"),
    ("LT 35 PB 10 PG 38  COCOA PALMS SUBD  S 1/2 OF S 32 T 24 R 36 SUBID 50", "24-36-32-50-*-35"),
    ("LT 75H PB 55 PG 37  WATERSTONE PLAT ONE P.U.D. S 04 T 30 R 37 SUBID UT", "30-37-04-UT-*-75H"),
]


def test_all_live_confirmed_constructions():
    for legal, expected in CONFIRMED:
        parsed = parse_legal(legal)
        assert build_parcel_id(parsed, BREVARD_CFG) == expected, legal


def test_unverified_county_raises():
    parsed = parse_legal(CONFIRMED[0][0])
    try:
        build_parcel_id(parsed, {"format": None, "verified": False})
    except ValueError:
        return
    raise AssertionError("expected ValueError for unverified county config")
