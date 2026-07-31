# goal-ops-hardening-iter-39 — Implementation Summary

**Phase:** goal-ops-hardening-iter-39
**Date:** 2026-07-30
**Written by:** developer

---

## Features Implemented

This iteration is operational hardening and test-tooling repair, not a new user-facing
feature. Nothing new appears on any screen.

- **Deterministic replay lane now tells "backend is down" apart from "this journey actually
  broke."** When the automated pipeline replays a saved browser test and the backend isn't
  answering, every test in that run is now marked "Blocked" instead of "Failed." Previously a
  down backend produced false failure reports that looked exactly like real regressions — this
  happened twice in this project's history and wasted investigation time both times.
- **The automated test report now lists every test the AI browser-checker overturned**, not
  just some of them. Previously the summary line at the bottom of a test report ("these N tests
  were re-checked and found to actually be fine") sometimes silently left tests off that list
  even though they genuinely were re-checked and found fine.
- **A backend on/off switch used for testing (`TRENDORA_FORCE_LEGACY_BAR_CACHE`) now behaves
  correctly when explicitly turned off.** Before this fix, setting it to `0` (meant to mean
  "off") was silently treated the same as turning it "on" — the opposite of what someone
  setting it would expect.
- **The backend now writes its own routine activity to its logfile.** Previously the app had no
  logging configuration at all, so only warnings and errors ever made it into
  `logs/backend.log` — ordinary "this ran successfully" notes were silently thrown away. Operators
  investigating what happened during a job now have a fuller record.
- **A specific memory-pressure test proving the app doesn't crash under load was re-measured
  end to end.** It confirms: when part of a background data job runs low on memory partway
  through, the app catches that specific failure, logs it, and keeps serving normal requests
  (the health check and cached results) without crashing or needing a restart. See "Known
  Limitations" below for exactly which part of the job this was proven for, and which part
  was not.

---

## Changed Behavior

- **Automated regression test reports**: Previously, if the backend was down when the
  automated (non-AI) replay tool ran, it reported every test as a hard "Failed." Now it reports
  them as "Blocked" — a distinct outcome meaning "we couldn't check this, the backend wasn't
  answering," never a claim that something is actually broken.
- **A specific internal logging line about the backend's data-caching behavior** moved from
  showing up in the log as a "Warning" to showing up as ordinary "Info" — it was never actually
  a warning, it was mislabeled that way only because the old logging setup would have silently
  dropped it otherwise.

---

## Backend-Only Items

None — every change this iteration is either internal hardening (no user-visible surface at
all) or automated-testing infrastructure (not part of the product itself).

---

## Incomplete Items

- **The specific "prove the app survives a memory-pressure failure in this exact spot" test**
  did not land in the exact spot the plan asked for. It proved the app survives a
  memory-pressure failure that happens in a DIFFERENT, closely-related internal step (the
  step that checks how complete the price-history data is), not the two originally-targeted
  steps (a forward-looking-returns calculation and a drawdown-odds calculation). All three
  live attempts at different memory ceilings are documented with full detail in
  `reports/perf-budgets.md`. This is a disposition call for the project owner: the broader
  promise ("the app never crashes under memory pressure") IS proven with real evidence; the
  narrower promise (proven in that one specific spot) is not.
- **A new, previously-unknown issue was found while testing tighter memory ceilings**: at one
  tested ceiling, the backend became completely unresponsive for over 7 minutes after a
  background job otherwise finished successfully — a real hang, not just slowness. This was
  NOT fixed this iteration (it's a new, separate problem outside this iteration's planned
  scope); it's documented as a priority item for a future iteration.
- **Refreshing the automated browser test scripts' outdated element-selectors** (flagged in a
  prior review as causing test failures) was not done by this developer session — that
  refresh requires an actual browser session, which is a different pipeline stage's job (it
  runs automatically later in this same iteration).

---

## Config and Environment Changes

- No new user-facing config or environment variables.
- `TRENDORA_FORCE_LEGACY_BAR_CACHE` (existing, internal/test-only toggle) — behavior corrected
  (see "Changed Behavior" above); no new default, no new usage.
- A new internal Python module (`app/logging_config.py`) configures the backend's log output
  level; no new setting to configure, it is on by default and cannot be turned off.

---

## Known Limitations

- The memory-pressure resilience proof (see "Incomplete Items") covers a real, but not the
  originally-targeted, internal computation step. See `reports/perf-budgets.md`'s "Iteration
  39" section for the full technical account.
- A real backend hang (not a crash — a hang requiring the process to be killed and restarted)
  was discovered at a tighter memory ceiling than the one used for the completed proof above.
  It has not been fixed. See the dev handoff's "Known Issues" for detail.
- Two overdue live tests (does the "in-progress job" screen survive a hard backend kill and
  restart; does the "data coverage" screen show real numbers immediately after a cold restart)
  were both run for real this iteration, against the actual development database, with a real
  `kill -9` and restart — both passed with real evidence. This closes an item that had been
  postponed across several prior iterations.

---
---

# FIX PASS — after the audit returned FAIL (2026-07-31)

The audit failed this iteration on two items. Everything above still stands; the sections below
supersede the specific items they name. Written for operators, not developers.

## What the audit objected to, in plain language

Trendora computes a set of heavy summaries at the end of every data-import job. Journey J-07 promises
that if the machine runs short of memory while one of those summaries is being built, that **one**
summary gives up honestly and everything else keeps working — the app must never freeze, and must never
need restarting.

Proving that promise meant deliberately running the app out of memory and watching where it broke. The
first pass did that by squeezing the app's memory ceiling tighter and tighter. Three squeezes later it
still had not broken in the intended place, and the tightest squeeze froze the app outright. The audit
called out both: the promise was not proven where it was supposed to be, and the attempt had produced an
example of the very freeze J-07 says must never happen.

## Features Implemented (fix pass)

- **A safe way to rehearse a memory failure.** The app can now be told, *at startup only*, to pretend it
  ran out of memory at one specific internal step. Nothing about normal behaviour changes — the switch
  is off unless someone deliberately sets it. This replaces "squeeze the whole machine and hope the
  failure lands in the right place" with "make the failure happen exactly where we want to watch it".
  It is repeatable, and because no real memory shortage is created it carries none of the hardware risk
  the squeeze method carried on this machine (which has twice hard-reset under that kind of load).

- **The rehearsal was run against a live, running copy of the app** — throwaway database, started
  through the project's normal start script with all its safety limits intact, at the **normal shipped
  memory ceiling, deliberately not lowered**. What happened:
  - the intended step, and only that step, gave up;
  - the job still finished successfully and reported honestly which summary was missing;
  - every other summary completed normally, including ones that run *after* the failed one;
  - the app answered its health check **68 times out of 68** during the job, with no gap;
  - a page request already **in mid-flight at the exact instant of the failure** completed normally with
    the full expected result — as did 500 more requests after it;
  - the app never restarted and never froze.

- **Import jobs now handle a memory shortage inside their own worker threads.** Previously, when one
  date's work ran out of memory the failure was handed back to the coordinating thread while the worker
  immediately started the *next* date and asked for more memory again — and the failed work stayed in
  memory the whole time. Now it is handled where it happens: memory is released immediately and the
  remaining dates stop rather than piling on. Those dates are reported as failures, honestly, so the
  job's totals still add up exactly.

## Changed Behavior (fix pass)

- **Import job under memory shortage**: previously every remaining date kept trying and kept allocating
  after the first failure. Now the first failure stops the rest. Measured with three dates where the
  first fails: dates that went on to attempt real work dropped from **3 to 1**.
- **Pipeline reporting wording** (internal tooling, not the product): when the automated browser-test
  lane overturns an earlier failure, its closing note now describes what actually happened per journey.
  Before, it always said the failure had been "disproven by a re-confirmation" — even when the truth was
  "this journey was never re-checked". A result meaning *not verified* can no longer be written up in
  words meaning *verified good*.
- **Still no change to any screen, number, or user action.**

## Incomplete Items (fix pass) — supersedes the first two entries above

- **The freeze is not proven fixed. Treat it as open.** The audit's best guess was that an import worker
  thread caused it. That guess does not survive checking: by the time the freeze began, those workers
  had already finished and been shut down. The worker fix in this pass is correct and worth having on
  its own merits, but it should **not** be read as retiring the freeze. Reproducing it would mean
  deliberately exhausting the machine's memory again — the exact action this pass removed.

- **The most likely underlying cause was identified but deliberately not fixed.** One step of the
  end-of-import summary work loads the **entire price table into memory at once** (~3.3 million rows)
  before doing anything with it. This is visible in the freeze's own error trace, it is why the
  memory-squeeze method could never reach the intended step, and it conflicts with the project's own
  rule against unbounded whole-table loads. The fix looks straightforward and would not change any
  displayed number, but it is a structural change the audit did not ask for, so it was left for the next
  iteration rather than bundled in. **This is the recommended next item.**

- **Interrupted-job progress still under-reports** (carried forward): after a hard kill, the job-history
  panel shows the last saved progress, which can lag well behind what was actually done. The row is
  real, not blank — the requirement was met — but a user reads a smaller number than the truth.

## Config and Environment Changes (fix pass)

- `TRENDORA_FAULT_INJECT_MEMORY_ERROR` — **new, rehearsal/test only.** Names which internal step should
  pretend to run out of memory. Default: **unset**, and unset means the app behaves exactly as before.
  Intentionally *not* a setting in `config.yaml` — a failure rehearsal must not be reachable through the
  product's normal configuration.
- No database migration, no schema change, no change to `config.yaml`. The drill used a scratch config
  kept alongside its evidence, at the normal shipped memory ceiling.

## Known Limitations (fix pass)

- The rehearsal switch proves the app's *handling* of a memory failure at a chosen step. It does not by
  itself prove a real shortage would strike at that step. A separate, pre-existing test that squeezes
  real memory in a throwaway process still covers that half; both are kept.
- The freeze hazard above is open and unreproduced. Anyone re-testing it should know the method that
  triggered it has twice hard-reset this machine, and should not repeat it without an explicit decision
  from the owner.
- Two decisions remain that no automated agent can settle (unchanged): whether the health-check speed
  target should be revised for the window when background work is running, and whether the frontend
  start script should come under the same host safety limits as the backend.

## Where the evidence lives

- Live drill, both runs, raw logs and per-request timings:
  `runs/goal-ops-hardening-iter-39/fault-drill/` — start with its `README.md`
- Numbers written up: `reports/perf-budgets.md`, section "Iteration 39 FIX PASS"
- Reviewer-level detail: `docs/handoffs/goal-ops-hardening-iter-39-dev.md`, section "Fix Notes"
