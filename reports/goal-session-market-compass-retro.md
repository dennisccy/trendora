# Session retro — market-compass

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** market-compass · **Terminal status:** STALLED · **Iterations:** 11

## Candidate items

### RETRO-1 · Reviewer agent wall-time dominance
- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** The reviewer agent consumed 900.5 minutes total, the largest of any agent and 31% more than developer (687.8m). This suggests reviewer is either a bottleneck or running inefficient loops that could be optimized.
- **Evidence:** Agent economics — "total reviewer 900.5m", "total developer 687.8m"; Wall breakdown — "iter-6: reviewer 152.5m calls=1", "iter-7: reviewer 373.9m calls=2 failures=1", "iter-8: reviewer 300.0m calls=1 failures=1"
- **Sketch:** Profile reviewer per-iteration execution: check if it's waiting on dependencies, re-reviewing same artifact, or running unnecessarily deep checks. Options: cache review outputs across retry attempts, parallelize independent review checks, shorten review depth for low-risk paths.
- **Verify idea:** Next similar-scope goal session should show reviewer wall-time ≤ developer wall-time (or within 10% margin).

### RETRO-2 · Repeated stage budget overages
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** Eight of eleven iterations exceeded their per-stage time budgets (1–3 hours each), forcing automatic trimming. This recurring friction prevents the pipeline from staying within its resource envelope.
- **Evidence:** Friction counters (wall breakdown) — "OVER BUDGET at qa-loop: 4178s > 3600s (mode=trim)" (iter-1), "OVER BUDGET at browser-qa: 5705s > 3600s (mode=trim)" (iter-2), "OVER BUDGET at post-dev-fanout: 4769s > 3600s (mode=trim)" (iter-3), "OVER BUDGET at post-dev-fanout: 4319s > 3600s (mode=trim)" (iter-7), "OVER BUDGET at post-dev-fanout: 4809s > 3600s (mode=trim)" (iter-9), "OVER BUDGET at goal-evaluator: 3757s > 3600s (mode=trim)" (iter-10), plus iters 4 and 6
- **Sketch:** Review stage budgets in .claude/workflow.md or engine config. Determine if consistently-overrunning stages (browser-qa, post-dev-fanout, goal-evaluator) need higher budgets, fewer parallel agents, or reduced scope. Implement early-exit heuristics if progress stalls before budget exhaustion.
- **Verify idea:** Next session should show ≤2 OVER BUDGET warnings (one-off spikes acceptable, recurring pattern unacceptable).

### RETRO-3 · AWAITING_PUMP halts and pump-wait latency
- **Proposed:** P0 · Effort M · Risk MED
- **Problem:** Three AWAITING_PUMP halts accumulated 501.7 minutes (8.4 hours) of stalled wall time. This infrastructure friction suggests pump availability or dispatch latency is blocking session progress repeatedly.
- **Evidence:** Wall breakdown — "total AWAITING_PUMP paused gaps: 501.7m"; "halts: AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP, STALLED"; iter-7 "pump-wait 373.9m", iter-9 "pump-wait 341.1m"
- **Sketch:** Correlate AWAITING_PUMP instances with pump availability and dispatch-queue logs. Likely causes: pump restart loops, slow dispatch queuing, or dispatch-to-ready latency. Remedies: add pump heartbeat monitoring, implement dispatch backpressure, or trial an in-process pump variant for small sessions.
- **Verify idea:** Next session should have zero AWAITING_PUMP halts (or ≤1 brief transient with <10m wait).

### RETRO-4 · Fixture-test insufficiency for live-DB schema validation
- **Proposed:** P0 · Effort M · Risk LOW
- **Problem:** Acceptance criteria passed fixture-DB tests but failed on live schema: FK constraints remained in live DDL while code assumed they were dropped, and degenerate inputs (row exists, field missing) were not tested. Reviewer and QA relied on fixture tests; only auditor checked live DDL and caught the gap.
- **Evidence:** Lessons tail — iter-10: "A 'schema contract proven by fixture-DB tests' can be fully green and still be false on the production database", "Both the reviewer and QA recorded that DoD item complete on the strength of the passing fixture tests; only the auditor queried the live DDL", "TC-5 orphan test covered only the latter [missing-row branch]"
- **Sketch:** For acceptance items involving live schema or fail-closed read paths: (a) add a pre-approval verification step that checks live-DB artifacts (sqlite_master, pragma_foreign_key_check) before marking DoD complete; (b) extend test suites to cover degenerate cases (row exists but field missing) alongside missing-row cases; (c) update reviewer/QA instructions to explicitly require live-DB checks for schema-related acceptance items.
- **Verify idea:** Next session's equivalent acceptance items should cite live-DB checks in reviewer/QA/auditor verdicts, or acceptance criteria explicitly exclude live-schema validation.
