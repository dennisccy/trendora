# Phase goal-mcp-loop-iter-40 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-40
**Date:** 2026-07-15
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- On any stock's detail page (`/stocks/{ticker}`), users can now see a new **"Risk budget" card** that answers "how much can this hurt": ATR%, downside volatility, the worst historical 20-day window, distance to the invalidation level, and an overnight-gap profile (the near-worst p95 gap as the headline, with median and worst gap shown as supporting text), plus the overnight share of 20-day return variance.
- Every number on the Risk budget card carries a **"pXX of universe" percentile chip** (e.g., "p87 of universe"), so users can see at a glance how risky a stock is compared to the rest of the scanned universe — not just the raw number.
- Users can now **sort the `/stocks` leaderboard by 5 new risk columns** — ATR%, Downside vol, Gap p95, Worst 20d, and Dist. to invalidation — clicking a column header toggles ascending/descending, letting users rank the whole universe by any of these risk measures without opening each stock individually.
- Users can **hover/click the info icon next to each new leaderboard column header** to read that metric's definition inline, without leaving the leaderboard (the same mechanism already used for other columns like "High proximity").
- On `/methodology`, users can now find **three new glossary entries** — "overnight-gap profile," "worst 20-day window," and "distance-to-invalidation %" — each explaining the formula and the exact config window it's computed over (20 trading days for both new windows), searchable via the existing glossary search box.
- For a stock with too little trading history (e.g., a recent IPO), users see an honest **"NA — insufficient history"** message on the affected Risk budget tiles/columns instead of a fabricated number or blank cell.
- Users can cross-check that a stock's risk value is consistent everywhere it appears — the same number shown in a `/stocks` leaderboard cell for a ticker matches the number on that ticker's own detail-page card (single source, never recomputed in the browser).

## What Changed in the Visible UI

- The Stock Detail page (`/stocks/{ticker}`) now shows a new **"Risk budget" Card** directly below the existing "Theme & invalidation" card and above the pattern cards (VCP, etc.). It carries the caption "Descriptive only; not a recommendation." — no proven/edge language, no badge, no buy/sell/trim wording.
- The `/stocks` leaderboard table now has **5 additional right-aligned numeric columns** — "ATR%", "Downside vol", "Gap p95", "Worst 20d", "Dist. to invalidation" — inserted between the existing "High proximity" and "Setup" columns. The table (already horizontally scrollable) is now noticeably wider.
- The `/methodology` page's Glossary section gains **3 new rows** under the existing "Factor stats" category; the glossary's "N terms across M categories" count shown at the top of that section increases by 3 (the category count itself is unchanged, since "Factor stats" already existed for ATR%/HV/downside-vol).
- The new leaderboard column headers each carry a **new info-tooltip icon** linking to their glossary definition — visually the same small "i" affordance already used elsewhere on this table.

## What Old Behavior Changed

- None. This phase is purely additive. The developer's own automated check confirms the three existing scores (Leadership, Entry Quality, Risk) render byte-identically with the new fields present, and no other card, badge, score, or page was touched.

## Not Visible Yet

- **Operational data-refresh dependency (UI is wired, data may still be stale on a given running instance).** The Risk budget card and leaderboard columns are fully built and connected to real API fields, but as of this iteration's dev/review handoffs, the backend's database (`apps/backend/data/trendora.db`) had NOT yet been rebuilt under the new scoring code on this environment. Until an operator (or the pipeline's next operational step) deletes/rebuilds that database and the backend restarts, every stock will honestly show **no Risk budget card at all** on the detail page and **"NA" in every risk-budget leaderboard cell** — not because the feature is missing, but because the currently-served snapshot rows predate this feature. Before judging the card/columns as broken, confirm `GET /api/stocks/{ticker}` returns non-null `risk_budget` values for a liquid name.
- Risk-budget numbers will never appear for **historical (pre-iter-40) scanner dates** — by design, older stored scans stay honestly NA for the new fields rather than being retroactively recomputed (avoids a full-universe historical backfill).
- The risk-budget numbers do not appear anywhere **outside** the Stock Detail page and the `/stocks` leaderboard — e.g., the scanner-run detail page (`/scanner-runs/{runId}`) and the return-attribution component were not extended to show them. This matches the phase's explicit scope (no new page, no nav change), not an oversight.
