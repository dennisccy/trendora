# Iteration State — ops-hardening

**After iteration:** 1 · **Date:** 2026-07-19 · **Verdict:** CONTINUE

## Journeys

2 passing (J-01 J-03) · 1 partial (J-04) · 2 failing (J-05 J-06) — 5 total. J-01/J-03 newly passing this iter (browser-qa 17/17 + audit trace + unit tests). J-04 re-verified non-regressed.

## Active blockers

- None human-owned. Dev work remains: J-05's ingest-time aggregate hooks + `coverage_snapshot` table (retire the whole-table coverage prefill in `apps/backend/app/engine/data_manager.py` `compute_coverage`); J-06 per-page budgets; J-04's `scripts/start-backend.sh` persistent logfile + `ulimit`/`MALLOC_ARENA_MAX` enforcement.

## Last 2 verdicts

- iter 1: CONTINUE — J-01 + J-03 delivered and verified; AG-3 interrupted-row fabricated-zero found by browser-qa and FIXED by audit (B1) + tested; J-05/J-06 still failing so not achieved.
- iter 0: CONTINUE — baseline verify-only; all 5 fail as an honest measurement, no code changed.

## Do not redo

- J-01 DONE: cadence bypass for `backfill`/`both` (not `rebuild`), `dates_total` redefinition, run-summary breakdown (`calendar_days`/`non_trading_days`/`already_snapshotted`/`error_other`, invariants exact), persisted-history + zero-work-distinct UI — all live-verified. Do not rebuild.
- J-03 DONE: `max_range_days` removed everywhere (config.py/config.yaml/validate_job_request + 6 test files); `_do_backfill` date-window chunking via `import_chunking.date_window_days`. Do not re-add a cap.
- Audit B1/B2 fixes are IN TREE (data_manager.py `_run_detail` `_breakdown_computed` guard; `date_failures_total`). Do not re-report the interrupted-row fabricated-zero as new — but B3 (live `to_dict` `both`-during-fetch) + F1 (`dates_total` on interrupted rows) remain as one-line follow-ups if a future iter revisits interrupted-row rendering.
- J-04's boot speed / phase-aware badge / crash presentation / interrupted-after-restart already WORK — build ONLY the `start-backend.sh` logfile + memory-cap enforcement.
- `docs/goal.md` is lint-final (commit 9c98cb3) — do not edit it. The 25 mcp-loop journeys are archived — do not re-verify.
