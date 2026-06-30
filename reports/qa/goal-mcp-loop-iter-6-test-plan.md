# goal-mcp-loop-iter-6 Functional Test Plan

**Phase:** goal-mcp-loop-iter-6
**Date:** 2026-06-30
**Frontend Present:** yes

## Phase Goal

Repair the post-dev verification pipeline harness so the canonical `browser-qa-agent` lane and the auditor actually run this iteration, producing the canonical UI test results for all five journeys with J-04 flipping from `partial` to `passing`, and writing the auditor handoff — with zero `apps/` diff.

## Test Cases

### TC-01 — Artifact exists post-rc==0 in ui-impact-phase.sh

**Type:** artifact
**Preconditions:** The developer has applied defect #1 fix to `scripts/automation/ui-impact-phase.sh` (L96–109). `ui-impact-phase.sh` is invoked and returns rc==0.

**Steps:**
1. Run `scripts/automation/ui-impact-phase.sh goal-mcp-loop-iter-6`
2. Capture exit code
3. Check that `reports/phase-goal-mcp-loop-iter-6-user-visible-changes.md` exists and is non-empty
4. Check that `reports/phase-goal-mcp-loop-iter-6-ui-surface-map.md` exists and is non-empty

**Expected outcome:** When rc==0, both required artifacts exist and contain content (not zero-byte stub files). If either is missing or empty, the script must exit non-zero and write the failed-artifact stub.

**Pass criteria:** Both files exist with byte size > 100 bytes; script exit code is 0. If on any invocation rc==0 but a file is missing, rc must actually be non-zero and the stub must be written.

---

### TC-02 — Artifact exists post-rc==0 in ui-test-design-phase.sh

**Type:** artifact
**Preconditions:** The developer has applied defect #2 fix to `scripts/automation/ui-test-design-phase.sh`. The script is invoked and returns rc==0.

**Steps:**
1. Run `scripts/automation/ui-test-design-phase.sh goal-mcp-loop-iter-6`
2. Capture exit code
3. Check that `reports/phase-goal-mcp-loop-iter-6-ui-test-plan.md` exists and is non-empty
4. Check that `reports/phase-goal-mcp-loop-iter-6-what-to-click.md` exists and is non-empty

**Expected outcome:** When rc==0, both required artifacts exist and contain content. If either is missing or empty, the script must exit non-zero and write the failed-artifact stub.

**Pass criteria:** Both files exist with byte size > 100 bytes; script exit code is 0. If on any invocation rc==0 but a file is missing, rc must actually be non-zero.

---

### TC-03 — verdicts.py validates post_dev_parallel_complete step

**Type:** api
**Preconditions:** The developer has registered `POST_DEV_PARALLEL_COMPLETE = "post_dev_parallel_complete"` in the `PhaseStep` enum in `scripts/automation/lib/verdicts.py`.

**Steps:**
1. Run: `python3 scripts/automation/lib/verdicts.py validate-step post_dev_parallel_complete`
2. Capture exit code and output

**Expected outcome:** Script exits with code 0, indicating the step is whitelisted and valid.

**Pass criteria:** Exit code is 0; no error message printed to stderr. `update_status` can now call this step without aborting the run.

---

### TC-04 — Post-fanout update_status does not abort the run

**Type:** api
**Preconditions:** Defect #3 is fixed (verdicts.py updated). A fanout has completed. The checkpoint update at `run-phase.sh:648` is executed.

**Steps:**
1. Simulate the checkpoint update: `scripts/automation/lib/verdicts.py update-status goal-mcp-loop-iter-6 in_progress post_dev_parallel_complete`
2. Capture exit code

**Expected outcome:** Command exits with code 0; the status file is updated. The run continues (does not abort).

**Pass criteria:** Exit code is 0. The status checkpoint is recorded with the new step value.

---

### TC-05 — Soft-failed fanout does not unconditionally skip sequential retry steps

**Type:** artifact
**Preconditions:** Defect #4 is fixed in `run-phase.sh:645–647`. A fanout has failed (fanout_rc≠0), meaning `reports/phase-goal-mcp-loop-iter-6-ui-test-results.md` does NOT exist yet.

**Steps:**
1. Simulate fanout failure (e.g., remove or do not create the ui-test-results file)
2. Check the value of `SKIP_BROWSER_QA` after the conditional-skip logic at L645–647
3. Verify that `SKIP_BROWSER_QA` is NOT set to `true` when the artifact is missing

**Expected outcome:** When the fanout fails, the conditional logic gates each `SKIP_*` flag on artifact existence. Since the ui-test-results file does not exist, `SKIP_BROWSER_QA` remains `false`, allowing the sequential Step 5 retry block to re-run the missing step.

**Pass criteria:** `SKIP_BROWSER_QA=false` when `reports/phase-goal-mcp-loop-iter-6-ui-test-results.md` does not exist. Sequential retry blocks can then re-attempt the missing step.

---

### TC-06 — Canonical browser-qa lane produces fresh UT-* for all five journeys

**Type:** browser
**Preconditions:** Backend is running. Frontend is running at http://localhost:3000. All four harness defects are fixed. The developer handoff is complete.

**Steps:**
1. Start backend and frontend services
2. Run the full phase via `./scripts/automation/run-phase.sh goal-mcp-loop-iter-6`
3. Wait for the canonical browser-qa-agent lane to complete (after ui-test-design-phase.sh)
4. Verify that `reports/phase-goal-mcp-loop-iter-6-ui-test-results.md` exists and is not all-SKIP
5. Check that the file contains canonical UT-* entries (not QA agent parallel-lane entries) for J-01, J-02, J-03, J-04, J-05

**Expected outcome:** The canonical `browser-qa-agent` lane runs end-to-end (not skipped), producing fresh UT-* test cases for all five journeys with browser_checks_run=true.

**Pass criteria:** File exists; contains `browser_checks_run=true`; contains distinct UT-* IDs for each journey (J-01 through J-05); at least one UT-* entry is not SKIP.

---

### TC-07 — J-04 passes canonical lane with regime-labeled claim

**Type:** browser
**Preconditions:** Canonical browser-qa-agent lane has run. `reports/phase-goal-mcp-loop-iter-6-ui-test-results.md` exists. Frontend is running. User has navigated the Dashboard and `/evidence` surfaces.

**Steps:**
1. Open http://localhost:3000/ (Dashboard)
2. Observe the current market regime/phase
3. Navigate to `/evidence` (Evidence ledger)
4. Locate the Breakout-watch claim entry (the regime-conditioned claim)
5. Verify it displays "Regime: Risk-on" (or current regime label) and is scrolled into the screenshot
6. Check that `reports/phase-goal-mcp-loop-iter-6-ui-test-results.md` contains a passing UT-* for J-04 with evidence of regime labeling

**Expected outcome:** J-04's regime-conditioned claim is visible on `/evidence`, scoped to and labeled with the regime. The canonical test result shows this claim scrolled into frame (not below-the-fold).

**Pass criteria:** J-04 test case in the results file shows PASS verdict; screenshot evidence includes regime label ("Regime: Risk-on" or equivalent); claim is in the viewport (not cut off).

---

### TC-08 — J-02 proof panel captured fully expanded

**Type:** browser
**Preconditions:** Canonical browser-qa-agent lane has run. Frontend is running. `/stocks` and `/stocks/{ticker}` are accessible.

**Steps:**
1. Open http://localhost:3000/stocks
2. Click a stock row to open `/stocks/{ticker}`
3. Locate a score with a "Proven" badge and click to expand the proof panel
4. Verify the panel displays: out-of-sample test result, control comparison (vs SPY/QQQ/sector ETF/random), certified-claim id, registration date
5. Scroll the expanded panel into full view
6. Check that `reports/phase-goal-mcp-loop-iter-6-ui-test-results.md` contains a passing UT-* for J-02 with the expanded proof panel scrolled into frame

**Expected outcome:** The proof panel is fully expanded and all backing details (test, controls, id, date) are visible in the screenshot. Not just the score cards below-the-fold.

**Pass criteria:** J-02 test case in results file shows PASS; screenshot includes the expanded proof panel with all four details visible (test result, control names, id, date); panel is scrolled into the viewport.

---

### TC-09 — J-05 round-trip captured as distinct screenshot

**Type:** browser
**Preconditions:** Canonical browser-qa-agent lane has run. Frontend is running. `/evidence` is accessible.

**Steps:**
1. Open http://localhost:3000/evidence (Evidence ledger)
2. Locate a claim entry
3. Click the claim to navigate to its backing surface (e.g., /stocks/{ticker})
4. Observe the backing surface showing the score/data that backs the claim
5. Navigate back to `/evidence` using browser back or a link
6. Verify the round-trip produces two distinct screenshots: one of the claim on `/evidence`, one showing the backing surface drill-down
7. Check that `reports/phase-goal-mcp-loop-iter-6-ui-test-results.md` contains a passing UT-* for J-05 with distinct screenshots (not md5-byte-duplicates)

**Expected outcome:** The round-trip (claim → backing surface → back to evidence) is captured as separate screenshots with different content, not as a duplicate of the initial `/evidence` view.

**Pass criteria:** J-05 test case shows PASS; the screenshot evidence shows at least two distinct images (md5 hashes differ); one shows the `/evidence` list, the other shows the backing surface drill-down context.

---

### TC-10 — J-01 and J-03 remain green on canonical lane

**Type:** browser
**Preconditions:** Canonical browser-qa-agent lane has run. `reports/phase-mcp-loop-iter-6-ui-test-results.md` exists.

**Steps:**
1. Review the test results file for J-01 (every score shows evidence status) and J-03 (unproven/noise signals are honestly marked)
2. Verify both have UT-* entries with PASS verdicts
3. Verify the captured screenshots show evidence badges on the `/stocks` leaderboard and honest "Not yet proven" labels where applicable

**Expected outcome:** J-01 and J-03 are re-confirmed green, proving the canonical lane re-verified all five journeys without regression.

**Pass criteria:** Both J-01 and J-03 show PASS in the results file; associated screenshot evidence is present and coherent.

---

### TC-11 — Auditor handoff written with PASS or PASS_WITH_GAPS

**Type:** artifact
**Preconditions:** The full phase pipeline has completed. All four harness defects are fixed. Sequential retry blocks and the auditor have executed.

**Steps:**
1. Check that `docs/handoffs/goal-mcp-loop-iter-6-audit.md` exists
2. Read the file and locate the verdict line (e.g., `**Verdict:** PASS` or `**Verdict:** PASS_WITH_GAPS`)
3. Verify the auditor's assessment covers the required checks (zero `apps/` diff, ledger unchanged, anti-goal compliance, determinism preserved)

**Expected outcome:** Auditor handoff exists and contains a clear PASS or PASS_WITH_GAPS verdict, indicating skeptical review of the implementation and harness fixes.

**Pass criteria:** File exists and is non-empty; contains a `**Verdict:**` line with value PASS or PASS_WITH_GAPS; body includes specific audit findings (not vague).

---

### TC-12 — Zero apps/ diff verified

**Type:** artifact
**Preconditions:** The developer has completed the implementation. All harness fixes are in `scripts/automation/**`. The repo is in a clean state after the phase.

**Steps:**
1. Run: `git diff --name-only -- apps/`
2. Capture the output

**Expected outcome:** Output is empty (no files changed under `apps/`). All changes are confined to `scripts/automation/**` and doc/handoff files.

**Pass criteria:** `git diff --name-only -- apps/` produces zero lines of output.

---

### TC-13 — Harness unit tests pass with no regressions

**Type:** api
**Preconditions:** All four defects are fixed in `scripts/automation/**`. Backend environment is set up.

**Steps:**
1. Run: `./scripts/automation/run-evals.sh`
2. Capture exit code and test results

**Expected outcome:** All offline harness eval tests pass (exit code 0).

**Pass criteria:** Exit code is 0; test output shows no failures or regressions in the harness test suite.

---

### TC-14 — Dev handoff written with harness change summary

**Type:** artifact
**Preconditions:** Developer has completed the implementation.

**Steps:**
1. Check that `docs/handoffs/goal-mcp-loop-iter-6-dev.md` exists
2. Read the file and verify it documents the four harness defects fixed
3. Verify it lists the files modified (ui-impact-phase.sh, ui-test-design-phase.sh, verdicts.py, run-phase.sh)
4. Verify zero `apps/` diff is stated explicitly

**Expected outcome:** Dev handoff clearly explains the harness fixes, the files changed, and confirms zero `apps/` diff.

**Pass criteria:** File exists and is non-empty; documents all four defects and their fixes; explicitly states zero `apps/` diff; test results (run-evals.sh) are reported as green.

---

## Summary

Total test cases: 14
API tests: 4 (TC-03, TC-04, TC-13)
Browser tests: 4 (TC-06, TC-07, TC-08, TC-09, TC-10)
Artifact checks: 6 (TC-01, TC-02, TC-05, TC-11, TC-12, TC-14)

**Frontend Present:** yes — The canonical browser-qa-agent lane must run (TC-06 through TC-10), verifying all five journeys through fresh browser captures.

**Key Constraints:**
- Zero `apps/` diff is mandatory (TC-12)
- Harness unit tests must pass (TC-13)
- All four defects must be fixed in `scripts/automation/**` — no product code changes
- Canonical lane (not QA agent parallel lane) must produce the test results
- J-04 must flip from `partial` to `passing` via regime-labeled evidence on `/evidence`
