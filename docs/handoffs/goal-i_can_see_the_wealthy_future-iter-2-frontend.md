# goal-i_can_see_the_wealthy_future-iter-2 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future-iter-2
**Date:** 2026-05-29
**Agent:** developer
**Status:** complete

## What Was Built

Two empty-state pages from iter-1 became populated, read-only analytical surfaces that re-format
canonical backend values only (no score/bucket/return is ever computed client-side).

- **`/sectors` — Sector / Industry Leaderboard**: a dense, horizontally-scrollable ranked table.
  Columns: rank · ticker · kind (sector/industry) · **Sector Score** (A–E bucket foregrounded via
  `ScoreBadge`, colour-graded green→red, raw 0–100 secondary) · **RS-vs-SPY** (signed %, green/red) ·
  **distance-from-52w-high %** · **trend label**. Every row is keyboard-accessible (role=button,
  Enter/Space) and expands to its named **component breakdown** (explainability — no bare numbers).
  The RS benchmark (SPY) is shown as an excluded-benchmark badge, never as a ranked leader.
- **`/` — Dashboard**: a **Market Regime panel** (six-label `Badge` colour-mapped to regime
  sentiment + 0–100 score + component breakdown), three **breadth metric cards** (above-50-DMA %,
  above-200-DMA %, net new-highs) each labelled **"universe-relative"**, a **"Data as-of <date>"**
  badge, and a **Top Sectors** list that fetches `/api/sectors` and slices the top 5 — the SAME data
  the leaderboard renders. **Candidate counts** and **Top Themes** render an explicit **"pending"**
  placeholder card (an em-dash, never a fabricated 0).
- **Shared components**: `components/score-badge.tsx` (A–E → palette-token colour grade) and
  `components/component-breakdown.tsx` (named component table with human labels, contribution, and
  per-component detail/NA), reused by both pages.
- **Three states on both pages**: loading (animated skeleton), empty (no rows for the date), and an
  explicit red **"Backend unavailable"** state (no fabricated rows) when the API throws.

## Files Changed

**Created**
- `apps/frontend/components/score-badge.tsx` — A–E bucket badge (palette-token green→amber→red) + raw score
- `apps/frontend/components/component-breakdown.tsx` — named, explainable component table (re-format only)

**Modified**
- `apps/frontend/lib/api.ts` — typed `fetchSectors()` / `fetchDashboard()` clients + `SectorRow`,
  `SectorsResponse`, `DashboardResponse`, `ScoreComponent`, `NewHighLow` interfaces; shared `getJSON`
  helper that throws on non-200 so callers render "Backend unavailable" (mirrors the iter-1
  `fetchHealth` pattern).
- `apps/frontend/app/sectors/page.tsx` — populated ranked leaderboard table with expandable rows.
- `apps/frontend/app/page.tsx` — populated dashboard (regime panel + breadth cards + data-as-of +
  Top Sectors + pending placeholders).

## Design System Conformance

- shadcn `Card` / `Badge` primitives and a dense table — no raw `<div>` soup where a primitive exists.
- All colour via palette tokens only (`--pos`/`text-pos`, `--neg`/`text-neg`, `--warn`/`text-warn`,
  `--accent`, surface/border/text tokens). No arbitrary hex.
- All numbers use the monospace `.num` (tabular-nums) class so columns align.
- Buckets foregrounded, raw 0–100 secondary (per DESIGN SYSTEM).
- Hover / focus-visible / active states on the interactive (expandable) rows; honesty labels
  ("universe-relative", "pending") rendered with the `--warn` amber token.
- Both pages match the iter-1 shell (persistent sidebar + main content) and its empty-state styling.

## Tests Run

**Command:** `cd apps/frontend && npm run build`
**Result:** **Compiled successfully** — types valid, all **10 routes** generated. `/` = 3.45 kB,
`/sectors` = 3.76 kB (first load JS 116/117 kB). Re-verified in this session after clearing a stale
dev server (clean build, no type errors).

(There is no frontend unit suite by project convention; `npm run build` is the typecheck/compile
gate, and user-facing behaviour is covered by browser QA.)

## Known Issues

- **Backend dependency**: Both pages require the backend up at `NEXT_PUBLIC_API_URL`. The managed
  `scripts/start-frontend.sh` sets this to the auto-offset backend port (8835 for this repo path);
  the literal `http://localhost:8000` fallback in `lib/api.ts` is the pre-existing iter-1 default and
  is only used if the env var is unset. Browser-QA must start **both** managed servers before judging.
- **Stale dev server cleared**: an iter-1-era `next dev -p 3835` (serving pre-iter-2 content) was
  found running and has been terminated this session, so browser-QA's `start-frontend.sh` will boot a
  clean server against the new pages. The sibling project's server (`-p 3072`) was left untouched.
- **`min_history_bars` NA path** is not visible on `/sectors` against the real seed (every sector/
  industry ETF has enough history); short-history NA rendering is proven by the synthetic backend
  unit test, and the UI renders `NA` (amber) for any null value it receives.
