# Phase goal-mcp-loop-iter-2 — User-Visible Changes

**Phase:** goal-mcp-loop-iter-2
**Date:** 2026-06-30
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- On any stock's detail page (`/stocks/{ticker}`), expand a new **"Why proven?"** toggle on the Leadership score to read the exact statistical evidence behind the certification: the out-of-sample test result (PASS, holdout edge +6.36%, p-value 0.0004998, 12,297 sealed observations), the SPY benchmark comparison (+6.36% vs SPY), and the certified-claim id with registration date.
- Click **"View backing evidence row →"** inside the expanded proof panel to jump directly to the matching row on the Evidence ledger at `/evidence#signal-leadership_score`.
- Follow a full round-trip: Stocks leaderboard → stock-detail proof panel → Evidence ledger → back to Stocks leaderboard, with every hop linked.
- See a real **"Proven"** badge on the Leadership score on the Stocks leaderboard (`/stocks`) — the platform's first statistically certified score.
- See the populated **Leadership claim row** on the Evidence page (`/evidence`) with all five fields: Hypothesis, Out-of-sample verdict, SPY benchmark control, registration date, and forward-walk status.

---

## What Changed in the Visible UI

- The Leadership score badge on the Stocks leaderboard (`/stocks`) now reads **"Proven"** (accent green chip) instead of "Not yet proven". Clicking the badge navigates to `/evidence#signal-leadership_score`.
- The Leadership score badge on a stock's detail page (`/stocks/{ticker}`) now reads **"Proven"** for the same reason. A **"Why proven?"** disclosure button appears below it.
- Expanding the "Why proven?" disclosure on stock-detail reveals a proof panel with three labeled fields: **Out-of-sample test** (PASS chip + edge + p-value + cohort size), **Control comparison** (excess over SPY labeled "vs SPY (benchmark control)"), and **Certified claim** (signal id + registration date + link to evidence row).
- The Evidence page (`/evidence`) now shows a fully populated **`leadership_score` claim row** instead of the previous empty/no-claims state. The row includes a "Backs: Stocks leaderboard →" linkback.

---

## What Old Behavior Changed

- **Leadership score badge (everywhere):** Previously read "Not yet proven" on both the Stocks leaderboard and stock-detail because the evidence ledger was empty. Now reads "Proven" because the referee certified the first claim and appended it to the ledger.
- **Stock-detail score cards:** Previously showed only the score number and its status badge. Now, for the Proven Leadership score, an additional "Why proven?" toggle appears below the badge. Unproven scores (Entry Quality, Risk) are visually unchanged — no toggle, no panel.
- **Evidence page:** Previously showed no claim rows (empty state). Now shows one populated, certified claim row for Leadership.

---

## Not Visible Yet

- **Regime-conditioned evidence (J-04)** — the backend computes regime context for each score but there is no UI surface yet for viewing regime-sliced proof. Intentionally deferred to the next iteration to protect this first certification.
- **Entry Quality and Risk score proofs** — these scores remain honestly "Not yet proven" with no expandable panel. The proof-panel capability exists but only activates once the referee certifies a claim for those signals.
- **Additional benchmark controls (QQQ, sector ETF, same-sector random)** — the project roadmap calls for a richer control set but the referee certified only the SPY benchmark. The UI intentionally shows only what was computed.
