# goal-ops-hardening-iter-2 Execution Plan

Session `ops-hardening`, iteration 2, depth **full**. Target journeys: **J-05** (aggregates precomputed
at ingest) + **J-04** remaining acceptance (persistent logfile + enforced memory cap). Required-still-
passing: **J-01, J-03** (do not touch their shipped fields — only add alongside them). This is exactly
the scope the iter-1 evaluator recommended next; no drift from `docs/goal.md`.

## What to Build

- A new persisted `coverage_snapshot` table (following the `MarketPhaseCache`/`EventStudyCache`/
  `MembershipTimelineCache` convention already in `models.py`) that serves `GET /api/data`'s coverage
  block — replacing the request-path call to `compute_coverage`/`_compute_coverage_uncached` (today's
  whole-table-prefill OOM source, only in-process cached, lost on restart).
- An ingest **finalize hook** at the end of a successful `backfill`/`both`/`rebuild` job that: persists a
  fresh `coverage_snapshot` row, warms `MarketPhaseCache` for each snapshot date the run newly created,
  warms `MembershipTimelineCache`, and warms a small default set of `EventStudyCache` hot keys — reusing
  each cache's existing compute function, never a second derivation.
- A new `aggregates_refreshed: list[str] | null` field on the persisted run record, gated on the same
  "actually computed" pattern iter-1 built for `calendar_days` (null until the finalize hook has actually
  run; never fabricated on an interrupted/failed row).
- A warm-up-thread safety net (`_run_warmup`) that computes+persists `coverage_snapshot` for the current
  stamp if no row exists yet — for a not-yet-ingested-once DB. Runs strictly after `yield`; boot's own
  synchronous path gains no new compute.
- `scripts/start-backend.sh`: apply `ulimit -v` from `config.server.memory_cap_mb`, export
  `MALLOC_ARENA_MAX` from `config.server.malloc_arena_max`, redirect uvicorn output to a persistent
  logfile — closing the gap iter-0 confirmed is currently false (the script today sets no ulimit, no env
  var, no logfile; verified by direct read, 34 lines, no such logic anywhere).
- `reports/perf-budgets.md`: one new dated section measuring cold `GET /api/data` post-fix against the
  existing ~9.4-10.5s / ~1.8GB baseline already on file.
- Frontend: one additive read-only line on `/data`'s existing run-detail views naming which aggregates a
  completed run refreshed. No new page, panel, nav entry, button, or form.

**Explicitly out of scope this iteration** (carried from the phase spec, consistent with goal.md — no
drift): retiring `ensure_latest_snapshot`'s synchronous compute-if-missing boot branch; deleting the boot
warm-up loop's cadence/forward-returns bootstrap (only ADD the coverage safety-net step to it); any
`fetch`/`expand`-kind finalize behavior change; J-06's formal cross-page budget pass (this iteration's
cold-`/api/data` measurement is a preliminary section only); any change to J-01/J-03's shipped
`dates_total`/breakdown/chunk fields; wiring `limit_concurrency`/`timeout_keep_alive_seconds`/
`graceful_timeout_seconds` into the start script; a visible "coverage last refreshed at HH:MM" indicator.

## Agents Required

- developer: yes -- implements both stacks in one dispatch (matches iter-1's pattern of one dev pass
  producing both a `-dev.md` and a `-frontend.md` handoff). Backend is the large half of this iteration
  (new table, finalize hook, warm-up safety net, API read-path swap, launch script); frontend is a single
  additive line reusing an existing component.
  - backend-data: yes -- `coverage_snapshot` table, finalize hook, `aggregates_refreshed` field,
    warm-up safety net, `GET /api/data` read-path swap, `start-backend.sh` enforcement, perf-budgets entry.
  - frontend-ux: yes -- one additive line in `/data`'s run-detail rendering; no new UI surface.

## Frontend Present
yes

## Files to Create/Modify

Backend:
- `apps/backend/app/models.py` -- new `CoverageSnapshot(SQLModel, table=True)`: STANDALONE
  `create_all`-managed table (no Alembic migration needed — this repo has no `alembic/` dir; new
  standalone tables are picked up by `create_db_and_tables`'s `SQLModel.metadata.create_all`, same as the
  three precedent caches). Fields: `id: Optional[int]` (PK), `asof_key: str` (indexed), `dataset_version:
  str`, `payload_json: str`, `computed_at: datetime`. `UniqueConstraint("asof_key", "dataset_version")`.
- `apps/backend/app/engine/data_manager.py` -- the largest file touched:
  - `JobProgress`: add `aggregates_refreshed: list[str] = field(default_factory=list)`. Also add a way to
    know *which dates* a run newly created (today only a count, `snapshots_created`, is tracked) — e.g. a
    `new_snapshot_dates: list[date_cls] = field(default_factory=list)` populated inside `_persist()`
    (~line 2618) exactly where it already branches on `existed_before` — needed so the finalize hook knows
    which as-ofs to warm in `MarketPhaseCache` (the spec requires "for each newly-created snapshot date").
  - A new finalize-hook function (e.g. `_refresh_ingest_aggregates(session, cfg, prog)`) that: computes +
    upserts a `CoverageSnapshot` row for the current `(asof_key, dataset_version)` (reuse
    `_compute_coverage_uncached`, upsert pattern mirrors `market_phase_cached`'s prune-stale-then-insert);
    calls `market_phase_cached` for each `prog.new_snapshot_dates`; calls the existing
    `membership_timeline_cached` (already imported/used at line 562 for the coverage derivation — reuse,
    don't re-derive); calls `research.event_study_cached` for a small default set of hot keys. Returns the
    list of category strings actually refreshed (subset of `["latest_snapshot", "coverage",
    "membership_timeline", "market_phase", "research_hot_keys"]`) for `prog.aggregates_refreshed`.
  - `_run_job` (~line 3171-3434): call the new finalize hook once, gated on `prog.kind` being
    backfill/both/rebuild-like AND the job ending in `ok`/`partial` (not `failed`/`resumable`) — insert
    right after `prog.status = _final_status(prog)` succeeds inside the `try` block, **before** the
    `finally` block's `_finalize_run_record(eng, cfg, prog)` call, so the freshly-populated
    `prog.aggregates_refreshed` is captured in the SAME `_run_detail()` JSON persisted at finalize. Wrap
    in its own try/except (log + continue, never raise) mirroring `_warm_membership_timeline`'s non-fatal
    contract in `warmup.py` — an aggregate-refresh failure must never flip an otherwise-successful ingest
    job to `failed`.
  - **Crash-safety note (de-risks TC-13):** `sweep_orphaned_runs` never touches a row's `message` JSON —
    it only flips `status`/`finished_at`. A row's `message` is written once at job start
    (`_create_run_record`, when `prog.aggregates_refreshed` is still empty) and only overwritten by
    `_finalize_run_record` on a clean finalize. So a process killed between the date-loop and the finalize
    hook already leaves `aggregates_refreshed` at its empty default with **zero new code** in the sweep —
    same mechanism that already protects `calendar_days`. Do not add special-casing in
    `sweep_orphaned_runs`; it is not in scope and not needed.
  - `_run_detail()` (~line 3004): add `"aggregates_refreshed": prog.aggregates_refreshed if
    (_breakdown_computed and prog.aggregates_refreshed) else None` — matching the existing
    `_breakdown_computed` gate so a not-yet-computed or interrupted row serves `null`, and a fetch/expand
    row (never backfill-like) also serves `null`.
- `apps/backend/app/api/data.py` -- `data_overview` (line 97-148): replace the
  `data_manager.compute_coverage(session, cfg, as_of=resolved_asof)` call with a read of the persisted
  `CoverageSnapshot` row for the resolved `(asof_key, dataset_version)` key. A genuinely missing row (pre-
  ingest, or before the warm-up safety net has run) must still return HTTP 200 with an honest partial/"not
  yet computed" coverage payload — never a 500, never a live whole-table compute on this path.
- `apps/backend/app/engine/warmup.py` -- `_run_warmup` (line 122): add one more idempotent step after
  `_warm_membership_timeline` (mirror its exact contract: own session, non-fatal try/except, logged) that
  computes+persists a `CoverageSnapshot` row for the current stamp **only if no row exists yet** — the
  boot-time safety net for a not-yet-ingested-once DB. Already runs after `yield` since this whole function
  executes in the background daemon thread `start_warmup` spawns.
- `scripts/start-backend.sh` (currently 34 lines, no ulimit/env/logfile logic at all — confirmed by direct
  read) -- add, before the final `exec uvicorn ...` line: (1) read `memory_cap_mb`/`malloc_arena_max` from
  `config.yaml` via the venv Python (`app.config.get_config()` — no existing bash-side config reader
  exists, so this is new plumbing) and `ulimit -v $((memory_cap_mb * 1024))`; (2) `export
  MALLOC_ARENA_MAX=<value>`; (3) redirect uvicorn's stdout/stderr to a persistent logfile path (pick a
  path under a repo-relative `logs/` dir or similar; document the exact path in the dev handoff — J-04's
  acceptance requires the crash test to read this file afterward). Keep the existing port-offset/CORS/
  migration logic unchanged.
- `reports/perf-budgets.md` -- append one new dated section: cold `GET /api/data` wall time post-fix
  (real process restart, first request after), zero-prefill-call evidence, set against the pre-fix
  baseline already in the file.

Frontend:
- `apps/frontend/app/data/page.tsx` -- extend the existing shared `BackfillBreakdown` component
  (line ~2513, already the single reused renderer at 3 call sites: `LastRunSummary` ~2568,
  `JobProgressPanel`'s backfill section ~2723, `RunHistoryPanel` ~3474) with one new optional prop
  (e.g. `aggregatesRefreshed?: string[] | null`) rendering one additional muted inline line when non-
  null/non-empty — omit entirely otherwise (matching the component's existing all-null-renders-nothing
  convention). Thread the new field through from all 3 call sites. Do **not** build a new component —
  the plan's Visual Requirements below depend on reusing this exact one.
- `apps/frontend/lib/api.ts` -- `DataRun`/`DataJob` interfaces gain `aggregates_refreshed: string[] |
  null` (optional, matching the existing `calendar_days?`-style kind-specific-extension convention).

Tests (extend existing files per the phase spec's Testing Requirements; no new test infra needed):
- `apps/backend/tests/test_data_manager.py` -- `coverage_snapshot` creation/upsert + byte-identity vs a
  fresh `_compute_coverage_uncached` call; `aggregates_refreshed` honesty gating (empty on
  interrupted/failed, null on fetch/expand, non-empty + matching compute-call-counts on a clean backfill);
  re-run every existing `dates_total`/`calendar_days`/chunking assertion unedited (regression, J-01/J-03).
- `apps/backend/tests/test_api_data.py` -- cold-restart byte-identical coverage + zero
  `prefilled_bar_cache`/`_compute_coverage_uncached` calls on that request; a zero-row state serves HTTP
  200 with an honest partial payload, never 500/blank.
- `apps/backend/tests/test_warmup.py` -- the boot safety-net step creates exactly one `coverage_snapshot`
  row when none exists, is a no-op when one already does, and runs strictly after readiness goes ready.
- `apps/backend/tests/test_market_phase.py` -- a compute-call-count assertion (e.g. `mock.patch(...,
  wraps=compute_market_phase)`) showing it executes exactly once per newly-created date, during the
  finalize hook, not during a subsequent read.
- `apps/backend/tests/test_data_manager_membership_cache.py` -- the ingest-warm call site (finalize hook
  calls `membership_timeline_cached`, byte-identical payload).
- A research-cache test (extend an existing research test file, or add to `test_data_manager.py`) for the
  `event_study_cached` ingest-warm call site.
- Memory + responsiveness: mirror the existing "Item H" manual-measurement harness style (this repo has
  no pytest-level VmSize/VmPeak test today — `reports/perf-budgets.md`'s own measured sections are the
  precedent) for the heavy-job memory budget and `GET /api/health` responsiveness during a heavy job;
  record results in the dev handoff and the new perf-budgets.md section, not as a new pytest fixture,
  unless the developer judges a lightweight `/proc/<pid>/status`-sampling pytest is cheap to add.
- A script-level check of `scripts/start-backend.sh`'s `ulimit`/env/logfile behavior (subprocess-level:
  start it, inspect `/proc/<pid>/status` and `/proc/<pid>/environ`, read the logfile, kill it, re-read the
  logfile for the abrupt-end signature).

Docs:
- `docs/handoffs/goal-ops-hardening-iter-2-dev.md` -- required; must document the logfile's exact path
  and a sample `aggregates_refreshed` value from a real run (DoD requirement).
- `docs/handoffs/goal-ops-hardening-iter-2-frontend.md` -- matching iter-1's convention for the frontend
  half of the same dispatch.

## UI Evolution

- New user-facing capability: operators can see, per completed backfill/rebuild run, exactly which
  downstream aggregates (coverage, snapshot, membership timeline, market phase, research hot-keys) that
  run refreshed — while every reader page (`/data`, `/scanner-runs`, `/`, `/research/*`) continues to show
  identical numbers to today, now served instantly from storage instead of recomputed on request.
- New information displayed: the `aggregates_refreshed` list on a completed backfill/both/rebuild run's
  detail — nothing displayed for `fetch`/`expand` runs or a not-yet-computed row (matches the existing
  breakdown fields' nullability treatment exactly).
- New user actions: none. No new buttons, forms, or controls — the only additive element is a read-only
  detail line.
- UI surface changes: the existing `/data` run-detail view (live job card, last-run summary, run-history
  rows) gains one additive line each. No new pages or panels.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the existing `BackfillBreakdown` shared component verbatim (add a prop, don't
  fork it) — preserves the single-source-of-truth rendering across all 3 call sites the same way the
  existing 4 breakdown fields already do. No `Badge`/`Card`/`Dialog` or other component-library element is
  needed for this change.
- Layout: no layout change. Same `Card`/`PanelTitle` structure for the Job progress panel, same `<table>`
  structure for Run history, same reduced-view `LastRunSummary` card.
- Key visual effects: none new. Match the existing calm/muted `text-xs text-text-faint` inline-text
  treatment already used for the breakdown counts — never a new color, badge, or emphasis.
- States to handle: omit the line entirely (render nothing, not an empty placeholder) when
  `aggregates_refreshed` is null — covers fetch/expand kinds, a not-yet-computed running/interrupted row,
  and (per TC-13) an interrupted backfill row. Render the joined list once genuinely populated.

## Key Test Scenarios

(Condensed from the phase spec's 21 test-first contracts — see
`docs/phases/goal-ops-hardening-iter-2.md` TC-1..TC-21 for the full binding list the developer/reviewer/QA
should verify against.)

- A `backfill` for one unsnapshotted day (e.g. 2026-05-15) persists a `coverage_snapshot` row and a
  non-empty `aggregates_refreshed`; `/scanner-runs` and its leaderboard immediately reflect the new date
  from storage (TC-1/2/3).
- The market-phase-serving path for that as-of is served from `MarketPhaseCache` with `compute_market_phase`
  proven to execute exactly once (during the finalize hook, not during the subsequent read) (TC-4).
- `aggregates_refreshed` on the persisted run record matches exactly what was refreshed, verified against
  per-aggregate compute-call counts (TC-5).
- A cold restart + `/data` visit serves byte-identical coverage from storage with zero
  `prefilled_bar_cache`/`_compute_coverage_uncached` calls, in <= 2.0s (TC-6/7/8).
- A zero-`coverage_snapshot`-row state still serves HTTP 200 with an honest "not yet computed" partial
  payload — never 500/blank — and the background warm-up thread fills it exactly once, strictly after
  `yield` (TC-9/10).
- `GET /api/health` stays responsive (every poll <=1s, zero timeouts) throughout a heavy backfill/rebuild,
  and process memory stays under the committed `ulimit -v` cap with the existing Item H margin (TC-11/12).
- An interrupted (simulated-crash) backfill row never carries a fabricated `aggregates_refreshed`; a
  `fetch`/`expand` row always carries `null` (TC-13/14).
- Every existing J-01/J-03 breakdown/chunking unit test still passes unedited (TC-18) — the required-
  still-passing regression.
- No outbound network call occurs during the new finalize-hook calls (AG-9) (TC-19).
- `scripts/start-backend.sh`-launched process shows `RLIMIT_AS` reflecting `memory_cap_mb` and
  `MALLOC_ARENA_MAX` in its environment; its logfile contains the boot sequence and, after a simulated
  SIGKILL, ends abruptly with no clean-shutdown entry (TC-15/16/17).
- The `/data` UI renders the new `aggregates_refreshed` line for a completed run with a non-empty list
  (TC-20); the dev handoff documents the logfile path + a sample value from a real run (TC-21).
