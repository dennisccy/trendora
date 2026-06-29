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
