# goal-market-compass-iter-39 Frontend Handoff

**Phase:** goal-market-compass-iter-39
**Date:** 2026-09-02
**Agent:** developer
**Status:** complete

## What Was Built

Frontend-only AG-8 regression repair (no backend change). The Today page (`/`) fell to React's
error boundary on 21 of 23 historical `as_of` dates because two frontend files assumed every
stored manifest carries the iter-38 why-not detail fields, when in fact only 2 of 36 stored rows
(the ones minted at/after the iter-38 `rule_version` bump) do.

- `apps/frontend/lib/api.ts` — `CompassSelection.why_not_totals`, `WhyNotEntry.reason`,
  `.cap_rank`, `.cap` are now optional TS fields (`?:`), matching what was always true of the
  data `/api/compass` actually serves for pre-iter-38 manifests. Doc comments updated to state
  this explicitly.
- `apps/frontend/components/compass-focus-section.tsx` — the "Not priority" `Disclosure`
  summary no longer dereferences `selection.why_not_totals.excluded_by_cap_uncapped` unguarded;
  it calls a new pure helper (`whyNotSummary()`) that renders an honest degraded string when
  `why_not_totals` is absent, and the unchanged fully-counted string when present. No visual
  change for post-iter-38 manifests (currently only the 2026-08-12 frontier row).
- `apps/frontend/lib/why-not-summary.ts` (new) — the extracted pure summary-string function.
- `apps/frontend/lib/why-not-summary.test.ts` (new) — 6-check fixture test (TC-14).

## UI Evolution

- **New user-facing capability:** none new — this restores previously-working capability. The
  Today page loads on every historical `as_of` date again (it crashed to a full-page error card
  on 21 of 23 dates before this fix).
- **New information displayed:** none new. On pre-iter-38 manifests, the "Not priority"
  disclosure summary now reads an honest degraded count string
  (`Not priority (N shown — held-back counts unavailable for this manifest version)`) instead of
  crashing the whole page. On post-iter-38 manifests (currently only 2026-08-12, v10+), the
  fully-counted string is byte-identical to before this change — verified live in-browser.
- **New user actions:** none.
- **UI surface changes:** one string-variant change in an existing `Disclosure` summary inside
  the existing Next-session focus card on `/`. No new component, panel, or page. Uses only the
  existing `Disclosure` and `Card` primitives — no new UI component library usage.
- **Navigation changes:** none.
- **Visual/design-token changes:** none — text-only fix, no new color/spacing/effect.

## Visual verification (live, real browser — Chrome DevTools Protocol)

Backend + frontend started via the project's own `scripts/start-backend.sh` /
`scripts/start-frontend.sh` (ports 8255/3255, per this repo's deterministic per-project offset);
both stopped and confirmed dead after verification (`ps aux` clean, no leftover process).

- `/?asof=2026-08-11` (a genuine pre-iter-38 stored row — confirmed via direct API payload
  inspection that its `selection` object has no `why_not_totals` key and its `why_not[]` entries
  carry only `{ticker, failed_conditions}`): full Today page rendered top to bottom — state band,
  summary, what-changed, leadership rotation (its own honest "not recorded for this session"
  empty state, unrelated to this fix), Next-session focus section, manifest strip. No error
  boundary. Disclosure summary text, extracted via DOM query, read exactly:
  `Not priority (20 shown — held-back counts unavailable for this manifest version)`
- `/?asof=1996-01-02` (the oldest of the 21 previously-crashing dates): rendered without a
  crash; "Not priority" disclosure present.
- `/?asof=2026-08-12` (the frontier manifest, v10, a post-iter-38 row unchanged this iteration):
  rendered without a crash; disclosure summary text read the unchanged, fully-counted string:
  `Not priority (20 shown of 52 held back — 27 cap-excluded, 25 below-floor near-miss)`
  (27/25 matches the values already measured and recorded in `blueprint.md`'s iter-38 note).
  Expanded the disclosure and confirmed a cap-excluded entry's "ranked #N of the above-floor
  names, cap 20" lead-in sentence still renders — no regression on the path this iteration
  doesn't touch.
- All 21 previously-crashing `as_of` dates confirmed `GET /api/compass?as_of=<date>` -> HTTP 200
  (curl sweep, not sampled).

## Design system compliance

No new colors, spacing, or effects — pure text-content change inside an existing `Disclosure`.
No new component introduced; existing shadcn-style `Disclosure`/`Card` reused verbatim.

## Known Issues

- Full click-path acceptance for the seven target journeys (J-02, J-03, J-06, J-08, J-11, J-13,
  J-14) and the remaining 18 of 21 dates, plus the deterministic replay lane re-run, are
  browser-qa-agent's scope per this project's established pipeline convention (golden replay and
  full journey acceptance are downstream-agent responsibilities — not run by the developer
  agent). This handoff's own live verification (above) is a targeted developer-level sanity
  check, not a substitute for that full pass.
- `apps/frontend/.next-verify/` (a pre-existing, spec-acknowledged tracked build-artifact
  directory, not addressed by this iteration) picked up diffs from the TC-15 verification build
  run.
