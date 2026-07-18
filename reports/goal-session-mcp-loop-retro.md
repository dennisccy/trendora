# Session retro — mcp-loop

> **PROPOSALS ONLY** — a human promotes candidates into docs/improvement-roadmap.md §16
> per EVO-1; nothing here is scheduled work.

**Session:** mcp-loop · **Terminal status:** GOAL_ACHIEVED · **Iterations:** 43

## Candidate items

### RETRO-1 · Reduce unattributed glue overhead in wall-time accounting
- **Proposed:** P1 · Effort M · Risk LOW
- **Problem:** "Unattributed (glue)" consumes 40–70% of wall time per iteration but is not attributed to any agent, making it impossible to identify where time is lost. This obscures bottlenecks and inflates perceived iteration cost.
- **Evidence:** Agent economics — multiple iterations show "unattributed (glue)" dominating: "goal-mcp-loop-iter-1 wall=102.8m ... unattributed (glue) 86.3m", "goal-mcp-loop-iter-22 wall=344.4m ... unattributed (glue) 291.6m", "goal-mcp-loop-iter-23 wall=441.7m ... unattributed (glue) 404.6m"
- **Sketch:** Instrument the goal-mode loop to measure handoff time, queue time, file I/O, and dispatch overhead separately. Label each in wall-time telemetry so "unattributed" shrinks to <10% and new instrumentation reveals where the 1000+ paused minutes live. Consider adding checkpoint logging at major phase boundaries (decompose → evaluate → verdict → next iter) to track blocking operations.
- **Verify idea:** Re-run a representative iteration (e.g., iter-42) and confirm that unattributed overhead drops to <15% and newly labeled categories account for ≥80% of total wall.

### RETRO-2 · Diagnostic flag for incomplete/interrupted attempt sequences
- **Proposed:** P1 · Effort S · Risk LOW
- **Problem:** Multiple iterations (18, 20, 26, 27, 30, 31, 32) show repeated `(incomplete/interrupted attempt)` + `(resume-skipped: goal-decomposer)` patterns, but there is no centralized log explaining why each resumption occurred or what condition triggered the skip. Teams cannot diagnose or prevent recurrence without reviewing session history.
- **Evidence:** Agent economics — "(incomplete/interrupted attempt)" appears 20+ times across iters 7–32; iters 18 and 20 each show 5+ incomplete attempts before a final complete run. Example: "goal-mcp-loop-iter-18 depth=full verdict=? wall=? (incomplete/interrupted attempt) goal-decomposer 120.4m calls=1 failures=1" followed immediately by more attempts and resume-skips.
- **Sketch:** Add a resume-reason field to each incomplete-attempt marker (e.g., "timeout", "oom", "hang", "user-gate") and log it to telemetry. Include a structured lesion note at the iteration level with halt reason, duration, and retry count. Expose this in retro-input.md §Halt context as a résumé-failure digest.
- **Verify idea:** Run a session that encounters a known halt condition (e.g., pump timeout) and confirm that retro-input.md names the cause and counts retries per iteration without requiring session-history inspection.

### RETRO-3 · Quantify and gate AWAITING_PUMP paused time
- **Proposed:** P0 · Effort M · Risk MED
- **Problem:** The session accumulated 1308.7m (21.8 hours) in AWAITING_PUMP paused gaps — more time than most agents spent working — yet no SLA, retry budget, or resumption strategy is codified. The pump may be a bottleneck, an intermittently slow service, or a policy gap (e.g., heartbeat missing). Long pauses hide real issues and inflate iteration cost.
- **Evidence:** Agent economics — "session: 43 completed iteration(s), mean wall 193.9m ... total AWAITING_PUMP paused gaps: 1308.7m". Multiple iterations show "pump-wait 0.3m–25.0m" in wall-time breakdown; iter-28 shows "pump-wait 25.0m" (highest recorded).
- **Sketch:** Define a pump availability SLA (e.g., <5min P95 response time) and instrument the pump resumption path to report latency per call. Add a gate that issues a warning if any single AWAITING_PUMP pause exceeds 10 min, and escalates to HALT if cumulative paused time exceeds 10% of session time. Consider adding a heartbeat timeout that resets or logs stale-pump conditions.
- **Verify idea:** Run the session with a simulated pump delay (e.g., 15 min pause) and confirm that telemetry names the delay, the gate fires a warning, and docs/improvement-roadmap.md receives a P1 follow-up note if cumulative pause time warrants action.

### RETRO-4 · Replay brittleness and golden-reconciliation rules need framework codification
- **Proposed:** P1 · Effort M · Risk MED
- **Problem:** iter-42's lesson ("The deterministic-replay lane is a golden-brittleness detector") reveals that deterministic replay can FAIL on test-fixture artifacts (timing flakes, stale DB state, cleared watchlist) rather than product bugs. Current framework has no automated way to distinguish replay FAILs from real regressions, and reconciliation is manual and error-prone. Future continuous-improvement loops will face the same trap.
- **Evidence:** Lessons tail — "iter-42 — GOAL_ACHIEVED: The deterministic-replay lane... its first run of J-23.json/J-25.json surfaced 3 FAILs that were ALL test-fixture artifacts, not product bugs"; "Do NOT loop to force a byte-clean raw-replay artifact — J-23.json depends on non-self-seeding watchlist state, so a re-run could FAIL again on an empty watchlist; gating the goal on that framework-owned fixture fragility is the #1 (unachievable-criteria) anti-pattern."
- **Sketch:** Add a framework rule: "Replay FAIL reconciliation" — (1) if a replay FAIL's `-verify.png` screenshot shows correct product behavior, treat it as a golden-stale FAIL (not a regression); (2) document which goldens depend on live-DB state (watchlist, cohort count, etc.) and mark them as "brittle" in the golden registry; (3) add an automated pre-replay step that seeds known fixtures (watchlist state, clear stale data) or auto-skips brittleness-prone goldens on their first verify run. Codify in `.claude/skills/deterministic-replay.md` or similar.
- **Verify idea:** Add a reconciliation check to the demo-runner or iter-merge step that auto-flags replay FAILs where the `-verify.png` visually matches expected behavior, tags them as fixture-artifacts, and excludes them from GOAL_ACHIEVED blocking.
