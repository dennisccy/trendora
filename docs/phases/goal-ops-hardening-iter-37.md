# Goal Iteration 37 — Close J-07: bound the last unbounded whole-table backfill prefill, then run J-07's own steps 1-4

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 37
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — Prior evaluator verdict (iter-36) was `ESCALATE`; per the binding rule this makes full depth mandatory, not advisory, regardless of the arbiter's own signals.
- **Frontend Present:** no
- **Target journeys:** J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-06, J-08, J-09
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
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills, full-universe rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched only via the project launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those scripts MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env` whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`, `malloc_arena_max`). Never remove, weaken, or bypass these caps: stripping a HOST-GUARD marked block from a launch script is a REGRESSION regardless of test outcomes. The ceilings are a physical constraint of the current host (two instant hardware resets under all-core vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance budget to optimize away. *(critical)*

## GOAL

Close J-07 ("Heavy aggregates never take the service down") by bounding the last unbounded
whole-table `daily_prices` prefill on the multi-date backfill path, then actually executing
J-07's own long-deferred steps 1-4 (full-horizon warm, health-poll-during-warm, VmPeak margin
recorded in `reports/perf-budgets.md`, induced-memory-pressure abort drill) with the browser-qa
lane's test plan ordered so a backend-down test can never strand a later assertion.

## BACKGROUND

J-07 is the session's ONE remaining non-`passing` journey (`partial` for the third consecutive
iteration; `last_passing_iter=iter-34`). The iter-36 evaluator's binding next-step is unambiguous
and this spec follows it: item 1 was "finish J-07 — it needs no new feature, it needs to be RUN,"
and item 2 was the one remaining real code defect standing between the current tree and J-07's
own Acceptance clause being literally true. Per the priority rubric, J-07 is both the only
non-passing journey (rule 3 unblocker) and the smallest remaining scope (rule 4) — there is no
tie to break. Prior verdict was `ESCALATE`, which makes `Depth: full` mandatory (no escape
condition needed — ESCALATE itself is the trigger).

**The code defect (iter-36/l):** `_excluded_counts_by_date`'s own docstring, added in iter-36's
diff, states the scope exclusion verbatim — an ACTIVE outer `prefilled_bar_cache` opened by
`_do_backfill` (`data_manager.py:3085`) or `_persist_per_date_coverage_snapshots`
(`data_manager.py:3183`) is reused as-is inside that function, "this iteration does not touch
it." But those two callers still each open their OWN separate `prefilled_bar_cache` for the SAME
K-date backfill job, so the whole `daily_prices` table (~1.13 GB at the live basis) is loaded more
than once per job. This is directly evidenced by a live, currently-red test:
`test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` asserts `max(load_counts
.values()) == 1` for a K≥3-date parallel backfill; the reviewer's `git stash`-compared check found
max 10/typical 2 loads per symbol on iter-36's own WIP (max 11/typical 3 on unmodified HEAD — an
improvement, not a fix). This iteration makes those two call sites share ONE `prefilled_bar_cache`
for the whole job instead of opening two, closing the gap between "loaded once per job" (the
docstrings' stated intent throughout this module) and what the test actually measures.

**Applying binding lessons from this session's ledger:** (1) the iter-29/iter-32 lesson — any
memory-bound claim must name the exact failing frame and prove it with a `git show HEAD`-pinned
reference oracle plus a mutation-style test that fails when the fix is reverted, not a range-check
that would stay green after a full revert. (2) The iter-36 lesson — a browser test plan that
deliberately takes the backend DOWN must schedule those tests LAST, so a denied restart cannot
strand a later assertion (iter-36 lost UT-13/UT-14 and the entire J-07 verification this exact
way). (3) The iter-35 lesson — an `evidence`-depth dispatch paired with a spec whose Definition
of Done requires code guarantees a wasted iteration; this spec's `Depth: full` metadata line must
be honored by the dispatcher, and the full pipeline (developer → reviewer → browser-qa → audit →
closure) must actually run.

**Deliberately deferred (rule 5 — one risky code change per iteration):** iter-33/g (Regime Lab's
cold `view=pooled` background dispatch + the undiagnosed HTTP 200 carrying the body "Internal
Server Error" — UT-12 added fresh evidence this run: VmPeak within ~100 KB of cap, a
`MemoryError` at `research.py:3339`). This iteration's one risky change is confined to the
backfill-path shared-cache fix; a second structural change (Regime Lab's dispatch model) is left
for the next iteration, per the same rule that governed iter-30 through iter-36's scoping.

**Explicitly OUT of dev scope, both owner decisions carried unchanged:** iter-34/j (the `GET
/api/health` ≤0.1s budget, honestly missed on this host under CPU contention — root-caused,
not agent-fixable) and iter-33/i (whether `start-frontend.sh` should join
`HOST_GUARD_MARKER_FILES`). Also out of scope: the `closure_gate.py` backend-only regex false-
positive flagged by the iter-36 evaluator — that file lives in the vendored `incredible_auto_dev`
framework tree, not this product's `apps/`/`scripts/`/`project-extensions/` tracked scope, and
framework-file changes go through the separate clone-and-apply maintenance path, not a goal-mode
dev iteration.

## IN SCOPE

### Backend
- [ ] `_do_backfill` (`apps/backend/app/engine/data_manager.py:2888`) and
      `_persist_per_date_coverage_snapshots` (`apps/backend/app/engine/data_manager.py:3150`)
      share ONE `prefilled_bar_cache` for the whole backfill job instead of each opening its own —
      the whole-table bar load happens at most once per job, not up to twice. Same computing
      module (`app.engine.data_manager`), same serving endpoint (`GET /api/data`), no schema
      change. `_compute_coverage_uncached`'s standalone (no-active-cache) call path — already
      bounded at iter-35/36 — is untouched.
- [ ] Prove byte-identical persisted `CoverageSnapshot` rows and byte-identical
      `_do_backfill`-created snapshot payloads before/after, via a `git show HEAD`-pinned
      reference-oracle test (binding iter-32 lesson: pin the OLD body verbatim, do not call the
      new code from both sides of the comparison) plus a mutation-style test that fails when the
      shared-cache fix is reverted (binding iter-29/32 lesson).
- [ ] `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` passes (exactly 1
      load per symbol for the whole K-date parallel job — currently red, max 10).
- [ ] Execute J-07 step 1: with the full deep basis loaded, trigger the forward-aggregate warm for
      every configured horizon (the ingest finalize path) and serve `GET /api/backtest` for each
      horizon throughout, in one long-lived backend process launched via `scripts/start-backend.sh`
      (AG-10). No code change to `compute_forward_aggregates` / `resolved_forward_aggregate_evidence`
      / `ensure_historical_forward_aggregates_dispatched` — byte-frozen (binding, iteration-state.md
      "Do not redo").
- [ ] Execute J-07 step 2: poll `GET /api/health` once per second throughout step 1's warm; record
      HTTP status per poll (no frozen/unresponsive window).
- [ ] Execute J-07 step 3: record the process's peak memory (VmPeak) during step 1; write the
      margin under `server.memory_cap_mb` into a new dated section of `reports/perf-budgets.md`
      (this is the ONE J-07 line item that has never been written there against THIS exact
      step-1/step-2-concurrent scenario, per two consecutive evaluators).
  - **Applies-to lesson (iter-34):** a saved log EXCERPT is not the log — corroborate every
    claim against the LIVE log file with a bounded line range, not a trimmed excerpt.
- [ ] Execute J-07 step 4: induce memory pressure during a warm (tightened `server.memory_cap_mb`
      in a throwaway process launched via `scripts/start-backend.sh`, AG-10); confirm the warm
      aborts honestly (existing per-item `MemoryError`-catch convention, iter-8) while the SAME
      process keeps serving `GET /api/health` and previously-cached reads — no deadlock, wedge, or
      restart required. Re-run this drill against the paths bounded by this iteration and by
      iter-35/36 (the coverage/membership-timeline and drawdown-expectations bounds), not the
      pre-iter-35 unbounded state.

### New user-facing capability
None — this iteration is a correctness/resilience fix plus verification of an already-shipped
capability. No new UI surface.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None — backend-only.

### Product surface delta
No visible product surface changes. The user-visible delta is confidence: heavy multi-date
backfills now provably load the price basis at most once per job (lower peak memory, faster), and
J-07's own availability guarantee (the backend never wedges under a full-horizon warm, and
degrades honestly under induced memory pressure) is now measured and recorded rather than assumed.

### Blueprint conformance
No new page/nav. This iteration's work lives entirely under J-07's existing cross-cutting home
(global readiness badge + `/backtest`, `GET /api/backtest`) and the `/data` Coverage payload /
Backfill run-summary contract home (Data Manager nav section) per
`runs/goal-session-ops-hardening/state/blueprint.md`'s Information Architecture table — both
already registered, no change to either home this iteration.

### Data-contract additions
None. This iteration modifies the INTERNAL memory-loading mechanism of two already-registered
computing paths (`app.engine.data_manager`'s `_do_backfill` / `_persist_per_date_coverage_snapshots`,
serving `GET /api/data`'s Coverage payload and Backfill run-summary contract rows) — no new field,
no new endpoint, no second producer, no change to any served value's shape. `blueprint.md` has
been updated (additive only — a new "iter-37 update" paragraph plus one appended sentence on the
Coverage payload row's Notes cell) to record this targeted scope; no Information Architecture
change, so no `blueprint.reapproval-requested` file was written.

## OUT OF SCOPE

- iter-33/g — Regime Lab's cold `view=pooled` background dispatch + the undiagnosed HTTP 200
  carrying "Internal Server Error" body (deliberately deferred, rule 5 — next in queue).
- iter-34/j — the `GET /api/health` ≤0.1s budget, honestly missed under host CPU contention;
  owner decision (amend the budget for this shared host, or accept the WARN disposition), not
  agent-fixable.
- iter-33/i — whether `start-frontend.sh` should join `HOST_GUARD_MARKER_FILES`; owner decision.
- `warmup.py:194` and the badge wording after a permanently failed warm-up (7 iterations
  unmade) — carried, non-blocking.
- iter-31/e, iter-32/f (watch only), iter-36/n (`_excluded_counts_by_date` duplicate-date
  double-count, unreachable in production) — carried, unresolved, non-blocking; do not re-open.
- Audit B6 (`read_pool()` re-read once per batch × date, ~20,680 calls) and the stale
  `membership_timeline_cached` docstring / "591 symbols" → 548 correction in
  `perf-budgets.md:4466` — small, carried, non-blocking; not this iteration's scope.
- The `closure_gate.py` backend-only regex false-positive — lives in the vendored
  `incredible_auto_dev` framework tree, outside this product's tracked dev scope
  (`apps`/`scripts`/`project-extensions`/`config.yaml`); framework-maintainer follow-up, not a
  goal-mode dev task.
- J-07's `[NEW]` walkthrough capture and a J-06 budgets-table-vs-live-pages walkthrough — ride-
  alongs only, never an iteration's goal (rule 7); if the demo lane produces them as a side effect
  of this iteration's real work, good, but they are not a Definition-of-Done item.
- No new UI, no new nav entry, no new Data Contract value.

## DEFINITION OF DONE

- [ ] J-07 passes via browser-qa: steps 1-4 all execute with this-iteration evidence (not
      inference), and the backend-down/error-state portion of the test plan (if any) is scheduled
      strictly LAST so a denied restart cannot strand any other J-07 assertion.
- [ ] `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` passes (exactly 1
      load per symbol for the whole job).
- [ ] The byte-identity reference-oracle test and the mutation-style test for the shared-cache fix
      both pass, and the mutation test fails when the fix is reverted.
- [ ] `reports/perf-budgets.md` gains a new dated section recording J-07 step 3's VmPeak margin
      under `server.memory_cap_mb` for THIS iteration's step-1 warm.
- [ ] Required-still-passing journeys (J-01, J-03, J-04, J-05, J-06, J-08, J-09) remain green
      (deterministic replay + LLM fallback).
- [ ] No anti-goal violation introduced; AG-8/AG-10 respected throughout (all heavy compute
      launched only via `scripts/start-backend.sh`).
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-37-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-07 (all 4 steps, live evidence, backend-down/error-state tests scheduled LAST);
  smoke replay of J-01, J-03, J-04, J-05, J-06, J-08, J-09.
- Unit/integration: `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once`; a new
  byte-identity reference-oracle test pinned via `git show HEAD:apps/backend/app/engine/
  data_manager.py`; a new mutation-style test for the shared-cache fix; existing
  `test_data_manager.py` / `test_api_data.py` coverage-snapshot tests re-run for regressions.
- Error cases: a `MemoryError` raised mid-warm under a tightened `server.memory_cap_mb` (J-07 step
  4) must be caught by the existing per-item handler and must NOT propagate to a crash, wedge, or
  require a restart.

Test-first contract:

- TC-1: given the live full-deep-basis seed DB and a fresh backend process launched via
  `scripts/start-backend.sh`, when the ingest-finalize forward-aggregate warm runs for every
  configured horizon while `GET /api/backtest` is served for each horizon throughout in one
  long-lived process, then the warm completes without crashing and every `/api/backtest` response
  returns HTTP 200 with evidence byte-identical to a pre-warm baseline read.
- TC-2: given TC-1's warm is running, when `GET /api/health` is polled once per second for the
  full duration, then every poll returns HTTP 200 and no gap between consecutive successful polls
  exceeds ~2.15s of loop jitter (no frozen or unresponsive window).
- TC-3: given TC-1's warm completes, when the process's peak memory (VmPeak) is read from
  `/proc/<pid>/status`, then it is recorded as under `server.memory_cap_mb`, and the margin (KB
  and %) is written into a new dated section of `reports/perf-budgets.md`.
- TC-4: given a throwaway backend process launched via `scripts/start-backend.sh` with a tightened
  `server.memory_cap_mb`, when memory pressure is induced during a warm, then the warm aborts with
  a logged `MemoryError`-class abort (not a crash) while the SAME process continues to answer
  `GET /api/health` with HTTP 200 and continues serving previously-cached reads, with no restart.
- TC-5: given a browser-QA test plan targeting J-07, when the plan is assembled, then every
  backend-down / error-state test appears strictly AFTER every other J-07 assertion (steps 1-4),
  so a denied restart after an error-state test cannot strand any earlier assertion.
- TC-6: given `_do_backfill` runs a K≥3-date parallel backfill (`backfill_workers > 1`) against the
  live seed DB, when every full-series bar-store load (prefill + any lazy fallback) is counted per
  symbol across the whole job, then `max(load_counts.values()) == 1` for every symbol touched —
  `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` passes.
- TC-7: given the shared-cache fix from TC-6, when the persisted `CoverageSnapshot` rows and the
  `_do_backfill`-created scanner-run payloads for the same K dates are compared against a
  `git show HEAD`-pinned reference oracle for the same inputs, then the two are byte-identical.
- TC-8: given the fix from TC-6/TC-7, when a mutation-style test perturbs a value inside the
  shared-cache path (e.g. swaps which symbols' bars the second call site sees), then the mutation
  is detected as a test failure — proving the oracle is load-bearing, not a rubber stamp that would
  stay green after a full revert.
- TC-9: given J-01/J-03's own backfill journeys, when a bounded-range and an unrestricted-range
  backfill are each re-run after this iteration's fix, then their persisted run-summary contract
  fields (`dates_total`, per-date exclusion breakdown, `aggregates_refreshed`) are unchanged from
  pre-fix values for the same inputs (no regression to J-01/J-03's own acceptance).
- TC-10: given this iteration's dev/review/browser-qa/audit/closure lanes all complete, when the
  closure step reads `docs/handoffs/goal-ops-hardening-iter-37-user-visible-changes.md`, then the
  document is scored on whether it CLAIMS no visible changes (it correctly claims backend-only),
  not merely on whether the substring "backend-only" appears anywhere in it — if the gate still
  false-positives on the substring alone, record it as a repeat instance of the known
  `closure_gate.py` framework defect (out of dev scope) rather than treating it as a real
  closure failure.

## NOTES

- This is the third consecutive dispatch targeting J-07's completion (iter-35 built nothing due to
  an `evidence`-depth mis-dispatch; iter-36 built the code but never ran the browser lane because a
  mid-plan backend-down test stranded it). This spec's `Depth: full` line and the TC-5/binding
  iter-36 lesson exist specifically to prevent both failure modes from recurring a third time.
- If, despite TC-5's ordering, the browser-QA lane is still denied permission to restart the
  backend after a legitimate error-state test, that is worth recording as a NEW, distinct finding
  (not silently re-attempting) — the iter-36 evaluator already established this is session-specific
  rather than environmental (the auditor booted the backend himself with the ordinary launch
  script), so a repeat denial is process information, not a product defect.
- `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once`'s exact numbers (before
  this fix: max 10/typical 2 on iter-36's WIP tree, max 11/typical 3 on unmodified HEAD) come from
  the iter-36 reviewer's `git stash`-compared measurement, recorded in the iter-36 log tail
  inlined into this decompose dispatch — re-verify them fresh rather than trusting the prior
  numbers blind, since the tree has moved since that measurement.
