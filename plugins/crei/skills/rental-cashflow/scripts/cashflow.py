"""CLI for the rental cashflow analyzer.

Usage:
    python cashflow.py analyze --input work/property.json --out work/ \
        [--defaults path/to/defaults.json] [--as-of-year 2026]

Reads the property/financing/rent-scenarios JSON, runs calc.analyze, and
writes analysis.json (full structure) + summary.md (side-by-side tables)
into the --out directory.
"""
import argparse
import datetime
import json
import sys
from pathlib import Path

from calc import analyze

ROW_LABELS = [
    ("gross_rent", "Gross Rent"),
    ("vacancy", "Vacancy"),
    ("effective_rent", "Effective Rent"),
    ("mortgage_pi", "Mortgage P&I"),
    ("management", "Property Management"),
    ("insurance", "Insurance"),
    ("property_tax", "Property Tax"),
    ("maintenance", "Maintenance"),
    ("capex", "CapEx"),
    ("hoa", "HOA Fee"),
    ("cash_flow", "Cash Flow"),
]


def fmt_money(v):
    return "${:,.2f}".format(v)


def mode_table(result, mode_name, title):
    scenarios = result["scenarios"]
    out = ["### {}".format(title), ""]
    header = "| Monthly | " + " | ".join(s["label"] for s in scenarios) + " |"
    sep = "|---" * (len(scenarios) + 1) + "|"
    out += [header, sep]
    for item, label in ROW_LABELS:
        cells = []
        for s in scenarios:
            line = next(l for l in s["modes"][mode_name]["lines"]
                        if l["item"] == item)
            val = fmt_money(line["amount"])
            if line["sign"] == "-" and line["amount"] > 0:
                val = "-" + val
            if item in ("effective_rent", "cash_flow"):
                val = "**{}**".format(val)
            cells.append(val)
        out.append("| {} | {} |".format(label, " | ".join(cells)))
    dscr_cells, verdict_cells = [], []
    for s in scenarios:
        m = s["modes"][mode_name]
        dscr_cells.append("{:.2f}".format(m["dscr"]) if m["dscr"] is not None
                          else "N/A")
        verdict_cells.append(m["dscr_verdict"])
    out.append("| DSCR | {} |".format(" | ".join(dscr_cells)))
    out.append("| DSCR Verdict | {} |".format(" | ".join(verdict_cells)))
    out.append("")
    return out


def assumptions_block(assumptions):
    out = ["## Assumptions used", ""]
    for key, val in assumptions.items():
        if isinstance(val, dict) and "value" in val and "source" in val:
            out.append("- **{}**: {:.2%} ({})".format(
                key, val["value"], val["source"]))
        elif isinstance(val, dict):
            out.append("- **{}**: {}".format(key, json.dumps(val)))
        else:
            out.append("- **{}**: {}".format(key, val))
    out += ["", "_These are estimates for screening, not lending or investment"
            " advice. DSCR verdict is against a configurable threshold, not a"
            " lender decision._"]
    return out


def build_summary(result, inp):
    prop = inp["property"]
    lines = ["# Rental Cash Flow Analysis", "",
             "**Property:** {}".format(prop.get("address", "n/a")), ""]
    lines += mode_table(result, "self_managed", "Self-managed (0% management)")
    lines += mode_table(
        result, "managed",
        "With property management ({:.0%})".format(
            result["assumptions"]["management_pct_when_managed"]["value"]))
    lines += assumptions_block(result["assumptions"])
    return "\n".join(lines) + "\n"


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)
    p = sub.add_parser("analyze", help="run the full analysis")
    p.add_argument("--input", required=True, help="property.json path")
    p.add_argument("--out", required=True, help="output directory")
    p.add_argument("--defaults",
                   default=str(Path(__file__).resolve().parents[1]
                               / "config" / "defaults.json"))
    p.add_argument("--as-of-year", type=int, default=None,
                   help="year for home-age tiers (default: input file value,"
                        " else current year)")
    args = parser.parse_args(argv)

    inp = json.loads(Path(args.input).read_text(encoding="utf-8"))
    defaults = json.loads(Path(args.defaults).read_text(encoding="utf-8"))
    if args.as_of_year:
        inp["as_of_year"] = args.as_of_year
    elif not inp.get("as_of_year"):
        inp["as_of_year"] = datetime.date.today().year

    result = analyze(inp, defaults)

    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "analysis.json").write_text(
        json.dumps(result, indent=2), encoding="utf-8")
    (out_dir / "summary.md").write_text(build_summary(result, inp),
                                        encoding="utf-8")
    print(json.dumps({
        "analysis": str(out_dir / "analysis.json"),
        "summary": str(out_dir / "summary.md"),
        "scenarios": [s["label"] for s in result["scenarios"]],
    }))
    return 0


if __name__ == "__main__":
    sys.exit(main())
