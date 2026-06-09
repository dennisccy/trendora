# goal-i_can_see_the_wealthy_future_forever-iter-26 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-26
**Date:** 2026-06-09
**Agent:** developer
**Status:** complete

## What Was Built

One surgical UX fix on `/data` (Data Manager) — no new page, route, panel, nav entry, component, or date
control. This is the iter-25 UT-11 fix for J-38.

- **J-38 Resume-without-key inline error.** In `ResumeControl`, when a needs-key Resume is submitted without a
  key and the backend returns 400, the unfinished-imports row now stays visible and a **visible inline
  `role="alert"` error** renders next to the Resume button. When no key was entered for a needs-key source the
  message is an actionable, source-specific prompt ("Enter the session key for <label> to resume."); otherwise
  it shows the backend's honest `detail`. A `data-testid="resume-error"` was added for deterministic browser
  capture.
- **Failed-resume never drops the row (defensive gate).** `onResumed` (which re-reads the resumed job into the
  live card) runs on SUCCESS only — it is inside the `try`, after the `await`, before the `catch`. A FAILED
  resume hits the `catch`, sets the inline error, and does NOT call `onResumed` or any overview reload, so the
  row stays in the Unfinished-imports panel. A clarifying comment documents this invariant.

## Files Changed

- `apps/frontend/app/data/page.tsx` -- `ResumeControl.handleResume` error handling (clearer message +
  no-reload-on-failure gate); the error `<span>` gains `data-testid="resume-error"`.

## Visual / Design

- Reuses the existing dense dark `/data` styling. The inline error uses the existing `role="alert"` +
  `text-neg` (danger) treatment already present on `ResumeControl` — no new color, spacing, typography, or
  effect tokens; no new component.
- States on the Resume control: **failed** (visible inline error, row STAYS), **success** (continues from
  `next_chunk_index`, live card refreshes), **busy** (existing spinner). No date input/state added (J-18
  preserved — exactly one date `<select>` on `/data`).

## Tests Run

- `cd apps/frontend && npx tsc --noEmit -p tsconfig.json` — clean (exit 0).
- No prod `next build` was run against the live dev `.next` (MEMORY `browser-qa-dead-shell-next-cache`). The
  env-fix gate (stop strays by port, `rm -rf apps/frontend/.next`, restart `next dev`, confirm
  `GET /_next/static/chunks/main-app.js` → 200 + health badge cleared) is QA's step before driving the UI.

## Known Issues

- The success-leg Resume capture (continuing from `next_chunk_index`) and the failed-leg UT-11 capture are
  browser-qa work; the frontend wiring needed for both is verified to type-check and the error path renders an
  asserted, testid-tagged inline alert.
- No other frontend change is required for J-37 / J-39 / J-35 — they are already built; this iter only captures
  their flows against the offline `seed` source + fixture.
