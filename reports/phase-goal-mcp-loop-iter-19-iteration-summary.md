# Iteration Summary — goal-mcp-loop-iter-19

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-07
**Iteration:** 19

## In plain words

**What you can do now:** Browse a leaderboard of hundreds of companies with up to 30 years of price history each, sort and filter that list by sector — including an honest "Unassigned" label for companies with no sector on file — and switch a stock's chart between a recent view and its full history. Every score, evidence-ledger entry, and past trading idea carries an honest status (right now everything reads "not yet proven" while the system re-earns its results on the deeper history), you can see evidence tied to the current market regime, and you can browse the company list as it looked on any past date, including newer companies as they joined. If something goes wrong on a page, you now get a calm "try again" message instead of a blank screen.

**What changed this time:** The crash that used to wipe out the entire stock list when sorting by "Sector" is fixed — sorting and filtering by sector now works for every company, including the roughly 4-in-5 with no sector on file (they now show a plain "Unassigned" label instead of a blank cell or a crash). The Data page also no longer risks freezing or crashing the server right after a restart, and any future unexpected error now shows a calm "Something went wrong" message with a retry button instead of blanking the whole app.

**What's next:** Next we'll clean up the Data page so it matches the larger company list by default and make its status legend easier to read, now that the crash is fixed and the platform is stable again.

## Headline

Stocks leaderboard no longer crashes when sorting by Sector

## Direction

**Signal:** improving
**Why:** This iteration recovered J-01 (the `/stocks` Sector-sort crash) from regressed to passing and completed J-12's browser verification (partial to passing), cleanly closing out iteration 18's REGRESSION with a surgical, byte-identity-preserving fix. No new regressions or anti-goal violations occurred, and the five journeys held at "partial" (J-02, J-06–J-09) are correctly unchanged by the sanctioned data-basis reset rather than a fresh setback. With the crash fixed and the backend stable, the evaluator recommends resuming forward feature work on J-13 next.

**Trend (last 5 iters):**
- Newly passing this iter: J-01, J-12
- Newly passing in last 5 iters total: J-01, J-09, J-10, J-11, J-12
- Regressions in last 5 iters: J-01 (iter-18)
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 2 of last 5 (iter-16, iter-17)

**Latest evaluator reasoning:** iter-19 cleanly closes the iter-18 REGRESSION: the `/stocks` Sector-sort crash on the ~78%-null-sector 30-year pool is fixed at its source (null-safe comparator + shared `sectorLabel` helper + `string|null` contract type) and contained (new `error.tsx`/`global-error.tsx`), and the coupled `/api/data` prefill OOM is fixed by a streamed column-projected `Bar` load — both browser-verified end-to-end. J-01 recovers regressed->passing and J-12 goes partial->passing; J-03/J-04/J-05/J-10/J-11 re-verified on fresh pixels; both ledgers stay all-FAIL and the certification engine is byte-unchanged. Not GOAL_ACHIEVED — J-02/J-06/J-07/J-08/J-09 remain sanctioned-partial and J-13/J-14/J-15/J-16 are unbuilt/unknown — so the loop resumes normal forward progress.

## What was done

- Fixed the `/stocks` Sector-sort crash: a null-safe `compareSectors`/`sectorLabel` helper replaced the direct `.localeCompare` call; unmapped companies (~78% of the pool) now show "Unassigned" instead of crashing or leaving a blank cell.
- Fixed the `/api/data` bar-prefill OOM: rewrote `prefill()` to a streamed, column-projected `Bar` load plus a nested double-scan guard, cutting peak memory roughly sixfold and completing cold loads in 10-18s instead of hanging.
- Added crash containment: new `error.tsx` + `global-error.tsx` render a contained "Something went wrong" card with nav preserved instead of a blank app on any future uncaught error.
- Widened `StockRow.sector` to `string | null` and re-validated every consumer (`/stocks`, `/stocks/{ticker}`, `/scanner-runs/{runId}`) via `tsc --noEmit` (0 errors).
- Recorded the before/after memory and timing measurement in `reports/perf-budgets.md` (single cold request 10.5s/~1.09GB; 6-concurrent 18.5s/~1.10GB, both well under budget).
- Verified 2 target journey(s) (J-01, J-12) pass browser QA (23/24 overall, one documented P3 skip), and re-confirmed J-03/J-04/J-05/J-10/J-11 on fresh pixels with no regressions.

## What's left

- Journey J-02 (drill into the proof behind a score) stays partial — no "Proven" claim exists to drill into; both ledgers remain all-FAIL from the sanctioned 30-year data-basis reset, not a regression.
- Journeys J-06/J-07/J-08/J-09 (the previously-certified trading edges) stay partial — none of the retired edges survived re-certification on the deeper history; re-earning them is separate, later evidence work.
- Journey J-13 (Data Manager coherence with the 548-company default + a clearer availability legend) is unknown — the evaluator's primary next target.
- Journey J-14 (deep index/macro overlays with vendor labels) is unknown — the underlying data landed in iteration 17; the rendering/labeling steps are still open.
- Journeys J-15/J-16 ("fast platform" speed + honest job progress) are unknown — this iteration's OOM fix is a down payment only; the measurement harness and remaining optimizations are still open.
- Two backend test files (`test_scanner.py`, `test_bars.py`) were not run to completion this session (slow real-seed-load fixtures); judged low-risk but recommended for independent re-confirmation.
- Non-blocking carry-forwards from the audit: the Full-history chart x-axis doesn't visually extend to a deep-history name's true first bar (F1); `perf-budgets.md` samples resident memory rather than the virtual-memory figure the cap actually enforces (B2); `return-attribution.tsx` still shows a blank cell instead of "Unassigned" for unmapped sectors (F3).
- `status.json`'s `note`/`browser_checks_run`/`next_action` fields are stale relative to the pipeline's actual completed state (documentation hygiene only, does not affect the verdict).

## Next step

iter-20 (**full**) — resume forward feature work now the regression is closed and the backend is stable. Primary target per goal.md sequencing: **J-13** (Data Manager coherence with the 548 default — point Fetch at the 548 pool, remove the "Expand universe" job option + dead code, split the availability legend so cell-fill=price-completeness vs indicator=scored-snapshot stop colliding). Equally ready alternatives: **J-14** (deep `_SPX/_NDX/_DJI` + macro overlays with per-series vendor labels, registering the vendor-label Data Contract value) or the **fast-platform mechanical backend pass** (items B+C+D+G+H toward J-15/J-16). Full depth because each ships a new user-facing surface and/or a byte-identity-gated data-path change needing the audit + ux-regression + closure guards (which just proved their worth catching iter-18). Non-blocking carry-forwards (do NOT reopen iter-19): F1 Full-history chart x-domain widening; B1 genuine cold-restart `/api/data` re-repro; B2 sample VmSize (not RSS) in perf-budgets.md; T1 re-run `tests/test_scanner.py`+`tests/test_bars.py` when a seed-load budget allows; F3 `return-attribution.tsx` null-sector "Unassigned" consistency.

## Quick verify

From `reports/phase-goal-mcp-loop-iter-19-what-to-click.md`:

1. Open `http://localhost:3255/stocks` in your browser
2. Click the word "Sector" in the column header row of the table
3. Click "Sector" again
4. Above the table, click the dropdown labeled "Sector" (it currently reads "All sectors") and select "Unassigned"
5. Look underneath any score badge (Leadership, Entry Quality, or Risk) in the narrowed list

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-19.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-19-dev.md |
| Review | PASS | reports/reviews/goal-mcp-loop-iter-19-review.md |
| Browser QA | PASS | reports/phase-goal-mcp-loop-iter-19-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-19-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-19-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-19-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-19-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-19-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-mcp-loop-iter-19-ux-regression.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-19-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-mcp-loop-iter-19-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-mcp-loop-iter-19-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-mcp-loop/iter-19/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
