# Session retro — ops-hardening

> **PROPOSALS ONLY** — a human promotes candidates into docs/improvement-roadmap.md §16
> per EVO-1; nothing here is scheduled work.

**Session:** ops-hardening · **Terminal status:** REGRESSION_HALT · **Iterations:** 8

## Candidate items

### RETRO-1 · Instrument unattributed wall-time in full-depth iterations
- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** Full-depth iterations show 200–584m "unattributed (glue)" wall time, often 50–90% of total iteration time. Pipeline visibility into service startup, loop overhead, and async waits is missing.
- **Evidence:** Agent economics — "unattributed (glue): 200.4m" (iter 1), "unattributed (glue): 584.5m" (iter 2), "unattributed (glue): 261.7m" (iter 7) in the wall-time report.
- **Sketch:** Split "unattributed (glue)" into named intervals: service-ready delay (bootstrap time before first agent call), loop-overhead (inter-agent dispatch and artifact I/O), and async-waits (explicit poll/sleep periods). Tag each with its source (service restart, deterministic gate, resume handoff, etc.).
- **Verify idea:** A future full-depth iteration wall-time report shows named categories totaling the previous "unattributed" time, with zero residual "glue"; operator can diagnose which category dominates.

### RETRO-2 · Track partial-attempt halt/resume root cause
- **Proposed:** P2 · Effort M · Risk LOW
- **Problem:** Iterations 0 and 5 show "incomplete/interrupted attempt" entries with no reason logged. Absence of a cause field makes it impossible to distinguish transient failures, timeouts, and hard halts, blocking diagnosis of resumption reliability.
- **Evidence:** Agent economics — "goal-ops-hardening-iter-0  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)" and "goal-ops-hardening-iter-5  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)" in wall-time report.
- **Sketch:** When an iteration attempt terminates partway (before evaluator calls verdict), record the halt reason in telemetry: timeout, quota_limit, signal, service_error, or framework_gate. Pass this to the wall-time summarizer so each incomplete attempt line includes "(reason: <cause>)".
- **Verify idea:** Next incomplete attempt in any session will include a cause line; operator no longer guesses whether a resume is fixing transience or a real blocker.

### RETRO-3 · Decompose pump-wait variance into dispatch overhead and subagent-hold time
- **Proposed:** P2 · Effort M · Risk MED
- **Problem:** pump-wait ranges from 0.1m to 226.9m across iterations with no visibility into components: how much is dispatch+service-ready vs. subagent running but not counted to the subagent wall. This conflates infrastructure latency with long-running agent time, blocking optimization.
- **Evidence:** Agent economics — pump-wait variance across iters: "pump-wait 0.1m" (iter 0 resume), "pump-wait 226.9m" (iter 2), "pump-wait 1.6m" (iter 7) in wall-time report.
- **Sketch:** Split pump-wait into: dispatch-latency (elapsed from pump dispatch to subagent start), subagent-hold (time agent runs but frame-skip isn't complete), and service-ready-delay (time waiting for services to be available). Emit each as a separate telemetry counter per iteration.
- **Verify idea:** A future iteration shows pump-wait broken into three named sub-counters that sum to the previous "pump-wait" time; operator identifies whether high pump-wait is dispatch overhead or subagent lag.

