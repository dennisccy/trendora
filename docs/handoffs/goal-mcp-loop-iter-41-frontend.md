# goal-mcp-loop-iter-41 Frontend Handoff

**Phase:** goal-mcp-loop-iter-41
**Date:** 2026-07-15
**Agent:** developer
**Status:** complete

## What Was Built

- **Drawdown & dry-spell expectations panel on `/evidence`** — a new additive section inside EVERY
  existing claim card (`ClaimRow` in `apps/frontend/app/evidence/page.tsx`), rendered below the current
  hypothesis/verdict field grid, inside the same `CardContent`. For any claim whose cohort resolved (all
  7 real claims today do), it shows a compact table: one row per market phase (`Expansion`, `Pullback`,
  `Correction`, `Bear`, `Recovery`, always in this order, even at n=0), four columns (max-DD depth,
  underwater duration, time-to-recover, longest losing streak), each cell showing median + p90 + n, or
  the honest `"insufficient (n=…)"` text when below the server's floor.
- A method note ("Longest losing streak is counted at the walk-forward cadence…") and the served
  `survivorship_bias` caveat render below the table, read verbatim from the payload.
- **No new page, no new route, no nav change** — purely additive to the existing `/evidence` surface.
- **New pure types/formatters** in `apps/frontend/lib/evidence.ts`: `DistributionCell`, `LossStreakCell`,
  `PhaseExpectations`, `DrawdownExpectations` (mirroring the backend JSON exactly), plus
  `insufficientLabel`, `formatDays` (one-decimal day-count, e.g. "7.4d"), `formatStreak` (integer count).
  Re-exported from `apps/frontend/lib/api.ts` for discoverability alongside the other evidence types.

## UI Evolution

- **New user-facing capability:** on any certified claim's `/evidence` card, the user can read what
  following that cohort's methodology has historically felt like — drawdown depth, time underwater, time
  to recover, and worst losing streak — broken out by the market phase at entry, with honest sample sizes.
- **New information displayed:** per-phase median/p90 of max-drawdown depth, underwater duration,
  time-to-recover, and longest losing streak, each with `n`; `"insufficient (n=…)"` for thin phases; a
  walk-forward-cadence method note; the survivorship-bias caveat.
- **New user actions:** none — purely descriptive, read-only, no controls.
- **Visual treatment:** reuses the existing `Card`/`CardContent`/`Badge`/`dl`/`Field` primitives already
  on this page — no new UI primitives introduced. Phase labels use `Badge variant="default"` (the calm,
  neutral variant) rather than the `accent` variant the row's own regime badge uses, since FIVE repeated
  per-row labels in a data table read as noisy/hype under the loud `accent` treatment the DESIGN SYSTEM
  reserves for a single highlighted flag — this is a deliberate, minimal adaptation of "reuse the Badge
  component," not a new visual language. Max-drawdown cells reuse `fmtMdd` from
  `components/forward-return.tsx` (the SAME formatter Backtest/stock-detail MDD figures already use) for
  visual consistency across the app.
- **States handled:** a phase below the honesty floor renders `"insufficient (n=…)"` (never a blank
  cell); a claim whose `expectations` field is absent (session-less payload edge case, or an unresolvable
  cohort) renders NOTHING for the panel section — no error boundary, no empty placeholder — mirroring the
  iter-40 `RiskBudgetCard`'s "return null when absent" precedent; a `null` `median`/`p90`/`value` anywhere
  routes through the guarded `fmtMdd`/`formatDays`/`formatStreak` formatters (all null-safe, em-dash
  fallback), never an unguarded `.toFixed` crash. No new loading state — rides the existing `/evidence`
  fetch + `EvidenceSkeleton`.

## Files Changed

- `apps/frontend/app/evidence/page.tsx` — `DrawdownExpectationsPanel`, `DistributionCellView`,
  `LossStreakCellView` components; wired into `ClaimRow`.
- `apps/frontend/lib/evidence.ts` — new types + formatters (see dev handoff for the full list).
- `apps/frontend/lib/evidence.test.ts` — 3 new checks (`insufficientLabel`, `formatDays`, `formatStreak`).
- `apps/frontend/lib/api.ts` — re-exports the new types.

## Tests Run

- `cd apps/frontend && npx tsc --noEmit -p .` — clean, no type errors.
- `cd apps/frontend && npx tsx lib/evidence.test.ts` — **42 passed** (39 pre-existing unedited + 3 new).
  (This repo's convention for frontend unit tests — no framework installed; `node --experimental-strip-
  types` failed on this host's Node build (`ERR_NO_TYPESCRIPT` — not compiled with TS support), so `npx
  tsx` was used instead, matching the documented iter-14 precedent in `docs/handoffs/goal-mcp-loop-iter-
  14-dev.md`.)
- Verified live against the real, freshly-rebuilt 30-year/590-symbol database: started
  `scripts/start-backend.sh` + `scripts/start-frontend.sh` on ports 8255/3255, confirmed `/evidence`
  returns HTTP 200, and independently confirmed (via direct `curl` of `GET /api/evidence`) that all 7 real
  claims carry a well-formed `expectations` payload with the exact per-phase shape the panel component
  expects (see the dev handoff's "Live Verification" section for the full JSON captured).
- **Not done this session:** an actual browser-rendered visual check of the panel (scrolled into frame,
  below the fold inside a claim card, per the phase spec's own capture-discipline note) — Chrome MCP is
  not available to the developer agent. The JSX was reviewed manually against the served JSON shape and
  compiles/typechecks cleanly; recommend browser-qa do the visual confirmation pass.

## Known Issues

- See the dev handoff's "Known Issues" section for the `/api/evidence` latency regression discovered and
  fixed this iteration (backend-side cache addition — no frontend change was needed to fix it, since the
  frontend was always going to render whatever the API returned; the fix just made the API fast again).
- No frontend-specific known issues beyond the missing browser-visual verification noted above.
