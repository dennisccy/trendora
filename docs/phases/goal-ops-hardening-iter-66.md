# Goal Iteration 66 — Bound `coverage_membership_timeline_refresh`'s GIL hold and unify the health-poll instrument

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 66
- **Mode:** next
- **Depth:** lean
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
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills, full-universe rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched only via the project launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those scripts MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env` whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`, `malloc_arena_max`). Never remove, weaken, or bypass these caps: stripping a HOST-GUARD marked block from a launch script is a REGRESSION regardless of test outcomes. The ceilings are a physical constraint of the current host (two instant hardware resets under all-core vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance budget to optimize away. *(Owner amendment 2026-07-31, two corrections of record — nothing above is relaxed: `memory_cap_mb` / `malloc_arena_max` live in `config.yaml`, not in `host-guard.env`; and the 2026-07-20/21 resets were subsequently attributed to an uncorrected hardware data-fabric fault (`host-guard.env`, 2026-07-30), so the ceiling VALUES are an owner-set envelope — re-set by the dated entry in "Additional binding notes" below — while this paragraph's prohibition on agents removing, weakening, or bypassing caps is unchanged.)* *(critical)*

## GOAL

Find the specific call site inside `coverage_membership_timeline_refresh` — the one finalize-tail phase iter-65's own live drill pinned this session's remaining `GET /api/health` ceiling breach to — and bound it with the same proven chunk+yield pattern already used elsewhere in this finalize tail, then replace the two disagreeing health-poll counters this session has been running with one canonical, checked-in script so future rounds stop arguing over the number.

## BACKGROUND

The evaluator's depth recommendation for iteration 66 is **lean**, and it is binding: the prior verdict (iter-65) was CONTINUE, not ESCALATE/REGRESSION; iter-65's own coherence pass is COHERENCE-PASS (a deterministic zero-change pass); "Consecutive lean iterations dispatched: 2" is nowhere near the 6-iteration hardening cadence; and this iteration lands no new user-visible capability or brand-new full-stack journey — it bounds an already-existing internal compute path and canonicalizes a test/QA script (`apps/frontend/*` is untouched). No full trigger holds; needing tests is never a valid trigger, and this scope is a nameable blast radius (`apps/backend/app/engine/data_manager.py`'s and `universe_resolver.py`'s `coverage_membership_timeline_refresh` call chain, plus one QA drill script).

iter-65's own next-step order names this "the last named in-code target left for J-07": its drill (1,057 polls, 1,057 HTTP 200, 0 unanswered) found exactly ONE breach, 2.370s, opening and closing entirely inside `coverage_membership_timeline_refresh`'s own 6.81s window (`21:19:54.129Z` → `21:20:00.935Z`, per `logs/backend.log`'s phase-timing line) — with **zero** breaches inside `factor_lab_all_warm` (the prior five iterations' target, now closed per iter-65's own four escalating profiles finding no further hold there; binding "Do not redo"). `universe_resolver.py`'s own iter-53 comment trail already documents the leading candidate: `resolve_with_reasons`'s per-symbol loop, reached from this SAME phase's `membership_timeline_cached` cache-miss fallback. The SAME round also found its own instrument disagreeing with itself by ~40x (dev `poll_health.py`: 1/1,057; browser-QA lane's ad hoc subprocess-per-poll bash/curl loop: 8/240, max 4.194s) — iter-65's next-step item (2) asks to "use ONE counter everywhere."

Lesson applied (iter-65): prove the instrument and attribute each breach to an exact phase from the app's own millisecond log markers BEFORE chartering a code fix — done (the phase is already named); this iteration additionally removes the SECOND source of doubt (two disagreeing counters) so the NEXT round's drill speaks with one voice. Lesson applied (iter-63): recount any latency claim from the raw CSV as a full distribution (count-over-ceiling, p90, p99, max), never a single-poll headline. Lesson applied (iter-58/iter-64): open the evidence frame/log directly rather than trusting a prose summary of it.

Per priority rubric rule 6, this iteration does not touch either OWNER-gated item (the 17-times-asked 2-second-ceiling policy question; the `browser-qa-phase.sh` ordering fix) — both stay parked in NOTES/OUT OF SCOPE. Per rule 5, this iteration carries exactly ONE risky product-code action (bounding `coverage_membership_timeline_refresh`'s GIL hold); the poll-script canonicalization and the two small carried items (iter-64/c, iter-64/d) are tooling/mechanical/investigative, not a second risky change.

Cost discipline: this iteration's health-poll drill piggybacks on the SAME live ingest the developer already needs to trigger `coverage_membership_timeline_refresh` for verification, rather than launching a second job — matching the pattern iter-64/65's decomposers used while the owner's cost-sanction question on the replay lane's real ingest stays open.

## IN SCOPE

### Backend
- [ ] Re-run the session's established interrupt-driven stall-profiling method (thread-stack sampling on any `GET /api/health` handler blocked >0.30s — iter-52/53's own method, profile-before-bounding per their two-pass discipline, since iter-52's blind-yield-only first pass measured WORSE) during a real `coverage_membership_timeline_refresh` window, to name the exact call site still holding the GIL/a lock long enough to breach the 2.0s poll ceiling. Leading candidate per `universe_resolver.py`'s own iter-53 comment trail: `resolve_with_reasons`'s per-symbol loop (`data_manager.py` ~4310-4327 → `universe_resolver.py` ~234-243) — the live profile governs, not this guess.
- [ ] Bound whatever call site the profile names using the SAME established chunk+cooperative-yield pattern already proven on this finalize tail (iter-52's `_cooperative_sorted`/`_cyclic_gc_paused`; iter-53's own extension to this exact phase's coverage/membership-timeline pair) — no new aggregation algorithm, no change to what is computed, only when the GIL/lock is handed off.
- [ ] Add/extend a fixture-backed equality test proving the bounded call site returns byte-identical `admitted`/`excluded_counts` and persisted `coverage_snapshot`/`membership_timeline_cache` payload rows to the pre-fix computation for the same DB state.
- [ ] Preserve the existing MemoryError-distinct isolation handler wrapping this phase (`data_manager.py` ~4339-4345, iter-53/iter-8 convention) unchanged — verify its existing test still passes unmodified.
- [ ] Investigate the duplicate-run-row pattern (iter-64/d: one `job_id` producing both an `interrupted` row and a post-restart `ok` row in `data_provider_runs`) at its resume/retry call site (`start_data_job`/`resume_job`, `app.engine.data_manager`); fix it if the cause is a small, isolated write-path change, else write the named cause into the ledger honestly (never silence).

### QA / tooling (not product code, no Data Contract row — matches the iter-18/23/33/39/42 precedent)
- [ ] Promote the per-iteration throwaway `poll_health.py` drill script (previously freshly copied into each `runs/goal-ops-hardening-iter-N/evidence-drill/` directory) into ONE checked-in canonical script, `scripts/qa/poll_health.py`: single HTTP client, one poll per second, no subprocess-per-poll spawn.
- [ ] Extend the canonical script to record concurrent host load (`os.getloadavg()`'s 1-minute figure and `os.cpu_count()`) as a column on every poll row.
- [ ] Route this iteration's own dev evidence-drill AND its J-07 browser-qa test case (TESTING REQUIREMENTS below) through this SAME canonical script — no ad hoc curl/bash polling loop, no second counter.
- [ ] Correct `journey-scripts/J-05.json`'s closing `_notes` entry (iter-64/c) to state the actual shipped sentinel window (`demo_runner.py`'s `_SENTINEL_WINDOW_START`/`_END`, 2005-03-01..2016-12-31) instead of the currently wrong 1996-01-01..2004-12-31 text — a test-fixture comment fix only, no behavior change.

### Frontend
- None. No `apps/frontend/*` file is touched this iteration.

### New user-facing capability
None — this iteration bounds an internal compute path so an already-shipped guarantee (the app stays responsive during a heavy background job) holds under the one phase that currently breaches it, and canonicalizes a measurement script. No new page, control, or displayed field.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
No visible change to any page. The global readiness badge (top bar, every page) and `/backtest`'s per-horizon evidence keep answering the same way they always have — this iteration's success criterion is that they answer within budget during `coverage_membership_timeline_refresh` too, not that they look or behave differently.

### Blueprint conformance
No new page/route/nav entry. This work lives entirely under the blueprint's existing "J-07 — Heavy aggregates never take the service down" home (global readiness badge + `/backtest`) and reads/serves the already-registered "Coverage payload," "Membership timeline / research hot-key caches," and "Job history" Data Contract rows (`runs/goal-session-ops-hardening/state/blueprint.md`) unchanged. `blueprint.md` gains an additive iter-66 narrative note only (appended before the Information Architecture section) — no row, computing module, or endpoint changes.

### Data-contract additions
None. `refresh_coverage_snapshot`, `universe_resolver.resolve_with_reasons`, and `start_data_job`/`resume_job` keep their existing single computing module (`app.engine.data_manager` / `app.engine.universe_resolver`) and serving endpoint/table (`GET /api/data`, `coverage_snapshot`, `membership_timeline_cache`, `data_provider_runs`) — the equality test's whole purpose is to prove the bound introduces zero output difference. `scripts/qa/poll_health.py` is a QA/test artifact, not a served or displayed value, per this session's standing iter-18/23/33 precedent that pipeline/QA-tooling scripts are not Data Contract rows.

## OUT OF SCOPE

- Re-profiling `compute_factor_lab_all_warm` for a further GIL/lock hold — binding "Do not redo": four independent escalating tests already found none.
- A bare control/attribution drill re-run to re-litigate the iter-63/64 elevation — binding "Do not redo"; this iteration's drill verifies a real code change, not another attribution pass.
- The owner's 17-times-asked 2-second-ceiling policy question (long jobs vs. short jobs only) — human-owned, stays parked.
- The `scripts/automation/browser-qa-phase.sh` line-286-before-272 ordering fix — owner sign-off still pending.
- The cost-sanction decision on the replay lane's real ~17-minute ingest every round — owner-gated; this iteration's drill piggybacks on the same job it already needs to trigger for verification rather than adding a second one.
- A non-trivial resume/retry mechanism redesign for iter-64/d, if investigation shows the fix is not small and isolated — disclosed honestly, not force-fixed, per rule 5's one-risky-change discipline.
- The J-05 walkthrough capture (unrecorded for 7 rounds) — rides along only if a showcase/demo lane happens to run; not this iteration's own goal.
- iter-33/g (the Regime Lab) and the other long-carried items in iteration-state's history (iter-29/b, iter-31/e, iter-32/f, iter-35/k, iter-36/n, iter-37/o, iter-37/q, iter-39/u, iter-46/az, iter-46/ba, iter-47/bd, iter-47/bf, iter-47/bi, iter-48/bj, iter-57/f, iter-57/l, iter-59/g, iter-59/h, iter-59/k, iter-62/e, iter-62/f, iter-63/a, iter-63/b, iter-63/d, iter-64/b, iter-64/e) — none bear on J-07's remaining gap; left untouched.

## DEFINITION OF DONE

- [ ] Target journey J-07 re-verified via the canonical health-poll drill (TC-1) and browser-qa
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-06, J-08, J-09 remain green (deterministic replay + LLM fallback)
- [ ] No anti-goal violation introduced (AG-3 byte-identity, AG-8 resilience/no-unbounded-load, AG-9 offline-deterministic ingest, AG-10 host caps all hold)
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-66-dev.md`

## TESTING REQUIREMENTS

- Browser: J-07 (steps 1-2, the crash-free warm + healthy `/api/health` sequence, measured via `scripts/qa/poll_health.py`); regression replay/LLM fallback for J-01, J-03, J-04, J-05, J-06, J-08, J-09
- Unit/integration: a fixture-backed equality test for whatever call site inside `coverage_membership_timeline_refresh`'s chain gets bounded this iteration; the existing MemoryError-isolation test for this phase must keep passing unmodified; a unit test for `scripts/qa/poll_health.py`'s host-load column
- Error cases: the bounded call site must still degrade honestly under an injected `MemoryError` (matching the existing per-item isolation handler — no unhandled exception escapes the finalize-tail phase; AG-8)

Test-first contract:

- TC-1: given a live backend process running a real ingest finalize tail (a single-date backfill that creates a new snapshot triggers `coverage_membership_timeline_refresh`), when `scripts/qa/poll_health.py` polls `GET /api/health` once per second throughout the whole finalize tail, then every poll whose timestamp falls inside `coverage_membership_timeline_refresh`'s own logged start→end window (`logs/backend.log`'s phase-timing line) answers HTTP 200 in under 2.0 seconds — 0 breaches attributable to this phase — recorded as a new dated addendum in `reports/perf-budgets.md` with the raw CSV path and the full distribution (p50, p90, p99, max, count-over-2.0s).
- TC-2: given a pinned pre-fix reference DB, when the bounded `coverage_membership_timeline_refresh` call chain (`refresh_coverage_snapshot` → `universe_resolver.resolve_with_reasons`) runs once through the unbounded path and once through the bounded/cooperative-yield path, then `admitted`, `excluded_counts`, and the persisted `coverage_snapshot`/`membership_timeline_cache` payload rows are byte-identical between the two runs.
- TC-3: given the existing MemoryError-distinct isolation handler wrapping `coverage_membership_timeline_refresh`, when a MemoryError is injected at this phase (`TRENDORA_FAULT_INJECT_MEMORY_ERROR=coverage_membership_timeline`) after the bound lands, then the handler logs the isolation failure, calls `_release_process_memory()`, omits `"coverage"`/`"membership_timeline"` from `aggregates_refreshed`, and the SAME process keeps serving `GET /api/health` HTTP 200 afterward (no wedge, no restart).
- TC-4: given `scripts/qa/poll_health.py` checked in as one canonical, single-process script, when this iteration's own dev evidence-drill and its J-07 browser-qa test case each run a health-poll measurement, then both artifacts' raw CSVs share the identical column schema (timestamp, http_status, elapsed_s, breach_over_2s, load_avg_1m) and cite the same script path — no ad hoc curl/bash polling loop appears in either write-up.
- TC-5: given the canonical script's host-load column, when a health-poll drill runs during a real ingest job, then every CSV row has a populated (non-null) `load_avg_1m` value alongside its poll timestamp and HTTP status.
- TC-6: given `journey-scripts/J-05.json`'s closing `_notes` entry (currently stating the sentinel window as 1996-01-01..2004-12-31), when it is corrected, then it states the actual shipped constants (2005-03-01..2016-12-31) and J-05's own golden replay still passes unmodified in behavior.
- TC-7: given the duplicate-row pattern (iter-64/d), when the resume/retry call site is inspected and, if fixable in a small isolated change, corrected, then either (a) a fresh `kill -9`-mid-job/restart/resume drill produces exactly one persisted `data_provider_runs` row for that `job_id`, or (b) the cause is written into the ledger as investigated with the exact call site named and the fix explicitly deferred as non-trivial.
- TC-8: given J-01, J-03, J-04, J-05, J-06, J-08, J-09's deterministic goldens, when replayed against this iteration's built tree, then all seven remain `passing`/`already_passing` with fresh, byte-distinct evidence frames (md5-checked) and no journey moves to `failing`.

## NOTES

- If the profiling step in TC-1 finds the remaining hold is a DB read itself rather than a Python-level loop/sort/GC step, bound the READ (e.g. `yield_per`/keyset pagination with a cooperative yield between chunks, mirroring this codebase's existing `yield_per` precedent) rather than forcing a synthetic post-hoc chunk boundary on already-materialized rows — whichever site the live profile actually names governs the fix, not this guess.
- If, after bounding every hold the profile can find, a residual number of breaches remains (TC-1's "0 breaches" target not fully met), report the measured before/after numbers honestly in the dev handoff rather than rounding toward "fixed" — the evaluator, not this spec, decides whether J-07 moves off `partial` (mirrors iter-65's own delegation).
- Owner's 2-second-ceiling policy question (asked 17 times) is orthogonal to this iteration's work: under either reading (long jobs vs. short jobs only), eliminating this phase's breach is a real reliability improvement, not wasted effort.
- Per the priority rubric's rule 5, this iteration carries exactly ONE risky change (bounding a GIL/lock hold in a hot, previously-hand-tuned ingest path) — the poll-script canonicalization, the J-05.json note fix (TC-6), and the iter-64/d investigation (TC-7) are tooling/mechanical/investigative, not a second risky code change.
