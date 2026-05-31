# Phase goal-i_can_see_the_wealthy_future-iter-8 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future-iter-8
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8835` (the pages will show "Backend unavailable" if it is down)
- At least **2 stored Scanner Run dates** (so the date drop-down has a past date to pick). Verify with
  `curl -s http://localhost:8835/api/runs` — you should see ≥2 entries with `asof_date` values.

> In the steps below, **{latest}** = the date shown next to "Latest" in the drop-down, and
> **D_OLD** = any older date listed below it (e.g. `2022-10-07`).

---

## Verification Steps

1. Open `http://localhost:3835/` in your browser
   - **Expect:** The "Dashboard" page loads with regime/breadth panels. In the top bar (right side) a
     date drop-down shows "Latest · {latest}", and a quiet "Latest" badge sits to its left. No
     "Backend unavailable" card.

2. Click the date drop-down in the top bar and read its options
   - **Expect:** First option is "Latest · {latest}", followed by one or more older dates in
     newest-first order. No blank or duplicate entries.

3. Select a past date (**D_OLD**) from the drop-down
   - **Expect:** The "Data as-of" badge next to the "Dashboard" heading changes to "Data as-of {D_OLD}",
     and the badge by the drop-down turns **amber** reading "Viewing as-of {D_OLD} (historical)". At
     least one panel value changes versus the latest view.

4. Click "Stocks" in the left sidebar
   - **Expect:** The Stocks leaderboard loads showing "as of {D_OLD}" near the heading, and the amber
     "Viewing as-of {D_OLD} (historical)" badge is still in the top bar — the date carried over without
     re-selecting.

5. Note NVDA's three scores (Leadership, Entry Quality, Risk) on `/stocks`, then click the NVDA row
   - **Expect:** `http://localhost:3835/stocks/NVDA` opens showing "as of {D_OLD}" and the same three
     scores as the leaderboard row — list and detail agree.

6. On the NVDA detail page, look at the price chart caption
   - **Expect:** It reads "{n} bars · as of {D_OLD}" and the chart's right-most bar is on or before
     D_OLD — no price action after the selected date is shown.

7. Click "Themes", then "Sectors" in the left sidebar
   - **Expect:** Each page shows "as of {D_OLD}" with populated rows — the historical date is applied
     across all pages.

8. Open the top-bar date drop-down and select the top "Latest · {latest}" option
   - **Expect:** The amber badge disappears and the quiet "Latest" badge returns; the current page's
     "as of" badge reads "as of {latest}" again.

9. Press F5 to hard-refresh the page (after first re-selecting D_OLD, optional)
   - **Expect (known limitation):** The page returns to the latest view ("as of {latest}", "Latest"
     badge). The selected date is intentionally not in the URL — in-app navigation keeps it, a hard
     reload resets to Latest. This is expected, not a bug.

---

## What "Working Correctly" Looks Like

- The top-bar date drop-down appears on **every** page and keeps its selection while you click around
  the sidebar.
- Picking a past date flips every page (Dashboard, Stocks, Stock detail + chart, Themes, Sectors) to
  that date's snapshot, with an unmistakable amber "Viewing as-of {date} (historical)" badge.
- A stock's three scores are identical between the leaderboard and its detail page, at both the latest
  and the historical date.
- The price chart never shows bars dated after the selected as-of date.

## Common Issues

- **Drop-down only shows "Latest" with no past dates:** Only one Scanner Run is stored. Confirm
  `curl -s http://localhost:8835/api/runs` returns ≥2 dates; seed/scan an older date if needed.
- **"Backend unavailable" card / blank panels:** Backend not running — check
  `curl http://localhost:8835/health` and restart the backend.
- **Date resets after clicking around:** Expected only on a hard browser refresh (step 9); during
  normal sidebar navigation the date must persist — if it resets on a plain sidebar click, that is a bug.
- **Drop-down is greyed out / disabled:** The run list hasn't loaded yet or `/api/runs` failed — the
  switcher disables and pages fall back to the latest view (never fabricated data).
