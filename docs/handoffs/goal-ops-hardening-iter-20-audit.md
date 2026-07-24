# goal-ops-hardening-iter-20 Audit Report

**Date:** 2026-07-24
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The iteration's actual deliverable is achieved and correct: the historical (`is_latest == False`)
`/backtest` ensure-loop is off the request thread, first-view is `0.082 s` with `ensure_loop_ms` collapsed
from `9288–54281 ms` to `~1.67–3.34 ms` serving an honest interim state, byte-identity is preserved by
construction (`compute_forward_aggregates` / `resolved_forward_aggregate_evidence` are diff-confirmed
byte-unchanged), the single-flight dedup and guard-release-on-owner-failure are both proven by genuinely
discriminating tests, and MCP/HTTP parity holds. Three residuals keep it from a clean PASS — all GAP-level,
all documented honestly upstream, none compromising the goal: (a) transient in-process contention breaches
the ≤0.1 s health and ≤1.5 s request budgets DURING the bounded ~30 s background window (max 1.60 s health,
3.0–6.3 s requests) though the service never wedges and this is strictly better than the pre-iteration 54 s
block it replaces; (b) two DoD-named regression files were not executed this session; (c) the oldest dates
still exceed ≤1.5 s for reasons pre-existing and out of this iteration's scope. No fixes were applied — every
finding is GAP/OBSERVATION-level, and fixing them would be scope creep or is explicitly out of scope per the
spec.

---

## 2. Findings

### Backend Findings

**B1 — GAP (observation): TC-5's "≤0.1 s health throughout" DoD bullet is literally breached during the background-compute window.**
`reports/perf-budgets.md:3368–3375` records the operator's own live measurement: during a cold historical
background compute, `GET /api/health` stayed `200`/`readiness: ready` on all 16 samples but latency spiked to
**max 1.60 s** (0.64/0.90/1.01/1.60 s on 4 of 16), and concurrently-issued `/backtest` requests spiked to
**3.0–6.3 s** (`perf-budgets.md:3358–3366`). Root cause is in-process GIL/CPU contention from
`compute_forward_aggregates` running in the daemon thread (`apps/backend/app/engine/forward_testing.py:1222`),
not a request-path recompute (`ensure_loop_ms` stays ~2 ms). The DoD bullet TC-5 reads "stays within its
existing ≤0.1 s budget **throughout** … no frozen or unresponsive window" — the "no frozen/unresponsive
window" half holds (no wedge, readiness never drops, J-07's *core* promise met and live-verified in UT-07),
but the "≤0.1 s throughout" half does not. **Why this is a GAP, not IMPORTANT:** it is not a regression — the
identical compute previously ran ON the request thread for 9.6–54 s, contending the same way but for *longer*
and while also blocking the requester; iter-20 is strictly better on every axis. Fully removing it needs the
compute off-process or precomputed at ingest — both explicitly rejected/out-of-scope in the spec
(BACKGROUND, OUT OF SCOPE). **No fix applied** — the spec mandated the in-process thread idiom; eliminating
the residual is a different, larger iteration. Documented honestly by the operator, the reviewer (NOTE), and
ux-regression.

**B2 — GAP: the overall historical-view ≤1.5 s budget is not universal for the oldest dates, for reasons outside this iteration's scope.**
Browser-QA UT-02 (`reports/phase-goal-ops-hardening-iter-20-ui-test-results.md:22`) measured a cold
`2005-07-01` view at backend `total_ms=1321.85` (browser-perceived 1919 ms) with `ensure_loop_ms=3.34` — i.e.
iter-20's own contribution is 3.34 ms (a complete success for the targeted defect), but `resolved_run_ms +
scorecard_ms` (`apps/backend/app/api/backtest.py:162–177`, pre-existing, unchanged) push the whole request to
~1.3 s backend / ~1.9 s browser. The spec explicitly scopes these phases OUT
(`docs/phases/goal-ops-hardening-iter-20.md` OUT OF SCOPE: "`resolved_run_ms` staying small … not implicated
by this iteration's diagnosis. Untouched"). The honest-interim-state / never-a-frozen-skeleton half of the
DoD's first bullet IS met (UT-02: EmptyState rendered "essentially immediately"). This is a J-06/J-08
completeness gap for a *future* targeted iteration, not a defect in iter-20's deliverable and not a
regression (this same date was 9.6–54 s + this cost before). **No fix — out of scope.**

**B3 — GAP: the outer dispatch guard has a narrow non-owner wedge window the "structurally incapable of a permanent wedge" comment overstates.**
In `ensure_historical_forward_aggregates_dispatched` (`apps/backend/app/engine/forward_testing.py:1265–1277`)
the key is inserted into `_HIST_DISPATCH_INFLIGHT` under the lock at line 1268, but `session.get_bind()`
(1270), `threading.Thread(...)` (1271–1276), and `thread.start()` (1277) run *outside* the lock with no
`try/except`. If `thread.start()` raises (OS thread-exhaustion — a non-trivial concern on a host that has
hard-reset twice under load, AG-10) after the key insert, the key is stranded and that `(asof_key,
dataset_version)` never re-dispatches until the version bumps. The module comment at line 1197 claims the
guard is "structurally incapable of a permanent wedge" — that is true for the *owner-thread* failure the DoD
and TC-7 actually name (handled by the worker's `finally` at line 1234, genuinely proven), but slightly
overstated for this pre-owner-start edge. **Why still only a GAP:** even when stranded, the page serves an
honest interim state (`refreshing`/`not_yet_computed`) — no crash, no corruption, no fabricated numbers, no
service-down — and it self-heals on the next ingest's `dataset_version` bump. It is not the DoD's enumerated
"dispatch-owner failure" (which passes). **No fix applied** — fixing an exotic, self-healing edge that never
violates an anti-goal is scope creep per the auditor rubric; noted so a future hardening pass can wrap
1270–1277 in a key-discarding `try/except` if desired.

### Frontend Findings

**F1 — OBSERVATION: the historical `"refreshing"` copy attributes the compute to "viewing this page" even when a prior view started the in-flight compute.**
`apps/frontend/app/backtest/page.tsx:317–320` renders, for the historical branch, "This date's own evidence
is being computed in the background (started by viewing this page)…". Under a re-view or concurrency the
in-flight compute may have been started by an *earlier* view (this view's dispatch call is then a no-op), so
"started by viewing this page" is generically rather than literally precise. It is nonetheless honest — the
mechanism *is* "viewing this page triggers the compute", the evidence *is* being computed in the background,
and no number is fabricated. The frontend handoff (Known Issue #2) discloses this generality explicitly. No
action — this is calm, factual, never-fabricated copy, live-verified verbatim in UT-05
(`ui-test-results.md:25`) and independently re-confirmed by ux-regression
(`reports/phase-goal-ops-hardening-iter-20-ux-regression.md:22`).

### Test Findings

**T1 — GAP: two DoD-named regression files were edited/relied-upon but not executed this session.**
`apps/backend/tests/test_api_backtest.py::test_backtest_evidence_is_as_of_scoped_expanding_window` (TC-11,
edited at ~line 241 to poll for the dispatched compute before asserting `n_runs`/`asof_dates <= D`) and
`apps/backend/tests/test_data_manager.py` (DoD "no regressions" list) were not run — both carry deep-basis
fixtures (~80 min / 10 h+, correctly cited as out-of-scope-to-run per the spec and pump note). **Risk
assessment (I could not run them either — same host-guard constraint):** the TC-11 edit is a mechanical
mirror of the `_poll_until_ready` pattern in `test_forward_testing_serving_split.py` that WAS run and passes
(the oldest date has the smallest 1-run expanding window, so its background compute is fast — timeout risk
low); `test_data_manager.py` exercises only `compute_forward_aggregates`/`forward_aggregates_ingest_cached`,
which are diff-confirmed byte-unchanged, so a regression there is near-impossible from a purely-additive diff.
Low risk, but genuinely unverified through the whole pipeline. Recommend an off-box run before final closure
(the dev handoff and ux-regression both already recommend this).

**T2 — GAP (reporting accuracy, not a code defect): the QA report overstates the TC-05 health result.**
`reports/qa/goal-ops-hardening-iter-20-qa.md:150` summarizes "Health Endpoint (TC-05): 15/15 health polls
≤100ms", which is internally contradicted by its own TC-05 row ("15 health polls completed, **1 with
>100ms**", `qa.md:87`) and understated versus the operator's own 16-sample measurement (4/16 over budget, max
1.60 s; `perf-budgets.md:3371`). The honest record is `perf-budgets.md`; the QA "PASS" on TC-05 should be
read as "service stayed up/ready" (true) rather than "latency stayed ≤0.1 s" (false during the window). No
code impact — flagged so the evaluator weighs the operator's numbers, not the QA summary's, on the health
budget.

**Operator-gated carries (accepted, per DoD — neither silently dropped):** TC-13 (concurrent-ingest-overlay
`/backtest` re-measurement) and TC-14 (disruptive J-04 kill/restart replay) have NO evidence — blocked by the
AG-10 ingest-trigger classifier, recorded plainly in the dev handoff (Known Issues #5) and QA notes. The
consequence worth stating plainly: the ≤1.5 s budget under a concurrent INGEST remains **unproven** this
iteration — the spec itself is honest that TC-3 (pure request-concurrency) does not prove it, and TC-13 is
what would.

---

## 3. Domain Assessment

The core mechanism is correct, surgical, and honest — I traced every claim in the dev handoff and the pump
note's six verification asks against the actual code, not the summaries:

- **Byte-identity (AG-3 / TC-16) holds by construction.** `git diff HEAD` on `forward_testing.py` shows
  **zero deletion lines** — the diff only adds `import logging`, a module logger, and the two new dispatch
  functions; `compute_forward_aggregates` and `resolved_forward_aggregate_evidence` are untouched. The
  background worker (`forward_testing.py:1222`) calls the *identical* `forward_aggregates_ingest_cached`
  per-horizon loop the old synchronous path called, so the eventual `"ready"` payload is produced by the same
  code. TC-10's byte-identity assertions and the 30 streaming byte-identity tests corroborate.
- **Single-flight dedup is real, not coincidental.** `test_iter20_concurrent_first_touch_..._dispatch_exactly_once`
  monkeypatches the module-global `compute_forward_aggregates` (validly intercepted — it is called as a bare
  name at `forward_testing.py:1133`) and asserts exactly `len(horizons)` calls across 5 concurrent requests,
  **behind a ≥1.0 s calibration guard** that fails loudly if the fixture is too small to discriminate the old
  blocking path from the new one — this prevents a vacuous pass.
- **Guard-release-on-owner-failure is genuinely proven.** `_run_historical_forward_aggregates_dispatch`
  releases the slot in a `finally` on both success and exception (`forward_testing.py:1231–1235`). TC-7
  forces a first-call `RuntimeError` then re-triggers; it can only reach `"ready"` if the guard was released,
  and times out (fails) otherwise — a real discriminator, not a scheduling-luck pass.
- **Session lifecycle is clean.** The worker uses `with Session(engine) as session:` (context-managed
  open+close, no leak) and the writes persist because `forward_aggregates_ingest_cached` commits internally
  (`forward_testing.py:1163`) — I verified this specifically, since the context manager does not auto-commit.
- **MCP/HTTP parity held.** `apps/backend/app/mcp/tools.py:296–300` is a byte-for-byte mirror of
  `apps/backend/app/api/backtest.py:208–212` (same `not is_latest and evidence["evidence_status"] != "ready"`
  gate, same single dispatch call, same no-re-resolve). The updated iter-17 regression guard test proves the
  `!= "ready"` gate (which `"refreshing"` satisfies) still dispatches this date's OWN compute rather than
  short-circuiting on the fallback.
- **Honest interim state, never fabricated.** Both callers return the PRE-dispatch resolver read
  (`refreshing` with last-good `evidence_by_horizon`, or `not_yet_computed` with `{}`) — never a synthesized
  0. The frontend copy corrections (`page.tsx:236–239`, `315–327`) branch on the already-fetched
  `is_latest` and were live-verified verbatim (UT-05/UT-06).
- **The pre-existing autoflush `IntegrityError` hazard is genuinely pre-existing, not introduced.** iter-20's
  diff touches neither `_insert_run_forward_returns` nor `backfill_run_forward_returns` (both still called
  synchronously on the request thread, unchanged); the background dispatch path only reaches the read-only
  `compute_forward_aggregates`. The dev correctly reproduced it in a fixture draft, declined to fix it
  (iter-19's territory), and isolated the TC-3 fixture around it (`observable_days == 0` on the requested
  run). Confirmed out of scope.

The `evidence_status` three-state contract, the resolver's cross-`asof_key` fallback, and the compute's
streamed/column-projected pattern are all untouched — the coherence contract (no second producer, no second
resolver) holds. The frontend remains a thin, honest disclosure of server-computed state (no business logic).

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| — | — | — | **None.** Every finding is GAP/OBSERVATION-level. B1 and B2 are explicitly out-of-scope to fix per the spec (off-process/precompute rejected; scorecard/resolved_run untouched); B3 is a self-healing exotic edge whose fix would be scope creep; T1/T2 are execution/reporting gaps, not code defects. Fixing any of them would violate the auditor's "document GAPs, do not fix" discipline and risk drift on a working, verified implementation. |

---

## 5. Recommended Next Step

**Proceed to goal-evaluator scoring of J-06/J-07/J-08.** iter-20's targeted deliverable — taking the
historical-as-of forward-aggregate compute off the `/backtest` request thread — is fully and correctly
achieved (54 s block → 0.082 s, `ensure_loop_ms` → ~2 ms, honest interim state, byte-identity, single-flight,
no wedge, MCP parity), and the frontend copy is corrected and live-verified. The system is materially stronger
than before the iteration.

Two open questions belong to the evaluator's own budget judgment, not to this audit's pass/fail: (1) whether
the transient ~1.6 s health / 3.0–6.3 s request contention DURING the bounded ~30 s background window (B1) is
tolerable against the ≤1.5 s / ≤0.1 s budgets — noting it is strictly better than the pre-iteration state and
never takes the service down; and (2) whether the oldest dates' ~1.3–1.9 s total (B2), driven by pre-existing
out-of-scope phases, blocks the J-06/J-08 latency claim or belongs to a follow-on iteration.

Before final GOAL_ACHIEVED closure (not this iteration's blocker): run
`test_api_backtest.py::test_backtest_evidence_is_as_of_scoped_expanding_window` and `test_data_manager.py`
off this constrained box to close the "no regressions" DoD bullet (T1), and — the standing precondition every
evaluator since iter-15 has named — obtain owner authorization for the AG-10-gated TC-13 (ingest-overlay
budget proof) and TC-14 (disruptive J-04 checkpoint-survival replay), which remain the last genuinely
unmeasured conditions on this cluster.
