# Demo Script — goal-ops-hardening-iter-16

**Mode:** record
**Date:** 2026-07-23
**Frontend URL:** http://localhost:3255
**Iteration:** 16

## Highlights

### Step 01 — Open Trendora's home page

- **Narration:** Let's start where every visit begins — the home page, showing today's market regime at a glance.
- **Action:** Navigate to /
- **Point out:** The regime card and score appear right away, with no error banner or blank space.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-16/step-01.png

### Step 02 — Check the Data Manager's status

- **Narration:** Next, the Data Manager, where new market data arrives. A status badge near the top of every page always reflects the backend's real, current health.
- **Action:** Navigate to /data
- **Point out:** The badge reads "Ready" in green — an honest, live signal, not a guess.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-16/step-02.png

### Step 03 — See the latest completed data run

- **Narration:** The Job progress panel keeps a summary of the most recent data run, even if you weren't the one who started it.
- **Action:** Click "Job progress"
- **Point out:** The summary lists everything that was refreshed, including the forward-looking figures used on the Backtest page — computed once when the data arrived, never recalculated on the spot.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-16/step-03.png

### Step 04 — Confirm it in Run history too

- **Narration:** Scrolling down, the Run history table keeps a permanent record of every data run that has ever completed, even after a reload.
- **Action:** Click "Run history"
- **Point out:** That same run still shows a clean status here, with the same forward-looking figures confirmed a second, independent way.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-16/step-04.png

### Step 06 — No range cap enforced

- **Narration:** Even a span of more than a decade is accepted without any warning or truncation.
- **Action:** Type "2026-07-22" into the "End date" field
- **Point out:** Notice there's no error message or size warning — just a normal, ready-to-submit form.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-16/step-06.png

### Step 07 — Open the Backtest page's evidence panel  [NEW]

- **Narration:** The evidence panel at the bottom of the Backtest page now always tells you plainly whether it's showing the fully current numbers, a clearly labeled last-good version while newer data finishes processing, or an honest not-yet-computed notice — instead of silently going quiet or making you wait with no explanation.
- **Action:** Navigate to /backtest
- **Point out:** The evidence tables are fully populated with real figures and there's no refreshing notice showing — this is the everyday, fully current view, now backed by an explicit on-screen guarantee.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-16/step-07.png

### Step 08 — Spot-check Scanner Runs

- **Narration:** One last stop — the Scanner Runs history, which lists every dated scan that has ever been saved.
- **Action:** Navigate to /scanner-runs
- **Point out:** Past runs are still listed here with their full detail one click away, confirming this round's behind-the-scenes changes didn't disturb anything else.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-16/step-08.png

## Full tour (text only)

### Step 05 — Try a wide historical date range

- **Narration:** Back at the top of the Data Manager, the backfill form still accepts any historical range you like, with no hidden size limit.
- **Action:** Type "2015-06-01" into the "Start date" field
