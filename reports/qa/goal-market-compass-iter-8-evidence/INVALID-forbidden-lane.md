# ⚠ THIS EVIDENCE IS INVALID — do not use it as journey evidence

**Marked by the coordinator (pump), 2026-08-21, on the out-of-band iter-8 audit's finding.**

`J-01-verify.png` and `J-04-verify.png` in this directory, the replay state in
`runs/goal-session-market-compass/iter-8/.bqa-replay-state`, and the `**Browser QA Verdict:** PASS`
recorded in `reports/phase-goal-market-compass-iter-8-regression-replay-results.md` (rows `UT-J-01`
and `UT-J-04`, both PASS) were produced by a deterministic replay that **should never have run**.

## Why it is invalid

1. **The iteration spec forbade it unconditionally.** iter-8's TC-19, its Definition of Done, and its
   OUT OF SCOPE section all defer J-01–J-04 browser/replay verification to a later iteration —
   with no carve-out for a good result.
2. **`docs/goal.md`'s lane gate forbade it.** Loop mechanics, owner insert #2: no developer,
   reviewer, QA, browser-QA, evaluator, coherence, research or proposer lane may run against the
   knowingly damaged database before J-10's post-recovery verification passes. At 01:40 the recovery
   covered 20 of 587 symbols — verification had not passed.
3. **It started services on a host under a standing memory constraint.** The replay launched a
   frontend *and a second backend* on the box that froze on 2026-08-20 from memory overcommit.

## How it happened — the same root cause as iteration 6

iter-8's spec sets `Depth: full` (line 9), but `runs/goal-session-market-compass/iter-8/depth-dispatched`
reads `lean`. Lean depth auto-enables `CHAIN_LEAN_PARALLEL_BROWSER_QA`, which launched the replay
the instant `developer.done` was stamped. This is orchestration-layer behavior — **not** the
developer's doing. It is the second occurrence; the first is recorded at
`reports/qa/goal-market-compass-iter-6-evidence/INVALID-damaged-database.md`.

## What this means

- The `PASS` rows for J-01 and J-04 **must not** be merged into `journey-history.json`, must not be
  read as journey verification, and must not be treated as clean prospective/OOS evidence (AG-17).
- The reverse also applies: had these rows failed, that would have been expected damage, not a
  regression. Quarantine is symmetric — the iteration-7 evaluator's precedent.
- The audit confirmed the replay caused **no** `daily_prices`, manifest, or provenance mutation.

## Kept, not deleted

AG-17 forbids erasing incident evidence, and the recurrence is itself the evidence that a goal-level
lane gate can be silently bypassed by the depth arbiter. The files stay; they are labelled invalid.
The replay-results file itself is left byte-unchanged — a lane's own verdict is not edited by the
coordinator.

## Framework follow-up (not this cycle's build)

`docs/goal.md` Loop mechanics now requires that an unavailable `Depth: full` be surfaced as an
explicit unmet requirement rather than silently demoted. That rule needs enforcement in the engine's
depth arbiter, which is upstream framework work.
