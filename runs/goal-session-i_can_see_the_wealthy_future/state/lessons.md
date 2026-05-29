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

## iter-2 — 2026-05-29T19:10:15Z

**Verdict:** CONTINUE
**Lesson:** The coherence-auditor caught a *future*-duplicate risk that is invisible today: iter-2 computes
market breadth once in `app.engine.regime:score_regime` and serves it from the canonical `/api/dashboard`
(single source, no violation now), but the blueprint Data Contract registers "market breadth %" under
`app.engine.scanner:summarize_run` — which does not exist until iter-5. If iter-5 builds `summarize_run` to
recompute breadth from setup statuses, it silently creates the exact two-sources-for-one-number the
single-source gate forbids. A WARN about an unbuilt module is a real liability, not noise — reconcile the
contract attribution *before* the second module lands. (Also: the `next dev`/QA browser-qa SKIP-vs-PASS flap
recurred a 2nd time — the iter-1 lesson still applies; consider hardening frontend supervision.)
**Applies to:** any iter that builds `app.engine.scanner` / `summarize_run` or otherwise touches breadth,
new-high/low, or any value the blueprint attributes to a not-yet-built module — make the new module *read*
the existing canonical source, never recompute; and any iter relying on browser evidence (verify the
managed frontend is up and inspect the evidence dir, do not trust a lone SKIP/PASS).

## iter-3 — 2026-05-29T21:48:48Z

**Verdict:** CONTINUE
**Lesson:** The browser-qa SKIP-vs-PASS flap recurred a **3rd** consecutive time — and this time the iter-3
spec had *explicitly instructed the orchestrator to harden `next dev` supervision*, yet the dedicated
browser-qa still probed a dead frontend (HTTP 000) and SKIPPED all 23 cases while QA mode-2 independently
started its own `next dev`, ran the 5 browser cases, and saved 9 PNGs. A spec-level note to "keep the server
up" demonstrably does NOT fix this; the fix must be structural — the dedicated browser-qa agent should
*ensure/own* its frontend (start it if down, like QA mode-2 does) rather than precondition-skip, or the two
browser steps should share one managed server. Until then, evidence lives only in QA's PNGs, so always
reconcile from the on-disk evidence dir. (Also recurring: the **audit handoff was again not produced** at
full depth — 2nd time, iter-2 + iter-3.)
**Applies to:** the browser-qa-agent / orchestrator harness itself (make browser-qa self-heal its frontend
instead of SKIP-on-down); any future iter verified through the browser — trust the PNGs on disk, not a lone
verdict; and the full-depth pipeline (confirm the audit handoff is actually emitted).
