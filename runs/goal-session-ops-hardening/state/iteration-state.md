# Iteration State — ops-hardening

**After iteration:** 61 · **Date:** 2026-08-11 · **Verdict:** CONTINUE

## Journeys

7 passing (J-01 J-03 J-04 J-05 J-06 J-08 J-09) · 1 partial (J-07) · 0 failing — 8 total

## Active blockers

- **J-07, owner-owned (12th round):** the ≤2 s `/api/health` ceiling was written for a background
  window "of order ~30 s"; our jobs run 16-23 min. This round: 1078/1078 answered HTTP 200,
  exactly 1 answer over 2 s (2.849 s). Keep it for long jobs → J-07 stays open; apply it to short
  jobs only → J-07 closes. Nothing further can be measured.
- **Test lane, owner-approval (one move):** target-journey goldens are never replayed on the FULL
  path — `scripts/automation/browser-qa-phase.sh:272` calls `replay_lane_partition_and_verify`
  before `:286` assigns `TARGET_JOURNEYS`. Live on the LEAN path (`goal-iter-lean.sh:204`). Has
  swallowed iter-60's and iter-61's own verification.
- **Reporting, dev:** 4th round running, a "no blockers / complete" headline over a BLOCKED artifact.

## Last 2 verdicts

- iter 61: CONTINUE — J-05 promoted to passing; the defect this round was built to fix never
  existed (UTC-vs-local clock error at iter-60); J-07 measured properly, one owner call left.
- iter 60: ESCALATE — ran lean against a full spec; a served-number defect (now withdrawn) and a
  lane fix that could not self-verify.

## Do not redo

- **`/data` coverage staleness is NOT a defect** — `iter-60/a` withdrawn: sqlite stores naive UTC,
  logs/mtimes are local BST (+1h). Rendered = persisted = served (`coverage_snapshot` id=1 →
  2956/2440 = `UT-04-result.png`). Do not re-open it; backend serving is correct
  (`_upsert_coverage_snapshot`'s reclaim DELETE leaves one row per `asof_key`).
- **J-07 step 2 is measured** — `runs/goal-ops-hardening-iter-61/evidence-drill/` (1078 polls,
  reconciled). It is a decision now, not a data gap.
- **J-07 steps 3/4 + J-05 step 3 stand on prior live evidence** (iter-59 VmPeak 71.26 % of 8192;
  fault drill; cold restart) — warm/boot/coverage code byte-unchanged since. TC-4's "Unavailable"
  indicator is photographed with a control arm (`evidence-drill/TC-4-*.png`).
- **Still owed, non-blocking:** the `[NEW]` walkthrough for J-05 + J-07 (demo NOT_YET) — a passenger
  task, never a round's own goal.
