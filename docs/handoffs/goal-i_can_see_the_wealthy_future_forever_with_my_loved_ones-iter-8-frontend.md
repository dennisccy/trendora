# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8
**Date:** 2026-06-12
**Agent:** developer
**Status:** complete

## What Was Built
- **Stage-timings block on the `/data` job card** (`StageTimings` component in
  `apps/frontend/app/data/page.tsx`): renders `job.stages` — a fetch block and/or a backfill block,
  each with **Elapsed** (human-readable via the new `fmtDuration`), **Symbols/Dates** (items processed),
  and **Concurrency** (`N×`). The backfill block additionally shows **Per-date sum** and a green
  `X.X× faster than the per-date sum` line (read from `per_date_seconds_sum` ÷ `elapsed_seconds` via
  `speedupFactor`). Pure re-formatting of the backend payload — the frontend derives no figure beyond
  display rounding.
- **Honest stage absence**: a stage that never ran is ABSENT from `job.stages`, so its block does not
  render (no fabricated zero). A backfill-only job shows only the Backfill block; a fetch-only job only
  Fetch; a `both` job shows both.
- **J-47 info-tooltips on the new stat labels** ("Stage timings", "Concurrency") via the existing
  `TermInfo` component, reading two NEW config-backed glossary entries (`stage timings`, `concurrency`)
  — no hard-coded copy, catalog mechanism unchanged. The tooltip trigger is a SIBLING of the label text,
  never nested inside a clickable affordance (iter-5 lesson).
- **DIA now in the J-44 Major-indexes chart legend** (no frontend code change — the index-chart card
  reads `GET /api/indexes`, which now returns DIA's 1356-bar normalized series, so the legend grows from
  4 lines to 5: "Dow 30 (DIA)").

## Files Changed
- `apps/frontend/app/data/page.tsx` — `StageTimings` component, wired into `JobProgressPanel` after the
  backfill progress bar; `fmtDuration` + `speedupFactor` display helpers
- `apps/frontend/lib/api.ts` — `JobStageTiming` interface + `DataJob.stages?` field

## How To See It
1. Restart the backend (kill by port 8835 only) so the new `stages` payload field serves.
2. On `/data`, start a **backfill-only** job over an uncovered seed date range (deterministic — no
   provider needed). Watch the job card: live progress, then a **Stage timings** block with the Backfill
   sub-block (Elapsed / Dates / Concurrency / Per-date sum + the `×faster` line).
3. Hover the info icon next to "Stage timings" / "Concurrency" — the tooltip reads the new glossary
   entries (same copy as `/methodology`).
4. On `/` the Major-indexes & regime card now shows 5 lines including "Dow 30 (DIA)".

## Tests Run
Command: `cd apps/frontend && npx tsc --noEmit`
Result: clean (exit 0). ESLint is not installed in `apps/frontend` (per the spec gate).

## Known Issues
- The per-stage speedup line is display-only and reads the backend's own figures; it shows nothing
  (honest NA) when `per_date_seconds_sum` or `elapsed_seconds` is missing/zero.
- The backend must be restarted before the timings render (the in-memory job payload gained the
  `stages` field this iteration).
