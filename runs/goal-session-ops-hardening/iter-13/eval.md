# Iteration 13 Evaluation

**Verdict:** REGRESSION
**Depth Recommendation For Next Iteration:** full

## Summary

The iteration's own target succeeded decisively: `GET /api/indexes?full=true`'s default hot key,
2138.7-2257.7ms over its ≤1.5s budget in iter-12, now serves from the new ingest-warmed
`IndexSeriesCache` at 218.7 / 218.7 / 219.2 ms on `/data` and 70.5 ms on `/` — all ≤1500ms with ~7x
margin, on a verifiably idle host. The specific over-budget finding that held J-06 at `partial` is
genuinely closed. BUT this iteration also demonstrated the standing critical AG-8 `MemoryError`
(`forward_testing.py:826`, byte-unchanged) firing at **full-availability-outage severity**: on the
first browser-qa turn, under concurrent load (4 replay backfills + a diagnostic read), it wedged the
entire backend into a ~12-minute futex deadlock — `GET /api/health` unresponsive, UI frozen on
"Checking backend…" with blank cards — requiring an operator hard-restart. That is the iter-7 severity
the graceful-abort mitigation was supposed to have retired. Decision-tree C.1 (unresolved critical
anti-goal, this iteration escalated to newly-discovered full-outage damage) → REGRESSION.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing | regression-replay UT-J-01 PASS; `reports/qa/goal-ops-hardening-iter-13-evidence/J-01-verify.png` |
| J-03 | passing | passing | regression-replay UT-J-03 PASS; `reports/qa/goal-ops-hardening-iter-13-evidence/J-03-verify.png` |
| J-04 | passing | passing (carried; NOT re-verified this iter) | UT-J-04 SKIP (5/6 steps need a live kill/restart the agent may not perform); boot-path files `main.py`/`health.py`/`readiness.py`/`warmup.py` byte-unchanged (audit T1, closure, ux-regression). Frozen-UI during the AG-8 wedge is scored under AG-8, not as a J-04 code regression |
| J-05 | passing | passing | regression-replay UT-J-05 PASS; evaluator opened `reports/qa/goal-ops-hardening-iter-13-evidence/J-05-verify.png` (immutable 2025-05-15 snapshot, Regime 70.76 Risk-on, top-3 ZS/NFLX/OKTA) |
| J-06 | partial | partial (over-budget blocker CLOSED; two residual gaps) | UT-03 218.7/218.7/219.2ms `/data`, UT-04 70.5ms `/` (`UT-03-load1-result.png`, `UT-04-result.png`); page renders fully (Ready badge, coverage tiles). Held partial: (a) canonical `reports/perf-budgets.md` does NOT yet carry the passing readings (closure Non-Blocking note; its own Consistency/"single source" clause); (b) the AG-8 outage produced exactly the frozen/blank frame its honest-status clause forbids; (c) `[NEW]` `--session-live` walkthrough unproduced (owner/framework) |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 (no unbacked "proven") | OK | No proven-language; J-01…J-06 carry no evidence claims (goal.md Loop mechanics). scan CLEAN |
| AG-2 (decision-quality only) | OK | No orders/targets/alpha; unchanged surfaces |
| AG-3 (displayed numbers correct) | OK | Cache byte-identical to `compute_index_series` — verified by `test_api_indexes_*`/`test_indexes_*` full-dict `==`, closure + audit §3, and byte-identical vendor table across 3 `/data` loads |
| AG-4 (no overfit edges) | OK | No new pattern/claim |
| AG-5 (no lookahead) | OK | HIT path re-derives `asof_date` fresh via `resolve_as_of_date`, never trusts stored value (indexes.py:246-249; `test_index_series_cached_hit_re_derives_current_asof_not_stale`, audit §3) |
| AG-6 (referee gate) | OK | No evidence-derived claims this iteration |
| AG-7 (no committed secrets) | OK | `scan-report.md` CLEAN (0 findings) |
| **AG-8 (memory / availability)** | **VIOLATED — critical, UNRESOLVED, severity ESCALATED** | `forward_testing.py:826` unbounded `ScannerResult` load byte-unchanged (TC-12) but fired at **full-outage** severity: ~12-min futex deadlock, `/api/health` unresponsive, operator hard-restart. Corroborated by audit §1/§3, closure verdict, and `UT-01-blocked-backend-hang.png` (UI frozen on "Checking backend…" with blank cards — the iter-7 signature). "Degraded-but-alive, mitigation holds" (iter-9/11/12) is falsified under concurrent load |
| AG-9 (offline-deterministic ingest) | OK | 3 bounded ingest jobs ran against committed-seed/local fixtures only (fetch capped at the fixture ceiling 2026-07-22); no live network/paid service. scan dependency-CLEAN |
| AG-10 (host resource ceiling) | OK | pytest host-guard-confined (audit); `hwmon` load1 0.32-2.32, mem_avail 15.9-17.8GB, no hard-reset |

## Next-Step Recommendation

Halt for human review, then resume with `--acknowledge-regression` into a FULL-depth recovery
iteration. The owner decisions below each independently hard-block GOAL_ACHIEVED; the session has NO
remaining agent-tractable *substantive* work (J-06's last product gap is closed), so this is also a
human-owned-blocker boundary — halting costs no progress.

1. **AG-8 (the driver, now urgent):** scope a bounded/streamed rewrite of `forward_testing.py:826`
   (`select(ScannerResult).where(run_id.in_(...)).all()` over the ~329MB table), OR amend `docs/goal.md`
   to accept the graceful-abort behaviour explicitly AND require it to fail-fast to an honest "Backend
   unavailable" with automatic worker-pool recovery (never a 12-min "Checking backend…" wedge needing a
   manual restart), OR raise the cap (does not fix the unbounded pattern). A silent 6th deferral is no
   longer defensible: the deferred bug is now proven to cause a full availability outage.
2. **`HOST_GUARD_REQUIRE_MARKERS`** — owner decision, unchanged.
3. **`demo.sh ops-hardening --session-live` walkthrough** (J-05/J-06 Acceptance) — no autonomous
   mechanism produces it (iter-12 finding): human run-once, goal.md wording amendment, or framework
   session-record enhancement.
4. Small agent-tractable cleanup for the recovery iter (not journey-blocking): transcribe the passing
   218.7/218.7/219.2/70.5ms readings into `reports/perf-budgets.md` (closes J-06's single-source
   Consistency clause — closure flagged this), and add a J-04 boot spot-check to satisfy DoD-#7 literally.
   Framework-maintainer items carried: `merge_ui_test_results.py` dropped `**FAIL**` cells (the merged
   top-line read PASS while the raw `.llm.md` correctly read FAIL); retire/rewire the dead
   `major-indexes-card.tsx` so UT-07 stops failing OVERALL against unreachable code.

## Halt Justification

REGRESSION under decision-tree C.1 (first match): a **critical** anti-goal (AG-8) is unresolved and,
this iteration, escalated to newly-discovered full-outage damage. The escalation is corroborated by
three independent artifacts I opened — audit §1/§3 ("wedged the entire backend into a ~12-minute futex
deadlock … required an operator hard-restart … demonstrably capable of a full availability outage"),
the closure verdict ("observed operational severity escalated during this iteration's own testing to a
~12-minute full backend availability outage"), and `UT-01-blocked-backend-hang.png` (UI frozen on
"Checking backend…", blank cards) — not a single-source note. This directly falsifies the
"blast-radius-smaller-than-iter-7 / mitigation holds" rationale iters 11/12 logged (assumptions.md) to
withhold the literal C.1 halt; those evaluators even wrote "a human reading C.1 literally should halt
here." The human deferred a *degraded-but-alive* bug five times; iter-13 proves it is a *full-outage*
bug — new information that materially escalates the deferred decision's stakes, in an ops-hardening goal
whose core promise is "available in seconds … never a blank or frozen frame." No journey moved
passing→failing (J-01/J-03/J-05 replayed green, J-04 carried on byte-unchanged code, J-06 advanced), so
this halt is driven by the anti-goal clause of REGRESSION, not by a journey regression. Rejected
CONTINUE: the audit and closure both direct the next pass to be a "holding spec" with no agent-tractable
substantive work, so continuing would spend a loop while a proven full-outage bug stands unaddressed.
Rejected GOAL_ACHIEVED: J-06 `partial` and AG-8 unresolved. Rejected plain STALLED: it is the true
second-match (every remaining GOAL_ACHIEVED blocker is owner-owned), and I say so here — but C.1 matches
first and correctly foregrounds the outage. Coherence COHERENCE-PASS → no consolidation mandate. Resume
with `--acknowledge-regression` after the owner acts on AG-8.
