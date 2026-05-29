# Phase goal-i_can_see_the_wealthy_future-iter-3 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future-iter-3
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3836` (if that port is dead, the managed `next dev` may be on `3835` — open the base URL to confirm, then use the live port for every step)
- Backend API running with seed data loaded (the dashboard/leaderboards 503 if `latest_data_date` is null)
- No login required

---

## Verification Steps

<!-- 8 steps. Covers: 1) the two new leaderboards work, 2) the J-06 single-source check, 3) the dashboard is complete, 4) the J-04 regression still works. -->

1. Open `http://localhost:3836/stocks` in your browser
   - **Expect:** A dense dark ranked table with columns `#  Ticker  Sector  Leadership  Entry Quality  Risk  Setup  Reason`, many rows (≈122), an "as of {date}" badge, and a `visible / total` count (e.g. `122 / 122`). Each row has three letter+number score badges, a setup badge, and a non-empty reason.
   - **Broken looks like:** a blank page, an empty stub, or a red "Backend unavailable" card.

2. Click the "Sector" dropdown and select "Technology"
   - **Expect:** The table shrinks to only Technology rows; the `visible / total` left number drops below the total (e.g. `12 / 122`). Reset the Sector dropdown to its default afterward.

3. Click the "Setup" dropdown and select "Actionable"
   - **Expect:** Either only Actionable rows show, OR (expected on the current extended-market seed) the explicit message "No stocks match these filters" — **never** a fabricated row. Reset the Setup dropdown to its default afterward.

4. Note NVDA's three numbers + letters on `/stocks`, then click the "NVDA" ticker link
   - **Expect:** Navigate to `http://localhost:3836/stocks/NVDA`; three score cards (Leadership / Entry Quality / Risk) each showing a raw `NN.NN / 100`, an A–E badge, a caption, and a component breakdown, plus a "Back to leaderboard" link.

5. Compare NVDA's three numbers and three A–E letters on the detail page against what you noted in step 4 *(this is the J-06 single-source check)*
   - **Expect:** All three numbers AND all three buckets are **identical** between the leaderboard row and the detail page.
   - **Broken looks like:** any score or letter differs between the two views — that is a hard FAIL (the score is being recomputed instead of read from one source).

6. Open `http://localhost:3836/themes`
   - **Expect:** A ranked table (`#  Theme  Theme Score  1m  3m  Breadth  Trend`) with ≥3 themes whose Theme Scores are non-increasing top-to-bottom; the top row shows numeric 1m and 3m returns, a breadth %, and a trend label. Click the top row to expand it — member-ticker chips and a component breakdown appear; click again to collapse.

7. Open `http://localhost:3836/`
   - **Expect:** A complete dashboard — a Market Regime card (label + score), a "Candidate Counts" card with three numeric rows (Actionable / Breakout-watch / Pullback-watch; Actionable may be `0`), a Top Sectors list (≥3), a "Top Themes" list (≥3, each with a score badge), a breadth %, and a "Data as-of" timestamp. No "pending" placeholder cards remain.

8. Open `http://localhost:3836/sectors` *(J-04 regression guard)*
   - **Expect:** The Sector Leaderboard still renders ranked sectors with scores, A–E buckets, and labels exactly as before — unchanged by this iteration's `labels.py` refactor.

---

## What "Working Correctly" Looks Like

- `/stocks` and `/themes` are full ranked tables (not empty stubs), and the filters on `/stocks` visibly change the row count.
- NVDA's three scores read **identically** on `/stocks` and `/stocks/NVDA` (the headline single-source guarantee).
- The dashboard `/` has real Candidate Counts and Top Themes — no "pending" placeholders.
- `/sectors` is visually unchanged from the prior iteration.

## Common Issues

- **Blank page / "Backend unavailable" card on every page**: the backend API is down or has no seed data — start it and confirm `latest_data_date` is set.
- **`http://localhost:3836` not responding**: the managed `next dev` may be on a different port (try `3835`); the dev-server port has drifted between iterations. Confirm the live port before recording any verdict.
- **NVDA scores differ between list and detail**: single-source (J-06) violation — do not pass the iteration; flag for the developer.
- **Candidate Counts shows "pending"**: the dashboard wiring to `summarize_candidates` did not land — J-01 fails.
</content>
