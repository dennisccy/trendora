# Demo Script — goal-market-compass-iter-39

**Mode:** record
**Date:** 2026-09-02
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Open the Today page

- **Narration:** Welcome to the market compass — your ten-second read after the close. The Today page loads at the latest market data, showing the current regime, what changed since yesterday, and the top candidates worth monitoring.
- **Action:** Navigate to /
- **Point out:** The heading 'Today', the date badge showing the latest data, and the six cards below: Market state, Summary, What changed, Leadership rotation, Next-session focus, and Manifest strip.
- **Screenshot:** reports/demo/goal-market-compass-iter-39/step-01.png

### Step 02 — Check the market regime and breadth

- **Narration:** The Market state card at the top shows the current market regime, stress level, and market breadth. These three dimensions answer the first question: what is the overall market environment right now?
- **Action:** Click the "Market state" heading
- **Point out:** The regime (Risk-on or Risk-off), the market phase and severity line, and the breadth percentage. The 'Full market context' link navigates to the detailed market view.
- **Screenshot:** reports/demo/goal-market-compass-iter-39/step-02.png

### Step 03 — Read the plain-English summary

- **Narration:** The Summary card translates the market state into a single sentence that a non-analyst can understand. It names the regime, the market phase, the breadth direction, and how many candidates are worth monitoring today.
- **Action:** Click the "Summary" heading
- **Point out:** The summary sentence starting with the market regime, plus the 'Show cited facts' disclosure that reveals the exact numbers behind each claim.
- **Screenshot:** reports/demo/goal-market-compass-iter-39/step-03.png

### Step 04 — View the What changed card

- **Narration:** The 'What changed' card compares today's candidates to the previous session's selection. It breaks down the changes by category: market-wide winners and losers, then sectors, themes, and individual stocks that moved.
- **Action:** Click the "What changed" heading
- **Point out:** The comparison header showing the prior session date, and the ordered list of changes (Market, Breadth, Sectors, Themes, Stocks).
- **Screenshot:** reports/demo/goal-market-compass-iter-39/step-04.png

### Step 05 — See the leadership rotation

- **Narration:** The Leadership rotation card shows which candidates are moving in and out of the top selection. The board rotates as market conditions shift, and this card highlights the churn so you can spot emerging leaders.
- **Action:** Click the "Leadership rotation" heading
- **Point out:** Two sections showing candidates entering the selection (movers up) and candidates leaving (movers down), with the number of days each led the board.
- **Screenshot:** reports/demo/goal-market-compass-iter-39/step-05.png

### Step 06 — Explore the Next-session focus candidates

- **Narration:** The 'Next-session focus' card lists up to ten candidates worth monitoring. Each shows three evidence scores: leadership (past 60 days), entry quality (risk-adjusted return), and risk (downside volatility). Candidates who did not make the cut appear below in the 'Not priority' section with honest reasons why.
- **Action:** Click the "Next-session focus" heading
- **Point out:** The ten candidate cards with their three scores, and below that the 'Not priority' disclosure which expands to show why other candidates were passed over.
- **Screenshot:** reports/demo/goal-market-compass-iter-39/step-06.png

### Step 07 — Check a historical date — pre-fix manifest

- **Narration:** The Today page works on any stored historical date via the 'as_of' parameter. Navigate to August 11, which was stored before the new why-not reasons were computed. The page renders fully with an honest, degraded 'Not priority' note because that older stored session lacks the detailed held-back counts.
- **Action:** Navigate to /?asof=2026-08-11
- **Point out:** The page renders without crashing. The 'Not priority' disclosure now reads 'Not priority (20 shown — held-back counts unavailable for this manifest version)' instead of the fuller text that only exists on the newest date. Click to expand and confirm the entries render.
- **Screenshot:** reports/demo/goal-market-compass-iter-39/step-07.png

### Step 08 — Return to the frontier date and expand the full why-not list

- **Narration:** Back at the latest date (August 12), the 'Not priority' disclosure shows the full breakdown: 27 candidates excluded by the ten-candidate cap, and 25 more below the leadership floor. Click to expand and see both groups with honest reasons — those ranked 11-20 by leadership score are capped, and the near-misses show exactly how far below the threshold they fell.
- **Action:** Navigate to /?asof=2026-08-12
- **Point out:** The full 'Not priority' text showing the three counts. When expanded, at least one cap-excluded entry (showing 'ranked #N... cap 10') and at least one below-floor entry (showing the floor distance) are visible and fully readable.
- **Screenshot:** reports/demo/goal-market-compass-iter-39/step-08.png
