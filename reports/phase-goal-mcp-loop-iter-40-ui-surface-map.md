# Phase goal-mcp-loop-iter-40 — UI Surface Map

**Phase:** goal-mcp-loop-iter-40
**Date:** 2026-07-15
**Written by:** ui-impact-analyst

---

Context for the table below: `apps/backend/app/engine/scoring.py` (pass-3) now computes a `risk_budget`
field per stock — using two new pure functions in `apps/backend/app/engine/indicators.py`
(`overnight_gap_profile`, `worst_20d_window`) plus the reused `atr_pct`/`downside_vol` — and stores it
additively on the existing scanner row. That row is served verbatim, with no new endpoint, by the
already-consumed `GET /api/stocks` (leaderboard) and `GET /api/stocks/{ticker}` (detail) endpoints. The
two frontend pages below read that field directly; three new `config.methodology` glossary entries in
`config.yaml` (category `factor_stats`) surface on the existing `/methodology` page through the
existing, unchanged glossary renderer.

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/stocks/{ticker}` | `RiskBudgetCard` (`data-testid="risk-budget-card"`) — full-data state | New component | J-24/B-201: new "how much can this hurt" risk-budget metrics, computed once by `scoring.py` and served on the existing detail endpoint | Navigate to `/stocks/AAPL` (or another liquid, long-history ticker) after the backend's snapshot DB has been rebuilt under this iteration's code; confirm a "Risk budget" card renders below the "Theme & invalidation" card with 6 tiles — "ATR %", "Downside volatility", "Worst 20-day window", "Distance to invalidation", "Overnight gap · p95" (showing a `median X% · worst Y%` supporting line underneath), and "Overnight share of 20d variance" — each showing a numeric value ending in "%" and, where present, a "pXX of universe" chip. |
| `/stocks/{ticker}` | `RiskMetricTile` — NA / short-history state | New state (never-fabricate-0 guard) | DoD requires short-history names to show NA + reason, never a fabricated 0 | Navigate to a recently-listed ticker with materially less than the ~20-trading-day gap/worst-window history (e.g., ARM) and confirm at least one Risk budget tile renders the warn-colored text "NA — insufficient history" instead of a numeric value, with no percentile chip shown for that tile. |
| `/stocks/{ticker}` | `RiskBudgetCard` — absent-field state | New state (regression-safety) | Rows served before this iteration carry no `risk_budget` key at all (optional field) | For a ticker whose served detail JSON still lacks a `risk_budget` key (e.g., before an operator runs the DB rebuild described in the dev handoff), load `/stocks/{ticker}` and confirm NO "Risk budget" card section appears anywhere on the page (component returns null) and no console error/crash is thrown — the page must render normally otherwise. |
| `/stocks/{ticker}` | `RiskBudgetCard` — overnight-variance-share partial-NA edge case | New state (partial NA) | `overnight_variance_share` can independently drop to NA on a zero-variance window while median/p95/worst still report | Find (or construct via a test fixture) a ticker where the gap profile's median/p95/worst are populated but the trailing window has zero close-to-close variance; confirm the "Overnight gap · p95" tile shows real values while the separate "Overnight share of 20d variance" tile shows "NA — insufficient history" on its own, independent of the other tile. |
| `/stocks` | 5 new leaderboard columns: `RISK_BUDGET_COLUMNS` — "ATR%", "Downside vol", "Gap p95", "Worst 20d", "Dist. to invalidation" (cells `data-testid="rb_atr_pct"`, `"rb_downside_vol"`, `"rb_gap_p95"`, `"rb_worst_20d"`, `"rb_dist_invalidation"`) | New table columns | J-24/B-201: cross-name risk comparison on the leaderboard, reading the SAME served `risk_budget` field as the detail card | Navigate to `/stocks`, scroll the table horizontally if needed, and confirm 5 new right-aligned numeric columns titled "ATR%", "Downside vol", "Gap p95", "Worst 20d", "Dist. to invalidation" appear between the existing "High proximity" and "Setup" columns, with each cell showing either a `%`-suffixed number or a muted "NA". |
| `/stocks` | Leaderboard column sorting (`comparatorFor` risk-budget branch) | Changed behavior (new sortable columns) | DoD: users can rank the universe by any risk-budget measure; NA must always sort last | Click the "ATR%" column header once, confirm rows re-sort by that column's numeric value ascending with all "NA" rows at the bottom; click it again, confirm descending order with "NA" rows still at the bottom (not the top). Repeat for at least one more of the 5 new columns (e.g., "Worst 20d"). |
| `/stocks` | Leaderboard column header info tooltip (`TermInfo`, term keys "ATR%", "downside volatility (semivol)", "overnight-gap profile", "worst 20-day window", "distance-to-invalidation %") | New affordance | Column headers link to the new methodology glossary definitions, matching the existing "High proximity" precedent | Hover or click the info icon next to the "Gap p95" column header; confirm a tooltip appears showing the "overnight-gap profile" term's definition text, a "Where:" line mentioning the Stock Detail risk-budget card, and a "Gap window = 20 bars" threshold row. |
| `/stocks` + `/stocks/{ticker}` | Cross-page single-source consistency (`risk_budget` field) | Data-integrity check (no new surface; verifies "no UI recompute") | DoD explicitly requires a spot-checked leaderboard value to equal the detail-card value for the same stock | For one liquid ticker (e.g., AAPL), read the numeric value in its "ATR%" leaderboard cell on `/stocks`, then open `/stocks/AAPL` and confirm the "ATR %" tile in the Risk budget card shows the exact same number (same decimal rendering, both formatted via the shared `fmtRiskValue` helper). |
| `/methodology` | Glossary section, "Factor stats" category — 3 new rows ("overnight-gap profile", "worst 20-day window", "distance-to-invalidation %") | New content (page component unchanged; content is config-driven) | New `config.methodology.categories` glossary entries added to `config.yaml`, served by the existing, unmodified `build_catalog`/glossary endpoint | Navigate to `/methodology`, type "overnight-gap" into the glossary search box, and confirm the "overnight-gap profile" term appears with its full definition, a "Where: Stocks, Stock Detail risk-budget card" line, and a "Gap window = 20 bars" threshold row. Repeat the search for "worst 20-day window" (expect a "Window = 20 bars" threshold row) and "distance-to-invalidation %" (expect a definition with no threshold row, since it has none configured). |
| `/methodology` | Glossary section header term/category count | Changed display (count text only) | Adding 3 terms to an existing category changes the summary count text | Before/after comparison of the "{N} terms across {M} categories" text at the top of the Glossary section: confirm the term count `N` increased by exactly 3 and the category count `M` is unchanged (since `factor_stats` already existed for ATR%/HV/downside-vol). |
| `/stocks/{ticker}` | `RiskBudgetCard` — anti-goal / proven-language compliance | Content check (no new visual state, but a hard DoD requirement) | Anti-goals #1/#2: no score may be presented as proven/confident without a certified evidence claim; no buy/sell/position-advice language is allowed | On the Risk budget card, confirm the visible copy reads only "Descriptive only; not a recommendation." and none of the tile labels, values, or percentile chips contain the words "proven," "buy," "sell," "trim," "reduce," "rebalance," or any badge/pill styled like the existing evidence-ledger "Proven" badge used elsewhere on the same page. |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/prices.py` — new `opens(bars)` structural extractor (mirrors the existing `closes`/`highs`/`lows`/`volumes` helpers) — internal plumbing so `scoring.py` can read open prices for the gap profile; not itself rendered or referenced by any UI text.
- `apps/backend/app/config.py` — `IndicatorsCfg` gains `gap_window`/`worst_window_days` typed fields plus positivity and `max_lookback_bars` cross-validation — a boot-time config guard; the resulting numbers are what surface in the UI (via `config.yaml` and the methodology thresholds, covered by the `/methodology` rows above), but this validation logic itself renders nothing.
- `apps/backend/tests/test_indicators.py` — 8 new fixture tests for the two pure indicator functions — test-only, no UI surface.
- `apps/backend/tests/test_scoring.py` — 6 new tests (fields+percentiles present, byte-match spot checks, reuse call-count proof, score-invariance proof) — test-only, no UI surface.
- `apps/backend/tests/test_config.py`, `test_config_engine.py` — fixture/config extensions and boot-validation tests for the two new config fields — test-only, no UI surface.
- `apps/backend/tests/test_sectors.py`, `test_indexes.py`, `test_themes.py` — inline synthetic-config fixtures extended with the 2 new required config keys (unrelated to these files' own subject matter; a mechanical fixture update) — test-only, no UI surface.
- `apps/backend/tests/test_api_methodology.py` — `GLOSSARY_SPOT_CHECK_TERMS` extended with the 3 new terms — test-only, no UI surface (the terms themselves ARE UI-visible; this file just tests them).

---

## Summary

- **Frontend surfaces changed:** 2 pages with code changes (`/stocks/{ticker}` detail page, `/stocks` leaderboard) + 1 page with content-only change via existing data-driven rendering (`/methodology`, no code touched)
- **New pages/routes:** 0 — additive sections/columns on existing pages only, no new route
- **Modified components:** `RiskBudgetCard` (new), `RiskMetricTile` (new), `RiskBudgetCell` (new), `RISK_BUDGET_COLUMNS` config array (new), plus supporting type additions in `lib/api.ts` (`RiskBudgetComponent`, `GapProfile`, `RiskBudget`, `StockRow.risk_budget?`) and a new shared formatting module `lib/risk-budget.ts`
- **Navigation changes:** no
- **Backend-only changes:** 8 (1 engine helper, 1 config-validation file, 6 test-file groups covering 8 individual test files — see list above; `indicators.py`, `scoring.py`, and `config.yaml` are excluded from this count because their changes ARE UI-visible, per the table above)
