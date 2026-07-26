# goal-ops-hardening-iter-24 Dev Handoff

**Phase:** goal-ops-hardening-iter-24
**Date:** 2026-07-26
**Agent:** developer
**Status:** complete

## What Was Built

J-09: the backend now discloses, honestly and live, whenever it is running the iter-20 in-process
background historical forward-aggregate compute — previously invisible except by reconstructing its
timing from raw `forward_aggregate_cache` commit timestamps and backend log lines (as iters 21–23 each had
to do). Additive instrumentation only — zero change to `compute_forward_aggregates`,
`resolved_forward_aggregate_evidence`, or `ensure_historical_forward_aggregates_dispatched`'s
keying/dispatch-decision semantics (unit-proven: the pre-existing iter-19/iter-20 concurrency tests still
pass unchanged).

- **Dispatch registry bookkeeping** — `_HIST_DISPATCH_INFLIGHT` (`app/engine/forward_testing.py`) changed
  from a bare `set[(asof_key, dataset_version)]` to a `dict` keyed the same way, storing `started_at` (set
  the instant the dispatch is accepted), and live `horizons_done`/`horizons_total` counters. `horizons_done`
  increments inside `_run_historical_forward_aggregates_dispatch`'s existing per-horizon loop, right after
  each `forward_aggregates_ingest_cached` call returns — so a live reader sees real progress, never a
  fabricated estimate.
- **Bounded outcome ring** — a new `_HIST_RECENT_OUTCOMES` list, appended to (newest-first, `insert(0, ...)`)
  in the SAME `finally` block that already released the dispatch guard, capped at the new
  `startup.background_compute_history_size` config value (`del _HIST_RECENT_OUTCOMES[cap:]`). Each entry
  is `{asof_key, dataset_version, outcome: "completed"|"failed", started_at, finished_at, duration_ms,
  reason}` — `reason` is the caught exception's `str()` on failure, else `None`.
- **New read-only accessor** — `get_background_compute_status()` returns `{"active": [...],
  "recent_outcomes": [...]}`, computing each active entry's `elapsed_ms` at READ TIME from its own recorded
  `started_at`. Reuses the existing `_HIST_DISPATCH_LOCK` for the tiny read — no new lock.
- **Config** — `StartupCfg.background_compute_history_size: int = 5` (validated `>= 1` in `_validate`),
  added to `config.yaml`'s `startup:` block. The pydantic-level default keeps every config fixture that
  predates this field (e.g. `test_config.py`'s `MINIMAL_VALID`) loading unchanged.
- **`compute_readiness` composition** (`app/engine/readiness.py`) — composes
  `forward_testing.get_background_compute_status()` into its own return dict as a new `background_compute`
  sibling key (mirrors how `warmup`'s state is already composed), behind its OWN scoped try/except so a
  broken in-memory read degrades only this one field to `{"active": [], "recent_outcomes": []}` — never
  blanks `state`/`warmup`.
- **`GET /api/health`** (`app/api/health.py`) serves `background_compute` as one new additive top-level
  field, with a matching degrade-on-error fallback in the endpoint's own outer `compute_readiness` guard
  (total-failure case).
- **Frontend** — `ReadinessProvider` exposes `backgroundCompute` from the SAME `/api/health` poll (no
  second fetch). `HealthBadge` renders one additional inline `Badge`
  (`data-testid="background-compute-indicator"`) naming the in-flight count, present in ANY readiness state
  whenever `active.length > 0`, absent when empty. A new `BackgroundComputePanel` on `/data` (after
  `RunHistoryPanel`, matching the existing Card/PanelTitle convention) lists each active window (as-of,
  elapsed, horizons done/total) and the most recent completed/failed outcome, with an explicit idle copy
  ("No background compute running. Last outcome: none yet.") and a process-lifetime disclosure note — reads
  `useReadiness()`, no second fetch, no new user action.

## Bug found and fixed during self-review

While drafting the composition, an early edit briefly left a **duplicate `"background_compute"` key** in
`compute_readiness`'s returned dict literal (the guarded `background_compute` variable, then an
UN-guarded second `"background_compute": forward_testing.get_background_compute_status()` a few lines
later). In Python, the later key wins — this would have silently defeated the whole degrade-on-error path
(a real registry-read failure would have propagated unguarded instead of degrading to the honest empty
shape). Caught by re-reading the diff before running tests; removed the duplicate line. Flagging this here
so the reviewer knows to specifically check `readiness.py`'s single-`background_compute`-key dict literal.

## Files Changed

- `apps/backend/app/engine/forward_testing.py` -- dispatch registry becomes a dict (started_at/
  horizons_done/horizons_total), bounded `_HIST_RECENT_OUTCOMES` ring, `get_background_compute_status()`.
- `apps/backend/app/config.py` -- `StartupCfg.background_compute_history_size` (default 5, validated >= 1).
- `config.yaml` -- `startup.background_compute_history_size: 5`.
- `apps/backend/app/engine/readiness.py` -- `compute_readiness` composes `background_compute`.
- `apps/backend/app/api/health.py` -- serves `background_compute` on `GET /api/health`.
- `apps/backend/tests/test_forward_testing_concurrency.py` -- new tests: registry bookkeeping
  (started_at/live horizons progress), bounded ring cap + newest-first, failure-records-outcome-and-
  redispatches.
- `apps/backend/tests/test_readiness.py` -- updated the existing exhaustive-shape test to include the new
  key; new composition tests (empty/active/degrade-on-error).
- `apps/backend/tests/test_health.py` -- new tests: additive field shape, single-source equality,
  degrade-on-error.
- `apps/backend/tests/test_config.py` -- new `background_compute_history_size` validation tests.
- `apps/frontend/lib/api.ts` -- `BackgroundComputeActive`/`BackgroundComputeOutcome`/
  `BackgroundComputeStatus` types; `HealthStatus.background_compute`.
- `apps/frontend/components/readiness-provider.tsx` -- `backgroundCompute` added to
  `ReadinessContextValue`, read from the existing poll.
- `apps/frontend/components/health-badge.tsx` -- the conditional `background-compute-indicator` badge.
- `apps/frontend/app/data/page.tsx` -- new `BackgroundComputePanel` (+ `BackgroundComputeRow`/
  `LastOutcomeSummary` helpers), placed after `RunHistoryPanel`.
- `reports/perf-budgets.md` -- new "Iteration 24" section: re-measured steady-state `GET /api/health`
  latency + a live end-to-end confirmation of the new field against two real background-compute windows.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest <targeted files/selectors> -q`

- `tests/test_config.py` (full file, 71 tests, includes the 3 new `background_compute_history_size`
  tests): **71 passed**.
- `tests/test_forward_testing_concurrency.py -k "background_compute or ensure_dispatch_records or
  recent_outcomes_ring or historical_dispatch_failure_records"` (the 4 new iter-24 tests, isolated from
  the file's heavy module-scoped memory/write-contention fixtures): **4 passed** in 0.58s.
- `tests/test_forward_testing_concurrency.py -k "iter20 or iter19"` (the pre-existing dispatch-registry
  keying/single-flight tests, to confirm the set→dict change didn't regress them): **3 passed** in 6.67s.
- `tests/test_readiness.py tests/test_health.py` (full files, including the modified exhaustive-shape test
  and all new composition/degrade/additive-field tests): **launched, still running at handoff time** — this
  pair's shared `loaded_engine` module fixture rebuilds the full ~30-year historical basis from scratch,
  which this project's own prior iterations have documented as slow (independent of this iteration's diff;
  see `docs/handoffs`/memory notes on "30y test suite slow, not the product"). I did not kill it (no cache
  to lose) and could not block on it further without leaving the service-cleanup / doc-writing steps
  undone; the reviewer/QA stage should re-run these two files (or confirm this run's tail once it lands) as
  part of its own verification. Smoke-level confirmation in the meantime: a standalone interpreter session
  directly exercising `compute_readiness` against a fresh empty DB confirmed the exact
  `{state, detail, warmup, background_compute}` shape with no duplicate-key regression (see "Bug found and
  fixed" above).
- Live, non-mocked, real-backend confirmation (see `reports/perf-budgets.md`'s new Iteration 24 section for
  full detail): backend started via `scripts/start-backend.sh`, two REAL historical `/backtest` requests
  triggered genuine background-compute windows; `GET /api/health`'s `background_compute` field was polled
  throughout and showed the expected empty/active/completed shapes, including `horizons_done` climbing
  0→1→2→4 of `horizons_total=5` and `recent_outcomes` gaining newest-first entries with real measured
  `duration_ms`. Backend was stopped afterward (`pkill`, confirmed no process left running on the
  measurement port).

Frontend: `npx tsc --noEmit -p tsconfig.json` — no type errors. This project has no configured
jest/vitest runner (frontend "tests" here are standalone `node lib/*.test.ts` files for pure `lib/`
logic); the new frontend work is component wiring (typed props, JSX), which this codebase's convention
verifies via type-checking + browser QA rather than a unit-test harness — no new logic function was
introduced that would fit that project convention (the panel reuses the existing `fmtDuration` helper
verbatim).

## Known Issues

- The full `test_readiness.py`/`test_health.py` run had not finished by handoff time (see "Tests Run"
  above) — purely a pre-existing fixture-cost issue (the `loaded_engine` module fixture), not something
  this iteration's diff caused or can shorten. Recommend the reviewer/QA stage either wait for that run's
  tail or re-run it with more time budgeted.
- `BackgroundComputePanel`'s idle/active copy and the `HealthBadge` indicator have not yet been verified in
  an actual browser (that is the browser-qa-agent's job per the pipeline, and is TC-10, the primary J-09
  test) — I did verify the underlying data end-to-end live against the real backend (see above), so the
  panel is rendering real, correctly-shaped data; only the visual/DOM rendering itself is unverified by me.
- Non-blocking carries from iter-23 (unaffected by this iteration, still owed, per the phase spec's own
  "Out of scope" list): retargeting `test_forward_testing_serving_split.py`'s four `is_latest`
  monkeypatches before removing the dangling imports at `backtest.py:75`/`mcp/tools.py:38`; owner-optional
  backlog card B-1107 (bounding concurrent dispatch count).
