# goal-market-compass-iter-17 Execution Plan

## Alignment check

Faithful match to `docs/goal.md` J-11's "OWNER RULING — J-11 maintenance-boundary lifecycle
AUTHORIZED" (owner, 2026-08-25, `docs/goal.md:1519-1638`), verified by reading that ruling directly.
Its AUTHORIZATION MATRIX authorizes the lifecycle's *code* (create/activate/deactivate) while leaving
`J-11 Stage D execution` **NOT AUTHORIZED**; its own "BLOCKER ON RECORD" paragraph pre-emptively
requires the live-arm sub-step (requirement 4's invocation + all of requirement 7) to return `STALLED`
because `maintenance_boundaries` does not exist on the live DB and creating it is explicitly "NOT
authorized" — this phase spec's OUT OF SCOPE list matches that exactly. No drift found. This iteration
builds directly on iter-16 (which built the guard, `MaintenanceBoundary` model, and wired the one
`warmup.py` call site, but left the AG-8 unbounded-query finding (audit B7) unfixed and the
decision-impact trace's `volume_override` gap (audit B1) uncorrected) and iter-15 (whose
`j11-avb-provider-fetch-evidence.json` the AVB rider reuses unchanged).

**Ground-truth check against the spec's own text:** the spec's intro says
`test_j11_preboot_guard.py` "currently 17 tests" — the file actually has **19** (verified by direct
grep). Treat the repo as ground truth, not the spec's count; this does not change scope, only the
starting point.

## What to Build

**1. AG-8 fix — bound the unbounded load in `evaluate_boundary_for_date`**
(`apps/backend/app/engine/j11_preboot_guard.py`, currently `rows =
session.exec(select(MaintenanceBoundary)).all()`, flagged by iter-16 audit finding B7). Replace with a
query that is both (a) filtered to the only rows that can possibly matter — active-or-ambiguous, never
`active == True` alone, because standard SQL three-valued comparison silently drops `active IS NULL`
rows (the exact named trap) — and (b) deterministically bounded (e.g. a small `.limit(N)` with a
module-level `N`, fail-closed/ambiguous if the fetch hits the cap), per the ruling's "apply a
deterministic finite bound ... and fail closed if the bound is exceeded." No new `config.yaml` entry is
required for this cap: no `j11_*.py` module is in `test_no_magic_numbers.CALC_FILES` (verified) — six
prior J-11 iterations have used inline module constants (e.g. `j11_avb_correction._RATIO_RELATIVE_
TOLERANCE`) without a config entry; follow that precedent, not the compass-feature config regime.
- **Known crux #1 (the NULL-active row).** `MaintenanceBoundary.active` is a non-optional SQLModel
  field — audit finding B6 confirmed a normal ORM insert of `active=NULL` raises `IntegrityError`. TC-4's
  fixture therefore almost certainly needs a **raw SQL insert** (bypassing the ORM's own validation) to
  construct a row with SQL `NULL` in `active` at all. Confirm this before assuming the scenario is even
  reachable through the model layer, and construct the fixture accordingly.
- **Known crux #2 (table-absent, not just table-empty) — likely genuinely new gap.** The live DB has
  **zero** tables named `maintenance_boundaries` (confirmed via read-only `sqlite_master` count = 0, not
  merely zero rows). `select(MaintenanceBoundary)` against a DB where the table does not exist at all
  raises `sqlalchemy.exc.OperationalError: no such table`, not an empty list. All 19 existing tests run
  against fixture DBs where `create_db_and_tables()` already ran, so none of them exercise this. TC-11
  (see below) requires `evaluate_boundary_for_date` to run against the **live, table-absent** DB and
  return `blocked: False` cleanly — so the bounded-query rewrite must explicitly treat "table does not
  exist" the same as "table exists, zero rows," not let the exception propagate. Add this as an explicit
  test case alongside the owner's 9 named ones (it is not separately named in the ruling, but TC-11
  cannot pass without it).

**2. Arm entrypoint** — new `apps/backend/scripts/run_j11_*.py` (naming: developer's call, following
the established convention — e.g. `run_j11_maintenance_boundary_arm.py`). Thin CLI wrapping the
already-existing `register_j11_incident_boundary` (sources dates from `j11_maintenance.INCIDENT_DATES`
only — never re-typed). Idempotent (TC-7), prints the boundary row before/after, writes only to
`maintenance_boundaries` (TC-8). Mirror `run_j11_stage_c_bounded_clear.py`'s established idiom
(explicit flag gate, obvious mutation, no silent defaults) even though this script is **not invoked
against `trendora.db` this iteration** — fixture/temp-DB invocation only, in tests.

**3. Disarm entrypoint** — companion script wrapping the already-existing `clear_boundary(session,
name=...)`. Must take the boundary **name** as an explicit, required argument (never a hardcoded
target) so TC-9's two-boundary scenario (disarm one by name, the other's row is untouched in every
field) is naturally satisfied by the underlying function, not by test-only scoping. **Not invoked
against any live-armed state this iteration** (nothing is live-armed yet).

**4. Test suite extension** (`apps/backend/tests/test_j11_preboot_guard.py`, 19 → target ~29-32).
Owner's 9 lettered cases (A)-(I) mapped against current coverage (verified by reading existing test
names):
- **Already covered — do not duplicate:** (A) empty/unarmed no-false-protection
  (`test_tc25_no_boundary_registered_is_a_true_noop`); (C) non-incident date unaffected
  (`test_active_boundary_does_not_block_a_date_outside_its_own_set`); (G) boot/warmup cannot reach
  `run_scan` while blocked (`test_tc23_ensure_latest_snapshot_skips_write_and_returns_none_when_
  blocked` + siblings).
- **Net-new or must-extend:** (B) — existing single-date block test does not loop all 11
  `INCIDENT_DATES` individually (TC-2 requires it); (D) arm idempotency — TC-6/TC-7, needs the new
  script; (E) ambiguous/duplicate-active fails closed — existing malformed-JSON tests
  (`test_tc27_fails_closed_on_*`) don't cover the NULL-active or many-irrelevant-rows shapes (TC-4,
  TC-5 — the real AG-8 test); (F) bounded query doesn't require the full-table load — TC-5, must assert
  the query itself is bounded (row-fetch count or emitted SQL/`LIMIT` clause), not only the resulting
  boolean; (H) no forbidden writes while arming — TC-8, needs the new script; (I) disarm scoped
  correctly — TC-9/TC-10, needs the new script.
- Use a **new naming scheme for these tests** (e.g. `test_owner_case_a_...` or `test_tc{1..14}_...`
  keyed to *this iteration's own* TC numbers) rather than continuing the file's existing `tc23`-`tc30`
  labels, which are a different (iter-16-internal) numbering space — reusing "tc4"/"tc5" etc. against
  two different meanings in the same file is a readability trap.
- Script-level tests for arm/disarm: new file (e.g. `test_j11_preboot_guard_cli_scripts.py`), needs
  BOTH real fixture-DB execution (TC-6 through TC-10 require actually-created rows, not just mocked
  control flow) and `unittest.mock`-based flag/refusal tests mirroring `test_j11_stage_c_cli_script.py`.

**5. Live read-only verification** (new evidence artifact under `runs/goal-market-compass-iter-17/`,
e.g. `j11-iter17-live-preboot-guard-verification.json`). Open `apps/backend/data/trendora.db` with
`mode=ro` + `PRAGMA query_only=ON` (reuse the `_read_only_engine` idiom already in
`run_j11_iter16_stage_d_readiness.py`). Query `SELECT count(*) FROM sqlite_master WHERE type='table'
AND name='maintenance_boundaries'` (expect `0`) and call the real, unmodified
`evaluate_boundary_for_date` for `2026-08-12` (expect `blocked: False` — depends on Known crux #2
above being fixed). Persist both results (TC-11).

**6. Zero-live-writes proof.** Capture `trendora.db` mtime + size + `-wal` size at true start and true
end (e.g. `j11-iter17-readiness-db-file-true-start.json` / `-true-end.json`, mirroring iter-16's
naming). The spec's own NOTES section already gives the decomposer's independently-captured baseline
(2026-08-25, read-only): mtime `1787670395`, size `8365871104`, `-wal` `0`, table count `24`,
`maintenance_boundaries` count `0`. The true-start capture is expected to reproduce these exactly; if
it does not, that means something wrote to the live DB between decomposition and now, outside this
iteration — report it honestly rather than silently proceeding. True-end must match true-start exactly
(TC-12).

**7. AVB Stage D rider.** New thin read-only driver script (copy/adapt
`run_j11_iter16_stage_d_readiness.py`; do not edit it) that calls the **already-existing**
`trace_universe_resolver_impact` and `trace_scoring_and_selection_impact`
(`app/engine/j11_avb_diagnostic.py`) **with `volume_override`** built from iteration-15's committed
`runs/goal-market-compass-iter-15/j11-avb-provider-fetch-evidence.json` — both functions have accepted
an optional `volume_override: Optional[dict] = None` parameter since iteration 15 (Goal 5); iter-16
simply never passed it (audit finding B1). This is a small, mechanical rider, not new engine logic.
Persist the corrected artifact as a **new iter-17 file** (e.g.
`runs/goal-market-compass-iter-17/j11-iter17-stage-d-readiness.json`) — iteration 16's
`j11-stage-d-readiness.json` must stay byte-unedited (hash-check it before/after). Expect
classification `AVB-A`, `READY: YES` unchanged, both dates' A/B dollar-volume ratio within the
calibration window's existing relative tolerance (not landing exactly on `bridge_factor` — that exact
match was iteration 7's red flag, now a regression trap in its own right per J-10's lineage) (TC-13).
Does **not** re-invoke `run_j11_avb_correction.py` (already spent, one-time).

**8. Dev handoff status lines** (`docs/handoffs/goal-market-compass-iter-17-dev.md`) — render exactly,
verbatim (TC-14):
```
J-11 STAGE D READY: YES
J-11 STAGE D AUTHORIZED: NO
J-11 MAINTENANCE BOUNDARY: NOT ACTIVE
J-11 LIVE PRE-BOOT GUARD: NOT ARMED
```
plus naming the live-arm sub-step of the owner's requirements 4 and 7 as **blocked by the table's
absence** (STALLED, per the ruling's own stop condition) — never silently omitted, never silently
attempted. Also confirm and cite: this iteration's diff touches none of `apps/backend/app/api/*`,
`scoring.py`, `sectors.py`, or `compass.py` (so J-01/J-04/J-10 could not have moved — the
required-still-passing journeys are carried forward unverified-this-iteration, not re-proven).

## Guardrails (binding — restated from OUT OF SCOPE / maintenance isolation)

- **Maintenance isolation is ACTIVE.** Do not boot the backend, the frontend, browser QA, or the
  deterministic replay lane, at any point, for any reason — including "just to check." Every check in
  this plan is either a disposable/in-memory fixture test or a strictly read-only (`mode=ro` + `PRAGMA
  query_only=ON`) inspection of the live `trendora.db`. This binds the developer, reviewer, and QA
  stages alike — QA must not attempt to start services even though `Frontend Present: no` might
  otherwise invite a "boot backend, smoke the API" pattern for a backend-only phase; that pattern is
  explicitly forbidden here.
- **Creating `maintenance_boundaries` on the live DB is NOT authorized.** The live-arm sub-step
  (requirement 4's invocation) and all of requirement 7's live-write portions are expected to return
  `STALLED` with the blocker named — that is the correct, anticipated outcome, not a failure to fix.
  Do not create the table "because it's purely additive."
- No write of any kind to `daily_prices`, `scanner_runs`, `scanner_results`, `sector_scores`,
  `theme_scores`, `forward_returns`, `next_session_manifests`, `data_provider_runs`, or any table other
  than (in disposable fixtures only) `maintenance_boundaries`.
- No schema migration, ALTER, or table rewrite of any kind.
- No Stage D work — no `ScannerRun` creation, no `clear_snapshot_dates` call, no cache invalidation, no
  regeneration of the 11 incident dates, no Stage-D spec drafting.
- Never run the full backend suite; never two pytest processes concurrently; targeted files only
  (`pytest tests/test_j11_preboot_guard.py`, plus the new CLI-script test file and the Stage D rider's
  own test extension if any).
- `git status --porcelain` must stay clean on every prior `runs/goal-market-compass-iter-9/` through
  `-iter-16/` evidence directory before and after this iteration's test runs.

## Agents Required

- developer: yes -- backend-only implementation: the AG-8 bounded-query fix, the two new CLI
  entrypoints, the test suite extension (9 owner cases + the table-absent regression), the live
  read-only verification, the zero-write proof, the AVB rider script + artifact, and the dev handoff.
  One pass covers this; no design/review split needed beyond the standard pipeline.
- backend-data: yes -- every deliverable is backend/data-layer (`app/engine/`, `apps/backend/scripts/`,
  `apps/backend/tests/`) plus read-only evidence JSON under `runs/goal-market-compass-iter-17/`; the
  only live-DB interaction is strictly read-only.
- frontend-ux: no -- no frontend file is touched; maintenance isolation forbids any application-service,
  browser, or replay lane this iteration (see Guardrails).

## Frontend Present
no

## Files to Create/Modify

New:
- `apps/backend/scripts/run_j11_*_arm.py` -- committed, idempotent arm entrypoint (name developer's
  call, `run_j11_*.py` convention).
- `apps/backend/scripts/run_j11_*_disarm.py` -- companion disarm entrypoint, scoped by required
  `--name` argument.
- `apps/backend/scripts/run_j11_iter17_stage_d_readiness.py` (or similar) -- the AVB rider driver,
  adapted from `run_j11_iter16_stage_d_readiness.py` with `volume_override` wired through.
- `apps/backend/tests/test_j11_preboot_guard_cli_scripts.py` (or extend an existing CLI-script test
  file) -- arm/disarm idempotency, scoping, no-forbidden-writes tests (TC-6 through TC-10).
- `runs/goal-market-compass-iter-17/j11-iter17-live-preboot-guard-verification.json` -- TC-11 evidence.
- `runs/goal-market-compass-iter-17/j11-iter17-readiness-db-file-true-start.json` /
  `-true-end.json` -- TC-12 evidence.
- `runs/goal-market-compass-iter-17/j11-iter17-stage-d-readiness.json` -- TC-13 evidence (new file;
  iter-16's own artifact stays byte-unedited).

Modified:
- `apps/backend/app/engine/j11_preboot_guard.py` -- the AG-8 bounded-query rewrite in
  `evaluate_boundary_for_date` (Known crux #1 and #2 above); no other function's behavior changes.
- `apps/backend/tests/test_j11_preboot_guard.py` -- extended with the owner's net-new lettered cases
  (see breakdown above) and the table-absent regression case; all 19 existing tests stay green,
  unmodified in behavior.

Reused unchanged (do not reimplement):
- `j11_maintenance.INCIDENT_DATES`; `j11_preboot_guard.register_boundary` /
  `clear_boundary` / `register_j11_incident_boundary` / `J11_INCIDENT_BOUNDARY_NAME`;
  `j11_avb_diagnostic.trace_universe_resolver_impact` / `trace_scoring_and_selection_impact` (both
  already `volume_override`-capable) / `classify_local_convention_with_volume_evidence` / `classify_avb`
  / `load_j10_avb_evidence` / `fetch_avb_stored_series`; `j11_stage_d.capture_stage_d_preflight` /
  `compare_stage_d_preflight_to_certified` / `produce_stage_d_readiness_artifact` /
  `build_avb_correction_superseded_baseline`; the `_read_only_engine` (mode=ro + `PRAGMA
  query_only=ON`) idiom from `run_j11_iter16_stage_d_readiness.py`; the `--confirm`-gate CLI idiom from
  `run_j11_stage_c_bounded_clear.py`.

## Key Test Scenarios

Map 1:1 to the phase spec's TC-1 through TC-14 (already fully enumerated there with exact given/when/
then — not re-derived here). Priority order for the developer, cheapest-and-highest-signal first:
1. TC-4/TC-5 (the actual AG-8 fix + the NULL-active and table-absent traps) — the technical core of
   this iteration; get this right before the entrypoint scripts, since TC-11's live call depends on it.
2. TC-1/TC-2/TC-3 -- confirm already-passing coverage still holds after the query rewrite (regression
   guard on the rewrite itself), extend TC-2 to loop all 11 dates.
3. TC-6 through TC-10 -- arm/disarm entrypoints and their fixture-DB tests.
4. TC-11/TC-12 -- live read-only verification + zero-write proof (do this only after 1-3 are green;
   it is the one step touching the real `trendora.db`, even if only via `mode=ro` reads).
5. TC-13 -- AVB rider (independent of 1-4; can run in parallel/any time; zero shared state).
6. TC-14 -- dev handoff status lines, written last, after every artifact above exists to quote from.
