# Demo Script — goal-mcp-loop-iter-41

**Mode:** record
**Date:** 2026-07-16
**Frontend URL:** http://localhost:3255
**Iteration:** 41

## Highlights

### Step 01 — A new look at what a dry spell really costs  [NEW]

- **Narration:** Every certified claim on the Evidence page now includes a plain-language breakdown of what following it has historically felt like to hold, split out by the market phase you'd have entered in.
- **Action:** Navigate to /evidence
- **Point out:** Below each card's existing details, a new panel appears headed 'Historical drawdown & dry-spell expectations,' with one row per market phase — Expansion, Pullback, Correction, Bear, and Recovery. The green 'GO' banner at the top still confirms today's board is current.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-41/step-01.png

### Step 06 — The leaderboard looks exactly as before

- **Narration:** Away from the Evidence page, nothing else changed — the stock leaderboard still marks every score honestly.
- **Action:** Navigate to /stocks
- **Point out:** Every Leadership, Entry Quality, and Risk score still carries a small 'Not yet proven' badge, since no claim has passed certification yet.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-41/step-06.png

### Step 07 — A single stock's page is untouched too

- **Narration:** A stock's own page still shows the same three honestly-labeled scores, with no drill-down control appearing where none is warranted.
- **Action:** Navigate to /stocks/AAPL
- **Point out:** All three score cards on AAPL's page read 'Not yet proven,' and there's still no 'Why proven?' button, since nothing here is certified yet.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-41/step-07.png

### Step 08 — Deep price history still expands on demand

- **Narration:** The button that loads a stock's full multi-decade trading history still works exactly as before.
- **Action:** Click the "Full history" button
- **Point out:** Clicking 'Full history' grows the chart from about five years of bars to nearly thirty, adding a note that the older bars are weekly-sampled.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-41/step-08.png

### Step 09 — The Data Manager page is unaffected

- **Narration:** The page for growing and checking the dataset still loads cleanly, with its coverage details intact.
- **Action:** Navigate to /data
- **Point out:** The 'Dataset coverage' panel still lists price history, universe size, and backfill gaps — nothing about it changed.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-41/step-09.png

## Full tour (text only)

### Step 02 — Real figures, not vague warnings  [NEW]

- **Narration:** Where there's plenty of history to draw on, the panel shows real numbers: how deep the typical drawdown ran, how long positions stayed underwater, and how long recovery usually took — each labeled with its own sample size.
- **Action:** Navigate to /evidence
- **Point out:** The first card's Expansion row shows a median max-drawdown of -7.70% (90th-percentile -3.72%) across 1,264 observations.

### Step 03 — Honest when one measure runs thin  [NEW]

- **Narration:** When a single measure doesn't have enough history behind it, the panel says so plainly instead of guessing — while its neighboring measures still show real figures.
- **Action:** Navigate to /evidence
- **Point out:** On the same card, the Correction row's 'Longest losing streak' cell reads 'insufficient (n=5)' in muted gray, even though the row's other three measures are real, well-populated numbers.

### Step 04 — Even a whole empty phase is shown honestly  [NEW]

- **Narration:** For a claim whose history has zero examples in a given phase, every measure in that row admits it — never a fabricated number or a broken card.
- **Action:** Navigate to /evidence
- **Point out:** The second claim card's Correction and Bear rows both read 'insufficient (n=0)' across all four measures, while the rest of that same card renders normally around them.

### Step 05 — The method is explained, not hidden  [NEW]

- **Narration:** Two short sentences under every table spell out exactly how the numbers are counted and remind readers this is history, not a promise.
- **Action:** Navigate to /evidence
- **Point out:** The same two sentences appear word-for-word under every one of the seven cards, ending with 'Read the edge as an upper bound, not a guarantee.'
