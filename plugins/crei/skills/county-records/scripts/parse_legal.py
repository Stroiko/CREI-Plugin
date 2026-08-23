"""Parse Acclaim DocLegalDescription strings into structured fields.

Grammar (from real Brevard/Pinellas records):
    LT {lot} [BLK {block}] PB {book} PG {page}  {SUBDIVISION}  S {sec} T {twp} R {rng} SUBID {subid}

Anything that can't be parsed with confidence becomes a ReviewRecord with a
reason - records are never guessed at and never dropped.
"""
import re
from dataclasses import dataclass
from typing import Optional, Union


@dataclass
class ParsedLegal:
    lot: str
    block: Optional[str]
    plat_book: Optional[str]
    plat_page: Optional[str]
    subdivision: Optional[str]
    section: str
    township: str
    range: str
    subid: str
    raw: str


@dataclass
class ReviewRecord:
    reason: str  # empty | condo_unit | metes_and_bounds | missing_fields
    raw: str
    detail: str = ""


@dataclass
class ParsedNameLegal:
    """Name-based legal (Pinellas style): 'LOT 4 BLOCK A PINELLE PARTIAL REPLAT'.
    Joins via appraiser subdivision lookup, not string construction."""
    lot: str
    block: Optional[str]
    subdivision: str
    raw: str


# Standalone unit token: "U A228", "U 101", "U 19" (not the U in "P.U.D." - the
# dot after U breaks \s+; not "UNIT" inside subdivision names).
_UNIT_TOKEN = re.compile(r"(?:^|\s)U\s+[A-Z0-9]")
_UW_TOKEN = re.compile(r"\bUW\s*\d")
_ORB_REF = re.compile(r"\bORB\s+\d+\s*/\s*\d+")
_METES_START = re.compile(r"\b(FROM|BEG|COMM|COMMENCE|COMMENCING)\b")
_STR_CLAUSE = re.compile(r"\bS\s+(\d+[A-Z]?)\s+T\s+(\d+[A-Z]?)\s+R\s+(\d+[A-Z]?)\b")
_LOT = re.compile(r"\bLT\s+([A-Z0-9][A-Z0-9.]*)")
_BLK = re.compile(r"\bBLK\s+([A-Z0-9][A-Z0-9.]*)")
_PLAT = re.compile(r"\bPB\s+(\d+)\s+PG\s+(\d+)")
_SUBID = re.compile(r"\bSUBID\s+([A-Z0-9]+)")


def parse_legal(legal: str) -> Union[ParsedLegal, ReviewRecord]:
    raw = (legal or "").strip()
    text = re.sub(r"\s+", " ", raw.upper())
    if not text:
        return ReviewRecord("empty", raw)

    # Condo/timeshare units: parcel IDs are not constructible from these -
    # they carry unit/week tokens and/or ORB condo-declaration references.
    if _UNIT_TOKEN.search(text) or _UW_TOKEN.search(text) or _ORB_REF.search(text):
        return ReviewRecord("condo_unit", raw)

    has_lot = bool(_LOT.search(text))
    if not has_lot and _METES_START.search(text):
        return ReviewRecord("metes_and_bounds", raw)

    str_matches = list(_STR_CLAUSE.finditer(text))
    lot_m = _LOT.search(text)
    subid_m = _SUBID.search(text)
    if not (lot_m and str_matches and subid_m):
        missing = [name for name, ok in
                   (("lot", lot_m), ("section/township/range", str_matches),
                    ("subid", subid_m)) if not ok]
        return ReviewRecord("missing_fields", raw, detail="missing: " + ", ".join(missing))

    # The LAST S/T/R clause is authoritative ("S 1/2 OF S 32 T 24 R 36" -> 32/24/36).
    section, township, rng = str_matches[-1].groups()

    blk_m = _BLK.search(text)
    plat_m = _PLAT.search(text)

    subdivision = None
    if plat_m:
        subdivision = text[plat_m.end():str_matches[-1].start()].strip(" -,") or None

    return ParsedLegal(
        lot=lot_m.group(1),
        block=blk_m.group(1) if blk_m else None,
        plat_book=plat_m.group(1) if plat_m else None,
        plat_page=plat_m.group(2) if plat_m else None,
        subdivision=subdivision,
        section=section,
        township=township,
        range=rng,
        subid=subid_m.group(1),
        raw=raw,
    )


_NB_CONDO = re.compile(r"\b(UNIT|APARTMENT|APT|CONDOMINIUM|CONDO)\b")
_NB_LOT = re.compile(r"\bLOTS?\s+(\d+[A-Z0-9.]*)\b")
_NB_BLOCK = re.compile(r"\bBLOCK\s+([A-Z0-9][A-Z0-9.]*)\b")


def parse_legal_namebased(legal: str) -> Union[ParsedNameLegal, ReviewRecord]:
    """Parse a name-based legal: LOT {n} [BLOCK {b}] [OF] {SUBDIVISION NAME}.

    The subdivision NAME (not a code) is the join key - Layer A looks it up on
    the appraiser's sub/condo search, trying name variants as needed."""
    raw = (legal or "").strip()
    text = re.sub(r"\s+", " ", raw.upper())
    if not text:
        return ReviewRecord("empty", raw)
    if _NB_CONDO.search(text):
        return ReviewRecord("condo_unit", raw)

    lot_m = _NB_LOT.search(text)
    if not lot_m:
        return ReviewRecord("missing_fields", raw, detail="missing: lot")

    blk_m = _NB_BLOCK.search(text)
    # Subdivision = whatever follows the last structural token (BLOCK x or the
    # lot clause), minus a leading OF.
    tail_start = blk_m.end() if blk_m else lot_m.end()
    subdivision = text[tail_start:].strip()
    subdivision = re.sub(r"^OF\s+", "", subdivision).strip(" .,")
    if not subdivision:
        return ReviewRecord("missing_fields", raw, detail="missing: subdivision name")

    return ParsedNameLegal(
        lot=lot_m.group(1),
        block=blk_m.group(1) if blk_m else None,
        subdivision=subdivision,
        raw=raw,
    )
