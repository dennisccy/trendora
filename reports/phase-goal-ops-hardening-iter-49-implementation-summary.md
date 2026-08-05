# goal-ops-hardening-iter-49 — Implementation Summary

**Phase:** goal-ops-hardening-iter-49
**Date:** 2026-08-05
**Written by:** developer
**Revision:** 3 — updated after a **second** independent audit again returned FAIL. Revision 1 described
only the build pass; revision 2 carried the first audit's findings. This revision records what the second
audit found, and what the second fix pass did about it. Engineering detail: the two "Fix Notes" sections in
`docs/handoffs/goal-ops-hardening-iter-49-dev.md`.

> **Short version for an operator:** the *code* in this iteration is finished, independently re-checked
> twice, and does what it promised — a historical backfill that used to run long past its advertised window
> now finishes inside it, three times running. What is *not* finished is the round's own final
> verification: the end-to-end journey walkthrough has still not been able to run, because the backend
> crashed during the last attempt. That crash is real, it is in a part of the system this iteration was not
> allowed to touch, and it is the first thing the next round will fix. **No product code changed in this
> pass** — on purpose, so the pending walkthrough can finally be the last thing that happens.

---

## Features Implemented

- **A historical-day backfill now finishes inside the advertised ~20-minute window on an idle machine.**
  Previously, bringing in a historical trading day (a day the system has no snapshot for) appeared to
  finish quickly but then silently kept working for 20+ more minutes — and in the worst observed case never
  finished at all. Across three independent real runs on an otherwise-idle machine the job now reliably
  reaches a finished state in about 17 minutes each time. **Important caveat:** this holds when nothing else
  heavy is happening at the same time. See "Known Limitations".
- **The system now says which part of a data update is slow, not just that "the update" is slow.** New
  detailed logging breaks the time down per calculation step (which specific time horizon, which specific
  claim) instead of one lump total — so a future slowdown can be diagnosed without redoing this
  investigation from scratch.
- **The backend's own start-up promise is now checked automatically, by a test that is allowed to restart
  the service.** The product promise "restart the backend and it is answering within 5 seconds" had gone
  three rounds without ever actually being exercised, because the only checker assigned to it (a
  browser-driven agent) is not permitted to stop or start services. That check now runs in the automated
  test suite, which is permitted: it restarts the real backend, times the first successful health response,
  simulates a crash, restarts again, and confirms a data job that was in flight at the crash comes back as
  an explicit "interrupted" entry with its last saved progress — never a job stuck on "running" with
  nothing actually running.

## Changed Behavior

- **Aggregate calculations that feed the Backtest and Evidence pages run noticeably faster during data
  updates.** The calculation powering the Evidence page's "drawdown expectations" panels is roughly 3-4x
  faster per item, and a bookkeeping step that used to repeat once per item now runs once per data update.
  Nothing these pages *show* changes — the same numbers are produced, just faster, and every changed
  calculation was verified to produce byte-for-byte identical results to before, on 120 automated checks
  plus 3 live production-scale runs.
- **Under memory pressure, one clean-up path now stops instead of trying harder.** If the system runs short
  of memory while preparing a data update's final calculations, it now releases the memory and *stops that
  step*, honestly reporting that the step did not run. Previously it released the memory and then continued
  into a path that asked for *more* memory than the one that had just failed — the opposite of what the
  rest of the system does under pressure. Nothing changes in normal operation; this only affects behavior
  when memory is already exhausted.

## What the audit found (new since revision 1)

An independent audit re-checked this work and returned **FAIL** — not because of the code, which it
re-verified line by line and called "the strongest part of this iteration", but because of *how the
evidence was gathered*:

- During the browser-driven test round, an operator-style browsing session (viewing the Factor Lab and
  Backtest pages) happened at the same time as a routine historical backfill. The backend ran out of
  memory and **died**, and stayed down for roughly six minutes. That crash landed in a calculation this
  iteration never touched and had explicitly ruled out of scope, but it means the product promise "heavy
  aggregates never take the service down" was falsified live in this very round.
- Because the backend was down, most of the round's other journey checks could not run at all: 5 of 5
  replay checks were blocked, and three journeys recorded no result.
- The earlier QA report that says "Definition of Done met" was written 40 minutes before those later
  results and is contradicted by them. It should not be read on its own.

## What the second audit found (new since revision 2)

A second independent audit re-checked everything, re-derived every published number from the raw
measurement files rather than trusting the write-up, and confirmed the product change is genuine. It still
returned **FAIL**, for the same reason: the round's end-to-end verification has not happened. Three things
it added to the picture:

- **The earlier slowdown diagnosis pointed at the wrong place.** Revision 2 reported "one brief health-check
  delay on 2 of 3 runs, early in the backfill". Recounted from the same raw files, the health check was
  slower than its 2-second target **6 to 9 times per run, on all 3 runs**, and each run had two responses
  over 5 seconds. They cluster at three different points, one of which is a step this iteration itself
  added. The record has been corrected (`reports/perf-budgets.md`, Addendum 6) so the next round starts in
  the right place. The delays themselves remain out of scope and unfixed, as before.
- **Two smaller gaps were closed by the auditor directly**: one automated check could have passed without
  actually exercising the code it was meant to test (it now proves the injected fault fired), and one
  warning note pointed future readers at the wrong area.
- **One piece of genuine progress was confirmed**: the backend restart/crash-recovery promise, which had
  gone three rounds with no real check, is now covered by tests that restart and kill the real service and
  read the results back. The auditor read them in full and confirmed they are not placeholders.

## What this (second) fix pass did

The audit's own recommendation opens with "do not send this back for another developer fix pass on this
diff". This pass followed that:

- **No product code was changed at all** — deliberately. The final journey walkthrough is required to be
  the *last* thing that happens before the round is scored, and every further code edit resets that clock.
  It has now been reset three rounds in a row; this pass stops doing that.
- **The one remaining item a developer could close was closed**: a test file was missing from the previous
  pass's list of changed files (bookkeeping only — it was correctly recorded everywhere else).
- **The backend was restarted and left running, healthy.** This was the audit's own blocker #1 and the
  literal reason the last two verification attempts produced nothing. It answers its health check in 0.6
  seconds, finished its background warm-up without running out of memory, reports itself `ready`, and is
  using about a fifth of its allowed memory. Its safety limits were confirmed unchanged in the start-up log.
- **The restart/crash-recovery checks were re-run** and pass: 1.3 seconds to first response (budget: 5), and
  an in-flight data job correctly comes back as "interrupted" with its last saved progress after a crash.

## Backend-Only Items

None — this iteration adds no new user-facing control, page or endpoint. Everything here is internal
calculation speed, memory-pressure behavior, and automated verification.

## Incomplete Items

- **The service-availability promise is not met under concurrent use, and is not fixed here.** The crash
  described above traces to a research calculation (the Factor Lab's full computation) that has no memory
  bound and no coordination with the background data-update work. Fixing it is a change of the same size
  and risk as this iteration's own work, and the project's rules allow one such change per iteration, so
  it is deliberately carried to the next one — named, located, and with the evidence attached.
- **The full end-to-end journey verification still has to be run — this is the only thing left.** It must
  run against a healthy backend and be the last thing that happens before this iteration is scored. **Both
  preconditions are now in place**: the backend is up and healthy (this pass restarted it and left it
  running), and no product code has changed since, so the walkthrough can finally be last. Two of the eight
  journeys have produced no result for three rounds purely because the service was unavailable when they
  were attempted.
- **Delays in the system's own "are you alive?" health check.** Corrected count: the check exceeded its
  2-second target 6-9 times per run on all 3 runs, with two responses over 5 seconds in every run. Every one
  recovered on its own; none is a hang. They occur at three separate points, one of them a step this
  iteration added. Not fixed here — this class of finding is explicitly out of scope for this round — but
  now correctly located for the next one.
- **One remaining slow calculation** (a "combined-conditions" research claim, ~4 minutes on its own) was
  identified but not sped up, to avoid a second risky change in the same iteration. The overall backfill
  still finishes within budget without it.

## Config and Environment Changes

None. No new environment variables, no configuration changes, no database schema changes. The memory and
CPU safety limits were verified unchanged and still enforced (peak memory during the heaviest data update
stayed under half the allowed limit in every measured run), and re-confirmed in the start-up log of the
backend this pass left running.

**One operational note, not a change:** the backend is **currently running** on port 8255, started through
the normal launch script, and was deliberately left up so the pending end-to-end verification can proceed.
The frontend is **not** running and will need to be started (port 3255) for that verification.

## Known Limitations

- **The 20-minute promise is proven on an idle machine only.** Three runs met it with about 15% headroom
  with nothing else running. The one run that happened alongside ordinary page browsing did not — a single
  calculation that takes 50 seconds by itself had not finished after 10.5 minutes, and the process then
  ran out of memory and died. Operators should not treat the current build as safe for browsing heavy
  research pages during a backfill.
- **A brief unresponsive window can occur early in a historical backfill** (the ~10-second health-check
  delay above). It always recovered on its own in every measured run — a disclosed rough edge, not a hang.
- **Test-suite coverage note.** The suites that most directly cover this iteration's changes were run to
  completion and are green (146 + 33 checks). Two broader suites that nobody in this round had ever run to
  completion were run this pass:
  - The suite covering the calculations this iteration changed: **95 of 96 checks pass** in 12.5 minutes.
    The one not run needs a test-only setup step (building a full 30-year historical dataset from scratch)
    that takes hours on this machine; it covers a calculation this iteration never touched, and starting a
    multi-hour job now would have put exactly the kind of heavy background load on the machine that caused
    this round's crash.
  - The start-up/warm-up suite: **21 of 22 pass** in about an hour. The one failure is a *pre-existing*
    inefficiency, not a break: during a warm-up the two market-index symbols (S&P 500 and the volatility
    index) get their price history re-read once per historical date instead of once in total, while all
    ~500 company symbols are read exactly once. This was proven to pre-date this iteration by re-running the
    same check against the untouched original code, where it fails identically. It is recorded for a future
    round rather than fixed here, to keep this pass to the audit's own list.
