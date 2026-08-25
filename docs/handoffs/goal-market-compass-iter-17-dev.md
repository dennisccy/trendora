# goal-market-compass-iter-17 Dev Handoff

**Phase:** goal-market-compass-iter-17
**Date:** 2026-08-25
**Agent:** developer
**Status:** complete

## Owner-facing status lines (verbatim, TC-14)

```
J-11 STAGE D READY: YES
J-11 STAGE D AUTHORIZED: NO
J-11 MAINTENANCE BOUNDARY: NOT ACTIVE
J-11 LIVE PRE-BOOT GUARD: NOT ARMED
```

**Live-arm sub-step: STALLED — blocked by the table's absence.** Per the owner's own "BLOCKER ON RECORD"
paragraph (docs/goal.md J-11 step 11), the live-arm invocation of implementation requirement 4 and all of
requirement 7's live-write portions are **not attempted**. Read-only verification against the real
`apps/backend/data/trendora.db` (`mode=ro` + `PRAGMA query_only=ON`) confirms `maintenance_boundaries` is
still absent (`SELECT count(*) FROM sqlite_master WHERE type='table' AND name='maintenance_boundaries'` →
`0`) and the real, unmodified `evaluate_boundary_for_date` returns `blocked: False` for `2026-08-12`
against that live read-only session — evidence:
`runs/goal-market-compass-iter-17/j11-iter17-live-preboot-guard-verification.json`. Creating the table was
**not attempted** — never silently omitted (this document names the blocker explicitly), never silently
attempted (no `CREATE TABLE`, no `create_db_and_tables()`, no `metadata.create_all()` executed anywhere
against the live file this iteration).

**Required-still-passing journeys (J-01, J-04, J-10):** this iteration's diff touches **none** of
`apps/backend/app/api/*`, `scoring.py`, `sectors.py`, or `compass.py` (`git diff --name-only` grepped for
those paths returns zero matches — verified directly). None of their served values could have moved; these
journeys are carried forward at their last-verified status, not re-proven this iteration (maintenance
isolation forbids browser/replay verification).

## What Was Built

1. **AG-8 fix** — `evaluate_boundary_for_date` (`apps/backend/app/engine/j11_preboot_guard.py`) no longer
   issues an unbounded `select(MaintenanceBoundary)` whole-table load on the boot path. It now:
   - Checks table existence first via `sqlalchemy.inspect(session.get_bind()).has_table(...)` — a table
     that does not exist at all (the live DB's actual state today) is treated as the same true no-op as
     "table exists, zero rows" (`blocked: False`), rather than letting `OperationalError: no such table`
     propagate (Known crux #2, verified genuinely new: none of the 19 pre-existing tests exercised a
     table-absent DB).
   - Runs a new, factored-out `_relevant_boundary_rows_statement()` that is (a) filtered to
     `active IS NOT FALSE` (SQLAlchemy `.isnot(False)`) — **never** `active == True` alone, which silently
     drops `active IS NULL` rows under SQL's three-valued comparison logic (the exact trap named in the
     owner's ruling); (b) column-projected to only the four fields the decision logic reads; and (c)
     bounded via `.limit(_MAX_RELEVANT_BOUNDARY_ROWS + 1)`, where `_MAX_RELEVANT_BOUNDARY_ROWS = 100` is a
     plain module constant (no `j11_*.py` module is in `test_no_magic_numbers.CALC_FILES` — verified;
     following the established precedent of inline constants like
     `j11_avb_correction._RATIO_RELATIVE_TOLERANCE`, not a new `config.yaml` entry).
   - Fails closed (`blocked: True, ambiguous: True`) if more than `_MAX_RELEVANT_BOUNDARY_ROWS` rows are
     fetched, rather than silently truncating away a row that might have matched.
   - No other function in the module changed behavior (`register_boundary`, `clear_boundary`,
     `register_j11_incident_boundary` are byte-unchanged); no change to `warmup.py` was needed — the
     guard's call signature (`evaluate_boundary_for_date(session, one_date) -> dict`) is unchanged.
   - **Empirically confirmed reachability, before writing TC-4's fixture (per the plan's own
     instruction):** a normal `SQLModel.metadata.create_all` schema maps `MaintenanceBoundary.active`
     (a plain non-Optional `bool`) to a DB-level `NOT NULL` column — a raw parameterized
     `INSERT ... VALUES (NULL)` against that schema raises `sqlite3.IntegrityError: NOT NULL constraint
     failed`, so the NULL-active scenario is **not** reachable through the normal schema at all (verified
     directly, and asserted as a standing regression test,
     `test_null_active_row_is_not_constructible_through_the_normal_schema`). TC-4's fixture therefore uses
     a hand-rolled `CREATE TABLE maintenance_boundaries` (identical to the real DDL except `active` carries
     no `NOT NULL`), created *before* `SQLModel.metadata.create_all` (which has `checkfirst=True` and skips
     a table that already exists), so every other table still gets the normal, fully-constrained schema.
     This models a real class of future risk (e.g. this project's own documented additive-`ALTER TABLE`
     migration convention would leave existing rows `NULL` for any new required column added later).

2. **Arm entrypoint** — `apps/backend/scripts/run_j11_maintenance_boundary_arm.py`. Thin CLI wrapper around
   the already-existing, unchanged `register_j11_incident_boundary` (sources dates from
   `j11_maintenance.INCIDENT_DATES` only). Cross-checks the code constant against `docs/goal.md`'s own two
   11-date lists via the already-existing `j11_stage_c.check_c1_date_set_boundary` before writing anything
   (satisfies requirement 4's "must validate the exact incident-date set"). Idempotent (TC-7), prints the
   boundary row before/after, writes only to `maintenance_boundaries` (TC-8). Requires `--confirm` and an
   explicit `--database-url` with **no default** — mirrors `run_j11_stage_c_bounded_clear.py`'s idiom and
   iteration 14's lesson about silently-defaulted paths. **Refuses (no write of any kind) if the target
   table does not already exist** — never calls `create_db_and_tables`/`metadata.create_all`; creating the
   table is a separate, not-yet-authorized decision. **Not invoked against `trendora.db` this iteration** —
   fixture/temp-DB invocation only, in tests.

3. **Disarm entrypoint** — `apps/backend/scripts/run_j11_maintenance_boundary_disarm.py`. Companion wrapper
   around the already-existing, unchanged `clear_boundary(session, name=...)`. Takes the boundary `name` as
   an explicit, required argument (never hardcoded), so TC-9's two-boundary scenario is naturally satisfied
   by the underlying function, not by test-only scoping. Deactivates only (`active=False`), never deletes.
   Safe no-op (exit 0) when the named boundary or the table itself does not exist. **Not invoked against
   any live-armed state this iteration** (nothing is live-armed yet).

4. **Test suite extension** — `apps/backend/tests/test_j11_preboot_guard.py` grew from 19 → 26 tests (all
   19 original tests remain green, unmodified in behavior), plus a new
   `apps/backend/tests/test_j11_preboot_guard_cli_scripts.py` with 13 tests for the two new scripts (26 + 13
= 39 total). New
   tests use an `test_iter17_*` naming space, deliberately distinct from the file's existing `tc23`-`tc30`
   labels (a different, iter-16-internal numbering space). Owner cases (A)/(C)/(G) were already covered
   by iter-16's tests and are not duplicated. Mapping:
   - **(B) — all 11 incident dates blocked once armed, + (C) re-exercised against the real boundary:**
     `test_iter17_tc2_tc3_all_eleven_incident_dates_blocked_and_one_non_incident_date_is_not` — loops every
     `jm.INCIDENT_DATES` value individually (armed via the real `register_j11_incident_boundary`, not an
     arbitrary single-date boundary) and asserts `2026-07-23` (the phase spec's own example) is unaffected.
   - **(D) arm idempotency:** `test_tc7_arm_is_idempotent_on_second_invocation` (CLI script test file).
   - **(E) ambiguous/duplicate-active fails closed — the real AG-8 test:**
     `test_iter17_tc4_null_active_row_blocks_and_is_flagged_ambiguous` (NULL `active`, custom-DDL fixture)
     and `test_iter17_tc5_many_irrelevant_rows_plus_one_real_match_stays_correct_and_bounded` (50 irrelevant
     rows + 1 real match).
   - **(F) bounded query, not a full-table load:** the same TC-5 test additionally compiles
     `guard._relevant_boundary_rows_statement()` directly and asserts the emitted SQL text contains a
     `LIMIT` clause with the exact bound value — not only the resulting boolean. A supplementary
     `test_iter17_bound_exceeded_fails_closed` proves the overflow branch itself (>100 active/ambiguous
     rows) fails closed.
   - **(H) no forbidden writes while arming:** `test_tc8_arm_writes_only_to_maintenance_boundaries` (CLI
     script test file) — seeds `daily_prices`/`scanner_runs`/`watchlist` with content, snapshots every
     table other than `maintenance_boundaries` before/after, asserts zero changed rows.
   - **(I) disarm scoped correctly:** `test_tc9_disarm_scoped_to_named_boundary_only` and
     `test_tc10_after_disarm_incident_dates_unblocked_other_boundary_still_blocks` (CLI script test file) —
     two active boundaries, disarm by name, the other boundary's row is byte-identical in every field.
   - **Table-absent regression (Known crux #2, not separately lettered by the owner but required for
     TC-11):** `test_iter17_table_absent_evaluates_cleanly_as_unblocked`.
   - **Supplementary (requirement 2's "unexpectedly duplicated ... active-boundary state" +
     requirement 3's overflow branch):** `test_iter17_two_different_active_boundaries_covering_the_same_date_still_blocks`
     (two differently-named active boundaries both covering the same date — still blocked, naming one of
     them, never silently unblocked) and `test_iter17_bound_exceeded_fails_closed` (more than
     `_MAX_RELEVANT_BOUNDARY_ROWS` active/ambiguous rows — fails closed rather than truncating).

5. **Live read-only verification** —
   `apps/backend/scripts/run_j11_iter17_live_preboot_guard_verification.py`, run for real against
   `apps/backend/data/trendora.db` through an actual `mode=ro` + `PRAGMA query_only=ON` SQLite handle.
   Result, persisted at
   `runs/goal-market-compass-iter-17/j11-iter17-live-preboot-guard-verification.json`:
   `maintenance_boundaries_table_count: 0`; `guard_result: {"blocked": false, "boundary_name": null,
   "reason": null, "ambiguous": false}` — the **real, unmodified production function**, called against the
   **live database**, exercising exactly the new table-absent code path (TC-11 satisfied).

6. **Zero-live-writes proof (TC-12)** — `trendora.db` file mtime + size + `-wal` sidecar size captured at
   the true start of this iteration's live-DB-touching work
   (`runs/goal-market-compass-iter-17/j11-iter17-readiness-db-file-true-start.json`) and again at the true
   end, after **both** live-touching scripts (the preboot-guard verification and the AVB rider) had run
   (`runs/goal-market-compass-iter-17/j11-iter17-readiness-db-file-true-end.json`). All three values are
   byte-identical:
   - mtime: `1787670395.6520789` (both)
   - size_bytes: `8365871104` (both)
   - `-wal` size_bytes: `0` (both)
   Recipe to reproduce: `apps/backend/.venv/bin/python -c "from app.engine.j11_stage_c import
   db_file_fingerprint; from pathlib import Path;
   print(db_file_fingerprint(Path('apps/backend/data/trendora.db')))"` run from the repo root, before and
   after the two scripts named above. The pre-iteration baseline independently captured by the decomposer
   (`docs/phases/goal-market-compass-iter-17.md` NOTES: mtime `1787670395`, size `8365871104`, `-wal` `0`,
   table count `24`, `maintenance_boundaries` count `0`) was independently reproduced exactly before any
   work began (verified via a separate read-only `sqlite3` inspection at session start) — nothing wrote to
   the live DB between decomposition and this iteration's start, and nothing wrote to it during this
   iteration either.

7. **AVB Stage D rider** — `apps/backend/scripts/run_j11_iter17_stage_d_readiness.py` (new; does not edit
   `run_j11_iter16_stage_d_readiness.py`). Re-runs the AVB decision-impact trace supplying `volume_override`
   (built from iteration-15's committed `runs/goal-market-compass-iter-15/j11-avb-provider-fetch-evidence.json`)
   to **both** `trace_universe_resolver_impact` and `trace_scoring_and_selection_impact` — both functions
   have accepted this optional parameter, unchanged, since iteration 15; iteration 16 simply never passed
   it. Result, persisted at `runs/goal-market-compass-iter-17/j11-iter17-stage-d-readiness.json`:
   - `avb_classification: "AVB-A"` (was `AVB-B` in iteration 16)
   - `ready: true` (unchanged from iteration 16)
   - `authorized: false` (unconditional, as always)
   - Single-bar A/B dollar-volume ratio (a script-level computation over already-existing values, no new
     engine logic — persisted in `j11-avb-bridge-diagnostic.json`'s
     `single_bar_ab_dollar_volume_ratio_by_date`): **2026-08-11: `1.0000002381510753`** (within the
     calibration window's own `0.01` relative tolerance of `1.0`; **not** within tolerance of
     `bridge_factor=2.7930001225759193`); **2026-08-12: `1.000000133734225`** (same). This directly
     disproves the mechanical hybrid artifact iteration 16 left behind: without `volume_override`, the
     counterfactual close (`stored_close / bridge_factor`) was paired with the **already-corrected**
     stored volume (calibrated for the *bridged* close), so that ratio landed **exactly** on
     `bridge_factor` by algebraic construction, not from any genuine material effect. With
     `volume_override` supplying the raw fetched provider volume instead, both the counterfactual close
     and volume are on the same un-bridged basis, and the ratio lands near `1.0`.
   - Preflight gate against **iteration 16's own already-built** certified baseline
     (`runs/goal-market-compass-iter-16/j11-stage-d-certified-baseline.json`, loaded read-only, never
     rebuilt): `all_invariants_hold: true`, including `daily_prices_fingerprint_unchanged: true` — an
     honest, **expected** clean match this time (unlike iteration 16 vs 15, which expected a mismatch
     because iteration 16's own correction was what moved the fingerprint).
   - Iteration 16's own artifacts were **not edited**: `j11-stage-d-readiness.json` sha256
     `e794dbf21e10029329952a662564dffb4517e879f566aa0287bdda774f7a0138` verified identical before and after
     this script ran (hashed inside the script itself, and independently re-verified via a standalone
     `sha256sum` afterward); `j11-stage-d-certified-baseline.json` sha256
     `1e35942c287720c16fdb6702ff6d7b23eeff045468a1f7fefe76f8afedb57079` likewise unchanged.
   - Does **not** re-invoke `run_j11_avb_correction.py` (already spent, one-time; AG-9's dated exception #2
     remains exhausted — zero network calls this iteration).

## Files Changed

- `apps/backend/app/engine/j11_preboot_guard.py` — AG-8 bounded-query rewrite in
  `evaluate_boundary_for_date` + new `_relevant_boundary_rows_statement()` helper + new
  `_MAX_RELEVANT_BOUNDARY_ROWS` module constant. No other function changed.
- `apps/backend/tests/test_j11_preboot_guard.py` — extended 19 → 26 tests (all 19 original tests
  unmodified and still green).
- `apps/backend/scripts/run_j11_maintenance_boundary_arm.py` — new, arm entrypoint.
- `apps/backend/scripts/run_j11_maintenance_boundary_disarm.py` — new, disarm entrypoint.
- `apps/backend/tests/test_j11_preboot_guard_cli_scripts.py` — new, 13 tests for the two entrypoints.
- `apps/backend/scripts/run_j11_iter17_live_preboot_guard_verification.py` — new, live read-only
  verification + zero-write-proof driver (TC-11/TC-12).
- `apps/backend/scripts/run_j11_iter17_stage_d_readiness.py` — new, AVB Stage D readiness rider (TC-13).
- `runs/goal-market-compass-iter-17/j11-iter17-live-preboot-guard-verification.json` — TC-11 evidence.
- `runs/goal-market-compass-iter-17/j11-iter17-readiness-db-file-true-start.json` /
  `-true-end.json` — TC-12 evidence.
- `runs/goal-market-compass-iter-17/j11-stage-d-preflight.json`,
  `j11-stage-d-preflight-gate.json`, `j11-avb-bridge-diagnostic.json`,
  `j11-iter17-stage-d-readiness.json`, `j11-iter17-stage-d-readiness-zero-write-proof.json` — TC-13
  evidence (all new iter-17 files; iteration 16's own artifacts stay byte-unedited, see above).

## Tests Run

Command: `apps/backend/.venv/bin/python -m pytest tests/test_j11_preboot_guard.py
tests/test_j11_preboot_guard_cli_scripts.py -v`
Result: 39 passed, 0 failed (26 in `test_j11_preboot_guard.py`, 13 in
`test_j11_preboot_guard_cli_scripts.py`).

The full backend suite was **not** run (forbidden by the project's resource contract and this iteration's
guardrails — targeted files only). `tests/test_no_magic_numbers.py` was additionally run as a fast,
directly-relevant sanity check: it has one pre-existing failure (`indicators.py`, `forward_testing.py`,
`research.py` — float literals `0.5`/`0.95`/`45.0`/`0.9`/`0.0`), confirmed via `git diff --name-only` to be
**completely unrelated to this iteration's diff** (none of those three files appear in it). Not fixed —
out of scope for this iteration (touching them would violate "do not touch code outside your task scope");
recorded here honestly per the honesty contract, not silently ignored.

## Known Issues

- The pre-existing `test_no_magic_numbers.py::test_engine_calc_code_has_no_magic_numbers` failure
  (`indicators.py`, `forward_testing.py`, `research.py`) noted above is unrelated to this iteration and was
  not investigated further (out of scope).
- No config.yaml entry was added for `_MAX_RELEVANT_BOUNDARY_ROWS` — this is a deliberate design decision
  (see "What Was Built" §1), not an oversight; flagging it here so the reviewer can confirm the
  `test_no_magic_numbers.CALC_FILES` precedent-following reasoning independently.
- The arm/disarm scripts' `--confirm`/`--database-url`/`--name` gating was proven exclusively against
  disposable fixture/temp-file SQLite databases and mock-based control-flow tests, per this iteration's
  explicit scope; neither script has been invoked against `apps/backend/data/trendora.db`, and the live-arm
  path remains genuinely untested against the real file (by design — the table doesn't exist there, and
  creating it is not authorized).
- `runs/goal-market-compass-iter-17/j11-stage-d-preflight.json` is large (~6.1 MB, it embeds the full
  `manifest_dump`) — consistent with iteration 16's own equivalently-named artifact; not something this
  iteration changed the shape of.
