# goal-market-compass-iter-32 QA Report

**Phase:** goal-market-compass-iter-32  
**Date:** 2026-09-01  
**QA Agent:** qa  
**Frontend Present:** no

**Verdict:** PASS

---

## Artifact Verification

All required artifacts exist and are correct:

| Artifact | Status | Notes |
|----------|--------|-------|
| `docs/handoffs/goal-market-compass-iter-32-dev.md` | ✓ exists | Complete handoff with honest disclosure of host contention |
| `reports/reviews/goal-market-compass-iter-32-review.md` | ✓ PASS | Reviewer confirmed pure re-measurement, zero code changes |
| `runs/goal-market-compass-iter-32/status.json` | ✓ exists | current_step: review_passed, tests_run: true |
| `runs/goal-market-compass-iter-32/j09-vmpeak-samples.csv` | ✓ exists | 80 rows + header, UTC timestamps 2026-09-01T03:19:41Z → 03:26:17Z, peak 3,038,684 kB |
| `reports/perf-budgets.md` Addendum 43 | ✓ appended | 144 insertions, 0 deletions; addenda 40-42 byte-unchanged; new addendum at end |
| `reports/phase-goal-market-compass-iter-32-regression-replay-results.md` | ✓ exists | 10/10 journeys PASS, Browser QA Verdict: PASS |

---

## Backend Tests

### Configuration Check (TC-1)
- **Command:** `git diff -- config.yaml`
- **Result:** No changes
- **Verification:** 
  - `database.pragmas.cache_size`: -65536 ✓ (unchanged from iter-4)
  - `pool_size`: 24 ✓ (unchanged)
  - `max_overflow`: 44 ✓ (unchanged)

### Pragma Tests (TC-2/TC-3 — cache_size resolution)
- **Command:** `cd apps/backend && .venv/bin/python -m pytest tests/test_db.py -v -k pragma`
- **Result:** 2/2 PASS
  - `test_sqlite_pragmas_applied_on_connect` — PASS
  - `test_sqlite_pragmas_are_config_sourced_not_a_literal` — PASS
- **Verification:** cache_size correctly resolves to -65536 from config.yaml

### VmPeak Standing-Warm Measurement (TC-2/TC-3)
- **Command:** `bash scripts/start-backend.sh` with VmPeak sampler
- **Result:** Standing-warm plateau reached at 3,038,684 kB
- **Evidence file:** `runs/goal-market-compass-iter-32/j09-vmpeak-samples.csv`
  - 80 samples captured
  - 5-second interval
  - UTC timestamps: 2026-09-01T03:19:41Z → 03:26:17Z (~396 seconds)
  - Peak VmPeak: 3,038,684 kB (2,967.5 MB)
  - Target: ≤2,621,440 kB (2.5 GB)
  - Result: **Honest miss — +15.9% over target**

### Concurrent Load Check (TC-4)
- **Command:** 5 rounds of 64 simultaneous GET requests (`concurrent64-burst`)
- **Result:** 320 total requests, 0 non-200s, 0 QueuePool TimeoutError
- **Verification:** Pass (confirmed both client-side and server-side via logs/backend.log)

### Byte-Identity Spot-Check (TC-5)
- **Command:** `GET /api/compass` and `GET /api/dashboard` at authorized as-of values
- **Fixed as-of set:** {no param (frontier, 2026-08-12), "2025-04-15", "1996-02-01"}
- **Results:**
  - compass @ 2025-04-15: before/after byte-identical ✓
  - compass @ 1996-02-01: before/after byte-identical ✓
  - dashboard @ 2025-04-15: before/after byte-identical ✓
  - dashboard @ 1996-02-01: before/after byte-identical ✓
- **Evidence:** 12 raw captures in `runs/goal-market-compass-iter-32/byte-identity/`

### Concurrency Load Test (Addendum 40/41 methodology reproduction)
- **Command:** Replica burst (5 workers, 6 endpoints, 150s)
- **Result:** 482 requests, 0 non-200s
- **Verification:** Matches Addendum 40/41's own result exactly

---

## Frontend Tests

**Status:** SKIPPED — backend-only phase (`Frontend Present: no`)

No UI surface change, no new displayed values, no Walkthrough clause (explicitly waived per spec).

---

## Functional Test Plan Execution

**Status:** N/A — no functional test plan exists for this phase

Standard QA checks only (above).

---

## Browser Checks

**Status:** SKIPPED — backend-only phase (`Frontend Present: no`)

No UI surface change, no new capabilities to test via browser.

---

## Deterministic Regression Replay (Journey Verification)

**Command:** `python3 scripts/automation/lib/demo_runner.py --mode verify --journeys J-01,J-02,J-03,J-04,J-05,J-06,J-07,J-08,J-10,J-11`

**Result:** 10/10 PASS

| Test ID | Name | Expected | Actual | Verdict | Evidence |
|---------|------|----------|--------|---------|----------|
| UT-J-01 | Sector attribution is honest and near-complete on new runs | PASS | PASS | PASS | reports/qa/goal-market-compass-iter-32-evidence/J-01-verify.png |
| UT-J-02 | "What changed" reports meaningful session-over-session deltas with honest empties | PASS | PASS | PASS | reports/qa/goal-market-compass-iter-32-evidence/J-02-verify.png |
| UT-J-03 | The plain-English summary is deterministic, cited, and never invents a cause | PASS | PASS | PASS | reports/qa/goal-market-compass-iter-32-evidence/J-03-verify.png |
| UT-J-04 | Every next-session candidate explains why, why-not, and what would change it | PASS | PASS | PASS | reports/qa/goal-market-compass-iter-32-evidence/J-04-verify.png |
| UT-J-05 | Each close freezes one provenance-stamped next-session manifest, exported byte-consistently | PASS | PASS | PASS | reports/qa/goal-market-compass-iter-32-evidence/J-05-verify.png |
| UT-J-06 | A frozen manifest never changes — later data, rebuilds, and regeneration are safe | PASS | PASS | PASS | reports/qa/goal-market-compass-iter-32-evidence/J-06-verify.png |
| UT-J-07 | The Today page answers the ten-second read from served values only | PASS | PASS | PASS | reports/qa/goal-market-compass-iter-32-evidence/J-07-verify.png |
| UT-J-08 | The market surface relocates intact and history never lies | PASS | PASS | PASS | reports/qa/goal-market-compass-iter-32-evidence/J-08-verify.png |
| UT-J-10 | Bounded recovery of the two trading days the iter-5 drill deleted | PASS | PASS | PASS | reports/qa/goal-market-compass-iter-32-evidence/J-10-verify.png |
| UT-J-11 | Incident-bounded clean regeneration of derived state (disposable-clone serving verification) | PASS | PASS | PASS | reports/qa/goal-market-compass-iter-32-evidence/J-11-verify.png |

**Critical note:** J-02 and J-03 were rewritten AFTER iter-31's replay run and had **never been executed** in their current form. This iteration's deterministic replay executed them for the first time, and both passed with real evidence screenshots. Per the spec's binding rule, they were not edited after the replay run.

**Manifest census (post-replay):** 28 rows / 18 distinct `as_of` / max id 28 — unchanged from iter-31, zero new manifests minted. Only the 6 authorized before/after byte-identity spot-check calls were made (confirmed via server logs: exactly 6 compass-endpoint hits).

---

## Test Summary

| Category | Count | Status |
|----------|-------|--------|
| Backend tests (targeted) | 2 | 2 PASS |
| Concurrent load (320 req) | 1 | 0 errors ✓ |
| Byte-identity pairs | 6 | 6 byte-identical ✓ |
| Regression journeys | 10 | 10 PASS |
| **Overall** | — | **PASS** |

---

## Assessment

This iteration is a **pure re-measurement pass with complete evidence durability**:

1. ✓ Config unchanged (cache_size, pool_size, max_overflow all in spec)
2. ✓ VmPeak cleanly re-measured and saved to a durable file with UTC timestamps
3. ✓ Concurrent load check passes (zero pool timeouts)
4. ✓ Byte-identity confirms no displayed values moved
5. ✓ perf-budgets.md correctly updated with Addendum 43 (append-only, earlier addenda untouched)
6. ✓ All 10 Required-still-passing journeys pass (including J-02/J-03's first execution since rewrite)
7. ✓ No code/UI changes; no anti-goal violations

**The honest result:** J-09 still misses the ≤2.5 GB target (3,038,684 kB measured). Per the iteration spec's own escalation clause, **this is the point where J-09's "stop for owner review" gate genuinely fires** — the measurement is clean and thoroughly evidenced, no cap values were widened, and the remaining gap is unlikely to close through re-measurement alone.

**Host contention disclosure:** A sibling goal-mode session (tensteps) was actively running during the measurement window. This was disclosed plainly in the dev handoff and `perf-budgets.md` Addendum 43, not discovered post-hoc by audit. Despite the contention, VmPeak plateaued at exactly 3,038,684 kB for all 80 samples (stable, repeatable).

---

## Files Verified

- `docs/handoffs/goal-market-compass-iter-32-dev.md` — complete, honest, fully disclosed
- `reports/reviews/goal-market-compass-iter-32-review.md` — PASS verdict confirmed
- `reports/perf-budgets.md` — Addendum 43 appended correctly
- `reports/phase-goal-market-compass-iter-32-regression-replay-results.md` — 10/10 PASS
- `runs/goal-market-compass-iter-32/j09-vmpeak-samples.csv` — raw evidence file, durable

---

**Verdict:** PASS

All required Definition of Done checkboxes are complete. The iteration successfully delivers a clean, durably-evidenced re-measurement of J-09's standing-warm backend memory footprint with full regression verification. The honest miss vs the 2.5 GB target is recorded plainly, per spec, with no target widening.
