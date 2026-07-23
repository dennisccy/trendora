# Phase goal-ops-hardening-iter-16 — UI Surface Map

**Phase:** goal-ops-hardening-iter-16
**Date:** 2026-07-23
**Written by:** ui-impact-analyst

---

## File Classification (Step 1)

All 14 files listed in `docs/handoffs/goal-ops-hardening-iter-16-dev.md`'s "Files Changed" section,
classified per `.claude/skills/diff-to-ui-impact.md`:

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `apps/frontend/app/backtest/page.tsx` | frontend-direct | direct | `BacktestResults`'s evidence-section render restructured into a 3-way branch on `evidence_status`; new local `RefreshingEvidenceBanner` component added. |
| `apps/frontend/lib/api.ts` | frontend-direct | direct | `BacktestResponse` interface gains `evidence_status` / `evidence_generated_at` — the exact fields `page.tsx` branches on. |
| `apps/backend/app/api/backtest.py` | backend-api | direct (frontend already consumes `GET /api/backtest` via `fetchBacktest`) | Switches `evidence_by_horizon` population to the new read-only resolver; adds the 2 new response fields. This is the backend change that DRIVES the `/backtest` rows below. |
| `apps/backend/app/mcp/tools.py` | backend-api | none — different consumer | `query_backtest` MCP tool mirrors the endpoint's same 2 new fields, but is called by AI-agent/MCP clients, not the Next.js frontend — no browser surface of its own. |
| `apps/backend/app/engine/forward_testing.py` | backend-internal | indirect (feeds the backend-api row above) | Splits `forward_aggregates_cached` into `forward_aggregates_ingest_cached` (compute+persist) and `resolved_forward_aggregate_evidence` (read-only); changes cache pruning to a completeness-gated cutover. Not itself an API route or UI file. |
| `apps/backend/app/engine/data_manager.py` | backend-internal | none | Pure call-site rename (one line) inside the existing `/data` ingest finalize-warm loop; loop/trigger/behavior byte-unchanged. |
| `apps/backend/tests/conftest.py` | backend-internal (test) | none | Shared `loaded_engine` fixture now pre-warms the forward-aggregate cache so ~29 dependent test files keep passing post-split; no product code. |
| `apps/backend/tests/test_forward_testing_concurrency.py` | backend-internal (test) | none | Renamed references; these tests now prove TC-17 (single-flight guard survives the split) by construction. |
| `apps/backend/tests/test_forward_testing.py` | backend-internal (test) | none | Renamed references; dataset-version-change test rewritten for the new cutover-gating contract. |
| `apps/backend/tests/test_data_manager.py` | backend-internal (test) | none | 3 renamed call sites; 1 test rewritten to call the new read-only resolver. |
| `apps/backend/tests/test_api_backtest.py` | backend-internal (test) | none | One exact-key-set assertion updated to include the 2 new response fields. **Not executed this session** (a `loaded_engine`-fixture file, out of scope this pass) — see "What to Test" caveat below. |
| `apps/backend/tests/test_forward_testing_serving_split.py` | backend-internal (test, NEW) | none | 10 new tests proving completeness/cutover/never-computed/byte-identity/`asof_key`-filtering at the unit/fixture level. |
| `reports/perf-budgets.md` | config / reporting | none | Internal performance-budget ledger; gained the TC-16 live-measurement writeup. Not an in-product page. |
| `runs/goal-session-ops-hardening/state/blueprint.md` | config / reporting (pipeline state) | none | Internal goal-mode pipeline tracking document (light-touch corrections to the pre-drafted J-08 paragraphs). Not rendered in-product. |

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/backtest` | `BacktestResults` → `RefreshingEvidenceBanner` (new local component, `apps/frontend/app/backtest/page.tsx`) | New component | Backend now serves `evidence_status: "refreshing"` when a newer dataset version is warming but not yet complete (J-08); the page must honestly disclose that instead of silently showing numbers with no context, or blocking on a recompute. | With the backend's `/backtest` evidence at `evidence_status === "refreshing"` — trigger a single-day backfill on `/data` for the current as-of date, then reload/poll `/backtest` while that job's finalize warm is still in progress (before `aggregates_refreshed` includes `"forward_aggregates"`) — confirm a warn-toned card with a spinning icon and the text "Refreshing — showing the last complete evidence" (`data-testid="evidence-refreshing"`) renders directly ABOVE the "Forward-tested evidence" section, showing a formatted generation timestamp, while the evidence numbers below it remain fully populated (not blank, not a loading skeleton). |
| `/backtest` | `BacktestResults` → `EmptyState` (existing component, new call site, `apps/frontend/app/backtest/page.tsx`) | Changed behavior (replaces a silent omission) | Backend now serves `evidence_status: "not_yet_computed"` with `evidence_by_horizon: {}` for a date/store where no forward-aggregate warm has ever completed, replacing the prior silent `{evidence ? (...) : null}` gap. | Load `/backtest` for a date/store where forward-aggregate evidence has never been computed (e.g. a freshly seeded database, or a date with no prior ingest finalize warm) and confirm a dashed-border card reading "Backtest evidence not yet computed" plus its description ("...run an ingest to populate...") appears IN PLACE of the evidence section — no horizon numbers appear anywhere on the page — while the Scorecard, Return Attribution, and leadership-list sections above it still render normally. |
| `/backtest` | `BacktestResults` → evidence section (`ready` path, `EvidenceAggregateSection`) | Changed behavior (regression guard) | The evidence-section render was restructured into a 3-way branch on `evidence_status`; the `ready` branch must still render byte-for-byte as it did before this iteration (TC-12). | Load `/backtest` for a date whose `evidence_status` is `"ready"` (the normal steady state, e.g. right after an ingest finalize warm has fully completed) and confirm NEITHER the refreshing banner NOR the "not yet computed" empty state is present — only the normal populated Forward-tested evidence panels (score-bucket table, control-group cohorts, etc.) render, exactly matching the page's pre-iteration appearance. |
| `/backtest` (data contract) | `BacktestResponse` type (`apps/frontend/lib/api.ts`) consumed by `fetchBacktest` | Data contract addition | `GET /api/backtest` now returns `evidence_status` and `evidence_generated_at`; `page.tsx` destructures these directly off `backtest.evidence_status` / `backtest.evidence_generated_at` to drive the three rows above. | With the browser DevTools Network tab open, load `/backtest`, inspect the `GET /api/backtest` response body, and confirm it contains `evidence_status` (one of `"ready"` / `"refreshing"` / `"not_yet_computed"`) and `evidence_generated_at` (an ISO-8601 datetime string, or `null` only when `evidence_status` is `"not_yet_computed"`) alongside the pre-existing `evidence_by_horizon` field. |

<!-- Change Type key used above: New component | Changed behavior | Data contract addition -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/api/backtest.py` — the `GET /api/backtest` route: switches to the new read-only
  resolver and adds the 2 new fields to the response. This is the backend change that DRIVES the three
  `/backtest` rows above; listed here because the file itself is a Python API route module, not a
  frontend page/component — no UI surface of its own beyond what is already captured above.
- `apps/backend/app/engine/forward_testing.py` — the actual split: `forward_aggregates_ingest_cached`
  (ingest-only compute-and-persist, keeps iter-15's single-flight guard unchanged) and
  `resolved_forward_aggregate_evidence` (new, read-only, structurally cannot call
  `compute_forward_aggregates`); cache pruning changed from per-horizon-write deletion to a
  completeness-gated cutover. No UI surface of its own — its only user-visible trace is via the
  `/backtest` rows above, through the unchanged `GET /api/backtest` handler.
- `apps/backend/app/mcp/tools.py` — `query_backtest` MCP tool, mirrors the endpoint's same 2 new fields
  exactly. Consumed by AI-agent/Model-Context-Protocol clients, not the web frontend — no browser page of
  its own.
- `apps/backend/app/engine/data_manager.py` — one call-site rename (line 3230) inside
  `_refresh_ingest_aggregates`'s existing per-horizon warm loop; the loop, its trigger (an ingest
  finalize event on `/data`), and its `MemoryError` isolation are byte-for-byte unchanged. No UI impact.
- `apps/backend/tests/conftest.py` — the shared `loaded_engine` fixture now additionally pre-warms the
  latest run's forward-aggregate cache (via the SAME producer the real ingest hook calls) so the ~29 test
  files sharing this fixture keep seeing the values they already expect, post-split. Pure test
  infrastructure; no UI impact.
- `apps/backend/tests/test_forward_testing_concurrency.py`, `test_forward_testing.py`,
  `test_data_manager.py`, `test_api_backtest.py` — renamed references and/or rewritten assertions to match
  the new function names and the new cutover/serving-split contract. All test-only; no UI impact.
- `apps/backend/tests/test_forward_testing_serving_split.py` (**NEW**) — 10 tests covering the
  completeness/cutover/never-computed/byte-identity logic, the `asof_key`-filtered completeness query
  (TC-18), and both request-serving entry points' wiring, called as plain functions (no browser, no
  TestClient boot). No UI impact.
- `reports/perf-budgets.md` — gained a new dated section: the PENDING operator protocol plus its own
  RESULTS transcription (the live TC-16 measurement referenced in the companion User-Visible Changes
  report's "What Old Behavior Changed" section). This is the project's internal performance-budget ledger,
  not an in-product page — no UI impact of its own.
- `runs/goal-session-ops-hardening/state/blueprint.md` — light-touch corrections to the decomposer's
  pre-drafted J-08 paragraphs (naming the actual function names chosen, fixing one caller-count
  imprecision). An internal goal-mode pipeline tracking document, not rendered anywhere in the product —
  no UI impact.

---

## Summary

- **Frontend surfaces changed:** 1 (`/backtest`'s "Forward-tested evidence" section)
- **New pages/routes:** 0
- **Modified components:** 2 (`BacktestResults`'s evidence-render logic restructured into a 3-way branch;
  new `RefreshingEvidenceBanner` component added) — `EmptyState`, `Card`, and `Loader2` are reused
  unmodified from the existing design system.
- **Navigation changes:** no
- **Backend-only changes:** 12 (1 API route file whose response change drives the UI rows above, 1 engine
  file, 1 MCP tool file with a non-browser consumer, 1 ingest call-site rename, 6 test files (1 new), 2
  reporting/pipeline-state artifacts)
