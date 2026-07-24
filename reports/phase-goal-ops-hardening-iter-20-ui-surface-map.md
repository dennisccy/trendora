# Phase goal-ops-hardening-iter-20 — UI Surface Map

**Phase:** goal-ops-hardening-iter-20
**Date:** 2026-07-24
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

All changes this iteration land on the single existing `/backtest` page (reached via the pre-existing,
unchanged "Backtest" sidebar link — `apps/frontend/components/sidebar.tsx`, untouched this iteration) — no
new page, panel, route, or nav entry was added. The one frontend edit (`apps/frontend/app/backtest/page.tsx`)
is a pure copy branch on the already-fetched `backtest.is_latest` field (no new API field, fetch, or
component). The response-time behavior change is driven by two backend files whose output this same page
already consumes: `apps/backend/app/engine/forward_testing.py`'s new single-flight background-dispatch
function, and `apps/backend/app/api/backtest.py`'s historical branch, called directly by
`apps/frontend/lib/api.ts`'s `fetchBacktest`.

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/backtest` | Page response time for a first-ever view of a historical as-of (the page's own load behavior; no dedicated component) | Changed behavior | The historical branch of `GET /api/backtest` no longer computes forward-aggregate evidence synchronously on the request thread (`ensure_loop_ms` dropped from 9288–54281 ms to ~1.67 ms, `reports/perf-budgets.md` "Iteration 20"); it now dispatches a single-flight-guarded background compute keyed on `(asof_key, dataset_version)` and returns immediately with whatever evidence already exists. | Restart the backend (`scripts/start-backend.sh`) or pick a historical `as_of` date confirmed never viewed since the last restart/ingest, then navigate to `/backtest?as_of=<that date>` and time the page: it should finish loading in well under a second and show either the `RefreshingEvidenceBanner` or the "Backtest evidence not yet computed" empty state — never a blank tab that sits unresponsive for several seconds or longer. |
| `/backtest` | `RefreshingEvidenceBanner` | Changed behavior (copy branches on `is_latest`) | TC-8: the banner's cause/reload sentences were written only for the latest-view, ingest-triggered case; a historical view can now ALSO be `"refreshing"` because viewing it just triggered its own background compute, which the old copy misdescribed as an ingest/dataset change. | Load `/backtest` for a historical date whose `evidence_status` is `"refreshing"` (e.g. one resolving to an older complete fallback while its own evidence warms) and confirm the banner reads "This date's own evidence is being computed in the background (started by viewing this page)... Reload this page shortly to pick up this date's own evidence...". Separately, load the default (latest/today) date while ITS evidence is `"refreshing"` and confirm that view still reads "The dataset has changed... reload after the next ingest finishes..." unchanged. |
| `/backtest` | `EmptyState` (title "Backtest evidence not yet computed") | Changed behavior (copy branches on `is_latest`) | TC-9: the empty-state description credited only "backfilling or fetching data" with starting a compute; for a historical view, viewing the page itself now also does, which the old copy omitted. | Navigate to `/backtest?as_of=<a historical date with no complete evidence at or before it anywhere in the store>` and confirm the empty state's description reads "...Viewing this page has started computing it in the background — reload shortly to see it...". Reload the same URL again after roughly 30 seconds and confirm the empty state is gone, replaced by populated per-horizon evidence (`evidence_status: "ready"`). |
| `/backtest` | Page behavior during an in-flight background compute (a residual, cross-request effect; no dedicated component) | Changed behavior (partial improvement, documented residual) | The background compute runs in-process; per `reports/perf-budgets.md` ("Iteration 20"), other requests issued concurrently during its ~30 s run can see transient latency (3.0–6.3 s for `/backtest`, up to 1.60 s for `/api/health`) from resource contention — much improved from the old 9.6–54 s block but not fully eliminated. | Trigger a historical first-view to start a background compute, then within the next ~30 seconds load `/backtest` again in a second tab (any as-of) and separately poll `GET /api/health`. Confirm both still respond (not hung, not erroring) and `GET /api/health` stays HTTP 200 with `readiness: "ready"` on every poll, even if the second `/backtest` load takes a few seconds longer than its normal sub-second response. |

<!-- Change Type options: New page | New component | Updated layout | Added navigation | Changed behavior | Removed element | New form | New table | New modal -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/forward_testing.py` — new `ensure_historical_forward_aggregates_dispatched`
  function, its single-flight guard (`_HIST_DISPATCH_LOCK`/`_HIST_DISPATCH_INFLIGHT`), and the background
  worker thread — the mechanism that makes the `/backtest` behavior change above possible, but not itself a
  rendered surface; no UI file, no template, no response shape change. `compute_forward_aggregates` and
  `resolved_forward_aggregate_evidence`'s own logic are byte-unchanged.
- `apps/backend/app/mcp/tools.py` — `query_backtest` mirrors the identical dispatch fix for MCP/agent-tool
  consumers — a separate, non-browser integration channel not called by this Next.js frontend
  (`lib/api.ts` calls `GET /api/backtest` directly, never this MCP tool) — no browser page or route is
  affected (see "Not Visible Yet" in the companion user-visible-changes report for the distinction from a
  genuine gap).
- `apps/backend/tests/test_forward_testing_serving_split.py` — 2 existing tests updated to poll for
  background-dispatch completion instead of asserting synchronous same-call readiness — test coverage only,
  no UI surface.
- `apps/backend/tests/test_forward_testing_concurrency.py` — 2 new tests (dispatch-once-under-concurrency,
  dispatch-owner-failure recovery) — test coverage only, no UI surface.
- `apps/backend/tests/test_api_backtest.py` — one test
  (`test_backtest_evidence_is_as_of_scoped_expanding_window`) updated the same way; edited but not executed
  this session (its `loaded_engine` fixture takes ~80 minutes to build, out of scope per the phase spec) —
  test coverage only, no UI surface.
- `reports/perf-budgets.md` — new dated "Iteration 20" section recording the before/after latency
  measurements and the honest residual — a project/ops report consumed by the evaluator and future
  iterations, never rendered in the application itself.

---

## Summary

- **Frontend surfaces changed:** 1 (`/backtest` — its evidence-section copy plus the page's own
  response-time behavior; no other page touched)
- **New pages/routes:** 0
- **Modified components:** 2 (`RefreshingEvidenceBanner`, the `not_yet_computed` `EmptyState`'s copy) — both
  gain an `is_latest`-based text branch; no new component was created
- **Navigation changes:** no
- **Backend-only changes:** 6 (`forward_testing.py`'s new dispatch mechanism, `mcp/tools.py`, 3 backend test
  files, `perf-budgets.md`)
