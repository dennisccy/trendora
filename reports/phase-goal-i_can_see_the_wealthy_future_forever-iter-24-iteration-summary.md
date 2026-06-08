# Iteration Summary — goal-i_can_see_the_wealthy_future_forever-iter-24

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-06-08
**Iteration:** 24

## In plain words

**What you can do now:** See the day's market at a glance; browse ranked stocks, sectors, and themes filtered by setup or pattern; open any stock for a plain-English scorecard with matching scores across pages; rewind the whole app to any past date with one shared date control; read forward-tested evidence on the Backtest page; explore Research labs (factor deciles, market-mood splits, multi-signal blends, volatility family, event study, all-history or as-of toggle); travel from any research finding to the filtered leaderboard and on to a stock's scorecard; keep a restart-proof watchlist; read every label in the glossary; import data from a selectable provider with a pasted key held for that run only; run large imports in visible chunks that pause gracefully and resume after a restart; grow the universe from the Data Manager via the Expand job; understand exactly what data is and isn't covered through a labelled coverage panel with a per-symbol table showing date range, bar count, and thin or missing flags for every ticker and universe member; and safely remove user-imported data with a confirm-preview that protects the committed seed and shows exactly which derived snapshots will be deleted before anything is touched.

**What changed this time:** The Data Manager now shows a plain-language coverage panel: every coverage figure (price history, universe size, symbols count, trading days, snapshot dates, backfill gaps) is labelled with a one-line definition, a "universe vs symbols" sentence explains the distinction, and a per-symbol table lists every ticker and every universe member with its date range, bar count, and whether it is thin or missing. The table is sortable and filterable. A new "Remove imported data" panel lets the operator preview and then confirm deletion of user-added bars — it shows exactly what will be removed, which committed-seed bars are protected, and which derived snapshots and forward returns will cascade out, before anything is touched. The committed seed can never be deleted.

**What's next:** Next the app will show a diagnostic of exactly which universe members are missing enough history for analysis, with a one-click action to pull only the missing data, and will unify the import-management panel so resumable, retryable, and removable import jobs are handled from one place.

## Headline

Per-symbol coverage table and seed-safe Remove-data confirm-preview added to the Data Manager (J-36 passing, J-39 partial)

## Direction

**Signal:** improving
**Why:** J-36 (per-symbol coverage table and plain-language definitions) moved from failing to passing this iteration, verified by a genuine fully-hydrated QA MODE-2 render. J-39 (seed-safe Remove-data) was built and source-verified but landed partial because the dedicated browser-qa agent was blocked by the frontend being down — a recurring environmental issue, not a code defect. Board is now 32 passing / 2 partial (J-35, J-39) / 5 failing. No regressions, coherence passes, and two concrete browser re-capture targets plus two unbuilt journeys give the next iteration clear work.

**Trend (last 5 iters):**
- Newly passing this iter: J-36
- Newly passing in last 5 iters total: J-33 (iter-22), J-34 (iter-22), J-36 (iter-24)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 0 new; the iter-21 key-leak violation was resolved in iter-22 and has held since
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** J-36 (per-symbol coverage table + plain-language definitions + universe-vs-symbols clarity) landed and is passing — backend logic is green (73 J-36/J-39 tests pass; consistency invariant 162 symbol rows == symbol_count, 122 in-universe rows == universe_count), and the QA MODE-2 screenshot TC-01-coverage-defs.png is a genuine fully-hydrated render of the definitions block + universe-vs-symbols prose + the per-symbol table with thin/missing badges. J-39 (seed-safe Remove-data) is partial: its destructive cascade boundary is verified sound IN SOURCE (whole-row deletes, no in-place snapshot overwrite, no recompute, seed protection + refusal) and integration-proven, but its defining browser flow (preview → protected-seed breakdown + cascade → confirm/refusal) was not captured — the dedicated browser-qa-agent SKIPPED all 26 tests (frontend down), and the only J-39 QA shot is blank. J-35 stays partial — its end-to-end expand capture was again explicitly deferred.

## What was done

- Added `_per_symbol_coverage` to `data_manager.py`, wired into `compute_coverage`, returning one row per stored symbol and per universe member with `in_universe`, `has_data`, first/last date, `bar_count`, `thin` (threshold from config, no magic number), and `missing` fields; empty dataset serves gracefully
- Added seed-vs-user-added classifier (`load_seed_windows`, `is_seed_bar`) reading `apps/backend/data/seed/meta.json`; added `preview_removal` (read-only, `POST /api/data/remove/preview`) and `remove_data` (destructive, `POST /api/data/remove`) with whole-row cascade delete, seed protection + refusal, and append-only `DataProviderRun` audit recording
- Added `RemoveScope` request model and both removal endpoints to `api/data.py`; `ValueError` → 400
- Updated `apps/frontend/app/data/page.tsx` with a richer Coverage panel (definitions, universe-vs-symbols prose), a sortable/filterable `PerSymbolCoverageTable`, and a `RemoveDataPanel` with a confirm-preview modal
- Added `PerSymbolCoverage`, `RemoveScope`, `RemovePreview`, and related types to `lib/api.ts`; added `previewDataRemoval` and `executeDataRemoval` fetch clients
- Added 73 new backend tests across `test_data_manager.py` and `test_api_data.py` covering per-symbol exact values, consistency invariant, thin threshold, empty dataset, cascade-solely, fully-covered-snapshot-untouched, seed-only-refused, audit-recorded, no-recompute, and all 4xx error cases; frontend typechecks clean
- Verified J-36 passing via QA MODE-2 hydrated render (TC-01-coverage-defs.png): definitions block + universe-vs-symbols prose + per-symbol table with thin/missing badges, consistency invariant 162==symbol_count / 122==universe_count confirmed

## What's left

- Journey J-39 (Remove imported data — user-added-only, seed-safe, cascade-consistent, confirm-preview) — partial; re-capture the defining browser confirm-preview flow on a clean hydrated build (preview path only on live host per MEMORY j39-live-host-has-user-added-nvda-bars)
- Journey J-35 (Expand the universe from the Data Manager) — partial; re-capture the injected-provider expand end-to-end flow (passers + omitted-with-reason + grown universe-count) on a clean hydrated build
- Journey J-37 (Diagnose insufficient-for-analysis data and pull exactly the missing history) — failing, unbuilt; iter-25 target
- Journey J-38 (Unified Unfinished-imports — Resume / Retry / Remove with state explanation) — failing, unbuilt; iter-25 target
- Journey J-22 (Transparent, rule-based, expanded universe ~500 names) — failing, data-walled, NON-HALTING/NON-VETOING per re-scoped goal
- Journey J-23 (Multi-timeframe bars — intraday seed + timeframe-aware pipeline) — failing, data-walled, NON-HALTING/NON-VETOING
- Journey J-24 (Timeframe selector on the stock chart) — failing, data-walled, NON-HALTING/NON-VETOING
- Reviewer NOTE (non-blocking): logically redundant sub-expression in `_cascade_targets` at `data_manager.py:327`; dual key name `removed_bar_count` / `removable_bar_count` at line 523

## Next step

**full** depth, iter-25. (1) **Re-capture the two partial browser flows on a clean hydrated build** (stop strays by port; `rm -rf apps/frontend/.next`; restart `next dev`; confirm `GET /_next/static/chunks/main-app.js` → 200 + health badge cleared BEFORE driving any UI; do NOT run a prod build against the live dev `.next`): **J-39** — open Remove data → enter a user-added scope → preview rendering removable bars + range + protected committed-seed breakdown + dependent cascade → seed-only scope refusal (use the **preview** path on the live host per MEMORY `j39-live-host-has-user-added-nvda-bars`; the destructive confirm is proven by the fixture, never run against a real symbol on the live host); **J-35** — injected-provider expand to completion → passers + omitted-with-reason → grown `universe-count`. (2) **Build the two remaining buildable Must-haves**: **J-37** (missing-data diagnostic + one-click pull-missing via the J-34 engine — diagnostic deterministic, pull partly data-dependent/non-halting) and **J-38** (unified Unfinished-imports — generalize the iter-22 Resumable panel to Resume/Retry/Remove with state explanation, on the J-34 ImportCheckpoint surface; provable offline). After J-37/J-38 land green offline and J-39/J-35 capture green, GOAL_ACHIEVED is reachable — with J-22/J-23/J-24/J-35 live-fetch outcomes recorded honestly NA/non-halting. Do NOT autonomously re-probe J-22/J-23/J-24; do NOT declare completion on a single import-journey landing (iter-20 re-scope trap).

## Quick verify

From `reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-24-what-to-click.md`:

No `what-to-click.md` file was produced for iter-24. Use the test plan for manual verification.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-i_can_see_the_wealthy_future_forever-iter-24.md |
| Dev handoff | — | docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-24-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-i_can_see_the_wealthy_future_forever-iter-24-review.md |
| Browser QA | SKIPPED | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-24-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-24-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-i_can_see_the_wealthy_future_forever-iter-24-user-visible-changes.md |
| QA test plan | — | reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-24-test-plan.md |
| Goal evaluation | CONTINUE | runs/goal-session-i_can_see_the_wealthy_future_forever/iter-24/eval.md |
| Journey history | — | runs/goal-session-i_can_see_the_wealthy_future_forever/state/journey-history.json |
