# Demo Script — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-26

**Mode:** record
**Date:** 2026-06-17
**Frontend URL:** http://localhost:3835
**Iteration:** 26

## Highlights

### Step 01 — Data Manager loads cleanly

- **Narration:** We open the Data Manager — the central hub for importing and managing price history. The page shows a live backend status, the committed symbol count, and all import sections without any errors.
- **Action:** Navigate to /data
- **Point out:** The 'Data Manager' heading and the backend status line reading 'Ready · provider: seed · 585 symbols' are both visible immediately.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-26/step-01.png

### Step 02 — Unfinished-imports panel surfaces the paused job  [NEW]

- **Narration:** When an Expand-universe job hits a Yahoo authentication wall, it no longer vanishes silently. The Unfinished Imports section appears with an amber 'Resumable' badge and a plain-English explanation of exactly what paused the job.
- **Action:** Navigate to /data
- **Point out:** Look for the 'Unfinished imports' heading and the amber 'Resumable' badge on the job row — this is new behaviour replacing the old silent '0 passers' ghost completion.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-26/step-02.png

### Step 03 — Job card shows an honest, human-readable message  [NEW]

- **Narration:** The card explains that the job paused due to a provider rate-limit, shows exactly how far it got (chunk 22 of 22, 548 symbols processed), and tells the operator what to do next — all in plain English, with no raw URLs or secret tokens leaking through.
- **Action:** Navigate to /data
- **Point out:** The message 'Paused — hit a provider rate-limit (429); progress saved at chunk 22/22 (0 symbols remaining). Resume to continue.' is displayed. There are no long alphanumeric strings or Yahoo URLs in the card.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-26/step-03.png

### Step 04 — Click Resume to hand the job back to the queue  [NEW]

- **Narration:** One click on the Resume button is all it takes. The job immediately transitions from 'Resumable' to 'Running', picking up exactly where it left off — no duplicate downloads, no data loss.
- **Action:** Click the "Resume" button
- **Point out:** After clicking Resume the badge on that job row changes to indicate a running state. The page stays on /data and shows no error banners.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-26/step-04.png

### Step 05 — As-of date switcher stays independent of job form

- **Narration:** Switching the global as-of date to a historical snapshot updates the page URL and the header — but the Expand job date inputs are untouched. The two controls are completely independent, so a historical browse never accidentally populates a job form.
- **Action:** Click "[data-testid='asof-step-prev']"
- **Point out:** The URL now includes ?asof=2026-06-15 and the header reads 'Viewing as-of 2026-06-15 (historical)'. All job form date fields remain empty.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-26/step-05.png

### Step 06 — Stocks page still loads all 122 members

- **Narration:** The iter-26 backend changes also repaired a corrupted seed manifest. The Stocks page confirms the fix: all 122 universe members load with full leadership, sector, and theme data intact.
- **Action:** Navigate to /stocks
- **Point out:** The Stocks page shows 122 stocks with their sector, setup, and theme columns populated — no blank screen or 'backend unavailable' message.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-26/step-06.png
