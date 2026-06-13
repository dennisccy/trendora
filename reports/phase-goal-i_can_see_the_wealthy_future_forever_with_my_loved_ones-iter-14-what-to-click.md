# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8000` (verify: `curl http://localhost:8000/health` returns 200)
- At least one event study subject (e.g., "Risk-off-watchlist") with forward-tested observations exists in the database

---

## Verification Steps

1. Navigate to `http://localhost:3835/research` in your browser
   - **Expect:** The Setup & Pattern Lab loads; a segmented button group with "Episodes" and "Pooled" labels is visible near the event study controls; "Episodes" is highlighted/active

2. Locate the disclosure line near the event study figures (muted/small text showing three values)
   - **Expect:** The disclosure line reads something like "n 707  Unique symbols 42  Episodes 312" — three distinct labeled values are all non-zero; the n value reflects collapsed episode counts (lower than per-signal-day counts)

3. Click the "Pooled" button in the Episodes/Pooled toggle
   - **Expect:** The "Pooled" button becomes highlighted and "Episodes" becomes inactive; the n value in the disclosure line increases (e.g., from 707 to 2,242); the other figures in the lab (hit-rate, expectancy, by-regime breakdown) update in-place without a page reload

4. Hover over or right-click any "N=" chip visible in the event study figures (while in Pooled mode)
   - **Expect:** The chip's destination URL (shown in the browser status bar or "Copy link" address) contains `view=pooled`; the chip label reads "occurrences" (not "episodes")

5. Click "Episodes" in the toggle to return to Episodes mode, then click an "N=" chip (or right-click and open in new tab)
   - **Expect:** A new tab opens at `http://localhost:3835/research/samples?...&view=episodes`; the URL contains `view=episodes`; the chip label reads "episodes"

6. On the `/research/samples` page that opened, look at the cohort detail header line near the top
   - **Expect:** The header line reads "Episodes (first-trigger)" — this confirms the drill-down is showing one row per first-trigger episode, not all signal days

7. Navigate to `http://localhost:3835/methodology` in a new tab and use Ctrl+F to search for "Episode"
   - **Expect:** A glossary entry titled "Episode" is present with an authored definition; a second entry "Pooled (per-signal-day)" is also visible; both definitions are distinct and non-empty

---

## What "Working Correctly" Looks Like

- On `/research`: two clearly labeled buttons "Episodes" and "Pooled" form a segmented toggle; "Episodes" is active by default; clicking "Pooled" raises the n count in the visible disclosure line
- On `/research/samples`: the cohort header reads either "Episodes (first-trigger)" or "Pooled (per-signal-day)" depending on which toggle was active when the N= chip was clicked
- On `/methodology`: two new glossary definitions exist under "Episode" and "Pooled (per-signal-day)"

## Common Issues

- **Toggle not visible / lab not loading**: Check that the backend is running (`curl http://localhost:8000/health`) and that the database has scan data (a slow or failed backend boot may leave the lab blank)
- **n value does not change after toggling**: Hard-refresh the page (Ctrl+Shift+R) to clear any stale Next.js cache; if still not updating, check the browser console for API errors on the `/api/research/event-study` request
- **Samples page shows wrong cohort label**: Ensure you are opening the N= chip from the correct mode — episodes chips link with `view=episodes` and pooled chips link with `view=pooled`; if the URL is missing the `view=` parameter, the backend defaults to episodes
- **Methodology entries not found**: Navigate directly to `http://localhost:3835/methodology` and scroll the full glossary; if entries are absent, the config.yaml terms catalog may not have been updated in this deployment
