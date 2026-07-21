# Iteration 7 Evaluation

**Verdict:** REGRESSION
**Depth Recommendation For Next Iteration:** full

## Summary

The J-06 target fix (warm `/evidence`'s per-claim `drawdown_expectations` at ingest finalize)
is genuinely delivered and verified — first `/evidence` view after a real ingest measured 22.4ms
in a real browser, byte-identical values, honest gating. BUT the browser-qa lane (authoritative
RAW verdict = **FAIL**) directly observed **J-05 (required-still-passing, `passing` since iter-6)
break on its literal acceptance step**: `GET /api/health` went completely unresponsive for 7+
minutes during a heavy ingest job, the backend hit its own enforced `memory_cap_mb=6144`
`ulimit -v` ceiling with a worker-thread `MemoryError`, all 22 threads idle in `futex_do_wait`,
and it required a manual restart to recover. That is decision-tree item 1 (a journey moved
`passing`→`failing`) → REGRESSION. The merged `ui-test-results.md` top-line reads "PASS" — that is
the known priority-blind merge-script rollup bug (iter-6 lesson); the merged TABLE and the RAW
`.llm.md` both correctly record UT-J-05 as FAIL, and the screenshot corroborates.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing | deterministic replay UT-J-01 PASS · reports/qa/goal-ops-hardening-iter-7-evidence/J-01-verify.png (spot-checked: healthy "Ready" Data Manager, 591 symbols, coverage populated) |
| J-03 | passing | passing | deterministic replay UT-J-03 PASS · reports/qa/goal-ops-hardening-iter-7-evidence/J-03-verify.png |
| J-04 | passing | passing | LLM UT-J-04 6-step full-acceptance PASS · reports/qa/goal-ops-hardening-iter-7-evidence/J-04-initializing-badge.png (spot-checked: "Initializing… history 89/89" pre-ready badge = step-4 assertion) |
| **J-05** | **passing** | **regressed** | RAW browser-qa UT-J-05 **FAIL** — 7+ min `GET /api/health` connection-timeout during heavy ingest, `MemoryError` at the 6144MB cap, manual restart required · reports/qa/goal-ops-hardening-iter-7-evidence/J-05-backend-hung-checking.png (frozen "Checking backend…" skeleton) |
| J-06 | partial | partial | Target `/evidence` warm verified fixed (UT-02 22.4ms real-browser first-view, drawdown_expectations warmed, byte-identical) BUT overall browser-qa FAIL + a live `/api/backtest`→`forward_aggregates_cached`→large `ScannerResult` `MemoryError` on an on-load path + frozen-frame during the hang → not a clean pass · reports/qa/goal-ops-hardening-iter-7-evidence/UT-02-evidence-fast-first-view.png |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 / AG-4 / AG-6 (proven-language) | OK | No proven/edge language; all 7 ledger claims are FAIL/non-proven, untouched by the diff. |
| AG-2 (decision-quality only) | OK | No return promises/targets/orders; warm reuses existing read-only compute. |
| AG-3 (displayed numbers correct) | OK | TC-3 asserts warmed payload byte-identical to a fresh `compute_drawdown_expectations` (`stored == fresh`); audit re-traced identical cache keying warm-side vs read-side. |
| AG-5 (no lookahead) | OK | Warm calls the SAME barrier-respecting `compute_drawdown_expectations_cached` the live path already uses. |
| AG-7 (no secrets) | OK | scan-report CLEAN; diff is `data_manager.py` + its test only — no config/env/secret files. |
| **AG-8 (no memory exhaustion / graceful degrade on deep basis)** | **CONCERN (critical, attribution contested)** | Live-observed `MemoryError` exhausting the backend during heavy ingest on the grown live DB, hanging health 7+ min (ungraceful — the UI showed an ambiguous frozen "Checking backend…" rather than the honest "Backend unavailable" state, and it needed a manual restart). This is the exact failure mode AG-8 exists to forbid. Attribution to iter-7's diff is contested (earlier unrelated `/api/backtest` MemoryErrors predate the test → pre-existing capacity fragility), but the new synchronous per-claim warm runs on the ingest finalize hot path and browser-qa explicitly declined to wave it away as unrelated. Recorded as an unresolved violation for human adjudication (fail-closed). |
| AG-9 (offline ingest) | OK | No network; audit's `test_finalize_hook_makes_no_network_call` confirms zero socket.connect. |

## Next-Step Recommendation

Human review, then a full-depth recovery iteration targeting J-05 (and the AG-8 dimension):
1. **Root-cause the heavy-ingest health hang.** The backend hits its enforced `memory_cap_mb=6144`
   `ulimit -v` ceiling on a second back-to-back heavy ingest on the grown live DB; a worker-thread
   `MemoryError` leaves `/api/health` hung (all threads `futex_do_wait`) instead of degrading —
   requiring manual restart. Determine whether iter-7's new **synchronous per-claim
   `drawdown_expectations` warm** (7 `compute_drawdown_expectations` calls appended to every heavy
   ingest's finalize) materially raised peak RAM; if so, bound/defer/stream it so ingest finalize
   adds no peak.
2. **AG-8 graceful-degradation hardening.** On `MemoryError`, health must fail-fast to the honest
   "Backend unavailable" state (J-04's promise) and the worker pool must recover without a manual
   restart — never an indefinite ambiguous "Checking backend…" hang.
3. **The `/api/backtest`→`forward_aggregates_cached`→large `ScannerResult` MemoryError** is a
   separate on-load-endpoint memory exhaustion (itself a J-06/AG-8 concern) — audit/measure it.
4. Re-run J-05's heavy-ingest health step live to confirm recovery before re-attempting closeout.

Note: J-06's `/evidence` cold-miss target is genuinely closed — do NOT redo the drawdown warm
itself; the blocker is the availability/capacity failure it surfaced, not the warm's correctness.

## Halt Justification

Halting per decision-tree item 1: J-05, a Must-have required-still-passing journey verified
`passing` in iter-6 ("health 200 on 20/20 polls during the job"), is now verified `failing` on
its explicit acceptance ("while a heavy ingest job runs, poll GET /api/health; assert it stays
responsive throughout") — a 7+ minute total health hang requiring manual restart, with a
corroborating screenshot and `/proc` + log evidence. This is not adjudicable as a false positive
(unlike iter-5's stale golden-script proxy): it is the literal acceptance step, live-observed with
rich evidence, on the very code path (`_refresh_ingest_aggregates` ingest finalize) this iteration
modified. The upstream review/QA/audit PASSes are not counter-evidence — none exercised J-05's
heavy-ingest step, and the audit explicitly deferred journey pass/fail to this evaluator while
asserting (empirically refuted here) that the diff "cannot have regressed those journeys." A human
should review because (a) a required journey broke, (b) causal attribution to the diff is genuinely
contested, and (c) the fix likely needs a capacity/architecture decision (bound the ingest-time
warm vs. tune the memory cap vs. make heavy paths fit). Resume after manual fix with
`--acknowledge-regression`.
