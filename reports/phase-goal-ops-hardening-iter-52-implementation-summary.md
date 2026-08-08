# Goal iteration 52 — Implementation Summary

**Phase:** goal-ops-hardening-iter-52
**Date:** 2026-08-08
**Written by:** developer (audit-fix pass, after an audit FAIL — updated from the earlier fix pass)

---

## What this latest pass did, in one paragraph

The audit did not dispute the engineering; it failed the iteration on **verification**. Three checks the
iteration promised had never actually been run, and the eight-journey browser check had been run against
an older copy of the code, so its results no longer described what ships. This pass **ran the three
missing checks against the code as it stands**, corrected two comments that overstated what the change
does, and changed nothing else. Two of the three checks came back clean. The third — the one that runs a
data job **while somebody is using the research pages at the same time** — came back **much better but
not perfect**, and that is reported as "not met", not rounded up.

### The three checks, and what they found

1. **Status checks during a data job, with someone using the site at the same time.** 1,285 status checks
   over a full 23-minute data job while a Factor Lab / Factor Combination page load ran continuously
   alongside it: **1,283 answered, 2 missed.** The comparable historical measurement missed 19 out of 892
   — so the miss rate fell from 2.1% to 0.16%, about **14 times better**, but **not zero**. Both misses
   happened in two early stages of the job (the coverage refresh and the market-phase warm-up) that this
   iteration deliberately did not touch; **none** happened in the stage it did fix.
2. **The failure-recovery test** (what happens when a stage of the job runs out of memory) was re-run
   against the current code — **passed**, in 18 minutes. Previously it had only ever been run against an
   older copy.
3. **The Factor Lab page's load time**, owed to the budgets file for two rounds, was finally measured in
   a real browser: the page is **interactive in about 21-25 milliseconds**, fully settled in about
   **1.2 seconds**, and its data request comes back in **10-65 milliseconds** from the warmed store.

### One thing that got worse, stated plainly

With a user browsing the research pages at the same time, the data job's finishing stage took
**1,261 seconds against its 1,200-second budget — 5% over.** The same stage on the same code took 955
seconds with nobody else using the site. The budget was not changed or reinterpreted; it is simply
exceeded when the machine is doing two heavy things at once, and somebody needs to decide whether that
budget was ever meant to cover the busy case.

---

## The problem in plain language

When the app runs a data job, one long stage of that job (the "Factor Lab" warm-up) used to hog the
processor so completely that the app could not answer its own status check (`/api/health`) for over a
second at a time. The status badge every page polls would sometimes appear to hang, and in the previous
measurement 22 of ~1,500 status checks never got an answer before the client gave up after 5 seconds.

The first attempt at fixing this (earlier in the same iteration) added "let someone else have a turn"
points between items of each loop. It did not work — the measurement got *worse*, not better.

This pass found out why, by watching the running program and recording exactly where it was each time it
stopped responding. Two operations were each blocking everything for **over a second at a time**, and
neither of them could be interrupted by a "let someone else have a turn" point, because each is a single
indivisible internal operation:

1. **Sorting the observation list.** Each of the 55 factor/horizon combinations sorts about 1.27 million
   records in one go. Measured: 1.09–1.23 seconds of total blockage, 55 times per job.
2. **Automatic memory housekeeping.** Because each combination creates 1.27 million short-lived records,
   the runtime's garbage collector kept running full sweeps. Measured: 154 sweeps totalling **121 seconds**
   of total blockage in a single stage, the worst one 1.09 seconds.

---

## Features Implemented

- **Chunked sorting**: the big sorts are now done in pieces of 50,000 records and merged back together,
  releasing the processor between pieces. The result is the *identical* list — this was verified record by
  record, by object identity, not just by comparing values.
- **Bounded memory-housekeeping pause**: the automatic garbage collector is paused for the duration of one
  factor/horizon combination (seconds, not the whole job) and switched straight back on afterwards,
  including if that combination fails. The bulk data created there cannot form the kind of loop the
  collector exists to clean up, so pausing it changes nothing except when the pauses happen.
- **Bounded clean-up of finished work**: the ~1.27 million records from each combination are released in
  pieces rather than all at once, because releasing them in one go was itself a half-second freeze.
- **Kept from the first pass**: the "let someone else have a turn" points added to every loop boundary.
  They are cheap and they do help the ordinary loops; they simply could not reach the three operations
  above.

---

## Changed Behavior

- **Status checks during a data job now always get an answer.** A full data job was run through the real
  app and its status endpoint polled once a second from start to 40 seconds past completion: **1,021 polls,
  1,021 answers, zero misses.** The previous measurement of the same drill had 22 misses, and the
  measurement before the iteration started had 9.
- **Data jobs finish faster and inside their budget.** The whole finalize stage came in at **955.75 seconds
  against its 1,200-second budget**, on a job that ran to completion; the previous measurement was already
  1,670.95 seconds *before* it finished. The Factor Lab warm-up specifically dropped from 702.99 s to
  **486.62 s**, and an isolated like-for-like re-measurement on the same database shows 571.9 s → 462.5 s
  (**19% faster**).
- **Peak memory is slightly lower**, not higher (isolated measurement: 1,904,896 kB → 1,771,404 kB; in the
  live job, 4,147 MB against the 8,192 MB cap, a 49% margin).
- **Nothing a user sees changes.** No page, number, table, or button is different. Every figure the
  Factor Lab, decile tables, rank-IC and drawdown-expectation screens show is unchanged.

---

## Backend-Only Items

None. This iteration adds no capability that needs UI wiring — it changes only *when* the backend yields
the processor, never what it computes or serves.

---

## Incomplete Items

- **TC-2 (the measurement taken while somebody is using the research pages at the same time)** — now RUN,
  and **NOT MET**: 2 status checks of 1,285 went unanswered. Fourteen times better than the historical
  measurement it was written against, but the requirement says zero. Both misses are in two early job
  stages that were outside this iteration's scope; fixing those is the obvious next piece of work and was
  deliberately not attempted here, because a new code change would immediately invalidate the browser
  check that has to run after this pass.
- **TC-5 (the finishing stage's time budget)** — met with nobody else using the site (955s of 1,200s),
  **exceeded when somebody is** (1,261s, 5% over). Disclosed above.
- **TC-7 (Factor Lab page load time measured in a real browser)** — now MEASURED and written into the
  budgets file. Measured by the development pass rather than the browser lane; if the browser lane's
  re-run disagrees, its number is the one that counts.
- **TC-8, TC-9, TC-12 (the eight-journey browser/replay check)** — **still outstanding, and this is the
  blocking item.** It must run LAST, after this pass, with no further code change afterward. The previous
  run was measured against an older copy of the code, so it cannot be used.
- **The job's first stage (writing the snapshot) is still not tuned.** The previous measurement found 3 of
  its 22 unanswered checks there, and this pass did not change that code path. See Known Limitations.

---

## Config and Environment Changes

None. No new setting, no new environment variable, no schema or migration change. The chunk size is a
fixed in-code constant, deliberately not a configuration key.

`config.yaml`, `project-extensions/host-guard/host-guard.env`, `scripts/start-backend.sh`,
`scripts/dev.sh` and `scripts/start-frontend.sh` are untouched — verified empty in `git diff --stat`
before and after.

---

## Known Limitations

- **The status endpoint is not cheap.** `/api/health` does real database work on every call (roughly
  0.14 s at rest on this data), which is already above the 0.1 s steady-state target before any job is
  running. This pass did not change it; it is a separate, worthwhile piece of work.
- **The two-second target for individual status checks is closer but still not met.** 16 of the 1,021
  checks took longer than 2 seconds (worst: 3.8 s), down from 94 of 1,471 (worst: 5.0 s). None of them
  happened during the stage this fix targeted.
- **The snapshot-writing stage of a data job, and the market-phase warm-up, were not touched** and between
  them account for 11 of those 16 slow checks. Both were outside this iteration's scope; both are named as
  the strongest candidates for the next one.
- **The measurement is one job on one date**, as every previous measurement has been. The isolated
  like-for-like re-measurement is the stronger evidence for *why* it is faster; the live job is the
  stronger evidence for *that* it is.
- **The budget was not adjusted.** The 1,200-second finalize budget was set when the underlying data was
  far smaller — the forward-returns table has grown from ~344 thousand rows to ~6.5 million and the
  database from ~811 MB to 8.4 GB — but it was left exactly as it stands; this run simply came in under it.
- **The garbage-collector pause is a global setting, and it is in effect for far longer than the earlier
  wording here admitted.** This was corrected in the audit-fix pass: the pause is taken and released once
  per factor/horizon combination, but the 55 combinations run back to back with essentially nothing in
  between, so in practice the collector is switched off for the **whole Factor Lab warm-up stage**, not
  "for seconds". Anything else the server does in that window has its own memory housekeeping deferred
  until the window closes. Nothing is lost — the memory is still reclaimed, just later — and the setting
  is restored on every exit path including errors, which tests cover. It also does not stack: if two of
  these windows overlap, the first one to finish switches the collector back on underneath the second, so
  overlapping use weakens the effect rather than leaving the collector off. The audit asked for this to be
  measured under load; it now has been: peak memory 4,886 MB against the 8,192 MB ceiling (a 40% margin)
  with no out-of-memory error while a data job and continuous page loads ran together.
- **A Factor Lab page request made while a data job is running can still hang for over ten minutes.** One
  of the 164 page loads issued during the concurrent measurement never got an answer inside its own
  10-minute limit. This is the same underlying contention seen from the page's side rather than the status
  check's side. It is newly measured, not newly caused, and it has not been diagnosed.
- **The concurrent measurement did not actually exercise the stage this iteration fixed.** The page load
  running alongside the job computed the Factor Lab data itself, so by the time the job reached its own
  Factor Lab warm-up there was nothing left to do (0.05 seconds). The earlier solo measurement remains the
  evidence for that stage.
