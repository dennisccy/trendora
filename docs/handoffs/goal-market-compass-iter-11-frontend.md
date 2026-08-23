# goal-market-compass-iter-11 Frontend Handoff

**Phase:** goal-market-compass-iter-11 (J-11 Stage B1-completion)
**Date:** 2026-08-23
**Agent:** developer
**Status:** complete

## What Was Built

- **`CompassBasisDisclosure.status` type widened** (`lib/api.ts`): from a 3-member to a 4-member
  string-literal union (`"available" | "unavailable" | "rebuilt" | "unverifiable"`), matching the
  backend's new fail-closed `basis_disclosure` literal exactly.
- **Extracted the status→{variant, label} mapping** out of `compass-manifest-strip.tsx`'s `BasisLine`
  inline ternary into a new pure function, `lib/basis-disclosure-label.ts` — a mechanical refactor with
  no behavior change for the three pre-existing statuses (`available`/`rebuilt`/`unavailable`).
- The new `"unverifiable"` status maps to the neutral `default` Badge variant with the label
  `"Basis: unverifiable"` — deliberately NOT `ok` (would read as confident, violating AG-1: "never a
  confident claim") and NOT `danger` (would collapse it into `"unavailable"`'s different meaning — "the
  source run is gone" vs. "no basis was ever recorded").
- New plain node-script test, `lib/basis-disclosure-label.test.ts`, following the exact project
  convention (`lib/api-base.test.ts`'s pattern: `node:assert`, no test framework, explicit `.ts` import
  extensions). Asserts all four statuses map to unique, non-colliding `{variant, label}` pairs, and
  specifically that `"unverifiable"` is distinct from both `"available"` and `"unavailable"`.

## UI surface — what changed for a viewer (not visible this iteration)

- **No new page, no new route, no new user action.** The manifest strip on `/` (the existing Today
  compass page) will, once the app is booted and this reaches a live view, show a fourth possible
  `Basis:` badge state for a manifest whose recorded generation basis is missing/unreadable, instead of
  silently claiming `"Basis: available"` for it. This is the exact ~8-of-24 case this iteration's backend
  fix targets.
- **Not visually verifiable this iteration** — maintenance isolation (ruling A5) forbids booting any
  service or running browser QA. Verified only by `tsc --noEmit` (clean) and the node-script test (7/7
  passed via `npx tsx`, since this sandbox's `node` lacks TS-stripping support — see the dev handoff for
  the full explanation). A static, non-served `next build` into a throwaway `NEXT_DIST_DIR` also compiled
  cleanly with zero type errors across all 29 routes; the throwaway build directory was deleted
  immediately after and nothing was served.

## Files Changed

- `apps/frontend/lib/api.ts` -- `CompassBasisDisclosure.status` union widened to 4 literals, with a
  comment pointing at the backend fix and the new label module.
- `apps/frontend/lib/basis-disclosure-label.ts` -- new. Pure `basisDisclosureLabel(status)` function,
  dependency-free (its own local `CompassBasisStatus` type rather than importing `lib/api.ts`, so it stays
  runnable under plain `node`/`tsx` without pulling in fetch machinery — same pattern as
  `lib/mdd-color.ts`/`lib/regime-variant.ts`).
- `apps/frontend/lib/basis-disclosure-label.test.ts` -- new node-script test.
- `apps/frontend/components/compass-manifest-strip.tsx` -- `BasisLine` now calls
  `basisDisclosureLabel(basis.status)` instead of its inline ternary; no other change to this component.

## Tests Run

```
cd apps/frontend && ./node_modules/.bin/tsc --noEmit
```
Clean, zero errors.

```
cd apps/frontend && npx tsx lib/basis-disclosure-label.test.ts
```
7 passed, 0 failed. (Substitute runner — this sandbox's plain `node` cannot execute `.ts` files at all,
including the pre-existing `lib/api-base.test.ts`; the test FILE itself is written in, and follows, the
project's own `node lib/*.test.ts` convention verbatim.)

```
cd apps/frontend && NEXT_DIST_DIR=.next-verify NEXT_PUBLIC_API_URL=http://localhost:8000 npx next build
```
Compiled successfully, 29/29 routes generated, zero errors. Throwaway dist dir deleted after.

## Known Issues

- Visual rendering of the new `"unverifiable"` badge state is unverified this iteration by design
  (maintenance isolation) — Stage G (a later iteration) owns the first live/browser confirmation, per the
  plan's own "New information displayed" note.
- See the dev handoff (`docs/handoffs/goal-market-compass-iter-11-dev.md`) for the sandbox's missing
  native TypeScript-stripping support in `node`, and the pre-existing lack of a committed ESLint config —
  neither is caused by this iteration's changes.
