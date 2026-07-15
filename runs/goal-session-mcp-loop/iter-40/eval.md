# Iteration 40 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

iter-40 (FULL) delivered J-24 (per-stock risk-budget card + leaderboard columns, backlog B-201) as a
strictly-additive, single-source, honest, read-only surface. The target flips unknown -> passing on
multi-lane pixel evidence I personally opened plus the auditor's independent full-float-precision
byte-match — even though the canonical browser-qa lane SKIPPED all 16 tests (a Chrome-MCP DevTools
port-binding outage, product independently confirmed up + correct). No journey regressed; both prior
critical anti-goal #8 crashes stay resolved; coherence COHERENCE-PASS; closure CLOSURE-PASS. GOAL_ACHIEVED
is not reachable yet — J-25 (the last journey) is unbuilt.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-24 (target) | unknown | **passing** | `reports/qa/goal-mcp-loop-iter-40-evidence/TC-01-risk-budget-card-liquid.png` (card, all 6 tiles + percentiles) + `reports/demo/goal-mcp-loop-iter-40/step-02.png` (leaderboard columns) + `step-06.png` (/methodology) + audit §3 byte-match table |
| J-01 | passing | passing (live-corroborated) | `reports/demo/goal-mcp-loop-iter-40/step-02.png` (leaderboard 541/541, every score "Not yet proven") |
| J-03 | passing | passing (live-corroborated) | `reports/demo/goal-mcp-loop-iter-40/step-02.png` (strong scores still "Not yet proven") |
| J-10 | passing | passing (live-corroborated) | `reports/demo/goal-mcp-loop-iter-40/step-08.png` (Full history 3185 bars since 1996-01-02, weekly-sampled, DMAs + regime bands) |
| J-20 | passing | passing (live-corroborated) | TC-01 + `step-02.png` + `step-08.png` (single "GO" strip across /stocks, /stocks/AAPL) |
| J-02, J-05, J-12, J-13 | passing | passing (byte-identity carry) | required set NOT deterministically replayed (recurring FULL-iter replay gap); logic files git-untouched -> no regression mechanism; last_verified left at iter-39 |
| J-04, J-06–J-09, J-11, J-14–J-19, J-21–J-23 | passing | passing (byte-identity carry) | not in required set / perf journeys; ledgers byte-identical; last golden-replay iter-39 |
| J-25 | unknown | unknown | unbuilt (the last journey; FULL iter-41 target) |

Prior status source: inlined journey digest (iter-39). Only J-24 changed status.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| #1 No unproven value shown as proven/confident | OK | Ledgers byte-identical (7/7 FAIL, 0 PASS — my own git diff); no Evidence Claim; card carries NO badge/proven-language (audit F2 + ux-regression grep); "Descriptive only; not a recommendation." (TC-01 pixel); step-02 all scores "Not yet proven". |
| #2 Decision-quality only (no advice/orders/targets) | OK | "Research-only · decision support · no orders" header (TC-01/step-02/step-08); no buy/sell/trim/reduce/rebalance/target in new code (audit F2 + ux-regression grep). |
| #3 Displayed numbers correct (byte-match engine) | OK | Auditor independently re-derived every served leaf (gap p95/median/worst, variance-share, worst-20d, atr reuse, distance reframe) from stored bars → byte-match to full float precision vs served record_json (audit §3). |
| #4 No overfit edges | OK | No new "proven" claim; ledgers byte-identical; no Evidence Claim. |
| #5 Determinism + no-lookahead | OK | New reads date ≤ as-of (bars_asof_window trailing gap_window+1; closes(bars_asof(asof))); reviewer test_scoring_window.py 4/4 real seed → score_stocks byte-identical. |
| #6 No iteration ships uncertified evidence claim | OK | Pure UX/correctness work; no Evidence Claim; gate passes automatically. |
| #7 No hard-coded credentials/keys | OK | scan-report CLEAN; my own fail-closed grep of the parked warmup.py diff found no secret patterns. |
| #8 Resilience / no OOM / no whole-table load | OK | Audit: all reads per-symbol or resident bar_cache slices, NO whole-table ORM load; new windows folded into max_lookback_bars guard; QA DB rebuild (90 runs → 561 MB) hit no OOM; backend up + serving throughout. Prior iter-24 + iter-26 #8 crashes stay resolved=true. |

## Next-Step Recommendation

**iter-41 = FULL J-25** (backlog B-205 — phase-conditional drawdown/dry-spell expectations panel on a
certified claim's `/evidence` detail: max-drawdown depth / underwater duration / time-to-recover /
longest-losing-streak distributions split by market phase at entry, each with sample size; thin cells
say "insufficient (n=…)"; descriptive history only, historical wording, no forecasts). This is the LAST
unbuilt Must-have; one risky surface per iter; no Evidence Claim (divisor stays 8). Read the binding
B-205 card in `docs/improvement-backlog.md` first.

**HARD PRECONDITION for iter-41: the coordinator/pump must investigate the Chrome-MCP DevTools
port-binding outage** (this session's browser-qa lane could not bind port 9222 across 6 attempts / 2
profiles; two unrelated Chrome instances were also failing to bind — a session/time-window infra
regression, not a product signal). If it recurs, J-25's canonical browser evidence will be degraded the
same way J-24's was. The demo-narrator (Playwright) and the earlier functional-QA agent both drove a
browser fine this run, so the environment is not permanently broken.

**Then iter-42 = LEAN comprehensive verify-only closeout** paying down all accumulated verification debt
in one pass (the established FULL→LEAN pattern): deterministic golden replay over the full
required-still-passing set folding in the three never-replayed goldens (J-23.json [3rd carry], J-24.json,
J-25.json); a healthy Chrome-MCP browser walk formally closing the J-24 residual (5 leaderboard columns'
live sort/NA-last/tooltip + the /methodology DOM — demo frames already cover render) and re-verifying the
required set; and `pytest tests/test_scoring.py -k risk_budget -v` to completion (the 6 deferred
integration tests, currently byte-match-mitigated). After iter-42, all 25 Must-haves carry fresh evidence
→ GOAL_ACHIEVED becomes reachable. (Reasonable de-risking alternative the pump may prefer: run the lean
closeout BEFORE J-25 to lock in J-24 + the required set first — costs one extra iteration.)

**Carry-forward flags (do NOT bundle into feature work):**
- **SYSTEMIC (recurred iter-33/36/38/40):** the "required-still-passing deterministic replay" DoD line is
  structurally unsatisfiable by any FULL iter (run-phase.sh has no replay lane) — durable framework fix
  owed to the maintainer: add the replay lane to run-phase.sh / the full path of run-goal.sh, or run the
  closure one-liner replay inline inside full iters.
- **COMMIT-HYGIENE:** the parked `warmup.py` / `test_forward_testing.py` / `test_warmup.py` /
  `test_scoring_window.py` diff predates the iter-40 snapshot (parked iter-26 windowing work) and is not
  in iter-40's dev handoff. Release-manager should keep it isolated from iter-40's commit or commit it
  separately (closure note #4; ux-regression concurs; benign — no secrets, exercised by this pipeline).
- **J-24 record annotation (audit B1 / closure note #2):** the "short-history renders NA" acceptance
  sub-path is architecturally unreachable while `indicators.min_history_bars = 200` exceeds every
  risk-budget window (min resolved-member bar count = 346) — unit-tested at the function level, never
  browser-demonstrated. Recorded in journey-history so QA's TC-02 "PASS" is not mistaken for a true
  positive.

## Halt Justification (if halting)

N/A — not halting. CONTINUE.
