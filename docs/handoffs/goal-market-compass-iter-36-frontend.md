# goal-market-compass-iter-36 Frontend Handoff

**Phase:** goal-market-compass-iter-36
**Date:** 2026-09-01
**Agent:** developer
**Status:** complete

## What Was Built

The Today page's (`/`) Leadership rotation section is rewritten to render the SERVED
`session_delta.rotation.{sector,theme}` block from `GET /api/compass` directly, instead of filtering the
same `session_delta.changes` array the What-changed card above it already renders in full. See the main
dev handoff (`docs/handoffs/goal-market-compass-iter-36-dev.md`) for the backend producer-side detail —
this file covers only the UI surface.

- **Section body rewritten**: `apps/frontend/components/compass-leadership-rotation-section.tsx`. Two
  sub-sections ("Sector rotation", "Theme rotation"), each with two labelled sides ("Gaining"/"Losing")
  laid out `grid md:grid-cols-2` (matches `compass-state-band-card.tsx`'s existing breakpoint
  convention). Each row shows the label (a `Link` to the existing `drill_href`, unchanged behavior),
  `from → to (±delta) · direction_word`. An empty side renders its own dedicated empty-state sentence
  (e.g. "No sector lost ground beyond the threshold this session.") instead of a blank area. Each kind
  block ends with a small accounting line ("N of M shown · N below threshold · N beyond the display
  cap.") reading `shown_count`/`configured_total`/`suppressed_count`/`residual_count` verbatim.
- **No new page/route**: same `/` Today page, same card position (`apps/frontend/app/page.tsx` line 107,
  unchanged).
- **No new user action**: `drill_href` links are reused verbatim from the served rows — same click-path
  as before.
- **Design system compliance**: reuses existing `Card`/`CardHeader`/`CardTitle`/`Badge` primitives (no new
  component library, no new visual effect); `Badge variant="default"` for the side label (matching the
  neutral, non-color-coded convention `compass-state-band-card.tsx`'s own `DirectionBadge` already
  established for direction words in this exact product — deliberately NOT green/red-coded, consistent
  restraint); text tokens (`text-text-muted`, `text-text-faint`, `num`) all pre-existing, no new hex
  values. Loading/empty/error states: the existing `compass === null` -> "backend not reachable" branch is
  unchanged; the no-prior-run state and each side's own empty state are the "empty state" handling this
  component needed (there is no async loading state local to this component — it receives `compass` as an
  already-resolved prop from the page).
- **Responsive**: `grid md:grid-cols-2` collapses to a single column below the `md` (768px) breakpoint,
  consistent with the rest of the Today page's card grids.

## Files Changed
- `apps/frontend/lib/api.ts` -- `CompassRotationRow`, `CompassRotationKind`, `CompassRotation` types;
  `SessionDelta.rotation`; `SessionDeltaChange.delta`/`.direction_word` (optional, sector/theme only).
- `apps/frontend/components/compass-leadership-rotation-section.tsx` -- full rewrite.
- `apps/frontend/components/compass-whatchanged-card.tsx` -- NOT touched (verified via `git diff`: no
  changes). Same entries, same order, same thresholds, same suppressed count as before this iteration.

## Tests Run

Frontend "tests" per project-template.md = the production compile + typecheck:
```
cd apps/frontend && NEXT_DIST_DIR=.next-verify NEXT_PUBLIC_API_URL=http://localhost:8000 npx next build
```
(the plain `npm run build` refuses to target the live `.next` dir without `NEXT_PUBLIC_API_URL` set — a
pre-existing build guard, unrelated to this change; the throwaway-dir invocation is its own documented
escape hatch.) Result: compiled successfully, typecheck passed, all 30 routes generated. The throwaway
`.next-verify` output directory was removed afterward (never committed).

No `apps/frontend/lib/*.test.ts` plain-node test was added: this component has no pure logic left to
extract into a `lib/*.ts` module (it is now a pure served-data renderer — no client-side filter, sign, or
word selection remains, unlike the prior version's `ROTATION_KINDS.includes(...)` filter, which also had
no dedicated test file). This mirrors the existing precedent in this codebase: React component DOM output
is verified by the browser-qa-agent stage (Chrome MCP), not by a developer-level unit test — no
React-Testing-Library/jsdom harness is installed in this frontend (confirmed via `package.json`).

## Live browser verification

Built and started the frontend via `scripts/start-frontend.sh` (port 3255) against the live backend (port
8255, real 30-year seed data) and drove it with Chrome DevTools Protocol:

- Default `/` view: `[data-testid="compass-leadership-rotation-section"]` extracted text confirmed both
  kind blocks render with real gaining/losing rows, correct signed deltas, correct direction words, and
  the accounting line. Full-page screenshot confirmed visual consistency with the surrounding cards (same
  dark theme, same Card chrome, same typography scale) — see the screenshot referenced in the dev handoff's
  live-verification section.
- `/?asof=1996-02-01` (earliest stored run): confirmed the honest no-prior-run message renders instead of
  any rotation content.
- No console errors observed during either navigation.

## Known Issues

See the main dev handoff's Known Issues section (pre-existing `test_no_magic_numbers.py` failure on
untouched files, a `scripts/start-frontend.sh` child-process cleanup gap found during restart
verification, and the missing ESLint config making `npm run lint` non-functional in this repo today) — all
pre-existing and out of this iteration's scope.

---

## Fix Notes (round 2 — review FAIL)

Fixes the reviewer's CRITICAL: the rewritten section dereferenced `session_delta.rotation` unguarded, so
any as-of whose STORED manifest predates this iteration (17 of the 18 distinct stored as-of dates —
`prior_as_of` non-null, no `rotation` key, served verbatim per AG-12) threw
`Cannot read properties of undefined (reading 'sector')` and dropped the whole Today page into the
app-level `error.tsx` fallback.

- `apps/frontend/lib/api.ts` — `SessionDelta.rotation` is now OPTIONAL (`rotation?: CompassRotation`),
  which is the real wire contract. This is also what mechanically prevents the regression: with the guard
  removed, `npx tsc --noEmit` fails with `TS18048: 'session_delta.rotation' is possibly 'undefined'` at
  both call sites (verified by temporarily reverting the guard), and the typecheck IS this project's
  frontend test per `.claude/project-template.md`.
- `apps/frontend/components/compass-leadership-rotation-section.tsx` — a third render branch, ordered
  no-prior-run → rotation-absent → served block. The absent state
  (`data-testid="compass-leadership-rotation-not-recorded"`) is worded distinctly from the no-prior-run
  message and says why nothing is shown ("its stored manifest predates this section, and a frozen
  manifest is never rewritten … The What changed card above still lists this session's moves") — an
  honest placeholder, contained to the section, never a page crash (AG-8). The read is
  `session_delta.rotation ?? null`, mirroring `compass-state-band-card.tsx`'s `compass?.state_band ?? null`
  posture so a `null` on the wire degrades the same way as an absent key.

### Live browser verification of the fix (headless Chromium, `pageerror` + console-error listeners on)

- `/?asof=2026-08-11` (legacy row, `prior_as_of: "2026-08-10"`, no `rotation` — the previously crashing
  case): placeholder renders, What-changed card above still renders, ZERO page/console errors, no
  "Application error" text. Screenshot:
  `reports/qa/goal-market-compass-iter-36-evidence/J-13-legacy-asof-rotation-not-recorded.png`.
- `/?asof=2020-03-20` (a second legacy row): same, zero errors.
- `/` (default frontier, v9): unchanged — full two-sided sector/theme block with signed deltas, direction
  words, and both accounting lines. Zero errors.
- `/?asof=1996-02-01` (earliest run): unchanged no-prior-run message. Zero errors.

Both services stopped afterwards; ports 8255/3255 confirmed free.
