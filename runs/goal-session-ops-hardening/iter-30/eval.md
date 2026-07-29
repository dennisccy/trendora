# Iteration 30 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

This iteration did what it set out to do, and the proof holds up when checked. The background job
that builds backtest figures used to run out of memory; it now finishes cleanly over the full
30-year data set, and the health check answered 273 out of 273 times while it ran. The page-speed
table was also finally written down. Two things stop this from being finished. First, only two of
the three memory containers named in the plan were fixed — the third one is the exact line that was
crashing before, and it is still unbounded; the audit measured the improvement at about 16-22
percent, which is breathing room, not a fix. Second, the Factor Lab page (J-07-adjacent, two clicks
from the home page) still runs out of memory and shows no figures. Nothing that was working before
broke: all six other journeys replayed green.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | reports/qa/goal-ops-hardening-iter-30-evidence/J-01-verify.png (UT-J-01 PASS, replay 6/6) |
| J-03 No per-run range cap | passing | passing | reports/qa/goal-ops-hardening-iter-30-evidence/J-03-verify.png (UT-J-03 PASS) |
| J-04 Non-blocking boot with visible status | passing | passing | reports/qa/goal-ops-hardening-iter-30-evidence/J-04-verify.png (UT-J-04 PASS) |
| J-05 Aggregates are precomputed at ingest | passing | passing | reports/qa/goal-ops-hardening-iter-30-evidence/J-05-verify.png — spot-check #1, opened |
| J-06 Pages load only what they need | partial | partial | reports/perf-budgets.md lines ~3946-4022 (opened); NO J-06 replay row, NO J-06 capture this iteration |
| J-07 Heavy aggregates never take the service down | partial | partial | reports/phase-goal-ops-hardening-iter-30-ui-test-results.llm.md TC-01/TC-04 PASS (log/API only, no capture) |
| J-08 Backtest evidence serves from storage only | passing | passing | reports/qa/goal-ops-hardening-iter-30-evidence/J-08-verify.png (UT-J-08 PASS) |
| J-09 Backend discloses background-compute activity | passing | passing | reports/qa/goal-ops-hardening-iter-30-evidence/J-09-verify.png — spot-check #2, opened |

Newly passing: none. Newly failing: none. Regressed: none. Unknown: none.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven-language backing | OK | No evidence-claim, ledger or badge code in the diff (5 product files: `forward_testing.py`, `config.py`, `config.yaml`, one test file, `perf-budgets.md`, plus a README sentence). |
| AG-2 decision-quality only | OK | No return promise, target or order path added; no frontend file touched. |
| AG-3 displayed numbers correct | OK | 38 fixture assertions prove `compute_forward_aggregates` is byte-identical pre/post-change (5 horizons x chunk widths 1/2/4/100 x with/without `as_of`); audit T5 confirmed the reference oracle was not weakened (test diff is append-only past line 318). |
| AG-4 no overfit edges | OK | No referee, holdout or claim logic in the diff. |
| AG-5 determinism / no-lookahead | OK | `as_of` cutoff moved up into the run-discovery query, upstream of every derived structure; a dedicated no-lookahead test was added and passed. |
| AG-6 referee gate | OK | No evidence-derived claim introduced (goal.md Loop mechanics: J-01..J-06 carry none). |
| AG-7 no hard-coded credentials | OK | `scan-report.md`: CLEAN — no secret, dependency or license finding on added lines. |
| AG-8 resilience to data-scale change | **VIOLATED — 4 findings open, all minor, none new this iteration** | See below. |
| AG-9 offline-deterministic ingest | OK | No new dependency or manifest entry; the backfill ran against the committed seed (`provider: seed` in every capture). |
| AG-10 host resource ceiling | OK | No launch script in the diff; every boot banner in `logs/backend.log` this window carries the host-guard block (`memory_cap_mb=6144 cpu_list=0-3,8-11 blas_threads=4`), and the host stayed above 13.7 GB free memory with `psi_mem_avg10` at 0.00 throughout. |

**AG-8 detail — four open findings, all carried from iteration 29, none introduced by this diff:**

1. **`/research/factor-lab` runs out of memory** (`research.py:583`, `_all_factor_observations_by_horizon`).
   Re-confirmed live by this iteration's own required spot-check TC-05, which FAILED
   (`logs/backend.log:132232-132302`). The accumulator was bounded at iteration 29 but the returned
   `pools[h]` list still is not — its own docstring says "NOT bounded here (deliberate)" — about
   771,129 entries times 5 horizons. **2nd consecutive iteration unresolved.**
2. **Boot warm-up** (`warmup.py:194`) — no recurrence this window; the live health capture reads
   `readiness: ready`, `warmup {done:89, total:89, status:"ok"}`.
3. **`compute_forward_aggregates`** — the finding this iteration targeted. Operationally closed (zero
   MemoryError through a real full-basis warm), structurally not: `stock_obs`
   (`forward_testing.py:988`) is still unbounded and is the exact line that crashed before.
4. **Ingest coverage refresh** (`prices.py:141`) — no recurrence this window; explicitly deferred.

**Why minor, not critical (stated, not assumed).** I opened
`reports/qa/goal-ops-hardening-iter-30-evidence/TC-05-factor-lab-fail.png`: the page is fully drawn —
navigation, header, intro copy, analysis-mode toggles, survivorship-bias notice — with a calm bordered
box reading "Backend unavailable — The Factor-Lab evidence could not load from the API. No figures are
shown rather than fabricated values." and a global "NO-GO — do not rely on today's board." banner. AG-8's
own remedy clause is met and nothing is fabricated. The browser-QA and UX-regression reports both claim
the memory error "terminated the entire backend process"; **the log disproves that** — uvicorn's
signal-initiated `INFO: Shutting down` sits at line 132229, three lines *before* the traceback starts at
132232, and the identical error at lines 127815 and 129033 returned clean 500s with the process
surviving. Six later requests to the same endpoint returned 200 OK. This follows the iteration 26/27/28/29
precedent, which classified live memory failures minor on the same grounds and was not overruled.

## Pipeline-integrity findings (not anti-goals, but they gate any future "goal achieved" claim)

1. **A P1 FAIL was laundered into a canonical "PASS".** `phase-goal-ops-hardening-iter-30-ui-test-results.md`
   — the file this role reads — says "Browser QA Verdict: PASS, 6/6 journeys passed". The authoritative
   `...-ui-test-results.llm.md` says "FAIL, 3/5 tests passed (1 failed, 1 skipped)". Root cause proven by
   the audit (T2): `merge_ui_test_results.py`'s row pattern matches only `UT-` ids, browser-QA emitted
   `TC-01..TC-07`, so every one of its rows was dropped and its FAIL headline discarded. This is the exact
   failure that could rubber-stamp a goal-achieved verdict.
2. **The audit's own TC-07 result has no artifact.** The audit states it ran the `J-06.json` replay and it
   passed. I searched `reports/`, `runs/`, the repository and this run's temp directory: no results file,
   no screenshot, nothing dated 2026-07-29. It is prose only.
3. **The pipeline advanced fail-open.** Browser-QA FAIL, ux-regression UX-REGRESSION-FAIL and closure
   CLOSURE-FAIL all survived into evaluation.

## Next-Step Recommendation

Run the next iteration at full depth, with one main target and small ride-alongs.

1. **Main target: make the Factor Lab page stop running out of memory.** Bound the list it builds
   (`research.py:583`, `pools[h]`) the same way its accumulator was bounded, and add the missing
   "only one compute at a time" guard that `factor_lab_all_cached` lacks — the audit found the cache row
   was written successfully at 02:10:54 while a duplicate compute of the same thing was still running.
   Then open the page in a real browser on an idle machine and capture the decile table and rank-IC
   figures. This is the second time this exact item has been deferred.
2. **Finish J-07 "Heavy aggregates never take the service down":** bound `stock_obs`
   (`forward_testing.py:988`). This deliberately means changing `_attribution_slices`'s frozen
   `(stock_obs, cfg)` signature and re-pinning the tests that assert it — the planner must say so out
   loud. Also record the warm's peak memory and its margin under the declared cap in
   `reports/perf-budgets.md` (J-07 step 3, never done).
3. **Ride-alongs, capture only, never the goal of an iteration:** run `J-06.json` through the
   deterministic replay lane so a real PASS row exists (unmet since iteration 28), and have browser-QA do
   the real-browser page-speed pass so J-06 step 1's "time to interactive" half is measured rather than
   inferred from a command-line timing.
4. **Framework fix, queue it outside the journey loop:** widen the merge script's row pattern to accept
   `TC-` ids and make any input file's FAIL headline survive the merge. Until that lands, the canonical
   test-results file cannot be trusted to show a failure.
5. **Carried, unchanged:** audit B2 (`_backfill`'s cross-call rollback residual); the boot warm-up and
   ingest-coverage memory faults, still deferred; UT-04's fresh-install database fixture or a written
   waiver; the four `is_latest` monkeypatches in `test_forward_testing_serving_split.py`.
6. **Owner, non-blocking:** `GET /api/health` measured 0.127787s against its 0.1s budget, and ran
   0.094-2.431s while heavy compute was in flight. Until that budget line is amended or rescoped,
   J-06 step 2's "every measurement is within budget" and J-07 step 2's "within its existing budget"
   can never both read true. This is the one decision no agent can make.
7. **Framework nit, 10th recurrence:** `J-01-verify.png`, `J-03-verify.png` and `J-04-verify.png` are
   byte-identical (md5 `fb5f582b`), so two of those three journeys have no independent picture this run.

What should happen next, in one sentence: approve one more full-depth build whose single job is to stop
the Factor Lab page running out of memory and to finish the last memory bound in the backtest warm-up,
and separately decide whether the 0.1-second health-check budget should be relaxed.
