# Phase goal-ops-hardening-iter-14 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-14
**Time required:** ~10 minutes (most of it is waiting for one real backfill job to finish — this
iteration's whole fix is about staying responsive *during* that wait, so the wait itself is the test)
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`, backend at `http://localhost:8255`. No login required.
- **Do not cold-restart the backend to get started.** Per this iteration's dev handoff, the backend was
  deliberately left running after its own measurement pass specifically so this check wouldn't need a
  restart. If the frontend needs (re)starting, run `bash scripts/start-frontend.sh` only — do **not**
  run the combined `bash scripts/dev.sh`, which restarts the backend too and throws away that
  already-running, already-warmed process.
- This phase changes **zero** on-screen pixels. Nothing will look different from before — you are
  confirming a behavior (the app stays responsive while it computes), not a new feature or a new look.

---

## Verification Steps

1. Open `http://localhost:3255/data` in your browser
   - **Expect:** Page loads with a "Start a fetch / backfill job" card. In the top bar, the readiness
     badge reads "Ready" with a green dot.

2. Scroll to the card titled "Rebuild snapshots for current universe." Read the date shown in
   parentheses after "...in the latest snapshot"
   - **Expect:** A date like `(2026-07-21)`. Add one calendar day to get your test date — call it
     DATE_X (e.g. `2026-07-22`). If that lands on a Saturday or Sunday, use the following Monday
     instead.

3. Scroll back up to "Start a fetch / backfill job." Type DATE_X into both the "Start date" and "End
   date" fields, choose **"Backfill snapshots"** from the "Job kind" dropdown, then click **"Start"**
   - **Expect:** The "Job progress" panel's status badge switches to "running" with a small spinning
     icon.

4. For the next several minutes, glance at the top-bar readiness badge every 30 seconds or so (it's on
   every page, so you don't need to stay on `/data`)
   - **Expect:** It stays "Ready" (green dot) the entire time.
   - **Broken looks like:** it gets stuck on "Checking backend…" for more than a few seconds, or turns
     into the red "Backend unavailable" pill. This is exactly the bug this phase exists to fix — if you
     see it, report it plainly, do not assume it will resolve itself.

5. While that job is still running, open a **second browser tab** and navigate to
   `http://localhost:3255/backtest`
   - **Expect:** Within a couple of minutes the page shows its full scorecard tables and
     return-attribution lists — never a red "Backend unavailable" box, and never stuck indefinitely on
     gray pulsing placeholder cards.

6. Back on the `/data` tab, wait for the job's status badge to change from "running" to a terminal
   state
   - **Expect:** It turns green and reads "ok", roughly 4-6 minutes after you clicked Start. (If it
     instead reads "no new snapshots," DATE_X turned out to already have a snapshot or fell on a
     non-trading day — pick the next calendar day as a new DATE_X and repeat from step 3.)

7. Just below the job's snapshot counts, read the line that starts "Refreshed: ..."
   - **Expect:** The comma-separated list includes the phrase **"forward aggregates."**

8. Open a **brand-new tab** (so it has no job started in its own session) and go to
   `http://localhost:3255/data` again. Scroll to the "Run history" table at the very bottom and find the
   newest row (matching DATE_X)
   - **Expect:** That row's Status column reads "ok", and its Snapshots-column breakdown also includes
     the text "Refreshed: ..., forward aggregates" — the same information, shown again from the
     history table.

---

## What "Working Correctly" Looks Like

- The top-bar readiness badge stays "Ready" the whole time a backfill is computing — it never freezes
  on "Checking backend…" and never flips to "Backend unavailable."
- `/backtest` keeps loading its evidence panel normally even while that backfill is still running in
  the background.
- The word "forward aggregates" shows up in the "Refreshed: ..." line in all three places it can
  appear: the live Job progress panel, the persisted summary card (on a fresh reload), and the Run
  history table.

## Common Issues

- **Badge stuck on "Checking backend…" or turns red "Backend unavailable" while the job runs**: this is
  the exact defect this iteration was built to close (it caused two prior operator hard-restarts this
  session). Report it exactly as observed — do not round it into "probably fine."
- **`/backtest` shows the red "Backend unavailable" card**: same as above — report plainly.
- **Job status reads "no new snapshots" instead of "ok"**: your chosen DATE_X had no real work to do
  (already snapshotted, or a weekend/holiday). Pick the next calendar day and try again from step 3.
- **"forward aggregates" never appears even though the job says "ok" with new snapshots**: check with
  whoever is running the session that the backend currently up is actually this iteration's build (it
  may need a restart — use `scripts/start-backend.sh` under the project's normal host-guard confinement,
  never an ad hoc restart).
- **Frontend won't load at all**: confirm it's running — start it with `bash scripts/start-frontend.sh`
  if needed (not the combined `scripts/dev.sh`, which would also restart the backend and lose the
  process left running for this exact check).
