# Iteration 73 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-73
**Date:** 2026-08-13
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Summary of what this iteration touched

Confirmed via `git diff ae17fdf7...` (production-code path, lockfile/harness noise excluded) and the
matching `--stat` of the excluded paths:

- **Production/test code:** exactly one file, `apps/backend/tests/test_start_backend_script.py`
  (+278/-4). All additions are test infrastructure: a new opt-in heavy test
  `test_start_backend_forward_aggregate_warm_under_realistic_pool_pressure` (marked
  `xfail(strict=False)` — the live drill hit host-contention 503s and never reached a clean
  end-to-end completion, disclosed honestly in the addendum rather than forced), a
  `_HealthPoller.interval` parameter (defaults to the pre-existing 2s cadence — no sibling test's
  behavior changes), and load-generation helpers (`_pool_pressure_worker`,
  `_poll_job_to_terminal_resilient`) that issue plain `GET` requests against six already-existing
  endpoints (`/api/backtest`, `/api/watchlist`, `/api/sectors`, `/api/themes`, `/api/stocks`,
  `/api/data/availability`) purely to hold pooled DB connections open — they do not compute or
  display anything themselves.
- **No `config.yaml` change** — `git diff ae17fdf7... -- config.yaml` is empty (excluded-path stat
  also confirms zero `scripts/`/`project-extensions/` diff), matching the addendum's own account:
  TC-1's drill never reached a completed measurement, so neither TC-2 nor TC-3 fired and
  `pool_size`/`max_overflow`/`pragmas.cache_size` stayed byte-unchanged.
- **`reports/perf-budgets.md`** gained Addendum 38 — the measurement artifact already registered in
  the blueprint's Data Contract as "N/A — a measurement artifact, not a served runtime value."
- **`runs/goal-session-ops-hardening/state/blueprint.md`** gained exactly the two additive edits the
  spec's NOTES promised: a top-of-file "iter-73 update" narrative paragraph, and one sentence
  appended to the "Page performance budgets" row's Notes column. No Data Contract row's computing
  module or serving endpoint changed; no Information Architecture row changed.
- No `apps/frontend/**` file appears anywhere in the diff (`Frontend Present: no` in the iter spec,
  no ui-surface-map report was produced — consistent with zero frontend surface change).

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Page performance budgets (measurement artifact) | OK | `reports/perf-budgets.md` (Addendum 38 appended, same file, same "not a served value" status) |
| Backtest / Watchlist / Sectors / Themes / Stocks / Data availability (values the new load-generator hits) | OK — read-only, unmodified endpoints, no client-side recompute | `apps/backend/tests/test_start_backend_script.py:127-134` (`_POOL_PRESSURE_ENDPOINTS`, plain GETs against already-registered endpoints for load only, not display) |
| Job history / `aggregates_refreshed` (finalize-hook warm) | OK — same `rebuild` job path and `_expected_aggregate_categories` assertion the sibling iter-8 test already uses | `apps/backend/tests/test_start_backend_script.py:220-305` |
| `GET /api/health` readiness | OK — same route/instrument, only poll cadence parameterized | `apps/backend/tests/test_start_backend_script.py:642-663` (`_HealthPoller.__init__`) |

No new function computes a registered value by a second path; no new UI surface fetches a
registered value from a non-canonical endpoint (no UI surface was added at all this iteration).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route/feature this iteration) | OK — n/a | Confirmed via diff stat: zero files under `apps/frontend/**` changed; iter spec's "UI surface changes: None" / "Blueprint conformance: No new page or nav entry" holds |

J-07 keeps its existing homes (global readiness badge + `/backtest`) per the blueprint; nothing in
this iteration adds, moves, or duplicates a page.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The iteration's headline goal (a fresh, complete VmPeak measurement under realistic pool pressure)
  was not achieved — the new test is `xfail(strict=False)` and J-07 step 3 stays `partial`. This is
  a goal-achievement/evidence question for the goal-evaluator, not a coherence violation: no
  duplicate computation, no non-canonical source, and no IA drift was introduced while reaching that
  outcome. The addendum names concrete next-round options (quieter host window, phase-level timers,
  or accepting the pressure-free figure as interim) rather than silently re-carrying stale iter-32/
  iter-38 numbers, so it is on record for the decomposer to act on.
- Process-hygiene note disclosed in the addendum (an over-broad `pkill -f` killed the drill's own
  live backend mid-measurement) is operational, not a coherence issue — no code or data-contract
  surface was affected.
