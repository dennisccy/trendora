# goal-i_can_see_the_wealthy_future-iter-1 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future-iter-1
**Date:** 2026-05-29
**Agent:** developer
**Status:** complete

## What Was Built (UI)

The **navigable Trendora workstation shell** — a dense, dark analytical layout that boots offline and
proves frontend↔backend connectivity. No data/scores yet; every page is a styled empty state.

- **Persistent left sidebar** with the 7 approved IA destinations (exactly the blueprint nav, no
  changes): Dashboard `/`, Stocks `/stocks`, Themes `/themes`, Sectors `/sectors`, Scanner Runs
  `/scanner-runs`, System Health `/system-health`, Watchlist `/watchlist`. Active route is highlighted
  (surface-2 bg + accent dot) and links have hover/focus states.
- **Header health badge** (`components/health-badge.tsx`, client) — the visible proof of connectivity.
  Three explicit states: **loading** ("Checking backend…", pulsing dot) → **connected** (green "Backend
  OK" + `provider: seed` + `seed 2026-05-28` + `158 symbols`) or **"Backend unavailable"** (red) when
  `/api/health` fails. Never a fabricated "ok". Re-checks every 30 s.
- **7 nav pages + 2 detail-route stubs** (`/stocks/[ticker]`, `/scanner-runs/[runId]`, reached from
  rows that don't exist yet — not in nav). Each uses a shared styled `EmptyState` card describing what
  will appear once scoring lands, plus a `PageHeading`.
- **Design tokens** (`app/globals.css`): the dark palette as CSS variables (`--bg #0a0e14`,
  `--surface`, `--border`, `--accent #4fd1c5`, `--pos`, `--neg`, `--warn`, `--text`, `--text-muted`,
  `--text-faint`) + a monospace `tabular-nums` `.num` utility for numeric cells. shadcn/ui is
  initialized (`components.json`, `cn` util, `Card`/`Badge` primitives) so iter-2+ inherits the chrome.

## Visual Conformance

- Component library: shadcn-style `Card` (empty-state panels) + `Badge` (status chips) — no raw-div
  soup. Palette tokens only (no arbitrary hex). 4px-grid spacing (Tailwind defaults). Numbers in
  monospace tabular-nums.
- States handled: **empty** (every page), **loading** + **error/unavailable** (health badge). Interactive
  nav links have hover/focus-visible rings.
- Responsive: sidebar + main content; `main` is horizontally scrollable for the wide tables coming in
  iter-2+.

## API Contract Used

- `GET /api/health` → `{status, db_ok, provider, last_run_date, seed_latest_date, symbol_count}`.
  Consumed by `lib/api.ts::fetchHealth` and rendered by the badge. The client **re-formats only** — no
  score/bucket/return is computed client-side (single-source-of-truth discipline).
- Base URL from `NEXT_PUBLIC_API_URL` (set by `scripts/start-frontend.sh` to the offset backend port).

## Tests Run

- `cd apps/frontend && npm run build` → compiled + type-checked successfully; 10 routes generated.
- Live boot: homepage HTTP 200 with all 7 nav labels + "Trendora" present; `/stocks/NVDA` and
  `/scanner-runs/1` stubs resolve 200. (Full click-through + live-badge + CORS verification is the
  browser-qa-agent's job.)

## Known Issues / Limitations

- The live health-badge fetch + CORS behavior is best verified in a real browser (browser QA) — the
  build/boot checks confirm render + routing, not the in-browser fetch.
- No loading skeletons on pages (every page is intentionally an empty state this iteration); page-level
  loading/error states arrive with real data in iter-2+.
- ESLint is disabled during build (`ignoreDuringBuilds`) — no eslint config ships for the MVP;
  type-checking stays on. UI behavior is covered by browser QA, not a unit suite (per project-template).
