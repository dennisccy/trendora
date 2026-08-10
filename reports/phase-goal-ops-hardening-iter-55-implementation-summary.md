# goal-ops-hardening-iter-55 — Implementation Summary

**Phase:** goal-ops-hardening-iter-55
**Date:** 2026-08-10
**Written by:** developer

---

## Features Implemented

- **Honest job-history accounting**: when a heavy background data-refresh job runs out of memory partway
  through and has to stop early, the app's "what did this job actually finish?" record now tells the truth.
  Before this fix, if the job completed 3 of 5 steps of one particular background computation before
  running out of memory, the record would still claim that computation was fully refreshed. Now it only
  claims that when every step genuinely finished. Nothing about the job's overall pass/fail outcome
  changes — only this one completeness claim inside its detail record.
- **Finer-grained background scheduling inside the same computation**: the background computation involved
  above (the one that produces evidence used by the Backtest page) now checks in with the rest of the app
  more often while it works, instead of working through large batches uninterrupted. This is a genuine,
  tested improvement to how often the app can respond to other requests during that specific computation —
  though see "Known Limitations" below for why it did not fully solve the underlying responsiveness problem
  this iteration targeted.
- **A previously-flaky automated test script fixed**: one of the automated "replay" scripts that checks the
  app's boot-status indicator was asserting the indicator's final state immediately after the app restarted,
  without waiting for the indicator to actually settle — a race that could make a genuinely-working app look
  broken in automated testing. The script now waits for the real settled state first.

## Changed Behavior

- **Job-history "what was refreshed" list**: previously, a background job that aborted partway through one
  specific computation (forward-looking return statistics) due to memory pressure would still list that
  computation as refreshed in its own history record. Now it honestly omits it when the abort happened
  before every configured piece of that computation finished. Every other item in that same list (coverage,
  market phase, etc.) behaves exactly as before — this change narrows only the one item.

## Backend-Only Items

None — no frontend changes this iteration (the existing "what was refreshed" list on the Data page already
displays this field; it simply becomes accurate for the partial-completion case with no UI code change
needed).

## Incomplete Items

- **Closing the remaining brief unresponsive moments during heavy background computation**: this iteration's
  target was to eliminate the handful of moments where the app's health-check endpoint gave no response at
  all while a specific heavy background computation ran (previously measured at 6 such moments in roughly
  1,800 checks spread over a ~30-minute heavy job). A live, ~30-minute measured test after this iteration's
  fix found 11 such moments — not improved, and the underlying cause was traced to something outside this
  iteration's planned scope: when a SECOND heavy background computation happens to run at the same time
  (triggered by an unrelated concurrent request), the two together can still starve the health-check
  briefly, no matter how often either one individually checks in. Fully solving this would require an
  architectural change (running heavy computation in a separate process) that is a standing decision for the
  product owner, not something this iteration was scoped to change. Full technical evidence is recorded in
  `reports/perf-budgets.md`.
- **One background test file did not finish running** in the time available this dispatch (a known-slow,
  one-time test setup that rebuilds 30 years of historical data from scratch — documented elsewhere as
  taking a very long time by design, not a sign of a problem). The other, more directly relevant test files
  covering this iteration's actual code changes all passed cleanly. A follow-up confirmation run is
  recommended.

## Config and Environment Changes

None.

## Known Limitations

- The live "does the app stay responsive during heavy background work" test still shows brief gaps under
  the specific condition of TWO heavy background computations overlapping at once. This is disclosed in
  detail, with evidence, rather than hidden — see the dev handoff and `reports/perf-budgets.md` for the
  full diagnosis and the recommended next step (an owner-level decision, not a further code tweak).
- One automated regression check (unrelated to this iteration's actual code changes — a check that a
  historical date range's backfill correctly reports "nothing to do") failed on its first run this dispatch
  due to a self-inflicted testing-tool mistake (two copies of the same automated checker accidentally ran
  at once and interfered with each other). Re-running it by itself confirmed it genuinely works; this is
  documented transparently in the regression-replay results file rather than silently corrected.
