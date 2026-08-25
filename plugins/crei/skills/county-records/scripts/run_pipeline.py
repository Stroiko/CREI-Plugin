"""CLI for the county-records Layer B pipeline. Stdlib only.

  parse: raw Acclaim CSV -> parsed.json + parcel_ids.txt + review.csv
  score: parsed.json + parcels.json -> leads.csv + leads.json + summary.md

Between the two stages, the browser (Layer A) fetches each parcel ID in
parcel_ids.txt from the county appraiser and saves {parcelID: accountJSON}
as parcels.json (null for parcels that returned no match).
"""
import argparse
import csv
import json
import re
import sys
from datetime import date, datetime
from pathlib import Path

from parse_legal import (parse_legal, parse_legal_namebased, parse_legal_case_comments,
                         parse_legal_subfirst, parse_legal_labeled, parse_legal_govos,
                         parse_legal_ga_landmark,
                         ParsedLegal, ParsedNameLegal, ParsedCaseComments)
from build_parcel_id import build_parcel_id
from match_lookup import match_parcel
from enrich import derive_signals
from score import score_lead

DEFAULT_CSV_COLUMNS = {
    "legal": "DocLegalDescription",
    "caseNumber": "CaseNumber",
    "provisional": "U",
    "recordDate": "RecordDate",
    "directName": "DirectName",
    "indirectName": "IndirectName",
    "instrument": "InstrumentNumber",
    "docType": "DocTypeDescription",
}

_LANDMARK_CASE = re.compile(r"Case Number:\s*([A-Z0-9-]{6,})")


def landmark_fields(row):
    """Extract lead fields from one converted Landmark export row.

    Landmark ships the legal PRE-PARSED in columns (Lot/Block/Unit/
    Subdivision/Section/Township/Range); the free-text Legal column carries
    the case number. Units parse like lots because owner-lookup joins don't
    depend on lot/block matching."""
    lot = (row.get("Lot") or "").strip()
    unit = (row.get("Unit") or "").strip()
    subdivision = (row.get("Subdivision") or "").strip()
    defendants = [n.strip() for n in (row.get("Reverse Name") or "").split("\n") if n.strip()]

    case_m = _LANDMARK_CASE.search(row.get("Legal") or "")
    fields = {
        "lot": lot or unit or None,
        "is_unit": bool(unit and not lot),
        "block": (row.get("Block") or "").strip() or None,
        "subdivision": subdivision or None,
        "section": (row.get("Section") or "").strip() or None,
        "township": (row.get("Township") or "").strip() or None,
        "range": (row.get("Range") or "").strip() or None,
        "case_number": case_m.group(1) if case_m else "",
        "provisional": (row.get("Status") or "").strip().upper() != "V",
        "indirect_name": defendants[0] if defendants else "",
        "all_defendants": defendants,
        "review": None,
    }
    if not fields["lot"] and not fields["subdivision"]:
        fields["review"] = "missing_fields"
    return fields

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"


def load_json(path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def county_cfg(county_key):
    counties = load_json(CONFIG_DIR / "counties.json")
    if county_key not in counties:
        sys.exit(f"unknown county '{county_key}' - add it to config/counties.json "
                 f"(known: {', '.join(k for k in counties if not k.startswith('_'))})")
    return counties[county_key]


def parse_record_date(raw):
    token = (raw or "").strip().split(" ")[0]
    try:
        m, d, y = (int(p) for p in token.split("/"))
        return date(y, m, d)
    except (ValueError, AttributeError):
        return None


def cmd_parse(args):
    cfg = county_cfg(args.county)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    with open(args.csv, encoding="utf-8-sig", newline="") as f:
        rows = list(csv.DictReader(f))

    cols = {**DEFAULT_CSV_COLUMNS, **(cfg.get("csvColumns") or {})}
    legal_style = cfg.get("legalStyle", "str-subid")
    class_patterns = cfg.get("caseClassPatterns", {"CC": "-CC-", "CA": "-CA-"})

    def classify(case_number):
        for cls, pattern in class_patterns.items():
            if pattern and pattern in case_number:
                return cls
        return "other"

    seen, records, review = set(), [], []
    for row in rows:
        instrument = (row.get(cols["instrument"]) or "").strip()
        if instrument and instrument in seen:
            continue
        seen.add(instrument)

        case_number = (row.get(cols["caseNumber"]) or "").strip() if cols.get("caseNumber") else ""
        base = {
            "instrument": instrument,
            "record_date": (parse_record_date(row.get(cols["recordDate"])) or date.min).isoformat(),
            "doc_type": (row.get(cols["docType"]) or "").strip(),
            "direct_name": (row.get(cols["directName"]) or "").strip(),
            "indirect_name": (row.get(cols["indirectName"]) or "").strip(),
            "case_number": case_number,
            "legal": (row.get(cols["legal"]) or "").strip(),
            "provisional": ((row.get(cols["provisional"]) or "").strip().upper() == "U"
                            if cols.get("provisional") else False),
        }
        base["case_class"] = classify(base["case_number"])

        if legal_style == "landmark-columns":
            fields = landmark_fields(row)
            if fields["review"]:
                review.append({**row, "review_reason": fields["review"]})
                continue
            base.update(
                parcel_id=None,
                lot=fields["lot"], block=fields["block"],
                subdivision=fields["subdivision"], is_unit=fields["is_unit"],
                section=fields["section"], township=fields["township"],
                range=fields["range"],
                case_number=fields["case_number"],
                provisional=fields["provisional"],
                indirect_name=fields["indirect_name"],
                all_defendants=fields["all_defendants"],
            )
            base["case_class"] = classify(fields["case_number"])
            records.append(base)
            continue
        # Some counties put the PARCEL ID itself in the legal field - a free,
        # exact join. Config declares the county's ID shape via `directPattern`.
        # Polk's legal IS the parcel ID verbatim. Aumentum counties prefix it
        # ("PIN 18812010002") and the appraiser wants it dashed (18812-010-002):
        # `directFormat` is a numbered-group template applied to the match.
        # A trailing "(+)" (more-parties marker) is tolerated if not stripped.
        direct_pattern = (cfg.get("parcelId") or {}).get("directPattern")
        if direct_pattern:
            legal_for_direct = re.sub(r"\s*\(\+\)\s*$", "", base["legal"])
            dm = re.fullmatch(direct_pattern, legal_for_direct)
            if dm:
                direct_format = (cfg.get("parcelId") or {}).get("directFormat")
                base.update(
                    parcel_id=(direct_format.format(*dm.groups()) if direct_format
                               else legal_for_direct),
                    subdivision=None)
                records.append(base)
                continue

        # Some counties EMBED a parcel ID inside a longer legal string (GA
        # Landmark: "...SUB:RENAISSANCE LAKES Parcel: 15 122 02 012 Tax
        # District:..."). `parcelExtract` is a search (not fullmatch) whose
        # first group is the parcel - a direct join when present.
        parcel_extract = (cfg.get("parcelId") or {}).get("parcelExtract")
        if parcel_extract:
            pm = re.search(parcel_extract, base["legal"])
            if pm:
                base.update(parcel_id=pm.group(1).strip(), subdivision=None)
                records.append(base)
                continue

        if legal_style in ("name-based", "name-based-subfirst", "labeled-tokens",
                           "govos-labeled", "ga-landmark"):
            # GovOS counties whose grid carries pre-parsed Lot/Block (and
            # sometimes PropertyAddress) columns instead of a legal string
            # (Bexar pattern): a row with an empty legal but usable columns is
            # joinable, not a review case.
            if legal_style == "govos-labeled" and not base["legal"]:
                col_lot = (row.get("Lot") or "").strip()
                col_block = (row.get("Block") or "").strip()
                col_addr = (row.get("PropertyAddress") or "").strip()
                if col_lot.upper() not in ("", "N/A") and (
                        col_block.upper() not in ("", "N/A") or col_addr.upper() not in ("", "N/A")):
                    base.update(parcel_id=None,
                                lot=col_lot.upper(),
                                block=(col_block.upper() or None) if col_block.upper() != "N/A" else None,
                                subdivision=None)
                    if col_addr and col_addr.upper() != "N/A":
                        base["property_address"] = col_addr
                    records.append(base)
                    continue
            parser = {"name-based-subfirst": parse_legal_subfirst,
                      "labeled-tokens": parse_legal_labeled,
                      "govos-labeled": parse_legal_govos,
                      "ga-landmark": parse_legal_ga_landmark}.get(
                          legal_style, parse_legal_namebased)
            parsed = parser(base["legal"])
            if row.get("AllDefendants"):
                base["all_defendants"] = [n.strip() for n in
                                          row["AllDefendants"].split(";") if n.strip()]
            if isinstance(parsed, ParsedNameLegal):
                base.update(parcel_id=None, lot=parsed.lot, block=parsed.block,
                            subdivision=parsed.subdivision)
                if parsed.city:
                    base["city"] = parsed.city
                records.append(base)
                continue
        elif legal_style == "case-comments":
            parsed = parse_legal_case_comments(base["legal"])
            if isinstance(parsed, ParsedCaseComments):
                base["case_number"] = parsed.case_number
                base["case_class"] = classify(parsed.case_number)
                base.update(parcel_id=None, lot=parsed.lot, block=parsed.block,
                            subdivision=parsed.subdivision)
                records.append(base)
                continue
        else:
            parsed = parse_legal(base["legal"])
            if isinstance(parsed, ParsedLegal):
                try:
                    base["parcel_id"] = build_parcel_id(parsed, cfg.get("parcelId") or {})
                    base["subdivision"] = parsed.subdivision
                    records.append(base)
                    continue
                except ValueError as e:
                    review.append({**row, "review_reason": str(e)})
                    continue
        review.append({**row, "review_reason": f"{parsed.reason} {parsed.detail}".strip()})

    (out / "parsed.json").write_text(
        json.dumps({"county": args.county, "source_csv": str(args.csv),
                    "records": records}, indent=2), encoding="utf-8")
    strategy = cfg.get("joinStrategy", "construct")
    if strategy == "subdivision-lookup":
        (out / "lookups.txt").write_text(
            "\n".join(sorted({r["subdivision"] for r in records})) + "\n", encoding="utf-8")
    elif strategy == "owner-lookup":
        (out / "owners.txt").write_text(
            "\n".join(sorted({r["indirect_name"] for r in records
                              if r["indirect_name"] and not r.get("parcel_id")}))
            + "\n", encoding="utf-8")
        direct = sorted({r["parcel_id"] for r in records if r.get("parcel_id")})
        if direct:
            (out / "parcel_ids.txt").write_text("\n".join(direct) + "\n", encoding="utf-8")
    else:
        (out / "parcel_ids.txt").write_text(
            "\n".join(sorted({r["parcel_id"] for r in records})) + "\n", encoding="utf-8")
    if review:
        with open(out / "review.csv", "w", encoding="utf-8", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=list(review[0].keys()))
            writer.writeheader()
            writer.writerows(review)

    total = len(records) + len(review)
    print(f"parsed {len(records)}/{total} records -> {out / 'parsed.json'}")
    print(f"review {len(review)}/{total} records -> {out / 'review.csv' if review else '(none)'}")
    # Condo units and metes-and-bounds are known-unjoinable categories, not
    # parser failures - only unexpected reasons indicate a format mismatch.
    unexpected = [r for r in review
                  if not r["review_reason"].startswith(("condo_unit", "metes_and_bounds"))]
    if total and len(unexpected) / total > 0.30:
        print("WARNING: >30% of records failed parsing for unexpected reasons - "
              "county format may differ; investigate before shipping leads",
              file=sys.stderr)


def cmd_match(args):
    """Assign parcel IDs to name-based records from Layer A subdivision results."""
    out = Path(args.out)
    parsed = load_json(args.parsed)
    subdivisions = load_json(args.subdivisions)

    matched = unmatched = 0
    for rec in parsed["records"]:
        if rec.get("parcel_id"):
            continue
        candidates = subdivisions.get(rec.get("subdivision") or "", [])
        pid = match_parcel(rec["lot"], rec.get("block"), candidates) if candidates else None
        if pid:
            rec["parcel_id"] = pid
            matched += 1
        else:
            unmatched += 1

    out.mkdir(parents=True, exist_ok=True)
    (out / "parsed.json").write_text(json.dumps(parsed, indent=2), encoding="utf-8")
    (out / "parcel_ids.txt").write_text(
        "\n".join(sorted({r["parcel_id"] for r in parsed["records"] if r.get("parcel_id")}))
        + "\n", encoding="utf-8")
    print(f"matched {matched}, unmatched {unmatched} (ship unenriched) -> {out / 'parsed.json'}")


def cmd_score(args):
    cfg = county_cfg(args.county)
    scoring = load_json(args.scoring or CONFIG_DIR / "scoring.json")
    parsed = load_json(args.parsed)
    parcels = load_json(args.parcels) if args.parcels else {}
    as_of = args.as_of or date.today().isoformat()
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)

    leads = []
    for rec in parsed["records"]:
        # Owner-lookup counties key parcels.json by instrument number (no
        # parcel ID exists until the appraiser lookup resolves one).
        account = parcels.get(rec.get("parcel_id")) or parcels.get(rec["instrument"])
        if account and not rec.get("parcel_id"):
            rec["parcel_id"] = account.get("parcelID")
        rec_date = datetime.strptime(rec["record_date"], "%Y-%m-%d").date()
        age = (datetime.strptime(as_of, "%Y-%m-%d").date() - rec_date).days
        signals = derive_signals(rec["indirect_name"], account,
                                 cfg.get("state", ""), as_of)
        lead = {**rec, "record_age_days": age, "signals": signals}
        result = score_lead(lead, scoring)
        leads.append({
            **rec,
            "record_age_days": age,
            "score": result["score"],
            "contributions": result["contributions"],
            "signals": signals,
            "site_address": (account or {}).get("siteAddress"),
            "owner": (account or {}).get("owner"),
            "mailing_address": ((account or {}).get("mailingAddress") or {}).get("formatted"),
            "market_value": (account or {}).get("marketValue"),
        })

    leads.sort(key=lambda l: l["score"], reverse=True)

    signal_names = [s for s in scoring["signals"] if not s.startswith("_")]
    with open(out / "leads.csv", "w", encoding="utf-8", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["rank", "score", "lead", "parcel_id", "site_address",
                         "case_class", "case_number", "record_date", "market_value",
                         "tenure_years", "enriched"]
                        + [f"contrib_{s}" for s in signal_names])
        for i, l in enumerate(leads, 1):
            writer.writerow([i, l["score"], l["indirect_name"], l["parcel_id"],
                             l["site_address"], l["case_class"], l["case_number"],
                             l["record_date"], l["market_value"],
                             l["signals"]["tenure_years"], l["signals"]["enriched"]]
                            + [l["contributions"].get(s, 0) for s in signal_names])

    (out / "leads.json").write_text(json.dumps(leads, indent=2), encoding="utf-8")

    fired = {s: sum(1 for l in leads if s in l["contributions"]) for s in signal_names}
    unenriched = sum(1 for l in leads if not l["signals"]["enriched"])
    lines = [
        f"# Lead summary — {cfg.get('displayName', args.county)}",
        "",
        f"- Leads scored: **{len(leads)}** (as of {as_of})",
        f"- Unenriched (no appraiser match): **{unenriched}**" if unenriched else "- All leads enriched",
        "",
        "## Signal frequency",
        "",
        "| Signal | Leads |",
        "|---|---|",
        *[f"| {s} | {n} |" for s, n in sorted(fired.items(), key=lambda kv: -kv[1]) if n],
        "",
        "## Top leads",
        "",
        "| # | Score | Case | Why |",
        "|---|---|---|---|",
    ]
    for i, l in enumerate(leads[:10], 1):
        why = ", ".join(f"{k} +{v:g}" for k, v in
                        sorted(l["contributions"].items(), key=lambda kv: -kv[1]))
        lines.append(f"| {i} | {l['score']:g} | {l['case_class']} {l['case_number']} | {why} |")
    (out / "summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(f"scored {len(leads)} leads -> {out / 'leads.csv'}, {out / 'summary.md'}")


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("parse", help="raw Acclaim CSV -> parsed.json + parcel_ids.txt + review.csv")
    p.add_argument("--csv", required=True)
    p.add_argument("--county", required=True)
    p.add_argument("--out", required=True)
    p.set_defaults(func=cmd_parse)

    m = sub.add_parser("match", help="fill parcel IDs for name-based counties from subdivision lookup results")
    m.add_argument("--parsed", required=True)
    m.add_argument("--subdivisions", required=True,
                   help='JSON: {"<subdivision name>": [{"pid": ..., "legal": ...}]}')
    m.add_argument("--out", required=True)
    m.set_defaults(func=cmd_match)

    s = sub.add_parser("score", help="parsed.json + parcels.json -> ranked leads + summary")
    s.add_argument("--parsed", required=True)
    s.add_argument("--parcels", help="parcels.json from the enrichment stage (optional)")
    s.add_argument("--county", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--scoring", help="override scoring config path")
    s.add_argument("--as-of", dest="as_of", help="YYYY-MM-DD (default: today)")
    s.set_defaults(func=cmd_score)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
