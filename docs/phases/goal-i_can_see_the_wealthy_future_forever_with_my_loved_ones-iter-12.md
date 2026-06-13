# Goal Iteration 12 — Jobs pipeline made reliable: stage-resume, lifecycle records, honest progress, sound parallel backfill

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 12
- **Mode:** normal
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-59, J-60, J-66, J-67
- **Required-still-passing journeys:** J-17, J-34, J-38, J-39, J-40, J-41, J-46, J-53, J-08, J-36, J-37, J-42
- **Anti-goal reminders:**
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*
  - **On-demand snapshots stay immutable & lookahead-free.** Creating a snapshot for a newly selected date is create-once: an existing snapshot MUST be read, never overwritten; an as-of-D snapshot MUST use only bars with date ≤ D. *(critical)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Live fetch is real-data-only.** The Data Manager MUST use the config-selected live provider to fetch real EOD bars; on a provider failure it MUST surface an explicit error and MUST NOT synthesize prices to fill a gap or force a successful run. *(extends No fabricated data)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request.
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*
  - **No secrets in source / Import keys are env-or-session, never persisted.** The session-only key is never written to the job registry, the checkpoint, the persisted run, the detail JSON, or any log.

## GOAL

The Data Manager's import jobs become stage-resumable (a failed/interrupted job resumes from the backfill stage with zero provider calls and never re-fetches already-covered ranges), recorded in Run history from the instant they start, fine-grained and honest in their live progress (per-symbol/per-date ticks, current-activity line, heartbeat, counters that never exceed totals), and transactionally sound under concurrent multi-date backfill — so a long job finishes reliably, a single bad date is isolated instead of aborting the stage, and nothing is ever fabricated, lost, or double-fetched.

## BACKGROUND

This is the jobs-pipeline cluster the iter-11 evaluator flagged as the next FULL-depth target. J-59/J-60/J-66/J-67 all live in `apps/backend/app/engine/data_manager.py` and share one surface — the durable checkpoint (`import_checkpoints` / `ImportCheckpoint`), the job-lifecycle record (`data_provider_runs` / `DataProviderRun`), the `JobProgress` live registry, and the `_run_job` orchestrator with its parallel multi-date backfill writer. They are one coherent backend state-machine hardening, not four unrelated changes, so they are bundled into a single full-depth iteration to avoid leaving a half-built state machine. None is data-dependent: all four are provable **offline** with an injected counting/fault-injecting provider against the committed seed (goal.md: "J-55 … J-67 are NOT data-dependent … provable with injected/counting providers + fault injection"). This iteration also clears the iter-8 coherence-WARN residual carried on J-66: the frontend currently computes `speedupFactor` client-side at `apps/frontend/app/data/page.tsx:97` from the backend's `per_date_seconds_sum` / `elapsed_seconds` — that derived figure must move into the backend stages payload so the frontend only re-formats it.

## IN SCOPE

### Backend
- [ ] **J-59 — stage-aware checkpoint + zero-provider-call resume.** Extend the durable `ImportCheckpoint` to record per-stage completion (fetch → screen → backfill) so a job that failed or was interrupted **after** a completed fetch is resumable **from the backfill stage**. On Resume the fetch stage is skipped entirely (assert **zero** provider calls via an injected counting provider); only the remaining stage(s) run; existing snapshots are read, never recreated (create-once / J-41 / J-53 intact). The stage checkpoint MUST **survive a process/backend restart** (J-34 durability extended; its rate-limit chunk-resume semantics unchanged).
- [ ] **J-59 — covered-range fetch planner.** The fetch planner consults stored coverage against the benchmark trading calendar and **skips the provider call** for any `(symbol, window)` already fully covered — a re-run over a covered range reaches the backfill stage in seconds (never ~45 min of no-op re-fetching to add `0 new bars`). A partially-covered window still fetches; the per-`(symbol, date)` INSERT-new-only idempotency still guarantees no duplicate row. J-38 Retry stays available and idempotent.
- [ ] **J-60 — job lifecycle record created at start.** Starting any `/data` job **creates its `DataProviderRun` run-history record immediately** (status `running`, carrying kind / date range / source) instead of only writing it at the terminal `finally`. The record receives exactly **one** honest terminal transition (`ok` / `partial` / `failed`; rate-limited pause → `resumable`). A **boot sweep** marks any orphaned `running` row whose process is gone as `interrupted`. This is the **same** lifecycle the job card / Run history / Unfinished-imports already read — one bookkeeping source, never a second one; counts/summary match the job's own payload; a terminal record is never silently mutated afterwards (J-38 Dismiss semantics unchanged); no status ever fabricated.
- [ ] **J-66 — fine-grained, honest progress.** Fetch progress ticks at **per-symbol completion** granularity (a thread-safe completion counter the pool workers tick while ALL DB writes + checkpointing stay on the orchestrating thread; chunk-atomic commit/rollback + J-34 checkpoint semantics unchanged). Backfill progress stays per-date with the current date named. Add a **current-activity message** and a **last-progress heartbeat timestamp** to the job payload (`JobProgress` + `to_dict`). Per-stage progress/timings (J-53) render **live during the run**, not only at completion. **Counters are monotone and never exceed their totals** — the symbols figure counts **distinct symbols** completed across date windows (or labelled units against a matching unit total) — fixing the observed `318/159`. Polling/heartbeat/granularity knobs come from **config** (no magic numbers).
- [ ] **J-66 — move `speedupFactor` derivation into the backend stages payload** (clears the iter-8 coherence-WARN residual): the backfill stage entry carries the computed speedup figure server-side; the frontend only re-formats it. Remove the client-side division at `apps/frontend/app/data/page.tsx:97`.
- [ ] **J-67 — transactionally sound parallel multi-date backfill.** Make the concurrent backfill's DB session/transaction management sound: **no Session shared across concurrent workers mid-transaction**, and the orchestrating session is never left emitting SQL in an invalid (`'committed'`) state (mechanism open: per-worker sessions with a single serialized writer, orchestrator-owned write batches with correct transaction boundaries, or equivalent — SQLite writes stay serialized/transactional). A multi-month `both`/`backfill` job (the reported ~91-date repro) **completes without the committed-session failure**. A single date's failure is **isolated** — recorded per-date (honest error + counts) while the remaining dates complete, ending in an honest `partial`, never aborting the whole stage, never fabricating a snapshot. Canonical outputs stay **byte-identical** to the sequential engine.

### Frontend
- [ ] **J-59 / J-60** — `/data` Unfinished-imports renders the job as **"failed at backfill — resumable from the backfill stage"** (plain-language state + the single right action, **Resume**); Run history shows in-flight (`running`), `resumable`, `interrupted`, and finished jobs from the moment they start.
- [ ] **J-66** — the job card shows: per-symbol-advancing symbols bar, a **current-activity line** ("scanning 2021-03-11 (12/22)" during backfill; the symbol/chunk being worked during fetch), an **"updated Ns ago"** heartbeat, and live per-stage progress/timings/elapsed. Render the backend-supplied speedup figure (no client-side division). Counters never display a value exceeding their total.
- [ ] **J-67** — a `partial` job surfaces the per-date failure (honest error + which dates failed) while the rest are reported complete.

### New user-facing capability
The user can interrupt or fail a long import and resume it from where it stopped without re-fetching anything; re-run a covered range and have it skip straight to backfill in seconds; see every job in Run history the moment it starts (and an honest `interrupted` after a crash); watch fine-grained, trustworthy live progress that distinguishes slow-but-alive from stalled; and run a multi-month backfill to completion with a single bad date isolated as `partial` instead of crashing the stage.

### New information displayed
Stage-aware unfinished-import state ("failed at backfill — resumable from the backfill stage"); a `running` row in Run history from job start; an `interrupted` terminal state after a crash; a per-symbol-advancing progress bar; a current-activity line; an "updated Ns ago" heartbeat; live per-stage timings/elapsed during the run; the backend-computed speedup figure; per-date failure detail on a `partial` job.

### New user actions
**Resume** a job that failed/was interrupted after its completed fetch stage (resumes at backfill, zero provider calls). No other new controls — Resume/Retry/Dismiss already exist (J-38); their semantics are extended, not multiplied.

### UI surface changes
Only `/data` (Data Manager) — the Unfinished-imports section, the Run history list, and the live job card. No new page, no new route, no nav change.

### Product surface delta
The Data Manager stops being a place where a long job can silently vanish, double-fetch for 45 minutes, crash on a committed-session error, or show a misleading `318/159` counter. It becomes a reliable, auditable, honestly-instrumented job pipeline.

### Blueprint conformance
No new surfaces. All work lands on the existing **Data Manager** (`/data`) home (top-level sidebar link), reachable in 1 click — the registered home for J-17/J-33–J-39/J-53/J-59/J-60/J-61/J-66/J-67 in the IA skeleton. The Data Contract rows for these journeys are already registered as `[TARGET]` (Import job control row: J-59/J-66/J-67; the dedicated **J-60 — Job lifecycle record** row). This iteration moves them from `[TARGET]` to built — the developer/auditor will update the blueprint status tags as part of the change.

### Data-contract additions
**No genuinely new canonical value** is introduced. All four journeys operate on **already-registered** Data Contract rows:
- **Import job control** (`data_manager:*`, `import_checkpoints` + `DataProviderRun` job-control — NOT snapshots; served by `GET /api/data`, `POST /api/data/jobs*`): J-59 makes the checkpoint stage-aware + adds the covered-range fetch planner; J-66 makes progress fine-grained/honest + moves the speedup derivation server-side; J-67 makes the parallel backfill transaction-sound. Job stage timings / progress remain **descriptive operational metadata, not a canonical score** — the `/data` card only re-formats them.
- **J-60 — Job lifecycle record** (the same `data_provider_runs` lifecycle the job card reads; `GET /api/data` run history): create at start (`running`) → one honest terminal transition; boot sweep → `interrupted`. One bookkeeping source — never a second job-bookkeeping path.

The per-date availability heatmap (J-61) is a separate registered `[TARGET]` row and is **out of scope** this iteration.

## OUT OF SCOPE

- **J-61** (per-date availability heatmap), **J-62** (as-of calendar popover), **J-63** (event-study episode mode) — deferred to later iterations.
- Any change to canonical scores/buckets/setups/returns or the read-path serving of them — backfill outputs MUST stay byte-identical to the sequential engine.
- Any change to the live-provider fetch contract beyond the covered-range skip and the per-symbol completion counter — the chunked/rate-limit/429-resumable engine (J-34) and the per-`(symbol, date)` idempotency stay unchanged.
- Real network fetches — everything here is verified offline with injected counting/fault-injecting providers; the live-fetch leg stays honestly NA where the provider is walled (non-halting).
- The data-dependent journeys J-22/J-23/J-24 — remain blocked-NA, non-vetoing.

## DEFINITION OF DONE

- [ ] Target journeys J-59, J-60, J-66, J-67 pass (J-59/J-60/J-67 primarily via offline backend tests with injected counting/fault providers + the `/data` UI surfaces; J-66 via the live job card and the suite). Browser-QA exercises the `/data` Unfinished-imports / Run history / live job card surfaces.
- [ ] Required-still-passing journeys remain green — especially J-17, J-34, J-38, J-39, J-40, J-41, J-46, J-53 (the shared data-manager surface) and J-08/J-36/J-37/J-42.
- [ ] **Zero-provider-call resume** asserted by an injected counting provider (J-59).
- [ ] **Covered-range re-run** reaches backfill in seconds with zero provider calls for covered symbols (J-59).
- [ ] A **committed failure-isolation regression test** exercises a multi-date parallel backfill end-to-end including the per-date failure path, offline (J-67).
- [ ] **Counters never exceed totals** — a plan spanning 2+ date windows over the full symbol set never reads `318/159` (J-66), asserted in a test.
- [ ] No anti-goal violation introduced (no fabricated counts/timestamps/snapshots; no key persisted; snapshots immutable; create-once preserved; no recompute in the read path).
- [ ] Full pytest suite passes; no regressions; outputs byte-identical to the sequential engine (scanner / forward-returns / immutability / no-lookahead suites green).
- [ ] Coherence audit is COHERENCE-PASS (the iter-8 `speedupFactor` WARN residual cleared by moving the derivation server-side).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** J-59 (Unfinished-imports "failed at backfill — resumable from the backfill stage" + Resume), J-60 (a `running` row appears in Run history at job start; an `interrupted` row after a restart), J-66 (live job card: per-symbol bar, current-activity line, "updated Ns ago" heartbeat, live per-stage timings, no counter > total). All on `/data` against the committed seed.
- **Unit/integration (offline, the hard gate):**
  - J-59: stage-aware checkpoint records fetch/screen/backfill completion; Resume after a forced backfill fault performs **zero** provider calls (injected counting provider) and re-runs only backfill; checkpoint survives a simulated restart (reload the row, Resume still starts at backfill); covered-range fetch planner skips covered `(symbol, window)`s; partial window still fetches; per-`(symbol, date)` INSERT-new-only idempotency holds (no duplicate rows).
  - J-60: a job creates its `DataProviderRun` `running` row at start; exactly one terminal transition (`ok`/`partial`/`failed`/`resumable`); boot sweep marks an orphaned `running` row `interrupted`; counts/summary match the job payload; terminal record not mutated afterwards.
  - J-66: per-symbol completion counter is thread-safe and monotone; symbols counter counts distinct symbols and never exceeds its total across multi-window plans (the `318/159` regression test); heartbeat + current-activity present in the payload; speedup figure present in the backend stages payload.
  - J-67: multi-date (~91-date) parallel backfill completes with no committed-session error; injected single-date fault → that date `failed`, the rest complete, job ends `partial`; create-once re-run fills only what is missing (no UNIQUE crash); parallel-vs-sequential **byte-identical** equality re-asserted (`test_data_manager_backfill_parallel.py` family).
  - Regression: scanner / forward-returns / immutability / no-lookahead / `test_warmup.py` suites stay green.
- **Error cases:** forced backfill fault mid-stage (→ resumable-at-backfill, not lost); single-date failure in a multi-date backfill (→ isolated `partial`, others complete, no abort, no fabricated snapshot); process death mid-job (→ `interrupted` boot sweep, not stuck `running`); re-run over a fully-covered range (→ zero provider calls, no duplicate rows); a counter that would exceed its total (→ must be impossible by construction).

## NOTES

- **Lessons applied (surface to dev/reviewer/auditor):**
  - **New-config-section / new-required-field at EVERY site.** J-66's new config knobs (polling interval, heartbeat, granularity) and any new required typed config field must be added at EVERY config-narrowing + inline-test-config site. **Grep the new section key across `apps/backend`, including `apps/backend/scripts/build_qa_fixture_db.py`** — this exact miss (the QA fixture builder not pruning `stock_industries`) caused iter-11's single full-suite failure. Don't trust a fixed list; count GROWS over time.
  - **Snapshot immutability + byte-identical canonical values.** J-67's transaction rework and J-59's create-once-read path must leave `scanner_runs`/`scanner_results`/`*_scores` byte-identical to the sequential engine — re-assert with the existing parallel-vs-sequential equality tests. Any stored-copy/refactor proves byte-identity.
  - **Import keys are env-or-session, never persisted.** The session-only key must never reach the job registry, checkpoint, persisted `DataProviderRun`, detail JSON, or any log — preserved across the J-60 start-record change (the `running` record carries kind/range/source, never the key).
  - **Full pytest ~46 min — hand it to the pump; never run two concurrently.** The full suite must be handed to the pump and the **goal-evaluator dispatch must NOT block on it** — iter-11's first run aborted at the evaluator precisely because the pump blocked waiting on the suite. Run the suite in the background and gate the evaluator on the flushed terminal summary line, not on an in-flight stream.
  - **md5 evidence hygiene.** Capture distinct, correctly-named screenshots per `/data` sub-step; do not reuse a byte-duplicate image across sub-steps (prior iters carried mislabeled-capture caveats).
  - **iter-5 nested-interactive hazard.** Any new clickable control on the `/data` job card (e.g. Resume affordance copy/state) must not nest an interactive element inside another role=button — keep sibling controls in non-clickable rows with defensive `stopPropagation`, per the established pattern.
- **Why FULL depth:** new backend state machine (stage-aware checkpoint + lifecycle record + transaction-soundness), full pytest gate required, the prior evaluator recommended `full`, and the four journeys are tightly coupled across `data_manager.py` and the checkpoint/lifecycle model.
- **Evidence basis:** J-59/J-60/J-67 are primarily proven by offline backend tests (injected counting/fault providers) — the browser surfaces corroborate the plain-language states and lifecycle rows but are not the gate; J-66's live progress is the journey most directly browser-observable.
- Per the iter-11 evaluator and the blueprint `[TARGET]` tags, J-61/J-62/J-63 follow this cluster in subsequent iterations.
