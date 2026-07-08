# Iteration Summary — goal-mcp-loop-iter-20

**Verdict:** FAIL
**Iteration type:** goal-full
**Date:** 2026-07-08
**Iteration:** 20

## In plain words

**What you can do now:** Browse a leaderboard of hundreds of companies with up to 30 years of price history each, sort and filter that list by sector — including an honest "Unassigned" label for companies with no sector on file — and switch a stock's chart between a recent view and its full history. Every score, evidence-ledger entry, and past trading idea carries an honest status (right now everything reads "not yet proven" while the system re-earns its results on the deeper history), you can see evidence tied to the current market regime, and you can browse the company list as it looked on any past date, including newer companies as they joined. If something goes wrong on a page, you get a calm "try again" message instead of a blank screen.

**What changed this time:** The team made the Data Manager's "Fetch" button refresh the whole ~548-company list instead of just a small reference set, removed a now-unneeded "Expand universe" option, and made the page's daily-coverage chart clearer by giving "how much price data exists" and "has it been scored yet" distinct, non-clashing colors. A manual spot-check found it working correctly, but the team's usual automatic verification pass didn't finish this round (the app was briefly unreachable), so this isn't being marked as confirmed and ready yet.

**What's next:** Next, the team will re-run the verification pass now that the app is back up, so these Data Manager improvements can be confirmed working before the project moves on.

## Headline

Data Manager Fetch widened to the 548-stock pool; browser QA never confirmed it live

## Direction

**Signal:** holding
**Why:** iter-20 shipped a correct, reviewed, and audited J-13 implementation (Fetch scope widened to the full 548-pool ∪ context union, the "Expand universe" option removed, and the availability legend re-encoded into two collision-free signals) with zero code defects found by review or audit. Phase-closure still returned CLOSURE-FAIL because the canonical browser-qa-agent lane recorded a blanket 22/22 SKIP (both services unreachable at precondition check) and three required-still-passing journeys (J-05, J-10, J-12) were never replayed live, so J-13 stays unverified/`unknown` in the journey tracker. No journey flipped passing or regressed versus iter-19, so the project is holding rather than moving — the very next dispatch (re-run browser-qa-agent against the already-fixed, currently-running build) should close the gap without new code.

**Trend (last 5 iters):**
- Newly passing this iter: none (canonical verification never completed — CLOSURE-FAIL blocked before evaluation)
- Newly passing in last 5 iters total: J-01, J-09, J-10, J-11, J-12
- Regressions in last 5 iters: J-01 (iter-18)
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 2 of last 5 (iter-16, iter-17)

**Latest evaluator reasoning:** iter-19 cleanly closes the iter-18 REGRESSION and its coupled OOM defect. I verified every status change against artifacts I personally opened, not the handoffs. NOT GOAL_ACHIEVED (J-02/06/07/08/09 partial; J-13/14/15/16 unknown). NOT REGRESSION (no passing->failing; J-01 recovered; no critical anti-goal).

## What was done

- Widened the generic Fetch job's symbol scope from the ~162-symbol context set to the full ~548-name committed pool ∪ context (588 symbols total) via `price_load_symbols`, while keeping `compute_availability`/`GET /api/data/availability` byte-identical (enforced by a new frozen-output regression test).
- Removed the "Expand universe" job option and all its now-dead supporting code from `/data` (picker option, ineligibility alert, the `ExpandScreenResult` panel) — Fetch/Backfill/Both/Gap-pull/Rebuild are untouched.
- Re-encoded the availability heatmap legend into two labeled groups ("Price data — cell fill" vs. "Scored snapshot — indicator"), replaced the amber-topped rainbow density ramp with a monotonic single-hue blue ramp, and moved the snapshot ring from green to a new violet token, with tooltip/caption copy naming the Fetch/Backfill workflow.
- Fixed all three findings from an initial review FAIL in a retry (a shadowed test-class name, a fabricated tool-attribution claim, a loosened test assertion); 102/102 scoped backend tests and `tsc --noEmit` are green after the fix, and review now reads PASS.
- Verified 0 target journey(s) pass canonical browser QA — all 22 checks (14 of them P1) came back SKIPPED because both frontend (:3255) and backend (:8255) were unreachable at the precondition check.
- Phase-closure returned CLOSURE-FAIL on the resulting verification gap: no live evidence for J-13 or for 3 of the 5 required-still-passing journeys (J-05/J-10/J-12), and the QA report's browser-verification claims were found to contradict the same-day, unreachable-service reality.

## What's left

- Browser QA never executed for J-13 — the canonical lane recorded a blanket SKIP (0/22, including all 14 P1 cases) because both services were unreachable at precondition check; DoD line 1 is unmet.
- Required-still-passing journeys J-05, J-10, and J-12 have no live evidence from this iteration — only J-01/J-03 were spot-checked live, and only by the ux-regression reviewer, not the canonical QA lane.
- The QA report grades 12 browser-typed test cases (TC-03–TC-12, TC-16) as PASS from code inspection while the same-day canonical `ui-test-results.md` shows both services unreachable — the two artifacts contradict each other and need reconciling.
- Journey J-13 (548-pool Fetch coherence + unambiguous availability legend) stays `unknown` in the journey tracker until the canonical browser-qa-agent lane actually runs and passes.
- Non-blocking tooling gap: `scripts/start-frontend.sh`'s staleness stamp checks only the backend URL, not frontend-source freshness — it silently served a stale pre-iter-20 bundle once already this iteration (caught only because the ux-regression reviewer happened to inspect the live DOM).
- Sanctioned-partial evidence journeys J-02, J-06, J-07, J-08, and J-09 still await a new-basis re-certification on the 30-year history (deliberately deferred, separate future iteration).
- Journeys J-14 (deep index/macro overlays + vendor labels) and J-15/J-16 (fast-platform performance budgets) remain unbuilt/unknown.

## Next step

Re-run the verification stages, not new feature work: `rm -rf apps/frontend/.next` to avoid the stale-bundle trap, bring both services up in prod mode (`start-backend.sh` then `start-frontend.sh`, never `dev.sh`) and confirm reachability, then re-dispatch browser-qa-agent against the full 22-case `reports/phase-goal-mcp-loop-iter-20-ui-test-plan.md` — executing, not code-inspecting, all cases, including the J-05/J-10/J-12 regression replays (UT-19/UT-20/UT-21 already cover them). Capture and md5sum the required screenshot evidence, set `status.json`'s `browser_checks_run` to `true`, reconcile the QA report's browser-verification claims against the real run, and re-submit to phase-closure-auditor. The underlying J-13 code is already independently verified correct (review PASS, audit PASS_WITH_GAPS with zero critical/important defects, and a live DOM spot-check by the ux-regression reviewer) — this is a verification re-run, not a rebuild.

## Quick verify

From `reports/phase-goal-mcp-loop-iter-20-what-to-click.md`:

1. Open `http://localhost:3255/data` in your browser
2. Click the "Job kind" dropdown in that panel
3. Select "Fetch EOD prices," confirm the "Import source" dropdown that appears shows an option ending in "· available" (pick one if not), then click the "Start" button
4. Scroll down to the "Per-date availability" card
5. Look at the rightmost swatch in the "PRICE DATA — CELL FILL" row (labeled "full")

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-20.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-20-dev.md |
| Review | PASS | reports/reviews/goal-mcp-loop-iter-20-review.md |
| Browser QA | SKIPPED | reports/phase-goal-mcp-loop-iter-20-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-20-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-20-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-20-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-20-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-20-ui-test-plan.md |
| UX regression | UX-REGRESSION-WARN | reports/phase-goal-mcp-loop-iter-20-ux-regression.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-20-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-mcp-loop-iter-20-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-mcp-loop-iter-20-closure-verdict.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
