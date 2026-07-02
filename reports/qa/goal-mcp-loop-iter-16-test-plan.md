# goal-mcp-loop-iter-16 Functional Test Plan

**Phase:** goal-mcp-loop-iter-16
**Date:** 2026-07-01
**Frontend Present:** no

## Phase Goal

Stage a complete ~30-year Stooq price seed for ~548 symbols as a committed, validated, side-by-side data asset with ZERO runtime change, enabling the next iteration's atomic basis swap without contaminating the staged data fetch or the evidence ledger.

## Test Cases

### TC-01 — Ingest tool: --provider flag routing to Stooq

**Type:** api
**Preconditions:**
- `apps/backend/scripts/ingest_seed.py` has been modified to accept `--provider stooq|yahoo`
- `StooqProvider` is client-injectable (test-harness dependency injection pattern)
- The default provider remains `yahoo` for backward compatibility

**Steps:**
1. Run `ingest_seed.py --provider stooq --out /tmp/test-out --start 1996-01-01 --end 2026-06-30 --symbols-set pool` with a stubbed/mocked `StooqProvider` that returns valid CSVs for AAPL/SPY/NVDA
2. Verify the script calls `make_provider("stooq")` and routes through the injected StooqProvider
3. Verify the default invocation (no `--provider`) still uses Yahoo and produces no diff to the live seed directory

**Expected outcome:** The `--provider` flag correctly routes Stooq requests through the existing provider layer; the Yahoo default is unregressed.

**Pass criteria:**
- Unit test with a stubbed client passes (no actual network calls)
- Default invocation (no `--provider`) writes to the live seed dir unchanged
- A `--provider stooq` invocation writes to the staging dir with the correct layout (prices/*.csv + meta.json)

---

### TC-02 — Ingest tool: --out and --symbols-set flags

**Type:** api
**Preconditions:**
- `apps/backend/data/seed-stooq-30y/` does not exist initially
- `universe_pool.csv` is readable at `apps/backend/data/seed/universe_pool.csv`
- Test harness can stub the StooqProvider with mock symbol lists

**Steps:**
1. Run `ingest_seed.py --provider stooq --out /tmp/test-stooq-30y --symbols-set pool --start 1996-01-01 --end 2026-06-30` with a stubbed provider that returns valid data
2. Verify the script reads the pool from `universe_pool.csv` and merges with `all_seed_symbols(config)` to produce ~590 symbols
3. Verify the output is written to `/tmp/test-stooq-30y/prices/` and `/tmp/test-stooq-30y/meta.json`
4. Verify the default `--symbols-set` behavior (current universe + ETFs, ~162 symbols) is unchanged

**Expected outcome:** Custom output directory and pool symbol set are correctly routed and written with the live-seed layout.

**Pass criteria:**
- Stubbed run creates staging dir with the correct layout
- `meta.json` contains provider, pinned end, per-symbol metadata
- Default invocation (no `--symbols-set`) uses the current universe list (~162 symbols)

---

### TC-03 — Ingest tool: pinned --end and resume manifest

**Type:** api
**Preconditions:**
- Test can pin a specific end date (e.g., 2026-06-30)
- Manifest-driven resume logic is testable with a stubbed client

**Steps:**
1. Run ingest with `--end 2026-06-30` and capture the manifest
2. Verify `meta.json` records the pinned end date
3. Simulate a second run with the same `--end` on a staging dir with partial data (e.g., AAPL complete, SPY/NVDA missing)
4. Verify the resume run skips AAPL and fetches only SPY/NVDA
5. Verify the final manifest shows all three symbols at the pinned end

**Expected outcome:** Manifest-driven resume correctly skips completed symbols and reuses the pinned end date.

**Pass criteria:**
- First run's `meta.json` records `pinned_end: 2026-06-30`
- Resume run fetches only symbols missing or short of the pinned end
- Final manifest shows per-symbol first/last/bar-count consistent with the CSVs on disk

---

### TC-04 — Ingest tool: priority ordering (tier 1→3)

**Type:** api
**Preconditions:**
- Test harness can control the order of fetch calls
- Benchmark/control symbol set is defined (index ETFs, sector ETFs, ^VIX, macro proxies, legend symbols)
- Current universe.symbols is defined (~122 names)
- Pool names alphabetical fallback is known

**Steps:**
1. Run ingest with a stubbed provider that logs fetch order
2. Verify fetch order: (1) benchmarks/controls (SPY/QQQ/sector ETFs/^VIX/proxies), (2) current universe, (3) remaining pool names alphabetical
3. Simulate a rate-cap mid-tier-2; verify manifest is written with completed tier-1 and partial tier-2
4. Resume run completes tier-2 and proceeds to tier-3 until completion or another cap

**Expected outcome:** Fetch priority ensures benchmarks and current universe complete before alphabetical pool names; resume completes in tiers.

**Pass criteria:**
- Fetch call log shows tier 1→2→3 ordering
- Rate-cap stop writes manifest with tier-1 complete, tier-2 partial
- Resume run continues from the manifest's saved position

---

### TC-05 — Ingest tool: rate-limit and graceful stop (error handling)

**Type:** api
**Preconditions:**
- Test harness can simulate `ProviderUnavailableError` responses (e.g., "Exceeded the daily hits limit", non-CSV body, limit-page)
- Exit code and manifest output are verifiable

**Steps:**
1. Run ingest with a stubbed provider that raises `ProviderUnavailableError` on symbol #50 (mid-tier-2)
2. Verify the script records the failure in the manifest, writes the manifest to disk, and exits with non-zero status
3. Verify no partial/fabricated CSV row is written for the failed symbol
4. Resume the run and verify it skips completed symbols and picks up from symbol #51

**Expected outcome:** Rate-limit or endpoint error is handled gracefully; manifest is written; no partial data is left behind.

**Pass criteria:**
- Failed symbol is recorded in manifest as `missing` or `failed`
- Non-zero exit code returned (e.g., exit 1)
- No partial CSV file for the failed symbol
- Resume run continues without re-fetching the failed symbol

---

### TC-06 — Ingest tool: unknown symbol "N/D" handling

**Type:** api
**Preconditions:**
- Test harness can simulate a symbol Stooq does not carry (e.g., a defunct ticker or delisted name)
- The provider returns "N/D" or an empty CSV body for unknown symbols

**Steps:**
1. Run ingest with a stubbed provider that returns "N/D" for symbol #30
2. Verify the script records the failure in the manifest, does not create a CSV for that symbol, and continues
3. Verify the run completes with exit 0 (successful partial completion)
4. Verify the final manifest lists the missing symbol under `failed` / `not_found`

**Expected outcome:** Unknown symbols are recorded and honestly omitted; the run continues and succeeds.

**Pass criteria:**
- Missing symbol is recorded in manifest as `not_found`
- No CSV file created for the missing symbol
- Run completes with exit 0
- Manifest shows honest counts of fetched/failed/missing symbols

---

### TC-07 — Live probe: Stooq endpoint real-world check (AAPL/SPY/NVDA)

**Type:** api
**Preconditions:**
- Real Stooq endpoint is reachable (no mocking)
- Test can make actual HTTP requests
- Environment is set up to run the probe once per iteration (external integration test per spec)

**Steps:**
1. Run ingest with `--provider stooq` (no stub, real network) for symbols AAPL, SPY, NVDA only with `--start 1996-01-01 --end 2026-06-30`
2. Verify AAPL and SPY first bars are ≤ 1996-01-05 (real historical start dates)
3. Verify NVDA first bar is in 1999 (real IPO, not earlier)
4. Verify CSV schema is exactly `date,open,high,low,close,volume` with no extra columns
5. Verify close prices are back-adjusted: no ~10x gap at NVDA 2024-06-10 (10:1 split) or ~4x gap at AAPL 2020-08-31 (4:1 split)
6. Capture the exact response body (success or error) in the dev handoff

**Expected outcome:** Real Stooq endpoint either serves valid, schema-correct, adjusted-basis CSVs, or fails with an honest documented error (key-gated, rate-limited, etc.).

**Pass criteria:**
- AAPL/SPY first bar ≤ 1996-01-05
- NVDA first bar in 1999 (±5 days tolerance for real listing variations)
- Schema validation: exactly 6 columns, header + date rows
- Split continuity: |1-day close return| at known split dates is bounded (no >2x gap)
- Probe outcome (success or documented blocker) is recorded in the dev handoff

---

### TC-08 — Validation suite: schema and data integrity (staged seed)

**Type:** artifact
**Preconditions:**
- Staged seed exists at `apps/backend/data/seed-stooq-30y/prices/*.csv` and `meta.json` (probe-success branch)
- Test module `apps/backend/tests/test_seed_staged_30y.py` has been created

**Steps:**
1. Run `pytest apps/backend/tests/test_seed_staged_30y.py -v`
2. Verify each CSV:
   - Header is present and exactly `date,open,high,low,close,volume`
   - All rows have 6 fields
   - Dates are strictly ascending, unique
   - Prices (open/high/low/close) are positive
   - Volume is non-negative
3. Verify depth anchors: AAPL + MSFT first bar ≤ 1996-01-05, NVDA first bar in 1999
4. Verify post-IPO honesty: COIN ≈ 2021-04-14, ARM ≈ 2023-09-14, HOOD ≈ 2021-07-29 (first bar never before real listing)

**Expected outcome:** All staged CSVs pass schema, ascending-date, positive-price, and depth-anchor checks.

**Pass criteria:**
- All tests pass (or skip-with-reason if staged dir is absent)
- 0 schema violations across ~590 CSVs
- 0 backwards-date anomalies
- 0 post-IPO names with fabricated early rows

---

### TC-09 — Validation suite: split continuity and adjusted basis

**Type:** artifact
**Preconditions:**
- Staged seed exists
- Dates 2024-06-10 (NVDA) and 2020-08-31 (AAPL) are in the staged data

**Steps:**
1. Run validation suite checking split continuity
2. For NVDA 2024-06-10 (10:1 split): calculate |1-day close return| across the split and verify it is bounded (no >2x jump due to unadjustment)
3. For AAPL 2020-08-31 (4:1 split): same check
4. Verify both are consistent across the full span (no adjustment seam mid-data)

**Expected outcome:** Split adjustments are continuous; no unadjusted seam in the middle of the history.

**Pass criteria:**
- |1-day return| at split date is within realistic bounds (e.g., <5% absolute return, allowing for market moves)
- Both stocks show adjustment consistency across the full span

---

### TC-10 — Validation suite: cross-vendor returns agreement (Stooq vs live seed)

**Type:** artifact
**Preconditions:**
- Staged Stooq seed exists
- Live Yahoo seed exists at `apps/backend/data/seed/prices/`
- Overlap period is 2021-01-04 to 2026-05-28 (or latest available)

**Steps:**
1. Run validation suite cross-check for AAPL/NVDA/SPY
2. Calculate daily 1-day close returns for each symbol over the overlap period from both seeds
3. Verify the returns byte-match within a small tolerance (e.g., <0.01% absolute deviation, accounting for rounding)
4. Confirm both bases are fully adjusted (split/dividend basis match)

**Expected outcome:** Stooq and Yahoo returns agree over the overlap, confirming adjustment basis consistency.

**Pass criteria:**
- Returns correlate >0.99 over the overlap period for all three symbols
- Max |return difference| <0.01% (rounding tolerance)

---

### TC-11 — Validation suite: manifest agreement with CSVs

**Type:** artifact
**Preconditions:**
- Staged seed exists with `meta.json` and `prices/*.csv`

**Steps:**
1. Run validation suite checking manifest metadata
2. For each symbol in `meta.json`, verify:
   - `first_bar` matches the first date in the CSV
   - `last_bar` matches the last date in the CSV
   - `bar_count` matches the number of rows in the CSV
   - `status` field (success/failed/not_found) is consistent with CSV existence

**Expected outcome:** Manifest metadata exactly matches the on-disk CSVs.

**Pass criteria:**
- 0 mismatches between manifest and CSV for first/last/bar-count across all ~590 symbols (or per-tier if partial run)

---

### TC-12 — Validation suite: pytest skip on absent staged dir

**Type:** artifact
**Preconditions:**
- Staged dir `apps/backend/data/seed-stooq-30y/` does not exist (probe-blocked branch)

**Steps:**
1. Run `pytest apps/backend/tests/test_seed_staged_30y.py -v`
2. Verify all tests skip with a clear reason (e.g., "Staged seed not found; probe may have been blocked")

**Expected outcome:** Tests skip gracefully without failing.

**Pass criteria:**
- All tests skip (exit 0)
- Skip message clearly explains the reason (missing staged dir, not an infrastructure failure)

---

### TC-13 — Regression: existing suites unedited and green

**Type:** api
**Preconditions:**
- Existing test modules exist: `test_referee.py`, `test_forward_walk.py`, `test_evidence.py`, `test_staging_ledger_routing.py`, `test_seed_integrity.py`, `test_stooq_provider.py`
- No pins or fixtures have been refreshed this iteration (live seed unchanged)

**Steps:**
1. Run the full backend test suite: `cd apps/backend && pytest tests/ -v`
2. Verify all existing tests pass without modification
3. Verify no test pins or golden values were updated
4. Verify `certified-claims.jsonl` and `staging-ledger.jsonl` are byte-identical (git diff shows no change)

**Expected outcome:** All existing suites pass; no byte-identity regression; ledgers untouched.

**Pass criteria:**
- All tests pass (0 failures, 0 errors)
- Exit code 0
- `git diff` shows no changes to existing test files
- Evidence ledgers byte-identical (verified via git status)

---

### TC-14 — Non-regression: byte-identity of app/ + frontend/ + config

**Type:** artifact
**Preconditions:**
- Current branch is `goal/mcp-loop`
- Git HEAD points to the phase's final commit (or pre-commit state before release-manager)

**Steps:**
1. Run `git diff HEAD -- apps/backend/app/ apps/frontend/ config.yaml`
2. Verify the output is empty (no changes)
3. Run `git diff HEAD -- runs/goal-session-mcp-loop/state/certified-claims.jsonl runs/goal-session-mcp-loop/state/staging-ledger.jsonl`
4. Verify both ledgers are byte-identical

**Expected outcome:** No runtime or configuration changes; ledgers untouched.

**Pass criteria:**
- Zero byte differences in app/, frontend/, or config.yaml
- Zero byte differences in both ledgers
- J-01, J-02, J-05, J-09 remain passing (deterministic replay of stored golden scripts)

---

### TC-15 — Coverage manifest artifact existence and completeness

**Type:** artifact
**Preconditions:**
- Staged seed ingest has completed (success or partial)
- Coverage manifest file should be at `reports/phase-goal-mcp-loop-iter-16-seed-coverage.md`

**Steps:**
1. Verify the file exists at the expected path
2. Verify it contains:
   - Fetched/missing/short-history counts by priority tier
   - Pool names Stooq lacks entirely
   - ETF/index coverage (^VIX explicitly called out — gap recorded if absent)
   - Rate-cap events and resume instructions (if applicable)
3. Verify the counts are consistent with the staged `meta.json` (or with the partial manifest if probe-blocked)

**Expected outcome:** Coverage manifest exists and accurately reports the ingest outcome.

**Pass criteria:**
- File exists at `reports/phase-goal-mcp-loop-iter-16-seed-coverage.md`
- Tier-1 and tier-2 counts are present and plausible
- ^VIX coverage is explicitly documented
- Counts sum to expected totals (~590 for successful run, partial for rate-capped run)

---

## Summary

**Total test cases:** 15
**API tests:** 7 (TC-01, TC-02, TC-03, TC-04, TC-05, TC-06, TC-07)
**Unit/integration tests:** 5 (TC-13 regression suite)
**Artifact checks:** 8 (TC-08, TC-09, TC-10, TC-11, TC-12, TC-14, TC-15 + validation-suite execution)

**Testing approach:**
- Unit tests (TC-01 through TC-06) use a stubbed/injectable StooqProvider to verify tool logic without network calls
- TC-07 is the mandatory real-system integration test (external integration testing honesty); outcome documented in dev handoff
- Validation suite (TC-08 through TC-12) runs over the staged seed (or skips gracefully if probe-blocked)
- Regression checks (TC-13, TC-14) verify zero app/frontend/config/ledger changes
- Coverage manifest (TC-15) documents the ingest outcome for iter-17 planning

**Pass criteria summary:**
- All tool functionality (provider routing, --out, --symbols-set, pinned-end, resume, priority ordering, error handling) works as specified
- Real Stooq probe outcome is documented (success or honest blocker) in the dev handoff
- Validation suite is green over staged data (or skips-with-reason if probe-blocked)
- Existing suites are unregressed; ledgers byte-identical; J-01/J-02/J-05/J-09 pass
- Coverage manifest accurately reports the ingest result
