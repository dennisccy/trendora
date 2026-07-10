# Iteration 26 Evaluation

**Verdict:** REGRESSION
**Depth Recommendation For Next Iteration:** full

## Summary

The live browser lane, running the sanctioned J-16 path ("Rebuild snapshots for current universe", 322 dates × 541 members), reproduced a `MemoryError` that took the ENTIRE backend down — every data endpoint (`/api/data`, `/api/stocks`, `/api/evidence`, eventually `/api/health`) returned HTTP 500 and never recovered. This is a live, reproduced, still-**unresolved** violation of critical anti-goal #8 ("widening the data basis … must never crash an existing page or exhaust a service's memory"): the process pinned VSZ at exactly the 6144 MB `ulimit -v` ceiling (RSS ~4.93 GB, under its own cap) — a virtual-address-space exhaustion. The target journey J-16 FAILED at its direct proof (UT-02) and all eight required-still-passing journeys were SKIPPED behind the outage. Four gates concur (QA FAIL, browser-QA FAIL, audit FAIL, ux-regression UX-REGRESSION-FAIL); only reviewer PASS_WITH_NOTES (which itself flags the crash unfixed) and coherence COHERENCE-PASS (correctly — the crash is operational, not IA/data-contract drift). Per decision-tree rule 1 (an unresolved critical anti-goal violation) the loop halts for human review — the iter-24 precedent verbatim.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing (carried; NOT re-verified — SKIPPED behind outage) | zero frontend diff + byte-identity-gated backend; last live iter-25 UT-08 |
| J-02 | partial | partial (unchanged; zero evidence work) | iter-23 UT-19 (data-basis-change provision) |
| J-03 | passing | passing (carried; NOT re-verified — SKIPPED) | zero engine/scoring diff; last live iter-25 |
| J-04 | passing | passing (carried; NOT re-verified — SKIPPED) | regime engine byte-identical; last live iter-25 |
| J-05 | passing | passing (carried; NOT re-verified — SKIPPED) | ledgers git-unchanged all-FAIL; last live iter-25 |
| J-06 | partial | partial (unchanged; zero evidence work) | iter-23 UT-19 |
| J-07 | partial | partial (unchanged; zero evidence work) | iter-23 UT-19 |
| J-08 | partial | partial (unchanged; zero evidence work) | iter-23 UT-19 |
| J-09 | partial | partial (unchanged; zero evidence work) | iter-23 UT-19 |
| J-10 | passing | passing (carried; NOT re-verified — SKIPPED) | prices.py chart path unaffected; last live iter-25 |
| J-11 | passing | passing (carried; untouched, not in required set) | ledgers byte-identical all-FAIL |
| J-12 | passing | passing (carried; NOT re-verified — SKIPPED) | universe-resolver untouched; last live iter-25 |
| J-13 | passing | passing (carried; NOT re-verified — SKIPPED) | availability-heatmap.tsx zero-diff; last live iter-25 |
| J-14 | passing | passing (carried; untouched, not in required set) | index-chart config byte-identical |
| J-15 | passing | passing (carried; NOT re-verified — SKIPPED; CAVEAT below) | perf-budgets warm/cold last live iter-25 |
| **J-16** | **unknown** | **failing** (target; direct browser proof UT-02 CRASHED the backend) | `reports/qa/goal-mcp-loop-iter-26-evidence/UT-02-fail-backend-unavailable.png` + `UT-02-backend-log-tail.txt` (MemoryError, prices.py:191) |

Note on the carried journeys: browser-qa SKIPPED J-01/03/04/05/10/12/13/15 behind the outage (evidence dir holds only UT-01, UT-02 artifacts). Per the coordinator note they are treated as **unverified this iteration** — carried at their last-good `passing` on zero-frontend-diff + byte-identity-gated backend, `last_verified_iter` left at iter-25, NOT re-verified live. None was observed to fail, so none is `regressed`. **J-15 caveat:** its own "never crash / no OOM on the deep basis" acceptance is directly undercut by this iteration's anti-goal #8 crash, but its specific cold-path test (UT-04) was SKIPPED (not failed), so it is carried, not marked regressed — the next iteration MUST re-verify J-15's cold-path and job resilience on the fixed backend.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| #1 Proven only via passing ledger entry | OK | No ledger change; both ledgers byte-identical all-FAIL (7 canonical / 7 staging); no `## Evidence Claim` this iter. |
| #2 No return/price/buy-sell/alpha | OK | No frontend change; no such language in the diff. |
| #3 Displayed numbers correct (byte-match engine) | OK | Byte-identity harness `test_scoring_window.py` 0 diffs, windowed(320) vs unwindowed(1e6) over 3 dates × full pool + short-history date (auditor B4, reviewer-corroborated). Not live-verified (backend down) but proven at the unit gate. |
| #4 No overfit edges | OK | No ledger write. |
| #5 Determinism / no-lookahead | OK | Scoring ≤ as-of, forward > as-of preserved; warmup cache-scope is load-scope only; byte-identity confirms (coherence Data Contract check + `test_forward_testing.py` cache-awareness cases). |
| #6 No unbacked claim ships | OK | No evidence-derived claim this iter; post-decompose gate auto-passes. |
| #7 No hard-coded credentials | OK | `scan-report.md` CLEAN; diff file list (config/scoring/prices/warmup + tests + perf-budgets + handoff) carries no secret/dependency/license hit. |
| **#8 Resilience to data-scale change; never crash a page or exhaust memory; no unbounded whole-table ORM loads** | **VIOLATED — CRITICAL, unresolved** | The full-universe "Rebuild snapshots" backfill (322×541) crashed the entire backend via `MemoryError` (VSZ pinned at the 6144 MB `ulimit -v` ceiling), reproduced 2/2; every endpoint returned 500 and did not self-heal. Root frame `_BarCache.bars_asof:191` (`full[:cut]`) reached via the pre-existing regime path; the underlying `_do_backfill` prefills the entire 3.29M-bar universe up front (`prefilled_bar_cache(session, expected_symbols=pool_symbols)`) — the standing whole-universe load the anti-goal warns about. Root-cause fix (audit B1) is explicitly NOT applied. Evidence: `reports/phase-goal-mcp-loop-iter-26-ui-test-results.md` (Critical Finding), `UT-02-backend-log-tail.txt`, `docs/handoffs/goal-mcp-loop-iter-26-audit.md` §B1, `reports/phase-goal-mcp-loop-iter-26-ux-regression.md`. |

## Causation note (does not change the verdict)

The crash *frame* (regime `full[:cut]` + the full-universe prefill in `_do_backfill`) is pre-existing, unmodified code — `git diff HEAD` shows iter-26 touched only `config.py`, `config.yaml`, `scoring.py`, `prices.py`, `warmup.py` (+ tests + reports), not `regime.py`/`data_manager.py`/`scanner.py`. So iter-26 cannot be **proven** to have caused the crash. But it is not a proven bystander either: auditor B3 / ux-regression charge that iter-26's cache-aware `close_on`/`bars_after` newly routed the same job's ~6,110 forward-return lookups through `_BarCache` slice allocations (later removed byte-identically in the audit fix-mode pass, reviewer-verified, and measured in isolation NOT to be the VSZ driver — but never measured at the crashing full-universe shape). The verdict does not depend on causation: a critical anti-goal is demonstrably, reproducibly violated on the current tree and is unresolved, so per rule 1 the framework halts for human review — matching the iter-24 memory-crash precedent (also a critical anti-goal #8 halt).

## Next-Step Recommendation

Halt for human review; on `--acknowledge-regression`, iter-27 (FULL) is a dedicated memory-hardening + fix-verification pass, NO new feature/evidence work (out of scope: J-02/06/07/08/09 re-certification — rubric rule 5):
1. **Restore the backend** — the harness-owned process (PID 499553) is wedged/down and browser-qa lacked permission to restart it; bring up both prod-mode services and confirm HTTP-200 before dispatching QA.
2. **Reproduce + gate the crash:** run the full `_do_backfill` "Rebuild snapshots for current universe" (full universe × ~322 cadence dates) under the real `ulimit -v 6291456`, sampling **BOTH VSZ and RSS** (VSZ is the failing metric — an RSS-only probe cannot catch it). Add it to `reports/perf-budgets.md` as a before→after never-regress budget — the shape iter-26's 12-date-subset Item-F measurement omitted.
3. **Fix the root allocation (audit §5.4):** bound/stream the regime/backfill `full[:cut]` allocations and/or the full-universe prefill so the deep-basis rebuild stays under the `ulimit -v` cap; verify byte-identity via `test_scoring_window.py` + `test_forward_testing.py` cache-awareness cases before trusting.
4. **Re-run the full browser lane live:** J-16 (UT-02/UT-03 to a *verified completed* state), UT-04 cold-`/data` OOM repro (iter-24 lesson, mandatory), and a genuine PASS (not SKIPPED) on all eight required-still-passing journeys.
5. Harden the false-positive `/api/health` 200-before-death probe (recurred from iter-24) as a non-blocking carry-forward.

GOAL_ACHIEVED remains out of reach regardless: J-02/06/07/08/09 stay sanctioned-partial on the 30-year all-FAIL ledgers (no staging winner clears divisor-8 today) — the separate priority-2 work after J-16 lands.

## Halt Justification

REGRESSION (decision-tree rule 1): a **critical** anti-goal (#8) is violated by a live, reproduced, backend-wide crash (VSZ exhaustion on the deep basis) and is **unresolved** — the audit deliberately applied NO root-cause fix (unlike iter-24, where the fix was in-tree and iter-25 was pure verification), so no fix exists yet and its scope is open-ended architectural memory work. The framework's fail-closed rule for critical anti-goal violations is to halt for human review, not auto-loop — especially since the next iteration cannot even run its browser lane until a human/harness restarts the wedged backend. Not GOAL_ACHIEVED (J-16 failed + critical anti-goal + 8 required unverified + sanctioned-partials). Not CONTINUE (a critical anti-goal violation halts for human review; it does not auto-dispatch an unattended next iteration). Not STALLED (rule 1 precedes rule 2, and the fix is autonomously-reachable dev work, not a human-owned blocker). Not ESCALATE (already full; review PASSED-with-notes, not fail-open; J-16 is newly failing, not a same-journey 2-consecutive failure).
