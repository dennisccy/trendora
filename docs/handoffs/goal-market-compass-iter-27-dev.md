# goal-market-compass-iter-27 Dev Handoff

**Phase:** goal-market-compass-iter-27
**Date:** 2026-08-28
**Agent:** developer
**Status:** complete

## What Was Built

J-06's last unmet acceptance limb ("assert `GET /api/compass` still serves the manifest verbatim with a
read-time basis disclosure showing the underlying run is unavailable — never a 404, never a recompute")
is now closed. `GET /api/compass` no longer calls `resolved_run` (which self-heals a missing `ScannerRun`
via `run_scan`) before checking whether a manifest already exists for the resolved as-of. It now:

1. Resolves the as-of STRING to a concrete date via the already-imported `resolved_date` (validates only,
   never self-heals, never creates a `ScannerRun`).
2. Looks up the latest stored manifest for that date via a new pure-read helper,
   `app.engine.compass.latest_manifest_for_date(session, as_of)`.
3. If a manifest already exists: serves it directly (`manifest_row_payload` + `_read_time_additions`,
   whose `basis_disclosure` call is a pure read-only `ScannerRun` SELECT) WITHOUT ever calling
   `resolved_run`/`run_scan`. This is the branch that makes `basis.status == "unavailable"` reachable when
   the manifest's source run has been removed — previously structurally unreachable (iter-3 audit finding
   B2, re-confirmed live by iter-26's dev+reviewer+evaluator).
4. Only when NO manifest exists yet does it fall through to the original path — `resolved_run` →
   `get_or_create_manifest` — unchanged, still the only branch that may create a `ScannerRun` or mint a
   manifest.

`get_or_create_manifest`'s own existing-row check (previously an inline duplicate `select(...)`) now calls
the same new `latest_manifest_for_date` helper — one query shape for "does a manifest already exist for
this date," shared by both callers.

`snapshot_serving.resolved_run`, `scanner.resolve_run`, and `scanner.resolve_as_of_date` are byte-identical
to before this iteration (verified via `git diff --stat` — zero lines changed) — the shared self-heal
machinery every other route (`/`, `/stocks`, `/sectors`, `/themes`, dashboard, market-phase) depends on is
untouched, and their self-heal behavior for those routes is unchanged. `POST /api/compass/regenerate` is
also untouched (it already reads the current run via a plain SELECT and never self-heals).

## Files Changed

- `apps/backend/app/engine/compass.py` -- added `latest_manifest_for_date(session, as_of)` (pure read, no
  run lookup, no write); refactored `get_or_create_manifest`'s existing-row check to call it instead of a
  duplicate inline query. +23/-8 lines (net; see diffstat below).
- `apps/backend/app/api/compass.py` -- reordered `compass()` (`GET /api/compass`) to check
  `latest_manifest_for_date` (via `resolved_date`) BEFORE ever calling `resolved_run`/`run_scan`; added the
  new import. `compass_regenerate` untouched. +16/-1 lines.
- `apps/backend/tests/test_api_compass.py` -- flipped
  `test_compass_route_never_404s_and_manifest_bytes_survive_a_removed_historical_run`'s final assertions
  from documenting the bug (`basis.status == "rebuilt"`, `healed is not None`) to proving the fix
  (`basis.status == "unavailable"`, `healed is None`, zero new `scanner_runs` rows); rewrote the
  surrounding docstring/comment block; added two new tests
  (`test_compass_route_restore_path_flips_basis_back_to_available_or_rebuilt`,
  `test_compass_route_warm_path_is_inert_two_gets_are_byte_identical_zero_new_runs`) and one helper
  (`_scanner_run_count`). +153/-24 lines.

`git diff --stat` for the three files: `apps/backend/app/api/compass.py | 16 ++`,
`apps/backend/app/engine/compass.py | 23 +-`, `apps/backend/tests/test_api_compass.py | 153 ++++--`.
No other file under `apps/backend/app/` or `apps/backend/tests/` changed (verified: `git status --short`
shows exactly these three plus goal-mode run/telemetry bookkeeping files).

## TDD Evidence

Before applying the source fix, the flipped test and the two new tests were run against the pre-fix
source (temporarily reverted via `git checkout --`) to confirm they fail for the expected reason:

```
FAILED test_compass_route_never_404s_and_manifest_bytes_survive_a_removed_historical_run
  AssertionError: assert 'rebuilt' == 'unavailable'
FAILED test_compass_route_restore_path_flips_basis_back_to_available_or_rebuilt
  AssertionError: assert 'rebuilt' == 'unavailable'
2 failed, 9 passed in 2.28s
```

(The 9 pre-existing tests, including the new warm-path test, already passed unmodified — the warm-path
case was never broken; only the removal-branch behavior was.) The source fix was then re-applied
(`git apply` of the saved diff) and the full suite re-run — all pass (below).

## Tests Run

Command:
```
cd apps/backend && .venv/bin/python -m pytest tests/test_api_compass.py tests/test_manifest_invariants.py \
  tests/test_ingest_finalize_compass.py tests/test_compass.py -v
```
Result: **93 passed, 0 failed** (11.05s — 11.32s across two runs).

### TC-1 .. TC-10 (fixture-DB, route-level, `apps/backend/tests/test_api_compass.py`)

- **TC-1** (`test_compass_route_serves_every_new_field_directly` + warm-path new test): intact
  manifest+run → `basis.status == "available"`, zero `scanner_runs` row-count change. PASS.
- **TC-2 (the core fix)** (`test_compass_route_never_404s_and_manifest_bytes_survive_a_removed_historical_run`,
  flipped): `ScannerRun` deleted in the fixture → `GET` still 200 (never 404), `basis.status ==
  "unavailable"`, `basis.detail` contains "no longer stored", `manifest_hash`/`version`/`content_hash`/
  `selection`/`comparison_cohort`/`near_threshold_shadow` byte-identical to the pre-removal capture,
  `scanner_runs` row count UNCHANGED (self-heal did not fire), and the removed run stays absent
  (`healed is None`). PASS — this is the assertion that flipped from bug-proving to fix-proving.
- **TC-3 / TC-4 (restore path)** (new test `test_compass_route_restore_path_flips_basis_back_to_available_or_rebuilt`):
  starting from the "unavailable" state left by TC-2, re-creating the `ScannerRun` with the SAME recorded
  `created_at` flips `basis.status` to `"available"` (payload bytes unchanged from the pre-removal
  capture); re-creating with a DIFFERENT `created_at` instead yields `"rebuilt"` (payload bytes still
  unchanged). PASS.
- **TC-5**: `test_compass_route_historical_asof_serves_that_dates_own_manifest` +
  `test_compass_route_computes_once_serves_from_storage_after` cover the create-once-on-GET path is
  unmodified by the reorder (first call mints, second call adds zero rows). PASS.
- **TC-6/TC-7 (live canonical DB)**: see "Live Canonical Database Verification" below — these are
  live-route checks, not fixture tests, run separately.
- **TC-8**: see "Incident-Date Enumeration" below.
- **TC-9**: `test_compass_route_unknown_asof_returns_honest_error_never_fabricated` (far-future date) —
  unchanged 4xx status. PASS. (Unparseable-date and both-branch coverage is structurally guaranteed:
  `resolved_date` is now the FIRST call on both the fast — existing-manifest — and slow — create — paths,
  matching `resolve_run`'s own internal ordering, `resolve_as_of_date` then `run_scan` — verified directly
  against `apps/backend/app/engine/scanner.py:338-347` before making this change.)
- **TC-10**: `test_compass_route_frontier_with_no_manifest_yet_returns_honest_404` — current frontier with
  no manifest yet still raises `ManifestNotYetFrozen` → still 404; zero rows written. PASS (this guard is
  structurally unaffected: the fast path only fires when `latest_manifest_for_date` returns non-`None`).
- **New warm-path test** (`test_compass_route_warm_path_is_inert_two_gets_are_byte_identical_zero_new_runs`):
  with an existing manifest and its run intact, two consecutive `GET`s through the route function return
  byte-identical responses and add zero new `ScannerRun` rows — proves the new fast-path branch is inert
  on the common, already-working case. PASS.

### Live Canonical Database Verification (TC-6 / TC-7 / TC-8)

Performed via a real backend boot against the canonical `apps/backend/data/trendora.db` (authorized per
the coordinator note: "Booting against the canonical DB is authorized for ordinary non-destructive
work"), started with `bash scripts/start-backend.sh` on port 8255 (computed offset), confirmed healthy
(`GET /api/health` → `preflight.verdict: "GO"`), exercised with real HTTP `GET /api/compass` calls through
the actual reordered route, then shut down cleanly (`pkill`, confirmed via a failed health check and
`pgrep` showing no remaining trendora uvicorn process).

Row counts on `next_session_manifests` / `scanner_runs` / `daily_prices`, taken via read-only SQLite
connections (`mode=ro`) BEFORE starting the backend, AFTER the HTTP calls (backend still running), and
AFTER shutdown:

| Table | Before | After (backend up) | After (shutdown) |
|---|---|---|---|
| `next_session_manifests` | 25 | 25 | 25 |
| `scanner_runs` | 3128 | 3128 | 3128 |
| `daily_prices` | 3,310,374 | 3,310,374 | 3,310,374 |

Zero rows added, removed, or changed at any point.

- **TC-6**: `GET /api/compass?as_of=2025-04-15` requested twice. Both HTTP 200. `basis.status ==
  "available"`. The two response bodies are byte-identical (`diff` on the saved JSON — no output).
  Served `version: 2`, `mode: "retrospective"`, `manifest_hash:
  b063a0ebd9b58891d4e97d9ad087e4df375e6d0823d5929151652147e2faba22` — matches the row already stored in
  `next_session_manifests` (queried read-only beforehand: `(25, '2025-04-15', 2, 'retrospective', 1,
  'b063a0eb...')`). The plan's note that this manifest was "frozen in iter-26" refers to version 1
  (`1325e689...`); a later, unrelated iteration minted version 2 for the same date — `latest_manifest_for_date`
  correctly serves the latest version, and TC-6 only requires byte-identity across the two calls in THIS
  iteration's own verification window, which holds.
- **TC-7**: `GET /api/compass?as_of=2026-08-12` (the frontier) requested once, per the test-first contract's
  wording. HTTP 200. `mode: "at_ingest"`, `version: 6`, `manifest_hash:
  9bc08cfba04fc2dcab7eeb35f7b695834ef69da5ca3b6634acca4c605d5769c3` — matches the row already stored
  (queried read-only beforehand: `(23, '2026-08-12', 6, 'at_ingest', 1, '9bc08cfb...')`) — unchanged, as
  required. `basis.status` reported `"rebuilt"` (the live scanner run's recorded `created_at` differs from
  what version 6's generation block recorded, from prior J-11 recovery/regeneration work in earlier
  iterations) — TC-7 does not require any particular `basis.status`, only that `mode`/`version`/
  `manifest_hash` stay unchanged, which they did.

### Incident-Date Enumeration (TC-8)

Enumerated via a read-only SQL query against the live canonical DB (never hardcoded), joining
`scanner_runs` to `next_session_manifests` on `as_of` for the `id BETWEEN 3140 AND 3160` window (the
window containing the run ids the iter-22/iter-23 handoffs already cited as manifest-less):

```sql
SELECT sr.id, sr.asof_date,
       (SELECT COUNT(*) FROM next_session_manifests m WHERE m.as_of = sr.asof_date) AS manifest_count
FROM scanner_runs sr WHERE sr.id BETWEEN 3140 AND 3160 ORDER BY sr.id
```

Exactly 7 dates have `manifest_count == 0` (run ids 3148-3154, all `created_at` 2026-08-26, matching the
J-10/J-11 recovery-era backfill window described in `docs/goal.md`):

`2026-05-12`, `2026-05-13`, `2026-07-10`, `2026-07-13`, `2026-07-24`, `2026-07-27`, `2026-08-03`

None of these 7 dates was ever requested by this iteration's own test/verification plan — the only live
`GET /api/compass` calls made were for `2025-04-15` (TC-6) and `2026-08-12` (TC-7); the fixture-DB tests
never touch the canonical database at all (each uses its own `tmp_path`-scoped SQLite file). A read-only
count of `next_session_manifests` rows WHERE `as_of` is one of the 7 dates was **0 before AND after** this
iteration's entire verification window (confirmed in the same query that produced the "after (shutdown)"
row counts above).

### `test_no_magic_numbers.py` — pre-existing, unrelated failure (not caused by this iteration)

Ran as an extra precaution since engine code was touched. `test_engine_calc_code_has_no_magic_numbers`
fails on literals in `indicators.py`, `forward_testing.py`, and `research.py` — none of which this
iteration touches (`git diff --stat` confirms zero changes to those three files). `compass.py` is NOT
among the reported offenders — the new `latest_manifest_for_date` helper introduces no magic numbers. Not
in this iteration's target test list per the plan; recorded here for reviewer/auditor transparency only,
not fixed (out of scope — pre-existing, unrelated to this fix).

### Required-still-passing journeys (J-01, J-04, J-05, J-10, J-11)

No production code outside `apps/backend/app/api/compass.py` / `apps/backend/app/engine/compass.py` was
touched. The J-06 test list this iteration does NOT re-touch — confirmed still passing, unmodified, in the
same 93-test run above:

- **Time-safety**: `test_tc14_time_safety_content_hash_unchanged_by_post_asof_bar_change` — PASS.
- **Rebuild survival**: `test_tc15_clear_snapshot_set_and_remove_data_delete_zero_manifest_rows` — PASS.
- **Reproducibility**: `test_tc16_two_independent_builds_of_same_inputs_produce_identical_content_hash` —
  PASS.
- **Create-once concurrency**: `test_tc17_concurrent_requests_for_same_not_yet_computed_asof_yield_one_row`
  — PASS.
- **Cohort reproducibility**: `test_tc19_comparison_and_shadow_cohorts_reproduce_exactly` — PASS.
- **Prospective-eligibility derivation**: `test_tc20_baseline_is_eligible` +
  `test_tc20_each_violated_condition_independently_forces_false` (10 parametrized cases) — all PASS.
- **Availability-fence conservatism**:
  `test_tc21_available_at_utc_never_earlier_than_generated_at_plus_margin` — PASS.
- **Artifact tamper detection**:
  `test_tc22_flipping_a_byte_including_inside_prospective_eligible_fails_verification` — PASS.
- **Hash-scope separation**:
  `test_tc23_metadata_only_regeneration_content_hash_equal_manifest_hash_differs` — PASS.
- **Identity-separation counter-tests**: `test_tc23_why_not_and_qualifier_changes_move_only_manifest_config_hash`,
  `test_tc23_shadow_min_score_moves_only_cohort_rule_hash`,
  `test_tc23_leadership_min_score_moves_both_candidate_and_cohort_rule_hash`,
  `test_tc23_max_candidates_moves_only_candidate_rule_hash` — all PASS.
- **Disposition partition**:
  `test_tc24_disposition_tallies_partition_member_count_minus_candidate_count` — PASS.
- **Schema conformance**: `test_tc25_frozen_at_ingest_manifest_validates`,
  `test_tc25_retrospective_manifest_validates`, `test_tc25_manifest_missing_required_field_fails_validation`
  — all PASS.

J-01/J-04/J-05/J-10/J-11 have no dedicated fixture files run this iteration beyond the four listed in the
test command (which already cover J-04/J-05/J-06's engine-level behavior); no code path they depend on
changed. The deterministic replay lane + LLM fallback (goal-mode evaluator) is the mechanism specified to
confirm this — not re-run manually here, per this iteration's IN SCOPE list, which assigns that
verification to the evaluator stage.

## Pre-handoff Verification

- **Service startup**: `bash scripts/start-backend.sh` was run once (for the live TC-6/TC-7 checks above)
  and confirmed healthy (`preflight.verdict: "GO"`, `db_ok: true`) before any request was made; shut down
  cleanly afterward (`pkill`, confirmed via failed health probe and `pgrep` showing no remaining trendora
  uvicorn process). No frontend was started (`Frontend Present: no` — zero frontend files touched).
- **External integrations**: none added this iteration (no new adapters/scrapers/external calls).
- **Native dependency binaries**: none added this iteration.

## Known Issues

None introduced by this fix. Carried forward from the spec's own NOTES (none blocking, none in scope this
iteration): TC-15 AST scanner strengthening (`test_manifest_invariants.py:155`), J-04's screenshot re-take,
J-05/J-06 walkthrough recordings, the four leftover export files, J-09's ~2.99 GB acceptability question,
and the four older owner questions (J-06 wording, J-01 test steps, empty "next-session focus", MNST) — all
explicitly out of scope for this iteration and untouched.

The pre-existing `test_no_magic_numbers.py` failure (unrelated files) is noted above for transparency;
not fixed, not in scope.

---

## Auditor correction (2026-08-28, iter-27 audit) — the `next_session_manifests` row count above is stale

The "Live Canonical Database Verification (TC-6 / TC-7 / TC-8)" table above records
`next_session_manifests = 25` before **and** after. That was accurate when the developer wrote it, but it
was invalidated later in the same iteration: the LLM browser-QA lane issued
`GET /api/compass?as_of=2019-03-01` under its UT-J-05 step-7 check, which minted a new manifest row
(`reports/phase-goal-market-compass-iter-27-ui-test-results.llm.md:165-170`). The reviewer and QA reports
both repeat the stale `25`.

Auditor-verified counts, read-only (`sqlite3 "file:data/trendora.db?mode=ro"`), taken AFTER every lane
including this audit's own:

| Table | True count at audit close |
|---|---|
| `next_session_manifests` | **26** |
| `scanner_runs` | 3128 (unchanged) |
| `daily_prices` | 3,310,374 (unchanged) |

The added row is `id=26, as_of='2019-03-01', version=1, mode='retrospective', frozen=1,
prospective_eligible=0` — correctly classified, no incident date involved, AG-12/AG-17 intact. The 7
manifest-less incident dates still hold **0** manifest rows. See finding B2 of
`docs/handoffs/goal-market-compass-iter-27-audit.md` for the scope assessment.
