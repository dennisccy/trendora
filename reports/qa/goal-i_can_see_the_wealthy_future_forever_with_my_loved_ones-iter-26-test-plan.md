# Goal Iteration 26 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-26  
**Date:** 2026-06-17  
**Frontend Present:** yes

## Phase Goal

The Data Manager Expand-universe job's market-cap reference authenticates with Yahoo via cookie + crumb (no API key required), returns real market caps instead of silently omitting all candidates, and on systemic auth/limit failure pauses the job resumable with a clear operator message instead of falsely reporting an empty universe.

## Test Cases

### TC-01 — YahooProvider.get_market_cap acquires cookie + crumb once and reuses across batch

**Type:** api  
**Preconditions:** Backend is running; YahooProvider is instantiated with an injectable `httpx.Client`.

**Steps:**
1. Create a YahooProvider with an injected mock `httpx.Client` that tracks all requests.
2. Call `get_market_cap(["AAPL", "MSFT", "GOOGL", "TSLA"])` (a batch of 4 symbols).
3. Verify the mock client received exactly one GET to `https://finance.yahoo.com` with a browser-like User-Agent to acquire the cookie.
4. Verify the mock client received exactly one GET to `/v1/test/getcrumb` with the cookie jar and a browser-like UA to acquire the crumb.
5. Verify the mock client received exactly one GET to `/v7/finance/quote?symbols=AAPL,MSFT,GOOGL,TSLA&crumb=<CRUMB>` with the crumb embedded.
6. Mock the quote response to return `{"quoteResponse":{"result":[{"symbol":"AAPL","marketCap":3000000000000},...{"symbol":"TSLA","marketCap":800000000000}]}}`.

**Expected outcome:** The method returns a dict mapping each symbol to its market cap (float) or None if absent. No credential/crumb is logged or echoed.

**Pass criteria:** (1) Exactly three HTTP calls in order: cookie GET, crumb GET, batched quote GET; (2) cookie and crumb acquired once and reused; (3) all four symbols return their real caps or None; (4) no crumb/cookie string appears in the returned data or any error message.

---

### TC-02 — YahooProvider.get_market_cap returns None for symbols without marketCap in 200 response

**Type:** api  
**Preconditions:** Backend is running; YahooProvider with injected mock `httpx.Client`.

**Steps:**
1. Create a YahooProvider with an injected mock client.
2. Mock the `/v7/finance/quote` response to return `{"quoteResponse":{"result":[{"symbol":"AAPL","marketCap":3000000000000},{"symbol":"DEAD","noMarketCapField":null}]}}` (DEAD has no `marketCap` key).
3. Call `get_market_cap(["AAPL", "DEAD"])`.

**Expected outcome:** Returns `{"AAPL": 3000000000000.0, "DEAD": None}` — the missing cap is recorded as absent, never fabricated.

**Pass criteria:** Symbol without `marketCap` field returns `None` (honest omission, no synthesized value).

---

### TC-03 — YahooProvider.get_market_cap raises ProviderUnavailableError with redacted URL on parse failure

**Type:** api  
**Preconditions:** Backend is running; YahooProvider with injected mock client.

**Steps:**
1. Create a YahooProvider with an injected mock client.
2. Mock the `/v7/finance/quote` response to return invalid JSON (e.g., `"broken"`).
3. Call `get_market_cap(["AAPL"])`.

**Expected outcome:** Raises `ProviderUnavailableError` with a redacted error message (the URL contains no credential or crumb value).

**Pass criteria:** Error is raised; error message does not contain the crumb value, any credential, or the raw full URL.

---

### TC-04 — Systemic 401 on cookie/crumb acquisition triggers resumable pause in expand screen

**Type:** api  
**Preconditions:** Backend is running; DataProviderRun and import_checkpoints tables exist; an expand-universe job is queued with an injected YahooProvider that raises `ProviderUnavailableError` (simulating 401) on cookie acquisition.

**Steps:**
1. Create an expand-universe job spec targeting the Yahoo source with a batch of 100 candidate symbols.
2. Inject a YahooProvider whose cookie-fetch step raises `ProviderUnavailableError` (mimics HTTP 401).
3. Run the expand job through the REAL `_run_expand_screen` orchestration entry point (not a stand-in).
4. Query the `data_provider_runs` table for the job record.
5. Query the `import_checkpoints` table for the expand checkpoint.

**Expected outcome:** The job status is `resumable`; the job message is "market-cap provider auth failed — Resume to retry" (or similar, from the backend); no candidate is recorded `market_cap_fetch_failed` (the whole batch is paused, not all-omitted).

**Pass criteria:** (1) Job status = `resumable`; (2) job message contains "auth failed" or "provider" + "auth"; (3) `import_checkpoints` checkpoint is durable and marks the job paused-resumable; (4) the job does NOT record all 100 candidates with `market_cap_fetch_failed`.

---

### TC-05 — Systemic 429 on batched quote triggers resumable pause in expand screen

**Type:** api  
**Preconditions:** Backend is running; an expand-universe job is queued with an injected YahooProvider that returns HTTP 429 (rate limit) on the batched `/v7/finance/quote` call.

**Steps:**
1. Create an expand-universe job targeting the Yahoo source.
2. Inject a YahooProvider that acquires cookie+crumb successfully but returns 429 on the batched quote call.
3. Run the expand job through the REAL `_run_expand_screen` orchestration entry point.
4. Query the job status and message.

**Expected outcome:** Job is marked `resumable` with an honest message (e.g., "market-cap provider rate-limited — Resume to retry"); no candidates recorded `market_cap_fetch_failed`.

**Pass criteria:** (1) Job status = `resumable`; (2) message indicates rate-limit or auth failure; (3) candidates are NOT recorded with per-candidate `market_cap_fetch_failed`.

---

### TC-06 — Per-candidate absent marketCap stays honest omission (NOT resumable)

**Type:** api  
**Preconditions:** Backend is running; an expand-universe job with an injected provider that returns a 200 response with some symbols missing `marketCap`.

**Steps:**
1. Create an expand-universe job targeting a cap-capable source.
2. Inject a YahooProvider that returns HTTP 200 with `marketCap` present for 3 symbols and absent for 2 symbols (e.g., `[{sym:"AAPL",cap:1T}, {sym:"MSFT",cap:2T}, {sym:"NOCAP",noMarketCap:null}, {sym:"NOMONEY",noMarketCap:null}, {sym:"GOOG",cap:1.5T}]`).
3. Run the expand job.
4. Query the resulting `universe.json` and the job message.

**Expected outcome:** The job completes with status `completed`; the 3 symbols with caps pass the screen (are in `universe.json`); the 2 capless symbols are recorded with the reason `no_market_cap` (a normal omission, not a systemic failure); the job message is a success summary (not a resumable pause).

**Pass criteria:** (1) Job status = `completed` (not `resumable`); (2) capless symbols recorded as `no_market_cap` omission; (3) job message does not indicate a systemic failure.

---

### TC-07 — Resume after systemic-failure pause executes zero duplicate provider calls

**Type:** api  
**Preconditions:** A previous expand-universe job is paused-resumable due to systemic 401. The durable checkpoint is stored in `import_checkpoints`. Backend is restarted.

**Steps:**
1. Query the `import_checkpoints` table to confirm the checkpoint is durable (contains the paused-expand checkpoint).
2. Restart the backend to verify the checkpoint survives.
3. Trigger a Resume action on the paused expand job via the API (or UI if frontend-testable).
4. Inject a counting-provider (or a mock that tracks all calls) for the resumed expand.
5. Run the resume-expand orchestration.
6. Count the total number of provider calls made during resume.

**Expected outcome:** The resume continues from the durable checkpoint with ZERO additional provider calls for the OHLCV fetch (already completed in the first run); the market-cap screen step re-runs from the checkpoint with only the cap-provider calls needed for retry (the cookie/crumb/quote calls for the batch, not re-fetching symbols).

**Pass criteria:** (1) Checkpoint is durable across restart; (2) resume executes only the skipped screen stage, not the completed fetch; (3) total provider calls during resume = only the cap-retry calls (not the OHLCV fetch re-run).

---

### TC-08 — Crumb/cookie never leak into errors, messages, or API responses

**Type:** api  
**Preconditions:** Backend is running; an expand-universe job is executed with real or injected YahooProvider (no mocks that hide the crumb).

**Steps:**
1. Start a backend with a YahooProvider that will make real/injected requests (ensure the crumb value would be captured if leaked).
2. Trigger an expand-universe job (can be with injected provider that raises an error mid-batch).
3. Capture the HTTP response from `GET /api/data/jobs/{id}` (the job-status endpoint).
4. Capture the DB row from `data_provider_runs`.
5. Grep the job status response JSON for any crumb-like value (a ~32-character alphanumeric from Yahoo's `/v1/test/getcrumb`).
6. Grep the `errors[]` array in the response and the job `message` field for any credential/token/crumb value.

**Expected outcome:** No crumb, cookie, or auth credential appears in the job-status response, the job message, or the `errors[]` array. All URLs in error messages are redacted (e.g., `GET /v7/finance/quote?...` with no param values shown).

**Pass criteria:** Grep of job-status response, `data_provider_runs.message`, `data_provider_runs.errors`, and any logged error strings returns zero matches for the crumb value (or any bearer/auth token).

---

### TC-09 — Expand-universe job card renders resumable state with operator message on /data

**Type:** browser  
**Preconditions:** Frontend is running at localhost:3835; backend is running at localhost:8835; a paused-resumable expand-universe job exists in the DB.

**Steps:**
1. Navigate to `http://localhost:3835/data` (the Data Manager home).
2. Locate the Unfinished-imports section.
3. Find the paused expand-universe job row.
4. Verify the job row displays a `resumable` state indicator (e.g., amber badge or "Resumable" label).
5. Verify the job message text is visible and contains "auth failed" or similar.
6. Verify a Resume button or link is present on the job row.

**Expected outcome:** The resumable job is visibly displayed with its honest operator message (not a silent "0 members" success or an error state); the Resume affordance is present.

**Pass criteria:** (1) Job row shows `resumable` state; (2) operator message visible; (3) Resume button/link clickable.

---

### TC-10 — Resume button on paused expand job triggers resume action and continues fetch

**Type:** browser  
**Preconditions:** Frontend and backend running; a paused expand-universe job in the Unfinished-imports panel.

**Steps:**
1. Navigate to `/data`.
2. Locate the paused expand job row.
3. Click the Resume button.
4. Wait for the job to complete (or reach a terminal state).
5. Verify the job status updates from `resumable` to the final state (e.g., `completed` or another terminal).
6. Verify the Unfinished-imports panel updates to reflect the new job state.

**Expected outcome:** The Resume action triggers the backend resume endpoint; the job transitions from `resumable` to a terminal state; the UI updates.

**Pass criteria:** (1) Resume button initiates a request; (2) job status changes; (3) Unfinished-imports panel re-renders with the new state.

---

### TC-11 — Required-still-passing: J-35 (expand source capability check) unchanged

**Type:** api  
**Preconditions:** Backend is running.

**Steps:**
1. Call `GET /api/data/import-sources` to list available import sources.
2. Identify the Yahoo/market-cap-capable source in the response.
3. Call `POST /api/data/jobs/expand` with the Yahoo source.
4. Verify the request succeeds (no 4xx error blocking the expand).

**Expected outcome:** The Yahoo source is available; the expand endpoint accepts it without an `unsupported_market_cap` rejection.

**Pass criteria:** Expand job can be queued against the Yahoo source without a 4xx rejection (J-35 check unchanged).

---

### TC-12 — Required-still-passing: J-38 (Unfinished-imports surface) shows the paused job

**Type:** browser  
**Preconditions:** Frontend and backend running; a paused-resumable expand job exists.

**Steps:**
1. Navigate to `/data`.
2. Verify the Unfinished-imports section exists and is visible.
3. Verify the paused expand job appears in the Unfinished-imports list.
4. Verify the job carries a Resume affordance (button/link).

**Expected outcome:** The Unfinished-imports section renders the paused job with the Resume control, unchanged from J-38.

**Pass criteria:** (1) Unfinished-imports panel visible; (2) paused job listed; (3) Resume control present.

---

### TC-13 — Required-still-passing: J-59 (stage-resumable checkpoint) survives restart

**Type:** api  
**Preconditions:** A completed-fetch, paused-screen expand job exists with a durable checkpoint. Backend is restarted.

**Steps:**
1. Query `import_checkpoints` to note the checkpoint row and its fields.
2. Stop and restart the backend.
3. Query `import_checkpoints` again for the same job ID.
4. Verify the checkpoint row is unchanged.

**Expected outcome:** The checkpoint is durable; the stage markers (fetch completed, screen paused) are preserved across restart.

**Pass criteria:** `import_checkpoints` row is identical before and after restart.

---

### TC-14 — Required-still-passing: J-18 (single date selector) — import/expand dates are job params, not a second date state

**Type:** browser  
**Preconditions:** Frontend and backend running; a date-scoped expand job can be created via the Data Manager form.

**Steps:**
1. Navigate to `/data`.
2. Verify the Data Manager form has a date/date-range input for the expand job (NOT a second as-of date picker).
3. Verify the top-bar global as-of switcher is independent of the job form date.
4. Create an expand job for a specific date range via the form.
5. Change the global as-of switcher to a different date.
6. Verify the job date remains unchanged; the global as-of is a separate state.

**Expected outcome:** The expand form's date input is a job parameter; the global as-of is a separate, independent control. Both coexist without interference.

**Pass criteria:** (1) Expand form date input is present; (2) global as-of switcher is independent; (3) changing as-of does not affect the job date.

---

### TC-15 — Backend boots cleanly and Ready after J-84 changes (J-40 / J-41)

**Type:** api  
**Preconditions:** Backend source code has J-84 changes (cookie+crumb auth, systemic-failure classification).

**Steps:**
1. Stop any running backend.
2. Start the backend fresh (cold boot) with `uvicorn --port 8835`.
3. Wait for the server to report Ready (or similar).
4. Call `GET /api/health` to confirm the backend is reachable.
5. Call `GET /api/data` (the Data Manager endpoint) to verify core functionality.

**Expected outcome:** Backend boots without errors; responds to health and data endpoints; no crashed lifespan or failed warm-up.

**Pass criteria:** (1) Backend starts and reports Ready status; (2) health endpoint returns 200; (3) data endpoint returns 200 with expected payload shape.

---

## Summary

**Total test cases:** 15  
**API tests:** 11 (TC-01 through TC-08, TC-11, TC-13, TC-15)  
**Browser tests:** 4 (TC-09, TC-10, TC-12, TC-14)  
**Artifact checks:** 0

**Coverage:**
- Cookie+crumb acquisition and reuse (TC-01)
- Honest per-candidate omissions (TC-02)
- Error redaction on parse failure (TC-03)
- Systemic 401 → resumable pause (TC-04)
- Systemic 429 → resumable pause (TC-05)
- Per-candidate absent cap ≠ systemic failure (TC-06)
- Resume zero-duplicate fetch (TC-07)
- Secret non-leakage in errors/messages/API (TC-08)
- UI rendering of resumable state and operator message (TC-09)
- Resume action triggers continuation (TC-10)
- Required-still-passing journeys: J-35 (source check), J-38 (Unfinished-imports), J-59 (durable checkpoint), J-18 (single date selector), J-40/J-41 (boot readiness)
