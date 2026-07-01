# goal-mcp-loop-iter-10 Functional Test Plan

**Phase:** goal-mcp-loop-iter-10
**Date:** 2026-07-01
**Frontend Present:** no

## Phase Goal

Open the certification engine's multi-horizon aperture (h1, h5, h10, h20, h60) and run a fixed pre-registered set of single-factor hypotheses through the referee into an isolated STAGING ledger under the online-FDR economy, discovering which non-20-horizon cohorts clear the out-of-sample bar WITHOUT modifying the canonical ledger or user-facing surfaces. This discovery produces referee-scored candidates for iter-11 to promote to J-07.

## Test Cases

### TC-01 — Multi-horizon enumeration: horizons configured and enumerated

**Type:** artifact
**Preconditions:** 
- `config.yaml` contains `triad.horizons: [1, 5, 10, 20, 60]`
- `app.engine.triad_scan.scan_product_triad` is callable

**Steps:**
1. Read `config.yaml` and extract the `triad.horizons` value
2. Call `scan_product_triad()` or `scan_factor_decile_cells()` with the configured horizons
3. Collect all returned cells and group by horizon
4. Assert the set of horizons present matches exactly `{1, 5, 10, 20, 60}`
5. Count cells per horizon

**Expected outcome:** The scan enumerates cells for all five configured horizons; each horizon has a non-zero cell count
**Pass criteria:** Exact horizon set is `{1, 5, 10, 20, 60}` and per-horizon cell counts are consistent with the factor set and decile enumeration (e.g., per-horizon count = `num_factors × 2 deciles`)

---

### TC-02 — Multi-horizon enumeration: cell count scales with wider aperture

**Type:** artifact
**Preconditions:** 
- `config.yaml` has `triad.horizons: [1, 5, 10, 20, 60]` (5 horizons)
- Previous baseline: single-horizon (h20) enumeration produced N cells

**Steps:**
1. Run `scan_product_triad()` and count total cells across all horizons
2. Expected cell count = N_factors × 2 × 5 horizons (e.g., ~11 factors × 2 × 5 = ~110 cells)
3. Verify no duplicates across the cross-product

**Expected outcome:** Cell count scales proportionally with the 5-horizon aperture; no duplicate (factor, horizon, decile) tuples
**Pass criteria:** Total cells ≥ 100 and exact factor-horizon-decile tuples are unique (no cross-horizon collisions)

---

### TC-03 — Staging ledger routing: append to staging, never canonical

**Type:** api
**Preconditions:**
- `runs/goal-session-mcp-loop/state/certified-claims.jsonl` exists and is tracked in git (canonical ledger, unmodified by this iteration)
- `runs/goal-session-mcp-loop/state/staging-ledger.jsonl` does not exist or is empty before the test
- `config.yaml` has `evidence.fdr.enabled: true`

**Steps:**
1. Call `verify_edge(claim={"kind":"factor","factor":"vcp_contraction","slice_kind":"decile","decile":10,"horizon":10,"direction":"positive"}, ledger="staging", ledger_path=$STAGING_LEDGER_PATH, register_date="2024-06-01")`
2. Check that the verdict (PASS/FAIL/INSUFFICIENT) is appended to `staging-ledger.jsonl`
3. Check that `certified-claims.jsonl` remains unmodified (git diff shows no change)
4. Call `count_trials("canonical")` and record the divisor

**Expected outcome:** The staging verdict is written to the staging ledger file; the canonical ledger and canonical divisor are unchanged
**Pass criteria:** `staging-ledger.jsonl` contains exactly one entry; `certified-claims.jsonl` git-diff shows no modification; canonical `count_trials("canonical")` returns the pre-test value

---

### TC-04 — Honesty fence: canonical Bonferroni preserved with FDR enabled

**Type:** api
**Preconditions:**
- `config.yaml` has `evidence.fdr.enabled: true`
- A canonical claim with known deflation exists in `certified-claims.jsonl` (e.g., the leadership_score h20 claim with deflation="bonferroni")
- The canonical ledger has N_trials entries

**Steps:**
1. Call `verify_edge(claim=<existing_canonical_claim>, ledger="canonical", register_date="2024-06-01")`
2. Extract the returned `required_p` and `deflation` fields
3. Calculate expected strict-Bonferroni `required_p = alpha / N_trials` where alpha=0.05
4. Compare returned `required_p` against expected

**Expected outcome:** A canonical `verify_edge` call returns `deflation="bonferroni"` and `required_p = 0.05 / N_trials` (strict Bonferroni), byte-identically reproducible
**Pass criteria:** `required_p` exactly equals `0.05 / N_trials` and `deflation == "bonferroni"` (FDR routing does NOT apply to canonical claims)

---

### TC-05 — Online-FDR correctness: staging claims use FDR deflation

**Type:** api
**Preconditions:**
- `config.yaml` has `evidence.fdr.enabled: true`
- At least one staging verdict exists with a known rejection ordinal
- LORD++ rejection levels are deterministic for a fixed sequence

**Steps:**
1. Read the rejection times from an existing staging ledger (or invoke a test sequence)
2. Call `online_fdr.test_level(rejection_ordinals=[1, 2, 3, 4])` with a known deterministic sequence (no RNG, no IO)
3. Extract the returned FDR-adjusted levels
4. Verify levels are deterministic (re-run yields byte-identical values)

**Expected outcome:** `online_fdr.test_level` returns exact LORD++ alpha levels for the given rejection sequence; levels are weaker (higher) than strict Bonferroni
**Pass criteria:** Returned levels are deterministic and monotonically weaker than `0.05 / [1, 2, 3, 4]` (i.e., higher p-value thresholds)

---

### TC-06 — Pre-registered candidate set: configured, mirrored, and exploration iterates only the set

**Type:** artifact
**Preconditions:**
- `config.yaml` contains a `triad.candidates` section with the 4 pre-registered candidates
- `project-extensions/proposer-guidance.md` mirrors the same candidate set with rationales

**Steps:**
1. Read the `triad.candidates` list from `config.yaml`
2. Parse the list and verify exactly 4 entries: vcp_contraction h10, vcp_contraction h60, rs_spy_3m h60, leadership_score h60
3. Read `project-extensions/proposer-guidance.md` and locate the candidate section
4. Assert the mirrored list matches the config exactly (same order, same rationales)
5. Run the staging exploration function and verify it iterates ONLY these 4 candidates (count staging verdicts = 4)

**Expected outcome:** Config and guidance file contain exactly the same 4 pre-registered candidates; the exploration produces exactly 4 staging verdicts, one per candidate
**Pass criteria:** `config.yaml` has `triad.candidates: [...]` with length 4; `proposer-guidance.md` contains an identical list; staging ledger contains exactly 4 entries post-exploration

---

### TC-07 — Deterministic staging exploration: byte-identical re-run

**Type:** artifact
**Preconditions:**
- Seed `walk_forward.control_group.seed = 20240601` is set in `config.yaml`
- `runs/goal-session-mcp-loop/state/staging-ledger.jsonl` exists with 4 verdicts from the first run
- All config values (horizons, candidates, register dates) are fixed

**Steps:**
1. Back up the current `staging-ledger.jsonl`
2. Delete `staging-ledger.jsonl`
3. Re-run the staging exploration function with identical config and seed
4. Compare the new ledger line-by-line against the backed-up version

**Expected outcome:** The re-run produces a byte-identical staging ledger (same p-values, same status, same deflation values)
**Pass criteria:** Diff between the two staging-ledger.jsonl files is zero-byte (perfect match)

---

### TC-08 — No-lookahead: forward returns use bars > as-of at each horizon

**Type:** api
**Preconditions:**
- A staging verdict exists for a candidate at a non-20 horizon (e.g., vcp_contraction h10)
- The referee uses a sealed temporal holdout split

**Steps:**
1. Locate the cohort's as-of dates from the snapshot
2. Extract the forward returns used for the holdout test at the new horizon (h10)
3. Verify that all forward-return bars are > as-of date (no lookahead)
4. Compare the holdout split: first N/2 dates for training, final N/2 for holdout

**Expected outcome:** Forward returns come only from bars > as-of at each new horizon; the holdout split is temporally correct and does not leak training data
**Pass criteria:** Every forward-return observation has `bar > as_of_date` and the holdout split is contiguous in time (no interleaving)

---

### TC-09 — Canonical byte-identity: certified-claims.jsonl unmodified, proven_signals unchanged

**Type:** artifact
**Preconditions:**
- `certified-claims.jsonl` is git-tracked and unmodified at the start of the iteration
- `proven_signals` in the referee is set to `{leadership_score}`

**Steps:**
1. Run the full iteration (dev through QA)
2. Execute `git diff certified-claims.jsonl` and record the diff
3. Execute `git diff` on the entire `apps/backend/app/engine/` directory for any reference to `proven_signals`
4. Verify `GET /api/evidence` returns the same payload as before (byte-compare)

**Expected outcome:** `certified-claims.jsonl` has no modifications; `proven_signals` remains exactly `{leadership_score}`; `/api/evidence` response is byte-identical
**Pass criteria:** Git diff is empty for both files; API response byte-matches a known golden copy

---

### TC-10 — Default-path regression proof: unedited unit tests pass

**Type:** artifact
**Preconditions:**
- Unit tests `test_referee.py`, `test_forward_walk.py`, `test_evidence.py` exist and have frozen-golden expectations
- These files are NOT edited during this iteration (editing = regression signal)

**Steps:**
1. Verify that `test_referee.py`, `test_forward_walk.py`, `test_evidence.py` have no git modifications
2. Run `pytest apps/backend/tests/test_referee.py -v` and record the output
3. Run `pytest apps/backend/tests/test_forward_walk.py -v` and record the output
4. Run `pytest apps/backend/tests/test_evidence.py -v` and record the output
5. Count the total pass/fail

**Expected outcome:** All three test files are unedited; all tests pass
**Pass criteria:** No modifications to the test files; 100% of test cases pass (e.g., `passed = N, failed = 0`)

---

### TC-11 — Multi-horizon staging exploration: 4 candidates produce 4 verdicts

**Type:** artifact
**Preconditions:**
- Config has 4 pre-registered candidates
- Staging ledger is empty or freshly initialized
- The staging exploration function is implemented and callable

**Steps:**
1. Call the staging exploration function (e.g., `app.engine.triad_scan.run_multi_horizon_staging_exploration()`)
2. Wait for completion
3. Read `staging-ledger.jsonl` and count entries
4. For each entry, verify the structure: `factor`, `horizon`, `p_value`, `status` (PASS/FAIL/INSUFFICIENT), `deflation`, `required_p`

**Expected outcome:** Exactly 4 verdicts are written, one per candidate; each carries valid p-value, status, and deflation
**Pass criteria:** Staging ledger has exactly 4 lines; each JSON object contains all required fields; `status` is one of `{PASS, FAIL, INSUFFICIENT}`

---

### TC-12 — Error path: INSUFFICIENT candidate is recorded, not silently dropped

**Type:** artifact
**Preconditions:**
- One of the pre-registered candidates is infeasible (e.g., a horizon with insufficient post-snapshot bars or a cohort too thin for block bootstrap)
- The exploration function handles infeasible candidates gracefully

**Steps:**
1. Identify which candidate is expected to be infeasible (check the specific horizon and snapshot date range)
2. Run the staging exploration
3. Read `staging-ledger.jsonl` and find the entry for that candidate
4. Assert the `status` field is `"INSUFFICIENT"`
5. Verify the iteration does not crash

**Expected outcome:** An infeasible candidate is recorded with `status: "INSUFFICIENT"` in the staging ledger; the iteration completes without error
**Pass criteria:** The staging ledger contains an `INSUFFICIENT` entry and the exploration function returns successfully (exit code 0)

---

### TC-13 — Staging isolation: no staging references reach evidence.py or GET /api/evidence

**Type:** api
**Preconditions:**
- The entire iteration diff is available (git diff)
- `apps/backend/app/routes/evidence.py` exists and serves `GET /api/evidence`

**Steps:**
1. Inspect `apps/backend/app/routes/evidence.py` for any reference to "staging" or `staging_ledger`
2. Inspect the referee routing logic in `app.engine.referee` for any staging-related paths in the canonical route
3. Run `grep -r "staging" apps/backend/app/routes/ apps/backend/app/engine/evidence.py | grep -v test`
4. Verify zero matches (or only in comments/strings unrelated to execution)

**Expected outcome:** No staging ledger references are wired into the canonical evidence route
**Pass criteria:** Grep returns zero hits in production code paths (tests and comments excluded)

---

### TC-14 — Config changes: triad.top_k raised, haircut_coef set, horizons configured

**Type:** artifact
**Preconditions:**
- `config.yaml` is the source of truth for configuration values

**Steps:**
1. Read `config.yaml` and extract `triad.top_k` value
2. Verify it is raised above the previous default (e.g., 20 → 40 or similar for 5× aperture)
3. Extract `triad.screen.haircut_coef` value
4. Verify it is non-zero and scaled appropriately (e.g., 0.001 → higher value)
5. Verify `evidence.fdr.enabled: true` is set

**Expected outcome:** Config values reflect the multi-horizon scaling; FDR is explicitly enabled for this iteration
**Pass criteria:** `triad.top_k > 20`; `triad.screen.haircut_coef > 0.001`; `evidence.fdr.enabled == true`

---

### TC-15 — Handoff artifacts: dev handoff and audit handoff exist

**Type:** artifact
**Preconditions:**
- Iteration is complete (dev, review, QA stages finished)

**Steps:**
1. Check that `docs/handoffs/goal-mcp-loop-iter-10-dev.md` exists
2. Verify it contains per-candidate block-bootstrap `p_value` and whether each clears `p < 0.010`
3. Check that `docs/handoffs/goal-mcp-loop-iter-10-audit.md` exists (to be written by the auditor)
4. Verify the audit handoff documents the honesty fence check (canonical Bonferroni verified)

**Expected outcome:** Both handoff files exist and are non-empty; dev handoff lists all 4 candidates with their p-values and pass/fail status relative to divisor-5 threshold
**Pass criteria:** File `docs/handoffs/goal-mcp-loop-iter-10-dev.md` exists and contains `p_value` for each candidate; file `docs/handoffs/goal-mcp-loop-iter-10-audit.md` exists and documents fence verification

---

## Summary

**Total test cases:** 15
**API tests:** 7 (TC-03, TC-04, TC-05, TC-08, TC-09, TC-10, TC-13)
**Artifact checks:** 8 (TC-01, TC-02, TC-06, TC-07, TC-11, TC-12, TC-14, TC-15)

All test cases are backend-only (Frontend Present: no); browser tests are not applicable. Tests validate configuration, multi-horizon enumeration, staging ledger isolation, canonical byte-identity, FDR correctness, determinism, and error handling per the DEFINITION OF DONE and TESTING REQUIREMENTS in the phase spec.
