# Goal Iteration 65 — Find and bound J-07's remaining GIL/lock hold inside `factor_lab_all_warm`

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 65
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

Find the specific still-uninterruptible call site inside `factor_lab_all_warm` (research.py's `compute_factor_lab_all`) that is causing `GET /api/health` polls to breach their 2.0s ceiling — and the first-ever unanswered poll — during ingest finalize, and bound it the same proven way iter-52 bounded the sort and the GC pause, so the drill reruns clean.

## BACKGROUND

The evaluator's depth recommendation for iteration 65 is **lean**, and it is binding: the prior verdict (iter-64) was CONTINUE, not ESCALATE/REGRESSION; iter-64's own `coherence.md` is COHERENCE-PASS (0 blocking, 2 advisory); "Consecutive lean iterations dispatched: 1" is nowhere near the 6-iteration cadence; and this iteration lands no new user-visible capability — it bounds an already-existing internal compute path, not a brand-new full-stack journey (`apps/frontend/*` is untouched). No full trigger holds; needing tests is never a valid trigger, and this scope is a nameable blast radius (`apps/backend/app/engine/research.py`'s `factor_lab_all_warm` call chain plus its equality tests).

iter-64's own next-step order item (1) states this is "the only agent path left to close J-07": `factor_lab_all_warm` now carries 58 of 59 health-poll ceiling breaches and the session's first-ever unanswered poll, reproduced within 11% across two independent live drills (iter-63: 53/983; iter-64: 59/930). iter-52 already bounded the two GIL-holders its own stall profile found at the time — `sorted()` (via `_cooperative_sorted`, research.py:143-156) and the cyclic GC (via `_cyclic_gc_paused`, research.py:159-204) — and both fixes are proven byte-identical by fixture equality tests. That those fixes are real and still in place (confirmed: `_SORT_YIELD_CHUNK`/`_cooperative_sorted`/`_cyclic_gc_paused` unchanged since iter-52) yet the breach count is unchanged/worse means a **third, still-unbounded** hold exists somewhere in the same call chain (`compute_factor_lab_all` → `_combination_observations` / `_factor_decile_observations` / `_all_factor_observations_by_horizon`, or the initiating DB read) — iter-52's own docstring (data_manager.py:4204-4206) names the honest limit up front: "this closes the CONNECTION-LEVEL non-answer; it is not guaranteed to fully close every poll's ≤2s latency ceiling." This iteration re-runs iter-52's own method — interrupt-driven stack sampling of live stalls >0.30s during a real `factor_lab_all_warm` run — to find and name that third hold, then bounds it with the SAME established chunk+yield pattern, preserving byte-identical output (per J-07's own Correctness acceptance clause).

Lesson applied (iter-58, iter-63): recompute any latency claim from the raw per-poll log/CSV, never trust a prose summary — this iteration's own drill output must be recounted the same way before any breach-count claim goes into `reports/perf-budgets.md`. Lesson applied (iter-60/61): a fix to a file the running executor sources at startup cannot self-verify in the same run that edits it — this does not apply to `research.py`/`data_manager.py` (loaded fresh by each spawned backend process, not sourced by the goal-mode shell executor), so this iteration's own dev-pass live drill DOES self-verify. Per priority rubric rule 6, this iteration does not touch either OWNER-gated item (the 2-second-ceiling policy question; the `browser-qa-phase.sh` ordering fix) — both stay parked in NOTES.

Cost discipline: rather than launching a second live ingest, this iteration's health-poll drill piggybacks on the SAME live backfill the developer runs to verify the fix (a single-date backfill still triggers the full, history-wide `factor_lab_all_warm` recompute, per data_manager.py:4599-4634) — matching the pattern iter-64's own decomposer used, and avoiding a second ~15-20 minute AG-10-gated job while the owner's cost-sanction question is still open.

Also carried in from iter-64's Active blockers, as small dev-actionable items riding alongside the primary fix (never the goal themselves): (a) confirm `CHAIN_BACKEND_READY_WAIT_S`'s 60→90 bump (`scripts/automation/lib/common.sh:1434`, `scripts/automation/lib/replay-lane.sh:341`) actually fired, from this iteration's own engine log (iter-60/61 lesson: verify a shell-lib fix from the live log, not the diff); (b) root-cause `/scanner-runs`'s one-off contained error boundary (iter-64/a, `reports/qa/goal-ops-hardening-iter-64-evidence/J-05-verify.png`) — write the answer down even if it does not reproduce this round (iter-64's own next-step item 2).

## IN SCOPE

### Backend
- [ ] Re-run iter-52's interrupt-driven stall-profiling method (sample the live process's stack whenever a `GET /api/health` handler thread is blocked >0.30s) during a real `factor_lab_all_warm` phase, to name the specific call site(s) inside `compute_factor_lab_all`'s chain (research.py: `_combination_observations`, `_factor_decile_observations`, `_all_factor_observations_by_horizon`, or the initiating DB read/JSON-serialization step) still holding the GIL/a lock long enough to breach the 2.0s poll ceiling post iter-52's sort/GC fixes.
- [ ] Bound whatever call site the profile names, using the SAME established pattern already proven in this file (`_cooperative_sorted`'s chunk-then-`heapq.merge` shape, or an equivalent chunk+yield bound for a DB read/serialization step) — no new aggregation algorithm, no change to what is computed, only when the GIL is handed off.
- [ ] Add/extend a fixture-backed equality test proving the bounded call site returns byte-identical output to the pre-fix computation (all configured horizons, with and without `as_of`) — mirroring the existing `test_factor_decile_observations_is_byte_identical_with_the_trim_sort_chunked`-style tests in `test_research_streaming.py`.
- [ ] Re-run the same 1 Hz `GET /api/health` poll drill throughout a real ingest finalize tail (piggybacked on the dev-pass live backfill, not a second job), recount it from the raw per-poll log (iter-58/63 lesson — no hand-picked segment boundaries), and publish a new dated addendum in `reports/perf-budgets.md` with the raw file path, total polls, over-ceiling count, unanswered-poll count, and the phase-by-phase timing breakdown.
- [ ] Confirm from this iteration's own `logs/backend.log` / engine log that `CHAIN_BACKEND_READY_WAIT_S` used a 90-second (not 60-second) window during this round's own backend-readiness gating; record the confirming log line/timestamp in the dev handoff.
- [ ] Root-cause `/scanner-runs`'s iter-64 contained-error-boundary render (`J-05-verify.png`): inspect `logs/backend.log` around the capture's timestamp for the causing exception/traceback; if it reproduces during this round's own J-05 replay, capture the traceback directly. Write the finding into the ledger either way (a named cause, or "reproduced attempt made, did not recur, no traceback found" — never silence).

### Frontend
- None. No `apps/frontend/*` file is touched this iteration.

### New user-facing capability
None — this iteration bounds an internal compute path so an already-shipped guarantee (the app stays responsive during a heavy background job) holds under the phase that currently breaches it. No new page, control, or displayed field.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
No visible change to any page. The global readiness badge (top bar, every page) and `/backtest`'s per-horizon evidence keep answering the same way they always have — this iteration's success criterion is that they answer FASTER/more reliably during `factor_lab_all_warm`, not that they look or behave differently.

### Blueprint conformance
No new page/route/nav entry. This work lives entirely under the blueprint's existing "J-07 — Heavy aggregates never take the service down" home (global readiness badge + `/backtest`, `runs/goal-session-ops-hardening/state/blueprint.md:412`) and reads/serves the already-registered "Membership timeline / research hot-key caches" Data Contract row (`blueprint.md` Data Contract table, `event_study_cache`/factor-lab hot keys) unchanged — no edit to `blueprint.md` this iteration.

### Data-contract additions
None. `compute_factor_lab_all`'s output, computing module (`app.engine.research`), and serving path (`event_study_cache` warmed at ingest finalize, served via the existing research endpoints) are unchanged — the equality test's whole purpose is to prove the bound introduces zero output difference. No new field, table, or endpoint.

## OUT OF SCOPE

- The owner's 16-times-asked 2-second-ceiling policy question (long jobs vs. short jobs only) — human-owned, stays parked.
- The `scripts/automation/browser-qa-phase.sh` line-286-before-272 ordering fix — owner sign-off still pending.
- The cost-sanction decision on the replay lane's real ~15-20 minute ingest every round — owner-gated; this iteration's drill piggybacks on the existing job rather than adding a second one, but does not change the policy.
- A second, separately-launched live ingest job purely for a control/attribution re-run — the 1→53→59 breach-count reproduction is already settled (iter-64's "Do not redo"); this iteration is a FIX pass, not another measurement pass.
- The J-05 walkthrough capture (unrecorded for 6 rounds) — rides along only if a showcase/demo lane happens to run; not this iteration's own goal, and not expected at lean depth.
- iter-33/g (the Regime Lab) and the other long-carried items in iteration-state's history (iter-29/b, iter-31/e, iter-32/f, iter-35/k, iter-36/n, iter-37/o, iter-37/q, iter-39/u, iter-46/az, iter-46/ba, iter-47/bd, iter-47/bf, iter-47/bi, iter-48/bj, iter-57/f, iter-57/l, iter-59/g, iter-59/h, iter-59/k, iter-62/e, iter-62/f, iter-63/a, iter-63/b, iter-63/d, iter-63/f) — none of these bear on J-07's remaining gap; left untouched.

## DEFINITION OF DONE

- [ ] Target journey J-07 re-verified via the health-poll drill and browser-qa
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-06, J-08, J-09 remain green (deterministic replay + LLM fallback)
- [ ] No anti-goal violation introduced (AG-3 byte-identity, AG-8 resilience, AG-9 offline-deterministic ingest, AG-10 host caps all hold)
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-65-dev.md`

## TESTING REQUIREMENTS

- Browser: J-07 (steps 1-2, the crash-free warm + healthy `/api/health` sequence); regression replay/LLM fallback for J-01, J-03, J-04, J-05, J-06, J-08, J-09
- Unit/integration: a fixture-backed equality test for whatever call site inside `compute_factor_lab_all`'s chain gets bounded this iteration (all configured horizons, with and without `as_of`); the existing `_cooperative_sorted`/`_cyclic_gc_paused` tests must keep passing unmodified (they pin an already-proven contract)
- Error cases: the bounded call site must still degrade honestly under an injected `MemoryError` (matching `factor_lab_all_cached`'s existing internal catch — no unhandled exception escapes the finalize-tail phase; AG-8)

Test-first contract:

- TC-1: given a live backend process running a real ingest finalize tail (any single-date backfill triggers the full history-wide `factor_lab_all_warm` recompute), when `GET /api/health` is polled once per second throughout the whole finalize tail, then every poll answers HTTP 200 within 2.0s (0 breaches attributable to `factor_lab_all_warm`) and 0 polls go unanswered — recorded as a new dated addendum in `reports/perf-budgets.md` with the raw per-poll log path and the reconciled total/breach/unanswered counts.
- TC-2: given the SAME fixture DB used by iter-52's equality tests, when the bounded call site is invoked once through the plain (unchunked) path and once through the chunked path (e.g. via `monkeypatch.setattr` forcing a small chunk size, matching `test_factor_decile_observations_is_byte_identical_with_the_trim_sort_chunked`'s pattern), then `json.dumps(result, sort_keys=True, default=str)` is byte-identical between the two runs, for all configured horizons and both with and without `as_of`.
- TC-3: given a `MemoryError` injected at the bounded call site (matching the project's existing `_FAULT_INJECT_SITES` convention), when `factor_lab_all_warm` runs, then `factor_lab_all_cached` returns its existing honest degraded payload (`factors_status: "unavailable"` or a per-`(factor, horizon)` `by_horizon[].status: "unavailable"`), the finalize tail's `except MemoryError` branch logs the isolation failure and calls `_release_process_memory()`, and the SAME backend process keeps serving `/api/health` afterward (no wedge, no restart).
- TC-4: given this iteration's own goal-mode engine log, when it is inspected for the backend-readiness-wait constant, then it shows a 90-second (not 60-second) window was used for this round's readiness gating.
- TC-5: given `/scanner-runs` immediately after this iteration's own J-05 replay backfill, when the page is opened via browser-qa, then either (a) it renders the stored leaderboard successfully with no error boundary, or (b) if the contained error boundary reappears, `logs/backend.log` around that timestamp is inspected and the causing exception/traceback (or its confirmed absence) is written into the ledger.
- TC-6: given J-01, J-03, J-04, J-05, J-06, J-08, J-09's deterministic goldens, when replayed against this iteration's built tree, then all seven remain `passing` with fresh, byte-distinct evidence frames (md5-checked) and no journey moves to `failing`.

## NOTES

- If the profiling step in TC-1 finds that the remaining hold is the initiating DB read itself (a single large `session.execute(...)` materializing ~1.27M rows per `(factor, horizon)` entry, 55 entries) rather than a Python-level sort/GC step, the bound should chunk the READ (e.g. `yield_per`/keyset pagination with a `time.sleep(0)` between chunks, mirroring the project's existing `yield_per` precedent used elsewhere in `data_manager.py`) rather than forcing a synthetic post-hoc chunk boundary on already-materialized rows — whichever site the live profile actually names governs the fix, not this guess.
- If, after bounding every hold the profile can find, a residual number of breaches remains (i.e., TC-1's "0 breaches" target is not fully met), report the measured before/after numbers honestly in the dev handoff rather than rounding toward "fixed" — the evaluator, not this spec, decides whether J-07 moves off `partial`.
- Owner's 2-second-ceiling policy question (asked 16 times) is orthogonal to this iteration's work: even under the strictest reading (the promise applies to long jobs), eliminating `factor_lab_all_warm`'s breaches is a necessary step toward closing J-07; under the relaxed reading (short jobs only), this work is still a real reliability improvement, not wasted effort.
- Per the priority rubric's rule 5, this iteration deliberately carries only ONE risky change (bounding a hot, previously-hand-tuned compute path in `research.py`) — the `/scanner-runs` root-cause item (TC-5) is investigative/read-only (log inspection, or capturing a traceback if it reproduces), not a second risky code change, so it rides alongside without violating "never bundle two risky journeys."
