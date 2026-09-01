# goal-market-compass-iter-37 Execution Plan

## Context check against docs/goal.md
All thirteen Must-have journeys (J-01..J-13) are functionally built and previously verified
correct (iter-36's own re-derivation: 9/9 rotation rows, 31/31 sector + 11/11 theme accounting
closed exactly). The prior verdict was ESCALATE for two reasons that are **process integrity**,
not correctness: (1) `Depth: full` was silently dispatched as `lean` — the fourth recurrence this
session — so none of `docs/handoffs/goal-market-compass-iter-36-audit.md`,
`reports/qa/goal-market-compass-iter-36-qa.md`,
`reports/phase-goal-market-compass-iter-36-ux-regression.md`, or
`reports/phase-goal-market-compass-iter-36-closure-verdict.md` exist; (2) J-13's acceptance
screenshot `reports/qa/goal-market-compass-iter-36-evidence/UT-J-13-rotation-both-directions.png`
is confirmed present but was measured single-colour (a failed capture — 1683×1260, one colour
across 2.12M pixels), and `journey-scripts/J-13.json` (mtime **Sep 1 13:35**, confirmed on disk)
was written five minutes after the 13:30 replay it was meant to cover, so it has never actually
executed. This iteration is explicitly a **closing round, zero new feature work**: genuinely run
the full checking team, retake the J-13 screenshot as a passenger, replay the golden for the
first time, and land two already-scoped backend robustness repairs the evaluator carried forward.
`Frontend Present: no` matches the spec's Goal Mode Metadata block verbatim — no `.tsx` file
changes this iteration; J-13's product UI is binding "Do not redo."

## What to Build

### A. Backend repair 1 — TC-24 fixture confound (`test_manifest_invariants.py`)
- `test_tc24_leadership_min_score_is_the_only_gate_regardless_of_qualifiers`
  (~line 933, `_mk_result(session, run.id, "HPE", 92.7, "A", 21.5, "E", 58.9, "C")`): the HPE row's
  risk score `58.9` is BELOW `compass.selection.risk_max_score` (`60.0`), so the risk qualifier
  actually clears today even though the test's own comment claims HPE "fails BOTH qualifiers."
  Raise the risk score above the ceiling (e.g. `65.0`) so entry (`21.5` < `70.0`) AND risk
  (`>60.0`) genuinely both fail, while leadership (`92.7`) still clears the `80.0` floor
  unchanged. No other fixture row (`LOW`) or assertion changes — this is a single numeric literal
  fix confirmed by reading the live fixture and `compass.py`'s `SelectionRule` defaults
  (`leadership_min_score=80.0, entry_min_score=70.0, risk_max_score=60.0`).
- Confirm post-fix the existing assertions still hold: HPE is a candidate or `excluded_by_cap`
  (never `below_selection_floor`, since leadership clears); LOW stays `below_selection_floor`.

### B. Backend repair 2 — `-O`-strippable guard (`compass.py`)
- `_assert_disposition_predicate` (line ~586) has two bare `assert cond, msg` statements guarding
  that `below_selection_floor` / `excluded_by_cap` labels are truthful by construction. Convert
  each to `if not cond: raise AssertionError(msg)` — same exception type (so any existing
  `pytest.raises(AssertionError)` usage is unaffected), same message, same condition, but no
  longer eligible for `-O`/`-OO` stripping. Zero change to predicate logic, inputs, or any
  computed/served value; compass.py already defines custom exceptions elsewhere
  (`ManifestNotFoundError`, `ManifestNotYetFrozen`) but `AssertionError` is the right minimal-diff
  choice here since the spec calls this an "explicit raise" conversion, not a new taxonomy.
  No new numeric/string literal is introduced — `test_no_magic_numbers.py`'s `compass.py` scan
  stays green.
- New unit test (new or existing disposition test file) proving the converted guard still raises
  under `python -O` (assertions stripped) when invoked directly against a deliberately-constructed
  comparison-cohort row that violates the predicate (e.g. a row labeled `below_selection_floor`
  with `leadership_score` above `leadership_min_score`). Realistic pattern: spawn a subprocess
  `python -O -c "..."` that imports `_assert_disposition_predicate` and the bad row, and asserts
  the subprocess exits non-zero with `AssertionError` in stderr — this is the only way to prove
  `-O` behavior from inside a pytest process (pytest itself doesn't run under `-O`).
- Byte-identity check (AG-12, TC-7): before/after md5 checksums of every existing
  `next_session_manifests` row's `payload_json` and every exported JSON file under
  `runs/goal-session-market-compass/exports/` (or wherever manifests are exported) must be
  identical — this touch is guard-only and must never mutate a frozen row.

### C. Genuine full-depth pipeline execution (process, not code)
- Confirm `runs/goal-market-compass-iter-37/depth-dispatched` reads `full` before any downstream
  agent claims completion (TC-5).
- Ensure all four full-only artifacts are actually produced with non-trivial content (not empty
  stubs): `docs/handoffs/goal-market-compass-iter-37-audit.md`,
  `reports/qa/goal-market-compass-iter-37-qa.md`,
  `reports/phase-goal-market-compass-iter-37-ux-regression.md`,
  `reports/phase-goal-market-compass-iter-37-closure-verdict.md`. These are downstream-agent
  responsibilities (auditor, qa, ux-regression-reviewer, closure step), not the developer's — the
  developer's job is only to not silently skip anything and to disclose depth status honestly in
  the dev handoff.

### D. J-13 re-verification — real screenshot + first golden replay (browser-qa / replay lane)
- Browser-qa-agent re-captures the Leadership rotation panel at the frontier as-of (`2026-08-12`
  per the phase spec's TC-3, or whatever the current frontier as-of resolves to) as a genuine
  passenger through the full pipeline — not a standalone script. Save as
  `reports/qa/goal-market-compass-iter-37-evidence/UT-J-13-rotation-both-directions.png` (or
  iter-37-suffixed equivalent) and **measure it** before citing it: `PIL.Image.getcolors()` must
  report more than one distinct colour, and file size should be comparable to sibling captures in
  the same evidence directory (iter-36's blank capture and any healthy sibling screenshot are
  useful size references). The image must visibly show both a labelled "gaining" side and a
  labelled "losing" side with at least one row each — matching `journey-scripts/J-13.json` steps
  2-4 (`Regional Banks (SPDR)`, `13 → 10 (-3) · improving`, `21 → 25 (+4) · deteriorating`).
- Replay lane executes `journey-scripts/J-13.json` (mtime confirmed **Sep 1 13:35**, already
  strictly earlier than this iteration's replay-run start) for the first time it will have
  actually run; record J-13 as `PASS` (not merely present) in the merged results file.
- Regression smoke across all twelve Required-still-passing journeys (J-01..J-12) via
  deterministic replay + LLM fallback, 0 FAIL, 0 skipped — this also refreshes every golden
  script per the spec's own rationale (widening after an ESCALATE catches selector drift).

## Out of scope (do NOT build)
- Any change to `compass.selection.*` threshold VALUES, `evaluate_selection`'s membership/ordering
  logic, or J-12's disposition vocabulary — J-12 is CLOSED (binding "Do not redo").
- Any change to `session_delta.rotation`, `_rotation_kind`, `_attach_rank_direction_words`, or any
  other J-13 product logic, or any `.tsx` file — J-13's product work is DONE (binding "Do not
  redo"); this round is evidence-only for J-13.
- Any touch to `warmup.py` / `prices.py` — J-09 stays closed (binding "Do not redo").
- Any mutation, relabeling, re-hashing, or deletion of a stored `next_session_manifests` row or
  export file (AG-12/AG-17) — every prior version (v1..v9+) keeps its bytes exactly; confirm via
  md5 before/after.
- The third pre-existing `assert` in `compass.py` ("expected exactly one gating qualifier
  check…") — confirmed by the spec via `git blame` to be a different, unflagged check. Leave
  untouched.
- J-04's screenshot crop fix, the eight journeys' owed `[NEW]`-flagged walkthrough recordings, the
  five older non-blocking owner questions, pre-existing red `test_no_magic_numbers.py` failures on
  3 untouched files, the iteration-23 throwaway clone, `apps/frontend/.next-verify/` tracked in
  git, and the rotation-panel-vs-what-changed row-count owner question — all binding "Do not redo"
  / carried, non-blocking.

## Agents Required
- backend-data: yes — TC-24 fixture fix, `_assert_disposition_predicate` guard conversion, new
  `-O` subprocess unit test, targeted pytest for `test_manifest_invariants.py` and any new
  disposition-guard test file, `test_no_magic_numbers.py` targeted re-check for `compass.py`,
  AG-12 byte-identity check, dev handoff.
- frontend-ux: no — zero UI surface, zero `.tsx` change; J-13's rotation panel is already shipped
  and is binding "Do not redo." Frontend involvement this iteration is limited to the QA/replay
  lanes re-viewing the already-built page, not implementation.

Frontend Present: no

## Files to Create/Modify
- `apps/backend/tests/test_manifest_invariants.py` -- TC-24 HPE fixture: raise risk score above
  `60.0` (currently `58.9`) so entry AND risk both genuinely fail.
- `apps/backend/app/engine/compass.py` -- `_assert_disposition_predicate`: convert both bare
  `assert` statements to explicit `if not cond: raise AssertionError(msg)`. No other line in this
  file changes.
- `apps/backend/tests/test_manifest_invariants.py` (or a new focused test file, developer's call)
  -- new `-O`-subprocess unit test proving the converted guard still raises with assertions
  stripped, against a deliberately-invalid comparison-cohort row.
- `docs/handoffs/goal-market-compass-iter-37-dev.md` -- new dev handoff, including the actual
  dispatched-depth disclosure and the AG-12 before/after md5 confirmation.
- (Downstream, non-developer artifacts expected on disk by end of iteration, not created by the
  developer agent): `docs/handoffs/goal-market-compass-iter-37-audit.md`,
  `reports/qa/goal-market-compass-iter-37-qa.md`,
  `reports/phase-goal-market-compass-iter-37-ux-regression.md`,
  `reports/phase-goal-market-compass-iter-37-closure-verdict.md`,
  `reports/qa/goal-market-compass-iter-37-evidence/UT-J-13-rotation-both-directions.png` (measured
  non-blank), merged regression-replay results file covering J-01..J-13.
- No files under `apps/frontend/`, `apps/backend/app/engine/warmup.py`,
  `apps/backend/app/engine/prices.py`, `apps/backend/app/engine/session_delta.py`, or any
  `compass.selection.*` config value should change this iteration.

## Key Test Scenarios
- TC-1: corrected TC-24 fixture (HPE risk score `>60.0`, entry unchanged `21.5`) — HPE's
  `entry_min_score.met == False` AND `risk_max_score.met == False`, while HPE's
  `selection_disposition` is never `below_selection_floor` (leadership `92.7` clears `80.0`).
- TC-2: a comparison-cohort row deliberately violating `_assert_disposition_predicate`'s invariant
  (e.g. `below_selection_floor` label with `leadership_score` above the floor) raises a real
  exception under `python -O` (assertions stripped), proven by a subprocess-based test.
- TC-3: J-13's Leadership rotation section at the frontier as-of, captured fresh by
  browser-qa-agent, is measured non-single-colour (`PIL.Image.getcolors()`), comparable file size
  to healthy siblings, and visibly shows both a "gaining" and a "losing" side with ≥1 row each.
- TC-4: `journey-scripts/J-13.json` mtime (Sep 1 13:35, confirmed) is strictly earlier than this
  iteration's replay-run start; merged results file records J-13 as `PASS`.
- TC-5: `runs/goal-market-compass-iter-37/depth-dispatched` reads `full`; all four full-only
  artifacts exist on disk with non-trivial content.
- TC-6: all twelve Required-still-passing journeys (J-01..J-12) report `PASS` with 0 FAIL, 0
  skipped in the merged regression results.
- TC-7: every pre-existing `next_session_manifests` row and export file's md5 is byte-identical
  before vs. after this iteration's two backend changes (AG-12).
- TC-8: targeted `pytest tests/test_manifest_invariants.py -v` and the new guard test pass; a
  targeted `test_no_magic_numbers.py` check confirms no new literal was introduced in
  `compass.py`.
