# Goal Ops-Hardening Iter-6 Functional Test Plan

**Phase:** goal-ops-hardening-iter-6  
**Date:** 2026-07-20  
**Frontend Present:** yes

## Phase Goal

Closing J-06 (the last failing Must-have journey) by fixing the Dashboard and Data Manager's genuine browser-connection-queuing latency caused by Chrome's 6-connections-per-origin cap. Iter-5 fixed the backend (`ForwardAggregateCache`), but real-browser measurement showed `GET /api/indexes?full=true` at 1.68–2.19s (budget ≤1.5s) and `GET /api/data/availability` at 2.9–3.0s (previously unbudgeted). The fix is frontend-only: defer/stagger the `PhaseCrossViewCard`'s on-load fetch and the Data Manager's `loadAvailability()` to reduce same-origin connection contention. No new endpoint, no computed-value change — only request timing/ordering.

## Test Cases

### TC-01 — Dashboard `/api/indexes?full=true` real-browser latency (3 reloads)

**Type:** browser  
**Preconditions:**
- Backend running in prod mode via `scripts/start-backend.sh`
- Frontend running in prod mode via `scripts/start-frontend.sh`
- Both services warm and ready
- Chrome DevTools Network tab accessible

**Steps:**
1. Open Dashboard (`/`) in Chrome
2. Open Chrome DevTools Network tab, filter by `/api/indexes?full=true`
3. Reload the page (F5)
4. Observe the Network tab timing for `GET /api/indexes?full=true`; record response time in milliseconds
5. Repeat steps 3–4 two more times (total 3 reloads)

**Expected outcome:** All 3 reload measurements show Network-tab response time ≤1500ms

**Pass criteria:** Each of the 3 reload timings for `GET /api/indexes?full=true` is ≤1500ms; no single reload exceeds budget

---

### TC-02 — Data Manager `/api/data/availability` real-browser latency (3 reloads)

**Type:** browser  
**Preconditions:**
- Backend and frontend running in prod mode (same as TC-01)
- Chrome DevTools Network tab accessible

**Steps:**
1. Open Data Manager (`/data`) in Chrome
2. Open Chrome DevTools Network tab, filter by `/api/data/availability`
3. Reload the page (F5)
4. Observe the Network tab timing for `GET /api/data/availability`; record response time
5. Repeat steps 3–4 two more times (total 3 reloads)

**Expected outcome:** All 3 reload measurements show Network-tab response time within newly committed `reports/perf-budgets.md` budget

**Pass criteria:** Each of the 3 reload timings for `GET /api/data/availability` is within the budget documented in `reports/perf-budgets.md` for this endpoint

---

### TC-03 — All 11 J-06 pages stay within budget after scheduling fix

**Type:** browser  
**Preconditions:**
- Backend and frontend running in prod mode
- `reports/perf-budgets.md` contains TTI and on-load endpoint budgets for all 11 pages

**Steps:**
1. Load each of the 11 named J-06 pages once: `/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, one `/research` lab (e.g., `/research/event-study`)
2. For each page, record time-to-interactive (TTI) and each on-load endpoint's response time from Network tab
3. Cross-reference each measurement against `reports/perf-budgets.md`

**Expected outcome:** Every page's TTI and every on-load endpoint's latency stays within committed budget; no new violation introduced elsewhere

**Pass criteria:** All 11 pages + all on-load endpoints within their respective `reports/perf-budgets.md` budgets; zero violations

---

### TC-04 — `/api/data/availability` budget row added to perf-budgets.md

**Type:** artifact  
**Preconditions:**
- Functional test plan executed (TC-01, TC-02, TC-03 complete)
- `reports/perf-budgets.md` is accessible

**Steps:**
1. Read `reports/perf-budgets.md`
2. Search for any row containing `GET /api/data/availability`
3. Verify exactly one such row exists and contains real-browser-measured timing

**Expected outcome:** File contains exactly one new budget entry for `GET /api/data/availability` at the generic ≤1.5s endpoint-budget class (or documented adjustment with stated reason)

**Pass criteria:** Exactly one `GET /api/data/availability` row exists in `reports/perf-budgets.md`; no second budgets file created anywhere in the repo

---

### TC-05 — Payload byte-identity: fetch-scheduling fix does not change response values

**Type:** api  
**Preconditions:**
- Backend running in prod mode
- A fixed `as_of` date is chosen (e.g., latest or a known snapshot date)

**Steps:**
1. Capture baseline response for `GET /api/dashboard?as_of=<fixed_as_of>` via curl
2. Capture baseline response for `GET /api/market-phase?as_of=<fixed_as_of>`
3. Capture baseline response for `GET /api/sectors?as_of=<fixed_as_of>`
4. Capture baseline response for `GET /api/themes?as_of=<fixed_as_of>`
5. Capture baseline response for `GET /api/indexes?full=true&as_of=<fixed_as_of>`
6. Capture baseline response for `GET /api/regime-history?full=true&as_of=<fixed_as_of>`
7. Capture baseline response for `GET /api/market-phase?full=true&as_of=<fixed_as_of>`
8. Capture baseline response for `GET /api/data/availability?as_of=<fixed_as_of>`
9. After frontend fetch-scheduling fix is deployed, re-capture all 8 endpoints at the same `as_of`
10. Compare pre/post payloads byte-for-byte

**Expected outcome:** Every endpoint payload is byte-identical pre/post fix; only request timing/ordering changed, never values

**Pass criteria:** MD5 hash (or byte-for-byte comparison) of each endpoint's response body matches pre/post; zero payload differences

---

### TC-06 — J-01 golden script step 6 rewritten: asserts on own run's persisted entry

**Type:** browser  
**Preconditions:**
- `runs/goal-session-ops-hardening/journey-scripts/J-01.json` exists with step 6 rewritten
- Backend and frontend running in prod mode
- Deterministic replay infrastructure available

**Steps:**
1. Run the J-01 golden script deterministically via the replay harness
2. Execute all 6 steps in order: steps 1–5 (backfill submission and completion), step 6 (assertion on own run's persisted `/data` entry)
3. Observe the step 6 assertion against the run's own history entry (not a stale fixed historical date)

**Expected outcome:** All 6 steps pass without manual adjudication; step 6 assertion succeeds on the run this script submitted

**Pass criteria:** Deterministic replay of J-01.json completes with all steps passing; step 6 assertion targets the submitted run's own `/data` history entry, not a fixed `/scanner-runs` date

---

### TC-07 — J-03 golden script unchanged: still passes deterministically

**Type:** browser  
**Preconditions:**
- `runs/goal-session-ops-hardening/journey-scripts/J-03.json` exists unchanged
- Backend and frontend running in prod mode
- Deterministic replay infrastructure available

**Steps:**
1. Run the J-03 golden script deterministically via the replay harness
2. Execute all steps in order
3. Observe that J-03 remains green (J-03 unchanged, should not regress)

**Expected outcome:** All J-03 steps pass without manual adjudication; journey remains green

**Pass criteria:** Deterministic replay of J-03.json completes with all steps passing; zero regressions from iter-5

---

### TC-08 — J-04 and J-05 pass via browser-qa LLM fallback (no golden script on file)

**Type:** browser  
**Preconditions:**
- No golden script exists for J-04 or J-05
- Backend and frontend running in prod mode
- Browser-qa-agent available for LLM fallback execution

**Steps:**
1. browser-qa-agent runs J-04's numbered acceptance steps from `docs/goal.md` (non-blocking boot with visible status, 6 steps)
2. browser-qa-agent runs J-05's numbered acceptance steps from `docs/goal.md` (aggregates precomputed at ingest, 4 steps)
3. For each journey, capture evidence (screenshots, Network-tab timings, dom assertions as needed)
4. Score each journey based on acceptance criteria passing and evidence quality

**Expected outcome:** Both J-04 and J-05 scored as `passing` with cited evidence; both journeys move out of `unknown` status

**Pass criteria:** J-04 passes non-blocking boot acceptance steps with evidence of phase/progress response + badge visibility + crash presentation; J-05 passes aggregate precomputation acceptance steps with evidence of ingest-time updates + storage-served values + cold-restart performance

---

### TC-09 — Backend unit/integration tests: pytest runs to completion with zero failures

**Type:** api  
**Preconditions:**
- TMPDIR set to `/home/dennis-chan/.cache/iad/iad.goal-ops-harde-c41f8e4e.11312`
- Backend test environment available

**Steps:**
1. Set environment: `export TMPDIR="/home/dennis-chan/.cache/iad/iad.goal-ops-harde-c41f8e4e.11312"`
2. Run: `pytest tests/test_api_backtest.py tests/test_mcp_window.py -v`
3. Wait for full suite completion
4. Record test count, pass count, fail count, errors

**Expected outcome:** All tests in both files pass; zero failures; `loaded_engine` fixture suite runs to completion (may take several minutes)

**Pass criteria:** `pytest` exit code 0; all tests pass; no timeouts or incomplete runs

---

### TC-10 — PhaseCrossViewCard deferred fetch aborted mid-flight: shows honest loading/error state

**Type:** browser  
**Preconditions:**
- Frontend deployed with staggered fetch in `PhaseCrossViewCard`
- Dashboard (`/`) loaded and rendering the card
- DevTools open to observe state changes

**Steps:**
1. Load Dashboard (`/`)
2. Immediately (while PhaseCrossViewCard's deferred fetch is in-flight or queued) toggle `as_of` date selector to a different date
3. Observe the card's rendering during and after the abort
4. Wait for the new fetch to complete or be aborted
5. Verify the card shows a clear, honest state (loading skeleton, error card, or final result)

**Expected outcome:** Card shows existing honest `loading`/`error`/`ok` state skeleton or spinner; never a blank, frozen, or hung frame during the abort window

**Pass criteria:** Card rendering remains visible and responsive throughout; no blank/frozen/hung frame when deferred fetch is aborted mid-flight; existing loading affordance (`animate-pulse` skeleton or spinner) remains visible

---

### TC-11 — Backend ≤5s boot budget preserved: frontend fix does not affect boot

**Type:** api  
**Preconditions:**
- Backend not yet started
- Process start timing infrastructure available

**Steps:**
1. Stop the backend if running
2. Measure process start time (mark t0)
3. Run `scripts/start-backend.sh` (prod mode)
4. Poll `GET /api/health` at regular intervals from t0
5. Record the timestamp of the first HTTP 200 response
6. Calculate elapsed time from t0 to first 200

**Expected outcome:** First HTTP 200 arrives within 5 seconds of process start on warm DB

**Pass criteria:** `(t_first_200 - t_start) ≤ 5 seconds`; confirms this frontend-only fix does not affect the existing boot-to-health budget (expected trivially true since no boot-path file is touched)

---

## Summary

**Total test cases:** 11

**Test breakdown by type:**
- **Browser tests:** 6 (TC-01, TC-02, TC-03, TC-06, TC-07, TC-08, TC-10 = 7 browser tests)
- **API tests:** 3 (TC-05, TC-09, TC-11)
- **Artifact checks:** 1 (TC-04)

**Key measurement gates:**
- TC-01/TC-02/TC-03: Real-browser Network-tab latency ≤ budget for 11 pages
- TC-04: `reports/perf-budgets.md` updated with `/api/data/availability` budget
- TC-05: Payload byte-identity across fetch-scheduling change
- TC-06/TC-07: Golden script replay (J-01 fixed step 6; J-03 unchanged)
- TC-08: J-04/J-05 journey acceptance via browser-qa LLM fallback
- TC-09: Unit tests pass to completion
- TC-10: Abort-mid-flight error handling
- TC-11: Boot budget preserved

**Pass decision:** All 11 test cases must pass for QA verdict PASS. Any test failure = QA FAIL.
