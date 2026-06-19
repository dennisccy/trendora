# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## What This Phase Changed (For Context)

No UI elements changed. This iteration fixed a backend bar-cache bug that caused the `/data` page to get stuck in a skeleton/loading state under certain conditions (iter-36 regression). The verification goal is: confirm `/data` hydrates fully and shows the membership-timeline and coverage-diagnostic sections.

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8835`
- Do NOT open multiple browser tabs to `/data` at the same time — concurrent requests can exhaust the database connection pool and reproduce the skeleton bug

---

## Verification Steps

1. Navigate to `http://localhost:8835/api/health` in your browser
   - **Expect:** A JSON response containing `"readiness": "ready"` and `"db_ok": true`
   - **Broken looks like:** Response shows `"readiness": "warming"` or the page returns an error. Wait 60 seconds and retry before proceeding.

2. Open a new tab and navigate to `http://localhost:3835/data` — then wait up to 30 seconds without reloading
   - **Expect:** The content area populates with visible sections (membership-timeline chart and coverage-diagnostic cards/table). The text "Checking backend…" disappears within 30 seconds.
   - **Broken looks like:** "Checking backend…" still visible after 30 seconds, or the entire content area remains blank/white. This is the iter-36 regression symptom — record a screenshot and report FAIL.

3. On the same `/data` page, scroll down to the membership-timeline chart
   - **Expect:** A chart showing a rising step-function of symbol counts over time is rendered with visible lines, bars, or segments — not a blank white area. Below or beside the chart, the words "Survivorship", "Warm-up", and "Universe-relative" each appear as labels.
   - **Broken looks like:** Chart area is blank/white, or one of the three honesty labels is missing.

4. Still on `/data`, scroll to the coverage-diagnostic section (cards or table showing symbol counts per date)
   - **Expect:** An admitted count (positive integer, e.g., "504") is displayed. Three exclusion-reason fields labeled "below_history", "below_price", and "below_ADV" (or equivalent readable text) each show a numeric value. At least one of the three is non-zero.
   - **Broken looks like:** All three exclusion counts are 0 simultaneously, fields show "–" or "undefined", or the section is missing entirely.

5. Open a new tab and navigate to `http://localhost:3835/stocks`
   - **Expect:** A list of stock ticker symbols populates within 10 seconds. A single date input control is visible in the toolbar (not two date pickers). No persistent "Checking backend…" skeleton.
   - **Broken looks like:** Stock list does not populate after 10 seconds, or two date pickers appear on the page.

6. In the same `/stocks` tab, click on the "NVDA" row (or navigate to `http://localhost:3835/stocks/NVDA` directly)
   - **Expect:** The Stock-Detail page loads for NVDA showing its ticker name, a bucket label (one of A–E), and at least one numeric score value. No 404 page.
   - **Broken looks like:** 404 error, or all score and bucket fields are blank.

---

## What "Working Correctly" Looks Like

- `/data` page content area is fully populated within 30 seconds of a single page load (no skeleton)
- Membership-timeline chart shows a rendered step-function with three honesty labels present
- Coverage-diagnostic shows non-zero admitted and exclusion counts
- `/stocks` and `/stocks/NVDA` load normally — this backend fix made no scoring changes

## Common Issues

- **"/data" stuck at "Checking backend…" after 30 s:** Do not reload repeatedly — each reload fires another `GET /api/data` request and can pile up connections. Check `http://localhost:8835/api/health` for `"readiness"`. If still warming, wait 2 minutes and try a single fresh load.
- **Backend not responding at :8835:** The backend may still be in its background warm-up (can take 1–3 minutes after a cold start). Wait and check `/api/health` until `"readiness": "ready"`.
- **Second concurrent /data tab:** If you accidentally opened two `/data` tabs at the same time and both appear stuck, close both, wait 30 seconds, then open a single tab.
