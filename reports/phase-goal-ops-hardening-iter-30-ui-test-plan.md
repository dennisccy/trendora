# Phase goal-ops-hardening-iter-30 — UI Test Plan

**Status:** N/A — Backend-only phase. No UI tests required.

## Basis

- `runs/goal-ops-hardening-iter-30/plan.md` states `Frontend Present: no` and "zero UI/frontend files touched this iteration."
- `docs/phases/goal-ops-hardening-iter-30.md`'s Frontend / New user-facing capability / New information displayed / New user actions / UI surface changes sections are all explicitly "None."
- `reports/phase-goal-ops-hardening-iter-30-user-visible-changes.md` and `reports/phase-goal-ops-hardening-iter-30-ui-surface-map.md` both classify this iteration as N/A backend-only: the diff bounds three in-RAM accumulators inside `compute_forward_aggregates` (`apps/backend/app/engine/forward_testing.py`) and adds a config knob (`apps/backend/app/config.py`, `config.yaml`), with byte-identity tests proving the served payload to `/api/backtest` and MCP `query_backtest` is unchanged. No route, component, form, chart, modal, table, or CSS changed.
- The functional test plan (`reports/qa/goal-ops-hardening-iter-30-test-plan.md`) covers this iteration's actual verification surface: API/unit tests (TC-01–TC-04), deterministic replay/artifact checks (TC-06–TC-09), and exactly one browser test — TC-05, a regression spot-check of the pre-existing `/research/factor-lab` page. TC-05 is owned by the functional/browser-qa test plan, not this UI test plan, because it verifies that an *unrelated, unchanged* existing page still renders correctly after a shared-pattern backend refactor — it is not testing any new or changed UI surface produced by this iteration.

No UI test cases are generated for this phase.
