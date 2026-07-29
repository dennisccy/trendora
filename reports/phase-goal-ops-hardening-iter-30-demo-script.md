# Demo Script — goal-ops-hardening-iter-30

**Mode:** record
**Date:** 2026-07-29
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Open the Evidence page

- **Narration:** This iteration refactored the forward aggregate calculator to use bounded memory. Let's verify the Evidence page still loads with all its claim cards intact.
- **Action:** Navigate to /evidence
- **Point out:** The page shows 7 claim cards, each with its title and badge fully rendered.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-30/step-01.png

### Step 02 — Scroll to the drawdown expectations table

- **Narration:** The backend now chunks its accumulators, so the historical data tables should load without memory pressure.
- **Action:** Click the "Historical drawdown & dry-spell expectations" heading
- **Point out:** The first card's 'Historical drawdown & dry-spell expectations' table shows real figures like phases, max drawdown depth, and time to recover.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-30/step-02.png

### Step 03 — Verify the Backtest page

- **Narration:** The core backtest computation is unchanged; its caller now uses bounded accumulation.
- **Action:** Navigate to /backtest
- **Point out:** The page displays the dataset coverage panel with real metrics (price history range, universe size, trading days).
- **Screenshot:** reports/demo/goal-ops-hardening-iter-30/step-03.png

## Full tour (text only)

### Step 04 — Open Factor Lab to spot-check research surface

- **Narration:** Factor Lab shares a similar join pattern that this iteration fixed in a sibling function. Let's confirm it loads.
- **Action:** Navigate to /research/factor-lab
- **Point out:** The page shows the Factor Lab heading and the factors table renders with real Rank-IC values.
