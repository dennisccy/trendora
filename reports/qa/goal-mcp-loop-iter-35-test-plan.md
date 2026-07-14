# goal-mcp-loop-iter-35 Functional Test Plan

**Phase:** goal-mcp-loop-iter-35
**Date:** 2026-07-14
**Frontend Present:** yes

## Phase Goal

When a live fetch re-adjusts a symbol's already-committed history, the platform detects the mismatch, records it in a drift report artifact, names the affected symbol and exact mismatching dates as an "adjustment seam," and degrades the daily preflight verdict to DEGRADED until the mismatch is resolved — so silently-corrupted boards can never be trusted.

## Test Cases

### TC-01 — Build drift report with re-adjusted overlap detects mismatch

**Type:** api
**Preconditions:** 
- Backend is running
- Seed CSV files exist at `data/seed/prices/{symbol}.csv` for test symbols
- Test fixture has constructed two bars arrays with the last N common dates where one has been re-adjusted

**Steps:**
1. Call `app.engine.drift:build_drift_report(fetched_bars, seed_bars, overlap_days=30, reference="2026-07-14T00:00:00Z")`
2. Pass `fetched_bars` with re-adjusted OHLCV in the overlap window (e.g., changed close price by 1%)
3. Pass `seed_bars` with original committed values

**Expected outcome:** 
- Returns dict with `status: "drift"`, `reference: "2026-07-14T00:00:00Z"`, `overlap_days: 30`
- `affected` array contains one entry for the test symbol
- Entry contains exact `mismatching_dates` list matching the fixture's re-adjusted dates
- Classification is `"adjustment_seam"`

**Pass criteria:** 
```
response["status"] == "drift"
and len(response["affected"]) == 1
and response["affected"][0]["symbol"] == expected_symbol
and response["affected"][0]["mismatching_dates"] == expected_dates
and response["affected"][0]["classification"] == "adjustment_seam"
```

---

### TC-02 — Build drift report with clean overlap returns clean status

**Type:** api
**Preconditions:**
- Backend is running
- Test fixture has two bars arrays with identical OHLCV over the last N common dates

**Steps:**
1. Call `app.engine.drift:build_drift_report(fetched_bars, seed_bars, overlap_days=30, reference="2026-07-14T00:00:00Z")`
2. Pass both arrays with byte-identical OHLCV in the overlap window

**Expected outcome:**
- Returns dict with `status: "clean"`, `reference: "2026-07-14T00:00:00Z"`, `overlap_days: 30`
- `affected` array is empty

**Pass criteria:**
```
response["status"] == "clean"
and response["affected"] == []
and response["overlap_days"] == 30
```

---

### TC-03 — Byte-precision compare catches re-adjustment loose float compare would miss

**Type:** api
**Preconditions:**
- Backend is running
- Test fixture has two bars arrays where overlap region differs by < 1 ULP (unit in last place) — e.g., close price 123.456000000001 vs 123.456000000002

**Steps:**
1. Call `app.engine.drift:build_drift_report(fetched_bars_loose_float, seed_bars, overlap_days=30, reference="2026-07-14T00:00:00Z")`
2. Verify that a loose float `==` compare (with tolerance) would NOT catch the difference
3. Verify the drift module's byte/fixed-precision compare DOES catch it

**Expected outcome:**
- Returns `status: "drift"` with the difference identified
- The affected mismatching dates include the dates where the precision difference exists

**Pass criteria:**
```
response["status"] == "drift"
and len(response["affected"]) > 0
and len(response["affected"][0]["mismatching_dates"]) > 0
```

---

### TC-04 — Read and write drift report round-trip

**Type:** api
**Preconditions:**
- Backend is running
- `TRENDORA_DRIFT_REPORT_PATH` or config `data_quality.drift.report_path` resolves correctly
- Temp directory is writable

**Steps:**
1. Create a drift report dict: `{"status": "drift", "reference": "2026-07-14T00:00:00Z", "overlap_days": 30, "affected": [{"symbol": "AAPL", "mismatching_dates": ["2026-07-10", "2026-07-11"], "classification": "adjustment_seam"}]}`
2. Call `app.engine.drift:write_drift_report(report)`
3. Call `app.engine.drift:read_drift_report()`
4. Compare the returned dict to the original

**Expected outcome:**
- Written file is valid JSON in the configured path
- Read dict matches the original exactly (all fields, values, and order)

**Pass criteria:**
```
read_report == written_report
and read_report["status"] == "drift"
and read_report["affected"][0]["symbol"] == "AAPL"
```

---

### TC-05 — Missing drift report file returns inert/clean state

**Type:** api
**Preconditions:**
- Backend is running
- Drift report file does not exist at `resolve_drift_report_path()`

**Steps:**
1. Call `app.engine.drift:read_drift_report()` when the report file is absent
2. Verify no exception is raised

**Expected outcome:**
- Returns `None` or an empty/inert dict representing "no drift artifact written yet"
- Caller can safely assume "clean" state

**Pass criteria:**
```
read_report is None or (isinstance(read_report, dict) and read_report.get("status") == "clean" or read_report == {})
and no exception raised
```

---

### TC-06 — Unparseable drift report returns honest degraded state, never crashes

**Type:** api
**Preconditions:**
- Backend is running
- Drift report file exists but contains invalid JSON or is corrupted

**Steps:**
1. Write malformed JSON to the drift report path (e.g., `{invalid`)
2. Call `app.engine.drift:read_drift_report()`
3. Verify no exception is raised and the error is handled gracefully

**Expected outcome:**
- Returns a dict with `status: "degraded"` or `status: "error"`, never raises exception
- Caller can log the degraded state and continue

**Pass criteria:**
```
read_report is not None
and read_report.get("status") in ("degraded", "error")
and no exception raised
```

---

### TC-07 — Drift report path honors env override

**Type:** api
**Preconditions:**
- Backend is running

**Steps:**
1. Set env var `TRENDORA_DRIFT_REPORT_PATH=/tmp/custom-drift.json`
2. Call `app.engine.drift:resolve_drift_report_path()`
3. Verify it returns the custom path

**Expected outcome:**
- Returns `/tmp/custom-drift.json`

**Pass criteria:**
```
resolve_drift_report_path() == "/tmp/custom-drift.json"
```

---

### TC-08 — Drift report path defaults to config and resolves REPO_ROOT

**Type:** api
**Preconditions:**
- Backend is running
- `TRENDORA_DRIFT_REPORT_PATH` env var is not set
- `config.data_quality.drift.report_path` is set to a repo-relative path like `runs/goal-session-mcp-loop/state/drift.json`

**Steps:**
1. Call `app.engine.drift:resolve_drift_report_path()`
2. Verify it resolves the path against `REPO_ROOT`

**Expected outcome:**
- Returns absolute path like `/home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/drift.json`

**Pass criteria:**
```
os.path.isabs(resolve_drift_report_path())
and resolve_drift_report_path().endswith("runs/goal-session-mcp-loop/state/drift.json")
```

---

### TC-09 — Compute preflight with clean/absent drift artifact leaves verdict GO unchanged

**Type:** api
**Preconditions:**
- Backend is running
- Drift report file is absent or contains `status: "clean"`
- Servability, freshness, integrity components are all `ok: true` with verdict GO

**Steps:**
1. Seed DB with minimal data (fresh state)
2. Do NOT run a fetch job (no drift artifact written)
3. Call `app.engine.readiness:compute_preflight()`
4. Inspect the result

**Expected outcome:**
- Preflight verdict is `GO`
- Reasons list is empty
- All four components (servability, freshness, integrity, drift) have `ok: true`
- Drift component detail is `None` or empty

**Pass criteria:**
```
preflight["verdict"] == "GO"
and preflight["reasons"] == []
and preflight["components"]["drift"]["ok"] == True
and preflight["components"]["drift"]["detail"] is None or preflight["components"]["drift"]["detail"] == ""
```

---

### TC-10 — Compute preflight with drift artifact status=drift forces DEGRADED

**Type:** api
**Preconditions:**
- Backend is running
- Drift report file contains `status: "drift"` with affected symbols
- Config `readiness.severity.drift` is set to `"degraded"`

**Steps:**
1. Write a drift report: `{"status": "drift", "affected": [{"symbol": "AAPL", "mismatching_dates": ["2026-07-10"], "classification": "adjustment_seam"}]}`
2. Call `app.engine.readiness:compute_preflight()`
3. Inspect the result

**Expected outcome:**
- Preflight verdict is `DEGRADED`
- Reasons list contains a string mentioning drift and the affected symbol "AAPL"
- Drift component has `ok: false`
- Detail field names the affected symbols

**Pass criteria:**
```
preflight["verdict"] == "DEGRADED"
and any("drift" in reason.lower() and "AAPL" in reason for reason in preflight["reasons"])
and preflight["components"]["drift"]["ok"] == False
and "AAPL" in preflight["components"]["drift"]["detail"]
```

---

### TC-11 — Fetch pipeline runs drift check post-fetch, not on resumable pause

**Type:** api
**Preconditions:**
- Backend is running
- Config data fetch is enabled
- A real or test fetch can be triggered

**Steps:**
1. Trigger a completed fetch job via `data_manager._run_job(job_spec, prog)`
2. Verify `prog.status != "resumable"` at the post-fetch stage
3. Inspect that `build_drift_report` was called and the artifact was written
4. Now trigger a resumable/paused fetch at the same point
5. Verify the drift check is NOT run (no second artifact write)

**Expected outcome:**
- On completed fetch: drift artifact exists with a valid report
- On resumable pause: no new drift artifact is written (or the timestamp is unchanged)

**Pass criteria:**
```
completed_fetch_has_drift_artifact == True
and resumable_pause_does_not_write_new_artifact == True
```

---

### TC-12 — GET /api/data returns additive drift field

**Type:** api
**Preconditions:**
- Backend is running
- `/api/data` endpoint is available
- Drift report artifact exists (or is absent)

**Steps:**
1. Call `curl -s http://localhost:8000/api/data | jq .drift`
2. Verify the response contains the `drift` field
3. If artifact exists, verify the field equals the read artifact exactly

**Expected outcome:**
- HTTP 200
- Response JSON contains `"drift"` key
- Value matches `read_drift_report()` verbatim

**Pass criteria:**
```
response.status_code == 200
and "drift" in response.json()
and response.json()["drift"] == read_drift_report()
```

---

### TC-13 — ReadinessCfg boot-time validation accepts drift component

**Type:** api
**Preconditions:**
- Backend is running
- Config YAML contains `readiness.severity.drift: degraded`

**Steps:**
1. Boot the application
2. Verify config loads without error
3. Inspect that `ReadinessCfg._validate` passes the `drift` component in `required_components`

**Expected outcome:**
- Application boots successfully
- Config validation does not raise an error

**Pass criteria:**
```
app_boots_successfully == True
and config.readiness.severity.get("drift") == "degraded"
```

---

### TC-14 — ReadinessCfg boot-time validation rejects config missing drift component

**Type:** api
**Preconditions:**
- Config YAML missing `readiness.severity.drift` entry

**Steps:**
1. Boot the application with incomplete config
2. Verify `ReadinessCfg._validate` catches the missing component

**Expected outcome:**
- Application boot fails with a clear config validation error
- Error message mentions `drift` is required in `readiness.severity`

**Pass criteria:**
```
boot_raises_config_error == True
and "drift" in error_message.lower()
```

---

### TC-15 — Browser: J-21 drift report displays on /data when status is clean

**Type:** browser
**Preconditions:**
- Frontend is running at http://localhost:3000
- Backend is running
- A fetch has completed with clean/no-drift status
- Drift report artifact exists with `status: "clean"`

**Steps:**
1. Navigate to http://localhost:3000/data
2. Scroll to the drift-report section
3. Verify the card is rendered with a clean/quiet state

**Expected outcome:**
- Drift report card is visible on `/data`
- Text indicates clean status (e.g., "No data drift detected" or similar)
- No affected-symbol list is shown
- Card uses neutral/quiet styling (no amber/warning colors)

**Pass criteria:**
- Card rendered and visible
- Status text is neutral and does not list affected symbols
- CSS classes do not include warning/error state

---

### TC-16 — Browser: J-21 drift report displays affected symbols when status is drift

**Type:** browser
**Preconditions:**
- Frontend is running at http://localhost:3000
- Backend is running
- A fetch has been artificially re-adjusted to create a drift condition
- Drift report artifact exists with `status: "drift"` and affected symbols

**Steps:**
1. Navigate to http://localhost:3000/data
2. Scroll to the drift-report section
3. Verify the card displays the affected symbol list with mismatching dates

**Expected outcome:**
- Drift report card is loud/amber (warning styling matching preflight banner's `DEGRADED` state)
- Lists each affected symbol (e.g., "AAPL")
- Each entry shows mismatching dates (e.g., "2026-07-10, 2026-07-11")
- Each entry is labeled "adjustment seam"

**Pass criteria:**
- Card rendered with warning styling
- Symbol "AAPL" (or test symbol) is visible
- Mismatching dates list is visible and matches the artifact

---

### TC-17 — Browser: Preflight banner reflects drift DEGRADED reason

**Type:** browser
**Preconditions:**
- Frontend is running at http://localhost:3000
- Drift report artifact exists with `status: "drift"` with affected symbols
- Preflight verdict is DEGRADED due to drift

**Steps:**
1. Visit any page (e.g., http://localhost:3000/stocks)
2. Observe the preflight banner at the top
3. Verify it reads DEGRADED
4. Verify the reasons list includes a mention of drift

**Expected outcome:**
- Banner status is DEGRADED (amber/warning color)
- Reasons include text like "drift detected on AAPL" or similar
- Banner is persistent across page navigation

**Pass criteria:**
- Banner class includes `DEGRADED` state
- Text includes both "drift" and the affected symbol name

---

### TC-18 — Browser: Preflight banner recovers to GO after clean fetch

**Type:** browser
**Preconditions:**
- Frontend is running at http://localhost:3000
- Preflight is currently DEGRADED due to drift
- A clean fetch is run (no re-adjustments in overlap)

**Steps:**
1. Observe the preflight banner reads DEGRADED
2. Trigger a new fetch job that completes cleanly (via backend data manager or test endpoint)
3. Refresh the browser or wait for automatic preflight re-compute (health poll)
4. Observe the preflight banner

**Expected outcome:**
- Banner status changes to GO
- Reasons list is empty
- Drift card on `/data` shows clean state

**Pass criteria:**
- Banner class includes `GO` state after refresh/poll
- Reasons list is empty
- Drift card text is neutral

---

### TC-19 — Browser: J-20 non-regression preflight banner still composes all four components correctly

**Type:** browser
**Preconditions:**
- Frontend is running at http://localhost:3000
- Backend is running
- Fresh seed state with no fetch run (drift artifact absent)

**Steps:**
1. Navigate to http://localhost:3000/stocks (or any page with preflight banner)
2. Observe the preflight banner
3. Verify all four component states (servability, freshness, integrity, drift)

**Expected outcome:**
- Banner reads GO
- Reasons list is empty
- All components are ok (internal verification via `/api/health`)

**Pass criteria:**
- Banner shows GO status
- No warnings or reasons in the banner

---

### TC-20 — Browser: J-13 /data page coverage section un-regressed

**Type:** browser
**Preconditions:**
- Frontend is running at http://localhost:3000
- Backend is running
- Seed data is loaded

**Steps:**
1. Navigate to http://localhost:3000/data
2. Scroll to the coverage/legend section (existing section before drift report card added)
3. Verify it renders correctly and displays coverage statistics

**Expected outcome:**
- Coverage section is rendered with no visual regressions
- Statistics (symbol count, etc.) are correct
- No layout shift or missing content

**Pass criteria:**
- Section rendered and styled correctly
- Statistics are present and accurate

---

### TC-21 — Browser: J-01 leaderboard evidence badges un-regressed

**Type:** browser
**Preconditions:**
- Frontend is running at http://localhost:3000
- Backend is running
- Evidence ledger is populated

**Steps:**
1. Navigate to http://localhost:3000/stocks
2. Observe the leaderboard rows
3. Verify each row displays an evidence badge (Proven or Not yet proven)

**Expected outcome:**
- Evidence badges are visible on every score
- No layout regressions in the leaderboard
- Badges display correct proven/not-yet-proven states

**Pass criteria:**
- At least one badge is visible
- Badges display correct evidence status

---

### TC-22 — Browser: J-05 evidence ledger page un-regressed

**Type:** browser
**Preconditions:**
- Frontend is running at http://localhost:3000
- Backend is running
- Evidence ledger data exists

**Steps:**
1. Navigate to http://localhost:3000/evidence (or the evidence ledger page)
2. Verify the page renders and displays ledger entries

**Expected outcome:**
- Page loads and displays certified claims
- No regressions in layout or data display
- Ledger is byte-identical to pre-iter-35 state (no new entries added this iteration)

**Pass criteria:**
- Page loads without error
- Ledger entries are rendered
- No new/unexpected entries visible

---

### TC-23 — API key is never written into drift artifact

**Type:** artifact
**Preconditions:**
- Backend is running
- A fetch has been completed with an API key in the session

**Steps:**
1. Trigger a fetch job with a test API key in the session
2. Read the written drift report artifact from disk
3. Search for the API key string in the artifact

**Expected outcome:**
- Drift artifact is valid JSON
- No occurrence of the API key or provider URL/query string
- Only immutable reference (timestamp, config values) is present

**Pass criteria:**
```
api_key not in artifact_contents
and provider_url not in artifact_contents
and artifact_is_valid_json == True
```

---

## Summary

Total test cases: 23
- API tests: 14 (TC-01 to TC-14)
- Browser tests: 8 (TC-15 to TC-22)
- Artifact checks: 1 (TC-23)

**Coverage by spec requirement:**

| Spec Element | Test Cases |
|--------------|-----------|
| `build_drift_report` — byte compare & fixture matrix | TC-01, TC-02, TC-03 |
| Path resolution & round-trip I/O | TC-04, TC-05, TC-06, TC-07, TC-08 |
| Preflight component integration | TC-09, TC-10, TC-13, TC-14 |
| Fetch pipeline wiring | TC-11 |
| `/api/data` additive field | TC-12 |
| `/data` drift report card (clean/drift states) | TC-15, TC-16 |
| Preflight banner drift reason | TC-17, TC-18 |
| J-20 non-regression (banner composition) | TC-19 |
| J-13 non-regression (/data coverage) | TC-20 |
| J-01 non-regression (leaderboard badges) | TC-21 |
| J-05 non-regression (evidence ledger) | TC-22 |
| Anti-goal #7 (no API key persisted) | TC-23 |
