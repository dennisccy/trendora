# Phase goal-ops-hardening-iter-44 — UI Test Results

**Phase:** goal-ops-hardening-iter-44
**Date:** 2026-08-03
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- Both P1 target-journey tests (UT-J-05, UT-J-07) failed against a live-reproduced availability
incident that occurred during this run. Per verdict rules, any P1 failure -> FAIL. -->

**Overall:** 0/2 tests passed (0 skipped) — this run's scope per the dispatch is EXACTLY UT-J-05 and
UT-J-07 (the two target journeys). Deterministic replay already re-verified J-01/J-03/J-04/J-06/J-08/J-09
from stored golden scripts before this run started (evidence timestamped ~19:48-19:49 UTC in
`reports/qa/goal-ops-hardening-iter-44-evidence/J-0{1,3,4,6,8,9}-verify.png`); those rows merge in
separately and are not re-emitted here per the dispatch instruction.

---

## Headline finding (read before the per-test detail)

While executing UT-J-05's own mandated trigger (a real backfill on a confirmed-unsnapshotted date), the
backend became **completely unresponsive to every request — including `GET /api/health` — for at least
21 minutes 26 seconds** (20:10:11 UTC last confirmed-good poll → 20:31:37 UTC when this tester sent
`SIGKILL` because a prior graceful `SIGTERM` did not cause the process to exit within its own configured
120s `graceful_timeout_seconds`). This is worse than the exact failure mode iter-44's own dev handoff and
`reports/perf-budgets.md` disclosed as "diagnosed but not fixed" (TC-4) and worse than iter-43's original
incident (which needed `kill -9` after "several minutes"). Full timeline and evidence below.

Context: a background compute (`asof_key: 2026-07-30`) was **already active and stalled at
`horizons_done: 0/5`** when this test session began (started 19:49:20 UTC, before this tester did
anything) — a pre-existing condition, not something this tester triggered. This tester's own single,
test-plan-mandated backfill trigger (2019-02-26) was added on top of that pre-existing stall, and the
combination produced the total outage described below. This is a realistic condition (a new job started
while a previous one's finalize tail is still running), not a contrived stress test, and it sits squarely
inside AG-8/AG-10's resilience scope.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-05 | Aggregates precomputed at ingest, never on the fly (target) | regression | P1 | A backfill on a confirmed-unsnapshotted date (2019-02-26) creates a snapshot quickly (fast scan stage), badge stays Ready throughout, `/scanner-runs` shows the new date with a leaderboard | Job entered `running`, `dates_done` stayed `0/1` for the entire ~10 min it was live, then the job record shows `status: failed`, `snapshots_created: 0`, message unchanged generic text ("backfill: 0 snapshots over 1 dates, 0 forward returns"); no `/scanner-runs` row for 2019-02-26 was ever created; badge went from Ready to stuck on "Checking backend…" during the concurrent outage | FAIL | `reports/qa/goal-ops-hardening-iter-44-evidence/UT-J-05-job-failed.png`, `UT-J-07-outage-checking-backend.png`, `UT-J-05-J-07-job-and-outage-timeline.csv` |
| UT-J-07 | Heavy aggregate warm never takes health/`/backtest` down (target) | regression | P1 | Steps 1-3 anchors render; `GET /api/health` returns 200 throughout the warm (rescoped ≤2s budget); badge stays `ready`; `/backtest` renders promptly (normal or "Refreshing" banner), never blank/frozen | Steps 1-3 anchors rendered (with the caveat that the two golden numeric anchors "n=8878"/"3508" have drifted with dataset growth — see Notes). During the warm: 84/84 clean baseline polls were 200 (max 1.756s) BEFORE the incident, then the backend went **fully unresponsive for 21m26s** — `GET /api/health` timed out on 51 consecutive independent polls (5s timeout each) plus this tester's own direct `curl` calls (one hung >120s); badge stuck on "Checking backend…"/loading; the process required a manual `SIGKILL` after `SIGTERM` failed to exit it within its configured 120s graceful window | FAIL | `reports/qa/goal-ops-hardening-iter-44-evidence/UT-J-07-outage-checking-backend.png`, `UT-J-05-job-failed.png`, `UT-J-07-health-poll-baseline.csv`, `UT-J-05-J-07-job-and-outage-timeline.csv` |

---

## Failed Tests

### UT-J-05 — Aggregates are precomputed at ingest, never on the fly (target journey)

**Verdict:** FAIL
**Evidence:** `reports/qa/goal-ops-hardening-iter-44-evidence/UT-J-05-job-failed.png` (post-recovery Run
History row for the job), `UT-J-07-outage-checking-backend.png` (browser-captured loading-skeleton state
during the incident), `UT-J-05-J-07-job-and-outage-timeline.csv` (raw poll timeline)

**Preconditions confirmed:** `2019-02-26` was checked against `GET /api/runs` immediately before starting
and confirmed absent (2005-04-12, 2019-02-27, 2019-02-28 were already present in this session's DB —
2019-02-26 and 2019-02-25 were the two confirmed-absent trading days found; 2019-02-26 was used).

**Steps taken:**
1. Navigated to `http://localhost:3255/data` — confirmed "Data Manager" heading. (`019-navigate.png`
   equivalent state, healthy at this point.)
2. Set Start date and End date to `2019-02-26` (via a JS native-setter fill after this tester's Chrome MCP
   `type` action was found to append rather than replace pre-filled default values — a tool-side quirk of
   this session's Chrome MCP, not a product bug; confirmed both fields read exactly `2019-02-26` before
   submit).
3. Clicked "Start". `data-testid="job-status"` immediately read `running`. Confirmed via
   `GET /api/data` that run id 272 was created: `start=end=2019-02-26`, `status=running`,
   `started_at=2026-08-03T20:01:36`.
4. Watched the readiness badge — read `ready`/"Ready" at multiple checks in the first ~8 minutes.
5. Polled run 272's status repeatedly. **`dates_done` stayed `0/1` and `snapshots_created` stayed `0` for
   the entire time the job was observably alive** (over 9 minutes) — this contradicts this iteration's own
   dev handoff claim that the scan/snapshot stage "completes within the create-once scan stage, unaffected
   by the disclosed finalize-tail slowness." In this run it never got there before the surrounding outage
   (see UT-J-07 below) engulfed it.
6. After recovery (this tester's forced restart, detailed under UT-J-07), re-checked run 272:
   `status: failed`, `finished_at: 2026-08-03T20:11:29` (i.e. it had already flipped to failed ~11 minutes
   after starting, well before this tester's restart at 20:31), `snapshots_created: 0`, `dates_done: 0`,
   message unchanged from the pre-failure generic text: `"backfill: 0 snapshots over 1 dates, 0 forward
   returns"` — no real captured-exception text is visible in this message (relevant context for TC-10,
   though this tester makes no claim about which code path produced this specific failure — recorded as an
   observation, not a diagnosis).
7. Confirmed via `GET /api/runs` that **no row for `2019-02-26` exists** — the scanner-run page
   (`/scanner-runs/<id>`) was never reachable for this date because no run/snapshot was ever created.
8. Post-restart, navigated to `/data` cold: page loaded fully populated (badge Ready, Dataset coverage
   panel populated, Run History table populated including the failed row above) — screenshot
   `UT-J-05-job-failed.png`. Tailed `logs/backend.log` around the restart/cold-load window (line 170793
   onward): no full-table/3.3M-row bar-prefill signature present — this part of the step held.

**Expected:** the backfill completes its fast scan/snapshot stage promptly, `/scanner-runs` shows the new
date with a populated leaderboard well under a minute, and the badge never leaves `ready` during the
process.
**Actual:** the job never produced a snapshot at all; it ended `failed`; `/scanner-runs` has no entry for
the date; the badge left `ready` (stuck on "Checking backend…") for over 20 minutes as part of the same
incident documented under UT-J-07.

---

### UT-J-07 — Heavy aggregates never take the service down (target journey)

**Verdict:** FAIL
**Evidence:** `reports/qa/goal-ops-hardening-iter-44-evidence/UT-J-07-outage-checking-backend.png`,
`UT-J-07-health-poll-baseline.csv` (pre-incident clean baseline), `UT-J-05-J-07-job-and-outage-timeline.csv`
(incident timeline)

**Steps taken:**
1. `http://localhost:3255/` — confirmed text "Ready" present. PASS for this anchor.
2. `http://localhost:3255/backtest` — page rendered fully (evidence tables, scorecard, etc.) but the
   literal golden anchor text `"n=8878"` was **not found** anywhere on the page. This appears to be
   ordinary data drift (bucket sample sizes now read `n=8991`/`n=49627`/etc. — larger than whatever
   iteration the golden script's "8878" figure was captured against), not a rendering failure — the page
   was fully healthy and showing a "Refreshing — showing the last complete evidence" banner (expected
   behavior, evidence for a stale-vs-fresh dataset version, already correctly served even before this
   tester triggered anything).
3. `http://localhost:3255/data` — page rendered fully (Data Manager heading, Dataset coverage panel with
   real populated numbers: Universe 539, Candidate universe 122, Symbols 591, Trading days 5390, Snapshot
   dates 2862, Backfill gaps 2533) but the literal golden anchor `"3508"` was **not found** — the same kind
   of drift as above (2533 "backfill gaps" today vs. presumably 3508 when the golden script was recorded;
   gaps monotonically shrink as more iterations backfill more days). Recorded as a stale-anchor data-drift
   observation, not a functional failure — the underlying panel is genuinely populated and correct-looking.
4. Triggered a heavy warm via UT-J-05's own mandated single-day backfill (2019-02-26, run id 272,
   started 20:01:36 UTC) — per this iteration's own dev handoff, ANY ingest that bumps `dataset_version`
   forces the full O(dates × pool) `_excluded_counts_by_date` recompute over the whole 2,862-row scanner-run
   history regardless of the new range's size, so this single trigger is a valid heavy-warm trigger for
   this journey too (this tester deliberately avoided ALSO re-triggering UT-J-03's wide multi-month range
   concurrently, to avoid needlessly stacking two heavy triggers on top of the already-active stalled
   background compute — a judgment call in the interest of the host resource ceiling, AG-10).
5. Polled `GET /api/health` at ~5s intervals starting immediately after the trigger:
   - **20:02:15 → 20:09:48 UTC (84 polls, ~7.5 min): 84/84 HTTP 200, 0 non-200, max latency 1.756s, 0%
     over the rescoped ≤2s budget** — a clean baseline, consistent with (slightly better than) this
     iteration's dev-reported clean re-measurement.
   - A second, independent monitor (separate Python process, 20s interval, polling both `/api/data` and
     `/api/health`) recorded the **last fully successful poll at 20:10:11 UTC** (health `ok`,
     background-compute `horizons_done: 1`), then **51 consecutive `timed out` results** (5s timeout each)
     from **20:10:33 UTC through 20:31:24 UTC** — i.e. every single poll for **20 minutes 51 seconds**
     failed to get any response at all.
   - This tester's own direct `curl --max-time 4 http://localhost:8255/api/health` during this window
     returned `http_code=000` after the full 4s timeout (exit code 28); an earlier, unbounded `curl` check
     of frontend+backend ran past its 120s tool timeout without completing at all.
6. Badge check during the incident: navigating to `/data` produced a page stuck mid-load — badge read
   `data-state="loading"` / text `"Checking backend…"`, with the Dataset coverage / Run history panels
   rendered as empty loading-skeleton placeholders (screenshot `UT-J-07-outage-checking-backend.png`) —
   this is the badge/page genuinely reflecting the outage (an honest "checking" state, not a blank crash
   page), but it did NOT stay at `data-state="ready"` as J-07's acceptance requires; it left `ready` for the
   full duration of the incident.
7. `/backtest` in a "second tab": this tester's Chrome MCP tool hit repeated
   `Page session timeout: Page.captureScreenshot` errors on a genuinely separate tab loading `/backtest`
   around the same time the outage began (tab was closed and the check re-run via direct navigation in the
   primary tab instead, which succeeded once, showing `Refreshing` banner + `Ready` badge, at roughly
   20:08-20:09 UTC — i.e. just before the confirmed 20:10:11/20:10:33 outage boundary). This tester did not
   get a second, distinct confirmation of `/backtest`'s specific behavior DURING the deepest part of the
   20:10-20:31 outage window (attention was on `/api/health` and `/data`); given `/api/health` itself was
   fully unresponsive for the whole window on the same event loop, it is a reasonable but not directly
   observed inference that `/api/backtest` would have been equally unreachable — recorded as inference, not
   fact, per the "don't speculate" rule.
8. Investigated whether the process was deadlocked vs. merely slow: `/proc/<pid>/status` showed **all 19
   threads in state `S` (sleeping)** at 20:31:12 UTC (4m59s after this tester's `SIGTERM`, past its
   configured 120s `graceful_timeout_seconds`) — no thread was `R` (running/CPU-bound) at the sampled
   instant, and cumulative CPU time (`/proc/<pid>/stat` utime+stime) was not visibly advancing across
   repeated checks, consistent with a genuine stuck-lock condition rather than active computation. The
   backend's own log (`logs/backend.log`) had **stopped producing any new lines at all since 20:13:56
   UTC** (last line: a caught `MemoryError` inside `evidence.py`'s per-claim drawdown-expectations compute,
   a different, third concurrent code path from the two the dev's own diagnostic named) — i.e. even
   internal logging activity ceased, not just HTTP serving.
9. **This tester sent `SIGTERM` at 20:26:13 UTC** (a full graceful-shutdown attempt, the same signal
   `scripts/start-backend.sh`'s new `--timeout-graceful-shutdown 120` wiring is supposed to honor). The
   process **did not exit within its configured 120s window** (still alive, all-threads-sleeping, at
   20:31:12 — 4m59s later). This tester then **escalated to `SIGKILL` at 20:31:37 UTC**, per this exact
   test step's own sanctioned recovery action (J-05 step 10 explicitly calls for a `scripts/start-backend.sh`
   restart) and to restore the shared backend for the rest of this pipeline run. This directly contradicts
   this iteration's own TC-2 Definition-of-Done promise ("self-terminates within its configured
   graceful-shutdown window, **without requiring a manual `kill -9`**") — TC-2 held in the dev's own
   simpler single-stuck-background-task test, but did not hold here under this run's specific
   multiple-concurrent-heavy-compute condition.
10. Restarted via `bash scripts/start-backend.sh` (same `CHAIN_BACKEND_PORT=8255` /
    `CHAIN_FRONTEND_PORT=3255` / `CORS_ORIGINS` the original process used, captured from
    `/proc/<pid>/environ` before killing it). **Backend responded to `GET /api/health` within 0.4s of the
    new process starting** (20:31:56 UTC, ~19s port-turnaround including OS/venv startup) and reached
    `readiness: ready` shortly after — this part matches J-04's non-blocking-boot contract well. Confirmed
    via the browser: badge back to `Ready`, `/data` fully populated, both the pre-existing stalled
    background-compute entry and job 272 are gone from `background_compute.active` (expected —
    process-lifetime-only per J-09's own disclosed contract).

**Expected:** `GET /api/health` returns 200 throughout the warm (≤2s rescoped budget, small % over
tolerated per this iteration's own disclosed finding); the badge never leaves `ready`; the port never goes
fully unreachable; if a stuck background task requires shutdown, it exits within its configured graceful
window without a manual `kill -9`.
**Actual:** health held cleanly for the first ~7.5 minutes (84/84 200s), then the backend became **totally
unresponsive to every request for 20m51s** (confirmed by two independent pollers plus this tester's own
direct checks), the badge left `ready` for that whole window, and graceful shutdown did not complete within
its own configured 120s window — a manual `SIGKILL` was required. This is the exact failure mode (full,
extended unreachability + reliance on a hard kill) that TC-7 and TC-2 were written to close, and it
recurred, worse than what this iteration's own perf-budgets.md reported measuring.

---

## Notes on stale golden-script anchors ("n=8878", "3508")

Both `J-07.json`'s `"n=8878"` anchor and this journey's `/data` `"3508"` anchor did not literally appear on
the live pages during this run (steps 2-3 above), even though the underlying pages were fully healthy and
populated with real, plausible numbers at the time each was checked. This reads as ordinary data drift —
this session's dataset has accumulated more scanner runs / more backfilled days across 44 iterations since
those golden figures were captured (e.g. `Backfill gaps` today reads 2533, consistent with a larger
"3508" figure at some earlier point before more days were filled in) — not a functional regression. No
golden replay script update was made for J-05/J-07 this run (see below); this is left as a note for
whoever next refreshes those goldens.

## Golden replay scripts

**Not written for J-05 or J-07 this run** — both journeys are reported FAIL above, and the instruction is
to write a golden only "for every journey you verify PASS." The existing
`runs/goal-session-ops-hardening/journey-scripts/J-05.json` and `J-07.json` are left untouched.

## Skipped Tests

None. Both in-scope test cases (UT-J-05, UT-J-07) were executed to a definitive result.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless, pinned
  profile per skill instructions
- **Test Date:** 2026-08-03 (UTC times cited throughout; local host time is BST, UTC+1)
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-44-evidence/`
- **Backend process observed:** PID 292479 (booted 19:42:01 UTC via `scripts/start-backend.sh`, cmdline
  confirmed carrying `--limit-concurrency 64 --timeout-keep-alive 65 --timeout-graceful-shutdown 120` —
  TC-1's launcher-flag wiring is confirmed live on the actual running process); terminated by this tester
  (`SIGTERM` 20:26:13 UTC, `SIGKILL` 20:31:37 UTC after the graceful window elapsed without exit); replaced
  by a fresh instance (PID confirmed responsive from 20:31:56 UTC onward, still healthy at report time).
- **Backend restart performed by this tester:** yes, once — required both by UT-J-05 step 10's own test
  script and to restore the shared backend for the rest of this pipeline run after the confirmed 20m51s
  total outage. No other debugging/recovery action was taken; no source files were modified.
