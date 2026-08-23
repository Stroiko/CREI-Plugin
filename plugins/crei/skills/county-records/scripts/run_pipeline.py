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
import sys
from datetime import date, datetime
from pathlib import Path

from parse_legal import parse_legal, ParsedLegal
from build_parcel_id import build_parcel_id
from enrich import derive_signals
from score import score_lead

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

    seen, records, review = set(), [], []
    for row in rows:
        instrument = (row.get("InstrumentNumber") or "").strip()
        if instrument and instrument in seen:
            continue
        seen.add(instrument)

        base = {
            "instrument": instrument,
            "record_date": (parse_record_date(row.get("RecordDate")) or date.min).isoformat(),
            "doc_type": (row.get("DocTypeDescription") or "").strip(),
            "direct_name": (row.get("DirectName") or "").strip(),
            "indirect_name": (row.get("IndirectName") or "").strip(),
            "case_number": (row.get("CaseNumber") or "").strip(),
            "legal": (row.get("DocLegalDescription") or "").strip(),
            "provisional": (row.get("U") or "").strip().upper() == "U",
        }
        base["case_class"] = ("CC" if "-CC-" in base["case_number"]
                              else "CA" if "-CA-" in base["case_number"] else "other")

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
    if total and len(review) / total > 0.30:
        print("WARNING: >30% of records in review - county format may differ; "
              "investigate before shipping leads", file=sys.stderr)


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
        account = parcels.get(rec["parcel_id"])
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
