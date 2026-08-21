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

---

## ADDENDUM — the forbidden lane RAN A SECOND TIME, at `full` depth, and overwrote these files

**Added by the in-pipeline auditor, 2026-08-21, during the full-depth re-run of iteration 8.**

The quarantine above was placed at 08:30. At **12:53-12:55 the same day** — inside the `full`-depth
re-dispatch commissioned specifically to add the missing audit lane — the UI/replay chain ran again
end to end and **re-executed the J-01/J-04 deterministic replay**, overwriting both screenshots:

| file | bytes at 01:40 (quarantined, committed `47d50d04`) | bytes written 12:54-12:55 |
|---|---|---|
| `J-01-verify.png` | md5 `bd13782d00c37abd0a0ee4a17eeb852d` | md5 `eaacb5973639ca0dd96c695b968534fb` |
| `J-04-verify.png` | md5 `9e9cc6fe68e08e08ab496d6be6c081bd` (134,545 B) | md5 `190d16c0f5f8f0df0ec38396a68ee418` (134,514 B) |

Corroborating timestamps for the second lane: `…-ui-surface-map.md` 12:53:06,
`…-ui-test-plan.md` 12:53:57, `…-what-to-click.md` 12:54:12, the two PNGs 12:54:58 / 12:55:02,
`…-regression-replay-results.md` re-written 12:55:02 (byte-identical content, same `PASS` rows),
merged `…-ui-test-results.md` 13:01:14. A Next.js frontend was started for it
(`fanout-frontend-8255.log`: "Ready in 270ms" … "Killed") and a backend start was attempted
(`fanout-backend-8255.log`, created 12:48:07, empty) — both of which this iteration's spec forbids
in OUT OF SCOPE.

**`depth-dispatched` now reads `full`, so lean-depth auto-parallel-browser-QA is NOT the mechanism
this time.** The replay lane runs at full depth too. The reviewer's note that this was "already
remediated (depth-dispatched now reads full)"
(`reports/reviews/goal-market-compass-iter-8-review.md`, NOTE item) is therefore incorrect: the
depth marker was corrected and the forbidden lane ran anyway. TC-19 is violated by the pipeline at
**both** depths.

### What the auditor did about it

1. **The original quarantined bytes were restored** from commit `47d50d04` into `J-01-verify.png`
   and `J-04-verify.png` (hashes re-verified above), because AG-17 forbids the incident record being
   "deleted, rewritten, or silently superseded" and this note names those specific files.
2. **The second run's bytes were preserved, not deleted**, as
   `INVALID-rerun-2026-08-21T1254-J-01-verify.png` and
   `INVALID-rerun-2026-08-21T1254-J-04-verify.png` — they are the evidence that the lane recurred.
   Both are invalid as journey evidence for exactly the reasons listed at the top of this file.
3. **No database mutation resulted from the second lane.** `apps/backend/data/trendora.db-wal` has
   not been written since 2026-08-21 01:44:51 local, and every cache/derived row created on
   2026-08-21 carries a timestamp ≤ 00:44:51 UTC. The 12:48-13:02 services made no writes.

Everything the original quarantine says still applies, unchanged, to both sets of screenshots.
