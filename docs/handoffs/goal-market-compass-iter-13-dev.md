# goal-market-compass-iter-13 Dev Handoff

**Phase:** goal-market-compass-iter-13
**Date:** 2026-08-24
**Agent:** developer
**Status:** complete

## Governing contract

`docs/goal.md` J-11 step 11's "## OWNER AUTHORIZATION — J-11 Stage C (owner, 2026-08-24)" block,
rulings C1-C12, read in full before any code was written. Stage C stands alone (C10) — this iteration
covers ONLY the bounded destructive clear, its fresh preflight, and its mutation accounting. No Stage
D/E/F/G work was planned, scoped, or executed.

## What Was Built

- **`app.engine.j11_stage_c`** (new module) — read-only Stage C precondition/evidence tooling: fresh
  preflight capture (ruling C2), the preflight comparison gate against iteration 12's certified state
  (TC-1/TC-2), the C1 date-set boundary check (TC-3, anchor-based extraction from the live `docs/goal.md`
  text — fails closed if an anchor is missing, never guesses from a broad pattern), the intended-delete-set
  capture (ruling C9, persisted BEFORE any DELETE), the post-delete mutation-accounting builder
  (TC-7..TC-12), and the completion-marker helpers (`stage_c_overall_verdict` /
  `build_completion_marker`, TC-13 — the marker's own timestamp is proven strictly after every other
  evidence artifact's timestamp before it is returned).
- **`clear_snapshot_dates(session, exact_date_set)`** in `app.engine.data_manager` (added immediately
  after `clear_snapshot_set`, which it specializes) — the bounded, exact-date-filtered deletion mechanism
  (ruling C6). Never calls `clear_snapshot_set` itself. Child-before-parent order
  (`ForwardReturn`/`ScannerResult`/`SectorScoreRow`/`ThemeScoreRow` → `ScannerRun`), whole-row deletes
  only, `daily_prices` row-count invariant asserted before/after the whole batch. Issues DELETE
  statements only — never calls `compass.get_or_create_manifest`, `scanner.run_scan`,
  `scanner.persist_run_payload`, or `_refresh_ingest_aggregates` (ruling C8, proven by
  call-count/mock-instrumented fixture tests).
- **`apps/backend/scripts/run_j11_stage_c_bounded_clear.py`** (new CLI script) — `--confirm`-gated,
  mirroring `run_j11_stage_b1_manifest_schema_migration.py`'s idiom exactly. Sequence: fresh preflight →
  preflight comparison gate → C1 check → intended-delete-set capture → `clear_snapshot_dates` →
  post-delete mutation accounting → completion marker (written ONLY if every check passes). Evidence is
  persisted at every checkpoint, before the destructive step, so a mid-run failure leaves a forensic
  trail.
- **Fixture-only unit tests** — `apps/backend/tests/test_j11_stage_c_bounded_clear.py` (TC-4/TC-5/TC-6)
  and `apps/backend/tests/test_j11_stage_c_preflight.py` (TC-1/TC-2/TC-3/TC-13). Synthetic SQLite
  fixtures only — never `apps/backend/data/trendora.db`.
- **Executed the live Stage C run** (`--confirm`) against `apps/backend/data/trendora.db` — the ONE
  authorized live write this iteration.

## Preflight and gate evidence

- Fresh Stage C preflight persisted: `runs/goal-market-compass-iter-13/j11-stage-c-preflight.json`.
  `git_head=48e83a8e240c4619e44d88054efdbe37dfbf756e`;
  `goal_md_j11_contract_hash=6fbefa8c4ee9e121638fd4be1a570092ec82e8402cd4803630b9fbb9810f65e1`;
  re-derived `engine_identity=53d2ffd10cdbf89ef16681111bd900766e00e5809bc4ebc7d4b5f2bf1b7f6c55` (a NEW
  Stage C attempt id/timestamp layered on top of the re-derived Stage B2 identity, never a second
  competing identity). **Corrected at audit (2026-08-24) — this value is NOT the certified
  iteration-10 identity.** `runs/goal-market-compass-iter-10/j11-frozen-identity.json` froze
  `6261ca1791b59771f3b6b6829142e2cf7c0f33d0fa4ea00a2f1e2c8d1d6b3a6e`; the freshly re-derived Stage C
  value differs. The logged interpretive assumption (`state/assumptions.md`, iter-13 entry #2)
  predicted byte-identity "since no code/config change has landed since" — that prediction is false:
  `apps/backend/app/engine/compass.py` is one of `config.yaml`'s three `provenance.engine_files` and
  changed in commits `a7380009` (iter-11 `basis_disclosure` fix) and `a9e651c4` (iter-12), so the code
  side of the digest moved. `config_subset_hash` is unchanged (`10bc4504ed9f28961a6342c3306d8a8eaeceac5ec7d233645540dffb0a653614`),
  so the drift is code-side only. This changed NOTHING about Stage C — `clear_snapshot_dates` is
  deletion-only and no delete predicate reads an engine identity — and it is not a step-12 violation,
  because step 12's invariant is scoped to ONE attempt and this iteration freezes a new Stage C attempt.
  It is, however, a live trap for Stage D: two frozen-identity artifacts now exist with different
  values, and 34 surviving non-incident `scanner_runs` still carry `6261ca17…` (3,083 more carry NULL,
  pre-stamping era). Stage D must state explicitly which frozen identity its step-12 per-run check
  compares against. See `docs/handoffs/goal-market-compass-iter-13-audit.md` finding B1.
  `manifest_row_count=24`; C1 date-set boundary
  check `ok=True` (the code's `INCIDENT_DATES`, the "incident date set — all 11" authoritative bullet,
  and the C1 restatement are byte-identical — verified against the LIVE `docs/goal.md` text, not a
  synthetic fixture, before the destructive run).
- Preflight comparison gate persisted: `runs/goal-market-compass-iter-13/j11-stage-c-preflight-comparison-gate.json`.
  Compared against `runs/goal-market-compass-iter-12/j11-stage-b1-cleanup-fingerprint-after.json` (the
  latest certified state — iteration 12's own diff artifact already proves that file
  `identical_except_capture_timestamps` against iteration 11's post-migration state). All 11 named
  invariant checks passed: manifest row count matches certified (24=24); no live FK on `source_run_id`;
  manifest DDL/index set unchanged (the four owner-accepted residuals included, no further drift); every
  manifest row's every column value unchanged (a full 24×28 diff, not aggregate-only);
  `source_run_id` provenance values unchanged; `daily_prices`/`data_provider_runs`/`watchlist` counts
  unchanged; the per-incident-date `ScannerRun` inventory unchanged (still exactly 4
  currently-run-bearing incident dates: 2026-05-12, 2026-08-10, 2026-08-11, 2026-08-12 — matching the
  spec's own expectation, re-derived fresh rather than trusted). `all_invariants_hold=True`,
  `material_mismatch=False`.
- Intended delete set persisted BEFORE any DELETE statement executed:
  `runs/goal-market-compass-iter-13/j11-stage-c-intended-delete-set.json`. `deleted_run_ids=[3114, 3148,
  3149, 3150]`; per-table counts: `scanner_runs=4, forward_returns=2811, scanner_results=2159,
  sector_scores=124, theme_scores=44`.

## Mutation accounting (per `runs/goal-market-compass-iter-13/j11-stage-c-mutation-accounting.json`)

All 10 named checks pass (`all_checks_pass=True`):

| Table | pre_total | deleted (incident) | post_total | non-incident population fingerprint unchanged |
|---|---|---|---|---|
| scanner_runs | 3,121 | 4 | 3,117 | yes |
| forward_returns | 6,800,539 | 2,811 | 6,797,728 | yes |
| scanner_results | 1,327,944 | 2,159 | 1,325,785 | yes |
| sector_scores | 96,751 | 124 | 96,627 | yes |
| theme_scores | 34,331 | 44 | 34,287 | yes |

Every one of the above is arithmetic-consistent (`pre_total - deleted_incident == post_total`) AND the
non-incident population's SQL-side aggregate fingerprint (count, min id, max id, id-sum → sha256,
computed over `run_id NOT IN (3114, 3148, 3149, 3150)`) is byte-identical before and after — the ID-set
diff proof ruling C9 requires, not aggregate counts alone. `incident_scoped_counts` (rows still matching
the deleted run ids) went from exactly the intended totals (pre) to all-zero (post) — the "deleted, and
only those" proof. The actual per-date/per-table deleted counts from `clear_snapshot_dates`'s own return
value matched the pre-declared intended-delete-set exactly for every date, including the 7 dates that
were documented zero-row no-ops.

- **`daily_prices`**: 3,310,374 rows before AND after; content fingerprint (row count, min/max date, id
  sum, OHLCV sum → sha256) byte-identical. Zero writes to canonical inputs (ruling C4).
- **`next_session_manifests`**: 24 rows before AND after; full 24×28 column diff `equal=true` — zero
  mutation of any kind (ruling C3/C5/AG-12/AG-17/AG-18).
- **`data_provider_runs`**: 549 rows before AND after, identical id-set — zero network activity of any
  kind occurred (AG-9; a network fetch would have appended a new provider-run row, and none appeared).
- **`watchlist`**: 6 rows before AND after, identical id-set — user state untouched.
- **Non-Layer-2 tables**: `no_non_layer2_table_row_count_changed=true` — every other table's row count
  (stocks, etfs, sectors, industries, themes, theme_members, macro_series, caches, import_checkpoints,
  etc.) is identical before/after; `non_layer2_table_changes` is an empty list.
- **DB file / WAL**: main file size unchanged at 8,365,871,104 bytes both before and after (SQLite WAL
  mode does not shrink the main file on DELETE without an explicit VACUUM, which this run never
  performs). Main file `mtime` at true process start (`1787522416.23`) matches iteration 12's own
  recorded "after" mtime exactly — proving the file was genuinely untouched between iteration 12 and this
  run's write. Main file `mtime` at true process end (`1787591622.43`) reflects this run's write. The
  `-wal` sidecar grew from 0 bytes (true start) to 5,871,032 bytes (true end) during the run and no
  longer exists on disk after the process closed its connection pool (SQLite auto-checkpointed and
  removed it on last-connection-close) — this sidecar activity is expected WAL-mode behavior for the one
  authorized write, not evidence of anything beyond it; per the coordinator's own note, a WAL mtime
  change alone would NOT have been evidence of a write (any WAL-mode connection, including read-only
  ones, touches it) — here it is corroborating, not sole, evidence, alongside the main file's own
  mtime/size and every count/fingerprint above.

## Anti-goal re-verification (read-only, post-run)

- **AG-5 (no lookahead)**: Stage C is deletion-only; no scoring/forward-return computation code path was
  touched or exercised. `daily_prices` (the sole no-lookahead input) is byte-identical before/after.
- **AG-9 (offline-deterministic ingest)**: `data_provider_runs` unchanged (549=549, identical id-set) —
  no provider-run row was appended, which is how every real fetch in this codebase is recorded; zero
  network activity occurred. J-10 stays closed and was not reopened.
- **AG-12 (manifest immutability)**: 24 manifest rows, full 24×28 value diff `equal=true` — no manifest
  row was mutated, deleted, or re-created.
- **AG-17 (repair never rewrites provenance)**: `source_run_id`, `source_run_created_at` (inside
  `generation_json`), `prospective_eligible`, `available_at_utc`, and both hashes are all part of the
  byte-identical manifest diff above — none moved. The iter-5 incident evidence and iter-10/11
  handoffs/artifacts were not touched.
- **AG-18 (the manifest migration preserves everything)**: the manifest DDL text and index set are
  byte-identical to the certified iteration-12 state (which itself carries the four owner-accepted
  residuals from iter-11/12, ruling A8/A9) — no further schema drift, no manifest regenerated/rebound.

## Files Changed

- `apps/backend/app/engine/data_manager.py` — added `clear_snapshot_dates(session, exact_date_set)`
  immediately after `clear_snapshot_set` (~line 2239). No other function in this file touched.
- `apps/backend/app/engine/j11_stage_c.py` — new module (Stage C preflight/gate/C1-check/intended-delete-set/mutation-accounting/completion-marker tooling; read-only except for pure-computation functions).
- `apps/backend/scripts/run_j11_stage_c_bounded_clear.py` — new `--confirm`-gated CLI script.
- `apps/backend/tests/test_j11_stage_c_bounded_clear.py` — new fixture tests (TC-4/TC-5/TC-6).
- `apps/backend/tests/test_j11_stage_c_preflight.py` — new fixture tests (TC-1/TC-2/TC-3/TC-13).
- `runs/goal-market-compass-iter-13/j11-stage-c-preflight.json` — persisted preflight evidence.
- `runs/goal-market-compass-iter-13/j11-stage-c-preflight-comparison-gate.json` — persisted gate result.
- `runs/goal-market-compass-iter-13/j11-stage-c-intended-delete-set.json` — persisted pre-declared delete set.
- `runs/goal-market-compass-iter-13/j11-stage-c-mutation-accounting.json` — persisted post-delete accounting.
- `runs/goal-market-compass-iter-13/j11-stage-c-complete.json` — completion marker.
- `runs/goal-market-compass-iter-13/j11-stage-c-db-file-true-start.json` / `-db-file-true-end.json` —
  db file/WAL fingerprints at the true process boundaries.
- `runs/goal-market-compass-iter-13/j11-stage-c-run.log` — the live run's stderr transcript.

**Confirmed OUT of the diff (TC-16)**: `apps/backend/app/engine/scanner.py`,
`apps/backend/app/engine/forward_testing.py`, `apps/backend/app/engine/research.py`,
`apps/backend/app/engine/j11_schema_migration.py`, `apps/backend/app/models.py`, and every file under
`apps/frontend/` — verified via `git status`/`git diff --stat` before the live run: none appear.

## Tests Run

Command: `apps/backend/.venv/bin/python -m pytest tests/test_j11_stage_c_bounded_clear.py tests/test_j11_stage_c_preflight.py tests/test_j11_maintenance.py tests/test_j11_stage_b1_migration.py -q`
Result: 42 passed, 0 failed, single pytest process, never run concurrently with any other pytest
invocation on this host, never against `apps/backend/data/trendora.db` (all fixture-DB-only). The two
pre-existing J-11 test files (`test_j11_maintenance.py`, `test_j11_stage_b1_migration.py`) re-ran
unmodified with zero regression.

The full backend suite was NOT run (resource contract — targeted files only, per
`.claude/project-template.md`). No frontend "tests"/build were run — zero frontend files touched.

## Maintenance isolation compliance

No backend boot, no frontend boot, no browser QA, no deterministic replay, no demo, no app
warmup/cache-warmup, no second backend/frontend server was started this iteration. The ONLY database
write performed anywhere in this iteration was the single bounded `clear_snapshot_dates` call inside the
`--confirm`-gated CLI script, executed once. `apps/backend/data/trendora.db` was never copied, moved, or
opened for write by anything other than that one call (all preflight/verification reads used the same
pooled `app.db.get_engine()` connection the script itself uses — read statements only, proven by the
mutation-accounting evidence above showing zero unexpected writes anywhere).

## Known Issues

- Every gate passed on the first live attempt; no retry was needed, and no defect was found in the
  bounded clear itself.
- **Found at audit (2026-08-24), corrected above — the Stage B2 engine identity has drifted since it
  was certified in iteration 10** (`6261ca17…` → `53d2ffd1…`, caused by iter-11/iter-12 edits to
  `compass.py`, a `provenance.engine_files` member). Harmless for Stage C; a Stage D precondition.
  The preflight comparison gate (`app/engine/j11_stage_c.py:264-334`) captures engine and config
  identity but does not compare either against the certified baseline, which is why nothing flagged it.
- **Found at audit — `state/assumptions.md` iter-13 entry #1's factual premise is wrong.** It states
  the `measured_date`-only forward-return population "is ALREADY absent today"; the live database
  post-Stage-C holds 16,614 such rows across 8 incident dates (2026-05-12: 2,770 · 05-13: 2,216 ·
  07-10: 2,769 · 07-13: 2,217 · 07-24: 1,660 · 07-27: 1,660 · 08-03: 1,662 · 08-05: 1,660), all owned
  by RETAINED runs. The scoping DECISION built on that premise — delete only `run_id`-owned rows — is
  exactly what C6/C7 require and was implemented correctly, so the wrong premise produced the right
  action; but Stage E must not inherit the premise. See audit findings B1/B3.
- Per ruling C10, the seven older non-blocking owner questions, the AVB price/volume scale note, and
  the two C11 framework findings (`goal_gate.py` duplicate J-ID hashing; the manifest-migration
  live-vs-model column-list defect) remain untouched and unaddressed by this iteration — they were never
  in scope.

## J-11 STAGE C COMPLETE: YES

## J-11 STAGE D AUTHORIZED: NO
