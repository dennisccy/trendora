# Phase goal-i_can_see_the_wealthy_future_forever-iter-15 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-15
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running and reachable (the labs and leaderboard read live data)
- No login required

---

## Verification Steps

<!-- Verifies the J-31 synthesis travel: lab evidence → pre-filtered leaderboard → Stock Detail,
     plus the principal risk (exactly one date control). -->

1. Open `http://localhost:3835/research` in your browser
   - **Expect:** Page loads with heading "Research — Factor Lab"; no error card. Scrolling down reveals the card **"Setup & Pattern Lab — event study"**.

2. In that card, open the **Subject** dropdown and choose **"Pullback to rising DMA"** (under the "Patterns" group); wait for the tables to finish loading
   - **Expect:** Directly under the Subject dropdown you see the accent link **"View the names expressing this on the leaderboard →"** with a grey caption beginning "completes the synthesis path…".

3. Click **"View the names expressing this on the leaderboard →"**
   - **Expect:** You land on `http://localhost:3835/stocks?pattern=pullback_to_rising_dma__only`. The **Pattern** dropdown reads **"Pullback to rising DMA only"** and the count (e.g. "9 / 42") is narrowed — every visible row has a "Pullback" badge.

4. Click the **Ticker** link of the first row
   - **Expect:** You navigate to `http://localhost:3835/stocks/<TICKER>`; the detail page shows the pattern/setup badge, three A–E score badges, and an invalidation note. The three score buckets match what that row showed on the leaderboard.

5. Go back, then paste `http://localhost:3835/stocks?sector=Energy` straight into the address bar and load it
   - **Expect:** The **Sector** dropdown is already set to "Energy" on load and every visible row's Sector column reads "Energy" (deep-link pre-filter works). *(If your dataset has no Energy names, use any sector listed in the Sector dropdown.)*

6. On `/stocks`, change the **Pattern** dropdown to **"Pullback to rising DMA only"** and watch the address bar
   - **Expect:** The address bar updates to `…/stocks?pattern=pullback_to_rising_dma__only` and the page does NOT scroll-jump. Setting it back to "All patterns" clears the param from the URL.

7. **(Principal risk — J-18)** With a filter still in the URL, use the **top-bar as-of date switcher** to pick a different date
   - **Expect:** The "as of …" badge changes to the new date, BUT the `pattern=…` param stays in the address bar and the Pattern dropdown stays selected. No `as_of`/date param ever appears in the URL. There is only ONE date control on the page.

8. Paste `http://localhost:3835/stocks?pattern=garbage_value` into the address bar and load it
   - **Expect:** Page loads normally, no crash; the **Pattern** dropdown shows "All patterns" and the full list is shown (bad param ignored, nothing fabricated).

---

## What "Working Correctly" Looks Like

- Clicking the lab cross-link lands you on the leaderboard already filtered — you never have to re-pick the filter by hand.
- The leaderboard's address bar always reflects its active filters, so the view can be copied and re-opened.
- Switching the date keeps the filter; the filter never becomes a second date control.

## Common Issues

- **Blank page / "useSearchParams should be wrapped in a Suspense boundary" console error:** the Suspense wrapper around `StocksInner` is missing/broken — fail UT-02.
- **Cross-link missing in the lab card:** the subject hasn't resolved yet — wait for loading to finish; the link should appear for every resolved subject, including NA/low-sample ones.
- **`as_of`/date param appears in the URL after toggling the date, or the filter is lost:** J-18 violation — fail UT-12 (principal risk).
- **Backend down:** `/research` and `/stocks` show a red "Backend unavailable" card instead of data — start the backend and reload.
