# Iteration 1 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The full pipeline ran cleanly and captured real browser evidence (closing the iter-0 gap): the read-side
evidence path is live end to end. Against the absent/empty ledger, every score on `/stocks` and stock-detail
honestly renders "Not yet proven" and the nav-reachable `/evidence` page shows an honest empty state — so J-01
and J-03 are newly verified passing and J-05's ledger surface is delivered. Nothing is presented as "Proven"
(no certified claim exists), no anti-goal was violated, and coherence passed — but J-02, J-04, and J-05's
populated-claim audit (steps 2-3) all need the first referee-certified claim, so the goal is not yet achieved.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Every score shows an evidence status | unknown | **passing** | reports/qa/goal-mcp-loop-iter-1-evidence/UT-02-result.png (120 rows, 3 "Not yet proven" chips/row, grades+scores intact) |
| J-02 Drill into the proof behind a score | unknown | unknown (deferred) | none — needs a referee-certified PASS claim; correctly out of scope this iter |
| J-03 Unproven / noise signals honestly marked | unknown | **passing** | reports/qa/goal-mcp-loop-iter-1-evidence/UT-08-result.png (MU detail: 94.58/23.66/53.11 each "Not yet proven", no confident "Proven") |
| J-04 Regime-conditioned evidence | unknown | unknown (deferred) | none — needs regime-scoped certified evidence; correctly out of scope this iter |
| J-05 Audit the evidence ledger | unknown | **partial** | reports/qa/goal-mcp-loop-iter-1-evidence/UT-06-07-result.png (Evidence nav 1 click, honest empty state, all 5 claim fields in markup) |

J-05 is **partial**, not passing: the ledger surface (nav ≤2 clicks, page renders, honest empty state, 5-field
claim-row layout, linkback text) is verified, but J-05 steps 2-3 — a populated claim row rendering its
hypothesis/verdict/control/date/score and the click-through claim→surface linkback — are not exercisable
against an empty ledger (zero claims). The spec's J-05 boundary note anticipates this: credit the ledger
surface now, mark the populated-claim linkback pending the first certified iteration.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No value shown as proven without a PASS certified-claim | OK | Ledger absent (`certified-claims.jsonl` does not exist) ⇒ empty payload; resolver marks `proven` only on `verdict.status == STATUS_PASS` AND a named signal; frontend `resolveEvidenceStatus` is fail-safe. Screenshots: every badge "Not yet proven", zero "Proven". |
| Decision-quality only; no return promises / price targets / buy-sell / orders | OK | Header reads "Research-only · decision support · no orders"; iter adds only status chips + a ledger page. No new order/target/alpha language. |
| Displayed numbers correct — match the engine (no recompute) | OK | Evidence read path never references scoring (`apps/backend/app/engine/evidence.py` reads ledger only); MU detail scores byte-identical to leaderboard (94.58/23.66/53.11); QA regression TC-16 confirms `/api/stocks` unchanged; badge is additive. |
| No overfit edges (referee-certified only) | OK (N/A) | Nothing surfaced as "Proven" this iter; no `## Evidence Claim` block ⇒ post-decompose gate passed automatically. |
| Preserve determinism / no-lookahead | OK | Read-side only; no scoring/forward-return computation changed. Forward returns still render NA where no post-date bars exist (UT-08), never fabricated. |
| No iteration ships if evidence-derived claims lack a passing referee verdict | OK (N/A) | No claims this iteration. |
| No hard-coded credentials / API keys / tokens in source | OK | Secret scan found only env-var NAMES (`FRED_API_KEY` etc.) in pre-existing config/data-import code + a doc comment; none in this iteration's new evidence files; no literal credential values. |

**Coherence:** COHERENCE-PASS (`runs/goal-session-mcp-loop/iter-1/coherence.md`) — single canonical module
(`build_evidence_payload`) + single endpoint (`GET /api/evidence`); no duplicate computation; `/evidence` in
the blueprint-approved IA home; top-level sidebar link (1 click). One advisory WARN (`SCORE_SIGNALS` duplicated
across `stocks/page.tsx` and `stocks/[ticker]/page.tsx`) — non-blocking. No structural veto.

## Next-Step Recommendation

Run iter-2 as the **first certified iteration** (full depth): propose a narrow, regime-conditioned machine-readable
`## Evidence Claim` JSON block that earns a referee **PASS** at the post-decompose gate (prefer a tight,
regime-scoped cohort — the referee counts independent holdout *dates*, not correlated same-date names, and
deflates for every claim ever tested). Two things must land together for the PASS to actually light up a badge:

1. **Wire the ledger writer to stamp `claim.signal`.** Per the dev handoff's known issue, the real
   `app.mcp.tools.verify_edge` appends a cohort-selector `claim` with **no `signal` key**, and the read side keys
   `proven_signals` on `claim.get("signal")` (fail-safe) — so even a genuine referee PASS would stay
   "Not yet proven" until the writer stamps the canonical signal key (`leadership_score` / `entry_quality_score`
   / `risk_score`). Closing this is the prerequisite for J-01's/J-02's "Proven" path to ever appear.
2. **Build the J-02 drill panel** on stock-detail: a "Proven" badge expanding to the out-of-sample test result,
   the control comparison (vs SPY/QQQ/sector/random), and the certified-claim id + registration date — read
   verbatim from `/api/evidence`.

That single certified iteration advances **J-02** (drill panel), completes **J-05** end-to-end (a populated
claim row + claim→surface linkback, steps 2-3), and lays the groundwork for **J-04** (label the claim with the
regime it holds in). Full depth is warranted because it ships a new "Proven" data surface gated by the referee
and adds new drill UI needing the browser-QA / ux-regression / closure lanes. Optionally fold in the coherence
WARN cleanup (extract `SCORE_SIGNALS` to `apps/frontend/lib/evidence.ts`) — advisory, not required.

## Halt Justification (if halting)

N/A — not halting. Progress was made (J-01, J-03 newly passing; J-05 surface delivered), no prior-passing
journey regressed, no critical anti-goal was violated, and a clear, tractable next step exists (certify the
first claim). Not GOAL_ACHIEVED because J-02/J-04 are deferred-unknown and J-05 is only partial.
