# Demo Script — goal-i_can_see_the_wealthy_future_forever-iter-17

**Mode:** record
**Date:** 2026-06-04
**Frontend URL:** http://localhost:3835
**Iteration:** 17

## Highlights

### Step 01 — Open the Backtest workspace

- **Narration:** We open Trendora's Backtest workspace. As of this iteration it has a new role: it is the single home for the platform's forward-tested track record — the historical evidence of how the rankings actually performed, read entirely from stored daily snapshots.
- **Action:** Navigate to /backtest
- **Point out:** The left navigation now lists ten sections with no 'System Health' link, and one global 'View as-of date' switcher sits at the top of the app. Scroll to the very bottom and the page now ends in a brand-new evidence section.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-17/step-01.png

### Step 02 — The relocated, now date-aware evidence  [NEW]

- **Narration:** At the bottom is the headline: the forward-tested evidence that used to live on the separate System Health page now lives here, and it is scoped to a point in time. The heading reads 'expanding window ≤' a date — the section pools every snapshot taken on or before the global as-of date.
- **Action:** Click "Excess vs benchmarks"
- **Point out:** Forward return is broken out by A–E score bucket, each row showing its mean return and its exact sample size n. Moving the global date switcher to an earlier date re-points this whole section to only the snapshots on or before that date — the sample n shrinks — and returning to the latest date reproduces the full all-history numbers. Thin rows are flagged ⚠ so low sample is never mistaken for a solid result.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-17/step-02.png

### Step 03 — Breakdowns by setup, regime and chart pattern  [NEW]

- **Narration:** The same as-of-scoped evidence is sliced several more ways: excess return versus the SPY and QQQ benchmarks, by setup type, by market regime, and by detected chart pattern — VCP, pullback-to-rising-average, and flat-base breakout.
- **Action:** Click "Flat-base breakout"
- **Point out:** Every cell carries its own sample size n. A cell with no observations shows an honest em-dash '—', never a fabricated 0%. It is the very same evidence System Health used to show, except it now answers 'as of this date, did it work?'
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-17/step-03.png

### Step 04 — The control-group honesty check  [NEW]

- **Narration:** Right at the bottom is the control-group comparison — the platform's built-in honesty check. It lines the top-ranked cohort up against random same-sector peers and the SPY, QQQ and sector-ETF benchmarks, so you can judge whether the selection truly beat plain sector beta.
- **Action:** Click "Sector ETF"
- **Point out:** The top-ranked cohort row is highlighted, and every row shows its return and sample n at the chosen horizon. If the selection only matched a random same-sector basket, this table would say so — it is not built to flatter the rankings.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-17/step-04.png

### Step 06 — System Health is retired — one home for the evidence  [NEW]

- **Narration:** Finally, the old System Health page is gone. Typing its address straight into the browser now returns a plain 404 — the forward-tested evidence has exactly one home.
- **Action:** Navigate to /system-health
- **Point out:** A 404 'This page could not be found'. There is no second copy of this evidence and no second date control anywhere in the app: one source of truth, read through one global as-of date.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-17/step-06.png

## Full tour (text only)

### Step 05 — One shared horizon control re-points everything

- **Narration:** The whole page follows one shared Horizon control. Switching it from 60 to 20 days instantly re-points the realized-return attribution and the evidence below it alike.
- **Action:** Click the "20d" button
- **Point out:** The switch is purely client-side — no page reload and no new network request, because every horizon ships in a single payload. One date switcher and one horizon control drive the entire page; there is deliberately no second control to drift out of sync.
