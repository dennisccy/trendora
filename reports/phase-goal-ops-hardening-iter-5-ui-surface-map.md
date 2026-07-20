# Phase goal-ops-hardening-iter-5 — UI Surface Map

**Phase:** goal-ops-hardening-iter-5
**Date:** 2026-07-20
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/backtest` | "Evidence by horizon" panel (backed by `GET /api/backtest`, `BacktestSkeleton` loading state unchanged) | Changed behavior | `evidence_by_horizon` now reads an ingest-time-warmed cache (`ForwardAggregateCache`) instead of recomputing `compute_forward_aggregates` 5x live on every request (measured 34.766s pre-fix); the served values are byte-identical, only latency changed | In prod mode (`scripts/start-backend.sh` + `scripts/start-frontend.sh`), open `/backtest`, watch the `BacktestSkeleton` placeholder clear, and time how long the "evidence by horizon" table takes to populate for the current as-of date — confirm well under 1 second (not up to ~35s), with the same 1/5/10/20/60-day values as before the fix |
| `/data` | `BackfillBreakdown` "Refreshed: ..." line, `data-testid="aggregates-refreshed"`, inside the **live** Job progress panel | Changed behavior | The finalize hook (`_refresh_ingest_aggregates`) now also warms the Backtest page's cache and reports it through the existing generic `aggregates_refreshed` list the frontend already renders verbatim | On `/data`, start a "Backfill snapshots" or "Fetch + backfill" job over a small date range and let it run to completion; in the live Job progress panel's "Refreshed: ..." sub-line (under "Snapshots backfilled"), confirm the text now includes "forward aggregates" as one of the comma-separated items |
| `/data` | `BackfillBreakdown` "Refreshed: ..." line inside the cross-session `LastRunSummary` card (shown when persisted run history exists but no job has started this browser session) | Changed behavior | Same `aggregates_refreshed` field, same generic renderer, different render site | After the job above completes, reload `/data` in a fresh tab/session (no job started yet this session) so the page falls back to the persisted last-run card; confirm its "Refreshed: ..." line also includes "forward aggregates" |
| `/data` | `BackfillBreakdown` "Refreshed: ..." line inside the Run History table row for a completed run | Changed behavior | Same `aggregates_refreshed` field, same generic renderer, different render site | On `/data`'s Run History table, find the row for the just-completed backfill/rebuild run and confirm its snapshots-created cell's "Refreshed: ..." sub-line includes "forward aggregates," matching the live card and last-run summary |
| `/data` | Job progress panel — overall time-to-"completed" and the "updated Ns ago" heartbeat text (no new visual element) | Changed behavior | The finalize step now performs up to 5 additional cache-warm computations (one per configured horizon, up to ~35s combined on a cold key) before a backfill/both/rebuild job reports as finished | Start a "Rebuild snapshots for current universe" job (or a backfill job) and watch the job card while it finishes — confirm the "updated Ns ago" heartbeat keeps refreshing (never appears stale/stuck) even though the job may take noticeably longer than before this iteration to reach its final status badge |

<!-- Change Type used throughout: "Changed behavior" — no new page, component, form, table, modal, or nav
     entry was added or removed this iteration; every row above is an existing UI element whose content or
     timing differs due to a backend-only code change. -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/models.py` — new `ForwardAggregateCache` STANDALONE table (mirrors `EventStudyCache`/
  `MarketPhaseCache`'s shape) — pure storage; no UI surface affected directly (its effect surfaces only via
  the `/backtest` and `/data` rows above).
- `apps/backend/app/engine/forward_testing.py` — new `forward_aggregates_cached()` cache-wrapping function;
  the underlying `compute_forward_aggregates` math itself is unchanged and remains the sole producer — no
  UI surface affected beyond the `/backtest` timing change already listed above.
- `apps/backend/app/mcp/tools.py`'s `query_backtest` — same cache-wrapper swap as `backtest.py`, but this
  function serves MCP (Model Context Protocol) clients (e.g. an external AI-assistant integration), not the
  Trendora web frontend — no web UI surface affected; not reachable from any page in `apps/frontend/`.
- `incredible_auto_dev/scripts/measure-perf.sh` (symlinked as `scripts/measure-perf.sh`) — internal
  measurement/ops tooling used by the dev pipeline, never shipped to end users — no UI surface affected.
- `reports/perf-budgets.md` — engineering measurement log; explicitly a measurement artifact and not a UI
  surface per the phase spec itself — no UI surface affected.
- `apps/backend/tests/test_forward_testing.py`, `apps/backend/tests/test_data_manager.py` — test-only
  changes — no UI surface affected.
- Measured-only this iteration, zero code change, zero behavior change for users: `/` (Dashboard),
  `/sectors`, `/themes`, `/watchlist`, and `/research/event-study` — all five were already
  snapshot-served/cached before this iteration; this pass only recorded their existing latency into
  `reports/perf-budgets.md` for the first time. Same for `/scanner-runs` — its `/api/runs` per-run
  count-query (N+1) pattern was measured (0.050–0.196s, confirmed within budget) and deliberately left
  unfixed per the dev handoff's TC-13 audit. None of these six pages' code or behavior changed.

---

## Summary

- **Frontend surfaces changed:** 0 frontend files touched (`.tsx`/`.ts` diff is empty this iteration,
  confirmed via `git status`); 2 existing pages (`/backtest`, `/data`) nonetheless show a user-visible
  effect purely from backend-only code changes flowing through pre-existing generic UI elements
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 6 files/tooling items with zero UI impact, plus 6 pages that were measured for
  the first time this iteration but had zero code change and zero behavior change
