# goal-ops-hardening-iter-20 Frontend Handoff

**Phase:** goal-ops-hardening-iter-20
**Date:** 2026-07-24
**Agent:** developer
**Status:** complete

## What Was Built

No new component, fetch, field, or nav change — this is a pure copy audit/correction (TC-8/TC-9) of two
pre-existing `/backtest` states, both of which now have a NEW possible CAUSE this iteration introduced:
a historical view's own background dispatch (distinct from the pre-existing latest-view version-bump /
true fresh-install causes the original copy was written for). Both fixes branch on `backtest.is_latest`
(already fetched — `BacktestResponse.is_latest: boolean`, `lib/api.ts`), so no new API field was needed.

- **`RefreshingEvidenceBanner`** (shown when `evidence_status === "refreshing"`) gains an `isLatest:
  boolean` prop, threaded from `backtest.is_latest` at its one call site. Two sentences now branch:
  - *Cause statement* — was unconditionally "The dataset has changed since this evidence was generated,
    and the newer version is not complete yet." This is still accurate for the LATEST view (unchanged: the
    LATEST branch never dispatches anything itself, so `"refreshing"` there can only mean a genuine
    dataset-version bump elsewhere). For a HISTORICAL view, it is now "This date's own evidence is being
    computed in the background (started by viewing this page) and is not complete yet." — true regardless
    of which of the two historical `"refreshing"` sub-cases applies (a stale prior-version row for this
    SAME identity, or the widened cross-`asof_key` fallback to an older date).
  - *Reload instruction* — was unconditionally "Reload this page after the next ingest finishes to pick up
    the new version." Kept verbatim for the LATEST view (still literally true). For a HISTORICAL view, now
    "Reload this page shortly to pick up this date's own evidence once the background compute finishes." —
    no ingest is claimed when none is necessarily involved.
- **The `not_yet_computed` `EmptyState` description** also branches on `backtest.is_latest`:
  - LATEST (the genuine fresh-install shape, unchanged): "No forward-tested evidence exists yet for this
    date. Backfilling or fetching data that covers it will compute this evidence — no numbers are
    fabricated in the meantime." (byte-identical to the iter-17 wording — still true: the LATEST branch is
    structurally incapable of dispatching anything itself).
  - HISTORICAL (new this iteration — reachable when this identity has never had complete evidence AND no
    older fallback exists either): "No forward-tested evidence exists yet for this date. Viewing this page
    has started computing it in the background — reload shortly to see it. No numbers are fabricated in
    the meantime." — states the TRUE cause (viewing itself triggers the dispatch on this branch, per
    `apps/backend/app/api/backtest.py`'s historical branch: it dispatches whenever `evidence_status !=
    "ready"`, which includes `"not_yet_computed"`).

Tone: kept calm/factual, no new visual elements, same `Card` + `Loader2` (banner) / existing `EmptyState`
component (empty state) — matches the plan's Visual Requirements exactly ("no new component library
usage... correct only what is now factually untrue, keep the calm/factual/never-fabricated tone already
established").

## Files Changed

- `apps/frontend/app/backtest/page.tsx` --
  - `RefreshingEvidenceBanner`'s signature gains `isLatest: boolean`; its two prose sentences branch on it
    (see above); its own leading code comment updated to explain the two DIFFERENT causes `"refreshing"`
    now covers and why the copy must name the actual one.
  - The `not_yet_computed` `EmptyState`'s `description` prop is now a ternary on `backtest.is_latest`
    instead of a single fixed string.
  - The call site passes `isLatest={backtest.is_latest}` to `RefreshingEvidenceBanner`.
  - The section's leading comment block gained a short iter-20 note pointing at the new is_latest-aware
    behavior.

No change to `apps/frontend/lib/api.ts` — `is_latest` already exists on `BacktestResponse` (added
pre-iter-16); no new field was needed for this fix, matching the plan's explicit "no new field" scope.

## Tests Run

This project has no frontend unit-test runner (no `test` script in `package.json`; the established
convention per prior iterations, e.g. iter-17's frontend handoff, is a type-check only). Command:

```
cd apps/frontend && npx tsc --noEmit -p tsconfig.json
```

Result: **0 errors.**

No new dependency was added. Grepped for other references to `RefreshingEvidenceBanner` / the
`not_yet_computed` empty-state block across `apps/frontend` — both are local to `app/backtest/page.tsx`
only, so no other component needed a change.

## Known Issues

1. **No live browser render captured this session.** TC-8/TC-9 both explicitly require a live-rendered
   copy check per the phase spec ("though the rendered-copy half (TC-8/TC-9) still needs a live browser
   render"), which is QA-stage work (`TC-12`), not something I ran — I cannot start/stop services or drive
   a browser this session (AG-10 / no browser tooling in this dispatch). Verified instead by: (a) `tsc
   --noEmit` confirming the conditional compiles and types correctly, (b) manual trace of the exact
   backend condition each copy branch corresponds to (documented in the code comments and in the dev
   handoff), matching the iter-16 lesson this session repeatedly cites — "verify each sentence against the
   code that would have to be true for it."
2. **The historical `"refreshing"` copy is necessarily generic across its two sub-causes** (a stale
   prior-version row for the SAME identity vs. the widened cross-`asof_key` fallback to an older date) —
   both are true statements of "this date's own evidence is being computed in the background," but the
   copy does not further distinguish which of the two applies. This mirrors the LATEST view's own existing
   copy, which is similarly generic across ITS two sub-causes; no new precedent set, no regression.
3. **No new component, so no new loading/empty/error states to audit beyond what's listed above** — this
   was a copy-only change to two pre-existing states; the third state (`"ready"`) is untouched.
