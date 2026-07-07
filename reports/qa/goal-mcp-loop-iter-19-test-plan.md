# goal-mcp-loop-iter-19 Functional Test Plan

**Phase:** goal-mcp-loop-iter-19
**Date:** 2026-07-07
**Frontend Present:** yes

## Phase Goal

Fix the `/stocks` leaderboard crash on Sector-sort with broadened 30-year universe (~78% null sectors), fix the backend `/api/data` prefill OOM that hangs under concurrent load, add crash containment, and verify end-to-end via browser QA.

## Test Cases

### TC-01 — Stocks leaderboard sort by Sector (ascending)

**Type:** browser
**Preconditions:** 
- Frontend running at http://localhost:3000
- Backend running at http://localhost:8000
- `/stocks` page loads without error
- Default leaderboard shows ~2000+ rows with mixed null and non-null sector values

**Steps:**
1. Navigate to `/stocks`
2. Click the "Sector" column header to sort ascending
3. Verify the page does not crash and sidebar nav remains visible
4. Verify rows are sorted with null-sector rows grouped together (empty string sorts first)

**Expected outcome:** Leaderboard sorts by Sector without throwing; nav intact; rows render correctly
**Pass criteria:** No application error; nav sidebar visible; sorted rows display correctly; MD5 of screenshot matches expected hash

---

### TC-02 — Stocks leaderboard sort by Sector (descending)

**Type:** browser
**Preconditions:** 
- Frontend running at http://localhost:3000
- Backend running at http://localhost:8000
- Previous TC-01 passed or leaderboard in initial state
- Sector column has been sorted once

**Steps:**
1. On `/stocks` leaderboard, click Sector column header again to reverse sort (descending)
2. Verify page does not crash and nav remains visible
3. Verify rows are now sorted in reverse order

**Expected outcome:** Leaderboard re-sorts descending without crashing; nav intact; rows render in reverse
**Pass criteria:** No error thrown; nav visible; MD5 of screenshot is distinct from TC-01 (descending order)

---

### TC-03 — Stocks leaderboard filter by "Unassigned" sector

**Type:** browser
**Preconditions:**
- Frontend running at http://localhost:3000
- Backend running at http://localhost:8000
- `/stocks` page loaded
- Sector filter dropdown present in UI

**Steps:**
1. Locate the Sector filter dropdown
2. Open dropdown and verify "Unassigned" option exists (not a null/blank entry)
3. Select "Unassigned" from dropdown
4. Verify leaderboard filters to show only rows with null sector

**Expected outcome:** Filter dropdown displays "Unassigned" label; filtering works; only null-sector rows display
**Pass criteria:** "Unassigned" option present and selectable; filtered rows show only null sector entries; no errors

---

### TC-04 — Evidence badge visible on every leaderboard row

**Type:** browser
**Preconditions:**
- Frontend running at http://localhost:3000
- Backend running at http://localhost:8000
- `/stocks` page loaded with default sort
- At least 10 rows visible on screen

**Steps:**
1. Navigate to `/stocks` 
2. Scroll to first 10 visible rows
3. For each row, inspect for evidence status badge (either "Proven" or "Not yet proven")
4. Verify no score cell lacks a badge

**Expected outcome:** Every visible row displays an evidence status badge
**Pass criteria:** All visible rows contain evidence badge; no row missing status indicator; badges readable

---

### TC-05 — /api/data cold-path completes without OOM

**Type:** api
**Preconditions:**
- Backend running with 6144 MB memory cap (`server.memory_cap_mb`)
- No prior `/api/data` calls in this session (cold cache)
- Backend process memory monitored (baseline before call)

**Steps:**
1. Invoke `curl -s http://localhost:8000/api/data | jq length` (cold `/api/data` endpoint)
2. Monitor backend process RSS memory during execution
3. Verify call completes successfully with HTTP 200
4. Verify response contains expected `availability`, `snapshots`, `stale_series` fields

**Expected outcome:** 
- Cold `/api/data` completes ≤ 60 s without OOM
- Response HTTP 200 with valid JSON structure
- Peak memory footprint ~0.4–0.5 GB (vs prior ~3+ GB)

**Pass criteria:** 
- Exit code 0; HTTP 200 status
- Response contains `{"availability": {...}, "snapshots": [...], "stale_series": [...]}`
- No timeout; no "MemoryError" in backend logs
- Peak RSS ≤ 6144 MB

---

### TC-06 — Concurrent /api/data probes serialize correctly

**Type:** api
**Preconditions:**
- Backend running with 6144 MB memory cap
- No prior `/api/data` cache warm
- Server in clean state

**Steps:**
1. Launch 6 concurrent `curl` requests to `http://localhost:8000/api/data` (e.g., `for i in {1..6}; do curl -s http://localhost:8000/api/data > /dev/null & done; wait`)
2. Monitor backend logs for evidence of concurrent `compute_coverage` calls
3. Verify all 6 requests complete successfully
4. Verify backend memory remains ≤ 6144 MB throughout

**Expected outcome:**
- All 6 concurrent requests succeed (HTTP 200)
- Only 1 `_compute_coverage_uncached` prefill runs (serialized via single-flight)
- No OOM; backend remains responsive

**Pass criteria:**
- All 6 requests return HTTP 200
- Backend logs show ≤1 concurrent prefill event
- No "MemoryError"; peak RSS ≤ 6144 MB

---

### TC-07 — /stocks/{ticker} Full-history chart byte-identical bars

**Type:** browser
**Preconditions:**
- Frontend running at http://localhost:3000
- Backend running at http://localhost:8000
- `/stocks/AAPL` page loaded

**Steps:**
1. Navigate to `/stocks/AAPL`
2. Locate the Full-history chart (price chart spanning deepest available history)
3. Toggle to "Full history" mode
4. Capture chart data via browser DevTools or API call to `GET /api/stocks/AAPL/bars?interval=...`
5. Compare returned bar values (open, close, high, low, volume) against a known golden/reference snapshot

**Expected outcome:** Chart renders and bar data matches pre-test golden values exactly (byte-identical)
**Pass criteria:** 
- Chart displays without error
- For any bar `date, close, high, low, open, volume` matches golden snapshot exactly (no rounding drift)
- MD5 of JSON bars response = expected hash

---

### TC-08 — /methodology membership timeline entries/exits

**Type:** browser
**Preconditions:**
- Frontend running at http://localhost:3000
- Backend running at http://localhost:8000
- `/methodology` page accessible

**Steps:**
1. Navigate to `/methodology`
2. Locate membership timeline or entry/exit history (showing dates names entered/left universe)
3. Pick a known mid-history IPO name (e.g., ARM or a name IPO'd 2009-2020)
4. Verify the name is ABSENT from timeline before its IPO date
5. Verify the name is PRESENT from on/after its IPO date
6. Scroll timeline forward to verify no fabricated pre-IPO entries

**Expected outcome:** 
- Timeline shows point-in-time accurate entry/exit dates
- No pre-IPO entries for names verified to have IPO'd mid-history
- Exit dates align with data end or membership rule changes

**Pass criteria:**
- Mid-history-IPO name absent in all pre-IPO dates
- Entry date matches known IPO date (±1 day for weekend/market-close variance)
- MD5 of timeline capture distinct and correctly labeled

---

### TC-09 — /data stale_series card visible and in-frame

**Type:** browser
**Preconditions:**
- Frontend running at http://localhost:3000
- Backend running at http://localhost:8000
- `/data` page loaded

**Steps:**
1. Navigate to `/data`
2. Locate the "stale_series" or "data staleness" reason card
3. Scroll element into viewport (if not initially visible)
4. Capture screenshot showing card in frame with readable text
5. Verify card displays reason for stale series (e.g., "Last bar >X days old")

**Expected outcome:** 
- Card is rendered and scrollable-to or full-page visible
- Card displays readable staleness reason
- Card is not clipped or hidden behind other UI

**Pass criteria:**
- Card element found in DOM
- Screenshot MD5 confirms element in-frame (not blank ~5855-byte frame)
- Readable text present in card

---

### TC-10 — Uncaught client error renders contained error card with nav preserved

**Type:** browser
**Preconditions:**
- Frontend running at http://localhost:3000
- Error boundary files (`error.tsx`, `global-error.tsx`) present in codebase
- ability to trigger an uncaught error (e.g., a malformed API response or forced JS error)

**Steps:**
1. Navigate to a page (e.g., `/stocks`)
2. Trigger an uncaught client error (e.g., inject a broken component state or network error via DevTools)
3. Verify page does not show blank "Application error" 
4. Verify an error card renders with readable error message
5. Verify sidebar nav remains visible and clickable

**Expected outcome:**
- Error card renders with informative message
- Sidebar nav remains visible and interactive
- No blank white page or completely wiped layout

**Pass criteria:**
- Error card present in DOM (not blank page)
- Nav sidebar rendered and not hidden
- Card text readable (not a generic browser error)
- Screenshot MD5 confirms distinct error layout

---

### TC-11 — Sector field type correctly nullable (TypeScript validation)

**Type:** artifact
**Preconditions:**
- TypeScript compilation successful (`tsc --noEmit` in `apps/frontend/`)
- `lib/api.ts` updated with `sector: string | null` type

**Steps:**
1. Run `cd apps/frontend && tsc --noEmit --noError`
2. Grep for all usages of `.sector` property across frontend codebase: `grep -r "\.sector" apps/frontend/`
3. For each usage found, verify it has a null-guard or uses the `??` operator
4. Verify no `.sector.localeCompare()` or `.sector.toUpperCase()` call without guard

**Expected outcome:**
- TypeScript compilation succeeds with no type errors
- Every `.sector` usage either:
  - Guards with `?.` optional chaining
  - Uses `??` null coalescing
  - Is inside a conditional check for non-null

**Pass criteria:**
- `tsc --noEmit` exit code 0
- No unguarded `.sector` method calls found via manual inspection
- Sector comparator in `stocks/page.tsx` reads `(a.sector ?? "").localeCompare(b.sector ?? "")`

---

### TC-12 — Bar prefill streaming returns byte-identical data

**Type:** api
**Preconditions:**
- Backend running
- `test_bar_cache.py` test file present and executable
- pytest available

**Steps:**
1. Run targeted test: `pytest tests/test_bar_cache.py::test_prefilled_cache_matches_direct_query -v`
2. Capture test output (PASS/FAIL + assertion details)
3. Verify test passes with zero failures

**Expected outcome:**
- Test runs and passes
- Streamed prefill returns identical rows and order as prior whole-table ORM load
- No data corruption or reordering from column-projection refactoring

**Pass criteria:**
- pytest exit code 0 (all assertions passed)
- Test log shows "PASSED"
- No assertion mismatch on symbol/date/OHLCV values

---

### TC-13 — Monkeypatch shims in test_bar_cache remain compatible

**Type:** artifact
**Preconditions:**
- `test_bar_cache.py` file exists
- Monkeypatch shims at lines ~91, ~102, ~256 present
- No breaking changes to `prefilled_bar_cache()` or `_BarCache.prefill()` signature

**Steps:**
1. Inspect `tests/test_bar_cache.py:91` — verify `prices._BarCache.bars_asof` monkeypatch call succeeds
2. Inspect `tests/test_bar_cache.py:102` — verify 2-arg `prefilled_bar_cache(session, expected_symbols=[...])` call succeeds
3. Inspect `tests/test_bar_cache.py:256` — verify monkeypatch call to `.prefill` succeeds
4. Run full `pytest tests/test_bar_cache.py` to confirm no signature-related errors

**Expected outcome:**
- All monkeypatch shims execute without AttributeError or TypeError
- Existing test structure preserved
- No required-parameter additions break shims

**Pass criteria:**
- `pytest tests/test_bar_cache.py` exit code 0
- No "TypeError: missing required argument" or "AttributeError" in test output
- All monkeypatch lines execute without exception

---

### TC-14 — Config comment updated for memory cap

**Type:** artifact
**Preconditions:**
- `config.yaml` file exists at repo root
- Line ~1183 contains `server.memory_cap_mb` setting

**Steps:**
1. Read `config.yaml` line 1183 (or search for `memory_cap_mb`)
2. Verify comment is updated from "~1.3M-row" to "~3.27M-row" (or similar accurate figure)
3. Verify cap value remains 6144 MB

**Expected outcome:**
- Comment accurately reflects current 3.27M daily_prices row count
- Cap unchanged at 6144 MB

**Pass criteria:**
- `grep -A 2 "memory_cap_mb" config.yaml` shows updated comment
- Memory cap: 6144 (not changed)

---

### TC-15 — Reports/perf-budgets.md measurement recorded

**Type:** artifact
**Preconditions:**
- `reports/perf-budgets.md` file exists (created if new)
- Cold `/api/data` latency measured
- Peak memory footprint captured

**Steps:**
1. Read `reports/perf-budgets.md`
2. Verify it contains an item-A entry with:
   - Cold `/api/data` latency (must be ≤ 60 s)
   - Retained memory footprint before/after comparison (~3+ GB → ~0.4–0.5 GB)
3. Verify numbers are realistic and not placeholder text

**Expected outcome:**
- Measurement table present with item-A row
- Cold path latency ≤ 60 s documented
- Memory improvement from ~3+ GB to ~0.4–0.5 GB recorded

**Pass criteria:**
- File contains item-A measurement entry
- Latency value ≤ 60 s and ≥ 1 s (realistic)
- Memory improvement >50% (3GB → 0.5GB is ~83% reduction)

---

### TC-16 — Dev handoff file created

**Type:** artifact
**Preconditions:**
- Iteration development complete
- Handoff path: `docs/handoffs/goal-mcp-loop-iter-19-dev.md`

**Steps:**
1. Verify file exists at `docs/handoffs/goal-mcp-loop-iter-19-dev.md`
2. Read file and confirm it documents:
   - Changes made (sector null-guard, OOM fix, error boundaries)
   - Files modified (frontend + backend locations)
   - Test coverage (unit + integration tests run, passed)
3. Verify file is not empty or placeholder

**Expected outcome:** Handoff file present with substantive content documenting iteration work
**Pass criteria:** File exists and contains >500 words of real content; all major changes documented

---

## Summary

**Total test cases:** 16

**By type:**
- Browser tests: 8 (TC-01, TC-02, TC-03, TC-04, TC-08, TC-09, TC-10)
- API tests: 2 (TC-05, TC-06)
- TypeScript/artifact validation: 6 (TC-07, TC-11, TC-12, TC-13, TC-14, TC-15, TC-16)

**Critical path (must pass for iteration success):**
- TC-01, TC-02, TC-03 (Sector sort/filter crash regression)
- TC-04 (Evidence badges present)
- TC-05, TC-06 (OOM fix + serialization)
- TC-10 (Error containment)
- TC-11, TC-12, TC-13 (Type safety + byte-identity)
