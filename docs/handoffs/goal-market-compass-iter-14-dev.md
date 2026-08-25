# goal-market-compass-iter-14 Dev Handoff

**Phase:** goal-market-compass-iter-14 (J-11 Stage D readiness hardening)
**Date:** 2026-08-24
**Agent:** developer
**Status:** complete

## Governing contract

Non-destructive, read-only-against-the-live-DB hardening iteration. Stage D itself (canonical
regeneration of the 11 incident dates) is **NOT authorized and was NOT executed**. Zero writes to
`apps/backend/data/trendora.db` — proven below.

## What Was Built

- **Goal 1 — Fresh Stage D attempt identity.** `app.engine.j11_stage_d.freeze_stage_d_attempt_identity`
  wraps `j11_maintenance.freeze_attempt_identity`, re-derives the identity fresh via
  `app.engine.engine_identity.compute_engine_identity` (never hardcodes iteration 10's `6261ca17…` or
  iteration 13's `53d2ffd1…`), and assembles the attempt-identity artifact with attempt id, frozen
  timestamp, `engine_identity`, `config_subset_hash`, `config_subset`, `provenance.engine_files`,
  `provenance.config_keys`, git HEAD, the J-11 contract hash, and the 11-date `INCIDENT_DATES` set. Persisted
  to `runs/goal-market-compass-iter-14/j11-stage-d-attempt-identity.json`.
  **Frozen value: `engine_identity = 53d2ffd10cdbf89ef16681111bd900766e00e5809bc4ebc7d4b5f2bf1b7f6c55`**
  — **honestly recorded as evidence, not drifted again**: it is byte-identical to iteration 13's already-
  drifted-from-`6261ca17…` value, meaning `provenance.engine_files` has not changed since iteration 13.
  `attempt_id = j11-stage-d-20260824T215449974250Z`, `git_head = 1b869561c7b6146662b41fce2b571113ddff6e53`.
- **Goal 2 — Three fail-closed identity COMPARE checks.** `check_identity_before_first_write` (A),
  `check_identity_before_date` (B), `check_identity_after_persist` (C) — each wraps
  `j11_maintenance.check_attempt_identity_consistency` (reused, never reimplemented) and returns a
  per-call evidence record. (B) and (C) take an explicit `date` and vacuously PASS
  (`in_scope: False`, no comparison performed) for any date outside `INCIDENT_DATES` — implementing the
  step-12 clarification's "the 34 surviving runs … are not members of the new 11-date attempt" as
  first-class code behavior (TC-ID-6), not just an operational habit. Built and fixture-unit-tested only
  — never invoked against the live DB or a regeneration loop.
- **Goal 3a — Stage D preflight gate, executed live read-only.** `capture_stage_d_preflight` +
  `compare_stage_d_preflight_to_certified` + `stage_d_preflight_verdict`. The certified baseline
  (`load_stage_d_certified_baseline`) composes from TWO already-persisted iteration-13 artifacts:
  `j11-stage-c-preflight.json` for the manifest DDL/dump (captured pre-delete, proven byte-identical
  post-delete by iteration 13's own `manifests_unchanged: true` mutation-accounting check — the loader
  raises if that proof isn't present) and `j11-stage-c-mutation-accounting.json` for the actual post-delete
  `daily_prices`/`data_provider_runs`/`watchlist` figures. Executed live via
  `apps/backend/scripts/run_j11_stage_d_preflight.py` (new; not explicitly named in the plan's file list,
  but required to run Goal 3a live per the spec's own instruction — added as additive tooling, mirroring
  every other live-capture script's read-only-handle idiom). **Result: ALL 11 checks pass**
  (`all_invariants_hold: true`) — see `runs/goal-market-compass-iter-14/j11-stage-d-preflight-gate.json`.
- **Goal 3b — Missing negative/precondition tests.** Verified each named item against current code
  FIRST. All items correspond to real, already-existing checks in `j11_stage_c.compare_preflight_to_
  certified` (manifest DDL/index/value drift, `source_run_id` drift, `daily_prices`/`data_provider_runs`/
  `watchlist` drift) **except** "unexpected incident ScannerRun population," which is a genuinely NEW
  Stage-D-specific precondition (Stage C has no "zero runs" concept) — built as
  `all_incident_dates_zero_scanner_runs` inside `j11_stage_d.compare_stage_d_preflight_to_certified`.
  **No item required inventing a fictitious gate** — every named negative test maps to real code.
  Added: `test_j11_stage_c_preflight.py` TC-14..18 (7 new tests exercising the previously-untested
  `compare_preflight_to_certified` checks), `test_j11_stage_c_cli_script.py` (new — `unittest.mock`
  control-flow tests for `run_j11_stage_c_bounded_clear.py`'s `main()`), `test_j11_stage_d.py`'s TC-19
  (the Stage-D-specific zero-runs precondition).
- **Goal 4 — Read-only AVB bridge/volume diagnostic.** `app.engine.j11_avb_diagnostic` (pure/read-only)
  + `apps/backend/scripts/run_j11_avb_bridge_diagnostic.py` (read-only SQLite handle, no `--confirm`
  needed — zero writes). Re-derives the bridge factor (`2.7930001225759193`) and 4 calibration pairs
  (2026-08-05/06/07/10) from `runs/goal-market-compass-iter-9/j10-population-evidence.json` — verbatim
  reproduction, never re-fetched. **New finding, independently re-derived and worth flagging**: of the
  566 pool symbols the J-10 evidence computed a `bridge_factor` for, **AVB is the ONLY one materially
  different from 1.0** (every other symbol is a raw+raw pass-through) — this is what makes the
  classification question real. Full results in `runs/goal-market-compass-iter-14/j11-avb-bridge-
  diagnostic.json`.
- **Goal 5 — Explicit Stage D readiness verdict.** `stage_d_readiness_verdict` combines Goal 3a's
  preflight-gate verdict with Goal 4's AVB classification (AVB-C/D forces `NO` unconditionally).
  Persisted to `runs/goal-market-compass-iter-14/j11-stage-d-readiness.json`. `authorized: false`
  unconditionally in every branch (never self-authorizing).
- **Whole-iteration zero-live-write proof.** `apps/backend/data/trendora.db` main-file mtime + size and
  `-wal` size captured at the TRUE first live read this iteration performed (the AVB diagnostic script's
  own start) and the TRUE last (the AVB diagnostic script's second, corrected run — see "Bug found and
  fixed" below). **mtime unchanged, size unchanged, WAL empty at both ends** — see
  `runs/goal-market-compass-iter-14/j11-stage-d-db-file-true-start.json` /
  `j11-stage-d-db-file-true-end.json`.
- Fixture-only unit tests for every new function in `j11_stage_d`/`j11_avb_diagnostic`: `test_j11_stage_d.py`
  (25 tests), `test_j11_avb_diagnostic.py` (16 tests).

## Bug found and fixed during test-writing (worth flagging explicitly)

Writing `test_j11_avb_diagnostic.py`'s fixture test for `trace_universe_resolver_impact` caught a **real
correctness bug** in the first draft of that function: it called
`ur.resolve_candidate(bars_real, AVB_SYMBOL, cfg, asof)` **without** passing `bar_count` explicitly, so
`resolve_candidate` defaulted `bar_count = len(bars)` — the `adv_window_days`-BOUNDED bar list (63 on the
live config), not AVB's TRUE trailing-bar count (5,396/5,397 on the live DB). Since
`min_history_bars` (200) > `adv_window_days` (63), this silently misreported AVB as `below_history` and
NOT admitted — **the exact opposite of the true, correct result**. Production's own
`resolve_with_reasons` avoids this by computing a full grouped-`COUNT` separately from the bounded bar
fetch and passing it through explicitly (`bars.py` comment: "the bounded fetch changes WHAT IS FETCHED,
never what is COMPUTED or DISCLOSED"). Fixed `trace_universe_resolver_impact` to mirror that exact
two-step pattern (a real `COUNT(*) WHERE date <= asof` query, passed as `bar_count=`). **The live AVB
diagnostic script was re-run after the fix** — the FIRST run's persisted `j11-avb-bridge-diagnostic.json`
was overwritten with the corrected evidence before this handoff was written. The final classification
(AVB-B) is unchanged by the fix (only the previously-wrong `resolution_a`/`resolution_b.admitted`/`bars`
fields were corrected — from `False`/`63`/`below_history` to `True`/`5396`-`5397`/`None`); the ADV dollar
values themselves (`_adv_dollar`, unaffected by the bug) were always correct.

## Live capture results (Goal 3a — Stage D preflight, all against the real `trendora.db`, read-only)

- `all_incident_dates_zero_scanner_runs`: **true** (re-verified independently outside the gate too — see
  "Baseline re-derivation" below).
- `daily_prices_fingerprint_unchanged`: **true** (row_count 3,310,374, matches iter-13's post-Stage-C
  fingerprint `572691772b7313b893055a9ada984945292bbcd07686f4702193a03e9223451a`).
- `manifest_row_count_unchanged` / `manifest_ddl_unchanged` / `manifest_indexes_unchanged` /
  `manifest_values_unchanged` / `source_run_id_values_unchanged`: **all true** (24 rows, full 28-column
  diff against iteration 13's certified dump — zero mismatches).
- `data_provider_runs_count_unchanged` (549) / `watchlist_count_unchanged` (6): **both true**.
- `c1_date_set_boundary_ok`: **true** (code's `INCIDENT_DATES` byte-identical to both `docs/goal.md`
  11-date lists).
- `identity_check_a_ok`: **true** (a second, independent `compute_engine_identity(cfg)` call reproduces
  the just-frozen value).
- `CHAIN_MAINTENANCE_ISOLATION` recorded verbatim in the preflight artifact (presence/value only, no
  interpretation).

## Live capture results (Goal 4 — AVB diagnostic)

- **Bridge factor / calibration pairs**: reproduced exactly (`2.7930001225759193`; 4 pairs, dispersion
  `2.87e-08`).
- **Local-convention classification**: `bridged+raw`, **internally_consistent: true**. The 4 calibration-
  window pairs (2026-08-05/06/07/10 — all NEVER deleted, never touched by J-10) independently show the
  SAME ~2.793x bridge relative to the fallback provider, proving the bridging is a **pre-existing,
  longstanding characteristic of AVB's stored series**, not something J-10's recovery introduced. Zero
  anomalous day-over-day jumps found across 49 checked transitions in the fetched window (2026-06-01
  through the frontier), including zero at the 2026-08-11/12 recovery boundary specifically — no
  discontinuity.
- **Representations A/B/C**: computed for both 2026-08-11 and 2026-08-12. `volume_a_equals_b: true`
  (stated explicitly per date) — confirms J-10 never transformed volume.
- **Decision-impact trace** (both dates), through the named canonical functions:
  - `universe_resolver._adv_dollar`/`resolve_candidate`: ADV ≈ $187.6M (08-11 A) / $184.8M (08-11 B) —
    both comfortably above the $50M `min_dollar_vol` floor. **`admission_changed: false`** both dates.
  - `scoring`'s liquidity component: `liquidity_raw_a_reproduces_served: true` and
    `percentile_a_reproduces_served: true` both dates — an internal cross-check proving the diagnostic's
    narrower re-derivation matches the real `score_stocks` output exactly.
  - Risk score moves marginally (31.14 → 31.23 on 08-11); **`risk_bucket` unchanged (E → E)** both dates.
  - **`setup_status` unchanged, `eligible` unchanged (`False` → `False`, both dates — AVB fails the
    selection rule on OTHER grounds unrelated to liquidity/ADV either way)**.
  - **Pool-wide liquidity-percentile shift**: 4 other pool tickers shift on 08-11, 35 on 08-12 (index
    perturbations of a few thousandths each — AVB's rank moves a handful of positions in a ~539-member
    sorted list; no OTHER individual ticker's Risk bucket/eligibility was checked for a resulting flip,
    since that would require a second full `score_stocks` pass per affected ticker — out of this
    diagnostic's "narrowly as practical" scope, and the percentile deltas involved are index-of-539-scale
    perturbations, not the kind of magnitude that plausibly crosses a bucket edge).
- **Classification: AVB-B** — material effect confirmed (the pool-percentile shifts) but the canonical
  stored convention is proven internally consistent from the stored series itself. Explicit caveat
  recorded; volume was NOT "corrected." **Stage D may proceed per AVB.**

## Baseline re-derivation (owner-specified, re-verified live, read-only)

All matched the coordinator's stated pre-iteration baselines exactly:

| Baseline | Stated | Re-derived |
|---|---|---|
| 11 incident dates: runs/results/sector/theme scores | 0 | 0 (confirmed) |
| `daily_prices` | 3,310,374 | 3,310,374 |
| `scanner_runs` | 3,117 | 3,117 |
| `forward_returns` | 6,797,728 | 6,797,728 |
| `data_provider_runs` | 549 | 549 |
| `next_session_manifests` | 24, DDL sha256 `9f653c81…c501ee` | 24, DDL sha256 `9f653c8147c7c8931b07ea4a88d46ef1d6ddefb2ef5177b700d2b60e7fc501ee` (exact match) |
| `next_session_manifests` full-row sha256 | `bb954b60…a2a2e6` | **exact match** under the method that defines it — `bb954b60187e39a1aa8f59b1bf736be9808e25760d2a0494f176116416d2a2e6` (see below) |
| `watchlist` | 6 | 6 |
| retained-run forward returns measured into incident dates | 16,614 | 16,614 |
| 34 surviving runs stamped `6261ca17…` | 34 | 34 (confirmed via exact-string match against the full recorded value, `6261ca1791b59771f3b6b6829142e2cf7c0f33d0fa4ea00a2f1e2c8d1d6b3a6e`) |
| NULL-stamped pre-stamping-era runs | (not stated) | 3,083 |

**Manifest full-row sha256 — a method mismatch, NOT a data discrepancy (corrected in the fix pass).**
My first pass reported this baseline as "could not reproduce." That framing was wrong, and it is corrected
here: `bb954b60…a2a2e6` is a **Python-specific fingerprint**, not a portable checksum, and it reproduces
**exactly** under the method that defines it —

```
sqlite3.connect("file:apps/backend/data/trendora.db?mode=ro", uri=True)   # read-only handle
PRAGMA query_only=ON
h = sha256(); for row in "SELECT * FROM next_session_manifests ORDER BY id": h.update(repr(row).encode())
```

which yields `bb954b60187e39a1aa8f59b1bf736be9808e25760d2a0494f176116416d2a2e6` over 24 rows × 28 columns
— head and tail both matching the cited value. Re-derived live in the fix pass; the db file's size and
mtime and the `-wal` size were captured before and after that read and are **identical** (8,365,871,104
bytes / mtime `2026-08-24 18:13:42.427743230`; WAL 0 bytes), so the re-derivation itself wrote nothing.

The reason my earlier serializations disagreed is simply that they were different methods, not different
data: the digest is taken over CPython's `repr()` of a `sqlite3` row tuple, so it encodes Python literal
formatting (quoting, `datetime` repr, float repr) and cannot be reproduced by `sqlite3` CLI `.dump`,
`SELECT * | sha256sum`, or any JSON serialization. Near-neighbour variants over the very same rows land
on completely different digests (newline-joined `repr` → `3565d624…`, `repr(list_of_rows)` → `194bd600…`,
per-row-hash concatenation → `659cff46…`), which is exactly what a method-sensitive fingerprint should do
and is *not* evidence of drift.

Independently of that fingerprint, the load-bearing proof for "manifests unchanged" remains the stronger
instrument and its result stands: `compare_stage_d_preflight_to_certified`'s `manifest_values_unchanged`
is a full 28-column **per-row diff** (`migration.diff_dumps`) against iteration 13's certified dump, and
it found **zero mismatches**.

## CRITICAL — iteration-13 evidence corruption: caused by THIS iteration's own test (corrected)

Three of **iteration 13's committed Stage C evidence files** were truncated in the working tree while
this iteration ran:

- `runs/goal-market-compass-iter-13/j11-stage-c-preflight.json` (6,219,233 bytes → 130)
- `runs/goal-market-compass-iter-13/j11-stage-c-preflight-comparison-gate.json` (833 → 155)
- `runs/goal-market-compass-iter-13/j11-stage-c-db-file-true-start.json` (242 → 2, i.e. `{}`)

**My first pass attributed this to "some OTHER process … not this agent's work." That attribution was
wrong, and I retract it.** The cause was a test I wrote this iteration:
`apps/backend/tests/test_j11_stage_c_cli_script.py::test_comparison_gate_failure_never_calls_clear_snapshot_dates`
called `run_j11_stage_c_bounded_clear.main()` with `--confirm` but **without `--evidence-dir`**, so the
script fell back to its argparse default — `runs/goal-market-compass-iter-13`, the real committed
evidence directory — and wrote its mocked payloads over those three files before reaching the
gate-failure return path. The evidence for the attribution is in the corrupted content I documented
myself: `captured_at: "2026-01-01T00:00:00+00:00"`, `generated_at: "x"`, `material_mismatch: true` are
*that test's own mock return values*, and the `{}` stub is its mocked `db_file_fingerprint`. The
`2026-08-24T22:05:25Z` mtime is the targeted pytest run cited in "Tests Run", not an external process.
My earlier reasoning ("my script read the full 6.2 MB successfully, so nothing corrupted it") was a
sequencing error: the Stage D preflight ran at ~21:54Z, ten minutes *before* the pytest run that did the
damage. The reviewer independently reproduced the corruption by re-running the cited pytest command and
flagged the misattribution; both are fixed in this pass.

**Resolution (all three verified):**

1. The files were restored from git (`git checkout HEAD -- …`); all three are byte-identical to HEAD and
   `git status --porcelain runs/goal-market-compass-iter-13/` is empty.
2. The test now passes `--evidence-dir` pointing at pytest's `tmp_path`, matching the pattern its two
   sibling tests already used, and asserts the pre-gate evidence landed there.
3. The CLI itself is hardened so a forgotten flag can never do this again (below). Re-running the full
   targeted suite after the fix leaves all three files' sha256 unchanged — verified before and after.

**No live-database exposure at any point.** The corruption was confined to committed JSON evidence files
under `runs/`; every DB-touching name in that test is a `unittest.mock` object, so no engine, session, or
`clear_snapshot_dates` call ever reached `apps/backend/data/trendora.db`. Its size and mtime are still
those of iteration 13's Stage C run (8,365,871,104 bytes, `2026-08-24 18:13:42.427743230`) with a 0-byte
WAL, unchanged across every command in this fix pass.

**Hardening — `--evidence-dir` is now required, with no implicit default.** The root cause was not just
one missing flag; it was that omitting it *silently succeeded* against a real evidence path.
`run_j11_stage_c_bounded_clear.py`'s `--evidence-dir` now defaults to `None`, and `main()` exits `2` with
an explanatory message before touching the database or writing anything when it is absent. The committed
directory is still a perfectly legal target — it just has to be named on the command line. Covered by a
new test (`test_confirm_without_explicit_evidence_dir_refuses_before_writing_anything`) that patches
`_write_json`, `get_engine`, `Session`, `db_file_fingerprint` and `clear_snapshot_dates` and asserts none
of them is called. Note that the script's real Stage C run is already complete and is not re-run, so this
changes no executed behavior — only the failure mode of a future invocation.

## Files Changed

- `apps/backend/app/engine/j11_stage_d.py` — new module (Goals 1, 2, 3a, 5).
- `apps/backend/app/engine/j11_avb_diagnostic.py` — new module (Goal 4).
- `apps/backend/scripts/run_j11_avb_bridge_diagnostic.py` — new read-only CLI script (Goal 4), executed
  live twice (second run after the bug fix above).
- `apps/backend/scripts/run_j11_stage_d_preflight.py` — new read-only CLI script (Goals 1 + 3a), executed
  live once. Not explicitly named in the plan's file list; added because Goal 3a's spec explicitly
  requires live execution and every other live capture in this codebase is a dedicated script — flagging
  the addition rather than silently improvising an ad hoc one-off.
- `apps/backend/tests/test_j11_stage_d.py` — new, 25 tests (TC-1, TC-ID-1..6, TC-8..13, TC-19 Stage-D
  half, TC-25, plus the comparison-gate pass/fail pair).
- `apps/backend/tests/test_j11_stage_c_preflight.py` — extended with 7 new tests (TC-14..18).
- `apps/backend/tests/test_j11_stage_c_cli_script.py` — new, 4 tests (TC-19 CLI half + the fix pass's
  `--evidence-dir` guard test). The gate-failure test now passes `--evidence-dir` (fix pass).
- `apps/backend/scripts/run_j11_stage_c_bounded_clear.py` — **modified in the fix pass only**:
  `--evidence-dir` no longer has a filesystem default (`default=None`), and `main()` refuses with exit 2
  before any DB interaction or write when it is absent. Docstring/usage updated to match. No change to
  the destructive sequence itself, the gate ordering, or any DB statement.
- `apps/backend/tests/test_j11_avb_diagnostic.py` — new, 16 tests (TC-20..24 plus supporting coverage).
- `runs/goal-market-compass-iter-14/j11-stage-d-attempt-identity.json` — Goal 1 evidence.
- `runs/goal-market-compass-iter-14/j11-stage-d-preflight.json`,
  `j11-stage-d-preflight-gate.json` — Goal 3a evidence (live, read-only).
- `runs/goal-market-compass-iter-14/j11-avb-bridge-diagnostic.json` — Goal 4 evidence (live, read-only;
  regenerated once after the bug fix).
- `runs/goal-market-compass-iter-14/j11-stage-d-readiness.json` — Goal 5 verdict.
- `runs/goal-market-compass-iter-14/j11-stage-d-db-file-true-start.json` /
  `j11-stage-d-db-file-true-end.json` — whole-iteration zero-write proof.
- `runs/goal-market-compass-iter-14/status.json` — `current_step: dev_complete`.

No file under `apps/frontend/` touched. No destructive-path *logic* modified: `data_manager.py` and
`scanner.py` are untouched, and the only edit to `run_j11_stage_c_bounded_clear.py` is the argument guard
described above (it adds a refusal, removes no check, and cannot make a write happen that previously
did not).

## Tests Run

Command (targeted files only, ONE pytest process, never the full suite, never `loaded_engine`):
```
cd apps/backend && .venv/bin/python -m pytest \
  tests/test_j11_maintenance.py tests/test_j11_stage_b1_migration.py \
  tests/test_j11_stage_c_bounded_clear.py tests/test_j11_stage_c_preflight.py \
  tests/test_j11_stage_c_cli_script.py tests/test_j11_stage_d.py tests/test_j11_avb_diagnostic.py -q
```
Result after the fix pass: **92 passed, 0 failed** in 4.57s (was 91 before; +1 for the new
`--evidence-dir` guard test). Breakdown: 14 pre-existing `test_j11_maintenance.py`, ~10
`test_j11_stage_b1_migration.py`, ~a handful `test_j11_stage_c_bounded_clear.py`, 21
`test_j11_stage_c_preflight.py` [14 pre-existing + 7 new], **4** `test_j11_stage_c_cli_script.py`, 25
`test_j11_stage_d.py`, 16 `test_j11_avb_diagnostic.py`. Zero regression on the three "do-not-redo"
regression files (`test_j11_maintenance.py`, `test_j11_stage_b1_migration.py`,
`test_j11_stage_c_bounded_clear.py`).

**Evidence-safety check around the test run (fix pass).** sha256 of all three previously-corrupted
iteration-13 files captured immediately before the run and re-checked immediately after: all three `OK`
(unchanged), and `git status --porcelain runs/goal-market-compass-iter-13/ runs/goal-market-compass-iter-12/
runs/goal-market-compass-iter-9/` is empty. The suite no longer writes outside `tmp_path`.

Live (read-only, against `apps/backend/data/trendora.db`): `run_j11_stage_d_preflight.py` (once),
`run_j11_avb_bridge_diagnostic.py` (twice — the second run after the bug fix above). Neither script
requires `--confirm`; neither performed any write (proven by the true-start/true-end db-file
mtime/size/WAL-size comparison — identical at both ends).

## Known Issues

- ~~The manifest full-row sha256 mismatch against the coordinator's cited baseline value.~~ **Closed in
  the fix pass** — it was a method mismatch, not a discrepancy; the value reproduces exactly under the
  `repr(row)`-over-`sqlite3`-rows method that defines it (see the corrected section above).
- The pool-wide liquidity-percentile-shift trace (Goal 4) checks whether OTHER tickers' percentile VALUES
  moved, but does not re-run `score_stocks` for each affected ticker to confirm none crossed a Risk-bucket
  or eligibility edge as a second-order effect — scoped out as "narrowly as practical" per the spec; the
  magnitude of the shifts (thousandths of a percentile point) makes this unlikely to matter, but it is not
  independently proven.
- `evaluate_selection`'s full population-wide "selection disposition"/candidate ranking could not be
  replayed for 2026-08-11/12 because no `ScannerRun` exists for those dates (Stage C cleared it) and
  creating one is forbidden this iteration — the individual `_qualifier_checks` pass/fail is used as the
  direct, checkable proxy for candidate eligibility instead (documented inline in the diagnostic's own
  `relative_ranking_note` field).
- ~~The unrelated iteration-13 evidence-file truncation.~~ **Not unrelated, and now resolved** — it was
  this iteration's own CLI test; files restored, test fixed, CLI hardened (see the corrected CRITICAL
  section above).
- **New, NOT fixed in this pass (flagged for triage, per fix-mode scope).**
  `apps/backend/scripts/run_j11_stage_d_preflight.py` still carries the same footgun the Stage C script
  just had: `DEFAULT_EVIDENCE_DIR = runs/goal-market-compass-iter-14` as a live argparse default. No test
  calls that script's `main()` today, so nothing is corrupting anything now, but the moment one does
  without `--evidence-dir` it will overwrite this iteration's own evidence the same way. The same
  three-line guard should be applied to it (and to any future evidence-writing CLI) when Stage D work is
  authorized; I did not change it in this pass because it is outside the review's findings and the
  reviewer already passed that file.

## Two logged interpretive calls (independently re-derived, per the standing instruction)

1. "The identity-comparison blind spot is closed by building the new Stage D compare call-sites, not by
   patching `j11_stage_c.py`'s already-executed capture" — confirmed correct: `j11_stage_d.py` never
   modifies `j11_stage_c.py`; it composes three new call sites around the existing pure
   `check_attempt_identity_consistency` primitive.
2. "AVB counterfactual representation B's raw provider close is `stored_close / bridge_factor` (arithmetic
   only, never a new fetch)" — confirmed correct and implemented exactly as stated in
   `compute_counterfactual_representations`.

## Fix Notes (fix pass after review FAIL — `reports/reviews/goal-market-compass-iter-14-review.md`)

Scope: the two review findings plus the one hardening the coordinator authorized. Nothing else touched;
no module the reviewer passed was rebuilt, and Stage D was neither authorized nor executed.

1. **CRITICAL (`test_j11_stage_c_cli_script.py:113`) — fixed.**
   `test_comparison_gate_failure_never_calls_clear_snapshot_dates` now passes
   `--evidence-dir str(tmp_path / "evidence")` and asserts the pre-gate evidence files land *there*, so
   the script's write target can never be a real evidence path. It still exercises the genuine
   gate-failure path (the guard in item 3 is satisfied by the explicit flag, so the test is not passing
   vacuously): `clear_snapshot_dates` is asserted un-called with the gate returning
   `all_invariants_hold: False`.
2. **MINOR (handoff root-cause attribution) — corrected.** The "CRITICAL — unrelated repo anomaly"
   section has been rewritten and its attribution retracted; see that section. I also corrected the
   manifest-fingerprint claim *in my own favour*: it was a method mismatch, not an unresolved
   discrepancy, and the value reproduces exactly (re-derived live, read-only, in this pass).
3. **Hardening (authorized by the coordinator, kept minimal) — done.**
   `run_j11_stage_c_bounded_clear.py`'s `--evidence-dir` has no filesystem default any more; `main()`
   returns `2` with an explanatory message before any DB interaction or write when it is missing. One new
   test covers it. The one same-class defect I found but did **not** fix (the sibling Stage D preflight
   script's default) is recorded under Known Issues for triage rather than silently patched.

**Verification of the fix (all re-run in this pass):**

- Targeted suite: `92 passed, 0 failed` (7 j11 files, one pytest process, never the full suite).
- The three previously-corrupted iteration-13 files: sha256 identical before and after the run; `git
  status --porcelain runs/goal-market-compass-iter-13/` empty.
- `apps/backend/data/trendora.db`: size 8,365,871,104 and mtime `2026-08-24 18:13:42.427743230` — still
  iteration 13's Stage C values, unchanged by every command in this pass; `-wal` 0 bytes. **Live DB
  writes this pass: ZERO.** The only live-DB access was one read-only `mode=ro` + `PRAGMA query_only=ON`
  handle reading 24 manifest rows for the fingerprint re-derivation, with the file's stat captured either
  side of it.
- No backend/frontend boot, no browser, no replay, no demo, no network call, no Stage C re-run, no
  Stage D execution, no J-10 reopening, no framework file touched.

**Readiness re-derived (not inherited).** `J-11 STAGE D READY` rests on two artifacts, both re-read in
this pass: `j11-stage-d-preflight-gate.json` — all 11 checks `true`, `verdict.passed: true`,
`reason: "all_checks_passed"` — and `j11-stage-d-readiness.json` — `ready: true`, `blocking_reasons: []`,
`avb_classification: "AVB-B"` (AVB-C/D would force `NO`; AVB-B does not). Both captures ran at ~21:54Z and
22:05:04Z, *before* the 22:05:25Z pytest run that corrupted the iteration-13 files, so the certified
baseline they consumed was the intact committed content — and that content is byte-identical to what is
in the working tree now (restored from HEAD, `git status` clean), so re-deriving from today's tree would
read exactly the same bytes. The defect was confined to test code writing JSON under `runs/`; it never
opened the database. The readiness artifacts were therefore not regenerated — none of their inputs
changed — and the verdict below is unchanged and stands on its own re-checked evidence.

---

**J-11 STAGE D READY: YES**

**J-11 STAGE D AUTHORIZED: NO** — this verdict does not authorize Stage D. Per the established C10/A12
pattern, a separate, explicit owner instruction is required before Stage D's own execution (canonical
regeneration of the 11 incident dates) may begin.
