# UI Test Results (merged)

**Date:** 2026-08-31
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 10/10 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Sector attribution is honest and near-complete on new runs | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-28-evidence/J-01-verify.png |
| UT-J-02 | "What changed" reports meaningful session-over-session deltas with honest empties | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-28-evidence/J-02-verify.png |
| UT-J-03 | The plain-English summary is deterministic, cited, and never invents a cause | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-28-evidence/J-03-verify.png |
| UT-J-04 | Every next-session candidate explains why, why-not, and what would change it | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-28-evidence/J-04-verify.png |
| UT-J-05 | Each close freezes one provenance-stamped next-session manifest, exported byte-consistently | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-28-evidence/J-05-verify.png |
| UT-J-06 | A frozen manifest never changes — later data, rebuilds, and regeneration are safe | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-28-evidence/J-06-verify.png |
| UT-J-10 | Bounded recovery of the two trading days the iter-5 drill deleted | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-28-evidence/J-10-verify.png |
| UT-J-11 | Incident-bounded clean regeneration of derived state (disposable-clone serving verification) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-28-evidence/J-11-verify.png |
| UT-J-07 | The Today page answers the ten-second read from served values only | happy-path | P1 | `/` renders the six body sections in order (state band, summary, what-changed, leadership rotation, next-session focus, manifest strip) with readiness/preflight chrome above; tile values/breakdowns/direction words equal served fields; cross-view chart absent from `/`, link-out reaches `/market`; no `/api/sectors`/`/api/themes` fetch on load; TTI/API latencies within budget | All 7 steps verified via live DOM/API inspection — see notes below for the one structural caveat (direction-word badges read NA this iteration, which is the correct served value) | PASS | `reports/qa/goal-market-compass-iter-28-evidence/UT-J-07-today-page.png` |
| UT-J-08 | The market surface relocates intact and history never lies | happy-path | P1 | `/market` renders the full former dashboard inventory unchanged; sidebar lists Today then Market with correct active-highlighting; historical `?asof=2025-04-15` shows that date's stored values with a retrospective-labeled manifest; frontier `?asof=2026-08-12` shows frozen at_ingest stamps; fresh-tab load is already D-scoped; Latest clears the param | All 6 steps verified live; one wording caveat (manifest shows "version 6" not literally "version 1" — see notes) | PASS | `reports/qa/goal-market-compass-iter-28-evidence/UT-J-08-market-page.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-31

