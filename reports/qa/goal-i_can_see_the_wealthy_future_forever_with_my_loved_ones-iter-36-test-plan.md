# iter-36 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-36  
**Date:** 2026-06-19  
**Frontend Present:** no

## Phase Goal

Make `GET /api/data` responsive on the post-rebuild DB by caching the membership-timeline derivation — with zero change to any served value (byte-identity is a hard requirement). This restores the J-94 and J-96 surfaces on the `/data` page that regressed when data volume growth exposed a latent O(dates × pool) cost in the uncached timeline resolver.

## Test Cases

### TC-01 — Timed GET /api/data returns promptly on warm cache

**Type:** api  
**Preconditions:** Backend running on :8835 with post-rebuild DB; membership-timeline cache table exists and is populated (warm).

**Steps:**
1. Send `curl -w "%{time_total}\n" -o /dev/null -s http://localhost:8835/api/data`
2. Record the response time and HTTP status code

**Expected outcome:** Request completes within 5 seconds (normal budget); HTTP 200.

**Pass criteria:** `time_total` ≤ 5.0 seconds AND HTTP status = 200

---

### TC-02 — GET /api/data serves byte-identical membership_timeline on cache hit

**Type:** api  
**Preconditions:** Backend running; cache table populated with latest `_dataset_version` stamp; a fresh `_membership_timeline` computation is available for comparison.

**Steps:**
1. Send `curl -s http://localhost:8835/api/data`
2. Extract the `coverage.membership_timeline` field from the response JSON
3. Compute a fresh `_membership_timeline` from the current DB session (via test harness)
4. Deep-compare the cached payload to the fresh payload (field-by-field, including all nested `entries`, `exits`, `excluded_by_reason` per date)

**Expected outcome:** Cached payload is byte-identical (deep-equal) to the fresh computation.

**Pass criteria:** All nested fields of `membership_timeline` match exactly (no value differs, no array reordering).

---

### TC-03 — Membership-timeline cache invalidates on dataset version change

**Type:** api  
**Preconditions:** Backend running; cache table has a row keyed to version stamp V1; dataset changes (e.g. a new snapshot is added, triggering `_dataset_version` to return V2).

**Steps:**
1. Read the current `_dataset_version` stamp via test harness (returns V2)
2. Send `curl -s http://localhost:8835/api/data`
3. Verify the response contains a `membership_timeline` field
4. Confirm the query hit the NEW stamp (V2) and NOT the stale row (V1)
5. Verify the payload matches a fresh `_membership_timeline` compute against V2

**Expected outcome:** Stale cache row is not returned; a fresh computation is performed and cached under the new stamp.

**Pass criteria:** Response `membership_timeline` matches a fresh compute against V2; stale row is never served.

---

### TC-04 — Cold cache miss does not hang; bounded within normal request budget

**Type:** api  
**Preconditions:** Backend running; cache table exists but is EMPTY (or flushed) for the current `_dataset_version` stamp.

**Steps:**
1. Delete all rows from the membership-timeline cache table (simulating a cold miss)
2. Send `curl -w "%{time_total}\n" -o /dev/null -s http://localhost:8835/api/data`
3. Record response time and HTTP status

**Expected outcome:** Request completes; response time stays bounded (no >300 s hang); HTTP 200; the cache is populated with the computed payload on return.

**Pass criteria:** `time_total` ≤ 60 seconds AND HTTP 200 (a cold compute may be slower than a warm cache, but must not exceed the old regression hang threshold).

---

### TC-05 — Empty DB returns empty-but-valid timeline (no fabricated data)

**Type:** api  
**Preconditions:** Backend running with an EMPTY test DB (no `scanner_run` rows; no snapshots).

**Steps:**
1. Send `curl -s http://localhost:8835/api/data`
2. Extract the `coverage.membership_timeline` field from the response

**Expected outcome:** `membership_timeline` is present (not null/missing) but contains an empty list of dates (no fabricated entries).

**Pass criteria:** Response is HTTP 200; `membership_timeline` is a valid JSON array of length 0; no error; no 4xx status.

---

### TC-06 — test_db.py registers new standalone cache table

**Type:** artifact  
**Preconditions:** All DB models are defined; `test_db.py::test_create_all_produces_expected_tables` exists.

**Steps:**
1. Read `apps/backend/tests/test_db.py` line 70 (the expected-tables union)
2. Verify the `MEMBERSHIP_TIMELINE_CACHE_TABLES` group is defined with the new cache table name
3. Run `pytest apps/backend/tests/test_db.py::test_create_all_produces_expected_tables -v`

**Expected outcome:** Test passes (exact-set match includes the new cache table in the expected union).

**Pass criteria:** pytest exit code 0; table is registered in the expected union and matches the actual created table count.

---

### TC-07 — Byte-identity: coverage block fields unchanged (universe_count, universe_diagnostic)

**Type:** api  
**Preconditions:** Backend running; cache populated; both a cached and a fresh `compute_coverage` result available.

**Steps:**
1. Call `compute_coverage(...)` via the cache-backed path (real GET /api/data)
2. Call `compute_coverage(...)` fresh (via test harness, bypassing cache)
3. Compare the `universe_count` and `universe_diagnostic` fields

**Expected outcome:** Both fields are identical; no new top-level `/api/data` key is introduced.

**Pass criteria:** `universe_count` matches exactly; `universe_diagnostic` (with `admitted` + `excluded_by_reason` counts per date) matches exactly.

---

### TC-08 — Causality: timeline dates observed only from ≤ D snapshots (no lookahead)

**Type:** api  
**Preconditions:** Backend running; cache populated; DB contains snapshots across multiple dates (e.g. 2021-10-18 through current date).

**Steps:**
1. Call the cached `_membership_timeline(session, as_of=D)` via GET /api/data with `?as_of=D`
2. For each date in the returned timeline, verify that the resolved universe was derived ONLY from snapshots and bars dated ≤ D
3. Verify no future-dated snapshot or bar influenced the result

**Expected outcome:** Each timeline entry is causally correct; no date-ordering violation; no future leakage.

**Pass criteria:** Every date in `membership_timeline` is ≤ the resolved as-of date; all symbol admissions/exclusions are based on bars ≤ D.

---

### TC-09 — Warm-up precomputes membership-timeline cache on boot

**Type:** api  
**Preconditions:** Backend is not running; cache table exists but is empty; startup will trigger `_run_warmup`.

**Steps:**
1. Start the backend: `uvicorn apps.backend.app.main:app --port 8835 --host 0.0.0.0`
2. Wait for the lifespan to complete and warm-up daemon to finish (logs show "warm-up complete" or similar)
3. Query the cache table to verify at least one row exists for the current `_dataset_version` stamp
4. Send `GET /api/data` and verify it returns within 2 seconds (cache warm)

**Expected outcome:** Warm-up successfully populates the cache; the first `/data` request is fast.

**Pass criteria:** Cache table has ≥1 row for the current version after startup; `GET /api/data` response time ≤ 2 seconds.

---

### TC-10 — Warm-up failure does not block lifespan (non-fatal)

**Type:** api  
**Preconditions:** Backend is not running; warm-up precompute will be forced to fail (e.g. mock an exception in `_membership_timeline`).

**Steps:**
1. Instrument the warm-up to raise an exception during the timeline precompute
2. Start the backend
3. Verify the lifespan completes and the backend is ready (HTTP 200 on a simple health endpoint)
4. Verify the cache remains empty or with an older stamp
5. Send `GET /api/data` and verify it still returns a valid response (cold compute path)

**Expected outcome:** Warm-up failure is caught and logged; backend remains operational; GET /api/data still works (slower, but correct).

**Pass criteria:** Backend starts successfully; `GET /api/data` returns HTTP 200 with a valid payload (even if slow).

---

### TC-11 — Browser: J-94 per-date coverage diagnostic renders on /data

**Type:** browser  
**Preconditions:** Frontend running on :3835; backend :8835 responsive; cache warm; as-of date set to a historical snapshot date.

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for the page to fully load (not skeleton state)
3. Scroll to the "Data Manager" or coverage diagnostic section
4. Verify the per-date grid renders with admitted + excluded-by-reason counts for the resolved as-of date
5. Take a screenshot

**Expected outcome:** Coverage diagnostic is visible (not a skeleton), showing the universe-resolution breakdown for each date.

**Pass criteria:** Grid is rendered (not loading state); row exists for the resolved as-of; screenshot is non-blank, non-duplicate of a skeleton frame (md5 check).

---

### TC-12 — Browser: J-96 membership-timeline step function renders with Entries/Exits and honesty labels

**Type:** browser  
**Preconditions:** Frontend running; backend responsive; cache warm; /data page navigable.

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Wait for full page load
3. Scroll the membership-timeline step-function chart into the viewport (below the fold)
4. Verify the rising step function is visible from ~2021-10-18 to recent date
5. Verify the Entries and Exits rows below the chart are populated (not empty)
6. Verify the three honesty labels are visible ("universe-relative", "survivorship bias", etc.)
7. Take a screenshot

**Expected outcome:** Step function chart renders; Entries/Exits rows are populated; all labels present.

**Pass criteria:** Chart is rendered (not skeleton); Entries/Exits have non-zero values; labels are readable; screenshot is md5-unique and non-skeleton.

---

### TC-13 — Browser: J-93 /stocks slides 0→544 (fast path unaffected)

**Type:** browser  
**Preconditions:** Frontend running; backend responsive; /stocks page accessible.

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Verify the stock count in the header or list shows the correct dynamic count (should slide from 0 → 544 or similar based on the resolved universe)
3. Take a screenshot

**Expected outcome:** Stock count is correct and reflects the dynamic universe size; fast `/api/stocks` path is unaffected by the cache change.

**Pass criteria:** Count matches the expected universe size for the resolved as-of date; no regression in the stocks list rendering.

---

### TC-14 — Browser: CRITICAL J-18 — exactly one date selector (0 input[type=date])

**Type:** browser  
**Preconditions:** Frontend running.

**Steps:**
1. Navigate to any page (`/stocks`, `/data`, `/themes`, etc.)
2. Search the DOM for all elements matching `input[type=date]`
3. Verify the count is exactly 0 (no page-local date state)

**Expected outcome:** No HTML date-input fields on any page; the single global as-of selector is the only date control.

**Pass criteria:** `document.querySelectorAll('input[type=date]').length === 0` returns true on all navigated pages.

---

### TC-15 — Browser: CRITICAL J-07 Risk-Off → 0 Actionable stocks

**Type:** browser  
**Preconditions:** Frontend running; backend responsive; a Risk-Off regime snapshot exists in the DB.

**Steps:**
1. Navigate to `http://localhost:3835/stocks`
2. Set the as-of date to a Risk-Off regime date (via the as-of picker)
3. Verify the "Actionable" count shows 0 (stocks in watchlist-only mode)
4. Verify the list does not display any Actionable stocks

**Expected outcome:** Risk-Off regime correctly gates the Actionable count to 0.

**Pass criteria:** Actionable count = 0; no Actionable stocks appear in the list on a Risk-Off date.

---

### TC-16 — Browser: J-36, J-37, J-39, J-85 re-smoke on /data (co-located journeys)

**Type:** browser  
**Preconditions:** Frontend running; backend responsive; /data page loads and renders.

**Steps:**
1. Navigate to `http://localhost:3835/data`
2. Verify the page fully hydrates (no skeleton state)
3. Spot-check each co-located journey:
   - J-36: presence of market-overview data (if present)
   - J-37: any portfolio or allocation view (if present)
   - J-39: member-listing or similar (if present)
   - J-85: any new-member confirmation or rebuild-related state (if present)
4. Take a screenshot

**Expected outcome:** All co-located journeys on `/data` are still functional and render correctly after the cache changes.

**Pass criteria:** Page fully loads; no regression in any co-located journey rendering.

---

### TC-17 — Backend unit/integration: test_data_manager_membership_cache.py passes

**Type:** artifact  
**Preconditions:** Test file `apps/backend/tests/test_data_manager_membership_cache.py` is created and implemented.

**Steps:**
1. Run `pytest apps/backend/tests/test_data_manager_membership_cache.py -v`
2. Verify all test cases pass (byte-identity, cache-invalidation, causality, empty-DB)

**Expected outcome:** All tests pass; exit code 0.

**Pass criteria:** pytest exit code 0; all test functions pass.

---

### TC-18 — Backend unit/integration: test_warmup.py includes cache precompute assertion

**Type:** artifact  
**Preconditions:** `apps/backend/tests/test_warmup.py` is extended to cover membership-timeline cache precompute.

**Steps:**
1. Run `pytest apps/backend/tests/test_warmup.py -v -k "membership_timeline or cache"`
2. Verify the warm-up precompute test passes
3. Verify the non-fatal failure test passes

**Expected outcome:** Warm-up tests pass; cache precompute is asserted; non-fatal failure is validated.

**Pass criteria:** pytest exit code 0; relevant test functions pass.

---

## Summary

**Total test cases:** 18  
**API tests:** 10 (TC-01 through TC-10)  
**Browser tests:** 7 (TC-11 through TC-16)  
**Artifact checks:** 2 (TC-06, TC-17, TC-18)

**Key assertion:** Every served value (membership_timeline, universe_diagnostic, universe_count) is byte-identical to pre-cache computation. Response time is bounded on cold cache and fast on warm. All required journeys (J-94, J-96, J-93, J-07, J-18, J-36, J-37, J-39, J-85) remain green or are newly restored to green.
