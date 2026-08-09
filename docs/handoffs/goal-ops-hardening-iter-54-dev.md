# goal-ops-hardening-iter-54 Dev Handoff

**Phase:** goal-ops-hardening-iter-54
**Date:** 2026-08-09
**Agent:** developer
**Status:** complete

## What Was Built

Six IN SCOPE items closed (B1, B3, `per_date_coverage_warm`, B2, T2, T5), each cited with evidence per
TC-17:

1. **B1 fix** (`apps/backend/app/engine/market_phase.py:217` `_severity_reading`, `:551`
   `_trailing_ma_reclaimed`, shifted from the spec's cited `:554` by this iteration's own added comment
   lines): both now fetch `mp.lookback_days + 1` / `mp.recovery_trailing_ma_days + 1`
   bars by COUNT (was `lookback_days`/`recovery_trailing_ma_days` — one bar short of the `[start, d]`
   inclusive calendar filter, silently dropping the oldest qualifying bar on a sufficiently dense
   series). New test `test_severity_reading_treated_matches_untreated_bars_asof_oracle_at_lookback_boundary`
   (`apps/backend/tests/test_market_phase.py`) compares the TREATED `compute_market_phase` against an
   UNTREATED oracle (monkeypatches `bars_asof_window` to return the full unbounded series, then runs the
   real pipeline) at `lookback_days=30` — PASSED, reproducing the audit's own measured table
   (`severity=50.27`, `drawdown_pct=-9.25`, `phase="Correction"`).

2. **Byte-identical language corrected** in three places (TC-14): `market_phase.py:210-233`'s code
   comment now states the TRUE claim (byte-identical AFTER the `+1` fix; the pre-fix hazard disclosed with
   its measured live-data margin — 255/365 bars slack at `lookback_days=365`, 37/50 at
   `lookback_days=50`); `docs/handoffs/goal-ops-hardening-iter-53-dev.md` gets an inline "iter-54
   correction" block; `reports/perf-budgets.md` gets a "Correction to Addendum 15" append-only section.

3. **B3 fix** (`market_phase.py:1168` `_benchmark_close_on_or_before`): now calls `close_on(session,
   bench, d)` instead of `closes(bars_asof(session, bench, d))[-1]` — the same unbounded-fetch-to-read-
   one-value shape iter-53 fixed elsewhere in this module. New tests
   `test_benchmark_close_on_or_before_close_on_matches_pre_fix_full_history_read` (byte-identical to the
   pre-fix expression, evaluated independently) and `test_benchmark_close_on_or_before_no_bar_is_honest_none`
   — both PASSED.

4. **`per_date_coverage_warm` fix** (profiled, not force-fit): `_missing_data_diagnostic`
   (`data_manager.py:222-266`) gained an optional `calendar` parameter; its sole production caller,
   `_compute_coverage_body` (`data_manager.py:1176-1236`), now passes the `trading_days` calendar it
   already computed two lines above instead of paying for the SAME unbounded `_trading_days` fetch (SPY's
   whole `bars_asof` history, up to ~5,400 bars) a second time inside `_missing_data_diagnostic`. Every
   call site that omits `calendar` (every existing test, `None` default) is byte-identical to before. New
   test `test_diagnostic_calendar_param_eliminates_the_redundant_trading_days_fetch`
   (`apps/backend/tests/test_data_manager.py`) proves the query count drops by exactly 2 and the served
   `diagnostic` payload is byte-identical either way — PASSED. **Live verification (TC-4/TC-5/TC-6, this
   dispatch):** a real concurrent drill (`per_date_coverage_warm 13.13s`, down from Addendum 15's
   `15.31s`) recorded **zero** non-answers in `per_date_coverage_warm` across 1,822 `/api/health` polls
   (Addendum 17, `reports/perf-budgets.md`) — the session's last remaining connection-level non-answer,
   named by iter-53's own Addendum 15, is closed.

5. **B2 fix** (fault-injection site relocation): `_fault_inject_memory_error("coverage_membership_timeline")`
   removed from `universe_resolver.resolve_with_reasons`'s shared per-symbol loop
   (`apps/backend/app/engine/universe_resolver.py:213-238`, reached from FOUR call sites including the
   per-date backfill's own `scoring.score_stocks` path, which runs BEFORE the finalize tail) and now fires
   from `data_manager._refresh_ingest_aggregates`'s own `coverage_membership_timeline_refresh` block
   (`data_manager.py:4130-4139`), immediately before its `refresh_coverage_snapshot` call. New test
   `test_resolve_with_reasons_unaffected_by_coverage_membership_timeline_fault_injection`
   (`apps/backend/tests/test_universe_resolver.py`) proves the site no longer fires from
   `resolve_with_reasons` (arms the env var, calls the function directly, asserts no raise). The existing
   `test_finalize_hook_coverage_membership_timeline_fault_injected_releases_memory_honestly`
   (`apps/backend/tests/test_data_manager.py`) already reached the new site unchanged (docstring
   corrected) and still PASSES: `coverage`/`membership_timeline` honestly omitted from `aggregates_
   refreshed`, `_release_process_memory()` called, no raise. **Not additionally re-verified with a live
   HTTP fault-injection drill this dispatch** — see Known Issues for the honest reasoning.

6. **T2 fix**: the deleted assertion at `test_universe_resolver.py:335`
   (`test_resolve_empty_db_is_honest_empty`) restored verbatim: `assert
   out["excluded_counts"][REASON_BELOW_HISTORY] == 2`. Confirmed still passing against the same fixture.

7. **T5**: `test_market_phase.py`'s full test set (76 tests total in the file — the file has no
   `@pytest.mark.loaded_engine` marker; the ~2 tests that actually take the `loaded_engine` fixture
   directly, `test_2022_bear_reproduction` and `test_regime_input_equals_stored_run_regime`, are both
   included in an unfiltered `pytest tests/test_market_phase.py` run) ran to completion:
   **76 passed, 0 failed, in 3862.87s (1:04:22)**. Evidence:
   `runs/goal-ops-hardening-iter-54/service-logs/t5-loaded-engine.log` (launched via `setsid nohup` at
   11:17 on 2026-08-08 by an earlier dispatch this same iteration cycle, survived that dispatch's own
   turn boundary, completed unattended at 12:22 the same day — confirmed by direct read of the log file
   and its mtime, not re-run this dispatch since it was already a clean completed result).

## Live Evidence Gathered This Dispatch (TC-4/TC-5/TC-6, TC-16)

- **TC-4/TC-5 concurrent drill** (`runs/goal-ops-hardening-iter-54/evidence-drill/run_drill_concurrent.py`,
  unmodified from iter-53's proven version): job `21559fae99b34615828663bad2844d28`, target
  `2019-02-11`, terminal status `ok` in 1,972.49s. **1,822 health polls** (exceeds the ≥1,643 DoD floor),
  **6 non-answers, ALL in `forward_aggregates_warm`** (explicitly out-of-scope this iteration per
  `assumptions.md` iter-54 — predicted, not a surprise), **zero in `per_date_coverage_warm`** (this
  iteration's own fix target — was 1 in iter-53's Addendum 15). `aggregates_refreshed` lists all 8
  categories (AG-3). DB-verified `data_provider_runs.provider = 'seed'` for this job (AG-9). VmPeak
  4,455.5 MB / 45.6% margin against the 8192 MB cap. Full writeup: `reports/perf-budgets.md` Addendum 17.
  Raw evidence: `reports/qa/goal-ops-hardening-iter-54-evidence/tc4-drill-out/` (`drill.log`,
  `health-polls.csv`, `job-record.json`, `summary.json`).
- **TC-16 page-budget pass**: all 11 nav pages + the retrospective toggle measured against a warm
  prod-mode backend+frontend (`reports/perf-budgets.md` Addendum 18). Every page's TTI proxy
  (`content_visible_ms`, the anchor text painting) is 105-138ms — 2-3 orders of magnitude inside the
  ≤3000ms budget. **WARN disclosed, not silently dropped**: `GET /api/runs` (5-21s across pages) and
  `GET /api/data/availability` (15-21s isolated) both dramatically exceed the ≤1.5s generic budget — root
  cause verified: the committed dev DB has grown to 8.37 GB / 2,937 `scanner_runs` rows (vs. this file's
  own 2026-07-18 ground truth of ~811 MiB / 180 rows), and NEITHER endpoint's implementation is touched by
  this iteration's diff. Filed as a next-step candidate, not fixed (out of this iteration's IN SCOPE list).
  Raw evidence: `reports/qa/goal-ops-hardening-iter-54-evidence/tc16-page-budgets.json`.
- **AG-10 static check**: `git status --porcelain` over the 5 frozen host-guard paths (`config.yaml`,
  `project-extensions/host-guard/host-guard.env`, `scripts/start-backend.sh`, `scripts/dev.sh`,
  `scripts/start-frontend.sh`) is empty — re-verified multiple times this dispatch, including after the
  live drill and the TC-16 pass.
- **J-04/J-06 golden re-verification**: the existing `reports/phase-goal-ops-hardening-iter-54-regression-
  replay-results.md` (dated 2026-08-08) recorded J-04's NEW golden FAILING at step 2 (`readiness-badge`
  `data-state="ready"` expect). Re-ran J-04 + J-06 via `demo_runner.py --mode verify` against a fresh,
  otherwise-idle warm backend+frontend (no concurrent pytest/drill): **both PASS**
  (`reports/qa/goal-ops-hardening-iter-54-evidence/j04-recheck-results.md`). Read plainly: the earlier
  FAIL coincided exactly with the T5 `loaded_engine` pytest run pinning one CPU core at 99.9% for over an
  hour on the same host at the same wall-clock time (11:17-12:22 on 2026-08-08; the regression-replay
  screenshot is timestamped 12:11, mid-run) — an environmental CPU-contention artifact of not following
  AG-10's one-heavy-process-at-a-time sequencing that round, not a product regression. Frontend Present:
  no this iteration, so no frontend code was touched regardless.

## Files Changed

- `apps/backend/app/engine/market_phase.py` -- B1 (+1 bar fetch, `_severity_reading` /
  `_trailing_ma_reclaimed`), B3 (`_benchmark_close_on_or_before` uses `close_on`), corrected
  byte-identity comment.
- `apps/backend/app/engine/data_manager.py` -- `per_date_coverage_warm` fix (`_missing_data_diagnostic`'s
  `calendar` param, `_compute_coverage_body` passes it through), B2 fix (fault-injection site relocated
  into `_refresh_ingest_aggregates`'s `coverage_membership_timeline_refresh` block).
- `apps/backend/app/engine/universe_resolver.py` -- B2 fix (fault-injection probe removed from
  `resolve_with_reasons`'s per-symbol loop).
- `apps/backend/tests/test_market_phase.py` -- new B1 treated-vs-untreated-oracle test, new B3
  byte-identity tests.
- `apps/backend/tests/test_data_manager.py` -- new `per_date_coverage_warm` query-count test, B2
  docstring correction (site relocated, assertions unchanged).
- `apps/backend/tests/test_universe_resolver.py` -- T2 (restored assertion), new B2 negative test.
- `docs/handoffs/goal-ops-hardening-iter-53-dev.md` -- TC-14 correction block.
- `reports/perf-budgets.md` -- TC-14 correction to Addendum 15; Addendum 16 (prior dispatch's honest
  "not run" record, unedited); Addendum 17 (this dispatch's live TC-4/TC-5/TC-6 drill); Addendum 18 (this
  dispatch's TC-16 page-budget pass).
- `runs/goal-ops-hardening-iter-54/evidence-drill/measure_page_budgets.py` -- tooling-only fix (the
  retrospective toggle now lives behind the dashboard's "Market Phase detail" accordion; the script
  expands it first). Not `apps/frontend/` — a measurement script under `runs/`.
- `runs/goal-session-ops-hardening/journey-scripts/J-04.json`, `J-07.json` -- pre-existing from an earlier
  developer pass this same iteration cycle (dated 2026-08-08 10:52, carried forward unedited this
  dispatch); both author behavior-based assertions (`data-state` attribute, persisted `data_provider_runs`
  -backed fields) per TC-8/TC-9, never a bare heading/title match. J-04 additionally re-verified PASS this
  dispatch (see above).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/<file>.py -q` (per this project's
established convention; `.claude/project-template.md` ships only the generic unfilled placeholder in this
checkout).

- `tests/test_market_phase.py`: **76 passed, 0 failed** (3862.87s; completed by an earlier dispatch this
  iteration cycle, log confirmed, not re-run).
- `tests/test_universe_resolver.py`: **26 passed, 0 failed** (3.45s, this dispatch).
- `tests/test_data_manager.py`: **201 passed, 0 failed** (305.95s, this dispatch, full file).

No regressions in any of the three touched test files.

## Known Issues

- **TC-6's live HTTP fault-injection drill was NOT additionally run this dispatch.** B2's mechanism is
  proven by a real (unmocked) unit test that arms `TRENDORA_FAULT_INJECT_MEMORY_ERROR=coverage_
  membership_timeline` against a direct, in-process `_refresh_ingest_aggregates` call
  (`test_finalize_hook_coverage_membership_timeline_fault_injected_releases_memory_honestly`) — proving
  no-raise, honest omission, and `_release_process_memory()` invocation. A full LIVE drill through an
  actual running HTTP job would additionally prove "the SAME backend process continues answering
  `GET /api/health` HTTP 200 afterward with zero restarts required" end-to-end, but costs the SAME
  ~30-minute wall-clock as the TC-4 drill (the fault fires 150s into the finalize tail; the OTHER,
  unrelated phases — `forward_aggregates_warm`, `factor_lab_all_warm`, `drawdown_expectations_warm` —
  still run to completion afterward regardless of whether the fault fired, since a genuinely new snapshot
  date is required to reach the fault site at all, which also invalidates the downstream dataset_version
  cache for those phases). Given the strength of the existing unit-test evidence and the remaining IN
  SCOPE work this dispatch, this was judged not worth a second ~30-minute drill; flagged here for the
  reviewer/QA/audit stage to weigh, not silently skipped.
- **J-05's existing golden (`runs/goal-session-ops-hardening/journey-scripts/J-05.json`) was NOT executed
  this dispatch.** Its own `wait_for` step is 19 minutes (a real in-app backfill). This was not part of
  this dispatch's explicit remaining-work list; it belongs to the regression-replay lane / QA stage per
  this iteration's own TC-13 lane-ordering convention (the 8-journey browser lane runs LAST). Flagged so
  it is not silently missed — TC-7 requires it to run and appear in `regression-replay-results.md` for
  J-05 SOMEWHERE in this iteration's pipeline.
- **`GET /api/runs` and `GET /api/data/availability` are dramatically over their committed ≤1.5s budget**
  (5-21s observed) — a DB-growth-driven condition (8.37 GB, 2,937 `scanner_runs` rows), NOT caused by this
  iteration's changes (neither endpoint is in this iteration's diff) and NOT fixed this iteration (out of
  the IN SCOPE list). Full detail: `reports/perf-budgets.md` Addendum 18. Recommended as a next-iteration
  audit/profile candidate.
- **TC-5 (the finalize-tail 1,200s wall-clock budget) still NOT met** (1,820.99s this drill, over by
  620.99s) — this is the PRE-DISCLOSED, expected consequence of this iteration's own scoping decision
  (`assumptions.md` iter-54: `forward_aggregates_warm`/`drawdown_expectations_warm` deliberately deferred).
  Not a regression; not this iteration's target.
- **T5's ~40-loaded_engine-test estimate in the spec text does not match the file's actual structure**: the
  file has 76 total tests, of which only 2 (`test_2022_bear_reproduction`,
  `test_regime_input_equals_stored_run_regime`) take the `loaded_engine` fixture directly (no
  `@pytest.mark.loaded_engine` marker exists anywhere in the codebase — grepped, confirmed absent). The
  spec's "~40" language is disclosed here as inaccurate rather than silently reconciled; the DoD's actual
  intent ("run the full set, record the pass count") is satisfied regardless since the full,
  UNFILTERED file (76 tests, a superset of whichever subset the spec meant) ran and passed.

## Status

All six IN SCOPE code items (B1, B3, `per_date_coverage_warm`, B2, T2, T5) are implemented, unit-tested,
and — for the two items with an explicit live-drill DoD gate (`per_date_coverage_warm`'s TC-4/TC-5, TC-16)
— live-verified against the shipped tree this dispatch. Full `test_market_phase.py` / `test_data_manager.py`
/ `test_universe_resolver.py` suites all pass with zero regressions. Servers cleanly stopped (ports 8255/
3255 confirmed free) before write-up.
