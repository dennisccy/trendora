# Session retro — market-compass

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** market-compass · **Terminal status:** REGRESSION_HALT · **Iterations:** 39

## Candidate items

### RETRO-1 · Golden-script mutation detection
- **Proposed:** P0 · Effort M · Risk LOW
- **Problem:** Evaluators can edit golden replay scripts AFTER they fail, but the pipeline never compares script bytes before and after, making this invisible and breaking regression detection. It's a human process issue that needs automation.
- **Evidence:** Lessons tail — "A golden replay script that is edited AFTER it fails, in the same run, is no longer regression evidence. This round's replay failed 9 of 12 at 18:41-18:43; at 19:26 the goldens for J-04/J-05/J-06/J-07 were rewritten... Nothing in the pipeline compares a golden's bytes before and after a replay, so this is invisible unless the evaluator runs `git diff` on `runs/goal-session-*/journey-scripts/`."
- **Sketch:** Snapshot golden scripts (`journey-scripts/` tree) at the start of evaluator logic. After replay completes, diff the tree and flag any mutations in the reconciliation footer or evaluator output. This blocks false-positive regression credits and forces explicit override if edits are intentional.
- **Verify idea:** Run a test session that deliberately mutates a golden mid-evaluation; the evaluator flag must catch and report it before reconciliation concludes.

### RETRO-2 · Reviewer time-budget overages
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The reviewer exceeds its 1-hour budget in at least 5 iterations (6, 7, 19, 21, 22), with wall times ranging 152–374 min. This causes cascade delays and may trigger stalled sequences downstream.
- **Evidence:** Agent economics wall-time report — iter 6: "reviewer 152.5m", iter 7: "reviewer 373.9m", iter 19: "reviewer 172.2m", iter 21: "reviewer 142.6m", iter 22: "reviewer 198.6m"; multiple entries show "OVER BUDGET at post-dev-fanout: <time>s > 3600s (mode=trim)".
- **Sketch:** Analyze review invocations during high-budget iterations to identify scope outliers (e.g., unusually large diffs, feedback loops). Either split reviewer workload earlier (tier-1 quick-pass before fanout) or increase the budget cap for review-heavy iterations. Tune evaluator's workload-sensing.
- **Verify idea:** Run a repeat of an over-budget iteration (e.g., iter 7); if wall time for reviewer stays under 60 min after the change, the fix worked.

### RETRO-3 · Attempt-1 review failures
- **Proposed:** P1 · Effort S · Risk LOW
- **Problem:** Reviews fail on first attempt 4 times across 50 reviewer invocations (8% failure rate). This suggests incomplete input preparation, async state issues, or reviewer expectation mismatches.
- **Evidence:** Friction counters — "Attempt-1 review FAILs: 4 (source: telemetry review_verdict events, attempt 1)"
- **Sketch:** Profile the 4 failures by examining telemetry review_verdict events; check if they share a pattern (e.g., missing file, malformed code diff, stale branch). Add a pre-review validation step to detect and fail-fast on common input gaps before invoking the reviewer.
- **Verify idea:** Fix the root cause and run 10 goal-mode iterations; if attempt-1 fail rate drops to ≤1%, the fix is solid.

### RETRO-4 · GOAL_ACHIEVED continuation and regression halt
- **Proposed:** P0 · Effort S · Risk MED
- **Problem:** The session declared GOAL_ACHIEVED at iters 34 and 37, but continued to iter 38 and emitted a REGRESSION verdict, halting the run. This violates the expectation that GOAL_ACHIEVED is terminal or requires explicit re-engagement.
- **Evidence:** Verdict sequence — "iter 34: GOAL_ACHIEVED iter 35: CONTINUE iter 36: ESCALATE iter 37: GOAL_ACHIEVED iter 38: REGRESSION" and Outcome — "Terminal status: REGRESSION_HALT".
- **Sketch:** Clarify engine halting logic: either GOAL_ACHIEVED is truly terminal (engine stops, no further iterations), or if continuation is allowed, add a "post-achievement verification" gate that prevents regression verdicts from overriding an already-achieved state. Document the expected behavior in `.claude/workflow.md`.
- **Verify idea:** Run a goal-mode session that achieves the goal; verify the engine halts cleanly and does not produce a REGRESSION verdict in a later iteration.

### RETRO-5 · Extended stalled sequence without escalation
- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** The session entered a stalled sequence (iters 10–18, eight consecutive STALLED or STALLED-ish verdicts) with no automatic escalation or halt. The evaluator lacks a detector for unproductive loops or stuck states.
- **Evidence:** Verdict sequence — "iter 10: STALLED iter 11: REGRESSION iter 12: STALLED iter 13: STALLED iter 14: STALLED iter 15: STALLED iter 16: STALLED iter 17: STALLED iter 18: STALLED"
- **Sketch:** Implement a stall-counter in the evaluator: if ≥5 consecutive STALLED verdicts occur without a CONTINUE/ESCALATE/GOAL_ACHIEVED, auto-escalate to BLOCKED or trigger a manual review checkpoint. Alternatively, add a heuristic to detect zero progress (e.g., no new fixes, same test failures) and halt earlier.
- **Verify idea:** Inject a synthetic stalled loop (modify goal-evaluator to emit STALLED repeatedly) and verify the engine detects it and escalates within 5 iterations.
