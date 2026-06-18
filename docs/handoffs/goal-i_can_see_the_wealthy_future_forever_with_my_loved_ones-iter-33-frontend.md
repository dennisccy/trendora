# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-33 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-33
**Date:** 2026-06-18
**Agent:** developer
**Status:** complete

## What Was Built

All new UI lands on EXISTING Information-Architecture homes — no new top-level nav, no new page (blueprint
IA skeleton unchanged → no re-approval). Every surface reads the SINGLE global as-of (`useAsOf`); no second
date state, no `<input type=date>` for viewing, no window/document keydown listener (J-18 preserved).

- **Data Manager (`/data`) — coverage block (J-93):** the "Universe" metric is now "Universe (as of date)"
  = the point-in-time members resolved at the current global as-of, with the resolved date shown; a new
  "Candidate universe" metric shows the static screened count. The explanatory note states the dynamic
  behavior. Stepping the global as-of switcher re-fetches `GET /api/data?as_of=` so the figure slides.
- **`UniverseDiagnosticPanel` (J-94):** for the resolved as-of — the admitted count + the excluded-by-reason
  counts (below history / below price / below liquidity) against the candidate-pool denominator + the exact
  config thresholds. An as-of before the warm-up boundary renders an explicit honest empty-universe banner.
- **`MembershipTimelinePanel` (J-96):** an SVG step-function chart of the resolved universe size across the
  snapshot dates (design-token `var(--accent)` stroke, no magic hex), a per-date table (size + entries /
  exits + excluded-by-reason counts), and the THREE honest labels VERBATIM from the backend (survivorship /
  warm-up / universe-relative). An empty DB renders an honest empty timeline (no fabricated dates/members).
- **`BackwardHistoryPanel` + confirm modal (J-95):** a confirm-gated "Extend history backward" control
  (reusing the rebuild confirm chrome + the live job card) that starts a best-effort `both` job over an
  earlier price start. It carries the survivorship caveat and, on start, an honest blocked / limited-
  coverage (NA) note (the real fetch is data-walled — non-halting).
- **`/stocks` empty-universe honest state (J-93/J-94):** the `rows.length === 0` empty-state copy now
  explains the warm-up window (the universe is honestly empty at early dates), pointing to the Data Manager
  diagnostic — never a fabricated row. `/themes` / `/sectors` / `/scanner-runs` reflect the stored
  membership automatically (they read the snapshot's scored set), so they shrink with the universe.

## Files Changed

- `apps/frontend/lib/api.ts` -- new types (`UniverseDiagnostic`, `MembershipTimelinePoint`,
  `PoolSurvivorship`, `MembershipLabels`, `MembershipTimeline`); migrated `DataCoverage`
  (`universe_count` now as-of-resolved + `universe_asof` / `candidate_pool_count` /
  `candidate_universe_count`; `universe_diagnostic`, `membership_timeline`); `AbsentFromLatestSnapshot`
  gains `candidate_pool_count`; `fetchDataCoverage(asof?, signal?)`.
- `apps/frontend/app/data/page.tsx` -- coverage Universe/Candidate-universe metrics + note; the three new
  panels + the J-95 confirm modal; `loadOverview` reads `useAsOf().asOf` and re-fetches on as-of change.
- `apps/frontend/app/stocks/page.tsx` -- warm-up-aware empty-state copy.

## Tests Run

Command: `cd apps/frontend && npx tsc --noEmit`
Result: clean (exit 0).

Browser QA (J-93/J-94/J-96/J-95) is the browser-qa-agent's job. Evidence-hygiene reminders for the
membership-timeline (below the fold on `/data`): md5sum the evidence dir first, scroll the colored step
chart into the viewport, capture full-viewport, and VIEW the pixels (a table-only/blank frame is rejected).

## Known Issues

- The membership-timeline step chart is a compact SVG sparkline (the J-44/J-49 overlay treatment, no axis
  ticks) — deliberately dense to sit on the coverage home below the fold.
- The backward-history control's `both` job is best-effort; on this data-walled host the live job card will
  show an honest blocked / partial (NA) outcome — that is the expected, non-halting result (not a UI bug).
