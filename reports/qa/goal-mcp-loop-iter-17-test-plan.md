# goal-mcp-loop-iter-17 Functional Test Plan

**Phase:** goal-mcp-loop-iter-17  
**Date:** 2026-07-02  
**Frontend Present:** no

## Phase Goal

Complete the staged 30-year seed with deep, vendor-disclosed index & macro context (deep `_SPX`/`_NDX`/`_DJI` from Stooq's local world bundle, deep `_VIX` from Yahoo with a sanctioned offline fallback, and byte-identical FRED-macro proxies), so the staged asset is swap-complete and iter-18 can perform the atomic basis swap once over one complete seed with ZERO runtime change this iteration.

## Test Cases

### TC-01 — World-bundle file discovery and index mapping

**Type:** api  
**Preconditions:** `data/d_world_txt/data/daily/world/indices/` exists with `^spx.txt`, `^ndx.txt`, `^dji.txt` present; `apps/backend/scripts/ingest_seed.py` has the world-bundle indexing implementation.

**Steps:**
1. Run `python3 apps/backend/scripts/ingest_seed.py --provider stooq-local --archive-dir data/d_world_txt --out apps/backend/data/seed-stooq-30y --start 1996-01-01 --end 2026-07-01`
2. Verify the script completes without error
3. Inspect `apps/backend/data/seed-stooq-30y/prices/` directory

**Expected outcome:** Staged directory contains `_SPX.csv`, `_NDX.csv`, `_DJI.csv` in addition to existing equity CSVs.  
**Pass criteria:** All three files exist, each contains at least 100 rows, and the script exit code is 0.

---

### TC-02 — Window clipping prevents pre-1996 leakage

**Type:** artifact  
**Preconditions:** `_SPX.csv` staged from world-bundle archive (TC-01 passed); world archive `^spx.txt` contains pre-1996 rows (documented as reaching 1789 with flat/monthly early data).

**Steps:**
1. Examine the first row of `apps/backend/data/seed-stooq-30y/prices/_SPX.csv`
2. Parse the date field (first column after `date`)
3. Verify no rows exist before 1996-01-01
4. Verify the last row's date equals 2026-07-01 (the pinned manifest end)

**Expected outcome:** Earliest date ≥ 1996-01-01, latest date = 2026-07-01 (or the last trading day ≤ 2026-07-01).  
**Pass criteria:** First row date ≥ 1996-01-01 AND last row date == manifest pinned end; zero pre-1996 rows leaked.

---

### TC-03 — Index series have correct schema and non-fabricated data

**Type:** artifact  
**Preconditions:** `_SPX.csv`, `_NDX.csv`, `_DJI.csv` staged; `tests/test_seed_staged_30y.py` extended with index validations.

**Steps:**
1. Run `pytest apps/backend/tests/test_seed_staged_30y.py::test_index_schema_and_integrity -v`
2. Verify the test asserts each index CSV has schema: `date,open,high,low,close,volume`
3. Verify strictly ascending unique dates
4. Verify positive prices and non-negative volumes
5. Verify no flat-OHLC fabricated-looking runs in the staged window

**Expected outcome:** All assertions pass for all three index files.  
**Pass criteria:** Test output shows PASSED; no schema errors, date violations, or fabricated bars detected.

---

### TC-04 — FRED-macro proxies copied byte-identical

**Type:** artifact  
**Preconditions:** Live proxy files exist at `data/seed/prices/_TNX.csv`, `data/seed/prices/_DXY.csv`, `data/seed/prices/_VXN.csv`.

**Steps:**
1. Copy the three live files: `data/seed/prices/_TNX.csv` → staged, `data/seed/prices/_DXY.csv` → staged, `data/seed/prices/_VXN.csv` → staged
2. Run byte-comparison: `cmp -l data/seed/prices/_TNX.csv apps/backend/data/seed-stooq-30y/prices/_TNX.csv`
3. Repeat for `_DXY.csv` and `_VXN.csv`

**Expected outcome:** All three files are byte-identical (no differences reported by `cmp`).  
**Pass criteria:** `cmp` exit code 0 for all three; no differing bytes.

---

### TC-05 — VIX deep pull from Yahoo OR sanctioned fallback

**Type:** api  
**Preconditions:** Yahoo endpoint reachable OR sanctioned fallback logic implemented; `ingest_seed.py` has context-merge mode.

**Steps:**
1. Run `python3 apps/backend/scripts/ingest_seed.py --provider yahoo --symbol VIX --start 1996-01-01 --end 2026-07-01 --merge-into apps/backend/data/seed-stooq-30y/meta.json` (or equivalent merge-mode invocation)
2. If Yahoo is reachable: verify `_VIX.csv` is created with first bar ≤ 1996-01-05
3. If Yahoo is unreachable: verify the script falls back to copying `data/seed/prices/_VIX.csv` verbatim
4. Verify `meta.json` records the `_VIX` coverage with `vendor: yahoo` and the actual span (deep or short)

**Expected outcome:** `_VIX.csv` exists; either deep (1996-01-05 start) or byte-identical to live (2021-01-04 start); manifest records it.  
**Pass criteria:** CSV file exists, manifest includes `_VIX` record with `vendor: yahoo`, and test assertion `_VIX deep XOR fallback` passes.

---

### TC-06 — Manifest merge preserves equities and adds vendor disclosure

**Type:** artifact  
**Preconditions:** Original manifest with 583 equity records; context staging adds 4 new context series (`_SPX`, `_NDX`, `_DJI`, `_VIX`); proxy copies add 3 more (`_TNX`, `_DXY`, `_VXN`).

**Steps:**
1. Inspect `apps/backend/data/seed-stooq-30y/meta.json`
2. Count the `coverages[]` records for equity symbols (should be 583)
3. Count the context/index records (should be 7: `_SPX`, `_NDX`, `_DJI`, `_VIX`, `_TNX`, `_DXY`, `_VXN`)
4. Verify each context series has a `vendor` field with value ∈ {stooq, yahoo, fred-macro-proxy}
5. Verify `planned/ok/failed` accounting is consistent (expected: planned ~591, ok 590, failed 1 = SATS only)
6. Verify the pinned window is unchanged (1996-01-01 → 2026-07-01)

**Expected outcome:** Manifest has 590 context+equity records total; vendor disclosure present for all 7 context series; accounting balanced; window unchanged.  
**Pass criteria:** `jq '.coverages | length'` == 590; `jq '.coverages[] | select(.vendor) | .vendor' | wc -l` >= 7; `planned/ok/failed` sum correctly; window pins match original.

---

### TC-07 — Swap-completeness: staged ⊇ live

**Type:** artifact  
**Preconditions:** Live seed at `data/seed/prices/`; staged seed at `apps/backend/data/seed-stooq-30y/prices/`.

**Steps:**
1. List live seed files: `ls data/seed/prices/*.csv | wc -l`
2. List staged seed files: `ls apps/backend/data/seed-stooq-30y/prices/*.csv | wc -l`
3. For each live file, verify it has a staged counterpart: `for f in data/seed/prices/*.csv; do test -f apps/backend/data/seed-stooq-30y/prices/$(basename $f) || echo "MISSING: $f"; done`
4. Run `pytest apps/backend/tests/test_seed_staged_30y.py::test_swap_completeness -v`

**Expected outcome:** Every live seed file has a staged counterpart; staged set ⊇ live set test passes.  
**Pass criteria:** Staged file count ≥ live file count; zero MISSING files reported; test PASSED.

---

### TC-08 — `_solve_stooq_pow` iteration cap and bounded failure

**Type:** api  
**Preconditions:** `_solve_stooq_pow` function in `ingest_seed.py` has an iteration cap implemented; test exists to exercise the cap.

**Steps:**
1. Run `pytest apps/backend/tests/test_ingest_seed.py::test_solve_stooq_pow_cap -v`
2. Verify the test creates a scenario where `_solve_stooq_pow` would exceed the cap
3. Verify the loop terminates with an honest failure message
4. Verify no infinite loop occurs

**Expected outcome:** Test passes; iteration cap enforced; honest error message logged.  
**Pass criteria:** Test PASSED; execution time < 5 seconds (no spin); failure message present in log.

---

### TC-09 — Redaction of sensitive data on failure path

**Type:** api  
**Preconditions:** `redact_stooq_key` function exists in `ingest_seed.py`; a failure scenario (e.g., Yahoo unreachable) is tested.

**Steps:**
1. Run `pytest apps/backend/tests/test_ingest_seed.py::test_yahoo_unreachable_redacts_failure -v`
2. Verify the test simulates a Yahoo network failure
3. Inspect the persisted error log or manifest output
4. Verify any exception text or URL does not contain unredacted environment-sourced credentials

**Expected outcome:** Failure is recorded; error message is safe for committed artifacts.  
**Pass criteria:** Test PASSED; no raw API keys or env variables in any persisted output.

---

### TC-10 — Byte-identity non-regression on protected paths

**Type:** artifact  
**Preconditions:** Zero diff on `apps/backend/app/**`, `apps/frontend/**`, `config.yaml`, `certified-claims.jsonl`, `staging-ledger.jsonl`.

**Steps:**
1. Run `git diff --name-only apps/backend/app/ apps/frontend/ config.yaml runs/goal-session-mcp-loop/state/certified-claims.jsonl runs/goal-session-mcp-loop/state/staging-ledger.jsonl`
2. Verify no files are listed

**Expected outcome:** No diffs on protected paths.  
**Pass criteria:** `git diff` output is empty (no changes to runtime code or ledgers).

---

### TC-11 — Unedited DoD suites pass green

**Type:** api  
**Preconditions:** Test suites exist: `test_referee.py`, `test_forward_walk.py`, `test_evidence.py`, `test_staging_ledger_routing.py`, `test_seed_integrity.py`, `test_seed_provider.py`; no changes to these files.

**Steps:**
1. Run `pytest apps/backend/tests/test_referee.py -v --tb=short`
2. Run `pytest apps/backend/tests/test_forward_walk.py -v --tb=short`
3. Run `pytest apps/backend/tests/test_evidence.py -v --tb=short`
4. Run `pytest apps/backend/tests/test_staging_ledger_routing.py -v --tb=short`
5. Run `pytest apps/backend/tests/test_seed_integrity.py -v --tb=short`
6. Run `pytest apps/backend/tests/test_seed_provider.py -v --tb=short`
7. Aggregate results

**Expected outcome:** All tests pass.  
**Pass criteria:** Total failures = 0; no test file was edited this iteration.

---

### TC-12 — Extended validation suite passes for context series

**Type:** api  
**Preconditions:** Tests extended in `tests/test_seed_staged_30y.py` or sibling to validate context series.

**Steps:**
1. Run `pytest apps/backend/tests/test_seed_staged_30y.py -v`
2. Verify test output includes assertions for:
   - `_SPX/_NDX/_DJI` present + schema-identical + ascending dates + positive prices / non-negative volumes + first ≥ 1996-01-01 + last == pinned end + no fabricated runs
   - `_TNX/_DXY/_VXN` byte-identical to live
   - `_VIX` deep-XOR-fallback (exactly one state, never hybrid)
   - swap-completeness (staged ⊇ live)
   - manifest vendor agreement

**Expected outcome:** All assertions pass.  
**Pass criteria:** Test run shows all checks PASSED; no schema, date, or fabrication violations.

---

### TC-13 — Coverage report artifact exists and is complete

**Type:** artifact  
**Preconditions:** `reports/phase-goal-mcp-loop-iter-17-seed-coverage.md` written by dev handoff step.

**Steps:**
1. Verify file exists: `test -f reports/phase-goal-mcp-loop-iter-17-seed-coverage.md`
2. Grep for final inventory line: `grep -i "590" reports/phase-goal-mcp-loop-iter-17-seed-coverage.md`
3. Grep for vendor table: `grep -i "vendor" reports/phase-goal-mcp-loop-iter-17-seed-coverage.md`
4. Grep for VIX outcome: `grep -i "_vix" reports/phase-goal-mcp-loop-iter-17-seed-coverage.md`
5. Grep for swap-complete verdict: `grep -i "swap-complete" reports/phase-goal-mcp-loop-iter-17-seed-coverage.md`

**Expected outcome:** File exists and contains final inventory (590 expected), vendor table, `_VIX` outcome, and explicit swap-complete verdict.  
**Pass criteria:** File exists; all four grep patterns match; swap-complete verdict is yes/no (explicit).

---

### TC-14 — Dev handoff document exists with External-Integration section

**Type:** artifact  
**Preconditions:** `docs/handoffs/goal-mcp-loop-iter-17-dev.md` written by developer.

**Steps:**
1. Verify file exists: `test -f docs/handoffs/goal-mcp-loop-iter-17-dev.md`
2. Grep for External-Integration section: `grep -A 10 "## External-Integration" docs/handoffs/goal-mcp-loop-iter-17-dev.md`
3. Verify it documents the Yahoo `_VIX` pull outcome (success or fallback)

**Expected outcome:** Handoff file exists with External-Integration section describing Yahoo outcome.  
**Pass criteria:** File exists; section present; outcome (deep vs fallback) documented with evidence.

---

### TC-15 — Manifest notes extended with mixed-vendor context and proxy disclaimer

**Type:** artifact  
**Preconditions:** `meta.json` manifest has a `note` field describing the completed context.

**Steps:**
1. Read `apps/backend/data/seed-stooq-30y/meta.json`
2. Extract and display the `note` field
3. Verify it mentions mixed-vendor context (stooq, yahoo, fred-macro-proxy)
4. Verify it includes the disclaimer: "a proxy is never presented as a market index"

**Expected outcome:** Manifest note describes vendor mix and includes proxy disclaimer.  
**Pass criteria:** Note field exists; contains keywords "vendor", "proxy", "market index".

---

## Summary

**Total test cases:** 15  
**API tests:** 6 (TC-01, TC-05, TC-08, TC-09, TC-11, TC-12)  
**Artifact checks:** 9 (TC-02, TC-03, TC-04, TC-06, TC-07, TC-10, TC-13, TC-14, TC-15)

**Key flow verified:**
- World-bundle indexing discovers and maps `^spx/^ndx/^dji` to staged CSVs (TC-01, TC-02, TC-03)
- FRED proxies copied byte-identical (TC-04)
- Yahoo `_VIX` pulled deep or fallback to live copy (TC-05)
- Manifest merged with 7 context series, vendor disclosure added, accounting balanced (TC-06)
- Swap-completeness verified (staged ⊇ live) (TC-07)
- Audit carry-forwards: iteration cap + redaction (TC-08, TC-09)
- Zero runtime code/ledger changes (TC-10)
- Unedited DoD suites green (non-regression for J-01..J-09) (TC-11)
- Extended validation suite passes all context checks (TC-12)
- Coverage report and handoff document both complete with honest outcomes (TC-13, TC-14, TC-15)
