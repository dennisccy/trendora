# ⚠ THIS EVIDENCE IS INVALID — do not use it as journey evidence

**Marked by the coordinator (pump), 2026-08-20, on the iter-6 reviewer's recommendation.**

The four screenshots in this directory (`J-01-verify.png`, `J-02-verify.png`, `J-03-verify.png`,
`J-04-verify.png`) and the replay state in
`runs/goal-session-market-compass/iter-6/.bqa-replay-state` were produced by a deterministic
J-01–J-04 browser replay that ran at 18:15–18:16Z **against the knowingly damaged database**, after
the iter-6 developer's turn had already ended.

That run should not have happened. `docs/goal.md` (Loop mechanics, owner insert #2) states that no
developer, reviewer, QA, browser-QA, evaluator, coherence, research or proposer lane may run against
the damaged database before J-10's post-recovery verification passes. The lane fired anyway because
iter-6's depth was silently demoted full→lean ("full-cap"), and lean depth enables
`CHAIN_LEAN_PARALLEL_BROWSER_QA`, which launches the replay automatically.

## What this means

- `REPLAY_FAILED=J-02 J-03` in `.bqa-replay-state` is **expected damage, not a regression**. Those
  journeys depend on data the iter-5 drill deleted (2026-08-11 / 2026-08-12; bar frontier is
  2026-08-10). They cannot pass until J-10's recovery completes.
- Per **AG-17**, artifacts produced while the database was damaged remain unusable as evidence.
  These rows must NOT be merged into `journey-history.json`, must NOT be read as a regression
  signal, and must NOT be treated as clean prospective/OOS evidence.
- The run caused **no database or provenance mutation** — independently confirmed by the reviewer
  and by the coordinator (`daily_prices` max date 2026-08-10, `scanner_runs` max `asof_date`
  2026-08-10, `next_session_manifests` 24 rows reaching as_of 2026-08-12, all unchanged).

## Kept, not deleted

The files stay in place because AG-17 forbids erasing incident evidence, and because the depth
demotion → parallel-browser-QA interaction is itself a framework finding worth keeping. They are
labelled invalid rather than removed.

## Framework follow-up (not this cycle's build)

The lean-depth parallel browser-QA lane has no awareness of a goal-level lane gate. Any project that
declares "no lanes against this dataset" in `goal.md` currently has that rule silently bypassed when
the depth arbiter demotes an iteration to lean. Recorded for the framework maintainers; not fixed
here.
