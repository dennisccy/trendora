# Goal Iteration 43 — REGRESSION_HALT resume: revert the prefill regression, honest job-launch failures, `start-frontend.sh` host-guard, live J-05/J-07 re-verification

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 43
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict was REGRESSION (an explicit escape condition alongside ESCALATE per the binding-by-default rule); the evaluator's own depth recommendation for this iteration is independently `full`.
- **Frontend Present:** no
- **Target journeys:** J-05, J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-06, J-08, J-09 (full regression of the passing set — explicit evaluator next-step item 3: "re-run all eight journey checks after the memory decision lands," since the six passes recorded at iter-42 were photographed minutes before that iteration's outage)
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a
    **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked
    values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha
    claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
    for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed
    out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of;
    never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the
    post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every
    existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error
    boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded
    whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only
    against the committed seed / local provider fixtures — no live external network calls or
    paid data services may be introduced without an explicit goal.md amendment. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills,
    full-universe rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched
    only via the project launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those
    scripts MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env`
    whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`,
    `malloc_arena_max`). Never remove, weaken, or bypass these caps: stripping a HOST-GUARD
    marked block from a launch script is a REGRESSION regardless of test outcomes. The ceilings
    are a physical constraint of the current host (two instant hardware resets under all-core
    vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance budget to
    optimize away. *(Owner amendment 2026-07-31, two corrections of record — nothing above is
    relaxed: `memory_cap_mb` / `malloc_arena_max` live in `config.yaml`, not in `host-guard.env`;
    and the 2026-07-20/21 resets were subsequently attributed to an uncorrected hardware
    data-fabric fault (`host-guard.env`, 2026-07-30), so the ceiling VALUES are an owner-set
    envelope — re-set by the dated entry in "Additional binding notes" below — while this
    paragraph's prohibition on agents removing, weakening, or bypassing caps is unchanged.)*
    *(critical)*

## GOAL

Resume from the iter-42 REGRESSION_HALT now that the owner has raised the memory envelope: execute
the four owner-commissioned follow-up actions (revert the proven-net-negative `_BarCache.prefill`
filter, close the job-launch silent-failure gap behind J-05's regression, extend host-guard coverage
to `start-frontend.sh`, and live re-verify J-05 and J-07 against the raised cap and rescoped health
budget) so both journeys are re-scored on honest, current evidence.

## BACKGROUND

Prior verdict was REGRESSION. iter-42 closed the target-journey verification hole and the first real
check it ran found J-05 "Aggregates are precomputed at ingest" regressed (a backfill job whose worker
never started stayed `running` forever, showing nothing) and J-07 "Heavy aggregates never take the
service down" newly failing (a live outage: `/api/health` 500×4 then unresponsive, `MemoryError`).
Root cause: the 30-year basis (~3.3M rows) no longer fit `memory_cap_mb: 6144` — the iter-42 evaluator
halted for an owner-only decision among three options (raise the cap, shorten the basis, or relax the
goal's timing promise).

**The owner has since decided and it is already committed** (`1376601c`, 2026-07-31, dated amendment
in `docs/goal.md` "Additional binding notes"): `server.memory_cap_mb` 6144→8192, `HOST_GUARD_MEMORY_HIGH`
10G→12G, and the machine-wide `HOST_GUARD_GLOBAL_MEMORY_BUDGET` 22G→24G are **already live in the
tree — not this iteration's diff.** The same amendment commissions four follow-up actions, none of
which has landed yet (verified directly: `git show 1376601c --stat` touches only `config.py`,
`config.yaml`, `docs/goal.md`, `host-guard.env`, `reports/perf-budgets.md`; `_BarCache.prefill`'s
`WHERE symbol IN (...)` filter is still present in `prices.py:258`; `HOST_GUARD_MARKER_FILES` still
reads only `"scripts/dev.sh scripts/start-backend.sh"`): (1) revert iter-42's `_BarCache.prefill`
symbol filter — the iter-42 auditor re-measured it as a **+5.1% peak-memory REGRESSION**, not the
recorded 2.5% win; (2) `scripts/start-frontend.sh` joins `HOST_GUARD_MARKER_FILES`; (3) the
`GET /api/health` budget is rescoped (steady-state ≤0.1s unchanged; a bounded ~30s background-compute
window now reads ≤2s, 100% HTTP 200) and needs a live re-measurement, not just the amendment's
re-expression of old numbers against the new cap; (4) the warm seam (`compute_forward_aggregates` and
its siblings) is **unfrozen** (permitted, not mandated) for further bounding work if the raised cap
still proves insufficient. This iteration executes all four.

Separately — and this is *not* part of the owner amendment — J-05's regression has a second, distinct
cause the evaluator named as next-step priority (1): `start_data_job`/`start_resume_job`
(`app.engine.data_manager:4643/4686`) call `threading.Thread(...).start()` with no guard. `_run_job`'s
own outer exception handler already marks a job `failed` with a message for every failure that occurs
*inside* the thread body (`prog.status = "failed"` + `_record_error`, `data_manager.py:4505-4506`) —
but a failure to *launch* the thread at all (the live incident: `RuntimeError: can't start new thread`,
`logs/backend.log:153050-153075`) happens outside that guard, orphaning the just-created run-history
row at its creation-time `running` default forever. This breaks goal.md's own "Zero silent zero-work
jobs" promise and is fixed narrowly here — a general stuck-but-technically-running-thread watchdog is
a materially larger, unevidenced change and stays out of scope (see OUT OF SCOPE).

Per rule 3 (unblockers next) and rule 5 (never bundle two risky journeys), J-05 and J-07 are targeted
together because they share the SAME root cause and the SAME owner decision unblocks both — not
because this iteration takes two risky code actions. Of the five concrete changes this iteration makes,
three are small and mechanical (the revert, the host-guard extension, the thread-launch guard) and the
fourth is pure re-verification; the one genuinely risky lever — bounding `compute_forward_aggregates`
et al. — is made CONDITIONAL on what the live re-measurement actually shows, not committed upfront (see
`assumptions.md` iter-43 for the full reasoning). Ground-truth evidence already on record
(`reports/perf-budgets.md`'s OWNER AMENDMENT section) measured an isolated full historical
forward-aggregate warm at 2.6–3.7 GB VmPeak against the new 8192 MB cap (32–44%), so a passing
measurement is the likelier outcome. Depth is `full` both because the evaluator's own recommendation is
binding by default and because a prior REGRESSION verdict is an explicit escape condition in its own
right (Full trigger 3 above) — this is also, independently, a structurally cross-cutting change (host
config, two launch scripts, `data_manager.py`, `prices.py`, `reports/perf-budgets.md`, and potentially
`forward_testing.py`).

Applies the binding iter-42 (second) lesson verbatim: a memory measurement that only measures the work
REMOVED is not a measurement — any before/after figure taken for the revert, or for the conditional
warm-seam bound if it triggers, must measure the whole job, not a narrowed function. Applies the
binding iter-39 lesson: reuse the ALREADY-sanctioned J-07 step-4 test hook rather than tuning a fresh
cap. Deliberately NOT this iteration's scope: a sixth `_BarCache.prefill` bound attempt beyond the
revert (the compression-only disposition — "a COMPRESSION, not a BOUND" — stays disclosed, unresolved,
per the carried assessment); T2's `bars_asof` 70-80× slowdown (iter-41's `_SymbolColumns`, unrelated
to the filter being reverted here); the same thread-launch-guard gap in `warmup.start_warmup` /
`forward_testing`'s background-dispatch thread (same class, no evidenced incident — rule 5); iter-33/g,
Regime Lab's cold `view=pooled` dispatch (deferred an eighth time); J-07's `[NEW]` walkthrough
(capture-only, never an iteration's own goal — rule 7).

## IN SCOPE

### Backend

- [ ] `apps/backend/app/engine/prices.py` (`_BarCache.prefill`) — revert the iter-42
      `WHERE symbol IN (expected_symbols)` filtered-eager path back to the pre-iter-42 whole-table
      streamed load (iter-41's `_SymbolColumns` columnar compression itself is UNCHANGED and stays;
      only the filter layered on top is undone). Preserve the `KeyError` publish-race fix that landed
      alongside the filter (`prices.py:364-377`/`:422-427`, a lock-barrier guard in
      `bars_asof`/`bars_asof_window`'s lazy-fallback path) and its regression test unchanged through
      the revert. Update `apps/backend/tests/test_bar_cache.py`'s filter-specific tests to a
      byte-identity oracle against the pre-iter-42 reference body.
- [ ] `apps/backend/app/engine/data_manager.py` (`start_data_job`, `start_resume_job`) — guard each
      `threading.Thread(...).start()` call so a launch failure reaches the SAME `prog.status = "failed"`
      + `_record_error` mechanism `_run_job`'s own outer exception handler already uses for every
      in-flight failure, finalizing the run-history row with a descriptive message instead of leaving
      it at its creation-time `running` default. The HTTP layer must return an honest error response
      for this case, never a false 200 over an orphaned job.
- [ ] `scripts/start-frontend.sh` — add the HOST-GUARD block (CPU-affinity mask + BLAS/OMP/numexpr
      thread caps read from `project-extensions/host-guard/host-guard.env`), mirroring
      `scripts/start-backend.sh`'s existing block.
- [ ] `project-extensions/host-guard/host-guard.env` — add `scripts/start-frontend.sh` to
      `HOST_GUARD_MARKER_FILES` (currently `"scripts/dev.sh scripts/start-backend.sh"`).
- [ ] `reports/perf-budgets.md` — run J-07 steps 1-3 live against the now-committed
      `memory_cap_mb: 8192` (full-horizon forward-aggregate warm via the ingest finalize path, 1Hz
      `/api/health` poll throughout, a previously-cached `/api/backtest` read served concurrently,
      VmPeak recorded) and add a fresh dated section with the measured margin under 8192 MB. Re-run
      step 4's EXISTING sanctioned induced-pressure test hook (throwaway process, tightened cap,
      launched only via `scripts/start-backend.sh` — binding iter-39 lesson: reuse the hook, do not
      re-tune a fresh cap) and record whether the SAME process keeps serving `/api/health` and cached
      reads through the abort.
- [ ] Conditional, second priority, ONLY if the live measurement above shows the warm still exceeding
      8192 MB or the pressure-abort still wedging the process: apply a bounded-footprint change to
      `compute_forward_aggregates` / `_forward_agg_slice_map` / `_fr_slice_map` /
      `ensure_historical_forward_aggregates_dispatched` (now permitted, not mandated, by the dated
      goal.md amendment's "warm seam is UNFROZEN" clause) — byte-identical output required for all 5
      configured horizons, with and without `as_of` (J-07 acceptance). If the measurement instead
      confirms the warm already fits comfortably, do not touch these functions — document the passing
      measurement instead of a speculative change.

### Frontend

None — backend/tooling/launch-script only (`Frontend Present: no`).

### New user-facing capability

None — this iteration restores prior-known-good memory behavior, closes a job-status honesty gap using
the EXISTING status vocabulary, and re-verifies existing journeys against the owner's raised envelope;
no new feature.

### New information displayed

None new. A thread-launch failure now reaches the SAME already-displayed Job history `status`/
`message` fields every other job failure already surfaces through — this fixes the one gap where a
specific failure mode reached neither.

### New user actions

None.

### UI surface changes

None — no new component; the existing Data Manager run-history rows and global readiness badge render
unchanged shapes.

### Product surface delta

None visible in shape. J-05's Data Manager/coverage surfaces and J-07's global readiness badge +
`/backtest` surfaces are unchanged — only their underlying memory footprint, job-failure honesty, and
measured budgets change.

### Blueprint conformance

J-05 and J-07 keep their existing cross-cutting homes per `runs/goal-session-ops-hardening/state/blueprint.md`'s
Information Architecture table (J-05: Data Manager / Scanner Runs / Dashboard / Research / Evidence;
J-07: global readiness badge + `/backtest`) — no new page/nav/route this iteration. Blueprint updated
with an iter-43 narrative paragraph recording this scope (no Data Contract or Information Architecture
change).

### Data-contract additions

None. The revert, the thread-launch guard, and the host-guard script change are implementation-only
changes to the ALREADY-registered Coverage payload row (`app.engine.data_manager`/
`_compute_coverage_uncached`, `GET /api/data`) and Job history row (`app.engine.data_manager` finalize,
`GET /api/data` + `GET /api/data/jobs/{job_id}`) — same computing module, same serving endpoint,
byte-identical served values; job status/message reuse the row's existing field vocabulary (no new
field). If the conditional warm-seam bound lands, it is likewise an implementation change to the
ALREADY-registered "Regime score, market phase, realized forward-returns" row's
`compute_forward_aggregates` producer — same module, same three call sites, byte-identical output
required, never a second producer.

## OUT OF SCOPE

- A sixth attempt at bounding `_BarCache.prefill` beyond reverting iter-42's filter — the
  compression-only disposition stays disclosed and carried (assumptions.md iter-42 precedent).
- T2's `bars_asof` 70-80× slowdown (iter-41's `_SymbolColumns`, unrelated to the filter reverted here).
- The same thread-launch-guard gap in `warmup.start_warmup` / `forward_testing`'s background-dispatch
  thread (`forward_testing.py:1691`) — same class of gap, no evidenced incident there, deliberately
  deferred (rule 5: keep this iteration's risky surface confined to the two evidenced sites).
- iter-33/g — Regime Lab's cold `view=pooled` background dispatch (deferred an eighth time; rule 5).
- J-07's `[NEW]` walkthrough recording — capture-only, never an iteration's own goal (rule 7).
- Any further change to `server.memory_cap_mb` / `HOST_GUARD_MEMORY_HIGH` / the machine-wide budget
  beyond the owner's already-committed values (8192 / 12G / 24G) — byte-frozen this iteration.
- Any further `docs/goal.md` edit — the owner's amendment is already authored and committed; no
  additional edit is needed or authorized here.

## DEFINITION OF DONE

- [ ] `_BarCache.prefill`'s iter-42 symbol filter is reverted; `Bar` output is byte-identical to the
      pre-iter-42 (unfiltered, `_SymbolColumns`-based) implementation for every existing consumer (TC-1).
- [ ] The `KeyError` publish-race fix and its regression test survive the revert (TC-2).
- [ ] A thread-launch failure in `start_data_job`/`start_resume_job` marks the job `failed` with a
      descriptive message instead of leaving it `running` forever (TC-3, TC-4).
- [ ] `scripts/start-frontend.sh` carries a HOST-GUARD block and is listed in
      `HOST_GUARD_MARKER_FILES` (TC-5).
- [ ] J-05 is re-verified live via the existing `journey-scripts/J-05.json` golden script against the
      raised cap (TC-6).
- [ ] J-07 steps 1-4 are re-verified live via the existing `journey-scripts/J-07.json` golden script
      plus the sanctioned induced-pressure test hook, against `memory_cap_mb: 8192` and the rescoped
      ≤2s bounded-compute-window `/api/health` budget, with VmPeak margin recorded in
      `reports/perf-budgets.md` (TC-7, TC-8, TC-9).
- [ ] If the live measurement in TC-7/TC-9 shows the warm still over cap or the abort still wedging,
      `compute_forward_aggregates`'s bounding lands with byte-identical output (TC-10); otherwise the
      passing measurement is documented and these functions stay untouched.
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-06, J-08, J-09 remain green via full
      regression replay against this iteration's build (TC-11).
- [ ] No anti-goal violation introduced — AG-10's caps stay enforced end-to-end (strengthened, not
      weakened, by the `start-frontend.sh` addition); `_BarCache.prefill`'s AG-8 disposition in the QA
      report states the accurate carried state ("compression, not a bound"), never an unqualified pass.
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-43-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-05 (`journey-scripts/J-05.json`), J-07 (`journey-scripts/J-07.json`, all 4 steps); full
  regression replay of J-01, J-03, J-04, J-06, J-08, J-09.
- Unit/integration: `_BarCache.prefill`/`_SymbolColumns` byte-identity fixture (post-revert vs.
  pre-iter-42 reference); the `KeyError` publish-race regression test (unchanged, must still pass);
  a mocked `threading.Thread.start()`-raises test for both `start_data_job` and `start_resume_job`
  asserting the run-history row reaches `failed` with a message; (conditional) a fixture-backed
  byte-identity test for any warm-seam bounding change.
- Error cases: a `RuntimeError` (or equivalent) raised by `threading.Thread.start()` must never leave
  a job's run-history row at `running` with no further update; the existing NULL-tolerance path (B6,
  shipped iter-42) must not regress under the reverted prefill.

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps
to at least one concrete scenario line below.

- TC-1: given the pre-iter-42 `_BarCache.prefill` reference body (unfiltered, `_SymbolColumns`-based)
  captured as a byte-identity oracle, when `prefill` is called with an `expected_symbols` subset after
  this iteration's revert, then the returned `Bar` sequence for every symbol is byte-identical to the
  oracle's output and no `WHERE symbol IN (...)` filter is applied to the SELECT.
- TC-2: given a concurrent backfill exercising the parallel `bars_asof` publish path that previously
  raised `KeyError` before iter-42's in-audit fix, when the reverted `prefill` runs under the same
  concurrency, then no `KeyError` is raised and the existing regression test for this race still passes.
- TC-3: given `threading.Thread.start()` is mocked to raise `RuntimeError("can't start new thread")`
  inside `start_data_job`, when a backfill is requested, then the created run-history row's `status`
  reads `failed` and its `message` names the thread-launch failure, with no row left at `running` with
  zero further updates.
- TC-4: given the same mocked failure inside `start_resume_job`, when a resume is requested, then the
  resumed import's row reaches `failed` with a descriptive message via the same mechanism.
- TC-5: given `scripts/start-frontend.sh` after this iteration, when
  `project-extensions/host-guard/host-guard.env` declares `HOST_GUARD_MEMORY_HIGH`/CPU-affinity/
  thread-cap values, then `start-frontend.sh` applies the same HOST-GUARD block `start-backend.sh`
  already applies, and `HOST_GUARD_MARKER_FILES` lists `scripts/start-frontend.sh` alongside the two
  existing entries.
- TC-6: given the backend running the current build with `memory_cap_mb: 8192`, when the browser-qa
  agent replays `journey-scripts/J-05.json`'s single-day backfill step, then `/scanner-runs` lists the
  ingested date, its leaderboard renders the stored snapshot, and the persisted run record lists the
  finalize hook's refreshed aggregates with zero recompute-on-read.
- TC-7: given the backend running the deep basis with `memory_cap_mb: 8192`, when the full-horizon
  forward-aggregate warm is triggered via the ingest finalize path while `GET /api/health` is polled at
  1Hz throughout, then every poll returns HTTP 200 within the rescoped ≤2s bounded-compute-window
  budget, and the warm's VmPeak is recorded in a fresh `reports/perf-budgets.md` section showing its
  margin under 8192 MB.
- TC-8: given the same warm scenario, when a previously-cached `GET /api/backtest` read is issued
  concurrently, then it returns HTTP 200 throughout (J-07 step 1's "served ... throughout" clause).
- TC-9: given J-07 step 4's existing sanctioned induced-pressure test hook (a tightened
  `server.memory_cap_mb` in a throwaway process, launched only via `scripts/start-backend.sh`), when
  memory pressure is induced during a warm, then the warm aborts honestly via the existing per-item
  `MemoryError` isolation handler while the SAME process's `GET /api/health` and previously-cached
  reads keep responding HTTP 200 — no deadlock, wedge, or restart.
- TC-10 (conditional — only if TC-7/TC-9 show the cap or the abort path insufficient): given
  `compute_forward_aggregates`'s pre-bound reference output for a fixed as-of and horizon set, when the
  bounded implementation runs the same inputs post-fix, then its output is byte-identical to the
  reference for all 5 configured horizons, with and without `as_of`.
- TC-11: given the full required-still-passing set (J-01, J-03, J-04, J-06, J-08, J-09), when the full
  regression replay runs against this iteration's build, then all six journeys report PASS with dated
  evidence (screenshot or replay row).

## NOTES

- Applies the binding iter-42 (second) lesson verbatim: a memory measurement that only measures the
  work REMOVED is not a measurement — any before/after figure taken for the revert, or for the
  conditional warm-seam bound if triggered, must measure the whole job, not a narrowed function.
- Applies the binding iter-39 lesson: reuse the ALREADY-sanctioned J-07 step-4 induced-pressure test
  hook rather than tuning a fresh cap; and the binding iter-40 (second) lesson — `.yield_per()` bounds
  the cursor, not the accumulator — is directly relevant if the conditional TC-10 path is taken.
- The owner's 2026-07-31 amendment (commit `1376601c`) already raised `server.memory_cap_mb`,
  `HOST_GUARD_MEMORY_HIGH`, and the machine-wide budget; those three VALUES are NOT this iteration's
  diff. This iteration's diff is the amendment's four commissioned follow-up actions (revert,
  host-guard extension, live re-verification, conditional warm-seam bound) PLUS the job-launch
  honesty fix, which the evaluator named separately and is not part of the amendment itself.
- `_BarCache.prefill` remains a COMPRESSION, not a BOUND, on `daily_prices` after this revert — this
  iteration does not change that disposition, only removes iter-42's proven-net-negative filter
  attempt. State this honestly in the QA report's AG-8 row (carried disposition, not resolved).
- See `runs/goal-session-ops-hardening/state/assumptions.md` iter-43 for the full reasoning on bundling
  J-05/J-07 into one iteration while keeping the warm-seam rewrite conditional rather than committed
  upfront.
- Six consecutive evaluators have called the `GET /api/health` steady-state budget an owner decision;
  the owner has now rescoped it (not waived it) — this iteration re-measures against the NEW rescoped
  table, it does not revisit the decision itself.
