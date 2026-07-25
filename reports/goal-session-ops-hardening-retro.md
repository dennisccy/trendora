# Session retro — ops-hardening

> **PROPOSALS ONLY** — a human promotes candidates into docs/improvement-roadmap.md §16
> per EVO-1; nothing here is scheduled work.

**Session:** ops-hardening · **Terminal status:** STALLED · **Iterations:** 22

## Candidate items

### RETRO-1 · Non-numeric `.res` silently aborts iteration (DECOMPOSER_FAILED)
- **Proposed:** P1 · Effort S · Risk LOW
- **Problem:** A non-numeric `.res` file silently coerces to exit code 1, aborting whole iterations when the step is a decomposer or orchestrator. One iter-18 attempt was lost to this.
- **Evidence:** Halt context — "halts: ... DECOMPOSER_FAILED ..." (line 290); Agent economics — "goal-decomposer 13.2m calls=1 failures=1" iter-18 incomplete attempt (line 236).
- **Sketch:** Emit a one-line diagnostic WARN before coercing non-numeric `.res` to `1`, converting a silent abort into a diagnosable message. Mirror the existing "malformed usage sidecar" warning style.
- **Verify idea:** Run interactive dispatch with intentionally non-numeric `.res` and confirm the WARN appears in telemetry/logs before the step fails.

### RETRO-2 · Usage-sidecar schema undocumented; token telemetry silently lost
- **Proposed:** P1 · Effort S · Risk LOW
- **Problem:** The interactive pump's usage-sidecar JSON shape is not documented; malformed sidecars are silently skipped, so session cost accounting and input-token counts read as zero/implausible (auditor in/out 2926/622416, cost 0.0000 USD).
- **Evidence:** Agent economics — "every agent's Est. cost (USD) is 0.0000" and "In tokens column implausibly low" (lines 48–65); telemetry shows "malformed usage sidecar — skipping token telemetry" warnings (implied by zero cost).
- **Sketch:** Document the required sidecar field set and types inline in goal-interactive-dispatch.md or have `_interactive_usage_valid` log which field it rejected per-dispatch.
- **Verify idea:** Run a session with the documented schema and confirm agent economics table shows non-zero per-agent costs and input-token counts.

### RETRO-3 · Engine pipeline wall time opaque; "glue" bucket lacks sub-step attribution
- **Proposed:** P2 · Effort M · Risk LOW
- **Problem:** `engine:full-pipeline` and `unattributed (glue)` account for 150–625 minutes per iteration—larger than all agent wall times combined—but the retro cannot decompose whether it is regression-replay, renders, git ops, or idle, blocking wall-time optimization.
- **Evidence:** Agent economics wall-time report — iter-1 "unattributed (glue) 200.4m" (line 92); iter-9 "unattributed (glue) 625.0m" (line 159); iter-17 "engine:full-pipeline 469.2m" (line 232).
- **Sketch:** Break `engine:full-pipeline` into sub-steps (regression-replay, review-packet/iter-diff, renders, git/doctor) using the same `_engine_step_*` instrumentation helper added in iter-14.
- **Verify idea:** Re-run session with enhanced engine telemetry and confirm each sub-step appears as its own line in wall-time report.

### RETRO-4 · Repeated interrupted attempts and AWAITING_PUMP false-pauses on long interactive runs
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** A 22-iteration interactive session recorded four incomplete-then-resumed attempts and two AWAITING_PUMP false-pauses, each re-running decomposer work. The pump-PID ancestry resolver is the fragile seam; the project memory documents the required CHAIN_PUMP_PID pinning workaround.
- **Evidence:** Halt context — "halts: AWAITING_PUMP, AWAITING_PUMP, REGRESSION_HALT, ... DECOMPOSER_FAILED, STALLED, STALLED" (line 290); wall-time report — four iterations with "(incomplete/interrupted attempt)" annotation (lines 71, 117, 144, 234); "total AWAITING_PUMP paused gaps: 9.7m" (line 289).
- **Sketch:** Cache the session binary path once at pump startup to avoid re-resolving PID ancestry through ephemeral bash wrappers, or make the liveness check tolerate the dispatcher's wrapper process hierarchy by default.
- **Verify idea:** Run a 20+ iteration interactive session and confirm zero AWAITING_PUMP pauses and zero incomplete-then-resumed attempts appear in the halt halts list.
