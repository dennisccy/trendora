# Session retro — market-compass

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** market-compass · **Terminal status:** STALLED · **Iterations:** 16

## Candidate items

### RETRO-1 · Post-dev-fanout and qa-loop stage budgets hit quota limits in 13 iterations

- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** The goal pipeline's post-dev-fanout and qa-loop stages exceed their 3600-second quota limits in most iterations, forcing work to be trimmed. This systematic bottleneck may compromise verdict quality or miss detection of problems.
- **Evidence:** Agent economics — "OVER BUDGET at qa-loop: 4178s > 3600s (mode=trim)" (line 102), "OVER BUDGET at post-dev-fanout: 4769s > 3600s (mode=trim)" (line 139), "OVER BUDGET at browser-qa: 5705s > 3600s (mode=trim)" (line 117), and similar entries at lines 154, 175, 194, 241, 265, 281, 295, 320, 336, 352.
- **Sketch:** Analyze workload distribution in post-dev-fanout (auditor, qa, reviewer, etc.) and qa-loop; split lower-priority agents (e.g., demo-narrator, ui-test-designer, readme-maintainer) into optional async lanes, or increase budgets for critical-path stages.
- **Verify idea:** Next session shows OVER BUDGET entries in <3 of 16 iterations, or trimmed work represents <5% of verdict decisions.

### RETRO-2 · AWAITING_PUMP idle delays consume 8% of session wall time

- **Proposed:** P1 · Effort S · Risk LOW
- **Problem:** The pump (goal-mode background service executor) paused iteration progress for 501.7 minutes total, about one hour per iteration. This system-level bottleneck is listed as a halt reason multiple times.
- **Evidence:** Agent economics — "total AWAITING_PUMP paused gaps: 501.7m" (line 371); halt trace includes "halts: AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP" (line 372).
- **Sketch:** Profile pump dispatch overhead and service startup latency; check whether dispatch is serialized when parallel startup is possible, or if service boot times are unexpectedly slow.
- **Verify idea:** Add pump-level latency instrumentation; confirm AWAITING_PUMP paused gaps drop to <100m in the next session.

### RETRO-3 · Incomplete iteration attempts lack documented failure reason

- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** Eight iterations show multiple failed attempts before a successful verdict. Developers and agents marked failures but the root cause (timeout, transient error, gate rejection, or logic error) is not recorded, blocking root-cause diagnosis.
- **Evidence:** Agent economics — iter 0 "(incomplete/interrupted attempt)" with "goal-decomposer failures=1" (line 62), iter 1 with "developer failures=2" (line 80), iter 8 with "reviewer failures=1" (line 197), iter 9 with "orchestrator failures=1" (line 221); many other iterations show duplicate attempts without explanation.
- **Sketch:** Extend telemetry to emit the failure mode for each incomplete attempt: timeout, agent-returned error, deterministic gate rejection, or transient error. Log this before the retry.
- **Verify idea:** Next session's incomplete attempts are tagged by failure mode; retry patterns are actionable from telemetry.

### RETRO-4 · Six consecutive STALLED verdicts indicate halt gate is too lenient

- **Proposed:** P1 · Effort S · Risk MED
- **Problem:** Iterations 10–15 all verdict as STALLED (with one REGRESSION at iter 11), suggesting the goal state became unreachable or goal-evaluator is stuck. The session did not halt early despite obvious convergence failure.
- **Evidence:** Verdict sequence — "iter 10: STALLED iter 11: REGRESSION iter 12: STALLED iter 13: STALLED iter 14: STALLED iter 15: STALLED" (lines 28–34).
- **Sketch:** Add a halt gate that fires after N consecutive STALLED verdicts (propose N=3). Alternatively, investigate whether goal-evaluator logs show why convergence failed and whether that signal is being ignored.
- **Verify idea:** Next session halts by iter 13 if the pattern emerges; gate fires correctly before iteration 16, saving wall time.
