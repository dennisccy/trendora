# Goal Iteration 40 — Bound `_missing_data_diagnostic`'s materialization (J-07's last blocker) + checkpoint honesty + tooling fixes

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 40
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — Prior verdict was ESCALATE (iter-39); full depth is mandatory, no exceptions (also matches the dispatch prompt's own binding "full" recommendation).
- **Frontend Present:** no
- **Target journeys:** J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-06, J-08, J-09 (widened to the FULL passing set per the "widen after ESCALATE" cadence — the changed function feeds the shared Coverage payload row that six of these journeys' homes read from)
- **Anti-goal reminders:**
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only against the committed seed / local provider fixtures — no live external network calls or paid data services may be introduced without an explicit goal.md amendment. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills, full-universe rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched only via the project launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those scripts MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env` whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`, `malloc_arena_max`). Never remove, weaken, or bypass these caps: stripping a HOST-GUARD marked block from a launch script is a REGRESSION regardless of test outcomes. The ceilings are a physical constraint of the current host (two instant hardware resets under all-core vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance budget to optimize away. *(critical)*

## GOAL

Bound `_missing_data_diagnostic`'s unbounded whole-result materialization — the one change iter-39's own evaluator named as moving three things at once: J-07's last standing acceptance clause, the most likely cause of the trial-3 wedge, and the reason three live cap trials could never reach the handlers J-07 names — then re-check the wedge once against the fixed code and close three small, already-diagnosed items (checkpoint honesty, a stale doc correction, a merged-QA-headline bug).

## BACKGROUND

iter-39 (ESCALATE, prior verdict) finally proved J-07 step 4's per-horizon `MemoryError` isolation live at the named handler, but the drill's own honest disclosure surfaced two NEW blockers before it could cross: `_missing_data_diagnostic` (`apps/backend/app/engine/data_manager.py:271`) buffers every universe member's `(symbol, date)` rows (~3.3M) into one Python list via SQLAlchemy `_raw_all_rows` before its loop body runs — live on both the ingest finalize path and `GET /api/data`'s serving path — and a 7+ minute process wedge (iter-39/u) whose dying thread was never identified, discovered at a 2650 MB throwaway cap that never actually reached the aggregate-warm handlers because this earlier, larger allocation exhausted memory first. The iter-39 evaluator's next-step recommendation is unambiguous and singular: fix this ONE site with a bounded `yield_per` read (output-identical, grouping loop unchanged) and correct the in-code comment at `:262-274` that currently claims "no unbounded whole-table scan" (true of the query's SCOPE — bounded to the universe — false of its MATERIALIZATION). This is this iteration's one risky code change; three small, already-written-down items ride alongside it (rule 5 — a risky change plus cheap mechanical fixes is exactly what that rule permits, per the iter-36/37 decomposer precedent already logged in this session).

**Lessons applied:**
- iter-39 (first lesson, binding): when a drill can't reach its target, the obstacle is usually a LARGER allocation upstream, not a cap needing one more turn of tuning — three cap trials (3420/2700/2650 MB) all died in `_missing_data_diagnostic` before the aggregate-warm handlers were ever reached. This iteration fixes that upstream allocation directly rather than probing a fourth cap.
- iter-39 (second lesson): `select(...).where(...)` bounded by symbol set is NOT bounded in memory — SQLAlchemy buffers the whole result via `_raw_all_rows` before the loop body runs. The fix must stream (`yield_per`), not merely trust the query's `WHERE` clause.
- iter-34 (first lesson): a saved log EXCERPT is not the log — the wedge re-check drill (if run) must be verified against the live `logs/backend.log` line range, not a trimmed evidence file.
- iter-38 (first lesson): a drill proving a failure mode and a drill comparing two arms are different experiments — the wedge re-check is a single PROVE-or-DIAGNOSE pass, not a cap-tuning comparison; do not widen the cap "so it completes gracefully."
- iter-39 (second entry, second lesson): a deterministic-lane repair must be verified in both directions, and a merged artifact's headline can diverge from its own results-table rows — the `merge_ui_test_results.py` fix below must be proven with a unit test asserting the headline for an all-`BLOCKED` run, not just for the already-fixed per-file `demo_runner.py` output.

## IN SCOPE

### Backend
- [ ] Rewrite `_missing_data_diagnostic`'s second query (`apps/backend/app/engine/data_manager.py:271`, `select(DailyPrice.symbol, DailyPrice.date).where(DailyPrice.symbol.in_(universe))`) to stream via `.yield_per(cfg.research.read_batch_size)` — the SAME config knob every other bounded read in this codebase already uses (`forward_testing.py`, `research.py`) — instead of materializing the whole result. The query is already column-projected (symbol + date only); only the fetch strategy changes. The downstream grouping into `own_dates_by_symbol` and every consumer of it stays byte-identical.
- [ ] Correct the in-code comment at `data_manager.py:262-274` ("no unbounded whole-table scan") to state plainly that the query is bounded by symbol set but was previously materialized whole-result in memory — now streamed — so a future reader cannot repeat iter-39's finding that the comment asserted the opposite of what the code did.
- [ ] Add a fixture-backed equality test proving `_missing_data_diagnostic`'s output (`no_history`/`thin`/`intra_series_gap` lists) is byte-identical before and after the fetch-strategy change, for the same DB state.
- [ ] Re-run the tightened-cap wedge-recurrence drill EXACTLY ONCE, throwaway DB via `scripts/start-backend.sh` (AG-10), at the same cap family iter-39's trial 3 used (~2650 MB) or tighter — never widened "so it completes gracefully" (binding iter-38 lesson). Assert from the live `logs/backend.log` line range (not a trimmed excerpt — binding iter-34 lesson) whether the wedge recurs post-fix. If it does not recur, record that in `reports/perf-budgets.md`. If it does, positively identify the dying thread (thread name/stack, e.g. via a stack dump or targeted logging) rather than attributing it by inference, and record that finding as a new, separate ledger item — do not attempt a second cap trial this iteration.
- [ ] iter-39/w (AG-3): make the post-crash `/data` Run History checkpoint figure honest. Tighten `_checkpoint_run_record`'s effective cadence so it is invoked after every date's completion within `_do_backfill`'s per-date loop (the function's own existing throttle interval still governs whether each call actually writes) — so a `kill -9` at any point leaves the persisted row within one checkpoint interval of the true in-memory progress, never off by an order of magnitude as observed in iter-39 (18/18 in memory, 2/18 persisted). Same `message` field, same `_run_detail()` serializer, no new field, no second endpoint.
- [ ] Correct `reports/perf-budgets.md:4996`'s RETRACTED `backfill_workers` wedge attribution IN PLACE (the fix-pass section already corrects it, but its supersession sentence names only TC-1..TC-4, so a reader of the earlier section alone still gets the withdrawn story — iter-39 evaluator's fifth stated-plainly item).
- [ ] Teach `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py`'s `parse_rows`/`compute_overall` a `BLOCKED` verdict class, mirroring `demo_runner.py`'s already-shipped priority (`FAIL` > `BLOCKED` > `PASS` > `SKIP`/`SKIPPED`) so the merged headline can never read `PASS` or `SKIPPED` for a run whose surviving rows are `BLOCKED` (iter-39/x). The machine gate (`goal_gate.py:89,151`) already blocks achievement on any `BLOCKED` cell — this fixes the LLM-readable headline only, no gate-logic change.

### Frontend
None — the checkpoint-honesty fix is a backend cadence/timing change to an already-persisted field; the `/data` Run History panel already renders that field unchanged.

### New user-facing capability
None — this iteration is a correctness/hardening fix on already-shipped J-07/J-04 behavior plus two tooling-only corrections; no new user-facing capability.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
No visible product surface change. A `kill -9`'d backfill's post-restart Run History row will show progress closer to what was actually done at kill time (same field, more timely writes) — a correctness improvement to an existing display, not a new one.

### Blueprint conformance
- J-07 (the fix + wedge re-check): global readiness badge (top bar) + `/backtest` — existing "J-07 — Heavy aggregates never take the service down" row, unchanged home. The fixed function also serves the Coverage payload row (`GET /api/data`) — existing home, unchanged.
- iter-39/w (checkpoint honesty): `/data` Job history & per-date exclusion reasons row — existing home, unchanged.
- `perf-budgets.md` correction and the `merge_ui_test_results.py` fix touch only already-registered Data Contract rows' Notes columns (Page performance budgets) or QA-tooling artifacts (matching the iter-18/23/33 precedent that a test artifact is not a Data Contract row) — no computing module or serving endpoint changes.

### Data-contract additions
None. This iteration adds no new displayed value; the touched rows (Coverage payload, Job history & per-date exclusion reasons, Page performance budgets) keep their existing single computing module and single serving endpoint. `blueprint.md` gets an additive "iter-40 update" narrative paragraph only — no Information Architecture or Data Contract table change.

## OUT OF SCOPE

- **iter-39/v's ~11%-under-report display itself beyond the checkpoint-cadence fix** — if per-date checkpointing alone does not fully close the honesty gap (e.g. the job completes faster than one checkpoint interval even at per-date granularity), relabeling the figure "last saved checkpoint" is the documented fallback (iter-39 evaluator's next-step item 2) but is NOT independently in scope this iteration unless the cadence fix proves insufficient — avoid a second, unbudgeted UI-copy change for a problem the cadence fix may already solve.
- **iter-33/g** — Regime Lab's cold `view=pooled` background dispatch — deferred a 5th time. Rule 5: this iteration's one risky code change (the diagnostic-fetch fix) plus small mechanical items already fill the budget; a second structural code change makes a joint failure undiagnosable.
- **iter-29/b + `warmup.py:194`** badge wording after a permanently failed warm-up — carried, unmade for 10 iterations, not in the iter-39 evaluator's numbered queue for this iteration.
- **iter-31/e, iter-32/f (WATCH only), iter-35/k, iter-36/n, iter-37/o, iter-37/q** — carried minor findings, unaffected by this iteration's diff.
- **iter-34/j** — the `GET /api/health` ≤0.1s budget disposition (6 consecutive misses under the bounded background-compute window). OWNER decision (ratify honest-WARN / rescope / commission a cached-snapshot fix) — not agent-actionable.
- **iter-33/i** — whether `start-frontend.sh` joins `HOST_GUARD_MARKER_FILES`. OWNER decision.
- J-07's `[NEW]` `demo.sh --session-live` walkthrough (unrecorded for 9 iterations) and the three-way J-01/J-03/J-05 identical-screenshot collision — capture-only ride-alongs, never an iteration's own goal (rule 7).
- Any change to `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, `ensure_historical_forward_aggregates_dispatched` — byte-frozen (binding "Do not redo").
- Re-running J-07 steps 1, 2, 3, or the already-closed step-4 per-horizon isolation proof itself — all CLOSED with this-iteration-quality evidence at iter-39 (binding "Do not redo"); this iteration's drill re-check is a NEW post-fix wedge check, not a repeat of the closed proof, and does not resume open-ended cap-tuning.
- The env-toggle guard, root-logger config, `read_pool()` in-situ measurement, `_compute_one_isolated` worker-thread `MemoryError` isolation — settled at iter-39, do not re-open (binding "Do not redo").

## DEFINITION OF DONE

- [ ] `_missing_data_diagnostic`'s per-symbol date scan streams via `yield_per` instead of materializing the whole result; the in-code comment at `:262-274` accurately describes bounded-scope-vs-streamed-materialization.
- [ ] A fixture-backed equality test proves byte-identical diagnostic output pre/post fix.
- [ ] The tightened-cap wedge-recurrence drill has run exactly once post-fix, throwaway DB via `scripts/start-backend.sh`, with its outcome (wedge did or did not recur; if it did, the dying thread positively identified) recorded from the live log, not an excerpt.
- [ ] The post-crash `/data` Run History checkpoint figure is within one checkpoint interval of true in-memory progress at kill time for a fresh live `kill -9` test.
- [ ] `reports/perf-budgets.md:4996`'s retracted `backfill_workers` attribution is corrected in place.
- [ ] `merge_ui_test_results.py` recognizes a `BLOCKED` verdict class; an all-`BLOCKED` merged run headlines `BLOCKED` (never `PASS`/`SKIPPED`), and `FAIL` still wins over `BLOCKED` when both are present — proven by a unit test.
- [ ] J-07 re-scored by the evaluator against all four acceptance clauses (single-source consistency, byte-identical correctness, honest-status/no-unbounded-materialization, walkthrough) using this iteration's live evidence.
- [ ] Required-still-passing journeys (J-01, J-03, J-04, J-05, J-06, J-08, J-09) remain green via deterministic replay + LLM fallback.
- [ ] No anti-goal violation introduced (AG-3/AG-8/AG-9/AG-10 respected: drill launched only via `scripts/start-backend.sh`, offline/local throwaway DB, host-guard caps intact and unweakened).
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-40-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-07 (the fixed diagnostic path exercised via `GET /api/data`'s coverage compute + the wedge re-check drill's `/api/health`/`/api/backtest` spot-checks), plus standard replay/spot-check for J-01, J-03, J-04, J-05, J-06, J-08, J-09.
- Unit/integration: `_missing_data_diagnostic` byte-identity fixture test; `_checkpoint_run_record` cadence test (per-date invocation, throttle interval still honored); `merge_ui_test_results.py` `BLOCKED`-headline unit tests; existing `data_manager.py`/`test_data_manager.py` suites re-run for regression.
- Error cases: a `MemoryError` raised inside the aggregate-warm loop (downstream of the fixed diagnostic call) must still be caught and isolated exactly as iter-39 proved (job continues/finalizes honestly, never crashes the process); a merged results file with a mix of `FAIL` and `BLOCKED` rows must headline `FAIL`, never `BLOCKED` or `PASS`.

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps to at least one concrete scenario line, numbered sequentially:

- TC-1: given the current live DB's `daily_prices` table, when `_missing_data_diagnostic` runs via `GET /api/data`'s coverage compute both before and after the fetch-strategy change, then its `no_history`/`thin`/`intra_series_gap` output lists are byte-identical for the same DB state (fixture-backed equality test).
- TC-2: given a throwaway backend process launched via `scripts/start-backend.sh` with a tightened `server.memory_cap_mb` (the same cap family that previously died inside `_missing_data_diagnostic`), when the SAME ingest/coverage-compute path runs post-fix, then `logs/backend.log` shows no traceback naming `_missing_data_diagnostic` / `data_manager.py:271` / `_raw_all_rows` for that call.
- TC-3: given the tightened-cap drill re-run once at ~2650 MB or tighter (not widened to make both arms complete), when the aggregate-warm stage is reached and induces pressure, then EITHER (a) the SAME process's `/api/health` answers every 1 Hz poll HTTP 200 for the drill's full duration with no gap exceeding the existing budget's tolerance, and no unresponsive window is observed in `logs/backend.log`'s live line range — the wedge does not recur — OR (b) an unresponsive window recurs and the drill's evidence file names the specific dying thread (by name/stack), not an inferred attribution.
- TC-4: given a live backend and a backfill job covering N dates, when the job is `kill -9`'d after M < N dates have completed in memory (M tracked independently, e.g. a log line at each date's completion) and the backend is restarted, then the restarted backend's `/data` Run History row for that job shows a checkpointed `dates_done` value within one checkpoint interval's worth of M (not stuck at an early value from long before the kill).
- TC-5: given `reports/perf-budgets.md`'s earlier section (around line 4996) previously attributed the trial-3 wedge to `backfill_workers`, when this iteration's edit is applied, then that earlier section's own text states the retraction in place (not solely in a later section) and no unqualified sentence in the file still names `backfill_workers` as the wedge's cause.
- TC-6: given two input UI-test-results files whose surviving rows are ALL `BLOCKED` (e.g. J-01 and J-03 both `BLOCKED`), when `merge_ui_test_results.merge()` runs, then the merged file's `**Browser QA Verdict:**` line reads `BLOCKED`.
- TC-7: given a merged set of rows containing at least one `FAIL` and at least one `BLOCKED`, when `merge_ui_test_results.merge()` runs, then the merged headline reads `FAIL` (FAIL still wins over BLOCKED).
- TC-8: given the fixed `_missing_data_diagnostic` and a live full-horizon aggregate warm under the COMMITTED `memory_cap_mb` (6144 MB, non-drill conditions), when the warm completes, then all previously-closed J-07 step 1/2/3 evidence (per-horizon isolation, 1 Hz health-poll coverage, VmPeak margin) is unaffected — re-confirmed via the existing regression suite, not re-run live (binding "Do not redo").
- TC-9: given J-01/J-03/J-04/J-05/J-06/J-08/J-09 already `passing`, when the deterministic replay lane runs against this iteration's build, then each replays PASS (or falls back cleanly to the LLM lane per the iter-38/39 `BLOCKED`-vs-`FAIL` fix) with no regressed verdict.

## NOTES

- This iteration targets the SINGLE change the iter-39 evaluator identified as moving three things at once (J-07's last acceptance clause, the trial-3 wedge's most likely cause, and the reason cap-tuning could never reach its target handlers) — do not expand scope to the deferred structural items (iter-33/g, iter-29/b) alongside it; rule 5 already has one risky code change in this iteration's budget.
- The wedge re-check drill is diagnostic, not a re-proof of anything already closed: if the wedge does NOT recur, that is a strong (not certain) signal the fixed allocation WAS the cause, and it should be recorded as such rather than declared certain; if it DOES recur, the correct response is thread identification, not a second cap trial in this same iteration (avoid iter-39's own three-trials-before-diagnosing pattern, applied here in miniature).
- Owner items (iter-34/j health budget, iter-33/i start-frontend.sh host-guard membership) remain open and unresolved by any agent path; both are explicitly named in OUT OF SCOPE and should be settled before any GOAL_ACHIEVED attempt, per four prior evaluators.
- No new assumptions-ledger entry: this iteration's scoping choices are direct applications of the iter-39 evaluator's own explicit, numbered next-step recommendation, not a fresh interpretation of an ambiguous goal.
