# Regression Replay — goal-ops-hardening-iter-9

**Phase:** goal-ops-hardening-iter-9
**Date:** 2026-07-22
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 0/2 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | step 02 could not perform fill: Locator.wait_for: Timeout 15000ms exceeded. | FAIL | reports/qa/goal-ops-hardening-iter-9-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | step 02 could not perform fill: Locator.wait_for: Timeout 20000ms exceeded. | FAIL | reports/qa/goal-ops-hardening-iter-9-evidence/J-03-verify.png |

## Failed Tests

### UT-J-01 — Backfill honors the requested range and explains zero-work

**Verdict:** FAIL
**Failure:** step 02 could not perform fill: Locator.wait_for: Timeout 15000ms exceeded.
**Evidence:** `reports/qa/goal-ops-hardening-iter-9-evidence/J-01-verify.png`

### UT-J-03 — No per-run range cap

**Verdict:** FAIL
**Failure:** step 02 could not perform fill: Locator.wait_for: Timeout 20000ms exceeded.
**Evidence:** `reports/qa/goal-ops-hardening-iter-9-evidence/J-03-verify.png`

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-07-22

---

_Reconciliation (2026-07-22): the replay FAIL row(s) for J-01 J-03 above were overturned by the LLM lane's re-confirmation this iteration (golden-script false positive). The authoritative merged verdicts are in phase-goal-ops-hardening-iter-9-ui-test-results.md; the FAIL row(s) above are superseded._

---

## AUDITOR ADDENDUM (2026-07-22, iter-9 audit — finding T2)

This artifact is named by the phase's DEFINITION OF DONE as the place recording **J-01, J-03 and J-04**
all passing. As generated it covers only J-01 and J-03 (both replay-lane FAILs, both overturned by the LLM
lane) and is **silent on J-04**. The actual, recorded J-04 outcome this iteration — read from the RAW lane
file `reports/phase-goal-ops-hardening-iter-9-ui-test-results.llm.md` (per TC-14, not from the merged
summary) — is:

| Journey | Lane | Outcome | Source |
|---|---|---|---|
| J-01 | LLM re-verification (8 steps) | **PASS** | `...-ui-test-results.llm.md` § "J-01" |
| J-03 | LLM live end-to-end (this pass) | **PASS** | `...-ui-test-results.llm.md` § "J-03" |
| J-04 | LLM 6-step acceptance | **FAIL — step 6** (an interrupted job's persisted progress is not frozen at the crash point; it is never written at all: `dates_total: 0`, `dates_done: 0`, `aggregates_refreshed: null`) | `...-ui-test-results.llm.md` § UT-J-04 / UT-10 |

Therefore the DoD item "records J-01, J-03 and J-04 all passing — moving all three out of `unknown`" is
**NOT met**: J-01 and J-03 move to `passing`; J-04 moves from `unknown` to `failing` (a genuine,
newly-discovered, pre-existing defect in `_finalize_run_record()`/`sweep_orphaned_runs`
(`apps/backend/app/engine/data_manager.py:3652`, `:3686`) — not introduced by this iteration's diff, which
touches no run-record persistence code). No result above is invented by the auditor; each is a citation of
the browser-qa lane's own raw output._
