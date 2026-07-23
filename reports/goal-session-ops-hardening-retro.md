# Session retro — ops-hardening

> **PROPOSALS ONLY** — a human promotes candidates into docs/improvement-roadmap.md §16
> per EVO-1; nothing here is scheduled work.

**Session:** ops-hardening · **Terminal status:** REGRESSION_HALT · **Iterations:** 14

## Candidate items

### RETRO-1 · Instrument unattributed (glue) time in wall-time breakdown
- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** Wall-time breakdown shows recurring large "unattributed (glue)" periods (200–625m per full-depth iteration), consuming ~40–70% of total iteration wall time. This prevents the framework from identifying actual bottlenecks, attributing cost accurately, or optimizing handoff latency in the goal loop.
- **Evidence:** Agent economics — "unattributed (glue): 200.4m" (iter 1), "unattributed (glue): 584.5m" (iter 2), "unattributed (glue): 625.0m" (iter 9), "unattributed (glue): 261.7m" (iter 7), "unattributed (glue): 228.4m" (iter 13).
- **Sketch:** Audit the pump/engine coordinator to identify where wall-clock time elapses between agent completion and the next agent dispatch. Add explicit timing instrumentation for: (1) pump-wait periods that span outside named agents, (2) inter-agent queue/handoff delays, (3) any background service startup/teardown. Emit a new telemetry event type for each gap.
- **Verify idea:** Run a test session and confirm that (unattributed glue time) + (sum of named agent times) ≈ total iteration wall time, with <5% unexplained residue.

nothing recurred worth proposing as additional items because all friction counters are zero, lessons tail is product-specific (AG-8 anti-goal regression under load), and verdict churn reflects correct evaluator behavior catching regressions.
