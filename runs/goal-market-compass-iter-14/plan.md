# goal-market-compass-iter-14 Execution Plan

## Governing contract

`docs/goal.md` J-11 step 12's "Clarification — which attempt, and which frozen identity (owner,
2026-08-24)" block (read in full while planning). Stage D itself is NOT authorized this iteration.
This is a small, full-depth, **non-destructive** hardening iteration: zero expected live writes to
`apps/backend/data/trendora.db`. Maintenance isolation is active — no backend/frontend boot, no
browser, no live provenance work touched (browser-QA and deterministic-replay lanes stay shut; the
walkthrough is waived by `docs/goal.md`). Resource contract applies: targeted pytest files only,
never the full suite, never two pytest processes concurrently.

## What to Build

- **Goal 1 — Fresh Stage D attempt identity.** New `app.engine.j11_stage_d` module,
  `freeze_stage_d_attempt_identity(session, config)`: wraps `j11_maintenance.freeze_attempt_identity`
  (re-derives fresh — never hardcodes iteration 10's `6261ca17…` or iteration 13's `53d2ffd1…`) and
  assembles an attempt-identity artifact (attempt id, frozen timestamp, `engine_identity`,
  `config_subset_hash`, `config_subset`, `provenance.engine_files`, `provenance.config_keys`, git HEAD
  via `j11_stage_c.read_git_head`, J-11 contract hash via `j11_stage_c.compute_contract_hash`, the
  11-date `INCIDENT_DATES` set). Persist to `j11-stage-d-attempt-identity.json`. Document explicitly:
  applies ONLY to the 11 rebuilt runs; the 34 surviving `6261ca17…` runs and 3,083 NULL-stamped runs
  are out of scope and must never be restamped.
- **Goal 2 — Three fail-closed identity COMPARE checks (not a second capture).** In `j11_stage_d`,
  reusing `j11_maintenance.check_attempt_identity_consistency` (never reimplementing comparison
  logic): `check_identity_before_first_write(frozen, current)`, `check_identity_before_date(frozen,
  current, date)`, `check_identity_after_persist(frozen, persisted_run_identity, run_id, date)`. Each
  returns a per-call evidence record, never an aggregate boolean alone. Built and fixture-unit-tested
  only — NOT invoked against the live DB or any Stage D regeneration loop.
- **Goal 3a — Stage D preflight gate, executed read-only against the live DB THIS iteration.**
  `capture_stage_d_preflight(session, engine, db_path, *, goal_md_text, git_head, config)` +
  verdict function (mirrors `j11_stage_c.stage_c_overall_verdict`), proving: zero `ScannerRun` rows on
  all 11 incident dates; `daily_prices` fingerprint matches `runs/goal-market-compass-iter-13/
  j11-stage-c-mutation-accounting.json`'s post value; manifests unchanged (24 rows, DDL, full-row
  dump vs. the same iter-13 baseline, via `j11_schema_migration.fetch_object_ddl`/`dump_table`/
  `diff_dumps`); the fresh Stage D identity (Goal 1) frozen and Check (A) passing against it; the
  11-date set matches both `docs/goal.md` lists (`j11_stage_c.check_c1_date_set_boundary`); the
  `CHAIN_MAINTENANCE_ISOLATION` env value recorded verbatim (presence/value only). Persist
  `j11-stage-d-preflight.json` and `j11-stage-d-preflight-gate.json`.
- **Goal 3b — Missing negative/precondition tests.** Verify each named item against current code
  first; report any non-real item as a correction in the dev handoff rather than inventing a gate.
  `test_tc3_c1_boundary_disagreeing_lists_stop` and `test_tc2_comparison_gate_stops_on_material_
  mismatch_manifest_row_count` already exist — cite, don't duplicate. Add: manifest DDL drift, index-set
  drift, value-fingerprint drift, `source_run_id` provenance drift, `daily_prices` fingerprint drift,
  `data_provider_runs`/`watchlist` mismatch, unexpected incident `ScannerRun` population — all →
  refusal (extend `test_j11_stage_c_preflight.py` for `compare_preflight_to_certified`'s still-untested
  checks; new `test_j11_stage_d.py` for the genuinely new Stage D checks). New
  `test_j11_stage_c_cli_script.py` (mock `main()` via `unittest.mock`, never a live DB): missing
  `--confirm` → zero DB interaction (`get_engine`/`Session` never called); comparison-gate failure →
  `clear_snapshot_dates` never called; any failing check → no completion marker written.
- **Goal 4 — Read-only AVB bridge/volume diagnostic.** New `app.engine.j11_avb_diagnostic` (pure,
  read-only) + `apps/backend/scripts/run_j11_avb_bridge_diagnostic.py` (no `--confirm` needed — zero
  writes; still capture db mtime/WAL-size at true start/end as corroboration). Re-derive the bridge
  factor and 4 calibration pairs from `runs/goal-market-compass-iter-9/j10-population-evidence.json`
  (confirmed present: `bridge_factor=2.7930001225759193`, pairs dated 2026-08-05/06/07/10 — never
  re-fetch). Classify AVB's actual stored local convention per window (pre-08-11, the two recovered
  dates, later dates) from the stored `daily_prices` series itself. Compute representations A (stored
  bridged close × stored volume — canonical today), B (`stored_close / bridge_factor` × same stored
  volume, per the logged assumption that volume was never transformed), C (bridged close × a stated
  hypothetical inverse-adjusted volume, diagnostic only, never written). Trace A vs. B through
  `app.engine.universe_resolver._adv_dollar`/`resolve_candidate` (`REASON_BELOW_ADV`),
  `app.engine.scoring`'s `liquidity` component (`_neg(adv)`), AVB's cross-sectional liquidity
  percentile, Risk score/bucket, setup status, eligibility, selection, ranking — plus whether OTHER
  pool names' liquidity percentiles shift (full-pool percentile under both A and B via column-projected
  queries only, never a whole-table ORM load — AG-8). Compare against any frozen pre-incident AVB
  artifact where one exists. Classify AVB-A / AVB-B / AVB-C / AVB-D; persist
  `j11-avb-bridge-diagnostic.json`. AVB-C/D forces Stage D NOT READY. Never mutate `daily_prices`,
  never call any J-10 recovery/fetch function.
- **Goal 5 — Explicit `J-11 STAGE D READY: YES/NO` verdict.** Combine Goal 3a's preflight-gate result,
  Goal 2's fixture-test results, Goal 3b's negative-test coverage, and Goal 4's AVB classification
  (AVB-C/D forces `NO` regardless of the preflight gate). Persist `j11-stage-d-readiness.json`;
  restate literally in the dev handoff. Does not authorize Stage D — a separate owner instruction is
  still required (C10/A12 pattern).
- **Whole-iteration zero-live-write proof.** Capture `apps/backend/data/trendora.db` main-file
  mtime+size and `-wal` size at the TRUE process start (before any work) and TRUE process end (after
  all of it) — the mtime-unchanged-AND-WAL-empty pair is the primary instrument (iter-12's lesson).
  Persist alongside the other artifacts.
- Fixture-only unit tests (synthetic `sqlite://`, never the live DB, following `test_j11_maintenance.py`'s
  pattern) for every new function in `j11_stage_d` and `j11_avb_diagnostic`.
- Dev handoff cites every artifact by name; closes with the literal `J-11 STAGE D READY: YES/NO` line
  and unconditional `J-11 STAGE D AUTHORIZED: NO`.

**Reuse, do not reimplement** (already verified present in the codebase): `j11_maintenance.
freeze_attempt_identity` / `check_attempt_identity_consistency`; `j11_stage_c.read_goal_md_text` /
`read_git_head` / `compute_contract_hash` / `check_c1_date_set_boundary` / `db_file_fingerprint` /
`capture_stage_c_preflight`'s composition pattern; `j11_schema_migration.fetch_object_ddl` /
`dump_table` / `diff_dumps` / `capture_full_db_snapshot`; the `--confirm`-gated CLI idiom in
`run_j11_stage_c_bounded_clear.py`.

**Two logged interpretive calls** (`runs/goal-session-market-compass/state/assumptions.md`, iter-14
entries) the developer must independently re-derive rather than trust verbatim: (1) the identity blind
spot is closed via new Stage D compare call-sites, not by patching the already-executed
`j11_stage_c.py` capture; (2) AVB representation B's raw close is `stored_close / bridge_factor`
(arithmetic only, never a new fetch).

## Agents Required

- backend-data: yes — all five goals plus the negative tests and diagnostics are backend Python
  (`app/engine/`, `apps/backend/scripts/`, `apps/backend/tests/`) and read-only evidence JSON under
  `runs/goal-market-compass-iter-14/`. One developer pass covers this; no separate design/review split
  needed beyond the standard pipeline.
- frontend-ux: no — no frontend file is touched; no UI, page, nav, or API surface changes this
  iteration (maintenance isolation, ruling A5/A13, still active).

## Frontend Present: no

## Files to Create/Modify

- `apps/backend/app/engine/j11_stage_d.py` — new module (Goals 1, 2, 3a).
- `apps/backend/app/engine/j11_avb_diagnostic.py` — new module (Goal 4).
- `apps/backend/scripts/run_j11_avb_bridge_diagnostic.py` — new read-only CLI script (Goal 4).
- `apps/backend/tests/test_j11_stage_d.py` — new fixture tests (Goals 1-3a; TC-1, TC-ID-1..6, TC-8..13).
- `apps/backend/tests/test_j11_stage_c_preflight.py` — extended with the still-missing negative checks
  for `compare_preflight_to_certified` (TC-14..19, minus the two already covered).
- `apps/backend/tests/test_j11_stage_c_cli_script.py` — new, `unittest.mock`-based CLI control-flow
  tests (part of TC-19: no `--confirm` ⇒ zero DB interaction; gate failure ⇒ mutation fn never called;
  failed check ⇒ no completion marker).
- `apps/backend/tests/test_j11_avb_diagnostic.py` — new fixture tests (TC-20..24).
- `runs/goal-market-compass-iter-14/j11-stage-d-attempt-identity.json` — Goal 1 evidence.
- `runs/goal-market-compass-iter-14/j11-stage-d-preflight.json`,
  `j11-stage-d-preflight-gate.json` — Goal 3a evidence (executed live, read-only, against
  `apps/backend/data/trendora.db`).
- `runs/goal-market-compass-iter-14/j11-avb-bridge-diagnostic.json` — Goal 4 evidence.
- `runs/goal-market-compass-iter-14/j11-stage-d-readiness.json` — Goal 5 verdict.
- `runs/goal-market-compass-iter-14/j11-stage-d-db-file-true-start.json` /
  `-db-file-true-end.json` — whole-iteration zero-write proof.
- `docs/handoffs/goal-market-compass-iter-14-dev.md` — dev handoff, closing with the literal
  `J-11 STAGE D READY: YES/NO` and `J-11 STAGE D AUTHORIZED: NO` lines.
- No file under `apps/frontend/` is touched. No existing destructive-path file
  (`data_manager.py`'s `clear_snapshot_dates`, `scanner.py`, `run_j11_stage_c_bounded_clear.py`) is
  modified — this iteration is additive tooling only.

## Key Test Scenarios

- TC-1: `freeze_stage_d_attempt_identity` writes the attempt-identity artifact with a freshly
  recomputed `engine_identity` (neither `6261ca17…` nor hardcoded).
- TC-ID-1..6: Checks A/B/C pass on matching identities, fail closed with zero writes on drift
  (before-first-write and before-a-later-date), fail on NULL/mismatched persisted `engine_identity`,
  and correctly ignore the 34 `6261ca17…`-stamped surviving runs (out of this attempt's scope, no
  failure raised).
- TC-8..13: the live, read-only Stage D preflight proves zero incident-date runs, unchanged
  `daily_prices`/manifests vs. the iter-13 certified baseline, Check (A) passing on the fresh identity,
  the 11-date set agreeing with `docs/goal.md`, and `CHAIN_MAINTENANCE_ISOLATION` recorded verbatim.
- TC-14..19: each of the seven still-missing negative/precondition checks (manifest DDL/index/value
  drift, `source_run_id` drift, `daily_prices` fingerprint drift, `data_provider_runs`/`watchlist`
  mismatch, unexpected incident `ScannerRun` population) refuses; `--confirm`-less CLI invocation
  touches the DB not at all; gate failure never reaches `clear_snapshot_dates`; no completion marker on
  any failing check.
- TC-20..24: the AVB bridge factor and 4 calibration pairs reproduce exactly from the persisted iter-9
  evidence; per-window local-convention classification is derived from the stored series, never
  convention alone; representations A/B/C computed with A's and B's volume shown equal; the ADV impact
  is traced through the named `universe_resolver`/`scoring` call sites for both the pool and other
  names' percentiles; classification lands in exactly one of AVB-A/B/C/D with named evidence.
- TC-25: `J-11 STAGE D READY: NO` if AVB is C/D or any preflight check fails; `YES` only if every check
  passes and AVB is A/B; `J-11 STAGE D AUTHORIZED: NO` unconditionally either way.
- TC-26: DB main-file mtime+size and `-wal` size identical between true process start and true process
  end, WAL size 0 at both points.
- Regression: `test_j11_maintenance.py`, `test_j11_stage_b1_migration.py`, and
  `test_j11_stage_c_bounded_clear.py` re-run unmodified with zero regression.

## Out of scope / boundaries (carried into the plan, not the developer's to reopen)

Stage D/E/F/G execution, `scanner.run_scan`/`persist_run_payload`, any Stage C re-run, any live
network fetch or J-10 reopening (AG-9 exhausted), any mutation of AVB's `daily_prices` or its volume
convention, any restamping of the 34 `6261ca17…` runs or the 3,083 NULL-stamped runs, any manifest
migration, any browser/replay lane, any full or partial copy of `trendora.db`, and the two standing
framework findings (`goal_gate.py` duplicate J-ID hashing; the browser/replay lane defect) — all stay
untouched per the spec's OUT OF SCOPE section.

## Alignment check

This plan advances J-11 (`docs/goal.md`) exactly as scoped — it closes the two live defects iteration
13's auditor found (B1: no per-run identity comparison exists yet for Stage D; B2: the preflight gate
captures but never compares) and the associated test gaps (T1-T3), without touching Stage C's completed
work or reopening J-10. It builds only on primitives already present in `j11_maintenance.py`,
`j11_stage_c.py`, and `j11_schema_migration.py` (verified by reading the code, not assumed) — no
duplication of prior iterations' work. No scope creep identified: every Goal traces to a DoD line and a
TC in the phase spec; nothing in the spec asks for Stage D execution itself, and this plan does not
either.
