# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-12 Execution Plan

Jobs-pipeline hardening (J-59, J-60, J-66, J-67). One coherent backend state-machine change on
`apps/backend/app/engine/data_manager.py` + its checkpoint/lifecycle models, with the `/data` job card /
Run history / Unfinished-imports surfaces reformatting the new fields. No new page, route, or nav. No
canonical score/return/bucket changes — backfill outputs MUST stay byte-identical to the sequential engine.

## What to Build

- **J-59 — stage-aware checkpoint + zero-provider-call resume.** Extend `ImportCheckpoint` to record
  per-stage completion (fetch → screen → backfill). A job that failed/interrupted AFTER a completed fetch
  resumes FROM the backfill stage with **zero provider calls** (assert via an injected counting provider).
  Existing snapshots are read, never recreated (create-once / J-41 / J-53 intact). The stage checkpoint
  survives a process/backend restart (reload the row → Resume still starts at backfill). J-34 rate-limit
  chunk-resume semantics unchanged.
- **J-59 — covered-range fetch planner.** The fetch planner consults stored coverage against the benchmark
  trading calendar and SKIPS the provider call for any `(symbol, window)` already fully covered — a re-run
  over a covered range reaches backfill in seconds, never ~45 min of no-op re-fetching to add `0 new bars`.
  A partially-covered window still fetches; per-`(symbol, date)` INSERT-new-only idempotency still holds
  (no duplicate rows). J-38 Retry stays available + idempotent.
- **J-60 — job lifecycle record created at start.** Starting ANY `/data` job creates its `DataProviderRun`
  row IMMEDIATELY (status `running`, carrying kind / date range / source) instead of only at the terminal
  `finally`. Exactly ONE honest terminal transition (`ok`/`partial`/`failed`; rate-limited pause →
  `resumable`). A **boot sweep** in `main.py` lifespan marks any orphaned `running` row (process gone) as
  `interrupted`. Same single bookkeeping source the job card / Run history / Unfinished-imports already
  read — never a second path. Key NEVER persisted onto the `running` record. J-38 Dismiss semantics
  unchanged; a terminal record is never silently mutated afterward.
- **J-66 — fine-grained, honest progress.** Fetch progress ticks at per-symbol-completion granularity with
  a **thread-safe distinct-symbol completion counter** (workers may tick; ALL DB writes + checkpointing
  stay on the orchestrating thread; chunk-atomic commit/rollback + J-34 checkpoint semantics unchanged).
  Fix the `318/159` bug: `prog.symbols_ok += 1` currently fires once per `(symbol, date-window)` chunk, so
  with 2+ windows the counter exceeds `symbols_total` (distinct symbols). Count **distinct symbols**
  completed (or label units against a matching unit total) — counters MUST be monotone and never exceed
  totals. Add a **current-activity message** and a **last-progress heartbeat timestamp** to `JobProgress` +
  `to_dict`. Per-stage progress/timings (J-53) render LIVE during the run, not only at completion. New
  polling/heartbeat/granularity knobs come from **config** (`data_manager.import_chunking` or a new
  config block) — no magic numbers.
- **J-66 — move `speedupFactor` derivation server-side.** The backfill stage entry in the backend stages
  payload carries the computed speedup figure (sequential `per_date_seconds_sum` / parallel
  `elapsed_seconds`, honest-NA when either is missing/zero). The frontend only re-formats it. Remove the
  client-side division at `apps/frontend/app/data/page.tsx` (`speedupFactor()` ~line 97 + its caller
  ~line 1200). Clears the iter-8 coherence-WARN residual.
- **J-67 — transactionally sound parallel multi-date backfill.** Make the concurrent backfill's
  session/transaction management sound: no Session shared across concurrent workers mid-transaction, and
  the orchestrating session is never left emitting SQL in an invalid `'committed'` state. A multi-month
  `both`/`backfill` job (the reported ~91-date repro) completes WITHOUT the committed-session failure. A
  single date's failure is **isolated** — recorded per-date (honest error + counts) while the remaining
  dates complete, ending in an honest `partial`, never aborting the whole stage, never fabricating a
  snapshot. Canonical outputs stay byte-identical to the sequential engine.

## Agents Required

- backend-data: **yes** — all four journeys are primarily a backend state-machine change in
  `data_manager.py` + `models.py` + the `main.py` boot sweep, proven offline with injected
  counting/fault-injecting providers + the full pytest gate. This is the hard gate.
- frontend-ux: **yes** — `/data` job card (per-symbol bar that never exceeds total, current-activity line,
  "updated Ns ago" heartbeat, live per-stage timings, backend-supplied speedup), Unfinished-imports
  ("failed at backfill — resumable from the backfill stage" + Resume), Run history (`running` / `resumable`
  / `interrupted` rows from job start), and a `partial` job's per-date failure detail. Reformat-only — no
  new client-side derived value.
- developer: yes -- implements both the backend and frontend changes above following TDD; updates the
  blueprint Data Contract status tags (Import-job-control + J-60 Job-lifecycle-record rows: `[TARGET]` →
  built); writes the dev handoff.

## Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/models.py` -- `ImportCheckpoint`: add stage-completion fields (e.g. `fetch_done` /
  `screen_done` / `backfill_done` flags or a `completed_stages` column) so resume can route to backfill;
  keep NO key column. `DataProviderRun`: support a `running` start-state + an `interrupted` terminal status
  (extend the `status` comment/contract; no new table). Append-only column additions (defaulted) so a
  fresh DB carries them; no migration tool (SQLModel `create_all`).
- `apps/backend/app/engine/data_manager.py` -- the core change:
  (a) **J-60** create the `DataProviderRun` `running` row at job start (new helper, INSERT once) and have
  the terminal `_persist_run` UPDATE that same row's status/finished_at/counts (one record, one terminal
  transition) instead of inserting a second row; ensure the key never reaches it.
  (b) **J-59** stage-aware checkpoint write/read; a `resume`-at-backfill path that skips the fetch stage
  entirely (zero provider calls); a covered-range fetch planner that skips fully-covered `(symbol, window)`
  chunks against the trading calendar (reuse `_existing_dates` / `_trading_days`).
  (c) **J-66** distinct-symbol completion counter (fix `prog.symbols_ok += 1` in `_run_chunked_fetch` so it
  counts a symbol once across windows); `current_activity` + `last_progress_at` heartbeat on `JobProgress`
  + `to_dict`; record the speedup figure into the backfill stage entry server-side (in `record_stage` /
  `_run_job`).
  (d) **J-67** per-date failure isolation in `_do_backfill` (catch a worker `future.result()` exception
  per-date → record an honest per-date error + continue draining the rest → end `partial`); ensure no
  shared session is used mid-transaction by a worker and the orchestrating session never lands in a
  `'committed'` invalid state across the drain loop.
- `apps/backend/main.py` -- `lifespan`: a **boot sweep** that marks orphaned `running` `DataProviderRun`
  rows (no live process) as `interrupted` before/around `start_warmup` (idempotent, non-fatal).
- `apps/backend/app/api/data.py` -- ensure `resume_job` routes a backfill-stage resume (zero provider
  calls) and the `/data` overview / job-status payloads expose the new fields (current-activity, heartbeat,
  per-date failure detail, `running`/`interrupted` rows). No new endpoint expected.
- `config.yaml` + `apps/backend/app/config.py` -- new J-66 knobs (poll interval / heartbeat / granularity)
  added to the typed config with boot validation (positive, etc.). **Grep the new section key across ALL
  config-narrowing + inline-test-config sites, including `apps/backend/scripts/build_qa_fixture_db.py`** —
  this exact miss caused iter-11's single full-suite failure.
- `apps/frontend/app/data/page.tsx` -- job card: per-symbol bar capped at total, current-activity line,
  "updated Ns ago" heartbeat, live per-stage timings/elapsed during the run, render the backend speedup
  figure (DELETE `speedupFactor()` division ~line 97 + caller ~1200); Unfinished-imports stage-resume copy
  + Resume action; Run history `running`/`resumable`/`interrupted` states; `partial` per-date failure
  detail. Keep any new clickable control as a sibling in a non-clickable row with `stopPropagation`
  (iter-5 nested-interactive hazard).
- `apps/frontend/lib/api.ts` -- extend the job / run / checkpoint TS types with the new fields
  (current_activity, last_progress_at / heartbeat, backfill speedup, stage state, per-date failures,
  `running`/`interrupted` statuses).
- Backend tests (TDD, the hard gate):
  `tests/test_data_manager.py`, `tests/test_data_manager_backfill_parallel.py`,
  `tests/test_data_manager_parallel.py` (+ a new lifecycle/boot-sweep test module if cleaner) — see Key
  Test Scenarios. Sweep every new required config field into every inline-config site.

## UI Evolution

- New user-facing capability: interrupt/fail a long import and **Resume from the backfill stage** with zero
  re-fetch; re-run a covered range and have it skip straight to backfill in seconds; see every job in Run
  history the moment it starts (and an honest `interrupted` after a crash); watch fine-grained, trustworthy
  live progress; run a multi-month backfill to completion with one bad date isolated as `partial`.
- New information displayed: stage-aware unfinished-import state ("failed at backfill — resumable from the
  backfill stage"); a `running` Run-history row from job start; an `interrupted` terminal state after a
  crash; a per-symbol-advancing progress bar that never exceeds its total; a current-activity line; an
  "updated Ns ago" heartbeat; live per-stage timings/elapsed during the run; the backend-computed speedup
  figure; per-date failure detail on a `partial` job.
- New user actions: **Resume** a job that failed/was interrupted after its completed fetch stage (resumes
  at backfill, zero provider calls). No other new controls — Resume/Retry/Dismiss already exist (J-38);
  their semantics are extended, not multiplied.
- UI surface changes: only `/data` (Data Manager) — the Unfinished-imports section, the Run history list,
  and the live job card. No new page/route.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the EXISTING `/data` job-card, Unfinished-imports, and Run-history components
  + the shared `ProgressBar`; add the current-activity line + heartbeat as plain text rows inside the
  existing card. No new component library primitives — this is a reformat of existing surfaces.
- Layout: unchanged `/data` page layout (job form + live job card + Unfinished-imports + Run history +
  coverage). New fields slot into the existing job card / row layouts.
- Key visual effects: match the established dense dark analytical workstation style; monospace/tabular
  numbers; keep status colors consistent with existing run-status badges (add an `interrupted` color
  treatment distinct from `failed`, and a `running` in-flight treatment).
- States to handle: live (running, ticking heartbeat) / paused-`resumable` / `interrupted` / `partial`
  (per-date failure detail) / terminal `ok` / `failed`. A counter must never render a value exceeding its
  total. Honest-NA for an absent speedup (missing/zero timings) — never a fabricated ratio.

## Key Test Scenarios

Offline backend tests (injected counting/fault providers) are the HARD GATE; browser corroborates.

- **J-59** stage-aware checkpoint records fetch/screen/backfill completion; Resume after a forced backfill
  fault performs **zero** provider calls (injected counting provider) and re-runs only backfill; the
  checkpoint survives a simulated restart (reload the row → Resume still starts at backfill); covered-range
  fetch planner skips covered `(symbol, window)`s; a partial window still fetches; per-`(symbol, date)`
  INSERT-new-only idempotency holds (no duplicate rows).
- **J-60** a job creates its `DataProviderRun` `running` row at start; exactly ONE terminal transition
  (`ok`/`partial`/`failed`/`resumable`); boot sweep marks an orphaned `running` row `interrupted`;
  counts/summary match the job payload; the terminal record is not mutated afterward; the session key never
  reaches the record/checkpoint/detail JSON/log.
- **J-66** per-symbol completion counter is thread-safe + monotone; the symbols counter counts DISTINCT
  symbols and never exceeds its total across a multi-window plan (the explicit `318/159` regression test);
  heartbeat + current-activity present in the payload; the speedup figure is present in the BACKEND stages
  payload (and the frontend no longer divides).
- **J-67** a multi-date (~91-date) parallel backfill completes with no committed-session error; an injected
  single-date fault → that date `failed`, the rest complete, job ends `partial`, no snapshot fabricated,
  no whole-stage abort; create-once re-run fills only what is missing (no UNIQUE crash); the
  parallel-vs-sequential **byte-identical** equality re-asserted (`test_data_manager_backfill_parallel.py`
  family).
- **Regression (required-still-passing):** J-17, J-34, J-38, J-39, J-40, J-41, J-46, J-53 (the shared
  data-manager surface) and J-08/J-36/J-37/J-42; scanner / forward-returns / immutability / no-lookahead /
  `test_warmup.py` suites stay green; full pytest passes (hand the ~46-min full suite to the pump — the
  evaluator dispatch MUST NOT block on it; gate on the flushed terminal summary line).
- **Browser:** `/data` Unfinished-imports "failed at backfill — resumable from the backfill stage" +
  Resume; a `running` row appears in Run history at job start; an `interrupted` row after a restart; the
  live job card per-symbol bar / current-activity line / "updated Ns ago" heartbeat / live per-stage
  timings, with no counter exceeding its total. Distinct, correctly-named screenshots per sub-step (no
  byte-duplicate reuse).

## Risks / Open Questions

- **Boot-sweep "process gone" detection.** There is no per-job PID stored on `DataProviderRun` today.
  Assumption: a fresh process boot owns no in-flight jobs, so ANY `running` row found at lifespan start is
  by definition orphaned from a prior (now-dead) process and is swept to `interrupted` — the in-memory
  `_JOBS` registry is empty on a fresh boot, so this is sound without adding a PID column. Documented as an
  assumption; revisit only if multi-process serving is introduced (out of scope).
- **J-60 one-record contract vs the current append-only INSERT.** Today `_persist_run` INSERTs a fresh
  `DataProviderRun` at the terminal `finally`. Moving to create-at-start means the terminal step must
  UPDATE that same row, not insert a second one. This is a legitimate mutation of MUTABLE job-control
  state (NOT a snapshot) — the anti-goal "terminal record never silently mutated afterward" binds the
  POST-terminal record, not the `running` → terminal transition. The reviewer/auditor should confirm
  exactly one row per job and one terminal transition. J-38 Retry (which re-dispatches) must still produce
  its own honest record per the existing contract.
- **Byte-identity under the J-67 transaction rework.** The per-date failure-isolation + session changes
  must leave `scanner_runs`/`scanner_results`/`*_scores`/`forward_returns` byte-identical to the
  sequential engine — re-assert with the existing parallel-vs-sequential equality tests. Any worker that
  writes (it must not) would break determinism; keep ALL writes on the orchestrating thread (the existing
  pattern), only adding per-date exception capture in the drain loop.
- **Covered-range planner correctness against partial coverage.** The skip must be exact: only a window
  fully covered for a symbol is skipped; a single missing trading day in the window forces the fetch.
  Build the coverage check off the benchmark trading calendar (`_trading_days`) intersected with
  `_existing_dates`, not a naive min/max range, to avoid skipping a window with internal gaps.
- **New config knobs at EVERY site.** The J-66 poll/heartbeat/granularity knobs are a new required typed
  config field — grep the new section key across `apps/backend` INCLUDING
  `apps/backend/scripts/build_qa_fixture_db.py` and every inline-test-config dict; the count GROWS over
  time. (iter-11's single full-suite failure was exactly this miss.)
- **Full-suite runtime (~46 min).** Hand it to the pump; never run two concurrently; gate the evaluator on
  the flushed terminal summary, not an in-flight stream (iter-11's first run aborted by blocking on it).
- **Live-fetch leg stays NA.** Real network fetches are walled — everything is verified offline with
  injected counting/fault providers; the live-fetch leg is honestly NA, non-halting.

## Scope Guard (excluded — out of scope per the spec, do NOT build)

- **J-61** (per-date availability heatmap), **J-62** (as-of calendar popover), **J-63** (event-study
  episode mode) — deferred to later iterations.
- **J-22/J-23/J-24** (data-dependent) — remain blocked-NA, non-vetoing.
- Any change to canonical scores/buckets/setups/returns or the read-path serving of them — backfill
  outputs MUST stay byte-identical to the sequential engine.
- Any change to the live-provider fetch contract beyond the covered-range skip + the per-symbol completion
  counter — the chunked/rate-limit/429-resumable engine (J-34) + per-`(symbol, date)` idempotency stay
  unchanged.
