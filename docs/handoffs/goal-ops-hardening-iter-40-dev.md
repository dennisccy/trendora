# goal-ops-hardening-iter-40 Dev Handoff

**Phase:** goal-ops-hardening-iter-40
**Date:** 2026-07-31
**Agent:** developer
**Status:** complete

## What Was Built

- **Streamed `_missing_data_diagnostic`'s second query** (`data_manager.py:271`, J-07's last standing
  blocker): replaced a bare `session.exec(select(...))` iteration — which SQLAlchemy materializes WHOLE-
  RESULT via `cursor._raw_all_rows()` before the loop body runs, ~3.3M `(symbol, date)` rows on the deep
  basis — with `.yield_per(cfg.research.read_batch_size)`, the SAME config knob `prices.py`'s
  `_BarCache.prefill` already uses for this exact pattern. Grouping into `own_dates_by_symbol` and every
  downstream consumer are byte-identical; only the fetch strategy changed.
- Corrected the in-code comment at `data_manager.py:262-274`, which previously claimed "no unbounded
  whole-table scan" (true of the query's SCOPE, false of its pre-fix MATERIALIZATION) — now states the
  query was always bounded in scope but was previously materialized whole-result in memory, and is now
  streamed.
- **Tightened `_checkpoint_run_record`'s effective cadence** (`_RUN_RECORD_CHECKPOINT_INTERVAL_S`,
  `data_manager.py:~4055`): 10.0 s → 1.0 s. At the old interval, a job whose ENTIRE run completed faster
  than one interval only ever wrote its first checkpoint, then throttled away every later per-date call —
  iter-39's live drill measured 18/18 dates done in memory against a persisted row stuck near the start
  (an order-of-magnitude gap). The per-date call sites, the throttle mechanism itself, the `message`
  field, and the `_run_detail()` serializer are all unchanged — only the interval value + its documented
  reasoning changed.
- **Live post-fix wedge-recurrence drill** (TC-2/TC-3, throwaway DB, `scripts/start-backend.sh`, same
  2650 MB cap family as iter-39 trial 3, never widened): the wedge did **not** recur in the clean,
  authoritative run — job completed `status: ok`, `GET /api/health` answered 200 on all 28 polls (0
  non-200, max gap 1.826 s), `VmPeak` peaked at exactly the declared cap without wedging, and a
  `MemoryError` that DID fire elsewhere (a small COUNT-DISTINCT at `data_manager.py:898`, not the fixed
  site) was caught cleanly by the pre-existing non-fatal isolation handler with zero downtime. Full
  evidence + a first, confounded, discarded run: `runs/goal-ops-hardening-iter-40/wedge-drill/`.
- **Live checkpoint-honesty kill -9 + restart drill** (TC-4): a 25-date backfill, `kill -9`'d after an
  independently-polled M=12 dates done, restarted — the persisted Run History row showed `dates_done: 11`,
  a 1-date gap (vs. iter-39's order-of-magnitude gap at the old interval). Full evidence:
  `runs/goal-ops-hardening-iter-40/checkpoint-drill/`.
- **`reports/perf-budgets.md` corrections**: inline `[RETRACTED]` notes added in place at the trial-3
  table row (~line 4996) and the "Recommendation" paragraph (~line 5018), both pointing forward to the
  already-existing "Audit B2" correction and this iteration's own new section, so a reader stopping at
  either earlier passage no longer gets the withdrawn `backfill_workers` attribution story. New
  "Iteration 40" section records the wedge-drill and checkpoint-drill outcomes in full.
- **`merge_ui_test_results.py` BLOCKED verdict class**: `parse_rows` now recognizes `BLOCKED` (both the
  primary cell scan and the annotated-cell fallback regex); `compute_overall` now applies
  `FAIL > BLOCKED > PASS > SKIP/SKIPPED` priority (mirroring `demo_runner.py`'s already-shipped
  `compute_regression_verdict`), in both the row-verdicts branch and the file-headline fallback branch.
  `merge()`'s rendered output also gained a "## Blocked Tests" section and a blocked count in the Overall
  line, mirroring `demo_runner.py`'s `render_regression_results_md` shape for consistency (a BLOCKED row
  previously had no detail section at all, unlike FAIL/SKIP rows).

## Files Changed

- `apps/backend/app/engine/data_manager.py` -- streamed `_missing_data_diagnostic`'s own-dates query;
  corrected the `:262-274` comment; tightened `_RUN_RECORD_CHECKPOINT_INTERVAL_S` 10.0 → 1.0 with
  documented reasoning.
- `apps/backend/tests/test_data_manager.py` -- added
  `test_diagnostic_own_dates_streamed_fetch_byte_identical_to_whole_result` (TC-1) and
  `test_checkpoint_cadence_density_and_throttle_control` (TC-4 unit-level).
- `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py` -- `BLOCKED` verdict recognized
  in `parse_rows`; `FAIL > BLOCKED > PASS > SKIP` priority in `compute_overall` (both branches); "##
  Blocked Tests" section + blocked count in `merge()`'s rendered output; two new self-tests
  (`t_blocked_all_headlines_blocked` / TC-6, `t_fail_still_wins_over_blocked` / TC-7).
- `reports/perf-budgets.md` -- inline retraction notes at ~4996/~5018 (TC-5); new "Iteration 40" section.
- `runs/goal-ops-hardening-iter-40/wedge-drill/` -- scratch config, seed script, monitor script, two
  runs' worth of live evidence (`README.md` is the index).
- `runs/goal-ops-hardening-iter-40/checkpoint-drill/` -- scratch config, seed script, combined
  trigger+poll+kill script, live evidence (`README.md` is the index).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py -v -k "cadence or diagnostic"`
Result: 9 passed (includes both new TC-1/TC-4 unit tests)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager.py -q`
Result: **142 passed** (0.72 s cadence test included; ~297 s total)

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager_jobs_pipeline.py tests/test_ingest_finalize_fault_injection.py -q`
Result: **26 passed** (~663 s) — confirms iter-39's per-item `MemoryError` isolation and the pre-existing
checkpoint-throttle unit test (which monkeypatches `_RUN_RECORD_CHECKPOINT_INTERVAL_S` directly, so it is
unaffected by the new default value) are unaffected by this iteration's changes.

Command: `python3 incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py self-test`
Result: **14 passed, 0 failed** (12 pre-existing + 2 new: TC-6, TC-7)

Command: `bash incredible_auto_dev/tests/automation/test-replay-lane.sh`
Result: **65 passed, 0 failed** — confirms the `merge_ui_test_results.py` change did not regress the
replay-lane integration tests that already exercise it (canary reconciliation, void, deferred-budget
rows, etc.).

Live drills (not pytest, evidence-based per J-07's own acceptance clause):
- Wedge-recurrence re-check: `runs/goal-ops-hardening-iter-40/wedge-drill/README.md` — wedge did NOT
  recur in the clean, authoritative run.
- Checkpoint-honesty kill -9: `runs/goal-ops-hardening-iter-40/checkpoint-drill/README.md` — 1-date gap
  between true kill-time progress (M=12) and persisted `dates_done` (11) after restart.

## Pre-handoff Verification

- **Service startup**: `bash scripts/dev.sh` — both backend (`:8255`) and frontend (`:3255`) started
  cleanly on the real committed product DB; `GET /api/health`, `/api/dashboard`, `/api/sectors`,
  `/api/themes`, `/api/stocks`, `/api/backtest` all answered 200. Stopped and restarted a second time;
  `dev.sh`'s own port-freeing logic (`lsof -ti :$PORT` / `fuser -k`, by PORT not by process-name pattern)
  correctly reclaimed both ports each time — no port-conflict error from the script itself. (My own first,
  informal verification attempt used a raw `&`-backgrounded launch outside the tool's tracked mechanism
  and left a stray `next dev` process that an ad hoc `pkill -f "next dev -p 3255"` pattern match missed —
  that was an artifact of my own manual cleanup command, not of `dev.sh`, whose built-in cleanup is
  port-based and unaffected.)
- **External integrations**: N/A — no new adapters/scrapers/external API calls introduced this iteration
  (AG-9 unaffected; the wedge/checkpoint drills' `source: "yahoo"` field is accepted but never used for
  `kind: "backfill"` jobs — only `fetch`/`both`/`expand` kinds resolve a live provider — confirmed by
  reading `_FETCH_KINDS = ("fetch", "both")` vs `_BACKFILL_KINDS = ("backfill", "both")` in
  `data_manager.py`; both drills ran purely against already-seeded offline data).
- **Native dependency binaries**: N/A — no new dependencies added.

## Known Issues

- **Run 1 of the wedge-recurrence drill was inconclusive** (my own test-setup confound: the job was
  triggered while the boot warmup thread was still mid-flight, so two independent heavy memory consumers
  raced for the same 2650 MB cap). The process wedged in that run, but the dying thread was not positively
  identified (`gdb` attach was denied by this host's `yama.ptrace_scope` policy; no `py-spy` was
  installed). Retained as `runs/goal-ops-hardening-iter-40/wedge-drill/run1-notes.md` for honesty, not
  used as this iteration's evidence — run 2 (clean, same cap, corrected trigger timing) is authoritative
  and shows no wedge. If a future iteration wants ptrace-based stack dumps for live drills, `gdb`'s
  non-root attach needs a host policy change (`kernel.yama.ptrace_scope`) or `py-spy` would need to be
  added as a dev-only dependency — neither was done here (out of scope for a single-iteration diagnostic,
  and the clean run 2 already answered TC-2/TC-3 without needing it).
- **The checkpoint-cadence density guarantee is time-based, not count-based**: `_checkpoint_run_record`
  still throttles by wall-clock seconds (now 1.0 s instead of 10.0 s), so a job whose per-date compute is
  faster than ~1.0 s/date can still let more than one date complete between checkpoint writes (the live
  drill observed a 1-date gap at a burst rate of ~120-140 ms/date). This is a much tighter bound than
  before, and the unit test (`test_checkpoint_cadence_density_and_throttle_control`) proves the density
  guarantee holds mathematically (`max_staleness <= ceil(interval/dt)`), but an extremely fast job (e.g. a
  future platform upgrade making per-date compute sub-100ms) could still show a multi-date gap under this
  same time-based mechanism. Not addressed this iteration (plan explicitly scoped this as "tighten the
  interval," not "redesign the mechanism"); flagged for awareness only.
- **iter-39/w's out-of-scope fallback (relabeling the checkpoint figure "last saved checkpoint")** was not
  needed — the cadence fix alone closed the honesty gap to within 1 date on a live drill, so the fallback
  UI-copy change remains correctly out of scope per this iteration's own boundary.
- Owner-decision items (iter-34/j health budget, iter-33/i `start-frontend.sh` host-guard membership)
  remain open, unresolved by this iteration (explicitly out of scope, per four prior evaluators).
