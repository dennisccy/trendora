# goal-ops-hardening-iter-24 Execution Plan

## What to Build

Disclose the existing iter-20 in-process background historical forward-aggregate dispatch
(`_HIST_DISPATCH_LOCK` / `_HIST_DISPATCH_INFLIGHT` in `app.engine.forward_testing`) so operators can see
it live instead of reconstructing its timing from raw DB timestamps (J-09, the sole non-passing journey;
J-01/J-03/J-04/J-05/J-06/J-07/J-08 stay green, unaffected). Additive instrumentation only — zero change to
`compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, or the dispatch's keying/single-flight
semantics.

- Extend the dispatch registry to record, per in-flight `(asof_key, dataset_version)`: `started_at` (UTC,
  set at dispatch time) and live `horizons_done`/`horizons_total` counters (incremented as each configured
  horizon's `forward_aggregates_ingest_cached` call completes inside the existing background worker).
- On worker completion (success or caught exception, in the existing `finally`), append one newest-first
  outcome record to a bounded in-process ring — `{asof_key, dataset_version, outcome, started_at,
  finished_at, duration_ms, reason}` — capped at a new config value, never a hardcoded literal.
- Add one new read-only accessor, `get_background_compute_status()`, returning
  `{"active": [...], "recent_outcomes": [...]}` — no new lock beyond the existing `_HIST_DISPATCH_LOCK`.
- Add `startup.background_compute_history_size: int` (>= 1, default 5) to `config.yaml` + `StartupCfg`.
- `app.engine.readiness.compute_readiness` composes the accessor's output into its returned dict as a new
  `background_compute` sibling key (same pattern it already uses for `app.engine.warmup`'s state) — no DB
  read added.
- `GET /api/health` serves `background_compute` as one new additive top-level field, degrading to
  `{"active": [], "recent_outcomes": []}` on any compute error (mirrors the existing readiness/preflight
  degrade-on-error convention).
- Frontend: `ReadinessProvider` reads `background_compute` from the SAME existing `/api/health` poll (no
  second fetch); `HealthBadge` renders one additional inline element
  (`data-testid="background-compute-indicator"`) alongside the existing pill whenever
  `background_compute.active.length > 0`, in ANY readiness state, absent when empty; a new
  `BackgroundComputePanel` on `/data` lists active windows (as-of, elapsed, horizons done/total) and the
  most recent completed/failed outcome (duration, failure reason), with an explicit idle copy and a
  process-lifetime disclosure note, reading `useReadiness()` (no second fetch).
- Re-measure steady-state `GET /api/health` latency and record it in `reports/perf-budgets.md`'s
  Iteration 24 section — must stay within the UNCHANGED `<= 0.1s` budget (zero DB work added by this
  field).
- Unit/integration coverage: registry bookkeeping (started_at/horizons_done/horizons_total), bounded
  `recent_outcomes` ring behavior (config-driven cap, newest-first), `get_background_compute_status()`
  shapes (empty/active/failed), `compute_readiness` composition, `GET /api/health` degrade-on-error path,
  `StartupCfg` validation of the new field, and a simulated dispatch-worker-exception path proving the
  in-flight slot is released and the same identity can re-dispatch (mirrors the existing TC-7 contract).
- Dev handoff at `docs/handoffs/goal-ops-hardening-iter-24-dev.md`.

**Out of scope (per phase spec — do not implement):** bounding concurrent dispatch count (backlog B-1107);
any change to `compute_forward_aggregates` / `resolved_forward_aggregate_evidence` / the dispatch's
keying/single-flight semantics or any served evidence value; amending the `<=1.5s`/`<=0.1s` budgets or BCW
ceilings (settled owner policy); re-running TC-13/TC-14; retargeting
`test_forward_testing_serving_split.py`'s `is_latest` monkeypatches or removing the dangling imports at
`backtest.py:75`/`mcp/tools.py:38`; fabricated finish-time estimates or completion percentages; persisting
background-compute history across a restart (must stay in-memory, process-lifetime, honestly scoped as
such); any new nav entry or route.

## Agents Required
- backend-data: yes -- dispatch-registry bookkeeping, `get_background_compute_status()`, config addition,
  `compute_readiness` composition, `GET /api/health` field, unit tests, perf-budgets re-measurement.
- frontend-ux: yes -- `ReadinessProvider`/`HealthBadge` field plumbing + the new `BackgroundComputePanel`
  on `/data`, plus a browser-verifiable walkthrough of a real background-compute window.

Frontend Present: yes

## Files to Create/Modify

Backend:
- `apps/backend/app/engine/forward_testing.py` -- extend `_HIST_DISPATCH_INFLIGHT` (set -> dict keyed by
  `(asof_key, dataset_version)` storing `started_at`/`horizons_done`/`horizons_total`), increment
  `horizons_done` inside `_run_historical_forward_aggregates_dispatch`'s per-horizon loop, append to a new
  bounded `_HIST_RECENT_OUTCOMES` ring (config-capped) in the existing `finally` block, add
  `get_background_compute_status()`. `_HIST_DISPATCH_LOCK` stays the only lock; keying/dispatch-decision
  logic in `ensure_historical_forward_aggregates_dispatched` is unchanged.
- `apps/backend/app/config.py` -- `StartupCfg` gains `background_compute_history_size: int` (validated
  `>= 1`, default `5`), following the existing field-validation pattern in `_validate`.
- `config.yaml` -- add `startup.background_compute_history_size: 5` beside the existing `startup:` block.
- `apps/backend/app/engine/readiness.py` -- `compute_readiness` composes
  `forward_testing.get_background_compute_status()`'s output into its returned dict as the new
  `background_compute` key (deferred import to avoid a cycle, mirroring the existing
  `forward_testing._dataset_version` deferred-import precedent in that same module).
- `apps/backend/app/api/health.py` -- serve `background_compute` as one new top-level field in the
  response dict; wrap the read in the same try/except degrade-on-error convention used for
  `readiness`/`preflight`.
- `apps/backend/tests/test_forward_testing_concurrency.py` (or a new adjacent test module) -- new tests
  for `started_at`/`horizons_done`/`horizons_total` bookkeeping, the bounded `recent_outcomes` ring, and
  the failure-releases-guard-and-redispatches contract.
- `apps/backend/tests/test_readiness.py` -- `compute_readiness` composition test (empty/active shapes).
- `apps/backend/tests/test_health.py` -- `GET /api/health` serves `background_compute`, including its
  degrade-on-error shape.
- `apps/backend/tests/test_config.py` -- `StartupCfg.background_compute_history_size` validation
  (`>= 1`, default `5`).

Frontend:
- `apps/frontend/lib/api.ts` -- new `BackgroundComputeActive`/`BackgroundComputeOutcome`/
  `BackgroundComputeStatus` types; `background_compute` added to `HealthStatus`.
- `apps/frontend/components/readiness-provider.tsx` -- `ReadinessContextValue` gains `backgroundCompute`,
  read from the SAME `fetchHealth()` poll (no second fetch/poll).
- `apps/frontend/components/health-badge.tsx` -- one additional inline element,
  `data-testid="background-compute-indicator"`, rendered alongside the existing pill whenever
  `backgroundCompute.active.length > 0` in ANY readiness state; absent when empty.
- `apps/frontend/app/data/page.tsx` -- new `BackgroundComputePanel` component (Card/PanelTitle/
  `data-testid="background-compute-panel"` convention, matching `JobProgressPanel`/`RunHistoryPanel`),
  placed alongside those existing panels; reads `useReadiness()`.

Docs/reports:
- `reports/perf-budgets.md` -- new "Iteration 24" section: re-measured steady-state `GET /api/health`
  latency, confirmed within the unchanged `<= 0.1s` budget.
- `docs/handoffs/goal-ops-hardening-iter-24-dev.md` -- dev handoff (required).

## UI Evolution

- New user-facing capability: any operator, on any page, can see live whether the backend is currently
  running a background historical-evidence compute, and on `/data` see full detail (which as-of date(s),
  horizon progress, and the most recent outcome) without reading logs or querying the DB.
- New information displayed: top-bar "background compute running (N)" indicator (all pages, conditional);
  `/data` panel listing in-flight windows (as-of, elapsed, horizons done/total) and recent
  completed/failed outcomes (duration, failure reason).
- New user actions: none -- this is a read-only disclosure surface (no new buttons/forms/controls).
- UI surface changes: `HealthBadge` (every page) gains one conditional inline child; `/data` gains one new
  panel (`BackgroundComputePanel`) beside the existing `JobProgressPanel`/`RunHistoryPanel`.
- Navigation changes: none -- no new nav entry or route; lives entirely under the existing global badge +
  `/data` home.

## Visual Requirements

- Component patterns: reuse `Badge` (existing variants) for the badge indicator; reuse `Card` +
  `PanelTitle` (the exact convention `JobProgressPanel`/`RunHistoryPanel`/`StorageCapacityPanel` already
  use) for `BackgroundComputePanel` -- no new component primitives introduced.
- Layout: `BackgroundComputePanel` sits in the existing `/data` panel stack (after
  `JobProgressPanel`/`RunHistoryPanel`, following the page's existing vertical panel flow) -- no new page
  layout or grid structure.
- Key visual effects: none new -- match the existing calm, factual badge/panel styling already used for
  readiness/warmup/preflight (no hype language, no color escalation beyond the existing warn/accent
  vocabulary if used for an active-compute hint).
- States to handle: empty/idle (`active` empty -- explicit "No background compute running. Last outcome:
  none yet." or the most recent entry, plus the process-lifetime disclosure note), active (>=1 in-flight
  window, elapsed + horizons done/total), and failed-outcome (duration + non-null reason string) -- all
  read directly from the shared readiness poll, never a second fetch or client-side derivation.

## Key Test Scenarios

- TC-1: warm backend at rest, no dispatch ever triggered -> `GET /api/health` returns
  `background_compute.active == []` and `recent_outcomes == []`, `readiness == "ready"`.
- TC-2/TC-3: a `/backtest` (or MCP `query_backtest`) request for a historical as-of not yet `"ready"` for
  the current `dataset_version` returns within J-08's unchanged budget while the registry gains one
  `active` entry (`horizons_total == len(cfg.walk_forward.horizons)`, `horizons_done == 0` initially,
  `0 <= horizons_done < horizons_total` during the window, `started_at` matching within 1s); the top bar
  (any page) shows `data-testid="background-compute-indicator"` naming the in-flight count.
- TC-4: `/data` open during the same window -> `BackgroundComputePanel` displays the as-of key, an
  elapsed-time value > 0, and the live `horizons_done`/`horizons_total` pair.
- TC-5: dispatch completes -> `active` no longer contains the identity; `recent_outcomes[0]` shows
  `outcome == "completed"`, a `finished_at` timestamp, `duration_ms >= 0`, consistent (within 2s) with the
  corresponding `forward_aggregate_cache` row's `created_at`.
- TC-6: a test-injected exception in one horizon's compute -> `recent_outcomes[0]` shows
  `outcome == "failed"` with a non-null `reason`, the `active` slot is released, and a subsequent request
  for the SAME identity re-dispatches (no permanent wedge).
- TC-7: steady-state `GET /api/health` (no background compute in flight) max latency `<= 0.1s` over the
  existing repeated-poll harness, recorded in `reports/perf-budgets.md`'s Iteration 24 section.
- TC-8: backend restart -> `background_compute.active == []` and `recent_outcomes == []` (in-memory state
  cleared); the `/data` panel's copy states the history is since the last restart, not a fabricated empty
  history.
- TC-9: more than `startup.background_compute_history_size` dispatches complete since boot ->
  `len(recent_outcomes) <= background_compute_history_size`, newest entry first.
- TC-10 (browser, primary J-09 test): trigger exactly one real background-compute window by loading
  `/backtest` for a historical as-of not yet complete for the current `dataset_version`; assert the badge
  indicator is present during the window and absent after completion, and the `/data` panel's
  `recent_outcomes` gains a new entry with a real measured `duration_ms`. If a real BCW cannot be
  reliably triggered deterministically in the browser-QA window, a narrow test-only hook may force-dispatch
  one historical as-of on demand, calling the SAME `ensure_historical_forward_aggregates_dispatched`
  function unchanged (never a second dispatch path).
- Regression smoke (deterministic replay): J-01, J-03, J-04, J-05, J-06, J-07, J-08 all stay green --
  unaffected by this additive-only change.
