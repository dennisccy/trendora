# Goal Session i_can_see_the_wealthy_future — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-1 — 2026-05-29T17:04:13Z

**Verdict:** CONTINUE
**Lesson:** Two browser-driven steps disagreed: the dedicated browser-qa report said SKIPPED ("frontend
not running") while the QA mode-2 report said PASS with Chrome MCP screenshots. Both were "true" at
different moments — the managed `next dev` server exited mid-run and QA restarted it. Reconcile by
checking the evidence directory on disk (the 3 PNGs were present), not by trusting either verdict alone.
Separately: the spec named **Stooq** as the seed source, but Stooq now gates bulk CSV behind a
captcha/apikey; the dev correctly pivoted to the no-key Yahoo chart API rather than commit a key — a
pivot that *preserves* the No-secrets anti-goal is the right call, not scope drift.
**Applies to:** any iter whose browser-qa and QA both drive a browser (verify the managed frontend is up
and stable before trusting a SKIP/PASS — inspect the evidence dir); any iter that depends on a specific
named external data source (confirm it is still free/no-key before relying on it, and a key-avoiding
pivot is acceptable and must be documented in handoff + meta provenance).
