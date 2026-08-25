# goal-market-compass-iter-15 Execution Plan

Goal alignment: this iteration adds no Key Capability and touches no Data Contract row — it
diagnoses and reconciles J-11 Stage D readiness (docs/goal.md J-11, Stage D still unauthorized).
The phase spec's own OUT OF SCOPE section is already self-policing (no Stage D/E/F/G execution,
no J-10 reopening, no full suite, no hardcoded classification); no drift or scope creep found
against docs/goal.md's constraints (no-magic-numbers, AG-1/AG-9/AG-12/AG-17). This plan adds no
new constraint and does not self-declare depth/maintenance-isolation lines — those stay
operator-set per the spec's own BACKGROUND policy note.

## What to Build
- **Goal 1 — reconcile iter-14's contradiction.** New read-only `reconcile_prior_iteration_truth`
  re-derives live-DB truth (11 incident dates, `daily_prices`/`scanner_runs`/`forward_returns`/
  `data_provider_runs`/manifests/`watchlist`/AVB fingerprint) against the owner's true-start
  capture; loads iter-14's stale `AVB-B`/`ready:true` JSON verbatim, quotes `iter-14/eval.md`'s
  corrected `J-11 STAGE D READY: NO`, and writes a NEW artifact marking the old one superseded.
  iter-13/iter-14 evidence dirs stay byte-untouched (confirmed clean today).
- **Goal 2 — the one authorized AG-9 exception #2 fetch.** New narrow module + script fetch AVB
  close/volume for exactly six named dates via the real Yahoo provider, exactly once, fail-closed
  (never guesses) on shortfall/error; full auditable provenance persisted to a NEW iteration-15
  artifact only (no DB write, no other call site anywhere in the diff may construct a live
  provider).
- **Goal 3 — fix the tautology.** `compute_counterfactual_representations` sources
  representation B's volume (and preferentially its close) from FETCHED evidence, never a copy of
  stored volume; per-date comparison metrics (`close_ratio`, `volume_ratio`,
  `expected_inverse_volume_ratio`, dollar-volume compensation test) computed for all six dates so
  `bridged+compensating`/`bridged+raw` become genuinely reachable.
- **Goal 4 — fix the classifier.** `classify_avb` re-fed by genuine volume evidence; all four
  labels (A/B/C/D) mechanically reachable from real fixtures, none hardcoded or pre-selected.
- **Goal 5 — re-run the decision-impact trace** through the UNCHANGED canonical
  scoring/universe-resolver modules against the proven representation (close AND volume both
  substitutable), still read-only/in-memory; state plainly if today's stored representation turns
  out wrong, never silently correct it.
- **Goal 6 — close the two footgun scripts.** `run_j11_stage_d_preflight.py` and
  `run_j11_avb_bridge_diagnostic.py` get a required output path (`default=None`), refusing before
  any DB/engine construction — mirror the already-fixed `run_j11_stage_c_bounded_clear.py` pattern
  exactly; every NEW script this iteration adds carries the identical guard from the start.
- **Goal 7 — a committed readiness producer.** `produce_stage_d_readiness_artifact` (+ CLI
  script) becomes the first real producer of the readiness JSON outside a test; fails closed on
  missing/unknown/mutually-stale inputs; `authorized: false` unconditionally.
- **Goal 8 — harden negative test coverage.** 8 new one-field-perturbation fixture tests for
  `compare_stage_d_preflight_to_certified` checks that currently have none.
- **Goal 9 — attempt-identity honesty.** Label this iteration's identity re-derivation
  `readiness_time_only`/non-authorizing/non-reusable; honestly compare against iter-14's frozen
  `53d2ffd1…`; `freeze_stage_d_attempt_identity` itself stays path-param-free and unchanged for a
  real future Stage D freeze.
- **Goal 10 — final consistent verdict.** Run the now-fixed scripts end to end against
  `runs/goal-market-compass-iter-15/` to produce this iteration's own `j11-stage-d-readiness.json`;
  every lane (dev handoff/review/QA/audit) quotes that ONE artifact's `ready` value; iter-14's
  file explicitly named superseded.
- **Whole-iteration zero-live-write proof** (TRUE-start/TRUE-end db mtime+size+WAL, `ScannerRun`
  counts + exact 34-id-set, all-11-incident-dates-zero, `daily_prices`/manifest/16,614-row
  figures) bracketing every script this iteration runs, not just one.
- Fixture-only unit tests for every new/changed function; new/extended CLI control-flow tests for
  all four touched/added scripts; commit code+tests+evidence to git; dev handoff at
  `docs/handoffs/goal-market-compass-iter-15-dev.md` closing with the literal
  `J-11 STAGE D READY: YES/NO` and unconditional `J-11 STAGE D AUTHORIZED: NO`.

## Hard Constraints (binding on every downstream agent)
- **Stage D itself is NEVER executed this iteration, under any outcome** — no `scanner.run_scan`,
  no `persist_run_payload`, no `ScannerRun`/`ForwardReturn` write. Even
  `J-11 STAGE D READY: YES` still ends with `J-11 STAGE D AUTHORIZED: NO`.
- **Read-only against `apps/backend/data/trendora.db`** except the one carve-out: AG-9 dated
  exception #2 authorizes exactly one bounded fetch — symbol `AVB` only, dates
  `2026-08-05/06/07/10/11/12` only, fields `date`/`close`/`volume` only, via the canonical Yahoo
  provider path, called at most once, never written to any DB table. Insufficient evidence
  classifies **AVB-D** and stops — never a guess, never a broadened fetch, never an adjacent-day
  substitute.
- No boot of backend/frontend, no browser, no full pytest suite, no two pytest processes
  concurrently (maintenance isolation active, operator-set — do not self-declare it in any
  artifact this iteration writes).
- `runs/goal-market-compass-iter-13/` and `runs/goal-market-compass-iter-14/` must remain
  byte-identical / `git status --porcelain` clean throughout — every script's evidence-path
  argument must be explicit, never a default pointing into either directory.
- No hand-picked/hardcoded classification or `ready` verdict anywhere — every label must be
  mechanically reachable from real evidence; fail closed on ambiguity or missing evidence.

## Agents Required
- developer: yes -- implement Goals 1-10 (new fetch module + two CLI scripts, diagnostic/
  classifier fixes, readiness producer, footgun-guard fixes on two existing scripts, reconciliation
  function, identity-labeling fields), the fixture/CLI tests below, run the fixed scripts
  read-only against the live DB to produce this iteration's evidence artifacts, and write the dev
  handoff. No frontend work.

## Frontend Present
no

## Files to Create/Modify

New:
- `apps/backend/app/engine/j11_avb_provider_fetch.py` -- Goal 2: symbol/date constants, an
  injected-`PriceProvider` fetch function (calls `.get_daily` exactly once), fail-closed on
  `ProviderUnavailableError`/`RateLimitError`/a short return.
- `apps/backend/scripts/run_j11_avb_provider_fetch.py` -- Goal 2 CLI: constructs a real
  `YahooProvider()`, required `--output-path` (no default), no DB engine/session anywhere in
  `main()`.
- `apps/backend/scripts/run_j11_stage_d_readiness.py` -- Goal 7 CLI: same required-path guard,
  wired to `produce_stage_d_readiness_artifact`, prints the literal
  `J-11 STAGE D READY:`/`J-11 STAGE D AUTHORIZED: NO` lines.
- `apps/backend/tests/test_j11_avb_provider_fetch.py` -- Goal 2 fixture/mock-provider tests
  (TC-5..TC-9); never a real network call.
- A new CLI-script test file (e.g. `apps/backend/tests/test_j11_stage_d_cli_scripts.py`)
  mirroring `test_j11_stage_c_cli_script.py`'s import-as-module + monkeypatch pattern -- covers
  all four touched/added scripts' required-path refusal and control flow (TC-8, TC-9, TC-25..TC-29).
- `runs/goal-market-compass-iter-15/j11-iteration-14-truth-reconciliation.json` -- Goal 1's NEW
  reconciliation artifact (machine-produced, never hand-typed).
- This iteration's own evidence set under `runs/goal-market-compass-iter-15/`: AVB fetch
  evidence, AVB bridge diagnostic, Stage D attempt-identity/preflight/preflight-gate, db-file
  true-start/true-end fingerprints, and the final `j11-stage-d-readiness.json` -- all produced by
  running the Goal-6-fixed scripts, never hand-authored.
- Optional: a standalone reconciliation CLI script for Goal 1, if the developer chooses not to
  run it inline -- must carry the identical required-output-path guard as every other new script
  this iteration.

Modify:
- `apps/backend/app/engine/j11_avb_diagnostic.py` -- Goal 3/4/5: `compute_counterfactual_
  representations` takes fetched `provider_close`/`provider_volume` (fail-closed per date when
  absent, never a stored-volume copy); extend `classify_local_convention` (or a volume-aware
  successor) with the per-date comparison record + a new named, documented tolerance constant
  (module-level, join the `_CONTINUITY_JUMP_THRESHOLD`-style `test_no_magic_numbers.CALC_FILES`
  exclusion); `classify_avb` reasoning cites the fetched comparison;
  `trace_universe_resolver_impact`/`trace_scoring_and_selection_impact`/
  `_build_bars_with_transformed_close` gain an optional per-date volume override.
- `apps/backend/app/engine/j11_stage_d.py` -- Goal 7: new `produce_stage_d_readiness_artifact
  (preflight_gate_path, avb_diagnostic_path, *, output_path)`, fail-closed per TC-31/32/33, calls
  the existing `stage_d_readiness_verdict` unchanged. Goal 1: new
  `reconcile_prior_iteration_truth` (the spec's own suggested home; a sibling module is
  acceptable if cleaner), reusing `j11_maintenance.capture_pre_reset_inventory` +
  `j11_schema_migration.fetch_object_ddl`/`dump_table`, never reimplementing. Goal 9: place
  `readiness_time_only`/`authorizing`/`reusable_for_stage_d_execution` at the call-site layer that
  records THIS iteration's observation -- **not** inside `freeze_stage_d_attempt_identity`'s own
  return shape, since TC-39 requires that function stay reusable unchanged (path-param-free) for a
  real future Stage D freeze; confirm exact placement against TC-37/38/39 before implementing.
- `apps/backend/scripts/run_j11_stage_d_preflight.py` -- Goal 6: `--evidence-dir` becomes
  `default=None` with a refuse-before-`load_config` guard (mirror `run_j11_stage_c_bounded_
  clear.py`'s existing pattern exactly, i.e. the None-check must run before `cfg = load_config()`,
  not after); this iteration's runs pass `--evidence-dir runs/goal-market-compass-iter-15`
  explicitly.
- `apps/backend/scripts/run_j11_avb_bridge_diagnostic.py` -- Goal 6: `--output-path` becomes
  `default=None` with the same refuse-before-engine-construction guard. Goal 2/3: new required
  `--provider-fetch-evidence-path`; restructure the representation/classification loop to run
  over all six permitted dates (not only `RECOVERED_DATES`, as it does today) using the fetched
  evidence; the script itself still performs no network fetch.
- `apps/backend/tests/test_j11_avb_diagnostic.py` -- extend for TC-11..TC-24 (fetched-volume-
  driven representations, a genuine `volume_a_equals_b` False case, a fail-closed missing-evidence
  case, `bridged+compensating`/`bridged+raw` reachability, all four `classify_avb` labels, the
  in-memory trace with a volume override).
- `apps/backend/tests/test_j11_stage_d.py` -- extend for TC-30..TC-39 (readiness-producer
  fail-closed cases, identity re-derivation labeling/comparison) and Goal 8's 8 new
  one-field-perturbation negative tests (TC-34), re-running `test_tc_id_1..6` and the existing
  `daily_prices_fingerprint`/`all_incident_dates_zero_scanner_runs` negative tests unmodified
  (TC-35/36) alongside them.
- Confirm only (likely no change needed) -- `apps/backend/tests/test_no_magic_numbers.py`: verify
  the new tolerance constant lands under `j11_avb_diagnostic.py`'s existing `CALC_FILES`
  exclusion rather than adding a fresh one.

Reused unchanged (do not modify): `apps/backend/app/engine/j11_maintenance.py`,
`j11_schema_migration.py`, `j11_stage_c.py`; `runs/goal-market-compass-iter-13/*`,
`runs/goal-market-compass-iter-14/*` (byte-preserved throughout).

## UI Evolution
N/A -- Frontend Present: no. No page, nav entry, or served value changes this iteration.

## Visual Requirements
N/A -- Frontend Present: no.

## Key Test Scenarios
- TC-1/TC-2/TC-3: reconciliation artifact records every re-derived figure's match/mismatch
  against the owner's true-start capture and the 16,614 forward-return total; explicitly marks
  iter-14's `AVB-B`/`ready:true` artifact `stale_artifact_superseded: true` without touching the
  file itself.
- TC-4/TC-29: `git status --porcelain` on `runs/goal-market-compass-iter-13/` and `iter-14/`
  returns zero lines after the full targeted test run.
- TC-5/TC-7/TC-9: the AVB fetch calls `.get_daily` exactly once for the six permitted dates; a
  short/failed fetch never substitutes adjacent-day data and records `sufficient_evidence: false`;
  the fetch script constructs no DB engine/session at all.
- TC-12/TC-13/TC-14/TC-15: `volume_a_equals_b` is provably `False` in a fixture where
  `provider_volume != stored_volume`; a date with unavailable fetched evidence fails closed
  rather than falling back to the old arithmetic; `bridged+compensating` and `bridged+raw` are
  each genuinely reachable from real evidence shapes (exercised, not merely asserted).
- TC-17..TC-21: all four `classify_avb` labels (A/B/C/D) are independently reachable from their
  own fixture; none hardcoded.
- TC-22..TC-24: the decision-impact trace re-run is read-only/in-memory (zero `ScannerRun`/
  persist calls) and states plainly if the proven convention diverges from what's currently
  stored.
- TC-25/TC-26/TC-27/TC-28: all four scripts (`run_j11_stage_d_preflight.py`,
  `run_j11_avb_bridge_diagnostic.py`, `run_j11_avb_provider_fetch.py`,
  `run_j11_stage_d_readiness.py`) refuse before any DB/network access when their required path is
  omitted, and write only under `tmp_path` in tests.
- TC-30..TC-33: `produce_stage_d_readiness_artifact` fails closed on a missing/unreadable
  preflight path, an unknown AVB classification, and mutually-stale inputs.
- TC-34/TC-35/TC-36: each of the 8 newly-tested preconditions fails via its own
  single-field-perturbation fixture; the pre-existing identity and negative tests still pass
  unmodified alongside them; no test touches the 34 `6261ca17…` rows or the NULL-stamped rows.
- TC-37/TC-38/TC-39: this iteration's re-derived identity is honestly compared against iter-14's
  `53d2ffd1…` (equal or drifted, stated plainly) and labeled non-authorizing/non-reusable;
  `freeze_stage_d_attempt_identity` takes no path parameter.
- TC-40/TC-41/TC-42: `run_j11_stage_d_readiness.py` prints the literal `ready` value from the one
  committed artifact (never re-typed); every lane quotes the same value from the same file;
  iter-14's artifact is explicitly named superseded.
- TC-43..TC-46: whole-iteration db mtime/size/WAL, `ScannerRun` counts + exact 34-id-set,
  all-11-incident-dates-zero, and `daily_prices`/manifest/forward-return figures are
  byte-identical at TRUE start and TRUE end.
