# goal-market-compass-iter-37 Dev Handoff

**Phase:** goal-market-compass-iter-37
**Date:** 2026-09-01
**Agent:** developer
**Status:** complete

## What Was Built

This is a closing round per the spec ("zero new feature work") — two small, already-scoped
backend robustness repairs, plus test coverage proving each. No product-facing capability,
UI, endpoint, config value, or served field changed.

- **Repair 1 — TC-24 fixture confound fixed** (`test_manifest_invariants.py`,
  `test_tc24_leadership_min_score_is_the_only_gate_regardless_of_qualifiers`): the HPE row's
  risk score was `58.9` — below `compass.selection.risk_max_score` (`60.0`) — so the row
  actually *cleared* the risk qualifier while the test's own comment and docstring claimed it
  "fails BOTH qualifiers." Raised the risk score to `65.0` (entry score `21.5` unchanged, well
  below the `70.0` entry floor; leadership `92.7` unchanged, still clears the `80.0` floor).
  Strengthened the test with two new assertions that directly check the served
  `what_would_change` checklist on the resulting HPE candidate: `entry_min_score.met is False`
  and `risk_max_score.met is False` — the fixture's claim is now actually verified, not just
  implied by fixture literals.
- **Repair 2 — `_assert_disposition_predicate` guard is no longer `-O`-strippable**
  (`apps/backend/app/engine/compass.py`): converted both bare `assert cond, msg` statements
  guarding that `below_selection_floor` / `excluded_by_cap` labels are truthful by
  construction to `if not cond: raise AssertionError(msg)`. Same exception type, same
  message, same condition — pure control-flow rewrite; nothing computed, compared, or served
  differs. Python's `-O`/`-OO` flags strip bare `assert` statements entirely, which would have
  silently defeated this correctness guard; the explicit `raise` form cannot be stripped.
- **New unit test proving the guard survives `-O`**
  (`test_assert_disposition_predicate_raises_under_dash_o` in
  `test_manifest_invariants.py`): spawns a subprocess `python -O -c "..."` (pytest itself
  never runs under `-O`, so this is the only way to prove the behavior from inside a pytest
  process) that imports `_assert_disposition_predicate` directly and feeds it a deliberately
  invalid comparison-cohort row (`below_selection_floor` label on a row whose
  `leadership_score` is above `leadership_min_score`). Asserts the child process exits
  non-zero with `AssertionError` in stderr, and that it never reaches the post-call `print`.

## Files Changed

- `apps/backend/tests/test_manifest_invariants.py` — TC-24 HPE fixture risk score
  `58.9` → `65.0`; added two `what_would_change` assertions to the existing TC-24 qualifier
  test; added new imports (`subprocess`, `sys`); added
  `test_assert_disposition_predicate_raises_under_dash_o` (new TC-2 section, placed between
  the TC-24 tests and the TC-25 schema-conformance section).
- `apps/backend/app/engine/compass.py` — `_assert_disposition_predicate`: converted its two
  bare `assert` statements to explicit `if not cond: raise AssertionError(msg)`. No other line
  in this file changed. No new numeric/string literal introduced.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_manifest_invariants.py -v`
Result: 56 passed, 0 failed (all pre-existing TC-* tests still pass; the corrected TC-24 test
and the new `-O` subprocess test both pass).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_no_magic_numbers.py -v`
Result: 1 passed (`test_scanner_has_no_scoring_or_date_literals`), 1 failed
(`test_engine_calc_code_has_no_magic_numbers`) — the failure is on `indicators.py`,
`forward_testing.py`, and `research.py`, none of which this iteration touched. This is the
pre-existing, out-of-scope red state named verbatim in the phase spec's OUT-OF-SCOPE list
("pre-existing red `test_no_magic_numbers.py` failures on 3 untouched files") and the
execution plan's "Out of scope" section. `compass.py` (the file this iteration touched)
appears in zero offender lines — confirms the guard-statement conversion introduced no new
literal.

## Pre-handoff verification

- **Service startup**: started the backend via `bash scripts/start-backend.sh` (port 8255,
  this repo's deterministic offset). `GET /api/health` returned `200` with
  `preflight.verdict: "GO"` within 1 second (warm start, no ingest needed).
  `GET /api/compass?asof=2026-08-12` returned `200` with a full manifest document
  (`manifest_hash`, 10 candidates, `comparison_cohort`, `near_threshold_shadow` all present),
  exercising `_assert_disposition_predicate` end-to-end through the live server with no
  errors. Backend was stopped cleanly afterward (`pkill -f uvicorn`); confirmed no residual
  processes. Frontend was not started — `Frontend Present: no`, zero `.tsx` changes this
  iteration (per plan and spec, binding "Do not redo" on J-13's already-shipped UI).
- **AG-12 byte-identity (TC-7)**: read-only `sqlite3 -readonly` queries (never opened the
  7.8 GB DB for write, never copied it) against `next_session_manifests` — all 34 rows'
  `(id, as_of, version, content_hash, manifest_hash)` tuples, and md5 of all 9 files under
  `apps/backend/data/exports/next_session_manifests/` — were captured immediately after the
  code edits, again after running the full targeted test suite, and again after the live
  `GET /api/compass` server round-trip. All three snapshots are byte-identical (`diff`
  reported no differences each time). No backend/frontend process was running before this
  session started (confirmed via `ps aux`), and the only DB-touching operation this iteration
  performed anywhere was the read-only verification queries above — no finalize/ingest/
  regenerate path was invoked, so no manifest row or export file was created, mutated, or
  deleted.
- **No native dependency / external integration change**: this iteration adds no new
  dependency and makes no external network call.

## Depth / process disclosure (plan section C)

This developer agent's own scope was limited to the two backend repairs above; the four
full-depth-only artifacts (`docs/handoffs/goal-market-compass-iter-37-audit.md`,
`reports/qa/goal-market-compass-iter-37-qa.md`,
`reports/phase-goal-market-compass-iter-37-ux-regression.md`,
`reports/phase-goal-market-compass-iter-37-closure-verdict.md`) and the J-13 screenshot
re-capture / golden replay are downstream-agent responsibilities per the plan, not the
developer's. For the record at hand-off time: `runs/goal-market-compass-iter-37/`
contained only `goal-slice-exec.md`, `plan.md`, and `status.json` — no
`depth-dispatched` file existed yet when this developer agent began work. This is disclosed
here, not silently passed over, per the plan's instruction to "disclose depth status honestly
in the dev handoff." Whether `depth-dispatched` is written before or after developer dispatch
is an orchestration-script concern outside this agent's tools/scope; the downstream full-depth
agents (auditor, qa, ux-regression-reviewer, closure step) are the ones responsible for
confirming it reads `full` before claiming completion, per the plan.

## Known Issues

None discovered in the two files this iteration touched. Everything the plan named as
"out of scope" (compass.selection.* threshold values, evaluate_selection membership/ordering
logic, session_delta.rotation, warmup.py/prices.py, the third pre-existing `assert` in
compass.py at ~line 813, any `.tsx` file, J-04's screenshot crop fix, the owed `[NEW]`-flagged
walkthrough recordings, the five older non-blocking owner questions) was left untouched, as
directed. The pre-existing `test_no_magic_numbers.py` failures on `indicators.py`,
`forward_testing.py`, and `research.py` remain (carried, non-blocking, explicitly out of
scope for this iteration).
