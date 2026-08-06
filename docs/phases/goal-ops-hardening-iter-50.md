# Goal Iteration 50 — Interlock the two heavy warms that killed the service; finish J-05's in-app proof

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 50
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior evaluator verdict was ESCALATE (iter-49); full depth is mandatory, no exceptions.
- **Frontend Present:** no
- **Target journeys:** J-07, J-05, J-06
- **Required-still-passing journeys:** J-01, J-03, J-04, J-08, J-09
- **Anti-goal reminders:**
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
    for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of;
    never introduce lookahead anywhere. *(critical)*
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

The backend stops dying when a live `/research/factor-lab` page view runs concurrently with the boot/re-warm path's own heavy evidence warm, and J-05's own defining case (a live in-app backfill of one unsnapshotted historical day) finally gets its first real in-product proof.

## BACKGROUND

Iter-49 fixed its own scoped work (both finalize-tail phases now terminate within TC-1's 1,200s bound on 3/3 live runs) but the backend DIED for 12m45s during that same round's own browser lane — the evaluator reconstructed the crash as **three concurrent heavy loops**, not one: (1) the ingest finalize tail (already isolation-guarded), (2) the boot/re-warm path's `_warm_drawdown_expectations` (`warmup.py:198`, uninterlocked with ingest — audit B2, now proven live-contributory by its own traceback), and (3) a live user page load of `/research/factor-lab` that raised an **uncaught** `MemoryError` at `research.py:1051` (`compute_factor_lab_all`'s per-(factor,horizon) `sorted(obs, ...)`) which is what actually killed the process. J-07 dropped `partial` → `failing` on this. The evaluator's next-step item (1) is explicit: "two changes must land together as ONE job" — bound the Factor Lab read and interlock the boot re-warm with ingest. This iteration does exactly that, plus one small same-subsystem companion fix (iter-49's own `phase_context_by_date` precompute currently runs unconditionally, contributing ~23.6-23.9s of the measured health-poll breaches — `reports/perf-budgets.md` Item R Addendum 6 mid-cluster).

Per the priority rubric: J-07 is the top-priority target (rule 1 — the most-recently-regressed-in-spirit journey; formally `partial`→`failing`, not a C.1 REGRESSION since it never held `passing`, per the iter-49 evaluator's own explicit, logged rejection of that verdict). J-05 and J-06 ride the SAME fix as unblockers (rule 3) — both need only a live-drill re-verification, not new code, once the crash source is removed: J-05's own in-app defining case has never completed because the crash (and predecessor crashes) kept interrupting it; J-06's Factor Lab page (UT-07) has never had a clean, in-budget measurement for the same reason. This keeps the iteration to ONE risky code change (rule 5) with two riders that need only verification.

**Lessons applied:** iter-49's lesson on attribution ("a per-phase log MESSAGE is not a per-phase ATTRIBUTION — read the traceback under it") binds the developer to confirm the actual crash frame during implementation, not just the log text, before claiming the fix addresses it. iter-49's second lesson ("a bound proven on an idle host with a throwaway DB copy is not a bound proven in the product") is why J-05's TC-10/TC-11 below require a live in-app measurement, not another isolated drill. iter-44's lesson (a memory-pressure guard proven by ONE green run is not proven) binds TC-2 to 3-5 consecutive runs. iter-46's lesson binds this iteration's browser lane to be the truly LAST product-code-adjacent event — any audit-fix after it voids the round (TC-13). iter-47's lesson binds the J-05 golden to assert against the NEW run's own row/testid, never page-wide text, and to be read (not just scored) before trusting it.

## IN SCOPE

### Backend
- [ ] Bound `compute_factor_lab_all`'s per-(factor,horizon) obs-build + sort (`apps/backend/app/engine/research.py:1051`, the confirmed crash frame) so a live page view cannot allocate an unbounded transient list-of-dicts on top of concurrent ingest/warm work — byte-identical output required for every (factor, horizon, decile) figure against a pinned pre-fix reference. Do NOT touch `_all_factor_observations_by_horizon` / `_all_fr_slice_map` (already bounded, iter-31/iter-52 work, unaffected by this defect).
- [ ] Add a shared warm-in-progress guard between the boot/re-warm path's `_warm_drawdown_expectations` (`apps/backend/app/engine/warmup.py:198`) and the ingest finalize tail's own heavy warm loops (`apps/backend/app/engine/data_manager.py`'s `_refresh_ingest_aggregates`) so the two never execute concurrently in the same process — the later one defers (log + retry on its own next natural trigger), non-fatal either way, mirroring this module's existing single-flight/guard conventions.
- [ ] Ensure a `MemoryError` raised inside the bounded `compute_factor_lab_all` loop is caught by the module's existing isolation convention (degrades the request honestly, never crashes the process) — a dedicated regression test under a tightened `ulimit -v` drill.
- [ ] Skip `drawdown_expectations_warm`'s per-claim `phase_context_by_date` precompute (`data_manager.py`, iter-49's own new code) entirely when zero claims actually need (re)computing, instead of running it unconditionally — closes the ~23.6-23.9s MID health-poll-stall cluster (`reports/perf-budgets.md` Item R Addendum 6).

### Frontend
None — this iteration is backend-only; no new UI surface, no changed rendering.

### New user-facing capability
None new. The existing `/research/factor-lab` page and the existing `/data` backfill flow become reliably crash-free under ordinary concurrent use; no new controls or displayed values.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
`/research/factor-lab` no longer risks taking the whole backend down when viewed while an ingest job or the boot re-warm is running; a historical-day backfill on `/data` now has a real chance to complete without being interrupted by that same crash.

### Blueprint conformance
All changes live inside the already-registered **Membership timeline / research hot-key caches** row (`blueprint.md` Data Contract) — same computing modules (`app.engine.research`, `app.engine.forward_testing`, `app.engine.data_manager`), same tables, same serving paths. Canonical homes unchanged: J-05 → Data Manager (`/data`) / Scanner Runs / Research; J-06 → cross-cutting measurement (`reports/perf-budgets.md`); J-07 → global readiness badge + `/backtest`, with `/research/factor-lab` as the crash site this iteration bounds. No new page, route, or nav entry.

### Data-contract additions
None. No new displayed value, no new field, no second computing module or serving endpoint for any already-registered row. The warm-in-progress guard is an internal control-flow mechanism, not a served value.

## OUT OF SCOPE

- The health-poll EARLY stall cluster (inside `coverage_membership_timeline_refresh`, at the backfill-stage boundary) and LATE stall cluster (inside the `combination:composite:h20` claim, `_combination_observations`'s own ~250s cost) — both real, both named in `reports/perf-budgets.md` Item R Addendum 6, both separate diagnosis efforts from this iteration's one risky action (rule 5). Carried.
- Raising `memory_cap_mb` / `malloc_arena_max` or any other AG-10 owner-set value — the fix must work inside the existing 8192MB envelope.
- The Regime Lab's own separate 8192MB-cap hit (`research.py`, iter-33/g) — 15th deferral, carried, untouched.
- The badge wording after a permanently-failed warm-up (iter-29/b) — carried, untouched.
- Carried, untouched (same as iter-49's list): iter-31/e; iter-32/f; iter-35/k; iter-36/n; iter-37/o; iter-37/q; iter-39/u; iter-46/az; iter-46/ba; iter-47/bd; iter-47/bf; iter-47/bi; iter-48/bj.
- Evidence capture, screenshot retakes, and the J-07/J-05 `[NEW]` demo walkthroughs — never an iteration goal (binding "Do not redo"); ride the showcase / evidence-makeup lane on whatever fresh, real screenshots this iteration's own browser lane produces.
- `_combination_observations`'s own ~250s cost and the per-claim timing label collision (both iter-49's own item 5, small, not this iteration's one risky action).
- Extending the golden replay script to prove TC-1's full 1,200s termination directly — already investigated and found infeasible (iter-49, `demo_runner.py`'s hard-capped 20,000ms per-step timeout); TC-1 continues to be proven via the live/integration drill pattern, not the replay lane.

## DEFINITION OF DONE

- [ ] J-07 passes via browser-qa-agent — all 4 acceptance steps, including the health poll honoring its ≤2s bounded-background-compute ceiling with zero non-200/timeout responses
- [ ] J-05 moves visibly on real, in-app lane evidence (not an isolated-drill-only proof) via browser-qa-agent
- [ ] J-06's Factor Lab page load is measured within budget and recorded in `reports/perf-budgets.md`
- [ ] Required-still-passing journeys (J-01, J-03, J-04, J-08, J-09) each produce a real executed row (PASS or FAIL, never SKIP/blank) via deterministic replay + LLM fallback
- [ ] No anti-goal violation introduced — in particular no new AG-8 crash and no AG-10 cap change
- [ ] Unit tests pass; byte-identity proven for `compute_factor_lab_all`'s bounded implementation; no regressions
- [ ] The full 8-journey browser/replay lane runs LAST, strictly after all code for this iteration lands — no product-code change follows it; any audit-fix pass that touches product code triggers a mandatory re-run before closure
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-50-dev.md`

## TESTING REQUIREMENTS

- Browser: J-05, J-06, J-07 (target journeys); J-01, J-03, J-04, J-08, J-09 (required-still-passing, replay + LLM fallback)
- Unit/integration: `compute_factor_lab_all` byte-identity test against a pinned pre-fix reference for every (factor, horizon, decile) figure; a memory-pressure drill under a tightened `ulimit -v` proving the bounded loop degrades honestly instead of crashing, run 3-5 consecutive times; a warm-in-progress guard test proving the boot re-warm and the ingest finalize warm never run concurrently in one process, in both trigger orders; a test proving `phase_context_by_date` is not invoked when zero claims need (re)computing
- Error cases: a `MemoryError` raised inside `compute_factor_lab_all`'s bounded loop must be caught by the existing isolation convention and degrade the request honestly (never propagate to kill the process); a warm that defers under the new guard must resume on its own next natural trigger, never silently drop the work

Test-first contract: every DEFINITION OF DONE checkbox maps to at least one concrete scenario line below.

- TC-1: given the live committed DB with an ingest job's finalize-tail warm running, when a user loads `/research/factor-lab`, then `GET /research/factor-lab`'s `?all=true` call to `compute_factor_lab_all` completes without an uncaught `MemoryError` and an immediately-following `GET /api/health` still answers 200.
- TC-2: given a tightened `ulimit -v` memory-pressure drill launched via `scripts/start-backend.sh`, when `compute_factor_lab_all` is invoked against a full-scale live-shaped fixture, then any `MemoryError` raised inside the per-(factor,horizon) sort loop is caught by the existing isolation convention and the response degrades honestly — run 3-5 consecutive times with no new escape site on any run.
- TC-3: given `compute_factor_lab_all`'s bounded implementation, when compared against a pinned pre-iter-50 reference oracle, then every (factor, horizon, decile) figure is byte-identical (AG-3).
- TC-4: given the boot/re-warm's `_warm_drawdown_expectations` is about to start, when an ingest job's own finalize-tail heavy warm is already in flight in the same process, then the boot re-warm defers (does not start a second concurrent heavy loop), logs the deferral, and resumes on its own next natural trigger.
- TC-5: given the ingest finalize-tail's own heavy warm is about to start, when the boot re-warm is already in flight, then the finalize-tail warm defers analogously (the guard holds in both trigger orders) — never two heavy warms live at once in one process.
- TC-6: given a real live ingest finalize-tail run where zero drawdown-expectation claims need (re)computing, when the `phase_context_by_date` precompute step is reached, then it is skipped entirely (not invoked), versus the prior unconditional ~23.6-23.9s cost recorded in `reports/perf-budgets.md` Item R Addendum 6.
- TC-7: given J-07 step 1's full-horizon forward-aggregate warm running live in one long-lived process, when `GET /api/health` is polled once per second throughout, then every poll answers HTTP 200 within the owner-amended ≤2s bounded-background-compute ceiling, zero non-200 responses, zero timeouts, on 3 consecutive live runs.
- TC-8: given the SAME warm running, when peak process memory (VmPeak) is recorded, then it stays under `server.memory_cap_mb=8192` with the margin recorded in `reports/perf-budgets.md`.
- TC-9: given a throwaway process with a tightened memory cap, when memory pressure is induced mid-warm, then the warm aborts honestly per the existing isolation convention while the SAME process keeps serving `GET /api/health` and previously-cached reads — never a deadlock, wedge, or restart requirement.
- TC-10: given `/data` on a live backend, when a backfill is run covering exactly one unsnapshotted historical trading day (verify live, before running, that the target date still has 0 snapshot rows — `2012-01-04` was confirmed 0-rows/480-symbols-with-bars as of iter-49; re-verify it was not consumed by any intervening lane run), then `/scanner-runs` lists the date and its leaderboard renders the stored snapshot, and the persisted run record's `aggregates_refreshed` lists which finalize-hook aggregates it actually refreshed.
- TC-11: given the SAME backfill just completed, when the backend is restarted and `/data` is visited cold, then coverage renders from the persisted payload within its committed budget and the process performs no whole-table `daily_prices` prefill.
- TC-12: given `/research/factor-lab` loaded on a warm backend in prod mode (`scripts/start-backend.sh` / `scripts/start-frontend.sh`) with this iteration's bound in place, when time-to-interactive and on-load API latency are measured, then both are recorded in `reports/perf-budgets.md` and within their committed budgets.
- TC-13: given all code changes for this iteration have landed, when the full 8-journey browser/replay lane is run, then it is the LAST product-code-adjacent event before this iteration is scored; any subsequent fix-mode/audit-fix pass that changes product code triggers a mandatory re-run of the full lane before closure.
- TC-14: given J-04/J-08/J-09's own journey checks, when the lane described in TC-13 runs, then each produces a real executed row (PASS or FAIL, never SKIP/blank) because the backend stays continuously available throughout this iteration's own testing.

## NOTES

- **Assumption logged (see `assumptions.md`):** this spec bundles three sub-fixes (the Factor Lab bound, the warm-in-progress guard, and the `phase_context_by_date` skip) under ONE "risky change" per rule 5, on the grounds that the evaluator's own words call the first two "ONE job" and the third is a small companion fix inside the SAME subsystem iter-49 itself just modified. A reader who takes rule 5 more strictly could split the third fix into its own iteration.
- **Do not re-open** iter-46/47/48's already-confirmed accumulator bounds (`_combination_observations`'s chunking, `compute_drawdown_expectations`'s retention bound, `samples.py`'s `total`/`regime` slices) — those are "Do not redo," unaffected by this iteration.
- **QA report discipline (iter-46 lesson):** if any fix-mode or audit-fix pass changes product code after the browser lane has run, the QA report must be regenerated from that re-run, never hand-edited to reconcile a stale PASS against a browser FAIL — iter-49 shipped exactly that contradiction (`bt`) and it must not repeat.
- **Golden discipline (iter-47/iter-48 lessons):** before trusting J-05's replay row as evidence, read `journey-scripts/J-05.json`'s actual step content (not just its PASS/FAIL verdict) and confirm it asserts against the NEW run's own row/testid, not page-wide text that a persisted history panel could satisfy regardless of outcome.
- If, after landing the fix, TC-1/TC-2 still show `compute_factor_lab_all` as a live contributor to memory pressure (rather than fully closed), score J-07 honestly on what was actually proven rather than rounding up — this session's evaluator has repeatedly flagged over-claiming from a single or idle-host measurement.
