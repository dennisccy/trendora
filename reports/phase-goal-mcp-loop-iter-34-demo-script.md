# Demo Script — goal-mcp-loop-iter-34

**Mode:** record
**Date:** 2026-07-14
**Frontend URL:** http://localhost:3255
**Iteration:** 34

## Highlights

### Step 01 — Open the dashboard

- **Narration:** Every page opens with one simple answer: is today's board safe to rely on? A quiet green strip right under the header gives the verdict before you look at anything else.
- **Action:** Navigate to /
- **Point out:** The green "GO — today's board is current." strip just below the header.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-34/step-01.png

### Step 02 — Browse the stock leaderboard

- **Narration:** The leaderboard ranks hundreds of companies, and every score carries an honest evidence status instead of a bare number.
- **Action:** Click the "Stocks" link
- **Point out:** 541 of 541 candidates scored, each showing a plain "Not yet proven" badge next to its signal.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-34/step-02.png

### Step 03 — Drill into one stock's evidence

- **Narration:** Opening a single name like NVDA carries the same honesty right down to the individual stock page — nothing gets dressed up once you zoom in.
- **Action:** Navigate to /stocks/NVDA
- **Point out:** The "Not yet proven" evidence status sitting right next to NVDA's scores.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-34/step-03.png

### Step 04 — See up to thirty years of price history

- **Narration:** One click on the chart's full-range control reveals nearly three decades of price history for this stock, honestly bounded to what actually exists for the name.
- **Action:** Click "chart-range-full"
- **Point out:** The chart redraws to 3,025 daily bars — close to thirty years of history.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-34/step-04.png

### Step 05 — Audit the evidence ledger

- **Narration:** The Evidence page is the single source of truth for every trading idea ever tested, including the honest record of the ones that didn't hold up.
- **Action:** Click the "Evidence" link
- **Point out:** The leadership_score entry, plainly marked FAIL with its real -0.03% out-of-sample result and test date.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-34/step-05.png

### Step 06 — Check how much of the market is covered

- **Narration:** The Data Manager page shows exactly how wide and how current the underlying dataset is, in plain numbers.
- **Action:** Click the "Data Manager" link
- **Point out:** 590 symbols tracked, with the full coverage panel laid out underneath.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-34/step-06.png

### Step 07 — Open the research hub

- **Narration:** The Research hub is where the deeper bookkeeping lives — how much testing budget remains, and every idea ever put on record.
- **Action:** Click the "Research" link
- **Point out:** A "Certification-budget accounting" card sitting alongside the research labs.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-34/step-07.png

### Step 08 — See the statistics budget before it's spent

- **Narration:** One click into the budget panel shows exactly how much statistical rigor has been used so far, and how much is left before the next idea can be tested.
- **Action:** Click "research-governance-link-budget"
- **Point out:** The trial counter reading "Next canonical trial will be #8," next to the required-significance and remaining-budget figures.
- **Screenshot:** reports/demo/goal-mcp-loop-iter-34/step-08.png

## Full tour (text only)

### Step 09 — Your watchlist carries the same guarantee

- **Narration:** A personal shortlist gets covered by the exact same daily check as every other page — nothing is exempt.
- **Action:** Click the "Watchlist" link
- **Point out:** The identical GO strip sitting above the watchlist table.

### Step 10 — Evidence that knows the market's mood

- **Narration:** Back on the Evidence page, a different kind of check shows up: some ideas are only ever tested inside one kind of market, and the ledger keeps track of exactly which one.
- **Action:** Navigate to /evidence
- **Point out:** A "Regime: Risk-on" tag on the Breakout-watch entry, still honestly marked FAIL.

### Step 11 — Combined signals get tested too

- **Narration:** It's not just single signals under the microscope — pairing two ideas together is held to the exact same bar.
- **Action:** Navigate to /evidence
- **Point out:** The "rs_spy_3m × high_proximity — composite" entry, tested together and still marked FAIL.

### Step 12 — A broad, point-in-time universe

- **Narration:** Back on the Data Manager page, the candidate list isn't a fixed set frozen in time — it's tracked as it actually changed across the full thirty-year history.
- **Action:** Navigate to /data
- **Point out:** The dynamic-universe membership timeline underneath the coverage numbers.

### Step 13 — Decades of market context, each one sourced

- **Narration:** Index and macro context go just as deep as the stock data, and every series is labeled with exactly where it came from.
- **Action:** Navigate to /data
- **Point out:** The "Index & benchmark data provenance" panel, naming each vendor down to the FRED-sourced macro proxy.

### Step 14 — Every registered idea, discoverable in one place

- **Narration:** Before any idea can be tested, it has to be written down first — and that registry is one click away from the research hub.
- **Action:** Navigate to /research
- **Point out:** A "Pre-registration registry" link sitting on the Research hub page.

### Step 15 — Open the pre-registration registry

- **Narration:** Opening the registry shows every hypothesis exactly as it was written down before testing began — nothing gets added after the fact.
- **Action:** Click the "Pre-registration registry" link
- **Point out:** The registered vcp_contraction hypothesis, with its selectors and registration date.

### Step 16 — Browse the rejected-ideas graveyard

- **Narration:** Every idea that didn't survive testing stays on record too, so nobody wastes time re-testing something already ruled out.
- **Action:** Navigate to /research/graveyard
- **Point out:** The negative-results graveyard listing every rejected hypothesis.

### Step 17 — Jump from a rejected idea straight to its record

- **Narration:** Clicking a rejected idea in the graveyard jumps straight to its exact entry in the registry — the two records stay linked, not just filed separately.
- **Action:** Click "factor-leadership_score-d10-h20 →"
- **Point out:** The registry scrolling to and highlighting the matching leadership_score entry.
