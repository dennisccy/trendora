# Iteration 9 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

iter-9 cleanly delivered its sole deliverable — Part A of goal.md's engineering direction, the
sustainable trial economy (an injectable, default-off online-FDR / LORD++ deflation policy in a
separate internal staging ledger). This is a backend infrastructure milestone (like the iter-2
"backend milestone — not a journey-state change"): by explicit spec design it flips NO journey to
passing. The two new human-authored Must-have journeys J-07 (multi-horizon) and J-08 (multi-factor
combination) remain unbuilt/unknown, so the goal is not yet achieved — but real, load-bearing
progress landed and the next step is crisp, so this is CONTINUE.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing (no regression) | canonical ledger git-unmodified + unedited `test_referee.py`/`test_forward_walk.py` green + `test_evidence.py` golden; last pixel reports/qa/goal-mcp-loop-iter-8-evidence/UT-15-result.png |
| J-02 | passing | passing (no regression) | byte-identical `/api/evidence`; leadership proof byte-matches certified-claims.jsonl L1 (git-unchanged); reports/qa/goal-mcp-loop-iter-8-evidence/UT-16-result.png |
| J-03 | passing | passing (no regression) | `proven_signals == {leadership_score}` (golden); FDR fenced to staging, never served (audit B5); reports/qa/goal-mcp-loop-iter-8-evidence/UT-15-result.png |
| J-04 | passing | passing (no regression) | Breakout-watch Risk-on row byte-identical (ledger L2 git-unchanged); reports/qa/goal-mcp-loop-iter-8-evidence/UT-05-result.png |
| J-05 | passing | passing (no regression) | all 4 ledger rows byte-identical; `build_evidence_payload` golden green; reports/qa/goal-mcp-loop-iter-8-evidence/UT-05-result.png |
| J-06 | passing | passing (no regression) | vcp L4 byte-unchanged; `rejection_offsets()==[1,2,4]` derived, no entry rewritten (audit B1); reports/qa/goal-mcp-loop-iter-8-evidence/UT-05-result.png |
| J-07 | (new / absent) | unknown — unbuilt by design | none — Part B, targeted iter-10 (spec: "Neither flips to passing this iteration") |
| J-08 | (new / absent) | unknown — unbuilt by design | none — Part B, targeted iter-11 |

Note: browser QA is SKIPPED by design (Frontend Present: no, zero `apps/frontend/**` diff). Per the
iter-6 lesson (embedded verbatim in this spec), J-01..J-06 non-regression is judged on the canonical
`/api/evidence` byte-match + the unit suite, NOT on a fresh pixel or the dead `browser_checks_run`
flag. I verified that byte-identity path independently (see Halt/Next-Step); J-01..J-06 hold.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No value shown proven unless backed by a passing certified-claim | OK | proven_signals stays exactly {leadership_score}; FDR is default-OFF and fenced to an internal staging ledger NEVER read by GET /api/evidence (audit B5); no new "Proven" claim shipped (no Evidence-Claim block by design) |
| Decision-quality only (no return/price/buy-sell/orders) | OK | secret+language scan of the full source diff clean; only test-level/statistics vocabulary added |
| Displayed numbers correct (match engine for same as-of) | OK | canonical `/api/evidence` byte-identical (ledger git-unmodified; `test_evidence` frozen-golden green); default `certify_edge` byte-identical (unedited `test_referee.py`) |
| No overfit edges (must survive referee) | OK | canonical stays strict Bonferroni via the honesty fence `use_fdr = ledger==STAGING and fdr.enabled`; FDR (weaker, false-discovery-rate) fenced to staging only |
| Preserve determinism + no-lookahead | OK | `online_fdr.py` pure — grep finds no random/np.random/time/datetime/now/uuid/urandom/open; referee sealed-holdout procedure untouched on default path |
| No iteration ships without a passing referee verdict for its claims | OK | no claims this iter; gate passes through (audit T3 re-ran the gate regex: 0 sections, exit 0) |
| No hard-coded credentials/keys/tokens | OK | secret scan of tracked+untracked source diff returned nothing |

Coherence: **COHERENCE-PASS** (no IA/data-contract drift; backend-only; no new endpoint or displayed
value) — no structural veto.

## Next-Step Recommendation

iter-10 (FULL): open the scan aperture — Part B Phase 1 — and surface **J-07**. Use the new staging
ledger to explore a NON-20 forward horizon (1/5/10/60) for a factor-decile cohort cheaply under the
online-FDR economy, then promote exactly one out-of-sample winner to canonical by carrying an
`## Evidence Claim` with an explicit `"ledger":"canonical"` key so the post-decompose gate certifies
it under strict Bonferroni (divisor 5, `required_p=0.010`). On PASS, surface the row on `/evidence` +
the factor-lab "Proven" badge at that horizon (uncertified horizons read "Not yet proven"), and
browser-verify J-07. FULL depth because iter-10 ships a new referee-gated "Proven" claim and a new
public-surface badge (the iter-8 escalation rule). Then iter-11 does the same for a PRE-REGISTERED
2-factor combination to surface J-08. GOAL_ACHIEVED becomes reachable once both land verified.

Load-bearing reminder for the iter-10 author (audit §5): the gate default is now `"ledger":"staging"`
— a claim intended for the user-facing badge MUST set `"ledger":"canonical"` EXPLICITLY, or the
winner is certified into staging and silently never surfaces (conservative fail direction, but a real
footgun for J-07/J-08 surfacing).

## Halt Justification (if halting)

Not halting. Not GOAL_ACHIEVED — two Must-have journeys (J-07, J-08) are unbuilt/unknown with no
positive evidence of passing (the goal was re-opened when goal.md was extended with them before
iter-9). Not REGRESSION — nothing passing→failing: I independently confirmed the canonical
`certified-claims.jsonl` is git-UNMODIFIED (working tree clean; last touched at iter-8 commit
8043863; 4 entries PASS/PASS/FAIL/PASS, all deflation=bonferroni, divisors 1-4), the default-path
tests are unedited and green (0 diff lines — the strongest proof defaults reproduce byte-identically),
`proven_signals` stays `{leadership_score}`, and no critical anti-goal was violated. Not STALLED —
this iter made genuine enablement progress (the full pipeline ran end to end to `closure_passed` with
a present audit handoff PASS, review PASS, QA PASS, coherence PASS) and a precise, named next step
exists (iter-10 Part B → J-07). Not ESCALATE — already full and the next target is unambiguous.
