# Iteration 57 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-57
**Date:** 2026-08-10
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Availability heatmap `stale`/`served_dataset_version` (new additive fields) | OK | Blueprint row registers these under `app.engine.data_manager.availability_from_storage` / `GET /api/data/availability`, tagged `[TARGET, iter-57 building]` before this iteration ran (`runs/goal-session-ops-hardening/state/blueprint.md:429`). Diff implements exactly that — same function extended, same table (`AvailabilityCache`), same endpoint (`apps/backend/app/engine/data_manager.py:1688-1729`). Frontend reads the field from the existing `/api/data/availability` fetch and re-renders, no new fetch (`apps/frontend/components/availability-heatmap.tsx:224-230`, `apps/frontend/lib/api.ts:2715-2731`). |
| `GET /api/health` distinct-symbol count | OK | Query-shape optimization only (recursive-CTE loose-index-scan replacing `COUNT(DISTINCT symbol)`), same inline read inside the health handler the blueprint already documents as "unrelated to the readiness computation itself" (`runs/goal-session-ops-hardening/state/blueprint.md:423`, iter-5 note). No new module, no new endpoint, response shape unchanged (`apps/backend/app/api/health.py:45-79`). |
| `GET /api/stocks/{ticker}/bars?through=latest` latency fix | OK | `sma_series` (`apps/backend/app/engine/indicators.py:52-73`) bounds its input slice to the trailing window instead of the full growing prefix — pure algorithmic fix to the existing single MA implementation `sma_series` already owned; byte-identity claimed and (per iter spec) tested. No second MA/indicator implementation introduced, no new endpoint. This endpoint has no dedicated Data Contract row — it is covered by goal.md's "cannot be precomputed, user-parameterized" carve-out, consistent with iter-57 spec's framing. |
| `persisted_this_call` honesty fix (availability + index-series caches) | OK | Both `availability_cached_with_status` (`apps/backend/app/engine/data_manager.py:1661-1670`) and its documented sibling `index_series_cached_with_status` (`apps/backend/app/engine/indexes.py:278-286`) now return `False` on a rolled-back commit instead of always `True`. Same functions, same `aggregates_refreshed` field already registered in the Backfill run-summary contract row (`blueprint.md:426`) — no new field, no second producer. |
| MCP `list_runs` `n_stocks` | OK — closes prior advisory | `apps/backend/app/mcp/tools.py:715-744` now reads `n_stocks` from one grouped `select(ScannerResult.run_id, func.count()).group_by(ScannerResult.run_id)` query. Confirmed structurally identical to the canonical aggregate `app.api.runs.runs` already uses (`apps/backend/app/api/runs.py:42-44`) — same shape, same grouping key. This resolves the iter-56 coherence-auditor's own advisory finding (stale duplicate `n_stocks` computation) rather than introducing a new one. |

No new displayed value was introduced outside the Data Contract this iteration — `stale` and `served_dataset_version` were pre-registered as this iteration's Data-contract additions before dispatch (iter-57 spec, "Data-contract additions" section), and the blueprint row was updated additively, matching the shipped diff exactly.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/data` — `AvailabilityHeatmap` stale/updating banner | OK | No new route; conditional banner added inside the existing component that already renders on `/data`'s canonical Data Manager home (IA table row for J-05/J-09, `blueprint.md:405`/`409`). `apps/frontend/components/sidebar.tsx` is untouched in this diff (absent from `git diff --stat` against the snapshot SHA) — nav skeleton unchanged, confirming the spec's "no Information Architecture change" claim. |

No new page, route, or nav entry was introduced this iteration. `git diff <snapshot-sha> --stat` touches only `apps/backend/app/api/health.py`, `apps/backend/app/engine/{data_manager,indexes,indicators}.py`, `apps/backend/app/mcp/tools.py`, six backend test files, `apps/frontend/components/availability-heatmap.tsx`, and `apps/frontend/lib/api.ts` — no router, layout, or sidebar file appears. The UI-surface-map (`reports/phase-goal-ops-hardening-iter-57-ui-surface-map.md`) independently confirms "Navigation changes: no" and "New pages/routes: 0."

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Stale-banner copy is worded differently from its sibling.** The new availability banner reads "Data as of `<version>` — updating" (`apps/frontend/components/availability-heatmap.tsx:229`); the pre-existing, analogous Coverage-panel stale banner reads "Coverage as of a prior scan (version `<version>`) — refreshes on the next data job" (`apps/frontend/app/data/page.tsx:759-764`). Both use identical styling (`border-b border-border bg-surface-2 px-4 py-2 text-xs text-text-muted`) and convey the same concept (serving a prior persisted snapshot during an in-flight ingest), but the phrasing diverges ("updating" vs. "refreshes on the next data job", "Data as of" vs. "Coverage as of a prior scan"). Not a Data Contract or IA violation — purely a copy-consistency polish item for a future iteration to align, if desired.
- Everything else reviewed (the `GET /api/health` query-shape fix, the `sma_series` windowing fix, the two `persisted_this_call` honesty fixes, and the MCP `list_runs` consolidation) is a same-module/same-endpoint correctness or performance change with no new displayed value and no new UI surface — no advisory needed beyond the note above.
