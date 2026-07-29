# Phase goal-ops-hardening-iter-32 — UX Regression Review

**Date:** 2026-07-29

**Verdict:** UX-REGRESSION-PASS

Backend-only phase. No UI regression review required.

---

## Basis for the backend-only classification (verified, not just cited)

The phase spec states `Frontend Present: no`. Checked against the actual diff rather than taken on
faith:

```
git diff --stat -- apps/frontend
(empty — zero frontend files touched)

git diff --stat -- apps/backend
 apps/backend/app/engine/forward_testing.py         | 456 ++++++++++++++++-----
 apps/backend/tests/test_forward_testing.py         |  46 ++-
 .../test_forward_testing_aggregates_streaming.py   |  87 +++-
 3 files changed, 478 insertions(+), 111 deletions(-)
```

All three changed files (plus the new `reports/perf-budgets.md` dated section and the dev handoff,
both non-code artifacts) are backend engine/test files. No `.tsx`, `.ts`, or CSS file under
`apps/frontend/` differs from `HEAD`. `plan.md`, `docs/phases/goal-ops-hardening-iter-32.md`
("### Frontend — None this iteration" / "### New user-facing capability — None" / "### UI surface
changes — None" / "### Product surface delta — None visible to the user"),
`reports/phase-goal-ops-hardening-iter-32-user-visible-changes.md`, and
`reports/phase-goal-ops-hardening-iter-32-ui-surface-map.md` all independently agree: this iteration
restructures `compute_forward_aggregates`'s internal accumulation (replacing the unbounded `stock_obs`
list with bounded `_ExactMeanAcc`/`_GroupAcc`/`_ControlGroupBuilder`/`_AttributionAccumulator` state)
with a response payload proven byte-identical before/after by a 46-test reference oracle
(`test_forward_testing_aggregates_streaming.py`) — a pure reliability fix, not a feature.

## New Capability Discoverability

No new capability was added. `GET /api/backtest`, MCP `query_backtest`, and the ingest finalize warm
call sites stay byte-unchanged per the spec's own explicit contract, and the byte-identity oracle
(TC-2, 46/46 PASS per `reports/qa/goal-ops-hardening-iter-32-qa.md`) confirms it. There is nothing new
to place in navigation.

## Regression Risk

| Prior feature | Shared component | Risk level | Evidence |
|---|---|---|---|
| `/backtest` page (J-05/J-08, "Backtest evidence serves from storage only") | `compute_forward_aggregates` (`forward_testing.py`) via `GET /api/backtest` | **Low, verified** | Live Chrome MCP navigation to `/backtest` (`reports/phase-goal-ops-hardening-iter-32-ui-test-results.llm.md`, UT-J-07) rendered every restructured section — `by_bucket`, `by_setup`, `by_regime`, `by_vcp`, `excess`, `control_group` — with real non-NA numbers (e.g. Excess vs SPY `+0.60% n=749441`, Top-ranked cohort `+6.77% n=36316`), zero console errors, 6/6 fresh `GET /api/health` polls HTTP 200. Independently re-verified live in this review: `curl` to `/backtest` returns 200 and `/` (home) returns 200. |
| MCP `query_backtest` | same producer | N/A (not a UI surface) | Byte-identity oracle covers this call path's payload shape; no separate check needed. |
| Ingest finalize warm (background) | same producer | **Improved this iteration** | Live full-deep-basis warm across all 5 horizons, two independent trials, zero `MemoryError`, VmPeak flat at 2,691,600 kB / 57.2% headroom under the 6144 MB cap (`reports/perf-budgets.md` "Iteration 32" section, TC-4/TC-5 both PASS). |
| `compute_run_scorecard`'s own per-run `stock_obs` builder (`forward_testing.py:1832`) | same module, different accumulator | **Low, verified** | Source lines confirmed byte-unchanged by diff (TC-7); only its one `_attribution_slices` call line took the spec-authorized mechanical signature wrap; 20/20 `test_backtest_scorecard.py` PASS. |
| `/research/factor-lab` (the page that crashed the entire backend process in iter-30, fixed in iter-31) | Sibling accumulator in `research.py` — **not touched by this iteration's diff** (`git diff --stat` confirms `research.py` absent from the changed-files list) | **None — reconfirmed healthy** | Live spot-check performed for this review: `curl http://localhost:8255/api/research/factor-lab?all=true` → 200; `curl http://localhost:3255/research/factor-lab` → 200. No re-regression of the two-consecutive-iteration CRITICAL finding iter-30 caught and iter-31 fixed. |

Required-still-passing journeys J-01, J-03, J-04, J-05, J-08, J-09 all show PASS via deterministic
golden replay (`reports/phase-goal-ops-hardening-iter-32-regression-replay-results.md`, cited in
`reports/phase-goal-ops-hardening-iter-32-ui-test-results.md`, 7/7 overall including J-07), with zero
FAIL rows and zero reconciliation overturns per TC-9.

No `runs/goal-session-ops-hardening/iter-32/coherence.md` exists yet at review time — nothing to cite
there, and nothing in the QA report or UI test results contradicts it, so there is no "audit
contradiction" to flag.

## UI vs Backend Parity

| Backend capability (this iteration) | UI exposure |
|---|---|
| Bounded per-group/per-run/per-ticker accumulators (`_ExactMeanAcc`, `_GroupAcc`, `_ControlGroupBuilder`, `_AttributionAccumulator`) replacing the unbounded `stock_obs` list | N/A — internal implementation detail, correctly not surfaced; response payload byte-identical per the oracle |
| Live-scale accumulator-size test (TC-1) proving the bound holds at realistic scale | N/A — engineering proof, not a UI concern |
| `reports/perf-budgets.md`'s new "Iteration 32" VmPeak measurement section | N/A — an internal ops-engineering record per this session's existing convention, not a rendered UI surface |
| `_attribution_slices`'s signature lift (`stock_obs` → `acc`) | N/A — pure internal refactor; the three consumers (`compute_forward_aggregates`, `compute_run_scorecard`, the reference oracle) are all backend code, no UI-facing contract changed |

No gap. The only externally observable effect — the forward-aggregate warm and its two serving
endpoints no longer risk a `MemoryError` at scale — is a reliability property with no corresponding UI
element to add either way, exactly as `docs/phases/goal-ops-hardening-iter-32.md`'s own "New
information displayed: None" / "New user actions: None" sections state.

## Flags

### Hidden Capabilities
- None.

### Undiscoverable Capabilities
- None.

### Potential Regressions
- None identified. Zero frontend diff; `/backtest` live-verified rendering correctly with the
  restructured accumulators' real output; `/research/factor-lab` (the module previously responsible for
  a full-process crash in iter-30) reconfirmed healthy and untouched by this iteration's diff; all six
  required-still-passing journeys plus J-07 show PASS with zero FAIL rows.

### Visual Consistency
- Not applicable — no page, component, or style was added or modified this iteration.

## Recommendation

No action required.
