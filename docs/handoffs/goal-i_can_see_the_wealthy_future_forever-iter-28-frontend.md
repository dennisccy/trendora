# goal-i_can_see_the_wealthy_future_forever-iter-28 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-28
**Date:** 2026-06-10
**Agent:** developer
**Status:** complete

## What Was Built

The honest backend-readiness UI for J-40 — no new page, route, or nav entry. Everything reads ONE shared
readiness value (the single `GET /api/health` read), so the frontend never computes readiness itself and
there is no second readiness read in the client.

- **Single client readiness source (`components/readiness-provider.tsx`, new).** A `ReadinessProvider`
  context mounted in the app shell (`app/layout.tsx`) that polls `GET /api/health` and shares
  `{ state, warmup, loading }`. The poll cadence is CONFIG-DERIVED — it reads `poll_interval_seconds`
  (fast, while warming, so the flip to Ready shows within ~a poll of completion) and
  `poll_idle_interval_seconds` (backs off once Ready) from the payload. No client-side poll literal. On a
  network/non-200 it surfaces `unavailable` — never a fabricated "ok".
- **Three-state top-bar readiness badge (`components/health-badge.tsx`, extended).** Renders **Ready**
  (`ok` green dot), **Initializing… history n/m** (`warn` variant + animated pulse dot + monospace `n/m`
  progress), or **Backend unavailable** (`danger` red dot), driven by the shared readiness value. The
  existing provider / seed-date / symbol-count context badges are preserved. Lives in the EXISTING layout
  shell next to the global as-of switcher — no layout change.
- **Backtest / Research "warming up (n/m)" state (`components/warming-state.tsx`, new).** While readiness
  = `initializing`, `/backtest` and `/research` render a `WarmingState` card ("Warming up — historical
  evidence still loading (n/m)") instead of an error, an empty result, or a partial result presented as
  complete. Both pages add `readiness` to their fetch effect deps, so they AUTO-POPULATE the moment the
  warm-up finishes (the flip to `ready` re-runs the fetch). The warming state adds NO date state — J-18
  preserved.

## Files Changed

- `apps/frontend/lib/api.ts` — `ReadinessState`, `WarmupProgress`; extended `HealthStatus` with
  `readiness`, `warmup`, `poll_interval_seconds`, `poll_idle_interval_seconds`.
- `apps/frontend/components/readiness-provider.tsx` (new) — shared readiness poll + context.
- `apps/frontend/components/health-badge.tsx` — three honest states + live progress.
- `apps/frontend/components/warming-state.tsx` (new) — the warming card + `shouldShowWarming` predicate.
- `apps/frontend/app/layout.tsx` — mount `ReadinessProvider` around the shell.
- `apps/frontend/app/backtest/page.tsx` — warming gate + auto-populate on readiness flip.
- `apps/frontend/app/research/page.tsx` — warming gate (all three labs) + auto-populate.

## Design / Component Notes

- Reuses the existing `Badge` component variants (`ok` / `warn` / `danger` / `default` / `accent`) — no
  raw HTML for the states. The Initializing pulse reuses the established `animate-pulse` dot pattern.
- The warming card reuses the existing `Card` component + `lucide-react` `Loader2` spinner, matching the
  dense dark analytical style; the `n/m` progress is monospace (`num`).
- States handled: loading (initial poll → "Checking backend…"), ready, initializing-with-progress,
  unavailable; on Backtest/Research: warming(n/m) vs populated. Warming is never an error and never a
  partial-as-complete result.

## Tests Run

- `npx tsc --noEmit` — clean (0 errors).
- Live browser-path behavior was verified at the API level (the badge/warming states read `GET
  /api/health`): a cold-boot reported `initializing history 0/6 → 6/6` then `ready`, with `/api/dashboard`
  serving 200 throughout — so the badge would show Initializing with live progress, the analytics pages
  would show "warming up (n/m)", and both would flip to populated/Ready on completion.

## Known Issues

- ESLint is not configured in `apps/frontend` (running `next lint` prompts interactively) — pre-existing,
  unrelated to this iteration. Typecheck is the enforced gate and is clean.
- The live three-state browser walkthrough (cold-boot badge flip + warming pages) is left to browser-QA;
  bring the frontend up cleanly by port + `rm -rf apps/frontend/.next` + confirm `main-app.js` 200 BEFORE
  driving the UI (episodic memory `browser-qa-dead-shell-next-cache`; a dead-shell is an environmental
  SKIP, not a code FAIL).
