# Phase goal-mcp-loop-iter-21 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-21
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255` and backend running at `http://localhost:8255`, both
  started in **prod mode** (`scripts/start-backend.sh` then `scripts/start-frontend.sh` — never
  `dev.sh`) against a **fresh** frontend build (whoever started it should have run
  `rm -rf apps/frontend/.next` first — a stale build has silently served the wrong UI before)
- No login required
- No special setup needed — the shipped dataset already has a mix of fetched-but-not-yet-backfilled
  days and fully backfilled days, which step 6 below relies on

---

## Verification Steps

1. Open `http://localhost:3255/data` in your browser
   - **Expect:** The Data Manager page loads with a panel titled "Start a fetch / backfill job"; no "Backend unavailable" message appears, and the browser does not show a "can't reach this page" connection error.

2. Click the "Job kind" dropdown in that panel
   - **Expect:** Exactly three options: "Backfill snapshots", "Fetch EOD prices", "Fetch + backfill." There is **no** "Expand universe" option anymore.

3. Select "Fetch EOD prices," confirm the "Import source" dropdown that appears shows an option ending in "· available" (pick one if not), then click the "Start" button
   - **Expect:** A "Job progress" panel appears below showing a "Symbols fetched" line like "`0/588 (0 ok, 0 failed)`" — the total should be in the high 500s (at least 548). Fetch used to only cover about 162 symbols; it now covers the whole committed stock pool automatically.

4. Scroll down to the "Per-date availability" card
   - **Expect:** The legend above the calendar grid shows **two separate labeled rows**: "PRICE DATA — CELL FILL" (with 6 small color swatches) and "SCORED SNAPSHOT — INDICATOR" (with one ringed swatch) — never squeezed into one row.

5. Look at the rightmost swatch in the "PRICE DATA — CELL FILL" row (labeled "full")
   - **Expect:** It is a bright **blue**, not amber/orange. All 6 swatches should read as shades of blue, each one clearly lighter than the last.

6. Hover your mouse over a calendar cell that is brightly filled but has **no** ring around it, then hover a cell that **does** have a ring
   - **Expect:** The first cell's tooltip reads something like "...no snapshot yet — Backfill gap"; the second reads "...scored snapshot exists (Backfill)." The two tooltips should read clearly differently. (If every visible cell already has a ring, the Fetch job from step 3 will create gap days once it finishes — wait a few seconds and re-check its most recent days.)

7. Back in the job form, select "Backfill snapshots" as the Job kind and click "Start"
   - **Expect:** A "Snapshots backfilled" line appears in the job progress panel; no error message appears anywhere on the page.

8. Navigate to `http://localhost:3255/stocks` and click the word "Sector" in the table's column header, twice
   - **Expect:** The table re-sorts both times (an arrow icon appears/flips next to "Sector"). The page must **never** go blank or lose its left sidebar.

9. Navigate to `http://localhost:3255/evidence`
   - **Expect:** The page loads with the heading "Evidence" visible — either a "No certified claims yet" message or a list of claims. No blank page, no "Backend unavailable" card.

10. Go back to `http://localhost:3255/data` and refresh the page (F5)
    - **Expect:** Everything from steps 1, 2, and 4–5 still looks the same after the refresh — the job-kind picker still has exactly 3 options and the legend still shows two labeled groups with blue swatches. Nothing reverts or breaks on reload.

---

## What "Working Correctly" Looks Like

- Both `:3255` and `:8255` answer immediately when you open their URLs — no "can't reach this page" browser errors. (This exact gap caused the previous verification attempt to be skipped entirely — if you see it now, stop and get both services confirmed up before judging anything else.)
- The Job kind dropdown on `/data` never offers "Expand universe" again, under any circumstance.
- Starting a Fetch job shows a symbol total in the high 500s (never the old ~162) — the whole committed stock pool gets refreshed automatically, with no new button to find or click.
- The availability heatmap's legend always shows two clearly separate, clearly labeled rows — one for "price data" (blue swatches) and one for "scored snapshot" (a violet ring) — and hovering a cell that has data-but-no-snapshot reads visibly differently from hovering a cell that has both.
- The top ("full") density color is blue, never amber; the snapshot ring is violet, never green.
- `/stocks` Sector sort and `/evidence` keep working exactly as before — nothing in this round of checks touches source code, so nothing here should have changed since it was last confirmed working.

## Common Issues

- **"This site can't be reached" on either URL**: the services aren't both started, or aren't bound to these ports yet. Ask a developer to run `scripts/start-backend.sh` then `scripts/start-frontend.sh` (never `dev.sh`) and re-confirm both load before retrying — this is the exact condition that caused the last verification attempt to be skipped entirely rather than pass or fail.
- **"Backend unavailable" card on any page**: confirm the backend process is actually running (a developer can check with `curl http://localhost:8255/health`) before treating it as a UI bug.
- **Job-kind dropdown still shows "Expand universe"**: treat as broken — this was already removed and verified once before, so seeing it again means something regressed.
- **Fetch job's symbol total still shows ~162 instead of the high 500s**: treat as broken — same reasoning, this was already fixed.
- **Legend still shows one merged row, the "full" bucket still looks amber/orange, or the snapshot ring still looks green**: treat as broken — the color/legend re-encode was already verified once; seeing the old look again is a regression, not a new bug to triage from scratch.
- **Clicking "Start" for any job kind shows an error or the page goes blank**: note exactly which job kind (Backfill / Fetch / Fetch + backfill) failed — this would point to a regression in shared form logic.
