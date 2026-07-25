# Demo Script — goal-ops-hardening-iter-22

**Mode:** record
**Date:** 2026-07-25
**Frontend URL:** http://localhost:3255
**Iteration:** 22

## Highlights

### Step 01 — Open Trendora

- **Narration:** Trendora opens on the Dashboard, its home for today's market status and stock rankings.
- **Action:** Navigate to /
- **Point out:** A status banner near the top says plainly whether today's data is fully fresh, rather than staying quiet about it.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-22/step-01.png

### Step 02 — Browse the stock rankings  [NEW]

- **Narration:** The Stocks page lists ranked tickers with real, evidence-checked scores. This round, the team confirmed pages like this one load quickly, pulling only the data they actually need.
- **Action:** Navigate to /stocks
- **Point out:** The list appears fully populated right away — confirmed this round to hold up even during heavier background work elsewhere in the app.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-22/step-02.png

### Step 04 — Open the Data Manager

- **Narration:** Behind the scenes, an operator uses the Data Manager to backfill historical data and watch ingest jobs run.
- **Action:** Navigate to /data
- **Point out:** The coverage panel shows exactly what's already stored before anything new is requested.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-22/step-04.png

### Step 08 — See the honest zero-work result

- **Narration:** Those two days turn out to be already fully covered, mostly non-trading days, so Trendora says so plainly instead of pretending to do work.
- **Action:** Navigate to /data
- **Point out:** The result explains there are no new snapshots, rather than staying silent or claiming success with no explanation.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-22/step-08.png

### Step 12 — See the full range accepted

- **Narration:** Trendora accepts the entire request and reports exactly how much ground it covers.
- **Action:** Navigate to /data
- **Point out:** 412 calendar days, accepted in a single request, with no artificial per-run limit.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-22/step-12.png

### Step 13 — Revisit a stored day

- **Narration:** Let's open one specific day that was already scanned a while back.
- **Action:** Navigate to /scanner-runs/1436
- **Point out:** It's labeled an immutable snapshot: stored exactly as scanned, never recalculated for today.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-22/step-13.png

### Step 14 — Check the backtest evidence

- **Narration:** The Backtest page never runs a fresh calculation while you wait — it only ever shows evidence that was already prepared in advance.
- **Action:** Navigate to /backtest
- **Point out:** The evidence shown is always a specific, dated version — current, or a clearly labeled still-good version, but never a live guess.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-22/step-14.png

### Step 15 — Confirm the app stays healthy under heavy background work  [NEW]

- **Narration:** This round, the team also confirmed something reassuring: even while a slow calculation runs in the background, Trendora keeps answering normally the whole time — nothing freezes, nothing goes down.
- **Action:** Navigate to /
- **Point out:** The status badge stays green and 'Ready' — measured this round to hold steady for the entire background-calculation window, with every page and the health check answering throughout.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-22/step-15.png

## Full tour (text only)

### Step 03 — Open the evidence ledger

- **Narration:** The Evidence page is Trendora's certified-claims ledger, where a pattern only counts as proven once it has survived independent testing.
- **Action:** Navigate to /evidence
- **Point out:** Nothing here gets called confident without real evidence behind it.

### Step 05 — Request a small backfill

- **Narration:** Let's ask for just two days of data.
- **Action:** Type "2026-05-02" into "job-start-date"
- **Point out:** The start date is set to 2026-05-02.

### Step 06 — Set the end date

- **Narration:** One day later closes out the range.
- **Action:** Type "2026-05-03" into "job-end-date"
- **Point out:** The end date is set to 2026-05-03.

### Step 07 — Submit the request

- **Narration:** Clicking Start sends the request.
- **Action:** Click the "Start" button
- **Point out:** The job is accepted immediately.

### Step 09 — Request a much wider backfill

- **Narration:** Now let's ask for something bigger: over a year of history in a single request.
- **Action:** Type "2025-06-01" into "job-start-date"
- **Point out:** The start date is set to 2025-06-01.

### Step 10 — Set the wide end date

- **Narration:** The range stretches all the way to 2026-07-17.
- **Action:** Type "2026-07-17" into "job-end-date"
- **Point out:** The end date is set to 2026-07-17.

### Step 11 — Submit the wide request

- **Narration:** Clicking Start sends the whole range in one go.
- **Action:** Click the "Start" button
- **Point out:** There's no prompt to split it into smaller pieces.
