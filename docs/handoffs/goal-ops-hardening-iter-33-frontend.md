# goal-ops-hardening-iter-33 Frontend Handoff

**Phase:** goal-ops-hardening-iter-33
**Date:** 2026-07-29
**Agent:** developer (frontend-ux role)
**Status:** complete

## What Was Built

This iteration's frontend-facing work is entirely about **how the frontend is served for automated
evidence capture/measurement**, not the product UI itself. Per the plan's own UI Evolution section: no new
user-facing capability, no new information displayed, no new user actions, no UI surface change.

- **`scripts/start-frontend.sh` now genuinely serves production mode** (build-if-stale, then
  `next start` — never `next dev`). See the dev handoff (`docs/handoffs/goal-ops-hardening-iter-33-dev.md`)
  for the full technical write-up; this file focuses on the user-visible consequence.
- **The only visible-but-incidental difference**: pages served through this launcher no longer show the
  Next.js dev-mode error-overlay pill (a defect-fix side effect of running a real production build, not a
  new capability). No page's rendered content, layout, or behavior changed.
- **No `apps/frontend/**/*.tsx` source changes were needed** — a real `next build` against the current tree
  compiled and type-checked cleanly on the first attempt. Next 15's stricter production type-checking
  surfaced zero errors that dev mode had been tolerating.
- **No golden-script repairs were needed** — all 8 stored journey-scripts (J-01, J-03, J-04, J-05, J-06,
  J-07, J-08, J-09) replayed PASS against the now-prod-mode frontend in a pre-handoff dry run (see the dev
  handoff's "Golden-script dry-run replay" section). The dev→prod switch introduced no markup diff (no
  dev-overlay pill, no CSS-module class-name shift) that broke any stored assertion.

## Files Changed

- `incredible_auto_dev/scripts/start-frontend.sh` -- launcher rewrite (build-if-stale + `next start`); see
  dev handoff for the full design.
- `incredible_auto_dev/scripts/measure-perf.sh` -- header-comment correction only, no code change.

No page, component, or style file under `apps/frontend/app|components|lib` changed.

## Tests Run

Same as the dev handoff: `apps/backend/tests/test_start_frontend_script.py` (3 passed, real-subprocess
smoke tests), plus a pre-handoff manual verification (real `next build` + `next start` on the actual
default `.next`, `curl` 200 on all 11 J-06 pages, and an 8/8 PASS golden-script dry-run replay against the
live prod-mode frontend on :3255).

## Known Issues

- The formal, dated real-browser TTI + on-load-latency sweep (TC-4/TC-5, `reports/perf-budgets.md`) is the
  browser-qa-agent's job, not this handoff's — see the dev handoff's "Known Issues" for the exact division
  of labor.
- No UI/visual work of any kind was in scope this iteration (per the plan's own Visual Requirements: N/A);
  none was done.

---

# Fix Notes — QA FAIL retry (2026-07-29): real UI work landed this pass

The statement above ("no page, component, or style file changed") described the FIRST pass only. QA's
re-validation then found a genuine user-visible defect on an existing page, so this pass **does** change
product UI. Full technical write-up is in `docs/handoffs/goal-ops-hardening-iter-33-dev.md`'s Fix Notes;
this section covers only what a user sees.

## The defect (browser QA UT-11, P1)

`/research/regime-lab` is fed by a derivation that is computed once per dataset over the whole stored
history. On the FIRST read after a data change that takes 60-90 seconds. During the whole of that window
the page showed nothing but an unlabelled grey animated placeholder — no explanation, no elapsed time, no
error, no way to retry. A first-time visitor could not tell "still working" from "broken", which is exactly
the honest-status expectation the rest of this product holds itself to.

## What a user sees now

1. **A short wait is unchanged.** Under 3 seconds the page still shows the plain skeleton — an ordinary
   fast load does not flash alarming copy.
2. **A long wait is explained.** Past 3 seconds a warning-toned card appears above the skeleton:
   *"Still computing — 12s elapsed"* with a plain-language paragraph saying the view is derived once per
   dataset from the whole stored forward-return history, that the first read after a data change computes
   it (a minute or two on a deep history), that every later read is served from the stored result, and that
   the table will appear by itself. The counter is this page's OWN measured wait — it is never a predicted
   finish time, and no partial or placeholder figure is ever shown in the meantime.
3. **The notice disappears** the moment the data lands, and the normal decile / regime-label tables render
   exactly as before (byte-identical figures — nothing about the data path changed).
4. **A failed read is now escapable.** The existing "Backend unavailable" card gained a **Retry** button on
   this page. Clicking it re-runs the read in place — no page reload, no lost as-of/mode selection.

## UI surface / navigation

- No new page, no new route, no nav change, no new user-facing capability, no new figure displayed.
  Reachability is unchanged (Research → Regime Lab, still 2 clicks).
- Styling uses existing design tokens only: the notice reuses the same warning-toned card treatment and
  spinner as the existing "Warming up — historical evidence still loading" state, so it reads as part of
  the same family; the Retry button reuses the exact button class already used by `app/error.tsx` and
  carries hover, focus-visible and active states.
- Responsive/dark-mode behaviour is inherited from the shared `Card` primitive — no new layout rules.

## Files changed (this pass)

- `apps/frontend/lib/lab-load-panel.ts` -- NEW. The pure resolver deciding which honest pre-data state a
  lab shows (skeleton / labelled computing / retryable error / data) + the elapsed-time label formatter.
- `apps/frontend/lib/lab-load-panel.test.ts` -- NEW. 13 unit tests pinning that rule (RED before the module
  existed, GREEN after).
- `apps/frontend/app/research/_labs.tsx` -- added `SlowComputeNotice` + `useElapsedSeconds`; `ResearchError`
  gained an optional `onRetry` (call sites that pass none render exactly as before); `RegimeLabPage` now
  renders from the resolver and offers Retry.

## Evidence

- `reports/qa/goal-ops-hardening-iter-33-evidence/UT-11-fix-computing-notice.png` — the labelled
  "Still computing — 6s elapsed" state on a deliberately slowed read.
- `reports/qa/goal-ops-hardening-iter-33-evidence/UT-11-fix-error-retry.png` — the error card with Retry.
- `reports/qa/goal-ops-hardening-iter-33-evidence/UT-11-fix-warm-load.png` — the ordinary warm load,
  visually unchanged.
- All 8 golden journey scripts replayed 8/8 PASS against the rebuilt prod-mode frontend; all 11 J-06 pages
  return HTTP 200.

## Known Issues (this pass)

- The 60-90 s cold compute itself is unchanged — this makes the wait honest and escapable, not shorter.
- The sibling research labs (`/research/phase-severity-lab`, `/research/regime-phase-factor`, …) still show
  a bare skeleton while loading. They were not in QA's blocker list and their reads are materially faster
  today, so they were deliberately left alone; the new resolver is generic enough for them to adopt.
