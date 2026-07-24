# Iteration 17 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The load-bearing B1 cross-`asof_key` fallback landed and is correct — the resolver now serves the most
recent OLDER complete evidence (labeled with the new `evidence_asof`) instead of a fresh-install
`not_yet_computed` when the latest date advances mid-warm, verified by 15 unit tests (reviewer + QA +
auditor each re-ran green), a strictly-older AG-5 SQL check, and AG-3 byte-identity. Two states that had
zero live evidence before now have it: `not_yet_computed` (TC-09, first browser capture this session) and
the corrected refreshing banner with `evidence_asof` (TC-07); the auditor additionally found and fixed a
real UI-truthfulness defect (F1 — window labels bound to the requested, not the served, as-of) that
review and QA both missed. No journey crossed to `passing` and none regressed: J-06/J-07/J-08 stay
`partial`, held by the un-remediated ≤1.5 s serving-budget breaches (11/68, max 12.655 s) which this
iteration narrowed but did not pin (no fresh TC-10 measurement). The remaining work is agent-tractable
(add per-request timing instrumentation, then diagnose/mitigate), so this is CONTINUE, not STALLED.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing | Deterministic replay UT-J-01 PASS; spot-check `reports/qa/goal-ops-hardening-iter-17-evidence/J-01-verify.png` |
| J-03 | passing | passing | Deterministic replay UT-J-03 PASS; `reports/qa/goal-ops-hardening-iter-17-evidence/J-03-verify.png` |
| J-04 | passing | passing (carried) | UT-J-04 SKIPPED (no kill/restart this iter); TC-11 steady-state sanity: `GET /api/health` 200/`ready`, no new crash banner; code surface untouched (not in the 8-file diff) |
| J-05 | passing | passing | Deterministic replay UT-J-05 PASS; spot-check opened `reports/qa/goal-ops-hardening-iter-17-evidence/J-05-verify.png` (immutable stored snapshot as-of 2025-05-15, "never recomputed for today") |
| J-06 | partial | partial | 11/68 ≤1.5 s breaches stand (max 12.655 s) — `reports/perf-budgets.md` iter-17 section; TC-10 not re-measured. Page renders fully (TC-07) — honest-status holds; budget clause fails |
| J-07 | partial | partial | Core AG-8 memory/availability guarantee holds (resolved since iter-14; `compute_forward_aggregates` byte-unchanged); health truthful (TC-11); served-from-storage correct for gap-shape; latency shared with J-06 |
| J-08 | partial | partial | B1 fix correct (15 unit tests, `test_forward_testing_serving_split.py`); live `not_yet_computed` `reports/qa/goal-ops-hardening-iter-17-evidence/TC-09-not-yet-computed-state.png`; live refreshing banner `.../TC-07-refreshing-banner-with-asof.png`; cross-boundary render `.../AUDIT-A1-crossboundary-refreshing-after-fix.png`. Held by ≤1.5 s budget (step 2), not by TC-8 |

No status changed this iteration (no journey newly passing, newly failing, or regressed).

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 (proven-ness backed by ledger) | OK | J-06/07/08 are ops journeys, no evidence claims; `evidence_asof` is a date label, not a proven-ness assertion |
| AG-2 (decision-support only) | OK | No return promises / orders; unchanged surface |
| AG-3 (displayed numbers correct) | OK | Served aggregates byte-identical to stored rows (reviewer + auditor); F1 fix *improved* truthfulness (window label now matches served as-of) |
| AG-4 (no overfit edges) | OK | No proven-language introduced |
| AG-5 (no-lookahead) | OK | Fallback filter is strictly `asof_key < requested` (SQL-verified, TC-5); a future-dated complete key would win the tie-break if admitted and is not |
| AG-6 (referee gate) | OK | No evidence-derived claims this iteration |
| AG-7 (no secrets) | OK | scan-report.md CLEAN (no secret/dependency/license findings) |
| AG-8 (data-scale resilience) | OK | `compute_forward_aggregates` byte-unchanged; the widened fallback query materialises older `payload_json` but is bounded by distinct-as-of count (~650 KB worst case today, 25 rows), NOT the deep price basis — auditor B1 explicitly not an AG-8 violation. Cheap follow-up (project metadata columns first) noted |
| AG-9 (offline-deterministic) | OK | No external network/adapter added (dev handoff Pre-Handoff Verification N/A) |
| AG-10 (host resource ceiling) | Minor lapse, disclosed + corrected | Operator relaunched the TC-9 throwaway backend with raw `uvicorn` (bypassing caps) then corrected via `scripts/start-backend.sh`; auditor /proc-verified the current :18255 listener is capped (address-space 6 GiB, affinity 0-3,8-11). NO launch script modified (`scripts/` untouched) → no code-level regression. Recorded minor+resolved (as with iter-8/iter-10) |

## Next-Step Recommendation

FULL depth, no new features — resolve the latency question that holds J-06/J-07/J-08 short of `passing`.

1. **AGENT (the unblocking step):** add per-request timing instrumentation to the `/backtest` serving
   path (a wall-clock-timestamped response-timing log line). `logs/backend.log` currently has ZERO
   per-request timestamps (dev + auditor confirmed by grep), so the two surviving candidate mechanisms
   (SQLite writer/checkpoint contention vs. GIL/threadpool scheduling from the ingest thread) are
   indistinguishable — this is exactly why TC-10 could not diagnose anything this iteration.
2. **OPERATOR (AG-10-class, one pass):** re-run the deep-basis 68-poll TC-10 protocol WITH the new
   instrumentation, recorded in `reports/perf-budgets.md` directly comparable to the iter-16 baseline
   (11/68, max 12.655 s) — this pass finally distinguishes the mechanism instead of re-confirming the baseline.
3. **AGENT then OWNER-fork:** apply a bounded mitigation IF the diagnosis reveals a fixable contention
   (e.g. checkpoint/WAL tuning, ingest commit-batching) → budget met → J-06/J-08 pass. If the residual
   is confirmed a hard, unavoidable contention cost, route the ≤1.5 s budget-amendment to the OWNER
   (a conscious logged `perf-budgets.md` change, never a silent loosening — iter-15 option 3 precedent).
   The fork only fires AFTER the agent-owned diagnosis; it is not a blocker now.
4. **AGENT (cheap wins, non-blocking):** project the four metadata columns in the widened fallback query
   before reading payloads (auditor B1), and add one endpoint-level test carrying an OLDER `evidence_asof`
   through `backtest()`/`query_backtest()` (auditor T1 — the only cross-boundary value with no
   endpoint-level test today).
5. **TC-8 (cross-boundary live capture) is NOT a next-iteration blocker.** It is unproducible on the
   committed seed (`MAX(daily_prices.date)` = `MAX(scanner_runs.asof_date)` = `2026-07-22`,
   auditor-verified; advancing it needs new price data, which AG-9/AG-5 forbid fabricating — an
   owner-owned data-cycle action). I rule the resolver unit tests + the audit's client-side cross-boundary
   render + the same-key live banner a sufficient evidence floor for B1's code correctness (see assumptions.md).
6. **OPERATOR (still owed before any GOAL_ACHIEVED):** a fresh live J-04 kill/restart replay — carried
   since iter-14; TC-11's steady-state health poll is a sanity check, not a substitute.

## Halt Justification (if halting)

N/A — not halting.

Rejected REGRESSION: no journey moved `passing`→`failing` (J-01/03/04/05 stay passing, J-06/07/08 stay
partial) and no unresolved critical anti-goal (all 9 recorded violations `resolved: true`; the AG-10
operator lapse is minor, disclosed, corrected, no script change). The browser-QA OVERALL = FAIL is a
single test (UT-01) traced to an operator dev-server build-directory collision, independently re-verified
environmental by the auditor and coherence-auditor (implicated files `readiness-provider.tsx`,
`health-badge.tsx`, `preflight-banner.tsx`, `app/data/page.tsx` are NOT in this iteration's 8-file diff —
I confirmed against `iter-diff.md`; `/backtest` renders fully in TC-07/TC-09/AUDIT-A1) — not a product
regression.

Rejected STALLED (iter-15's verdict on the same latency surface): iter-15 halted because the cost was
KNOWN (a cold full-basis compute) and only the product-direction response was owner-owned. Here the cost
is UNKNOWN — undiagnosed contention narrowed to two mechanisms — and the next step (add timing
instrumentation, then diagnose) is agent-owned. Not every unblock path is human-owned, so C.2 does not match.

Rejected GOAL_ACHIEVED: J-06/J-07/J-08 all `partial`; J-04 without fresh live evidence.

Rejected ESCALATE: already full depth; review PASS (no fail-open), QA PASS, audit PASS_WITH_GAPS,
coherence COHERENCE-PASS; no journey failed twice.

Progress was made (two previously-unrendered states now have live evidence; iter-16's audit-B1 gap
closed in code + tests + client render; F1 defect fixed) and tractable work remains → CONTINUE.
