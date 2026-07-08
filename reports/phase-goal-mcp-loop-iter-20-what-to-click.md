# Phase goal-mcp-loop-iter-20 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-20
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running at `http://localhost:8255` (the Data Manager and Stocks pages show a "Backend unavailable" card if it isn't reachable)
- No login required
- No special setup needed — the shipped dataset already has a mix of fetched-but-not-yet-backfilled days and fully backfilled days, which is what step 6 below relies on

---

## Verification Steps

1. Open `http://localhost:3255/data` in your browser
   - **Expect:** The Data Manager page loads with a panel titled "Start a fetch / backfill job"; no "Backend unavailable" message appears.

2. Click the "Job kind" dropdown in that panel
   - **Expect:** Exactly three options: "Backfill snapshots", "Fetch EOD prices", "Fetch + backfill." There is **no** "Expand universe" option anymore — it has been removed.

3. Select "Fetch EOD prices," confirm the "Import source" dropdown that appears shows an option ending in "· available" (pick one if not), then click the "Start" button
   - **Expect:** A "Job progress" panel appears below showing a "Symbols fetched" line like "`0/588 (0 ok, 0 failed)`" — the total should be in the high 500s (at least 548). This is the headline change: Fetch used to only cover about 162 symbols; it now covers the whole committed stock pool automatically.

4. Scroll down to the "Per-date availability" card
   - **Expect:** The legend above the calendar grid shows **two separate labeled rows**: "PRICE DATA — CELL FILL" (with 6 small color swatches) and "SCORED SNAPSHOT — INDICATOR" (with one ringed swatch). These used to be squeezed into a single ambiguous "Coverage" row.

5. Look at the rightmost swatch in the "PRICE DATA — CELL FILL" row (labeled "full")
   - **Expect:** It is a bright **blue**, not the old amber/orange color. All 6 swatches should read as shades of blue, each one clearly lighter than the last.

6. Hover your mouse over a calendar cell that is brightly filled but has **no** ring around it, then hover a cell that **does** have a ring
   - **Expect:** The first cell's tooltip reads something like "...no snapshot yet — Backfill gap"; the second reads "...scored snapshot exists (Backfill)." The two tooltips should read clearly differently. (If every visible cell has a ring, the Fetch job you just started in step 3 will create some gap days once it finishes — wait a few seconds and re-check its most recent days.)

7. Back in the job form, select "Backfill snapshots" as the Job kind and click "Start"
   - **Expect:** A "Snapshots backfilled" line appears in the job progress panel; no error message appears anywhere on the page. (This confirms removing the old "Expand universe" option didn't break Backfill.)

8. Navigate to `http://localhost:3255/stocks` and click the word "Sector" in the table's column header, twice
   - **Expect:** The table re-sorts both times (an arrow icon appears/flips next to "Sector"). The page must **never** go blank or lose its left sidebar — this is a required regression check from an earlier fix.

9. Navigate to `http://localhost:3255/evidence`
   - **Expect:** The page loads with the heading "Evidence" visible — either a "No certified claims yet" message or a list of claims. No blank page, no "Backend unavailable" card.

10. Go back to `http://localhost:3255/data` and refresh the page (F5)
    - **Expect:** Everything from steps 1, 2, and 4–5 still looks the same after the refresh — the job-kind picker still has exactly 3 options and the legend still shows two labeled groups with blue swatches. Nothing reverts or breaks on reload.

---

## What "Working Correctly" Looks Like

- The Job kind dropdown on `/data` never offers "Expand universe" again, under any circumstance.
- Starting a Fetch job shows a symbol total in the high 500s (never the old ~162) — the whole committed stock pool gets refreshed automatically, with no new button to find or click.
- The availability heatmap's legend always shows two clearly separate, clearly labeled rows — one for "price data" (blue swatches) and one for "scored snapshot" (a violet ring) — and hovering a cell that has data-but-no-snapshot reads visibly differently from hovering a cell that has both.
- The top ("full") density color is blue, never amber; the snapshot ring is violet, never green.
- `/stocks` Sector sort and `/evidence` keep working exactly as before — this phase touched only `/data`.

## Common Issues

- **"Backend unavailable" card on any page**: confirm the backend process is running (a developer can check with `curl http://localhost:8255/health`) before treating it as a UI bug.
- **Job-kind dropdown still shows "Expand universe"**: the removal did not fully ship — treat as broken, this is the phase's core requirement.
- **Fetch job's symbol total still shows ~162 instead of ~588**: the backend wiring to the full 548-pool wasn't applied — treat as broken, this is the phase's other core requirement.
- **Legend still shows one merged row, or the "full" bucket still looks amber/orange, or the snapshot ring still looks green**: the color/legend re-encode didn't ship correctly — treat as broken.
- **Clicking "Start" for any job kind shows an error or the page goes blank**: this would be a regression from the Expand-code removal touching shared form logic — note exactly which job kind (Backfill / Fetch / Fetch + backfill) failed.
