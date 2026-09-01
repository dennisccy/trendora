# J-09 Non-UI Evidence — goal-market-compass-iter-34

**Phase:** goal-market-compass-iter-34
**Date:** 2026-09-01
**Written by:** developer (goal-mode harness fix, TC-7/TC-8 — cited non-UI evidence for a
walkthrough-waived journey; see `merge_ui_test_results.py`'s `parse_waived_journeys_from_text` /
`_has_cited_evidence`)

---

**Browser QA Verdict:** SKIPPED

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-09 | The backend fits the host — standing memory halves with zero behavior change | smoke | P1 | N/A — journey's own `docs/goal.md` Acceptance carries the literal `**Walkthrough:** waived` marker (backend-only; no displayed value may move) | No UI surface exists for this journey; verified instead through the extended (369.43s, ≥360s) standing-warm VmPeak/VmSize/VmRSS re-measurement (max VmPeak 2,307,092 kB, 11.99% under the 2,621,440 kB target), the 16/16 clean byte-identity spot check, and the zero-database-write proof, all recorded in `reports/perf-budgets.md` Addendum 45 and `docs/handoffs/goal-market-compass-iter-34-dev.md` | SKIP | `reports/perf-budgets.md` Addendum 45; `runs/goal-market-compass-iter-34/j09-vmpeak-samples-dev.csv`; `runs/goal-market-compass-iter-34/byte-identity-now/` |

## Skipped Tests

### UT-J-09 — The backend fits the host — standing memory halves with zero behavior change

**Verdict:** SKIPPED
**Reason:** `docs/goal.md`'s J-09 Acceptance section states verbatim: "**Walkthrough:** waived —
deliberately backend-only (no UI surface changes); the demo requirement is replaced by the dated
VmPeak measurement and drill citations in the dev handoff." There is no page, route, or
user-visible element for a browser to exercise. Verification instead cites the concrete artifacts
above (Addendum 45, the raw sampler CSV, the byte-identity capture directory) — this is the "cited
non-UI evidence" the goal-mode harness fix (`merge_ui_test_results.py` iter-34) reads to avoid
forcing a clean `BLOCKED` on a journey with no UI to check.

## Environment

- **Browser:** N/A — no UI surface for this journey (see Reason above)
- **Test Date:** 2026-09-01
