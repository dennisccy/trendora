# Session retro — market-compass

> **Ideas only — nothing here is scheduled work.** These are suggestions for
> improving the build system itself, not your product. A human reviews them and
> decides (promotion into docs/improvement-roadmap.md §16, the staging list).
> Codes: P0/P1/P2 = how urgent · Effort S/M/L = how much work · Risk LOW/MED/HIGH
> = chance a change breaks something else.

**Session:** market-compass · **Terminal status:** STALLED · **Iterations:** 16

## Candidate items

### RETRO-1 · Review verdict reliability
- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** The reviewer produced an invalid first-attempt verdict once, requiring retry. Review verdict failures add wall time and delay the goal loop.
- **Evidence:** Friction counters — "Attempt-1 review FAILs: 1"
- **Sketch:** Add pre-flight format validation before the reviewer emits its verdict line, checking format against the spec in .claude/workflow.md. If validation fails, rewrite the raw verdict rather than letting deterministic gates catch it later. Log both original and rewritten verdicts in lessons.md so implementers can track churn frequency.
- **Verify idea:** Run next session; measure whether Attempt-1 review FAILs stays at 0.

### RETRO-2 · Budget model needs recalibration
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** Twelve of 15 completed iterations exceeded the per-stage 3600-second budget, triggering trim mode repeatedly across different agent stages. This suggests the budget is misaligned with actual workload or parallelization is insufficient.
- **Evidence:** Agent economics (per-step wall breakdown) — "OVER BUDGET at qa-loop: 4178s > 3600s (mode=trim)", "OVER BUDGET at browser-qa: 5705s > 3600s (mode=trim)", "OVER BUDGET at post-dev-fanout: 4769s > 3600s (mode=trim)"
- **Sketch:** Analyze the budget-setting logic in goal-mode config. For stages most frequently over budget (post-dev-fanout appears in 6+ iterations), either increase the per-stage budget or split into finer parallel sub-stages. Use historical per-agent wall times from past sessions to refit the budget model via percentile analysis.
- **Verify idea:** Run next session and count OVER BUDGET warnings; target fewer than 4 (< 27% of iterations).

### RETRO-3 · AWAITING_PUMP idle delays erode session efficiency
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** The pump (goal-mode background service executor) paused iteration progress 501.7 minutes total, roughly one hour per iteration. This is listed as a halt reason multiple times and represents ~8% of session wall time.
- **Evidence:** Agent economics (per-step wall breakdown) — "total AWAITING_PUMP paused gaps: 501.7m"; Halt context — "halts: AWAITING_PUMP, AWAITING_PUMP, AWAITING_PUMP, STALLED, REGRESSION_HALT, STALLED, STALLED, STALLED, STALLED, STALLED"
- **Sketch:** Profile pump dispatch overhead and service startup latency. Check whether dispatch is serialized when parallel startup is possible, or whether service boot times are unexpectedly slow. Correlate AWAITING_PUMP pauses with specific iteration phases to identify which service(s) are the bottleneck.
- **Verify idea:** Add pump-level latency instrumentation; confirm AWAITING_PUMP paused gaps drop to <100m in next session.

### RETRO-4 · Long verdict stall tail without diagnostic
- **Proposed:** P2 · Effort M · Risk LOW
- **Problem:** Starting at iteration 10, the goal-evaluator declared STALLED and remained stalled through iteration 15 (6 consecutive iterations). No diagnostic was emitted to explain why or propose a recovery path before the session halted.
- **Evidence:** Verdict sequence — "iter 10: STALLED iter 11: REGRESSION iter 12: STALLED iter 13: STALLED iter 14: STALLED iter 15: STALLED"
- **Sketch:** When the goal-evaluator emits a second consecutive STALLED verdict, add a diagnostic checkpoint: list journeys still incomplete, their blockers (dependency not met, acceptance criteria mismatch, or agent timeout pattern), and a suggested retry strategy or goal amendment. Emit as a lessons entry so the human can inspect and decide whether to pause/edit or escalate.
- **Verify idea:** Run next session; if a STALLED chain ≥3 occurs, verify that a diagnostic checkpoint was emitted by iteration N+1.

### RETRO-5 · Incomplete-attempt instrumentation gap
- **Proposed:** P2 · Effort S · Risk LOW
- **Problem:** Multiple iterations recorded incomplete/interrupted attempts (7+ instances), but telemetry does not distinguish between pump death, agent timeout, and deterministic-gate halts. This obscures the true failure mode and prevents targeted fixes.
- **Evidence:** Agent economics (per-step wall breakdown) — "(incomplete/interrupted attempt)" marked at iter-0, iter-1, iter-3, iter-5, iter-8, iter-9 (2×), iter-10 (2×)
- **Sketch:** Add telemetry events before/after each major agent stage that capture pump PID and heartbeat. If an incomplete attempt is detected, emit a lessons entry with a root-cause tag: "pump-death", "agent-timeout", "deterministic-gate", or "unknown-halt". This allows post-session analysis to aggregate failure modes across sessions.
- **Verify idea:** Run next session; verify all incomplete attempts in telemetry.jsonl have a root-cause tag in lessons.md by session end.
