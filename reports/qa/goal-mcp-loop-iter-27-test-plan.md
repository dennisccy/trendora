# goal-mcp-loop-iter-27 Functional Test Plan

**Phase:** goal-mcp-loop-iter-27
**Date:** 2026-07-10
**Frontend Present:** yes

## Phase Goal

The full-universe (322-date × 541-member) "Rebuild snapshots" backfill job runs to completion under the `ulimit -v 6291456` cap without exhausting virtual address space, resolving the iter-26 regression and restoring the backend to a stable state.

## Test Cases

### TC-01 — Full-universe rebuild memory footprint under VSZ cap

**Type:** api
**Preconditions:**
- Backend is stopped
- A fresh SQLite database is available at `apps/backend/app.db`
- The system can enforce `ulimit -v 6291456` (6 GB virtual memory hard limit)
- `/proc/self/status` is readable to sample `VmPeak`, `VmSize`, and `VmRSS`

**Steps:**
1. Start a fresh backend instance with `bash scripts/start-backend.sh`
2. Wait up to 180s for the backend to report healthy (check `curl -s http://localhost:8000/health` returns 200)
3. Trigger a full-universe "Rebuild snapshots" backfill job via `POST /api/data/rebuild-all` (or the UI equivalent on `/data`)
4. Poll `/api/data` job-progress every 5s until the job completes or fails
5. During the job run, every 30s sample `/proc/self/status` from the backend process, recording `VmPeak` (KB), `VmSize` (KB), and `VmRSS` (KB) into a local log
6. After job completion (or failure), collect the peak values from the log and stop the backend

**Expected outcome:**
- The job completes in a verified completed state (not "done early", not hung, not crashing)
- Backend process remains alive throughout
- Every API endpoint (especially `/api/health`, `/api/stocks`, `/api/data`) remains 200 after the job
- Sampled `VmSize` (virtual address space) never exceeds 6,291,456 KB (6144 MB)
- Sampled `VmRSS` (resident set) never exceeds 6,291,456 KB (6144 MB)

**Pass criteria:**
- Job completion: status endpoint shows `"status": "completed"` or `"progress": 1.0` (fully advanced, never truncated early)
- Memory gate: `max(VmSize samples) < 6291456` AND `max(VmRSS samples) < 6291456` over the entire rebuild
- Both values are recorded in `reports/perf-budgets.md` as a dated "iter-27" section, matching the format of prior perf entries
- Backend survives: no `MemoryError` in logs, all endpoints 200 post-job

---

### TC-02 — Cold-path /api/data no-OOM repro (iter-24 lesson)

**Type:** api
**Preconditions:**
- Backend is stopped
- Database is reset to a clean state
- The backend can be started fresh

**Steps:**
1. Restart the backend with `bash scripts/start-backend.sh`
2. Wait up to 180s for the backend to reach healthy (non-HTTP `/proc/net/tcp` check: port 8000 is listening)
3. Make the FIRST HTTP request to `GET /api/data` (no prior warm requests)
4. Assert the response is 200 with a populated job-progress body (not an error, not an empty response)
5. Make a second request to `GET /api/stocks` and assert 200 with populated data
6. Make a third request to `GET /api/health` and assert 200
7. Stop the backend, wait 5s, and repeat steps 1–6 a second time (verify cold start works consistently)

**Expected outcome:**
- Both cold starts complete without `MemoryError`
- `/api/data` serves populated data as the FIRST request (before any warmup)
- `/api/stocks` and `/api/health` remain reachable and 200 after cold `/api/data`
- No "Backend unavailable" error card or blank application-error page

**Pass criteria:**
- First cold start: `/api/data` response code = 200, response body contains job-progress fields (status, progress, timestamp, or similar)
- First cold start: subsequent `/api/stocks` and `/api/health` both 200
- Second cold start: same as first (repeatability gate)
- Logs show no `MemoryError`, no OOM killer event

---

### TC-03 — Byte-identity: test_scoring_window.py passes (existing windowed vs. unwindowed)

**Type:** artifact
**Preconditions:**
- Backend code is built with the memory-fix implementation
- `apps/backend/tests/test_scoring_window.py` exists and contains the existing byte-identity harness
- Pytest and the backend test environment are available

**Steps:**
1. Run `cd /home/dennis-chan/Git/trendora/apps/backend && .venv/bin/python -m pytest tests/test_scoring_window.py -v`
2. Capture stdout and stderr
3. Assert the exit code is 0 (all tests pass)

**Expected outcome:**
- All existing test cases in `test_scoring_window.py` pass
- No test is skipped
- The harness verifies that windowed and unwindowed code paths produce byte-identical per-(symbol,date) snapshots

**Pass criteria:**
- Exit code = 0
- Output includes "passed" count > 0 and "failed" = 0
- Test names include assertions on `score_stocks` / `score_regime` output (verifying the byte-identity gate)

---

### TC-04 — Byte-identity: bars_asof_window equivalence for both cache and default paths

**Type:** artifact
**Preconditions:**
- Backend code is built with the new `bars_asof_window` accessor in `prices.py`
- Unit tests exist that compare windowed and full-path bar accessor output
- Pytest environment is available

**Steps:**
1. Run `cd /home/dennis-chan/Git/trendora/apps/backend && .venv/bin/python -m pytest tests/test_bar_cache.py -v -k "bars_asof_window or equivalence"`
2. Capture stdout and stderr
3. Assert the exit code is 0

**Expected outcome:**
- Tests verify that `bars_asof_window(session, symbol, d, lookback)` returns the same rows as `bars_asof(session, symbol, d)[-lookback:]`
- Tests cover both the cache-active path and the default (no-context) path
- Tests cover long-history symbols (e.g., AAPL) and short-history symbols (e.g., ARM)

**Pass criteria:**
- Exit code = 0
- At least 4 test cases pass (2 paths × 2 history lengths minimum)
- No assertion failure comparing windowed vs. full-slice output

---

### TC-05 — Byte-identity: test_forward_testing.py cache-awareness (existing, must stay green)

**Type:** artifact
**Preconditions:**
- Backend code is built
- `apps/backend/tests/test_forward_testing.py` exists
- Pytest environment is available

**Steps:**
1. Run `cd /home/dennis-chan/Git/trendora/apps/backend && .venv/bin/python -m pytest tests/test_forward_testing.py -v -k "cache"`
2. Capture stdout and stderr
3. Assert the exit code is 0

**Expected outcome:**
- Existing cache-awareness test cases (testing `close_on`/`bars_after` against both cache and default paths) still pass
- These tests are unchanged by the iter-27 memory fix and must remain green to verify no regression in the cache dispatch logic

**Pass criteria:**
- Exit code = 0
- All "cache" tagged tests pass
- No new failures vs. iter-26 baseline

---

### TC-06 — Byte-identity: test_bar_cache.py snapshot monkeypatch shims stay green

**Type:** artifact
**Preconditions:**
- Backend code is built
- `apps/backend/tests/test_bar_cache.py` exists
- Pytest environment is available

**Steps:**
1. Run `cd /home/dennis-chan/Git/trendora/apps/backend && .venv/bin/python -m pytest tests/test_bar_cache.py -v`
2. Capture stdout and stderr
3. Assert the exit code is 0

**Expected outcome:**
- The 12 existing `test_bar_cache.py` test cases pass
- The monkeypatch shims at lines 91, 256, and 102 (patching the snapshot of `_BarCache.prefill` and `bars_asof` for byte-identity verification) still work correctly
- If the fallback `prefill` lever (optional `symbols=`/`min_date=` params) was added, those params default to None and do not break the 2-arg snapshot call

**Pass criteria:**
- Exit code = 0
- All 12 tests pass
- No test failure related to `prefill` signature change (all new params are optional with safe defaults)

---

### TC-07 — J-16 live: Full-universe backfill completes on the browser without crashing the backend

**Type:** browser
**Preconditions:**
- Backend is running with the memory-fixed implementation
- Frontend is running at `http://localhost:3000`
- `/data` page is accessible
- Browser (Chrome MCP) is available

**Steps:**
1. Navigate to `http://localhost:3000/data`
2. Verify the "Rebuild snapshots" or "Backfill" button is visible
3. Click the button to start the full-universe rebuild job
4. Poll the page every 3s for 30 minutes, recording the job-progress counter and status
5. Verify the counter advances monotonically (never jumps backward, never stays stuck for >2 minutes)
6. Verify the page never shows an error card or blank application-error page
7. Wait for the job to complete (status changes to "completed" or progress reaches 1.0)
8. After completion, load `/api/stocks` in a new tab and verify 200 and populated leaderboard

**Expected outcome:**
- Job starts cleanly (button click registered, no immediate error)
- Progress counter advances through deep-history dates (dot-com era / GFC / COVID / recent)
- Backend remains alive throughout (no "Backend unavailable" card, no server error)
- Job completes within 45 minutes without crashing
- Downstream APIs (`/api/stocks`) remain reachable and 200 after job completion

**Pass criteria:**
- Progress counter advances from 0 to N (where N ≥ 100, representing at least 100 dates processed)
- No backward jump in counter (monotonically non-decreasing)
- No stuck state > 2 minutes
- Job completion: final status shows "completed" or progress = 1.0
- Post-job `/api/stocks` is 200 with populated data
- No error logs in backend (check server console for `MemoryError`, `Exception`, or `Error` keywords)

---

### TC-08 — J-13 cold-start: /data page loads and renders on cold backend as FIRST request

**Type:** browser
**Preconditions:**
- Backend is stopped
- Frontend is running or will be restarted
- Database is clean
- Browser (Chrome MCP) is available

**Steps:**
1. Ensure backend is stopped
2. Start the backend with `bash scripts/start-backend.sh`
3. Wait up to 180s for backend to be healthy (port 8000 listening, `/api/health` returns 200)
4. Navigate to `http://localhost:3000/data` (this is the FIRST page request to the backend, not `/api/health` or a different API)
5. Wait for the page to fully load and render (time-to-interactive)
6. Verify the page displays:
   - The Data Manager header
   - Job-progress panel with status and counter
   - Per-date availability heatmap or legend
   - No error cards, no blank page, no "Backend unavailable" message
7. Click to `/stocks` and verify it loads and shows the leaderboard

**Expected outcome:**
- Cold-start `/data` page loads within 60s without OOM
- Page renders populated job-progress data (not a skeleton, not an error)
- Navigation to `/stocks` works and shows data

**Pass criteria:**
- Page fully loads and renders within 60s of backend startup
- No 503 or 500 error
- Job-progress counter is visible and non-zero (at least one date already scanned on cold start, or the counter shows 0 honestly)
- `/stocks` page loads successfully after `/data`

---

### TC-09 — J-01 through J-05, J-10, J-12, J-15: Required-still-passing journeys re-verified live

**Type:** browser
**Preconditions:**
- Backend is running with the memory-fixed implementation
- Frontend is running at `http://localhost:3000`
- All core pages (`/stocks`, `/stocks/{ticker}`, `/evidence`, `/data`, `/sectors`, `/themes`, `/research`) are reachable
- Browser (Chrome MCP) is available

**Steps:**
1. **J-01**: Navigate to `/stocks`. Verify each row's score area shows a visible evidence badge ("Proven" or "Not yet proven"). Assert at least one badge is present and no score lacks a status.
2. **J-03**: Find a score with a "Not yet proven" badge (or a failed claim). Verify the UI clearly marks it as unproven, not as a confident number.
3. **J-04**: Navigate to Dashboard and note the current market regime. Open a research lab or Evidence surface. Verify evidence is labeled with the regime it applies to.
4. **J-05**: Click "Evidence" in the nav. Verify a list of certified claims renders with hypothesis, verdict, control comparison, date, and forward-walk score. Click a claim and verify it links back to the badge.
5. **J-10**: Open a long-history stock (AAPL). Toggle the "Full-history" option on the chart. Verify the chart spans back to ~1996 (or the stock's real IPO). Verify no fabricated bars are present.
6. **J-12**: Open the leaderboard on `/stocks`. Note the date displayed. Open a stock that IPO'd mid-history (e.g., ARM). Verify it is ABSENT from dates before its real IPO and PRESENT after. Check that a stock with ended data shows honest NA/n=0 for future horizons.
7. **J-15**: Measure the time-to-interactive for `/stocks`, `/stocks/AAPL`, `/data`, `/evidence`. Record each in a log. Verify all are under 3s warm (after a second load). Verify API endpoints (`/api/stocks`, `/api/stocks/AAPL`, `/api/data`) respond within their budgets (≤1.5s for `/api/stocks`, ≤0.3s for `/api/stocks/{ticker}`, ≤1.5s warm for `/api/data`).

**Expected outcome:**
- **J-01**: Every score has a badge
- **J-03**: Unproven/failed scores are clearly marked
- **J-04**: Regime labels are present and correct
- **J-05**: Evidence ledger is auditable, claims link back to surfaces
- **J-10**: Deep history is visible and byte-accurate, no fabrication
- **J-12**: Membership timeline is honest (entries/exits at real IPO/delisting dates)
- **J-15**: All pages and APIs meet their performance budgets

**Pass criteria:**
- **J-01**: ≥3 rows on `/stocks` leaderboard, each shows a badge (pass/fail count)
- **J-03**: At least one "Not yet proven" badge found and visibly marked (screenshot evidence)
- **J-04**: Regime label visible on at least one evidence surface (screenshot evidence)
- **J-05**: Evidence page loads, shows ≥1 row with all fields, at least one claim links back to a badge
- **J-10**: AAPL chart spans to ≥1996, close is continuous across any known splits, no fabricated bars (spot-check 3 dates)
- **J-12**: ARM absent before real IPO, present after; a delisted name shows honest NA/n=0 (spot-check 2 symbols)
- **J-15**: All pages ≤3s warm, all APIs within budget; record timings in `reports/qa/goal-mcp-loop-iter-27-perf.log`

---

### TC-10 — Anti-goal #8 resolved: Backend degradation is honest, never crashes with blank application-error page

**Type:** browser
**Preconditions:**
- Backend is running
- Frontend is running
- Browser (Chrome MCP) is available

**Steps:**
1. Start the frontend at `http://localhost:3000`
2. Verify the app loads normally (Dashboard or `/stocks` renders)
3. Stop the backend via `pkill -f "uvicorn.*--port 8000"` (or your backend stop command)
4. Wait 5s for TCP connections to fully close
5. On the frontend, click to a data-dependent page (e.g., `/stocks`)
6. Verify the page does NOT show a blank application-error crash page
7. Verify the page shows a single, contained "Backend unavailable" card (or error boundary)
8. Verify nav/shell/other UI elements remain visible and responsive (not a full-page takeover)
9. Restart the backend and verify the page recovers (data reappears, no manual refresh needed)

**Expected outcome:**
- When backend is down, the frontend gracefully shows ONE contained error card
- The card clearly states "Backend unavailable" or similar
- Navigation and shell remain interactive (user can navigate to other pages, see nav structure)
- No blank page, no cryptic error dump, no application-error crash page
- Backend recovery is auto-detected and the page re-renders with data

**Pass criteria:**
- Degraded state: only ONE error card visible, nav intact (screenshot evidence)
- No blank page or application-error dump visible
- Message clearly communicates backend unavailability (not a vague error)
- Recovery: data re-appears within 10s of backend restart (no manual refresh)

---

## Summary

Total test cases: 10
API tests: 5 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06 are artifact/unit, TC-07 and TC-08 bridge to browser)
Browser tests: 4 (TC-07, TC-08, TC-09, TC-10)
Artifact checks: 3 (TC-03, TC-04, TC-05, TC-06)

**Centerpiece:** TC-01 (full-universe memory footprint) must pass with VSZ + RSS both under 6144 MB, measured under literal `ulimit -v 6291456` on the complete 322-date × 541-member rebuild shape.

**Mandatory iteration lessons applied:**
- TC-01 samples BOTH `VmSize` (VSZ) AND `VmRSS` (RSS), not RSS-only (iter-26 lesson)
- TC-01 uses the full 322-date × 541-member rebuild shape, not a 12-date subset (iter-26 lesson)
- TC-02 uses the stop→cold-start→`/api/data`-first sequence, not just an `/api/health` check (iter-24 lesson)
- TC-09 includes live browser re-verification of all 8 required-still-passing journeys (iter-26 gap: they were SKIPPED behind the outage)
- TC-10 re-verifies anti-goal #8 via the canonical browser-qa lane, not just a unit-test ablation (iter-24 lesson)

**No full pytest suite:** Targeted tests only (test_scoring_window.py, test_forward_testing.py, test_bar_cache.py, plus the new bars_asof_window equivalence cases). Full suite (~10–11 h) is out of scope.
