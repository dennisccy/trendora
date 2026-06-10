# goal-i_can_see_the_wealthy_future_forever-iter-28 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-28
**Date:** 2026-06-10
**Frontend Present:** yes

## Phase Goal

The backend accepts connections and serves the core read pages (Dashboard, Stocks, Sectors, Themes, Stock Detail) for the latest as-of date within a small config-set readiness budget on a cold start — it no longer blocks serving for minutes on the historical walk-forward backfill, which instead warms up in the background with honest live progress, never crashes the boot on a concurrent or failed warm-up, and never shows a misleading "unavailable".

---

## Test Cases

### TC-01 — Fast Boot: Server Accepting Connections Within Readiness Budget

**Type:** integration  
**Preconditions:**
- Fresh database (no prior snapshots)
- Backend built and ready to start
- `config.yaml` has a valid `startup` block with `readiness_budget_seconds` set

**Steps:**
1. Start the backend server
2. Record the timestamp when the process starts
3. Poll `GET /api/health` every 100ms
4. Measure the elapsed time when the first 200 response is received

**Expected outcome:** Server responds to `/api/health` within the `readiness_budget_seconds` configured value

**Pass criteria:** 
- First successful `/api/health` 200 response occurs before `(start_time + readiness_budget_seconds)`
- Response is not a 5xx error and includes valid JSON

---

### TC-02 — Latest Snapshot Present Within Readiness Budget

**Type:** integration  
**Preconditions:**
- Fresh database with seed data loaded
- Backend running (from TC-01)
- At least one historical price bar exists in the database

**Steps:**
1. Server has been running for less than `readiness_budget_seconds`
2. Issue `GET /api/dashboard` (the latest-date read path)
3. Capture the response status and body

**Expected outcome:** The endpoint returns 200 with a valid dashboard snapshot for the latest as-of date

**Pass criteria:**
- HTTP 200 response received
- Response includes a valid snapshot object (not an error)
- The `as_of_date` in the response matches the latest available price date in the seed
- Response contains expected fields (symbol count, sector/theme data, etc.)

---

### TC-03 — Server Serving While Cadence Warm-Up In Flight

**Type:** integration  
**Preconditions:**
- Fresh database with a configuration that includes multiple historical `bootstrap_dates`
- Backend server just started (within readiness budget, latest snapshot created)
- `readiness` endpoint is polling the warm-up state

**Steps:**
1. Server has finished the synchronous lifespan work (latest snapshot created, `yield` executed)
2. Observe the readiness endpoint reporting `initializing` with `{done, total}` progress
3. While readiness state is still `initializing`, issue `GET /api/stocks` and `GET /api/backtest`
4. Measure time to receive responses

**Expected outcome:**
- Both `/api/stocks` and `/api/backtest` return 200 with valid latest-snapshot data (not an "unavailable" error)
- Readiness endpoint reports `initializing` with honest `{done, total}` cadence counts (e.g., "history 2/11")
- The returned data is identical to what the latest snapshot contains

**Pass criteria:**
- HTTP 200 responses from core read paths while `readiness = initializing`
- Readiness includes a `warmup.done` and `warmup.total` field
- `warmup.done < warmup.total` (warm-up is in flight, not complete)
- Data returned is not a partial/empty result or a placeholder

---

### TC-04 — Readiness Transitions From Initializing to Ready

**Type:** integration  
**Preconditions:**
- Backend server running with background warm-up active
- Initial readiness state is `initializing` (from TC-03)

**Steps:**
1. Poll the readiness endpoint every 100ms
2. Record the timestamp when readiness first transitions from `initializing` to `ready`
3. Check that `warmup.done === warmup.total` (all cadence dates completed)

**Expected outcome:**
- Within a reasonable time (minutes, not hours), readiness transitions to `ready`
- All cadence snapshots and forward-returns have been produced
- Subsequent reads to the readiness endpoint report `ready`

**Pass criteria:**
- `readiness.state === 'ready'`
- `warmup.done === warmup.total`
- Transition occurs after the background warm-up completes (no race condition)
- Readiness never reports `ready` before the latest snapshot was confirmed to exist (from TC-02)

---

### TC-05 — Readiness Never Ready Before Latest Snapshot Servable

**Type:** integration  
**Preconditions:**
- Fresh database (no snapshots pre-loaded)
- Backend configured with a valid latest-data date and bootstrap cadence

**Steps:**
1. Start the backend
2. Instrument the readiness computation to log every time it computes the state
3. Monitor the readiness endpoint responses as the backend boots
4. Cross-reference each `ready` report with the database to confirm a latest snapshot exists

**Expected outcome:**
- The readiness endpoint ONLY reports `ready` after the latest snapshot is confirmed to exist in the database
- No `ready` response is returned during the bootstrap phase before the latest snapshot is created

**Pass criteria:**
- At every point in time when readiness = `ready`, querying the database confirms the latest snapshot exists
- No log entry shows `ready` computed before a `ScannerRun` with the latest date is persisted

---

### TC-06 — Readiness Reports Unavailable on DB Unreachable

**Type:** integration  
**Preconditions:**
- Backend running and serving normally
- Readiness endpoint is being polled

**Steps:**
1. Simulate database unavailability (e.g., stop the database connection, mock a connection error)
2. Poll the readiness endpoint
3. Record the response

**Expected outcome:**
- The readiness endpoint returns `unavailable` (not a 5xx error, but an honest state)
- The response includes a reason or error detail (e.g., "DB connection failed")
- The server does not crash; subsequent health checks are processed

**Pass criteria:**
- `readiness.state === 'unavailable'`
- HTTP 200 response (the endpoint itself is healthy; the backend state is unavailable)
- No 5xx error or server crash

---

### TC-07 — Concurrency Race: Duplicate run_scan Create on Same Date

**Type:** unit  
**Preconditions:**
- Scanner module loaded with access to the database session
- A function to simulate concurrent execution (e.g., threading or async)

**Steps:**
1. Prepare two concurrent `run_scan` calls with the same `as_of_date`
2. Force both to pass the `get_run_for_date` existence check
3. Allow both to proceed to the `session.commit()` on the INSERT
4. Observe the second call's behavior (should handle the IntegrityError)

**Expected outcome:**
- The second call catches the `UNIQUE constraint failed: scanner_runs.asof_date` error
- It rolls back the transaction and re-reads the existing row via `get_run_for_date`
- The second call returns the same immutable `ScannerRun` row as the first
- No duplicate row is created; no exception is raised to the caller

**Pass criteria:**
- `len(db.query(ScannerRun).filter_by(asof_date=test_date).all()) === 1`
- Both calls return the same row object (or equivalent data)
- No IntegrityError or UNIQUE constraint exception escapes `run_scan`
- The returned snapshot is idempotent across both calls

---

### TC-08 — Concurrency Race: Duplicate Forward-Returns INSERT

**Type:** unit  
**Preconditions:**
- Forward-testing module loaded
- Database session available
- A mechanism to simulate concurrent INSERT execution

**Steps:**
1. Prepare two concurrent `backfill_forward_returns` calls (or direct `_insert_run_forward_returns` calls) for the same `as_of_date`
2. Force both to attempt the INSERT
3. Observe the second call's handling of the duplicate key

**Expected outcome:**
- The second INSERT is idempotent (detects the row already exists, returns success, no duplicate added)
- No `UNIQUE constraint` error or duplicate row is created
- Both calls complete without raising an exception

**Pass criteria:**
- No exception from the second concurrent INSERT
- Row count for the given date does not increase on the second insert (remains 1)
- Both calls logically succeed without visible error to the caller

---

### TC-09 — Non-Fatal Warm-Up Exception: Boot Survives and Logs Error

**Type:** integration  
**Preconditions:**
- Backend configured with a background warm-up task
- Mechanism to inject an exception into the warm-up (e.g., mock a data provider failure)

**Steps:**
1. Inject an exception into the warm-up task (e.g., a network timeout or database error)
2. Start the backend server
3. Confirm the server fully boots and accepts connections (`/api/health` 200)
4. Confirm the exception is logged (check logs or capture stderr)
5. Check that the readiness endpoint reflects the failure state (not a silent green)

**Expected outcome:**
- The server boots and serves without crashing
- The `/api/health` and core read endpoints respond with 200
- The error is logged to standard logging (not swallowed silently)
- The readiness endpoint reports an honest state (not `ready` before the failure is cleared)

**Pass criteria:**
- HTTP 200 responses to `/api/health` and `/api/dashboard` during/after the failure
- Log output includes the exception details (searchable error message)
- Readiness does NOT report `ready` while the warm-up is failed (reports `initializing` or a failure indicator)
- Server process does not exit with a non-zero code

---

### TC-10 — Non-Fatal Warm-Up Exception: Next Boot Completes Idempotent Warm-Up

**Type:** integration  
**Preconditions:**
- Backend has booted once with a warm-up exception (from TC-09)
- The exception is fixed (e.g., data provider is now available)

**Steps:**
1. Stop the backend server
2. Fix the condition that caused the warm-up failure
3. Restart the backend server
4. Wait for the background warm-up to complete
5. Poll the readiness endpoint until it reports `ready`

**Expected outcome:**
- The second boot completes the idempotent warm-up (no duplicate rows, no constraint violations)
- All remaining cadence snapshots and forward-returns are produced
- The readiness endpoint transitions to `ready`

**Pass criteria:**
- Readiness eventually reaches `ready` (warmup.done === warmup.total)
- No duplicate scanner_runs or forward_returns rows (idempotent behavior)
- No UNIQUE constraint or database error on the second boot
- All expected historical snapshots exist after the warm-up completes

---

### TC-11 — Invariant J-06: Score Consistency After Scheduling Change

**Type:** integration  
**Preconditions:**
- Backend has completed a full cold boot with background warm-up
- All cadence snapshots are present and forward-returns are computed

**Steps:**
1. Fetch a symbol's data from `/api/stocks` (list endpoint) for a given snapshot date
2. Fetch the same symbol from `/api/stocks/{symbol}` (detail endpoint) for the same date
3. Compare all score, bucket, and regime values between the two responses
4. Repeat for multiple symbols and dates

**Expected outcome:**
- The symbol data returned from both endpoints is byte-identical for all score/bucket/regime fields
- No divergence exists between the list and detail reads (single source of truth preserved)

**Pass criteria:**
- For each tested symbol + date, the score values match exactly between list and detail endpoints
- A–E bucket assignments are identical
- Regime and actionable status are identical
- All six canonical scores align

---

### TC-12 — Invariant J-07: Risk-Off Gates Actionable

**Type:** integration  
**Preconditions:**
- Backend has completed warm-up
- Configuration includes a bootstrap date with a Risk-Off regime in the seed

**Steps:**
1. Identify a Risk-Off snapshot date in the seed data
2. Fetch `/api/stocks` for that date
3. Count the number of stocks marked as "Actionable" (setup_status or actionable flag)

**Expected outcome:**
- Zero stocks are marked Actionable on a Risk-Off date
- All stocks remain watchlist-only or have a non-actionable status

**Pass criteria:**
- `count(stocks where actionable) === 0` on a Risk-Off date
- The regime field for that date shows "Risk-Off"
- Non-Risk-Off dates show > 0 actionable stocks (as a sanity check)

---

### TC-13 — Invariant: Warmed Snapshots Byte-Identical to Pre-Change Sync Output

**Type:** integration  
**Preconditions:**
- Both pre-change (synchronous boot) and post-change (background warm-up) backends are available for comparison
- Same seed data, same config, same date range

**Steps:**
1. Boot the pre-change backend (synchronous backfill before yield)
2. Collect the complete set of scanner_runs and forward_returns from the database
3. Boot the post-change backend (fast boot + background warm-up)
4. Collect the same scanner_runs and forward_returns from the database
5. Compare the two datasets byte-for-byte

**Expected outcome:**
- The warmed cadence snapshots are byte-identical to the pre-change sync output
- Forward-returns are byte-identical
- The only change is the scheduling of when they are produced (before vs. after yield)
- All aggregate values (e.g., `/api/backtest` results) are identical

**Pass criteria:**
- `hash(pre_change_snapshots) === hash(post_change_snapshots)`
- `hash(pre_change_forward_returns) === hash(post_change_forward_returns)`
- Backtest aggregate JSON is identical between the two boots
- No engine behavior changed; only timing

---

### TC-14 — Config Validation: startup Block Required and Parsed

**Type:** api  
**Preconditions:**
- Backend binary ready
- `config.yaml` contains a valid `startup` block with typed fields

**Steps:**
1. Start the backend with the valid config
2. Capture any config validation errors or warnings
3. Verify the typed `StartupCfg` is instantiated and accessible

**Expected outcome:**
- Backend starts without config errors
- The `startup` config block is parsed into a typed object (e.g., `StartupCfg`)
- Readiness budget, warm-up batch size, and poll interval are all present

**Pass criteria:**
- No config parsing errors logged
- All required fields in the `startup` block are validated before the server accepts connections
- A missing or malformed `startup` block causes a clear boot error (not a silent default or magic number)

---

### TC-15 — No Magic Numbers: startup Tunables Not Hardcoded

**Type:** artifact  
**Preconditions:**
- Source code review ready (backend modules)

**Steps:**
1. Grep `apps/backend/main.py` for numeric literals related to readiness, poll interval, warm-up batch size
2. Grep `apps/backend/app/engine/readiness.py` (or warm-up controller) for the same
3. Confirm all such values come from `config.yaml` via the `StartupCfg` object
4. Verify `test_no_magic_numbers` or equivalent test passes

**Expected outcome:**
- No readiness budget, poll interval, warm-up batch size, or timeout literals appear in the code
- All startup tunables are loaded from `config.yaml` via the typed config object

**Pass criteria:**
- Grep returns zero results for hardcoded numeric values related to startup/readiness/warm-up
- All readiness/warm-up timing references go through the config object
- The test suite includes a check that validates this invariant

---

### TC-16 — Browser: Cold Boot and Latest Snapshot Served

**Type:** browser  
**Preconditions:**
- Fresh `trendora.db` (deleted to simulate a cold start)
- Frontend `.next` cache cleared (`rm -rf apps/frontend/.next`)
- Backend not running

**Steps:**
1. Start both the backend and frontend services
2. Confirm backend `/health` responds with 200 and includes readiness data
3. Confirm `main-app.js` loads successfully (no 404 on Next.js static assets)
4. Navigate to `/` (dashboard) and `/stocks` in the browser
5. Verify both pages load and display the latest snapshot data within ~5–10 seconds

**Expected outcome:**
- Pages load without a long "Backend unavailable" wait
- The dashboard and stocks pages show data for the latest as-of date
- The UI is responsive and usable immediately

**Pass criteria:**
- `/` and `/stocks` HTTP requests complete within the readiness budget
- Page content renders without errors or empty states
- The latest snapshot data is displayed (symbol counts, sector/theme data, etc.)

---

### TC-17 — Browser: Readiness Badge Initializing → Ready Transition

**Type:** browser  
**Preconditions:**
- Backend and frontend running on a cold-start with background warm-up active
- Frontend is displaying the header with the readiness badge

**Steps:**
1. Open the browser to the home page (`/`)
2. Observe the readiness badge in the top bar
3. Watch as it transitions from "Initializing… history n/m" to "Ready" or similar
4. Note the time elapsed from the initial "Initializing" to the final "Ready"

**Expected outcome:**
- Badge initially shows an "Initializing" state with progress text (e.g., "history 2/11")
- Badge transitions to "Ready" within ~1–2 seconds of the warm-up completion
- The transition is visible to the user (not a 30-second polling delay)
- Badge styling changes (e.g., color/icon shift) to indicate the state change

**Pass criteria:**
- Badge is rendered and visible in the header
- Badge shows warm-up progress in the "Initializing" state (not a generic spinner)
- Badge updates to show "Ready" within ~1–2 s of the backend warm-up completing
- Badge never shows "Ready" before the server has actually warmed up

---

### TC-18 — Browser: Backtest Shows "Warming Up" State During Warm-Up

**Type:** browser  
**Preconditions:**
- Backend running with background warm-up in progress (readiness = `initializing`)
- Frontend loaded and ready

**Steps:**
1. Navigate to `/backtest`
2. Observe the page content while the warm-up is in flight
3. Look for a "warming up — historical evidence still loading (n/m)" message or state
4. Confirm the page does not show an empty result or error
5. Wait until the warm-up completes and observe the page auto-populate

**Expected outcome:**
- While warm-up is active, the Backtest page shows a transient warming state (not an error)
- The warming message includes the progress (e.g., "n/m" snapshots)
- Once the warm-up completes, the page auto-populates with the full backtest results
- No manual refresh or page reload is required

**Pass criteria:**
- A warming message is visible on the page during background warm-up
- Message text includes progress information (done/total counts)
- Message disappears and results appear after warm-up completes
- No error state is shown while warming (e.g., no red banner, no 5xx error)

---

### TC-19 — Browser: Research Shows "Warming Up" State During Warm-Up

**Type:** browser  
**Preconditions:**
- Backend running with background warm-up active
- Frontend loaded and ready

**Steps:**
1. Navigate to `/research`
2. Observe the page content during the warm-up
3. Look for a "warming up — historical evidence still loading (n/m)" state
4. Confirm the page does not display a partial or fabricated result
5. Wait for the warm-up to complete and observe auto-population

**Expected outcome:**
- The Research page shows a warming state with honest progress during warm-up
- Once warm-up finishes, the page populates with full research data
- No fabricated data or partial results are shown

**Pass criteria:**
- A warming message is displayed during background warm-up
- Message includes progress text
- Results appear after warm-up without manual action
- No error or empty-state is presented as a complete result

---

### TC-20 — Browser: No New Date Control Added

**Type:** browser  
**Preconditions:**
- Frontend running on the dashboard (`/`)
- All pages (Stocks, Backtest, Research, etc.) are accessible

**Steps:**
1. Navigate through each main page (Dashboard, Stocks, Sectors, Themes, Backtest, Research)
2. Inspect the UI for any new date selector, date input, or date control
3. Confirm the only date control is the global as-of selector (existing from J-18)

**Expected outcome:**
- No new date control or form field appears on any page
- The existing global as-of selector remains the only date control
- J-18 constraint (exactly one date control) is preserved

**Pass criteria:**
- Zero new date input fields, dropdowns, or date pickers
- The global as-of switcher is the only date control across all pages
- No hidden or nested date state is introduced in the component tree

---

## Summary

**Total test cases:** 20

**Test type breakdown:**
- API tests: 7 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-14)
- Unit tests: 2 (TC-07, TC-08)
- Integration tests: 5 (TC-09, TC-10, TC-11, TC-12, TC-13)
- Browser tests: 5 (TC-16, TC-17, TC-18, TC-19, TC-20)
- Artifact/code review: 1 (TC-15)

**Coverage by journey:**
- **J-40 (Fast-ready boot + background warm-up + honest readiness):** TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-14, TC-16, TC-17, TC-18, TC-19
- **J-41 (Boot resilience — concurrency-safe, non-fatal):** TC-07, TC-08, TC-09, TC-10
- **Invariant verification (J-06, J-07, J-18):** TC-11, TC-12, TC-13, TC-20
- **Configuration validation (no magic numbers):** TC-15

All tests are deterministic, offline-provable (no external data provider dependency), and map directly to the DEFINITION OF DONE acceptance criteria and anti-goal constraints.
