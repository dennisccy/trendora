# Goal Session ops-hardening — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-07-19T15:19:32Z

**Verdict:** CONTINUE
**Lesson:** J-01's real blocker is NOT the obvious missing exclusion-reason schema but the
cadence gate: `_do_backfill` (`data_manager.py` ~:2496) filters every backfill through
`_cadence_allowed_dates`, and because `snapshot_cadence.daily_start` is `2026-06-01`, the exact
goal.md-suggested May 2026 range (and J-05's 2026-05-15 single-day date) both compute
`dates_total=0` and ingest nothing. So J-01 and J-05 share ONE root cause — "requested range
always wins" must land before either journey can even be exercised. Secondary: the iter-25 prose
in `reports/perf-budgets.md` claims `start-backend.sh` applies a `ulimit -v` cap, but the current
script applies none (confirmed by source read + `/proc/<pid>/environ`) — whoever builds J-04's
memory-cap enforcement must not assume that doc reflects reality.
**Applies to:** any iter touching `data_manager.py` `_do_backfill` / `_cadence_allowed_dates`
(build J-01's explicit-request override before J-05); any iter building J-04's logfile/memory-cap
layer in `scripts/start-backend.sh`.
