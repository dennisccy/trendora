# Iteration Summary — goal-mcp-loop-iter-38

**Verdict:** FAIL
**Iteration type:** goal-full
**Date:** 2026-07-15
**Iteration:** 38

## In plain words

**What you can do now:** Browse a leaderboard of hundreds of stocks with an honest "proven" / "not yet proven" status on every score, open a full audit trail behind any tested trading idea (including combined-factor and relative-strength ideas), and view up to thirty years of price history plus index and macro context, each clearly sourced. Browse every idea the system has planned, tested, or rejected, see how much of the statistical testing budget has been used, and check one shared trust banner on every page that also watches for live data quietly drifting from the validated history and for whether the testing system's own checker can be trusted. On the Watchlist page, see how your saved stocks tend to move together, grouped into clusters, with one headline number for how many genuinely independent bets your list actually represents, plus breakdowns by sector, theme, and current signal.

**What changed this time:** The Watchlist page now shows a new "Concentration X-ray" section: a grid showing how closely your saved stocks move together, clusters of names that behave alike, crowding bars by sector/theme/signal, and a headline number for how many genuinely independent bets your list represents. A stock with too little price history shows an honest "not enough data" mark instead of a guess. This was built and thoroughly tested, but the usual last-step double-check that nothing else on the site still works wasn't finished this round, so the round is on hold until that check runs.

**What's next:** Finish the double-check that the rest of the app still works, then add a new per-stock risk card showing how much a pick could realistically hurt.

## Headline

Watchlist concentration X-ray ships; closure blocked pending required-journey replay

## Direction

**Signal:** holding
**Why:** J-23 (watchlist concentration X-ray) shipped with strong evidence — 24/24 backend tests, a live production-data pass matching the closed-form ENB formula to 10+ digits, and 13/15 browser-QA tests passing live — but the iteration ended CLOSURE-FAIL because the required-still-passing replay for J-01/J-02/J-03/J-05/J-10/J-13/J-20 was never executed, the same systemic replay-lane gap that hit iter-33 and iter-36. No regression occurred and journey-history.json shows no status change yet for iter-38, so the project is holding rather than advancing or slipping.

**Trend (last 5 iters):**
- Newly passing this iter: none (iter-38 is blocked at CLOSURE-FAIL, before the evaluator has run)
- Newly passing in last 5 iters total: J-20 (iter-33), J-21 (iter-35), J-22 (iter-36)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none new (the two prior critical violations from iter-24/iter-26 remain resolved)
- Iters with no journey state change: 2 of last 5 (iter-34, iter-37 — both lean verify-only closeouts)

**Latest evaluator reasoning:** "iter-37 is the lean verify-only closeout the iter-36 CONTINUE asked for, and it landed cleanly, closing the iter-36 CLOSURE-FAIL replay gap with ZERO product change. Depth lean was MANDATORY (the deterministic-replay lane lives only in goal-iter-lean.sh; a full iter routes through run-phase.sh which has 0 replay-lane refs and would re-skip it — the exact iter-33/iter-36 structural gap)."

## What was done

- Built the ONE canonical ENB/correlation helper (`app.engine.concentration`), reused by this iteration and reserved for the future evidence-correlation audit.
- Built the pure watchlist X-ray composer (`app.engine.watchlist_xray`) — bounded per-symbol reads, deterministic correlation-threshold clustering, sector/theme/setup concentration.
- Served the X-ray as an additive `xray` field on `GET /api/watchlist`; the existing `asof_date`/`entries[]` shape stayed byte-identical.
- Shipped the frontend "Concentration X-ray" section on `/watchlist` (correlation heatmap, cluster badges, effective-independent-bets headline + info tooltip, concentration bars) with zero browser-side recompute.
- Added typed config (`watchlist.xray.*`) with honest NA handling for short-history/missing-bar members and for empty/1-name watchlists.
- Verified J-23 passes browser QA — 13/15 UI tests PASS live (2 P2 tests sanctioned-skip for documented reasons); a separate live production-data pass confirmed the effective-independent-bets math matches the closed-form formula to 10+ digits.

## What's left

- Required-still-passing replay for J-01, J-02, J-03, J-05, J-10, J-13, and J-20 was never executed this iteration (only an HTTP-200 smoke check ran) — the same systemic gap that CLOSURE-FAILed iter-33 and iter-36; must run before J-23 can be promoted to passing.
- J-23 (watchlist concentration X-ray) is fully built and browser-QA-verified but not yet marked "passing" in the goal ledger pending that replay.
- J-24 (per-stock "how much can this hurt" risk-budget card) — unbuilt.
- J-25 (phase-conditional drawdown/dry-spell expectations panel) — unbuilt.
- `enb_member_count` is computed and served by the API but has no render site in the UI yet (self-disclosed, non-blocking).
- Minor config-validator gap: `WatchlistXrayCfg` rejects only `min_overlap_days > corr_window_days`, not the also-unreachable `==` case (one-character fix, not a shipped defect).
- The recurring framework gap — a FULL iteration has no built-in deterministic-replay lane — is still owed to the framework maintainer (add the lane to `run-phase.sh` / `run-goal.sh`'s full path).

## Next step

Per the closure verdict's remediation: bring the backend and frontend up, then run the deterministic replay (`demo_runner.py --mode verify`) against the existing golden scripts for J-01, J-02, J-03, J-05, J-10, J-13, and J-20, fold the results into `ui-test-results.md`, and correct QA's TC-17 row to cite that evidence instead of the smoke-200 check it currently rests on — then re-run phase-closure-auditor. The closure verdict's own diff analysis found no plausible regression path from this iteration's changes, so the replay is expected to pass cleanly, but per this project's standing rule it must be executed, not inferred. Per the Definition of Done's "OR" clause, a dedicated lean verify-pass iteration (the iter-34 / iter-37 precedent) can close this instead of an inline replay.

## Assumptions made

none recorded

## Quick verify

From `reports/phase-goal-mcp-loop-iter-38-what-to-click.md`:

1. Open http://localhost:3255/watchlist in your browser
2. Scroll down below the entries table
3. Read the headline just above the correlation grid, then hover the cell where the "ABBV" row crosses the "MSFT" column
4. Look at the "Clusters" badges, then the three bar sections below them (Sector concentration / Theme concentration / Shared setup)
5. Click the small "i" info icon immediately to the right of the "effective independent bets" headline

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-38.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-38-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-mcp-loop-iter-38-review.md |
| Browser QA | PASS | reports/phase-goal-mcp-loop-iter-38-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-38-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-38-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-38-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-38-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-38-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-mcp-loop-iter-38-ux-regression.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-38-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-mcp-loop-iter-38-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-mcp-loop-iter-38-closure-verdict.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
