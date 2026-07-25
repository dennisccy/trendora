# Session retro — ops-hardening

> **PROPOSALS ONLY** — a human promotes candidates into docs/improvement-roadmap.md §16
> per EVO-1; nothing here is scheduled work.

Terminal status **STALLED** after 21 iterations (retro-input.md lines 9, 11). Drafted by the pump
directly (200-agent subagent spawn limit reached mid terminal-tail; retro-analyst is a non-gating
proposal step). Each item cites its exact evidence line in `state/retro-input.md`. Zero items would
have been valid; five are offered for human triage.

## R1 — A non-numeric `.res` silently aborts an entire iteration (DECOMPOSER_FAILED)

**Evidence:** retro-input line 276 `halts: ... DECOMPOSER_FAILED ...`; line 235
`goal-decomposer 13.2m calls=1 failures=1` (the iter-18 interrupted attempt).

**Problem:** the interactive-dispatch resolver derives a dispatch's exit code from the raw content
of the pump's `.res` file and coerces any non-numeric content to `1`
(`rc="$(cat "$res")"; [[ "$rc" =~ ^[0-9]+$ ]] || rc=1`). A pump that writes a word like `ok`
instead of `0` therefore reports a *failure* — and for a step whose success is judged by rc
directly (the goal-decomposer, Step 1), that silently aborts the whole iteration and the engine.
Gate agents mask it (their verdict is read from the artifact, so rc is ignored), so the mistake is
invisible until it lands on a decomposer/orchestrator step. It cost one full aborted iteration.

**Proposed improvement:** when `.res` content is present but non-numeric, emit a one-line WARN
(`non-numeric .res '<content>' from <agent> — coercing to 1`) before coercing, symmetric with the
existing "malformed usage sidecar" warning — converting a silent whole-iteration abort into a
diagnosable message.

## R2 — Usage-sidecar schema is under-documented; token telemetry is silently lost

**Evidence:** retro-input lines 48–65 — every agent's `Est. cost (USD)` is `0.0000` and the
`In tokens` column is implausibly low (e.g. `auditor … In 2926 / Out 622416`), alongside repeated
`interactive-dispatch … returned a malformed usage sidecar — skipping token telemetry` warnings.

**Problem:** the exact JSON shape the interactive pump must write to `$usage_path` for
`_interactive_usage_valid` to accept it is not spelled out in the dispatch skill beyond an example;
plausible shapes (`{subagent_tokens,tool_uses,duration_ms}` and `{model,num_turns,duration_ms}`)
were both rejected as malformed this session, so per-dispatch telemetry was skipped and the whole
agent-economics table reads zero cost / undercounted input tokens — the session's own cost
accounting is unusable.

**Proposed improvement:** document the required sidecar field set + types inline in
`goal-interactive-dispatch.md` (or have `_interactive_usage_valid` log which field it rejected),
so an interactive pump produces telemetry the analyzer actually ingests.

## R3 — Very large unattributed / whole-pipeline "glue" wall time

**Evidence:** retro-input line 92 `unattributed (glue) 200.4m` (iter-1); line 158
`unattributed (glue) 625.0m` (iter-9); line 230 `engine:full-pipeline 469.2m` (iter-17).

**Problem:** even after the iter-14 engine-step telemetry (RETRO-1) reclassified "unattributed
(glue)" into `engine:full-pipeline`, that bucket is still 150–470 minutes per full iteration —
larger than the sum of all agent wall times. The retro can't tell whether that is the deterministic
regression-replay lane, HTML renders, git operations, or genuine idle, so the single biggest
wall-time cost of the session is opaque to triage.

**Proposed improvement:** break `engine:full-pipeline` into its sub-steps (regression-replay,
review-packet/iter-diff build, renders, git commit/push, doctor) with the same `_engine_step_*`
helper already added in iter-14, so the dominant wall cost becomes attributable and optimizable.

## R4 — Repeated interrupted attempts + AWAITING_PUMP pauses on a long interactive run

**Evidence:** retro-input line 276 `halts: AWAITING_PUMP, AWAITING_PUMP, … DECOMPOSER_FAILED …`;
line 275 `total AWAITING_PUMP paused gaps: 9.7m`; four `(incomplete/interrupted attempt)` iteration
blocks (lines 71, 117, 144, 234).

**Problem:** across a 21-iteration interactive session the engine recorded two AWAITING_PUMP
false-pauses and four interrupted-then-resumed attempts, each of which re-runs Step 1 work (the
`resume-skipped:` lines show the re-do). The pump-PID ancestry resolver and heartbeat timing are the
known-fragile seam (project memory already documents pinning `CHAIN_PUMP_PID`).

**Proposed improvement:** make the pump-liveness check tolerate the interactive dispatcher's own
ephemeral bash wrappers by default (resolve the session binary once and cache it), so a healthy
long-running interactive pump is never mistaken for dead — cutting both the AWAITING_PUMP pauses and
the wasted re-do work.

## R5 — "Complete success but no journey crosses"; owner-gated blockers surface late

**Evidence:** retro-input line 39 `iter 20: STALLED`; line 308 lesson — *"an iteration can be a
complete, correct success at its stated target yet move NO journey to passing … STALLED is the
honest verdict."*

**Problem:** iters 18–20 were each a clean success (diagnosis, then two verified latency fixes) yet
the journeys stayed `partial` because the decisive proofs (TC-13 concurrent-ingest budget, TC-14
disruptive J-04 replay) are owner-gated behind the AG-10 ingest classifier — known since iter-15's
first STALLED. The loop nonetheless spent three full iterations before re-surfacing the same owner
decision, with no way for the owner to *durably* pre-authorize a specific gated proof (the operator
had verbal "with-watchdog-after-cooldown" authorization, yet the classifier still blocked every
ingest trigger).

**Proposed improvement:** add an owner-grantable, scoped authorization token (e.g. a
`state/authorized-ops.md` entry naming "AG-10 ingest measurement, host-guard-required") that the
safety classifier honors, so a journey blocked *only* on an owner-gated measurement can be proven or
explicitly deferred when first identified — instead of re-running full iterations that structurally
cannot cross.
