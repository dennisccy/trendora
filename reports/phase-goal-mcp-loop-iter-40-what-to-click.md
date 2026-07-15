# Phase goal-mcp-loop-iter-40 — What to Click (Operator Verification Guide)

**Phase:** goal-mcp-loop-iter-40
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3255`
- Backend running and reachable at `http://localhost:8255` (the top bar should show a green "Ready"
  badge, not a spinner or error state) — no login is required anywhere in this app
- The backend's snapshot database must already have been rebuilt under this iteration's code (this was
  confirmed done as of the last QA pass). If step 1 below shows no "Risk budget" card at all, this is
  the most likely cause — see "If Something Looks Wrong" below

---

## Verification Steps

1. Open `http://localhost:3255/stocks/AAPL` in your browser
   - **Expect:** The page loads with heading "AAPL". Below the card showing "THEMES" and
     "INVALIDATION", a new card titled "Risk budget" appears with 6 tiles: "ATR %", "Downside
     volatility", "Worst 20-day window", "Distance to invalidation", "Overnight gap · p95", and
     "Overnight share of 20d variance" — each showing a real percentage value (never blank, never
     "0%") with a small "pXX of universe" note underneath it.

2. Read the small paragraph of text at the top of the "Risk budget" card
   - **Expect:** It ends with the exact phrase "Descriptive only; not a recommendation." Nowhere in
     the card do the words "proven", "buy", "sell", "trim", or "edge" appear, and no colored
     badge/pill sits inside this card.

3. Open `http://localhost:3255/stocks` in a new tab
   - **Expect:** The leaderboard table loads with rows visible (a count like "590 / 590" appears near
     the search box).

4. Scroll the table horizontally to the right until you pass the "Proximity to 52w high" column
   - **Expect:** 5 new columns appear, in this order, right before the "Setup" column: "ATR%",
     "Downside vol", "Gap p95", "Worst 20d", "Dist. to invalidation" — each cell shows a "%" number or
     a muted gray "NA", never a blank cell.

5. Type `AAPL` into the "Search ticker or name…" box, then compare the number in the "ATR%" column
   for the AAPL row to the "ATR %" tile you saw in step 1
   - **Expect:** The two numbers are exactly identical (e.g. both read "2.84%") — confirming the
     leaderboard and the detail page are reading the same single stored value, not recomputing it.

6. Click the "ATR%" column header once
   - **Expect:** An arrow icon appears on that header and the rows re-sort by ATR% value; any rows
     showing "NA" in that column sink to the very bottom of the table (not scattered in the middle).

7. Click the small circular "i" icon next to the "Gap p95" column header
   - **Expect:** A popup appears with the term "overnight-gap profile", a definition, and a line
     reading "Gap window = 20 bars".

8. Open `http://localhost:3255/methodology`, scroll to the "Glossary" section, and type
   `distance-to-invalidation` into the "Search terms and definitions…" box
   - **Expect:** One result appears under the "FACTOR LAB & STATISTICS" category: term
     "distance-to-invalidation %" with its definition.

9. Go back to the `/stocks/AAPL` tab from step 1 and scroll to the very bottom of the page, to the 3
   score cards titled "Leadership", "Entry Quality", "Risk"
   - **Expect:** All 3 scores still display normally, each with a "Not yet proven" badge underneath —
     unchanged by the new card above them. Also check the thin strip at the very top of the page (just
     below the top bar): it should read "GO — today's board is current." in green.

10. Scroll a little further down on the same page to the "Price & moving averages" chart
    - **Expect:** The candlestick/price chart still renders normally with visible price bars — it is
      not pushed off-screen, hidden, or broken by the new Risk budget card higher up the page.

---

## What "Working Correctly" Looks Like

- The "Risk budget" card on a liquid stock's detail page (e.g. AAPL) shows 6 real-number tiles, each
  with a "pXX of universe" note — never a blank tile and never a fabricated "0%".
- The exact same number appears in both the `/stocks` leaderboard cell and the `/stocks/{ticker}` tile
  for the same stock and the same metric.
- The 5 new leaderboard columns sort correctly and always push "NA" rows to the bottom, in both sort
  directions.
- Nothing else on the page changed: the 3 scores, the evidence badges, the price chart, and the green
  "GO" banner all look exactly as they did before this phase.

## If Something Looks Wrong

- **No "Risk budget" card appears anywhere, and every leaderboard risk column reads "NA":** the
  backend's snapshot database has not been rebuilt under this iteration's code yet. This is a known
  operational step documented in `docs/handoffs/goal-mcp-loop-iter-40-dev.md` — an operator needs to
  rebuild `apps/backend/data/trendora.db` and restart the backend. You can confirm this is the cause
  by checking `http://localhost:8255/api/stocks/AAPL` for a `risk_budget` field — if it's missing or
  null, this is the cause, not a UI bug.
- **Blank page / "Backend unavailable" banner:** confirm the backend is running
  (`curl http://localhost:8255/api/health` should return a healthy status).
- **A short-history "NA — insufficient history" tile can't be found on any stock:** this is a known,
  already-investigated limitation of the current seed data (every ticker has well over the 20 days of
  history the new components need) — not evidence of a UI defect. Skip this check.
- **The card shows numbers but no "pXX of universe" percentile chips:** this WOULD be a real bug — the
  percentile pass should attach to every non-NA value.
