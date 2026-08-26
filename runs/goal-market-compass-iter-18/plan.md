# goal-market-compass-iter-18 Execution Plan

## Alignment check

Faithful match to `docs/goal.md`'s "OWNER RULING — J-11 exact maintenance-boundary table creation and
live arm AUTHORIZED" (owner, 2026-08-25, `docs/goal.md:1640-1748`), verified by reading that ruling
directly rather than trusting the phase spec's paraphrase alone. The ruling's ten numbered requirements
map onto the spec's IN SCOPE/OUT OF SCOPE exactly: requirements 1-2 (exact single-table creation from
`MaintenanceBoundary.__table__`, never `create_db_and_tables()`/full `metadata.create_all()`) →
Goal 2 below; requirement 3 (reuse the arm entrypoint) → Goal 3; requirement 6 (six live-verification
conditions) → Goal 4; requirement 7 (the background-warmup coverage gap) → Goal 1; requirement 8
(readiness stays `YES`, authorization stays `NO`) and requirement 9 (mandatory stop even on full
success) and requirement 10 (no fresh Stage D identity) → Guardrails below. No drift found. The
"chronology" paragraph explicitly preserves iteration 17's `STALLED` verdict as correct-at-the-time —
this plan does not, and must not, redescribe iteration 17 as having been wrong.

Builds directly on iter-17 (built the AG-8-fixed `j11_preboot_guard.py`, the arm/disarm entrypoints,
and the live read-only verification tooling — all reused unmodified here except where named) and
iter-16 (the original `MaintenanceBoundary` model and the synchronous-path guard wiring). The three
riders bundled in are pre-scoped by the decomposer's own reasoning in
`runs/goal-session-market-compass/state/assumptions.md` (iter-18 entry): low-risk, additive
evidence/test corrections with zero live-database interaction, excluding the framework-level items
(the `build_review_packet` gap, the two standing `.claude`/`scripts/automation` defects) as outside
this product session's remit, consistent with iterations 13-17's own precedent.

**Ground-truth checks performed against the live repo (not trusted from the spec alone):**
- `apps/backend/app/engine/warmup.py:352-353` is exactly the unguarded `for index, asof in
  enumerate(dates, start=1): run_scan(session, asof, cfg)` cadence-loop call the spec names.
- `apps/backend/main.py:113` (`start_warmup(engine, config)`) fires unconditionally after `yield`
  whenever `latest is not None` — confirms the background path is boot-initiated and separate from the
  already-guarded synchronous path.
- `j11_preboot_guard.py` already has `evaluate_boundary_for_date` (line 185) and the bounded,
  column-projected `_relevant_boundary_rows_statement` (line 153) from iter-17's AG-8 fix — nothing here
  needs re-fixing, only reuse.
- `apps/backend/app/models.py` already declares `MaintenanceBoundary` with `__tablename__ =
  "maintenance_boundaries"` and the exact fields the spec describes.
- `apps/backend/scripts/` already has `run_j11_maintenance_boundary_arm.py` and
  `run_j11_maintenance_boundary_disarm.py` (iter-17) — the arm script's own docstring confirms it
  REFUSES when the target table is absent, i.e. no table-create entrypoint exists yet anywhere in the
  repo. That gap is real and is this iteration's net-new engineering, not already-done work.
- Live `apps/backend/data/trendora.db`: current size `8365871104` bytes and `-wal` `0` bytes match the
  spec's posted pre-iteration baseline exactly — no drift since iteration 17 closed. (mtime/table-count/
  `max(daily_prices.date)` are the developer's own true-start capture to make, not re-derived here.)

No scope creep found; nothing in IN SCOPE goes beyond the ruling's ten requirements plus the three
pre-approved riders.

## What to Build

1. **Close the background-warmup coverage gap** (`apps/backend/app/engine/warmup.py`, `_run_warmup`'s
   cadence loop, currently lines 352-353). Before each `run_scan` call, check
   `j11_preboot_guard.evaluate_boundary_for_date(session, asof)` using the SAME fail-closed exception
   handling `ensure_latest_snapshot` already uses (`warmup.py:106-120`): active matching boundary → skip
   that date's write, log the date + boundary name, continue the loop (never abort the whole warm-up
   job); ambiguous/unreadable state → fail closed (skip, continue); no boundary or an explicitly cleared
   one → behavior byte-identical to today. State-driven only — no second hardcoded J-11 date
   conditional. Re-derive from the current code (grep the boot/warmup call graph) whether any OTHER
   boot-initiated path can reach `run_scan` or otherwise mint a canonical `ScannerRun`; close any other
   one found the same way.

2. **New table-create-or-verify entrypoint** under `apps/backend/scripts/` (suggested name
   `run_j11_maintenance_boundary_table_create.py`, following the existing `run_j11_*` idiom — exact name
   is the developer's call). Mirrors the arm script's gating exactly: explicit required
   `--database-url` with no default, explicit `--confirm` gate, zero DB interaction of any kind — not
   even a read — without both. Behavior: if `maintenance_boundaries` is absent from live
   `sqlite_master`, create it via a single-table create operation sourced from
   `app.models.MaintenanceBoundary.__table__` only (never a hand-authored duplicate schema, never
   `create_db_and_tables()`/full `SQLModel.metadata.create_all()`); if present, inspect its live columns
   — an exact match is a no-op ("already correct, no action taken"); any mismatch is a STOP (exit
   non-zero, zero write of any kind, name the exact mismatched column(s) — never `ALTER`/migrate/
   guess-repair).

3. **Reuse, unmodified,** `run_j11_maintenance_boundary_arm.py` (iter-17 — do not rebuild it) for the
   boundary-row activation step, run only after Goal 2 confirms the table exists and matches exactly.

4. **New/extended live, non-booting verification tooling** (extend, or add alongside,
   `run_j11_iter17_live_preboot_guard_verification.py`), proving through the same production guard
   entry points — never by starting FastAPI — all of: boundary exists; `active=True`; persisted date set
   exactly equals the canonical 11 `INCIDENT_DATES`; `evaluate_boundary_for_date` returns blocked for
   all eleven quarantined dates and for the current latest stored date (`2026-08-12`); a non-incident
   control date (e.g. `2026-07-23`) returns not-blocked; zero `ScannerRun` rows created by the
   verification itself; PLUS the background-warmup call site closed in Goal 1 also reports blocked for a
   quarantined date when exercised through its own guard check (not only the synchronous path).

5. **Execute the live sequence**, backend OFF throughout, only after every fixture/unit test above is
   green, in this exact order against `apps/backend/data/trendora.db`: (1) table-create-or-verify;
   (2) arm; (3) live verification. Capture before/after mutation accounting: file mtime + size + `-wal`
   size, plus a row-count-and-content-fingerprint sweep over all 24 pre-existing tables (the iter-12/13
   "mtime+WAL as primary instrument, corroborated by a narrower fingerprint" pattern), proving the only
   live change anywhere is the one new table plus its one row. Re-verify (do not blindly copy) the
   decomposer's posted baseline before this sequence runs: mtime `1787670395.652078900`, size
   `8365871104`, `-wal` `0`, table count `24`, `maintenance_boundaries` count `0`, `max(daily_prices.
   date)` `2026-08-12`.

6. **Three riders** (additive, non-blocking, zero live-DB interaction):
   - **(a)** Refusal tests added to `run_j11_iter17_live_preboot_guard_verification.py` and
     `run_j11_iter17_stage_d_readiness.py` proving each refuses to write (exits non-zero, writes
     nothing) when its evidence-destination argument collides with an existing committed evidence path.
   - **(b)** Correct the "genuinely independent" wording at
     `runs/goal-market-compass-iter-17/j11-avb-bridge-diagnostic.json:576` and `:589` (verified present,
     unchanged, at exactly those two lines) to state the actual algebraic relationship — representation
     B's price is A's price divided by `bridge_factor`, and B's counterfactual volume is A's stored
     volume multiplied by `bridge_factor` — instead of an independence claim that does not hold. Do not
     touch iteration 16's own artifact; the `AVB-A` classification field is unaffected and stays as
     recorded.
   - **(c)** Correct the iteration-17 report's eleven-date "damaged dates" list
     (`reports/phase-goal-market-compass-iter-17-ui-test-plan.md`, the enumeration near line 74) to
     separate the two dates that actually carry incident price/derived-state damage from the remaining
     nine that carry none, matching iter-17's own live re-derivation already on record (eval.md: "of the
     eleven dates it lists, only two are actually damaged dates, and seven hold no data at all").

7. **Test suite extension**, fixture/in-memory SQLite only, never the live file during test collection/
   execution: `test_j11_preboot_guard.py` gets TC-1 through TC-4 (background-warmup: skip on matching
   active boundary; normal write on an uncovered date; fail-closed on an evaluation exception;
   byte-identical `dates_done`/`snapshots_created`/`forward_returns_inserted` figures with zero
   boundaries registered). `test_j11_preboot_guard_cli_scripts.py` gets TC-5 through TC-8 (the new
   table-create entrypoint's four states: absent-so-create-exact; present-and-exact-so-noop;
   present-and-mismatched-so-stop-naming-the-column; missing `--confirm` or `--database-url`-so-refuse-
   zero-interaction).

8. **Dev handoff** (`docs/handoffs/goal-market-compass-iter-18-dev.md`) states in prose — not only as
   booleans — what the live system could do before this iteration's arm step (write a canonical result
   onto `2026-08-12` from either boot-initiated path) and what it can no longer do after. Reports exactly
   the four status lines, verbatim: `J-11 MAINTENANCE BOUNDARY: ACTIVE`, `J-11 LIVE PRE-BOOT GUARD:
   ARMED`, `J-11 STAGE D READY: YES` (cited from iteration 17's artifact, not re-derived — this
   iteration touches no AVB/readiness input), `J-11 STAGE D AUTHORIZED: NO`. Confirms and cites that the
   complete changed-file set (tracked AND untracked together) contains none of `apps/backend/app/api/*`,
   `scoring.py`, `sectors.py`, `compass.py` (so J-01/J-04/J-10 could not have moved).

## Guardrails (binding — maintenance isolation, restated from OUT OF SCOPE / NOTES)

- **Maintenance isolation is ACTIVE for the whole iteration.** Do not boot the backend, the frontend,
  browser QA, or the deterministic replay lane, at any point, for any reason — including "just to
  confirm it now works" after a successful arm. This binds developer, reviewer, and QA alike; QA must
  not start services even though `Frontend Present: no` might otherwise invite an API-smoke-test pattern
  for a backend-only phase — that pattern is explicitly forbidden here, same handling as iterations
  13-17.
- Exactly two live writes are authorized on `apps/backend/data/trendora.db`, in this exact order, only
  after every fixture/unit test is green: (1) the new table-create-or-verify entrypoint; (2) the
  existing unmodified arm entrypoint. Then (3) live, read-only verification. Nothing else touches the
  file in between or after.
- Table creation must be a single-table create derived from `app.models.MaintenanceBoundary.__table__`
  — never `create_db_and_tables()`, never full `SQLModel.metadata.create_all()` over the complete
  application metadata (either could mint an unrelated missing table as a side effect).
- Do **not** invoke `run_j11_maintenance_boundary_disarm.py` this iteration — it exists but nothing is
  disarmed merely to prove the code still works.
- No write of any kind to `daily_prices`, `scanner_runs`, `scanner_results`, `sector_scores`,
  `theme_scores`, `forward_returns`, `next_session_manifests`, `data_provider_runs`, or watchlist state.
- No schema migration, `ALTER`, or table rewrite of any table other than the one exact
  `maintenance_boundaries` creation.
- No Stage D work of any kind, and no freezing/reusing a Stage D execution identity. `J-11 STAGE D
  AUTHORIZED` must remain `NO` regardless of the readiness result — `READY: YES` is a measurement, never
  authorization.
- No new network/provider fetch of any kind (AG-9's dated exceptions remain exhausted).
- Targeted pytest only (the two named test files); never the full backend suite; never two pytest
  processes concurrently (resource contract — this host has frozen before).
- **Mandatory stop, even on full success.** The instant `MAINTENANCE BOUNDARY: ACTIVE` + `LIVE PRE-BOOT
  GUARD: ARMED` + `STAGE D READY: YES` are all established, STOP — do not read that as Stage D
  permission under any framing. If a ruling stop-condition fires instead (a schema mismatch requiring
  more than the one table; any write outside table+row; the incident-date set cannot be represented
  safely; the boundary cannot be armed without touching forbidden state; boot safety cannot be made
  fail-closed), return `STALLED` and name the exact blocker rather than expanding scope or improvising a
  workaround.

## Agents Required

- developer: yes -- backend-only implementation: the `warmup.py` guard-check wiring (Goal 1), the new
  table-create-or-verify entrypoint (Goal 2), the live 3-step execution sequence plus mutation-
  accounting evidence (Goals 3-5), the three riders (Goal 6), fixture tests (Goal 7), and the dev
  handoff (Goal 8). One pass covers this; no design/review split needed beyond the standard pipeline.
- backend-data: yes -- every deliverable is backend/data-layer (`app/engine/`, `apps/backend/scripts/`,
  `apps/backend/tests/`) plus read-only/evidence JSON under `runs/goal-market-compass-iter-18/`; the
  only live-DB interaction is the two owner-authorized bounded writes (table-create, arm) plus strictly
  read-only verification — never a booted service.
- frontend-ux: no -- no frontend file is touched; maintenance isolation forbids any application-service,
  browser, or replay lane this iteration (see Guardrails).

## Frontend Present
no

Frontend Present: no — backend-only maintenance iteration; no UI surface of its own (J-11's walkthrough
is waived per `docs/goal.md` J-11 Acceptance), no application boot, no browser QA (see Guardrails above).

## Files to Create/Modify

New:
- `apps/backend/scripts/run_j11_maintenance_boundary_table_create.py` (name developer's call) -- the
  confirm-gated exact-schema table-create-or-verify entrypoint (Goal 2).
- `runs/goal-market-compass-iter-18/` evidence set, naming consistent with the iter-16/17 convention,
  e.g.: `j11-iter18-db-file-true-start.json` / `-true-end.json`, a table-create evidence file, a live
  preboot-guard verification file, and the 24-table mutation-accounting sweep -- exact filenames at the
  developer's discretion.
- `docs/handoffs/goal-market-compass-iter-18-dev.md` -- required dev handoff (Goal 8).

Modified:
- `apps/backend/app/engine/warmup.py` -- the guard check inserted into `_run_warmup`'s cadence loop
  (currently lines 352-353), mirroring `ensure_latest_snapshot`'s existing exception handling (lines
  106-120) (Goal 1).
- `apps/backend/scripts/run_j11_iter17_live_preboot_guard_verification.py` -- extended for the
  background-warmup call-site condition (Goal 4) and the evidence-destination-collision refusal test
  (rider 6a).
- `apps/backend/scripts/run_j11_iter17_stage_d_readiness.py` -- evidence-destination-collision refusal
  test only (rider 6a); no change to its AVB/readiness logic (spent, do not redo).
- `apps/backend/tests/test_j11_preboot_guard.py` -- TC-1 through TC-4 (background-warmup fixture
  coverage, Goal 7).
- `apps/backend/tests/test_j11_preboot_guard_cli_scripts.py` -- TC-5 through TC-8 (table-create
  entrypoint fixture coverage, Goal 7), plus refusal-test additions for rider 6a if colocated there.
- `runs/goal-market-compass-iter-17/j11-avb-bridge-diagnostic.json` -- wording-only correction at lines
  576 and 589 (rider 6b); `AVB-A` classification field unchanged; iteration 16's own artifacts untouched.
- `reports/phase-goal-market-compass-iter-17-ui-test-plan.md` -- damaged-date list correction near line
  74 (rider 6c).

Reused unchanged (do not reimplement):
- `run_j11_maintenance_boundary_arm.py` (Goal 3, iter-17, "do not redo").
- `app.engine.j11_maintenance.INCIDENT_DATES` (the sole source of the canonical 11-date set — never
  retype a second list).
- `app.engine.j11_preboot_guard.evaluate_boundary_for_date` / `_relevant_boundary_rows_statement` /
  `register_j11_incident_boundary` (iter-16/17, AG-8-fixed — bounded and column-projected already).
- `app.models.MaintenanceBoundary.__table__` (the exact schema source for Goal 2's table-create).

## Key Test Scenarios

Map 1:1 to the phase spec's TC-1 through TC-18 (already fully enumerated there with exact given/when/
then — not re-derived here). Priority order for the developer, cheapest-and-highest-signal first:
1. TC-1 through TC-4 -- the background-warmup guard fix; this iteration's technical core. Get this
   right before anything else, since TC-11's live check depends on it.
2. TC-5 through TC-8 -- the new table-create entrypoint's four live-state scenarios, entirely on
   disposable fixtures.
3. TC-9 through TC-12 -- the live 3-step sequence against the real `trendora.db` (table-create, arm,
   verify) plus the 24-table mutation-accounting sweep. Only after 1-2 are green; the one part of this
   iteration touching the real file, and only via the two authorized bounded writes plus read-only
   verification.
4. TC-13 through TC-15 -- the three riders (evidence-destination refusal tests, AVB wording correction,
   damaged-date list correction). Independent of 1-3, zero shared state, safe to do any time.
5. TC-16 -- final status lines exactly as specified, plus the mandatory stop (no Stage D action, no
   application boot, no browser-QA invocation, no replay-lane invocation anywhere in the evidence
   trail).
6. TC-17 -- the complete changed-file set (tracked and untracked together) excludes
   `apps/backend/app/api/*`, `scoring.py`, `sectors.py`, `compass.py` (J-01/J-04/J-10 carry forward
   unaffected).
7. TC-18 -- dev handoff states the before/after safety property in prose, written last, after every
   artifact above exists to cite.
