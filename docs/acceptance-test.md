# Acceptance test — real Cowork run (Kevin drives this)

The build was verified with Playwright on a residential connection, which
proves the *sites and data*. This checklist proves the *runtime end users
actually have*: Claude Desktop + Cowork + Claude in Chrome. Run it before
tagging v1.0.0, and again after any platform update. It doubles as tutorial
footage.

## Setup (once)

- [ ] Claude Desktop app installed, signed in, open
- [ ] Claude in Chrome extension installed and enabled, Chrome open
- [ ] Plan tier has Cowork with browser use
- [ ] Repo pushed to public GitHub

## Test 1 — marketplace install (the 60-second promise)

- [ ] Customize → Plugins → Add → Add Marketplace → paste the repo URL
- [ ] The CREI plugin appears with name/description rendered correctly
- [ ] Install it; both skills (`county-records`, `zillow`) are available

## Test 2 — Zillow skill alone (fast smoke test)

Prompt: *"Check Zillow for foreclosure listings in Orlando from the last 7 days."*

- [ ] Claude drives Chrome to a Zillow search with filters in the URL
- [ ] Reads the header result count (not the tab title)
- [ ] Returns structured listing data, no CAPTCHA bypass attempts

## Test 3 — county records pull (the core capability under test)

This is the pass/fail heart of the acceptance run: does the skill trigger on
a natural request and drive the county portal to a real CSV in the user's
runtime? Scoring/enrichment are NOT part of this test.

Try each prompt in a fresh chat:

- *"Find motivated sellers in Brevard County, FL from the last two weeks."*
- *"Find me liens in Brevard County."*

Watch for:

- [ ] The `county-records` skill triggers on the phrasing (no need to name
      the skill)
- [ ] Portal: Brevard Acclaim reached, disclaimer accepted, doc types
      enumerated via the autocomplete (LP + LP1), dates typed (not scripted),
      search kept within the released-through banner date
- [ ] Results grid appears; Claude clicks **Export to CSV**
- [ ] The CSV actually reaches Claude's working context (note HOW the file
      crosses the browser→sandbox boundary — this is the one step we could
      not rehearse outside Cowork; if Claude gets stuck here, the fix belongs
      in SKILL.md Stage 1 step 7)
- [ ] Claude reports what it pulled (row count, date window) truthfully
- [ ] Pacing stays polite (~2–3s between actions, no hammering)

**Pass = a real, current Brevard lis pendens CSV in hand, obtained through
the skill.** Anything Claude does after that (parse/score) is a bonus at this
stage, not a requirement.

## Test 3b — full pipeline (optional, after Test 3 passes)

When you're ready to exercise the whole product: let the run continue through
parse → BCPAO enrichment (serial, ~1–2s pacing) → scoring, and check that a
top lead's score is explained signal-by-signal when you ask "why did #1 score
that?" and that unenriched records are explained via the review file /
ambiguous-match rule. Not a blocker for v1 tagging if Test 3 passes.

## Test 4 — honest failure modes

- [ ] Ask for a Tyler/gated county (e.g. a countygovernmentrecords.com one):
      plugin says upfront it can't automate it, does NOT attempt registration
- [ ] Ask for Broward: plugin explains pull-only (no legals on LP docs)

## Record the results

Note anything that surprised Claude or you in a `docs/field-notes.md` —
those notes are the input for the next SKILL.md revision (and YouTube
material).
