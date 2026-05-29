# Phase goal-i_can_see_the_wealthy_future-iter-2 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future-iter-2
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8000` (the pages fetch `/api/sectors` and `/api/dashboard`)
- Frozen seed loaded (data-as-of **2026-05-28**). No login required.

---

## Verification Steps

1. Open `http://localhost:3835/sectors` in your browser
   - **Expect:** A dense table loads under the "Sectors" heading with columns `#`, `Ticker`, `Kind`, `Sector Score`, `RS vs SPY`, `Dist. 52w high`, `Trend`. At least 10 rows. NOT an empty placeholder and NOT a red error card.

2. Read the `Sector Score` raw numbers (the small number next to each A–E badge) from top to bottom
   - **Expect:** They only go down or stay equal — the list is ranked highest-score first. Top rows show green A/B badges, lower rows show amber/red C/D/E badges.

3. Look at row #1's "RS vs SPY", "Dist. 52w high", and "Trend" cells
   - **Expect:** A signed percent (e.g. `+3.21%`, green if positive), a percent (e.g. `-4.50%`), and a non-empty trend word (e.g. "Leading"). None blank.

4. Click on row #1
   - **Expect:** The row expands; the right-end chevron flips from `>` to `v`; a breakdown grid appears with "Component / Detail / Contribution" headers listing named drivers (RS vs SPY · 1m/3m/6m, MA stack, Dist. from 52w high, Volume trend). No bare unexplained number.

5. Scan the whole `Ticker` column for `SPY`, then read the header badges
   - **Expect:** `SPY` is NOT a ranked row. It appears only in the "RS benchmark: SPY (excluded)" badge near the top. An "as of 2026-05-28" badge is also present.

6. Click "Dashboard" in the left sidebar (or open `http://localhost:3835/`)
   - **Expect:** The "Market Regime" card shows a coloured label badge that is one of: Strong risk-on / Risk-on / Narrow leadership / Choppy / Risk-off / Defensive (expected **Risk-on**), and a big number `/ 100` (expected ≈ **74.32**). Below it, a named component breakdown.

7. Read the three small breadth cards to the right of the regime panel
   - **Expect:** "Breadth · above 50-DMA", "Breadth · above 200-DMA", and "Net new highs" — each with a `%` value and an amber caption containing "universe-relative". Top-right shows a "Data as-of 2026-05-28" clock badge.

8. Read the "Top Sectors" card (lower-left), then compare its top row to row #1 from step 1
   - **Expect:** 5 rows, each with rank + ticker + trend + A–E score badge. The top ticker, badge letter, and score **match** `/sectors` row #1 exactly (same data source).

9. Read the "Candidate Counts" and "Top Themes" cards
   - **Expect:** Both show an amber "pending" badge and em-dashes (—) for every value — NOT `0`. This is the intended honest placeholder for iter-3 work.

10. (Optional, ~30s) Stop the backend, then reload `http://localhost:3835/sectors` and `http://localhost:3835/`
    - **Expect:** Both pages show a red "Backend unavailable" card with no fabricated rows, scores, or regime values. Restart the backend afterward.

---

## What "Working Correctly" Looks Like

- `/sectors` is a populated, top-to-bottom descending leaderboard of A–E badges — not an empty state.
- The Dashboard shows a live regime label + score, three "universe-relative" breadth cards, a Data-as-of badge, and a Top Sectors list that matches `/sectors`.
- Anything not yet computed (Candidate Counts, Top Themes) is an explicit "pending" placeholder with em-dashes, never a fake `0`.

## Common Issues

- **Red "Backend unavailable" card on every page**: The backend isn't running. Check `curl http://localhost:8000/api/dashboard` returns JSON.
- **Page stuck on grey pulsing skeleton bars**: The API call is hanging — check the browser console (F12) for a failed/blocked request to `/api/sectors` or `/api/dashboard`.
- **Top Sectors top row doesn't match `/sectors` row #1**: This is a real bug (data divergence) — the dashboard must source the same ranking; report it.
- **Any value shown as `0` instead of `—` in Candidate Counts / Top Themes**: This is a fabrication regression — those must stay em-dashes this iteration.
