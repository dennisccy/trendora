# Iteration Summary — goal-mcp-loop-iter-21

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-08
**Iteration:** 21

## In plain words

**What you can do now:** Browse a leaderboard of hundreds of companies with up to 30 years of price history each, sort that list by sector, and switch any stock's chart between a recent view and its full history. Every score, evidence entry, and past trading idea carries an honest "proven" or "not yet proven" status tied to the current market regime, backed by a full evidence ledger you can audit yourself, and companies join and leave the list honestly as their real trading histories start and end. On the Data Manager page, refreshing prices now covers the entire company list in one click, with a redesigned daily calendar that clearly separates "we have price data for this day" from "we've already scored it." If something goes wrong on a page, you get a calm retry message instead of a blank screen.

**What changed this time:** Behind-the-scenes work — nothing new appeared on screen this round. The team spent this round proving, on the live running site rather than just by reading the code, that last round's Data Manager update (the whole-list price refresh and the clearer two-color coverage calendar) truly works — and it does, so that update is now fully confirmed and complete. Along the way they also re-confirmed four other already-working areas (sorting the company list, the evidence page, a stock's chart, and the honest "not yet proven" labels) are still working correctly.

**What's next:** Next, the team will add deep historical stock-index and economic-indicator charts — going back up to 30 years — each clearly labeled by where its data comes from.

## Headline

J-13 flips partial → passing after a clean live browser-QA re-verification

## Direction

**Signal:** improving
**Why:** J-13 (Data Manager 548-pool fetch + unambiguous availability legend) flipped partial → passing this iteration after the canonical browser-qa-agent lane ran live end-to-end and every DoD-named case passed, closing the iter-20 verification gap and clearing CLOSURE-PASS. Four of five required-still-passing replays (J-01, J-03, J-05, J-10) came back clean live; J-12 held its substantive claim despite one mistargeted test case on an unrelated, pre-existing `/methodology` gate. No regression and no anti-goal violation occurred, so direction is improving; iter-22 should target J-14 next.

**Trend (last 5 iters):**
- Newly passing this iter: J-13
- Newly passing in last 5 iters total: J-01, J-10, J-11, J-12, J-13
- Regressions in last 5 iters: J-01 (iter-18)
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 1 of last 5

**Latest evaluator reasoning:** "The verification-only re-run succeeded exactly as specced: the canonical `browser-qa-agent` lane ran **live** this time (it correctly overrode a stale dispatch SKIP flag by independently re-verifying both services at HTTP 200), producing the non-empty, md5-distinct evidence dir that iter-20 lacked, and **J-13 flips `partial → passing`** — every DoD-named J-13 case passed live with DOM/computed-style precision, and CLOSURE-PASS cleared. Four of five required-still-passing replays (J-01/J-03/J-05/J-10) came back live-clean, closing iter-20's replay gap. The two literal UT failures (UT-16 P2, UT-21 P1) are independently verified **non-regressions on non-J-13 cases** — a compliant coarser honest-degrade gate, and a mistargeted test reference to `/methodology` whose Universe Selection section is correctly suppressed by a pre-existing anti-fabrication gate. Not GOAL_ACHIEVED because J-02/J-06/J-07/J-08/J-09 remain goal.md-sanctioned `partial` and J-14/J-15/J-16 are `unknown`/unbuilt."

## What was done

- Re-confirmed zero source-code drift on all five J-13 implementation files (`git diff HEAD` empty) and re-ran the four scoped backend test suites — 102/102 passed — plus a clean frontend type-check.
- Cleared the iter-20 stale-bundle trap and brought both prod-mode services up fresh before dispatching QA.
- The browser-qa-agent independently re-verified live reachability (overriding a stale "services unreachable" dispatch flag) and executed, rather than code-inspected, the full 22-case UI test plan live for ~59 minutes.
- Captured 12 md5-distinct evidence screenshots into a non-empty evidence directory, closing the empty-evidence gap that drove iter-20's CLOSURE-FAIL.
- Live-verified all 8 DoD-named J-13 cases (job-kind picker, two-group legend, blue density ramp, violet snapshot ring, distinguishing hover tooltip) with computed-style/DOM precision.
- Reconciled the QA report's stale "services unreachable" section against the real live run and re-ran phase-closure to CLOSURE-PASS.
- Verified 1 target journey (J-13) passes browser QA live, plus 4 of 5 required-still-passing regression replays (J-01, J-03, J-05, J-10).

## What's left

- J-02, J-06, J-07, J-08, and J-09 (five previously-certified trading-edge journeys) remain goal.md-sanctioned "partial" — none has re-earned certification on the new 30-year price history yet.
- J-14 (deep index/macro overlays with vendor labels) is unbuilt, but its data basis is already staged, making it the most ready next target.
- J-15 and J-16 (fast-platform performance budgets) remain unbuilt beyond an initial down-payment fix.
- The backend's "Expand universe" job kind and market-cap refresh logic still exist with no UI path — reachable only via the offline `scripts/screen_universe.py` script.
- Non-blocking: the J-12 regression-replay test case targets the wrong page (`/methodology` instead of `/data`/`/stocks`) and needs retargeting.
- Non-blocking: the honest-degrade test case expects narrower error text than the actual (compliant) page-level "Backend unavailable" gate produces.
- Non-blocking: `scripts/start-frontend.sh`'s freshness stamp checks only the backend URL, not frontend-source freshness.

## Next step

iter-22 (FULL). J-13 was the last non-evidence journey to close, so the extended goal is not yet met; in priority order: (1) J-14 is the most ready forward-feature target since its data basis is already staged — render the deep benchmark and macro overlays with per-series vendor labels, registering the new vendor-label Data Contract value; (2) J-15/J-16 — commit the performance-measurement harness and budgets, land the mechanical backend pass, and re-measure a ≥30% improvement, byte-identical; (3) the riskiest option, re-certify J-02/J-06/J-07/J-08/J-09 on the 30-year basis by re-running the pre-registered staging exploration and promoting only a winner that clears the canonical Bonferroni bar with margin, honoring the honest-stop guard. Non-blocking follow-ups to file without reopening J-13: retarget the J-12 replay test case at `/data`/`/stocks`, loosen the honest-degrade test's expected text, and carry forward the `start-frontend.sh` freshness-stamp gap.

## Quick verify

From `reports/phase-goal-mcp-loop-iter-21-what-to-click.md`:

1. Open `http://localhost:3255/data` in your browser
2. Click the "Job kind" dropdown in that panel
3. Select "Fetch EOD prices," confirm the "Import source" dropdown that appears shows an option ending in "· available" (pick one if not), then click the "Start" button
4. Scroll down to the "Per-date availability" card
5. Look at the rightmost swatch in the "PRICE DATA — CELL FILL" row (labeled "full")

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-21.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-21-dev.md |
| Review | PASS | reports/reviews/goal-mcp-loop-iter-21-review.md |
| Browser QA | FAIL | reports/phase-goal-mcp-loop-iter-21-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-21-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-21-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-21-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-21-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-21-ui-test-plan.md |
| UX regression | UX-REGRESSION-WARN | reports/phase-goal-mcp-loop-iter-21-ux-regression.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-21-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-mcp-loop-iter-21-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-mcp-loop-iter-21-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-mcp-loop/iter-21/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
