# CREI — Claude Real Estate Investing

Find motivated-seller leads with Claude. CREI pulls fresh pre-foreclosure
filings (lis pendens) straight from county court records — before they hit any
listing site — joins them to ownership data, and hands you a **ranked, scored
lead list where every score is explained**.

## ✅ Before you install — you need ALL THREE of these

1. **The Claude Desktop app, installed and open.** The plugin drives your
   browser as part of the task; the web version of claude.ai can't do that.
2. **Claude in Chrome enabled** (the Claude Chrome extension, signed in). All
   county-records and Zillow browsing happens in *your* Chrome — county sites
   only answer real residential connections.
3. **A plan with Cowork + browser use** (Max or Team at time of writing;
   check current availability).

If any of these is missing the plugin will not work — this is a platform
requirement, not a plugin bug.

## Install (about 60 seconds)

1. Open the Claude Desktop app.
2. Go to **Customize → Plugins**.
3. Click **Add → Add Marketplace**.
4. Paste this repository's URL:
   `https://github.com/kjf305/CREI_plugin`
5. Install the **CREI — Claude Real Estate Investing** plugin.

## Use it

Just ask Claude things like:

> "Find motivated sellers in Brevard County from the last two weeks."

> "Pull this week's lis pendens for Pinellas County and score the leads."

> "Check Zillow for new foreclosure listings in Orlando under $400k."

Claude will drive the county records portal in your Chrome, export the
filings, construct/lookup each property's parcel, pull ownership data from
the county appraiser, and give you a ranked CSV + summary. Expect a full
county run to take several minutes — it deliberately works slowly and
politely against government websites.

## What's inside

| Skill | What it does |
|---|---|
| `county-records` | The lead pipeline: county distress filings → parcel join → ownership signals → explainable scoring |
| `zillow` | Zillow search & property detail extraction: listings, foreclosures, FSBO, rent estimates |

## County coverage (v1)

| County | Status |
|---|---|
| Brevard, FL | ✅ Fully verified end-to-end |
| Pinellas, FL | ✅ Verified (condo units excluded for now) |
| Highlands, FL | ✅ Verified |
| Broward, FL | ⚠️ Records pull works; county doesn't index legals on lis pendens, so no ownership join |
| Other open-Acclaim counties | Claude can attempt them and will verify the parcel join before trusting it |
| Tyler / login-gated counties | ❌ Not automated — the plugin will tell you upfront |

Scoring weights live in the skill's `config/scoring.json` — ask Claude to
show or adjust them; every lead's score is the visible sum of its signals.

## Privacy — read this

- County records name real people in financial distress. This plugin
  **produces a research list and stops.** It will not contact, skip-trace, or
  solicit property owners, and you shouldn't either without understanding the
  laws that apply to you (e.g. do-not-call, CAN-SPAM, state solicitation rules).
- Cowork processes your task — including files it touches — on Anthropic's
  servers. Don't run this plugin if that's not acceptable for your use.
- Keep exported record files private. Don't commit them to repos or show them
  on stream/screen recordings.
- The plugin never creates accounts, never logs in, and never enters payment
  information on county sites, and it stops at any CAPTCHA rather than
  bypassing it.

## For developers

Repo layout: `.claude-plugin/marketplace.json` (marketplace manifest) →
`plugins/crei/` (the plugin) → `skills/` (each skill is a folder with
`SKILL.md` + bundled Python in `scripts/` + JSON config in `config/`).
Pipeline code is stdlib-only Python 3 — no pip installs, by design.

```
python -m pytest tests/          # 54 tests; fixtures are real county records
```

Design docs: [docs/data-sources.md](docs/data-sources.md),
[docs/vendor-router.md](docs/vendor-router.md),
[CONTEXT.md](CONTEXT.md) (glossary). Verification evidence and per-county
findings are recorded in those docs with dates.
