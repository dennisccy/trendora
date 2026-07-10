# Phase goal-mcp-loop-iter-26 — UI Test Results

**Phase:** goal-mcp-loop-iter-26
**Date:** 2026-07-10
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL: UT-02 (P1, the direct browser-observable proof of J-16) failed with a reproducible backend
     MemoryError crash that took the ENTIRE backend down (including /api/health) for the rest of the
     session. This is a critical regression, not a flaky/UI issue. -->

**Overall:** 1/16 tests passed (14 skipped, 1 failed) — testing was halted after UT-02/UT-03 because the
backend entered a total, non-self-healing outage (see Critical Finding below) that made every
remaining backend-dependent test impossible to execute honestly.

---

## Critical Finding (read this first)

While executing **UT-02** exactly as specified (see steps below), starting a real multi-date job on
`/data` triggered a **`MemoryError` inside `apps/backend/app/engine/prices.py:191`, inside `bars_asof`**
— the exact function this iteration's phase spec (`docs/phases/goal-mcp-loop-iter-26.md`) documents as
changed ("`close_on`/`bars_after` made cache-aware; new `_BarCache.bars_after` method"). The traceback
(captured verbatim in `reports/qa/goal-mcp-loop-iter-26-evidence/UT-02-backend-log-tail.txt`) shows the
same failure repeating identically for many different scanner dates:

```
File ".../app/engine/data_manager.py", line 2302, in _compute_one_backfill_date
    payload = scanner.compute_run_payload(wsession, d, cfg)
File ".../app/engine/scanner.py", line 68, in compute_run_payload
    regime = score_regime(session, asof, cfg)
File ".../app/engine/regime.py", line 100, in score_regime
    index_ma_stack = _index_ma_stack(session, asof, cfg)
File ".../app/engine/regime.py", line 39, in _index_ma_stack
    stack = ind.ma_stack(closes(bars_asof(session, symbol, asof)), cfg.indicators.ma_periods)
File ".../app/engine/prices.py", line 333, in bars_asof
    return cache.bars_asof(session, symbol, d)
File ".../app/engine/prices.py", line 191, in bars_asof
    return full[:cut]
MemoryError
```

Before the crash, the job (a "Rebuild snapshots for current universe" run over 322 dates × 541
members — see UT-02 below for why this path was used) also logged 20+ `sqlite3.OperationalError: disk
I/O error` failures for unrelated historical dates (2007, 2008, 2009, 2011…), consistent with the
process being under severe memory/resource pressure before the fatal `MemoryError`.

**After the crash, the backend became completely unresponsive for the remainder of the session:**
- `GET /api/data`, `GET /api/stocks`, `GET /api/evidence`, `GET /api/data/jobs/{id}` all returned
  **HTTP 500** repeatedly.
- `GET /api/health` returned 200 for a short window immediately after the crash, then also started
  returning **HTTP 500** — i.e. the health endpoint gave a **false-positive "OK"** for a period while
  the actual data path was already dead, then failed itself. This is the exact false-positive risk
  called out in the phase's own "iter-24 lesson" notes, reproduced in a new form.
- The backend process (PID 499553) stayed alive but **stopped doing any work**: `/proc/<pid>/stat`
  `utime`/`stime` were byte-identical across repeated polls 20+ seconds apart, and RSS was frozen at
  ~4,932 MB (`5050584` KB) — the process did not crash/exit and was not auto-restarted (it never
  "died" in the process sense, so no supervisor auto-restart fires).
- **Peak RSS never reached the 6144 MB `server.memory_cap_mb` cap** (~4.93 GB observed, comfortably
  under 6144 MB) — but **VSZ (virtual address space) was pinned at exactly 6,291,456 KB = 6144 MB**,
  i.e. the process hit the `ulimit -v` ceiling that `scripts/start-backend.sh` sets from the same
  `memory_cap_mb` config value. The `MemoryError` is consistent with a virtual-address-space
  exhaustion (the `ulimit -v` hard cap), which is a **different signal than peak RSS** and would not be
  caught by an RSS-only perf-budget check.
- I attempted to restart the backend (stop → cold-start via `scripts/start-backend.sh`, exactly as
  UT-04 specifies) to continue testing, but the sandbox permission system **denied sending
  SIGTERM/SIGKILL to PID 499553** ("a process it did not create this session (started by the
  harness)"). I did not attempt to work around this. The backend was confirmed still fully down
  (HTTP 500 on `/api/health` and `/api/data`) at the last check before writing this report — **someone
  with permission to manage the harness-owned backend process needs to restart it** before any further
  testing (browser or otherwise) can proceed.

This single reproducible crash is why only UT-01/UT-02/UT-03 were actually exercised; UT-04 through
UT-16 could not be honestly executed against a live backend and are recorded as SKIPPED below, each
tracing back to this one root cause.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/data` loads without errors | smoke | P1 | Heading + coverage/storage panels render with real numbers, no error card | Page loaded cleanly: "Data Manager" heading, Dataset coverage (Price history 1996-01-02→2026-07-01, Universe 541, Candidate universe 122, Symbols 590, Trading days 5369, Snapshot dates 412, Backfill gaps 4959) and Storage footprint (1.22 GB, 3,293,160 price bars, 166,213 scanner rows, 823,409 forward returns) both populated. No error card. | PASS | `reports/qa/goal-mcp-loop-iter-26-evidence/UT-01-result.png` |
| UT-02 | Backfill progress ticks honestly (J-16 target) | happy-path | P1 | `done` climbs incrementally across ticks; badge never says done while counter < total; badge/counter agree at completion | Pre-filled Backfill range (2005-02-28→2005-03-07) was a genuine 0/0 no-op, so the sanctioned fallback (Rebuild snapshots for current universe, 322 dates) was used per test-plan step 2b. Counter DID tick incrementally while observable (0→117→246 of 322, confirmed via `GET /api/data/jobs/{id}`) — no jump-to-done was seen. But partway through, the backend crashed with a `MemoryError` inside the iteration-changed `prices.py:bars_asof` and the ENTIRE backend went down (500s on all data endpoints, including eventually `/api/health`); the Job progress panel became permanently inaccessible (`/data` shows "Backend unavailable") before the job could reach a clean, verifiable completed state. | FAIL | `reports/qa/goal-mcp-loop-iter-26-evidence/UT-02-fail-backend-unavailable.png`, `.md`, `reports/qa/goal-mcp-loop-iter-26-evidence/UT-02-backend-log-tail.txt` |
| UT-03 | Stage timings show measured speedup | happy-path | P1 | Elapsed/Dates/Concurrency + speedup-factor line render after a completed job | Not observable — the same backend crash from UT-02 hit before the job reached a stable completed state, and `/data` (and the job-status API) has returned 500/"Backend unavailable" ever since. | FAIL | (blocked by UT-02 crash; same evidence) |
| UT-04 | Cold-start `/data` survives, no OOM | regression | P1 | `/data` renders cleanly as first request after 2 cold backend restarts, no crash | Could not execute: attempted the exact prescribed restart procedure (stop backend → `start-backend.sh` cold start) to both recover the service and run this test, but the sandbox denied permission to signal the harness-owned backend process (PID 499553, "not created this session"). Backend remained down (500 on `/api/health` and `/api/data`) at last check. | SKIPPED | reason: cannot stop/restart the harness-managed backend process (permission denied); backend is down following the UT-02 crash |
| UT-05 | Storage footprint values well-formed | regression | P2 | Four well-formed values, stable across refresh | Not executed — backend down | SKIPPED | reason: backend unresponsive (see Critical Finding) |
| UT-06 | Availability heatmap + legend unchanged | regression | P2 | Legend groups + hover readout render | Not executed — backend down | SKIPPED | reason: backend unresponsive |
| UT-07 | Job form rejects malformed dates | validation | P2 | Inline error + disabled Start button | Not executed — backend down (form itself may render, but this test's own precondition "no job is currently running" and a meaningful validation check both depend on a live backend) | SKIPPED | reason: backend unresponsive |
| UT-08 | Second job start blocked while running | error | P2 | "Job running…" disabled button | Not executed — backend down | SKIPPED | reason: backend unresponsive |
| UT-09 | Leaderboard scores byte-identical (sample) | regression | P1 | Leaderboard renders with real scores | `/stocks` shows "Checking backend…", "No regime for this date", "No ranked themes for this date" — leaderboard data did not load | SKIPPED | reason: backend unresponsive (confirmed on `/stocks` directly, see below) |
| UT-10 | Evidence badges still "Not yet proven" | regression | P1 | Badges present with correct text | Not executed — depends on UT-09's leaderboard, which did not load | SKIPPED | reason: backend unresponsive |
| UT-11 | Ticker detail scores match leaderboard | regression | P1 | Detail page matches leaderboard | Not executed — no leaderboard row to click through from | SKIPPED | reason: backend unresponsive |
| UT-12 | Dashboard regime card unchanged | regression | P1 | Regime card + phase card render | Not executed — `/` dashboard depends on the same backend | SKIPPED | reason: backend unresponsive |
| UT-13 | Evidence ledger all-FAIL unchanged | regression | P1 | Ledger renders, all-FAIL, no crash | Not executed — backend down | SKIPPED | reason: backend unresponsive |
| UT-14 | Deep-history chart still full-range | regression | P2 | Full-range chart renders | Not executed — no ticker detail page reachable | SKIPPED | reason: backend unresponsive |
| UT-15 | Universe/membership counts unchanged | regression | P2 | Counts + timeline render | Not executed — backend down | SKIPPED | reason: backend unresponsive |
| UT-16 | Data Manager discoverable, labels unchanged | ux | P3 | Nav + panel titles unchanged | Not executed (nav itself was visually confirmed present and correctly labeled in UT-01/UT-02 screenshots, but the full 1-click-navigation + panel-title check requires the page to actually load, which it no longer does) | SKIPPED | reason: backend unresponsive |

---

## Passed Tests

### UT-01 — `/data` page loads without errors (smoke)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-26-evidence/UT-01-result.png`
- Navigated to `http://localhost:3255/data` before any job was started (clean baseline state).
- Heading "Data Manager" visible.
- Dataset coverage panel populated: Price history 1996-01-02 → 2026-07-01, Universe (as of date) 541,
  Candidate universe 122, Symbols 590, Trading days 5369, Snapshot dates 412, Backfill gaps 4959.
- Storage footprint panel populated: Database file 1.22 GB, Price bars 3,293,160, Scanner rows
  166,213, Forward returns 823,409.
- No "Backend unavailable" error card, no blank page.

---

## Failed Tests

### UT-02 — Backfill job progress ticks honestly, never jumps to "done" early (happy-path, J-16 target)
**Verdict:** FAIL
**Failure:** Backend crashed with a `MemoryError` in the iteration-changed `prices.py:bars_asof` mid-job,
taking the entire backend down for the rest of the session (500s on every data endpoint, eventually
including `/api/health`). The Job progress panel became permanently inaccessible before a clean,
verifiable "done" state could be observed, so the test's own final acceptance bullets ("badge reads ok
and counter reads total/total, matching each other exactly") could never be checked.
**Evidence:** `reports/qa/goal-mcp-loop-iter-26-evidence/UT-02-fail-backend-unavailable.png`,
`reports/qa/goal-mcp-loop-iter-26-evidence/UT-02-fail-backend-unavailable.md`,
`reports/qa/goal-mcp-loop-iter-26-evidence/UT-02-backend-log-tail.txt`

**Steps taken:**
1. Navigated to `/data`. "Backfill gaps" showed 4959 (> 0), so per step 2 I left "Job kind" at
   "Backfill snapshots" with the auto-pre-filled range (Start 2005-02-28, End 2005-03-07) and clicked
   "Start".
2. That job completed almost instantly (145ms) as a genuine **0/0-dates no-op** (`backfill: 0 snapshots
   over 0 dates, 0 forward returns`, badge "ok") — an allowed outcome per the test's own expected-result
   clause, but it gave no ticks to observe, so per the test plan's explicit guidance for this situation
   I used the sanctioned alternate path (step 2b): clicked "Rebuild snapshots for current universe",
   confirmed the "Confirm snapshot rebuild" dialog.
3. This started a real 322-date rebuild job. Polling `GET /api/data/jobs/{id}` confirmed the "Snapshots
   backfilled" counter ticking honestly and incrementally: `0/322` → `117/322` → `246/322` across
   multiple observed polls (no jump from a low number straight to done) — this part matched the
   expected behavior.
4. Starting around date 117-246, the backend log began recording `sqlite3.OperationalError: disk I/O
   error` for individual, historically-unrelated dates (2007-10-01, 2008-05-01, 2009-06-01, 2011-07-01,
   2011-08-01, 2011-09-01, …) — 20+ such failures accumulated in the job's `date_failures` list.
5. The job status transitioned to `"partial"` while `dates_done` (246) was still below `dates_total`
   (322) — before I could confirm from the browser whether the frontend badge itself ever displayed a
   completed-looking state prematurely, the backend crashed.
6. The backend log recorded a `MemoryError` with the deepest application frame at
   `apps/backend/app/engine/prices.py:191`, inside `bars_asof` — reached via
   `data_manager._compute_one_backfill_date` → `scanner.compute_run_payload` → `regime.score_regime` →
   `regime._index_ma_stack` → `prices.bars_asof`. This exact traceback repeated identically many times.
7. From that point on, `GET /api/data`, `GET /api/stocks`, `GET /api/evidence`, and
   `GET /api/data/jobs/{id}` all returned HTTP 500. `GET /api/health` returned 200 for a short window
   (a false-positive "backend is fine" signal) then also began returning 500.
8. The `/data` page itself showed the header badge "Checking backend…" indefinitely, and on one reload
   explicitly rendered the red "Backend unavailable — Dataset coverage could not load from the API. No
   figures are shown rather than fabricated values." card — i.e. the honest-degradation UI worked
   correctly, but the underlying panel this test needed to observe was gone.
9. Backend process (PID 499553) remained alive (not OOM-killed/exited) but frozen: `/proc/<pid>/stat`
   `utime`/`stime` were unchanged across repeated ~10-20s polls, RSS stayed pinned at ~4.93 GB (under
   the 6144 MB cap), VSZ stayed pinned at exactly 6144 MB (the `ulimit -v` ceiling).
10. Attempted to recover by restarting the backend (the same procedure UT-04 itself prescribes) — the
    sandbox permission system denied signaling PID 499553 as "a process it did not create this
    session." I did not attempt a workaround. Backend was still down at last check.

**Expected:** `done` climbs incrementally, badge never claims completion while counter < total, and at
completion badge + counter agree exactly; non-zero snapshots/forward-returns unless a genuine no-op.
**Actual:** Counter did climb incrementally while the backend was alive (positive partial evidence) —
but the backend then crashed with a `MemoryError` in the exact code path this iteration modified,
before reaching any verifiable completed state, and stayed down for the rest of the session.

---

## Skipped Tests

### UT-03 — Stage timings panel shows the measured speedup (happy-path / visible regression-budget proof)
**Verdict:** SKIPPED (reported as FAIL above since it directly depends on the crashed UT-02 job and is P1)
**Reason:** The job that UT-03 needs to inspect never reached a stable, viewable completed state before
the backend crash documented in UT-02; `/data` and the job-status API have returned errors ever since.

### UT-04 — Cold-start `/data` load survives without crash or OOM (regression, iter-24 lesson)
**Verdict:** SKIPPED
**Reason:** This test's own procedure (stop backend → cold-start via `start-backend.sh` → load `/data`
as first request, twice) is exactly what I attempted in order to both recover the service and execute
this test honestly. The sandbox denied permission to send SIGTERM/SIGKILL to the backend process (PID
499553) because I did not start it this session and no user direction named that specific action. I did
not attempt to bypass this. The backend was confirmed still down (HTTP 500 on `/api/health` and
`/api/data`) at the time this report was written.

### UT-05 — Storage footprint card values are consistent and well-formed (regression)
**Verdict:** SKIPPED
**Reason:** Backend unresponsive (500 on `/api/data`) since the UT-02 crash; the panel cannot render.

### UT-06 — Per-date availability heatmap and legend are unchanged (regression)
**Verdict:** SKIPPED
**Reason:** Backend unresponsive since the UT-02 crash; the panel cannot render.

### UT-07 — Job start form still validates malformed dates (validation)
**Verdict:** SKIPPED
**Reason:** Backend unresponsive since the UT-02 crash; cannot confirm the required precondition ("no
job is currently running") or exercise the form meaningfully against a live backend.

### UT-08 — Starting a job while one is already running is blocked with a clear message (error)
**Verdict:** SKIPPED
**Reason:** Backend unresponsive since the UT-02 crash.

### UT-09 — `/stocks` leaderboard loads and scores match pre-iteration values (smoke + regression, byte-identity gated)
**Verdict:** SKIPPED
**Reason:** Navigated to `/stocks` directly to check: page shows "Checking backend…", "No regime for
this date", and "No ranked themes for this date" — the leaderboard did not load. Backend unresponsive
since the UT-02 crash.

### UT-10 — Evidence badges on `/stocks` still read "Not yet proven" for every score (regression, J-01 / J-03)
**Verdict:** SKIPPED
**Reason:** Depends on UT-09's leaderboard rows, which did not load.

### UT-11 — `/stocks/[ticker]` detail page scores match the leaderboard row exactly (regression)
**Verdict:** SKIPPED
**Reason:** No leaderboard row available to navigate from; backend unresponsive.

### UT-12 — Dashboard Market Regime card renders unchanged (regression, J-04)
**Verdict:** SKIPPED
**Reason:** Backend unresponsive since the UT-02 crash; `/` depends on the same failed data endpoints.

### UT-13 — `/evidence` ledger renders unchanged (all-FAIL / no-certified-claims state) (regression, J-05)
**Verdict:** SKIPPED
**Reason:** Backend unresponsive since the UT-02 crash (`GET /api/evidence` confirmed returning 500).

### UT-14 — Deep-history chart on ticker detail still renders full range (regression, J-10)
**Verdict:** SKIPPED
**Reason:** No ticker detail page reachable; backend unresponsive.

### UT-15 — `/data` universe and membership-timeline counts render unchanged (regression, J-12)
**Verdict:** SKIPPED
**Reason:** Backend unresponsive since the UT-02 crash.

### UT-16 — Data Manager remains discoverable within 2 clicks; panel labels unchanged (ux)
**Verdict:** SKIPPED
**Reason:** Nav sidebar itself was visually present and correctly labeled throughout (visible in the
UT-01 and UT-02 screenshots), but the full check requires `/data` to actually render its panels, which
it no longer does following the backend crash.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (down at time of report — see Critical Finding)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-10
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-26-evidence/`
- **Backend process:** PID 499553, started 2026-07-10 12:09 (prod mode, `uvicorn main:app --port 8255`).
  Degraded from HTTP 500 on all data endpoints to full connection timeout (`curl` exit "000", no
  response at all) on `/api/health` and `/api/data` by the final check immediately before this report
  was written — the outage worsened over the ~30 minutes since the crash rather than self-healing.
  **Requires a restart by someone with permission to manage the harness-owned process before further
  browser QA can proceed.**
