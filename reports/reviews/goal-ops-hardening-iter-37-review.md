**Verdict:** PASS_WITH_NOTES

```yaml
phase: goal-ops-hardening-iter-37
date: 2026-07-30
reviewer: reviewer
summary: |
  `_do_backfill` now stashes its already-loaded whole-table `_BarCache` on `JobProgress
  ._shared_bar_cache`; `_refresh_ingest_aggregates` wraps its entire finalize tail in
  `attach_shared_cache` (reusing pre-existing, already-tested infra) so every warm call for the
  same job (coverage, market-phase, forward-aggregates, drawdown-expectations) reuses one
  pre-loaded cache instead of loading `daily_prices` twice per job. Release moves to
  `_refresh_ingest_aggregates`'s own `finally`; a whole-stage `_do_backfill` exception still
  releases immediately (unchanged discipline). Verified via code reading that the two
  orchestration call sites in `_run_job` always route a successful backfill through
  `_refresh_ingest_aggregates`, so the deferred-release invariant holds in production.
  Independently re-ran `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once`
  (PASS, 48.64s) and the new `test_backfill_coverage_shared_cache.py` (2 passed, 122.28s) — the
  pinned reference body matches `git show HEAD` verbatim. `reports/perf-budgets.md` gains a
  thorough, honestly-disclosed Iteration 37 section covering TC-1 through TC-5/step-4, including a
  disclosed non-blocking new finding (two unrelated read-path `MemoryError`s at the same tight
  drill cap). No scope creep — only `data_manager.py` and the new test file changed.
spec_alignment:
  definition_of_done: complete
  scope_creep: none
issues:
  - severity: MINOR
    file: apps/backend/app/engine/data_manager.py
    line: 3162
    category: tests
    summary: the new `except Exception:` branch in `_do_backfill` (clears `prog._shared_bar_cache`,
      releases immediately, re-raises on a whole-stage failure) has no direct test — existing
      backfill-failure tests only exercise per-date isolated failures, which never reach this
      branch (they're caught inside `_run_targets`, never raised past the `with` block).
    fix: add a test that monkeypatches `read_pool`/`prefilled_bar_cache` to raise inside
      `_do_backfill` and asserts `prog._shared_bar_cache is None` plus a `_release_process_memory`
      call before the exception propagates.
  - severity: NOTE
    file: apps/backend/app/engine/data_manager.py
    line: 3172
    category: code-quality
    summary: the deferred-release guarantee ("second consecutive rebuild starts lean") now only
      holds for the full `_run_job` orchestration path; a direct caller of `_do_backfill` that
      never calls `_refresh_ingest_aggregates` afterward (several existing unit tests do this,
      e.g. `test_data_manager.py:2154`) no longer gets `_release_process_memory()` on success. Not
      a production regression (both real call sites in `_run_job` always route a successful
      backfill through the finalize hook) — worth a doc note for future direct callers.
    fix: none required this iteration; note in a future test-hygiene pass if a new direct-call
      test site is added that runs many `_do_backfill` calls back-to-back near the memory cap.
standards:
  state_transitions_server_side: n/a
  test_quality: pass
  no_dead_code: pass
  no_hardcoded_localhost: pass
  architecture_principles: pass
```
