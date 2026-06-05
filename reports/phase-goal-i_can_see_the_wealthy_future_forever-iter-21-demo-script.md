# Demo Script — goal-i_can_see_the_wealthy_future_forever-iter-21

**Mode:** record
**Date:** 2026-06-05
**Frontend URL:** http://localhost:3835
**Iteration:** 21

## Highlights

### Step 01 — Open the Data Manager

- **Narration:** Open the Data Manager — Trendora's home for growing its own price history. It loads straight to a coverage summary and a job panel, with no sign-in needed.
- **Action:** Navigate to /data
- **Point out:** The 'Dataset coverage' card showing your current price history, universe size, and snapshot counts, with the subtitle now pointing toward the Backtest evidence.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-21/step-01.png

### Step 02 — Choose a live fetch — the source picker appears  [NEW]

- **Narration:** Pick 'Fetch EOD prices' as the job kind and a brand-new Import source picker appears, pre-set to Yahoo. The picker is built entirely from configuration, so it lists every provider Trendora knows about.
- **Action:** Type "Fetch EOD prices" into the "Job kind" field
- **Point out:** The new Import source dropdown, and the green 'available' line telling you Yahoo is ready with no key required.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-21/step-02.png

### Step 03 — Switch to a key-gated source  [NEW]

- **Narration:** Switch the source to Tiingo and Trendora is honest about it — the status flips to an amber 'needs key', and a paste field appears for a key you provide for this run only.
- **Action:** Type "Tiingo · needs key" into the "Import source" field
- **Point out:** The amber 'needs key' status with the exact environment variable to set, plus the masked Session API key field and its promise: held in memory for this run only, never saved to disk and never echoed back.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-21/step-03.png

### Step 04 — No key, no silent failure  [NEW]

- **Narration:** Press Start without pasting a key and Trendora stops you up front with a clear message. There's no half-started job and no guessing — it tells you exactly which key the chosen source needs.
- **Action:** Click the "Start" button
- **Point out:** The inline warning that the selected source requires a key, naming the environment variable, while the Job progress card stays idle — nothing was started.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-21/step-04.png

### Step 05 — Paste a key — masked and kept for this run only  [NEW]

- **Narration:** Now paste a key and it shows only as dots. It stays masked on screen, lives in the browser's memory for just this run, and is never written to disk, the database, or the run log.
- **Action:** Type "demo-session-key-2468" into the "Session API key" field
- **Point out:** The Session API key field masking every character you type — a key you can supply without it ever being stored or shown back.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever-iter-21/step-05.png

## Full tour (text only)

### Step 06 — Backfill is untouched, and there's still one date control

- **Narration:** Switch back to a Backfill job and the source and key fields tidy themselves away — they only appear for live fetches. The familiar offline backfill still runs exactly as before, and the single as-of switcher in the header remains the only date control anywhere in the app.
- **Action:** Type "Backfill snapshots" into the "Job kind" field
- **Point out:** The Import source and key fields disappearing for a backfill job, confirming the new controls are additive and the one-date-switcher rule still holds.
