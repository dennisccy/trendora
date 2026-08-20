# goal-market-compass-iter-3 — What to Click (Operator Verification Guide)

**Phase:** goal-market-compass-iter-3
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running and reachable (no login is required — this product has no auth)
- No special seed data needed — the committed 30-year seed already has trading dates to step through

---

## Verification Steps

1. Open `http://localhost:3255/` in your browser
   - **Expect:** The Dashboard page loads with heading "Dashboard". Scrolling down, you see four cards
     in order — "Summary", "What changed", "Next-session focus", and a new **"Manifest"** card — above
     the regular Market Regime / Market Phase charts.

2. In the top bar, click the "◀" arrow button once (just left of the date badge that reads "Latest")
   - **Expect:** The date badge changes to "Viewing as-of \<some date\> (historical)" in amber, and the
     page's content updates for that date.

3. Scroll down to the "Manifest" card and look at it
   - **Expect:** You see a row of badges — a mode word ("retrospective" or "at ingest"), "version 1", a
     "frozen"/"not frozen" badge, and a "prospective-eligible"/"not prospective-eligible" badge — plus a
     "Frozen \<date/time\>" line and four short hash values labeled "Engine identity", "Candidate rule",
     "Cohort rule", "Manifest config". If instead you see only the sentence "This manifest predates the
     freeze/integrity block…", click "◀" again to step to an older date and re-check — most historical
     dates create a fresh manifest the first time you view them.

4. On the Manifest card, click the row that starts with "Audit table — comparison cohort ("
   - **Expect:** It expands to show a table of stock tickers with a "Disposition" column, plus a second
     table below an amber "Near-threshold shadow — research-only substrate…" label.

5. Click the "Regenerate manifest" button on the Manifest card
   - **Expect:** A modal titled "Confirm manifest regenerate" opens, explaining that this mints a new
     version and never touches the existing one.

6. In the modal's footer, click "Regenerate manifest" again to confirm
   - **Expect:** The modal closes, and — without the page reloading — the card's version badge jumps up
     by one (e.g. "version 1" → "version 2") and the eligibility badge now reads "not
     prospective-eligible". A new "Versions" list appears listing both versions.

7. Refresh the page (press F5 or Cmd+R)
   - **Expect:** The Manifest card still shows the same (now higher) version number and the "Versions"
     list still lists both versions — confirms the new version persisted, and the original version
     was not overwritten.

8. Click the date-picker button in the top bar (the one showing the current date next to a calendar
   icon), then click the "Latest · \<date\>" button at the bottom of the popover that opens
   - **Expect:** The date badge returns to "Latest", and on the Manifest card the "Regenerate manifest"
     button is now GONE, replaced by a line of text explaining regenerate is only available for a
     historical date.

9. Scroll up to the "Summary" card and click "Show cited facts"
   - **Expect:** A list of numeric facts expands, and every number shown has exactly two digits after
     the decimal point (e.g. "6.27") — never a long string of digits like "6.2700000000000005".

10. Scroll to "Next-session focus" and open any candidate card's "Cautions" section (visible directly on
    the card, no extra click needed, if that candidate has one)
    - **Expect:** If an "ATR_RISK_BUDGET:" caution is present, it ends with "...of universe)." — it does
      NOT end with the phrase "sized risk accordingly".

---

## What "Working Correctly" Looks Like

- The "Manifest" card is the last of four compass cards on `/`, sitting above the older Market
  Regime/Phase charts, and never shows a blank space — it always shows either full badges/chips, the
  "predates the freeze/integrity block" message, or a red "unavailable" message.
- Clicking "Regenerate manifest" → confirming always increases the version number by exactly one, never
  changes an existing version's badges, and survives a page refresh.

## Common Issues

- **Manifest card missing entirely / whole page blank**: check that the backend is running
  (`curl http://localhost:8000/api/health` or the configured backend port) — the card degrades to a red
  "unavailable" message on any backend failure, it should never disappear silently.
- **"Regenerate manifest" button never appears**: confirm the date badge in the top bar reads "Viewing
  as-of … (historical)", not "Latest" — the button is intentionally hidden while viewing the live
  frontier.
- **Version number doesn't change after confirming**: check the browser console/network tab for a failed
  `POST /api/compass/regenerate` request — a 400 means the confirm flag didn't reach the backend, a 404
  means the selected date has no manifest yet (re-check step 3 succeeded first).
