# Phase goal-mcp-loop-iter-23 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-23
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running at `http://localhost:8255`
- No login is required anywhere in this app
- The local database already has the deep benchmark symbols loaded (done as part of iter-22; you don't
  need to run anything yourself)
- **Context:** this iteration made zero application code changes. It only re-proves, through the live
  browser, that a chart fix already shipped in iter-22 actually works — the previous verification report
  had gone stale. If everything below looks correct, this iteration succeeded.

---

## Verification Steps

1. Open `http://localhost:3255` in your browser
   - **Expect:** The "Dashboard" heading loads with a green "Ready" badge in the top-right header (not a
     red "Backend unavailable" badge). Scroll down slightly until you see a card titled **"Regime × phase
     cross-view"**. If you instead see a dashed button reading "Show regime × phase cross-view", click it
     once to reveal the chart.

2. Without zooming or dragging, look at the chart's overall shape
   - **Expect:** Most of the 10 colored lines start partway across the chart (around the left third), but
     a few lines run the full width, all the way to the left edge — this is the deep 1996 history rendering
     by default. **This is the single most important thing to check this iteration** — a prior version of
     this chart only showed data starting around 2018 by default; if that's what you see now, the fix did
     not ship correctly.

3. Move your mouse to the very left edge of the chart's plotted lines
   - **Expect:** A tooltip appears in the top-right of the chart showing a date at or near `1996-01-02`,
     listing `^SPX`, `^NDX`, `^DJI`, and `^VIX` — each followed by a small `· Stooq` or `· Yahoo` tag.

4. Look at the row of labels (the legend) below the chart
   - **Expect:** 10 entries total. 5 of them show a small gray tag in parentheses after the name —
     `(Stooq)`, `(Stooq)`, `(Stooq)`, `(Yahoo)`, `(FRED-macro proxy)` — and the other 5
     (`S&P 500 (SPY)`, `Nasdaq 100 (QQQ)`, `Russell 2000 (IWM)`, `S&P 500 Equal-Weight (RSP)`,
     `Dow 30 (DIA)`) show no such tag.

5. Click **"Data Manager"** in the left sidebar, then scroll down past the **"Macro feed"** card
   - **Expect:** A card titled **"Index & benchmark data provenance"** appears directly after it, showing
     a 3-column table. The `S&P 500 Index (^SPX)` row shows Vendor `Stooq` and First bar `1996-01-02`.

6. On the same `/data` page, look at the top-right header badges
   - **Expect:** The last small badge reads exactly **"590 symbols"**. (This confirms the one intentional
     fixture update this iteration made — a test assertion changed from 587 to 590 — actually matches what
     the live app shows.)

7. Scroll down to the **"Per-date availability"** card and read its legend (two rows)
   - **Expect:** The first row is labeled "Price data — cell fill" with a strip of blue swatches going
     from dark to bright (never amber/orange at the bright end). The second row is labeled "Scored
     snapshot — indicator" with a small square that has a **violet ring** around it.

8. In the calendar grid on that same card, hover one fully-colored (brightest blue) day, then hover a
   different fully-colored day that has a violet ring around it
   - **Expect:** The readout text (top-right of the legend area) changes between the two: the first ends
     "... symbols · snapshot no", the second ends "... symbols · snapshot yes" (in a violet color).

9. Click **"Stocks"** in the left sidebar
   - **Expect:** The leaderboard loads with a count reading exactly **"541 / 541"** near the top-right of
     the filter row. Scan the symbol column — you should **not** see any row for `^SPX`, `^NDX`, `^DJI`,
     `^VIX`, or `^TNX`, and every score should read "Not yet proven" (never "Proven").

10. Click **"Evidence"** in the left sidebar
    - **Expect:** The page navigates to `/evidence`, heading "Evidence" is visible, and exactly **7** rows
      render, every one showing a **FAIL** verdict.

---

## What "Working Correctly" Looks Like

- The Dashboard's "Regime × phase cross-view" chart shows deep history (pre-2005 data) by DEFAULT, with no
  zooming or dragging required.
- The chart's 10 legend entries include vendor tags on 5 of them (`Stooq`/`Yahoo`/`FRED-macro proxy`), and
  the `/data` page's "Index & benchmark data provenance" table lists the same 10 series consistently.
- The header's "590 symbols" badge, the `/stocks` "541 / 541" count, and the availability heatmap's legend
  and hover states all match what's described above.
- Everything from before this change still works: `/stocks` shows only real stock tickers with
  "Not yet proven" badges, and `/evidence` still shows 7 all-FAIL rows.

## If Something Looks Wrong

- **Blank page / red "Backend unavailable" badge anywhere**: check the backend is running —
  `curl http://localhost:8255/api/health` should respond, not time out.
- **Chart's default view still floors around ~2018 (step 2 fails)**: this is the exact defect this
  iteration exists to re-verify as fixed. It usually means the frontend is serving a stale cached build —
  hard-refresh (Ctrl+Shift+R); if that doesn't clear it, the `apps/frontend/.next` build cache needs to be
  deleted and the frontend restarted. If it still fails after that, this is a real regression — escalate.
- **Header badge in step 6 shows "587 symbols" or any number other than "590"**: this means the live
  backend's data doesn't match what the (already-updated) test fixture expects — a real backend data-state
  problem, not something you can fix by refreshing the page.
- **The 1st and 6th legend dots in step 4 look like the exact same color**: this is a previously-fixed
  color-collision defect resurfacing — a real regression.
- **A row in `/stocks` (step 9) shows a symbol starting with `^`**: a deep index/macro symbol leaked into
  the scored leaderboard — a real regression, not expected under any circumstance.
