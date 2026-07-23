# Demo Script — goal-ops-hardening-iter-14

**Mode:** record
**Date:** 2026-07-23
**Frontend URL:** http://localhost:3255
**Iteration:** 14

## Highlights

### Step 01 — Open Trendora's home page

- **Narration:** Let's start on Trendora's home page, where the current market regime is summarized at a glance.
- **Action:** Navigate to /
- **Point out:** The regime chart appears right away, with no error banner or blank space.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-14/step-01.png

### Step 02 — Check the Data Manager's status

- **Narration:** Now let's visit the Data Manager, where new market data arrives. The status badge in the top bar is visible on every page and always reflects the backend's real, current health.
- **Action:** Navigate to /data
- **Point out:** The badge reads "Ready" with a green dot — an honest signal, not a guess, even while other work may be happening behind the scenes.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-14/step-02.png

### Step 03 — See the latest completed data run

- **Narration:** The Job progress panel keeps a summary of the most recent data run, even if you weren't the one who started it.
- **Action:** Click "Job progress"
- **Point out:** The summary line lists everything that was refreshed, including the forward-looking aggregates used elsewhere in the app — computed once when the data arrived, not recalculated every time someone looks.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-14/step-03.png

### Step 04 — Confirm it in Run history too

- **Narration:** Scrolling down, the Run history table keeps a permanent record of every data run that's ever completed.
- **Action:** Click "Run history"
- **Point out:** That same run shows a clean "ok" status here too, with the forward-looking aggregates confirmed refreshed a second, independent way.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-14/step-04.png

### Step 06 — No range cap enforced

- **Narration:** Even an eleven-year span is accepted without any warning or truncation — there's no cap on how much data a single request can cover.
- **Action:** Type "2026-07-20" into the "End date" field
- **Point out:** Notice there's no error message or size warning — just a normal, ready-to-submit form.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-14/step-06.png

### Step 07 — Open the Backtest page

- **Narration:** The Backtest page shows how a strategy would have performed historically, broken down by holding period.
- **Action:** Navigate to /backtest
- **Point out:** The full scorecard and return-attribution lists load with real numbers right away — no error card, no stuck loading skeleton.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-14/step-07.png

### Step 08 — Spot-check the Evidence page

- **Narration:** One last quick look at the Evidence page confirms this round's behind-the-scenes work didn't disturb anything else.
- **Action:** Navigate to /evidence
- **Point out:** It loads normally, just as it always has.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-14/step-08.png

## Full tour (text only)

### Step 05 — Try a wide date range

- **Narration:** Back at the top of the Data Manager, the backfill form still accepts any historical range you like, with no artificial limit on how much history you can request in one go.
- **Action:** Type "2015-01-01" into the "Start date" field
