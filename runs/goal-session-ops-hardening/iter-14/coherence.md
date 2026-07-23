# Iteration 14 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-14
**Date:** 2026-07-23
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

Diff scope confirmed via `git diff 680823748c37b06a7bf48155a46da8b8cb7604e0 --stat` (noise-excluded):
only `apps/backend/app/engine/forward_testing.py` (+84/-36) changed in tracked product source, plus two
new untracked test files (`apps/backend/tests/test_forward_testing_aggregates_streaming.py`,
`apps/backend/tests/test_forward_testing_concurrency.py` — not visible to `git diff` since untracked; read
directly). `reports/perf-budgets.md`, `runs/.../state/{blueprint,assumptions}.md` also changed (reporting/
contract bookkeeping, reviewed below). No file under `apps/api/`, `apps/backend/app/api/`,
`apps/backend/app/mcp/`, `apps/backend/app/engine/data_manager.py`, or `apps/backend/app/models.py`
appears anywhere in the diff (`git diff <sha> -- apps/backend/app/api/ apps/backend/app/models.py
apps/backend/app/mcp/ apps/backend/app/engine/data_manager.py` returns empty).

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Regime score, market phase, realized forward-returns (`app.engine.forward_testing.compute_forward_aggregates`, served by `GET /api/backtest` + MCP `query_backtest`) | OK | `apps/backend/app/engine/forward_testing.py:796-909` (diff hunk) — the two whole-partition `.all()` reads (`ForwardReturn` at old `:805`/new area, `ScannerResult` at old `:826`) are rewritten in place to column-projected `select(...)` + `.yield_per(cfg.research.read_batch_size)` streaming. Same function name, same signature, same module. `git diff` on `apps/backend/app/api/backtest.py` and `apps/backend/app/mcp/tools.py` is empty — both call sites unchanged. `cfg.research.read_batch_size` is a pre-existing knob (defined `apps/backend/app/config.py:1317`, already used at `forward_testing.py:469` and 10+ sites in `research.py` prior to this iteration per `grep`) — no second batch-size config introduced. No new function/class/endpoint/table added anywhere in the reviewable diff (`grep '^+.*def \|^-.*def '` on the forward_testing.py diff returns nothing — pure body rewrite, no new def). |
| Same value — test-file reference implementations | OK (not a violation) | `apps/backend/tests/test_forward_testing_aggregates_streaming.py:46-154` (`_reference_compute_forward_aggregates`) and `apps/backend/tests/test_forward_testing_concurrency.py:127-143` (`old_unbounded_read`, generated into a throwaway child-process script) are PINNED copies of the pre-rewrite function body, used exclusively as test oracles to prove byte-identity (TC-1/TC-2) and to calibrate/demonstrate the induced-memory-pressure fixture (TC-3). Neither is imported by, or reachable from, any production module, endpoint, or UI surface — both docstrings explicitly disclaim reintroduction ("never reintroduced into the shipped module"). This is the standard reference-implementation/golden-oracle test pattern, not a second production producer — Data Contract Step 1's "new function that computes the same value independently" targets a second *serving* path, which this is not. |
| Index series (`app.engine.indexes.compute_index_series`, `GET /api/indexes`) | OK — unaffected | Blueprint diff only removes the `[TARGET, iter-13 building]` tag (iter-13 already evaluator-confirmed); no code in this iteration's diff touches `app/engine/indexes.py` or any indexes endpoint. |
| Page performance budgets (`reports/perf-budgets.md`, measurement artifact, not a served value) | OK | `git diff --stat` shows exactly one file, `reports/perf-budgets.md` (+229/-0) — still the single canonical budgets artifact, no second file created. New content is (a) a transcription of iter-13's already-evaluator-confirmed readings (TC-8) and (b) the TC-5/TC-6/TC-7 full-deep-basis measurement, both attributed and reconciled against raw CSVs (`runs/goal-ops-hardening-iter-14/tc5-vm-samples.csv`, `tc5-health.csv`) rather than a second measurement path. |

No new displayed value or entity is introduced by this iteration (confirmed: no frontend file in the
diff; iter spec's "New information displayed" / "New user actions" / "UI surface changes" sections all
state "None"). Step 1's "new unregistered value" check therefore has nothing to evaluate.

## Information Architecture check

`Frontend Present: no` in the iteration spec is accurate: zero files under `apps/frontend/` appear in
`git status`/`git diff --stat`. The `reports/phase-goal-ops-hardening-iter-14-ui-surface-map.md` (present)
independently confirms this and enumerates the rendering surfaces affected only *behaviorally* (badge
never freezing, `/backtest` never showing the error card) — no new route, no new component, no nav change.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| J-07 (global readiness badge + `/backtest`) | OK — no new route | No nav file needed inspection: `blueprint.md`'s new Feature/journey-homes row (`runs/goal-session-ops-hardening/state/blueprint.md`, IA table) assigns J-07 to two ALREADY-existing homes — the global top-bar badge (rendered on every page per the pre-existing layout shell) and the pre-existing `/backtest` nav item. No new page/route/nav entry is added or claimed anywhere in the diff, the ui-surface-map, or the iter spec's "Blueprint conformance"/"UI surface changes" fields (both state "None"/"no new page/nav"). |

Nothing in this iteration's diff introduces a new page, duplicates an existing entity's home, or invents
a parallel shell — there is no new frontend surface to check reachability or duplication against.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The Data Contract row "Regime score, market phase, realized forward-returns" Notes cell currently
  reads the iter-14 sub-note as "PLANNED, not yet evaluator-confirmed" (`runs/goal-session-ops-hardening/state/blueprint.md`).
  This is expected process sequencing (decomposer registers the plan; the evaluator confirms after
  scoring) — not a defect. Flagged only so the next iteration's decomposer remembers to flip this cell to
  "built + evaluator-confirmed" once the goal-evaluator scores J-07/TC-1-TC-11, mirroring the iter-13
  `IndexSeriesCache` precedent already visible in the same table.
- No other coherence drift observed. This is an unusually clean iteration from a coherence standpoint: a
  single in-place function-body rewrite in its sole registered module, zero new endpoints, zero schema
  change, zero frontend surface, and two new test files whose reference implementations are correctly
  scoped as test-only oracles rather than shipped code paths.
