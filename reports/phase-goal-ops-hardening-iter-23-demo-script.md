# Demo Script — goal-ops-hardening-iter-23

**Mode:** record
**Date:** 2026-07-25
**Frontend URL:** http://localhost:3255
**Iteration:** 23

## Highlights

### Step 01 — Open Trendora's dashboard

- **Narration:** Let's take a quick tour of Trendora, the equity screening and evidence dashboard. It opens straight to today's market snapshot.
- **Action:** Navigate to /
- **Point out:** A live status banner at the top always describes today's data in plain language — nothing is ever hidden behind a normal-looking dashboard.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-23/step-01.png

### Step 02 — Check the Data Manager's honest status

- **Narration:** Now let's visit the Data Manager, where new market data arrives. The status badge in the top bar is visible on every page and always reflects the backend's real, current health — never a guess, and never stuck mid-boot without saying so.
- **Action:** Navigate to /data
- **Point out:** The badge reads "Ready," and the Run history table below keeps a permanent record of every data job that's ever run.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-23/step-02.png

### Step 06 — See the honest zero-work explanation

- **Narration:** Back on the Run history table, the job that just ran shows up immediately — and when there's nothing new to fetch, Trendora says so plainly instead of just marking the job "done" like a real one.
- **Action:** Navigate to /data
- **Point out:** The new row explains it plainly: 2 non-trading days in the range, no new snapshots added.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-23/step-06.png

### Step 08 — No range cap enforced

- **Narration:** Filling in a span of well over a year, from mid-2025 through mid-2026, is accepted without any warning or truncation.
- **Action:** Type "2026-07-17" into "job-end-date"
- **Point out:** Notice there's no error message or size warning — just a normal, ready-to-submit form covering the full span requested.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-23/step-08.png

### Step 09 — Aggregates computed once, at ingest

- **Narration:** Every backfill computes its forward-looking aggregates immediately, as part of the job itself — never recalculated later just because someone's looking. Here's a stored snapshot from a past scan.
- **Action:** Navigate to /scanner-runs/1436
- **Point out:** The market regime score for that date, 70.76, is a stored read from when the job originally ran — not something calculated on the spot right now.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-23/step-09.png

### Step 10 — Every page loads only what it needs

- **Narration:** Trendora doesn't just feel fast — every page's loading time is measured and checked against a committed budget. Here's a stock detail page, scores and all.
- **Action:** Navigate to /stocks/AAPL
- **Point out:** The page renders this stock's real, current data — including a live price of $304.89 — well inside its own committed time budget.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-23/step-10.png

### Step 12 — Backtest evidence, served instantly from storage

- **Narration:** At the latest date, Backtest doesn't calculate anything on the spot — it simply displays evidence that was already computed and stored ahead of time.
- **Action:** Navigate to /backtest
- **Point out:** The full forward-tested evidence panel renders immediately, with no refreshing banner and no waiting.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-23/step-12.png

## Full tour (text only)

### Step 03 — Request a small backfill

- **Narration:** The same page's backfill form lets you request historical data for any date range. Let's fill in a short two-day window.
- **Action:** Type "2026-05-02" into "job-start-date"
- **Point out:** The start-date field now reads 2026-05-02.

### Step 04 — Finish the date range

- **Narration:** One more field completes the request.
- **Action:** Type "2026-05-03" into "job-end-date"
- **Point out:** The end-date field now reads 2026-05-03.

### Step 05 — Submit the backfill job

- **Narration:** Clicking Start submits the job. Trendora checks the range against what it already has and only fetches what's actually missing.
- **Action:** Click the "Start" button
- **Point out:** The job is submitted right away — no need to wait on this page for it to finish.

### Step 07 — Try a much wider date range

- **Narration:** The same form accepts any historical range you like, with no artificial limit on how much history you can request in one go. Let's fill in a much wider window this time.
- **Action:** Type "2025-06-01" into "job-start-date"
- **Point out:** The start-date field now reads 2025-06-01.

### Step 11 — Research pages load correctly too

- **Narration:** The tour continues to a research page most owners check less often — it loads just as reliably as the rest of the app.
- **Action:** Navigate to /research/event-study
- **Point out:** The event-study heading and its content render correctly, with no blank or frozen frame.

### Step 13 — Heavy background number-crunching never slows the app down

- **Narration:** When Trendora computes a big batch of forward-looking evidence in the background, the rest of the app keeps answering normally the whole time — this is measured, not just claimed.
- **Action:** Navigate to /backtest
- **Point out:** Across a measured 68.79 s background computation window, Backtest's slowest reply was 7.119 s and the health check's slowest was 0.253 s — both comfortably inside budget — while memory stayed with 58.2% headroom free the entire time.

### Step 14 — An older result, shown honestly while a new one finishes

- **Narration:** Ask Backtest for a date whose own evidence hasn't finished computing yet, and it never leaves you staring at a blank screen — it instantly shows the last complete version it has, clearly labeled, while the new one finishes in the background.
- **Action:** Navigate to /backtest?asof=2026-06-15
- **Point out:** A "Refreshing — showing the last complete evidence" banner names exactly which older, complete result is being shown, while the page still renders full evidence right away — never a blank wait.
