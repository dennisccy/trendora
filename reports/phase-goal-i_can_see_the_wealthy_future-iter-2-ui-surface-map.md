# Phase goal-i_can_see_the_wealthy_future-iter-2 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future-iter-2
**Date:** 2026-05-29
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/sectors` | `SectorsPage` ranked table (`<table>`) | Updated layout (empty → populated) | J-04: leaderboard now ranks sector/industry ETFs by Sector Score | Load `/sectors`; confirm ≥10 rows appear and the Sector Score column is non-increasing from row 1 to the last row (descending rank). |
| `/sectors` | `SectorRows` — top row cells | New table | J-04 DoD: top row must show numeric RS-vs-SPY + dist-from-52w-high % + trend label | Read row #1; confirm it shows a numeric "RS vs SPY" %, a numeric "Dist. 52w high" %, and a non-empty trend label (e.g. "Leading"/"Improving"). |
| `/sectors` | `ScoreBadge` (Sector Score cell) | New component | Buckets foregrounded + colour grade | Confirm each row's Sector Score cell shows an A–E letter badge with a raw 0–100 number, colour-graded green (A) → red (E). |
| `/sectors` | Benchmark badge ("RS benchmark: SPY (excluded)") | New component | SPY is the RS benchmark and must not be ranked as a leader | Scan all ticker rows; confirm **SPY is absent** from the ranked rows and appears only in the "RS benchmark: SPY (excluded)" badge in the header strip. |
| `/sectors` | `SectorRows` expandable row + `ComponentBreakdown` | New component / changed behavior | Explainability: no bare score numbers | Click row #1 (or press Enter while focused); confirm it expands to a named component breakdown table showing component names and contributions, and the chevron flips down. Click again to collapse. |
| `/sectors` | "as of <date>" badge | New component | Honest as-of date | Confirm the header shows an "as of YYYY-MM-DD" badge (expected `2026-05-28`). |
| `/sectors` | Loading skeleton / `EmptyState` / "Backend unavailable" card | New states | Honest states, no fabricated rows | Stop the backend, reload `/sectors`; confirm a red "Backend unavailable" card appears and **no table rows are shown**. |
| `/` | `DashboardPage` body (empty → populated grid) | Updated layout | J-01 partial: regime + breadth + data-as-of + Top Sectors now live | Load `/`; confirm the page renders the Market Regime panel, three breadth cards, a Top Sectors card, and two pending cards (not an empty placeholder). |
| `/` | Market Regime panel (`CardTitle` "Market Regime" + label `Badge` + score) | New component | J-01: show regime label + numeric 0–100 score | Confirm the panel shows a label badge that is exactly one of: Strong risk-on / Risk-on / Narrow leadership / Choppy / Risk-off / Defensive, and a numeric score between 0.00 and 100.00 (expected ≈ "Risk-on" / 74.32). |
| `/` | `ComponentBreakdown` (regime) | New component | Explainability: regime score must carry components | Confirm the regime panel lists named components (e.g. MA stack, breadth, VIX gate) with contribution values below the score. |
| `/` | `MetricCard` ×3 (breadth) | New component | J-01: universe-relative breadth | Confirm three cards: "above 50-DMA", "above 200-DMA", "Net new highs"; each shows a % value and an amber caption containing "universe-relative". |
| `/` | "Data as-of <date>" `Badge` (top-right) | New component | J-01: data-as-of indicator | Confirm a clock badge reading "Data as-of 2026-05-28" appears at the top right of the dashboard. |
| `/` | Top Sectors `Card` list | New component | J-01: ≥3 top sectors sourced from `/api/sectors` (same data as `/sectors`) | Confirm the Top Sectors card lists 5 rows, each with rank + ticker + trend label + an A–E score badge, and that the **top ticker/score matches row #1 on `/sectors`** (single source of truth). |
| `/` | `PendingCard` ×2 (Candidate Counts, Top Themes) | New component | Honest pending placeholders — no fabricated zeros | Confirm "Candidate Counts" (Actionable/Breakout-watch/Pullback-watch) and "Top Themes" cards each show a "pending" badge and em-dashes (—), **not** 0 values. |
| `/` | `DashboardSkeleton` / "Backend unavailable" card | New states | Honest states, no fabricated regime | Stop the backend, reload `/`; confirm a red "Backend unavailable" card appears and no regime score/breadth numbers are shown. |
| `/` | Top Sectors degraded state | Changed behavior | Sectors fetch can fail independently of dashboard fetch | With backend up but `/api/sectors` failing, confirm the Top Sectors card shows "Sector data unavailable — backend not reachable" while the regime panel still renders. |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/prices.py` — `bars_asof` no-lookahead accessor + `latest_data_date` + extractors — feeds the engine; no direct UI surface.
- `apps/backend/app/engine/indicators.py` — pure indicator functions (`sma`, `rs_vs`, `atr_pct`, `dist_from_high`, `ma_stack`, `vol_trend`) — values surface only indirectly via the sector/regime scores.
- `apps/backend/app/engine/buckets.py` — `to_bucket(score)` (A–E) — surfaces only as the bucket letters in `ScoreBadge`.
- `apps/backend/app/engine/regime.py` / `sectors.py` — scoring engines; surfaced via `/api/dashboard` and `/api/sectors`.
- `apps/backend/app/config.py`, `config.yaml` — new `indicators:` / `sectors:` sections + `regime.label_edges` + validation — config only; no UI surface (a `ConfigError` would prevent the backend booting, surfacing as "Backend unavailable").
- `apps/backend/main.py` — router registration for the two new endpoints — no UI surface itself.
- `apps/backend/tests/*` (8 new test files), `apps/backend/tests/test_config.py` — tests; no UI surface.

---

## Summary

- **Frontend surfaces changed:** 2 routes (`/sectors`, `/`)
- **New pages/routes:** 0 (both routes pre-existed as empty states in the IA; no navigation change)
- **Modified components:** `app/sectors/page.tsx`, `app/page.tsx`, `lib/api.ts`; 2 new shared components (`score-badge.tsx`, `component-breakdown.tsx`)
- **Navigation changes:** no
- **Backend-only changes:** 9 (engine package + API package + config + main.py + tests)
