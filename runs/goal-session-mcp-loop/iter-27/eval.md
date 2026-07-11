# Iteration 27 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

iter-27 is the dedicated memory-hardening + fix-verification recovery pass the iter-26 REGRESSION
asked for, and it landed cleanly. The full-universe (322-date x 541-member) "Rebuild snapshots" job
now runs to a verified completed state under the `ulimit -v 6291456` cap without exhausting memory —
the unresolved critical anti-goal #8 that halted iter-26 is RESOLVED, live-verified via the canonical
browser-qa lane (three consecutive rebuilds, all `status:"ok"` 322/322, VmPeak flat at 5,147,876 KB
with 1,116 MB margin, no MemoryError). J-16 flips failing -> passing and all 8 required-still-passing
journeys were re-driven LIVE and PASSED, closing the iter-26 skipped-behind-the-outage replay gap.
GOAL_ACHIEVED remains out of reach because J-02/J-06/J-07/J-08/J-09 stay sanctioned-partial on the
30-year basis (no staging winner clears the canonical Bonferroni divisor-8) — so the verdict is
CONTINUE, exactly as the spec's own reachability note predicted.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-16 | failing | **passing** | `reports/qa/goal-mcp-loop-iter-27-evidence/UT-02-run2-ok.png`, `UT-02-post-both-runs-stocks.png` (browser-qa UT-02/UT-03) |
| J-01 | passing | passing (re-verified live) | `reports/qa/goal-mcp-loop-iter-27-evidence/UT-02-post-both-runs-stocks.png` (UT-07/UT-08) |
| J-03 | passing | passing (re-verified live) | UT-08 DOM inspection (same frame) |
| J-04 | passing | passing (re-verified live) | `reports/qa/goal-mcp-loop-iter-27-evidence/UT-06-dashboard.png` (UT-06) |
| J-05 | passing | passing (re-verified live; evaluator opened) | `reports/qa/goal-mcp-loop-iter-27-evidence/UT-09-evidence-empty-state.png` (UT-09) |
| J-10 | passing | passing (re-verified live; evaluator opened) | `reports/qa/goal-mcp-loop-iter-27-evidence/UT-10-aapl-full-history.png` (UT-10) |
| J-12 | passing | passing (re-verified live) | `reports/qa/goal-mcp-loop-iter-27-evidence/UT-11-membership-timeline-fullpage.png` (UT-11) |
| J-13 | passing | passing (re-verified live) | `reports/qa/goal-mcp-loop-iter-27-evidence/UT-15-data-manager-nav.png` (UT-15/UT-02/04/05) |
| J-15 | passing | passing (re-verified live) | `reports/phase-goal-mcp-loop-iter-27-ui-test-results.md#UT-12` + `reports/perf-budgets.md` Item H |
| J-11 | passing | passing (carried; byte-identity, incidentally corroborated by UT-09 all-FAIL) | `reports/qa/goal-mcp-loop-iter-27-evidence/UT-09-evidence-empty-state.png` |
| J-14 | passing | passing (carried; byte-identity, index/chart source zero-diff) | `reports/qa/goal-mcp-loop-iter-25-evidence/UT-02-run1-data-fullpage.png` |
| J-02 | partial | partial (sanctioned; zero evidence work) | no Proven badge to drill (ledger all-FAIL, UT-09) |
| J-06 | partial | partial (sanctioned; zero evidence work) | UT-09 vcp_contraction D10 = FAIL |
| J-07 | partial | partial (sanctioned; zero evidence work) | ledger row FAIL |
| J-08 | partial | partial (sanctioned; zero evidence work) | ledger row FAIL |
| J-09 | partial | partial (sanctioned; zero evidence work) | ledger row FAIL |

Newly passing: J-16. Newly failing: none. Regressed: none.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| #1 Proven only if backed by passing certified-claim | OK | UT-09: all-FAIL ledger, every badge "Not yet proven"; no new claim; both ledgers byte-identical all-FAIL |
| #2 Decision-quality only (no return/price/buy-sell) | OK | No frontend change (backend memory-hygiene only); honest-status language intact; iter-diff carries no return/buy-sell text in product source |
| #3 Displayed numbers correct (byte-match engine) | OK | Byte-identity gated: test_scoring_window.py 4/4 (score_stocks + score_regime + bars_asof_window windowed==unwindowed, 0 diffs), test_bar_cache 12/12, test_forward_testing 5/5; 597,044 forward returns bit-identical across runs; fix is allocator/OS-return only |
| #4 No overfit edges | OK | No new proven edge; ledger all-FAIL |
| #5 Determinism + no-lookahead | OK | bars_asof_window preserves `date <= d` boundary (audit §3); scoring <= as-of, forward returns > as-of |
| #6 No ship without passing referee verdict | OK | No Evidence Claim this iter; post-decompose gate passes automatically |
| #7 No hard-coded credentials/keys/tokens in source | OK (see note) | The scan-report's 12 CRITICAL secret findings are ALL planted fixtures inside the vendored `incredible_auto_dev/tests/judgment/` framework subtree (cases named `case-04-paid-service-live-key`, `case-05-secret-committed`, `case-03-hardcoded-credential` — self-test harness whose PURPOSE is to be detected; keys are the AWS-doc example `AKIAIOSFODNN7EXAMPLE` + fictional `lv_live_`/`qs_live_` LISTVAULT keys). They entered via the framework squash-merge (`5e173ba`/`eaf42d1`/`6306568`), NOT iter-27's dev work (the 6 backend memory files + config.yaml). The changed Trendora product source carries no credentials. Not a product anti-goal violation; I checked fail-closed and these are non-real fixtures in disjoint tooling, corroborated by reviewer + auditor + coherence all treating the subtree as out-of-scope framework tooling. |
| #8 Resilience to data-shape/scale change (never crash/exhaust memory) | **RESOLVED** | The iter-26 critical violation is fixed + live-verified: full-universe rebuild survives 3x consecutive (UT-02), VmPeak flat 5,147,876 KB under the 6144 MB cap (1,116 MB margin), no MemoryError, backend healthy throughout; `anti_goal_violations` iter-26 entry flipped `resolved=true` |

No unresolved anti-goal violation. No NEW violation introduced.

## Coherence

COHERENCE-PASS (`runs/goal-session-mcp-loop/iter-27/coherence.md`) — no Data-Contract or
Information-Architecture drift; the change is an INTERNAL memory/load-path change beneath already-
registered values (three scores, regime score, bars, coverage), every value re-serving byte-identically
from its existing single computing module and endpoint; zero `apps/frontend` diff, no new route. No
structural veto.

## Next-Step Recommendation

iter-28 (FULL) — the ONLY remaining path to GOAL_ACHIEVED is re-certifying the five sanctioned-partial
evidence journeys J-02, J-06, J-07, J-08, J-09 on the 30-year basis. Per goal.md loop mechanics: run a
NEW-basis pre-registered staging exploration (never an ad-hoc data-mined cohort), then promote ONLY a
winner clearing the canonical Bonferroni divisor-8 with margin via an explicit `"ledger":"canonical"`
`## Evidence Claim`, and HONOR the honest-stop guard — no staging winner clears divisor-8 today, so this
may honestly surface nothing; report, do not force. FULL because it ships a referee-gated canonical claim
that needs the audit/ux-regression/closure guards. Skeptical flag for the next evaluator: J-02/06/07/08/09
have been sanctioned-partial since the iter-18 data-basis reset (5+ iterations) with the standing note that
"no staging winner clears divisor-8"; if the staging exploration again surfaces no promotable edge, the
next iteration should weigh whether these five represent a genuine plateau on the current data (a candidate
for a STALLED verdict or a goal.md amendment) rather than indefinitely re-attempting the same
un-clearing search.

Non-blocking carry-forwards (do NOT bundle into the evidence work):
- **B1** (review/audit): add `breadth_short_ma`/`breadth_long_ma` to `IndicatorsCfg._validate`'s `max_needed`
  tuple the next time `config.py` is touched — latent guard hole, byte-safe today only because
  `breadth_long_ma`(200) coincides with `max(ma_periods)`(200).
- **T1/F1** (audit): the next QA setup should grant the browser-qa agent backend-lifecycle permission (or
  have the coordinator perform the stop/cold-start) so UT-01/UT-13/UT-14 (cold-start-first `/data` +
  backend-down contained-card + recovery) are re-driven LIVE by the canonical lane; optionally add a
  `/data` re-rebuild guardrail and a client-side readiness-poll timeout.
- Housekeeping: `rm -rf .pytest-tmp-iter27/` (2.9 GB untracked scratch left in repo root — review NOTE).

## Halt Justification (if halting)

N/A — CONTINUE, not a halt. Real load-bearing progress was made (J-16 failing->passing; critical
anti-goal #8 resolved and live-verified), all 8 required-still-passing journeys re-verified live, no
regression, no unresolved anti-goal, coherence PASS, and a concrete next step exists — so none of
REGRESSION / STALLED / GOAL_ACHIEVED / ESCALATE applies (review PASS_WITH_NOTES, not fail-open; no
journey failed two consecutive iterations — J-16 recovered in one).
