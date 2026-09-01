# Iteration State — market-compass

**After iteration:** 37 · **Date:** 2026-09-01 · **Verdict:** GOAL_ACHIEVED

## Journeys

13 passing (J-01..J-13) · 0 failing · 0 partial · 0 unknown — 13 total. All 13 re-verified THIS
iteration (12 by deterministic replay + fresh screenshot; J-09 by the evidence lane its own goal text
prescribes). 0 FAIL, 0 skipped, 0 DEFERRED-BUDGET. All gates exit 0; drift `changed: []`; ledger 0 unresolved.

## Active blockers

- none. The goal is reached; the loop should halt.
- Non-blocking evidence debt (never an iteration goal): 6 journeys owe a labelled walkthrough
  frame — J-02, J-03, J-05, J-06, J-07, J-12 (`evidence_makeup: true`). One `Depth: evidence`
  round captures all six, no code change.

## Last 2 verdicts

- iter 37: GOAL_ACHIEVED — full depth genuinely ran (`engine.log:7947-7951`); J-13's acceptance
  screenshot measured at 13,647 distinct colours and read by the evaluator; its golden executed and
  passed; both carried repairs landed and were re-derived under `python -O`.
- iter 36: ESCALATE — full depth silently became lean, and J-13's only screenshot was 100% blank.

## Do not redo

- **The goal is CLOSED at 13/13.** Do not manufacture new scope from the journey list; new work
  requires a `docs/goal.md` edit by the owner.
- **J-13 is DONE and verified visually** — `session_delta.rotation`, both labelled sides, signed
  deltas, direction words, 31/31 and 11/11 accounting. Evidence:
  `reports/qa/goal-market-compass-iter-37-evidence/UT-J-13-rotation-both-directions.png`.
- **Both iter-37 repairs are DONE**: `compass.py` `_assert_disposition_predicate` raises explicitly
  (both branches verified under `-O`); `test_manifest_invariants.py` TC-24 risk fixture is `65.0`.
- **J-04's and J-08's capture debt is PAID** — `reports/demo/goal-market-compass-iter-37/step-05.png`
  and `step-06.png` show their acceptance states; `evidence_makeup` cleared. Do not schedule a round
  for them.
- **Never schedule an iteration whose only content is evidence capture.** Remaining recordings ride
  as passenger tasks or one `Depth: evidence` round.
- **Golden mtime is NOT a "has it run" signal** — browser-QA re-writes unchanged goldens
  (`J-13.json`, 15:12:41, md5 identical to the HEAD blob). Compare md5 vs `git show HEAD:<path>`.
