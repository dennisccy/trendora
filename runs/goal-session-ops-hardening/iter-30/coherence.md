# Iteration 30 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-30
**Date:** 2026-07-29
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

The iteration's entire product diff (`git diff 9fdff7b3`) touches exactly five files:
`README.md`, `apps/backend/app/config.py`, `apps/backend/app/engine/forward_testing.py`,
`apps/backend/tests/test_forward_testing_aggregates_streaming.py`, `config.yaml` — plus an
append-only dated section in `reports/perf-budgets.md`. No other backend or frontend file changed
(confirmed via `git diff --stat` against the snapshot SHA and cross-checked against `git status`).

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Regime score, market phase, realized forward-returns (`compute_forward_aggregates`) | OK | `apps/backend/app/engine/forward_testing.py:857-1102` |
| Page performance budgets (never-regress measurements) | OK | `reports/perf-budgets.md:3870-4022` (appended section only) |

Detail on the first row: the diff restructures `compute_forward_aggregates`'s internal accumulation
by adding two **private** helpers in the same module — `_forward_agg_runs_with_fr` (`forward_testing.py:857-866`)
and `_forward_agg_slice_map` (`forward_testing.py:869-891`) — both called only from inside
`compute_forward_aggregates` itself (`forward_testing.py:975, 1005`), never from a route, service, or
any other module. The function keeps its exact pre-iteration signature and remains the sole producer
called from all three pre-existing sites: `GET /api/backtest`, MCP `query_backtest`, and the ingest
finalize warm (`data_manager.py`, unchanged this iteration — not in the diff). No new endpoint is
added; no UI file changed (`Frontend Present: no` in the spec, confirmed by the diff and by
`reports/phase-goal-ops-hardening-iter-30-ui-surface-map.md`, which classifies every changed file as
backend-internal or config). This is a bounded-memory rewrite of one function's own containers, not a
second computation path — it matches exactly what the blueprint's iter-30 note (added *ahead of
dispatch*, `state/blueprint.md` line 341) pre-registered: "SAME canonical producer
(`compute_forward_aggregates`), SAME three call sites … no schema change, no new field, no second
producer." A fixture-backed byte-identity test suite (`test_compute_forward_aggregates_chunked_equals_reference_across_run_chunk_widths`
and neighbors, `test_forward_testing_aggregates_streaming.py:376+`) asserts the new chunked path
against the pre-existing un-chunked `_reference_compute_forward_aggregates` oracle, so this is a
verified re-format/re-derivation of the SAME value, not a duplicate.

The new `walk_forward.forward_agg_run_chunk` config key (`config.py:768`, `config.yaml:806`) is a
tuning knob consumed only inside `compute_forward_aggregates` — not a displayed value, not a second
Data Contract entry.

Second row: `reports/perf-budgets.md` gains new dated sections (a mechanical re-measurement pass plus
a J-06 PASS/WARN scoring table) appended to the SAME single artifact the blueprint already registers
as the sole "Page performance budgets" home — no second budgets file, no second measurement producer.

No new displayed value or entity is introduced by this iteration (spec's own "New information
displayed: None" / "Data-contract additions: None" are corroborated by the diff).

## Information Architecture check

No new page, route, nav entry, or UI file exists in the diff. `apps/frontend/` has zero changes
against the snapshot SHA. The ui-surface-map (`reports/phase-goal-ops-hardening-iter-30-ui-surface-map.md`)
independently reaches the same conclusion, classifying all five product files as
backend-internal/config with no route/component/API-contract impact.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new UI surface this iteration) | OK | N/A — no frontend file in diff; nav/sidebar untouched |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `README.md` gains one sentence describing an Evidence-panel graceful-degradation fallback text
  ("Unavailable — monitored and refreshed as new data arrives.") that is not itself part of this
  iteration's diff to `evidence.py` or the frontend Evidence page (those files are unchanged relative
  to the snapshot SHA — they sit outside this iteration's scope entirely, as pre-existing working-tree
  state). This is documentation catch-up for already-existing behavior, not a new code path or a new
  Data Contract value; flagging only so the next iteration's decomposer is aware the README edit
  landed alongside an otherwise backend-only iteration.
- No other advisory issues found. The iteration is a clean, narrowly-scoped accumulator-bounding
  refactor that matches its own blueprint pre-registration almost verbatim.
