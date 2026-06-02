# Phase goal-i_can_see_the_wealthy_future_forever-iter-9 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-9
**Date:** 2026-06-02
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/stocks` | "Pattern" `<Select>` filter (replaces VCP filter) | Changed behavior | VCP filter generalized to all 3 patterns via `PATTERNS` registry | Select "Pullback to rising DMA only"; confirm the row count shrinks to only rows carrying a Pullback badge. Then select "Not Flat base"; confirm flat-base-flagged rows disappear. |
| `/stocks` | Per-pattern badges (`VCP`, `Pullback`, `Flat base`) on flagged rows | New element | New patterns surfaced alongside VCP | Find a row flagged for a new pattern; confirm a teal `Pullback` or `Flat base` badge renders. Hover it; confirm tooltip shows server reason + pivot + invalidation text. |
| `/stocks` | Pattern glossary `InfoTooltip` on badge | New element | Glossary meaning pulled from config catalog | Hover the info icon next to a Pullback/Flat base badge; confirm the pattern's definition text appears. |
| `/stocks` | Pattern-aware empty state | Changed behavior | Honest empty copy per active pattern filter | Apply a pattern filter that matches zero rows; confirm message names that pattern (e.g. "No Pullback to rising DMA name…") and no rows are fabricated. |
| `/stocks/[ticker]` | Header `PatternBadge`(s) | New element | Per-flagged-pattern badge beside setup status | Open a ticker flagged for a new pattern; confirm the pattern badge appears in the header next to the setup status. |
| `/stocks/[ticker]` | `PatternCard` (reason + pivot + invalidation) | New component | Detail card per flagged new pattern | On a flat-base-flagged ticker, confirm a Flat-base card shows reason, pivot (base high), and invalidation (base low). Confirm the VCP card is still present and unchanged. |
| `/system-health` | `BreakdownPanel` "Forward return: Pullback-to-rising-DMA vs not" | New component | Surfaces new pattern forward-return cohort | Confirm the panel renders flagged vs not rows with mean return and sample size `n`; confirm a cohort below min sample shows NA with its `n`. |
| `/system-health` | `BreakdownPanel` "Forward return: Flat-base breakout vs not" | New component | Surfaces new pattern forward-return cohort | Confirm the panel renders both cohorts with `n`; confirm NA appears (not a fabricated number) when below min sample. |
| `/methodology` | Two new auto-rendered `EntryCard`s (Pullback to rising DMA, Flat-base breakout) | New component | Catalog-driven glossary cards | Scroll to the pattern section; confirm both new cards render with definition, config thresholds (live values), and worked example. |
| `/methodology` | Page subtitle | Changed behavior | Generalized from "VCP pattern" to "detected price pattern" | Confirm the subtitle reads generically and is not VCP-specific. |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/patterns.py` — `detect_pullback_to_rising_dma` / `detect_flat_base_breakout` detectors — surfaced indirectly via the row fields the UI renders; detector logic itself has no UI surface.
- `apps/backend/app/config.py` — `PullbackToRisingDmaCfg` / `FlatBaseBreakoutCfg` sub-models + cross-validator — config schema only.
- `apps/backend/app/engine/scoring.py` — attaches new row keys at the VCP call site — no UI surface (data flows into existing API).
- `apps/backend/app/models.py` — `is_pullback_to_rising_dma` / `is_flat_base_breakout` indexed columns — persistence only.
- `apps/backend/app/engine/scanner.py` — writes the two new boolean mirrors — persistence only.
- `apps/backend/app/engine/forward_testing.py` — computes `by_pullback_to_rising_dma` / `by_flat_base_breakout` aggregates — consumed by the `/system-health` panels (UI impact captured above).
- `config.yaml` — new `patterns.*` blocks + catalog entries — feeds `/methodology` and tooltips (UI impact captured above).
- `apps/frontend/lib/api.ts` — `PullbackToRisingDma` / `FlatBaseBreakout` interfaces + `StockRow` / `SystemHealthResponse` extensions — type definitions consumed by the pages above; no standalone surface.

---

## Summary

- **Frontend surfaces changed:** 10 (across 4 routes)
- **New pages/routes:** 0
- **Modified components:** 4 pages (`/stocks`, `/stocks/[ticker]`, `/system-health`, `/methodology`)
- **Navigation changes:** no
- **Backend-only changes:** 8
