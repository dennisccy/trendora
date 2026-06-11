# Goal Session i_can_see_the_wealthy_future_forever_with_my_loved_ones — Lessons Learned

Append-only ledger of takeaways from prior iterations. The goal-evaluator
appends one entry per iteration; the goal-decomposer reads this file before
planning each iteration to avoid repeating known pitfalls.

Each entry should be 1-3 sentences capturing a non-obvious lesson — surprising
failures, regression triggers, or decisions that worked well. Avoid
restating the verdict (the evaluator-log.md already does that).

## iter-0 — 2026-06-11T08:41:43+01:00

**Verdict:** CONTINUE
**Lesson:** The browser-qa agent invented its own journey list instead of reading docs/goal.md — ~20 IDs got fabricated descriptions (J-22/23/24 graded as "broker/orders/portfolio", J-14 as "Research page") and some evidence was recycled byte-identical or misfiled (UT-J-17-data-manager.png is actually the Research Factor Lab; the real Data Manager/VCP captures landed in stray reports/qa/goal-iter-0-evidence/). The raw screenshots were mostly genuine and sufficient, but every verdict had to be re-derived from them + the dev source-scan; J-42's PASS was an overclaim (only the displayed-dates leg was checked — /data still has native type="date" inputs).
**Applies to:** every future browser-qa dispatch (pass the goal.md journey text verbatim into the QA prompt; evaluator must md5-spot-check evidence and grade against goal.md acceptance, never the QA table) and any iter touching J-42 (acceptance includes validated ISO text inputs + one shared formatter, not just ISO-looking output). Also: the full pytest suite (~14 min) was skipped at baseline (collect-only) — iter-1's gate must run it once.
