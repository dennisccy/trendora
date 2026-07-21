# Demo Script — goal-ops-hardening-iter-6

**Mode:** record
**Date:** 2026-07-21
**Frontend URL:** http://localhost:3255
**Iteration:** 6

## Highlights

### Step 01 — Open the dashboard

- **Narration:** Trendora opens straight to today's market read — no sign-in required, and every card fills in with real numbers right away.
- **Action:** Navigate to /
- **Point out:** The Market Regime card reads "Risk-on 65.98/100" and the Market Phase & Severity card shows "Expansion" — both settle in well under a second.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-6/step-01.png

### Step 02 — Tuck away the regime x phase chart

- **Narration:** Further down the page, a "Regime x phase cross-view" chart lines up index performance against the market's phase history — you can hide it any time you don't need it.
- **Action:** Click the "Hide" button
- **Point out:** Clicking Hide collapses the whole chart down to a single small toggle button.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-6/step-02.png

### Step 03 — Bring the chart back — now noticeably snappier  [NEW]

- **Narration:** Clicking it again reloads the chart on demand. This iteration's fix shaved its real-browser load time from over two seconds down to under one, so the wait barely registers.
- **Action:** Click the "Show regime × phase cross-view" button
- **Point out:** The full two-pane chart reappears, already labeled with its as-of date.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-6/step-03.png

### Step 04 — Open Data Manager  [NEW]

- **Narration:** Data Manager tracks exactly how much price history and how many daily snapshots are on hand, including a calendar heatmap of coverage over time.
- **Action:** Navigate to /data
- **Point out:** The coverage heatmap and its color-coded legend now finish loading well inside their speed budget too.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-6/step-04.png

### Step 07 — Run the backfill

- **Narration:** Clicking Start kicks the job off immediately — this particular range covers two weekend days, so there's no real data to fetch.
- **Action:** Click the "Start" button
- **Point out:** The job finishes right away and honestly reports "2 non-trading" days rather than pretending it did work.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-6/step-07.png

### Step 08 — Check the run history stays honest

- **Narration:** Reloading the page and scrolling to Run history shows exactly what happened — a zero-work run is never dressed up as a normal success.
- **Action:** Navigate to /data
- **Point out:** The newest row carries a distinct grey "no new snapshots" badge instead of the green "ok" badge a real data-producing run gets.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-6/step-08.png

## Full tour (text only)

### Step 05 — Fill in a backfill start date

- **Narration:** In the "Start a fetch / backfill job" panel, you can queue a backfill for any date range directly from the browser.
- **Action:** Type "2026-05-02" into the "Start date" field

### Step 06 — Fill in the end date

- **Narration:** Rounding out the range with an end date is all it takes to define the job.
- **Action:** Type "2026-05-03" into the "End date" field
