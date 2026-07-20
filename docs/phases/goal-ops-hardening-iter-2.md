# Goal Iteration 2 — Ingest-time aggregate maintenance (coverage, market phase, membership timeline, research hot-keys) + launch-script memory/logfile enforcement

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 2
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-05, J-04
- **Required-still-passing journeys:** J-01, J-03
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

## GOAL

The backend maintains coverage, latest-snapshot, membership-timeline, market-phase, and research
hot-key aggregates at ingest time (persisted, byte-identical to today's values), so a cold `/data`
visit and every reader page serve them instantly from storage with zero request-path whole-table
loads, and `scripts/start-backend.sh` actually enforces the declared memory cap and writes a
persistent boot logfile.

## BACKGROUND

The iter-1 evaluator explicitly recommended this exact scope next (full depth): "Build the ingest
finalize hooks + the new `coverage_snapshot` table so `GET /api/data` coverage, latest-date
snapshot, membership timeline, market phase, and research hot-key caches are all served from
persisted rows... This also completes J-04's remaining memory-cap/boot-no-prefill story." J-05 is
the priority-rubric unblocker (rule 3): it unblocks J-04's last open acceptance bullet ("boot
performs no whole-table loads and no synchronous snapshot computation") and J-06's forthcoming
per-page budgets (goal.md's own suggested build order). J-04 is bundled because its remaining gap —
persistent logfile + enforced `memory_cap_mb`/`malloc_arena_max` — is small, mechanical, and
addressed by the same body of work; only J-05 is the risky (data-model) change, so this does not
violate "never bundle two risky journeys" (rubric rule 5). Depth is **full**: trigger 1
(cross-cutting — `data_manager.py`, `models.py`, `api/data.py`, `warmup.py`, `market_phase.py`,
`research.py`, `scripts/start-backend.sh`, and the frontend data page all change) and trigger 2
(data model — a new persisted `coverage_snapshot` table becomes part of the blueprint Data
Contract). Two lessons apply directly: iter-0's lesson that `reports/perf-budgets.md`'s and
`config.yaml`'s prose claiming `scripts/start-backend.sh` already enforces `memory_cap_mb`/
`malloc_arena_max` is **false** (re-confirmed this iteration by a direct read of the script — it
sets no `ulimit`, exports no env var, and writes no logfile); and iter-1's lesson that a new
persisted/served field's honesty risk lives in its not-yet-computed/interrupted edge, not its
happy path — directly applicable to this iteration's new `aggregates_refreshed` field, which must
be gated the same way `_run_detail()` already gates `calendar_days` (null/empty until the finalize
hook that computes it actually ran, never a fabricated list on an interrupted row).

Investigation (this iteration) also found `compute_coverage` already has an in-process
single-flight/result cache (`data_manager.py:703`) — it just never survives a restart and its first
per-key compute still pays the full `prefilled_bar_cache` whole-table load (the documented OOM
source); and `MarketPhaseCache`/`EventStudyCache`/`MembershipTimelineCache` are already real,
restart-surviving DB-backed read-through caches (unlike coverage) — so the market-phase/research/
membership piece of this iteration is "warm the existing cache at ingest instead of on first
request," not a new table, while coverage needs a genuinely new persisted table.

## IN SCOPE

### Backend
- [ ] New persisted `coverage_snapshot` table (`apps/backend/app/models.py`, following the existing
      `MarketPhaseCache`/`EventStudyCache`/`MembershipTimelineCache` convention) serving `GET
      /api/data`'s coverage block — replaces the request-path call to `compute_coverage`.
- [ ] An ingest finalize hook reached at the end of a successful `backfill`/`both`/`rebuild` job
      (`app.engine.data_manager`, the `_do_backfill`/`_run_job` completion point) that persists a
      fresh `coverage_snapshot` row for the current membership/dataset stamp, and re-warms the
      existing `MarketPhaseCache` (for each newly-created snapshot date), `MembershipTimelineCache`,
      and `EventStudyCache` (default/hot keys) — reusing each cache's existing compute function
      (`market_phase_cached`, `membership_timeline_cached`, `event_study_cached`), never a second
      derivation of any of them.
- [ ] New `aggregates_refreshed` field on the persisted run record (`JobProgress` / `_run_detail()`),
      gated on the SAME "actually computed" pattern iter-1 established for `calendar_days`
      (non-null/non-empty only once the finalize hook that populates it has actually run) — present
      for `backfill`/`both`/`rebuild` kinds only, `null` for `fetch`/`expand` (matches the existing
      `dates_total` nullability convention).
- [ ] Background warm-up thread (`app.engine.warmup._run_warmup`) gains one more idempotent step,
      mirroring `_warm_membership_timeline`'s exact contract (own session, non-fatal, logged):
      compute + persist `coverage_snapshot` for the current stamp only if no row exists yet — the
      boot-time safety net for a not-yet-ingested-once database. It runs strictly AFTER `yield` (the
      existing pattern); boot's own synchronous path gains no new compute.
- [ ] `GET /api/data` (`apps/backend/app/api/data.py::data_overview`) reads the persisted
      `coverage_snapshot` row for the resolved `(asof_key, dataset_version)` key instead of calling
      `compute_coverage` live. A genuinely missing row (e.g., before the boot safety net above has
      run) serves an honest "not yet computed" partial coverage state — never a live whole-table
      compute on this request path, never a blank/500 response.
- [ ] `scripts/start-backend.sh`: apply `ulimit -v` sourced from `config.server.memory_cap_mb`,
      export `MALLOC_ARENA_MAX` sourced from `config.server.malloc_arena_max`, and redirect uvicorn's
      output to a persistent logfile at a path documented in the dev handoff — closing exactly the
      gap goal.md's binding note names ("Launch scripts must actually enforce the declared
      `server.memory_cap_mb` / `malloc_arena_max`... and write a persistent backend logfile").
- [ ] `reports/perf-budgets.md`: append one new dated section measuring cold `GET /api/data`
      post-fix (real process restart, first request after), set against the pre-fix ~9.4–10.5 s /
      ~1.8 GB baseline already on file.

### Frontend
- [ ] `/data`'s existing run-detail rendering (`apps/frontend/app/data/page.tsx` —
      `BackfillBreakdown`/`LastRunSummary`/`RunHistoryPanel`) gains one additive read-only line
      naming which aggregates a completed `backfill`/`both`/`rebuild` run's finalize hook refreshed
      (omitted for `fetch`/`expand` runs, and for a not-yet-computed row, matching the existing
      breakdown's nullability treatment). No new page, panel, or nav entry.

### New user-facing capability
Operators can see, per completed backfill/rebuild run, exactly which downstream aggregates
(coverage, snapshot, membership timeline, market phase, research hot-keys) that run refreshed — and
every page reading those aggregates (`/data`, `/scanner-runs`, `/`, `/research/*`) now serves them
instantly, cold or warm, because they were computed once at ingest and persisted, never recomputed
on a page load.

### New information displayed
The `aggregates_refreshed` list on a completed backfill/rebuild run's detail (existing Run History /
last-run panels on `/data`).

### New user actions
None — no new buttons, forms, or controls; the only additive UI element is a read-only detail line.

### UI surface changes
The existing `/data` run-detail view (live job card, last-run summary, run-history rows) gains one
additive line. No new pages or panels.

### Product surface delta
`/data`, `/scanner-runs`, `/`, and `/research/*` continue to show the identical numbers they show
today, but a cold restart no longer pays a multi-second whole-table scan to render them, and the
`/data` job surface now honestly names which background aggregates a given run kept fresh.

### Blueprint conformance
Data Manager (`/data`) is the canonical home for the finalize-hook/coverage/run-detail work;
`/scanner-runs`, `/` (Dashboard), and `/research/*` are pre-existing homes being re-verified, not new
surfaces. No nav change.

### Data-contract additions
- **`coverage_snapshot` table** — fields `id: int (PK)`, `asof_key: str` (indexed; the resolved as-of
  ISO cutoff, same value `_coverage_cache_key` already computes), `dataset_version: str` (the same
  narrow membership/bars-manifest stamp `_membership_dataset_version` already produces), `payload_json:
  str` (the serialized `_compute_coverage_uncached(...)` dict, byte-identical to a fresh compute),
  `computed_at: datetime` (UTC, when this row was last (re)computed). Unique on `(asof_key,
  dataset_version)`. Computed by `app.engine.data_manager` (the ingest finalize hook above + the
  warm-up-thread safety net); served only by `GET /api/data`. To be registered in `blueprint.md`.
- **`aggregates_refreshed: list[str]`** (subset of `["latest_snapshot", "coverage",
  "membership_timeline", "market_phase", "research_hot_keys"]`, `null` for kinds that don't apply) on
  the existing persisted run record — computed by `app.engine.data_manager`'s `_do_backfill`/
  `_run_job` finalize (the SAME `_run_detail()`/`JobProgress` mechanism `calendar_days` etc. already
  use — no new DB column), served by the SAME two existing endpoints (`GET /api/data`'s `runs` list +
  `GET /api/data/jobs/{job_id}`'s live poll). To be registered in `blueprint.md`.

## OUT OF SCOPE

- Retiring `ensure_latest_snapshot`'s synchronous compute-if-missing branch at boot — dormant in this
  session (the current DB's latest date already has a snapshot, per iter-1's <2 s fast-boot
  evidence) and unverifiable against the offline seed (see Assumption ledger).
- Deleting the boot warm-up loop's cadence-snapshot/forward-returns bootstrap responsibility — only
  ADDING the coverage safety-net step to it, per Assumption ledger; full retirement is not required
  by any Must-have journey and risks regressing archived mcp-loop-era guarantees.
- Any change to `fetch`/`expand` kinds' finalize behavior — offline/zero-work in this environment
  (AG-9); no Must-have journey exercises a fetch that lands new bars this cycle.
- J-06 (measurement capstone) — goal.md's suggested build order sequences it after J-05; this
  iteration's cold-`/api/data` measurement is a preliminary section J-06 will fold into its formal
  cross-page budget pass, not that pass itself.
- Any change to J-01/J-03's shipped `dates_total`/breakdown/chunk fields — "Do not redo" per
  iteration-state.md.
- Wiring `config.server.limit_concurrency`/`timeout_keep_alive_seconds`/`graceful_timeout_seconds`
  into `scripts/start-backend.sh` — also declared-but-unenforced (see NOTES), but not named by
  goal.md's binding note; deferred unless TC-11 reveals it's actually needed.
- A new visible "coverage last refreshed at HH:MM" freshness indicator — `computed_at` is stored for
  bookkeeping/audit but rendering it is not required by any journey's acceptance text this iteration.

## DEFINITION OF DONE

- [ ] J-05 passes via browser-qa-agent — all 4 steps: a single unsnapshotted day's backfill serves
      its aggregates from storage immediately after; a cold restart-and-visit of `/data` shows no
      whole-table prefill; `GET /api/health` stays responsive throughout a heavy ingest job
- [ ] J-04 passes via browser-qa-agent on its remaining acceptance: the persistent logfile contains
      boot events and ends abruptly after a simulated crash; "boot performs no whole-table loads and
      no synchronous snapshot computation" holds
- [ ] Required-still-passing journeys J-01, J-03 remain green (deterministic replay + LLM fallback)
- [ ] No anti-goal violation introduced (AG-3 byte-identity, AG-8 no unbounded load on a serving
      path, AG-9 no network call introduced by the new finalize-hook calls)
- [ ] Unit tests pass; no regressions (existing J-01/J-03 breakdown/chunking suites pass unedited)
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-2-dev.md`, documenting the
      logfile's path and a sample `aggregates_refreshed` value

## TESTING REQUIREMENTS

- Browser: J-05 (target, all 4 steps), J-04 (target, remaining acceptance bullets); J-01, J-03
  (required-still-passing regression, deterministic replay with LLM fallback)
- Unit/integration: extend `test_data_manager.py` (or a new focused test module) for the new table,
  the finalize hook, and the honesty gating on `aggregates_refreshed`; extend `test_warmup.py` for the
  boot safety-net step; extend `test_market_phase.py` / `test_data_manager_membership_cache.py` /
  the research-cache tests for the new ingest-warm call sites; a memory/perf test mirroring the
  existing Item H harness for the heavy-job memory budget; a script-level check of
  `scripts/start-backend.sh`'s `ulimit`/env/logfile behavior
- Error cases: a genuinely missing `coverage_snapshot` row serves an honest partial payload (never a
  500 or blank page); an interrupted/failed run never populates `aggregates_refreshed`; `fetch`/
  `expand` runs carry `aggregates_refreshed: null`

Test-first contract:

- TC-1: given a backend with no prior snapshot for 2026-05-15, when a `backfill` job for exactly
  `2026-05-15`→`2026-05-15` completes, then its finalize hook persists a `coverage_snapshot` row for
  the resulting `(asof_key, dataset_version)` and the run's persisted detail's `aggregates_refreshed`
  list is non-empty.
- TC-2: given the same completed 2026-05-15 backfill, when `/scanner-runs` is loaded immediately
  after, then a row for date `2026-05-15` is present in the run list.
- TC-3: given the same completed backfill, when the operator opens the `2026-05-15` row's
  leaderboard, then a non-empty table of stored `ScannerResult` rows for that date renders.
- TC-4: given the same completed backfill, when the market-phase-serving path is queried for as-of
  `2026-05-15` immediately after (no intervening request), then the response is served from an
  existing `MarketPhaseCache` row, verified by a compute-call-count assertion showing
  `compute_market_phase` executed exactly once — during the finalize hook, not during this request.
- TC-5: given the same completed backfill, when the persisted run record is read via `GET
  /api/data`'s `runs` list, then its `aggregates_refreshed` field lists exactly the aggregates the
  finalize hook refreshed, matching per-aggregate compute-call counts taken during the run.
- TC-6: given the `coverage_snapshot` row from TC-1 exists, when the backend is restarted (kill +
  fresh `scripts/start-backend.sh`) and `/data` is visited cold (first request post-restart), then
  the coverage block in the `GET /api/data` response is byte-identical to the pre-restart payload
  and zero calls to `prefilled_bar_cache`/`_compute_coverage_uncached` occur during that request
  (call-count assertion).
- TC-7: given the same cold restart-and-visit sequence as TC-6, when `GET /api/data`'s wall time is
  measured (`curl -w '%{time_total}'` or equivalent), then it completes in <= 2.0 seconds, recorded
  as a new row in `reports/perf-budgets.md`.
- TC-8: given a `coverage_snapshot` row exists for a given `(asof_key, dataset_version)`, when its
  `payload_json` is compared field-by-field against a direct fresh call to
  `_compute_coverage_uncached` for the same session state, then every field is byte-identical (AG-3).
- TC-9: given a database with zero `coverage_snapshot` rows for the current `(asof_key,
  dataset_version)` (a simulated pre-ingest state), when `GET /api/data` is called, then the
  response returns HTTP 200 with the coverage block carrying an honest "not yet computed" sentinel
  (never a blank page or 500) and zero whole-table prefill calls occur on that request.
- TC-10: given that same zero-row state, when the background warm-up thread
  (`warmup.py::_run_warmup`) completes its post-boot pass, then exactly one `coverage_snapshot` row
  now exists for the current stamp, computed strictly after `yield` (verified by comparing the
  first-`/api/health`-200 timestamp against the warm-up thread's coverage-warm completion timestamp).
- TC-11: given a heavy `backfill`/`rebuild` job is running, when `GET /api/health` is polled at
  <= 250 ms intervals for the job's full duration, then every poll returns HTTP 200 within 1 second,
  with zero timeouts or non-200 responses.
- TC-12: given the same heavy job as TC-11, when peak `VmSize`/`VmPeak` is sampled from
  `/proc/<pid>/status` for the job's duration, then it stays under the committed 6144 MB `ulimit -v`
  cap with the existing Item H margin (`reports/perf-budgets.md`), unregressed by the new
  finalize-hook calls.
- TC-13: given a backfill job's process is killed (simulated crash) after its date-loop but before
  its finalize hook's aggregate-refresh step completes, when the boot orphan sweep marks that job's
  run record `interrupted`, then the persisted record's `aggregates_refreshed` is empty/null — never
  a fabricated list of refreshed names (mirrors the existing `calendar_days` gating; AG-3).
- TC-14: given a completed run whose kind is `fetch` or `expand`, when its persisted detail is read,
  then `aggregates_refreshed` is `null` (matching the existing `dates_total`/`calendar_days`
  nullability convention for non-applicable kinds).
- TC-15: given the backend is started via `scripts/start-backend.sh`, when the process's resource
  limits and environment are inspected (`getrlimit(RLIMIT_AS)` via `/proc/<pid>/status` and
  `/proc/<pid>/environ`), then `RLIMIT_AS` reflects `config.server.memory_cap_mb` (6144 MB) and
  `MALLOC_ARENA_MAX=2` is present in the process environment.
- TC-16: given the backend has completed boot via `scripts/start-backend.sh`, when the documented
  persistent logfile path (named in the dev handoff) is read, then it contains the boot sequence's
  log lines (config load, table creation, orphan sweep, readiness-ready).
- TC-17: given a running backend started via `scripts/start-backend.sh` is killed (SIGKILL,
  simulated crash), when the persistent logfile is read afterward, then it ends abruptly after the
  last boot/serving line with no clean-shutdown entry.
- TC-18: given the existing J-01/J-03 backfill breakdown and chunking unit tests
  (`test_data_manager.py`'s `dates_total`/`calendar_days`/`non_trading_days`/`already_snapshotted`/
  `error_other` invariant tests and the `chunk_index`/`chunk_total` chunking tests), when the full
  suite runs after this iteration's finalize-hook addition, then every previously-passing assertion
  still passes unedited.
- TC-19: given the new finalize-hook aggregate-refresh calls execute during a backfill/rebuild
  completion, when outbound network activity is monitored for that process (e.g., a test fixture
  that fails on any socket/`requests`/`httpx` call), then zero external network calls occur (AG-9).
- TC-20: given a completed backfill run with a non-empty `aggregates_refreshed` list, when the
  operator expands that run's detail on `/data`, then the rendered detail includes a line naming
  each refreshed aggregate.
- TC-21: given the iteration completes, when `docs/handoffs/goal-ops-hardening-iter-2-dev.md` is
  read, then it documents the persistent logfile's path and a sample `aggregates_refreshed` value
  from a real run.

## NOTES

- **Lessons applied:** iter-0's lesson that `reports/perf-budgets.md`/`config.yaml` prose claiming
  `scripts/start-backend.sh` already enforces `memory_cap_mb`/`malloc_arena_max` is false — this
  iteration re-confirmed it by a direct script read (no `ulimit`, no env export, no logfile
  redirect anywhere in the file). Do not treat that prose as evidence; build the enforcement from
  scratch. Iter-1's lesson that a new persisted/served field's honesty risk lives in the
  not-yet-computed/interrupted edge, not the happy path — applied directly to
  `aggregates_refreshed` (TC-13/TC-14), gated the same way `_breakdown_computed` already gates
  `calendar_days` in `_run_detail()`.
- **Additional drift found (not in scope):** `config.yaml`'s `server:` section also declares
  `limit_concurrency`/`timeout_keep_alive_seconds`/`graceful_timeout_seconds` with a comment block
  claiming `start-backend.sh` "reads every value from here via the venv python" — confirmed also
  false by the same direct script read. Not fixed this iteration (goal.md's binding note names only
  `memory_cap_mb`/`malloc_arena_max`/logfile) — flagged for a future iteration if TC-11 ever
  reveals health responsiveness actually needs it.
- Two assumption-ledger entries were logged this iteration (`runs/goal-session-ops-hardening/state/
  assumptions.md`, iter-2 — goal-decomposer): (1) scoping J-05 to what its own 4 acceptance steps
  literally exercise rather than the full "four offenders" retirement, and (2) scoping the
  launch-script fix to exactly goal.md's three named items rather than the full `server:` config
  section.
- `blueprint.md` updated this iteration: removed the `[TARGET, iter-1 building]` tag from the
  now-passing "Job history & per-date exclusion reasons" and "Backfill run-summary contract" rows
  (marking their iter-1 fields built), added the new `aggregates_refreshed` field to the latter, and
  retagged "Coverage payload" and "Membership timeline / research hot-key caches" as `[TARGET,
  iter-2 building]` with mechanisms matching this spec exactly.
- No blueprint nav-skeleton change — no `blueprint.reapproval-requested` file written.
