# goal-i_can_see_the_wealthy_future-iter-3 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future-iter-3
**Date:** 2026-05-29
**Agent:** developer
**Status:** complete

## What Was Built

Four UI surfaces graduate the product from "regime + sectors only" to the full
**regime → sectors → themes → stocks** leadership view. Every value is **re-formatted from the API
only** — no score, bucket, or return is computed client-side (single source of truth).

- **`/stocks` — Stock Leaderboard** (`app/stocks/page.tsx`, replaced the stub): a dense dark table
  ranked by Leadership. Each row: ticker (links to `/stocks/[ticker]`), **Leadership / Entry Quality
  / Risk** via `ScoreBadge` (A–E bucket + raw number), a setup-status `Badge`, and a reason summary.
  Two working **client-side** filters — a **Sector** dropdown and a **Setup-status** dropdown (incl.
  "Actionable") — which re-display the server rows only (no recompute/re-sort). Loading skeleton,
  "Backend unavailable" error state, no-rows empty state, and a filter-empty empty state.
- **`/stocks/[ticker]` — Stock Detail** (`app/stocks/[ticker]/page.tsx`, replaced the stub): a client
  component reading **`GET /api/stocks/{ticker}`**. Renders the three scores (`ScoreBadge` + raw +
  `ComponentBreakdown`), the setup status, and the reason — the **same** values as the leaderboard
  (J-06). Handles unknown ticker (404 → "Unknown ticker") and backend-unavailable. Notes that the
  chart/invalidation arrive in iter-4.
- **`/themes` — Theme Leaderboard** (`app/themes/page.tsx`, replaced the stub): a table ranked by
  Theme Score (`ScoreBadge`); each row shows 1m & 3m basket return (green/red), breadth %, trend
  label, and an expandable row with member-ticker chips + `ComponentBreakdown`. Breadth labelled
  "universe-relative".
- **`/` — Dashboard** (`app/page.tsx`): the two "pending" placeholders are replaced with **real**
  data — a **Candidate Counts** card (# Actionable / Breakout-watch / Pullback-watch from
  `/api/dashboard.candidate_counts`) and a **Top Themes** card (top 5 from `/api/themes`, each with a
  `ScoreBadge`), rendered exactly like the existing Top Sectors card reads `/api/sectors`.

## Files Changed

**Created:**
- `apps/frontend/components/ui/select.tsx` — palette-themed native `<select>` wrapper for the
  leaderboard filters (no Radix dependency was available; native control keeps it dependency-free,
  accessible, with hover/focus states and a chevron).

**Modified:**
- `apps/frontend/lib/api.ts` — added `ScoreBlock`, `StockSetup`, `StockRow`, `StocksResponse`,
  `StockDetailResponse`, `ThemeRow`, `ThemesResponse` types and `fetchStocks` / `fetchStock(ticker)` /
  `fetchThemes`; changed `DashboardResponse.candidate_counts` to a real `Record<string, number>` and
  removed the `top_themes` field (served by `/api/themes`).
- `apps/frontend/app/stocks/page.tsx` — leaderboard + filters (was a stub).
- `apps/frontend/app/stocks/[ticker]/page.tsx` — 3-score detail (was a stub).
- `apps/frontend/app/themes/page.tsx` — theme leaderboard (was a stub).
- `apps/frontend/app/page.tsx` — real Candidate Counts + Top Themes cards (removed the now-unused
  `PendingCard`); dashboard now also fetches `/api/themes`.
- `apps/frontend/components/score-badge.tsx` — added an `invert` option so the **Risk** score is
  colour-graded by its *danger* direction (high Risk bucket → red, low → green). Leadership/Entry use
  the normal green→red grade.
- `apps/frontend/components/component-breakdown.tsx` — added human labels for the new per-stock and
  theme component keys (rs_sector, rs_theme, extension, contraction, breadth, ma_participation, …).

## Design System Conformance

- shadcn-style `Card` / `Badge` / new `Select`; `ScoreBadge` (A–E foregrounded, raw secondary);
  `ComponentBreakdown` for expandable rows; `EmptyState` for empty/filter-empty.
- Palette tokens only (no arbitrary hex/px); monospace `.num` for all numbers; dense dark tables with
  `overflow-x-auto` at the ~640px breakpoint; hover/focus/active states on rows, links, filters.
- Loading (skeleton), empty, filter-empty, and explicit red "Backend unavailable" states on every new
  page — never a fabricated value when the API is unreachable.

## Tests Run

Command: `cd apps/frontend && npm run build`
Result: **Compiled successfully** — all 10 routes typecheck + build clean (`/stocks` 3.48 kB,
`/stocks/[ticker]` 3.99 kB, `/themes` 4.23 kB, `/` 3.95 kB).

## Known Issues / Notes for Browser QA

- **J-02 Actionable filter shows an empty-state on the current seed date** because zero stocks meet
  the strict Actionable gate in this Risk-on-but-extended market (correct behavior — see the dev
  handoff). To exercise a non-empty status filter, browser QA should also try **Breakout-watch** (8
  rows) or **Pullback-watch** (1 row); the **Sector** filter reduces rows to one sector. The
  Actionable→empty-state path satisfies the J-02 acceptance criterion ("or an explicit empty-state if
  none").
- **J-06 visual check**: open `/stocks`, note NVDA's three buckets+numbers, then open `/stocks/NVDA`
  (click the ticker) — they must match exactly (verified byte-identical at the API level).
- **Risk colour looks inverted by design**: a high Risk score renders red (danger), unlike Leadership
  where high renders green. The bucket *letter* still reflects the raw 0–100 position.
- Confirm the managed `next dev` (port 3835) is up and stable and inspect the on-disk screenshots
  before recording any SKIP/PASS (the SKIP-vs-PASS flap recurred in iter-1/2).
