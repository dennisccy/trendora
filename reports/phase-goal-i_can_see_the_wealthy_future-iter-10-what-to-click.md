# Phase goal-i_can_see_the_wealthy_future-iter-10 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future-iter-10
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8835` with seed data (at least one stored scanner run, ideally several dates)
- No login required

---

## Verification Steps

<!-- Maximum 10 steps. Prioritizes: 1) the new Backtest scorecard works, 2) honest NA / no fabrication, 3) regression on System Health + global switcher. -->

1. Open `http://localhost:3835/` in your browser
   - **Expect:** Dashboard loads, no error page

2. In the left sidebar, find and click "Backtest" (flask icon, between "Scanner Runs" and "System Health")
   - **Expect:** URL becomes `http://localhost:3835/backtest`; the heading "Backtest" and an "As-of date" dropdown (top-right) are visible

3. Confirm the warning banner near the top
   - **Expect:** A "Survivorship bias" amber card is visible explaining the walk-forward evidence limitation

4. Read the as-of badge and the default scorecard (Latest date)
   - **Expect:** Badge reads "Viewing as-of <date> (latest)"; the "Forward-test scorecard" table shows rows 1d/5d/10d/20d/60d. Longer horizons likely show "—" with "n=0" (honest NA — no fabricated numbers)

5. Click the "As-of date" dropdown and select the OLDEST historical date listed
   - **Expect:** Page re-fetches; the badge changes to "Viewing as-of <D> (historical)" in amber with a history icon

6. Read the "As-of scan summary" section for that older date
   - **Expect:** "Market Regime" card shows a label badge + "NN.NN / 100" score; "Candidate Counts" shows Actionable / Breakout-watch / Pullback-watch numbers; "Top Sectors", "Top Themes", and a "Ranked cohort" table all populate

7. Read the "Forward-test scorecard" table for that older date
   - **Expect:** At least one row shows a numeric "Cohort" return like "+1.23%" paired with "n=N" (N ≥ 1); the vs SPY/QQQ/Sector, Random peers, SPY, QQQ, Sector ETF cells also show numbers with "n=" tokens. No cell shows a percent with "n=0"
   - **Broken looks like:** a numeric return next to "n=0", or "0.00%" placeholders filling every cell

8. Reset the dropdown to "Latest · <date>"
   - **Expect:** Badge returns to "Viewing as-of <date> (latest)"; longer-horizon rows go back to "—" / "n=0" (or the empty state "No elapsed forward window for this date yet" if every horizon is NA)

9. Navigate to `http://localhost:3835/system-health` (regression)
   - **Expect:** Forward-return figures still render as "+1.23%" / "—", green/red coloring intact, "n=N" sample sizes shown, low-sample figures still flagged with "⚠" — identical to before the refactor

10. Navigate to `http://localhost:3835/` and use the global top-bar as-of switcher to pick a historical date (regression)
    - **Expect:** Dashboard values time-travel to that date without error; the global switcher is independent of the Backtest page's own picker

---

## What "Working Correctly" Looks Like

- The Backtest scorecard shows REAL numeric returns (with `n≥1`) for an old date, and honest "—"/`n=0` for recent dates where the window hasn't elapsed — never a fabricated number next to `n=0`.
- The page's own "As-of date" picker drives the whole page; the as-of badge flips between "(historical)" and "(latest)".
- System Health and the global top-bar switcher behave exactly as before this iteration.

## Common Issues

- **"Backend unavailable" card on `/backtest`**: backend on :8835 is down — confirm with `curl http://localhost:8835/api/backtest` (should return JSON).
- **Every scorecard cell is "—" / `n=0`**: you're on the Latest date with no post-snapshot bars; pick an older date from the "As-of date" dropdown.
- **"Scan summary unavailable" card but scorecard renders**: a scan-summary endpoint failed for that date — this is the intended graceful degradation, not a scorecard failure.
- **Blank page / no dates in picker**: confirm the backend has stored scanner runs (`curl http://localhost:8835/api/runs`).
