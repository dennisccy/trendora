# goal-ops-hardening-iter-51 Execution Plan

## Alignment check

Advances `docs/goal.md` directly: Key Capability 3 ("Ingest-time aggregate maintenance") and
Improvement-direction candidate #6 ("Research event-study/factor-lab/regime-lab hot keys ... warm
default keys at ingest"). This iteration extends the SAME `_refresh_ingest_aggregates` finalize-tail
precedent that already warms `event_study_cache`'s default key to the sibling `factor_lab_all_cached`
key — no new architecture, no new endpoint, no new Data Contract producer/consumer pair. Builds
directly on iter-50's FAIL audit, whose own recommended next step (#3) named this exact fix verbatim:
"serve `/research/factor-lab` from an ingest-time artifact instead of computing it on the request
path." No drift from goal/spec detected; no scope creep to flag — every IN SCOPE item traces to an
existing goal.md capability or a named iter-50 carry-forward.

Iter-50 verdict was ESCALATE/FAIL (see `docs/handoffs/goal-ops-hardening-iter-50-audit.md`): J-07's
health-poll ceiling breached under the concurrency the fix itself required (96/1,179 polls > 2.0s,
GIL contention between the Factor Lab request-path compute and the finalize tail), and J-05's
defining case still lacked in-app browser proof. This iteration's fix (warm at ingest, so the request
path is a cache HIT) is the structural change the auditor and `docs/goal.md` both prescribe.

## What to Build

- New finalize-tail warm phase `factor_lab_all_warm` inside `_refresh_ingest_aggregates`
  (`apps/backend/app/engine/data_manager.py`), calling
  `research.factor_lab_all_cached(session, cfg, as_of=None)` for the default all-history key —
  mirroring the existing `research_hot_keys_warm` (single default-key warm, non-fatal isolation) and
  `index_series_warm` (distinct `MemoryError` catch + `_release_process_memory()`, honest
  "persisted-this-run" gating) phases immediately below it. Include: `prog.tick()` heartbeat
  before/inside the call (this phase can run several minutes per iter-50's 578-875s cold-miss
  measurement), a `J-05 finalize-tail phase timing` log line matching the existing per-phase log
  format, and on success append `"factor_lab_all"` to `aggregates_refreshed` — omitted (never
  fabricated) on a MemoryError or non-fatal exception, mirroring every sibling category's honesty
  gate.
- Bound `_combination_cohort_members`'s `strict_members` construction
  (`apps/backend/app/engine/research.py:1562`) so it no longer unconditionally allocates
  `set(range(pool_n))` before reducing it by intersection. Start instead from the first
  single-condition membership set (or an empty set when `resolved` has no conditions), then intersect
  with the rest. Must remain byte-identical: same `single`/`strict`/`composite` output sets for every
  existing caller (`compute_factor_combination` and its samples drill-down), proven against a pinned
  pre-fix reference fixture — this is the exact frame logged before the 2026-08-05 17m30s wedge, so
  the fix must be a pure allocation-strategy change, not a semantics change.
- Dated addendum in `reports/perf-budgets.md` recording the new `factor_lab_all_warm` phase's own
  measured wall-clock contribution, and reconciliation of the existing TC-1 1,200s finalize-tail-total
  budget against the new real total (record honestly; do not silently loosen or silently exceed).
- Confirm the iter-50 teardown timing lines (`_release_process_memory: START/DONE`,
  `J-05 finalize-tail teardown timing`) fire and are captured in this iteration's own concurrent
  heavy-warm drill (diagnostic only — no new fix claimed toward the still-open, unproven-either-way
  2026-08-05 wedge; do not touch `_try_acquire_drawdown_warm`/`_release_drawdown_warm`, an explicit
  owner-deferred spec contradiction, `iter-50/cc`).
- New/updated unit tests for the warm phase (cache-row creation, honest `aggregates_refreshed` gating
  on MemoryError, `_release_process_memory()` invoked on abort — mirror the existing
  `test_finalize_hook_warms_index_series_hot_key` /
  `test_finalize_hook_index_series_memory_error_isolated_and_not_reported` pattern in
  `test_data_manager.py`) and for the `_combination_cohort_members` bound (byte-identical
  `single`/`strict`/`composite` sets against a pinned reference, no `set(range(pool_n))` allocation for
  a representative pool size — see `test_research_streaming.py`'s existing
  `factor_lab_all_cached`/pinned-oracle tests for house style).
- Dev handoff at `docs/handoffs/goal-ops-hardening-iter-51-dev.md`.

## Agents Required

- backend-data: yes -- all IN SCOPE work is backend (`data_manager.py`, `research.py`, their tests,
  `perf-budgets.md`). No frontend/UX agent needed.
- frontend-ux: no

Frontend Present: no

## Files to Create/Modify

- `apps/backend/app/engine/data_manager.py` -- add the `factor_lab_all_warm` phase to
  `_refresh_ingest_aggregates`'s finalize tail (near `research_hot_keys_warm` /
  `index_series_warm`, ~line 4196-4258), appending the new legal `aggregates_refreshed` member
  `"factor_lab_all"`.
- `apps/backend/app/engine/research.py` -- bound `_combination_cohort_members`'s `strict_members`
  construction at line 1562 (no unconditional `set(range(pool_n))`); no signature/behavior change to
  `factor_lab_all_cached`/`compute_factor_lab_all` themselves.
- `apps/backend/tests/test_data_manager.py` -- new tests for the `factor_lab_all_warm` phase
  (cache-row creation on MISS, honest gating on success/HIT/MemoryError, `_release_process_memory()`
  called on abort, phase-timing log line present).
- `apps/backend/tests/test_research_streaming.py` -- new/updated test(s) for
  `_combination_cohort_members`'s bound (byte-identical membership sets vs. a pinned pre-fix reference
  fixture; no `set(range(pool_n))` allocation asserted for a representative pool size).
- `reports/perf-budgets.md` -- fresh dated addendum: new phase's measured cost + reconciled
  finalize-tail total (append-only, per this file's existing convention — never rewrite prior
  addenda).
- `docs/handoffs/goal-ops-hardening-iter-51-dev.md` -- dev handoff (new file).

Do not touch (frozen/out-of-scope per spec): `config.yaml`, `project-extensions/host-guard/host-guard.env`,
`scripts/start-backend.sh`, `scripts/dev.sh`, `scripts/start-frontend.sh` (AG-10);
`_try_acquire_drawdown_warm`/`_release_drawdown_warm` (owner-deferred `iter-50/cc` contradiction); the
columnar `_FactorCoreRecords`/`_FactorObsPool` bound, the single-flight waiter cooldown, and
`phase_context_by_date` (all DONE per iteration-state.md's "Do not redo" list).

## Key Test Scenarios (from the phase spec's TC-1..TC-9)

- TC-1/TC-2: a `/data` backfill that bumps the dataset-version stamp leaves `aggregates_refreshed`
  containing `"factor_lab_all"` and a matching `EventStudyCache` row
  (`subject=_ALL_FACTORS_SUBJECT`, `view=_ALL_FACTORS_VIEW`, `asof_key=None`, current
  `dataset_version`+token, `horizon=default_horizon`); the immediately-following
  `GET /api/research/factor-lab?all=true` is a cache HIT (HTTP 200, no live
  `compute_factor_lab_all` invocation logged).
- TC-3: live browser load of `/research/factor-lab` (all-factors) immediately after ingest, measured
  time-to-interactive + API latency recorded in `reports/perf-budgets.md`, closing the previously
  recorded 780.2s/874.7s/742.07s over-budget readings.
- TC-4: `_combination_cohort_members` on a representative-size pool allocates no
  `set(range(pool_n))` scratch set; `single`/`strict`/`composite` outputs byte-identical to the
  pinned pre-fix reference oracle.
- TC-5/TC-6: during the finalize tail (including the new phase), `GET /api/health` polled 1/s for the
  full duration + 300s past completion answers HTTP 200 every time, peak VmPeak stays under
  `server.memory_cap_mb` with margin recorded; a concurrent Factor Lab / factor-combination request
  mid-warm is a cache HIT, no live compute, no `MemoryError` traceback.
- TC-7: iter-50's teardown timing log lines present and captured (diagnostic capture only, no new
  fix claimed).
- TC-8: the full 8-journey browser/replay lane (J-01..J-09) runs LAST — no product-code file has an
  mtime later than the lane's results-file mtime; any post-lane fix-mode/audit-fix pass forces a
  mandatory re-run before scoring (the sequencing rule breached 5 consecutive prior rounds).
- TC-9: `reports/perf-budgets.md`'s TC-1 1,200s finalize-tail-total budget reconciled against the new
  measured total in a fresh dated addendum (never silently loosened or exceeded).
- Target journeys J-05, J-06, J-07 scored via browser-qa-agent/deterministic replay + LLM fallback;
  required-still-passing J-01, J-03, J-04, J-08, J-09 stay green.
- Anti-goal gates: `git diff --stat` over the four AG-10 frozen files stays EMPTY; all drill ingest
  uses `provider='seed'` (AG-9); no committed secret (AG-7); no lookahead introduced (AG-5).
