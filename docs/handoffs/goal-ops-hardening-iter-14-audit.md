# goal-ops-hardening-iter-14 Audit Report

**Date:** 2026-07-23
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal is achieved and independently verified: the session-long critical AG-8 defect (unbounded whole-partition ORM reads in `compute_forward_aggregates` that caused the iter-7 and iter-13 full-availability outages) is closed. The two named reads are now column-projected `yield_per`-streamed with byte-identical output (I re-ran the suite myself: 35/35 pass), the first successful full-deep-basis 5-horizon warm this basis size has ever completed ran with `/api/health` 250/250 HTTP 200 and `VmPeak` 2,404,408 KB / 61.8% margin (recomputed by me directly from the retained CSVs). Real, non-monkeypatched memory-cap induction and concurrent-caller resilience are proven. Documented, honestly-surfaced gaps remain — chiefly UT-04 (`/backtest` cache-miss under a *concurrent* warm resolves in 211.8 s, a prior-phase budget violation, not a wedge) and TC-6 (live induced-pressure not executed on the measured process) — all outside iter-14's stated scope and none compromising the goal's own availability definition. No CRITICAL or IMPORTANT issue survives; no audit fix was required or applied.

---

## 2. Findings

### Backend Findings

**B1 — GAP (observation): the fix bounds the READS but the accumulators are still O(total rows) — memory remains linear in basis size.**
`apps/backend/app/engine/forward_testing.py:844-852, 875-906` — the rewrite streams the two reads (no `.all()` of ORM objects, `record_json` blobs excluded from the projection), but it still accumulates every row into `ret_by_run_symbol` / `mdd_by_run_symbol` (line 844-847) and `stock_obs` (line 875). The memory win is a large constant-factor reduction (no full ORM objects, no JSON blobs, no intermediate `fr_rows`/`results` lists held alongside the derived dicts), empirically 587 MB → 255 MB on the 60K-row TC-3 fixture and 2.40 GB peak on the real basis — but growth is still linear. At today's ~9× basis the margin is 61.8%; a further ~2.5× growth would revisit the 6144 MB cap. This is **not a spec deviation** — the DEFINITION OF DONE scopes only "the two whole-partition ORM reads … to column-projected, `yield_per`-streamed access," which is fully satisfied, and the byte-identity acceptance criterion structurally precludes a deeper streaming-aggregation rewrite (the downstream helpers consume the whole `stock_obs` list). Recorded as a forward-looking limitation; the measured 61.8% margin (TC-5) honestly bounds it. No fix applied (out of scope; a fix would break byte-identity).

**B2 — OBSERVATION: `implementation-summary.md` is stale and contradicts the canonical result.**
`reports/phase-goal-ops-hardening-iter-14-implementation-summary.md:45` still lists under "Incomplete Items" that "The full-scale, real-database measurement pass is not done yet," while the dev handoff's later same-day "Operator-Supervised Measurement Transcription" section and `reports/perf-budgets.md:2089-2231` record TC-5/TC-7 as CLOSED PASS. Zero product impact (both describe an internal measurement step) and already flagged by the ux-regression report. Noted, not fixed — the canonical single-source artifact (`perf-budgets.md`) is correct, and editing a showcase/summary artifact for a documentation-freshness nit is scope creep per the auditor's own severity rules.

### Frontend Findings

*(No frontend file was touched this iteration — `git status` confirms `apps/frontend/` is empty in the diff. These findings are on prior-phase surfaces that sit behind the rewritten function, surfaced by the browser-qa and ux-regression lanes.)*

**F1 — GAP: `/backtest` cache-miss during a concurrent forward-aggregate warm resolves in 211.8 s (UT-04).**
`reports/phase-goal-ops-hardening-iter-14-ux-regression.md:61,118-122` — a tab opened at a cache-miss while a concurrent warm ran stayed on `BacktestSkeleton` to 135.5 s and resolved at 257.4 s; the resolving `GET /api/backtest` measured 211,829 ms via the browser's Resource Timing API. This is a ~580–1500× violation of the page's committed budgets (≤1.5 s per `perf-budgets.md`; ≤2 min this iteration's UX bound). **It is not the iter-7/iter-13 catastrophic mode** — no crash, no red "Backend unavailable" card, the readiness badge stayed healthy, `/api/health` stayed green, and the read self-resolved. I considered rating this IMPORTANT (a committed budget fails in a realistic scenario — a user opening `/backtest` during a backfill). I land on **GAP** because: (a) the ≤1.5 s budget belongs to a *prior* phase (iter-5/J-06) under a concurrent-cache-miss condition that phase never tested — it is not one of iter-14's DEFINITION-OF-DONE items; (b) the phase goal's own definition of "available and honestly responsive" (`/api/health` keeps answering; no page freezes on a blank "Checking backend…" frame; the catastrophic wedge is gone) is independently verified met; (c) the finding is honestly surfaced by two agents, not hidden; (d) a real fix (root-cause the contention, add an elapsed-time affordance / optimize the endpoint) is explicitly out of scope, cross-cutting, and not a surgical audit fix. **Undiagnosed root cause** (the dev handoff declines to assert one; ux-regression flags plausible DB/connection contention). Worth an explicit follow-up hypothesis for the next iteration: the streamed read holds a cursor over `forward_returns`/`scanner_results` open for the duration of iteration, which *may* contend more with the concurrent warm's writes than the old fast `.all()` fetch-and-release did — i.e. the fix may trade peak memory for a longer read-lock window under concurrent load. This is a hypothesis, not a verified claim; it is the exact "concurrent load on the deep basis" condition that neither TC-4 (concurrent-on-fixture, no cap) nor TC-5 (sequential-on-deep-basis) reproduces.

**F2 — GAP (P3): `current_activity` frozen and a false "possibly stalled" heartbeat during the long warm (UT-10).**
`reports/phase-goal-ops-hardening-iter-14-ux-regression.md:63,123-129` — the job-progress heartbeat briefly read "possibly stalled" (~103 s, self-recovering) and `current_activity` stayed pinned on "scanning 2026-07-21 (1/1)" for the entire ~6.8-min run. This is iter-4's deliberate per-horizon-tick tradeoff (`apps/backend/app/engine/data_manager.py:3220`, a bare `prog.tick()` sized against an assumed ~35 s/horizon, left frozen to preserve `test_progress_payload_has_heartbeat_and_activity`) now outpaced by the same ~9× data growth this iteration is about. `data_manager.py` is **byte-unchanged** this iteration (out of scope), so this is exposed, not introduced. A false "stalled" reading on a healthy job is a minor honesty-of-responsiveness blemish. Honestly surfaced; not surgically fixable without touching the tick cadence and an existing test assertion (both out of scope).

### Test Findings

**T1 — Positive assessment (no defect): the new tests are high-quality and genuinely discriminating.**
- Byte-identity (`tests/test_forward_testing_aggregates_streaming.py`): the reference `_reference_compute_forward_aggregates` (lines 46-154) is a faithful pinned copy of the pre-rewrite body — same two `.all()` reads (lines 55, 61), matching the `git diff` exactly, calling the same unchanged downstream helpers — so any divergence is attributable only to the rewritten reads. Distinct-per-cell returns (line 191-195) turn a misaligned projection into a wrong mean; a dedicated test proves the historical `as_of` genuinely narrows the pool (line 282-291); the n=0 zero-FR run is exercised (line 294-303); parametrized across batch sizes `[1, 3, 1_000_000]` proves chunk-boundary independence; sanity asserts guard against empty-dict false passes (line 278-279). The dev's mutation check (column-swap → 31/32 fail) confirms discriminating power.
- Byte-identity is airtight on **any** basis, not merely the fixture: `_mean_or_none`/`_group_means` use `statistics.mean` (`forward_testing.py:41,517,553`), whose CPython implementation sums via exact `Fraction` arithmetic and is therefore summation-order-independent; `ForwardReturn` carries `UniqueConstraint(run_id, symbol, horizon)` (`models.py:388`) so per-horizon dict keys never collide; every output ordering uses explicit `sorted(key=...)`. The added `.order_by(ScannerResult.id)` (line 881) is harmless belt-and-suspenders that makes the rewrite *more* deterministic than the prior unordered `.all()`.
- TC-3 (`tests/test_forward_testing_concurrency.py:184-231`) is a **real** `bash -c "ulimit -v 420000"` subprocess induction (RLIMIT_AS, not monkeypatch), with a verbatim pre-rewrite `.all()` probe proven to raise `MemoryError` under the cap while the rewritten function succeeds under the *identical* cap, plus a same-process `ForwardAggregateCache` recovery read and a hang-vs-slow timeout guard. TC-4 (line 250-280) runs 4+1 concurrent callers on a shared file-based engine with a byte-identity cross-check.
- **Honest limitation (already captured by TC-6-partial and F1):** neither TC-4 nor TC-5 reproduces the exact iter-13 trigger — concurrent load *on the deep basis* — and UT-04 shows that precise condition still produces a latency anomaly. This was deliberately not reproduced (AG-10 host protection on a two-hard-reset host) and the spec did not require it. Not a test defect; a bounded evidence gap, honestly disclosed.

---

## 3. Domain Assessment

The domain logic is correct and the change is genuinely surgical. `compute_forward_aggregates` remains the single canonical forward-aggregate producer: it is called only by `forward_aggregates_cached` (same module, line 1035), which is called only by `GET /api/backtest` (`app/api/backtest.py:72`), the MCP `query_backtest` tool (`app/mcp/tools.py:205`), and the ingest finalize warm (`app/engine/data_manager.py:3230`) — all three **byte-unchanged** (`git status` confirms). `research.py` references the function only in comments, not calls. This satisfies TC-11's sole-producer expectation (formally the coherence-auditor's, but grep-confirmed here). The rewrite reads bucket/setup/sector/rank/regime/flags verbatim from the snapshot (no recomputation → AG-3/AG-5 preserved), and the `as_of` walk-forward membership filter is preserved on the streamed statement (`forward_testing.py:840-843`), keeping no-lookahead intact.

The core reliability guarantee is met and **measured on the real basis**, not merely asserted: I recomputed the retained CSVs (`runs/goal-ops-hardening-iter-14/tc5-health.csv`, `tc5-vm-samples.csv`, 250 rows each) — 250/250 `GET /api/health` HTTP 200 (zero non-200; max latency 1.4436 s), `VmPeak` a flat 2,404,408 KB throughout = 38.2 % of the 6,291,456 KB cap (61.8 % margin), boot-to-first-200 1.80 s. iters 11-13 aborted this exact warm 3-for-3 with `MemoryError`; this pass completed it. The anti-goals are respected: AG-8 is the defect being closed; AG-10 launcher confinement is untouched (`scripts/`, host-guard byte-unchanged; TC-5 launched via `scripts/start-backend.sh`); AG-7 (no secrets — synthetic fixtures only) and AG-9 (offline — local SQLite fixtures, no network) hold.

The honest bound on the guarantee: it is proven for single-caller load on the deep basis and for concurrency on a fixture; it is **not** proven for concurrent load on the deep basis, where UT-04 shows a real (non-catastrophic) latency regression. The reporting chain treats this with exemplary honesty — the dev handoff, `perf-budgets.md` (TC-6 explicitly "evidence recorded, NOT self-scored — evaluator decides", lines 2182-2216), the QA report, and the ux-regression WARN all surface it rather than round up.

---

## 4. Fixes Applied During This Audit

None. All findings are GAP- or OBSERVATION-level — real limitations the spec did not require solving, all honestly surfaced, none compromising the phase goal, and none surgically fixable without scope creep or breaking the byte-identity contract. Per the auditor severity rules, CRITICAL/IMPORTANT are fixed and GAP/OBSERVATION are documented; nothing here rose to CRITICAL or IMPORTANT.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fix required or applied |

---

## 5. Recommended Next Step

**Proceed** — score J-07/J-06 at the evaluator gate. The iteration's own deliverable (bounded/streamed rewrite, byte-identity, real memory-cap induction, concurrent-caller resilience, full-deep-basis availability) is complete and independently verified; the system is materially stronger than before this iteration (a critical defect behind two full outages is closed with wide, measured margin).

Two items for the evaluator to weigh explicitly when scoring J-07 (both already disclosed, neither an audit-fixable code defect):
1. **TC-6 sufficiency** — decide whether TC-3's real synthetic-subprocess induction plus TC-5's organic-absence evidence satisfy J-07's induced-pressure clause, or whether a follow-up live-induction pass is still owed. The spec assigns this call to the evaluator.
2. **UT-04 (`/backtest` 211.8 s under concurrent warm)** — decide whether J-07's "serving … honestly responsive" clause extends to the concurrent-cache-miss case. If so, treat it as a scoped follow-up, not an iter-14 blocker: (a) root-cause the contention (DB/connection vs. compute-under-GIL vs. the longer-held streamed-read cursor hypothesis in F1), (b) consider an elapsed-time affordance for long cache-misses, (c) spot-check other data-reading pages under a concurrent warm, and (d) revisit iter-4's per-horizon heartbeat cadence (F2) now that a single horizon's compute outruns its ~35 s sizing assumption. All four are new-iteration scope, not corrections to this one.
