# goal-ops-hardening-iter-13 Execution Plan

## Context (read before building)

This is the session's first REAL code-change iteration in a while (depth FULL, trigger 2 — data
model). Prior iterations (10-12) were verification/measurement-only. Goal: close J-06's last
agent-owned gap by warming `GET /api/indexes?full=true`'s single unparameterized default hot key
(aggregation candidate #7, `docs/goal.md` Improvement direction table) at ingest time.

**The confirmed violation** (iter-12 G2 closure, `reports/perf-budgets.md`): three independent
fresh-navigation real-Chrome loads of `/data` measured `GET /api/indexes?full=true` at
2138.7-2257.7ms against its committed ≤1.5s budget, on a verifiably idle host. This is the ONLY
non-passing Must-have (J-06 `partial`); J-01/J-03/J-04/J-05 are all `passing`.

**The hot key, precisely:** `range_key=cfg.index_chart.default_range` (currently `"all"`,
`days=None` — all-history), `full=True`. This is exactly what `PhaseCrossViewCard` (`/`,
`fetchIndexes(undefined, asof, controller.signal, true)`) and `IndexVendorPanel` (`/data`,
`fetchIndexes(undefined, undefined, controller.signal, true)`) both request unparameterized on
mount — confirmed by reading `apps/frontend/lib/api.ts` + both components. 9 symbols configured
under `index_chart.symbols` (`config.yaml:325-347`).

**Technical note for the implementer (not mandated, from goal.md):** for this specific hot key,
`compute_index_series`'s series computation does not depend on the resolved `as_of` at all —
`bars_through_latest` (full=True path) ignores it, and `start` is `None` for the all-history
preset (`apps/backend/app/engine/indexes.py:84-176`). The only as-of-dependent part of the
response is the echoed `asof_date` field. Re-deriving/echoing the CURRENT resolved `as_of` at read
time (rather than baking a stale one into the stored payload) avoids an unnecessary correctness
trap — left to the developer's design.

**Dataset-version stamp — use a NARROW, index-scoped stamp, not the broad `research._dataset_version`.**
This codebase already has precedent for scoping the invalidation stamp to only the inputs a given
cache actually reads (`research._membership_dataset_version`, which deliberately excludes the
`forward_returns` count that the broad `_dataset_version` folds in, to avoid needless
invalidation). `IndexSeriesCache`'s stamp should depend ONLY on the freshness of the configured
`index_chart.symbols`' stored bars (e.g. `max(date)` + `count(*)` from `daily_prices` filtered to
`symbol IN (...)` those ~9 symbols) — a bounded, indexed read (existing
`uq_daily_prices_symbol_date` / `ix_daily_prices_date` indexes), never a whole-table scan and never
the broad scanner-run/forward-return-based stamp (which would invalidate on unrelated ingest
activity that never touches an index symbol's bars).

**Mirror the "research_hot_keys" / "forward_aggregates" warm-block shape, not the per-date
coverage/market-phase sweep.** This is a SINGLE hot key, not a loop over many items — the existing
unconditional (not gated on `prog.new_snapshot_dates`) single-key warm pattern already used for
`research_hot_keys` (`data_manager.py:3243-3252`) is the closer precedent, because the dataset-
version stamp is scoped to bar freshness, not to "this run's new snapshot dates" — any ingest that
lands a bar for a configured index symbol (anywhere) must invalidate it, mirroring
`forward_aggregates`'s "the stamp is global, so any ingest anywhere can invalidate it" reasoning
(`data_manager.py:3200-3213`).

**PUMP NOTE constraints (operator, this dispatch) — binding on this plan:**
- Scope is ONLY this cache/warm-step. Do NOT fold in the AG-8 `forward_testing.py:826`
  MemoryError fix, `HOST_GUARD_REQUIRE_MARKERS`, or the `demo.sh --session-live` walkthrough — all
  separate owner decisions, explicitly out of scope (goal.md OUT OF SCOPE section agrees).
- Agents in this pipeline CANNOT start/stop services this session (permission classifier), and the
  subagent-resume channel is broken. Any kill/restart/boot step, or a fresh-ingest-warm needed to
  populate the new cache table for browser-qa, must be written as an OPERATOR-performed fallback
  (the operator restarts on request with recorded pid/timestamp) — do not plan on agents
  restarting the backend themselves. Services are being restarted now; expect them up on :8255
  (backend) / :3255 (frontend) shortly. This iteration DOES change backend source (new table + new
  module code), so the backend process needs a restart before browser-qa can exercise it.
- Do NOT plan the full pytest suite. Name targeted test files only, run host-guard-confined:
  `taskset -c 0-3,8-11`, `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=NUMEXPR_NUM_THREADS=4`
  (values from `project-extensions/host-guard/host-guard.env`, matching iter-8/iter-12 precedent).
- Do NOT plan the opt-in heavy-ingest / full-universe backfill (AG-10; two hard hardware resets
  under that class of load, 2026-07-20/21). A small, bounded backfill/fetch touching one configured
  index symbol is sufficient for TC-4's invalidation test — never a full-universe rebuild.
- Environment: before running tests or anything that writes temp files, export
  `TMPDIR=TMP=TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-3c35d720.791787"`.

**Blueprint bookkeeping already done — do not re-do.** The goal-mode decomposer has already
registered this iteration's two Data-Contract bookkeeping additions in
`runs/goal-session-ops-hardening/state/blueprint.md` (the "Index series (J-44)" row naming
`IndexSeriesCache` as its ingest-warmed serving-path cache, and the `aggregates_refreshed` row
naming the new `"index_series"` enum member) — confirmed by direct read. The developer does not
need to touch `blueprint.md`.

## What to Build

- **`IndexSeriesCache` table** (`apps/backend/app/models.py`) — a STANDALONE, `create_all`-managed
  cache table mirroring the `ForwardAggregateCache`/`EventStudyCache`/`MarketPhaseCache` docstring
  convention exactly (own table, no `_ADDITIVE_COLUMNS` trap; a cache of the deterministic
  read-only `compute_index_series` derivation, never a second computation). Stores the serialized
  payload for the single unparameterized default hot key, keyed by that key plus the new narrow
  index-scoped `dataset_version` stamp described above.
- **`index_series_cached` wrapper** (e.g. `app.engine.indexes.index_series_cached`) — serves the
  stored row on a hit; on a miss or stale dataset-version stamp, computes via the UNCHANGED
  `compute_index_series` and persists (self-healing, mirroring every sibling cache).
- **Route `GET /api/indexes` through the wrapper ONLY for the hot key** (`apps/backend/app/api/indexes.py`):
  request matches hot key exactly (no `range` param or `range == default_range`, `full=True`, no
  explicit historical `as_of`). Every other combination — an explicit non-default `range`, an
  explicit historical `as_of` — keeps calling `compute_index_series` directly, unchanged, lazy (the
  existing "cannot be precomputed (user-parameterized)" carve-out).
- **Warm the hot key inside `_refresh_ingest_aggregates`** (`apps/backend/app/engine/data_manager.py`):
  unconditional single-key warm block (mirrors `research_hot_keys`/`forward_aggregates` shape),
  with its own `MemoryError`-specific isolation (catch distinctly, stop immediately, call
  `_release_process_memory()`, never flip the ingest job's own status) exactly like the other four
  warm loops in this function already do (iter-8 convention). Append `"index_series"` to
  `aggregates_refreshed` ONLY when the warm step actually persisted a row this run.
- **No change** to `compute_index_series`'s signature, return shape, or byte-level output for any
  input; no change to its other call site (`app/mcp/tools.py`/`server.py`'s `get_indexes` tool).
- **Targeted tests** (see Files to Create/Modify + Key Test Scenarios below).
- **Dev handoff** at `docs/handoffs/goal-ops-hardening-iter-13-dev.md`, stating PLAINLY whether the
  post-fix control readings actually landed ≤1.5s or not (iter-12's own lesson: score the number,
  not the fact that code was written).

## Agents Required

- backend-data: yes -- new `IndexSeriesCache` model, `index_series_cached` wrapper +
  index-scoped dataset-version stamp, `_refresh_ingest_aggregates` warm-step + MemoryError
  isolation, `GET /api/indexes` hot-key routing, targeted backend tests, dev handoff.
- frontend-ux: no -- goal.md iter-13 spec states "no product source changes anticipated"; same
  endpoint, same request shape, same response shape, only a faster hot-key path. No frontend file
  may be touched this iteration.

## Frontend Present

yes

`Frontend Present: yes` is set SOLELY to force the real-browser latency re-measurement (iter-5's
own lesson: curl under-reports call-heavy pages) via browser-qa-agent — not because any UI file
changes. See UI Evolution below.

## Out of Scope (do not build)

- The critical AG-8 `forward_aggregates_cached` → `compute_forward_aggregates` unbounded-load
  `MemoryError` (`apps/backend/app/engine/forward_testing.py:826`) — separate, owner-scoped,
  unresolved since iter-8. TC-12 requires this file be byte-unchanged; do not touch it, not even
  incidentally.
- `HOST_GUARD_REQUIRE_MARKERS` and the `demo.sh ops-hardening --session-live` walkthrough — owner
  decisions, unchanged since iter-8/iter-12.
- Caching any range preset other than the configured default, or any explicit historical `as_of` —
  those stay on the existing lazy, uncached path.
- The full pytest suite or any concurrent pytest run — targeted subset only, host-guard-confined.
- Any opt-in heavy-ingest workload or full-universe backfill (AG-10).
- Re-measuring the other 10 already-in-budget J-06 pages' TTI or the boot-to-health budget — spot-
  check only for regression, per goal.md.
- Any change to `app/api/health.py`, `app/engine/readiness.py`, `main.py`'s boot sequence,
  `warmup.py`, `max_range_days`/`snapshot_cadence`, the `/evidence` drawdown warm, or
  `server.memory_cap_mb` — all BINDING "do not redo" items from iteration-state.
- Framework harness bugs (`merge_ui_test_results.py`, browser-qa-skip misrouting) — never patch
  `scripts/automation/*` from inside a product iteration.
- Editing `runs/goal-session-ops-hardening/state/blueprint.md` — already done by the decomposer.

## Files to Create/Modify

- `apps/backend/app/models.py` -- add `IndexSeriesCache` (STANDALONE `create_all`-managed table),
  mirroring `ForwardAggregateCache`/`EventStudyCache`/`MarketPhaseCache`'s docstring + unique-
  constraint-keyed-upsert convention. Suggested columns: `range_key`, `full` (bool),
  `dataset_version`, `payload_json`, `created_at`; unique constraint on
  `(range_key, full, dataset_version)`.
- `apps/backend/app/engine/indexes.py` (or `data_manager.py`, developer's choice of home) -- add
  a narrow index-scoped dataset-version helper (bounded `max(date)`/`count(*)` read over
  `index_chart.symbols` only) and the `index_series_cached` self-healing wrapper. Do not modify
  `compute_index_series` itself.
- `apps/backend/app/api/indexes.py` -- route the hot-key request (no/default `range`, `full=True`,
  no explicit `as_of`) through `index_series_cached`; every other combination unchanged.
- `apps/backend/app/engine/data_manager.py` -- new unconditional single-key warm block inside
  `_refresh_ingest_aggregates` (mirrors the `research_hot_keys`/`forward_aggregates` shape, own
  `MemoryError` isolation + `_release_process_memory()`); add `"index_series"` to the two existing
  `aggregates_refreshed` enumeration comments (`JobProgress` field doc ~line 1888-1889, and the
  `_refresh_ingest_aggregates` docstring ~line 3121-3123) for consistency with the other six.
- `apps/backend/tests/test_indexes.py` -- new tests for `index_series_cached`'s hit/miss/self-heal
  path and byte-identity against the uncached `compute_index_series` call; existing
  `compute_index_series` coverage stays green, unchanged.
- `apps/backend/tests/test_api_indexes.py` -- routing tests: hot key served from cache; an explicit
  `range=3M` or explicit historical `as_of` bypasses the cache and is byte-identical to
  pre-iteration output.
- `apps/backend/tests/test_data_manager.py` -- new finalize-hook warm-step test, a `MemoryError`-
  isolation test mirroring
  `test_finalize_hook_forward_aggregates_memory_error_on_first_horizon_aborts_loop` (confirmed
  present at `test_data_manager.py:1654`), and an `aggregates_refreshed` test confirming
  `"index_series"` is honestly gated (present only when the warm step actually persisted a row).
- `docs/handoffs/goal-ops-hardening-iter-13-dev.md` -- new dev handoff: files changed, targeted
  test results, and an EXPLICIT plain statement of whether all three `/data` control readings and
  the `/` spot-check landed ≤1.5s (never rounding a marginal miss into "close enough").
- `reports/perf-budgets.md` -- new dated section for the post-fix control readings (browser-qa-
  agent's own three-load + spot-check pass, mirroring iter-12's G2 methodology); developer may add
  a backend-side pre-check note but the canonical browser-measured control readings are QA's.

No file under `apps/frontend/` should appear in the diff. `apps/backend/app/engine/forward_testing.py`
must be byte-unchanged (TC-12).

## UI Evolution

- New user-facing capability: none — same Dashboard (`/`) and Data Manager (`/data`) surfaces,
  same displayed values.
- New information displayed: none.
- New user actions: none.
- UI surface changes: none — only the LATENCY of an existing on-load call improves; every
  card/panel keeps its existing appearance, content, and loading/error/empty states.
- Navigation changes: none.

## Visual Requirements

- Component patterns: no new components; no frontend file is touched this iteration.
- Layout: unchanged — `/` and `/data` keep their current page layout and card order.
- Key visual effects: none introduced.
- States to handle: existing loading/error/empty states on `PhaseCrossViewCard` and
  `IndexVendorPanel` must render identically before and after — response shape is byte-identical,
  only faster on the hot key.

## Key Test Scenarios

- TC-1: with the ingest-warmed `IndexSeriesCache` row present and no concurrent ingest job running
  (confirmed via `logs/backend.log`), three independent fresh-navigation real-Chrome loads of
  `/data` each measure `GET /api/indexes?full=true` ≤1500ms, with `logs/hwmon/hwmon.csv` load1 <2.0
  at each reading's timestamp.
- TC-2: one fresh-navigation real-Chrome load of `/` (Dashboard) also measures the same call
  ≤1500ms.
- TC-3: the hot key requested twice with no intervening ingest → `series`/`asof_date`/`range`/
  `ranges` byte-identical to each other AND to a direct uncached `compute_index_series(...,
  as_of=None, range_key=cfg.index_chart.default_range, full=True)` call on the same DB state.
- TC-4: a small, bounded backfill/fetch (NOT a full-universe rebuild) lands a new bar for one
  configured `index_chart` symbol → the finalize hook invalidates the stale row → the next hot-key
  request's `series` includes the new bar's date.
- TC-5: `aggregates_refreshed` contains `"index_series"` if and only if the warm step actually
  persisted a row that run.
- TC-6: an explicit `range=3M` OR explicit historical `?as_of=` request bypasses `IndexSeriesCache`
  entirely and is byte-identical to pre-iteration output for the same inputs.
- TC-7: a `MemoryError` raised during the index-series warm step stops that step immediately, calls
  `_release_process_memory()`, never flips the ingest job's own terminal status, and
  `"index_series"` is absent from that run's `aggregates_refreshed`.
- TC-8: J-01/J-03/J-04/J-05 (required-still-passing) re-verified via deterministic golden replay
  with LLM fallback — all four recorded `passing`, none transitions to `failing`.
- TC-9: the 10 already-in-budget J-06 pages/endpoints spot-checked for regression only — each
  remains within its committed `reports/perf-budgets.md` budget.
- TC-10: targeted backend test subset (files listed above) run host-guard-confined
  (`taskset -c 0-3,8-11`, BLAS/OMP/numexpr threads=4) → zero failures beyond the pre-existing,
  documented `tests/test_db.py::test_create_all_produces_expected_tables` failure (this test is
  stale from before `ForwardAggregateCache` was added and already fails today for an unrelated
  reason; adding `IndexSeriesCache` does not newly break or fix it — do not touch it).
- TC-11: dev handoff exists, lists every changed file, and states plainly whether the three control
  readings (TC-1) and the `/` spot-check (TC-2) held budget or not.
- TC-12: `apps/backend/app/engine/forward_testing.py` byte-unchanged vs. its pre-iteration state.

## Environment Note (for the developer agent)

Before running any test or command that writes temp files:
`export TMPDIR=TMP=TEMP="/home/dennis-chan/.cache/iad/iad.goal-ops-hard-3c35d720.791787"`.
Services are expected up on backend `:8255` / frontend `:3255` shortly (operator restarting now);
if a backend restart is needed to pick up this iteration's source changes and the harness's own
restart mechanism is blocked, request it from the operator with recorded pid/timestamp rather than
attempting to start/stop the process directly.
