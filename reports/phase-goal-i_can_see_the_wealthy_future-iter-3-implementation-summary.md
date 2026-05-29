# Goal Iteration 3 — Implementation Summary

**Phase:** goal-i_can_see_the_wealthy_future-iter-3
**Date:** 2026-05-29
**Written by:** developer

---

## Features Implemented

- **Stock Leaderboard (`/stocks`)**: Every stock in the universe (122 names) is now ranked and shown
  with three independent, colour-graded A–E scores — **Leadership** (how strong it is), **Entry
  Quality** (is the price buyable or already too extended), and **Risk** (how dangerous) — plus a
  **setup status** (Actionable, Breakout-watch, Pullback-watch, Extended, Avoid, or
  Risk-off-watchlist) and a plain-language reason. Two filters let you narrow the table by **sector**
  and by **setup status**.
- **Stock Detail (`/stocks/[ticker]`)**: Clicking a stock opens a page showing the same three scores,
  each with the named components that produced it, plus the setup status and reason. The scores are
  guaranteed identical to the leaderboard (the whole point of "compute once, show everywhere").
- **Theme Leaderboard (`/themes`)**: The 11 themes (AI/data-centre, semiconductors, cybersecurity,
  nuclear/uranium, defence, homebuilders, etc.) are ranked by a price-confirmed **Theme Score**. Each
  row shows the theme's 1-month and 3-month basket return, how many of its members are above their
  50-day average ("breadth"), a trend label, and — when expanded — its member tickers and score
  breakdown.
- **Completed Dashboard (`/`)**: The two "pending" cards now show real data — the **candidate counts**
  (how many stocks are Actionable / Breakout-watch / Pullback-watch today) and a **Top Themes** list.
  The dashboard is now a complete at-a-glance daily snapshot: regime + breadth + top sectors + top
  themes + candidate counts + as-of date.
- **Risk-Off safety gate (built + tested)**: When the market regime is "Risk-off", the system marks
  **zero** stocks "Actionable" no matter how strong they look — it produces watchlist-only labels.
  (The market in the current data is Risk-on, so this gate is proven by automated tests rather than
  visible on screen this iteration.)

---

## Changed Behavior

- **Dashboard candidate counts & Top Themes**: Previously showed "pending" placeholders. Now show real
  numbers and a ranked theme list.
- **Sector Leaderboard (`/sectors`)**: Unchanged in output, but a shared internal helper used to label
  trends was reorganized; the sector page looks and behaves exactly as before (verified by tests).
- **Stock & Theme pages**: Previously empty "coming soon" placeholders; now fully functional.

---

## Backend-Only Items

- None. Every backend capability added this iteration is reachable in the UI. The Risk-off→zero-
  Actionable gate is backend logic verified by tests; it will become visible on screen in iter-5 when
  historical Risk-Off scanner runs exist.

---

## Incomplete Items

- **Full Stock Detail (deferred to iter-4 by design)**: The detail page shows scores + components
  only. The price/moving-average chart, volume series, theme-membership chips, and the concrete
  invalidation level ("below 50-DMA at $X") are scheduled for the next iteration.
- **Earnings-gap risk component**: One risk factor (`gap_climax`) needs earnings data the offline seed
  does not contain. It is shown as "not available" and excluded from the Risk score — never guessed.

---

## Config and Environment Changes

- **`config.yaml`** — added two new sections (no environment variables or secrets):
  - `theme_scores` — the weights and trend cut-offs for the new Theme Score.
  - `stock_sectors` — a factual map of each stock to its GICS sector (e.g. `NVDA: Technology`), used
    so a stock can be compared to its own sector. This is reference data, like the universe list.
  - The previously-reserved `scores` and `decision_rules` sections are now actively used and validated.
- No database migration (the data model is unchanged this iteration). The local database is rebuilt
  automatically from the committed seed; on the first restart after this change, each stock's sector
  is filled in automatically.

---

## Known Limitations

- **No "Actionable" stocks on the current date — and that is the correct, intended signal.** The
  market is strong (Risk-on) but the leaders have run up and are extended, so none currently meet the
  strict "buy-now" bar (strong **and** at a good entry **and** low risk). Trendora deliberately refuses
  to call an extended leader "Actionable" — it labels it "Extended" and says wait for a pullback. The
  Actionable filter therefore shows a clear "no matches" message today; Breakout-watch (8 stocks) and
  Pullback-watch (1 stock) do have entries. The thresholds live in the config file and can be tuned.
- **Scores are relative, not absolute.** Each score ranks a stock against its peers on the current
  date, so the exact 0–100 numbers will shift as the configuration is tuned; the rankings and labels
  are what matter. The illustrative weights are starting points to be refined against the forward-
  tested evidence in later iterations.
- **Breadth figures are "universe-relative"** (computed from Trendora's ~120-stock universe, not the
  whole market) and are labelled as such, so they are never overstated.
- **The dashboard recomputes the day's scores on each load** to derive the candidate counts (about 1–2
  seconds locally). This keeps a single source of truth; later iterations will save daily snapshots so
  the dashboard reads stored values instead.
