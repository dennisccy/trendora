# Demo Script — goal-market-compass-iter-28

**Mode:** record
**Date:** 2026-08-31
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Navigate to the Today page  [NEW]

- **Narration:** We start at the home page, now called Today. This is the main decision surface—a ten-second read of the entire market state, from served values.
- **Action:** Navigate to /
- **Point out:** The page shows six sections in order: market state band (top), summary, what changed, leadership rotation, next-session focus, and manifest strip. The readiness badge and preflight strip remain above everything.
- **Screenshot:** reports/demo/goal-market-compass-iter-28/step-01.png

### Step 02 — Review the state-band tiles  [NEW]

- **Narration:** The state band shows regime and market phase at a glance. Regime reads Risk-on at 73.18 out of 100. The phase shows Expansion with a severity of 25.85.
- **Action:** Click "[data-testid='compass-state-band-card']"
- **Point out:** Each tile has a breakdown disclosure—click 'Why this X' to see component scores. The regime is built from Index MA, Breadth above moving averages, Net new highs, and a VIX gate. The phase comes from breadth, drawdown, regime risk, time underwater, and another VIX gate.
- **Screenshot:** reports/demo/goal-market-compass-iter-28/step-02.png

### Step 03 — See what changed since the last session  [NEW]

- **Narration:** Below the state band, the What Changed section lists leadership rotations—sectors, themes, and stocks that moved in or out of our focus list. This comes straight from the engine's session-over-session analysis.
- **Action:** Click "[data-testid='compass-whatchanged-card']"
- **Point out:** The Leadership Rotation section now has its own row, showing just sector, theme, and stock movements. All numbers are honest—empty changes are shown as such.
- **Screenshot:** reports/demo/goal-market-compass-iter-28/step-03.png

### Step 04 — Check the next-session focus  [NEW]

- **Narration:** The focus card lists actionable candidates for the next session. Each candidate shows why the system thinks it's worth monitoring, why not (if any), and what threshold changes would shift the call.
- **Action:** Click "[data-testid='compass-focus-section']"
- **Point out:** No fabricated scores here—just the three core buckets and honest explanations. Candidate presentation never invents return promises or buy-sell advice.
- **Screenshot:** reports/demo/goal-market-compass-iter-28/step-04.png

### Step 05 — Navigate to the Market page  [NEW]

- **Narration:** The state band includes a link to the Market page, where the full former dashboard lives. Let's click that link-out to see the complete regime × phase cross-view chart and deeper analysis.
- **Action:** Click "[data-testid='compass-state-band-market-link']"
- **Point out:** The cross-view chart is now absent from the Today page—by design. It lives on the Market page, one click away, keeping Today focused on the ten-second read.
- **Screenshot:** reports/demo/goal-market-compass-iter-28/step-05.png

### Step 06 — Explore the Market page  [NEW]

- **Narration:** Here is the Market page, showing everything the old dashboard carried: the regime and phase glance cards, the full cross-view chart with a show/hide toggle, and the More Detail section with breadth cards, top sectors, candidate counts, and the complete market phase timeline.
- **Action:** Navigate to /market
- **Point out:** Nothing is lost in the move. The chart's hide-show state is remembered in your browser storage. Sectors and themes endpoints are now fetched only on this page, not on Today.
- **Screenshot:** reports/demo/goal-market-compass-iter-28/step-06.png

### Step 07 — Check a historical date

- **Narration:** The as-of switcher at the top works on both pages. Let's look at April 15, 2025—a historical date where the system had a very different view.
- **Action:** Navigate to /?asof=2025-04-15
- **Point out:** At that historical date, the regime was Risk-off at 14.01, and the phase was Recovery with high severity. The manifest strip shows a retrospective label, confirming this is a past snapshot reconstructed from the stored run.
- **Screenshot:** reports/demo/goal-market-compass-iter-28/step-07.png

### Step 08 — Return to the latest view

- **Narration:** Clearing the date selector brings us back to Latest, the current frontier. The manifest strip shows the current session's frozen state, already locked in at ingest time.
- **Action:** Navigate to /
- **Point out:** The parameter vanishes from the URL, and the tiles refresh to show today's live values. History is immutable—each date's manifest never changes, even as later data arrives.
- **Screenshot:** reports/demo/goal-market-compass-iter-28/step-08.png
