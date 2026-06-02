# Phase goal-i_can_see_the_wealthy_future_forever-iter-6 — What to Click (Operator Verification Guide)

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-6
**Time required:** ~5 minutes
**Written by:** ui-test-designer

---

## Prerequisites

- Frontend running at `http://localhost:3835`
- Backend running at `http://localhost:8000`
- Seed data present with at least one historical date that has bars after it (use `2025-04-04` below)
- **IMPORTANT:** Do NOT press F5 / hard-reload after setting the as-of date — the as-of resets to "Latest" on reload. Always move between pages with in-app links/clicks.

---

## Verification Steps

1. Open `http://localhost:3835/stocks/NVDA` in your browser
   - **Expect:** The NVDA page loads, score cards and the price chart render. No greyed region (as-of is Latest). No error banner.

2. Open the global as-of switcher (top of the page) and select the date `2025-04-04`. Do NOT refresh.
   - **Expect:** The chart now extends past `2025-04-04`. Candles up to `2025-04-04` are in normal green/red; candles after it are **greyed/muted**, including their volume bars.
   - **Broken looks like:** the chart stops at `2025-04-04` (no candles to the right), OR every candle is greyed.

3. Look at the boundary between coloured and greyed candles, the legend, and the line just above the chart.
   - **Expect:** An arrow marker labelled `as-of 2025-04-04` sits at the boundary; the legend shows `Forward — after as-of 2025-04-04 (display only)`; a one-line caption above the chart says the forward bars are display-only and don't affect the scores/setup/VCP.

4. Switch the global as-of switcher back to **Latest** (stay on NVDA, no refresh).
   - **Expect:** The greyed forward region, the `as-of …` divider, the forward legend entry, and the caption all disappear. The chart looks like a normal Latest chart.

5. Re-select `2025-04-04` in the as-of switcher, then click the in-app nav link to the **Backtest** page (`/backtest`).
   - **Expect:** Backtest results load with sections in this top-to-bottom order: **As-of scan summary → Forward-test scorecard → Return Attribution → Top Sectors → Top Themes → Ranked Cohort**.
   - **Broken looks like:** Top Sectors / Top Themes / Ranked Cohort appearing *above* the scorecard.

6. Look at the **Top Sectors**, **Top Themes**, and **Ranked Cohort** lists.
   - **Expect:** Each list has a realized forward-return column with values for the current horizon. Themes also show a sample count (n). Missing data shows "—", never a fake 0%.

7. In the **Return Attribution** header, open the horizon view selector and pick a different horizon (e.g. switch from 5D to 21D).
   - **Expect:** The Return Attribution panel AND the return columns on all three lists update together, instantly, with no page reload and no loading spinner. The as-of switcher still shows `2025-04-04` (unchanged).
   - **Broken looks like:** only the attribution panel changes while the list columns stay put, or a full-page refetch/spinner fires, or the as-of date changes.

8. Confirm there is no second date control: scan the whole Backtest page.
   - **Expect:** The only date control is the global as-of switcher. The horizon selector lists horizons (e.g. 5D/21D/63D), not dates.

---

## What "Working Correctly" Looks Like

- On a historical as-of, the NVDA chart visibly continues past the as-of date with a greyed "forward" region, an `as-of {date}` marker, a matching legend swatch, and a display-only caption.
- At Latest as-of, none of those forward elements appear and the chart looks unchanged.
- On `/backtest`, the three leadership lists sit below Return Attribution and each carries a realized-return column, and one horizon selector drives the attribution panel and all three columns at once.

## Common Issues

- **Forward region missing on a historical as-of:** you probably hard-reloaded (F5), which reset the as-of to Latest. Re-set `2025-04-04` and use in-app nav only.
- **Blank page / error screen:** confirm the backend is up (`curl http://localhost:8000/health`) and the frontend dev server is on port 3835.
- **Return columns all show "—":** the selected horizon may have no after-the-as-of data for this date — try an earlier as-of (e.g. `2025-04-04`) or a shorter horizon; this NA behavior is intentional, not a bug.
