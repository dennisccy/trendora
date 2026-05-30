# Phase goal-i_can_see_the_wealthy_future-iter-5 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future-iter-5
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3836`
- Backend running at `http://localhost:8000` (the run history loads from `/api/runs`)
- Bootstrapped runs exist — created automatically on backend startup from the frozen seed
  (dates **2022-10-07**, **2025-04-04**, plus the latest **2026-05-28**). No login needed.

---

## Verification Steps

1. Open `http://localhost:3836/scanner-runs` in your browser
   - **Expect:** Heading "Scanner Runs" and a table with columns "As of / Regime / Actionable / Breakout-watch / Pullback-watch / Stocks", with at least 3 dated rows, newest first (2026-05-28 at the top).

2. Look at the "Regime" column for the top row vs the 2025-04-04 / 2022-10-07 rows
   - **Expect:** 2026-05-28 shows a **green "Risk-on"** badge (score ≈ 74.32); 2025-04-04 and 2022-10-07 show a **red "Risk-off"** badge.

3. Read the "Actionable" column across those rows
   - **Expect:** Both Risk-off rows read **0**; the 2026-05-28 Risk-on row reads a **non-zero** count. (J-07 gate, visible at a glance.)

4. Click the **2025-04-04** date link (accent-coloured)
   - **Expect:** URL becomes `/scanner-runs/<number>`; a lock-icon header reads **"Immutable snapshot — as of 2025-04-04"**; the "Market Regime" card shows a red "Risk-off" badge and score 6.30.

5. Read the "Candidate Counts" card, then scan the whole "Setup" column of the stock table
   - **Expect:** The **Actionable** tile reads **0** and **Risk-off-watchlist** shows a large count; **no** row's Setup says "Actionable" — all watchlist-only. (J-07 confirmed.)

6. Click the "All runs" button (top-right, left-arrow), then click the **2022-10-07** date link
   - **Expect:** Returns to the list, then opens 2022-10-07; note the top 3 tickers (e.g. HUBB / REGN / AXON).

7. Click "All runs" again, then click the **2026-05-28** date link
   - **Expect:** The top 3 tickers differ from 2022-10-07 (e.g. MU / ARM / MRVL) — different dates show different stored rankings. (J-08 confirmed: frozen, not recomputed.)

8. Navigate to `http://localhost:3836/scanner-runs/999999`
   - **Expect:** A "Run not found" card saying no run is fabricated to fill the gap — NOT a crash, blank page, or fake run.

9. Navigate to `http://localhost:3836/stocks` (regression check)
   - **Expect:** The live leaderboard still renders real rows with score badges — unchanged by the new snapshot store.

---

## What "Working Correctly" Looks Like

- The run list is a dense dark table; Risk-off rows are clearly red and read 0 Actionable, the latest Risk-on row is green with a non-zero Actionable count.
- Each detail page is unmistakably a frozen historical snapshot ("Immutable snapshot — as of <date>"), and two different dates show different stored tickers/scores.

## Common Issues

- **Red "Backend unavailable" card on `/scanner-runs`**: backend not running — start it on port 8000 (`curl http://localhost:8000/api/runs` should return JSON), then reload.
- **"No scanner runs yet" empty card**: backend up but bootstrap hasn't finished persisting — wait a few seconds (first boot is ~1–2s per date) and reload.
- **A detail page shows today's numbers for an old date**: that would be an immutability bug — the detail must always show the stored as-of values, never recomputed live scores.
</content>
