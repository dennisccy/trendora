# Demo Script — goal-mcp-loop-iter-39

**Mode:** record
**Date:** 2026-07-15
**Frontend URL:** http://localhost:3255
**Iteration:** 39

## Highlights

### Step 01 — Open the dashboard

- **Narration:** Trendora opens on a live dashboard for the tracked stock universe, with one simple trust signal confirming today's numbers are current before you look at anything else.
- **Action:** Navigate to /
- **Point out:** The green "GO — today's board is current" banner sitting right below the header.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-39/step-01.png

### Step 02 — Browse the stock leaderboard

- **Narration:** Every tracked stock gets a Leadership, Entry Quality, and Risk score — and every single one of those scores is honestly labeled with its evidence status.
- **Action:** Navigate to /stocks
- **Point out:** The "541 / 541" coverage count at the top, and a small badge next to every score in the table.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-39/step-02.png

### Step 03 — Drill into one stock's evidence

- **Narration:** Opening any stock shows its full score breakdown — and each score carries the same honest badge, so nothing is ever quietly dressed up as proven.
- **Action:** Navigate to /stocks/AAPL
- **Point out:** The "Not yet proven" badge sitting next to each of AAPL's three scores.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-39/step-03.png

### Step 05 — See three decades of price history

- **Narration:** Stock pages default to a stock's full price history — for a long-tenured name like NVDA, that stretches all the way back to its real 1999 listing.
- **Action:** Navigate to /stocks/NVDA
- **Point out:** The full-history chart running to 3025 bars, and the "Technology" sector tag above it.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-39/step-05.png

### Step 07 — Audit the evidence ledger

- **Narration:** The Evidence ledger is where every tested idea gets judged out loud — wins and losses both, with nothing held back.
- **Action:** Navigate to /evidence
- **Point out:** Each claim card's real out-of-sample result, like "FAIL · holdout edge -0.03%", alongside its comparison against the S&P 500 and its registration date.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-39/step-07.png

### Step 14 — Check the statistical budget before it's spent

- **Narration:** Trendora keeps a running account of its own statistical testing budget, so nobody can quietly run endless tests until one passes by chance.
- **Action:** Navigate to /research/budget
- **Point out:** The note confirming the next canonical trial will be test #8, alongside the bar it has to clear.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-39/step-14.png

### Step 19 — See the tracked universe in the Data Manager

- **Narration:** The Data Manager shows exactly how many stocks are tracked and how complete their data is — with two separate, clearly-labeled signals instead of one confusing color.
- **Action:** Navigate to /data
- **Point out:** The "590 symbols" count, and a legend explaining the cell fill versus the ring around each cell.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-39/step-19.png

### Step 24 — Open the Watchlist's Concentration X-ray

- **Narration:** Below the familiar saved-stocks table, the Watchlist shows exactly how concentrated those picks really are — as one clear number, not a guess.
- **Action:** Navigate to /watchlist
- **Point out:** The "≈ 2.0 effective independent bets" headline, with the exact 126-trading-day window stated right next to it.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-39/step-24.png

## Full tour (text only)

### Step 04 — See the honesty hold even on a strong score

- **Narration:** MU's Leadership score is strong enough to earn a C grade, but it still gets exactly the same honest badge as every other stock — strength alone never buys a free pass.
- **Action:** Navigate to /stocks/MU
- **Point out:** MU's 77.18 Leadership score sitting right next to its "Not yet proven" badge.

### Step 06 — See an honestly short history for a recent listing

- **Narration:** Switching to a stock that only went public a couple of years ago, like ARM, shows a much shorter chart — real and short, never stretched or invented.
- **Action:** Navigate to /stocks/ARM
- **Point out:** ARM's chart starting at its actual 2023 IPO date, with 701 bars instead of thousands.

### Step 08 — Trace evidence back to where it lives

- **Narration:** Every claim on the ledger links straight back to the exact place in the product it backs, so the trail from claim to feature never dead-ends.
- **Action:** Click "Backs: Stocks leaderboard"
- **Point out:** Clicking "Backs: Stocks leaderboard" jumps straight to the leaderboard page.

### Step 09 — See evidence tied to today's market regime

- **Narration:** Some ideas are only meaningful in a specific kind of market — this claim shows exactly how a Risk-on-only setup performed, honestly, out of sample.
- **Action:** Navigate to /evidence
- **Point out:** The "Regime: Risk-on" condition tag on its own claim card.

### Step 10 — See evidence tested at a longer hold

- **Narration:** The same kind of idea is also retested holding for 60 days instead of the usual 20, and reports its honest result either way.
- **Action:** Navigate to /evidence
- **Point out:** The 60-day-hold claim card reading "FAIL · holdout edge -1.64%."

### Step 11 — See combined-factor evidence

- **Narration:** Ideas that blend more than one signal — like relative strength crossed with closeness to a high — go through the exact same rigorous, out-of-sample test as any single factor.
- **Action:** Navigate to /evidence
- **Point out:** The composite claim card labeled "rs_spy_3m × high_proximity — composite."

### Step 12 — Re-certify factors on the full history

- **Narration:** The Factor Lab confirms every tested signal has been re-checked against the platform's full three-decade history, not just a shorter recent window.
- **Action:** Navigate to /research/factor-lab
- **Point out:** The "~30 years of history" note near the top of the page.

### Step 13 — Open a factor's full decile breakdown

- **Narration:** Clicking into a factor opens its complete decile grid, showing exactly how each tier of stocks actually performed afterward — no summary hiding the real spread.
- **Action:** Click "factor-evidence-vcp_contraction"
- **Point out:** The "Decile grid — forward return" table, ranked from weakest to strongest tier.

### Step 15 — Browse the pre-registration registry

- **Narration:** Every idea gets logged here — reasoning, tags, and a registration date — before it's ever tested, so nothing can be cherry-picked after the fact.
- **Action:** Navigate to /research/registry
- **Point out:** Selector chips like "factor=vcp_contraction" next to each registered idea's plain-language rationale.

### Step 16 — Browse the graveyard of rejected ideas

- **Narration:** Ideas that failed testing aren't hidden away — they're archived here in the open, so nobody wastes time re-deriving a dead idea from scratch.
- **Action:** Navigate to /research/graveyard
- **Point out:** The full list of past rejected ideas, each with its own honest reason.

### Step 17 — Trace a rejected idea back to its registration

- **Narration:** Clicking a rejected idea's lineage link jumps straight to its original registration row, so the whole history of an idea is always one click away.
- **Action:** Click "[data-testid='graveyard-lineage-link']"
- **Point out:** The registry page scrolling itself right to the matching row.

### Step 18 — Check the tester's own calibration

- **Narration:** Trendora even audits its own statistical tester — running null trials and a deliberately corrupted factor to confirm the testing process itself can be trusted.
- **Action:** Navigate to /research/referee-audit
- **Point out:** The false-pass rate measured across 200 null trials, and the corrupted factor correctly labeled "expected: rejected."

### Step 20 — See the universe change over time

- **Narration:** The tracked universe isn't a fixed list frozen in time — it grows and shrinks as real companies list, delist, and merge, and this page shows exactly when.
- **Action:** Navigate to /data
- **Point out:** The dynamic-universe membership timeline.

### Step 21 — See where the benchmark data comes from

- **Narration:** Every index and macro series behind the scenes — the S&P 500, VIX, and more — is labeled with its real data source and how far back it goes.
- **Action:** Navigate to /data
- **Point out:** The provenance table listing each index's vendor and earliest available date.

### Step 22 — Watch for silent data drift

- **Narration:** The Data Manager quietly compares freshly-pulled prices against the trusted saved history, and flags anything that was silently revised.
- **Action:** Navigate to /data
- **Point out:** The Live-vs-seed drift panel.

### Step 23 — Run an honest backfill

- **Narration:** Kicking off a backfill completes cleanly and reports exactly what it did — no silent partial job, no guessed numbers.
- **Action:** Click the "Start" button
- **Point out:** The "Snapshots backfilled" confirmation once the job finishes.

### Step 25 — See the real computed correlation

- **Narration:** Behind that headline sits a real, computed correlation between every pair of saved stocks — not a color with nothing backing it.
- **Action:** Navigate to /watchlist
- **Point out:** The ABBV × MSFT cell reading "-0.11" right where the two rows and columns cross.

### Step 26 — See where the watchlist is concentrated

- **Narration:** Sector, theme, and shared-setup breakdowns show exactly where a watchlist leans too heavily on one thing — including an honest "Unassigned" bucket rather than a blank or crashed row.
- **Action:** Navigate to /watchlist
- **Point out:** The "Technology" and "Unassigned" sector bars, plus the concentration bars beneath them.

### Step 27 — Check the methodology behind the headline

- **Narration:** A small info icon next to the headline opens a plain-language explanation of exactly how that number gets worked out.
- **Action:** Click the "What is effective independent bets?" button
- **Point out:** The tooltip explaining the eigenvalues of the correlation matrix, in plain language.
