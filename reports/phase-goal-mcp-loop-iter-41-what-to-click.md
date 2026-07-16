# Phase goal-mcp-loop-iter-41 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-41
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running and reachable (the page will show a red "Backend unavailable" card if not)
- No login required — this app has no authentication
- The evidence ledger already has 7 certified claims today (0 currently show "PASS" — all 7 read
  "FAIL"). That is expected and unrelated to this phase; do not treat "FAIL" badges as a bug.

---

## Verification Steps

1. Open `http://localhost:3255/evidence` in your browser
   - **Expect:** Page heading reads "Evidence"; 7 claim cards are visible; no red error card

2. On the FIRST claim card (its "Hypothesis" row shows badges "factor=leadership_score",
   "decile=10", "horizon=20"), scroll down past the 5 existing fields (Hypothesis, Out-of-sample
   verdict, Control comparison, Registration date, Forward-walk score-to-date)
   - **Expect:** A new section appears headed "Historical drawdown & dry-spell expectations
     (20-day hold)", with a 5-row table below it (rows: Expansion, Pullback, Correction, Bear,
     Recovery)

3. In that table, find the "Expansion" row (the first row) and read its "Max-DD depth" cell
   - **Expect:** The cell reads exactly "-7.70% (p90 -3.72%) n=1264" — a real number, not blank
     and not "undefined"

4. Scroll down to the "Correction" row (third row) and read its "Longest losing streak" cell
   - **Expect:** The cell reads exactly "insufficient (n=5)" in muted gray text — an honest
     "not enough data" label, not a made-up streak number

5. Scroll to the very bottom of the panel and read the two sentences below the table
   - **Expect:** First sentence starts "Longest losing streak is counted at the walk-forward
     cadence…"; second sentence starts "Walk-forward evidence now spans up to ~30 years of
     history…" and ends "…Read the edge as an upper bound, not a guarantee."

6. Scroll back to the top of that same card and check the badge next to its title
   - **Expect:** Badge still reads "FAIL" — unchanged by the new panel; the panel appears only
     BELOW the existing fields, never mixed into them

7. Refresh the page (press F5)
   - **Expect:** All 7 cards reload with the same panel content, and the page returns in well
     under a second (no long spinner) — the numbers are cached, not recomputed on every visit

8. Navigate to `http://localhost:3255/stocks/AAPL`
   - **Expect:** Page heading reads "AAPL"; each of the 3 score cards (Leadership, Entry Quality,
     Risk) still shows a small "Not yet proven" badge directly beneath its score, exactly as
     before this change

---

## What "Working Correctly" Looks Like

- Every claim card on `/evidence` has the new "Historical drawdown & dry-spell expectations"
  section below its existing fields, showing a 5-row table (one row per market phase) with real
  numbers or an honest "insufficient (n=…)" label — never a blank cell
- The two explanatory sentences (method note + survivorship caveat) are visible at the bottom of
  every panel without clicking anything, and read identically on every card
- Nothing elsewhere on the site changed: verdict badges, other pages' scores, and badges all look
  exactly like they did before this phase

## Common Issues

- **Red "Backend unavailable" card on `/evidence`**: the backend isn't running or isn't reachable
  — start/restart it and reload
- **Panel section is completely missing on some or all cards**: likely means the database hasn't
  been rebuilt since this feature shipped (the two new data columns are still NULL) — check
  `reports/perf-budgets.md` for the last recorded rebuild
- **Every phase on every card reads "insufficient (n=0)"**: same root cause as above — the
  historical backfill hasn't populated the new columns yet
- **First page load after a fresh database rebuild takes ~9-10 seconds**: this is expected
  one-time behavior (cache-cold); every visit after that, by anyone, should be fast again. If it
  stays slow on a normal repeat visit with no rebuild in between, that is a real regression.
