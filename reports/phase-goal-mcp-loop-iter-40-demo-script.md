# Demo Script — goal-mcp-loop-iter-40

**Mode:** record
**Date:** 2026-07-15
**Frontend URL:** http://localhost:3255
**Iteration:** 40

## Highlights

### Step 01 — A new 'how much can this hurt' card  [NEW]

- **Narration:** Every stock's detail page now includes a Risk budget card that spells out, in plain percentages, how much a name could realistically hurt you.
- **Action:** Navigate to /stocks/AAPL
- **Point out:** Below the Themes and Invalidation section, six tiles show ATR%, downside volatility, the worst historical 20-day drop, distance to the invalidation level, and an overnight-gap profile — each compared against the rest of the universe.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-40/step-01.png

### Step 02 — The same risk measures, ranked market-wide  [NEW]

- **Narration:** The stocks leaderboard now carries five new sortable risk columns, so you can rank the entire universe by risk exposure, not just by opportunity score.
- **Action:** Navigate to /stocks
- **Point out:** Scroll right past 'Proximity to 52w high' to see the new ATR%, Downside vol, Gap p95, Worst 20d, and Dist. to invalidation columns, each showing a real number or an honest 'NA'.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-40/step-02.png

### Step 03 — Sort by risk, not just by score  [NEW]

- **Narration:** Clicking a risk column header re-ranks every stock by that measure, and names without enough history to compute it honestly sink to the bottom instead of being hidden.
- **Action:** Click the "Worst 20d" button
- **Point out:** Watch the row order change and a sort arrow appear next to 'Worst 20d'.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-40/step-03.png

### Step 04 — Definitions built right into the table  [NEW]

- **Narration:** Every new risk column carries its own info icon, so anyone can check exactly how a measure is defined without leaving the leaderboard.
- **Action:** Click the "Gap p95 info" button
- **Point out:** The popup names the metric, explains it in plain language, and states the exact lookback window it's computed over.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-40/step-04.png

### Step 05 — A glossary that keeps up with new metrics  [NEW]

- **Narration:** The methodology page's glossary now documents every new risk term — its formula and the exact time window it uses — right alongside the site's existing definitions.
- **Action:** Navigate to /methodology
- **Point out:** The 'Factor Lab & Statistics' category gains three new entries; no new category was needed.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-40/step-05.png

### Step 06 — Searching for a new term  [NEW]

- **Narration:** Typing a new risk term into the glossary's search box instantly narrows the list to the one matching definition — the same search box that already covers every other term on the site.
- **Action:** Type "distance-to-invalidation" into "Search terms and definitions…"
- **Point out:** The single matching result, 'distance-to-invalidation %', appears with its plain-language definition.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-40/step-06.png

### Step 07 — Scores stay exactly as they were

- **Narration:** Back on a stock's detail page, the Leadership, Entry Quality, and Risk scores — and their honest 'Not yet proven' badges — look exactly as they did before the new card arrived.
- **Action:** Navigate to /stocks/AAPL
- **Point out:** Nothing about the existing scores or evidence badges changed; the new risk card lives entirely on its own, higher up the page.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-40/step-07.png

### Step 08 — Deep price history still works

- **Narration:** Further down the same page, the price chart still expands to a stock's full trading history at the click of a button, undisturbed by the new card above it.
- **Action:** Click the "Full history" button
- **Point out:** The chart redraws with a longer bar count and an updated 'as of' caption.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-40/step-08.png
