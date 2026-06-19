# Iteration 35 Functional Test Plan

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35  
**Date:** 2026-06-19  
**Frontend Present:** yes

## Phase Goal

Verify that the J-85 confirm-gated rebuild has persisted the dynamic per-date universe into the snapshots, enabling J-93 (stock universe slides by as-of date) and J-96 (membership timeline shows entries/exits) to pass with genuine differential evidence.

## Test Cases

### TC-01 — Backend seed safety verification after rebuild

**Type:** api  
**Preconditions:** The J-85 rebuild has completed (job `eb48cbf1` with 1369/1369 dates rebuilt); backend is running on port 8835

**Steps:**
1. Query `GET /api/data/jobs?job_id=eb48cbf1` to fetch the rebuild job record
2. Verify the job status is terminal (e.g., `"completed"` or `"succeeded"`)
3. Query the database directly to confirm `bars_before == bars_after` (committed `daily_prices` seed row count unchanged after `clear_snapshot_set`)
4. Verify no `daily_prices` rows were deleted or modified (only snapshot layer cleared)

**Expected outcome:** The job completed successfully, seed safety assertion passed, and committed price data is intact.

**Pass criteria:** Job status is terminal and successful; `bars_before == bars_after` logged in the job record or DB; `SELECT COUNT(*) FROM daily_prices` matches the pre-rebuild count.

---

### TC-02 — Dynamic universe: early date before warm-up boundary (J-93 early/empty state)

**Type:** api  
**Preconditions:** Backend running on port 8835; J-85 rebuild completed with new dynamic per-date snapshots

**Steps:**
1. Call `GET /api/stocks?as_of=2021-01-04` (a date well before the ~2021-10-18 warm-up boundary)
2. Parse the response to count the returned stock rows
3. Verify the count is **0 or a very small number** (fewer than 50) representing the honest empty/minimal early universe
4. Confirm each row's `asof_date` equals `2021-01-04`

**Expected outcome:** The endpoint returns 0 rows or a small honest subset, not the pre-rebuild flat 122.

**Pass criteria:** Row count at 2021-01-04 is 0–50 (genuine early empty state); response status 200; all returned rows dated 2021-01-04.

---

### TC-03 — Dynamic universe: full date after warm-up (J-93 full state)

**Type:** api  
**Preconditions:** Backend running on port 8835; J-85 rebuild completed

**Steps:**
1. Call `GET /api/stocks?as_of=2022-02-01` (a date after the warm-up boundary, in the full universe window)
2. Parse the response to count the returned stock rows
3. Verify the count is **approximately 496–544**, the full or near-full rebuilt universe
4. Confirm each row's `asof_date` equals `2022-02-01`

**Expected outcome:** The endpoint returns the full dynamic universe count for that date, showing growth from the early empty state.

**Pass criteria:** Row count at 2022-02-01 is 450–544 (full universe); response status 200; all returned rows dated 2022-02-01.

---

### TC-04 — Dynamic universe differential: confirm byte-distinct frames (J-93 evidence)

**Type:** artifact  
**Preconditions:** Both TC-02 and TC-03 passed; evidence capture system ready

**Steps:**
1. Take a screenshot or capture JSON response of `/api/stocks?as_of=2021-01-04` and save as `TC-04-early-2021-01-04.json` (or .png)
2. Take a screenshot or capture JSON response of `/api/stocks?as_of=2022-02-01` and save as `TC-04-full-2022-02-01.json` (or .png)
3. Compute md5sum of each captured file
4. Verify the two checksums are **different** (byte-distinct frames)
5. Verify the two frame's row counts are **significantly different** (e.g., 0–50 vs 450–544)

**Expected outcome:** Two byte-distinct frames with visibly different row counts, proving the universe is not flat 122 at every date.

**Pass criteria:** `md5sum(frame_early) != md5sum(frame_full)`; row count differential ≥ 400; both frames valid JSON/HTML.

---

### TC-05 — J-96 membership timeline renders with step function (rising, not flat)

**Type:** browser  
**Preconditions:** Frontend running on port 3000; backend on 8835; Chrome MCP available on 9222

**Steps:**
1. Navigate to `http://localhost:3000/data`
2. Locate the Data Manager panel with the membership-timeline chart (scroll below the fold if needed)
3. Visually inspect the timeline's SIZE column across dates
4. Verify the line chart or step function **rises from near-zero/empty at 2021-01-04 to ~544 at recent dates** (not a flat 122 line)
5. Capture a screenshot showing the rising step function and save to `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35-evidence/TC-05-timeline-rising.png`

**Expected outcome:** The membership-timeline step function is visibly rising over time, reflecting the dynamic per-date universe.

**Pass criteria:** Line chart shows clear upward step pattern from early empty to full; early dates show SIZE near 0, late dates show SIZE ≥ 450; screenshot is non-blank and shows rendered pixels.

---

### TC-06 — J-96 entries and exits are populated (not all "—")

**Type:** browser  
**Preconditions:** Frontend running on port 3000; backend on 8835; J-96 membership timeline rendered

**Steps:**
1. Navigate to `http://localhost:3000/data` and scroll the membership-timeline table into view
2. Locate the "Entries" and "Exits" columns in the timeline table
3. Scroll through several rows (covering early, mid, and late dates)
4. Verify that Entries and Exits columns contain **populated values** (e.g., "AAPL, MSFT, …" or counts) — not all "—" (placeholder)
5. Capture a screenshot showing the populated entries/exits and save to `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35-evidence/TC-06-entries-exits-populated.png`

**Expected outcome:** The timeline table's Entries and Exits columns show actual stock symbols or entry/exit counts, not empty placeholders.

**Pass criteria:** At least 5 rows have non-empty Entries or Exits values; screenshot shows rendered table rows with symbols/counts; Entries/Exits are not all "—" or blank.

---

### TC-07 — J-96 honesty labels present (survivorship, warm-up, universe-relative)

**Type:** browser  
**Preconditions:** Frontend running on port 3000; J-96 membership timeline visible

**Steps:**
1. Navigate to `http://localhost:3000/data` and scroll to the membership-timeline panel header or legend
2. Search the rendered text for the three honesty labels:
   - "survivorship bias" or "survivorship" language
   - "warm-up boundary" or "minimum history" language
   - "universe-relative" language
3. Verify all three labels are present and verbatim as defined in the spec
4. Capture a screenshot showing the label text and save to `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35-evidence/TC-07-honesty-labels.png`

**Expected outcome:** The J-96 panel displays all three honesty labels verbatim, warning users of survivor bias and the warm-up boundary.

**Pass criteria:** All three label phrases present in the rendered panel text; screenshot shows clear, readable label text; labels match the spec wording.

---

### TC-08 — J-06 count reconciliation: diagnostic vs served membership agree

**Type:** api  
**Preconditions:** Backend running on port 8835; rebuild complete with dynamic per-date snapshots

**Steps:**
1. Call `GET /api/data` to fetch the diagnostic endpoint (J-94 per-date coverage diagnostic)
2. Extract the `universe_count` or `resolved_size` for the latest as-of date (e.g., 2026-06-16)
3. Call `GET /api/stocks?as_of=2026-06-16` and count the returned stock rows
4. Compare the two counts: diagnostic resolved size vs served snapshot row count
5. Verify they **agree within the documented benchmark-vs-stocks-only distinction** (both ~544 or within 2–5 row margin)

**Expected outcome:** The diagnostic's resolved-size count and the snapshot-served row count are consistent at the same instant.

**Pass criteria:** `abs(diagnostic_resolved_size - served_row_count) ≤ 5`; both endpoints return status 200; counts match expected ~540–544 range at latest date.

---

### TC-09 — J-06 NVDA leaderboard consistency: list score == detail score

**Type:** browser  
**Preconditions:** Frontend running on port 3000; backend on 8835; J-85 rebuild complete

**Steps:**
1. Navigate to `http://localhost:3000/stocks` with the latest as-of date
2. Search the leaderboard table for NVDA; record its visible Leadership/Entry/Risk scores
3. Click on NVDA to navigate to the detail page (`/stocks/NVDA?as_of=...`)
4. Record the Leadership/Entry/Risk scores on the detail page
5. Verify the scores are **identical** on both views
6. Capture a screenshot of the list view and detail view for evidence

**Expected outcome:** NVDA's scores on the leaderboard match exactly with the detail page, confirming single-source-of-truth serving.

**Pass criteria:** Leadership score matches; Entry score matches; Risk score matches; screenshot evidence shows both views; status 200 on both endpoints.

---

### TC-10 — J-18 single global as-of control: zero date inputs

**Type:** browser  
**Preconditions:** Frontend running on port 3000; backend on 8835

**Steps:**
1. Navigate to `http://localhost:3000/stocks`
2. Inspect the entire page using browser dev tools or visual scan
3. Search for any `<input type="date">` elements in the DOM
4. Verify that **zero (0)** date input fields exist on the page
5. Confirm the only as-of control is the single global switcher (e.g., the as-of button/dropdown at the top)
6. Capture a screenshot of the page showing no date inputs and save to `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35-evidence/TC-10-no-date-inputs.png`

**Expected outcome:** The page has no local date inputs; the single global as-of selector is the only date control.

**Pass criteria:** DOM search for `input[type=date]` returns 0 results; single as-of control visible; screenshot shows clean page without hidden date fields.

---

### TC-11 — J-07 Risk-Off date returns zero actionable stocks (CRITICAL)

**Type:** api  
**Preconditions:** Backend running on port 8835; rebuild complete; a Risk-Off date is known (from historical regime data)

**Steps:**
1. Identify a known Risk-Off date from the committed seed (e.g., a date during the 2022 bear market when regime is "Risk-Off")
2. Call `GET /api/stocks?as_of=<risk_off_date>&status=actionable` (or filter the response to count status="Actionable")
3. Verify the count of Actionable stocks is **exactly 0** (or the response returns empty when filtered for Actionable)
4. Call `GET /api/stocks?as_of=<risk_off_date>` (all statuses) and confirm some stocks still exist (not an empty universe date), but none are marked Actionable

**Expected outcome:** On a Risk-Off date, the scanner marks zero stocks Actionable, gating the watchlist to Risk-On dates only.

**Pass criteria:** Actionable count = 0 on a Risk-Off date; total stock count > 0 (not an empty date); status 200; risk-gating logic preserved.

---

### TC-12 — Unit/integration: test_iter27_rebuild_mdd.py all pass (GREEN)

**Type:** artifact  
**Preconditions:** Backend test environment ready; full pytest suite executable

**Steps:**
1. Run the command: `cd apps/backend && python -m pytest tests/test_iter27_rebuild_mdd.py -v`
2. Capture the output to `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-35-test.log`
3. Verify all 13 tests in the module pass
4. Confirm the output includes the line `13 passed` (or similar "all passed" summary)
5. Verify seed-safety assertion logs are present: `bars_before == bars_after`

**Expected outcome:** All 13 rebuild tests pass; seed integrity confirmed; snapshot immutability asserted.

**Pass criteria:** Test exit code 0; "13 passed" in summary; no FAILED or ERROR lines; seed-safety assertion found in logs.

---

### TC-13 — Unit/integration: test_universe_resolver.py all pass (GREEN)

**Type:** artifact  
**Preconditions:** Backend test environment ready; full pytest suite executable

**Steps:**
1. Run the command: `cd apps/backend && python -m pytest tests/test_asof_resolver.py -v` (or the resolver-specific test file)
2. Capture the output to the test log
3. Verify all 14+ universe resolver tests pass
4. Confirm the summary shows "X passed" with X ≥ 14
5. Verify no "FAILED" or "ERROR" lines appear for tail-invariance, warm-up boundary, or excluded-by-reason tests

**Expected outcome:** All resolver tests pass; per-date universe logic is unit-correct; no regressions in screening logic.

**Pass criteria:** Test exit code 0; ≥14 passed; no FAILED/ERROR; tail-invariance (removing future bars never changes D's membership) confirmed.

---

### TC-14 — Unit/integration: test_no_magic_numbers passes (resolver module included)

**Type:** artifact  
**Preconditions:** Backend test environment ready

**Steps:**
1. Run the command: `cd apps/backend && python -m pytest tests/test_no_magic_numbers.py -v`
2. Verify the resolver module is included in `CALC_FILES` (the source files checked for literal thresholds)
3. Confirm the test passes (no magic numbers found in resolver or other scoring modules)
4. Verify no assertion errors about hardcoded thresholds in `apps/backend/app/engine/universe_screen.py` or similar

**Expected outcome:** All thresholds (min_price, adv_window_days, min_history_bars) are read from config, not hardcoded.

**Pass criteria:** Test exit code 0; "passed" in summary; resolver module verified as clean of literals; config-only thresholds confirmed.

---

### TC-15 — No lookahead unit test: resolver uses only bars ≤ as_of_date

**Type:** artifact  
**Preconditions:** Backend test environment ready; resolver tests include no-lookahead verification

**Steps:**
1. Run the command: `cd apps/backend && python -m pytest tests/test_asof_resolver.py -v -k "lookahead or tail_invariance"`
2. Verify at least one test asserts that removing bars dated > D never changes D's resolved membership
3. Confirm the test logic:
   - Resolve membership for date D using full bars history
   - Resolve membership for date D using bars limited to ≤ D
   - Assert both results are identical
4. Capture the test output showing the no-lookahead assertion passes

**Expected outcome:** The resolver's per-date membership computation uses only historical data; future bars are never consulted.

**Pass criteria:** At least one tail-invariance or no-lookahead test passes; assertion logic is explicit; test output confirms bars > D are excluded.

---

### TC-16 — Full backend suite (targeted modules) runs to zero failures

**Type:** artifact  
**Preconditions:** Backend environment ready; test environment clean; no concurrent pytest runs

**Steps:**
1. Run the full backend test suite on targeted modules: `cd apps/backend && python -m pytest tests/test_api_engine.py tests/test_api_data.py tests/test_data_manager.py tests/test_scoring.py tests/test_universe_screen.py -v --tb=short`
2. Capture full output (stdout + stderr) to a test log file
3. At the end of the run, verify the summary shows `X passed, 0 failed` (exit code 0)
4. If any `F` (failed) or `E` (error) appears in `test_warmup.py` or `test_data_manager_jobs_pipeline.py`, re-run that single module in isolation before calling it a regression (iter-30/34 flake precedent)
5. Record the exact output line with pass/fail counts

**Expected outcome:** The targeted backend modules re-run after the rebuild and confirm no regressions in universe/scoring/data-manager logic.

**Pass criteria:** Test exit code 0; final summary shows "X passed, 0 failed" (X ≥ 300); no FAILED lines in output; any transient `test_warmup.py` flake is isolated and re-confirmed.

---

### TC-17 — Browser smoke: J-87 market phase unperturbed at full-universe date

**Type:** browser  
**Preconditions:** Frontend running on port 3000; backend on 8835; rebuild complete

**Steps:**
1. Navigate to `http://localhost:3000/` (Dashboard)
2. Set the as-of date to a full-universe date (e.g., 2022-02-01 or latest 2026-06-16)
3. Locate the Market Phase or Regime panel on the Dashboard
4. Verify the phase label is rendered (e.g., "Risk-On", "Risk-Off", "Normal", etc.)
5. Compare this value to a known baseline from the committed seed for that date
6. Confirm the phase is **consistent and unchanged** by the J-85 rebuild

**Expected outcome:** The regime/market-phase machinery renders unchanged for a full-universe date; the rebuild did not corrupt regime state.

**Pass criteria:** Phase label renders correctly; value matches expected regime for the date; status 200; panel loads without errors.

---

### TC-18 — Browser smoke: J-08 and J-15 immutability + snapshot-served reads still work

**Type:** browser  
**Preconditions:** Frontend running on port 3000; backend on 8835

**Steps:**
1. Navigate to `http://localhost:3000/data` and locate the Rebuild Snapshots panel (J-85 control)
2. Verify the panel is rendered as read-only or with the confirm-gated control (not a destructive button)
3. Scroll down to the Scanner Runs / Run History section
4. Verify the list of historical runs is populated and immutable (runs are not editable, deletable, or recomputeable in-place)
5. Confirm the oldest runs (from iter-27 before the rebuild) are still listed with their original results
6. Verify snapshot-served reads: fetch a historical run from before the rebuild and confirm its stored results are returned verbatim (not recomputed)

**Expected outcome:** The immutability contract and snapshot-served read path remain intact after the rebuild; no runs or results were updated in-place.

**Pass criteria:** Rebuild panel renders safely; run history list populated and immutable; old runs' snapshots still served correctly; no data modification detected.

---

## Summary

**Total test cases:** 18  
**API tests:** 8 (TC-01, TC-02, TC-03, TC-08, TC-09, TC-11, TC-12, TC-13)  
**Browser tests:** 7 (TC-05, TC-06, TC-07, TC-10, TC-17, TC-18, plus TC-09 hybrid)  
**Unit/integration tests:** 4 (TC-12, TC-13, TC-14, TC-15, TC-16)  
**Artifact checks:** 2 (TC-04, TC-07)

**Core J-93 and J-96 verification:**
- **J-93 (failing → passing):** TC-02, TC-03, TC-04 — two byte-distinct frames with significantly different row counts (0–50 vs 450–544), proving the dynamic universe is not flat
- **J-96 (partial → passing):** TC-05, TC-06, TC-07 — membership timeline rises from warm-up to full, entries/exits populated, honesty labels present
- **J-06 reconciliation (critical):** TC-08, TC-09 — diagnostic count agrees with served membership, NVDA scores identical on list and detail
- **Required-still-passing smoke:** TC-10 (J-18: 0 date inputs), TC-11 (J-07: Risk-Off → 0 Actionable), TC-17 (J-87: regime unchanged), TC-18 (J-08/J-15: immutability intact)
- **Backend regression guard:** TC-12, TC-13, TC-14, TC-15, TC-16 — all unit/integration tests pass, no-lookahead verified, seed safety confirmed
