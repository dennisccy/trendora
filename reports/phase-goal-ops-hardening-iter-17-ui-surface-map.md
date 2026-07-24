# Phase goal-ops-hardening-iter-17 — UI Surface Map

**Phase:** goal-ops-hardening-iter-17
**Date:** 2026-07-24
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

All changes this iteration land on the single existing `/backtest` page — no new page, panel, route, or
nav entry was added. The rows below are driven by two backend files whose output the frontend already
consumes (`apps/backend/app/engine/forward_testing.py`'s widened completeness/fallback search and new
`evidence_asof` field; `apps/backend/app/api/backtest.py`'s threading of that field into `GET
/api/backtest`, which `apps/frontend/lib/api.ts`'s `fetchBacktest` calls directly) plus the two frontend
edits in `apps/frontend/app/backtest/page.tsx`.

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/backtest` | Evidence-section state routing (`BacktestResults`: chooses between the `EmptyState`, the `RefreshingEvidenceBanner` + `EvidenceAggregateSection`, keyed on `backtest.evidence_status`) | Changed behavior | Backend widened `resolved_forward_aggregate_evidence`'s fallback search to older `asof_key`s (audit B1) — the single most common daily data-update shape (a new latest trading day landing before its forward-aggregate warm finishes) now resolves to `refreshing` with a populated evidence section instead of falling through to the empty `not_yet_computed` state. | Today (the live scenario cannot be produced on the working DB — its latest price date has no future day to backfill into, per the operator's finding): run `curl -s http://localhost:8255/api/backtest \| python3 -m json.tool` and confirm the JSON now includes an `evidence_asof` key alongside `evidence_status`, present for every status value, not only `refreshing`. Then, the first time a real new trading day is ingested as the latest run (a normal daily update, not a historical backfill), reload `/backtest` at its default (latest) as-of while that date's forward-aggregate warm is still incomplete, and confirm the evidence section at the bottom of the page shows populated numbers (`EvidenceAggregateSection`) rather than the "Backtest evidence not yet computed" empty state. |
| `/backtest` | `RefreshingEvidenceBanner` | Changed behavior (new displayed field) | J-08 step 2 requires the banner to disclose WHICH as-of's evidence is being served, not only when it was generated; the component now takes an `evidenceAsof` prop and renders it. | Find or produce a request where the API response has `"evidence_status": "refreshing"` (e.g. `curl -s 'http://localhost:8255/api/backtest?as_of=<a date>' \| python3 -m json.tool` to locate one, or reuse the date from the existing iter-16 screenshot), load `/backtest` for that date, and confirm the banner's second sentence reads "...the last complete version — evidence as of `<date>`, generated `<timestamp>`..." with a real calendar date (not an em dash, not blank) appearing immediately before the word "generated" — this date text did not exist in the banner before this iteration. |
| `/backtest` | `EmptyState` (title "Backtest evidence not yet computed") | Changed behavior (copy only) | Audit F2 (removed "run an ingest" phrasing that presumed the user hadn't already started one) + audit F3 (de-duplicated the description's repeated opening sentence). | Navigate to `http://127.0.0.1:13255/backtest` — the already-running throwaway frontend pointed at a disposable, never-ingested database copy on `:18255` (do not start, stop, or restart it; it is a live standing fixture for exactly this check) — and confirm the empty-state card shows the unchanged title "Backtest evidence not yet computed" together with the new description beginning "No forward-tested evidence exists yet for this date. Backfilling or fetching data that covers it will compute this evidence...", and confirm the phrase "run an ingest" does not appear anywhere in that description. |

<!-- Change Type options: New page | New component | Updated layout | Added navigation | Changed behavior | Removed element | New form | New table | New modal -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/mcp/tools.py` — `query_backtest` mirrors the same `evidence_asof` field and B5 read-dedup for MCP/AI-agent clients — not rendered on any page in this Next.js frontend, so no browser UI surface is affected by this file (see "Not Visible Yet" in the companion user-visible-changes report for the distinction from a genuine gap).
- `apps/backend/tests/test_forward_testing_serving_split.py` — 5 new unit tests (TC-1/2/4/5/6) plus `evidence_asof` assertions added to 6 existing tests — test coverage only, no UI surface.
- `apps/backend/tests/test_api_backtest.py` — one exact-key-set assertion updated to include `evidence_asof` (edited, not run this session — the `loaded_engine` fixture is out of scope) — test coverage only, no UI surface.
- `reports/perf-budgets.md` — new dated section recording the `/backtest` latency root-cause investigation and the TC-8/TC-9/TC-10/TC-11 operator results — a project/ops report consumed by the evaluator and future iterations, never rendered in the application itself.
- `apps/backend/app/engine/data_manager.py` — investigated only this iteration (traced every commit boundary in the ingest finalize hook); not modified — no diff, no UI impact.

---

## Summary

- **Frontend surfaces changed:** 1 (`/backtest` — its evidence section only; no other page touched)
- **New pages/routes:** 0
- **Modified components:** 2 (`RefreshingEvidenceBanner`, the `EmptyState` call site's copy)
- **Navigation changes:** no
- **Backend-only changes:** 4 (`mcp/tools.py`, `test_forward_testing_serving_split.py`, `test_api_backtest.py`, `reports/perf-budgets.md`) — plus `data_manager.py`, investigated with zero resulting diff.
