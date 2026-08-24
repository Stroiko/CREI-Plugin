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
    city: Optional[str] = None  # GovOS carries the municipality ("Township:") - disambiguates appraiser owner matches


@dataclass
class ParsedCaseComments:
    """Case-comments legal (Highlands style): 'CASE # 26-413-GCAXMX/L8 PT L9
    BLK 180 WOODLAWN TERRACE'. Joins via appraiser owner-name lookup with a
    legal-description cross-check."""
    case_number: str
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


# Case numbers never contain '/', so split at the FIRST slash - legals often do
# ("L8/9 BLK A ...").
_SF_LOT = re.compile(r"\b(?:LT|UN)\s+(\d+[A-Z]?)")
_SF_BLK = re.compile(r"\bBLK\s+([A-Z0-9][A-Z0-9.]*)\b")
_SF_FIRST_TOKEN = re.compile(r"\b(?:BLK\s+[A-Z0-9]|(?:LT|UN)\s+\d)")


def parse_legal_subfirst(legal: str) -> Union[ParsedNameLegal, ReviewRecord]:
    """Parse subdivision-first name-based legals (NewVision style):
    '{SUBDIVISION NAME} [BLK b] LT l [trailing refs]'."""
    raw = (legal or "").strip()
    text = re.sub(r"\s+", " ", raw.upper())
    if not text:
        return ReviewRecord("empty", raw)

    lot_m = _SF_LOT.search(text)
    if not lot_m:
        return ReviewRecord("missing_fields", raw, detail="missing: lot")

    first = _SF_FIRST_TOKEN.search(text)
    subdivision = text[:first.start()].strip(" .,-")
    if not subdivision:
        return ReviewRecord("missing_fields", raw, detail="missing: subdivision name")

    blk_m = _SF_BLK.search(text)
    return ParsedNameLegal(
        lot=lot_m.group(1),
        block=blk_m.group(1) if blk_m else None,
        subdivision=subdivision,
        raw=raw,
    )


_LB_TOKEN = re.compile(r"\b(Lot|Block|Unit|Tract|Section|Township|Range|Building):\s*([A-Z0-9.]+)", re.I)


def parse_legal_labeled(legal: str) -> Union[ParsedNameLegal, ReviewRecord]:
    """Parse labeled-token legals (Tyler Self-Service style):
    'Lot: 8 Block: C    RI MAR RIDGE' / 'Unit: 2427    SOME CONDO'.
    The subdivision NAME is whatever free text follows the labeled tokens."""
    raw = (legal or "").strip()
    text = re.sub(r"\s+", " ", raw.upper())
    if not text:
        return ReviewRecord("empty", raw)

    # TS: = timeshare (fractional interests, e.g. Disney resorts) - not
    # joinable to a whole parcel and not a usable lead.
    if re.search(r"\bTS:", text):
        return ReviewRecord("condo_unit", raw, detail="timeshare")

    tokens = {m.group(1).upper(): m.group(2)
              for m in _LB_TOKEN.finditer(raw)}
    tail = _LB_TOKEN.sub("", raw)
    subdivision = re.sub(r"\s+", " ", tail).strip(" .,-").upper() or None

    lot = tokens.get("LOT") or tokens.get("UNIT") or tokens.get("TRACT")
    if not lot:
        if {"SECTION", "TOWNSHIP", "RANGE"} & tokens.keys():
            return ReviewRecord("metes_and_bounds", raw)
        return ReviewRecord("missing_fields", raw, detail="missing: lot/unit")
    if not subdivision:
        return ReviewRecord("missing_fields", raw, detail="missing: subdivision name")

    return ParsedNameLegal(
        lot=lot,
        block=tokens.get("BLOCK"),
        subdivision=subdivision,
        raw=raw,
    )


# GovOS Cloud Search legals are segment-structured:
#   'Subdivision - Name: LUNA BUSINESS PARK Lot: 1R Block: C Township: CARROLLTON Reference - 202600116366/'
#   'Survey - Name: JJ METCALF SUR Survey: 885 Acres: 26.1'
# "Township:" is the MUNICIPALITY (Dallas-area cities), not a PLSS township.
# "Reference -" carries a prior book/page or instrument - not part of the legal.
_GV_KIND = re.compile(r"\b(Subdivision|Survey|Condominium|Abstract)\s*-\s*Name:", re.I)
_GV_LABELS = r"Name|Lot|Block|City Block|Township|Unit|Building|Survey|Acres|Tract"
_GV_TOKEN = re.compile(
    rf"\b({_GV_LABELS}):\s*(.+?)(?=\s+(?:{_GV_LABELS}):|\s+Reference\s*-|$)", re.I)


def parse_legal_govos(legal: str) -> Union[ParsedNameLegal, ReviewRecord]:
    """Parse a GovOS Cloud Search legal-description string (see grammar above).
    Only the first Subdivision segment is used; Survey-only legals are
    metes-and-bounds equivalents and go to review."""
    raw = (legal or "").strip()
    if not raw:
        return ReviewRecord("empty", raw)

    kinds = [(m.group(1).upper(), m.start()) for m in _GV_KIND.finditer(raw)]
    if not kinds:
        return ReviewRecord("missing_fields", raw, detail="no Subdivision/Survey segment")
    sub_starts = [start for kind, start in kinds if kind == "SUBDIVISION"]
    if not sub_starts:
        if any(kind == "CONDOMINIUM" for kind, _ in kinds):
            return ReviewRecord("condo_unit", raw)
        return ReviewRecord("metes_and_bounds", raw)

    # First Subdivision segment runs to the next kind marker (or end of string).
    start = sub_starts[0]
    later = [s for _, s in kinds if s > start]
    segment = raw[start:min(later)] if later else raw[start:]

    tokens = {m.group(1).upper(): m.group(2).strip()
              for m in _GV_TOKEN.finditer(segment)}
    subdivision = (tokens.get("NAME") or "").strip().upper() or None
    lot = tokens.get("LOT") or tokens.get("UNIT")
    if not subdivision:
        return ReviewRecord("missing_fields", raw, detail="missing: subdivision name")
    if not lot:
        return ReviewRecord("missing_fields", raw, detail="missing: lot/unit")
    return ParsedNameLegal(
        lot=lot.upper(),
        block=(tokens.get("BLOCK") or "").upper() or None,
        subdivision=subdivision,
        raw=raw,
        city=(tokens.get("TOWNSHIP") or "").upper() or None,
    )


_CC_SPLIT = re.compile(r"^CASE\s*#\s*([^/\s]+)\s*/\s*(.*)$")
# L8, L84A, L8/9 (first taken), L137-139 (first taken), PARCEL 45
_CC_LOT = re.compile(r"\b(?:L|PARCEL\s+)(\d+[A-Z]?)")
_CC_BLK = re.compile(r"\bBLK\s+([A-Z0-9][A-Z0-9.]*)\b")
_CC_SEC_ONLY = re.compile(r"\bSEC\s+\d")


def parse_legal_case_comments(text: str) -> Union[ParsedCaseComments, ReviewRecord]:
    """Parse 'CASE # {case}/{abbreviated legal}' comments (Highlands style)."""
    raw = (text or "").strip()
    norm = re.sub(r"\s+", " ", raw.upper())
    if not norm:
        return ReviewRecord("empty", raw)

    split = _CC_SPLIT.match(norm)
    if not split:
        return ReviewRecord("missing_fields", raw, detail="no CASE #/legal structure")
    case_number, legal = split.groups()

    if _CC_SEC_ONLY.search(legal) and not _CC_LOT.search(legal):
        return ReviewRecord("metes_and_bounds", raw)

    lot_m = _CC_LOT.search(legal)
    if not lot_m:
        return ReviewRecord("missing_fields", raw, detail="missing: lot")

    blk_m = _CC_BLK.search(legal)
    # Subdivision = text after the last structural token (block if present,
    # otherwise the full lot clause incl. PT L9 / /9 / -139 continuations).
    tail_start = blk_m.end() if blk_m else lot_m.end()
    subdivision = legal[tail_start:]
    subdivision = re.sub(r"^[/0-9A-Z-]*?\s", "", subdivision + " ").strip() \
        if re.match(r"^[/-]", subdivision) else subdivision.strip()
    subdivision = re.sub(r"^(PT\s+L?\d+[A-Z]?(/\d+)?\s+)+", "", subdivision).strip(" .,")
    if not subdivision:
        return ReviewRecord("missing_fields", raw, detail="missing: subdivision name")

    return ParsedCaseComments(
        case_number=case_number,
        lot=lot_m.group(1),
        block=blk_m.group(1) if blk_m else None,
        subdivision=subdivision,
        raw=raw,
    )
