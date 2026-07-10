# Phase goal-mcp-loop-iter-26 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-26
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`, backend reachable — both started in **prod mode**
  (`start-backend.sh` / `start-frontend.sh`, never `dev.sh --reload`)
- No login required
- The standing 30-year price database is already loaded (this is the normal dev-environment state)
- Nothing else to set up — this iteration changed no UI. You are verifying that everything still looks
  the same AND that data jobs now finish noticeably faster without lying about progress.

---

## Verification Steps

1. Open `http://localhost:3255/data` in your browser
   - **Expect:** "Data Manager" heading loads; the "Dataset coverage" and "Storage footprint" panels
     show real numbers (not blank, not a red "Backend unavailable" error card)

2. In the "Dataset coverage" panel, check the "Backfill gaps" number. In the "Start a fetch / backfill
   job" panel (Job kind already defaulted to "Backfill snapshots"), click the "Start" button.
   - **If "Backfill gaps" was 0**, instead scroll down and click "Rebuild snapshots for current
     universe", then click "Rebuild snapshots" in the confirmation dialog that appears.
   - **Expect:** The "Job progress" panel (right side) shows a teal "running" badge with a spinning icon

3. Watch the "Snapshots backfilled" counter (reads like "`3/40 dates`") in the "Job progress" panel for
   about 10–15 seconds without touching anything
   - **Expect:** The count climbs step by step (e.g. `3/40` → `11/40` → `24/40`) and the progress bar
     above it visibly fills in — it does NOT jump straight from a low number to the final total in one
     step. This is the core thing this iteration must get right: **faster, but never dishonestly "done
     early."**
   - **Broken looks like:** the counter sitting at a low number for a while, then suddenly showing
     `40/40` in a single refresh with no intermediate values seen, OR the badge turning green ("ok")
     while the counter still reads less than the total.

4. Wait for the job to finish (badge turns green and reads "ok"), then look at the "Stage timings" box
   that appears in the same panel
   - **Expect:** A line reading something like "`3.5× faster than the per-date sum`" under the
     "Backfill" section — this is the backend's own proof that item F's speedup landed

5. Navigate to `http://localhost:3255/stocks`
   - **Expect:** The "Stocks" leaderboard loads with rows; every row shows three score numbers
     (Leadership, Entry Quality, Risk) each with a letter bucket (A–E) and a small "Not yet proven" gray
     badge next to it — no row shows a blank score

6. Click on any ticker in the leaderboard, and note its Leadership/Entry Quality/Risk numbers before you
   click
   - **Expect:** You land on `http://localhost:3255/stocks/{TICKER}`, and the three scores shown there
     are the EXACT same numbers and bucket letters you just saw on the leaderboard row — this is the
     "same score everywhere" guarantee the backend change is not allowed to break

7. Navigate to `http://localhost:3255/` (Dashboard)
   - **Expect:** The "Market Regime" card renders a colored label (e.g. "Risk-on") with a two-decimal
     score underneath, and the "Market Phase & Severity" card beside it also renders normally — no error
     card, no blank card

8. Navigate to `http://localhost:3255/evidence`
   - **Expect:** The "Evidence" ledger page loads; no entry anywhere reads "Proven" — every score status
     across the product should still be "Not yet proven" this iteration (no new certified claims were
     added)

---

## What "Working Correctly" Looks Like

- Data jobs on `/data` finish noticeably faster than they used to, but the `done/total` progress
  counter still ticks up visibly, one step at a time, while a job is running
- Every score you check on `/stocks` and its detail page shows the exact same numbers as before — the
  backend now computes them from a smaller trailing window of history, but the answer never changes
- The Dashboard, `/stocks`, and `/evidence` pages look pixel-for-pixel the same as before this
  iteration — there is nothing new to discover in the UI

## Common Issues

- **Blank page / red error card on `/data`**: backend is not running or not reachable — confirm
  `start-backend.sh` was used (not `dev.sh`) and check `curl http://localhost:8000/api/health`
- **Progress counter jumps straight to "done"**: this is the exact regression this iteration must
  avoid — flag it immediately, it means the honest-progress guarantee broke
- **A score on `/stocks` looks different from what you remember**: compare against the detail page for
  the same ticker (step 6) — if they also disagree with each other, or you have a pre-iteration
  screenshot showing a different number, this is a byte-identity regression and should be flagged
- **Backend crashes / restarts right after a cold `/data` load**: this is the iter-24 OOM pattern —
  stop the backend, cold-start it again, and confirm `/data` is the very first request made
