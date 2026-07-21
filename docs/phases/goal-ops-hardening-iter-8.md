# Goal Iteration 8 — REGRESSION recovery: bound ingest-finalize peak memory so J-05's heavy-ingest health-responsiveness holds

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 8
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-05
- **Required-still-passing journeys:** J-01, J-03, J-04
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only against the committed seed / local provider fixtures — no live external network calls or paid data services may be introduced without an explicit goal.md amendment. *(critical)*

## GOAL

Restore J-05's regressed acceptance step ("while a heavy ingest job runs, `GET /api/health` stays
responsive throughout") by bounding the peak memory the ingest finalize hook's warm loops consume, so a
real back-to-back heavy ingest on the grown live DB never hits the enforced `memory_cap_mb=6144`
`ulimit -v` ceiling — closing the critical AG-8 violation iter-7 introduced.

## BACKGROUND

iter-7's genuinely-correct `/evidence` cold-miss fix (warming `drawdown_expectations` for every ledger
claim at ingest finalize) shipped alongside a REGRESSION: browser-qa live-observed `GET /api/health`
hang for 7+ minutes during a second back-to-back heavy ingest, with a worker-thread `MemoryError` at the
enforced 6144 MB `ulimit -v` cap, all 22 threads idle in `futex_do_wait`, and a manual restart required
(`runs/goal-session-ops-hardening/iter-7/eval.md`). Per the priority rubric, rule 1 (regressed journeys
outrank everything) makes J-05 this iteration's sole target — no other journey is bundled (rule 6: this
is already one architecture/capacity-adjacent risky change; the evaluator's separately-named
`/api/backtest`→`forward_aggregates_cached`→`ScannerResult` on-load `MemoryError` is a distinct J-06/AG-8
concern, explicitly deferred — see OUT OF SCOPE).

**Root-cause reading (code inspection ahead of this iteration).** `_run_job`'s outer
`except Exception as exc:` (`app.engine.data_manager:3904`) already marks a job `failed` on any exception
that escapes to it — but `_refresh_ingest_aggregates`'s per-item warm loops (coverage per-date,
market-phase per-date, forward-aggregates per-horizon, and iter-7's new drawdown-expectations per-claim
loop) each wrap their own call in a **generic** `except Exception: log + continue`. A `MemoryError`
(a subtype of `Exception`) raised by one item is caught THERE, logged, and the loop immediately attempts
the NEXT item's allocation — under real memory pressure this keeps hammering further large allocations
instead of backing off, which is consistent with the observed process-wide stall (not a single caught
exception, but sustained pressure across the whole finalize tail — coverage + market-phase + 5
forward-aggregate horizons + drawdown's ~7 ledger claims, all newly sequential as of iter-4/iter-5/iter-7,
now running back-to-back on the SAME long-lived process a second time). The fix targets this SOURCE
(bound peak RAM in the loops that grew synchronously across iter-4/5/7), not `app/api/health.py` — its
existing try/except already degrades honestly to `unavailable` on any readiness-compute failure
(including `MemoryError`) IF the process has enough headroom to execute at all; that headroom is exactly
what bounding peak RAM restores.

**Depth is full**, citing trigger 1 (structural/cross-cutting): the fix touches a shared ingest-finalize
hot path that every backfill/rebuild job (J-01/J-03/J-05) runs through, and its correctness is only
provable via a REAL back-to-back heavy ingest measured live (iter-7's own lesson: "its peak-RAM cost must
be measured during a real back-to-back heavy ingest, not just unit-tested") — not a trigger the prior
verdict forces (prior verdict was REGRESSION, not ESCALATE; trigger 3 does not literally apply), but the
evaluator's explicit "full-depth recovery iteration" recommendation and the high blast radius of a
regressed Must-have journey on a shared hot path both corroborate it.

**Lessons applied** (per `lessons.md`): (iter-7, verbatim pattern) "Adding ANY synchronous per-item
compute to the ingest finalize hook is a memory/availability risk on the grown live DB, not a free timing
move — its peak-RAM cost must be measured during a real back-to-back heavy ingest" — this iteration's own
DoD requires exactly that live measurement, not a unit-test-only claim. (iter-3) never score a target
journey clean on backend-correctness alone — cross-check the RAW `ui-test-results.llm.md` browser-qa
verdict, not the merged summary (iter-4's known priority-blind merge bug). (iter-6) a concurrent heavy
pytest run contaminates live perf/memory readings — the VmPeak measurement for this iteration's DoD must
run on an otherwise-idle host, and the pump must not run the full test suite concurrently with it.

**Scope-selection deviation note:** none from the priority rubric itself, but this iteration deliberately
does NOT fold in the evaluator's next-step item 3 (the separate `/api/backtest` on-load `MemoryError`) —
rule 6 bars bundling two risky changes in one iteration; it is named explicitly in OUT OF SCOPE as the
likely next target after J-05 is confirmed recovered.

## IN SCOPE

### Backend
- [ ] Live-measure (via `/proc/<pid>/status` VmPeak/VmSize sampling, `spawned_backend`-style real
      process, on an idle host) the ingest-finalize tail's peak memory for a real back-to-back heavy
      ingest (a full-universe rebuild immediately followed by a second heavy backfill in the SAME
      long-lived process — mirrors iter-7's failure scenario), WITH the current iter-7 code, to confirm
      and quantify the drawdown-expectations warm block's marginal contribution to peak VSZ (the
      root-cause confirmation `lessons.md` iter-7 requires before changing anything).
- [ ] Harden `_refresh_ingest_aggregates`'s per-item warm loops (`app.engine.data_manager`: the per-date
      coverage loop, the per-date market-phase loop, the per-horizon forward-aggregates loop, and the
      per-claim drawdown-expectations loop) to catch `MemoryError` **distinctly** from the existing
      generic `except Exception: log + continue` per item: on the FIRST `MemoryError` in any one of these
      loops, stop attempting further items in THAT loop (do not keep hammering further large allocations
      under pressure), log an honest "aborted remaining <category> warm — memory pressure" message, and
      force `gc.collect()` before returning/continuing to the next independent block. Every other
      loop's own try/except boundary is untouched — one loop backing off does not abort the whole
      function (mirrors the function's existing "each aggregate refreshed independently" contract).
- [ ] `aggregates_refreshed`'s existing "actually computed" gating (no code change to the gate itself)
      already omits a category that never completed a successful item — confirm this holds for the new
      early-abort path (a partially-completed loop that warmed ≥1 item before the abort still honestly
      reports that category; a loop that aborts on its FIRST item does not).
- [ ] Re-verify `GET /api/health` stays responsive (every poll within its existing committed budget, zero
      hangs/timeouts) throughout the SAME real back-to-back heavy ingest, on the hardened build.
- [ ] No change to `app/api/health.py`, `app/engine/readiness.py`, or `main.py`'s boot sequence — their
      existing exception handling already degrades honestly once the process has allocation headroom;
      this iteration restores that headroom at the source (see BACKGROUND).

### Frontend
None. No UI surface, state, or contract changes — J-05's regression was a backend
availability/memory-exhaustion defect with no new user-facing element; the existing "Backend
unavailable" readiness presentation (already built, iter-4) is what a graceful degradation would reuse,
not a new one.

### New user-facing capability
None (recovery of an already-shipped acceptance step, not a new feature).

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
`GET /api/health` (and therefore the global readiness badge every page reads) stops going silent for
minutes during a heavy ingest — it stays live and honest throughout, restoring J-05's already-shipped
promise rather than adding a new one.

### Blueprint conformance
No new surfaces. Both touched rows — "Job history & per-date exclusion reasons" (the
`_refresh_ingest_aggregates` finalize hook) and, by re-verification only, "Backend readiness / boot phase
+ preflight verdict" (`GET /api/health`) — already have their homes in `blueprint.md`; this iteration is
an additive Notes update to the first row only (no nav-skeleton change, no reapproval needed).

### Data-contract additions
None. This iteration changes ONLY the internal error-handling/memory-behavior of the ALREADY-REGISTERED
`_refresh_ingest_aggregates` finalize hook and the ALREADY-REGISTERED `aggregates_refreshed: list[str]`
field's honesty gating under a new failure mode (memory pressure) — no new field, no new computing
module, no new endpoint, for this or any other Data Contract value.

## OUT OF SCOPE

- The separate live `/api/backtest`→`forward_aggregates_cached`→large `ScannerResult` `MemoryError` on an
  ON-LOAD (not ingest-finalize) path — a distinct J-06/AG-8 concern per iter-7's eval item 3. Deferred to
  a follow-up iteration once J-05's recovery is confirmed (rule 6: never bundle two risky changes).
- Raising `server.memory_cap_mb` (config.yaml) as a workaround. Considered and rejected — it does not fix
  the underlying unbounded-growth pattern AG-8 forbids, only postpones the same failure to a larger
  dataset; the fix bounds peak RAM instead (logged in `assumptions.md`).
- Any change to `readiness.py`, `main.py`'s boot sequence, or `warmup.py` (settled — "Do not redo"; also
  unaffected per this iteration's own root-cause reading above).
- Any change to `max_range_days`, `snapshot_cadence`, or the backfill range-cap logic (settled — "Do not
  redo").
- Removing, disabling, or changing the CORRECTNESS of the `drawdown_expectations` (or any other) warm —
  it stays byte-identical to a fresh compute and keeps warming at ingest finalize; only its
  failure-handling/memory profile changes ("Do not redo the drawdown warm itself" — iter-7 eval note).
- Isolating ingest jobs into a separate OS process (would remove the shared-`ulimit -v` failure mode
  structurally, but is a bigger architecture change than this bounded fix and conflicts with goal.md's
  "not a rewrite" non-goal); flagged as a fallback direction only if this iteration's live measurement
  shows the loop-level bound is insufficient.
- A second computing module, a second endpoint, or a second cache table for any already-registered Data
  Contract value.
- Loosening any committed budget number in `reports/perf-budgets.md` — only additive, honestly-measured
  rows.

## DEFINITION OF DONE

- [ ] J-05 passes cleanly via browser-qa-agent: all 4 acceptance steps, especially step 4 (heavy-ingest
      `GET /api/health` responsiveness), re-run live and pass with no hang/timeout.
- [ ] Live `/proc` VmPeak measurement across a real back-to-back heavy ingest confirms peak memory stays
      under the enforced 6144 MB `ulimit -v` cap with a documented safety margin, recorded as a new dated
      section in `reports/perf-budgets.md` (extends Item L).
- [ ] The AG-8 critical violation recorded in iter-7's eval (memory exhaustion + ungraceful hang) is
      resolved: no `MemoryError` is observed during the tested real-load scenario; if one is deliberately
      injected in a unit test, the process/job recovers without a manual restart.
- [ ] `drawdown_expectations` (and every other finalize-hook warm value) remains byte-identical to a
      fresh uncached compute — correctness untouched.
- [ ] Required-still-passing journeys J-01, J-03, J-04 remain green (deterministic replay where a golden
      script exists; LLM fallback otherwise).
- [ ] No anti-goal violation introduced; AG-8 closed for the tested scenario.
- [ ] Unit tests pass; no regressions —
      `pytest apps/backend/tests/test_data_manager.py apps/backend/tests/test_start_backend_script.py -v`
      runs to completion with 0 failures (targeted files only — do not run the full suite concurrently
      with the live VmPeak measurement; `lessons.md` iter-6 + the pump's own "don't run the full suite"
      constraint both apply).
- [ ] `blueprint.md`'s Data Contract stays internally consistent with the shipped code (already updated
      this iteration by the decomposer; developer/reviewer confirm no drift).
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-8-dev.md`, and its "Known Issues"
      section explicitly carries forward the deferred `/api/backtest` on-load `MemoryError` (OUT OF
      SCOPE item) as next-iteration work — not silently dropped.

## TESTING REQUIREMENTS

- Browser: J-05 (all 4 steps, especially step 4 live-polled `GET /api/health` throughout a real heavy
  ingest). Required-still-passing: J-01, J-03 (deterministic replay), J-04 (LLM acceptance).
- Unit/integration: `_refresh_ingest_aggregates`'s per-loop `MemoryError`-specific early-abort behavior
  (distinct from the existing generic-exception continue-on-error tests, e.g.
  `test_finalize_hook_drawdown_expectations_isolates_claim_that_raises`, which must keep passing for
  NON-memory exceptions), exact-value coverage of the "actually warmed" gating on an early abort, and a
  real-process back-to-back heavy-ingest health-poll test (mirrors the `spawned_backend` fixture pattern
  in `test_start_backend_script.py`).
- Error cases: a `MemoryError` injected on the FIRST item of a loop (zero items warmed — category
  honestly omitted), a `MemoryError` injected after ≥1 item succeeded (that category honestly reports
  only what was actually warmed, then aborts), and a non-memory exception on one item (existing
  isolate-and-continue behavior unchanged).

Test-first contract:

- TC-1: given a real spawned backend process (`scripts/start-backend.sh`, not `dev.sh`) with the enforced
  `ulimit -v` memory cap active, when a full-universe rebuild is run immediately followed by a second
  heavy backfill in the SAME process (back-to-back), then `/proc/<pid>/status` VmPeak sampled throughout
  both ingests stays below `memory_cap_mb` (6144 MB) with a documented margin, and no `MemoryError` is
  raised.
- TC-2: given the same back-to-back heavy-ingest run, when `GET /api/health` is polled every 2 seconds
  for the full duration of both ingests, then every poll returns HTTP 200 within its existing committed
  budget — zero timeouts, zero hangs exceeding the budget.
- TC-3: given a unit test that monkeypatches one per-item warm call (e.g.
  `forward_testing.compute_drawdown_expectations_cached`) to raise `MemoryError` on the FIRST item, when
  `_refresh_ingest_aggregates` runs, then that loop stops attempting further items immediately, `refreshed`
  does NOT include that category (zero items actually warmed), and the job still reaches a terminal
  status (not stuck `running`).
- TC-4: given the SAME injected-`MemoryError` scenario (in-process, single test), when a subsequent DB
  read (e.g. a fresh `refresh_coverage_snapshot` call or `GET /api/data`) runs afterward in the SAME
  process, then it succeeds — proving no leaked lock/open transaction blocks recovery without a process
  restart.
- TC-5: given a unit test that monkeypatches the SAME per-item warm call to raise `MemoryError` only on
  the SECOND of N items (first item succeeds), when the loop runs, then `refreshed` DOES include that
  category (≥1 item was actually warmed, honestly reported) and no further items after the second are
  attempted.
- TC-6: given the existing `test_finalize_hook_drawdown_expectations_isolates_claim_that_raises` (a
  non-`MemoryError` exception on one claim), when re-run against this iteration's build, then it still
  passes unchanged — the generic isolate-and-continue behavior for ordinary exceptions is NOT altered by
  the new `MemoryError`-specific early-abort path.
- TC-7: given the hardened build, when a warmed value (e.g. one ledger claim's `drawdown_expectations`)
  is compared to a fresh uncached compute for the same claim, then the two are byte-identical (AG-3;
  correctness untouched by the error-handling change).
- TC-8: given `pytest apps/backend/tests/test_data_manager.py apps/backend/tests/test_start_backend_script.py -v`,
  when run to completion, then it reports 0 failures and 0 errors.
- TC-9: given J-01's and J-03's existing golden replay scripts, when replayed against this iteration's
  build, then both PASS end-to-end with no step failures attributable to this iteration's diff.
- TC-10: given J-04's existing acceptance (non-blocking boot with visible status), when re-verified live
  (LLM fallback), then it still passes unchanged — this iteration's diff does not touch boot/readiness
  code.

## NOTES

- The evaluator's next-step item 2 ("health must fail-fast to the honest 'Backend unavailable' state and
  the worker pool must recover without a manual restart") is interpreted as satisfied by preventing the
  process from ever losing allocation headroom under the tested load (bounding peak RAM), not by adding
  new fail-fast branching inside `app/api/health.py` itself — its existing generic exception handling
  already degrades honestly once the process CAN execute at all. If this iteration's live measurement
  shows peak RAM still approaches the cap even after bounding the finalize loops, escalate to a fresh
  decomposer pass rather than growing this iteration's scope into a job-process-isolation rewrite.
  (Logged in `assumptions.md`.)
- Do not re-litigate iter-7's `/evidence` cold-miss correctness — it is genuinely fixed and byte-identical
  (iter-7 eval); this iteration only changes how the SAME warm behaves under memory pressure.
- Environment: `export TMPDIR TMP TEMP` to the session-isolated scratch dir before running any test or
  measurement command (per the dispatch prompt's environment note) — the live VmPeak measurement and any
  spawned-backend test must not write to the shared system `/tmp`.
- CLOSURE REMINDER (carried from iter-4/5/6/7): the `[NEW]` `demo.sh ops-hardening --session-live`
  walkthrough for J-05/J-06 is still owed before the final GOAL_ACHIEVED gate (or explicit human
  deferral) — this iteration does not produce it (J-05 is not newly reaching `passing` for the first
  time; it is being RESTORED).
