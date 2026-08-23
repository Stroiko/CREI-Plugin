"""Construct a county parcel ID from a parsed legal description.

The format template comes from config/counties.json and is county-specific.
Construction is only allowed for counties whose format has been verified
against real parcels (verified: true) - guessing produces wrong joins.
"""
from parse_legal import ParsedLegal


def build_parcel_id(parsed: ParsedLegal, parcel_cfg: dict) -> str:
    if not parcel_cfg.get("verified") or not parcel_cfg.get("format"):
        raise ValueError(
            "parcel-ID format not verified for this county - "
            "verify 3+ real parcels before constructing (see references/acclaim.md)")

    block = parsed.block if parsed.block is not None else parcel_cfg.get("noBlockToken", "*")
    return (parcel_cfg["format"]
            .replace("{T}", parsed.township)
            .replace("{R}", parsed.range)
            .replace("{S}", parsed.section)
            .replace("{SUBID}", parsed.subid)
            .replace("{BLK}", block)
            .replace("{LOT}", parsed.lot))
