# goal-i_can_see_the_wealthy_future-iter-5 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future-iter-5
**Date:** 2026-05-30
**Agent:** developer
**Status:** complete

## What Was Built

Two iter-1 EmptyState stubs graduate to real, data-driven pages. Both re-format API values only —
no score, bucket, return, or count is ever computed client-side (single source of truth).

- **`/scanner-runs` (run list)** — `app/scanner-runs/page.tsx`. A dense dark table from
  `GET /api/runs`, newest first: as-of date (a link to the run), a colour-graded **regime badge**
  (green risk-on → red risk-off, palette tokens only) with its 0–100 score, the three candidate
  counts (Actionable in green, Breakout-watch, Pullback-watch), and the stock count. Loading skeleton,
  "Backend unavailable" error card (styled like `/stocks`), and an empty state when no runs exist.
- **`/scanner-runs/[runId]` (immutable detail)** — `app/scanner-runs/[runId]/page.tsx`. Client
  component; unwraps the route param with React `use(params)`. From `GET /api/runs/{run_id}`:
  - A header strip with a lock icon and **"Immutable snapshot — as of YYYY-MM-DD"** + scanned-at /
    provider / benchmark line, making the frozen historical nature unmistakable.
  - The **regime panel** for that date: label badge + 0–100 score + `ComponentBreakdown` (reused).
  - **Universe-relative breadth** metric cards (above 50-DMA, above 200-DMA, net new highs) — each
    labelled "universe-relative".
  - **Candidate counts** (incl. Risk-off-watchlist).
  - A **ranked stored stock table** (ticker, sector, Leadership / Entry Quality / Risk as A–E bucket +
    number via the reused `ScoreBadge` — Risk inverted, setup-status `Badge`, reason). Reuses the same
    rendering as the `/stocks` leaderboard so a stock reads identically.
  - Loading skeleton; explicit **404 "Run not found"** state; "Backend unavailable" error card.

- **`lib/api.ts`** — added `RunSummary`, `RunsResponse`, `RunDetail` types + `fetchRuns()` /
  `fetchRun(runId)` fetchers (throw on non-200 → explicit unavailable state). Run-detail rows reuse the
  existing `StockRow` type.

## Files Changed

- `apps/frontend/lib/api.ts` — `RunSummary` / `RunDetail` types + `fetchRuns()` / `fetchRun()`
- `apps/frontend/app/scanner-runs/page.tsx` — real run-list table (replaces EmptyState stub)
- `apps/frontend/app/scanner-runs/[runId]/page.tsx` — real immutable as-of detail (replaces stub)

## Design System Conformance

- shadcn `Card` panels; HTML `<table>` in a `Card` matching the `/stocks` leaderboard; `Badge` for
  regime label + setup status; reused `ScoreBadge` (A–E bucket + raw, Risk inverted), `ComponentBreakdown`,
  `EmptyState`, `PageHeading`.
- Palette tokens only (`text-pos`/`text-neg`/`text-warn`/`text-accent`/`surface*`/`border*`) — no
  arbitrary hex. `num` (tabular-nums monospace) on every number (dates, scores, counts).
- Hover/focus states on links and rows; loading skeletons, empty, error (unavailable), and 404 states
  all handled — not just the happy path. Table is horizontally scrollable on narrow widths
  (`overflow-x-auto`), matching the established responsive pattern.

## Navigation

No nav-skeleton change — "Scanner Runs" is already in the sidebar; Run Detail is reached from a run
row (not a top-nav tab), per the approved Information Architecture.

## Tests Run

Command: `cd apps/frontend && npm run build`
Result: PASS — compiled successfully, typechecked all 10 routes:
`/scanner-runs` (2.76 kB) and `/scanner-runs/[runId]` (4.83 kB, dynamic) both build clean.

## Known Issues

- The `regimeVariant` and `setupVariant` colour helpers are re-declared locally in the new pages
  rather than imported from `/stocks` and the dashboard (those weren't exported). This avoids touching
  the green `/stocks` / dashboard pages (zero regression risk to J-01/J-02/J-06); the duplication is
  ~12 lines each and could be lifted into a shared module later if desired.
- Run-detail tickers are plain text (not links to `/stocks/[ticker]`) by design — a stored as-of row
  must not deep-link to the live latest-date detail page (that would mix a frozen date with today's
  numbers).
