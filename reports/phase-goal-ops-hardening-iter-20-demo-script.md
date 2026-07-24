# Demo Script — goal-ops-hardening-iter-20

**Mode:** record
**Date:** 2026-07-24
**Frontend URL:** http://localhost:3255
**Iteration:** 20

## Highlights

### Step 01 — Open the home dashboard

- **Narration:** We start on Trendora's home dashboard — the daily market snapshot at a glance.
- **Action:** Navigate to /
- **Point out:** The Market Regime score and label, and the Market Phase & Severity read, right at the top of the page.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-20/step-01.png

### Step 02 — Check the dataset's health

- **Narration:** The Data Manager page shows exactly what's stored and whether anything still needs catching up.
- **Action:** Navigate to /data
- **Point out:** Price history range, universe and symbol counts, and any remaining backfill gaps — all read straight from the stored data, never guessed.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-20/step-02.png

### Step 03 — Open Backtest for the latest date

- **Narration:** Backtest lets you time-machine to a past scan date and read its forward-test scorecard — today's (Latest) view stays exactly as fast and unaffected as always.
- **Action:** Navigate to /backtest
- **Point out:** The badge names exactly which date you're viewing, with a standing note about survivorship bias always shown alongside the numbers — and the page settles in almost instantly.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-20/step-03.png

### Step 04 — Read today's scorecard

- **Narration:** The Forward-test scorecard reports how the top-ranked stocks from a given date actually performed afterward.
- **Action:** Click "Forward-test scorecard"
- **Point out:** For this very latest date, every horizon honestly reads a dash — nothing has happened yet to measure, so nothing is invented to fill the gap.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-20/step-04.png

### Step 05 — See the day's ranked leaders

- **Narration:** Leadership cohorts name the top sectors, themes, and individual stocks the scan singled out for this date.
- **Action:** Click "Leadership cohorts"
- **Point out:** Top Sectors, Top Themes, and the Ranked cohort table all show real rankings and scores; their forward-return columns stay an honest dash until enough time has passed to measure one.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-20/step-05.png

### Step 06 — See the accumulated evidence

- **Narration:** At the very bottom sits the forward-tested evidence — the track record pooled from every trading day scanned so far, not just today.
- **Action:** Click "Forward-tested evidence"
- **Point out:** Real accumulated numbers going back through the whole history, plus a guarantee behind the scenes: this section always shows either the freshest complete evidence or a clearly-labeled slightly older set — never a blank message.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-20/step-06.png

### Step 07 — Time-travel to a date nobody's looked at yet  [NEW]

- **Narration:** Opening an older backtest date that's never been viewed before used to freeze the tab for anywhere from several seconds to almost a minute with nothing on screen — it now responds right away.
- **Action:** Navigate to /backtest?asof=2006-02-01
- **Point out:** The page settles almost instantly and clearly names the historical date you're now viewing — never a blank, frozen tab.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-20/step-07.png

### Step 08 — An honest note instead of a blank wait  [NEW]

- **Narration:** Since this date's own numbers haven't been worked out before, the page says so plainly right away instead of leaving the screen blank or pretending the numbers are already in.
- **Action:** Click "in the background"
- **Point out:** A calm message explains that viewing this page itself started the calculation in the background, and that reloading shortly will show the finished numbers — no numbers are ever invented in the meantime.
- **Screenshot:** reports/demo/goal-ops-hardening-iter-20/step-08.png
