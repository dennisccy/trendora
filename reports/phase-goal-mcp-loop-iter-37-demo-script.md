# Demo Script — goal-mcp-loop-iter-37

**Mode:** record
**Date:** 2026-07-15
**Frontend URL:** http://localhost:3255
**Iteration:** 37

## Highlights

### Step 01 — Open the dashboard

- **Narration:** Trendora opens on a live dashboard that reads today's market regime and links straight to the evidence behind it.
- **Action:** Navigate to /
- **Point out:** The current regime badge (Risk-on) and the 'See evidence proven in this regime' link just below it.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-37/step-01.png

### Step 03 — Browse the stock leaderboard

- **Narration:** Every one of the 541 tracked stocks gets a leadership score, and every score is honestly labeled with its evidence status.
- **Action:** Navigate to /stocks
- **Point out:** The '541 / 541' coverage count and the 'Not yet proven' badge next to every score.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-37/step-03.png

### Step 04 — Open a stock's detail page

- **Narration:** Drilling into NVDA shows its full profile — sector, score breakdown, and price chart.
- **Action:** Navigate to /stocks/NVDA
- **Point out:** The sector tag and the per-factor score panel.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-37/step-04.png

### Step 07 — Audit the evidence ledger

- **Narration:** The Evidence ledger lists every tested idea with its real out-of-sample result, wins and losses both — no cherry-picking.
- **Action:** Navigate to /evidence
- **Point out:** Each claim card's out-of-sample verdict, control comparison versus SPY, registration date, and forward-walk score-to-date.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-37/step-07.png

### Step 08 — Trace evidence back to its surface

- **Narration:** Every claim links straight back to where it shows up in the product, so the evidence trail never dead-ends.
- **Action:** Click "Backs: Stocks leaderboard"
- **Point out:** Clicking 'Backs: Stocks leaderboard' jumps straight to the leaderboard.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-37/step-08.png

### Step 13 — See factors re-certified on 30 years of data

- **Narration:** The factor lab confirms every tested signal is re-certified on the full 30-year history — nothing coasts on a stale result.
- **Action:** Navigate to /research/factor-lab
- **Point out:** The '~30 years of history' disclosure and the per-horizon 'Not yet proven' badges.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-37/step-13.png

### Step 15 — See the statistical budget before it's spent

- **Narration:** Trendora shows exactly how much of its statistical testing budget has been used, so nobody can quietly run endless tests until one passes by chance.
- **Action:** Navigate to /research/budget
- **Point out:** The next-trial counter and the required significance threshold.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-37/step-15.png

### Step 19 — Check the certifier's own calibration

- **Narration:** Trendora even audits its own tester — this page runs null-trial and contamination checks to confirm the certifier itself can be trusted.
- **Action:** Navigate to /research/referee-audit
- **Point out:** The false-pass rate measured on null trials, and a deliberately contaminated factor correctly flagged 'expected: rejected'.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-37/step-19.png

## Full tour (text only)

### Step 02 — See the benchmark and macro context

- **Narration:** The same dashboard carries real index and macro context — the S&P 500, VIX, and a yield-curve proxy — right alongside the regime call.
- **Action:** Navigate to /
- **Point out:** The regime-by-phase panel listing each labeled index quote.

### Step 05 — See the full 30-year price history

- **Narration:** Switching the chart to full range reveals up to three decades of price history, honestly bounded to each stock's real listing date.
- **Action:** Click "chart-range-full"
- **Point out:** The bar count jumping from about 1,255 (five-year view) to 3,025 (full history).

### Step 06 — See the same honesty on another stock

- **Narration:** Switching to AAPL shows the identical 'Not yet proven' status — no score is dressed up as proven until it has passed independent testing.
- **Action:** Navigate to /stocks/AAPL
- **Point out:** The 'Not yet proven' badge next to AAPL's score.

### Step 09 — See regime-conditioned evidence

- **Narration:** Some ideas are only tested within a specific market regime — this card shows how a Risk-on breakout setup fared out of sample.
- **Action:** Navigate to /evidence
- **Point out:** The 'Regime: Risk-on' tag on the claim card, and its honest verdict.

### Step 10 — See evidence across hold horizons

- **Narration:** The same setup is retested at different hold lengths too — this one checks a 60-day hold instead of the usual 20 days, and reports the honest result either way.
- **Action:** Navigate to /evidence
- **Point out:** The '60-day hold' condition chip next to its own verdict.

### Step 11 — See combined-factor evidence

- **Narration:** Ideas that combine multiple signals — like relative strength crossed with proximity to highs — go through the exact same rigorous, out-of-sample test.
- **Action:** Navigate to /evidence
- **Point out:** The composite hypothesis chip and its own honest verdict.

### Step 12 — Open the Research hub

- **Narration:** The Research hub is the gateway to every governance page: pre-registration, the statistical budget, the graveyard of rejected ideas, and the referee's own calibration check.
- **Action:** Navigate to /research
- **Point out:** The links out to each governance surface.

### Step 14 — Drill into a factor's decile grid

- **Narration:** Clicking a factor's badge opens its full decile breakdown, showing exactly how each tier of stocks performed going forward.
- **Action:** Click "factor-evidence-vcp_contraction"
- **Point out:** The decile grid, ranked from weakest to strongest tier.

### Step 16 — Browse the pre-registration registry

- **Narration:** Every hypothesis is registered here before it's tested, so nothing can be quietly cherry-picked after the results are in.
- **Action:** Navigate to /research/registry
- **Point out:** The selector chips, rationale, registration date, and status for each pre-registered idea.

### Step 17 — Browse the graveyard of rejected ideas

- **Narration:** Ideas that failed testing aren't hidden — they're archived here so nobody wastes time re-testing them.
- **Action:** Navigate to /research/graveyard
- **Point out:** The list of negative results, each linking back to its registry entry.

### Step 18 — Trace a rejected idea back to its registration

- **Narration:** Clicking a graveyard entry scrolls straight to the matching row in the registry, so the full lineage is one click away.
- **Action:** Click "factor-leadership_score-d10-h20 →"
- **Point out:** The registry row that scrolls into view for the clicked idea.

### Step 20 — See the broad, point-in-time universe

- **Narration:** The tracked universe isn't a fixed list — it changes over time, and the Data Manager shows exactly when each stock entered or left.
- **Action:** Navigate to /data
- **Point out:** The dynamic-universe membership timeline.

### Step 21 — Run an honest backfill

- **Narration:** Kicking off a backfill across the widened, 590-symbol fetch scope completes cleanly and reports exactly what it did.
- **Action:** Click the "Start" button
- **Point out:** The 'Snapshots backfilled' confirmation once the job finishes.

### Step 22 — See where the index and macro data comes from

- **Narration:** Every benchmark and macro series is labeled by its real data vendor, going back to 1996.
- **Action:** Navigate to /data
- **Point out:** The provenance table listing each index's source and earliest date.

### Step 23 — Watch for silent data drift

- **Narration:** The Data Manager also quietly checks whether freshly-pulled prices agree with the trusted, saved history, and flags it if anything was silently revised.
- **Action:** Navigate to /data
- **Point out:** The Live-vs-seed drift panel.

### Step 24 — See one trust strip, everywhere

- **Narration:** The same green verdict strip appears on every page, including the watchlist — one shared trust signal instead of a different check on each screen.
- **Action:** Navigate to /watchlist
- **Point out:** The quiet green 'GO' strip just below the header.
