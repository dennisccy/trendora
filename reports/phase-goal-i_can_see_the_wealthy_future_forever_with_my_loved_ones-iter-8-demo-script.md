# Demo Script — goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8

**Mode:** record
**Date:** 2026-06-12
**Frontend URL:** http://localhost:3835

## Highlights

### Step 01 — Dashboard — five-index market chart  [NEW]

- **Narration:** The main dashboard now tracks five major indexes at once. Alongside the familiar S&P 500, Nasdaq 100, Russell 2000, and Equal-Weight S&P 500, the Dow 30 (DIA) is plotted as a fifth line so you can see how the oldest and most-watched benchmark fits into the current regime.
- **Action:** Navigate to /
- **Point out:** Five distinct colored lines in the 'Major indexes & regime' chart, with 'Dow 30 (DIA)' appearing as the fifth legend entry.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8/step-01.png

### Step 02 — Dashboard — DIA legend entry confirmed  [NEW]

- **Narration:** The chart legend makes each line easy to read at a glance. 'Dow 30 (DIA)' is written out in full so you know immediately which line represents the Dow Jones Industrial Average — no ticker decoding required.
- **Action:** Navigate to /
- **Point out:** The legend row reading 'Dow 30 (DIA)' with its distinct color swatch, clearly distinguishable from the other four index entries.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8/step-02.png

### Step 03 — Data Manager — stage timings on a completed job  [NEW]

- **Narration:** Every completed data job now shows a 'Stage timings' panel that breaks down exactly where the time was spent. You can see the wall-clock elapsed time, how many dates or symbols were processed, and how many worker threads ran in parallel — all on the job card itself.
- **Action:** Navigate to /data
- **Point out:** The 'Stage timings' section on the completed job card, with a Backfill sub-block showing Elapsed, Dates, Concurrency, Per-date sum, and the speed-up ratio line.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8/step-03.png

### Step 04 — Data Manager — Backfill sub-block detail  [NEW]

- **Narration:** The Backfill sub-block shows the concrete benefit of parallel processing: 'Per-date sum' tells you how long all the dates would have taken if run one by one, while 'Elapsed' shows the actual wall-clock time with workers running in parallel.
- **Action:** Navigate to /data
- **Point out:** The Backfill sub-block with Elapsed, Dates, Concurrency, Per-date sum, and the speed-up ratio, all showing real non-zero values from the last completed job.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8/step-04.png

### Step 05 — Data Manager — 'Stage timings' tooltip  [NEW]

- **Narration:** Not sure what 'Stage timings' means? Click the small info icon right next to the heading and a plain-language definition pops up on the spot — no need to navigate away to the glossary.
- **Action:** Click "button[aria-label='Definition of stage timings']"
- **Point out:** The tooltip panel that appears after clicking the info icon, showing a readable definition of 'stage timings' in place.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8/step-05.png

### Step 06 — Data Manager — 'Concurrency' tooltip  [NEW]

- **Narration:** The 'Concurrency' stat label inside each stage block also carries its own info icon. One click explains exactly how many worker threads are running in parallel and why that matters for job speed.
- **Action:** Click "button[aria-label='Definition of concurrency']"
- **Point out:** The tooltip showing the definition of 'concurrency', appearing inline next to the stat it describes.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8/step-06.png

### Step 07 — Methodology — new glossary terms  [NEW]

- **Narration:** The Methodology glossary has been updated with two new entries — 'stage timings' and 'concurrency' — so the definitions are also discoverable outside the job card for anyone who wants to read them in context.
- **Action:** Navigate to /methodology
- **Point out:** Both 'stage timings' and 'concurrency' listed in the glossary with their full definitions, in the UNIVERSE & DATA category.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8/step-07.png

### Step 08 — Methodology — concurrency definition in glossary  [NEW]

- **Narration:** Scrolling through the glossary confirms the 'concurrency' entry with its full definition, matching the tooltip you saw on the job card. The same authoritative copy is used in both places — no risk of the tooltip and the glossary saying different things.
- **Action:** Navigate to /methodology
- **Point out:** 'concurrency' as a named glossary entry with a multi-sentence definition explaining parallel worker threads, immediately following the 'stage timings' entry.
- **Screenshot:** reports/demo/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8/step-08.png
