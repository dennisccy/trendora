# Demo Script — goal-i_can_see_the_wealthy_future-iter-11

**Mode:** record
**Date:** 2026-05-31
**Frontend URL:** http://localhost:3835
**Iteration:** 11

## Highlights

### Step 01 — Open Trendora's daily dashboard

- **Narration:** We start on Trendora's home dashboard — the after-close read on the whole market: today's mood, breadth, and how many stocks are even worth acting on. It's the backdrop for everything that follows.
- **Action:** Navigate to /
- **Point out:** The Market Regime panel with its score and component breakdown, plus the candidate counts — Trendora always shows the reasoning, never just a verdict.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future-iter-11/step-01.png

### Step 02 — Find the VCP-flagged leaders on the Stock Leaderboard  [NEW]

- **Narration:** On the Stock Leaderboard, this release adds a brand-new VCP filter beside Sector and Setup, and a teal "VCP" badge on every flagged name. A VCP — Volatility Contraction Pattern — is Trendora's very first detected chart pattern.
- **Action:** Navigate to /stocks
- **Point out:** The new "VCP" dropdown (All / VCP only / Non-VCP) in the filter row, and the teal "VCP" badges marking flagged rows — they sit alongside the setup status, never replacing it.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future-iter-11/step-02.png

### Step 03 — Read the full VCP explanation on a flagged stock  [NEW]

- **Narration:** Opening a flagged name (STX) shows the whole story: why it qualifies, the exact breakout price to watch, and the price that would prove the pattern wrong — never a bare flag.
- **Action:** Navigate to /stocks/STX
- **Point out:** The teal "VCP" badge beside the "Extended" setup, and the "VCP — Volatility Contraction Pattern" card with its Pivot (breakout level) of $905.39 and an amber invalidation level — the same stored values the leaderboard serves.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future-iter-11/step-03.png

### Step 04 — Confirm the levels are real and per-stock  [NEW]

- **Narration:** A second flagged name (ORCL) proves the pattern isn't boilerplate — each stock gets its own measured pivot and invalidation, drawn from its own price history.
- **Action:** Navigate to /stocks/ORCL
- **Point out:** A different Pivot (breakout level) of $205.00 and invalidation $187.92 here — distinct from the previous stock, because they're computed from this stock's own chart.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future-iter-11/step-04.png

### Step 05 — See whether VCP names actually outperform  [NEW]

- **Narration:** Finally, the honest test: System Health now breaks forward returns into VCP versus non-VCP, so you can judge whether the pattern genuinely adds an edge — backed by sample sizes, not hype.
- **Action:** Navigate to /system-health
- **Point out:** The new "Forward return: VCP vs non-VCP" panel: VCP +3.18% (n=27, flagged ⚠ as a small sample) versus non-VCP +2.01% (n=1191), under the standing Survivorship bias banner.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future-iter-11/step-05.png
