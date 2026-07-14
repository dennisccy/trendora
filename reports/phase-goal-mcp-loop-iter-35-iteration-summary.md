# Iteration Summary — goal-mcp-loop-iter-35

**Verdict:** PASS
**Iteration type:** goal-full
**Date:** 2026-07-14
**Iteration:** 35

## In plain words

**What you can do now:** You can browse a leaderboard of hundreds of stocks where every score is honestly labeled as either backed by tested evidence or "not yet proven," open the full evidence behind any score, and look through a complete, auditable record of every trading idea the system has ever tested or rejected — including a working link back to each rejected idea's original registration and a live view of how much of the platform's testing budget has been used. You can view up to thirty years of price history and market-index context for any stock, and the page that manages your data connections stays fast even on its heaviest job. The system refuses to test any brand-new idea unless it was written down and registered first, and every page carries one shared status strip telling you at a glance whether today's board is safe to rely on.

**What changed this time:** That daily trust status strip now also watches for something new: whether freshly-fetched price data secretly disagrees with what's already been saved and validated. If a stock's price history was quietly revised by the data provider (which can happen after a dividend or stock split), the Data Manager page now names exactly which stock and which dates were affected, and the trust strip turns cautionary everywhere on the site — not just on the page showing the data — until a clean refresh clears it. If nothing has ever gone wrong, this new check stays quiet and nothing changes for you.

**What's next:** Next, the team will double-check this round's work with a quick verification pass, then continue through the remaining planned safety features — including a self-check for the testing system itself and new risk views for the watchlist and individual stocks.

## Headline

Shipped the live-vs-seed drift monitor (J-21): flags silent price re-adjustments, degrades the trust banner

## Direction

**Signal:** improving
**Why:** iter-35 shipped J-21 (backlog B-304, the live-vs-seed drift monitor) end-to-end — a new fetch-pipeline comparator, a 4th `compute_preflight` component, and a `/data` drift card — with all 14 browser-QA cases covering its acceptance states passing, UX-REGRESSION-PASS confirming full discoverability, and CLOSURE-PASS with zero blocking issues; the four required-still-passing journeys (J-20, J-13, J-01, J-05) were re-verified live with no regression. This iteration's own eval.md had not been written at summary time, so journey-history.json still shows J-21 as unknown pending the evaluator's formal pass — but every downstream gate that actually ran independently confirmed J-21's acceptance criteria, which is why this reads as forward progress rather than a stall.

**Trend (last 5 iters):**
- Newly passing this iter: J-21 — all pipeline gates (browser QA 14/14, UX-regression PASS, closure CLOSURE-PASS) confirm its acceptance criteria met, but journey-history.json had not yet been updated by the evaluator at summary time
- Newly passing in last 5 iters total: J-17 (iter-32), J-19 (iter-32), J-20 (iter-33), plus J-21 this iter pending formal confirmation (see above)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none new (the iter-24 and iter-26 critical anti-goal #8 findings remain resolved=true)
- Iters with no journey state change: 1 of last 5 (iter-34, a dedicated verification-only pass); iter-35's journey-history update is pending the evaluator run

**Latest evaluator reasoning:** iter-35's own eval.md had not been written at summary time. The most recent available evaluator-log entry (iter-34) read: iter-34 is the lean verification-only closeout the iter-33 CLOSURE-FAIL asked for, and it landed cleanly. Depth lean was MANDATORY (the deterministic-replay lane lives only in goal-iter-lean.sh; a full iter routes through run-phase.sh which has 0 replay-lane refs and would re-skip it — the exact iter-33 structural gap).

## What was done

- Shipped J-21 (backlog B-304): a live-vs-seed drift monitor that byte/fixed-precision-compares the last 20 days of a Fetch job's overlap against the committed reference data and flags any mismatch as an "adjustment seam."
- Added a new "Live-vs-seed drift" card to the Data Manager page, naming the affected symbol(s) and date(s) in four honest states (no fetch yet, clean, drift detected, report unreadable).
- Wired drift into the site-wide preflight trust banner as a 4th `compute_preflight` component: a detected drift degrades the banner on every page and it recovers automatically once a clean fetch supersedes it; confirmed byte-identical GO behavior when no fetch has ever run (the J-20 non-regression check).
- Built the new backend `app/engine/drift.py` module and fetch-pipeline wiring (`data_manager._run_job`), gated to stay inert on a resumable pause or a skip-fetch resume.
- Backend suite green end-to-end (252/252: 172 fast + 80 heavy, including `test_readiness` and `test_data_manager_jobs_pipeline`), frontend TypeScript clean; review PASS_WITH_NOTES, audit PASS_WITH_GAPS (3 non-blocking notes), UX-regression PASS, closure CLOSURE-PASS.
- Recovered cleanly from a mid-session tooling outage that blocked the developer's own test run — the reviewer, QA, and auditor each independently re-ran the full backend/frontend suite with matching results before the gap ever reached browser QA.
- Verified 1 target journey (J-21) passes browser QA (14/14 UT cases) and re-verified the 4 required-still-passing journeys (J-20, J-13, J-01, J-05) live with no regression.

## What's left

- Journey J-22 (unbuilt) — a self-check/calibration audit for the certifier itself (placebo + tripwire).
- Journey J-23 (unbuilt) — a watchlist concentration view (correlations, clusters, effective bets).
- Journey J-24 (unbuilt) — a per-stock "how much can this hurt" risk-budget card.
- Journey J-25 (unbuilt) — a drawdown/dry-spell expectations panel.
- The required-still-passing deterministic-replay report for this iteration was not produced (a structural gap of any FULL iteration; the phase spec pre-authorizes a lean iter-36 to close it).
- Two non-blocking audit gaps carried forward: the fetch-side overlap accumulator trims by fetched-bar count rather than common-date count (deployment-unreachable today), and no regression test yet asserts the drift artifact never contains a session API key (structurally safe today, hardening test absent).
- The two other B-304 sub-checks (a distribution-envelope comparison and a B-113-dependent anomaly seam scan) remain intentionally unbuilt, deferred to a follow-on.
- J-21's formal evaluator confirmation (the journey-history.json status flip from "unknown" to "passing") was still pending at summary time, even though every pipeline gate that ran this iteration passed cleanly.

## Next step

Run the full pipeline on the next phase. This iteration's own evaluator report (eval.md) had not yet been generated at summary time, so no formal Next-Step Recommendation exists to carry forward verbatim; closure returned CLOSURE-PASS with zero blocking issues, so the standard path is to proceed. The phase spec's own carried-forward NOTES flag that a FULL iteration structurally skips the required-still-passing deterministic-replay lane (it lives only in the lean pipeline), so — following the iteration 33→34 precedent — the anticipated next step is a lean verification pass before resuming forward feature work on the remaining unbuilt journeys (J-22–J-25).

## Assumptions made

none recorded

## Quick verify

From `reports/phase-goal-mcp-loop-iter-35-what-to-click.md`:

1. Open `http://localhost:3255/data` in your browser
2. Scroll down slightly until you see a card titled "Live-vs-seed drift" (it has a small two-arrow compare icon next to the title). It sits directly below the "Storage footprint" card
3. Read the card's main status line
4. Press F5 (or Cmd+R) to refresh the page, then look at the same card again
5. Click "Dashboard" at the top of the left sidebar (this takes you away from `/data`)

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-35.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-35-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-mcp-loop-iter-35-review.md |
| Browser QA | PASS | reports/phase-goal-mcp-loop-iter-35-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-35-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-35-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-35-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-35-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-35-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-mcp-loop-iter-35-ux-regression.md |
| QA | PASS_WITH_NOTES | reports/qa/goal-mcp-loop-iter-35-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-mcp-loop-iter-35-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-mcp-loop-iter-35-closure-verdict.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
