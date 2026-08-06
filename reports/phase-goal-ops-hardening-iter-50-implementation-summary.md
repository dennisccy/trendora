# goal-ops-hardening-iter-50 — Implementation Summary

**Phase:** goal-ops-hardening-iter-50
**Date:** 2026-08-06 (audit-fix pass 2 — supersedes the pass-1 summary below the line)
**Written by:** developer

---

## In one paragraph, for an operator

The Factor Lab research page used to be able to take the whole backend down when someone opened it while a
data job was finishing. This iteration bounded the memory that page consumes and taught it to fail one cell
at a time instead of taking the service with it. This second fix pass did three things: it **actually ran
the scenario the iteration exists to prevent** — a real data backfill running while someone loads the
Factor Lab page — and watched the service's health once a second for 25 minutes, including seven minutes
after the job ended; it **closed a data-tolerance gap** the previous pass accidentally introduced; and it
**added timing to the one part of the job-shutdown sequence nobody had ever measured**, so if the service
ever goes quiet again, the log will say where. The run came back clean: the page returned a full, correct
result, and the service answered every one of 1,179 health checks. One promise is still not met and is
reported as failing, not rounded up: during heavy work some health checks took up to ten seconds instead of
the promised two. They all succeeded — the service was slow, never down.

---

## Features Implemented

- **The crash scenario was executed for real, end to end.** A genuine backfill of one historical trading day
  was started through the product's own Data Manager API, the Factor Lab page was loaded 12 seconds later
  while that job's heavy finishing work was still running, and the service's health was checked once per
  second for 25 minutes — continuing for 7 minutes *after* the job finished, because the last outage began
  right after a job's final step. The Factor Lab page returned a complete, correct result (all 11 factors,
  all 55 factor/horizon cells, none degraded) and every single health check succeeded.
- **Timing added to the job-shutdown step.** The last thing a data job does is release the memory it used.
  That step had never been timed, and it sits exactly where the service went silent for 17 minutes on
  2026-08-05. It now writes one line before it starts and one line when it finishes, with how long each
  part took. In this run it took **0.11 seconds**.

---

## Changed Behavior

- **Factor Lab, unusual stored values.** Previously, if a stored factor value had been written as text
  (`"3.5"`) rather than a number (`3.5`), the whole Factor Lab page returned a server error for every
  visitor. Now such a value is read as the number it represents, exactly as it was before this iteration's
  memory rework. A value that is not a number at all (`"n/a"`, a list) is treated as missing — the same way
  a genuinely absent value has always been treated — and is written to the log, rather than being invented
  or blanking the page.
- **Factor Lab, one bad cell.** Previously, an unexpected error while computing any single factor/horizon
  cell returned a server error for the entire page — all 11 factors gone because of one. Now that one cell
  reads "unavailable" and every other cell still shows its real numbers. This mirrors how the Evidence page
  already handles a single failing claim.
- **The J-05 regression script now waits for the real job.** The stored click-by-click script for the
  "aggregates are precomputed at ingest" journey waited 15 seconds for a job that takes about 11 minutes,
  so it could never pass. It now waits the real duration and checks the specific job's own figures
  (its own date counts, its own list of refreshed aggregates, and its own row on the Scanner Runs page)
  rather than text that could appear anywhere on the page.

---

## Backend-Only Items

- None new. This pass added no endpoint, no field, and no displayed value. The two behavior changes above
  are corrections to how existing pages behave, not new capability.

---

## Incomplete Items

- **The full 8-journey browser test run has still never been executed against this iteration's current
  code**, and this pass changed backend code again, so that run is mandatory before the iteration can be
  closed. The existing QA report was deliberately left untouched: its verdict must be regenerated from the
  re-run, never edited by hand.
- **The "health answers within 2 seconds during heavy background work" promise is not met.** 96 of 1,179
  checks took longer, worst case 10.06 seconds. All 1,179 succeeded. The cause is two heavy computations
  competing inside one process, which bounding memory cannot fix; the structural fix (compute the Factor
  Lab result when data is ingested and serve it from storage) is a future iteration's work.
- **Whether the 17-minute service silence of 2026-08-05 is fixed is still unknown.** It did not happen
  again in this run, but this run's memory footprint was about a third of that day's, so the comparison is
  not like for like. The new timing lines mean a recurrence will now be attributable instead of a mystery.
- **The in-browser half of the J-05 journey** (the Scanner Runs page rendering the new snapshot) is the
  browser test lane's to prove; this pass proved the data half — the job's stored record lists all seven
  aggregate categories it refreshed.

---

## Config and Environment Changes

- **None.** No environment variable, no configuration value, no database migration. The four frozen launch
  and configuration files (`config.yaml`, the host-guard settings, and the two start scripts) were verified
  byte-identical before and after this pass.

---

## Known Limitations

- The J-05 regression script is **single-use per date**: it backfills a day that has no snapshot yet, so
  once it runs successfully that date is consumed and the script must be pointed at a new one. `2010-11-08`
  is reserved and confirmed unused; this pass's own test deliberately used `2010-11-09` instead so as not to
  spend it.
- That same script now takes about 19 minutes to run, because it waits out a real backfill. That is the
  price of proving the journey deterministically rather than skipping it.
- Under the concurrent load of this test, one stage of the data job took 448 seconds instead of its usual
  80 — the same slow-down cause as the health checks above. Nothing failed; the work simply shares one
  processor with the page request.
- A background aggregate refresh that steps aside for a data job still leaves its remaining work until the
  next restart (carried from the previous pass, unchanged).

---

<!-- ============================================================================================== -->

# Superseded — pass-1 summary (2026-08-05/06)

The sections above supersede the earlier summary for this iteration. Nothing below is deleted; it records
what the first development pass and the first audit-fix pass delivered, and the one claim of theirs that has
since been withdrawn.

**Withdrawn claim:** the first audit-fix pass reported "TC-1 both clauses met live". That measurement was
taken with **no data job running**, which is the defining condition of the scenario, so it did not establish
what it claimed. Its numbers remain valid as a record of a Factor Lab page load on an otherwise idle
instance. See `reports/perf-budgets.md` Addendum 9's correction block and Addendum 10.

**What those passes delivered, and still stands:**

- The Factor Lab page's memory use was re-engineered at the site where five real crashes actually occurred,
  cutting the observation store from roughly 128 bytes per row to about 26, with every displayed figure
  proven byte-identical to a pinned copy of the old code.
- A memory failure anywhere in that page's computation now degrades the response honestly instead of
  killing the backend process.
- Two heavy background warm-ups (the one a data job runs at the end, and the one the backend runs at boot)
  can no longer run at the same time in one process; the boot one steps aside and retries at the next start.
- A ~24-second precomputation inside the data job's finishing sequence is now skipped entirely when nothing
  needs it.
