# UI Test Results (merged)

**Date:** 2026-09-01
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 11/11 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Sector attribution is honest and near-complete on new runs | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-34-evidence/J-01-verify.png |
| UT-J-02 | "What changed" reports meaningful session-over-session deltas with honest empties | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-34-evidence/J-02-verify.png |
| UT-J-03 | The plain-English summary is deterministic, cited, and never invents a cause | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-34-evidence/J-03-verify.png |
| UT-J-04 | Every next-session candidate explains why, why-not, and what would change it | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-34-evidence/J-04-verify.png |
| UT-J-05 | Each close freezes one provenance-stamped next-session manifest, exported byte-consistently | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-34-evidence/J-05-verify.png |
| UT-J-06 | A frozen manifest never changes — later data, rebuilds, and regeneration are safe | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-34-evidence/J-06-verify.png |
| UT-J-07 | The Today page answers the ten-second read from served values only | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-34-evidence/J-07-verify.png |
| UT-J-08 | The market surface relocates intact and history never lies | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-34-evidence/J-08-verify.png |
| UT-J-10 | Bounded recovery of the two trading days the iter-5 drill deleted | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-34-evidence/J-10-verify.png |
| UT-J-11 | Incident-bounded clean regeneration of derived state (disposable-clone serving verification) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-market-compass-iter-34-evidence/J-11-verify.png |
| UT-J-09 | The backend fits the host (regression — evidence-based, walkthrough waived) | regression | P1 | (1) live `/proc/<pid>/status` `VmPeak_kB` ≤ 2,621,440 kB; (2) `reports/perf-budgets.md` Addendum 45 states the measured figure(s) against both the 2,621,440 kB bar and iter-33's 2,467,888 kB figure, with the plateau `VmRSS_kB`/`VmSize_kB` pair recorded distinct from the end-of-window pair; (3) dev handoff states the byte-identity spot-check count ("16 compared, 0 differing" or honest non-zero); (4) `git diff --stat reports/perf-budgets.md` is append-only (`+N/-0`) | (1) Live check on the running backend (pid 2742850, port 8255): `VmPeak: 2285012 kB` — under target. (2) Addendum 45's developer-run table states `2,307,092 kB` explicitly against both the 2,621,440 kB target (-11.99%, PASS) and Addendum 44's 2,467,888 kB figure (-6.52%); Checkpoints table gives the plateau pair (`VmRSS_kB=1,734,924`, `VmSize_kB=2,307,092` at elapsed 20.99s) as distinct from the end-of-window pair (`1,286,692`/`1,854,812`). The addendum's own "Auditor run (independent re-derivation) — pending" subsection honestly discloses that the SECOND (auditor) figure the test plan also asks for does not exist yet — expected, since the auditor pipeline stage runs after browser-QA, not a defect in this pass. (3) Dev handoff line 22/142 states "byte-identity spot check (16/16 clean)" and Addendum 45 TC-5 states "16 compared, 0 differing (cmp -s clean on every one of the 16 files)" — matches. (4) `git diff --stat reports/perf-budgets.md` → `1 file changed, 127 insertions(+)` — zero deletions, append-only confirmed. | PASS | none (evidence-based journey — no UI acceptance state to screenshot, per this journey's own `docs/goal.md` "Walkthrough: waived" marker and the test plan's own framing) |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-09-01

