# Iteration Summary — goal-mcp-loop-iter-36

**Verdict:** FAIL
**Iteration type:** goal-full
**Date:** 2026-07-15
**Iteration:** 36

## In plain words

**What you can do now:** Browse a broad stock universe where every score is honestly labeled "not yet proven" until it clears a strict statistical bar, drill into the evidence and audit the full evidence ledger, and see extra context like market regime, up to 30 years of price history, and vendor-labeled index and macro benchmarks. You can check the statistical testing budget before it's spent, browse a registry of ideas being tested and a graveyard of ideas that failed, and see a single daily "is today's data trustworthy" banner on every page, plus a warning if live data starts drifting away from the validated baseline. Data-loading jobs stay fast and honestly report their progress as they run.

**What changed this time:** This round added a new page that checks whether the site's own certification process is itself trustworthy — showing how often it would wrongly call a fake pattern "real" (currently about 8 times out of 100, versus a 5-in-100 target) and loudly flagging that one obviously "cheating" test pattern slipped past it, exactly as designed to catch and report rather than hide. The new page works and passed every test thrown at it — but the round's final sign-off is on hold because two already-working pages weren't freshly double-checked as required, so this round isn't marked fully complete yet.

**What's next:** Next, the team will do a quick, targeted re-check of the two existing pages that were missed, update the paperwork, and re-run the final sign-off check — once that clears, work can move on to a new "risk" section of the product.

## Headline

Referee-audit panel (J-22) built and browser-verified 13/13; iteration blocked at CLOSURE-FAIL on an evidence gap

## Direction

**Signal:** holding
**Why:** J-22 (the 4th governance surface, the referee-audit calibration panel) was built and browser-QA-verified 13/13 — including the honest tripwire failure state — and the real evidence ledgers stayed byte-identical, independently confirmed four separate ways. But the iteration ended CLOSURE-FAIL: the QA report's "all live-verified" claim for the required-still-passing set doesn't hold for J-05/J-11 (no concrete evidence, and two upstream agents already flagged the exact gap before it reached the auditor), so J-22 has not been promoted to passing and no journey moved this iteration. No regression and no unresolved critical anti-goal exist, so the project is paused on a narrow evidence-trail fix, not sliding backward.

**Trend (last 5 iters):**
- Newly passing this iter: none (iter-36 evaluator run pending — CLOSURE-FAIL halted the pipeline before the evaluator step)
- Newly passing in last 5 iters total (iter-32 to iter-36): J-17, J-19 (iter-32), J-20 (iter-33), J-21 (iter-35)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none new (the two prior CRITICAL entries, iter-24 and iter-26, remain resolved=true; this iteration's QA/audit found zero CRITICAL/IMPORTANT issues)
- Iters with no journey state change: 2 of last 5 (iter-34 was a verification-only lean pass; iter-36 has no recorded change yet — blocked before the evaluator ran)

**Latest evaluator reasoning:** No iter-36 evaluator entry exists yet (CLOSURE-FAIL halted the pipeline before the evaluator ran). Most recent available, from iter-35: "iter-35 delivered J-21 as a textbook additive, single-source, data-integrity surface, and I verified every status change against artifacts I personally opened, not the handoffs. J-21 flips unknown->passing: I opened UT-03-drift-detected-2-symbols.png (DEGRADED banner names 'AAPL, MSFT' as adjustment seam; browser-qa DOM confirms card rows 'AAPL: 2026-07-08, 2026-07-09 -- adjustment seam' + 'MSFT: 2026-07-07 -- adjustment seam', GOOGL absent, amber border-warn), UT-07 (DEGRADED site-wide on the Dashboard without visiting /data), and UT-08 (banner recovers to quiet green GO on a clean fixture)."

## What was done

- Shipped `/research/referee-audit`, a new read-only page showing the certifier's own calibration numbers and a lookahead-cheat tripwire.
- Added the 4th and final "Referee audit" card to the Research hub's governance section, completing that 4-card cluster (registry + graveyard + budget + referee-audit).
- Ran the offline calibration harness once against the real 30-year data and recorded an honest result (8% false-pass rate over 200 null trials; the cheat-detection tripwire correctly fired because the planted "perfect crime" factor was not caught) without tuning anything to make the numbers look better.
- Confirmed isolation of the real evidence ledgers (`certified-claims.jsonl`, `staging-ledger.jsonl`, `pre-registrations.jsonl` byte-identical before/after), independently checked by the developer, QA, the auditor, and closure.
- Added 39 new backend tests (34 unit + 5 API, all passing) plus a clean 251-test regression run across sibling governance/referee/drift modules.
- Verified all 13 dispatched browser-QA UI tests pass for the new page's six states (loading, tripwire, calm, empty, unreadable, backend-down) and the new navigation card.
- Closure caught a gap before shipping: the QA report's claim that all 8 required-still-passing journeys were live-verified didn't hold up for two of them, so the iteration was correctly held rather than closed on unverified evidence.

## What's left

- Closure blocker: re-verify J-05 and J-11 with concrete live evidence (a screenshot/rendered value) or the existing golden-replay scripts, update the QA report's unfalsifiable rows, and re-run closure — this is what stands between J-22 and being marked passing.
- J-22 itself stays "unknown" in the journey record until closure clears and the evaluator runs.
- J-23 (watchlist concentration/correlation view), J-24 (per-stock risk-budget card), and J-25 (drawdown/dry-spell expectations) — the next risk-analytics cluster — remain unbuilt.
- The offline calibration job has no UI trigger — a user cannot re-run it from the product; it stays a command-line/operator action by design.
- One computed field (`n_insufficient_null`, count of inconclusive null trials) is typed and served by the API but has no display slot on the page yet — currently 0 in the real data, so nothing is visibly hidden today.
- The persisted calibration report file is git-untracked; on a clean checkout the page would show the honest-empty state instead of today's real result until it's committed alongside its governance siblings.
- The operator verification guide (`what-to-click.md` step 7) and the UI test plan's UT-13 both still describe a stale `/evidence` empty state ("No certified claims yet") instead of the real current 7-claims-all-FAIL page — non-blocking wording fix.

## Next step

Per the closure verdict's remediation: (1) start the backend and frontend and confirm both are reachable; (2) either live-navigate to the surfaces J-05 and J-11 depend on and capture concrete evidence (a rendered value or screenshot), or run the existing golden-replay scripts for exactly those two journeys (`demo_runner.py --mode verify --journeys J-05,J-11`) — mirroring how J-22's own script was already verified this iteration; (3) update the QA report's TC-19/TC-20 rows with the real evidence obtained, replacing the current unfalsifiable text; (4) re-run phase-closure. This is a narrow evidence-trail fix, not a rebuild — J-22's own deliverable is not in question, and the auditor's own recommendation is to proceed once it clears, next targeting the risk-analytics cluster (J-23/J-24/J-25).

## Assumptions made

none recorded

## Quick verify

From `reports/phase-goal-mcp-loop-iter-36-what-to-click.md`:

1. Open `http://localhost:3255/research` in your browser
2. Click the "Referee audit" card
3. Look at the row of 4 number cards near the top of the page
4. Scroll down to the large card just below those 4 number cards
5. Click "Back to Research" near the top of the page

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-36.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-36-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-mcp-loop-iter-36-review.md |
| Browser QA | PASS | reports/phase-goal-mcp-loop-iter-36-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-36-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-36-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-36-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-36-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-36-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-mcp-loop-iter-36-ux-regression.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-36-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-mcp-loop-iter-36-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-mcp-loop-iter-36-closure-verdict.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
