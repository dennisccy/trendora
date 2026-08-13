# Phase goal-ops-hardening-iter-77 — What to Click (Operator Verification Guide)

**Phase:** goal-ops-hardening-iter-77
**Time required:** ~5 minutes
**Written by:** ui-impact-analyst (combined mode)

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running and reachable (the top-bar badge should be able to reach "Ready")
- No login required
- Nothing needs to be seeded — the default dataset is enough

---

## Verification Steps

1. Open `http://localhost:3255` in your browser
   - **Expect:** The top-right corner shows a green "Ready" pill, and immediately next to it a small
     gray text reading "as of Ns ago" (usually "as of 0s ago"). This is new this round — it tells you
     how fresh the status you're looking at is.

2. Look directly below the top bar, at the thin green strip
   - **Expect:** It reads "GO — today's board is current.  (as of Ns ago)" — the same kind of freshness
     note, now also on this strip.

3. Refresh the page (press F5 or Cmd+R)
   - **Expect:** The "Ready" pill and the "as of Ns ago" text both reappear right away — this confirms
     it's a live reading on every load, not a one-time fluke.

4. Resize your browser window to about 1280 pixels wide by 800 tall (or use your browser's
   responsive/device toolbar and set a custom size of 1280×800)
   - **Expect:** The page still looks normal and the "Ready" pill is still visible in the top-right —
     nothing should look cut off yet.

5. Click "Backtest" in the left sidebar
   - **Expect:** Navigates to `http://localhost:3255/backtest`; a "Backtest" heading and a "Forward-test
     scorecard" table are visible.

6. In the top bar, click the left-arrow button just to the left of the "Latest" date dropdown (its
   tooltip/label is "Previous available date") 2-3 times, landing on a few different historical dates
   - **Expect:** The top bar updates to "Viewing as-of <date> (historical)". Within a few seconds, an
     accent-colored chip reading "background compute running (N)" should appear in the top bar next to
     the "Ready" pill (try a couple more clicks on different dates if it doesn't appear right away).

7. With the browser window still at 1280×800, look at the full top bar
   - **Expect:** BOTH the "Ready" pill AND the "background compute running (N)" chip are visible
     on-screen at the same time. If there isn't room on one line, the row wraps onto a second line —
     but neither element should be missing or pushed off the edge of the screen. (This is the specific
     bug this round fixed — previously the "Ready" pill could disappear here.)

8. Scroll down to the "Forward-test scorecard" table on the same page
   - **Expect:** Rows for the 1d, 5d, 10d, 20d, and 60d horizons are all visible, each showing return
     figures (or "—" if not yet elapsed) — the table looks exactly as it did before this update.

---

## What "Working Correctly" Looks Like

- A small "as of Ns ago" note appears next to the "Ready" pill and on the "GO" strip on every page load
  — never a blank space where it should be, and never a frozen/stuck number after a page refresh.
- At a 1280×800 window size, the "Ready" pill never disappears, even when a "background compute running
  (N)" chip is also showing.

## Common Issues

- **No "as of Ns ago" text ever appears, on any page**: check that the backend is actually running
  (`curl http://localhost:8255/health` should return JSON with a `stale_for_s` field). If the badge
  itself shows "Backend unavailable" instead of "Ready", no annotation is expected — that's correct
  behavior, not a bug (the app never shows a fabricated staleness number when it can't reach the
  backend).
- **The "background compute running (N)" chip never appears after step 6**: this window only appears
  while the backend is actively computing forward-looking figures for a historical date that isn't
  already cached for the current dataset version — try a few more "Previous available date" clicks on
  dates you haven't visited yet this session, or move on; steps 1-3 and 5, 8 do not depend on it.
- **"Ready" pill or the chip is genuinely missing at 1280×800 after step 7**: this would indicate the
  layout regression this round was supposed to fix has NOT been fixed — flag this as a failure, take a
  screenshot, and note the exact window size used.
