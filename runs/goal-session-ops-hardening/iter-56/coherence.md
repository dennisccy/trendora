# Iteration 56 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-56
**Date:** 2026-08-10
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-WARN

<!-- COHERENCE-WARN: only advisory issues; does NOT block GOAL_ACHIEVED -->

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Availability heatmap (`compute_availability`, `GET /api/data/availability`) | OK | `apps/backend/app/engine/data_manager.py:1544` (unchanged sole producer), `:1620-1657` (new `availability_cached_with_status` — pure serving/persistence wrapper, calls `compute_availability` on MISS only), `:1670-1690` (new `availability_from_storage` — the ONLY caller of the endpoint, cache-read-or-honest-empty, never a live compute), `apps/backend/app/api/data.py:26` (endpoint now calls `availability_from_storage`, was `compute_availability`). Grepped all production (non-test) call sites of `compute_availability` — the only one is inside `availability_cached_with_status`; no second producer, no second endpoint. Matches the blueprint's new "Availability heatmap" Data Contract row (`runs/goal-session-ops-hardening/state/blueprint.md:428`), which this iteration itself additively registered. |
| `/api/runs`'s `n_stocks` (router path, `app.api.runs.runs`) | OK | `apps/backend/app/api/runs.py:49-56` — query-plan-only change (grouped `GROUP BY ScannerResult.run_id` replacing a per-run `COUNT`), same function, same endpoint, same response shape; matches the iter spec's own "no Data Contract row addition needed" reasoning (byte-identity proven by `test_api_runs_n_stocks_byte_identical_to_per_run_count`). |
| `n_stocks` (MCP mirror, `app.mcp.tools.list_runs`) | **UNREGISTERED / STALE DUPLICATE (pre-existing, not introduced this iteration — WARN, see Advisory notes)** | `apps/backend/app/mcp/tools.py:706-731`, specifically the per-run `session.scalar(select(func.count())...)` loop at `:718-720` |
| `aggregates_refreshed` enumerated list (`"availability_heatmap"` member) | OK | `apps/backend/app/engine/data_manager.py:4460-4491` (finalize-hook warm, iter-8 MemoryError-isolation convention applied, honesty-gated on `persisted_this_call`); blueprint's "Backfill run-summary contract" row Notes updated in the same commit (`blueprint.md:425`). No new field, no second record. |

## Information Architecture check

Frontend Present: no (iter spec, Metadata). Zero `apps/frontend/**` files touched (confirmed via `git diff --stat` against the snapshot SHA — only 7 backend/test files changed). No new page, route, or nav entry; both touched endpoints (`GET /api/runs`, `GET /api/data/availability`) keep their existing homes (`/scanner-runs`, `/data`) per the blueprint's Information Architecture table (`blueprint.md:382-408`), which itself was not modified this iteration (confirmed: the only blueprint.md diff hunks are the iter-56 changelog paragraph and the Data Contract table edits — the `## Information Architecture` heading appears only as unmodified diff context).

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| N/A — no new page/route/feature this iteration | OK | `apps/frontend/components/sidebar.tsx` unchanged (no diff); blueprint IA table unchanged |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Stale duplicate `n_stocks` computation in the MCP tool mirror, left unfixed by this iteration.** `apps/backend/app/mcp/tools.py:706-731`'s `list_runs` (the MCP tool backing `GET /api/runs`'s tool-surface equivalent) independently computes `n_stocks` via the SAME per-run `ScannerResult` COUNT-in-a-loop pattern this iteration just removed from the router (`apps/backend/app/api/runs.py`). Its own docstring (`tools.py:710-712`) documents why the duplication exists: "`/api/runs` keeps its read inline in the router (no engine function to delegate to), so this is the one tool that MIRRORS the router's stored-row read rather than calling a shared engine helper." That documented mirroring relationship is now stale in mechanism (though not in served value — both still return byte-identical counts, so this is not a "numbers don't match" defect): the router side is now O(1) query count via a grouped aggregate, while the MCP side is still the O(n) per-run loop that measured 6.8-10.7s live against the committed ≤1.5s budget on the current 2,937-run DB (per this iteration's own dev handoff / `reports/perf-budgets.md` Addendum 20). This is NOT a FAIL under the coherence-audit rules — `apps/backend/app/mcp/tools.py` was not touched by this iteration's diff (verified via `git diff --stat` against the snapshot SHA: only `apps/backend/app/api/data.py`, `apps/backend/app/api/runs.py`, `apps/backend/app/engine/data_manager.py`, `apps/backend/app/models.py`, and 3 test files changed), so there is no *new* offending file:line in this iteration's own diff to point at — the duplication pattern pre-dates iter-56. Recommended finite fix for a future iteration: point `list_runs` at the same grouped-aggregate query `app.api.runs.runs()` now uses (or, better, extract the shared row-assembly logic into one `app.engine`-level helper both the router and the MCP tool call, closing the "no engine function to delegate to" gap the docstring names as the root cause of the duplication) — otherwise a large concurrent MCP `list_runs` call remains exposed to the exact N+1 latency this iteration fixed on the REST path.
- No other advisory issues found: labels, units, and formatting for both touched values are unchanged from their pre-iteration presentation (Frontend Present: no, byte-identical response shapes confirmed by the developer's own byte-identity tests).
