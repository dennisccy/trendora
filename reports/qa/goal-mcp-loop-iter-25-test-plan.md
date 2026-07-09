# goal-mcp-loop-iter-25 Functional Test Plan

**Phase:** goal-mcp-loop-iter-25  
**Date:** 2026-07-09  
**Frontend Present:** yes

## Phase Goal

Verify the `mmap_size_bytes: 0` SQLite fix eliminates the iter-24 cold-load OOM crash on `/api/data`, restoring J-13 (Data Manager reliable on cold start) and passing J-15 (core pages/APIs stay fast, cold path ≤60s without OOM under 6144 MB cap), with anti-goal #8 confirmed upheld.

## Test Cases

### TC-01 — Cold-path cold-start OOM fix (crux)

**Type:** browser  
**Preconditions:** Backend service stopped; frontend running on prod build (`.next` rebuilt); both services HTTP-200 confirmed before test; `mmap_size_bytes: 0` verified in config.yaml:108.

**Steps:**
1. Stop the backend service completely (kill uvicorn process).
2. Wait 2 seconds for full shutdown.
3. Start backend from cold (no in-memory cache): `scripts/start-backend.sh`.
4. Navigate to `/data` in the browser as the FIRST request after backend boot (do not visit any other page first).
5. Observe: page loads without backend crash, no blank application-error page, no "Out of memory" message.
6. Repeat steps 1–5 at least once more.
7. Confirm the backend process stays alive in both runs (check `ps aux | grep uvicorn`).

**Expected outcome:** Backend does NOT OOM/crash on cold `/api/data` prefill. `/data` page renders with storage card, availability heatmap, and missing-data diagnostics visible. No blank error page.

**Pass criteria:** Cold `/data` load succeeds ≥2 consecutive times; backend process alive after each; `/data` page fully rendered (not blank, not generic error boundary); no "MemoryError" or "ulimit" messages in backend logs.

---

### TC-02 — Storage card values match API payload

**Type:** api + browser  
**Preconditions:** Backend running in prod mode; `/data` page loaded successfully (from TC-01).

**Steps:**
1. Call `curl -s http://localhost:8255/api/data | jq '.capacity'` to get the backend's capacity payload.
2. Record the numeric values (e.g., `capacity_bytes`, `used_bytes`, `percent_used`).
3. On the `/data` page in the browser, locate the storage-footprint card.
4. Read the displayed values from the card's text/legend.
5. Compare the two sets: API payload vs rendered card values.

**Expected outcome:** Storage card's displayed numbers byte-match the `GET /api/data` `capacity` payload exactly (same units, precision, no rounding).

**Pass criteria:** Every value in the card (total capacity, used bytes, percent used) matches the API response verbatim. No off-by-one, no rounding, no unit conversion mismatch.

---

### TC-03 — Per-date availability legend clarified

**Type:** browser  
**Preconditions:** Backend running; `/data` page loaded.

**Steps:**
1. Locate the "Per-date availability" heatmap on `/data`.
2. Identify the legend below or beside the heatmap.
3. Verify the legend separates TWO distinct signals: (a) cell FILL = price-data completeness, (b) snapshot indicator = scored-scan exists.
4. Hover over a cell with green fill but NO snapshot ring/badge (a backfill gap).
5. Verify the tooltip explains: "bars stored, but no scored snapshot for this date" or similar plain language.
6. Hover over a cell with both fill and snapshot indicator.
7. Verify the tooltip explains both are present.

**Expected outcome:** Legend clearly labels the two orthogonal signals without visual collision. Tooltips explain the Fetch→fills / Backfill→scores workflow.

**Pass criteria:** Legend has two distinct visual regions (e.g., labeled "Price data — cell fill" and "Scored snapshot — indicator"). Tooltip on a backfill gap clearly states the absence of a snapshot. No ambiguity that fill and snapshot mean the same thing.

---

### TC-04 — Missing-data diagnostic card renders on unreachable backend

**Type:** browser  
**Preconditions:** Backend service stopped; frontend running in prod.

**Steps:**
1. Stop the backend service completely.
2. Wait 2 seconds.
3. In the browser, navigate directly to `/data`.
4. Observe the page render.

**Expected outcome:** Page does NOT show a blank application-error page or white screen. Instead, a single contained error card appears, explaining the backend is unreachable and offering a retry option or status link.

**Pass criteria:** Exactly one error card rendered (not generic Error Boundary crash page). Card text includes a diagnostic message (e.g., "Data Manager unavailable — backend is not responding"). Card remains in-bounds and styled consistently with the rest of the app. No JavaScript exceptions in browser console.

---

### TC-05 — J-03 `/stocks` + `/evidence` "Not yet proven" workflow

**Type:** browser  
**Preconditions:** Backend running; all services HTTP-200.

**Steps:**
1. Navigate to `/stocks` leaderboard.
2. Locate a row with a score that displays "Not yet proven" badge or label.
3. Click the badge/label to expand or drill into the evidence detail.
4. Verify the detail panel explains: "This signal has not yet passed out-of-sample validation."
5. Navigate to `/evidence` ledger page.
6. Observe that no unproven claims appear as "Proven" (all unproven edges labeled "Not yet proven" or absent).

**Expected outcome:** Unproven signals are clearly marked "Not yet proven," not presented as confident numbers. The evidence ledger contains only certified (PASS) claims, never unvalidated ones.

**Pass criteria:** Badge/label text reads "Not yet proven" or equivalent. No score lacking an evidence status. `/evidence` ledger rows show only claims with explicit PASS verdicts or marked "Not yet proven" if provisional.

---

### TC-06 — J-04 Evidence ledger and regime labeling

**Type:** browser  
**Preconditions:** Backend running; evidence data available (at least one certified claim in ledger).

**Steps:**
1. Navigate to `/evidence`.
2. Observe the ledger table: hypothesis, out-of-sample verdict, control comparison, registration date, forward-walk score-to-date.
3. For each row, verify the hypothesis includes the regime it applies to (if regime-conditioned) or is labeled broadly (if universal).
4. Click a row to view the detail or drill back to the research lab that it backs.
5. Verify the linkback reaches the correct research page.

**Expected outcome:** Every claim row is scoped to a regime (or marked universal) and links back to its backing surface (Research lab / factor page).

**Pass criteria:** All rows in `/evidence` include a clear hypothesis + regime label. At least one linkback successfully navigates to a research lab. No broken links or regime-confused claims.

---

### TC-07 — J-05 Audit evidence ledger row fields

**Type:** artifact + browser  
**Preconditions:** Backend running; `/evidence` page loads.

**Steps:**
1. On `/evidence`, count the table columns: hypothesis, out-of-sample verdict, control comparison, registration date, forward-walk score-to-date, linkback.
2. Pick one row and expand/click it to verify all six fields are populated (no empty cells, no "—" for critical fields).
3. Cross-check the out-of-sample verdict value (e.g., "p = 0.0042") against `GET /api/evidence` response for the same claim id.
4. Verify the forward-walk score matches the ledger payload.

**Expected outcome:** All six fields present and populated. Values byte-match the API payload.

**Pass criteria:** Row has exactly six columns, all non-empty. Out-of-sample verdict and forward-walk scores match the API response verbatim. No "null" or missing fields.

---

### TC-08 — J-10 Deep history data availability (AAPL/MSFT/NVDA)

**Type:** browser  
**Preconditions:** Backend running; deep 30-year seed loaded.

**Steps:**
1. Navigate to `/stocks`.
2. Click on a long-tenured stock (AAPL, MSFT, or NVDA).
3. Locate the price chart on the stock detail page.
4. Verify the chart's earliest date is before 2015 (ideally 1996 or the stock's real IPO date).
5. Toggle the "Full history" or similar option if available.
6. Verify the chart renders the full depth without crashing or truncating.
7. Open the `/backtest` view for the same stock and verify the as-of window shows deep history dates.

**Expected outcome:** Chart and backtest show price history spanning 20+ years, not just the old ~5-year floor. AAPL/MSFT show history back to the 1990s; NVDA to early 2000s.

**Pass criteria:** Chart earliest date ≤ 2000 for old names. Full history toggle expands the window without crash. Backtest as-of selector includes dates ≤ 2000.

---

### TC-09 — J-12 Point-in-time universe membership (IPO'd and delisted names)

**Type:** browser + api  
**Preconditions:** Backend running; 548-name pool loaded.

**Steps:**
1. On `/stocks` leaderboard, search for or locate ARM (IPO'd 2023), a post-2020 entry.
2. Verify ARM is ABSENT from the leaderboard on dates before its IPO (e.g., 2020-01-01).
3. Backtest to a date after ARM's IPO (e.g., 2023-10-01) and verify ARM now appears.
4. For a stock with short history (e.g., one that delisted or has limited data), verify it exits cleanly from the leaderboard when its data ends (no misaligned scores, no NaN forward returns).
5. Call `curl -s 'http://localhost:8255/api/stocks?as_of=2020-01-01' | jq '.stocks | length'` and verify it does NOT exceed the number of available names on that date (honest membership count).

**Expected outcome:** ARM absent 2020–2023, present post-IPO. Delisted/short-history names exit cleanly. Membership count honest (no fabricated entries).

**Pass criteria:** ARM not in 2020-01-01 leaderboard, present in 2023-10-01. No NaN scores for ending-data names. API `stocks` count ≤ universe membership on that date.

---

### TC-10 — J-13 `/data` storage card reflects 548-symbol pool

**Type:** browser + api  
**Preconditions:** Backend running; `/data` loaded after cold start (TC-01).

**Steps:**
1. On `/data`, inspect the storage-footprint card.
2. Note the total symbols referenced (e.g., "548 symbols in pool").
3. Call `curl -s http://localhost:8255/api/data/availability | jq '.total_symbols'` to get the backend's count.
4. Verify the two numbers match: card displays 548 (or the committed pool size), API returns the same.
5. Verify the "Expand universe" job option is ABSENT from the Data Manager job form (it was removed per the spec).

**Expected outcome:** Card and API both report 548 total symbols. "Expand universe" option not visible in the job form.

**Pass criteria:** Storage card and API payload show identical symbol count (548 or committed pool size). Job form's symbol-source options do NOT include "Expand universe" button/option.

---

### TC-11 — J-14 Index/macro context vendor disclosure

**Type:** browser  
**Preconditions:** Backend running; dashboard or research page with deep history context loaded.

**Steps:**
1. Navigate to the Dashboard or a research lab showing regime/benchmark charts.
2. Locate the SPX (equity benchmark) and VIX (volatility index) on the chart or in the page.
3. Verify each series is labeled with its vendor (e.g., "SPX (Stooq)" or "VIX (Yahoo)").
4. Spot-check the chart's earliest date (should be ~1996 for SPX, matching the deep seed).
5. For TNX/DXY/VXN (macro proxies), verify they are labeled as proxies or macro series (not as market indices).

**Expected outcome:** Every external data series discloses its vendor. No vendor-spliced discontinuity. Proxies labeled as such, never as market indices.

**Pass criteria:** Each series on the page includes vendor label in the legend or tooltip. Earliest date matches the 30-year seed (≤2000). Macro proxies labeled "Proxy" or "Macro" in the legend.

---

### TC-12 — J-15 Perf budget — cold `/api/data` ≤60s without OOM

**Type:** browser + api  
**Preconditions:** Backend running in prod mode; no prior requests to warm the cache; 6144 MB ulimit `-v` cap enforced.

**Steps:**
1. Stop the backend service.
2. Clear any in-process cache (system level if applicable).
3. Start the backend from cold.
4. Using `time` command, measure the wall-clock time for: `curl -s 'http://localhost:8255/api/data' > /dev/null`.
5. Record the elapsed time and the backend's peak memory (from `top` or `/proc` during the call).
6. Repeat 2–3 times to confirm consistency.
7. Verify no "Out of memory" or "MemoryError" messages in logs.
8. Record the measurement in the test report.

**Expected outcome:** Cold `/api/data` completes in ≤60 seconds. Peak memory does not exceed 6144 MB (the server's ulimit). Backend stays alive throughout.

**Pass criteria:** Measured cold-start time ≤60 s. Backend peak memory ≤6144 MB. No OOM crash or MemoryError. Measurement logged for `reports/perf-budgets.md`.

---

### TC-13 — J-15 Perf budget — warm endpoints still fast

**Type:** api  
**Preconditions:** Backend running in prod mode; services warm (at least one full request to each endpoint).

**Steps:**
1. Warm the backend by calling each endpoint once:
   - `curl -s http://localhost:8255/api/stocks`
   - `curl -s http://localhost:8255/api/stocks/AAPL`
   - `curl -s http://localhost:8255/api/data`
   - `curl -s http://localhost:8255/api/health`
2. Wait 5 seconds for caches to settle.
3. Time each endpoint (warm run) using `curl -w "@<(echo -e 'Time: %{time_total}s')"`:
   - `/api/stocks` — expect ≤ 1.5 s
   - `/api/stocks/AAPL` — expect ≤ 0.3 s
   - `/api/data` — expect ≤ 1.5 s
   - `/api/health` — expect ≤ 0.1 s
4. Record all measurements.

**Expected outcome:** All warm-request latencies within budgeted bounds.

**Pass criteria:** `/api/stocks` ≤1.5s, `/api/stocks/AAPL` ≤0.3s, `/api/data` ≤1.5s, `/api/health` ≤0.1s (all warm, all ≤ target).

---

### TC-14 — Byte-identity test suite still green (regression check)

**Type:** api  
**Preconditions:** Backend running; test environment set up.

**Steps:**
1. Run the byte-identity test suite (do NOT edit): `pytest tests/test_bar_cache.py -v`.
2. Run: `pytest tests/test_api_engine.py::test_filtered_stock_rows_byte_identical_to_full_scan_row -v`.
3. Run: `pytest tests/test_health.py -v` (readiness-equivalence).
4. Run: `pytest tests/test_data_manager.py -v` (diagnostic query-count independence).
5. Record the exit code and test count (X passed, Y failed).

**Expected outcome:** All four test modules pass with no edits to their assertion logic (proof the fix did not drift values).

**Pass criteria:** Exit code 0 for all four test runs. No test assertion logic was changed. Total passed ≥ expected baseline count.

---

### TC-15 — Config.yaml `mmap_size_bytes: 0` present at line 108

**Type:** artifact  
**Preconditions:** None (verification at run start).

**Steps:**
1. Read `config.yaml` line 108.
2. Verify the line contains `mmap_size_bytes: 0` (or `mmap_size_bytes` with value 0).
3. Check that no other SQLite mmap or connection-pool settings have been re-tuned (pool_size, max_overflow, cache_size, memory_cap_mb must remain unchanged).

**Expected outcome:** `mmap_size_bytes: 0` is present and unchanged. No other pool/pragma tuning.

**Pass criteria:** Line 108 reads `mmap_size_bytes: 0` exactly. `grep "pool_size\|max_overflow\|cache_size\|memory_cap_mb" config.yaml` returns unchanged historical values (no new edits).

---

## Summary

**Total test cases:** 15  
**Browser tests:** 9 (TC-01, TC-03, TC-04, TC-05, TC-06, TC-07, TC-08, TC-09, TC-11)  
**API tests:** 5 (TC-02, TC-12, TC-13, TC-14, TC-13)  
**Artifact checks:** 2 (TC-10, TC-15)

**Key focus areas:**
- **Cold-load OOM recovery** (TC-01, TC-12): The crux of iter-25; verifies the fix works LIVE.
- **Storage & availability card correctness** (TC-02, TC-03, TC-10): UI reflects accurate backend state.
- **Error boundary compliance** (TC-04): Anti-goal #8 upheld (no blank crash page).
- **Evidence ledger & journey workflows** (TC-05, TC-06, TC-07): J-03, J-04, J-05 integration points.
- **Deep 30-year data availability** (TC-08, TC-09, TC-11): J-10, J-12, J-14 confirm broad pool loaded.
- **Perf budget maintenance** (TC-12, TC-13): J-15 acceptance; cold ≤60s, warm budgets hold.
- **Regression proof** (TC-14): Byte-identity suite unedited and green.
- **Config integrity** (TC-15): Fix is in-tree and stable.

All tests are reproducible, specific, and map directly to the spec's Definition of Done and journey acceptance criteria.
