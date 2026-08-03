# goal-ops-hardening-iter-44 — Implementation Summary

**Phase:** goal-ops-hardening-iter-44
**Date:** 2026-08-03 (revised after the audit's FAIL verdict — see "What changed in this revision")
**Written by:** developer

---

## Bottom line, first

**The iteration's main goal was not achieved.** It set out to stop a heavy background computation from
taking the whole service unreachable. During this pipeline's own browser testing, on this exact build, the
backend went **completely unresponsive for 20 minutes 51 seconds** and had to be force-killed — a longer
outage than the incident this work was written to prevent.

What *was* achieved is real but narrower: a genuine launcher misconfiguration was closed, two previously
invisible crash-handling defects were found and fixed, error messages became honest, and — for the first
time in seven attempts — the cause of the slow background computation was caught red-handed with live
evidence instead of guessed at.

---

## Features Implemented

- **The backend now actually enforces its own connection and shutdown-timeout settings.** A configuration
  file has declared "max 64 simultaneous connections", "close idle connections after 65 seconds", and
  "allow 120 seconds to shut down cleanly" for a long time — but the startup script never passed any of
  them to the web server. It does now, verified against the real running process rather than the script's
  text. **Important caveat:** this helps only when the process is still responsive. It does not, and
  cannot, rescue the situation described in the Bottom line above (see "Incomplete Items").

- **The cause of the long-running background "hang" is now proven, not suspected.** After new data is
  imported, the backend recomputes a piece of historical bookkeeping — which stock symbols were eligible
  on which day, going back to 1996. That recompute currently starts over **from scratch across the entire
  history** every time *any* new data is added, even a single day's worth: roughly 2,860 dates × 591
  symbols. Two live stack captures about 15 minutes apart pin the exact code responsible. Earlier
  iterations suspected a different culprit; this is the first hard evidence.

- **Two crash-handling defects were found and fixed — both had been silently doing nothing.** When the
  backend runs out of memory, it is supposed to abort that one piece of work, log it, and keep serving.
  Two places broke that promise because their error handling was written for the wrong kind of error, so
  the failure escaped and took down more than it should have. Both are fixed and now covered by a test
  that reproduces real memory exhaustion rather than simulating it.

- **Job failure messages are now honest — including for the failure that actually happens.** When an
  import job fails, its history record now names the real reason instead of a generic "no work performed"
  summary. This was shipped once in a form that **did not work for out-of-memory failures** — the one kind
  this system actually produces — because that error carries no text and the code fell back to the generic
  message anyway. That gap was caught and closed; a failed job now reads e.g. `MemoryError (no message)`
  rather than a misleading summary of work that never happened.

- **The "Retry" button now fails the same honest way as "Start" and "Resume."** If the server cannot launch
  a retry (for example, resource exhaustion), it returns a clear "temporarily unavailable" response instead
  of a bare, unexplained server error.

## Changed Behavior

- **Retry endpoint:** returns "temporarily unavailable" (503) instead of an unlabeled server error (500)
  when the retry worker cannot be launched — matching "Start" and "Resume".
- **Failed-job error messages:** a failed import's history record now shows the actual reason, including
  for out-of-memory failures, instead of a generic placeholder summary.
- **Startup:** the backend process is now launched with connection-limit and timeout settings that were
  previously declared but ignored.

## Backend-Only Items

None. Every change is either a launcher/infrastructure fix (invisible by design, no UI surface) or an
error-message correctness fix that surfaces through the existing Run History / Retry-error UI.

## Incomplete Items

- **NOT DONE — the service still becomes fully unreachable, and this is the phase's headline goal.**
  On this build, the backend stopped answering *every* request for 20m51s. A normal shutdown request was
  ignored for nearly 5 minutes past its 120-second deadline and the process had to be force-killed. The
  logs show the shutdown sequence never even started. **Why the new timeout setting did not help:** that
  setting is enforced by the backend's own internal scheduler, and in this failure the scheduler itself is
  frozen — so nothing inside the process can act on it. **What would actually fix it:** a deadline enforced
  from *outside* the process (a service supervisor, or the launcher script backgrounding the server and
  owning the force-kill escalation). That is a new mechanism and needs to be planned as its own piece of
  work, not slipped in as a settings change.

- **NOT MET — the response-time budget.** During a heavy import, health checks were supposed to answer
  within 2 seconds *every* time. 16 of 240 checks (6.7%) took longer, the slowest at 2.354 seconds. This
  is a large improvement over the previous measurement (70.9% over budget) and the best result this
  project has recorded — but the requirement is "every check", so it is a miss. An earlier version of this
  report and the QA report both presented it as met; that was wrong and is corrected here.

- **The slow background recompute is diagnosed but not sped up.** Fixing it means redesigning how that
  historical bookkeeping is cached so a one-day import doesn't recompute 26 years. That is a real design
  change, not a patch, and it needs its own iteration with a proof that the output is byte-for-byte
  identical. A superficially similar fix was attempted five times in earlier iterations; the most recent
  made things measurably worse and was undone. Recording the evidence for the next iteration was judged
  better than a sixth attempt.

- **A single-day import does not finish its housekeeping within a 10-minute observation window.** The
  user-visible part (the new day appearing) completes in well under a minute; the behind-the-scenes
  bookkeeping was still running when observation ended. This was reported honestly as in-flight, never as
  a success.

## Config/Env Changes

- **No new environment variables and no config-file schema changes.** The launcher script now *reads and
  applies* three configuration values that already existed but were silently ignored:
  `limit_concurrency` (64), `timeout_keep_alive_seconds` (65), `graceful_timeout_seconds` (120).
- Existing host-protection limits (memory cap, CPU/thread caps) are untouched — the new settings are
  additive, never a replacement.

## Known Limitations

- **The service can still go fully unreachable under a heavy import and require a force-kill.** This is
  the top open risk and is unresolved. Operators should expect that recovering from this state currently
  means killing the process manually.
- **The new 64-connection limit introduces a new way for health checks to fail.** Above 64 simultaneous
  connections the server will now deliberately refuse with a "server busy" response rather than answering
  slowly. This is the documented intent of the setting and there is no sign of it happening in practice,
  but it is a behaviour change worth knowing about.
- **The automated shutdown test cannot reproduce the real failure.** It exercises a healthy backend, which
  shuts down in well under a second. It is a useful check that the new settings are wired up; it is not
  evidence that shutdown works when the process is frozen.
- **The QA report for this iteration carries a stale PASS verdict.** It was written before the browser
  testing ran and records browser checks as skipped. The browser lane ran afterwards and returned FAIL.
  Read `reports/phase-goal-ops-hardening-iter-44-ui-test-results.llm.md` alongside it.
- **A latent startup hazard, pre-existing and unchanged:** if the launcher fails to read its configuration,
  it does not report an error and would apply a memory limit of zero. This iteration extended that existing
  pattern rather than introducing it; it was left alone as outside the audit's fix scope.

---

## What changed in this revision

The first version of this report stated that the service "stays reachable even during this slow
computation" and that the backend "always exits within its configured window, cleanly, every time". Both
statements were generalised from two controlled test runs and are contradicted by this pipeline's own
browser testing on the same build. They have been corrected here, along with the response-time budget
(reported as met, actually missed) and the memory-pressure test failure (blamed on a miscalibrated test
threshold, actually two real defects — since fixed, with the threshold confirmed correct as-is).
