# goal-market-compass-iter-13 Execution Plan

## Governing contract

`docs/goal.md` J-11 step 11's "## OWNER AUTHORIZATION — J-11 Stage C (owner, 2026-08-24)" block,
rulings **C1-C12**, plus the pre-existing "the incident date set — all 11" bullet, step 12 (Stage B2
frozen attempt identity), and step 13 (failure/retry semantics). **Stage C stands ALONE (C10)** — this
plan covers Stage C only: fresh preflight → preflight comparison gate → C1 date-set check → bounded
delete → mutation accounting → STOP. No Stage D/E/F/G work. Maintenance isolation is ACTIVE (session
level, per the coordinator's dispatch note and A5/A13) — no backend/frontend boot, no browser, static +
read-only-SQL + fixture-test verification only.

This is a **destructive iteration against the live 7.8 GB `apps/backend/data/trendora.db`** — the one
authorized live write is the single bounded `DELETE` inside `clear_snapshot_dates`, executed once via a
`--confirm`-gated CLI script, only after every precondition gate passes.

## What to Build

- A read-only **Stage C preflight-capture function** (new module `app.engine.j11_stage_c`, sibling to
  `j11_maintenance.py`) that re-derives live state fresh — never trusts iteration 10/11/12's certified
  figures — per ruling C2: git HEAD, a content hash of the `docs/goal.md` J-11 contract text (steps 1-14
  + the OWNER AUTHORIZATION block), engine identity + config identity (reuse
  `j11_maintenance.freeze_attempt_identity`), the exact 11-date `INCIDENT_DATES` set (reuse from
  `j11_maintenance`), `daily_prices` fingerprint, per-date `scanner_runs`/`scanner_results`/
  `sector_scores`/`theme_scores` inventories, the `forward_returns` inventory for affected runs/dates,
  manifest row count + full-row fingerprint + DDL fingerprint (reuse `j11_schema_migration.fetch_object_ddl`,
  `dump_table`) + index set, `data_provider_runs` state, watchlist/user-state counts+fingerprints, and the
  ledger/prereg/evidence fingerprints Stage B already defines (reuse `capture_pre_reset_inventory`'s
  shape). Freezes a NEW Stage C attempt id/timestamp that wraps the re-derived B2 `engine_identity` (see
  logged assumption below — do not treat it as a second competing identity). Persists to
  `runs/goal-market-compass-iter-13/j11-stage-c-preflight.json`.
- A **preflight comparison gate**: diff the fresh preflight against iteration 12's certified state
  (`runs/goal-market-compass-iter-12/j11-stage-b1-live-reverification.json` and the iter-10/11 artifacts)
  and every B/B1/B2 invariant (24 manifest rows; no live FK; the four owner-accepted DDL residuals
  unchanged; the three original indexes unchanged; `source_run_id` provenance unchanged; no manifest
  regenerated/rebound/upgraded). Any material mismatch or invariant failure → STOP before the first
  destructive statement, persist the failed-preflight evidence, exit non-zero, and treat that as this
  iteration's complete honest outcome.
- A **C1 date-set boundary check**: assert the literal 11-date ISO list this code uses is byte-identical
  to both the ruling C1 restatement's list and the "incident date set — all 11" authoritative bullet in
  `docs/goal.md` (both at the lines read during planning — `docs/goal.md:962-963` and `:1358-1359`). If
  they ever disagree, STOP before any deletion.
- **`clear_snapshot_dates(session, exact_date_set)`** in `apps/backend/app/engine/data_manager.py`,
  specializing the existing `clear_snapshot_set` (`data_manager.py:2212-2236`) pattern with an exact-date
  filter: for each date, freshly query the current `ScannerRun` (never a cached/prior inventory); no run
  → documented zero-row no-op; a run exists → delete children before parent
  (`ForwardReturn`/`ScannerResult`/`SectorScoreRow`/`ThemeScoreRow` filtered by `run_id ==
  that_run.id`, then the `ScannerRun` row) — all four child tables carry `run_id: int =
  Field(foreign_key="scanner_runs.id", ...)` (confirmed at `models.py:257,289,317,399`), so the
  `run_id`-scoped filter is mechanically correct. Assert `daily_prices` row count AND the same content
  fingerprint `capture_pre_reset_inventory` computes are identical before/after. Never call
  `compass.get_or_create_manifest`, `scanner.run_scan`, `scanner.persist_run_payload`, or
  `data_manager._refresh_ingest_aggregates`.
- **Intended-delete-set capture** (ruling C9): before any DELETE, query and persist the exact row-id set
  to be removed per table for each currently-run-bearing incident date (expected 4: 2026-05-12,
  2026-08-10, 2026-08-11, 2026-08-12 — re-derive fresh, do not trust this figure) plus every child row id,
  to `runs/goal-market-compass-iter-13/j11-stage-c-intended-delete-set.json`.
- **`--confirm`-gated CLI script** `apps/backend/scripts/run_j11_stage_c_bounded_clear.py`, mirroring
  `run_j11_stage_b1_manifest_schema_migration.py`'s idiom exactly (no DB interaction, not even a read,
  without `--confirm`; refuses to run without it; persists evidence at every checkpoint before the
  destructive step so a crash leaves a forensic trail): fresh preflight → comparison gate → C1 check →
  intended-delete-set capture → `clear_snapshot_dates` → post-delete verification + mutation accounting →
  completion marker `runs/goal-market-compass-iter-13/j11-stage-c-complete.json` written ONLY if every
  check passes. On any failure: no marker, non-zero exit, evidence preserved.
- **Post-delete mutation accounting**: per-table PRE/DELETED/POST counts for the five tables, split
  incident vs. non-incident; an explicit ID-set diff (not aggregate counts) proving every non-incident id
  survives and every intended-delete id (and only those) is gone; `daily_prices`, `next_session_manifests`
  (row count + full 24×28 value fingerprint), `data_provider_runs`, `watchlist` fingerprints before/after
  (must be identical); DB file mtime+size and `-wal` size captured at the TRUE process start and end (not
  a narrow internal bracket — iter-12's lesson). Persist to
  `runs/goal-market-compass-iter-13/j11-stage-c-mutation-accounting.json`.
- Fixture-only unit tests (new `apps/backend/tests/test_j11_stage_c_bounded_clear.py`, synthetic SQLite
  fixture only — never `trendora.db`): bounded-date deletion at the id level (not just count level),
  no-op-on-absent-run, non-incident rows untouched, `daily_prices` invariant, call-count/mock assertion
  that `get_or_create_manifest`/`run_scan`/`persist_run_payload` are never invoked.
- Fixture-only unit tests for the preflight capture, the comparison gate (incl. a synthetic "materially
  differs" STOP case), the C1 boundary check (incl. a synthetic "the two goal.md lists disagree" STOP
  case), and completion-marker gating (fail → no marker + non-zero exit; pass → marker written only
  after every check, with a timestamp strictly after every check's own timestamp).
- **Execute the live Stage C run** (`--confirm`) against `apps/backend/data/trendora.db` — the ONE
  authorized live write this iteration.
- Dev handoff at `docs/handoffs/goal-market-compass-iter-13-dev.md` citing every mutation-accounting
  figure by name, closing with the literal lines `J-11 STAGE C COMPLETE: YES` or `NO`, and unconditionally
  `J-11 STAGE D AUTHORIZED: NO`.

## Reuse — do not reimplement

- `app.engine.j11_maintenance.capture_pre_reset_inventory` / `freeze_attempt_identity` /
  `check_attempt_identity_consistency` / `INCIDENT_DATES` (`apps/backend/app/engine/j11_maintenance.py`)
  — Stage B/B2 read-only tooling, already live, re-verified through iteration 12.
- `app.engine.data_manager.clear_snapshot_set` (`data_manager.py:2212-2236`) — the pattern to specialize
  (same child-before-parent order, same whole-row-delete discipline, same `daily_prices`-untouched
  assertion) — never call it directly, it is unfiltered.
- The `--confirm`-gated CLI idiom in
  `apps/backend/scripts/run_j11_stage_b1_manifest_schema_migration.py` (evidence-before-destruction
  ordering, non-zero exit + no marker on any failure, idempotency-guard style).
- `app.engine.j11_schema_migration.fetch_object_ddl` / `dump_table` / `capture_full_db_snapshot` /
  `diff_snapshots` (`apps/backend/app/engine/j11_schema_migration.py`) — read-only DDL/whole-table-count/
  mtime-size helpers for the mutation-accounting evidence.

## Logged interpretive assumptions to independently re-verify (from `runs/goal-session-market-compass/state/assumptions.md`, iter-13 entries)

1. Stage C's forward-return DELETE is scoped to `run_id`-owned rows only, never `measured_date`-only
   membership (that population is Stage E's repair target, or already absent from the original incident —
   not Stage C's clear). The developer must independently re-derive this against the current
   code/schema, not trust the logged entry verbatim.
2. The "Stage C attempt identity" ruling C2 requires is a new bookkeeping identifier layered ON TOP OF,
   not replacing, the existing Stage B2 `engine_identity`.

## Agents Required

- backend-data: yes — all work above is backend Python (engine module, CLI script, fixture tests, the
  one authorized live delete + read-only verification).
- frontend-ux: no — zero frontend files touched this iteration (TC-16 mechanically forbids it; also
  forbidden: `scanner.py`, `forward_testing.py`, `research.py`, `j11_schema_migration.py`, `models.py`).

## Frontend Present: no

## Files to Create/Modify

- `apps/backend/app/engine/j11_stage_c.py` — NEW: Stage C preflight capture, preflight comparison gate,
  C1 boundary check, intended-delete-set capture, mutation-accounting builder (read-only helpers; the
  destructive call itself lives in `data_manager.clear_snapshot_dates`).
- `apps/backend/app/engine/data_manager.py` — add `clear_snapshot_dates(session, exact_date_set)` near
  `clear_snapshot_set` (~line 2212); no other function in this file may be touched.
- `apps/backend/scripts/run_j11_stage_c_bounded_clear.py` — NEW `--confirm`-gated CLI script orchestrating
  preflight → gate → C1 check → intended-delete-set → `clear_snapshot_dates` → verification → completion
  marker.
- `apps/backend/tests/test_j11_stage_c_bounded_clear.py` — NEW fixture-DB tests for `clear_snapshot_dates`
  (TC-4, TC-5, TC-6).
- `apps/backend/tests/test_j11_stage_c_preflight.py` (or folded into the module above — developer's
  call) — NEW fixture tests for preflight capture, comparison gate, C1 check, completion-marker gating
  (TC-1, TC-2, TC-3, TC-13).
- `runs/goal-market-compass-iter-13/j11-stage-c-preflight.json` — persisted preflight evidence.
- `runs/goal-market-compass-iter-13/j11-stage-c-intended-delete-set.json` — persisted pre-declared delete
  set.
- `runs/goal-market-compass-iter-13/j11-stage-c-mutation-accounting.json` — persisted post-delete
  accounting.
- `runs/goal-market-compass-iter-13/j11-stage-c-complete.json` — completion marker, written only on full
  verification pass.
- `docs/handoffs/goal-market-compass-iter-13-dev.md` — dev handoff with the two required literal lines.

**Explicitly OUT of the diff (TC-16, mechanically enforced):** `apps/backend/app/engine/scanner.py`,
`apps/backend/app/engine/forward_testing.py`, `apps/backend/app/engine/research.py`,
`apps/backend/app/engine/j11_schema_migration.py`, `apps/backend/app/models.py`, any file under
`apps/frontend/`.

## UI Evolution

N/A — Frontend Present: no. No new user-facing capability, no new information displayed, no new user
actions, no UI surface changes, no navigation changes. The entire delta is inside the derived-state layer
of the live database, provable only by mutation-accounting evidence and fixture tests, never by a served
page.

## Visual Requirements

N/A — no frontend work this iteration.

## Key Test Scenarios

- TC-1/TC-2: fresh Stage C preflight captured and persisted; a synthetic "materially differs from
  certified state" fixture case proves the comparison gate STOPS before any DELETE statement.
- TC-3: a synthetic "the two goal.md 11-date lists disagree" fixture case proves the C1 check STOPS
  before any deletion.
- TC-4/TC-5/TC-6: `clear_snapshot_dates` on a mixed incident/non-incident fixture deletes only rows owned
  (by `run_id`) by an incident-date `ScannerRun`; non-incident rows survive with identical ids; a date
  with no existing run is a documented no-op, not an error; `daily_prices` count+fingerprint unchanged;
  `get_or_create_manifest`/`run_scan`/`persist_run_payload` are never called (mock/call-count assertion).
- TC-7 through TC-12 (live, self-checked by the CLI script): the mutation-accounting artifact's DELETED
  set matches the pre-declared intended-delete-set exactly; every pre-existing id NOT in the deleted set
  is still present after with an identical id (explicit ID-set diff, not aggregate counts);
  `daily_prices` row count + SHA-256 content fingerprint byte-identical before/after; `next_session_manifests`
  row count stays 24 with all 28 columns per row identical; `data_provider_runs`/`watchlist` counts +
  fingerprints identical; DB file mtime/size + `-wal` size captured at TRUE process start/end.
- TC-13: completion marker's timestamp is strictly after every verification check's own timestamp on
  success; on any verification failure, no marker exists and the process exit code is non-zero.
- TC-14: the dev handoff contains the literal lines `J-11 STAGE C COMPLETE: YES` or `NO`, and
  unconditionally `J-11 STAGE D AUTHORIZED: NO`.
- TC-15: all new/extended targeted test files pass via
  `apps/backend/.venv/bin/python -m pytest <files> -q` in a single pytest process, never concurrently
  with any other pytest invocation, never against `apps/backend/data/trendora.db`; existing
  `test_j11_maintenance.py` and `test_j11_stage_b1_migration.py` re-run unmodified with zero regression.
- TC-16: `git diff --stat` / changed-file inspection confirms none of the six forbidden files/dirs
  appear in the diff.
- AG-5/AG-9/AG-12/AG-17/AG-18 each re-verified read-only against the post-run database and cited by name
  in the handoff (zero lookahead introduced; zero network calls; manifests untouched byte-for-byte; no
  eligibility upgraded; the four accepted DDL residuals from A8/A9 remain the only manifest-table schema
  delta — nothing further touched).

## Notes for the developer

- **Resource contract:** targeted test files only, single pytest process at a time, never against the
  live DB, never concurrent with another pytest run.
- **Maintenance isolation:** do not start the backend or frontend and do not use browser automation.
  Inspect statically and via read-only SQL only; never open `trendora.db` for write except through the
  one `clear_snapshot_dates` call inside the confirmed CLI script; never copy the DB file.
- **Long-running work:** if the live Stage C run or its verification queries could run long, launch via
  `setsid nohup <cmd> > <logfile> 2>&1 &` in the foreground, capture the PID, and poll with bounded sleep
  loops — do not let it die with a background shell at turn end.
- Regardless of Stage C's outcome (YES or NO), Stage D requires a SEPARATE, fresh owner instruction
  (ruling C10) — do not scope, plan, or begin any Stage D work this iteration under any circumstance.
