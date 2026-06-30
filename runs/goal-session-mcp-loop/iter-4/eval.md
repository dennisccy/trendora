# Iteration 4 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

J-04's regime-conditioned-evidence feature is genuinely built, gate-certified, and visually
confirmed working: the post-decompose gate PASSED the Breakout-watch × Risk-on event-study claim
(2nd `certified-claims.jsonl` entry, holdout +6.12% vs SPY, p=0.0004998 < alpha/2=0.025), and the QA
agent's own Chrome MCP lane captured two real screenshots (TC-01 Dashboard Risk-on 76.05 + "See
evidence proven in this regime →"; TC-03 `/evidence` "Regime: Risk-on" row with byte-correct values).
**However GOAL_ACHIEVED is withheld**: the canonical **browser-qa-agent** lane SKIPPED all 11 tests
(stale `next-server` held :3255 → "frontend not running"), so three of five journeys (J-01/J-02/J-03)
have no fresh iter-4 pixels, and the spec-required **post-QA audit handoff is absent**
(`current_step=qa_complete`). This is the exact iter-0/iter-2 pattern the spec's own embedded lesson
flags as a HARD verification gap — one clean canonical re-verification + audit pass makes the terminal
GOAL_ACHIEVED decisive.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Every score shows an evidence status | passing | passing (carried — code path untouched; QA-textual reconfirm TC-07; **no fresh iter-4 pixel**) | reports/qa/goal-mcp-loop-iter-3-evidence/UT-02-result.png |
| J-02 Drill into the proof behind a score | passing | passing (carried — ScoreProofPanel untouched; QA-textual reconfirm TC-08; **no fresh iter-4 pixel**) | reports/qa/goal-mcp-loop-iter-3-evidence/UT-08-proof-panel.png |
| J-03 Unproven / noise signals honestly marked | passing | passing (carried — proven_signals unchanged, unit-tested; **no fresh iter-4 pixel**) | reports/qa/goal-mcp-loop-iter-3-evidence/UT-06-result.png |
| J-04 Regime-conditioned evidence | unknown | **partial** (feature delivered + gate-certified + QA-lane-verified; canonical browser-qa lane SKIPPED → session-standard verification incomplete) | reports/qa/goal-mcp-loop-iter-4-evidence/TC-03-evidence-regime-label.png, TC-01-dashboard-regime.png |
| J-05 Audit the evidence ledger | passing | passing (fresh TC-03: leadership row byte-unchanged, "Backs: Stocks leaderboard →"; new regime row did not break the list) | reports/qa/goal-mcp-loop-iter-4-evidence/TC-03-evidence-regime-label.png |

### J-04 evidence detail (personally inspected)
- **TC-01-dashboard-regime.png** — Dashboard Market Regime card reads **Risk-on / 76.05 / 100**, with
  the **"See evidence proven in this regime →"** affordance directly below the regime breakdown. Page is
  fully populated (Ready, 162 symbols, regime×phase cross-view, SOXX 93.67). J-04 step 1 + affordance. ✅
- **TC-03-evidence-regime-label.png** — `/evidence` 2nd row: **"PASS  Breakout-watch setup  [Regime:
  Risk-on]"**, subtitle "Out-of-sample edge in the Risk-on regime", hypothesis chips
  (kind=event-study, regime=Risk-on, slice_kind=regime, subject=Breakout-watch, view=pooled,
  horizon=20, direction=positive), OUT-OF-SAMPLE VERDICT "PASS · holdout edge **+6.12%**" /
  "(p=0.0004998 < alpha/2=0.025)", CONTROL (VS SPY) **+6.12%**, REGISTRATION DATE **2026-06-30**,
  "Backs: **Research event-study lab** →". J-04 steps 2–3 (regime-scoped + clearly labeled). ✅
- **Byte-correctness cross-check vs `certified-claims.jsonl` line 2**: holdout_edge
  0.06124590639955655 → "+6.12%" ✓; control_excess 0.06124590639955655 vs SPY ✓; p_value
  0.0004997501249375312 → "0.0004998" ✓; deflation_divisor 2 → "alpha/2=0.025" ✓; register_date
  2026-06-30 ✓. Displayed numbers match the engine/ledger — anti-goal #3 satisfied for this row.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Nothing uncertified reads "Proven"/confident | OK | proven_signals keyed **only** on leadership_score (unit-tested `test_build_payload_regime_event_study_claim_adds_no_signal`); the regime claim carries `signal=null` → standalone claim row, lights no inline badge; gate PASS for the claim. |
| Decision-quality only — no buy/sell/price-target/return promise | OK | Only "buy/sell" match in the diff is a guard comment ("never a buy/sell or return promise (anti-goal #2)"). Row framed as "Out-of-sample edge in the Risk-on regime"; header still "Research-only · decision support · no orders". |
| Displayed numbers correct (match engine/ledger) | OK | TC-03 values byte-identical to certified-claims.jsonl line 2 (see J-04 cross-check) and leadership row (+6.36%, alpha/1=0.05) matches line 1. |
| No overfit edges — referee-certified only | OK | gate-post-decompose.json blocked=false; sealed temporal holdout 107 dates / 277 in-sample, same-dates SPY control n=414, bonferroni deflation, p=0.0004998 < required 0.025. |
| Preserve determinism / no-lookahead | OK | Zero `apps/backend/app/**` diff; zero engine/referee/endpoint diff. Frontend is pure read-only re-display. |
| No iteration ships uncertified evidence claims | OK | The one Evidence Claim earned a referee PASS at the post-decompose gate before code. |
| No hard-coded credentials/keys/tokens | OK | Secret scan over the apps/ diff clean. |

Coherence: **COHERENCE-PASS** (`runs/goal-session-mcp-loop/iter-4/coherence.md`) — no Data-Contract
duplication (regime label read verbatim; `resolveEvidenceStatus` unchanged), no IA drift (no new
pages/nav; `/evidence` + `/` both 1-click). No structural veto.

## Next-Step Recommendation

iter-5 (full) = the final, decisive verification pass — **no new feature code** beyond a harness fix.
1. **Free :3255 before the browser-qa lane binds** (kill any orphan `next-server`; the dev handoff
   flagged this — `start-frontend.sh` does not `fuser -k` the port before binding, unlike `dev.sh`).
   This is the root cause of the canonical lane's all-SKIP; fix it so the lane actually renders.
2. **Capture fresh canonical (UT-*) screenshots for ALL FIVE journeys** through the browser-qa-agent:
   - J-04 — Dashboard Risk-on + affordance → `/evidence` "Regime: Risk-on" row (scroll the 2nd row
     into frame before capture — iter-3 lesson), values matching `GET /api/evidence`.
   - J-05 — leadership row + "Backs: Stocks leaderboard →" linkback round-trip; new row doesn't break list.
   - **J-01 / J-03 — `/stocks`**: every score shows a status; Leadership "Proven", Entry Quality + Risk
     "Not yet proven" (these are the journeys with NO fresh iter-4 pixel — capture them).
   - **J-02 — `/stocks/{ticker}`**: Leadership proof drill-down (OOS test / SPY control / claim id+date).
3. **Produce the post-QA audit handoff** at `docs/handoffs/goal-mcp-loop-iter-5-audit.md` (the iter-3 +
   iter-4 process gap — the audit stage has stopped at `qa_complete` twice; the terminal run must
   complete it before declaring victory).
4. Optional carry: add `tsx` frontend devDependency (reviewer NOTE, iter-3/iter-4) through the
   supply-chain gate so `node lib/*.test.ts` runs without the tsc-transpile workaround.

On a clean full run with five fresh canonical screenshots + an audit handoff, **all five Must-have
journeys are green through the session-standard lane and GOAL_ACHIEVED is reachable.**

## Halt Justification (if halting)

Not halting. CONTINUE — clear forward progress (the session's first regime-conditioned edge certified
and surfaced; J-04 feature delivered and visually confirmed), with one tractable, low-cost
verification-integrity gap to close. Not GOAL_ACHIEVED: the canonical browser-qa lane SKIPPED (the
iter-0/iter-2 hard-gap pattern the spec's embedded lesson forbids treating as sufficient), J-01/J-02/J-03
lack fresh iter-4 pixels, and the spec-required audit handoff is absent — too thin a verification base
for the terminal success verdict. Not REGRESSION (no prior-passing journey broke; J-05 verified
byte-unchanged; J-01/J-02/J-03 code paths untouched; no critical anti-goal violated). Not STALLED
(real progress every iteration; the next step is concrete and cheap).
