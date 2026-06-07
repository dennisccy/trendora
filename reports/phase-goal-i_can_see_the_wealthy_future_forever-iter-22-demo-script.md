# Demo Script — goal-i_can_see_the_wealthy_future_forever-iter-22

**Mode:** record
**Date:** 2026-06-07
**Frontend URL:** http://localhost:3835
**Iteration:** 22

## Highlights

### Step 01 — Data Manager — page loads

- **Narration:** Open the Data Manager. The page shows a live coverage summary, a job form, and a job progress card — all without any backend error.
- **Action:** Navigate to /data
- **Point out:** The heading 'Data Manager' and the Dataset coverage card with six metrics including Price History, Universe, Symbols, and Trading Days. The backend status line reads 'Backend OK'.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-22/step-01.png

### Step 02 — Backfill job runs — no source label in header  [NEW]

- **Narration:** Start a backfill using the prefilled gap dates. When it finishes, the Job progress header reads only the date range with no import-source segment, because backfill does not use a live provider.
- **Action:** Click the "Start" button
- **Point out:** The job progress card header reading 'backfill job · <start> → <end>' with no source name. The status badge is green 'ok' and the Snapshots backfilled row shows N/N dates.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-22/step-02.png

### Step 03 — Switch to Fetch — Import source picker appears

- **Narration:** Change the job kind to 'Fetch EOD prices'. An Import source dropdown appears alongside an availability line that tells you whether each provider needs an API key.
- **Action:** Navigate to /data
- **Point out:** The 'Import source' dropdown now visible. The availability line shows the selected source as 'available' (green) or 'needs key' (amber).
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-22/step-03.png

### Step 04 — Needs-key source — masked key field appears

- **Narration:** Pick Tiingo, which requires an API key. A password-masked field labeled 'Session API key for Tiingo' appears immediately, with a note that the key is held in memory for this run only and never stored anywhere.
- **Action:** Navigate to /data
- **Point out:** The masked key field (dots, not plain text) and the helper text confirming the key is never written to disk, the database, the run log, a cookie, or echoed back.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-22/step-04.png

### Step 05 — API key never appears in error messages  [NEW]

- **Narration:** When a fetch with a pasted key fails at the provider, every error message on the job card and in run history contains no trace of the key or any URL query string — the secret is scrubbed at the source before it ever leaves the backend.
- **Action:** Navigate to /data
- **Point out:** Provider error messages like 'HTTP 403 at https://api.tiingo.com/…/prices' with no ?token=… or ?apikey=… visible anywhere in the text.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-22/step-05.png

### Step 06 — Resumable imports panel — survives a backend restart  [NEW]

- **Narration:** After a backend restart the in-memory job is gone, but any paused import is still listed. The 'Resumable imports' panel reads from the database checkpoint, so progress is never lost between restarts.
- **Action:** Navigate to /data
- **Point out:** The 'Resumable imports' card below the job progress area, showing the chunk X/N badge, source label, date range, symbols done and remaining, and a Resume button — all populated from the durable checkpoint.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-22/step-06.png

### Step 07 — Resume rejected gracefully — inline error, page stays up  [NEW]

- **Narration:** Clicking Resume without the required API key shows an inline alert explaining exactly what is needed. The page stays fully interactive — no crash, no reload required.
- **Action:** Click "[data-testid="resume-button"]"
- **Point out:** The inline alert message that the source requires a key, with the rest of the Data Manager form and panel still visible and usable below it.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-22/step-07.png

### Step 08 — Coverage card and run history intact after all changes

- **Narration:** The Dataset coverage card and the full run history table are completely unchanged after the chunking and resume machinery was added. All six coverage metrics and all seven run history columns are present with no regressions.
- **Action:** Navigate to /data
- **Point out:** All six coverage metrics (Price History, Universe, Symbols, Trading Days, Snapshot Dates, Backfill Gaps) and the run history table with its Started / Kind / Range / Status / Symbols / Snapshots / Summary columns.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-22/step-08.png
