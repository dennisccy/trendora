# Phase goal-i_can_see_the_wealthy_future-iter-3 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future-iter-3
**Date:** 2026-05-29
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now open the **Stock Leaderboard** at `/stocks` and see every universe stock (122 rows on the current seed) ranked by Leadership, each row showing three independent A–E-bucketed scores (Leadership / Entry Quality / Risk), a setup-status badge, and a plain-language reason.
- Users can now **filter the Stock Leaderboard by GICS sector** using the "Sector" dropdown — the table re-displays only stocks in the chosen sector and updates the visible-count indicator (e.g. `12 / 122`).
- Users can now **filter the Stock Leaderboard by setup status** using the "Setup" dropdown (Actionable, Breakout-watch, Pullback-watch, Extended, Avoid, Risk-off-watchlist). Selecting a status with no matching rows (e.g. "Actionable" on the current extended market) shows an explicit "No stocks match these filters" empty state instead of fabricated rows.
- Users can now **click any ticker** in the leaderboard to open its **Stock Detail** page (`/stocks/[ticker]`), showing the same three scores as large cards with raw 0–100 values, A–E buckets, captions explaining each score's direction, the setup status + reason, and an expandable named-component breakdown per score.
- Users can now open the **Theme Leaderboard** at `/themes` and see ≥3 themes (11 on the seed) ranked by a price-confirmed Theme Score, each row showing 1-month and 3-month basket return, member breadth %, and a trend label.
- Users can now **expand any theme row** to reveal its member-ticker chips and a named-component breakdown of the Theme Score.
- Users can now read a **complete Dashboard** at `/`: the previous "pending" placeholders are replaced with real **Candidate Counts** (# Actionable / Breakout-watch / Pullback-watch) and a **Top Themes** list (top 5, each with its score badge), alongside the existing Market Regime, Top Sectors, breadth, and as-of date.

---

## What Changed in the Visible UI

- **`/stocks`** changed from an empty stub to a dense dark ranked table with columns: #, Ticker (links), Sector, Leadership, Entry Quality, Risk, Setup, Reason — plus an "as of {date}" badge, a Sector dropdown, a Setup dropdown, and a `visible / total` count.
- **`/stocks/[ticker]`** changed from a stub to a detail page: a setup+reason header card, three score cards (Leadership / Entry Quality / Risk) each with a `ScoreBadge`, large raw number, caption, and `ComponentBreakdown`, plus a "Back to leaderboard" link and a note that the chart/invalidation arrive in iter-4.
- **`/themes`** changed from an empty stub to a ranked table with columns: #, Theme, Theme Score, 1m, 3m, Breadth, Trend, and an expand chevron — with a "breadth is universe-relative" badge and a "Price-confirmed, not news-driven" caption.
- **`/` (Dashboard)** replaced its two "pending" placeholder cards with a real **Candidate Counts** card and a real **Top Themes** card; the dashboard now also fetches `/api/themes`.
- The **Risk** score everywhere is colour-graded by *danger* direction (high Risk renders red, low renders green) via a new `invert` option on `ScoreBadge` — opposite to Leadership/Entry Quality where high renders green.
- The **ComponentBreakdown** component now renders human-readable labels for the new per-stock and theme component keys (e.g. rs_sector, rs_theme, extension, contraction, breadth, ma_participation).

---

## What Old Behavior Changed

- **Dashboard candidate counts & Top Themes:** previously rendered as static "pending" placeholder cards. Now they render live values read from `/api/dashboard.candidate_counts` and `/api/themes` (sliced). Testers should re-verify the Dashboard still loads and the Regime / Top Sectors / breadth cards are unchanged.
- **Sector Leaderboard (`/sectors`, J-04):** no intended visual change, but the underlying score→label helper was refactored (`labels.label_for` extracted from `regime.py`). The sector output must remain byte-identical — re-verify the Sector Leaderboard still ranks and labels as before (regression guard).
- **Risk score colour:** any place a Risk-type score appears is now colour-inverted by design (high = red). This is intentional, not a bug.

---

## Not Visible Yet

- **Full Stock Detail (J-05):** the price + moving-average candle chart, volume series, theme-membership chips, and concrete invalidation note ("below 50-DMA at $X") are deferred to iter-4. The detail page currently shows scores + components only.
- **`gap_climax` Risk component:** computed in the engine but always reports NA / `available:false` (needs earnings data not yet present) — visible only as an unavailable component row, never as a fabricated value.
- **`decision_rules.theme_floor`:** validated and present in config but not yet consumed by setup classification — no user-visible effect this iteration.
- **Historical Risk-Off run review (J-07):** the Risk-off ⇒ zero-Actionable gate is implemented and unit-tested, but the browser journey to open a historical Risk-Off run needs the scanner-runs history (iter-5).
