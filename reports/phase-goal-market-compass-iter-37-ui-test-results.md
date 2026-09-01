# UI Test Results (merged)

**Date:** 2026-09-01
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 13/13 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Sector attribution is honest and near-complete on new runs | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-37-evidence/J-01-verify.png |
| UT-J-02 | "What changed" reports meaningful session-over-session deltas with honest empties | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-37-evidence/J-02-verify.png |
| UT-J-03 | The plain-English summary is deterministic, cited, and never invents a cause | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-37-evidence/J-03-verify.png |
| UT-J-04 | Every next-session candidate explains why, why-not, and what would change it | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-37-evidence/J-04-verify.png |
| UT-J-05 | Each close freezes one provenance-stamped next-session manifest, exported byte-consistently | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-37-evidence/J-05-verify.png |
| UT-J-06 | A frozen manifest never changes — later data, rebuilds, and regeneration are safe | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-37-evidence/J-06-verify.png |
| UT-J-07 | The Today page answers the ten-second read from served values only | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-37-evidence/J-07-verify.png |
| UT-J-08 | The market surface relocates intact and history never lies | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-37-evidence/J-08-verify.png |
| UT-J-10 | Bounded recovery of the two trading days the iter-5 drill deleted | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-37-evidence/J-10-verify.png |
| UT-J-11 | Incident-bounded clean regeneration of derived state (disposable-clone serving verification) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-37-evidence/J-11-verify.png |
| UT-J-12 | Every frozen selection disposition is true -- the leadership floor is the only inclusion gate, and a caution qualifier moves no membership | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-37-evidence/J-12-verify.png |
| UT-J-13 | Leadership rotation shows both directions with signed deltas — this iteration's evidence target (fresh screenshot required) | regression | P1 | `/` renders a served `session_delta.rotation` block (not a client-side filter of `changes`) with two labelled, signed, both-directions sides per group kind (sector, theme), zero stock-kind rows, honest per-side empty states, complete accounting (`shown + suppressed + residual == configured_total`), signed `delta`/`direction_word` also on `session_delta.changes` sector/theme entries, What-changed unchanged, an honest no-prior-run state at the earliest stored session, and — specifically this iteration — a freshly captured acceptance screenshot that `PIL.Image.getcolors()` measures as more than one distinct colour | All assertions verified true against the live frontend (`http://localhost:3255/`) and cross-checked against `GET /api/compass`, `GET /api/sectors?as_of=`, `GET /api/themes?as_of=` on the backend (`:8255`) — see detail below. The acceptance screenshot was re-captured this iteration and measured: 1683×4320 px, **13,647 distinct colours** (`PIL.Image.getcolors()`), 693,670 bytes — comparable to healthy sibling captures in the same evidence directory and definitively NOT the iter-36 single-colour failure. | PASS | `reports/qa/goal-market-compass-iter-37-evidence/UT-J-13-rotation-both-directions.png` |
| UT-J-09 | The backend fits the host (regression — evidence-based, walkthrough waived) | regression | P1 | (1) live `/proc/<pid>/status` `VmPeak_kB` ≤ 2,621,440 kB; (2) `reports/perf-budgets.md`'s newest addendum is still Addendum 45 (2026-09-01, market-compass iter-34, "J-09 closing re-measurement"), recording ≤ 2,621,440 kB, no addendum regressed or went missing; (3) `git diff --stat reports/perf-budgets.md` shows zero diff this iteration | (1) Live backend (pid 68389, port 8255, `uvicorn main:app --host 0.0.0.0 --port 8255`): `VmPeak: 2292200 kB` — 329,240 kB (12.56%) under the 2,621,440 kB target. (2) `grep -n "^## Addendum" reports/perf-budgets.md` confirms Addendum 45 (line 12822) is still the last/newest heading in the file (46 addenda total, sequential, none missing) — its developer-run table states 2,307,092 kB (-11.99% vs target) and its auditor-run subsection states 2,305,668 kB (-12.05% vs target), both well under the bar. (3) `git status --porcelain -- reports/perf-budgets.md` and `git diff --stat HEAD -- reports/perf-budgets.md` are both empty — zero diff. Additionally confirmed this iteration's actual code touch is scoped exactly as the precondition states: `git diff --stat HEAD -- apps/backend/ config.yaml` shows only `apps/backend/app/engine/compass.py` (18 lines) and `apps/backend/tests/test_manifest_invariants.py` (47 lines) changed — `config.yaml`, `warmup.py`, `prices.py` untouched, so no memory-affecting code path moved this round. | PASS | none (evidence-based journey — no UI acceptance state to screenshot, per this journey's own `docs/goal.md` "Walkthrough: waived" marker and the test plan's own framing) |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-09-01

