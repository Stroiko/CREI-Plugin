"""Match a parsed name-based legal to exactly one appraiser candidate row.

Candidates come from the appraiser's subdivision search (Layer A saves
{query: [{"pid": ..., "legal": ...}]}). Matching is strict: the candidate's
legal must contain the lot as a whole token (LOT 1 must not match LOT 10),
the block must agree when present, and exactly ONE candidate may survive -
anything else returns None and the lead ships unenriched rather than
mis-joined.
"""
import re


def _lot_matches(lot: str, legal: str) -> bool:
    # Matches "LOT 4", "LOTS 10 AND 11", "W 60FT LOT 7" - lot as exact token.
    pattern = re.compile(r"\bLOTS?\b[^,]*?\b" + re.escape(lot) + r"\b")
    return bool(pattern.search(legal))


def _block_matches(block, legal: str) -> bool:
    blk_m = re.search(r"\bBLK\s+([A-Z0-9][A-Z0-9.]*)", legal)
    if block is None:
        return blk_m is None
    return bool(blk_m) and blk_m.group(1) == block


def match_parcel(lot, block, candidates):
    hits = [c for c in candidates
            if _lot_matches(lot, c["legal"].upper())
            and _block_matches(block.upper() if block else None, c["legal"].upper())]
    if len(hits) == 1:
        return hits[0]["pid"]
    return None
