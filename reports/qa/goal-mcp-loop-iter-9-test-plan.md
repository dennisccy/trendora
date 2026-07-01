# goal-mcp-loop-iter-9 Functional Test Plan

**Phase:** goal-mcp-loop-iter-9
**Date:** 2026-07-01
**Frontend Present:** no

## Phase Goal

Stand up the sustainable trial economy — an injectable, default-off online-FDR (LORD++) deflation policy running in a separate internal staging ledger — so future iterations can explore multi-horizon and multi-factor-combination edges (J-07, J-08) without permanently tightening the user-facing canonical Bonferroni bar, while the canonical `/evidence` ledger and every "Proven" badge stay byte-identical.

## Test Cases

### TC-01 — Online-FDR module is pure and deterministic

**Type:** artifact
**Preconditions:** `apps/backend/app/engine/online_fdr.py` exists and contains the LORD++ test_level allocation logic.

**Steps:**
1. Run the unit test suite for the new online_fdr module: `pytest apps/backend/tests/test_online_fdr.py -v`
2. Verify the test passes that allocates `test_level` from a known rejection-offset sequence (e.g., `[1, 2, 4]` corresponding to PASS entries in the canonical ledger)
3. Run the same test 3 times in sequence and verify the output is byte-identical each time (no RNG, no IO side effects)

**Expected outcome:** The allocated `test_level` is computed deterministically and consistently across runs.

**Pass criteria:** The pytest test `test_online_fdr.py` passes with exit code 0 and logs show `test_level` value is identical across three sequential runs for the same input rejection offsets.

---

### TC-02 — Canonical ledger entries are byte-identical (LOAD-BEARING INVARIANT)

**Type:** artifact
**Preconditions:** The application is built and ready to serve the evidence API; the canonical `certified-claims.jsonl` exists with the expected 4 existing entries.

**Steps:**
1. Run: `curl -s http://localhost:8000/api/evidence | jq .`
2. Capture the entire `GET /api/evidence` response and compare it against a frozen golden copy
3. Verify the 4 canonical ledger entries (`deflation="bonferroni"`, divisors 1–4; line 3 is a FAIL) are unchanged
4. Verify `proven_signals` in the payload equals exactly `["leadership_score"]`

**Expected outcome:** The `/api/evidence` payload is byte-identical to the frozen golden, and no canonical entry has been modified or moved.

**Pass criteria:** Exact JSON byte-match between the current `/api/evidence` payload and the pre-iteration frozen golden; `proven_signals == ["leadership_score"]` (no new signals introduced).

---

### TC-03 — Defaults reproduce today (Bonferroni unchanged)

**Type:** artifact
**Preconditions:** Existing unit tests exist for `test_referee.py`, `test_ledger.py`, `test_evidence.py`, and `test_forward_walk.py`.

**Steps:**
1. Run the existing test suite with no changes to test expectations: `pytest apps/backend/tests/test_referee.py apps/backend/tests/test_forward_walk.py -v`
2. Verify all tests pass without expectation edits
3. Verify a test that calls `certify_edge(...)` with default parameters reproduces the identical `required_p`, `deflation_divisor`, and verdict as before the changes

**Expected outcome:** All existing referee and forward-walk tests pass without modification.

**Pass criteria:** Exit code 0 from the test run; no failures or assertion edits in the test suite; `required_p` and `deflation_divisor` values match the pre-iteration expected values.

---

### TC-04 — Ledger rejection_offsets accessor derives PASS-entry ordinals

**Type:** artifact
**Preconditions:** `apps/backend/app/engine/ledger.py` has been extended with a `rejection_offsets()` method; the canonical ledger exists.

**Steps:**
1. Run: `python3 -c "from app.engine.ledger import Ledger; l = Ledger.load('runs/goal-session-mcp-loop/state/certified-claims.jsonl'); print(l.rejection_offsets())"`
2. Capture the output and verify it returns `[1, 2, 4]` (the ordinals of the PASS entries in the canonical ledger)
3. Verify the method does not rewrite any entries

**Expected outcome:** The `rejection_offsets()` method returns `[1, 2, 4]` derived from the live canonical ledger.

**Pass criteria:** Output equals `[1, 2, 4]`; no entries in `certified-claims.jsonl` have been added, modified, or deleted.

---

### TC-05 — Staging ledger is routed and isolated

**Type:** artifact
**Preconditions:** `apps/backend/app/mcp/tools.py` has been updated to route `verify_edge` based on target ledger; `STAGING_LEDGER_PATH` and `LEDGER_PATH` environment variables are set.

**Steps:**
1. Run an integration test that calls `verify_edge(...)` with `ledger="staging"` and captures the written entry
2. Verify the entry was written to the staging ledger file (at `$STAGING_LEDGER_PATH`) and NOT to the canonical file
3. Run a test that calls `verify_edge(...)` with `ledger="canonical"` and verify it writes to `$LEDGER_PATH` only
4. Verify no cross-contamination (staging entry does not appear in canonical, and vice versa)

**Expected outcome:** Staging and canonical ledgers are isolated; each claim writes to its target ledger only.

**Pass criteria:** Integration test passes; staging-routed claim is found in `$STAGING_LEDGER_PATH` only; canonical-routed claim is found in `$LEDGER_PATH` only.

---

### TC-06 — Forward_walk reproduces verdict from recorded required_p

**Type:** artifact
**Preconditions:** `apps/backend/app/engine/forward_walk.py` has been updated to reconstruct `test_level` from recorded `required_p`.

**Steps:**
1. Run the unit test for `forward_walk` that re-scores an existing verdict entry and checks byte-for-byte reproduction
2. Verify that reconstructing `test_level` from the recorded `required_p` yields the identical verdict as the original
3. Verify the re-score logic for both Bonferroni (canonical) and online-FDR (staging) entries reproduces correctly

**Expected outcome:** A re-scored verdict matches the original verdict byte-for-byte when using the recorded `required_p`.

**Pass criteria:** Test passes; `verdict.status`, `verdict.required_p`, and `verdict.deflation_divisor` match the original for both canonical and staging entries.

---

### TC-07 — Configuration loading with FdrCfg defaults

**Type:** artifact
**Preconditions:** `apps/backend/app/config.py` defines `FdrCfg` with defaults that disable FDR; `config.yaml` includes the new `evidence.fdr` and `evidence.staging_ledger_path` blocks.

**Steps:**
1. Run: `pytest apps/backend/tests/test_config.py::test_fdr_config_defaults -v`
2. Verify a configuration predating the FdrCfg block (without the new keys) still loads without error
3. Verify the loaded `EvidenceCfg` has `fdr.enabled == False` by default
4. Verify `staging_ledger_path` defaults to a documented path (or is required, with clear error if missing)

**Expected outcome:** Configuration loads successfully with backward compatibility; FDR is off by default.

**Pass criteria:** Test passes; `config.evidence.fdr.enabled == False`; no breaking change to existing config parsing.

---

### TC-08 — Malformed FdrCfg raises ConfigError (not silent weakening)

**Type:** artifact
**Preconditions:** The config loader attempts to parse `config.yaml` with an invalid FDR configuration.

**Steps:**
1. Create a test config file with malformed `fdr` settings (e.g., invalid `alpha` type or missing required field)
2. Attempt to load it: `python3 -c "from app.config import Config; Config.load('malformed.yaml')"`
3. Verify a `ConfigError` is raised with a clear error message (not silently falling back or weakening the bar)

**Expected outcome:** Malformed configuration triggers a loud, documented error.

**Pass criteria:** `ConfigError` is raised; error message mentions the malformed field and suggests a fix.

---

### TC-09 — Gate routes claims by ledger key (default: staging)

**Type:** artifact
**Preconditions:** `project-extensions/gates/verify_claim.py` reads the optional `"ledger"` key on each claim and routes accordingly.

**Steps:**
1. Run an integration test that processes a claim with no explicit `"ledger"` key and verifies it routes to staging by default
2. Run a test with `"ledger": "canonical"` and verify it routes to canonical
3. Run a test with an unrecognized ledger value (e.g., `"ledger": "invalid"`) and verify the gate fails (exit 3) instead of silently certifying

**Expected outcome:** The gate correctly routes claims based on the ledger key; unrecognized values fail safely.

**Pass criteria:** Default routing test passes; canonical routing test passes; invalid ledger value causes `exit 3` (fail-closed, no certification).

---

### TC-10 — STAGING_LEDGER_PATH and LEDGER_PATH exported in run-goal.sh

**Type:** artifact
**Preconditions:** `scripts/automation/run-goal.sh` has been updated to export both environment variables at the two dispatch sites.

**Steps:**
1. Source the script and inspect the environment at the dispatch points (around lines 1070 and 1401)
2. Run: `bash -x scripts/automation/run-goal.sh --session-id test-qa 2>&1 | grep -E "STAGING_LEDGER_PATH|LEDGER_PATH"`
3. Verify both variables are set and point to valid paths

**Expected outcome:** Both `STAGING_LEDGER_PATH` and `LEDGER_PATH` are exported at both dispatch sites.

**Pass criteria:** Both variables are set and non-empty; staging path and canonical path are distinct.

---

### TC-11 — Unset ledger paths fail-closed (no silent canonical write)

**Type:** artifact
**Preconditions:** A claim requires `LEDGER_PATH` or `STAGING_LEDGER_PATH`, but the variable is unset.

**Steps:**
1. Unset the required ledger environment variable: `unset STAGING_LEDGER_PATH`
2. Run `verify_edge(...)` for a staging-routed claim and verify it fails with a clear error (not writing to a default/fallback path)
3. Verify the canonical ledger remains unchanged

**Expected outcome:** Missing ledger path causes a fail-closed error, never a silent write.

**Pass criteria:** An error is raised (not a silent fallback); canonical ledger is unmodified; error message mentions the missing path.

---

### TC-12 — J-01 through J-06 regression (canonical evidence unchanged)

**Type:** artifact
**Preconditions:** The goal-mode deterministic golden-script replay is configured for journeys J-01 through J-06.

**Steps:**
1. Run the goal-mode deterministic golden-script replay: `bash scripts/automation/lib/replay_golden_evidence.sh`
2. Verify each of J-01, J-02, J-03, J-04, J-05, J-06 passes
3. Verify the displayed evidence badges on all surfaces (Dashboard, Stocks, Research labs, `/evidence`) match the canonical frozen golden
4. Verify `proven_signals == {leadership_score}` on each pass

**Expected outcome:** All Required-still-passing journeys (J-01..J-06) remain green and evidence-identical.

**Pass criteria:** All 6 journeys pass; evidence badges are byte-identical to pre-iteration golden; no regression in evidence display.

---

### TC-13 — J-07 and J-08 remain unbuilt (no regression to worse state)

**Type:** artifact
**Preconditions:** The journey-history.json tracks J-07 and J-08 status; they are currently "unknown" or "unbuilt".

**Steps:**
1. Check the journey-history status for J-07 and J-08: `jq '.journeys | map(select(.id == "J-07" or .id == "J-08"))' runs/goal-session-mcp-loop/journey-history.json`
2. Verify the status remains "unknown" or "unbuilt" (not regressed to "failing")

**Expected outcome:** Target journeys J-07 and J-08 do not regress; they remain unbuilt as expected.

**Pass criteria:** J-07 and J-08 status in journey-history.json is NOT "failing"; remains "unknown" or unchanged from pre-iteration.

---

### TC-14 — No anti-goal violations (determinism, no lookahead, no secrets)

**Type:** artifact
**Preconditions:** The implementation code and configuration files are ready for audit.

**Steps:**
1. Run a secret scan on the diff: `git diff --cached | grep -iE 'api.?key|secret|password|token|credential'`
2. Run a determinism check on the online-FDR module: verify no use of `random`, `time.time()`, or other non-deterministic functions
3. Run a lookahead check on the scoring: verify all score bars are `<= as_of` and forward returns are `> as_of` (no forward-looking bias)
4. Scan for buy/sell/return/price language: `grep -r 'buy\|sell\|return\|alpha\|price target' apps/backend/ --exclude-dir=tests`

**Expected outcome:** No secrets, no non-determinism in online-FDR, no lookahead, no return/price/buy-sell language.

**Pass criteria:** Secret scan returns 0 matches; online-FDR uses only deterministic operations; scoring bars follow the no-lookahead contract; no forbidden language in the implementation.

---

## Summary

**Total test cases:** 14
- **Artifact checks:** 14
- **API tests:** 0
- **Browser tests:** 0

**Scope notes:**
- This is a backend-infrastructure iteration with zero frontend changes.
- Frontend Present: no — no Chrome MCP browser tests.
- No user-visible surfaces are affected; canonical `/evidence` and all "Proven" badges remain byte-identical.
- The load-bearing invariant (canonical byte-identical defaults) is the central verification axis.
- Error cases (TC-08, TC-09, TC-11) ensure fail-closed behavior on misconfiguration.
- Regression tests (TC-12, TC-13) confirm that Required-still-passing journeys (J-01..J-06) and target journeys (J-07, J-08) are unaffected.
