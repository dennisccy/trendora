# goal-market-compass-iter-18 Dev Handoff

**Phase:** goal-market-compass-iter-18
**Date:** 2026-08-26
**Agent:** developer
**Status:** complete

## Before/after safety property (TC-18 — prose, not just booleans)

**Before this iteration's arm step:** starting Trendora — via either of the two boot-initiated code paths
that reach the canonical `run_scan` — could write a real, canonical `ScannerRun` result onto
`2026-08-12` (or any of the other ten quarantined incident dates), even though Stage D has never been
authorized to touch them. The synchronous path (`warmup.ensure_latest_snapshot`) was already guarded
since iteration 16, but the background historical warm-up thread had **two of its own, entirely
unguarded** `run_scan` call sites: its own cadence loop (`warmup._run_warmup`, the one named directly in
the owner's ruling) and, found only by re-deriving the boot/warmup call graph for this iteration, a
**second** one inside `forward_testing._backfill`'s own cadence loop — reachable in production *only*
via `backfill_forward_returns(session, cfg)`, itself called *only* from `warmup._run_warmup`. Because the
`maintenance_boundaries` table did not exist at all on the live database (confirmed: `sqlite_master`
carried zero rows named `maintenance_boundaries`), there was also no persisted state anywhere for any
guard to check — the risk was live and structural, not hypothetical: simply starting the backend would
have launched the background warm-up thread, which would have recreated a canonical `ScannerRun` for
`2026-08-12` (and every other date its cadence touched) before any operator could intervene.

**After this iteration's arm step:** the live database now carries an exact-schema `maintenance_boundaries`
table with one active `j11-incident-recovery` row whose persisted date set exactly equals the canonical
eleven `INCIDENT_DATES`. Both previously-unguarded boot-initiated `run_scan` call sites now check that
persisted boundary — through the exact same shared, fail-closed entry point
(`j11_preboot_guard.evaluate_boundary_for_date_fail_closed`) the synchronous path's own logic already used
— before writing anything, and skip (log, continue) rather than write for any of the eleven quarantined
dates. Live, non-booting verification (below) independently confirms all eleven dates now evaluate
`blocked: True` through both call sites, a non-incident control date still evaluates `blocked: False`, and
the verification itself created zero `ScannerRun` rows. **Starting Trendora today can no longer write a
canonical result onto any of the eleven quarantined incident dates, from either boot-initiated path.**
Stage D itself remains exactly as unauthorized as before this iteration — nothing above is Stage D
permission, only the safety substrate Stage D will eventually depend on.

## What Was Built

- **Closed the SECOND boot-initiated `run_scan` gap** (re-derived, not named directly in the ruling):
  `forward_testing._backfill`'s own cadence loop, reachable only via the background warm-up thread. Added
  the same fail-closed boundary check immediately before its `run_scan` call.
- **Closed the FIRST (named) gap**: `warmup._run_warmup`'s own cadence loop now checks the boundary before
  each `run_scan` call, mirroring `ensure_latest_snapshot`'s existing fail-closed exception handling.
- **New shared entry point** `j11_preboot_guard.evaluate_boundary_for_date_fail_closed(session, one_date)`
  — factors the fail-closed try/except wrapper out to ONE place so both new call sites (and the live
  verification tooling) share exactly one implementation, rather than a third/fourth hand-rolled copy.
  `ensure_latest_snapshot`'s own inline copy was deliberately left untouched (already correct, already
  tested — no reason to risk it).
- **New table-create-or-verify entrypoint**: `apps/backend/scripts/run_j11_maintenance_boundary_table_create.py`
  — confirm-gated, no-default `--database-url`, creates exactly `maintenance_boundaries` from
  `app.models.MaintenanceBoundary.__table__.create(bind=engine, checkfirst=True)` (never
  `create_db_and_tables()`/`SQLModel.metadata.create_all()`); inspects and exact-matches an existing table
  rather than blindly recreating; STOPs and names the exact mismatched column(s) on any disagreement.
- **Reused, unmodified**: `run_j11_maintenance_boundary_arm.py` (iteration 17) for the boundary-row
  activation step.
- **Extended** `run_j11_iter17_live_preboot_guard_verification.py` (iteration 17) to prove the ARMED state
  (all eleven canonical incident dates blocked, a control date not blocked, the current latest stored
  incident date blocked, the background-warmup call site's own guard function also blocked, zero
  `ScannerRun` rows created by the verification itself) against the real live database, reporting the
  actual result dynamically rather than a hardcoded iter-17-era expectation. Also fixed a latent bug this
  iteration's live run exposed in the WAL zero-write check (see "Bug found and fixed" below).
- **New mutation-accounting tooling**: `app.engine.j11_maintenance.capture_full_table_sweep` /
  `diff_full_table_sweeps` (schema-agnostic, rowid-based, read-only row-count-and-fingerprint sweep over
  every live table) plus a small CLI wrapper, `run_j11_iter18_full_table_sweep.py`, run once before and
  once after the live sequence.
- **Rider 6a** — evidence-destination-collision refusal added to both
  `run_j11_iter17_live_preboot_guard_verification.py` and `run_j11_iter17_stage_d_readiness.py` (and to
  the new `run_j11_iter18_full_table_sweep.py`): each now refuses to write anything if its target output
  file(s) already exist, catching a mistyped `--evidence-dir` pointed at an earlier iteration's populated
  folder.
- **Rider 6b** — corrected the "genuinely independent" wording in
  `runs/goal-market-compass-iter-17/j11-avb-bridge-diagnostic.json` (both occurrences, lines 576/589) to
  state the actual algebraic relationship (`close_b = close_a / bridge_factor`,
  `volume_b = volume_a * bridge_factor`, so `dollar_b` reduces to `dollar_a` by construction). The
  `AVB-A` classification field is unchanged; iteration 16's own artifact is untouched.
- **Rider 6c** — corrected `reports/phase-goal-market-compass-iter-17-ui-test-plan.md`'s eleven-date
  enumeration to distinguish the two dates that actually lost raw price data (`2026-08-11`, `2026-08-12`
  — the only two the committed seed could not restore) from the remaining nine, which only had their
  derived `scanner_runs` cleared by the same removal cascade and never lost raw `daily_prices` data
  (independently re-verified live: all eleven dates carry 585–590 `daily_prices` rows each).
- **Live sequence executed** against the real `apps/backend/data/trendora.db`, backend OFF throughout, in
  the authorized order: table-create → arm → verify. Full mutation-accounting evidence captured
  before/after. See "Live execution evidence" below.

## Bug found and fixed during the live run

The live-verification script's `zero_write_proof.wal_unchanged` check (inherited unmodified from
iteration 17) did a plain `start_wal == end_wal` dict comparison. Iteration 17's own live run never
exercised the case where no `-wal` sidecar exists at all at the true start — its sidecar already existed,
unchanged, at both ends. This iteration's own live sequence hit that case for the first time: after the
table-create + arm steps committed and their connections closed, the `-wal` sidecar was fully
checkpointed away (absent) by the time the verification script's own read-only connection opened —
merely connecting to a WAL-mode database creates an empty (`size_bytes: 0`) `-wal` file as a documented,
harmless SQLite side effect (`db_file_fingerprint`'s own docstring already says this: "SQLite touches the
WAL file on any connection open in WAL mode, including read-only ones"). The naive dict-equality check
therefore false-flagged a harmless artifact as a write and returned exit code 1 even though the main
database file's mtime and size were both provably unchanged across the verification's own run.

Diagnosed by first reproducing the exact `^VIX`-style incident-isolation discipline this codebase already
uses: computed the actual algebra, confirmed the main file (mtime, size) was byte-identical across the
verification's own bracket, and confirmed the `-wal` transition was exactly `absent → present, 0 bytes` —
the one documented-harmless shape. Fixed with a new `_wal_effectively_unchanged(start_wal, end_wal)`
helper that accepts only that one specific transition as non-mutating; any other WAL difference (grown
past zero bytes, disappeared, or present-but-different) still fails the check exactly as before. Added
three new unit tests (`test_wal_effectively_unchanged_*`) covering the identical-dicts case, the
newly-accepted harmless transition, and three cases that must still fail. The stale (pre-fix) verification
evidence files from the first, false-negative run were deleted and the script re-run cleanly (exit 0)
before being trusted as final evidence — the live database itself was never touched by that first attempt
(it is read-only tooling); only the evidence-file re-generation was needed.

## Pre-existing test failure found (not caused by this iteration, not fixed — out of scope)

`test_warmup.py::test_warmup_loads_each_symbol_at_most_once_across_cadence_and_forward_returns` fails
(`^VIX` loaded 8 times instead of 1; every other symbol loads exactly once) on the **unmodified,
pre-iteration-18 code** — confirmed directly: stashed this iteration's changes to `warmup.py` and
`forward_testing.py`, re-ran the single failing test against the clean checkout, and got the identical
failure (`^VIX: 8`, same shape). This is unrelated to this iteration's guard-wiring (my new boundary
checks read only `MaintenanceBoundary` rows, never touch the bar cache, and are a no-op when no boundary
is registered, which is the case in this test's fixture) and out of this iteration's scope to fix. Changes
were restored (`git stash pop`) immediately after confirming this. 21 of the file's 22 tests pass; this
one pre-existing failure is the only exception, in either the modified or unmodified code.

## Live execution evidence

All figures below are from this iteration's own read-only verification, captured 2026-08-26.

**Baseline re-verified immediately before the sequence (zero drift since the decomposer's posted
baseline and since iteration 17 closed):** mtime `1787670395.6520789`, size `8365871104` bytes, `-wal`
`0` bytes, table count `24`, `maintenance_boundaries` count `0`, `max(daily_prices.date)` `2026-08-12`.

**Sequence executed, in this exact order, backend OFF throughout:**
1. `run_j11_iter18_full_table_sweep.py --label before` — read-only 24-table sweep captured.
2. `run_j11_maintenance_boundary_table_create.py --confirm --database-url sqlite:////home/dennis-chan/Git/trendora/apps/backend/data/trendora.db`
   — table absent → created exact-schema `maintenance_boundaries` from `MaintenanceBoundary.__table__`.
   Verified immediately after: 7 columns matching the model exactly, 0 rows.
3. `run_j11_maintenance_boundary_arm.py --confirm --database-url <same>` (unmodified) — created exactly
   one `j11-incident-recovery` row, `active=True`, `quarantined_dates_json` parsing to exactly the eleven
   canonical `INCIDENT_DATES`.
4. `run_j11_iter17_live_preboot_guard_verification.py --evidence-dir runs/goal-market-compass-iter-18`
   — all six live-verification conditions true (see below); exit code 0.
5. `run_j11_iter18_full_table_sweep.py --label after` — read-only 24-table sweep captured again.
6. `j11_maintenance.diff_full_table_sweeps(before, after, expected_new_tables=("maintenance_boundaries",))`
   — `clean: true`, `unexpected_new_tables: []`, `unexpected_removed_tables: []`,
   `changed_existing_tables: []`, `expected_new_tables_present: ["maintenance_boundaries"]`.

**Independent post-sequence re-verification (read-only, this developer's own direct check, not just the
tooling's self-report):**
- File mtime `1787701766.6272907` (changed from baseline — the two authorized writes), size
  `8365871104` bytes (**unchanged**), `-wal` `0` bytes.
- Table count `25` (was `24` — exactly +1).
- `maintenance_boundaries` exists with exactly `1` row.
- `max(daily_prices.date)` = `2026-08-12` (**unchanged**).
- `daily_prices` row count `3310374` (**unchanged**).
- `scanner_runs` row count `3117` (**unchanged**).

**Six live-verification conditions (`j11-iter18-live-preboot-guard-verification.json`):**
- `maintenance_boundaries_table_count`: 1, `boundary_row.active`: true, `persisted_dates_match_canonical`: true
- `all_eleven_incident_dates_blocked`: true
- `control_date_not_blocked`: true (control date `2026-07-23`)
- `latest_incident_date_blocked`: true (`2026-08-12`)
- `background_warmup_site_blocked`: true (the exact shared function both new call sites use, exercised directly)
- `zero_scanner_runs_created_by_this_verification`: true
- `zero_write_proof`: `mtime_unchanged`/`size_unchanged`/`wal_unchanged` all true
- `armed`: **true**

## Final status (TC-16 — mandatory stop)

```
J-11 MAINTENANCE BOUNDARY: ACTIVE
J-11 LIVE PRE-BOOT GUARD:  ARMED
J-11 STAGE D READY:        YES   (cited from runs/goal-market-compass-iter-17/j11-iter17-stage-d-readiness.json:
                                   ready=true, avb_classification=AVB-A, preflight_gate_passed=true —
                                   NOT re-derived; this iteration touches no AVB/readiness input)
J-11 STAGE D AUTHORIZED:   NO
```

**Stopping here per the ruling's mandatory-stop requirement.** All three of MAINTENANCE BOUNDARY / LIVE
PRE-BOOT GUARD / STAGE D READY are established. This is not read as Stage D permission under any framing.
No Stage D action was taken or attempted: no incident-date `ScannerRun` regeneration, no manifest
generation, no cache invalidation/re-warm, no `GET /api/compass` call, no execution identity frozen. No
application service was booted (backend or frontend), no browser QA was run, no replay lane was invoked,
at any point in this iteration.

## Files Changed

- `apps/backend/app/engine/j11_preboot_guard.py` -- added `evaluate_boundary_for_date_fail_closed`, the shared fail-closed wrapper.
- `apps/backend/app/engine/warmup.py` -- `_run_warmup`'s cadence loop now checks the boundary before each `run_scan`.
- `apps/backend/app/engine/forward_testing.py` -- `_backfill`'s cadence loop (the second, re-derived boot-initiated gap) now checks the boundary too.
- `apps/backend/app/engine/j11_maintenance.py` -- added `capture_full_table_sweep` / `diff_full_table_sweeps` (schema-agnostic mutation-accounting evidence).
- `apps/backend/scripts/run_j11_maintenance_boundary_table_create.py` (new) -- the confirm-gated exact-schema table-create-or-verify entrypoint.
- `apps/backend/scripts/run_j11_iter18_full_table_sweep.py` (new) -- read-only before/after mutation-accounting snapshot tool.
- `apps/backend/scripts/run_j11_iter17_live_preboot_guard_verification.py` -- extended to prove the ARMED state live; added the evidence-destination-collision refusal; fixed the WAL zero-write-proof bug found during this iteration's own live run.
- `apps/backend/scripts/run_j11_iter17_stage_d_readiness.py` -- added the evidence-destination-collision refusal only; no change to its AVB/readiness logic.
- `apps/backend/tests/test_j11_preboot_guard.py` -- TC-1 through TC-4 (background-warmup + the second re-derived call site), plus tests for the new shared wrapper.
- `apps/backend/tests/test_j11_preboot_guard_cli_scripts.py` -- TC-5 through TC-8 (table-create entrypoint), TC-13 (both scripts' collision refusal), plus tests for the new full-table-sweep tool and the WAL-fix helper.
- `apps/backend/tests/test_j11_maintenance.py` -- tests for `capture_full_table_sweep` / `diff_full_table_sweeps`.
- `runs/goal-market-compass-iter-17/j11-avb-bridge-diagnostic.json` -- rider 6b wording fix (lines 576/589 only; `AVB-A` classification unchanged).
- `reports/phase-goal-market-compass-iter-17-ui-test-plan.md` -- rider 6c damaged-date list correction.
- `runs/goal-market-compass-iter-18/*.json` -- the live sequence's full evidence trail (baseline sweeps, live verification result, mutation-accounting diff).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_j11_preboot_guard.py tests/test_j11_preboot_guard_cli_scripts.py tests/test_j11_maintenance.py -q`
Result: 80 passed, 0 failed.

Additional regression checks (not part of this iteration's own two named test files, run for extra
confidence since real engine modules were touched):
- `pytest tests/test_forward_testing.py -k backfill` (5 tests, real seed, real scanner engine, unmocked
  `backfill_forward_returns` call): 5 passed, 0 failed.
- `pytest tests/test_warmup.py` (22 tests, real seed, real warm-up): 21 passed, 1 failed — the
  pre-existing, unrelated `^VIX` load-count failure described above (confirmed identical on unmodified
  code via `git stash`).

Per project resource policy, the full backend suite was never run; no two pytest processes ran
concurrently; the live 7.8 GB `apps/backend/data/trendora.db` file was never copied.

## Known Issues

- The pre-existing `test_warmup.py::test_warmup_loads_each_symbol_at_most_once_across_cadence_and_forward_returns`
  failure (see above) is unrelated to this iteration and was not fixed — out of scope, and fixing it was
  not authorized by this iteration's spec.
- J-11 Stages D through G remain entirely unauthorized, unstarted, and untouched by this iteration, as
  required. `J-11 STAGE D AUTHORIZED` remains `NO`.
- The two older standing framework notes (the `scripts/automation/` forbidden-test-lane defect,
  `goal_gate.py`'s duplicate-journey-heading defect) and the five older open owner questions are carried
  forward unchanged, per the phase spec's own NOTES section — none is this iteration's job.

---

## Audit addendum (added by the iteration-18 auditor, 2026-08-26)

Two statements the phase spec's DEFINITION OF DONE requires this handoff to carry were missing from the
version the reviewer and QA read. They are added here rather than left to a downstream report, because the
spec names *this* file as the artifact that must carry them.

### TC-17 — J-01 / J-04 / J-10 carry-forward proof (tracked AND untracked files together)

This iteration's complete changed-file set contains **none** of `apps/backend/app/api/*`, `scoring.py`,
`sectors.py`, or `compass.py`, so none of the values those journeys read could have moved. Proved over
tracked and untracked files together (iteration 17's own audit finding T2: `git diff` alone is blind to
new, not-yet-committed files, and five of this iteration's files are untracked):

```bash
{ git diff --name-only HEAD; git status --porcelain | awk '{print $NF}'; } | sort -u \
  | grep -E 'app/api|scoring\.py|sectors\.py|compass\.py'
# -> no matches (42 changed paths scanned, 2026-08-26)
```

Scope of the claim, stated honestly: this is a **code-identity** argument, not a re-verification.
Maintenance isolation forbids booting the app, browser QA, and the replay lane this iteration, so J-01,
J-04 and J-10 were **not** re-exercised — they carry forward on the untouched-code-path argument alone.

### Second-order boot consequence of the live arm (not boot-verified — isolation forbids it)

Stated for the record because the arm changes what a boot *does*, not only what it may write:
`ensure_latest_snapshot` returns `None` when the latest stored date is blocked
(`apps/backend/app/engine/warmup.py:113-120`), and `main.py:113` starts the background warm-up only
`if latest is not None`. The live latest stored date is `2026-08-12`, one of the eleven quarantined dates.
So while this boundary stays armed, a boot now skips the latest-snapshot write **and never launches the
background warm-up thread at all** — which means the two call sites this iteration guarded
(`warmup._run_warmup`, `forward_testing._backfill`) are currently unreachable on boot, and every
*non*-incident cadence date also goes unwarmed. That is fail-closed and safe, and it is the reason the two
new guards are defense-in-depth for a future state (a boundary whose date-set no longer covers the latest
stored date) rather than the live boot path's only protection today. Readiness would therefore report
`awaiting_snapshot`/`initializing` rather than `ready` on the next boot
(`apps/backend/app/engine/readiness.py:171-173, 204, 223-230`). Derived by reading the code, **not** by
booting — no application service was started to check this.
