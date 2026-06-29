# Phase goal-mcp-loop-iter-1 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-1
**Date:** 2026-06-29
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- See an evidence status chip ("Not yet proven") next to every Leadership, Entry Quality, and Risk score on the Stocks leaderboard at `/stocks` — the chip appears below each score badge on every row.
- See an evidence status chip ("Not yet proven") beneath each score value (Leadership, Entry Quality, Risk) on a stock's detail page at `/stocks/<ticker>`.
- Open the certified-claims ledger by clicking "Evidence" in the left navigation sidebar — reachable in one click from any page.
- Read the honest empty state on the Evidence page (`/evidence`) — "No certified claims yet — every signal currently reads Not yet proven" — which lists the five fields each future certified claim will show (Hypothesis, Out-of-sample verdict, Control comparison vs SPY, Registration date, Forward-walk score-to-date).
- (Once a certified claim exists) Click a "Proven" badge on any score to jump directly to its backing claim row on the Evidence page.
- (Once a certified claim exists) Click the "Backs: Stocks leaderboard →" linkback inside a claim row to return to the leaderboard surface the claim backs.

---

## What Changed in the Visible UI

- Every row on the Stocks leaderboard (`/stocks`) now shows a small "Not yet proven" chip (Shield icon, muted style) placed below each of the three score badges (Leadership, Entry Quality, Risk). Previously each score showed only its letter grade and numeric value; the chip is purely additive — it does not move or replace any existing element.
- Each `ScoreCard` on a stock detail page (`/stocks/<ticker>`) now shows a "Not yet proven" chip beneath the numeric score. The three ScoreCard blocks (Leadership, Entry Quality, Risk) all carry the chip.
- The left navigation sidebar now includes an "Evidence" entry (ShieldCheck icon) inserted after "Research". It is visible on every page without scrolling.
- A new page exists at `/evidence`: it shows a page heading with title "Evidence" and subtitle explaining the certified-claims ledger, a loading skeleton while the data loads, a styled error card if the backend is unreachable, and the honest empty-state card when (as today) no claims have been certified.

---

## What Old Behavior Changed

- Stocks leaderboard score columns: previously each score column showed only the letter-grade `ScoreBadge` and its numeric value. Each column now ADDITIONALLY shows an `EvidenceStatusBadge` chip directly below the existing badge. Scores, letter grades, and row ordering are byte-identical to before.
- Stock detail page ScoreCard: previously each ScoreCard showed a score value, label, and description. It now additionally shows an evidence-status chip beneath the score value. All other content in each ScoreCard is unchanged.

---

## Not Visible Yet

- "Proven" badge linking to its backing claim entry on the Evidence page: the link code and anchor targets (`#signal-<key>`) are built and unit-tested, but cannot be exercised until at least one certified claim exists in the ledger (the ledger is empty this iteration — every badge reads "Not yet proven").
- Claim→surface linkbacks on the Evidence page claim rows: built and unit-tested, but not exercisable end-to-end until a claim is certified.
- Evidence status badges on `/sectors`, `/themes`, and Research lab pages: explicitly out of scope this iteration; deferred to a later iteration that extends the same badge to those surfaces.
