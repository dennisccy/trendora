# Phase goal-i_can_see_the_wealthy_future-iter-2 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future-iter-2
**Date:** 2026-05-29
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now open the **Sectors** page (`/sectors`) and see **every sector and industry ETF ranked by a real Sector Score** (a dense table ordered highest→lowest score), instead of an empty placeholder.
- Users can now read, for each ranked sector/industry row, its **A–E bucket + raw 0–100 score**, its **RS-vs-SPY** (signed %), its **distance below its 52-week high** (%), and a **trend label** — all in one row.
- Users can now **click (or press Enter/Space on) any sector row to expand it** and see the **named component breakdown** that drove that score (RS windows, MA stack, distance-from-high, volume trend), so no score is shown as a bare unexplained number.
- Users can now open the **Dashboard** (`/`) and read **today's Market Regime**: one of the six regime labels as a colour-coded badge, its **numeric 0–100 score**, and its **component breakdown**.
- Users can now see **universe-relative market breadth** on the dashboard: % of the universe above the 50-DMA, % above the 200-DMA, and a net-new-highs figure — each explicitly labelled "universe-relative".
- Users can now see a **"Data as-of <date>"** badge on the dashboard telling them which data date the regime and figures reflect.
- Users can now see a **Top Sectors** list (top 5) on the dashboard — the same ranking data shown on `/sectors` — each with its ticker, rank, trend label, and score badge.

---

## What Changed in the Visible UI

- The **`/sectors` page** changed from an empty state to a **populated ranked leaderboard table** with columns: `#` (rank) · Ticker · Kind (sector/industry) · Sector Score (A–E badge + raw) · RS vs SPY · Dist. 52w high · Trend · expand chevron.
- The `/sectors` page now shows a **header strip** with an "as of <date>" badge, an **"RS benchmark: SPY (excluded)"** badge (SPY is shown as the excluded benchmark, never as a ranked leader), and an instruction to click a row for its breakdown.
- The **`/` (Dashboard) page** changed from an empty state to a **dashboard grid**: a large **Market Regime panel** (label badge + 0–100 score + component breakdown), three **breadth metric cards**, a **Top Sectors** card, and two **pending placeholder cards**.
- The dashboard now shows **Candidate Counts** (Actionable / Breakout-watch / Pullback-watch) and **Top Themes** as honest **"pending"** placeholder cards displaying an em-dash (—) and a "pending" badge — never a fabricated zero.
- Each Sector Score cell uses a **colour-graded A–E badge** (green→amber→red), and RS-vs-SPY values are colour-coded green (positive) / red (negative) / amber (NA).
- Both pages now render three distinct states: **loading skeleton**, **empty** ("No ranked sectors" / no rows), and an explicit red **"Backend unavailable"** card when the API cannot be reached.

---

## What Old Behavior Changed

- **`/sectors`**: previously rendered only a styled empty/placeholder state. Now it fetches `/api/sectors` on load and renders the live ranked table (or an explicit unavailable/empty state).
- **`/` (Dashboard)**: previously rendered only an empty/placeholder state. Now it fetches `/api/dashboard` (regime) plus `/api/sectors` (Top Sectors) on load and renders live analytical content; if the dashboard fetch fails, the whole page shows "Backend unavailable", and if only the sectors fetch fails, the Top Sectors card alone shows "Sector data unavailable".

---

## Not Visible Yet

- **Per-stock scoring, candidate counts (Actionable / Breakout-watch / Pullback-watch), and Top Themes** are NOT computed yet — the dashboard intentionally shows them as "pending" placeholders (these land in iter-3). The `/api/dashboard` endpoint returns `candidate_counts: null` and `top_themes: null` by design.
- **Stock & Theme Leaderboards, Stock Detail pages, Scanner Runs history, Watchlist, and System Health** have no UI this iteration (deferred to later iterations).
- **Short-history NA handling** (long MAs/RS reported as `NA` for symbols below `min_history_bars`) exists in the engine and the UI renders `NA` in amber, but it is **not exercised against the real seed** (every real sector/industry ETF has enough history) — it is proven only by a synthetic backend unit test.
- **Persistence of scores / scan-run timestamps** is not present — values are computed on-request from the frozen seed; the "Data as-of" date is the latest seed date, not a stored run timestamp (persistence lands in iter-5).
