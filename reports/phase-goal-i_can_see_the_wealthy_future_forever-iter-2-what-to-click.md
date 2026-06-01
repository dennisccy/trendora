# Phase goal-i_can_see_the_wealthy_future_forever-iter-2 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-2
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8000`
- At least one walk-forward snapshot with elapsed forward windows (otherwise System Health shows
  "No forward-tested evidence yet" and Backtest shows all-NA — pick an older as-of date if so)

---

## Verification Steps

1. Open `http://localhost:3835/system-health` in your browser
   - **Expect:** "System Health" page loads (skeleton replaced by panels), no "Backend unavailable"
     error card

2. Scroll to the very bottom of the page, past the "Control-group comparison — selection vs sector
   beta" card
   - **Expect:** A "Return attribution" section heading appears, with four panels: "Top contributors &
     detractors", "Distribution & hit-rate", "Forward return by sector", "Forward return by rank band"

3. In the "Top contributors & detractors" panel, read the two columns
   - **Expect:** Columns "Contributors" and "Detractors", each listing tickers with a sector label and a
     colored mean return showing `(n=…)` — real ticker symbols, not placeholders

4. Compare the "Distribution & hit-rate" → "Mean" row to the "Mean stock fwd return: …" value in the
   summary strip near the top of the page
   - **Expect:** The two values match exactly (same number, same color) — one canonical mean, no
     divergent second value

5. Click a different horizon button (e.g. "5d") in the "Horizon" selector at the top-right, next to the
   "System Health" heading
   - **Expect:** The "5d" button highlights, and the "Return attribution" panels update to the new
     horizon; the section intro now reads "Open the 5-day forward return:"

6. In the left sidebar, click "Backtest", then use the top-bar "View as-of date" dropdown to select a
   historical date (any date other than "Latest")
   - **Expect:** Page shows "Viewing as-of {date} (historical)" badge and a "Forward-test scorecard"
     table

7. Scroll below the "Forward-test scorecard" table to the "Return attribution" section
   - **Expect:** Four panels render, and the section header carries a "Horizon" segmented selector with
     buttons "1d / 5d / 10d / 20d / 60d"; the default-highlighted button shows real numbers, not all-NA

8. Click a different Horizon button in that section (e.g. "10d")
   - **Expect:** Only the four attribution panels change to the 10d slice; the "Forward-test scorecard"
     table above and the "Viewing as-of {date}" badge do NOT change

9. Open DevTools → Network tab, clear the log, then click between the Horizon buttons (1d → 5d → 60d)
   - **Expect:** NO new `/api/backtest` request fires during the clicks (the section re-renders from
     data already loaded); the as-of date is unchanged

10. Refresh the page (F5)
    - **Expect:** The same as-of date and scorecard reload, and the "Return attribution" section
      re-appears — the feature is stable across reload

---

## What "Working Correctly" Looks Like

- Both `/system-health` and `/backtest` show a "Return attribution" section with four populated panels
  for a horizon that has data
- On System Health, the attribution "Mean" matches the page's "Mean stock fwd return" header (single
  source of truth)
- On Backtest, the "Horizon" buttons re-render panels instantly with no network call and never change
  the as-of date or the scorecard above

## Common Issues

- **Blank page / "Backend unavailable" card**: Check the backend is running
  (`curl http://localhost:8000/health`)
- **All panels show "—" (NA)**: The selected as-of date / horizon has no elapsed forward window — this
  is honest behavior, not a bug. Pick an older as-of date or a shorter horizon to see populated figures.
- **A new `/api/backtest` request fires when clicking Horizon buttons**: This is a defect — the Horizon
  selector must be view-only and must not refetch or change the date.
</content>
