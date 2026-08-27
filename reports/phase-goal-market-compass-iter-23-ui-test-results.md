# UI Test Results (merged)

**Date:** 2026-08-27
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 4/4 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Sector attribution is honest and near-complete on new runs | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-23-evidence/J-01-verify.png |
| UT-J-04 | Every next-session candidate explains why, why-not, and what would change it | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-23-evidence/J-04-verify.png |
| UT-J-11 | Incident-bounded clean regeneration of derived state — disposable-clone serving verification | smoke | P1 | `/` renders correctly at the frontier (2026-08-12) and at an already-manifested incident date (2026-08-11) with real repaired values, honest `Basis: rebuilt` disclosure, zero unacceptable side effects (no new ScannerRun, no minted manifest, manifest bytes/hashes unchanged), and named trap 1 (FK survival) holds live | `/` and `/?asof=2026-08-11` both rendered real served values, no error boundary; `Basis: rebuilt` correctly shown for the incident date; before/after DB checks confirm zero unacceptable side effects; `PRAGMA foreign_keys=ON` + `foreign_key_check(next_session_manifests)` returned 0 violations live | PASS | `reports/qa/goal-market-compass-iter-23-evidence/J-11-today-frontier-result.png`, `reports/qa/goal-market-compass-iter-23-evidence/J-11-incident-2026-08-11-result.png` |
| UT-J-10 | Bounded recovery of the two trading days the iter-5 drill deleted — repaired data serves correctly | smoke | P1 | AVB stock detail page renders correctly at as_of 2026-08-11 and 2026-08-12 (the two repaired dates) with real computed values (not NA/broken); the underlying repaired volumes exactly match the certified figures (554757.0 / 3706010.0) | AVB page rendered real computed risk/pattern metrics at both dates, no error boundary; `GET /api/stocks/AVB/bars?range=full` (the same endpoint the page consumes) returned volume 554757.0 for 2026-08-11 and 3706010.0 for 2026-08-12 — exact match | PASS | `reports/qa/goal-market-compass-iter-23-evidence/J-10-AVB-2026-08-12-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-27

