# goal-ops-hardening-iter-19 Audit Report

**Date:** 2026-07-24
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's scoped deliverable — eliminate the redundant per-request work on the `/backtest` /
MCP `query_backtest` serving path for an already-backfilled run — is correctly implemented, tightly
tested, and proven live: the `backfill_forward_returns_ms` phase collapsed from 877–881 ms to a 13.9 ms
mean / 73.4 ms max under 6× concurrency (a ~63× collapse, DoD ≤350/≤400 ms PASS), with byte-identity
preserved by construction and verified three independent ways. It is **not** a clean PASS because two
material limitations remain openly documented: (a) TC-7 — the concurrent-**ingest** overlay that is the
*actual historical breach condition* (11/68 @ 12.655 s) — was never measured (AG-10 ingest-trigger
blocked), so the budget is proven only under pure concurrent reads; and (b) browser-QA found a **separate**
multi-second (9.6–54 s) cold-first-view stall on the *same* `/backtest` page, in a different subsystem
(`ensure_loop_ms`) this iteration does not touch — meaning the spec's "closes THE one shared latency
blocker for J-06/J-07/J-08" framing is incomplete. Both are correctly surfaced, not hidden. The delivered
code is correct; the residual gaps belong to the goal-evaluator's journey-pass call, not to a defect in
this diff.

---

## 2. Findings

### Backend Findings

**B1 — OBSERVATION (verified-correct): The horizon short-circuit is byte-identical by construction — confirmed airtight.**
`apps/backend/app/engine/forward_testing.py:1449-1482`. The fix computes
`observable_days = len(session.exec(select(DailyPrice.date).where(DailyPrice.date > run.asof_date).distinct().order_by(DailyPrice.date).limit(max_h)).all())`
and passes only `observable_horizons = [h for h in horizons if h <= observable_days]` into
`_insert_run_forward_returns`. I independently checked every capping/edge case: `observable_days` is a
**strict upper bound** on any single symbol's post-D bar count (a symbol cannot trade on more distinct
dates than exist in the table after D), so a horizon `h > observable_days` has `< h` post-D bars for
*every* symbol and already stored nothing via `forward_return`'s `len(post_bars) < horizon` NA gate
(`forward_testing.py:391-393`). When actual distinct dates > `max_h`, `observable_days == max_h` and all
horizons are kept (no filtering). There is **no** case where a fillable horizon is skipped. AG-3 holds.
This matches the reviewer's independent argument and is directly proven by
`test_iter19_partially_elapsed_run_processes_only_elapsed_horizons_byte_identical`
(`test_forward_testing_serving_split.py:1328-1329`), which compares the full per-column row surface
(`_fr_rows_sorted`) of the filtered path against the unfiltered `_insert_run_forward_returns(..., HORIZONS, ...)`
and asserts exact equality. No action.

**B2 — OBSERVATION (verified-correct): No-lookahead (AG-5), bounded-read (AG-8), and no-secrets (AG-7) all hold.**
The `observable_days` query counts only `date > run.asof_date` (`forward_testing.py:1452`) — never a
bar ≤ D — so no lookahead is introduced. It is `LIMIT max_h` (≤60 rows) over the `ix_daily_prices_date`
covering index, which is guaranteed present in production by `_ensure_index_hygiene`
(`apps/backend/app/db.py:172`, invoked at startup `db.py:190`); the operator's live 13.9 ms and the
reviewer's `EXPLAIN QUERY PLAN` both confirm the index is used, so this is not a whole-table scan (AG-8).
The diff introduces no credentials/keys/tokens (AG-7). No action.

**B3 — GAP (deferred, pre-existing): Autoflush `IntegrityError`/`OperationalError` hazard inside `_insert_run_forward_returns` is untested against the realistic multi-missing-symbol race.**
`apps/backend/app/engine/forward_testing.py:378-425`. When the per-symbol loop moves from a symbol with
staged pending INSERTs to the next symbol's `close_on`/`bars_after` read (`forward_testing.py:384-387`),
SQLAlchemy autoflush fires **outside** the `IntegrityError`-tolerant `_commit_forward_returns_concurrency_safe`
wrapper (`forward_testing.py:428-443`). Under 2+ concurrent callers racing a genuinely-missing run with
2+ missing symbols — the common shape for any real multi-ticker cold historical snapshot under concurrency
— this can propagate uncaught. The dev's own TC-4
(`test_forward_testing_concurrency.py:589-608`) had to **pre-seed the benchmark symbols as already-complete**
specifically to route around this hazard, so TC-4 proves the *commit-time* rollback path but does **not**
cover the *mid-loop autoflush* race. This is pre-existing (unrelated to this iteration's guard), the warm
path never reaches it (0 rows staged → no autoflush), and the reviewer classified it MINOR/deferred. I did
**not** fix it: the remedy restructures flush timing on the exact concurrency cluster that produced iter-13's
REGRESSION_HALT, which is scope creep here and explicitly risky — correctly filed as its own follow-up
iteration with its own concurrency-test budget.

### Frontend Findings

**F1 — GAP (out-of-scope, honestly surfaced): A separate multi-second cold-first-view stall remains on `/backtest`.**
Browser-QA UT-04 (`reports/phase-goal-ops-hardening-iter-19-ui-test-results.llm.md:56-61`) found that the
FIRST navigation to a not-yet-served historical as-of (`2025-05-30`) left the page on empty skeleton
placeholders for **9.6 s–54 s** (three concurrent first-touch requests logged `total_ms` 9548/54483/54328)
with **no loading/spinner affordance**. The cost is a distinctly-named field `ensure_loop_ms`
(9288/54281/54084 ms), a **different subsystem** — this iteration's own `backfill_forward_returns_ms`
stayed 12–80 ms with `write_taken=False` on those very requests. Repeat loads dropped to 0.08–0.13 s
(one-time per-date cold cost). This is correctly **not** attributed to this diff (different code path,
pre-existing) and the spec's OUT OF SCOPE list already excludes "J-06's other page-load budgets." I flag
it because it is a real, user-observable stall **of the same latency class the iteration is meant to be
closing, on the same page** — so the goal's "one shared blocker" framing is not literally closed. Both
browser-QA and ux-regression (`reports/phase-goal-ops-hardening-iter-19-ux-regression.md:145-148`) already
recommend registering it as its own tracked item; I concur. Fixing it here would be scope creep into a
different subsystem.

**F2 — OBSERVATION: Zero frontend surface changed, as specified.**
`git status` confirms no `apps/frontend/` file in the changeset; the served response dict in both
`backtest.py` and `mcp/tools.py` is byte-identical (only `backfill_result` capture + one log field added).
UT-03 (two independent full-DOM captures diffed byte-for-byte identical) and UT-04 (fully-elapsed
historical date renders every horizon's real values) corroborate live. No action.

### Test Findings

**T1 — OBSERVATION (verified): The new tests are tight and genuinely exercise the target behavior.**
TC-1/TC-2 (`test_forward_testing_serving_split.py:884,931`) assert `write_statements == []` via
`before_cursor_execute` SQL-inspection — real zero-write proof, not inference — and TC-2 asserts the full
MCP dict `== ` the API dict. TC-3 (`:980`) proves insert-then-zero-write with exact row-count assertions.
TC-4 (`test_forward_testing_concurrency.py:562`) forces a deterministic race via `threading.Barrier` and
proves the `IntegrityError` rollback path fires with an **instrumented call-counter** (`rollback_count["n"] >= 1`,
empirically 4/5) plus tight assertions (exactly `len(horizons)` rows, no duplicate keys). TC-5 (`:1071`)
and the three `test_iter19_*` short-circuit tests (`:1231,1282,1353`) assert exact byte-identity/realized
values, not loose ranges. I confirmed **57 passed in 25.20 s** from the QA log
(`reports/qa/goal-ops-hardening-iter-19-test.log`), matching the QA/reviewer/dev independent runs. No test
passes by accident.

**T2 — GAP: The DoD "all pre-existing tests keep passing" is not fully evidenced.**
`test_forward_testing.py` (83), `test_warmup.py`, `test_data_manager.py`, and `test_api_backtest.py` were
**not run** (host-guard time limits; the dev flagged this plainly, dev handoff §"Regression scope not run").
The mitigation is code-inspection (the returned dict shape is unchanged; the guard only removes redundant
work) plus the fact that `test_backtest_scorecard.py` (20 tests, which directly exercise
`backfill_run_forward_returns`'s create-once/idempotent/no-lookahead behavior) **did** pass. This is a
bounded evidence gap, not an observed regression — but the DoD checkbox is not fully closed by evidence.

---

## 3. Domain Assessment

The core domain logic — realized forward-return backfill with a no-lookahead, INSERT-only, idempotent,
NA-honest contract — is preserved exactly. The three cooperating changes (skip-commit-when-zero,
column-projected existence read, and the un-elapsed-horizon global short-circuit) are correctly layered,
and the handoff is honest that only the **third** is the latency driver — a conclusion reached the right
way, by three dev+review attempts each corrected by a **live operator re-measurement** rather than a
code-level argument (iter-18's "SQLite write-lock cost" hypothesis was live-disproven at attempt-1: skip
guard held at 877 ms; the real cost was ~1106 GIL-serialized per-request price fetches for horizons that
can never produce a row on the latest run). This is exactly the "trust the live number" discipline this
session's rubric demands, and the negative results are recorded honestly in `perf-budgets.md`
("Recorded as an honest negative result — the measurement did its job"). Byte-identity — the load-bearing
correctness property (AG-3) — is proven by construction (a strict upper bound that can never wrongly skip
an observable horizon), by a full-column filtered-vs-unfiltered unit assertion, and live (all 4793 TC-6
responses `evidence_status=ready`; double-curl + DOM diffs byte-identical). I independently recomputed the
raw TC-6 client CSV (`runs/goal-ops-hardening-iter-19/tc6-final-poll.csv`): 4793 requests, all HTTP 200,
mean 0.112 s, max 0.302 s, **0 breaches**, all `ready` — matching the report's prose exactly. Architecture
stays local-first and minimal: no new schema/column, no new service, no network, one surgical function
edit; failure handling is explicit (synchronous fallback for the genuinely-missing case, race-tolerant
commit); ambiguous data is surfaced with unusual honesty.

---

## 4. Fixes Applied During This Audit

None. The delivered code is correct; every finding is either verified-correct (B1, B2, T1, F2), a
pre-existing hazard explicitly deferred as its own follow-up (B3), an out-of-scope different-subsystem
issue (F1), or an evidence gap that cannot be closed without running host-guard-forbidden expensive
suites (T2). Applying any change would be scope creep — and B3's remedy is specifically risky on the
iter-13 REGRESSION cluster. No CRITICAL or IMPORTANT defect in this iteration's diff warranted a fix.

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | No fixes applied (see rationale above) |

---

## 5. Recommended Next Step

Proceed to goal-evaluation of J-06/J-07/J-08, weighing these documented gaps explicitly (as the spec's own
NOTES section instructs the evaluator to do):

1. **TC-7 is unmeasured.** The fix's *mechanism* (1106→0 per-request fetches) removes the dominant cost
   regardless of a concurrent ingest window, and pure-concurrency TC-6 passes with a ~63× margin — but the
   budget under the *actual historical breach condition* (concurrent ingest holding the writer lock) is not
   directly proven. Its block is documented in the QA report and dev handoff ("not silently dropped"), though
   not in a dedicated `perf-budgets.md` TC-7 section as the spec sketched; consider adding a one-line dated
   note there for record-keeping.
2. **Register the `ensure_loop_ms` cold-first-view stall (F1) as its own backlog/goal item** so it does not
   implicitly ride along as "solved" when J-06/J-08 are evaluated — a 9.6–54 s no-affordance stall on
   `/backtest` is a real, same-class latency gap on the same page, in a code path this iteration did not touch.
3. **Carry B3 (autoflush hazard) and T2 (unrun regression files) forward:** schedule the autoflush hardening
   as a focused follow-up with its own concurrency-test budget, and run the four skipped regression files off
   the host-constrained box before treating the DoD's "all pre-existing tests pass" bullet as fully closed.

The iteration's own deliverable is sound and materially strengthens the system; the open items are
journey-completeness questions for the evaluator, not defects to fix in this diff.
