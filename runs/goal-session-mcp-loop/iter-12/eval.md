# Iteration 12 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

iter-12 delivered exactly its scoped, backend-only discovery/enablement deliverable — the deferred "combinations" half of goal.md Part B Phase 1 — cleanly through the full pipeline (Review PASS, QA PASS 134/134, Audit PASS, Closure passed, coherence COHERENCE-PASS). It landed the previously-missing recorded staging basis that J-08 promotion needs: a FIXED pre-registered 3-pair 2-factor combination candidate set was certified through the UNCHANGED referee into the internal staging ledger (4→7 entries), producing one real promotable winner. No journey flips this iteration — by design — so NOT GOAL_ACHIEVED (J-08 stays `unknown`); no regression, no anti-goal violation, and a concrete tractable next step exists (surface J-08 in iter-13).

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing (re-verified, byte-identity) | git diff HEAD: apps/frontend + app/api + evidence.py = 0-diff; certified-claims.jsonl byte-identical (5 entries); proven_signals `{leadership_score}` |
| J-02 | passing | passing (re-verified, byte-identity) | certified-claims.jsonl L1 git-UNMODIFIED; read path (evidence.py, api/evidence.py) 0-diff |
| J-03 | passing | passing (reinforced) | honesty fence `use_fdr = ledger==LEDGER_STAGING and evidence.fdr.enabled` intact (referee.py 0-diff); 2 anchor combinations FAILED OOS and are NOT surfaced |
| J-04 | passing | passing (re-verified, byte-identity) | certified-claims.jsonl L2 (Breakout-watch regime row) git-UNMODIFIED; no regime surface added |
| J-05 | passing | passing (re-verified, byte-identity) | `git diff HEAD` certified-claims.jsonl EMPTY; 3 new verdicts went to SEPARATE internal staging-ledger.jsonl (never served) |
| J-06 | passing | passing (re-verified, byte-identity) | certified-claims.jsonl L4 (vcp h20) git-UNMODIFIED; factor-lab read path 0-diff |
| J-07 | passing | passing (re-verified, byte-identity) | certified-claims.jsonl L5 (vcp h60, ledger=canonical) git-UNMODIFIED; per-horizon factor-lab reader 0-diff |
| J-08 | unknown | unknown (enablement done; surfacing = iter-13) | staging-ledger.jsonl #7 rs_spy_3m+high_proximity PASS, raw p=0.0009995 < divisor-6 bar 0.00833 — real promotable basis |

Browser QA correctly SKIPPED (Frontend Present: no). Required-still-passing J-01..J-07 verified via the spec-designated byte-identity / frozen-golden path, not a fresh browser lane.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No unproven value shown as proven | OK | The 3 combination verdicts are signal-less composites written ONLY to the internal staging ledger; the 2 that FAILED OOS are honestly not surfaced. Canonical `proven_signals` byte-identical `{leadership_score}`. |
| Decision-quality only (no buy/sell/price/return) | OK | Diff language scan of apps/backend + config + proposer-guidance = clean. |
| Displayed numbers correct (no UI recompute) | OK | No UI change; canonical read path (evidence.py/api) 0-diff; referee is the sole computing source. |
| No overfit edges (referee-gated) | OK | Each pair ran through the UNCHANGED sealed-holdout + SPY control + LORD++ referee; winner cleared its level, FAILs honestly recorded. |
| Preserve determinism / no-lookahead | OK | reset=True re-run byte-identical (frozen-golden test T1); referee.py/online_fdr.py 0-diff; sealed temporal holdout. |
| No ship without passing referee verdict | OK | No canonical claim this iter (pure discovery); gate passes automatically per goal.md loop mechanics. |
| No hard-coded credentials/keys/tokens | OK | Secret scan of the full diff = clean. |

`anti_goal_violations` remains `[]`. Honesty fence (FDR fenced to staging; canonical stays strict Bonferroni) verified via referee.py zero-diff. `ma_stack` (iter-8 closed FAIL) appears only as an explicitly-excluded leg in documentation — never used.

## Next-Step Recommendation

**iter-13 (FULL) — surface J-08 and reach GOAL_ACHIEVED.** Promote the SINGLE recorded staging winner — `rs_spy_3m:top:quintile` + `high_proximity:top:tertile` (staging-ledger.jsonl #7, raw block-bootstrap p=0.0009995, holdout +0.0469) — to the canonical ledger via a `## Evidence Claim` that sets `"ledger":"canonical"` EXPLICITLY (iter-9b lesson: an omitted key silently re-stages and never surfaces). It faces Bonferroni divisor 6 (required_p ≈ 0.00833); the recorded raw p clears it with margin. Then surface J-08 on `/research/factor-combination` (composite-cohort "Proven" badge) + a new `/evidence` combination claim row — both as additional READERS of the SAME `GET /api/evidence` payload (no new module/endpoint). Read the recorded staging verdict; do NOT recompute. HONEST-STOP GUARD: if the winner no longer clears the divisor-6 bar against fresh data, report it rather than force an overfit promotion (anti-goal #1/#4). BROWSER-QA HARD REQUIREMENT (recurring iter-3/iter-11 lesson): scroll each asserted badge/row into the viewport and capture DISTINCT screenshots (md5-check them) — do not accept a single relabeled full-page frame. GOAL_ACHIEVED becomes reachable the moment J-08 lands browser-verified with J-01..J-07 non-regressed.

## Halt Justification (if halting)

N/A — not halting. This is a CONTINUE: real progress (the missing combination-staging basis now exists, with a certified promotable winner), no regression, no unresolved anti-goal, coherence COHERENCE-PASS, and one clear remaining Must-have journey (J-08) with a concrete build path.
