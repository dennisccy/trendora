# Phase goal-i_can_see_the_wealthy_future-iter-5 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future-iter-5
**Date:** 2026-05-30
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/scanner-runs` | `ScannerRunsPage` run-list table | New page (replaces EmptyState stub) | Adds the immutable scan-snapshot history (J-07/J-08 entry point) | Navigate to `/scanner-runs`; confirm a table renders with **≥2 dated rows** (e.g. 2026-05-28, 2025-04-04, 2022-10-07) newest first, each with a regime badge, candidate counts, and stock count |
| `/scanner-runs` | `RunTableRow` regime badge + score | New component | Show each run's regime label colour-graded | Confirm at least one row shows a **red "Risk-off"** badge (2025-04-04 or 2022-10-07) and the latest row (2026-05-28) shows a **green "Risk-on"** badge with its 0–100 score beside it |
| `/scanner-runs` | `RunTableRow` Actionable column | New table column | Show per-run Actionable count for the Risk-Off gate | Confirm the **Actionable column reads `0`** for every Risk-off row; confirm the latest Risk-on row shows a non-zero Actionable count |
| `/scanner-runs` | As-of date `Link` | New navigation | Open a run's immutable detail | Click a run's as-of date link; confirm the URL changes to `/scanner-runs/<id>` and the detail page loads |
| `/scanner-runs` | Error / empty / loading states | New behavior | Honest unavailable state (no fabrication) | With the backend stopped, load `/scanner-runs`; confirm a **"Backend unavailable"** card appears (not a blank table or fabricated rows) |
| `/scanner-runs/[runId]` | `RunDetailPage` / `RunBody` | New page (replaces EmptyState stub) | The immutable as-of view (J-07/J-08) | Open a Risk-off run; confirm the header strip reads **"Immutable snapshot — as of YYYY-MM-DD"** with a lock icon and the matching as-of date |
| `/scanner-runs/[runId]` | Regime panel + `ComponentBreakdown` | New component | Show the as-of regime for that date | On a 2025-04-04 (or 2022-10-07) run, confirm the regime panel reads **"Risk-off"** with its 0–100 score and a component breakdown |
| `/scanner-runs/[runId]` | Stored stock table + `ScoreBadge` | New table | Ranked stored per-stock results (J-07 zero-Actionable check) | On a Risk-off run, scan the **Setup column** down the full table and confirm **no row shows "Actionable"** (all watchlist-only) |
| `/scanner-runs/[runId]` | Stored stock table rankings | New table | Prove snapshots differ by date (J-08) | Open an older run (2022-10-07), note its top 3 tickers (e.g. HUBB/REGN/AXON); open the latest run (2026-05-28), confirm its top tickers (e.g. MU/ARM/MRVL) and per-stock scores **differ** |
| `/scanner-runs/[runId]` | Breadth `MetricCard` ×3 | New component | Show universe-relative breadth as-of date | Confirm three breadth tiles render (above 50-DMA, above 200-DMA, net new highs) each captioned/labelled and showing a `%` value or `NA` |
| `/scanner-runs/[runId]` | `CandidateCountsRow` | New component | Stored counts incl. Risk-off-watchlist | On a Risk-off run, confirm the **Actionable count tile reads `0`** and the Risk-off-watchlist tile shows a large count |
| `/scanner-runs/[runId]` | "All runs" back `Link` | New navigation | Return to list | Click "All runs"; confirm navigation back to `/scanner-runs` |
| `/scanner-runs/[runId]` | 404 / error states | New behavior | Honest no-fabrication on unknown run | Navigate to `/scanner-runs/999999`; confirm a **"Run not found"** empty state (no fabricated run) |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/models.py` — adds `ScannerRun`, `ScannerResult`, `SectorScoreRow`, `ThemeScoreRow` append-only snapshot tables. Their data surfaces only via the new `/scanner-runs` pages; the schema itself is internal.
- `apps/backend/app/engine/scanner.py` — `run_scan` + `bootstrap_runs` persistence logic. Drives what the new pages show but has no direct UI surface.
- `apps/backend/main.py` — registers `runs.router` and calls `bootstrap_runs` in the lifespan. Internal wiring; the visible effect is that runs exist to list.
- `apps/backend/app/config.py` + `config.yaml` — new `scanner.bootstrap_dates` config. Determines which dates appear in the list; no direct UI control.
- `apps/backend/tests/*` (test_scanner, test_api_runs, test_no_magic_numbers, test_config*, test_db, test_sectors, test_themes) — tests only, no UI.
- `apps/backend/app/api/runs.py` — `GET /api/runs` + `GET /api/runs/{run_id}`. Backend-API, but **consumed by the frontend** via `fetchRuns()` / `fetchRun()` in `lib/api.ts`, so the surfaces above ARE affected (listed for completeness, not backend-only).

---

## Summary

- **Frontend surfaces changed:** 2 routes (`/scanner-runs`, `/scanner-runs/[runId]`)
- **New pages/routes:** 2 (both replace iter-1 EmptyState stubs)
- **Modified components:** `lib/api.ts` (new `RunSummary`/`RunDetail` types + fetchers); reuses existing `ScoreBadge`, `ComponentBreakdown`, `Badge`, `EmptyState`, `PageHeading`, `Card`
- **Navigation changes:** no nav-skeleton change ("Scanner Runs" already in sidebar); new in-page links (as-of date → detail, "All runs" → list)
- **Backend-only changes:** 5 (models, scanner engine, lifespan wiring, config, tests) — the 2 new API endpoints are frontend-consumed, not backend-only
