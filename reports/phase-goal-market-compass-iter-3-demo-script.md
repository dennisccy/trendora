# Demo Script — goal-market-compass-iter-3

**Mode:** record
**Date:** 2026-08-20
**Frontend URL:** http://localhost:3255

## Highlights

### Step 01 — Open the Dashboard

- **Narration:** Let's start at the Dashboard home page. This iteration adds a new Manifest card that proves each close's decision was frozen, stamped, and exported — visible right on the page, no navigation needed.
- **Action:** Navigate to /
- **Point out:** Scroll down and you'll see four compass cards in order: Summary, What changed, Next-session focus, and the new Manifest card. Notice the Manifest sits above the older Market Regime and Market Phase charts — it's discoverable by scrolling alone.
- **Screenshot:** reports/demo/goal-market-compass-iter-3/step-01.png

### Step 02 — Step to a historical trading date

- **Narration:** We'll click the back arrow to view a specific past date. The Manifest card becomes fully visible with all its freeze-and-stamp details when viewing a stored historical close.
- **Action:** Click "[data-testid='asof-step-prev']"
- **Point out:** The date badge in the top bar changes from 'Latest' to 'Viewing as-of' with a specific date and '(historical)' label. That tells you the page is now showing a locked, past snapshot.
- **Screenshot:** reports/demo/goal-market-compass-iter-3/step-02.png

### Step 03 — See the Manifest's freeze-and-stamp proof  [NEW]

- **Narration:** Now the Manifest card shows its full proof: badges saying this data was frozen and stamped, plus four hash chips that prevent tampering. Each hash is a cryptographic identity of the rules and config used.
- **Action:** Click "html"
- **Point out:** Look at the badges — you'll see mode ('retrospective' or 'at ingest'), version number, a 'frozen' badge, and a 'prospective-eligible' or 'not prospective-eligible' status. Below that are four hash chips labeled Engine identity, Candidate rule, Cohort rule, and Manifest config. Hover over a hash chip's truncated value to see the full hash in a tooltip.
- **Screenshot:** reports/demo/goal-market-compass-iter-3/step-03.png

### Step 04 — Expand the audit table to see all candidates and near-misses  [NEW]

- **Narration:** Inside the Manifest card is an expandable audit table that shows every decision: which stocks were selected as candidates, which were rejected and why, and which scored just below the bar (research-only shadow list).
- **Action:** Click "Audit table"
- **Point out:** Click the 'Audit table' row to expand it. You'll see the comparison cohort — the rejected stocks, each marked either 'below selection floor' or 'excluded by cap' — and below that a separate 'Near-threshold shadow' section marked explicitly as research-only. Every row carries the stock's frozen scores and context from that close.
- **Screenshot:** reports/demo/goal-market-compass-iter-3/step-04.png

### Step 05 — Open the Regenerate confirmation modal  [NEW]

- **Narration:** The Manifest card offers a Regenerate button for historical dates. This lets us mint an explicit new version of that date's manifest under today's rules — without ever touching or hiding the original. A confirmation modal explains the contract.
- **Action:** Click "[data-testid='compass-manifest-regenerate-button']"
- **Point out:** Click 'Regenerate manifest' (amber button with refresh icon). A modal opens with the heading 'Confirm manifest regenerate'. Read the body text — it clearly states 'This mints a NEW manifest version for [date]' and 'The existing version is never touched, changed, or deleted.' This is the immutability guarantee at work.
- **Screenshot:** reports/demo/goal-market-compass-iter-3/step-05.png

### Step 06 — Confirm to create a new manifest version  [NEW]

- **Narration:** We'll click Confirm in the modal to mint version 2 for this same date. After confirmation, you'll see the version badge increment and a new Versions list showing both versions side by side — proof that each version is separate and preserved.
- **Action:** Click "[data-testid='compass-manifest-regenerate-confirm-button']"
- **Point out:** The modal closes (no page reload), and the Manifest card's version badge jumps from 1 to 2. The 'prospective-eligible' badge now reads 'not prospective-eligible' (regenerated versions are never eligible). A new 'Versions' section appears below showing both versions with their timestamps and badges.
- **Screenshot:** reports/demo/goal-market-compass-iter-3/step-06.png

### Step 07 — Summary card shows clean, rounded numbers  [NEW]

- **Narration:** A smaller but important fix this iteration: the Summary card's 'Show cited facts' disclosure used to occasionally render raw floating-point artifacts. Now every numeric value rounds cleanly to exactly two decimal places.
- **Action:** Click "Show cited facts"
- **Point out:** Scroll back up to the Summary card (the first compass card) and click 'Show cited facts' to expand it. You'll see cited facts like regime_score 73.24, severity 25.84, breadth 59.84, breadth_above_200dma 66.39 — all cleanly rounded, never raw float strings like '6.2700000000000005'.
- **Screenshot:** reports/demo/goal-market-compass-iter-3/step-07.png

### Step 08 — Risk caution is factual, not prescriptive  [NEW]

- **Narration:** Another refinement: the ATR risk caution on candidate cards used to sound prescriptive ('sized risk accordingly'). Now it states the fact only — the percentile, nothing else. Honest risk disclosure, no advice.
- **Action:** Click "html"
- **Point out:** Scroll down to Next-session focus and find a candidate card that has a caution section. Look for an 'ATR_RISK_BUDGET:' line. It now reads something like 'ATR is 2.99% of price (p6 of universe).' — a fact, ending with the percentile, no advice-sounding tail.
- **Screenshot:** reports/demo/goal-market-compass-iter-3/step-08.png
