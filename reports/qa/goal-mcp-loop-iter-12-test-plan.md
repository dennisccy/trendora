# goal-mcp-loop-iter-12 Functional Test Plan

**Phase:** goal-mcp-loop-iter-12  
**Date:** 2026-07-01  
**Frontend Present:** no

## Phase Goal

Register a pre-registered set of three 2-factor combination candidates in config, implement a combination staging explorer to certify each through the referee via `verify_edge(ledger="staging")`, and append verdicts to the internal staging ledger—enabling iter-13 to promote a winner and surface J-08. Zero user-facing change.

## Test Cases

### TC-01 — Configuration Candidates Registered

**Type:** artifact  
**Preconditions:** Git HEAD contains the phase changes; `config.yaml` exists at the repo root.

**Steps:**
1. Open `config.yaml` and search for `triad.combination_candidates` block.
2. Verify it contains exactly three entries with the registered pairs (exact order and details):
   - `rs_spy_3m:top:quintile` + `atr_pct:bottom:tertile`
   - `leadership_score:top:quintile` + `atr_pct:bottom:tertile`
   - `rs_spy_3m:top:quintile` + `high_proximity:top:tertile`
3. For each entry, verify `horizon: 20`, `direction: positive`, and a one-line economic rationale.
4. Open `project-extensions/proposer-guidance.md` and verify §4.2 exists with the SAME three pairs and rationales verbatim.

**Expected outcome:** Config block exists with exactly three pre-registered pairs; proposer-guidance.md mirrors them VERBATIM.  
**Pass criteria:** `git diff HEAD -- config.yaml | grep -A 30 "combination_candidates"` shows three entries; `grep -A 30 "§4.2" project-extensions/proposer-guidance.md | grep "rs_spy_3m:top:quintile"` matches config.

---

### TC-02 — Claim Shape and Projection

**Type:** api  
**Preconditions:** Backend is built; test imports `apps/backend/app/engine/triad_scan.py` and the referee tools.

**Steps:**
1. Invoke `explore_combination_staging(cfg=<config>)` (or equivalent entry point) with the registered config block.
2. For each of the three combinations, inspect the projected claim dict before it is certified.
3. Verify each claim has the exact shape: `{"kind":"combination", "cohort":"composite", "horizon":20, "direction":"positive", "condition":[leg1, leg2]}`.
4. Verify each `condition` leg is a string matching `<factor>:<side>:<quantile>` (e.g., `"rs_spy_3m:top:quintile"`).

**Expected outcome:** Each registered combination is projected into the correct claim shape with `kind="combination"`, `cohort="composite"`, `horizon=20`, and a two-element `condition` array.  
**Pass criteria:** `assert claim["kind"] == "combination" and len(claim["condition"]) == 2 and claim["cohort"] == "composite"` for all three claims in test output.

---

### TC-03 — Verdicts Routed to Staging Ledger Only

**Type:** artifact  
**Preconditions:** Backend is built; `runs/goal-session-mcp-loop/state/staging-ledger.jsonl` exists and contains 4 prior single-factor entries (from iter-10).

**Steps:**
1. Run `explore_combination_staging(...)` to completion (or the equivalent explorer invocation that certifies the three combinations).
2. Read the final staging ledger file line-by-line.
3. Count total entries; verify count increased from 4 to 7.
4. For each of the 3 NEW entries (trials #5–7), verify they carry: `status`, block-bootstrap `p_value`, `holdout_edge`, `control_excess`, `cohort_n`, `control_n`, `deflation`, `required_p`, `horizon`, and `condition` legs (the fields iter-13 reads).
5. Open `certified-claims.jsonl` (canonical ledger) and verify it contains exactly 5 entries (byte-identical to HEAD).

**Expected outcome:** Three combination verdicts appended to staging ledger (7 total); canonical ledger untouched (5 entries).  
**Pass criteria:** `wc -l runs/goal-session-mcp-loop/state/staging-ledger.jsonl` shows 7 lines; `git diff HEAD -- certified-claims.jsonl | wc -l` is 0 (no diff).

---

### TC-04 — Fail-Closed Guard Refuses Canonical Ledger

**Type:** api  
**Preconditions:** Backend is built; test can invoke `explore_combination_staging(...)` with a manual ledger path override.

**Steps:**
1. Call `explore_combination_staging(...)` with the `ledger_path` parameter explicitly set to the canonical ledger path (`cfg.evidence.ledger_path`).
2. Expect a `ValueError` to be raised before any write occurs.
3. Verify the error message mentions the ledger path guard (e.g., "ledger path must be staging, not canonical").

**Expected outcome:** Explorer raises `ValueError` and refuses to run when pointed at canonical ledger.  
**Pass criteria:** `pytest` output shows `test_combination_staging_explorer_refuses_canonical_ledger PASSED` and exception message contains "staging" or "canonical" guard text.

---

### TC-05 — Determinism: Reset Re-run Yields Byte-Identical Verdicts

**Type:** api  
**Preconditions:** Backend is built with a controlled test DB state; test creates a fresh temp staging ledger file.

**Steps:**
1. Run `explore_combination_staging(reset=True, temp_ledger_path="temp.jsonl")` to completion, capturing the three verdicts.
2. Wipe temp.jsonl and re-run the same command with identical config and DB state.
3. Read both runs and compare the three combination verdict entries (verdicts #5–7 or their equivalents).
4. Verify block-bootstrap `p_value`, `holdout_edge`, `control_excess`, `cohort_n` are byte-identical between runs.

**Expected outcome:** Two consecutive `reset=True` runs produce byte-identical combination verdicts.  
**Pass criteria:** `md5sum(verdicts_run1) == md5sum(verdicts_run2)` for the three combination entries; `pytest` output shows `test_determinism_combination_staging PASSED`.

---

### TC-06 — Canonical Byte-Identity / No Drift

**Type:** artifact  
**Preconditions:** Git HEAD contains iter-12 implementation; canonical ledger and evidence API are in place.

**Steps:**
1. Run `git diff HEAD -- certified-claims.jsonl` and verify diff is empty (no changes to the five canonical entries).
2. Call `curl -s http://localhost:8000/api/evidence | jq '.proven_signals'` and compare to the known-good value (should be `{"leadership_score": ...}`).
3. Run the DO-NOT-EDIT test suites: `pytest apps/backend/tests/test_referee.py -v`, `pytest apps/backend/tests/test_forward_walk.py -v`, `pytest apps/backend/tests/test_evidence.py -v`.
4. Verify all three suites pass and contain NO edited expectations (assertions still match the five canonical entries, not seven).

**Expected outcome:** Canonical ledger unchanged; evidence API returns byte-identical `proven_signals`; all default-path tests pass UNEDITED.  
**Pass criteria:** `git diff HEAD -- certified-claims.jsonl | wc -l` is 0; `test_referee.py::*`, `test_forward_walk.py::*`, `test_evidence.py::*` all PASS; no diff on test assertion lines.

---

### TC-07 — Error Case: Unknown Factor Key

**Type:** api  
**Preconditions:** Backend is built; test can inject a malformed config entry.

**Steps:**
1. Inject a config entry with an unknown factor key (e.g., `unknown_factor:top:quintile`).
2. Call `explore_combination_staging(...)` with the malformed config.
3. Expect a `ValueError` to be raised during factor resolution (not silently skipped).

**Expected outcome:** Explorer raises `ValueError` for unknown factor key.  
**Pass criteria:** `pytest` output shows `test_combination_staging_unknown_factor_raises_error PASSED` and exception message mentions the unknown factor.

---

### TC-08 — Error Case: Malformed Condition String

**Type:** api  
**Preconditions:** Backend is built; test can inject a config entry with an invalid `condition` format.

**Steps:**
1. Inject a config entry with a malformed `condition` string (e.g., `"rs_spy_3m_top_quintile"` instead of `"rs_spy_3m:top:quintile"`).
2. Call `explore_combination_staging(...)` with the malformed config.
3. Expect a `ValueError` to be raised during condition parsing (not silently skipped).

**Expected outcome:** Explorer raises `ValueError` for malformed condition format.  
**Pass criteria:** `pytest` output shows `test_combination_staging_malformed_condition_raises_error PASSED` and exception message mentions condition format.

---

### TC-09 — Error Case: Invalid Quantile in Condition

**Type:** api  
**Preconditions:** Backend is built; test can inject a config entry with an out-of-range quantile.

**Steps:**
1. Inject a config entry with an invalid quantile key (e.g., `"rs_spy_3m:top:decile"` where only quintile/tertile are valid).
2. Call `explore_combination_staging(...)` with the malformed config.
3. Expect a `ValueError` to be raised during quantile validation (not silently skipped).

**Expected outcome:** Explorer raises `ValueError` for invalid quantile.  
**Pass criteria:** `pytest` output shows `test_combination_staging_invalid_quantile_raises_error PASSED` and exception message mentions the invalid quantile.

---

### TC-10 — Honesty Fence Unchanged: FDR Gating

**Type:** api  
**Preconditions:** Backend is built; test can inspect the referee certification logic.

**Steps:**
1. Review the referee code path (`verify_edge` / `certify_edge` / `_cert_online_fdr`) for the line: `use_fdr = (ledger == LEDGER_STAGING and evidence.fdr.enabled)`.
2. Verify that canonical certification (ledger != STAGING) always uses strict Bonferroni, never FDR.
3. Verify that staging certification (ledger == STAGING) uses FDR only if `evidence.fdr.enabled` is true.
4. Confirm the three registered combinations run under the staging gate (ledger="staging") and thus use FDR economy.

**Expected outcome:** Canonical and staging certifications respect the FDR fence; no badge is lit by the combination staging exploration (internal-only).  
**Pass criteria:** `git diff HEAD -- apps/backend/app/engine/referee.py | grep -A 2 "use_fdr ="` shows no changes to the gating logic; `grep "use_fdr.*staging" apps/backend/app/engine/referee.py` confirms condition exists and is unchanged.

---

### TC-11 — Journey Status: J-08 Remains Unknown

**Type:** artifact  
**Preconditions:** Git HEAD contains iter-12 implementation; journey-history.json exists in the goal-session state.

**Steps:**
1. Open `runs/goal-session-mcp-loop/state/journey-history.json`.
2. Find the entry for journey J-08.
3. Verify its `status` is `"unknown"` (NOT `"passed"` or any other value).
4. Verify J-01 through J-07 all have `status: "passed"` and have NOT been modified by iter-12.

**Expected outcome:** J-08 remains `unknown`; J-01..J-07 remain `passed`.  
**Pass criteria:** `jq '.journeys[] | select(.id == "J-08") | .status' runs/goal-session-mcp-loop/state/journey-history.json` outputs `"unknown"`; `jq '.journeys[] | select(.id | startswith("J-0")) | select(.id != "J-08") | .status' runs/goal-session-mcp-loop/state/journey-history.json` outputs only `"passed"`.

---

### TC-12 — No Anti-Goal Violations Introduced

**Type:** artifact  
**Preconditions:** Git HEAD contains iter-12 implementation; diff can be scanned.

**Steps:**
1. Run `git diff HEAD -- apps/backend | grep -i "buy\|sell\|price.*target\|return.*promise\|predict"` and verify no matches (anti-goal #2 / decision-quality only).
2. Run `git diff HEAD -- apps/backend | grep -i "api.*key\|secret\|credential"` and verify no hardcoded secrets (anti-goal #7 / security).
3. Read the phase spec notes; confirm all seven anti-goals are upheld (FDR fence, Bonferroni canonical, determinism, no secrets, no return/price/buy-sell language, no data-mining overfit, preserve byte-identity).

**Expected outcome:** No anti-goal violations; secret scan and decision-language scan are clean.  
**Pass criteria:** `grep "anti_goal_violations" runs/goal-session-mcp-loop/state/iteration-N.json` shows `[]` (empty list); no diff matches the forbidden patterns above.

---

### TC-13 — Staging Golden Test Updated (Expected Change)

**Type:** artifact  
**Preconditions:** Git HEAD contains iter-12 implementation; staging ledger test exists.

**Steps:**
1. Open `apps/backend/tests/test_staging_ledger_routing.py` and find the test `test_committed_staging_ledger_is_the_frozen_multi_horizon_discovery`.
2. Verify the test expectation/golden value has been updated from 4 entries to 7 entries (this is an EXPECTED change, not a regression).
3. Verify that `test_online_fdr.py::test_test_level_matches_iter10_staging_exploration_sequence` still passes without edit (trials #1–4 unchanged; only #5–7 appended).

**Expected outcome:** Staging golden test updated to 7 entries; online-FDR test for trials #1–4 still passes.  
**Pass criteria:** `grep "assert.*len.*staging" apps/backend/tests/test_staging_ledger_routing.py` shows expectation of 7 (not 4); `pytest apps/backend/tests/test_online_fdr.py::test_test_level_matches_iter10_staging_exploration_sequence -v` shows PASSED.

---

### TC-14 — Dev Handoff Written

**Type:** artifact  
**Preconditions:** Phase implementation is complete.

**Steps:**
1. Verify `docs/handoffs/goal-mcp-loop-iter-12-dev.md` exists.
2. Check it contains the standard sections: What Was Built, Files Changed, Tests Run, Known Issues, Suggested Next Phase.
3. Verify "Tests Run" section lists the exact pytest commands used and reports counts of passed tests (e.g., "pytest apps/backend/tests/... —v → 14 passed").

**Expected outcome:** Dev handoff exists and is complete.  
**Pass criteria:** File exists at `docs/handoffs/goal-mcp-loop-iter-12-dev.md`; contains "What Was Built", "Files Changed", "Tests Run", "Known Issues", "Suggested Next Phase" sections; "Tests Run" reports exact test counts.

---

## Summary

**Total test cases:** 14  
**API tests:** 6 (TC-02, TC-04, TC-05, TC-07, TC-08, TC-09, TC-10)  
**Artifact checks:** 8 (TC-01, TC-03, TC-06, TC-11, TC-12, TC-13, TC-14)

**Test coverage:**
- Configuration registration and mirroring (TC-01)
- Claim shape and projection (TC-02)
- Routing to staging ledger only (TC-03)
- Fail-closed guard (TC-04)
- Determinism under reset (TC-05)
- Canonical byte-identity and no drift (TC-06)
- Error handling: unknown factor, malformed condition, invalid quantile (TC-07, TC-08, TC-09)
- FDR gating / honesty fence (TC-10)
- Journey status preservation (TC-11)
- Anti-goal compliance (TC-12)
- Staging test golden update and online-FDR sequence (TC-13)
- Dev handoff (TC-14)

All tests are backend-focused (no browser tests required; Frontend Present: no). Tests verify the internal staging exploration runs correctly, verdicts are recorded, canonical ledger remains untouched, and all error cases are caught loudly.
