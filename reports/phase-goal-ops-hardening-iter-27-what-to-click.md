# Phase goal-ops-hardening-iter-27 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-27
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running (the frontend will show a red "Backend unavailable" card if it isn't)
- No login required
- No seed data setup needed — this session's database already holds ~30 years of history

---

## What this iteration changed (in plain terms)

Nothing new to click. Two existing pages got more honest and more reliable:
- The Data Manager (`/data`) page's coverage panel can no longer show a misleading "empty database" look
  when the database actually has years of real data — it now says so plainly when its reading is a real
  but momentarily out-of-date one.
- The Backtest (`/backtest`) page can no longer occasionally crash with a server error when two requests
  for the same historical date land close together.

## Verification Steps

1. Open `http://localhost:3255/data` in your browser
   - **Expect:** The "Data Manager" page loads, no red error card, and a "Dataset coverage" panel is visible
     at the top of the page.

2. Look directly below the words "Dataset coverage" (above the grid of small figure boxes).
   - **Expect one of two things**, depending on this database's current state — both are correct, read
     whichever one is actually showing:
     - **If you see a line reading** "Coverage as of a prior scan (version …) — refreshes on the next data
       job" — that is the new honest "stale" notice. Check that the "Price history" and "Universe (as of
       date)" boxes right below it show REAL numbers (a real date range and a non-zero universe count), not
       dashes or zero.
     - **If you do NOT see that line** — the coverage is fully current. Just confirm "Price history" and
       "Universe (as of date)" still show real, non-zero numbers (not "— → —" / "0"). Only a genuinely
       empty, never-used database should ever show all dashes/zeros.

3. Click "Backtest" in the left sidebar.
   - **Expect:** The page loads at `http://localhost:3255/backtest` with no red error card, a heading
     "Backtest", and a "Latest" badge near the top.

4. Click the date button near the top of the page (it shows "Latest" with a small calendar icon and a
   down-arrow), then click any date shown in the calendar that appears.
   - **Expect:** The badge near the top changes to read "Viewing as-of `<the date you picked>` (historical)",
     and scrolling down shows a filled-in "Forward-test scorecard" table with numbers in it — not a blank
     page, not a red error card, not a frozen/half-loaded page.

5. Press F5 (or Cmd+R) to refresh the page.
   - **Expect:** The exact same historical date and the same scorecard numbers reappear — nothing crashes
     or resets to a blank state.

6. Click "Dashboard" in the left sidebar (top of the list).
   - **Expect:** The Dashboard page loads normally with a Market Regime score visible — confirms the rest
     of the product still works after this iteration's changes.

---

## What "Working Correctly" Looks Like

- The Data Manager coverage panel NEVER shows "— → —" / "Universe 0" unless the database is genuinely
  empty — if a stale-scan notice is showing, the numbers next to it are real, not zeroed out.
- The Backtest page never shows a red error card or a blank page for any date you pick from the calendar.

## Common Issues

- **Red "Backend unavailable" card on either page**: the backend process isn't running — start it and
  reload.
- **"— → —" / "Universe 0" on `/data` with no stale-scan notice line at all**: only expected on a
  brand-new, never-used database. On this session's already-seeded database, seeing this with no notice
  would be worth flagging.
- **A blank or frozen Backtest page after picking a historical date**: this is exactly the failure this
  iteration fixed — if you can reproduce it, note the exact date you picked and flag it; it should not
  happen anymore for any date reachable through the calendar.
- The specific race condition this iteration fixed (two requests hitting the very same never-before-viewed
  date at the same instant) needs two simultaneous backend calls to reproduce reliably — that reproduction
  is a QA/developer-level check (see `reports/phase-goal-ops-hardening-iter-27-ui-test-plan.md`, UT-06), not
  something this 5-minute click-through can trigger on its own.
