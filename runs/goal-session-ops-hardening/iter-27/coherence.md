# Iteration 27 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-27
**Date:** 2026-07-27
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Coverage payload (`coverage_status`, `stale_dataset_version`, `stale_computed_at` — additive fields registered this iteration on the existing "Coverage payload" row) | OK | Computed by the unchanged canonical module `app.engine.data_manager.coverage_from_storage` — new fallback branch at `apps/backend/app/engine/data_manager.py:1165-1178`, all three fields stamped via one new helper `_tag_coverage_status` (`data_manager.py:1095-1111`) that mutates an already-resolved payload rather than deriving a new one (each call site passes through `json.loads(row.payload_json)`, `refresh_coverage_snapshot_for(...)`, or `_coverage_not_yet_computed_payload(cfg)` — all pre-existing derivations). Served by the unchanged canonical endpoint `GET /api/data` — `apps/backend/app/api/data.py:127` calls `coverage_from_storage(...)` and the route has no `response_model` (`data.py:97`), so the new fields ride the existing raw-dict response with no second endpoint or filtering path. Frontend reads them from the SAME `DataOverviewResponse`/`fetchDataOverview()` call already consumed by `/data` — `apps/frontend/app/data/page.tsx:759-765` (new `coverage-stale-notice` paragraph) and `apps/frontend/lib/api.ts:2344-2348` (type additions) — no new fetch, no client-side recomputation. Matches the blueprint's Data-contract-additions section verbatim (field names `coverage_status`/`stale_dataset_version`/`stale_computed_at`), satisfying TC-12. |
| Regime score / market phase / realized forward-returns (row touched via the AG-8 concurrency fix, no new field) | OK | `apps/backend/app/engine/forward_testing.py:372-491` — the new duplicate-key-collision handling in `_insert_run_forward_returns` is a control-flow/error-handling change only; `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, and `ensure_historical_forward_aggregates_dispatched` are untouched (confirmed via diff — `forward_testing.py`'s only hunk is inside `_insert_run_forward_returns` and its new helper `_is_forward_return_duplicate_key_collision`). No new field is added to any served payload; `GET /api/backtest` and MCP `query_backtest` are unchanged in this diff (`git diff` against `apps/backend/app/api/backtest.py` and `apps/backend/app/mcp/tools.py` is empty). |

No new displayed value/entity outside the two rows above was introduced this iteration (no unregistered-value WARN needed — the three new coverage fields are explicitly registered in `blueprint.md`'s Data-contract-additions section and match the built field names exactly).

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/data` — `CoveragePanel`'s new "stale" notice | OK | No new page/route/component. `apps/frontend/app/data/page.tsx:759-765` adds a conditional paragraph inside the EXISTING `CoveragePanel` function, which already renders under `/data`'s registered home (Data Manager nav section). `git diff` shows no changes to `apps/frontend/components/sidebar.tsx` (checked directly, empty diff) — no nav entries added, removed, or reordered. |
| `/backtest` — concurrency-race reliability fix | OK | No new page/route/component; `apps/backend/app/api/backtest.py` and the frontend `/backtest` page have zero diff hunks this iteration — the fix is entirely inside the shared engine function `_insert_run_forward_returns`, invisible as a new UI surface. `/backtest` keeps its existing Backtest nav-section home. |

No new page, route, or feature was introduced this iteration (confirmed by `reports/phase-goal-ops-hardening-iter-27-ui-surface-map.md`: "New pages/routes: 0", "Navigation changes: no" — cross-checked directly against the diff, which touches only `apps/frontend/app/data/page.tsx` and `apps/frontend/lib/api.ts` on the frontend side).

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None. This iteration is a narrowly-scoped hardening fix exactly matching its own spec's "Blueprint conformance" claim: additive Notes-column updates to two existing rows, zero new rows, zero new computing modules, zero new endpoints, zero Information Architecture change. The blueprint.md diff itself (`git diff ... -- runs/goal-session-ops-hardening/state/blueprint.md`, 6 lines) is limited to the iter-27 narrative paragraph and the two rows' Notes appends already verified above — no Computed-by/Served-by column changed for any row.
