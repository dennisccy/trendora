# Iteration 37 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

iter-37 is the lean, verification-only closeout the iter-36 CONTINUE asked for: it ran the
deterministic golden-script regression replay that a FULL iteration structurally skips
(`run-phase.sh` has no replay lane — only `goal-iter-lean.sh` does), formally re-verifying all 20
built, golden-scripted journeys with **zero** product change and closing the iter-36 CLOSURE-FAIL
replay gap. The replay produced `regression-replay-results.md` (the artifact iter-36's full path
never wrote): 18/18 deterministic PASS over the Required-still-passing set — folding in J-21.json
(iter-35) and J-22.json (iter-36) for the first time — while the two closure-named Targets J-05 and
J-11 got a dedicated LLM browser-qa live walk plus a linted/replayed golden self-check (merged
results 20/20 PASS). No journey regressed, coherence is COHERENCE-PASS, and all 8 anti-goals hold;
GOAL_ACHIEVED is not reachable because J-23/J-24/J-25 remain unbuilt.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing (deterministic replay) | reports/qa/goal-mcp-loop-iter-37-evidence/J-01-verify.png |
| J-02 | passing | passing (deterministic replay) | reports/qa/goal-mcp-loop-iter-37-evidence/J-02-verify.png |
| J-03 | passing | passing (deterministic replay) | reports/qa/goal-mcp-loop-iter-37-evidence/J-03-verify.png |
| J-04 | passing | passing (deterministic replay) | reports/qa/goal-mcp-loop-iter-37-evidence/J-04-verify.png |
| **J-05** | passing | **passing (TARGET — dedicated LLM walk + golden self-check; iter-36 closure row closed)** | reports/qa/goal-mcp-loop-iter-37-evidence/J-05-ledger-list.png, J-05-backlink-stocks.png |
| J-06 | passing | passing (deterministic replay; opened as shared-group rep) | reports/qa/goal-mcp-loop-iter-37-evidence/J-06-verify.png |
| J-07 | passing | passing (deterministic replay) | reports/qa/goal-mcp-loop-iter-37-evidence/J-07-verify.png |
| J-08 | passing | passing (deterministic replay) | reports/qa/goal-mcp-loop-iter-37-evidence/J-08-verify.png |
| J-09 | passing | passing (deterministic replay) | reports/qa/goal-mcp-loop-iter-37-evidence/J-09-verify.png |
| J-10 | passing | passing (deterministic replay) | reports/qa/goal-mcp-loop-iter-37-evidence/J-10-verify.png |
| **J-11** | passing | **passing (TARGET — dedicated LLM walk + golden self-check; iter-36 closure row closed)** | reports/qa/goal-mcp-loop-iter-37-evidence/J-11-vcp-crosscheck.png, J-11-factor-lab-list.png |
| J-12 | passing | passing (deterministic replay) | reports/qa/goal-mcp-loop-iter-37-evidence/J-12-verify.png |
| J-13 | passing | passing (deterministic replay) | reports/qa/goal-mcp-loop-iter-37-evidence/J-13-verify.png |
| J-14 | passing | passing (deterministic replay) | reports/qa/goal-mcp-loop-iter-37-evidence/J-14-verify.png |
| J-15 | passing | passing (byte-identity carry — perf journey, no golden, OUT OF SCOPE) | reports/perf-budgets.md (last measured iter-27) |
| J-16 | passing | passing (byte-identity carry — no golden, OUT OF SCOPE) | reports/qa/goal-mcp-loop-iter-35-qa.md (last integration-tested iter-35) |
| J-17 | passing | passing (deterministic replay) | reports/qa/goal-mcp-loop-iter-37-evidence/J-17-verify.png |
| J-18 | passing | passing (deterministic replay; opened as spot-check) | reports/qa/goal-mcp-loop-iter-37-evidence/J-18-verify.png |
| J-19 | passing | passing (deterministic replay) | reports/qa/goal-mcp-loop-iter-37-evidence/J-19-verify.png |
| J-20 | passing | passing (deterministic replay; GO strip on every opened frame) | reports/qa/goal-mcp-loop-iter-37-evidence/J-20-verify.png |
| J-21 | passing | passing (FIRST deterministic replay — iter-35 golden folded in) | reports/qa/goal-mcp-loop-iter-37-evidence/J-21-verify.png |
| J-22 | passing | passing (FIRST deterministic replay — iter-36 golden folded in) | reports/qa/goal-mcp-loop-iter-37-evidence/J-22-verify.png |
| J-23 | unknown | unknown (unbuilt — next FULL target, B-204) | — |
| J-24 | unknown | unknown (unbuilt — B-201) | — |
| J-25 | unknown | unknown (unbuilt — B-205) | — |

No journey changed status this iteration; the value is the re-verification itself (closing the
iter-36 replay debt) and the two Targets' dedicated evidence. Deterministic replay is
assertion-driven ("all expects held"); per the spec NOTES + iter-29 lesson the `-verify.png`
md5-collision groups (567f90bb = J-04/06/07/08/09/20; 95533c1d = J-01/05/12; 943c5314 = J-13/14) are
BENIGN shared-endpoint captures — I opened J-06 from the largest group and confirmed it is a real
`/evidence` ledger, not a shared error frame.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| #1 No proven unless ledger-backed | OK | All /evidence rows FAIL, all badges "Not yet proven"; 0 "Proven" on /evidence, /stocks, or /research/factor-lab (frames opened). |
| #2 Decision-quality only (no orders/targets) | OK | "Research-only · decision support · no orders" header on every opened frame; no return/price/buy-sell language. |
| #3 Displayed numbers correct | OK | /evidence -0.03%/-0.38%/-1.64% byte-match /api/evidence control_excess (merged trace); frozen-golden ledger tests 2/2 pass (dev + reviewer re-ran). |
| #4 No overfit edges shown as proven | OK | 0 PASS in either ledger; no proven edge exists to overfit. |
| #5 Determinism + no-lookahead | OK | Zero code diff (only README.md +2/-1); seed 20240601 preserved; no mechanism to introduce lookahead. |
| #6 No ship without passing referee verdict | OK | No `## Evidence Claim` registered (grep-confirmed); gate auto-passes; canonical Bonferroni divisor stays 8; both ledgers byte-identical 7-FAIL. |
| #7 No hard-coded credentials | OK | scan-report.md CLEAN (no secret/dependency/license findings); the one changed file is prose README. |
| #8 Resilience to data-shape/scale (no crash/OOM) | OK | Zero code diff → no new consumer of a widened field; dev prod-mode readiness smoke: 16 pages HTTP 200, /api/health preflight verdict=GO (all 4 components ok), warmup 89/89, clean backend log, no OOM. iter-24 + iter-26 #8 entries stay resolved=true. |

No new anti-goal violation. `anti_goal_violations` unchanged (two prior critical #8 entries remain
resolved=true).

## Next-Step Recommendation

iter-38 = **FULL J-23** (backlog **B-204** watchlist concentration X-ray — pairwise correlation
view, cluster groupings, sector/theme concentration, headline "effective independent bets" with its
window stated; the ENB helper is the SAME module the evidence correlation audit uses → single
source; NA over fabrication for insufficient overlap; NO Evidence Claim, divisor stays 8). FULL
because it ships a new served surface + endpoint that needs the audit / ux-regression / closure
guards. Read the binding B-204 card in `docs/improvement-backlog.md` before planning.

**Carry the systemic flag:** a FULL iter re-creates the deterministic-replay gap (`run-phase.sh` has
no replay lane — it has CLOSURE-FAILed on this twice, iter-33 + iter-36), so iter-38 must either run
the closure one-liner replay inline OR be followed by a lean verify pass (what iter-34 and iter-37
were). Three journeys remain (J-23 → J-24/J-25, the risk-analytics cluster, one risky journey per
iter); after them GOAL_ACHIEVED becomes reachable. Durable framework fix (recorded, not owed to any
single iter): add the replay lane to `run-phase.sh` / the full path of `run-goal.sh`.

## Halt Justification (if halting)

Not halting — CONTINUE. GOAL_ACHIEVED is not reachable: J-23, J-24, and J-25 are unbuilt/unknown,
and no Must-have journey may be `unknown` at achievement. No regression (no passing→failing; no
unresolved critical anti-goal — both prior #8 entries resolved=true), so not REGRESSION. The next
step is concrete, autonomous dev work with binding backlog cards (B-204/B-201/B-205), so not STALLED.
Review PASSED (not fail-open), this was a clean planned lean pass with no cross-cutting ambiguity,
and no journey failed two consecutive iterations, so not ESCALATE.
