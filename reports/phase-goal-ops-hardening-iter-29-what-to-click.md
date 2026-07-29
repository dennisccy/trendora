# Phase goal-ops-hardening-iter-29 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-29
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running (no login required — this product has no auth)
- No special seed data needed — the existing evidence ledger and stored price history are enough

---

## Verification Steps

1. Open `http://localhost:3255/evidence` in your browser
   - **Expect:** The page loads with the heading "Evidence" and a list of claim cards appears (7 cards
     today). No red "Backend unavailable" message.

2. In the first card (its title reads "leadership_score"), scroll down to the section headed "Historical
   drawdown & dry-spell expectations"
   - **Expect:** A table with columns "Phase", "Max-DD depth", "Underwater", "Time to recover", "Longest
     losing streak", filled in with real numbers/percentages — not blank, not an error message.

3. Scroll through the rest of the page and check that all 7 claim cards fully loaded
   - **Expect:** Every card shows its badge, title, and field grid completely — no card is missing, no red
     error box, no blank gap where a card should be.

4. Refresh the page (press F5 or Cmd+R)
   - **Expect:** The same 7 cards reappear with the same information — a clean reload, no crash, no error
     page.

5. Click "Research" in the left sidebar, then click the "Factor Lab" card
   - **Expect:** The page navigates to `http://localhost:3255/research/factor-lab` and shows the heading
     "Research — Factor Lab".

6. Wait for the factors table to finish loading
   - **Expect:** A table appears listing factor names with a "Rank-IC" column filled in with real numbers
     (not all dashes). This can take up to about a minute the first time — that delay by itself is normal,
     not a bug.

7. Click on any row in that table
   - **Expect:** The row expands in place to show a grid of deciles (D1 through D10) with real return and
     drawdown figures underneath it.

---

## What "Working Correctly" Looks Like

- The Evidence page shows all 7 claim cards fully, each with a complete field grid, and most/all of them
  show a filled-in drawdown-expectations table (like step 2 above).
- The Factor Lab table fills in with real numbers (not blank or all "NA") once its one-time load finishes.
- **Informational, not something to force:** on rare occasions, one single claim card may instead show a
  small gray note under "Historical drawdown & dry-spell expectations" reading "Unavailable — monitored and
  refreshed as new data arrives." This is expected, honest behavior added this iteration (not a bug) as
  long as it stays limited to that one card and every other card still looks normal. You are not expected to
  see this during a normal 5-minute check — today, all 7 claims resolve successfully.

## If Something Looks Wrong

- **Blank page / error screen on `/evidence` or `/research/factor-lab`**: confirm the backend is running —
  `curl http://localhost:8000/api/health` should return a successful response.
- **Factor Lab table stuck loading for a long time**: expected on the first load after a data change
  (documented up to ~60–90 seconds); wait it out once and it should be fast on the next visit. Still stuck
  after 2 minutes is a real problem.
- **A claim card's drawdown section looks half-broken** (not a clean table, not cleanly blank, and not the
  calm "Unavailable" note described above — e.g. a red error box, raw text like "[object Object]", or a
  broken layout): that is a real bug — note which claim card and report it.
