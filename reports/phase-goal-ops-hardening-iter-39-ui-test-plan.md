# Phase goal-ops-hardening-iter-39 — UI Test Plan

**Status:** N/A — Backend-only phase. No UI tests required.

## Basis for this determination

- `runs/goal-ops-hardening-iter-39/plan.md` states `Frontend Present: no` and its "UI Evolution"
  section reads: "N/A -- Frontend Present: no. No new user-facing capability, no new information
  displayed, no new user actions, no UI surface changes, no navigation changes. J-04/J-05
  verification confirms already-shipped panels (global readiness badge, `/data` Run History,
  `/data` Coverage payload) behave correctly under a genuine live restart — it does not change
  what they render."
- `docs/phases/goal-ops-hardening-iter-39.md` metadata states `**Frontend Present:** no`; its
  "Frontend", "New user-facing capability", "New information displayed", "New user actions", and
  "UI surface changes" sections are all `None`. "Product surface delta" states: "No visible
  product surface change. This iteration is verification + backend hardening ... on already-shipped
  behavior."
- `reports/phase-goal-ops-hardening-iter-39-user-visible-changes.md` confirms no file under a
  frontend app directory appears in this iteration's changed-files list — only backend Python
  modules (`data_manager.py`, `main.py`, new `logging_config.py`, backend tests) and
  framework/tooling scripts (`demo_runner.py`, `merge_ui_test_results.py`, `replay-lane.sh` and its
  tests) were touched.
- `reports/phase-goal-ops-hardening-iter-39-ui-surface-map.md` confirms no route, endpoint response
  shape, or frontend component changed; its only table rows are traceability entries marked "No
  change (read-only verification)" for the `/data` Run History panel, `/data` Coverage payload
  panel, and the global readiness badge — used to visually confirm a genuine `kill -9` + restart
  behaves correctly, not because any of them were modified.

This iteration closes J-07's remaining step (a throwaway-DB induced-pressure drill proving a
`MemoryError` inside the aggregate-warm stage is caught by the existing per-item isolation handler
while `/api/health` and a cached `/api/backtest` read keep answering), repairs the deterministic
replay lane (new `BLOCKED` verdict class, backend-health pre-probe, reconciliation-footer fix), an
env-toggle truthy guard, a root-logger configuration fix, a `read_pool()` in-situ re-measurement,
and a genuine live `kill -9` + restart re-verification of J-04/J-05 — all backend/tooling work or
read-only confirmation of already-shipped, unchanged panels. No route, component, or API contract
changed. Functional verification of this iteration's work (drill evidence, health/backtest polling
during the drill, replay-lane `BLOCKED`/`FAIL` behavior, env-toggle unit test, logging test,
`read_pool()` measurement, live restart evidence) belongs to the backend/QA test plan, not a UI
test plan, since there is no new or changed UI surface to click through. Existing test coverage for
J-04, J-05, and J-07's UI-facing behavior (from prior iterations) already covers the panels named
above and remains valid unchanged.
