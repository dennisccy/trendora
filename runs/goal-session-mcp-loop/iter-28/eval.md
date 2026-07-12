# Iteration 28 Evaluation

**Verdict:** STALLED
**Depth Recommendation For Next Iteration:** full

## Summary

iter-28 was a deliberate zero-code plateau-assessment pass. It shipped no product source, no
data-model change, and — load-bearingly — no `## Evidence Claim`, establishing with recorded
referee evidence that the five sanctioned-partial evidence journeys (J-02/J-06/J-07/J-08/J-09)
have **no promotable edge** on the 30-year basis: the complete pre-registered candidate set
(`proposer-guidance.md` §4.1 four singles + §4.2 three combinations) is empirically exhausted —
all 7 canonical + 7 staging entries FAIL, six of seven staging members wrong-direction, the best
right-direction candidate far from any bar. The only remaining unblock for these journeys is a
**human** revision of the pre-registered candidate registry (`docs/goal.md` §4.1/§4.2 /
`proposer-guidance.md`) or a goal.md re-scope. Every other journey (J-01/J-03/J-04/J-05/J-10/J-11/
J-13 replayed green; J-12/J-14/J-15/J-16 carried on byte-identity) is passing, coherence is PASS,
scan is CLEAN, and no anti-goal is violated — but with no autonomous, in-scope, journey-advancing
work available, this halts STALLED for a human decision (iter-16 precedent).

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing | reports/qa/goal-mcp-loop-iter-28-evidence/UT-J-01-stocks-leaderboard.png (evaluator opened: 541/541, every score 'Not yet proven', no crash) |
| J-02 | partial | partial | reports/qa/goal-mcp-loop-iter-28-evidence/UT-J-02-J-05-J-06-J-07-J-09-evidence-ledger-full.png (no Proven badge exists to drill; honest-status half only) |
| J-03 | passing | passing | reports/qa/goal-mcp-loop-iter-28-evidence/J-03-verify.png (replay green) |
| J-04 | passing | passing | reports/qa/goal-mcp-loop-iter-28-evidence/J-04-verify.png (replay green) |
| J-05 | passing | passing | reports/qa/goal-mcp-loop-iter-28-evidence/UT-J-02-J-05-J-06-J-07-J-09-evidence-ledger-full.png (evaluator opened: 7/7 FAIL cards, numbers byte-match ledger) |
| J-06 | partial | partial | same /evidence full-page: vcp_contraction D10 FAIL -0.38%; factor-lab data-proven=false |
| J-07 | partial | partial | same /evidence full-page: vcp_contraction h60 FAIL -1.64%; factor-lab all horizons data-proven=false |
| J-08 | partial | partial | reports/qa/goal-mcp-loop-iter-28-evidence/UT-J-08-combo-configured-recheck.png (composite FAIL +0.01%, data-proven=false) |
| J-09 | partial | partial | same /evidence full-page: rs_spy_3m h60 FAIL -1.42%; no stale +21.34% anywhere |
| J-10 | passing | passing | reports/qa/goal-mcp-loop-iter-28-evidence/J-10-verify.png (replay green) |
| J-11 | passing | passing | reports/qa/goal-mcp-loop-iter-28-evidence/UT-J-02-J-05-J-06-J-07-J-09-evidence-ledger-full.png (0 PASS -> no stale edge; ledgers byte-unmodified) |
| J-12 | passing | passing (carried) | byte-identity (universe-resolver untouched; git diff HEAD empty); last pixel iter-27 |
| J-13 | passing | passing | reports/qa/goal-mcp-loop-iter-28-evidence/J-13-verify.png (replay green) |
| J-14 | passing | passing (carried) | byte-identity (index_chart config + chart components untouched); last pixel iter-25 |
| J-15 | passing | passing (carried) | byte-identity (zero source/config diff -> no perf-regression mechanism); last measured iter-27 |
| J-16 | passing | passing (carried) | byte-identity (memory-hardening data-path byte-identity-gated, untouched); iter-26 crash resolved=true |

**Skeptical finding on the browser-qa over-claim (non-verdict-changing):** the browser-qa lane
went beyond the required set and marked J-02/J-06/J-07/J-08/J-09 "PASS (see note)". I do NOT
accept those as `passing`. Each journey's acceptance criterion requires a *Proven* certified edge
to be surfaced/drilled; the ledger is all-FAIL (0 PASS, verified on disk and in the md5-distinct
/evidence screenshot I opened), so what the lane actually verified is the honest-status half only
(badges correctly read "Not yet proven", numbers byte-match the FAIL verdicts) = anti-goal #1
upheld, not full journey acceptance. Consistent with 10 prior iterations, they stay `partial`.
(Screenshot-hygiene note, recurring session lesson: J-02/J-05/J-06/J-07/J-08-verify.png collapse
to one md5 `71414b78`, and J-10/J-11-verify.png share a md5 — reused replay frames; non-blocking
here because I confirmed zero product diff (no regression mechanism) and grounded the crux on the
md5-distinct /evidence full-page frame + the on-disk ledgers.)

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| #1 Nothing shown as proven/confident unless backed by a passing certified-claim | OK | 0 PASS in either ledger (verified on disk); /evidence and /stocks show only "Not yet proven"; `proven_signals={}` |
| #2 No return promises / price targets / buy-sell / orders | OK | "Research-only · decision support · no orders" header; zero product diff; no new copy |
| #3 Displayed numbers correct (byte-match engine) | OK | 7 ledger cards byte-match certified-claims.jsonl read directly (e.g. leadership -0.0003136 -> -0.03%, combo +8.03e-05 -> +0.01%) |
| #4 No overfit edges surfaced as proven | OK | all-FAIL ledger; nothing surfaced as proven |
| #5 Determinism + no-lookahead preserved | OK | zero engine/scoring source diff (git diff HEAD empty on apps/backend/app) |
| #6 No iteration ships evidence-derived claims lacking a passing referee verdict | OK | no `## Evidence Claim` registered (grep-verified; DoD); post-decompose gate auto-passes; divisor stays 8 |
| #7 No hard-coded credentials/keys/tokens in source | OK | scan-report.md CLEAN (product diff, bookkeeping path-excluded); zero product source diff |
| #8 Resilience to data-shape/scale change (no crash/OOM, graceful degrade) | OK | both prior violations (iter-24, iter-26) resolved=true; no new crash — /stocks 541/541, /evidence, /data all render; browser-qa PASS; zero product diff |

Coherence: **COHERENCE-PASS** (no structural veto — verify-only pass, no IA/data-contract change;
confirmed apps/**, config.yaml, data/seed, both ledgers byte-identical to snapshot). Review: **PASS**
(no fail-open — the pipeline did not proceed past a failing review).

## Next-Step Recommendation

The path to advancing J-02/J-06/J-07/J-08/J-09 is **human-owned**. Present the operator the menu:

1. **Widen/revise the pre-registered candidate registry** (`docs/goal.md` §4.1/§4.2 /
   `proposer-guidance.md`) — e.g. open the goal.md-deferred, explicitly-human-authored families
   (quantile spreads D10−D1, regime-conditioning, sector cohorts). The anti-data-mining keystone
   reserves candidate-set authorship to the human; an autonomous agent may not fabricate a new
   hypothesis, and re-submitting any of the 14 closed FAILs only tightens the Bonferroni divisor
   (8→9→…) for no possible gain (lessons iter-8/10/12).
2. **Amend `docs/goal.md`** to re-scope the five journeys to accept the honest all-FAIL ledger as
   their terminal contract (the honest-status half is already satisfied; what is absent is a
   *Proven* row to drill, which requires a real certified edge that does not exist on this basis).

On `--resume` after option 1: the next iteration runs **FULL** — it would ship a referee-gated
canonical claim (a genuine new-basis staging winner promoted with explicit `"ledger":"canonical"`)
that needs the audit / ux-regression / closure guards, and must honor the honest-stop guard
(promote only a winner clearing divisor-8 with margin; report, don't force, if none clears).

## Halt Justification

STALLED per decision-tree rule 2: **every unblock path for the current blocker is a human-owned
action.** The five target journeys can only advance via a certified edge; the complete
pre-registered candidate set is empirically exhausted (7 canonical + 7 staging entries, all FAIL —
I read both ledgers on disk and opened the md5-distinct /evidence screenshot confirming it), so no
autonomous, in-scope evidence move exists (re-submitting a closed hypothesis is forbidden and
self-defeating; authoring a new blind candidate violates the anti-data-mining keystone). The only
remaining unblock is a human revision of the human-owned candidate registry or a goal.md
re-scope — matching the iter-16 STALLED-with-menu precedent. Not GOAL_ACHIEVED (five journeys are
`partial`, not passing — no Proven edge to drill/surface). Not REGRESSION (no passing→failing; both
prior critical anti-goal violations resolved=true; no new violation; zero product diff). Not
CONTINUE (no journey newly passing, and the remaining partials are not autonomously tractable — the
tree puts STALLED before CONTINUE; perf polish on already-passing J-15/J-16 would be manufactured
work). Not ESCALATE (review PASSED, no fail-open; no journey failed 2 consecutive iters as
`failing`; the full pipeline cannot resolve a human-owned candidate-set decision).
