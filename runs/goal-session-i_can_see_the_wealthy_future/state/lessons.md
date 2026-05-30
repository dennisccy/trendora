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

## iter-4 — 2026-05-30T03:30:00Z

**Verdict:** CONTINUE
**Lesson:** Two compounding traps. (1) The browser-qa SKIP/PASS flap recurred a **4th** time (dedicated
browser-qa SKIPPED on HTTP 000), but QA mode-2 self-healed and **persisted** TC-10/TC-11 to the evidence
dir, so reconciling J-05 from the on-disk PNGs worked and J-05 passed — the iters-1–3 standing lesson held.
(2) The *real* surprise was an evaluator-side trap: during a transient tool-output outage the Read of those
two PNGs spuriously returned **"files do not exist"**, which nearly drove a wrong `partial` cap on a journey
whose evidence was actually present (the calls were being *queued*, not failed, and flushed later showing the
files + the populated chart). Lesson: under a flaky/queuing harness a **negative existence result is not
trustworthy** — re-confirm with `ls`/Glob/re-read before letting "missing evidence" lower a verdict; and a
Write that returns no confirmation may still have landed (don't blind-retry appends; an overwrite Write can
also be rejected with "file modified since read" if another queued op touched the file first). Also: don't
let the demo-narrator's Playwright soft-notes ("text not found", click timeouts) override the QA evidence —
they are capture-timing artifacts of the non-gating showcase runner. (Audit handoff now missing **4**
full-depth iters running.)
**Applies to:** the goal-evaluator's own process on any flaky-tool run (re-verify negative file-existence
before acting; verify writes landed without double-appending); any canvas/chart-rendered journey
(Lightweight-Charts) — trust the QA evidence PNG over demo soft-notes; and the full-depth pipeline
(browser-qa must own/self-heal its frontend; the audit step must emit its handoff).

## iter-5 — 2026-05-30T05:30:00Z

**Verdict:** CONTINUE
**Lesson:** Spec-text cannot fix runner-level behaviour, and now we have two proofs: iter-3 escalated
the browser-qa self-heal ask to a spec NOTE (failed → flap recurred 4th/5th time), and iter-5 escalated
the audit-handoff ask all the way to the spec's **Definition of Done** (still failed → `reports/audits/`
does not even exist after 5 full-depth iters). When a missing artifact is produced by a pipeline *step*
(audit) or a precondition the *runner* controls (the dedicated browser-qa's frontend), the only durable
fix is editing `scripts/automation/*.sh` — stop re-asking via the iteration spec/DoD, it has demonstrably
no effect. Practical consequence: the evaluator must keep reconciling target journeys from on-disk
evidence PNGs + unit/API proofs + direct source reads, never from a lone browser-qa SKIP verdict.
**Applies to:** every future goal-mode iteration's evaluation while the audit-handoff / browser-qa-self-heal
harness gaps remain unfixed; and any decomposer tempted to fix a harness/runner gap by adding spec or
DoD text instead of a runner-script change.

## iter-6 — 2026-05-30T05:45:00Z

**Verdict:** CONTINUE
**Lesson:** Distinct journey-named evidence PNGs are NOT guaranteed to be distinct captures: this iter
`TC-14-system-health-j09.png` and `TC-16-control-group-j10.png` were byte-identical (same md5) — one
full-page `/system-health` screenshot saved under two journey labels. When a target journey (J-10) is a
sub-panel of a larger page already captured for another journey (J-09), QA tends to reuse the full-page
shot. So `md5sum`/diff the evidence files before treating a per-journey screenshot count as independent
visual proof, and confirm the specific panel is actually present in the shared image (it was, here). The
evidence was sufficient, but the count overstated distinctness.
**Applies to:** any iter whose target journeys are multiple panels of ONE page (e.g. system-health
J-09+J-10, or a future combined dashboard); and any evaluator weighing "N screenshots = N journeys
proven" — hash them first. A decomposer/QA spec can pre-empt this by asking for a focused/cropped capture
per sub-panel journey.
