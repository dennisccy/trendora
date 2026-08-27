# Session retro — market-compass

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** market-compass · **Terminal status:** STALLED · **Iterations:** 23

## Candidate items

### RETRO-1 · Gate-stage detection of vacuous/tautological acceptance checks

- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** Acceptance criteria that assert a fact rather than measure one are silently passing through gates that guard irreversible actions. They appeared three times in a four-iteration incident recovery, and were caught only by downstream lanes (reviewer, auditor, evaluator), never by the gate stage that wrote them.
- **Evidence:** Lessons tail — iter-22: "any acceptance item that no live query or test could ever falsify must be labelled as procedural/asserted, counted separately, and surfaced to the evaluator — never allowed to contribute a silent `true` to a gate." Iter-21: "A check that asserts rather than measures. The reviewer caught it — the first time in this arc the reviewer, not the auditor or the evaluator, found the decisive defect — and the fix pass had to reorder the CLI, not just the expression."
- **Sketch:** Add a pre-gate validation rule that flags acceptance criteria lacking a falsifiable test (a case that would return false on failure). Require such checks to be marked procedural and excluded from silent pass-through. Emit a warning to the evaluator listing all procedural checks in the gate, so they appear in the verdict rationale instead of hiding inside a `true`.
- **Verify idea:** Run a session with a deliberately vacuous acceptance check; the gate stage should catch and flag it, preventing silent pass-through.

### RETRO-2 · Stall-detection heuristic for STALLED/REGRESSION loops

- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** The session entered STALLED at iteration 10 and remained there for 8 consecutive iterations before external infrastructure work unblocked it. The loop cannot recognize or escape such stuck states; it only offers continuous retries.
- **Evidence:** Verdict sequence — "iter 10: STALLED", "iter 11: REGRESSION", "iter 12: STALLED", "iter 13: STALLED", "iter 14: STALLED", "iter 15: STALLED", "iter 16: STALLED", "iter 17: STALLED", "iter 18: STALLED", then "iter 19: CONTINUE" (after external authorization).
- **Sketch:** After 4 consecutive STALLED or REGRESSION verdicts, emit a human-readable decision gate to the evaluator listing the stuck condition and propose intervention points. Surface this gate in the eval log rather than silently looping; allow the user to approve the gate and resume, or pause and edit goal.md.
- **Verify idea:** Run a recovery scenario; measure whether the loop detects the stall at iteration 4, not iteration 10, and offers a decision gate for human approval.

### RETRO-3 · Budget allocation for post-dev-fanout in high-verification sessions

- **Proposed:** P2 · Effort M · Risk MED
- **Problem:** The post-dev-fanout stage exceeded budget (3600s mode=trim) in 11 of 15 consecutive full-pipeline iterations, with the largest overages occurring during incident recovery. Trim mode suppressed verification agents (qa, auditor, ui-test-designer) at the moment when scrutiny was most needed.
- **Evidence:** Wall-time breakdown — iter-19 "OVER_BUDGET at post-dev-fanout: 16335s > 3600s (mode=trim)", iter-21 "OVER_BUDGET at post-dev-fanout: 12749s > 3600s (mode=trim)", iter-22 "OVER_BUDGET at post-dev-fanout: 17833s > 3600s (mode=trim)".
- **Sketch:** For goal-mode sessions, increase post-dev-fanout budget to 5400s–7200s, or implement two-wave verification: fast checks (gate-blocking) in wave 1, deeper checks (non-blocking) in wave 2. Mark high-stakes iterations (those gating irreversible writes or schema changes) with a flag that enables the higher budget or extra wave.
- **Verify idea:** Run a session with higher post-dev-fanout budget; measure whether auditor and qa complete without trim, and whether the same defects are caught in fewer iterations.

### RETRO-4 · Attempt-1 review failures and pre-gate integrity check

- **Proposed:** P2 · Effort S · Risk LOW
- **Problem:** Two review attempts failed on first call (attempt-1 review FAILs: 2). Defects were caught by downstream lanes rather than by the reviewer's initial pass, suggesting incomplete first-pass criteria for gates guarding high-stakes changes.
- **Evidence:** Friction counters — "Attempt-1 review FAILs: 2 (source: telemetry review_verdict events, attempt 1)". Lessons tail iter-21: "Two rules earned: (a) for any check gating an irreversible action, mutate the REAL production module and prove the suite fails, never a hand-built fixture; (b) the proof must run BEFORE the action, or it is a post-mortem, not a gate."
- **Sketch:** Add a low-cost pre-review checklist for gates guarding irreversible actions. Checklist: (1) acceptance criteria are falsifiable, (2) real production code is mutated in the proof (not a mock), (3) proof runs before the action, not after. This runs in parallel with the reviewer's main review and surfaces gaps before the reviewer votes.
- **Verify idea:** Over the next 5 sessions, measure whether attempt-1 FAILs drop to ≤1, and whether the auditor/evaluator find fewer defects (implying the pre-check catches them earlier).

