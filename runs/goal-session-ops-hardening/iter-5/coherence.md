# Iteration 5 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-5
**Date:** 2026-07-20
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

This iteration is measurement + code-audit only, with one contingent backend fix (per the iter spec's
"CONTINGENT" bullet and the blueprint's own pre-registered exception). No frontend files changed
(confirmed: `git diff <snapshot>..HEAD -- apps/frontend` is empty; ui-surface-map confirms 0 `.tsx`/`.ts`
touched).

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Regime score, market phase, realized forward-returns (`app.engine.forward_testing` row) | OK | `apps/backend/app/engine/forward_testing.py:939-1010` (new `forward_aggregates_cached`) calls the existing `compute_forward_aggregates` (unchanged, still the sole producer) on a cache miss only; `apps/backend/app/api/backtest.py:68-73` and `apps/backend/app/mcp/tools.py:198-206` both switched their one call site from `compute_forward_aggregates` to `forward_aggregates_cached` — same module, same two existing callers, no second producer, no second endpoint. Byte-identity between cached and fresh compute is asserted by `test_forward_aggregates_cached_byte_identical_and_single_row` (`apps/backend/tests/test_forward_testing.py:820-838`). |
| Job history / Backfill run-summary contract (`aggregates_refreshed`) | OK | `apps/backend/app/engine/data_manager.py:3106-3130` appends `"forward_aggregates"` to the SAME existing `aggregates_refreshed` list via the SAME `_refresh_ingest_aggregates` finalize hook — no new field, no second record. Docstring enum widened in two places (`data_manager.py:1888`, `:3050`) consistently. |
| Page performance budgets | OK | `reports/perf-budgets.md` is the only budgets file touched (`git status --short reports/ | grep perf` → one file); no second measurement artifact created anywhere in the repo (checked via `find reports -iname "*perf*"`). |
| `ForwardAggregateCache` (new table) | OK — registered, not a duplicate | Not a new *displayed* value — it is a pure cache row for the already-registered "Regime score, market phase, realized forward-returns" row, following the `EventStudyCache`/`MarketPhaseCache`/`CoverageSnapshot` convention exactly (`apps/backend/app/models.py:507-561`). The blueprint's own iter-5 preamble (`runs/goal-session-ops-hardening/state/blueprint.md:45-59`) and the affected row's Notes column were both updated in this same diff to describe the fix — amending the EXISTING row, not adding a new one (`blueprint.md` diff: only the "Regime score..." row's Notes cell changed; no new table row appended). |

`/api/runs`'s known N+1 pattern (`ScannerResult` count per run) was measured (0.050-0.196s, within its
newly-committed budget) and deliberately left unfixed per the dev handoff's TC-13 audit — no code touched
there, so no contract question arises.

## Information Architecture check

No new page, route, nav entry, or component was added or removed this iteration (0 frontend files in the
diff; ui-surface-map's own summary: "New pages/routes: 0 … Navigation changes: no"). All four rows in the
ui-surface-map (`/backtest` evidence-by-horizon panel latency, three `aggregates_refreshed` "Refreshed:
..." render sites on `/data`) are pre-existing UI elements whose content/timing changed due to a
backend-only fix — not new surfaces requiring a nav check.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/backtest` (evidence-by-horizon panel, unchanged UI, faster data) | OK — no new surface | N/A — pre-existing route, unchanged nav; `sidebar.tsx` not touched (0 frontend diff) |
| `/data` (aggregates_refreshed rendering, unchanged UI, new list item) | OK — no new surface | N/A — pre-existing route, unchanged nav |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None. The iteration is a clean example of the blueprint's own pre-registered contingency: a value's
  existing computing module gained a warm-cache serving wrapper, both existing call sites (the REST
  endpoint and its MCP-tool sibling) were switched to it uniformly, and the blueprint's Data Contract row
  was amended in place rather than a new row or a second producer being introduced.
