# Demo Script — goal-market-compass-iter-34

**Mode:** record
**Date:** 2026-09-01
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Today's market compass overview

- **Narration:** The homepage shows today's market state at a glance. You see the key metrics, what changed since yesterday, and next-session focus candidates stacked in a natural reading order.
- **Action:** Navigate to /
- **Point out:** The page displays the market-state band at top, the plain-English summary, a 'What changed' card comparing to the prior session, Leadership rotation, next-session candidates with their reasoning, and the frozen manifest strip at the bottom.
- **Screenshot:** reports/demo/goal-market-compass-iter-34/step-01.png

### Step 02 — Incident recovery: August 12th data serves cleanly

- **Narration:** August 12th was one of two dates deleted by an earlier data incident. Viewing this historical date now shows it has been recovered and renders without error.
- **Action:** Navigate to /?asof=2026-08-12
- **Point out:** The page loads cleanly showing 2026-08-12's market state in the tiles. The manifest strip at the bottom shows the basis as 'available' or 'rebuilt'—confirming this date is accessible again.
- **Screenshot:** reports/demo/goal-market-compass-iter-34/step-02.png

### Step 03 — Incident recovery: August 5th renders with honest basis state

- **Narration:** August 5th is another incident date whose manifest was previously orphaned. Viewing it now shows the page renders and displays an honest state about the data basis.
- **Action:** Navigate to /?asof=2026-08-05
- **Point out:** The manifest strip shows the correct basis state for this date—either 'available' if the underlying data was recovered, or an honest 'unknown' if the source remains unverified. There is no false claim.
- **Screenshot:** reports/demo/goal-market-compass-iter-34/step-03.png

### Step 04 — Return to today's view

- **Narration:** We navigate back to the latest data to explore how the system explains its reasoning and data sources.
- **Action:** Navigate to /
- **Point out:** The home page is now showing today's market state and focus candidates.
- **Screenshot:** reports/demo/goal-market-compass-iter-34/step-04.png

### Step 05 — Summary backs every statement with cited data

- **Narration:** The summary card explains the market state. When you expand it, every sentence shows which template it used and the exact data values that generated it.
- **Action:** Click the "Show cited facts" button
- **Point out:** Click 'Show cited facts' to reveal that each summary statement lists its template ID and the specific values (breadth counts, threshold levels, metrics) the system cited to generate that sentence. This shows the system does not invent reasoning.
- **Screenshot:** reports/demo/goal-market-compass-iter-34/step-05.png

### Step 06 — Market analysis tools show regime and breadth detail

- **Narration:** The market page houses tools too detailed for the homepage. Here you see the regime × market-phase cross-view chart and deeper breadth analysis.
- **Action:** Navigate to /market
- **Point out:** You'll see the regime × phase cross-view chart, glance tiles, three breadth breakdown cards, Top Sectors and Top Themes, Candidate Counts, and the full Market Phase & Severity breakdown—all the market-analysis tools in one comprehensive view.
- **Screenshot:** reports/demo/goal-market-compass-iter-34/step-06.png

### Step 07 — Sector attribution is honest and near-complete

- **Narration:** The stocks page lists every stock with its assigned sector. Sectors come from a two-source method: first a curated config, then a fallback for unmapped symbols.
- **Action:** Navigate to /stocks
- **Point out:** Select 'Unassigned' in the Sector filter. The unassigned count should be at most 5% of total members—never the old baseline of 78%. This shows the two-source attribution is working correctly.
- **Screenshot:** reports/demo/goal-market-compass-iter-34/step-07.png

### Step 08 — Methodology page explains data sources and scope

- **Narration:** The methodology page discloses how the system works. It explains the two-source sector approach and clarifies that sector history is current-only—there is no point-in-time historical data.
- **Action:** Navigate to /methodology
- **Point out:** The Universe/Data section lists both the curated config and pool-snapshot sources, and explicitly states sector assignments apply only to the current session. This transparency helps you understand what the data does and does not cover.
- **Screenshot:** reports/demo/goal-market-compass-iter-34/step-08.png
