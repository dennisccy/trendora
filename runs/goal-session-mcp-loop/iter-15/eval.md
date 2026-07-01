# Iteration 15 Evaluation

**Verdict:** GOAL_ACHIEVED
**Depth Recommendation For Next Iteration:** full

## Summary

The auto-appended continuous-improvement journey **J-09** (relative-strength `rs_spy_3m` top-decile @ the non-20 **60-day** horizon) is delivered: the pre-registered §4.1 #3 staging winner was promoted to the canonical ledger as **row 7** (PASS, Bonferroni divisor 7, `required_p≈0.007143`, `p=0.0004998`, edge +21.34%, register 2026-07-01) and surfaces automatically through the unchanged general matcher. I independently byte-confirmed the ledger row against the rendered `/evidence` money frame, verified `git diff HEAD` touches **zero app source** (only test files, the gate-appended ledger row, docs/blueprint/state), and re-confirmed J-01..J-08 non-regression. Every Must-have journey J-01..J-09 passes, no anti-goal is violated, and coherence is COHERENCE-PASS — the goal (as extended by J-09) is achieved.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Every score shows an evidence status | passing | passing | reports/qa/goal-mcp-loop-iter-15-evidence/TC-06-stocks-no-regression.png (inline Proven/Not-yet-proven per row; no rs_spy_3m leak) |
| J-02 Drill into the proof behind a score | passing | passing | reports/qa/goal-mcp-loop-iter-15-evidence/UT-01-initial.png (leadership_score PASS +6.36%, hypothesis+control+date, "Backs: Stocks leaderboard") |
| J-03 Unproven / noise honestly marked | passing | passing | UT-01-initial.png (ma_stack FAIL) + TC-06 (Entry Quality/Risk "Not yet proven") + UT-09 (rs_spy_3m h1/h5/h10/h20 data-proven=false) |
| J-04 Regime-conditioned evidence | passing | passing | UT-01-initial.png (Breakout-watch "Regime: Risk-on", PASS +6.12%) |
| J-05 Audit the evidence ledger | passing | passing | UT-01-initial.png (all 7 canonical rows with full standard fields) |
| J-06 vcp_contraction top-decile edge | passing | passing | UT-01-initial.png (vcp h20 PASS +3.33%) + UT-11 (factor-lab h20 data-proven=true) |
| J-07 Multi-horizon (vcp h60) edge | passing | passing | UT-01-initial.png (vcp h60 PASS +8.91%, "60-day hold") + UT-11 (factor-lab h60 data-proven=true) |
| J-08 Multi-factor combination edge | passing | passing | UT-01-initial.png (rs_spy_3m×high_proximity composite PASS +4.69%, ledger row 6 byte-identical) |
| **J-09 rs_spy_3m 60-day certified edge (TARGET)** | new | **passing** | UT-01-initial.png (row 7: PASS +21.34%, alpha/7=0.007143, register 2026-07-01, "Backs: Research factor lab") + UT-07 DOM (h60 data-proven=true/href correct; h1–h20 false) + byte-match certified-claims.jsonl:7 |

**J-09 note on visual evidence:** the `/evidence` row 7 money frame is pixel-confirmed in `UT-01-initial.png` (a distinct full-page capture the phase audit's F1 overlooked). The one un-pixeled element is the factor-lab "Proven" chip on the rs_spy_3m h60 cohort (all factor-lab captures are scrolled to the top-of-table Proximity/Risk rows), but it is grounded by the DOM+ledger+unit-test triangle the spec explicitly endorses: browser-qa DOM assertions (UT-07), unit cases ee/ff against the unedited `evidence.ts` general matcher (39/39), the byte-identical matcher that visibly lights vcp_contraction h20/h60 identically, and the confirmed `/evidence` row's linkback + deep-link anchor.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No "proven" without a passing certified-claim | OK | Row 7 is a genuine referee PASS; uncertified rs_spy_3m horizons h1/h5/h10/h20 read "Not yet proven" (UT-09) |
| Decision-quality only (no return/price/buy-sell/orders) | OK | Evidence + factor-lab show only evidence status + realized holdout statistic under "descriptive, not predictive · read the edge as an upper bound" framing |
| Displayed numbers correct (byte-match engine) | OK | Rendered +21.34% / alpha/7=0.007143 / p=0.0004998 / date 2026-07-01 byte-match certified-claims.jsonl:7 (independently read) |
| No overfit edges (survived the referee) | OK | Sealed OOS holdout + SPY control + Bonferroni divisor 7. The +0.2134 OOS≫in-sample (0.0204) yellow flag is honestly surfaced verbatim; engine magnitude is out of scope (determinism) — cleared by coherence + phase auditors as non-blocking, not a violation |
| Preserve determinism / no-lookahead | OK | `git diff HEAD` = zero app/engine/referee/ledger/config source change (byte-identical); referee/ledger expectation suites UNEDITED and green |
| No ship without passing referee verdict | OK | Post-decompose gate certified row 7 PASS before build; honest-stop guard did not fire (correct) |
| No hard-coded credentials | OK | No source change; nothing added |

`anti_goal_violations` remains `[]`.

## Next-Step Recommendation

Halt — the goal, as extended by the auto-appended J-09, is achieved. All nine Must-have journeys (J-01..J-09) pass with positive evidence. If the continuous-improvement loop extends the goal again, the next iteration should run **full**: a new canonical promotion tightens the user-facing Bonferroni bar 7→8 permanently and needs the audit/closure/ux-regression guards that scrutinized this iteration's yellow flag. Route any new candidate through the **staging** ledger first, set `"ledger":"canonical"` explicitly only on a deliberately promoted winner (iter-9b/10 footgun), and honor the honest-stop guard on any non-PASS.

## Halt Justification

GOAL_ACHIEVED. Every Must-have user journey (J-01..J-09) has status `passing` with positive, independently-verified evidence; the target J-09 is newly passing (certified ledger row 7, byte-matched to the rendered `/evidence` row). No anti-goal is violated (`anti_goal_violations` = `[]`) — the +0.2134 magnitude is a documented, honestly-surfaced yellow flag whose root cause (seeded data / engine) is explicitly out of scope, not a violation. This iteration's coherence audit is **COHERENCE-PASS** (no duplicate computation, no non-canonical source, no new page/route, all surfaces on existing IA homes). With zero app-source diff, J-01..J-08 have no regression mechanism and are all re-verified. The three GOAL_ACHIEVED conditions are met, so the loop halts with success.

## Carry-Forward (non-blocking)

1. **Screenshot hygiene (recurring iter-11/13/14/15):** the browser-qa lane keeps emitting 5855-byte blank scrolled-headless frames and reused top-of-table captures; a future hardening pass should element-clip the actual asserted "Proven" chip / ledger row (or fail the capture) so the pixel artifact matches the (correct) DOM assertions.
2. **Yellow-flag magnitude:** the +0.2134 OOS edge (~10× its in-sample edge) is a seeded-data/engine characteristic worth a dedicated look IF the engine ever comes into scope — strictly out of scope now (determinism).
