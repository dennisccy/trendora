# goal-ops-hardening-iter-60 Frontend Handoff

**Phase:** goal-ops-hardening-iter-60
**Date:** 2026-08-11
**Agent:** developer
**Status:** complete

## What Was Built

- **`/research/regime-lab`'s by-label and by-decile tables no longer show a misleading `n=0` sample-size
  chip with a LIVE drill-down link for a DEGRADED horizon.** This closes exactly the finding iter-59's
  audit confirmed empirically (F2, `reports/perf-budgets.md` TC-11 addendum): a horizon that degraded
  under memory pressure (`by_horizon[].status === "unavailable"`) was visually IDENTICAL to a genuinely
  empty cohort — same muted `NA` value, same `n=0 ⚠` `SampleLink` chip, still wrapped in an active
  `<Link>` into `/research/samples` for a cohort the payload itself says was never computed. Only a hover
  `title` tooltip told the two apart, so keyboard, touch, and screenshot review could not.
- **Fix shape:** `SampleLink` (`components/sample-link.tsx`) gained one new, additive, OPTIONAL prop:
  `unavailable?: boolean` (default `false`). When `true`, the component renders a plain, always-visible
  indicator — an `AlertTriangle` icon plus the text "Unavailable", styled `text-text-faint` (calm, not an
  alarm color — matches this project's existing "never hype" convention for routine transient-failure
  disclosures, e.g. `app/evidence/page.tsx`'s `DrawdownExpectationsPanel`) — INSTEAD of the active
  `<Link>`-wrapped `n=…` chip. No `data-testid="sample-link"` element renders in this branch (a
  `data-testid="sample-link-unavailable"` element renders instead), so any test or tooling keyed on the
  link's testid correctly sees it as absent for a degraded cell. Every OTHER call site of `SampleLink` in
  the codebase (8+ others across `_labs.tsx` and elsewhere) never passes the new prop, so they render
  byte-unchanged — confirmed by `npx tsc --noEmit` (the prop is optional, so omitting it type-checks
  identically to before) and by not touching any of those call sites.
- `RegimeReturnCell` (the only Regime-Lab component with a `SampleLink` — the paired MDD cell,
  `RegimeMddCell`, has never had one) now passes `unavailable={isRegimeCellUnavailable(cell)}`, a new
  one-line pure predicate (`cell.status === "unavailable"`) extracted into a new file,
  `lib/regime-cell-status.ts`, specifically so the degrade-vs-not decision is independently unit-testable
  — this frontend has no React/DOM rendering test harness (no `@testing-library/react`, not even a test
  runner in `package.json`; existing `lib/*.test.ts` files run as plain Node scripts under native TS
  type-stripping), so pulling the one meaningful boolean decision out of the component into a pure
  function is the established pattern this project already uses for exactly this situation (mirrors
  `lib/availability-empty-state.ts`'s `shouldShowAvailabilityEmptyState`, cited in its own docstring as
  the precedent).
- A genuine low-sample-but-not-degraded cell (`low_sample: true`, `status` absent, a real `n` below
  `min`) is completely unaffected: `isRegimeCellUnavailable` resolves `false` for it, so `SampleLink`
  takes its ORIGINAL branch, rendering the existing `n={n} ⚠` chip with its drill-down link exactly as
  before — byte-identical, not just visually similar.

## Files Changed

- `apps/frontend/components/sample-link.tsx` -- new optional `unavailable` prop on `SampleLink` (default
  `false`); renders a non-link "Unavailable" indicator (`data-testid="sample-link-unavailable"`) instead
  of the active chip/link when `true`.
- `apps/frontend/app/research/_labs.tsx` -- `RegimeReturnCell`'s `SampleLink` call now passes
  `unavailable={isRegimeCellUnavailable(cell)}`; new import of `isRegimeCellUnavailable` and of the
  `regime-cell-status` module.
- `apps/frontend/lib/regime-cell-status.ts` -- new file: the single pure predicate.
- `apps/frontend/lib/regime-cell-status.test.ts` -- new file, 3 checks: a degraded cell (`status:
  "unavailable"`, `n: 0`) is reported unavailable; a genuine low-sample cell (`status` absent, `n: 3`) is
  not; a clean well-sampled cell is not.

No change to `apps/frontend/lib/api.ts` this iteration — the `status?: "unavailable"` field on
`RegimeLabHorizonCell` was already added in iter-59; this iteration only changes how the frontend
CONSUMES it (a robustness/consumption fix, matching `blueprint.md`'s iter-60 note on the "Regime score,
market phase, realized forward-returns" row).

## Tests Run

- `npx tsc --noEmit` (from `apps/frontend/`) — clean, zero errors.
- `npx tsx lib/regime-cell-status.test.ts` — **3 passed** (`node` on this dev box lacks native TS
  type-stripping, same documented pre-existing limitation as every other `lib/*.test.ts` file in this
  project; `npx tsx` is the established local fallback — see e.g. `docs/handoffs/goal-ops-hardening-
  iter-58-frontend.md`).
- All 11 other pre-existing `apps/frontend/lib/*.test.ts` files re-run individually — all pass, no
  regression from touching `sample-link.tsx`/`_labs.tsx`.
- Live `curl` checks against a running dev server (`GET /research/regime-lab` → 200; `GET
  /api/research/regime-lab` and its `?view=pooled`/`?as_of=…`/`?view=nope` variants → 200/200/422 as
  expected) confirm the page and its backing endpoint both still serve correctly with these changes in
  place — see the dev handoff's "Live verification" section for the full command list.

## Known Issues

- **No live capture of an actual DEGRADED cell's rendered "Unavailable" indicator was taken this pass.**
  Producing one requires restarting the backend with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=regime_lab`
  armed and hitting a guaranteed cache-miss key, then restarting the backend clean again afterward — the
  exact drill iter-59's OWN dev pass performed for its TC-11 evidence capture
  (`runs/goal-ops-hardening-iter-59/evidence-drill/capture_degrade_ui.py`). Given this iteration's
  backend-level behavior is already proven deterministically (the new `test_compute_regime_lab_
  prologue_failure_degrades_honestly` unit test, plus the pre-existing per-horizon isolate-and-continue
  tests) and the frontend-level decision is proven by `regime-cell-status.test.ts`, a live visual capture
  showing the OLD `n=0` chip replaced by the NEW "Unavailable" indicator (with a control arm showing a
  genuine low-sample cell keeps its chip) is left to the browser-qa-agent's pass, which this iteration's
  TC-5/TC-6 test-first contract explicitly frames as a browser-level check.
- `RegimeLabRankIcRow` still has no matching `status?` field surfaced to a distinct UI treatment (carried,
  unchanged, from iter-59's own disclosed Known Issue — this iteration's IN SCOPE list named only the
  `by_horizon` cell's `SampleLink` suppression, not the rank-IC row).
