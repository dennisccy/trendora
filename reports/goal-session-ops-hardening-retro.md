# Session retro — ops-hardening

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** ops-hardening · **Terminal status:** STALLED · **Iterations:** 79

## Candidate items

### RETRO-1 · Evaluator allows sustained escalation churn without halt
- **Proposed:** P0 · Effort M · Risk MED
- **Problem:** Verdicts went predominantly ESCALATE (43 of 53 iters) from iter 35 onward, with most iterations then timing out (OVER BUDGET). When the system is stuck in a loop where the developer is escalated, times out, then escalates again, the evaluator should detect this pattern and halt or ask the owner, not continue for 55 more iterations.
- **Evidence:** Verdict sequence — "iter 35–78: [35: ESCALATE, 36–41: ESCALATE×6, 42: REGRESSION, 43–52: ESCALATE×9, 53: CONTINUE, 54: ESCALATE, 55: CONTINUE, 56–78: alternating ESCALATE/CONTINUE, ending 78: STALLED]" and wall-time report — "OVER BUDGET at post-dev-fanout: 3712s > 3600s (mode=trim)" repeated at lines 672, 691, 711, 753, 772, 791, 810, 832, 860, 879, 930, 960, 991, 1006, 1022, 1047, 1069, 1084, 1103, 1138, 1153, 1167, 1182, 1197, 1212, 1227, 1247, 1262, 1281, 1296, 1311, 1323, 1335, 1354, 1373.
- **Sketch:** Add a detector to the goal-mode evaluator that tracks ESCALATE rate over a rolling window (e.g., last 5 verdicts). If ESCALATE ≥4 in 5, flag it as "churn detected" and emit a HALT_ESCALATE_CHURN or escalate to the owner for manual decision rather than continuing autonomously.
- **Verify idea:** Run a replay on this session's telemetry and confirm that the detector fires at iter 35–40 (before the budget messages) and recommends halt.

### RETRO-2 · Post-dev-fanout agents consistently exceed budgets, degrading verdicts
- **Proposed:** P0 · Effort M · Risk MED
- **Problem:** From iter 33 onward, nearly every iteration shows "OVER BUDGET at post-dev-fanout/browser-qa/coherence-auditor", trimming agent outputs. When evaluation agents are trimmed, the evaluator receives incomplete evidence, leading to unreliable verdicts. Over 40 budget-overflow events in 79 iterations is structural, not transient.
- **Evidence:** Wall-time report — 40+ lines with "OVER BUDGET at post-dev-fanout: ####s > 3600s (mode=trim)" or "OVER BUDGET at browser-qa: ####s > 3600s (mode=trim)" or "OVER BUDGET at coherence-auditor" from lines 537, 552, 582, 602, 622, 653, 672, 691, 711, 726, 753, 772, 791, 810, 832, 860, 879, 897, 930, 960, 991, 1006, 1022, 1047, 1069, 1084, 1103, 1138, 1153, 1167, 1182, 1197, 1212, 1227, 1247, 1262, 1281, 1296, 1311, 1323, 1335, 1354, 1373.
- **Sketch:** Increase the 3600s budget for post-dev-fanout or split it into two sequential phases (qa-fast, qa-slow) with independent budgets. Alternatively, add a circuit-breaker: if an agent is trimmed 3 times in 5 iterations, escalate rather than continue trimming.
- **Verify idea:** Re-run the session with updated budget(s) and confirm that OVER BUDGET count drops below 5 and ESCALATE rate normalizes.

### RETRO-3 · Closure gate regex rejects artifacts for quoting words it prohibits
- **Proposed:** P1 · Effort S · Risk LOW
- **Problem:** The closure_gate.py:66 regex (`\bTODO\b|\bTBD\b|<fill|…`) matches TODO/TBD anywhere in artifacts. A browser-qa report that honestly quoted Chrome-MCP's own file contents ("TODO: Console logging not yet implemented") failed the gate because the regex found the word in a quoted message, not in the reporter's own prose. Valid evidence gets rejected for its source text, not the reporter's work.
- **Evidence:** Lessons tail — iter-final lesson: "closure_gate.py:66's placeholder regex... matches the token anywhere in a UI-visibility artifact, including inside a QUOTED tool message. This round's browser-qa row honestly quoted Chrome-MCP's own file contents ("TODO: Console logging not yet implemented") and that single quotation failed the closure gate."
- **Sketch:** Improve the regex or pre-processing to skip quoted blocks (lines prefixed with `>` or inside code fences) before matching. Or add a manual-skip flag that agents can set for quoted sections.
- **Verify idea:** Add a unit test that confirms a quoted "TODO: ..." inside a browser-qa report now passes the gate, while an unquoted "TODO" still fails.

### RETRO-4 · Evaluator does not detect self-reinforcing acceptance-criteria feedback loops
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The session's unresolved-note count trended upward (138 → 140 → 146) across three consecutive rounds where all eight journeys passed, because each auditing cycle added more unresolved notes than it closed. The evaluator has no mechanism to recognize "this criterion itself is the blocker" and continues escalating. The goal loop should detect when a self-maintained criterion is trending away from zero despite all journeys passing, and halt or escalate to the owner for guidance.
- **Evidence:** Lessons tail — iter-78 lesson: "An acceptance criterion that a thorough audit keeps adding to cannot be driven to zero by working harder... When the count trends UP across rounds with no failing journeys, the criterion — not the work — is the blocker, and that is an owner decision, not another iteration."
- **Sketch:** Track each measured criterion's trend over the last 3 verdicts. If all journeys pass AND a criterion's value is trending away from zero (e.g., unresolved-notes: 138→140→146), emit a HALT_CRITERION_UNRESOLVABLE verdict instead of CONTINUE/ESCALATE. Escalate to owner for decision: raise the threshold, remove the criterion, or redefine it.
- **Verify idea:** Replay this session and confirm the detector fires at iter 78 (or earlier, once the trend is clear).

### RETRO-5 · Machine resets and pump coordination gaps interrupt session flow
- **Proposed:** P1 · Effort L · Risk HIGH
- **Problem:** The halt history shows 11 machine_reset halts and 5 AWAITING_PUMP halts, indicating infrastructure instability or coordination issues between the interactive pump and long-running subagents. When machines reset mid-iteration, the session must be resumed, but context and breadcrumbs are lost, causing the goal to drift or loop.
- **Evidence:** Halt context — halts list contains "machine_reset" 11 times and "AWAITING_PUMP" 4 times, suggesting infrastructure interruptions.
- **Sketch:** Implement persistent iteration checkpoints (save agent state mid-pipeline) and a recovery log so a resumed session can skip completed agent calls. Add a heartbeat from the pump to long-running agents to detect if the pump is dead and halt gracefully instead of AWAITING_PUMP for hours.
- **Verify idea:** Deploy the checkpoint/recovery system and re-run a similar 79-iteration session; confirm machine_reset halts drop to zero and AWAITING_PUMP pauses are < 1 minute total.
