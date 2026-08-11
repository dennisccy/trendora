# Iteration State — ops-hardening

**After iteration:** 60 · **Date:** 2026-08-11 · **Verdict:** ESCALATE

## Journeys

6 passing (J-01 J-03 J-04 J-06 J-08 J-09) · 2 partial (J-05 J-07) · 0 failing — 8 total

## Active blockers

- **J-05 stale served counts (dev, TOP).** `/data` showed 2953 snapshot dates / 2443 gaps at 07:47 while
  `coverage_snapshot` id=1 and sqlite both hold 2954 / 2442 — `data_manager.py:1057` `compute_coverage`.
- **Lane fix unproven (dev).** `replay-lane.sh`'s TARGET_JOURNEYS routing never ran — `goal-iter-lean.sh:45`
  sources it at executor start, pre-edit. Next run's log must list J-05/J-07 in the replay set.
- **Unseen UI (dev).** The new Regime-Lab "Unavailable" indicator (`components/sample-link.tsx:218-229`)
  has never been photographed; needs an armed-fault capture (dev arms, browser lane shoots).
- **J-07 owner decision, 11 rounds unanswered.** Does the relaxed ≤2 s `/api/health` ceiling apply to an
  18–23 minute job, or only the ~30 s window it was written for? `docs/goal.md`, 2026-07-31 amendment.
- **Measurement discipline (dev).** Addendum 27 gave a success count with no timings and no raw file;
  reuse iteration 59's `reconcile_drill.py` pattern.

## Last 2 verdicts

- iter 60: ESCALATE — lean run against a `Depth: full` spec surfaced three unreported defects (inert lane
  fix, unseen UI change, stale served counts); no journey moved.
- iter 59: CONTINUE — J-05/J-07 executed live and passed, but neither got a lane row; full depth worked.

## Do not redo

- **Regime-Lab prologue error handling is DONE** — `research.py:4455-4479` (closes iter-59/b).
- **Degraded-cell frontend fix is DONE in code** — `lib/regime-cell-status.ts`, `sample-link.tsx`,
  `_labs.tsx:3958`; only its photograph is owed (closes iter-59/a).
- **`journey-scripts/J-01.json` needs NO repair** — replayed PASS 4× by dev and again by the lane this
  round; leave byte-unchanged (closes iter-59/e).
- **J-05 steps 1/2/4 and J-07 steps 1/3 verified** — run 404 (2010-11-16, seed, ok, 18m20s, all 9
  aggregates), `scanner_runs.id=2954`, 932 health 200s / 0 5xx / 0 MemoryErrors in the process window.
- **J-05 step 3 and J-07 step 4 stand on iteration 59's live evidence** (Addenda 25/26) — boot, coverage,
  warm-seam and fault-hook code unchanged since; do not re-run to "refresh" them.
- **Do NOT plan a round whose only content is evidence capture** — the J-05/J-07 walkthrough and the
  "Unavailable" photograph ride along with real work at full depth.
