# Goal Iteration 0 — Baseline: verify the five ops-hardening journeys against the current codebase

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 0
- **Mode:** baseline
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-01, J-03, J-04, J-05, J-06
- **Required-still-passing journeys:** none (baseline — nothing verified yet)
- **Anti-goal reminders** (verbatim from `docs/goal.md`):
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

Establish the starting line for the `ops-hardening` session: run all five Must-have journeys (J-01, J-03, J-04, J-05, J-06) against the current Trendora codebase exactly as it stands, and record for each whether it already passes, fails, or is partial — with no code changes.

## BACKGROUND

This is a **baseline assessment, not a feature delivery** — iteration 0 of the `ops-hardening` goal session, which layers operational hardening (instant boot, ingest-time aggregates, per-page lazy loading, unrestricted backfill, honest job/backend status) on top of the already-`GOAL_ACHIEVED` `mcp-loop` product (25/25 journeys, 2026-07-16, archived at `docs/archive/goal-mcp-loop.md`). `docs/goal.md` was goal-linted and amended immediately before this session launched (commit `9c98cb3`: J-01/J-02 merged, anti-goals labeled AG-1..AG-9, the backfill run-summary contract pinned, J-04/J-05 steps de-flaked) — the version read for this spec is that final, lint-clean contract, so there are no outstanding lint findings to carry forward.

A codebase scan (recorded in `runs/goal-session-ops-hardening/state/blueprint.md`) shows a **mixed starting position**, not a from-scratch build: `app.engine.readiness.compute_readiness`/`compute_preflight` and the extended `GET /api/health` already exist (mcp-loop iter-28/iter-33) and already distinguish `ready`/`initializing`/`unavailable` — but `scripts/start-backend.sh` neither sets `ulimit -v`/`MALLOC_ARENA_MAX` (config.py already declares `memory_cap_mb`/`malloc_arena_max`, nothing enforces them) nor redirects uvicorn output to a persistent logfile, so J-04's crash-log and memory-cap acceptance criteria look unmet. `config.yaml`'s `data_manager.max_range_days: 370` and its pinning tests (`test_data_manager.py`, `test_api_data.py`, `test_config.py`) are still present exactly as goal.md describes, so J-03 looks unmet. `DataProviderRun` (`data_provider_runs` table) exists but carries no structured per-date exclusion-reason/`dates_total` fields, and no `coverage_snapshot` table exists yet, so J-01's zero-work-honesty contract and J-05's ingest-persisted coverage payload look unmet; `compute_coverage`'s `_compute_coverage_uncached` path is still the per-request whole-table-prefill shape goal.md's "Ground truth" section names as the OOM offender. These are the decomposer's own preliminary code-reading, not verdicts — the developer step below is a deliberate no-op and the browser-QA agent's empirical run against the live app is what actually determines pass/fail/partial per journey; the goal-evaluator records it.

No lessons exist yet in `runs/goal-session-ops-hardening/state/lessons.md` (first iteration — none to apply). No `coherence.md` exists yet (nothing to consolidate). Target-selection rubric: baseline mode bypasses the normal 1-3-journey rubric by design — ALL five Must-have journeys are listed as targets per the agent's baseline-mode instructions, so this is not a rubric deviation. Depth is `lean` because baseline mode mandates it unconditionally (no full-depth trigger is being evaluated): the developer step is a no-op, so there is no structural/data-model/cross-cutting change whose blast radius would call for the full 11-step pipeline — the entire value of this iteration is the browser-QA step observing the live app.

## IN SCOPE

### Backend
- [ ] None — verify-only. No source files are created or modified this iteration.

### Frontend (if applicable)
- [ ] None — verify-only. No source files are created or modified this iteration.

### Verification work (the actual iteration output)
- [ ] Run each of J-01, J-03, J-04, J-05, J-06 against the running app (backend + frontend up) and record the actual observed result (pass / fail / partial) with concrete evidence (what was on the page, what the API returned, what was missing).

### New user-facing capability
None. Baseline establishes which capabilities already exist.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — the product is observed, not changed.

### Blueprint conformance
No new surfaces this iteration. `runs/goal-session-ops-hardening/state/blueprint.md` is created alongside this spec and records the current Information Architecture (the existing 11-item nav + global readiness badge/preflight banner) and Data Contract (existing canonical values, plus `[TARGET]` entries this ops-hardening cycle will complete: job history exclusion reasons, the persisted coverage payload, the backfill run-summary contract). Nothing in this iteration adds to either — it is the registration baseline iter-1+ builds into.

### Data-contract additions
None. This iteration introduces no new displayed value; the `[TARGET]` values it registers (see blueprint) are built by later iterations, which must use the module/endpoint already named there.

## OUT OF SCOPE

- Any code, config, dependency, or migration change.
- Building or extending `data_provider_runs`'s exclusion-reason fields, the `coverage_snapshot` table, the persistent backend logfile, `ulimit`/`MALLOC_ARENA_MAX` enforcement, or removing `max_range_days` — all iter-1+ work.
- Re-verifying the 25 previously-`GOAL_ACHIEVED` `mcp-loop` journeys — they are archived and not tracked by this session's `journey-history.json`; only J-01, J-03, J-04, J-05, J-06 are in scope here.
- Editing `docs/goal.md` — it was goal-linted and finalized immediately before this session launched.
- Marking any journey passing/failing in `journey-history.json` — only the goal-evaluator does that.

## DEFINITION OF DONE

- [ ] Every Must-have journey (J-01, J-03, J-04, J-05, J-06) is verified against the current state and its actual result recorded with evidence.
- [ ] No code, config, or dependency changes were made (verify-only) — vacuously satisfies "no anti-goal violation introduced" (nothing was touched).
- [ ] Browser-QA results recorded for the goal-evaluator to score and seed `journey-history.json`.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-0-dev.md` stating "baseline verify-only — no changes" and listing the per-journey observations.

## TESTING REQUIREMENTS

- **Browser:** verify J-01, J-03, J-04, J-05, J-06 against the running app (backend + frontend up, started via `scripts/start-backend.sh` / `scripts/start-frontend.sh` — prod mode, never `dev.sh`, per J-04/J-06's own measurement conditions).
- **Unit/integration:** none required (no code paths changed this iteration).
- **Error cases:** none required (verify-only).

Test-first contract:

- TC-1: given the backend and frontend are running, when a backfill job is submitted on `/data` for range 2026-05-02 to 2026-05-29, then the job summary shows `dates_total = 19` and lists 2026-05-25 excluded with a non-trading reason.
- TC-2: given the May backfill has completed, when `/scanner-runs` is opened, then runs exist for 2026-05-04, 2026-05-15, and 2026-05-29, and opening one renders a leaderboard from the stored snapshot.
- TC-3: given a second backfill is submitted for the weekend-only range 2026-05-02 to 2026-05-03, when it completes, then the summary shows `dates_total = 0` with a breakdown of 2 non-trading days across the 2 calendar days.
- TC-4: given the identical 2026-05-02 to 2026-05-29 range is re-run after TC-1's backfill, when it completes, then the summary shows 0 snapshots created with a breakdown of 19 already-snapshotted + 9 non-trading across the 28 calendar days.
- TC-5: given both zero-work runs (TC-3, TC-4) have completed, when the `/data` page is reloaded, then the persisted job-history panel still lists all three runs with the same outcomes, and both zero-work runs render in a state visually distinct from the productive run's success presentation.
- TC-6: given `/data` is open, when a backfill spanning 2025-06-01 to 2026-07-17 (more than 370 calendar days) is submitted, then the request is accepted with no "date range too large" rejection and a live progress panel appears.
- TC-7: given the >370-day job is running, when its first chunk completes, then the progress panel advances past that chunk with no cap-related failure.
- TC-8: given the backend is stopped, when it is restarted via `scripts/start-backend.sh` and `GET /api/health` is polled from process start, then the first HTTP 200 response arrives within 5 seconds.
- TC-9: given the frontend is already open and the backend is restarted again, when `GET /api/health` is polled at ≤250ms intervals from process start, then at least one pre-ready response carries a boot phase and a progress value `n/m`, and the top-bar badge observed in that same window shows the same phase detail as an explicit initializing state.
- TC-10: given the backend process is killed to simulate a crash, when the UI is observed, then it shows an explicit unreachable/crashed presentation visibly distinct from the initializing state.
- TC-11: given the persistent backend logfile is inspected after the simulated crash, when its contents are read, then it contains the boot events and ends abruptly with no clean-shutdown entry.
- TC-12: given a job was mid-flight when the backend was killed, when the backend restarts and `/data` is opened, then that job shows an explicit interrupted/error state with its last persisted progress, never a still-"running" row.
- TC-13: given a backfill covering one unsnapshotted historical trading day (e.g. 2026-05-15) completes, when `/scanner-runs` is opened, then the date is listed and its leaderboard renders the stored snapshot.
- TC-14: given that same backfill has completed, when the persisted run record is inspected, then it lists which inventory aggregates its finalize hooks refreshed (latest-date snapshot, coverage payload, membership timeline, market phase, research hot-key caches).
- TC-15: given the backend is restarted after ingest, when `/data` is opened cold, then the coverage payload renders within its committed budget with no full `daily_prices` table scan.
- TC-16: given a heavy ingest job is running, when `GET /api/health` is polled during that job, then it continues returning responses throughout (no stall).
- TC-17: given a warm backend started via `scripts/start-backend.sh`/`scripts/start-frontend.sh`, when each of `/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, and one `/research` lab loads, then its time-to-interactive and on-load API latencies are recorded in `reports/perf-budgets.md`.
- TC-18: given the measurements from TC-17, when compared against the committed budgets table in `reports/perf-budgets.md`, then each is recorded as within budget or as a documented gap.
- TC-19: given the developer step completes, when `docs/handoffs/goal-ops-hardening-iter-0-dev.md` is read, then it states "baseline verify-only — no changes" and lists an observed result (pass/fail/partial) for each of J-01, J-03, J-04, J-05, J-06.
- TC-20: given the iteration completes, when `git status`/`git diff` is checked, then it shows zero changes to any file under `apps/` or `config.yaml` (only `docs/phases/goal-ops-hardening-iter-0.md`, `runs/goal-session-ops-hardening/state/blueprint.md`, `runs/goal-session-ops-hardening/state/assumptions.md`, and handoff/report artifacts are new).

## NOTES

- Record any journey (or step within one) that cannot be exercised because the surface is entirely absent (e.g. no persistent logfile, no `coverage_snapshot` row, no `max_range_days` removal) as **FAIL with reason "surface not yet implemented"** — not as blocked/NA. All five are buildable offline against the committed seed/fixtures (AG-9) and drive iter-1+.
- For the goal-evaluator: J-01, J-03, J-04, J-05, J-06 are this session's journey IDs (J-02 was merged into J-01 during pre-launch goal-linting and is retired — never reused). Seed `journey-history.json` with these five.
- Suggested build order once baseline results are in (per goal.md's "Loop mechanics," the decomposer may re-order with reasons): the data-jobs cluster first (J-01, J-03 — unblocks the owner's immediate backfill need), then the aggregate/boot cluster (J-05 enabling J-04), then the measurement capstone (J-06).
- Forward guidance for iter-1+: once this session has more than one iteration of passing history, fold a small rotating smoke check of core existing pages (Dashboard, Stocks, Data) into the Required-still-passing set even though they carry no `J-xx` id in this session — they are the Non-Goal's "additive, not a rewrite" guarantee and have no dedicated golden yet.
- Services: the goal-mode harness starts backend + frontend; per J-04/J-06's own measurement conditions, prefer `scripts/start-backend.sh`/`scripts/start-frontend.sh` (prod mode) over `scripts/dev.sh` wherever the journey's timing/logfile acceptance criteria are being checked.
- One assumption was logged to `runs/goal-session-ops-hardening/state/assumptions.md` (iter-0): the blueprint's Information Architecture keeps the actual 11-item sidebar rather than trimming to goal.md's 9-item prose list — reversible.
