# Iteration 25 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

iter-25 is the fix-VERIFICATION recovery pass the iter-24 REGRESSION asked for, and it landed cleanly. The already-committed `config.yaml:108 mmap_size_bytes: 0` fix (mmap disabled, zero source diff this iteration) was re-verified LIVE by the canonical browser-qa lane with two independent cold-restart reproductions: `/data` now renders fully populated as the first request after a cold backend boot (~10.2s / ~10.5s), the backend survives, and downstream pages load — so **J-13 recovers regressed -> passing** and target **J-15 flips partial -> passing**, with the iter-24 CRITICAL anti-goal #8 violation now RESOLVED. Not GOAL_ACHIEVED: J-02/J-06/J-07/J-08/J-09 remain sanctioned-partial (30-year data-basis reset, ledgers all-FAIL, no staging winner clears Bonferroni divisor-8) and J-16 is deliberately unbuilt.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing (fresh live) | reports/qa/goal-mcp-loop-iter-25-evidence/UT-08-sector-sorted.png |
| J-02 | partial | partial (by design; out of scope) | (no evidence work; ledgers git-unchanged all-FAIL) |
| J-03 | passing | passing (fresh live) | reports/qa/goal-mcp-loop-iter-25-evidence/UT-08-stocks-leaderboard.png, UT-11-evidence-ledger.png |
| J-04 | passing | passing (fresh live) | reports/qa/goal-mcp-loop-iter-25-evidence/UT-10-dashboard-to-evidence.png |
| J-05 | passing | passing (fresh live) | reports/qa/goal-mcp-loop-iter-25-evidence/UT-11-evidence-ledger.png |
| J-06 | partial | partial (by design; out of scope) | (no evidence work; ledger row = FAIL) |
| J-07 | partial | partial (by design; out of scope) | (no evidence work; ledger row = FAIL) |
| J-08 | partial | partial (by design; out of scope) | (no evidence work; ledger row = FAIL) |
| J-09 | partial | partial (by design; out of scope) | (no evidence work; ledger row = FAIL) |
| J-10 | passing | passing (fresh live) | reports/qa/goal-mcp-loop-iter-25-evidence/UT-12-aapl-recent.png (+ canvas pixel-buffer verify) |
| J-11 | passing | passing (fresh live) | reports/qa/goal-mcp-loop-iter-25-evidence/UT-11-evidence-ledger.png |
| J-12 | passing | passing (fresh live) | reports/qa/goal-mcp-loop-iter-25-evidence/UT-02-run1-data-fullpage.png |
| **J-13** | **regressed** | **passing** (recovered) | reports/qa/goal-mcp-loop-iter-25-evidence/UT-02-run1-data-fullpage.png, UT-03-run2-data-fullpage.png, UT-06-backend-unavailable.png |
| J-14 | passing | passing (fresh live) | reports/qa/goal-mcp-loop-iter-25-evidence/UT-02-run1-data-fullpage.png (index provenance) |
| **J-15** | **partial** | **passing** (target) | reports/qa/goal-mcp-loop-iter-25-evidence/UT-02-run1-data-fullpage.png + reports/perf-budgets.md (live cold-path + warm re-confirm) |
| J-16 | unknown | unknown (out of scope, unbuilt) | (deliberately deferred, rubric rule 5) |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| #1 Unproven not shown as proven | OK | UT-11: all-FAIL ledger, 0 "PASS" in raw HTML; every /stocks score "Not yet proven" (UT-08). |
| #2 No return/price-target/buy-sell/orders | OK | "Research-only · decision support · no orders" header (UT-08); zero source diff -> no new language. |
| #3 Displayed numbers correct | OK | Zero code diff -> byte-identical; storage-card values match current /api/data capacity payload; ledger values byte-match. |
| #4 No overfit edges | OK | All-FAIL ledger; nothing certified; Bonferroni divisor stays 8 (no ## Evidence Claim). |
| #5 Determinism / no-lookahead | OK | Zero engine diff (audit B2); the iter-24 bug was memory-footprint config, not correctness. |
| #6 No claim without referee verdict | OK | No ## Evidence Claim this iter; post-decompose gate auto-passes. |
| #7 No hard-coded credentials | OK | scan-report.md CLEAN; zero new config/env files. |
| #8 Resilience — no crash / no memory exhaustion | OK — **iter-24 violation now RESOLVED (resolved=true)** | UT-02/UT-03 cold-restart `/data` renders 2/2 (no OOM, backend survived); UT-06 contained "Backend unavailable" card (nav/shell intact, honest "no fabricated values") — NOT a blank app-error page; perf-budgets.md peak RSS ~1.8-1.9 GB << 6144 MB cap. Evaluator personally opened all three frames. |

Deterministic scan (scan-report.md): CLEAN — no secret/dependency/license findings. Coherence (iter-25/coherence.md): **COHERENCE-PASS** (zero source diff — no structural veto).

## Next-Step Recommendation

iter-26 (FULL). Two remaining gaps to GOAL_ACHIEVED, in priority order:

1. **J-16 — fast-platform data-jobs perf** (goal.md item F + A/B warmup-cache). Commit the measured baseline, land the byte-identity-gated scoring-window change (`indicators.max_lookback_bars` slice), and re-measure per-date backfill + full warmup >=30% improvement as the never-regress budgets. Gate on the one-off byte-identical harness — ANY per-(symbol,date) diff means an indicator depends on deeper history (fix the window; never accept drift). Most tractable unbuilt work; self-contained.
2. **J-02 / J-06 / J-07 / J-08 / J-09 — evidence re-certification on the 30-year basis.** Run a NEW-basis pre-registered staging exploration, then promote ONLY a winner clearing the canonical Bonferroni divisor-8 with margin (explicit `"ledger":"canonical"`). Honor the honest-stop guard — no staging winner clears divisor-8 today, so this may honestly surface nothing (report, don't force).

FULL either way: J-16 is the exact risky byte-identity-gated data-path change that needs the audit/ux-regression/closure guards, and must NOT be bundled with the evidence work (rubric rule 5); the evidence path ships a referee-gated canonical claim. Non-blocking carry-forwards (do NOT bundle): F1 (`/data` no-retry desync, P3); T3 (capture a clean same-instant storage-card <-> `/api/data` byte-diff in the next `/data`-touching iter); delete the dead-duplicate `index-regime-chart.tsx` / `major-indexes-card.tsx` (coherence-WARN) in a dedicated tidy iter; harden or formally down-weight the non-terminal QA lane (its PASS rested on a mis-cited error-card frame + an over-budget `/api/health` this iter).

## Halt Justification (if halting)

N/A — not halting. Verdict is CONTINUE. Per the decision tree: NOT REGRESSION (no journey moved passing->failing; J-13 recovered from its iter-24 regression, and the critical anti-goal #8 violation is now RESOLVED, re-verified by the canonical browser-qa lane that originally caught it); NOT STALLED (the blocker was an operational config fix, already applied and live-verified — no human-owned action); NOT GOAL_ACHIEVED (J-02/J-06/J-07/J-08/J-09 sanctioned-partial + J-16 unknown/unbuilt — Must-have journeys still lack positive passing evidence); NOT ESCALATE (already full depth; review PASS not fail-open; J-13 recovered in a single iteration, not two consecutive failures). Coherence is COHERENCE-PASS, so no consolidation mandate.
