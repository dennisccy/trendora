# Demo Script — goal-ops-hardening-iter-28

**Mode:** record
**Date:** 2026-07-27
**Frontend URL:** http://localhost:3255
**Iteration:** 28

## Highlights

### Step 01 — See today's market at a glance

- **Narration:** The homepage opens straight to today's market score. There's no setup and nothing to wait for.
- **Action:** Navigate to /
- **Point out:** The Market Regime score, already filled in on the very first load.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-28/step-01.png

### Step 08 — Open Data Manager while it's still starting up

- **Narration:** The Data Manager page shows its run history right away. The app never makes you wait for it to finish starting up first.
- **Action:** Navigate to /data
- **Point out:** The run history list, ready immediately.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-28/step-08.png

### Step 09 — See when work is happening in the background

- **Narration:** If the app is still crunching numbers behind the scenes, it says so plainly on this page. Nothing is hidden.
- **Action:** Navigate to /data
- **Point out:** The background-compute status.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-28/step-09.png

### Step 13 — An honest answer when there's nothing new to do

- **Narration:** Weekends have no trading days, so the app says plainly that no new snapshots were needed. It never pretends to have done work it didn't do.
- **Action:** Navigate to /data
- **Point out:** The message explaining why nothing new was created.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-28/step-13.png

### Step 17 — No artificial limit on how much you can request

- **Narration:** The app accepts the whole range in one request. That's 412 calendar days, with no need to split it into smaller chunks.
- **Action:** Navigate to /data
- **Point out:** The accepted range, covering all 412 calendar days.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-28/step-17.png

### Step 18 — Look up a past scan instantly

- **Narration:** Opening a specific day from years ago, like February 15, 2018, is instant. It was already worked out when the data first came in, so nothing needs recomputing now.
- **Action:** Navigate to /scanner-runs/1872
- **Point out:** A stored snapshot from that exact day, served instantly.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-28/step-18.png

### Step 19 — Open the time-machine view of the market

- **Narration:** The Backtest page loads cleanly on its own. It never has to wait on heavier work that might be running elsewhere.
- **Action:** Navigate to /backtest
- **Point out:** The time-machine control at the top of the page.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-28/step-19.png

### Step 20 — Revisit a specific day without recomputing it

- **Narration:** Looking up March 15, 2018 again shows the exact same numbers right away. The app reads what it already saved instead of redoing the work.
- **Action:** Navigate to /backtest?asof=2018-03-15
- **Point out:** The historical badge and scorecard for that exact date.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-28/step-20.png

## Full tour (text only)

### Step 02 — Browse the ranked stock list

- **Narration:** The Stocks page lists ranked companies right away. Familiar names, like Travelers, show up immediately.
- **Action:** Navigate to /stocks
- **Point out:** A ranked list of stocks, filled in already.

### Step 03 — Open one stock's own page

- **Narration:** Clicking into one stock, like Apple, shows its price and history at once. No extra lookup step is needed.
- **Action:** Navigate to /stocks/AAPL
- **Point out:** Apple's price and history, right there on the page.

### Step 04 — Check how stocks group by sector

- **Narration:** Sectors group related companies and funds together. This one groups cybersecurity names, including the fund HACK.
- **Action:** Navigate to /sectors
- **Point out:** Real sector groupings, not placeholders.

### Step 05 — See the record behind every claim

- **Narration:** The Evidence page keeps a running ledger of certified claims. A pattern only counts as proven once it earns a place on this ledger.
- **Action:** Navigate to /evidence
- **Point out:** The certified-claims ledger.

### Step 06 — Check a personal watchlist

- **Narration:** A personal watchlist works too. This one includes Johnson & Johnson, with real figures attached.
- **Action:** Navigate to /watchlist
- **Point out:** Real holdings on the watchlist, not sample data.

### Step 07 — Try the event-study research tool

- **Narration:** A dedicated research tool lets you set up and study patterns around chosen events.
- **Action:** Navigate to /research/event-study
- **Point out:** The event-study setup panel.

### Step 10 — Pick a date range to check

- **Narration:** Typing in a start date begins a new data check.
- **Action:** Type "2026-05-02" into "job-start-date"
- **Point out:** The start-date field being filled in.

### Step 11 — Set the end of the range

- **Narration:** A two-day range is entered, covering a weekend with no trading days.
- **Action:** Type "2026-05-03" into "job-end-date"
- **Point out:** The end-date field being filled in.

### Step 12 — Submit the request

- **Narration:** One click submits the request. No extra confirmation step is needed for a plain check like this.
- **Action:** Click the "Start" button
- **Point out:** The Start button being pressed.

### Step 14 — Ask for a much longer stretch of history

- **Narration:** This time the start date reaches back over a year.
- **Action:** Type "2025-06-01" into "job-start-date"
- **Point out:** The start-date field.

### Step 15 — Set a far-out end date

- **Narration:** The end date is set more than a year after the start. That's a much bigger request than a single day.
- **Action:** Type "2026-07-17" into "job-end-date"
- **Point out:** The end-date field.

### Step 16 — Submit the long-range request

- **Narration:** One click submits the whole multi-year request at once.
- **Action:** Click the "Start" button
- **Point out:** The Start button being pressed again.
