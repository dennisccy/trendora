# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-8
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8835`
- Seed data loaded (including DIA bars — a fresh database will have 159 symbols after seeding)
- At least one completed fetch+backfill job must be present on the `/data` page. If none exists, start a new job from `/data` and wait for it to complete before checking the timings block.

---

## Verification Steps

1. Open `http://localhost:3835/` in your browser
   - **Expect:** Dashboard loads; the "Major indexes & regime" chart is visible. The chart legend shows five entries: SPY, QQQ, IWM, RSP, and one labeled with "DIA" (e.g., "Dow 30 (DIA)"). Five distinct colored lines are drawn across the chart. If you see only four lines or no DIA entry in the legend, DIA was not loaded.

2. Navigate to `http://localhost:3835/data`
   - **Expect:** The data management page loads without an error banner. The job list section is visible.

3. Locate a completed job card in the job list (look for a success status indicator). Expand the card or scroll to its detail section.
   - **Expect:** A section labeled "Stage timings" is visible on the job card. If the job ran both a fetch and a backfill stage, you should see two sub-blocks — one labeled "Fetch" and one labeled "Backfill". Each sub-block shows non-zero values for "Elapsed", items processed (Symbols or Dates), and "Concurrency". If the job was backfill-only, only the "Backfill" sub-block appears (no Fetch sub-block at all).

4. Within the "Stage timings" section, look at the Backfill sub-block and find the speed-up line.
   - **Expect:** A line reading something like "2.1× faster than the per-date sum" is visible. The numeric ratio must be greater than 1. A "Per-date sum" duration is shown, and it is visibly larger than the actual "Elapsed" value. If the ratio reads "1.0×" or the line is absent, the parallel speed-up is not being displayed.

5. Still on the same job card, find the small info icon placed directly next to the "Stage timings" section header. Hover your mouse over it (do not click).
   - **Expect:** A tooltip pops up containing a plain-language explanation of what "stage timings" means. The tooltip text should be a readable sentence, not a blank box or a raw key like "stage_timings". Moving your cursor away should dismiss it.

6. Find the "Concurrency" label inside any stage sub-block on the same job card. Hover over the info icon next to that label.
   - **Expect:** A tooltip appears with a readable definition of "concurrency". The text is non-empty and distinct from the "stage timings" tooltip you saw in step 5.

7. Navigate to `http://localhost:3835/methodology`
   - **Expect:** The methodology/glossary page loads. Scroll through the glossary list and confirm that both "stage timings" and "concurrency" appear as named entries with non-empty definition text. If either entry is absent or shows placeholder text, the glossary was not updated.

---

## What "Working Correctly" Looks Like

- The dashboard chart legend has five entries and five visible lines; "DIA" or "Dow 30 (DIA)" is one of them.
- Every completed job card has a "Stage timings" section showing per-stage elapsed times, item counts, and a concurrency value. Backfill jobs show a speed-up ratio greater than 1.
- Both info icons (next to "Stage timings" and "Concurrency") reveal readable tooltip definitions on hover.
- The methodology glossary page lists "stage timings" and "concurrency" with definitions that match the tooltips.

## Common Issues

- **No "Stage timings" section on the job card**: The job may not have completed yet, or it may pre-date this iteration. Start a new job from `/data` and wait for completion.
- **Only four lines on the dashboard chart**: DIA seed data may not have been loaded. Check that the backend booted cleanly (`curl http://localhost:8835/health`) and that the seed ran after the code update.
- **Tooltip is blank or shows raw key text**: The backend glossary config may not have been updated, or the frontend is serving a cached build. Hard-refresh the page (Ctrl+Shift+R) and retry.
- **Speed-up ratio is 1.0×**: The backfill job may have covered only a single date (no parallelism possible), or `backfill_workers` is set to 1 in `config.yaml`. A multi-date backfill with the default workers=4 should show a ratio above 1.
