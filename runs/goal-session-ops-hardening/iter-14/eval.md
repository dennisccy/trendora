# Iteration 14 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The REGRESSION-recovery iteration succeeded at its stated purpose: the session-long critical AG-8 defect
(unbounded whole-partition ORM reads in `compute_forward_aggregates` that wedged the backend into full
availability outages in iter-7 and iter-13) is **resolved** — the two `.all()` reads are now
column-projected `yield_per`-streamed in place, byte-identity is proven (32/32), and the first successful
full-deep-basis 5-horizon warm at this basis size completed with `/api/health` 250/250 HTTP 200 and a flat
`VmPeak` of 2,404,408 KB (61.8% margin under the 6,291,456 KB cap) — all three headline numbers recomputed
by me directly from the retained CSVs. J-04 was additionally re-verified LIVE end-to-end this iteration. Not
GOAL_ACHIEVED: J-06 and J-07 stay `partial` — the `demo.sh --session-live` walkthrough (owner/framework) is
still unproduced, and a genuine P1 browser FAIL (UT-04: a `/backtest` cache-MISS resolved in 211.8 s under a
*concurrent* warm — honest/non-catastrophic, but far outside budget) leaves J-07's "honestly responsive
while serving" edge and J-06's budget open.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing | Golden replay UT-J-01 PASS (`reports/phase-goal-ops-hardening-iter-14-ui-test-results.md`); spot-check `reports/qa/goal-ops-hardening-iter-14-evidence/J-01-verify.png` (opened: `/data` coverage panel real, Ready badge) |
| J-03 | passing | passing | Golden replay UT-J-03 PASS (`…-ui-test-results.md`) |
| J-04 | passing (carried, last-verified iter-12) | passing (LIVE re-verified) | UT-J-04 PASS — real operator kill 12:57:13 / restart 13:01:13; screenshots opened: `…evidence/UT-J-04-02-crash-home.png` (honest "Backend unavailable" badge + NO-GO banner, no spinner/blank), `…-04-initializing.png` ("Initializing… history 89/89"), `…-05-boot-ready.png` ("Ready") |
| J-05 | passing | passing | Golden replay UT-J-05 PASS; spot-check `…evidence/J-05-verify.png` (opened: immutable 2025-05-15 snapshot, Regime 70.76/100 Risk-on, breadth 87.70%/54.10% — matches recorded) |
| J-06 | partial | partial | TC-8 single-source gap CLOSED (`reports/perf-budgets.md:2263` transcribes 218.7/218.7/219.2 ms `/data`, 70.5 ms `/`, all PASS); UT-01 `/data` Ready. Residual: walkthrough unproduced (owner); UT-04 `/backtest` budget breach under concurrent warm |
| J-07 | (new this iteration) | partial | Core availability guarantee proven: TC-5 (`reports/perf-budgets.md:2127-2165`, CSVs recomputed by me — 250/250 health 200, VmPeak 61.8% margin), TC-3 real `ulimit -v` induction, TC-4 concurrency, byte-identity 32/32. Gaps: TC-6 live-process induction only synthetically evidenced; UT-04 (211.8 s concurrent cache-MISS `/backtest`); walkthrough unproduced |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-8 (iter-9 dimension + iter-13 escalation) — resilience / no memory exhaustion / no unbounded ORM load | **RESOLVED** | The unbounded `.all()` reads are removed (iter-diff.md; coherence COHERENCE-PASS confirms in-place, no 2nd producer); full-basis warm completes at 61.8% memory margin with health 200 throughout (CSVs verified by me + reviewer + auditor independently); no wedge/outage/restart (live browser UT-03/UT-J-04). Real `ulimit -v` induction (TC-3) proves honest-abort-and-same-process-recovery. Residual UT-04 latency is NOT an AG-8 crash/memory violation (VmPeak flat, page rendered, health green) — carried as a non-critical follow-up |
| AG-7 (no hard-coded secrets) | OK | scan-report CLEAN; new test files use synthetic fixtures (`SYM000001`…), no credentials |
| AG-9 (offline-deterministic ingest) | OK | scan-report CLEAN (no dependency findings); tests use local SQLite via `make_engine`, no network/paid service |
| AG-10 (host resource ceiling) | OK | launcher host-guard blocks byte-unchanged (out of scope, verified); TC-5 launched via `scripts/start-backend.sh` under caps (`taskset 0-3,8-11`, `ulimit -v` 6144 MB on pid 3669411, perf-budgets.md:2107); pytest host-guard-confined |
| AG-3 (displayed numbers correct) | OK | byte-identity proven (32/32 + independent rerun); reads bucket/setup/sector/rank/regime/flags verbatim, no recomputation (audit §3) |
| AG-5 (no-lookahead) | OK | `as_of` walk-forward membership filter preserved on the streamed statement (iter-diff.md; audit §3) |
| AG-1/AG-2/AG-4/AG-6 (proven-language / orders / overfit / referee) | OK | Pure backend read-path rewrite; no proven-language, no orders, no evidence-claims introduced (J-01…J-07 carry no Evidence Claims per goal.md loop mechanics) |

## Next-Step Recommendation

FULL depth, focused follow-up — no new features.

1. **AGENT (the substantive item):** root-cause UT-04 — a `/backtest` cache-MISS during a concurrent
   forward-aggregate warm resolved in 211.8 s (audit F1 hypothesis: the streamed read holds a longer
   read-lock/cursor window under concurrent writes than the old fetch-and-release `.all()` did). It is the
   exact iter-13 trigger shape (concurrent load on the deep basis) that neither TC-4 (concurrent-on-fixture)
   nor TC-5 (sequential-on-deep-basis) reproduces. Also spot-check `/stocks` / `/sectors` / `/scanner-runs`
   / `/evidence` under a concurrent warm (audit/closure/ux-regression all flag the risk may not be confined
   to `/backtest` if the cause is shared DB/connection contention). Consider an elapsed-time affordance on
   `/backtest`'s skeleton for long cache-misses. This is what stands between J-07 and `passing`.
2. **OWNER DECISIONS (each independently blocks GOAL_ACHIEVED; do not let an agent invent them):** the
   `[NEW] demo.sh --session-live` walkthrough that J-05/J-06/J-07 Acceptance names (no autonomous mechanism
   — established iter-12); whether TC-3's real synthetic-subprocess induction + TC-5's organic absence
   suffice for TC-6, or an operator-authorized live-process induction is still owed (AG-10 hazard on this
   crash-history host — see assumptions.md).
3. **AGENT (non-blocking cleanup):** UT-10 (P3) — the per-horizon heartbeat tick (`data_manager.py:3220`,
   byte-unchanged, sized ~35 s/horizon) is outpaced ~9× so `current_activity` freezes / heartbeat briefly
   reads "possibly stalled" (self-recovering) on a healthy job; reconcile the stale "not done yet" line in
   `implementation-summary.md` (audit B2 / closure Non-Blocking #1). Carried: pre-existing
   `test_db.py::test_create_all_produces_expected_tables` failure (unrelated, no schema change).

## Halt Justification (if halting)

N/A — not halting. Not REGRESSION: no journey moved passing→failing (J-04 improved to a live re-verify), and
the critical AG-8 anti-goal that drove the iter-13 REGRESSION is now RESOLVED with wide, independently-verified
margin — for the first time this session there is no unresolved critical anti-goal. Not STALLED: substantive
agent-tractable work remains (UT-04 root-cause is concrete and cross-cutting; UT-10 cleanup) — the path to
GOAL_ACHIEVED is not purely human-owned. Not GOAL_ACHIEVED: J-06 and J-07 are `partial` (unproduced
walkthrough + UT-04 + TC-6-partial), so no positive evidence of a full pass for two Must-have journeys. Not
ESCALATE: already full depth, all gates PASS/PASS_WITH_NOTES/PASS_WITH_GAPS, no fail-open, no journey failing
twice. Coherence COHERENCE-PASS → no consolidation mandate. Progress made → CONTINUE.
