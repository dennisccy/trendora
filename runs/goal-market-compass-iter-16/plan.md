# goal-market-compass-iter-16 Execution Plan

Alignment check against `docs/goal.md`: the phase spec is a faithful transcription of the two new
owner rulings at J-11 step 11 ("AVB two-row raw-volume correction before Stage D" and "pre-boot
incident guard required", both 2026-08-25) — scope, formula, sequencing, and the unconditional STOP
all match the goal document verbatim. No drift found; nothing here goes beyond what the owner
authorized. This iteration builds directly on iter-13 (Stage C bounded clear — the CLI confirm-gate
pattern this iteration's script must mirror), iter-14 (Stage D preflight/certified-baseline pipeline
that Goal 5 extends), and iter-15 (the AVB diagnostic + provider-fetch evidence + `bridge_factor` that
Goal 2's derivation reuses, and the `AVB-C`/`ready: false` verdict Goal 8 re-runs from a corrected
baseline).

## What to Build

Owner-ordered sequence (binding, do not reorder): **AVB bounded correction → verify new certified
raw-input baseline → build and prove the fail-closed pre-boot guard → re-run Stage D readiness → STOP
unconditionally**, even on `READY: YES`.

- **Goal 1 — True-start safety envelope.** Read-only `stat` (mtime/size/`-wal`) + targeted indexed
  queries reconfirming the coordinator's posted baseline (db file stats, `daily_prices`/`scanner_runs`/
  `forward_returns`/`data_provider_runs`/`next_session_manifests`/`watchlist` counts, all 11 incident
  dates at zero runs, the two AVB target rows' exact OHLCV) plus three isolating hashes (AVB OHLC-only,
  AVB-other-dates-full-row, non-AVB-full-row) and the manifest DDL + row-dump fingerprints, every recipe
  stated. Persist `runs/goal-market-compass-iter-16/j11-avb-correction-true-start.json`. Any mismatch
  against the coordinator's or the spec's own posted values (TC-1 through TC-5) is reported explicitly,
  never silently reconciled — do not copy the spec's hex values uncritically; re-derive them.
- **Goal 2 — Derive the correction deterministically; fail closed before any write.** New pure/read-only
  module reading ONLY `runs/goal-market-compass-iter-15/j11-avb-provider-fetch-evidence.json` and the
  persisted J-10 `bridge_factor` (via `j11_avb_diagnostic.load_j10_avb_evidence`, reused not re-derived).
  Computes `corrected_volume(date) = provider_volume(date) / bridge_factor` for 2026-08-11/12 with one
  documented, consistently-applied rounding rule (whole-share convention is a reasonable default, not a
  mandate). Cross-verify BEFORE any write: `dollar_volume_ratio` for both dates must land within the same
  relative-tolerance band the calibration window (08-05/06/07/10) already passes. **Re-derive the formula
  independently — do not just accept the coordinator's stated inverse relationship as given.** If evidence
  is missing/insufficient or the cross-check fails, fail closed: do not proceed to Goal 3, persist the
  failed-verification evidence, state plainly that owner review is needed. Persist
  `j11-avb-correction-derivation.json` before Goal 3 runs.
- **Goal 3 — The ONE authorized live write.** New `--confirm`-gated CLI script, required
  `--evidence-dir`/`--output-path` with NO default, refusing (non-zero exit, no DB engine/session
  construction, nothing written) if either is omitted — apply the guard from the start, mirroring
  `run_j11_stage_c_bounded_clear.py`'s established idiom exactly (see iter-13/iter-14 handoffs: the
  omitted-flag footgun that silently overwrote committed evidence is exactly what this guard prevents).
  One bounded `UPDATE` scoped to `WHERE symbol='AVB' AND date IN ('2026-08-11','2026-08-12')`, `volume`
  column only. One controlled writer; no application boot; no second writer of any kind.
- **Goal 4 — True-end envelope + mutation-isolation proof.** Re-run every Goal-1 measurement; prove OHLC
  byte-identical on both rows, `volume` equals Goal 2's corrected value; `daily_prices`
  row_count/min_date/max_date/id_sum unchanged; `ohlcv_sum` shifted by EXACTLY the two-date corrected-minus-
  stored delta (arithmetic check, not just "the hash changed"); all three isolating hashes byte-identical;
  `scanner_runs` (by `engine_identity` group AND the exact 34-row `6261ca17…` id set via
  `j11_stage_c.small_table_id_snapshot`), `forward_returns` (total + the 16,614 measured-into-incident
  figure), `data_provider_runs`, manifests (row count + both fingerprints), `watchlist` all unchanged; db
  file mtime/size MOVED (real write happened), `-wal` back to 0 (checkpointed). Persist true-end +
  a consolidated `j11-avb-correction-mutation-evidence.json`.
- **Goal 5 — New certified J-11 raw-input baseline.** Extend/wrap `j11_stage_d.
  load_stage_d_certified_baseline` so ONLY its `daily_prices_fingerprint` field is superseded by the
  post-correction fingerprint, carrying explicit provenance (iteration number, mutation-evidence artifact
  pointer, pre/post fingerprint values, the "Raw inputs" amendment cited by name). Every OTHER composed
  field (`manifest_ddl`, `manifest_dump`, `manifest_row_count`, `data_provider_runs_count`,
  `watchlist_count`) keeps sourcing UNCHANGED from the original iteration-13 artifacts — this is an honest
  supersession of one field, not a re-derivation of the whole baseline. Prove
  `compare_stage_d_preflight_to_certified` reports `daily_prices_fingerprint_unchanged: False` (expected,
  honest) against the OLD baseline and `True` again (every other check also `True`) against the NEW one.
  Persist `j11-stage-d-certified-baseline.json`.
- **Goal 6 — Fail-closed, state-driven pre-boot guard.** Wire into the ONE call site
  (`main.py:100` → `warmup.ensure_latest_snapshot` → `run_scan`, between `latest_data_date` resolving and
  `run_scan` executing — see `apps/backend/app/engine/warmup.py:88-93`): if the resolved latest date falls
  inside an ACTIVE quarantine boundary, skip the write, log an actionable message naming the date + reason,
  return `None` (the SAME shape `ensure_latest_snapshot` already returns for an empty DB). Once cleared, or
  when no boundary is registered, behavior is BYTE-IDENTICAL to today's unmodified function.
  **Design constraint that is easy to get wrong:** the date-set's PRODUCTION membership must come from the
  existing `j11_maintenance.INCIDENT_DATES` (never a fresh literal), but the guard's runtime decision must
  read from persisted STATE (not a hardcoded `if date in INCIDENT_DATES` conditional) — a fixture test must
  be able to change the registered date-set or the active/cleared flag and see the guard's behavior change
  WITHOUT touching the guard's own source (TC-26). The active/cleared flag must be an EXPLICIT persisted
  marker, never inferred from partial per-date `ScannerRun` presence (a partially-completed future attempt
  must still read as blocked). If a new table is added it is purely additive via the existing
  `create_db_and_tables` convention; any new numeric threshold goes in `config.yaml` (no magic numbers) —
  the guard may well need none if it is purely boolean/state-driven.
- **Goal 7 — Prove the guard on disposable fixtures only.** Fixture/in-memory SQLite only — never
  `apps/backend/data/trendora.db`, the live backend is never booted. Cover: refuses inside an active
  boundary (actionable log); allows once cleared (byte-identical to unmodified behavior); no-op when no
  boundary registered (the common no-incident case every other journey's boot depends on); genuinely
  state-driven (fixture-only changes flip behavior); fails CLOSED on missing/unreadable/ambiguous state;
  stays blocked on a simulated partial 11-date attempt (some dates already carry a `ScannerRun`) — driven
  by the explicit flag, never per-date inference.
- **Goal 8 — Re-run Stage D readiness against the corrected, newly-certified baseline.** Re-execute the
  existing pipeline UNCHANGED (`fetch_avb_stored_series`, `classify_local_convention_with_volume_evidence`,
  the decision-impact trace, `classify_avb`, `stage_d_readiness_verdict`,
  `produce_stage_d_readiness_artifact`) against the corrected live `daily_prices` (reads the correction
  naturally — no `volume_override` substitution needed now that the write is real) and Goal 5's new
  baseline, reusing iter-15's provider evidence (zero new fetches). The classification/`ready` value must
  be reached mechanically — do not hand-select or pre-commit a label. Write
  `runs/goal-market-compass-iter-16/j11-stage-d-readiness.json` with `authorized: false` unconditionally.
  Print the literal `J-11 STAGE D READY: YES/NO` line (verbatim from the artifact) and the unconditional
  `J-11 STAGE D AUTHORIZED: NO` line. Cite iteration-15's own readiness artifact (`AVB-C`, `ready: false`)
  as historically accurate for the PRE-correction state — never edited, never deleted. **Regardless of
  outcome, no Stage D work is planned or performed, and the iteration STOPS here.**
- **Housekeeping.** `git status --porcelain` clean on `runs/goal-market-compass-iter-9/` through
  `-iter-15/` after the full targeted test run; commit this iteration's new code/tests/evidence. Fixture-
  only unit tests for every new function (never the live DB as a test fixture, except the one deliberate
  live-write mutation-evidence test); CLI control-flow tests mirroring `test_j11_stage_c_cli_script.py`'s
  `unittest.mock` pattern.

**Guardrails (binding, restated from the spec's OUT OF SCOPE):** Stage D itself, Stage E/F/G, any re-run
of Stage C/B1, any new network fetch, any correction outside `daily_prices.volume`/AVB/08-11+08-12, any
touch to `scanner_runs`/`scanner_results`/`sector_scores`/`theme_scores`/`forward_returns`/
`data_provider_runs`/`watchlist`/manifests, booting the live backend (including the guard's own tests),
any full copy of `trendora.db`, hand-picking the AVB classification or `ready` verdict, and planning or
scoping a future Stage-D iteration — ALL are out of scope even if Goal 8 returns `READY: YES`. Targeted
test files only; never the full backend suite; never two pytest processes concurrently (resource
contract — this host has frozen before). Any long-running check: foreground `setsid nohup ... &`, poll
with bounded sleeps, do not end the turn early.

## Agents Required
- developer: yes -- backend-only implementation (no frontend agent needed): the correction module +
  confirm-gated script, the pre-boot guard + its one `warmup.py` call-site wiring, the certified-baseline
  supersession, the Stage D readiness re-run, fixture-only tests, and the dev handoff.
- backend-data: yes -- all 8 goals are backend/data-layer work, including the one authorized live
  `daily_prices.volume` write (via the confirm-gated script only, never a booted service).
- frontend-ux: no -- no frontend file is touched; maintenance isolation forbids any application-service/
  browser/replay lane this iteration.

## Frontend Present
no

## Files to Create/Modify

New:
- `apps/backend/app/engine/j11_avb_correction.py` -- Goals 1/2/4: true-start/true-end capture helpers,
  the derivation function (no network dependency), the `dollar_volume_ratio` cross-check, the mutation-
  evidence comparison builder. Pure/read-only computation only -- the actual `UPDATE` statement lives in
  the CLI script (mirrors the `j11_stage_c.py` / `run_j11_stage_c_bounded_clear.py` split).
- `apps/backend/scripts/run_j11_avb_correction.py` -- Goal 3: the one `--confirm`-gated CLI script,
  required `--evidence-dir`/`--output-path` with no default.
- `apps/backend/app/engine/j11_preboot_guard.py` (illustrative name; extending `j11_maintenance.py` is
  also acceptable per the spec's own "e.g." hedge -- developer's call) -- Goals 6/7: the boundary state
  representation (date-set + explicit active/cleared marker) and the guarded check function.
- `apps/backend/tests/test_j11_avb_correction.py` -- Goals 1-4: fixture-only derivation/cross-check tests
  plus the one live-DB mutation-evidence test proving the write's exact scope.
- `apps/backend/tests/test_j11_preboot_guard.py` -- Goals 6-7: exclusively fixture/in-memory SQLite.
- `apps/backend/tests/test_j11_avb_correction_cli_script.py` (illustrative name; extending
  `test_j11_stage_d_cli_scripts.py` is also acceptable) -- Goal 3's refusal + confirm-gated CLI tests,
  mirroring `test_j11_stage_c_cli_script.py`'s `unittest.mock` pattern.
- `runs/goal-market-compass-iter-16/j11-avb-correction-true-start.json`,
  `j11-avb-correction-derivation.json`, `j11-avb-correction-true-end.json`,
  `j11-avb-correction-mutation-evidence.json`, `j11-stage-d-certified-baseline.json`,
  `j11-stage-d-readiness.json` -- the required evidence artifacts (Goals 1/2/4/5/8); additional supporting
  capture files (e.g. a fresh Stage D preflight re-capture used as Goal 5/8's comparison input) as the
  developer's implementation needs, named consistently with the iter-13/14/15 convention.

Modified:
- `apps/backend/app/engine/j11_stage_d.py` -- Goal 5: a supersession function wrapping
  `load_stage_d_certified_baseline` (see its exact composition at `j11_stage_d.py:341-382` and the
  comparison consumer at `:385-441` -- only `certified["daily_prices_fingerprint"]` may change).
- `apps/backend/app/engine/warmup.py` -- Goal 6: the guard check inserted into `ensure_latest_snapshot`
  (`warmup.py:88-93`) between resolving `latest` and calling `run_scan`.
- `apps/backend/app/models.py` + `apps/backend/app/db.py` -- Goal 6, ONLY if a new persisted state table
  is added: additive `SQLModel` table + idempotent wiring into `create_db_and_tables` (`db.py:226`).
- `apps/backend/scripts/run_j11_stage_d_preflight.py` and/or `run_j11_avb_bridge_diagnostic.py` and/or
  `run_j11_stage_d_readiness.py` -- Goal 8: extend additively (e.g. an optional
  `--avb-correction-baseline-path`-style flag) to compose Goal 5's superseded baseline instead of the raw
  iteration-13 pair, OR add one new thin iteration-16 driver script -- developer's choice, but the
  underlying engine functions must be reused unchanged, never reimplemented.
- `apps/backend/tests/test_j11_stage_d.py` -- extended for Goal 5's baseline-supersession comparison and
  Goal 8's re-run.
- `config.yaml` -- ONLY if Goal 6's guard introduces a new numeric threshold (e.g. a staleness bound);
  purely additive.

Reused unchanged (do not reimplement): `j11_maintenance.INCIDENT_DATES` /
`capture_pre_reset_inventory`; `j11_stage_c.small_table_id_snapshot`; `j11_avb_diagnostic.
load_j10_avb_evidence` / `fetch_avb_stored_series` / `classify_local_convention_with_volume_evidence` /
`trace_universe_resolver_impact` / `trace_scoring_and_selection_impact` / `classify_avb`; `j11_stage_d.
compare_stage_d_preflight_to_certified` / `stage_d_readiness_verdict` / `produce_stage_d_readiness_
artifact` / `capture_stage_d_preflight`; `engine_identity.compute_engine_identity`.

## Key Test Scenarios

- True-start capture matches (or explicitly, honestly reports any mismatch against) the coordinator's
  posted baseline: db mtime/size/`-wal`=0, all six table counts, all 11 incident dates at zero runs, both
  AVB target rows' exact OHLCV, and all three isolating hashes equal the spec's posted targets exactly.
- Derivation `corrected_volume = provider_volume / bridge_factor` is independently re-derived (not copied
  from the coordinator's note), and the post-correction `dollar_volume_ratio` cross-check lands within the
  same tolerance the four calibration dates already pass, persisted BEFORE any write.
- Fail-closed path: missing/insufficient evidence or an out-of-tolerance cross-check withholds the write
  entirely, mutates nothing, and the dev handoff says plainly that owner review is needed.
- CLI refusal: the script invoked without `--confirm` and/or without its required evidence path exits
  non-zero before any DB engine/session construction and touches neither DB nor network.
- The one write is a single `UPDATE` scoped to exactly `symbol='AVB' AND date IN ('2026-08-11',
  '2026-08-12')`, `volume` column only -- grep-verifiable, no other column/table/row/unbounded WHERE
  anywhere in the write path.
- True-end proof: OHLC byte-identical on both rows; `volume` equals the corrected value; `daily_prices`
  row_count/min/max/id_sum unchanged; `ohlcv_sum` shifted by EXACTLY the two-date delta (arithmetic check);
  all three isolating hashes unchanged; `scanner_runs`/`forward_returns`/`data_provider_runs`/manifests/
  `watchlist` all unchanged; db file mtime/size moved, `-wal` back to 0.
- New certified baseline supersedes ONLY `daily_prices_fingerprint` with explicit provenance; every other
  composed field is byte-sourced, unchanged, from the iteration-13 artifacts; the compare gate reports
  `False` (honest, expected) against the OLD baseline and `True` (every other check also `True`) against
  the NEW one.
- Guard: refuses a write for a date inside an active boundary (actionable log naming date + reason);
  allows once the SAME boundary is cleared (byte-identical to unmodified `ensure_latest_snapshot`); is a
  true no-op when no boundary is registered; changing ONLY fixture state (never guard source) flips
  refuse/allow behavior; fails CLOSED on missing/unreadable/ambiguous state; stays blocked on a simulated
  partial 11-date attempt where some dates already carry a `ScannerRun`, driven by the explicit flag, never
  per-date inference.
- Guard integration tests use direct function calls or fixture-scoped isolated engines only -- the live
  backend and `apps/backend/data/trendora.db` are never opened by the guard's own tests; any new table is
  created idempotently via `create_db_and_tables`, and a second run is a no-op.
- Readiness re-run reaches its AVB classification and `ready` value mechanically from the corrected live
  data (never hand-picked); `produce_stage_d_readiness_artifact` writes `authorized: false`
  unconditionally; both literal `READY`/`AUTHORIZED: NO` lines are printed verbatim from the artifact; no
  Stage D work is planned or performed regardless of outcome; iteration-15's readiness artifact is cited
  as historically accurate pre-correction, never edited or deleted.
- `git status --porcelain` returns zero lines on every `runs/goal-market-compass-iter-9/` through
  `-iter-15/` directory touched by this iteration's tests; this iteration's own new code/tests/evidence are
  committed to git.
