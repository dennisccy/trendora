# QA Validation Report — goal-ops-hardening-iter-45 (Re-validation)

**Verdict:** FAIL

**Date:** 2026-08-04 (re-validation after auditor/reviewer FAIL)  
**Phase:** goal-ops-hardening-iter-45  
**QA Agent:** qa (MODE 2: QA Validation)

---

## Context: Re-validation After Browser-QA Failure

This QA re-validation follows:
1. Initial QA report issued PASS before browser-qa-agent executed (error in sequencing)
2. Browser-qa-agent reported FAIL 0/2 for target journeys J-05, J-07 due to backend outage
3. Code reviewer issued FAIL with note that DoD item "Target journeys J-05, J-07 pass via browser-qa-agent" is unmet
4. Auditor also returned FAIL

**Critical Coordinator Note:** The backend went fully unreachable (~34-42 minutes) during browser-qa testing, a worse outcome than the stall the iteration aimed to fix. The browser-qa evidence is authoritative; revalidation confirms this FAIL verdict stands.

---

## Artifact Verification

### Required Artifacts

| Artifact | Location | Status |
|----------|----------|--------|
| Dev handoff | `docs/handoffs/goal-ops-hardening-iter-45-dev.md` | ✓ PRESENT |
| Review report | `reports/reviews/goal-ops-hardening-iter-45-review.md` | ✓ PRESENT — **FAIL** (DoD unmet) |
| Phase spec | `docs/phases/goal-ops-hardening-iter-45.md` | ✓ PRESENT |
| Status file | `runs/goal-ops-hardening-iter-45/status.json` | ✓ PRESENT |
| Browser-QA report | `reports/phase-goal-ops-hardening-iter-45-ui-test-results.llm.md` | ✓ PRESENT — **FAIL 0/2** |

**Verdict:** All required artifacts present. Review and browser-qa reports both declare FAIL.

---

## Backend Test Results (from earlier QA pass — still valid)

### Test Execution Summary

Per the dev handoff and earlier QA validation:

- **4 new tests (TC-1, TC-2, TC-3, gap-fill regression):** PASS ✓ — 4 passed in 1.12s
- **5 fault-injection tests:** PASS ✓ — 5 passed in 0.76s  
- **Memory-pressure tests (TC-8, 5 consecutive runs):** PASS ✓ — 10 executions, no `MemoryError` escape
- **10 membership-cache regression tests:** PASS ✓ — 10 passed in 1.90s
- **Total unique test executions:** 62 across 6 files/selections, all passing

**Backend unit-level acceptance (TC-1 through TC-3, TC-8 through TC-10):** ✓ MET

The append-forward fast path is correctly scoped, byte-identical to the pre-fix oracle, and thoroughly tested at the unit level.

---

## Browser-QA Journey Validation (Critical — DoD requirement)

### Definition of Done Requirement

**From phase spec, line 218:**
> "Target journeys J-05, J-07 pass via browser-qa-agent"

**Browser-qa-agent report:** `reports/phase-goal-ops-hardening-iter-45-ui-test-results.llm.md`

### Findings

**Verdict: FAIL 0/2** — Both target journeys failed due to backend outage.

| Journey | Expected | Actual | Verdict | Root Cause |
|---------|----------|--------|---------|-----------|
| UT-J-05 | Backfill of absent date reaches terminal `ok` within 300s | Job failed with `MemoryError` at ~5m; backend then unreachable for 34+ min | **FAIL** | Unbounded accumulators in `research.py:777`, `forward_testing.py:2343` (out-of-scope, deferred) |
| UT-J-07 | `/api/health` stays HTTP 200 throughout warm; badge stays ready | Backend **completely unreachable** for entire window (0/60+ polls returned HTTP 200 over 34+ minutes) | **FAIL** | Same unbounded accumulator issue |

**Critical evidence from browser-qa report:**
- J-05's backfill job (single day, `2019-02-25`) initially appeared to run within budgets
- At ~5 minutes elapsed (under TC-4's 300s budget), job reached terminal **`failed`** status with message `"MemoryError (no message)"`
- No snapshot was created; no scanner run was recorded for the target date
- Backend process stayed alive but stopped accepting new HTTP connections
- `GET /api/health` and `GET /api/data` both returned **zero response** (curl code `000`) for 60+ consecutive polls spanning ~34 minutes (`00:49:29Z` → `01:21:40Z`)
- Backend process actively logging continuous `MemoryError` tracebacks from exactly the two accumulators the phase spec lists in OUT OF SCOPE:
  - `research.py:777` — `_combination_observations`' `ret_by_run_symbol` dict
  - `forward_testing.py:2343` — `compute_drawdown_expectations`' `stored_by_key` dict

**What this iteration did vs. what happened:**
- **This iteration's scope:** Fix the membership-timeline O(dates × pool) recompute on every ingest → append-forward fast path ✓ correctly implemented at unit level
- **What went wrong live:** Unbounded memory accumulation from unrelated (deferred) code paths → backend wedge → **no HTTP responses for 34+ minutes**
- **Outcome:** The fix targeted the wrong bottleneck; the iteration did not achieve its acceptance criteria because a different, pre-existing latent bug blocked the target journeys during live execution

### Impact on Acceptance

The phase spec (line 218) requires: **"Target journeys J-05, J-07 pass via browser-qa-agent"**

This is part of the DEFINITION OF DONE, explicitly labeled as a DoD checkbox item.

**Status:** ✗ UNMET — browser-qa-agent reported FAIL 0/2.

---

## Regression Journeys (J-01, J-03, J-04, J-06, J-08, J-09)

Per browser-qa report:
> "UT-J-01, UT-J-03, UT-J-04, UT-J-06, UT-J-08, and UT-J-09 were **not** re-tested and have no rows in this report — they were already re-verified this iteration via deterministic golden-script replay"

**Status:** Evidence files present in `reports/qa/goal-ops-hardening-iter-45-evidence/` (J-01-verify.png through J-09-verify.png, pre-dating browser-qa dispatch). These pass at the deterministic golden-script replay level but cannot be independently re-verified live while the backend is unreachable / unstable.

---

## Root Cause Analysis

**From auditor/reviewer findings:**

The phase spec explicitly defers the true root cause:
- **Phase spec, OUT OF SCOPE section (lines 188-189):**
  > "iter-44/al's two unbounded evidence-path accumulators (`research.py:777`, `forward_testing.py:2343`) — a separate, real finding, deliberately not this iteration's second risky action (rule 5)."

**What happened:**
1. This iteration fixed the membership-timeline O(dates × pool) recompute bottleneck ✓
2. Live browser testing revealed a **different** bottleneck: unbounded dict accumulation in `research.py:777` and `forward_testing.py:2343`
3. These accumulators caused `MemoryError` exceptions under the combination of:
   - Heavy backfill load (J-05's target: single day `2019-02-25`, but fell into a historical gap-fill case which this iteration does NOT accelerate)
   - Pre-existing background `horizons_done` warm loop (unrelated J-07 preparation)
   - System running under `memory_cap_mb=8192` with pre-existing data basis

**The fix this iteration applied was targeted at the wrong call chain:**
- Targeted: `resolve_with_reasons` ← `_excluded_counts_by_date` ← `_membership_timeline` (verified unit-level PASS)
- Actual live bottleneck: unbounded `research.py:777` and `forward_testing.py:2343` accumulation (explicitly out-of-scope, deferred)

This is not a regression from this iteration's code; it is an **existing latent bug** that was exposed during live browser testing.

---

## Conformance to Definition of Done

| DoD Item | Status | Evidence |
|----------|--------|----------|
| Append-forward ingest does not re-invoke O(dates × pool) resolver (TC-1) | ✓ PASS | Unit test: call-count assertion confirmed |
| Previously-cached dates byte-identical after append-forward (TC-2) | ✓ PASS | Unit test: byte-identity assertion confirmed |
| Fast-path output == oracle == fallback (TC-3) | ✓ PASS | Fixture-backed byte-identity test confirmed |
| **J-05 backfill reaches terminal ok within 300s (TC-4)** | ✗ **FAIL** | Browser-qa: job failed at ~5m with MemoryError; backend subsequently unreachable 34+ min |
| **J-07 forward-warm advances horizons_done past 0 (TC-5)** | ✗ **FAIL** | Browser-qa: backend unreachable during J-07 step 4; condition never reached |
| **`/api/health` stays responsive throughout J-07 (TC-6)** | ✗ **FAIL** | Browser-qa: 0/60+ polls over 34+ minutes returned HTTP 200; backend fully wedged |
| Induced-pressure abort still holds (TC-7) | ✗ **SKIPPED** | Browser-qa: backend outage prevented reaching this regression check |
| `test_ingest_finalize_memory_pressure.py` passes 5 consecutive runs (TC-8) | ✓ PASS | Dev handoff: 5 runs, 10 executions, all passed; no MemoryError escape |
| J-07.json dataset anchors updated (TC-9) | ✓ PASS | Verified: `n=8991` and `2533` confirmed live |
| Stale comment corrected (TC-10) | ✓ PASS | Verified: `data_manager.py` comment updated |
| **Target journeys J-05, J-07 pass via browser-qa-agent** | ✗ **FAIL** | Browser-qa report: FAIL 0/2 due to backend outage |
| Required-still-passing journeys all pass (TC-11) | ✗ **UNMET** | Golden-script evidence present, but regression checks cannot be re-run live while backend unreachable |

**Summary:** 5/11 DoD items met (TC-1, TC-2, TC-3, TC-8, TC-9, TC-10). **6/11 items unmet or blocked** (TC-4, TC-5, TC-6, TC-7, TC-11, and the critical "Target journeys J-05, J-07 pass via browser-qa-agent" requirement).

---

## Conclusion

**Verdict: FAIL**

### Why

1. **Phase-level acceptance criterion unmet:** The phase spec's DEFINITION OF DONE includes "Target journeys J-05, J-07 pass via browser-qa-agent" (line 218). Browser-qa-agent reported FAIL 0/2, with both journeys unable to reach their acceptance conditions due to backend outage.

2. **Backend unit tests all pass, but live validation fails:** The implementation of the membership-timeline append-forward fast path is technically sound (TC-1/2/3/8/9/10 all pass). However, the live browser validation exposed a different, pre-existing bottleneck (unbounded accumulators in `research.py:777` and `forward_testing.py:2343`) that prevented target journeys from completing.

3. **Root cause is explicitly out-of-scope for this iteration:** The phase spec and assumptions.md both clearly state that the unbounded accumulator fix is deliberately deferred to a separate iteration. However, the iteration's own DoD cannot be met until this latent bug is addressed, because live testing exposes it as the actual blocker.

4. **This is not a regression from this iteration's changes:** The target journeys' failures are caused by pre-existing unbounded accumulation, not by the membership-timeline fix itself. The fix was correctly implemented in its scoped scope; it simply did not address the live bottleneck that manifested during browser testing.

### Next Steps (for next iteration)

Per the reviewer's and auditor's findings:
1. **CRITICAL:** Bound the unbounded evidence-path accumulators in `research.py:777` and `forward_testing.py:2343` — this is the prerequisite for J-05 and J-07 to pass live browser validation
2. Once this is fixed, re-attempt J-05/J-07 browser validation in a dedicated follow-up iteration
3. Re-verify the regression journeys (J-01, J-03, J-04, J-06, J-08, J-09) in the same follow-up, per the phase spec's requirement for "full regression of the entire currently-passing set"

### Escalation

This iteration is **blocked** and cannot proceed to release. The technical implementation is sound, but the live acceptance criteria are unmet due to a pre-existing bottleneck that requires a separate, dedicated iteration to resolve.

---

## Evidence and Artifacts

- **Backend unit test results:** Logged during implementation; all 62 test executions passed
- **Browser-qa live test results:** `reports/phase-goal-ops-hardening-iter-45-ui-test-results.llm.md` (FAIL 0/2)
- **Browser-qa evidence screenshots:** `reports/qa/goal-ops-hardening-iter-45-evidence/UT-J-05-fail.png`, `UT-J-07-fail.png`
- **Dev handoff:** `docs/handoffs/goal-ops-hardening-iter-45-dev.md` (thorough implementation documentation with disclosed known issues)
- **Review report:** `reports/reviews/goal-ops-hardening-iter-45-review.md` (FAIL; DoD unmet; recommends deferral)
