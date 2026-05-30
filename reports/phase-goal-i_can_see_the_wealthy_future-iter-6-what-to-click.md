# Phase goal-i_can_see_the_wealthy_future-iter-6 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future-iter-6 — Walk-forward forward-testing engine + System Health evidence (J-09, J-10)
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3836`
- Backend running. If you just restarted the backend on a fresh DB, the first boot runs a one-time walk-forward backfill (~223 s). Wait until it finishes before testing, or the page will show "Backend unavailable".
- No login required.

---

## Verification Steps

<!-- Maximum 10 steps. Each step has an exact action and exact expected outcome. -->

1. Open `http://localhost:3836/` in your browser
   - **Expect:** The Dashboard loads, no error page. The left sidebar shows a "System Health" link.

2. Click "System Health" in the left sidebar
   - **Expect:** You land on `http://localhost:3836/system-health`. Heading "System Health" appears with the subtitle starting "Forward-tested evidence — did higher-ranked buckets…". This is a full dashboard, NOT an empty placeholder.

3. Look directly under the heading row
   - **Expect:** An amber/warn-toned banner labelled "Survivorship bias" with an explanatory sentence is visible.

4. Find the "Forward return by score bucket" panel
   - **Expect:** Rows for buckets A, B, C, D, E, each with a colour-graded badge, a percent value like `+1.23%`, and a sample-size token `n=NN` to its right.

5. Find the "Excess vs benchmarks" panel
   - **Expect:** An "Excess vs SPY" row and an "Excess vs QQQ" row, each showing a Stocks value, a Benchmark value, an Excess value, and `n=NN`.

6. Find the "Forward return by market regime" panel
   - **Expect:** Both a "Risk-on" row and a "Risk-off" row, each with a numeric mean return and `n=NN`.

7. Find the "Control-group comparison — selection vs sector beta" panel (J-10)
   - **Expect:** Rows for the top-ranked cohort (highlighted/bolder), a random same-sector cohort, SPY, QQQ, and the sector ETF — each with a percent return and `n=NN`. The panel hint reads "At 20 days: …".

8. In the "Horizon" button group at the top-right, click the "5d" button
   - **Expect:** "5d" becomes the highlighted/active button (was "20d"), the control-group hint changes to "At 5 days: …", and at least one figure on the page changes value. No red error appears.

9. Press F5 to reload the page
   - **Expect:** The dashboard repopulates with figures (briefly a pulsing skeleton grid may flash first). Data persists — the page is not empty after reload.

10. Click "Scanner Runs" in the left sidebar, then read the runs list
   - **Expect:** The Scanner Runs page loads with MORE dated run rows than before (the walk-forward backfill added 8 as-of snapshots → ~11 total). Old runs are still listed — this is intended history, not a regression.

---

## What "Working Correctly" Looks Like

- Every number on `/system-health` is a percentage (`+1.23%` / `-0.84%` / `—`) paired with a sample size `n=NN`. Low-sample figures carry a `⚠` marker rather than being hidden.
- Changing the horizon (20d → 5d → 60d) re-renders the figures across all panels.
- The control-group panel proves whether the top-ranked cohort beat random same-sector peers and SPY/QQQ/sector-ETF.

## Common Issues

- **Red "Backend unavailable" alert:** The backend is down or still running the first-boot backfill. Wait for the backfill to complete (~223 s on a fresh DB), confirm the backend is up, then reload. Note: this red alert (no fabricated zeros) is the *correct* behavior when the backend is truly unavailable.
- **"No forward-tested evidence yet" empty state:** The selected horizon has no post-snapshot data. Pick a shorter horizon (e.g. 5d) or wait for the backfill. This is honest behavior, not a crash.
- **Blank page / white screen:** Confirm the frontend is running on port 3836 and the backend is reachable.
