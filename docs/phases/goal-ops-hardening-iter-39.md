# Goal Iteration 39 — J-07 step-4 pressure drill (right stage) + replay-lane BLOCKED fix + J-04/J-05 live re-verification

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 39
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — Prior verdict was ESCALATE (iter-38); full depth is mandatory, no exceptions.
- **Frontend Present:** no
- **Target journeys:** J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-06, J-08, J-09 (widened to the FULL passing set per the "widen after ESCALATE" cadence — J-04 and J-05 additionally get a genuine live kill/restart pass this iteration, not mere replay)
- **Anti-goal reminders:**
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only against the committed seed / local provider fixtures — no live external network calls or paid data services may be introduced without an explicit goal.md amendment. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills, full-universe rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched only via the project launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those scripts MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env` whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`, `malloc_arena_max`). Never remove, weaken, or bypass these caps: stripping a HOST-GUARD marked block from a launch script is a REGRESSION regardless of test outcomes. The ceilings are a physical constraint of the current host (two instant hardware resets under all-core vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance budget to optimize away. *(critical)*

## GOAL

Close J-07's last unrun step — an induced-pressure drill that actually raises `MemoryError` inside the aggregate-warm stage (not the bar-cache prefill stage iter-38's attempt hit) while the same process keeps serving health and cached reads — and, in the same full-depth pass, fix the deterministic replay lane so a downed backend can never again masquerade as regressions, then close two overdue live re-verifications (J-04's boot/crash/restart status truth, J-05's cold-boot coverage-from-storage).

## BACKGROUND

iter-38 (ESCALATE, prior verdict) closed J-07 steps 1 and 3 with real, this-iteration evidence but step 4's drill raised its `MemoryError` in the wrong stage (`_do_backfill`'s prefill, `RuntimeError: can't start new thread` at the `ulimit -v` cap, `dates_done: 0`) because the cap (3072 MB) was too tight to let prefill finish — so the per-item isolation handler the acceptance clause actually tests (`data_manager.py` ~3401-3407/3435-3440, inside the aggregate-warm loop) never fired, and the concurrent `/api/health` poll had a `MAX_SECONDS` bound that left a ~39s blind spot. This is the single remaining item in J-07's four-step acceptance; both this session's evaluator and audit lane confirm steps 1-3 are DONE and byte-frozen. Bundled in per rule 5's established reading (iter-37 decomposer entry: rule 5 covers CODE changes, not verification/measurement passes) — a repair to the deterministic replay lane (iter-38/t: it reported 6 FALSE regressions against a backend that was simply down, twice now) and three small, already-diagnosed mechanical fixes (env-toggle truthy guard, root-logger gap, `read_pool()` in-situ re-measurement). Also folds in the two live re-verifications the evaluator named as blocking any future achievement run: J-04's real kill/restart test (never run this session with a genuinely live backend — always declined or environment-artifacted) and J-05 step 3 (cold-boot coverage-from-storage), both skipped for the identical "could not restart services" reason across prior iterations.

**Lessons applied:**
- iter-34: the drill must target the SPECIFIC stage whose except-clause the acceptance text names; a cap too tight kills an earlier stage (here: prefill) before the target stage (the aggregate warm) is ever reached. Re-tune upward from 3072 MB, not down.
- iter-37/iter-38: a drill on a conditional/staged code path must ASSERT which stage actually aborted (log line or direct read), never infer it from "a `MemoryError` fired somewhere."
- iter-38 (first lesson): this iteration is a pure PROVE-the-failure-mode drill, not a two-arm COMPARE — do not widen the cap "so it completes gracefully"; that is precisely what silently defeated last iteration's drill.
- iter-38 (second lesson) + iter-36: the replay-lane fix directly implements "probe `/api/health` first, report BLOCKED not FAIL"; any backend-down/restart step in this iteration's browser-qa plan is scheduled LAST.

## IN SCOPE

### Backend
- [ ] Run ONE throwaway-DB induced-pressure drill via `scripts/start-backend.sh` (AG-10) with `server.memory_cap_mb` re-tuned (search upward from the 3072 MB that killed prefill) so bar-cache prefill completes but a subsequent per-item aggregate-warm sub-step (forward-aggregates or drawdown-expectations — the largest per-symbol/per-horizon computations in `_refresh_ingest_aggregates`) raises `MemoryError`, caught by the existing per-item isolation handler; seed the throwaway DB with `setup_status="Avoid"` (iter-34 lesson, avoids `research_hot_keys`' generic non-`MemoryError`-specific except firing first) and log/assert which stage actually aborted.
- [ ] Remove the drill's health-poll script's `MAX_SECONDS` bound so the 1 Hz `GET /api/health` poll runs for the whole job, not a fixed wall-clock window (closes audit B2's ~39s blind spot).
- [ ] During the same drill, assert one previously-warmed `GET /api/backtest?as_of=<a date cached before the drill started>` read returns HTTP 200 both during and immediately after the abort.
- [ ] Fix `incredible_auto_dev/scripts/automation/lib/demo_runner.py`'s `run_verify`: probe `GET /api/health` once before replaying any journey in the run; if it does not answer 200, write every journey's verdict as a new `BLOCKED` class (never `FAIL`), and make `compute_regression_verdict` (and the reconciliation footer the goal-evaluator reads) treat `BLOCKED` distinctly from a real FAIL/regression signal. Also refresh this session's stale golden selectors and fix the reconciliation footer to list every overturned journey (iter-38 under-reported by omitting J-05 and J-04).
- [ ] Guard `TRENDORA_FORCE_LEGACY_BAR_CACHE` (`data_manager.py:3123`, currently `if not os.environ.get(...)`) with an explicit truthy check (`in ("1", "true", "yes")`) so `=0` no longer silently ENABLES legacy mode; add the 2-line unit test naming one truthy and one falsy value (audit T3/B5).
- [ ] Configure a root-logger handler/level for `apps/backend` (currently none — uvicorn's last-resort handler only surfaces WARNING+, confirmed live) so routine liveness logging no longer needs to masquerade as `.warning`; downgrade the J-07 finalize-tail `cache_ctx` liveness line (`data_manager.py:3361`) from `.warning` to `.info` once it is confirmed to still reach `logs/backend.log`.
- [ ] Re-measure `read_pool()`'s wall-clock cost in situ during a real multi-date (K>=3) backfill (not the existing micro-benchmark-times-call-count projection) and record the measured figure in `reports/perf-budgets.md` alongside the existing projected one (audit B3/TC-10).

### Frontend
None — no frontend code change. J-04's live restart verification and J-05's cold-boot verification read the EXISTING rendered `/data` Run History panel, Coverage payload panel, and global readiness badge, unchanged this iteration.

### New user-facing capability
None — this iteration closes verification/hardening gaps on already-shipped J-07/J-04/J-05 behavior plus infrastructure repair; no new user-facing capability.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
No visible product surface change. This iteration is verification + backend hardening (a memory-pressure isolation proof in the correct stage, a deterministic-replay-lane repair, an env-toggle guard, a logging fix, and two overdue live re-verifications) on already-shipped behavior.

### Blueprint conformance
- J-07 (drill): global readiness badge (top bar) + `/backtest` — existing "J-07 — Heavy aggregates never take the service down" row, unchanged home.
- J-04 (live restart): global readiness badge + interrupted-job state on `/data` — existing "J-04" row, unchanged home.
- J-05 step 3 (cold-boot coverage-from-storage): `/data` Coverage payload panel — existing "J-05" row, unchanged home.
- The replay-lane fix, env-toggle guard, root-logger fix, and `read_pool()` re-measurement touch only already-registered Data Contract rows' Notes columns (Job history / Backend readiness / Coverage payload / Page performance budgets) — no computing module or serving endpoint changes.

### Data-contract additions
None. This iteration adds no new displayed value; every touched row (Job history & per-date exclusion reasons, Backend readiness / boot phase, Coverage payload, Page performance budgets) keeps its existing single computing module and single serving endpoint. `blueprint.md` gets an additive "iter-39 update" narrative paragraph only — no Information Architecture or Data Contract table change.

## OUT OF SCOPE

- **iter-33/g** — Regime Lab's cold `view=pooled` background dispatch + diagnosing the HTTP-200-with-"Internal Server Error"-body — deferred a 4th time. Rule 5: this iteration's one risky action (the memory-pressure drill) plus small mechanical fixes already fill the budget; a second structural code change makes a joint failure undiagnosable.
- **iter-29/d** — the last unbounded whole-table `daily_prices` load (`data_manager.py:3098` → `prices.py:131-152`, no `WHERE` clause). Real and still open, but NOT in the iter-38 evaluator's numbered next-step queue for this iteration, and adding it would be a second risky structural code change alongside the drill (rule 5). Next candidate once J-07 closes.
- **iter-34/j** — the `GET /api/health` ≤0.1s budget disposition (5 consecutive misses under the bounded background-compute window). OWNER decision (ratify honest-WARN / rescope / commission a cached-snapshot fix) — not agent-actionable.
- **iter-33/i** — whether `start-frontend.sh` joins `HOST_GUARD_MARKER_FILES`. OWNER decision.
- J-07's `[NEW]` `demo.sh --session-live` walkthrough (unrecorded for 8 iterations) and the J-01/J-03/J-05 identical-screenshot collision — capture-only ride-alongs, never an iteration's own goal (rule 7).
- Any change to `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, `ensure_historical_forward_aggregates_dispatched` — byte-frozen (binding "Do not redo").
- Re-running the two-arm live-cache-vs-fallback VmPeak comparison, or re-running J-07 steps 1/3 — both already closed with this-iteration-quality evidence this session (binding "Do not redo").

## DEFINITION OF DONE

- [ ] J-07 passes via browser-qa/audit: the induced-pressure drill raises `MemoryError` inside the aggregate-warm stage (not prefill), with the same process's `GET /api/health` and one previously-cached `GET /api/backtest` read both HTTP 200 during and after the abort, and the health poll covers the whole job (no `MAX_SECONDS` gap).
- [ ] Required-still-passing journeys (J-01, J-03, J-04, J-05, J-06, J-08, J-09) remain green; J-04 and J-05 step 3 are confirmed via a genuine live kill/restart pass, not replay alone.
- [ ] No anti-goal violation introduced (AG-8/AG-9/AG-10 respected: drill launched only via `scripts/start-backend.sh`, offline/local throwaway DB, host-guard caps intact and unweakened).
- [ ] Unit tests pass; no regressions (including the new env-toggle test and any updated `demo_runner.py` self-tests).
- [ ] The deterministic replay lane reports `BLOCKED`, never `FAIL`, when the backend is unreachable, and its reconciliation footer lists every overturned journey.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-39-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-07 (drill evidence + a browser-qa spot-check of `/api/health` and a cached `/api/backtest` read during the drill window), J-04 (live kill/restart, scheduled LAST in the plan per the binding iter-36 lesson), J-05 step 3 (cold-boot coverage-from-storage, folded into the same restart cycle), plus standard replay/spot-check for J-01, J-03, J-06, J-08, J-09.
- Unit/integration: `TRENDORA_FORCE_LEGACY_BAR_CACHE` truthy/falsy guard test; `demo_runner.py` `BLOCKED`-verdict + reconciliation-footer tests; a check that an `.info`-level liveness log line reaches `logs/backend.log`; existing `data_manager.py`/`forward_testing.py` suites re-run for regression.
- Error cases: a `MemoryError` raised inside the aggregate-warm loop must be caught and isolated (job continues/finalizes honestly, never crashes the process); a downed backend must never produce a `FAIL` verdict from the replay lane; `TRENDORA_FORCE_LEGACY_BAR_CACHE` unset or empty must NOT force legacy mode.

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps to at least one concrete scenario line, numbered sequentially:

- TC-1: given a throwaway backend process launched via `scripts/start-backend.sh` with `server.memory_cap_mb` re-tuned above 3072 MB so bar-cache prefill completes, when a real backfill's ingest-finalize aggregate warm runs, then the per-item `MemoryError` isolation handler inside the aggregate-warm loop (`data_manager.py` ~3401-3407/3435-3440) catches the exception — not `_do_backfill`'s prefill stage — confirmed by a direct log/read of which stage aborted.
- TC-2: given the same drill in progress, when the 1 Hz `GET /api/health` poll runs with its `MAX_SECONDS` bound removed, then every poll from job start to job completion returns HTTP 200 with no gap in coverage.
- TC-3: given a date already aggregate-cached before the drill started, when `GET /api/backtest?as_of=<that date>` is requested during and immediately after the `MemoryError` abort, then it returns HTTP 200 serving the previously-cached payload (not a 500, not a hang).
- TC-4: given the drilled process is still alive after the abort, when a follow-up `GET /api/health` request is sent, then it answers without any restart of the process (no wedge, no deadlock).
- TC-5: given the backend is NOT running, when `demo_runner.py --mode verify` is invoked for a set of journeys, then every journey in that run is written with verdict `BLOCKED` (not `FAIL`) and the merged results state the backend was unreachable.
- TC-6: given the backend IS running and a journey's stored golden script has a stale selector, when `demo_runner.py --mode verify` replays it, then the result is an ordinary `FAIL` distinct from `BLOCKED` (the health probe passed, so this is a genuine replay failure).
- TC-7: given at least two journeys are overturned by the LLM browser-qa lane after a replay run, when the reconciliation footer is rendered, then it names every overturned journey, not a subset.
- TC-8: given the live dev-DB backend is running with a checkpointed in-progress or completed backfill, when the coordinator authorizes `kill -9` on the process and it is restarted, then the restarted backend's `/data` Run History panel shows the interrupted run's real last-checkpointed progress (not "0 snapshots · 0 trading days in range").
- TC-9: given the same live restart cycle, when the backend comes back up cold, then the `/data` Coverage payload panel serves a real value read via `coverage_from_storage` (not the all-zero not-yet-computed sentinel) for a date it has already ingested.
- TC-10: given `TRENDORA_FORCE_LEGACY_BAR_CACHE=0` is set in the environment, when `_do_backfill` reaches the shared-cache stash line, then the value is treated as falsy (legacy mode is NOT forced) and `prog._shared_bar_cache` is set to the real shared cache.
- TC-11: given `TRENDORA_FORCE_LEGACY_BAR_CACHE=1` is set in the environment, when `_do_backfill` reaches the same line, then the value is treated as truthy (legacy mode IS forced) and the stash is skipped — proven by the new 2-line test.
- TC-12: given the root-logger fix is applied, when `_refresh_ingest_aggregates` logs the J-07 finalize-tail `cache_ctx` liveness line at `.info` level, then that line still appears in `logs/backend.log` (grep-able), confirming `.info` calls are no longer silently dropped.
- TC-13: given a real K>=3-date backfill running live, when `read_pool()`'s wall-clock cost is measured directly during that run (not projected from a micro-benchmark), then the measured figure is recorded in `reports/perf-budgets.md` next to the prior projected figure.

## NOTES

- Rule-5 precedent already logged: iter-37's decomposer explicitly ruled that rule 5 ("never bundle two risky journeys/changes") applies to CODE changes, not verification/measurement passes — this iteration bundles ONE risky code-adjacent action (re-tuning the drill's memory cap to hit the correct stage) with cheap, already-diagnosed mechanical fixes (env-toggle guard, root-logger config, replay-lane repair) and two verification-only passes (J-04, J-05 step 3), consistent with that established reading; no new assumptions-ledger entry needed for a routine application of a settled precedent.
- The replay-lane fix (`incredible_auto_dev/scripts/automation/lib/demo_runner.py`) is framework/tooling code, not product code — the same class of change iter-33 already made to `merge_ui_test_results.py` in this session with no coherence objection.
- Do not repeat iter-38's exact mistake: raising the cap from 3072 MB purely "so both arms complete gracefully" defeated the whole point of a PROVE-failure drill (iter-38's own binding lesson). This iteration runs no comparison arm — one drill, one goal: raise `MemoryError` in the aggregate-warm stage and prove the process stays alive.
- Owner items (iter-34/j health budget, iter-33/i start-frontend.sh host-guard membership) remain open and unresolved by any agent path; both are explicitly named in OUT OF SCOPE and should be settled before any GOAL_ACHIEVED attempt, per three prior evaluators.
