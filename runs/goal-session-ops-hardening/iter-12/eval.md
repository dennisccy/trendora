# Iteration 12 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

J-06's two agent-owned EVIDENCE gaps are genuinely closed this iteration: G1 (the 11-page sweep is
transcribed verbatim into the canonical `reports/perf-budgets.md`) and G2 (three cache-disabled fresh-Chrome
`GET /api/indexes?full=true` control readings recorded, cross-checked idle). But the G2 evidence itself is
the finding: the endpoint reads **2257.7 / 2148.2 / 2138.7 ms against its committed ≤1.5 s budget** on a
verifiably idle host (load1 1.48–1.83 < 2.0, mem_avail ~18 GB, no concurrent ingest) — a real, ruled-in
43–51% over-budget condition, not ambient noise. J-06 step 2 requires "assert every measurement is within
budget"; that assertion fails, so J-06 stays **partial** (not `passing`, despite the audit's recommendation).
No journey regressed; the carried critical AG-8 unbounded-load stays unresolved and hard-blocks
GOAL_ACHIEVED. Progress made (G1/G2 closed) with concrete agent-tractable next work → CONTINUE.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing | LLM lane UT-J-01 PASS (`…iter-12-ui-test-results.md`); replay FAIL (step-02 golden flake) reconciled+overturned (`…regression-replay-results.md` footer); DB run 121 zero-work weekend span |
| J-03 | passing | passing | LLM lane UT-J-03/UT-06/UT-07 PASS; 412-day span accepted, 5-chunk plan, no cap; replay FAIL reconciled; DB run 122 |
| J-04 | passing | passing | LLM lane UT-J-04 PASS; steps 5-6 fresh (logfile truncation + runs 124/119/114 `interrupted`); steps 3-4 carried on empty-diff basis; `UT-J-04-step6-live.png` (spot-checked: /data live, Ready) |
| J-05 | passing | passing | LLM lane UT-J-05 PASS; 2025-05-15 snapshot, 6 aggregates, `/scanner-runs/1436` top-3 ZS/NFLX/OKTA DB-verified; `UT-J-05-result.png` (spot-checked: exact match) |
| J-06 | partial | **partial** | G1+G2 closed in `reports/perf-budgets.md` "### G2 (closure)"; but `/api/indexes?full=true` 2257.7/2148.2/2138.7 ms > ≤1.5 s budget on idle host (`UT-02/03/04-reading*.txt`); walkthrough still unproduced. `UT-04-result-top.png`: /data renders fully, no frozen frame |

Note: the deterministic replay lane FAILed J-01/J-03/J-05 on the recurring step-02 `fill` timeout (a
golden-script flake upstream of any journey value); its reconciliation footer overturns it and the merged
`ui-test-results.md` (which wins) records all three PASS on the LLM lane's DB-cross-checked evidence — audit
T1 independently confirms the flake characterization. No product regression.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven-language | OK | J-01…J-06 carry no Evidence Claims; no proven-language shipped. scan-report CLEAN |
| AG-2 decision-quality only | OK | No return/price/buy-sell/order surface added; product diff empty |
| AG-3 displayed numbers correct | OK | UT-10 run-378 top-3 DB byte-exact; UT-J-05 1436 top-3 DB-exact; no fabricated values |
| AG-4 no overfit edges | OK | No referee/claim path touched |
| AG-5 determinism/no-lookahead | OK | Empty source diff; no caching/scoring change |
| AG-6 referee gate | OK | No evidence-derived claim this iteration |
| AG-7 no hard-coded secrets | OK | scan-report CLEAN (only `reports/perf-budgets.md` changed) |
| AG-8 resilience/no unbounded loads | **VIOLATED (critical, UNRESOLVED — carried, NOT re-fired)** | `forward_testing.py:826` unbounded `ScannerResult` load fired live twice this iteration (runs' ingest warm; `logs/backend.log:26920/27185/27233`), caught internally — **zero client-facing 500s this time** (smaller blast radius than iter-11's two 500s). Product diff empty → not introduced/worsened. Hard-blocks GOAL_ACHIEVED; does NOT fire REGRESSION (see below) |
| AG-9 offline-deterministic ingest | OK | No network/paid provider added; scan-report dependency-CLEAN |
| AG-10 host resource ceiling | OK | Both launch scripts keep host-guard block (banner `logs/backend.log:27068` idiom); this iteration's pytest confined `taskset -c 0-3,8-11` + BLAS=4 (dev handoff "Tests Run") |

## Next-Step Recommendation

**Full depth.** Two parallel tracks, keep them separated as prior iterations did:

1. **AGENT-TRACTABLE (the reason this is not STALLED): bring `/api/indexes?full=true` on `/data` into its
   committed ≤1.5 s budget** — this is core J-06 work ("each page's on-load calls read persisted aggregates
   or indexed windowed queries, measured against committed budgets"). goal.md already names the pattern:
   aggregation candidate #7 (normalized index series → a small keyed cache warmed at ingest), so the endpoint
   serves a stored row instead of a ~2.2 s per-request `full=true` computation. This endpoint was ~0.87 s in
   iter-6 and has slowed to ~2.2 s as the basis grew — a real product slowdown, now confirmed under a valid
   idle control. Closing it (or a conscious owner budget-raise, below) is the single item between J-06 and
   `passing`, alongside the walkthrough.

2. **OWNER DECISIONS, do not let an agent invent any of them** (each independently hard-blocks
   GOAL_ACHIEVED): (a) the critical **AG-8** `forward_aggregates_cached` → `compute_forward_aggregates`
   unbounded load (`forward_testing.py:826`) — scope a bounded/streamed rewrite, amend goal.md to accept the
   graceful-abort behaviour, or formally defer; reconfirmed live 3-for-3 this iteration; (b) the
   `/api/indexes?full=true` over-budget endpoint — either sanction the candidate-#7 fix (track 1) OR
   consciously raise its committed budget (a logged decision, never a silent "optimize the budget away");
   (c) `HOST_GUARD_REQUIRE_MARKERS` flip; (d) the `[NEW] demo.sh ops-hardening --session-live` walkthrough —
   this iteration's decomposer PROVED (by reading `run-goal.sh`) there is no autonomous mechanism to produce
   it; needs a human run-once, a goal.md wording amendment, or a framework session-record enhancement.

Framework-maintainer items carried unchanged (never patch `scripts/automation/*` from a product iteration):
`merge_ui_test_results.py` dropped-`**FAIL**` cells, `Frontend Present: no` browser-qa-skip misrouting, the
recurring golden-replay step-02 flake needing an LLM tiebreaker, undisclosed `J-05.json` fixture edit in
`changed_files` (audit T2), and the pre-existing `tests/test_db.py::test_create_all_produces_expected_tables`
failure.

## Halt Justification

Not halting — verdict is CONTINUE. Recorded here for the reader because the honest picture is close to a
holding pattern: J-06's agent-owned EVIDENCE work is now exhausted and what remains is one agent-tractable
perf fix (track 1) plus a cluster of owner decisions (track 2). This is NOT STALLED because track 1 is
concrete, identifiable, agent-owned product work with an implementation path already named in goal.md
(candidate #7). It is NOT REGRESSION: no journey moved passing→failing, and the AG-8 critical entry is the
same carried, human-known, four-times-deferred (iter-8/9/10/11) code path — this iteration introduced nothing
(product diff literally empty per `iter-diff.md` "(no changes)", scan-report CLEAN, coherence-verified) and
did not worsen it (caught internally, zero client 500s vs iter-11's two). A human reading decision-tree C.1
literally may still choose to halt on the unresolved critical AG-8; if so, the four owner decisions above are
the unblock menu. It is NOT GOAL_ACHIEVED: J-06 is `partial` (a committed budget breached 43–51% on an idle
host + the unproduced walkthrough), and AG-8 remains unresolved.
