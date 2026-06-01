# Goal Session i_can_see_the_wealthy_future_forever — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-06-01T01:00:00Z

**Verdict:** CONTINUE
**Lesson:** When the Chrome-MCP tool layer is degraded, browser-QA's *negative* interaction findings are unreliable: this run QA marked J-18 PARTIAL claiming "no separate date dropdown" on `/backtest`, but `apps/frontend/app/backtest/page.tsx:53-58,112-208` clearly carries a page-local `BacktestDatePicker` with its own date state (and the evidence screenshot shows the dropdown) — a genuine "exactly one date selector" violation. Always confirm date-control / single-source-of-truth claims against frontend source, not just the browser-QA summary.
**Applies to:** any iter verifying J-13/J-18 or the "exactly one date selector" / single-source-of-truth anti-goals; any iter touching `apps/frontend/app/backtest/` or `components/asof-*`.

