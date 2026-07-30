# goal-ops-hardening-iter-36 Frontend Handoff

**Phase:** goal-ops-hardening-iter-36
**Date:** 2026-07-30
**Agent:** developer
**Status:** complete

## What Was Built

Mechanical wiring only — zero new logic. The already-generic, already-exported `resolveLabLoadPanel` /
`useElapsedSeconds` / `SlowComputeNotice` (`apps/frontend/lib/lab-load-panel.ts`, proven correct at iter-33:
13/13 resolver tests, a line-level Retry trace for Regime Lab) is now wired into the 4 sibling research lab
pages that previously rendered a bare, unlabelled skeleton with no retry affordance on a cold/slow load or
a genuine backend-unavailable condition:

- **`FactorLabPage`** (`/research/factor-lab`, `apps/frontend/app/research/_labs.tsx`) — previously
  `state.kind === "loading" ? <LabSkeleton /> : null`, `ResearchError` called WITHOUT `onRetry` (no retry
  existed). Now matches Regime Lab exactly: a labelled "Still computing — Ns elapsed" card with a spinner
  once the wait crosses the grace window, and a working Retry button on the error card.
- **`PhaseSeverityLabPage`** (`/research/phase-severity-lab`) — same bare pattern before, same fix.
- **`RegimePhaseFactorPage`** (`/research/regime-phase-factor`) — a DIFFERENT shape from the other three: it
  uses its own inline "Backend unavailable" error card (not `<ResearchError>`) and `CombinationSkeleton`
  (not `LabSkeleton`). The SAME computing/error/retry SEMANTICS were wired into this page's EXISTING markup
  shape — its established visual/test-id contract (`data-testid="regime-phase-factor-section"` etc.) is
  unchanged; only a `SlowComputeNotice` above `CombinationSkeleton` during the computing state, and a new
  Retry button (`data-testid="rpf-error-retry"`) inside its own error card, were added.
- **`SeverityVelocityPage`** (`/research/severity-velocity/page.tsx`) — its own file, not inside `_labs.tsx`.
  Same fix as `FactorLabPage`/`PhaseSeverityLabPage`. `resolveLabLoadPanel` is imported directly from
  `@/lib/lab-load-panel` (it is not re-exported from `_labs.tsx` — only imported there — so this file
  sources it from its own module, the same way `_labs.tsx` itself does); `SlowComputeNotice` and
  `useElapsedSeconds` ARE re-exported from `_labs.tsx` and are imported from there, matching this file's
  existing `LabSkeleton`/`ResearchError` import style.

## New User-Facing Capability

On all 4 pages: a cold or slow load now shows a labelled "Still computing — Ns elapsed" card with a spinner
and honest explanatory copy instead of a bare unlabelled skeleton (identical copy/component to Regime Lab —
no new information is displayed, no new copy was authored), and a genuine backend-unavailable state shows a
working **Retry** button that safely re-enters the loading state (never a second frozen error card).

## Files Changed

- `apps/frontend/app/research/_labs.tsx` -- `FactorLabPage`, `PhaseSeverityLabPage`,
  `RegimePhaseFactorPage`: added `attempt` state, `useElapsedSeconds`, `resolveLabLoadPanel`-derived
  `panel`, `attempt` in each fetch effect's dependency array, `SlowComputeNotice` on the computing state,
  and a Retry action on the error state.
- `apps/frontend/app/research/severity-velocity/page.tsx` -- same pattern for `SeverityVelocityPage`.

No change to `lib/lab-load-panel.ts` or `lib/lab-load-panel.test.ts` (already proven correct — wiring only,
per the plan's explicit "no change to `resolveLabLoadPanel`'s own resolution logic" constraint).

## Tests Run

- `npx tsc --noEmit -p tsconfig.json` (from `apps/frontend`): **0 errors** (one pre-existing narrowing issue
  in `RegimePhaseFactorPage` — TS couldn't narrow `data` through a `panel.kind` check the way it could
  through the original `!data` check — fixed by keeping the branch condition as `!data` and using
  `panel.kind === "computing"` only INSIDE that branch to decide whether to also render
  `SlowComputeNotice`).
- `npx tsx lib/lab-load-panel.test.ts`: **13 passed** (unaffected, confirms the resolver itself is untouched).
- Live verification: started the real frontend via `scripts/start-frontend.sh` (a fresh `next build` was
  triggered since `.next` was stale relative to the edited sources) against the real backend. `GET` on
  `/research/factor-lab`, `/research/phase-severity-lab`, `/research/regime-phase-factor`,
  `/research/severity-velocity`, `/research/regime-lab` (unaffected, spot-checked as a control) all returned
  HTTP 200 with correct page titles in the HTML and no `Application error` / `__next_error__` markup.
  Process stopped cleanly afterward.

## Known Issues

- No component-level unit tests exist for `_labs.tsx`'s page components themselves (this project has no
  test framework installed for `.tsx` component testing — only `lib/*.ts` pure-function tests run via
  Node's native TS stripping). The wiring's actual rendered behavior (labelled computing card timing, Retry
  click re-entering loading, `CombinationSkeleton` still rendering) was verified by HTTP-200 + title checks
  only, not a full browser interaction trace — the plan assigns TC-5/TC-6's full browser verification
  (cold-load screenshot, error-state screenshot, Retry click trace) to the browser-qa-agent stage.
- `RegimePhaseFactorPage`'s Retry button uses a NEW `data-testid="rpf-error-retry"` (no prior convention
  existed on this page for a retry action) — browser-qa should target this test id.
