# goal-ops-hardening-iter-40 Execution Plan

## What to Build

- **The one risky change**: bound `_missing_data_diagnostic`'s second query
  (`apps/backend/app/engine/data_manager.py:271-274`) — replace the plain
  `for symbol, d in session.exec(select(DailyPrice.symbol, DailyPrice.date).where(DailyPrice.symbol.in_(universe))):`
  (which SQLAlchemy materializes whole-result via `_raw_all_rows` before the loop body runs, ~3.3M rows
  live) with a `.yield_per(cfg.research.read_batch_size)`-streamed read — the SAME knob
  `forward_testing.py`/`research.py`/`prices.py`'s `_BarCache.prefill`/`load_only` already use for this
  exact pattern (see `prices.py:132-141` for the idiom to mirror: `for symbol, d, ... in
  session.exec(stmt).yield_per(batch):`). The grouping into `own_dates_by_symbol` (line 274) and every
  downstream consumer of it stay byte-identical — only the fetch strategy changes.
- Correct the in-code comment at `data_manager.py:262-274` (currently: "no unbounded whole-table scan") to
  say the query is bounded **by symbol set** but was previously materialized **whole-result in memory**
  before this fix — now streamed — so it no longer asserts the opposite of what the pre-fix code did.
- A fixture-backed equality test proving `_missing_data_diagnostic`'s `no_history`/`thin`/
  `intra_series_gap` output is byte-identical for the same DB state before vs. after the fetch-strategy
  change (TC-1).
- Re-run the tightened-cap wedge-recurrence drill EXACTLY ONCE post-fix: throwaway DB via
  `scripts/start-backend.sh` (AG-10 — host-guard caps must stay intact), same cap family as iter-39 trial 3
  (~2650 MB) or tighter, never widened "so it completes gracefully" (binding iter-38 lesson). Assert from
  the LIVE `logs/backend.log` line range (not a trimmed excerpt — binding iter-34 lesson) whether the wedge
  recurs. Record the outcome in `reports/perf-budgets.md`. If the wedge does NOT recur, record that as a
  signal (not certainty) the fixed allocation was the cause. If it DOES recur, positively identify the
  dying thread (name/stack — e.g. a stack dump or targeted logging), not an inferred attribution, and log
  it as a new, separate ledger item — do NOT run a second cap trial this iteration (binding iter-39/iter-38
  lesson: don't chase a fourth cap tuning turn).
- iter-39/w checkpoint honesty (AG-3): tighten `_checkpoint_run_record`'s (`data_manager.py:4058-4093`)
  effective cadence so a `kill -9` at any point leaves the persisted `/data` Run History row within one
  checkpoint interval of the true in-memory progress — iter-39 measured 18/18 dates done in memory vs. only
  2/18 persisted (an order-of-magnitude gap), because the current `_RUN_RECORD_CHECKPOINT_INTERVAL_S =
  10.0` throttle (module-level constant, `data_manager.py:4055`) can skip nearly every per-date call
  (`_persist_isolated` already invokes `_checkpoint_run_record` after EVERY date in both the serial arm,
  `data_manager.py:3237`, and the parallel arm, `data_manager.py:3268` — the call site is not the gap; the
  10s throttle is). Tighten the interval (a config knob or a smaller constant — developer's call on
  mechanism, but no new magic number introduced silently) so per-date checkpoints land densely enough for a
  fast job; the throttle itself still governs whether any given call actually writes — same `message`
  field, same `_run_detail()` serializer, no new field, no second endpoint. Prove with a cadence test: a
  simulated multi-date run whose persisted `dates_done` never lags true progress by more than one interval,
  plus a control proving the throttle still bounds write volume (not a write on every single date
  regardless of interval).
- Correct `reports/perf-budgets.md:4996`'s trial-3 wedge attribution IN PLACE. Line 4996's own text still
  reads "most likely one of the `backfill_workers` parallel per-date compute threads" (repeated in the
  disposition paragraph at ~line 5018). The later "Audit B2" fix-pass section
  (`reports/perf-budgets.md:5198-5203`) already retracts this ("that wedge's dying thread was never
  positively identified... by the time trial 3's coverage `MemoryError` fired, `_do_backfill`'s pool had
  already been joined... Treat the wedge as an open, unreproduced hazard") but its supersession sentence
  names only TC-1..TC-4 — a reader stopping at the earlier ~line 4996/5018 text alone still gets the
  withdrawn story. Add an inline retraction note at both ~4996 and ~5018 pointing forward to the corrected
  account, so no unqualified sentence in the file still names `backfill_workers` as the wedge's cause.
- Teach `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py`'s `parse_rows` (verdict
  extraction, `_ROW_RE`/normalization around lines 62-94) and `compute_overall` (lines 119-134) a `BLOCKED`
  verdict class, mirroring `demo_runner.py`'s already-shipped priority `FAIL > BLOCKED > PASS >
  SKIP/SKIPPED` (see `demo_runner.py:142-160`'s `compute_regression_verdict` for the exact ordering to
  copy). Today `parse_rows` only recognizes `PASS/FAIL/SKIP/SKIPPED` cells, so a `BLOCKED` row's verdict
  cell is silently dropped and `compute_overall` never sees it — an all-`BLOCKED` merged run can headline
  `SKIPPED` (falls through) instead of `BLOCKED`. Fix both functions so `BLOCKED` is recognized, and the
  merged headline is `BLOCKED` when the surviving rows are all `BLOCKED`, while `FAIL` still wins when any
  row is `FAIL`. `goal_gate.py:89,151` already blocks achievement on any `BLOCKED` cell — this is an
  LLM-readable-headline fix only, no gate-logic change. Prove with unit tests (TC-6, TC-7) mirroring
  `merge_ui_test_results.py`'s existing `self-test` pattern (see the `void`/`verdict_for` self-tests
  already in the file for the harness shape).
- Re-score J-07 by the evaluator against all four acceptance clauses using this iteration's live evidence
  (single-source consistency, byte-identical correctness, honest-status/no-unbounded-materialization,
  walkthrough) — evaluator-side work, not a developer deliverable, but the dev handoff must supply the
  evidence trail the evaluator needs.

## Agents Required

- backend-data: yes — all seven in-scope items are backend Python (data_manager.py streaming fix + test,
  checkpoint cadence + test, live drill re-run + log evidence, perf-budgets.md correction,
  merge_ui_test_results.py BLOCKED class + unit tests).
- frontend-ux: no — goal spec is explicit: "None — the checkpoint-honesty fix is a backend cadence/timing
  change to an already-persisted field; the `/data` Run History panel already renders that field
  unchanged." No new UI capability, information, action, or surface this iteration.

## Frontend Present
no

## Files to Create/Modify

- `apps/backend/app/engine/data_manager.py` — stream `_missing_data_diagnostic`'s second query via
  `.yield_per(cfg.research.read_batch_size)`; correct the `:262-274` comment; tighten
  `_checkpoint_run_record`'s effective cadence (`_RUN_RECORD_CHECKPOINT_INTERVAL_S` / equivalent knob,
  `~line 4055`).
- `apps/backend/tests/test_data_manager.py` — fixture-backed equality test for
  `_missing_data_diagnostic`'s pre/post-fix output (TC-1); checkpoint-cadence test (TC-4: per-date
  invocation density, throttle still honored).
- `reports/perf-budgets.md` — new "Iteration 40" section recording the wedge-recurrence drill outcome
  (TC-2/TC-3) and the checkpoint-honesty live `kill -9` measurement (TC-4); in-place retraction note at
  `~line 4996` and `~line 5018` correcting the `backfill_workers` wedge attribution (TC-5).
- `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py` — `BLOCKED` verdict recognized in
  `parse_rows`/`compute_overall`, priority `FAIL > BLOCKED > PASS > SKIP`; new self-tests (TC-6, TC-7).
- `runs/goal-ops-hardening-iter-40/wedge-drill/` (or similar) — throwaway-DB drill config/scripts, raw
  `logs/backend.log` line-range evidence for the post-fix wedge re-check (TC-2/TC-3).
- `runs/goal-ops-hardening-iter-40/checkpoint-drill/` (or similar) — live `kill -9` + restart evidence for
  the checkpoint-honesty measurement (TC-4).
- `docs/handoffs/goal-ops-hardening-iter-40-dev.md` — dev handoff (required by Definition of Done).

## Key Test Scenarios

- TC-1: `_missing_data_diagnostic`'s `no_history`/`thin`/`intra_series_gap` output lists are byte-identical
  before and after the fetch-strategy change, for the same DB state (fixture-backed equality test).
- TC-2/TC-3: a throwaway backend launched via `scripts/start-backend.sh` with `server.memory_cap_mb`
  tightened to ~2650 MB or tighter (never widened) runs the same ingest/coverage-compute path post-fix;
  EITHER `/api/health` answers every 1 Hz poll HTTP 200 for the drill's full duration with no
  budget-exceeding gap and `logs/backend.log`'s live line range shows no traceback naming
  `_missing_data_diagnostic` / `data_manager.py:271` / `_raw_all_rows` (wedge does not recur — record as a
  signal, not certainty) OR an unresponsive window recurs and the dying thread is positively identified by
  name/stack (not inferred) and logged as a new ledger item, with no second cap trial attempted this
  iteration.
- TC-4: a live backend backfill job covering N dates, `kill -9`'d after M < N dates complete in memory
  (M independently tracked, e.g. a log line per date), restarted; the `/data` Run History row for that job
  shows a checkpointed `dates_done` within one checkpoint interval of M — never off by an order of
  magnitude as iter-39 observed (2/18 vs 18/18).
- TC-5: `reports/perf-budgets.md`'s earlier section (~line 4996, and the disposition paragraph ~line 5018)
  states the `backfill_workers` attribution retraction IN PLACE — no unqualified sentence anywhere in the
  file still names `backfill_workers` as the wedge's established cause.
- TC-6: two input UI-test-results files whose surviving rows are ALL `BLOCKED` merge to a
  `**Browser QA Verdict:** BLOCKED` headline (never `PASS`/`SKIPPED`).
- TC-7: a merged row set containing at least one `FAIL` and at least one `BLOCKED` headlines `FAIL` (FAIL
  still wins over BLOCKED).
- TC-8 (regression guard, not re-run live): existing `test_data_manager.py`/`test_ingest_finalize_fault_injection.py`
  suites re-run to confirm the byte-identical fetch-strategy change and iter-39's per-item `MemoryError`
  isolation are unaffected.
- TC-9: required-still-passing journeys (J-01, J-03, J-04, J-05, J-06, J-08, J-09) replay PASS via the
  deterministic lane or fall back cleanly to the LLM lane, no regressed verdict.
- Error case: a `MemoryError` raised inside the aggregate-warm loop (downstream of the fixed diagnostic
  call) is still caught and isolated exactly as iter-39 proved (job continues/finalizes honestly, never
  crashes the process).

## Out of Scope (per spec — flagged, not built)

- Relabeling the checkpoint figure "last saved checkpoint" — only if the cadence fix alone proves
  insufficient; not independently in scope this iteration.
- iter-33/g (Regime Lab cold `view=pooled` background dispatch) — rule 5 budget already full with this
  iteration's one risky change (the diagnostic-fetch fix) plus the three mechanical items.
- iter-29/b badge wording, iter-31/e, iter-32/f, iter-35/k, iter-36/n, iter-37/o, iter-37/q — carried,
  unaffected by this iteration's diff.
- iter-34/j (`/api/health` ≤0.1s budget disposition) and iter-33/i (`start-frontend.sh` host-guard
  membership) — owner decisions, not agent-actionable.
- Any change to `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`,
  `ensure_historical_forward_aggregates_dispatched` — byte-frozen.
- Re-running J-07 steps 1-3 or the already-closed step-4 per-horizon isolation proof, the env-toggle guard,
  root-logger config, `read_pool()` measurement, `_compute_one_isolated` isolation — all settled/closed at
  iter-39, binding "Do not redo."
