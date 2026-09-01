# UI Test Results (merged)

**Date:** 2026-09-01
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 8/8 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-02 | "What changed" reports meaningful session-over-session deltas with honest empties | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-36-evidence/J-02-verify.png |
| UT-J-04 | Every next-session candidate explains why, why-not, and what would change it | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-36-evidence/J-04-verify.png |
| UT-J-05 | Each close freezes one provenance-stamped next-session manifest, exported byte-consistently | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-36-evidence/J-05-verify.png |
| UT-J-06 | A frozen manifest never changes — later data, rebuilds, and regeneration are safe | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-36-evidence/J-06-verify.png |
| UT-J-07 | The Today page answers the ten-second read from served values only | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-36-evidence/J-07-verify.png |
| UT-J-08 | The market surface relocates intact and history never lies | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-36-evidence/J-08-verify.png |
| UT-J-12 | Every frozen selection disposition is true -- the leadership floor is the only inclusion gate, and a caution qualifier moves no membership | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-36-evidence/J-12-verify.png |
| UT-J-13 | Leadership rotation says which way, shows both directions, and stops repeating What-changed | happy-path | P1 | `/` renders a served `session_delta.rotation` block (not a client-side filter of `changes`) with two labelled, signed, both-directions sides per group kind (sector, theme), zero stock-kind rows, honest per-side empty states, complete accounting (`shown + suppressed + residual == configured_total`), signed `delta`/`direction_word` also on `session_delta.changes` sector/theme entries, What-changed unchanged, and an honest no-prior-run state at the earliest stored session | All assertions verified true against the live frontend (`http://localhost:3255/`) and cross-checked against `GET /api/compass`, `GET /api/sectors`, `GET /api/themes` on the backend (`:8255`) — see detail below | PASS | `reports/qa/goal-market-compass-iter-36-evidence/UT-J-13-rotation-both-directions.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-09-01

