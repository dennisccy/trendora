# Demo Script — goal-ops-hardening-iter-15

**Mode:** record
**Date:** 2026-07-23
**Frontend URL:** http://localhost:3255
**Iteration:** 15

## Highlights

### Step 01 — Open Trendora's home page

- **Narration:** Let's start where every session begins — the home page, showing today's market regime at a glance.
- **Action:** Navigate to /
- **Point out:** The regime card and score appear immediately, with no error banner or blank space.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-15/step-01.png

### Step 02 — Check the Data Manager's status

- **Narration:** Next, the Data Manager, where new market data arrives. A status badge in the top bar is visible on every page and always reflects the backend's real, current health.
- **Action:** Navigate to /data
- **Point out:** The badge reads "Ready" with a green dot — an honest, live signal, never a guess.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-15/step-02.png

### Step 03 — See the latest completed data run

- **Narration:** The Job progress panel keeps a summary of the most recent data run, even if you weren't the one who started it.
- **Action:** Click "Job progress"
- **Point out:** The summary lists everything that was refreshed, including the forward-looking figures used on the Backtest page — computed once when the data arrived, never recalculated on the spot.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-15/step-03.png

### Step 04 — Confirm it in Run history too

- **Narration:** Scrolling down, the Run history table keeps a permanent record of every data run that has ever completed, even after a reload.
- **Action:** Click "Run history"
- **Point out:** That same run still shows a clean status here, with the same forward-looking figures confirmed a second, independent way.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-15/step-04.png

### Step 06 — No range cap enforced

- **Narration:** Even a span of more than a year is accepted without any warning or truncation.
- **Action:** Type "2026-07-17" into the "End date" field
- **Point out:** Notice there's no error message or size warning — just a normal, ready-to-submit form.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-15/step-06.png

### Step 07 — Open the Backtest page

- **Narration:** The Backtest page shows how a strategy would have performed historically, broken down by holding period. This round's work was all about keeping this exact page quick and correct even while other data work runs in the background.
- **Action:** Navigate to /backtest
- **Point out:** The full scorecard and evidence panel load with real numbers right away — no error card, no stuck loading skeleton.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-15/step-07.png

### Step 08 — Spot-check Scanner Runs

- **Narration:** One last stop — the Scanner Runs history, which lists every dated scan that has ever been saved.
- **Action:** Navigate to /scanner-runs
- **Point out:** Past runs are still listed here with their full detail one click away, confirming this round's behind-the-scenes work didn't disturb anything else.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-15/step-08.png

## Full tour (text only)

### Step 05 — Try a wide historical date range

- **Narration:** Back at the top of the Data Manager, the backfill form still accepts any historical range you like, with no hidden size limit.
- **Action:** Type "2025-06-01" into the "Start date" field
