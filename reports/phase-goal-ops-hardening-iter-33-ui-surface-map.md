# Phase goal-ops-hardening-iter-33 — UI Surface Map

**Phase:** goal-ops-hardening-iter-33
**Date:** 2026-07-29
**Written by:** ui-impact-analyst

---

## File Classification (diff-to-ui-impact)

| File | Category | UI Impact | Explanation |
|------|----------|-----------|-------------|
| `incredible_auto_dev/scripts/start-frontend.sh` (symlinked as `scripts/start-frontend.sh`) | config / launch script | indirect — full-stack | No component/page code touched, but this script decides whether every page renders from a `next dev` (on-demand compiled, dev-overlay-capable) build or a genuine `next build`/`next start` production build. It is the "why changed" behind every row in the table below. |
| `incredible_auto_dev/scripts/measure-perf.sh` | config / documentation | none | Header-comment wording fix only (removes a now-moot caveat about not being able to detect `next dev`). No timing/measurement code changed, no UI surface touched. |
| `apps/backend/tests/test_start_frontend_script.py` (new) | backend-internal / test | none | New pytest smoke-test file proving the launcher's build-if-stale behavior via real subprocesses on a scratch port. Test-only, not shipped/served code. |
| `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py` | backend-internal / framework tooling | none | Widens an internal QA-report-merging regex (`_ROW_RE`) to accept `TC-`-prefixed rows alongside `UT-`. Affects only the automation pipeline's own merged report file, not the product application. |
| `apps/frontend/tsconfig.json` | config | none | Modified in the working tree (a scratch build-directory name, `.next-test-tc2-*`, appears in `compilerOptions.include` in place of the prior scratch entry). This is a TypeScript compiler include-path list, not rendered content — it has no effect on what any page displays. Not listed in the dev handoff's own "Files Changed" section. |

No `apps/frontend/app|components|lib/**/*.tsx` file changed. No `runs/goal-session-ops-hardening/journey-scripts/J-0*.json` file changed (all 8 golden scripts replayed PASS as-is against the fixed launcher, per the dev handoff's dry-run).

---

## Affected UI Surfaces

The launcher fix does not add, remove, or restyle any page/component — it changes the **build mode**
every existing page is served under. The concrete, testable effect is on the 11 pages the goal's J-06
journey already names as its step-1 targets: they now render from a real production build, and (if they
ever errored) would no longer show the Next.js dev-mode overlay pill. Content, data, and layout are
unchanged for all 11 rows below (confirmed byte-identical served payload per the phase's AG-3 requirement).

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|------------|------------|-------------|
| `/` | Dashboard (regime banner + sector/theme strips) | Changed behavior (serving mode) | `start-frontend.sh` now serves a real `next build`/`next start` instead of `next dev` | Load `/` via the instance started by `scripts/start-frontend.sh` (not `dev.sh`); open DevTools console and confirm zero error-level entries and no Next.js dev-overlay pill; confirm the regime banner and sector/theme strips render the same values as before |
| `/stocks` | Stock leaderboard table | Changed behavior (serving mode) | Same launcher fix | Load `/stocks`, confirm the leaderboard table populates with rows and the page loads without the dev-overlay pill appearing on any transient error |
| `/stocks/AAPL` | Stock detail (ticker header + price/MA chart) | Changed behavior (serving mode) | Same launcher fix | Navigate to `/stocks/AAPL`, confirm the ticker header and price/MA chart render, and DevTools console shows zero error-level entries |
| `/sectors` | Sector score table | Changed behavior (serving mode) | Same launcher fix | Load `/sectors`, confirm the sector score table renders with the same columns/values as the pre-fix baseline |
| `/themes` | Theme score table | Changed behavior (serving mode) | Same launcher fix | Load `/themes`, confirm the theme score table renders with the same columns/values as the pre-fix baseline |
| `/data` | Coverage / availability panel | Changed behavior (serving mode) | Same launcher fix | Load `/data`, confirm the coverage snapshot and availability panel render with populated values, not a blank/error state |
| `/evidence` | Certified-claims ledger list | Changed behavior (serving mode) | Same launcher fix | Load `/evidence`, confirm the certified-claims list renders with the same entries as the pre-fix baseline |
| `/scanner-runs` | Scanner runs list | Changed behavior (serving mode) | Same launcher fix | Load `/scanner-runs`, confirm the runs list populates and each row's result count renders |
| `/backtest` | Evidence-by-horizon table | Changed behavior (serving mode) | Same launcher fix | Load `/backtest`, confirm the evidence-by-horizon table renders the same figures as the pre-fix baseline (AG-3: byte-identical values) |
| `/watchlist` | Watchlist table + x-ray panel | Changed behavior (serving mode) | Same launcher fix | Load `/watchlist`, confirm the watchlist table and x-ray panel render for the existing saved tickers |
| `/research/regime-lab` | Regime-lab decile table | Changed behavior (serving mode) | Same launcher fix | Load `/research/regime-lab`, confirm the decile table renders with the same figures as the pre-fix baseline |
| All 11 pages above | Browser DevTools console | Changed behavior (dev-overlay removed) | Production build never ships the Next.js dev-mode error-overlay pill | Open DevTools console on each of the 11 pages after load; confirm zero error-level console entries and no dev-overlay pill (TC-7) |

---

## Backend-Only Changes (No UI Impact)

- `incredible_auto_dev/scripts/measure-perf.sh` — header-comment wording correction only, no functional
  or measurement-code change — no UI surface affected.
- `apps/backend/tests/test_start_frontend_script.py` — new real-subprocess smoke test (TC-1/TC-2/TC-3)
  proving the launcher's build-if-stale/never-fallback-to-dev behavior — a test file, not shipped/served
  code — no UI surface affected.
- `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py` — widened `_ROW_RE` regex so a
  `TC-`-prefixed failing row survives merging into the automation pipeline's merged QA report — affects
  only the pipeline's own internal report file, not the product application — no UI surface affected.
- `apps/frontend/tsconfig.json` — TypeScript compiler `include` path list; a scratch build-directory
  name appears/changes in this list, but this is compiler configuration, not rendered content — no UI
  surface affected.
- `reports/perf-budgets.md` — no `## Iteration 33` section exists yet at time of this analysis (confirmed
  by inspection); the formal TC-4/TC-5 browser-measured sweep is the browser-qa-agent's pending step, not
  a change delivered by this dev handoff. This artifact is a measurement report, not a rendered product
  page, so it would carry no UI surface impact even once appended.

---

## Summary

- **Frontend surfaces changed:** 0 (no page/component source file touched)
- **Frontend surfaces affected by a serving-mode change (indirect):** 11 (the J-06 step-1 page set)
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 4 (`measure-perf.sh`, `test_start_frontend_script.py`,
  `merge_ui_test_results.py`, `apps/frontend/tsconfig.json`)
