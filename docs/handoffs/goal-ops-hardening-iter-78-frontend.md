# goal-ops-hardening-iter-78 Frontend Handoff

**Phase:** goal-ops-hardening-iter-78
**Date:** 2026-08-13
**Agent:** developer
**Status:** complete

## What Was Built

- **Live staleness tick on the global readiness badge and preflight banner.** The "as of Ns ago"
  annotation (added iter-77, shown next to the top-bar `Ready` pill and on the preflight strip)
  previously only updated when a new `GET /api/health` poll landed -- since the badge backs off to
  a 30-second poll cadence once steady-state `Ready`, the annotation could visibly freeze for up to
  30 seconds even though real time was passing. It now ticks every second between polls, so the
  displayed age is always accurate.
- No new field, no new payload key, no new page, panel, or user action. Purely a client-side
  re-derivation of the already-served `stale_for_s` value.

## Changed Behavior

- **Readiness badge / preflight banner staleness annotation**: previously froze at the last-polled
  value until the next poll (up to 30s stale-looking). Now increases smoothly every second between
  polls, fed through the SAME existing `formatStaleAnnotation` formatter (no second formatter, no
  second poll).

## Files Changed

- `apps/frontend/components/readiness-provider.tsx` -- records each poll's `stale_for_s` base plus
  the client wall-clock time it was received, and runs a new independent 1-second `useEffect`
  interval that re-derives the live value and calls the existing `setStaleForS`. The exposed
  `ReadinessContextValue.staleForS` field is unchanged in shape/type/consumers.
- `apps/frontend/lib/staleness-tick.ts` (new) -- pure `deriveLiveStaleForS(baseStaleForS,
  receivedAtMs, nowMs)`. No formatting; the derived number is still fed through
  `lib/staleness-annotation.ts`'s `formatStaleAnnotation` as the single formatting authority.
- `apps/frontend/lib/staleness-tick.test.ts` (new) -- unit tests (plain-`node` convention, mirrors
  `lib/staleness-annotation.test.ts`), covering: a positive base ticking up correctly (TC-3); a
  `null` base never ticking (failed/not-yet-landed poll); `stale_for_s === 0` (fresh/synchronous
  compute) never ticking upward (TC-4); negative/non-finite bases passed through unchanged so
  `formatStaleAnnotation`'s own guards still catch them; a missing/invalid receipt anchor falling
  back to the unticked base; elapsed time never going negative.
- `health-badge.tsx` and `preflight-banner.tsx` -- **unchanged**. Both already consumed `staleForS`
  purely via `useReadiness()` + `formatStaleAnnotation()`; since the provider now re-renders every
  tick with an updated value through the SAME context field, no consumer edit was needed.

## Backend-Only Items

None -- this iteration's frontend work is a self-contained client-side re-derivation of an
already-served value; no new backend endpoint or field.

## Incomplete Items

- **J-09's "background compute in flight" walkthrough gallery frame** (the per-iteration demo
  capture, distinct from this session-level `reports/goal-session-ops-hardening-demo.json`, which
  already captures the scene correctly) still needs its OWN per-iteration demo JSON step
  (`reports/phase-goal-ops-hardening-iter-78-demo.json`) to target a discriminating `expect` and an
  elevated `timeout_ms` once that file is authored later this iteration by demo-narrator -- see the
  main dev handoff's "Known Issues" for the full explanation of why this could not be pre-seeded
  from the developer stage.

## Config and Environment Changes

None.

## Known Limitations

- The staleness tick is a fixed 1-second client-side interval, independent of the (config-derived,
  up to 30s) poll cadence -- this is intentional (the whole point is to keep ticking between slower
  polls), not a bug.
- `node lib/staleness-tick.test.ts` could not be executed directly on this dev box (pre-existing
  Node build limitation, no TypeScript type-stripping support -- documented in an earlier
  iteration's handoff); the assertions were verified via a scratch JS mirror instead (see the main
  dev handoff's "Tests Run" section for detail). The committed test file follows the project's
  established convention and will run in the CI/QA Node environment.
