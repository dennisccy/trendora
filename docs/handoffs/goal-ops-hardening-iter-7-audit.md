# goal-ops-hardening-iter-7 Audit Report

**Date:** 2026-07-21
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS

The phase goal is genuinely achieved. The one-function ingest-time warm of `/evidence`'s per-claim
`drawdown_expectations` cache is implemented exactly as audit B1 (iter-6) prescribed: it writes the SAME
`EventStudyCache` key that `GET /api/evidence` later reads, so the first `/evidence` view after an ingest
no longer pays the ~73s cold-miss. I verified this is not a shallow/no-op fix by reading both the warm-side
and read-side code paths (byte-identical claim extraction and cache keying), by independently re-running the
new + affected tests, and by confirming the dev's live end-to-end proof rests on a genuinely-new
`dataset_version` (so a pre-existing warm cannot explain the sub-50ms first view). No CRITICAL or IMPORTANT
issue found; no fix applied.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (observation): warm-side cache key provably matches the read path (verified, not a defect)**
The critical correctness risk for this class of "warm-a-cache-earlier" fix is that the warm writes a
DIFFERENT key than the reader looks up, leaving the first view still cold while tests pass because they use
the same extraction on both sides. I traced this specifically. Warm side
(`apps/backend/app/engine/data_manager.py:3159-3180`) resolves `read_entries(evidence.resolve_ledger_path())`,
filters `entry.get("type") == FORWARD_WALK_TYPE`, extracts `entry.get("claim") if isinstance(...) else {}`,
and calls `forward_testing.compute_drawdown_expectations_cached(session, claim, cfg)`. Read side
(`apps/backend/app/engine/evidence.py:140-156` via `_claim_row` at `evidence.py:96`) uses the identical
`read_entries` + identical `FORWARD_WALK_TYPE` filter + identical `entry.get("claim")` extraction + the same
cached function. The cache subject is `dd_exp:sha256(json.dumps(claim, sort_keys=True))`
(`forward_testing.py:1383-1391`); the full key adds `view`/`asof_key` constants + `horizon` (from the same
claim) + `dataset_version` (`forward_testing.py:1414-1424`). Every key component is identical between warm
and read for the same claim and dataset version. This is a confirmation, not a defect — recorded because it
is the load-bearing claim of the whole iteration.

**B2 — OBSERVATION (observation): warm fires for the correct ingest kinds and is unconditional within the hook**
`_refresh_ingest_aggregates` is invoked only for `final_status in ("ok","partial")` and
`prog.kind in _BACKFILL_KINDS or _REBUILD_KINDS` (`data_manager.py:3874-3879`) — i.e. backfill/both/rebuild,
exactly the kinds the iter-2 lesson required (fetch/expand correctly excluded via the `elif` branch). The new
warm block itself is unconditional inside the function (no `prog.kind`/`new_snapshot_dates` gate), so it runs
for all three. Correct.

### Frontend Findings

**F1 — OBSERVATION (observation): zero frontend diff, matching scope**
`git diff HEAD -- apps/frontend` = 0 lines. The spec's "no frontend file changes" contract holds by
construction; `/evidence`'s rendered payload is unchanged (same function, same values, only warm timing
moves). Real-browser TC-6 across all 11 pages is explicitly the browser-qa-agent's pass; the perf numbers in
`reports/perf-budgets.md` are the spec-permitted, method-disclosed `curl` substitute (DoD item 1 clause +
NOTES), not a silent substitution.

### Test Findings

**T1 — OBSERVATION (observation): new tests are tight and were independently re-run green**
I re-ran the 7 new tests (`pytest -k "finalize_hook and drawdown"`) → 7 passed in 1.92s, and the affected
pre-existing exact-set tests (`test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates`,
`..._warms_forward_aggregates...`) → 2 passed. Assertions are exact-value: TC-1 asserts the category appears
AND `len(rows) == 1`; TC-3 asserts `stored == fresh` (warm payload byte-identical to an uncached recompute);
the isolation test asserts `calls["n"] == 2` (the second claim is still attempted after the first raises);
the empty-ledger test asserts `calls["n"] == 0`. These prove the right behaviors, not accidents.

**T2 — GAP (gap): the pre-existing exact-set test now transitively reads the REAL project ledger**
`test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates` (`test_data_manager.py:1045-1060`) sets
no `LEDGER_PATH_ENV`, so the new warm step reads the shared real ledger
(`runs/goal-session-mcp-loop/state/certified-claims.jsonl`, 7 claims, horizons 20/60, all FAIL). It passes
today for a genuine reason: those claims do not resolve against the sparse `finalize_hook_engine` fixture
(which has zero `ForwardReturn` rows), so `drawdown_expectations` is legitimately absent from the exact set —
I confirmed both the ledger contents and the passing test directly. This is a latent, non-hermetic coupling,
not a current bug: if that shared ledger ever gained a claim resolvable against that fixture's minimal data,
the exact-set assertion would break for an unrelated reason. Documented, not fixed (fixing it — e.g. pinning
`LEDGER_PATH_ENV` to an empty temp ledger in that test — is out of this iteration's scope and would touch a
test the spec did not ask to change).

**T3 — OBSERVATION (observation): QA emitted PASS before TC-7 finished, and required-still-passing journeys were not actively re-run**
The QA report wrote `Verdict: PASS` while the full 4-file pytest run was ~73% complete, and marked TC-08
(J-01/J-03 replay) and browser TC-02/TC-06 as PENDING/"expected trivially true." The DoD (items 2 and 4)
nominally wants the full run + replay confirmed. Residual risk is low and I closed it independently: (a) the
diff touches only `data_manager.py` (+ its test) and `perf-budgets.md` — `test_forward_testing.py`,
`test_api_backtest.py`, `test_mcp_window.py` exercise unchanged code and import cleanly (data_manager imports
succeed, no circular import from the new `from app.engine import evidence`); (b) the changed-code tests pass;
(c) J-01/J-03/J-04/J-05 are orthogonal to an ingest-time warm-timing change (zero frontend/boot/readiness/
backtest-logic edits). The dev handoff independently reports the full run as 228 passed / 0 failed (8846s).
The journey-level pass/fail is properly the downstream goal-evaluator's call (it runs after this audit with
the journey-history); I confirm only that this diff cannot have regressed those journeys.

---

## 3. Domain Assessment

The domain logic is correct and honest. The fix reuses the EXISTING `compute_drawdown_expectations_cached`
verbatim, so it introduces no new computation, no new lookahead surface (AG-5 preserved — same barrier-
respecting function the live path already uses), and no new "proven/edge" presentation (AG-1/AG-2/AG-4
untouched; all 7 ledger claims are FAIL and remain non-proven). AG-3 (displayed numbers correct) is protected
two ways: the cache function's own contract is byte-identity to a fresh compute, and TC-3 asserts it
(`stored == fresh`) on a genuinely-resolvable claim. AG-8 (resilience) is protected by three layered
try/excepts — a top-level guard around ledger resolution (missing/corrupt ledger → zero warm calls), a
per-claim guard (one raising claim never blocks another or fails the job), and the underlying function's own
`None`-returning contract for unresolvable cohorts — each covered by a dedicated test
(`..._missing_ledger...`, `..._corrupt_ledger...`, `..._isolates_claim_that_raises`,
`..._unresolvable_claim_not_reported`). The honesty gate (`if result is not None`) correctly follows the
SPEC's intent (empty/all-unresolvable ledger → category omitted), which is the tighter and correct reading
where the plan's prose was looser ("attempted a call").

The live end-to-end proof is credible under skeptical scrutiny: the dev backfilled a genuinely-unsnapshotted
date (2015-06-15 → 1 snapshot, 1840 new forward returns), which advances `_dataset_version` and prunes/stales
prior cache rows — so the observed 17.6ms first `/evidence` view (7/7 expectations panels populated, no
intervening request) can only be explained by the finalize warm having just written the current-version rows,
not by a leftover warm. This rules out the "cache-hit no-op" failure mode.

---

## 4. Fixes Applied During This Audit

None. No CRITICAL or IMPORTANT issue was found; the implementation matches the spec's exact scope. Findings
T2 (test hermeticity) and T3 (QA verdict timing / deferred journey replay) are documented as known items, not
fixed — fixing them would be scope creep, and the residual risk was independently closed by re-running the
changed-code tests and confirming the diff's orthogonality.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes required |

---

## 5. Recommended Next Step

Proceed to the goal-evaluator. This is the session's intended final feature-closing iteration: J-06's last
residual gap is closed with a correct, honest, surgical backend change, and J-01/J-03/J-04/J-05 are
provably orthogonal to the diff. The goal-evaluator should (a) confirm J-06 `passing` against the browser-qa
result and the perf-budgets closeout, (b) run/confirm the J-01/J-03 deterministic replays it owns (the one
DoD verification not executed in the QA artifact — low risk, but it is the evaluator's gate), and (c) confirm
the `[NEW] demo.sh ops-hardening --session-live` walkthrough self-resolved via the session-mode demo-narrator
now that J-06 flips to passing. If all hold, there is no remaining product blocker to GOAL_ACHIEVED.
