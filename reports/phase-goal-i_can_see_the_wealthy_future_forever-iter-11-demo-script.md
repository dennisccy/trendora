# Demo Script — goal-i_can_see_the_wealthy_future_forever-iter-11

**Mode:** record
**Date:** 2026-06-02
**Frontend URL:** http://localhost:3835
**Iteration:** 11

## Highlights

### Step 01 — Open Trendora

- **Narration:** We start on Trendora's daily dashboard — a research workstation that ranks the US market after the close. Everything lives in the left sidebar, including the Research area we're about to open.
- **Action:** Navigate to /
- **Point out:** The "Research" entry in the left sidebar — the home of Trendora's analysis labs.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-11/step-01.png

### Step 02 — Open the Factor Lab

- **Narration:** One click on Research opens the Factor Lab. Here you choose one of eight market signals and a time horizon, and Trendora shows — from its stored history — whether stocks with more of that signal actually went on to earn higher returns.
- **Action:** Click the "Research" link
- **Point out:** The decile-sort table and the rank-correlation card: the signal split into ten groups with each group's average forward return, raw and adjusted only for downside risk.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-11/step-02.png

### Step 03 — See effectiveness by market regime  [NEW]

- **Narration:** This panel is new: the same signal, now broken out by market regime — the market's prevailing weather. Each row asks whether the signal still sorts returns inside that one environment, so a signal that looks strong overall can be shown to depend on the conditions.
- **Action:** Click "Risk-off"
- **Point out:** Six regime rows — Strong risk-on, Risk-on, Narrow leadership, Choppy, Defensive, Risk-off — each with its own sample size, rank correlation, and top-minus-bottom spread.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-11/step-03.png

### Step 05 — Real numbers where there's enough data  [NEW]

- **Narration:** At this short horizon the well-sampled regimes fill in with genuine signed figures — how well the signal ranks future returns, and the gap between its best and worst groups, both raw and adjusted only for downside risk.
- **Action:** Click "Risk-off"
- **Point out:** A deep regime like Risk-on, with hundreds of observations, shows a real signed rank correlation and spread — not a placeholder.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-11/step-05.png

### Step 07 — Honest "NA", never a fabricated number  [NEW]

- **Narration:** And here's the discipline Trendora insists on: regimes without enough data show a plain "NA" beside their true, honest count — never a made-up zero dressed up as a result.
- **Action:** Click "Risk-off"
- **Point out:** Sparse regimes such as Strong risk-on and Defensive read "NA" with their real sample size (for example n=0 ⚠), keeping the evidence honest.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-11/step-07.png

## Full tour (text only)

### Step 04 — Switch to a 5-day horizon

- **Narration:** We switch the horizon to five trading days. Shorter horizons have the most observations, so more regimes clear the minimum sample and fill in with real numbers.
- **Action:** Click the "5d" button
- **Point out:** The whole lab — including the regime table — re-points to the new horizon.

### Step 06 — Switch to a 60-day horizon

- **Narration:** Now we stretch the horizon to sixty trading days. Far fewer observations survive that long, so several regimes fall below the minimum sample.
- **Action:** Click the "60d" button
- **Point out:** The table re-points again, this time toward sparser regimes.
