# Iteration State — market-compass

**After iteration:** 36 · **Date:** 2026-09-01 · **Verdict:** ESCALATE

## Journeys

13 passing (J-01..J-13) · 0 failing · 0 unknown — 13 total. All gates green: `journeys` exit 0
`{"total":13,"passing":13,"blocking":[]}`, `results` 0, `regressions` 0, `coherence` 0, drift `changed: []`.

## Active blockers

- **Verification deficit, NOT a journey deficit (owner: engine/dev).** Spec
  `docs/phases/goal-market-compass-iter-36.md` reads `Depth: full`; `iter-36/depth-dispatched` reads
  `lean`; trace steps 370-375 launched every agent as "goal-mode **lean** iteration". Missing on disk:
  audit handoff, QA report, ux-regression, closure verdict — the lanes the Full trigger named.
- **J-13's acceptance screenshot is blank** (`UT-J-13-rotation-both-directions.png`, 1683×1260, ONE
  distinct colour): scored `passing` from re-derived data evidence + `evidence_makeup`, but no visual
  record of the new panel exists. **Its golden never ran** (`J-13.json` mtime 13:35; replay ran 13:30).
- Non-blocking: `test_manifest_invariants.py:933` risk fixture `58.9` vs a 60.0 ceiling; bare `assert`
  guards at `compass.py:462`/`:689`; `test_no_magic_numbers.py` red on 3 untouched files.

## Last 2 verdicts

- iter 36: ESCALATE — J-13 built and verified by me (9/9 rotation rows match stored ranks; accounting
  closes 31/31 and 11/11), nothing regressed, but the round ran lean where its spec said full and the
  new screen's only picture is blank. GOAL_ACHIEVED was available and declined; see `assumptions.md`.
- iter 35: CONTINUE — J-12 built (37→0 mislabeled rows); the goal GREW when J-13 landed unbuilt.

## Do not redo

- **J-13's PRODUCT WORK IS DONE — do not rebuild it.** Iteration 37 is a CLOSING round, no new feature
  work: (1) genuinely full depth, proven by the four missing report FILES and never by a marker;
  (2) replay the J-13 golden; (3) re-take the blank screenshot as a passenger.
- **J-12 is CLOSED** (do not re-open `evaluate_selection`; `selection.rule_version` `"v2"`); **J-09 stays
  closed** (do not touch `warmup.py`/`prices.py`; host-guard caps unmoved, AG-10).
- **Never mutate, relabel, re-hash or delete a stored manifest row or export file** (AG-12/AG-17); v1..v8
  keep their bytes and the rotation block lives ONLY in v9. **No threshold VALUE may change** (80.0 /
  70.0 / 60.0 / `rank_move_min` / `top_k`) — AG-15; only `compass.delta.rotation_top_k: 5` was added.
- **Evidence capture is never an iteration goal** — J-04's crop (18 rounds owed) and the 8 journeys owing
  a `[NEW]` walkthrough ride as passengers, never as the round's purpose.
