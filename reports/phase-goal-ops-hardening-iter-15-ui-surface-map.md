# Phase goal-ops-hardening-iter-15 — UI Surface Map

**Phase:** goal-ops-hardening-iter-15
**Date:** 2026-07-23
**Written by:** ui-impact-analyst

---

## Context: no frontend files changed, but one existing surface is behaviorally affected

Zero files under `apps/frontend/` appear in this iteration's diff (confirmed via `git status`). The only
product/test files touched are `apps/backend/app/engine/forward_testing.py` (modified — added a
single-flight de-duplication guard to `forward_aggregates_cached`'s cache-miss path only) and
`apps/backend/tests/test_forward_testing_concurrency.py` (modified — three new tests added).
`reports/perf-budgets.md` (modified) and `runs/goal-session-ops-hardening/state/blueprint.md` (modified)
are reporting/pipeline-state artifacts, not in-product pages. `apps/backend/app/db.py` was considered
(per the plan's conditional scope) but **not** touched — see "Backend-Only Changes" below.

The changed function, `forward_aggregates_cached`, is the sole computing wrapper behind `GET
/api/backtest` (unchanged, byte-identical file — confirmed absent from the diff) and is called by
`apps/frontend/lib/api.ts`'s `fetchBacktest`, which the unchanged `/backtest` page
(`apps/frontend/app/backtest/page.tsx`) invokes. Because this iteration's entire purpose is closing a
concurrency/latency defect on that existing, already-consumed endpoint, the row below captures the
resulting behavior change on that surface, per this dispatch's operator note not to suppress this report
on account of `Frontend Present: no`.

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/backtest` | Per-horizon evidence panel — the `by_horizon` scorecard table, return-attribution lists, `BacktestSkeleton` loading state, and "Backend unavailable" error card (`apps/frontend/app/backtest/page.tsx`; fetched via `fetchBacktest`, `apps/frontend/lib/api.ts:1094`, calling `GET /api/backtest`) | Changed behavior (concurrency/reliability only — `GET /api/backtest`'s response CONTENT is proven byte-identical; only its behavior when multiple requests target the same not-yet-cached horizon/date changes) | The page's fetch resolves through `forward_aggregates_cached` (`apps/backend/app/engine/forward_testing.py`), which this iteration changed from "every concurrent cache-miss on the same key redundantly recomputes" to "the first caller computes, every other concurrent caller for that SAME key waits (bounded, 45s) and reuses its answer" — closing the compounding/pile-up mechanism behind iter-14's 211.8s UT-04 finding. A LONE first-ever cache-miss (nothing else already computing the same key) is unaffected — same cost as before, confirmed still ~178.7s on the live deep-basis data. | Ask the operator to start a backfill/rebuild job on `/data` that changes the latest run's forward-return data for the current as-of date (invalidating `ForwardAggregateCache` for that date). While that job's background warm loop is actively computing forward aggregates (visible via the job's live progress on `/data`), open `/backtest` for that SAME as-of date in 2 or more concurrent browser tabs/requests. Expected results: (1) all requests eventually resolve — none hangs past roughly 45 seconds waiting on another; (2) the by-horizon scorecard numbers are identical across every tab (proving no duplicate/conflicting computation happened); (3) if this is the FIRST time this exact date has been requested this session, expect the load to still take on the order of minutes — this is the known, not-yet-closed residual cost, not a new regression; (4) watch the Network tab's `GET /api/backtest` timings for any additional isolated slow call (>1.5s) after the first one resolves — a single unexplained ~5.4-second spike was observed once during this iteration's own live measurement and remains open/uninvestigated. |

<!-- Change Type key used above: Changed behavior -->

---

## Additional Pages Spot-Checked Under the Same Concurrent Load (No Code Change This Iteration)

These four pages were exercised during the SAME live full-scale pass as the `/backtest` row above (per
the phase spec's TC-5 requirement), but none of their own backend call paths were touched by this
iteration's diff — they are regression/robustness spot-checks, not behavior changes, and are listed
separately from the required table above so "spot-checked" is never conflated with "changed."

| Route / Page | Backend call (frontend function → endpoint) | What this iteration's live pass found | What to test |
|-------------|--------------------------------------------|----------------------------------------|-------------|
| `/stocks` | `fetchStocks` → `GET /api/stocks?limit=50` | Operator-reported 0.09–0.10s during the concurrent warm; not independently re-verified from a raw log this pass (no CSV was captured for this ad hoc check) | Reload `/stocks` while a backfill's warm loop is running (same concurrent-warm setup as the `/backtest` row above) and confirm the stock table renders fully — not blank, not frozen — within a couple of seconds. |
| `/sectors` | `fetchSectors` → `GET /api/sectors` | Operator-reported 0.004–0.006s during the concurrent warm; not independently re-verified from a raw log this pass | Reload `/sectors` under the same concurrent warm and confirm the sector table renders fully — not blank, not frozen — within a couple of seconds. |
| `/scanner-runs` | `fetchRuns` / `fetchRun` → `GET /api/runs` / `GET /api/runs/{run_id}` (**not** `/api/scanner-runs` — that path does not exist in the backend) | The operator's ad hoc probe hit a guessed, nonexistent path (`/api/scanner-runs`) and got a 404; this pass confirmed by reading the backend's actual API modules that no such route has ever existed, and that the real `/scanner-runs` page correctly calls `GET /api/runs`/`GET /api/runs/{run_id}` instead — the 404 is a wrong manual probe, not a page defect. | Navigate the actual `/scanner-runs` page (not a raw request to a guessed path) while the same concurrent warm is running, and confirm the run list renders via its real `GET /api/runs` call — not blank, not frozen — and that clicking into a run detail loads via `GET /api/runs/{run_id}` the same way. |
| `/evidence` | `fetchEvidence` → `GET /api/evidence` | Operator-reported 0.009s on a post-warm read, but one ad hoc read DURING the heaviest part of the window hit a 30-second timeout — recorded honestly, not smoothed into the fast figure; not independently re-verified from a raw log this pass | Load `/evidence` WHILE the concurrent warm is still in its heaviest early phase (not just after it settles) and time how long the page takes to render. Confirm it either meets its own committed budget, or — if it is slow — that it degrades honestly (a loading state or a visible timeout/error message) rather than hanging silently with no feedback. |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/forward_testing.py` — the actual fix: a module-level lock
  (`_FORWARD_AGG_LOCK`) plus a per-key in-flight-event dictionary (`_FORWARD_AGG_INFLIGHT`) and a bounded
  45-second wait (`_FORWARD_AGG_WAIT_TIMEOUT_S`) added to `forward_aggregates_cached`'s cache-miss path
  only. `compute_forward_aggregates` (the actual calculation) is byte-identical/untouched — same
  signature, same columns read, same streamed pattern proven byte-identical in iter-14. No UI surface
  change of its own — its only user-visible trace is the `/backtest` row above, which flows through the
  unchanged `GET /api/backtest` handler.
- `apps/backend/tests/test_forward_testing_concurrency.py` — three new tests added (banner-separated
  from iter-14's own tests already in this file): a same-key concurrent-MISS dedup proof, a
  concurrent-write-during-read wall-clock-ratio bound, and a waiter-never-deadlocks-on-owner-failure
  proof. No UI impact — these run outside the browser, verifying backend behavior only.
- `apps/backend/app/db.py` — considered but **NOT modified** this iteration. The plan listed a
  session/connection/WAL configuration change here as conditional on the root-cause evidence; the
  developer's isolated measurement of that candidate (WAL/session contention alone, no redundant
  recomputation involved) showed only a 1.59x slowdown, well inside the accepted 5.0x guard, so no
  change was made. Recorded here for completeness since the plan named this file as a candidate. No UI
  impact.
- `reports/perf-budgets.md` — gained a new dated section transcribing the original 211.8-second UT-04
  finding (previously recorded only in a different report) plus this iteration's root-cause
  measurements, the fix description, and the live full-scale reproduction's results (including the two
  open WARN items surfaced in the reports above). This is the project's internal performance-budget
  ledger, not an in-product page — no UI impact.
- `runs/goal-session-ops-hardening/state/blueprint.md` — an internal pipeline planning/tracking document
  (this goal-mode session's own architecture notes), updated to record that the fix is now built and to
  describe its actual mechanism/outcome. Not rendered anywhere in the product — no UI impact.
- `apps/backend/app/mcp/tools.py`'s `query_backtest` MCP tool (confirmed byte-unchanged, absent from the
  diff) — the THIRD caller of the changed wrapper function, alongside `GET /api/backtest` and the ingest
  finalize warm, but a separate AI-agent/Model-Context-Protocol interface, not a page in the web app.
  Listed for completeness; no browser UI surface of its own.
- `apps/backend/app/engine/data_manager.py`'s ingest finalize warm loop (confirmed byte-unchanged,
  absent from the diff) — the OTHER real-world source of the concurrent same-key requests this fix
  de-duplicates against. Its own call site and the `/data` page's "Refreshed: ..." run-summary line are
  unaffected by this iteration — the same conditions as before still govern when that line appears; this
  iteration changes only what happens when its calls collide with a concurrent `/backtest` request on
  the same key.

---

## Summary

- **Frontend surfaces changed:** 0 (no `apps/frontend/` file appears in the diff)
- **UI surfaces with behavior impact via backend change:** 1 (`/backtest`'s per-horizon evidence panel)
- **Additional surfaces spot-checked under load, no code change:** 4 (`/stocks`, `/sectors`,
  `/scanner-runs`, `/evidence`)
- **New pages/routes:** 0
- **Modified components:** 0 (no frontend component source edited — the one effect above is a
  runtime/timing consequence of already-existing, unedited rendering code)
- **Navigation changes:** no
- **Backend-only changes:** 7 (1 product source file changed, 1 test file changed, 1 file considered but
  not touched, 1 reporting artifact, 1 pipeline state doc, 2 confirmed-unchanged call-site
  files/interfaces)
