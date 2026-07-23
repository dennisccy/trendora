# Iteration 16 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-16
**Date:** 2026-07-24
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope note (diff provenance)

No bounded `iter-diff.md` existed in `runs/goal-session-ops-hardening/iter-16/` (only `.steps/`,
`depth-dispatched`, `goal-slice.md`, `snapshot-sha`), so I used the exact snapshot-SHA commands from the
invocation prompt: `git diff d17ccb8e7e580eadeed677e5b4c019e8ffef075f` (noise-excluded) plus the `--stat`
of the excluded paths. The excluded-paths stat contains only `reports/perf-budgets.md` (the TC-16
measurement writeup, +216 lines — the SAME canonical budgets artifact, no second file),
`runs/goal-session-ops-hardening/state/blueprint.md` (+37/-3, the J-08 IA/Data-Contract additions),
`runs/goal-session-ops-hardening/state/assumptions.md` (+26, the logged historical-as-of interpretation
call), and `runs/*`/`goal-session-mcp-loop/*` harness bookkeeping (telemetry/trace/drift-report) — no
lockfiles, no dependency-file changes. `docs/goal.md` shows as modified in `git status` but is
byte-identical to the snapshot SHA (`git diff <sha> -- docs/goal.md` is empty) — the J-08 journey text
was already in place before this iteration's snapshot was taken, matching the spec's own framing ("the
owner has now decided"). The noise-excluded main diff touches exactly 11 tracked files, matching the
ui-surface-map's file-classification table exactly, plus one new untracked test file,
`apps/backend/tests/test_forward_testing_serving_split.py` (new/untracked files don't appear in
`git diff <sha>`; read directly — 10 test functions, no route/API definitions, no UI surface).

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| `compute_forward_aggregates` (sole producer, "Regime score, market phase, realized forward-returns" row) | OK | Only remaining call site is `apps/backend/app/engine/forward_testing.py:1120`, inside `forward_aggregates_ingest_cached` (the renamed ingest-only half). Repo-wide grep for `compute_forward_aggregates(` under `apps/backend/app` confirms zero other call sites — not in the new `resolved_forward_aggregate_evidence`, not in `backtest.py`, not in `mcp/tools.py`. |
| `evidence_status` / `evidence_generated_at` (new, registered fields on the SAME row) | OK | Produced by exactly one function, `resolved_forward_aggregate_evidence` (`apps/backend/app/engine/forward_testing.py:1163-1234`); consumed by exactly the two endpoints the blueprint names: `apps/backend/app/api/backtest.py:87` (`GET /api/backtest`) and `apps/backend/app/mcp/tools.py:215` (`query_backtest`). `runs/goal-session-ops-hardening/state/blueprint.md` (Data Contract, "Regime score..." row, iter-16 paragraph) registers both fields as an additive Notes-column append to this EXISTING row — not a new row, same computing module (`app.engine.forward_testing`), same two endpoints. |
| Frontend display of `evidence_status`/`evidence_generated_at` | OK — reformat, not a second source | `apps/frontend/app/backtest/page.tsx:235,243` branches on `backtest.evidence_status`, destructured directly off the existing `fetchBacktest()` response (`apps/frontend/lib/api.ts:1095,1098`, `BacktestResponse` interface). No new `fetch`/effect, no client-side computation of status — it renders exactly what the canonical endpoint served. |
| `ForwardAggregateCache` "current dataset version" resolution (used by both split halves) | OK — single shared source | Both `forward_aggregates_ingest_cached` (`forward_testing.py:1079,1082`, `version = _dataset_version(session)`) and `resolved_forward_aggregate_evidence` (`forward_testing.py:1198,1232`) resolve "current version" via the SAME deferred-imported `app.engine.research._dataset_version` — no divergent versioning logic between the write side and the read side. |
| Cutover pruning (`ForwardAggregateCache` stale-row deletion) | OK — same table, same module, no second cache identity | Pruning logic lives entirely inside `forward_aggregates_ingest_cached` (`forward_testing.py:1134-1155` region, the completeness-gated cutover replacing the old per-horizon-write deletion); no new table, no new cache column — matches the spec's explicit "any new DB table or a second cache identity" prohibition. |
| Job history / Backfill run-summary contract (`aggregates_refreshed`) | OK — unaffected | `apps/backend/app/engine/data_manager.py:3230` is a pure call-site rename (`forward_aggregates_cached` → `forward_aggregates_ingest_cached`); the surrounding loop, its `MemoryError` isolation, and the `aggregates_refreshed` list membership are byte-unchanged (only 2 lines touched in the whole file — the call and one comment, both renames). |

No new displayed value/entity appears in this diff that is absent from the Data Contract — the two new
fields were pre-registered in `blueprint.md` (read first, per the required reading order) before I read
the code, and the code matches the registration exactly: one producer, two consumers, no client-side
recomputation.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/backtest` evidence section — new `RefreshingEvidenceBanner` (refreshing state) | OK | Local component defined inside the EXISTING `apps/frontend/app/backtest/page.tsx:263` (same file as `BacktestResults`); reuses the page's already-imported `Card` primitive plus `Loader2` (added to the existing `lucide-react` import line) — not a parallel shell, no new file, no new route. |
| `/backtest` evidence section — `EmptyState` call site (not_yet_computed state) | OK | Reuses the existing `EmptyState` component (already imported at the top of `page.tsx` before this iteration) at a new call site inside the same file — not a new component, not a duplicate of an existing empty-state pattern elsewhere. |
| J-08 Feature/journey-homes row | OK | `runs/goal-session-ops-hardening/state/blueprint.md`'s IA table gained one additive row mapping J-08 to the SAME existing canonical home as J-07: `/backtest` + the MCP `query_backtest` tool. The Navigation skeleton (the actual nav tree, same file) is byte-unchanged — confirmed no diff to `apps/frontend/components/sidebar.tsx` or `layout.tsx` (absent from both the noise-excluded diff and `git status`). |
| Reachability | OK — unaffected | `/backtest` was already a top-level, 1-click nav entry before this iteration; nothing in this diff touches routing or nav depth. |
| Duplicate home | OK — none | J-08 intentionally shares `/backtest` + the MCP tool with J-07 (both are cross-cutting serving-architecture guarantees on the SAME existing page), mirroring the blueprint's own established pattern for J-05/J-06/J-07 (cross-cutting journeys sharing existing homes rather than inventing dedicated pages). |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

None. The two new fields were pre-registered in the blueprint before the code landed (rather than the
more common "unregistered-but-new value" pattern this gate usually flags), the rename left zero stray
references to the old `forward_aggregates_cached` name in application code (only in historical-context
prose/docstrings explaining the split), and the historical (`is_latest=false`) scope carve-out is an
explicitly logged interpretation call (`assumptions.md`, iter-16) rather than a silent one.
