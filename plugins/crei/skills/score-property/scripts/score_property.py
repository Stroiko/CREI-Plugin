"""CLI: gathered-facts JSON -> deal scorecard (scorecard.json + scorecard.md).

    python score_property.py score --input facts.json --out work/

Stdlib only. The facts JSON is assembled by the agent from the zillow / hud-fmr
/ rental-cashflow / county-records skills (see SKILL.md). The scoring math lives
in lenses.py and the weights in config/scoring.json - nothing is hardcoded here.
"""
import argparse
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from lenses import score_property

CONFIG_DIR = Path(__file__).resolve().parent.parent / "config"

_TIER_MEANING = {
    "A": "strong on two lenses - pursue",
    "B": "one lens strong - worth a closer look",
    "C": "middling across the board",
    "D": "a cash-flow or margin failure with nothing to offset it",
    "NR": "not rated - no lens could be scored",
}


def _load(path):
    with open(path, encoding="utf-8-sig") as f:
        return json.load(f)


def _fmt(v):
    return "—" if v is None else f"{v:g}"


def _why(contrib):
    return ", ".join(f"{k} +{v:g}" for k, v in
                     sorted(contrib.items(), key=lambda kv: -kv[1])) or "—"


def _markdown(card):
    lines = [
        f"# Deal scorecard — {card.get('address') or 'property'}",
        "",
        f"**Tier {card['tier']}** — {_TIER_MEANING.get(card['tier'], '')}  ",
        f"_{card['tier_basis']}_",
        "",
        "| Lens | Score | Confidence | Why |",
        "|---|---|---|---|",
    ]
    for name in ("cashflow", "margin", "motivation"):
        l = card["lenses"][name]
        label = name.capitalize()
        if name == "motivation" and l.get("layer"):
            label += f" ({l['layer']})"
        lines.append(f"| {label} | {_fmt(l['score'])} | {l['confidence']} | "
                     f"{_why(l['contrib'])} |")
    lines += ["", "## Lens detail", ""]
    for name in ("cashflow", "margin", "motivation"):
        l = card["lenses"][name]
        lines.append(f"- **{name.capitalize()}** ({l['confidence']}): {l['basis']}")
    lines += ["",
              "_Scores are screening estimates, not investment advice. "
              "Every lens degrades independently; a `—` means the data to score "
              "it was not available, not a zero._"]
    return "\n".join(lines) + "\n"


def cmd_score(args):
    cfg = _load(args.config or CONFIG_DIR / "scoring.json")
    facts = _load(args.input)
    card = score_property(facts, cfg)

    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    (out / "scorecard.json").write_text(json.dumps(card, indent=2), encoding="utf-8")
    (out / "scorecard.md").write_text(_markdown(card), encoding="utf-8")

    summary = {"tier": card["tier"], "lenses_available": card["lenses_available"],
               "lenses": {k: {"score": v["score"], "confidence": v["confidence"]}
                          for k, v in card["lenses"].items()}}
    print(json.dumps(summary))
    print(f"scored -> {out / 'scorecard.md'}", file=sys.stderr)


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    sub = ap.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("score", help="gathered-facts JSON -> scorecard")
    s.add_argument("--input", required=True)
    s.add_argument("--out", required=True)
    s.add_argument("--config", help="override config/scoring.json path")
    s.set_defaults(func=cmd_score)
    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
