# Goal Session mcp-loop — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-06-29T20:53:00Z

**Verdict:** ESCALATE
**Lesson:** The lean pipeline silently produced NO browser-QA evidence this iteration — telemetry.jsonl had no `browser-qa-agent` record (the sequence jumped reviewer → goal-evaluator), status.json stayed at `current_step: dev_complete` / `browser_checks_run: false`, and neither `reports/phase-<iter>-ui-test-results.md` nor the expected SKIPPED stub (goal-iter-lean.sh:392) was written. Do not infer journey pass/fail from the developer's static code scan; confirm the browser-qa-agent actually ran before scoring, and seed journeys as `unknown` (not `failing`) when it did not.
**Applies to:** any lean iteration / any baseline iter-0 — the evaluator should verify a `browser-qa-agent` telemetry record + a non-empty evidence dir BEFORE recording journey verdicts; a missing ui-test-results file should drive ESCALATE (force full), per goal-iter-lean.sh's own design intent (lines 185, 396).

## iter-1 — 2026-06-29T22:37:16Z

**Verdict:** CONTINUE
**Lesson:** The read-side "Proven" path is built but cannot light up yet: the real ledger writer `app.mcp.tools.verify_edge` appends a cohort-selector `claim` with NO `signal` key, while the read side keys `proven_signals` on `claim.get("signal")` (fail-safe). So even a genuine referee PASS would map to NO UI signal and stay "Not yet proven" — the first certified iteration MUST stamp the canonical signal key (`leadership_score`/`entry_quality_score`/`risk_score`) on the written claim, or J-01/J-02's Proven badge will silently never appear despite a passing ledger entry. (Also: against an empty ledger, J-05 steps 2-3 — populated claim row + claim->surface linkback — are structurally un-exercisable, so J-05 caps at `partial` until ≥1 claim is certified; don't score it `passing` on the empty-state surface alone.)
**Applies to:** the first certified iteration and any iter proposing a `## Evidence Claim` / touching `app.mcp.tools.verify_edge`, `app.engine.evidence`, or the `/evidence` page — verify the writer stamps `claim.signal` and that a PASS actually flips a badge end-to-end (browser-verified), not just that the ledger row exists.
