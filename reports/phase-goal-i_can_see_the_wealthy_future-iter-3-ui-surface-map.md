# Phase goal-i_can_see_the_wealthy_future-iter-3 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future-iter-3
**Date:** 2026-05-29
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/stocks` | `StocksPage` ranked table | New page (was stub) | J-02: rank every stock by three scores | Load `/stocks`; confirm multiple ranked rows appear, each with a # rank, ticker, sector, and three `ScoreBadge`s (letter + number) for Leadership/Entry Quality/Risk, a setup badge, and a non-empty reason |
| `/stocks` | `Sector` `<Select>` filter | New form control | J-02: filter by GICS sector | Open the "Sector" dropdown, pick one sector (e.g. Technology); confirm the table reduces to only that sector's rows and the `visible / total` count drops below total |
| `/stocks` | `Setup` `<Select>` filter | New form control | J-02: filter by setup status incl. Actionable | Select "Breakout-watch"; confirm only Breakout-watch rows show. Then select "Actionable"; confirm either only Actionable rows OR the "No stocks match these filters" empty state appears (current seed → empty state) |
| `/stocks` | `StockTableRow` ticker `Link` | New navigation | Drill into a stock (J-06 entry) | Click the NVDA ticker link; confirm navigation to `/stocks/NVDA` |
| `/stocks` | `Risk` `ScoreBadge` (invert) | Changed display | Risk = danger direction | Find a row with a high Risk number; confirm its Risk badge renders red (danger) while a high Leadership badge renders green |
| `/stocks` | `EmptyState` (filter-empty) | New component state | Honest empty signal | Apply the "Actionable" setup filter on the current seed; confirm "No stocks match these filters" shows instead of any fabricated row |
| `/stocks` | "Backend unavailable" `Card` | New error state | No fabricated data | With backend stopped, load `/stocks`; confirm a red "Backend unavailable" card appears and no rows are shown |
| `/stocks/[ticker]` | `StockDetailPage` / `ScoreCard` ×3 | New page (was stub) | J-06: same scores as leaderboard | Open `/stocks/NVDA`; confirm three score cards (Leadership/Entry Quality/Risk) each show a raw `NN.NN / 100`, an A–E badge, a caption, and a component breakdown |
| `/stocks/[ticker]` | J-06 cross-view check | New behavior | Single source of truth | Note NVDA's three buckets + numbers on `/stocks`, then open `/stocks/NVDA`; confirm all three buckets AND numbers match exactly |
| `/stocks/[ticker]` | `ComponentBreakdown` per score | New component | Explainability anti-goal | Expand/inspect a score card; confirm ≥3 named components with values appear, and `gap_climax` (if shown) is marked unavailable, not a number |
| `/stocks/[ticker]` | "Unknown ticker" `Card` | New error state | 404 handling | Open `/stocks/NOTREAL`; confirm a "Unknown ticker" warn card with a link back to the leaderboard, not a crash |
| `/stocks/[ticker]` | "Back to leaderboard" `Link` | New navigation | Return path | Click "Back to leaderboard"; confirm navigation back to `/stocks` |
| `/themes` | `ThemesPage` ranked table | New page (was stub) | J-03: rank themes by Theme Score | Load `/themes`; confirm ≥3 theme rows ranked by Theme Score in non-increasing order, each with a score badge |
| `/themes` | Theme row metrics columns | New display | J-03: members/returns/breadth/trend | On the top theme row, confirm a numeric 1m return, a numeric 3m return, a breadth % (or NA), and a trend label are all rendered |
| `/themes` | `ThemeRows` expandable row | New behavior | Component breakdown + members | Click the top theme row; confirm it expands to show member-ticker chips and a `ComponentBreakdown`; click again to collapse |
| `/themes` | "Backend unavailable" `Card` | New error state | No fabricated data | With backend stopped, load `/themes`; confirm the red "Backend unavailable" card and no rows |
| `/` | `CandidateCountsCard` | New component (replaced placeholder) | J-01: real candidate counts | Load `/`; confirm a "Candidate Counts" card shows three numeric rows — Actionable, Breakout-watch, Pullback-watch (Actionable may be 0) |
| `/` | `Top Themes` `Card` | New component (replaced placeholder) | J-01: real Top Themes | Load `/`; confirm a "Top Themes" card lists ≥3 themes, each with a rank, name, trend label, and a `ScoreBadge` |
| `/` | Dashboard regime/sectors/breadth | Changed behavior (regression check) | Dashboard now also fetches `/api/themes` | Load `/`; confirm the Market Regime card, Top Sectors list, breadth metrics, and "Data as-of" badge all still render correctly |
| (global) | `components/score-badge.tsx` | Changed component | `invert` option for Risk grading | On any page showing a Risk score, confirm high Risk → red and low Risk → green (inverted vs Leadership) |
| (global) | `components/component-breakdown.tsx` | Changed component | New component key labels | Expand any breakdown on `/stocks/[ticker]` or `/themes`; confirm new keys (rs_sector, rs_theme, breadth, ma_participation, etc.) show human labels, not raw keys |

---

## Backend-Only Changes (No UI Impact)

- `app/engine/scoring.py` — single producer of the three per-stock scores + setup composition; surfaced via `/api/stocks` (consumed by UI), but the module itself is not a UI surface.
- `app/engine/themes.py` — theme scoring + basket-return math; surfaced via `/api/themes`.
- `app/engine/setups.py` — setup classification + Risk-off→zero-Actionable gate + `summarize_candidates`; counts surfaced via `/api/dashboard`.
- `app/engine/labels.py` — shared `label_for` helper extracted from `regime.py`; no user-visible output change (J-04 must stay green).
- `app/engine/normalize.py` — shared cross-sectional percentile helper; internal math only.
- `app/api/stocks.py`, `app/api/themes.py` — new routers feeding the new pages (consumed by UI; not surfaces themselves).
- `app/api/dashboard.py` — now serves real `candidate_counts`; `top_themes` placeholder removed (Top Themes served by `/api/themes`).
- `app/config.py` — typed validation for `scores` / `theme_scores` / `decision_rules` / `stock_sectors`; no UI surface.
- `config.yaml` — added `theme_scores` and `stock_sectors` reference data; no UI surface.
- `app/seed_loader.py` — sets/backfills `Stock.sector_id`; enables the Sector column/filter data but is not itself a surface.
- `apps/backend/main.py` — registers the two new routers; no UI surface.
- Backend tests (`test_scoring.py`, `test_themes.py`, `test_setups.py`, `test_api_engine.py`, `test_config*.py`, `test_no_magic_numbers.py`, `test_regime.py`, `test_sectors.py`) — no UI impact.

---

## Summary

- **Frontend surfaces changed:** 4 routes (`/stocks`, `/stocks/[ticker]`, `/themes`, `/`) + 2 shared components (`score-badge`, `component-breakdown`) + 1 new component (`ui/select`)
- **New pages/routes:** 0 new routes (all four were pre-existing IA homes); 3 stubs → full pages + 1 dashboard completion
- **Modified components:** 3 (`score-badge.tsx`, `component-breakdown.tsx`, `lib/api.ts`); 1 created (`ui/select.tsx`)
- **Navigation changes:** no (nav skeleton unchanged; ticker links and back-link are within existing IA)
- **Backend-only changes:** 13 backend files (5 new engine modules, 2 new API routers, 6 modified backend files) + 8 test files
