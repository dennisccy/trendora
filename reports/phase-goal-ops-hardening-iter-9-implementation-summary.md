# goal-ops-hardening-iter-9 — Implementation Summary

**Phase:** goal-ops-hardening-iter-9
**Date:** 2026-07-22
**Written by:** developer

---

## Features Implemented

This iteration is a verification-and-compliance closeout, not a new-feature iteration — nothing new is
visible to an end user of the app. What changed is operational/hardware-safety plumbing:

- **Both launch scripts now actually apply the machine's declared safety limits.** Previously, only
  `scripts/start-backend.sh` enforced a memory ceiling, and neither script applied the CPU-core /
  processing-thread limits this machine needs after two unexpected full shutdowns earlier this week.
  Starting the backend now automatically confines it to the same safe set of CPU cores and thread limits
  every time — whether it's started the "production" way (`start-backend.sh`) or the "developer" way
  (`dev.sh`) — with zero action required from whoever launches it.
- **A stricter, more trustworthy safety-net test.** The existing automated check that proves "a big data
  rebuild followed immediately by another big data job won't crash the server" now also insists that both
  jobs report a fully successful outcome (not a partially-successful one), and that every piece of the
  job's follow-up bookkeeping actually completed — catching a subtler class of silent partial failure the
  previous version of this test could have missed.
- **New automated checks that prove the safety limits are really being applied** — and, just as
  importantly, that they never get applied by accident when the safety-limits file is missing or turned
  off (so a developer without that file still gets a normal, unrestricted experience).
- **A small internal efficiency fix** (optional, "if capacity allows" in the plan, and it did): a repeated
  low-level system lookup used during memory cleanup now only happens once per server run instead of every
  single time cleanup runs, removing some unnecessary background work with no change in what it actually
  does.

---

## Changed Behavior

- **`scripts/start-backend.sh`**: previously enforced only the memory ceiling and thread-arena limit. Now
  ALSO pins the process to the machine's declared safe CPU cores and caps its math-library thread counts —
  automatically, whenever the machine's safety-limits file says to. If that file is missing or turned off,
  behavior is unchanged from before.
- **`scripts/dev.sh`**: previously applied NO safety limits of any kind to the backend it starts (only the
  frontend and backend were started plainly). Now the backend half applies the exact same memory ceiling,
  thread-arena limit, CPU-core pinning, and math-library thread caps as `start-backend.sh` — the frontend
  half is completely unchanged (it still needs full, unrestricted resources to compile the app).
- **The heavy back-to-back ingest safety-net test**: previously accepted either a fully-successful or a
  "partially successful" result as passing. Now only a fully-successful result passes — a partial result
  is treated as a real problem to investigate, not a soft pass.

---

## Backend-Only Items

- All of this iteration's changes are backend/operational (launch scripts, an internal test, an internal
  memory-cleanup helper) — there was never a UI component to wire, per the phase's own "no UI code changes
  this iteration" instruction.

---

## Incomplete Items

- **The one full "real-world" proof run under the new safety limits was not performed this session.**
  The plan called for actually running the heaviest possible back-to-back data job on this machine, under
  the new safety limits, and recording the memory usage. At the time of this work, this machine was already
  noticeably warmer than its normal resting temperature because of a **completely separate, unrelated
  project's process** already running heavily in the background (not something this session started or
  could stop). Given this same machine already lost power unexpectedly twice this week under exactly this
  kind of heavy workload, adding another heavy workload on top of an already-warm machine was judged too
  risky to do without checking first. Everything else — that the safety limits are correctly wired into
  both scripts, and that the stricter test logic itself is correct — was proven through the full automated
  test suite instead; only the "real hardware, full-scale, right-now" proof run is outstanding. See the dev
  handoff's Known Issues #1 for the exact recommended next step (re-run once the machine is confirmed back
  to its normal resting temperature).
- The two carry-forward items named explicitly in the plan remain outstanding, as instructed (not this
  iteration's scope to fix): a separate, already-known memory problem on one report-loading page, and two
  outstanding "live walkthrough" recordings that need an owner decision before this project can be
  considered fully finished.
- This developer session's evidence-gathering scope did not include running the browser-based
  verification passes for four other user journeys (the May-backfill journey, the "any date range"
  journey, the "boot up fast and show honest status" journey, and confirming this session's own memory-fix
  journey works when clicked through in a real browser) — those are a separate stage of this project's
  quality-check pipeline that runs after development work like this, not part of what a developer session
  produces directly.

---

## Config and Environment Changes

- `project-extensions/host-guard/host-guard.env` (already existed, not modified this iteration) — its
  values (which CPU cores are safe to use, how many processing threads to allow) are now actually READ and
  applied by both launch scripts; previously this file's values were declared but silently ignored by both
  scripts.
- `HOST_GUARD_ENV_FILE` — a new, test-only environment variable that lets automated tests point at a
  practice copy of the safety-limits file instead of the real one, so tests can safely check "what happens
  if this file is missing" without ever touching the real file. Not used in any normal/real launch — safe
  to ignore for day-to-day use.
- No database schema changes, no new user-facing settings, no new required environment variables for
  normal operation.

---

## Known Limitations

- The real-hardware, full-scale proof run (see "Incomplete Items" above) still needs to be performed and
  its results recorded before this iteration's safety claim can be considered fully evidenced end-to-end —
  everything up to that final real-world check is done and passing.
- An unrelated rough edge was noticed (not caused by this iteration, not fixed here): if someone manually
  starts the "developer" launch script in the background and then tries to stop it with a plain kill
  command, one of its two halves (the web-app-building half) can sometimes keep running and holding its
  port open. The script's own normal startup process already cleans this up automatically the next time it
  runs, so this only matters for someone manually managing background processes outside of how this
  project's own automation runs them.

---

## Addendum — Audit Fix Round (2026-07-22)

The independent audit of this iteration returned a FAIL verdict. It fixed the reporting problems itself
(a summary file that said "PASS" while its own table said "FAIL", and a results file that was silent about
the one journey that failed) and left exactly **one** item for this developer round. That item is now fixed.

### What was wrong

The "big rebuild followed immediately by another big data job" safety-net test named a fixed calendar date
(15 July 2010) for its second job. That date has since been processed and stored in the project's own
database, so the second job would have found nothing left to do — a no-op. The test would then have
reported a failure ("two pieces of follow-up bookkeeping are missing") that had nothing to do with the
memory problem the test exists to catch. In short: the test could no longer pass, and if it had been run it
would have blamed the wrong thing.

### What changed (test code only — no change to the application itself)

- The second job's date is now **chosen while the test runs**, by asking the server that is under test
  which trading days it has data for but has not yet processed. It picks the most recent suitable day, and
  requires enough following calendar left over for the follow-up calculations to be real work.
- The test now explicitly checks that the second job **actually created something**. If it did not, the
  test fails immediately with a plain message saying the scenario went stale — instead of silently
  measuring nothing, or blaming a memory problem that never happened.
- If the database ever genuinely has no unprocessed day left to use, the test now **skips with a stated
  reason** rather than pretending to have proven something.
- The "all follow-up bookkeeping completed" check is now measured against what is actually achievable for
  that job: the full set when the job stored new data, and the subset that does not depend on new data
  otherwise. Because the second job is now guaranteed (and checked) to do real work, it is always held to
  the full standard.

### Incomplete items (unchanged from the main summary above)

- The real-hardware, full-scale proof run is **still deferred** for machine-safety reasons: this computer
  hard-reset twice last week under exactly that workload, and the operator's instruction for this round
  repeated that it must not be started on our own initiative. The fix above is precisely what the audit
  asked to be in place *before* that run happens, so that when it is finally run it cannot report a false
  failure.
- One genuine product defect was discovered by the browser testing lane (not introduced by this iteration):
  when a data job is interrupted by the machine or process dying, the progress it had made is never saved,
  so the job history always shows it as having done nothing. This is recorded as backlog work; it is why
  one of the "must still work" journeys is scored as failing.
- One tooling problem was found in the shared automation (not this project's product code): the script that
  merges browser-test results ignores a verdict cell when it is written in bold, which turned a FAIL into a
  PASS in the summary file. It has been flagged for the framework maintainer; the affected file was
  corrected by the audit.

### Verification performed this round

Targeted automated checks only (no heavy workload, no full suite): the five launch-safety checks pass, the
heavy test correctly stays opt-in/skipped, the edited test file loads cleanly with all nine of its checks
discovered, and the memory-cleanup check passes. The new date-picking logic was exercised end-to-end
against a faithful reconstruction of the real database's availability data: it correctly rejected the stale
hardcoded date, picked a genuinely unprocessed day (30 May 2025, with data for 589 symbols), and skipped
honestly when given a database with nothing left to process.

---

## Addendum 2 — Audit Fix Round 2 (2026-07-22): the deferred proof run was performed, and the interrupted-job defect was fixed

Two items that the previous rounds had to leave open are now closed.

### 1. The real-hardware, full-scale proof run HAPPENED — and passed

Everything up to this point had been proven in miniature; the one thing missing was running the actual
worst-case workload on this actual machine, under the new safety limits, and recording what it did. The
owner authorized that run, and before starting it the machine was confirmed cool and idle (41 °C, the
normal resting range — it had been 74-86 °C when the run was first postponed), with the temperature
logger running and an automatic emergency-stop armed.

**It ran for 18 minutes and passed.** In one server process: a full rebuild of the entire dataset (378
data snapshots, 709,093 follow-up calculations) immediately followed by a second big data job — the exact
pairing that crashed this machine twice last week.

- Memory: peaked at **4.63 GB against the 6.0 GB ceiling** the safety limits impose — it stayed inside its
  budget, with about a quarter of the headroom to spare.
- Responsiveness: the health check was polled 439 times throughout and answered **every single time**,
  with no hangs (median under half a second).
- Hardware: the machine peaked at **81 °C**, 14 °C below the emergency-stop threshold — and 8 °C cooler
  than the same workload ran last week, which is direct evidence that the new CPU limits are doing their
  job. The emergency stop never triggered; nothing reset.
- Both jobs reported a **fully successful** outcome with all follow-up bookkeeping complete — which is
  what the stricter test from the previous round now demands.

The raw measurements are kept alongside the iteration (memory samples, health-check timings, temperature
log, and the test output), and the results were written into the project's performance-budget document as
a new dated section.

**One honest caveat is recorded there rather than buried:** the memory headroom measured this time is
**24.7%**, noticeably less than the 43.6% measured last week. This run cannot say how much of that is a
finer measurement cadence and how much is the dataset having grown ~24% since — so it is written down as
a number to watch as the data grows, not as a comfortably passed budget.

### 2. Interrupted jobs now remember how far they got

Previously, if a data job was killed by a crash, a power loss, or the machine dying, the job history would
always show it as having done **nothing** — "0 snapshots, 0 trading days" — even if it had processed
hundreds of days before dying. The reason was simple: progress was only ever written to the history at the
moment a job *finished*, and a killed job never gets there.

Now the job writes its current progress into its own history record as it goes (at most once every 10
seconds, so it costs effectively nothing), and the boot-time cleanup that marks dead jobs "interrupted"
leaves that progress intact. An interrupted job now shows what it actually accomplished. No screen or
button changed — the Data page already displays these numbers; they were simply always zero before.

Care was taken so this cannot cause new problems: the progress write never marks a job finished, never
creates a duplicate history entry, and if the write itself fails it is logged and ignored rather than
failing the job.

**Still needed to close the loop:** the browser-based check that clicks through this scenario (start a job,
kill the server, restart, look at the history) should be re-run — this change makes the data correct, but
only that browser pass can confirm the journey end-to-end.

### Still outstanding after this round

- The two carry-forward items needing an owner decision are unchanged: the known memory problem on one
  report-loading page, and the two outstanding "live walkthrough" recordings.
- The shared-automation reporting bug (bold verdict cells being ignored when merging browser-test results)
  remains flagged for the framework maintainer — it is not this project's product code.
- A pre-existing, unrelated broken test was discovered while re-running the regression checks: one
  database test lists the expected set of database tables and has not been updated since two new tables
  were added back in iteration 2. It is recorded for triage rather than quietly fixed, because this round's
  rules only permit fixing what the audit listed.
