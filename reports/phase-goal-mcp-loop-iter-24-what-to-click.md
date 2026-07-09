# Phase goal-mcp-loop-iter-24 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-24
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running in prod mode at `http://localhost:3255`
- Backend running in prod mode at `http://localhost:8255` and reachable
- No login is required (this product has no auth)
- The backend has its normal dataset loaded (not a fresh/empty database) — you should already see real
  numbers on the Data Manager page, not all-zero placeholders
- AAPL and MSFT should both exist in the scanned universe (they do on the standard dataset)

---

## Verification Steps

1. Open `http://localhost:3255/data` in your browser
   - **Expect:** The "Data Manager" page loads. A "Dataset coverage" card appears near the top. No red
     "Backend unavailable" banner.

2. Scroll down just past "Dataset coverage"
   - **Expect:** A new card titled **"Storage footprint"** (small database icon next to the title) shows
     four values: **Database file** (a size like "1.22 GB"), **Price bars**, **Scanner rows**, and
     **Forward returns** (each a comma-formatted count, e.g. "3,293,160"). This is the one new thing this
     iteration adds — if this card is missing entirely, that is the single most important thing to flag.

3. Refresh the page (press F5)
   - **Expect:** The same four Storage footprint values reappear unchanged (they read stored numbers, not
     a fresh random computation).

4. Navigate to `http://localhost:3255/stocks`, type `AAPL` into the search box (placeholder "Search ticker
   or name…"), and note its **Leadership**, **Entry Quality**, **Risk**, and **Setup** column values
   - **Expect:** The AAPL row appears with values in each of those columns.

5. Click the **AAPL** ticker link in that row
   - **Expect:** The detail page loads at `http://localhost:3255/stocks/AAPL` within a few seconds. The
     setup badge and the three score cards ("Leadership", "Entry Quality", "Risk") show the **exact same
     values** you noted in step 4. If any number differs, that is a real regression — stop and report it.

6. On that same page, find the "Price & moving averages" card and click the **"Full history"** button
   (next to "Recent", top-right of that card)
   - **Expect:** The chart redraws with a longer date range (older candles appear, the bar count in the
     small caption above the chart increases). No error, no frozen/blank chart.

7. Look at the small badge in the top-right corner of the page header, next to the date control
   - **Expect:** It reads **"Ready"** (green) once the backend has finished warming up, or **"Initializing…
     history N/M"** (amber) if it just started. It should never be blank or stuck reading "Checking
     backend…" for more than a few seconds.

8. Navigate to `http://localhost:3255/watchlist`
   - **Expect:** The page loads with the "Add" form and any previously-saved entries, no error banner.

9. Navigate to `http://localhost:3255/evidence`
   - **Expect:** The page loads within a few seconds — no blank white screen, no frozen tab.

---

## What "Working Correctly" Looks Like

- The new "Storage footprint" card on `/data` shows a real, human-readable database file size and three
  comma-formatted row counts, styled the same as the "Dataset coverage" card right above it.
- AAPL's Leadership / Entry Quality / Risk / Setup values are identical whether you look at them on the
  `/stocks` leaderboard or on `/stocks/AAPL`'s own detail page.
- Every page you visited above appeared within a few seconds — never a blank white screen, never a frozen
  tab, never a Next.js "Application error" page.

## If Something Looks Wrong

- **Blank page / Next.js error screen on any page** — confirm the backend is actually reachable:
  `curl http://localhost:8255/api/health` should return a JSON body, not a connection error.
- **The "Storage footprint" card is missing from `/data` entirely** — the frontend may be running a stale
  build. Confirm `apps/frontend/.next` was cleared and the frontend was rebuilt/restarted after this
  iteration's changes were deployed.
- **Storage footprint values read "undefined" or stay blank** — the backend hasn't picked up this
  iteration's changes; confirm the backend process was restarted after deployment, and check that
  `GET http://localhost:8255/api/data` includes a `capacity` key in its JSON response.
- **AAPL's (or any ticker's) leaderboard value and detail-page value differ** — this is a genuine
  regression in this iteration's item D (ticker-filtered fetch), not a rendering quirk. Stop and report it
  rather than re-checking repeatedly.
- **A page takes noticeably longer than ~3 seconds to settle, or looks frozen** — check
  `reports/perf-budgets.md` for the committed budget on that specific page/endpoint before deciding whether
  it's a regression; a single slow load right after a cold backend restart is expected (see the cold-path
  budget), but a warm page consistently this slow is not.
