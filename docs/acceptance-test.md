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

## Test 3 — full Brevard pipeline (the product)

Prompt: *"Find motivated sellers in Brevard County, FL from the last two weeks
and score the leads."*

Watch for each stage:

- [ ] Portal: disclaimer accepted, doc types enumerated (LP + LP1), dates
      typed (not scripted), search run within the released-through date
- [ ] Export: CSV downloaded and handed into the sandbox (note HOW the file
      crosses the browser→sandbox boundary — this is the step we could not
      rehearse outside Cowork; if Claude gets stuck here, the fix belongs in
      SKILL.md Stage 1 step 7)
- [ ] Parse: reports N parsed / M review with reasons
- [ ] Enrich: BCPAO API navigated serially, visible ~1–2s pacing
- [ ] Score: ranked leads + summary presented; a top lead's score is
      explained signal-by-signal when asked "why did #1 score that?"
- [ ] Ask "why didn't record X get enriched?" — answer should reference the
      review file or ambiguous-match rule, not hand-wave

## Test 4 — honest failure modes

- [ ] Ask for a Tyler/gated county (e.g. a countygovernmentrecords.com one):
      plugin says upfront it can't automate it, does NOT attempt registration
- [ ] Ask for Broward: plugin explains pull-only (no legals on LP docs)

## Record the results

Note anything that surprised Claude or you in a `docs/field-notes.md` —
those notes are the input for the next SKILL.md revision (and YouTube
material).
