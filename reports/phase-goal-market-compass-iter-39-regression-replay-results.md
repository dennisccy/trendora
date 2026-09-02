# Regression Replay — goal-market-compass-iter-39

**Phase:** goal-market-compass-iter-39
**Date:** 2026-09-02
**Written by:** demo_runner.py (deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 11/13 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Sector attribution is honest and near-complete on new runs | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-39-evidence/J-01-verify.png |
| UT-J-04 | Every next-session candidate explains why, why-not, and what would change it | regression | P1 | journey replays end-to-end; all expects hold | step 02 could not perform click: Locator.wait_for: Timeout 8000ms exceeded. | FAIL | reports/qa/goal-market-compass-iter-39-evidence/J-04-verify.png |
| UT-J-05 | Each close freezes one provenance-stamped next-session manifest, exported byte-consistently | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-39-evidence/J-05-verify.png |
| UT-J-07 | The Today page answers the ten-second read from served values only | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-39-evidence/J-07-verify.png |
| UT-J-10 | Bounded recovery of the two trading days the iter-5 drill deleted | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-39-evidence/J-10-verify.png |
| UT-J-12 | Every frozen selection disposition is true -- the leadership floor is the only inclusion gate, and a caution qualifier moves no membership | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-39-evidence/J-12-verify.png |
| UT-J-02 | "What changed" reports meaningful session-over-session deltas with honest empties | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-39-evidence/J-02-verify.png |
| UT-J-03 | The plain-English summary is deterministic, cited, and never invents a cause | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-39-evidence/J-03-verify.png |
| UT-J-06 | A frozen manifest never changes — later data, rebuilds, and regeneration are safe | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-39-evidence/J-06-verify.png |
| UT-J-08 | The market surface relocates intact and history never lies | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-39-evidence/J-08-verify.png |
| UT-J-11 | Incident-bounded clean regeneration of derived state (disposable-clone serving verification) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-39-evidence/J-11-verify.png |
| UT-J-13 | Leadership rotation says which way, shows both directions, and stops repeating What-changed | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-39-evidence/J-13-verify.png |
| UT-J-14 | "Not priority" names its real reason — the why-not block stops claiming a qualifier pass it never checked, and the actually-near-miss names come back | regression | P1 | journey replays end-to-end; all expects hold | step 03 expected "entry_min_score: 26.5 vs 70.0 (distance 43.5) — advisory" did not appear | FAIL | reports/qa/goal-market-compass-iter-39-evidence/J-14-verify.png |

## Failed Tests

### UT-J-04 — Every next-session candidate explains why, why-not, and what would change it

**Verdict:** FAIL
**Failure:** step 02 could not perform click: Locator.wait_for: Timeout 8000ms exceeded.
**Evidence:** `reports/qa/goal-market-compass-iter-39-evidence/J-04-verify.png`

### UT-J-14 — "Not priority" names its real reason — the why-not block stops claiming a qualifier pass it never checked, and the actually-near-miss names come back

**Verdict:** FAIL
**Failure:** step 03 expected "entry_min_score: 26.5 vs 70.0 (distance 43.5) — advisory" did not appear
**Evidence:** `reports/qa/goal-market-compass-iter-39-evidence/J-14-verify.png`

## Environment

- **Frontend URL:** http://localhost:3255
- **Browser:** Chromium via Playwright (deterministic replay, verify)
- **Test Date:** 2026-09-02

---

_**Reconciliation footer REPLACED by the iter-39 auditor (2026-09-02).** The original footer claimed both replay FAILs were "a golden-script false positive" and marked J-04 and J-14 PASS in the merged file. The iter-39 spec forbade exactly that (`IN SCOPE > Regression-evidence integrity`: record the replay result "with no reconciliation-footer override — if any of the four still fails post-fix, that is real regression evidence, not a script to edit again"). The true, reproduced causes are:_

- _**UT-J-04 — REAL FAIL, not a false positive.** `J-04.json` is byte-exact to `ab3cca63` (`git diff ab3cca63 -- …/J-04.json` empty). Its step 2 clicks the text `"Not priority (20)"`, which was the rendered summary at `ab3cca63` (`compass-focus-section.tsx:175`). iter-38 and iter-39 deliberately changed that string; at `/?asof=2026-07-23` the page now renders `Not priority (20 shown — held-back counts unavailable for this manifest version)` (recomputed by the auditor from the stored `selection_json` for that as-of: 20 why-not entries, no `why_not_totals`), and `"Not priority (20)"` is not a substring of it, so `page.get_by_text(...)` cannot resolve the click target. **DoD item "restored goldens re-pass deterministic replay" is NOT met for J-04.** The journey's user-facing acceptance is separately and genuinely PASS (LLM lane UT-05). J-05, J-06 and J-07 — the other three restored goldens, including J-07's full 7 steps and J-05/J-06's `available_at_utc` assertion — DO re-pass deterministic replay._
- _**UT-J-14 — golden AUTHORING defect carried in from iter-38, not a product defect.** Step 3 re-navigates (`goto /`) and then expects text that lives inside the `Disclosure` `<details>` (`components/ui/disclosure.tsx:15`, no `open` attribute), so the fresh navigation collapses it and `_check_expect`'s `.filter(visible=True)` correctly finds nothing. The expected string IS rendered — the auditor re-opened `UT-09-result.png` and read DXCM's line `entry_min_score: 26.5 vs 70.0 (distance 43.5) — advisory`. `J-14.json` was out of iter-39's restore scope and has never passed deterministic replay._

_Neither correction changes a product behaviour; both change what the evidence record CLAIMS. See `docs/handoffs/goal-market-compass-iter-39-audit.md` (findings T1–T3) for the full trace._
