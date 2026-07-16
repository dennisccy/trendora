You are the goal-evaluator agent for goal-mode iteration evaluation.

Session ID: mcp-loop
Iteration index: 41
Iter name: goal-mcp-loop-iter-41
Depth dispatched: full

Project goal (SLICED — vision + anti-goals + target/failing journeys verbatim; stable passing journeys digested): /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/iter-41/goal-slice.md
  Full goal file: /home/dennis-chan/Git/trendora/docs/goal.md — Read it ONLY if a digested journey becomes relevant.
Iter spec: /home/dennis-chan/Git/trendora/docs/phases/goal-mcp-loop-iter-41.md
Agent instructions: .claude/agents/goal-evaluator.md  <-- read this first
(CLAUDE.md is already in your system prompt — do not Read it again.)

NOTE — dispatch reconstruction (read this): the usual inlined "recent evaluator-log entries (last 5)" and "assumption-ledger tail" blocks were OMITTED from this prompt because the full dispatch payload exceeded the OS argument-size limit (a known framework bug: interactive-dispatch.sh builds the JSON via `jq --arg`, which caps at MAX_ARG_STRLEN and fails on the ever-growing inlined evaluator-log — the engine published a 0-byte .ready). Nothing is lost — read the real on-disk sources directly, which are authoritative:
  - Evaluator log (append your new entry; its tail holds the recent per-iteration entries that would have been inlined): /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/evaluator-log.md
  - Assumption ledger (its tail holds recent scoring-assumption entries; append only if this iteration required interpreting an ambiguous goal): /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/assumptions.md
  - Lessons: /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/lessons.md

Iteration artifacts (read what exists):
  Deterministic diff scan (product diff; harness bookkeeping excluded — secrets/deps/license): /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/iter-41/scan-report.md
  Bounded diff view (complete file list; hunks capped, header lists omissions): /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/iter-41/iter-diff.md
  Dev handoff: docs/handoffs/goal-mcp-loop-iter-41-dev.md
  Frontend handoff: docs/handoffs/goal-mcp-loop-iter-41-frontend.md
  Review report: reports/reviews/goal-mcp-loop-iter-41-review.md
  QA report: reports/qa/goal-mcp-loop-iter-41-qa.md (full mode only)
  Audit handoff: docs/handoffs/goal-mcp-loop-iter-41-audit.md (full mode only)
  Browser QA results: reports/phase-goal-mcp-loop-iter-41-ui-test-results.md
  Evidence: reports/qa/goal-mcp-loop-iter-41-evidence/
  Coherence audit: /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/iter-41/coherence.md  <-- this iter = COHERENCE-WARN (one non-blocking Part-C advisory: the expectations-table phase badges use a flat variant instead of the shared lib/phase.ts color mapping). NOTE: only COHERENCE-FAIL vetoes GOAL_ACHIEVED / drives a consolidation CONTINUE; a WARN does NOT veto — weigh it as advisory.
  Goal-edit drift note: /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/iter-41/journeys-changed.md  <-- NOT present this iter (no journey spec_hash changed), so no journey's prior pass is voided on that account.

Journey state (inline digest — your methodology's section A table; AUTHORITATIVE copy is runs/goal-session-mcp-loop/state/journey-history.json, read it for any field this digest omits):
```
J-01 | passing         | last_passing=goal-mcp-loop-iter-40 | Every score shows an evidence status
J-02 | passing         | last_passing=goal-mcp-loop-iter-39 | Drill into the evidence behind a score
J-03 | passing         | last_passing=goal-mcp-loop-iter-40 | Unproven / noise signals are honestly marked
J-04 | passing         | last_passing=goal-mcp-loop-iter-39 | Regime-conditioned evidence
J-05 | passing         | last_passing=goal-mcp-loop-iter-39 | Audit the evidence ledger
J-06 | passing         | last_passing=goal-mcp-loop-iter-39 | vcp_contraction top-decile certified evidence outcome surfaced on Evidence + Research factor lab
J-07 | passing         | last_passing=goal-mcp-loop-iter-39 | Multi-horizon certified evidence outcome surfaced (the loop sees beyond the 20-day horizon)
J-08 | passing         | last_passing=goal-mcp-loop-iter-39 | Multi-factor combination certified evidence outcome surfaced on the Combination lab + Evidence
J-09 | passing         | last_passing=goal-mcp-loop-iter-39 | Relative-strength (rs_spy_3m) 60-day-horizon certified evidence outcome surfaced on Evidence + Research factor lab
J-10 | passing         | last_passing=goal-mcp-loop-iter-40 | The product surfaces deep (up to ~30-year) price history, honestly bounded per name
J-11 | passing         | last_passing=goal-mcp-loop-iter-39 | Every displayed 'Proven' edge is re-certified on the new 30-year data -- no stale edge survives
J-12 | passing         | last_passing=goal-mcp-loop-iter-39 | The universe is a broad, point-in-time dynamic set across the deep history
J-13 | passing         | last_passing=goal-mcp-loop-iter-39 | The Data Manager page reflects the broadened 548-symbol universe with an unambiguous availability legend
J-14 | passing         | last_passing=goal-mcp-loop-iter-39 | The 30-year basis carries deep, honestly-sourced index context (benchmarks + macro), each labeled by vendor
J-15 | passing         | last_passing=goal-mcp-loop-iter-27 | Core pages and APIs stay fast on the deep basis -- measured, budgeted, never regressing
J-16 | passing         | last_passing=goal-mcp-loop-iter-35 | Data jobs (Fetch + Backfill + warmup) are fast and honest about progress
J-17 | passing         | last_passing=goal-mcp-loop-iter-39 | The statistical budget is visible before it is spent
J-18 | passing         | last_passing=goal-mcp-loop-iter-39 | Every evidence claim must match a pre-registration -- enforced by the gate
J-19 | passing         | last_passing=goal-mcp-loop-iter-39 | Dead hypotheses are browsable so nobody retries them blindly
J-20 | passing         | last_passing=goal-mcp-loop-iter-40 | A single daily preflight verdict guards every decision surface
J-21 | passing         | last_passing=goal-mcp-loop-iter-39 | Live data cannot silently diverge from the validated seed
J-22 | passing         | last_passing=goal-mcp-loop-iter-39 | The certifier itself is calibrated (placebo + tripwire audit)
J-23 | passing         | last_passing=goal-mcp-loop-iter-39 | The watchlist discloses its real concentration (correlations, clusters, effective bets)
J-24 | passing         | last_passing=goal-mcp-loop-iter-40 | Every stock shows an honest 'how much can this hurt' risk-budget card
J-25 | unknown         | last_passing=- | Drawdown and dry-spell expectations are visible, phase-conditional, and honest
```

Prior session state:
  Journey history: /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/journey-history.json  <-- update this with new state (full atomic write)
  Evaluator log: /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/evaluator-log.md  <-- append a new entry; do not overwrite (read its tail for the recent entries the dispatch omitted)
  Lessons file: /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/lessons.md  <-- append a brief lesson entry capturing a non-obvious takeaway (1-3 sentences). Skip if nothing surprising happened.
  Assumption ledger: /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/assumptions.md  <-- append an entry when a scoring decision required interpreting an ambiguous goal (step 5b of your instructions). Skip when none.

This iteration in one line: FULL iteration delivering J-25 (backlog B-205) — the phase-conditional drawdown & dry-spell expectations panel on /evidence, the LAST unbuilt Must-have journey (24/25 already passing). Pre-evaluator gates: review PASS_WITH_NOTES, QA PASS (26/26 functional + 189 backend), audit PASS (re-derived every served cell for all 7 claims, zero mismatch), browser-qa PASS (14/14 live via Chrome MCP — the iter-40 Chrome outage has recovered; the 8 required-still-passing journeys re-verified green live), ux-regression UX-REGRESSION-PASS, closure CLOSURE-PASS, coherence COHERENCE-WARN (badge-color advisory only). A new golden replay script runs/goal-session-mcp-loop/journey-scripts/J-25.json was written this iter. If you score J-25 passing, all 25 Must-have journeys are passing — weigh GOAL_ACHIEVED against your deterministic gates (note the recurring FULL-iter deterministic-replay gap, which the iter-40 eval mandated closing in an iter-42 lean closeout).

Apply the TOKEN AND QUESTIONING POLICY from .claude/core.md strictly.

Write your verdict to: /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/iter-41/eval.md

The verdict line MUST appear at the top of /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/iter-41/eval.md and start exactly with:
**Verdict:** GOAL_ACHIEVED
  or **Verdict:** CONTINUE
  or **Verdict:** ESCALATE
  or **Verdict:** REGRESSION
  or **Verdict:** STALLED

Also include a 'Depth Recommendation For Next Iteration:' line: lean or full.

Then update /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/journey-history.json (full atomic write) and append an entry to /home/dennis-chan/Git/trendora/runs/goal-session-mcp-loop/state/evaluator-log.md.
STOP.

Environment note: this pipeline run isolates temp files. Before running tests or any command that writes temporary files, run: export TMPDIR="/tmp/iad.goal-mcp-loop-iter-41.2778307" TMP="/tmp/iad.goal-mcp-loop-iter-41.2778307" TEMP="/tmp/iad.goal-mcp-loop-iter-41.2778307"