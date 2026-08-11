# Iteration State — ops-hardening

**After iteration:** 59 · **Date:** 2026-08-11 · **Verdict:** CONTINUE

## Journeys

6 passing (J-01 J-03 J-04 J-06 J-08 J-09) · 2 partial (J-05 J-07) · 0 failing — 8 total

## Active blockers

- **LANE COVERAGE (dev/framework, TOP PRIORITY).** Target journeys get NO lane row: `replay-lane.sh` replays
  `REQUIRED_JOURNEYS` only, the LLM plan had no J-05/J-07 case. Both goldens PASSED when run by hand. Result:
  `phase-goal-ops-hardening-iter-59-ui-test-results.md` = BLOCKED, 2 target-missing → CLOSURE-FAIL.
- **WALKTHROUGH (dev).** `demo-results.md` = NOT_YET, zero steps. J-05 and J-07 each carry a `[NEW]`
  walkthrough acceptance clause — neither closes without it. Full depth only; rides along, never the goal.
- **J-07 step 2 latency (OWNER decision).** 12 of 1,520 health polls > the relaxed 2 s ceiling (worst
  4.068 s); zero non-answers, zero non-200. That 2 s promise was written for a ~30 s window; this was 23 min.
- **Degrade rendering + prologue (dev).** `_labs.tsx:3843/3849` shows `n=0` for 17,440-record cohorts, only a
  tooltip differs (iter-59/a); `research.py:4438-4441` prologue is outside the per-horizon `try` (iter-59/b).
- **J-01 golden (dev).** `journey-scripts/J-01.json` claimed rewritten; git says untouched since iter-47
  (db742cdc). Step 09 will fail replay again (iter-59/e).

## Last 2 verdicts

- iter 59: CONTINUE — full depth, all lanes ran; J-05 step 3 and J-07 steps 3/4 executed live and PASSED for
  the first time (boot 1.712 s; VmPeak 71.26% of cap; zero 500s) — no lane row + no walkthrough keeps both.
- iter 58: ESCALATE — lean round against a full spec; lane write-ups contradicted their own raw logs.

## Do not redo

- **J-05 steps 1-4 all EXECUTED and PASS** (run id=390, 2010-11-15, seed; `phase2-restart.json`: kill -9,
  boot 1.712 s, cold `/api/data` 0.243 s, watermarks identical, zero prefill). Only lane row + walkthrough
  owed — do not re-run the restart drill as a goal.
- **J-07 steps 1, 3, 4 PASS** (`tc4-vmpeak.csv` 5837.46 MB = 71.26% of 8192; `fault-drill.json` same pid,
  byte-identical reads; 472/472 concurrent 200s). Only step 2's latency half is open.
- **`compute_regime_lab`'s per-horizon bound is DONE, byte-identity PROVEN** vs an independent pinned oracle
  (36/36 re-run by reviewer AND auditor). Do not re-open it.
- **Drill reporting is MECHANISED** (`evidence-drill/reconcile_drill.py`); figures survived my own recount
  exactly — reuse it. **TC-12 golden rotated + live-verified** (`J-05.json` → 2010-11-16, 0 `scanner_runs`).
  **AG-9/AG-10 re-verified** (runs 383-390 all `provider='seed'`; frozen-path git checks empty; 8192 / 2).
