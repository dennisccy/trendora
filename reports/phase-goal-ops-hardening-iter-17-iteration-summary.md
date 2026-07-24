# Iteration Summary — goal-ops-hardening-iter-17

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-24
**Iteration:** 17

## In plain words

**What you can do now:** You can browse stock rankings, sector and theme views, backtests, and evidence-backed research. Backfilling any historical date range works with no size cap and gives an honest explanation when there's nothing new to fetch. The app's status stays truthful through startup, a data update, or a crash, and heavy calculations are prepared ahead of time instead of making you wait. On the Backtest page, you can already tell whether the evidence shown is fully current, a clearly labeled still-good earlier version, or genuinely not ready yet.

**What changed this time:** When the most common kind of daily data update happens, the Backtest page now keeps showing yesterday's real numbers with a small "Refreshing" notice — and that notice now tells you exactly which date's numbers you're looking at, not just when they were calculated. If you ever do see the "not yet ready" message (now reserved for a truly brand-new, never-used setup), it no longer confusingly tells you to start something you may have already started.

**What's next:** Next, the team will add better measurement tools to pin down exactly why the Backtest page is occasionally slow during a data update, then either fix it directly or bring a clear choice to the owner about accepting that slower speed.

## Headline

Backtest evidence now survives the single most common ingest shape

## Direction

**Signal:** holding
**Why:** J-06, J-07, and J-08 all stayed `partial` for a third consecutive iteration — this iteration closed the iter-16 audit gap in code (the cross-`asof_key` fallback, 15 green unit tests, and the first-ever live captures of the `not_yet_computed` and corrected `refreshing`-banner states) and fixed a real UI-truthfulness bug (evidence window labels bound to the wrong as-of), but the shared ≤1.5s serving-budget breach (11/68, max 12.655s) that has held these three journeys since iter-11 remains undiagnosed. No journey regressed and none crossed to passing, so this reads as holding steady on real, verified progress rather than stalling — the evaluator explicitly rejected a STALLED verdict because the next step (adding timing instrumentation) is still agent-owned, not purely a human decision.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: none
- Regressions in last 5 iters: iter-13 (anti-goal AG-8 escalation to a ~12-minute availability outage; no journey itself flipped passing→failing)
- Anti-goal violations in last 5 iters: 2 recorded — iter-13 AG-8 (critical, resolved iter-14), iter-17 AG-10 (minor, disclosed and corrected the same iteration)
- Iters with no journey state change: 3 of last 5 (iter-13, iter-15, iter-17; iter-14 added J-07 and iter-16 added J-08 as new partial journeys)

**Latest evaluator reasoning:** "The load-bearing B1 fix is real and I verified it at every reachable level — 15 unit tests (TC-1 cross-boundary, TC-4 tie-break, TC-5 strictly-older SQL, TC-6 historical carve-out) re-run green by three independent gates; AG-3 byte-identity + AG-5 no-lookahead hold; coherence confirms one producer/one resolver. I opened the two first-ever live captures myself (TC-09 not_yet_computed empty state with the reworded no-"run an ingest" copy; TC-07 refreshing banner reading "evidence as of 2026-07-22" over fully-populated numbers) and the auditor's AUDIT-A1 cross-boundary client render (banner + "≤ 2026-07-21" window label + n_runs all bound to the older served as-of — the F1 fix). But no journey crossed to passing: J-06/J-07/J-08 stay partial on the un-remediated ≤1.5s serving-budget breaches (11/68, max 12.655s), which this iteration NARROWED (thermal + single-long-transaction ruled out) but did not PIN (two contention mechanisms indistinguishable — logs/backend.log has zero per-request timestamps), and TC-10 was not re-measured."

## What was done

- Widened `resolved_forward_aggregate_evidence` to search strictly-older `asof_key`s and serve the most recent complete evidence (labeled `refreshing`) instead of falling to `not_yet_computed` when the latest date's warm is still in flight — reserves the empty state for the true fresh-install shape; no-lookahead preserved and SQL-verified.
- Added a new `evidence_asof` field, served identically by `GET /api/backtest` and MCP `query_backtest`, and wired it into `RefreshingEvidenceBanner` so the banner names which date's evidence is on screen.
- Fixed a real UI-truthfulness bug the auditor found (F1): the evidence section's window-size labels were bound to the requested as-of instead of the served one — corrected to use `evidence_asof`.
- Reworded the `not_yet_computed` empty-state copy to drop "run an ingest" phrasing and remove a duplicated sentence; fixed a redundant double-read on the historical serving path.
- Investigated (without modifying) the ingest write pattern behind the ≤1.5s `/backtest` latency breaches — ruled out thermal and single-long-transaction causes, narrowed to two indistinguishable contention mechanisms.
- Added 5 new unit tests and updated 6 existing ones in `test_forward_testing_serving_split.py`; 15/15 green, independently re-run by reviewer, QA, and auditor.
- Captured two first-ever live browser states this session: the `not_yet_computed` empty state on a disposable database, and the corrected `refreshing` banner showing `evidence_asof`; re-verified 3 required-still-passing journeys (J-01, J-03, J-05) via deterministic golden replay, with J-04 carried via a non-disruptive health sanity check.
- Disclosed and corrected a minor operator process lapse: a throwaway backend was briefly relaunched without host-guard resource caps; corrected via the standard launch script, independently re-confirmed by the auditor.

## What's left

- Journey J-06 (Pages load only what they need) stays partial — 11/68 `/backtest` reads still breach the ≤1.5s budget (max 12.655s); root cause narrowed (thermal and single-long-transaction ruled out) but not pinned to one mechanism.
- Journey J-07 (Heavy aggregates never take the service down) stays partial — held by the same shared latency breach as J-06; its own memory/availability guarantee is already resolved.
- Journey J-08 (Backtest evidence serves from storage only) stays partial — held by the same latency budget, not by the evidence fix itself, which is now complete and unit-tested.
- The cross-`asof_key` fallback (this iteration's load-bearing fix) has no live end-to-end browser capture yet — the seed database's latest trading day has no future day to advance into without fabricating data; the fix rests on 15 unit tests plus the auditor's client-side cross-boundary render.
- No per-request timing instrumentation exists yet in `/backtest`'s serving path, so the two remaining latency-contention candidates (SQLite writer/checkpoint contention vs. GIL/threadpool scheduling) cannot be told apart.
- A fresh live J-04 kill/restart replay is still owed before any GOAL_ACHIEVED — this iteration ran only a non-disruptive steady-state health sanity check.
- The `not_yet_computed` empty state has only ever been captured live against a disposable throwaway backend, never the main application most users actually visit.

## Next step

FULL depth, no new features — resolve the latency question holding J-06/J-07/J-08 short of passing. (1) AGENT: add per-request timing instrumentation to the `/backtest` serving path (diagnosis is currently blocked only by missing wall-clock timestamps in the backend log). (2) OPERATOR (heavy-pass class): re-run the deep-basis 68-poll measurement with that instrumentation to distinguish SQLite writer/checkpoint contention from GIL/threadpool scheduling contention. (3) AGENT then OWNER-fork: apply a bounded mitigation if the contention proves fixable (which would let J-06/J-08 pass); otherwise route the ≤1.5s budget-amendment decision to the owner (the iter-15 precedent) — this fork only fires after the agent diagnosis, it is not a blocker now. (4) AGENT, non-blocking: project metadata columns before reading payloads in the widened fallback query, and add one endpoint-level test carrying an older `evidence_asof`. The cross-boundary live capture is explicitly NOT a next-iteration blocker — it is unproducible on this seed's data (an owner-owned data-cycle action). (5) OPERATOR: a fresh live J-04 kill/restart replay is still owed before any GOAL_ACHIEVED.

## Assumptions made

- iter-17 · goal-evaluator — Ambiguity: the definition of done names a live cross-`asof_key` capture as required, but it is unproducible on this seed (no future trading day exists to advance into without fabricating data); the auditor asked whether unit tests plus a client-side render are a sufficient evidence floor. We chose: accepted that floor for the fix's code correctness (15 unit tests + the auditor's client-side cross-boundary render + the same-key live banner); the missing live capture is not treated as a standalone blocker going forward — the journey still stays partial, held instead by the separate latency budget. Reversible: yes
- iter-16 · goal-evaluator — Ambiguity: J-04 rode the browser-QA lane, which skipped it because its steps need a blocked kill/restart; unclear whether to carry it as passing or drop it to unknown. We chose: carried J-04 as passing but deliberately did not advance its last-verified iteration marker — the record shows plainly this iteration produced no fresh evidence for it; a live replay is now a hard precondition for any future GOAL_ACHIEVED. Reversible: yes
- iter-16 · goal-evaluator — Ambiguity: whether the prior iteration's gap (the empty-state fallback resolving only within one as-of, so an ordinary latest-date advance shows the empty state on a store full of complete evidence) is a goal-conformance issue to rule on, or an accepted scoping the iteration itself chose. We chose: ruled the fallback must cross as-of boundaries and kept the target journeys partial rather than accept the iteration's own narrower scoping as sufficient — the empty state was misleading a user who had already started an update. Reversible: yes
- iter-16 · goal-decomposer — Ambiguity: the "never compute on request" wording reads as unqualified (every as-of), but every sibling ingest-time cache carves out historical/non-default views as lazily-computed, and none of the journey's steps describe a historical as-of. We chose: scoped the zero-compute guarantee to the current-latest request only, leaving historical as-of viewing on its existing lazy create-once-and-cache behavior, and said so explicitly in the iteration's own scope sections. Reversible: yes
- iter-15 · goal-evaluator — Ambiguity: with a stacking bug fixed, whether a very slow (~119x over budget) but honest, never-frozen cold-cache response is enough to call the latency journeys passing, or whether they must stay partial pending an owner decision. We chose: did not flip either to passing on its own authority — kept both partial and halted for the owner, since the goal's own success criteria commit to staying within committed budgets and a prior human-ratified precedent already declined to launder a budget breach into a pass. Reversible: yes
- iter-15 · goal-decomposer — Ambiguity: whether a concurrent-load slow-response finding counts as a page-budget violation, an availability-guarantee violation, both, or neither, since the goal text doesn't explicitly require response time under concurrent load in either journey's own wording. We chose: followed the prior iteration's evaluator, who already read it as blocking both journeys, and built this iteration's whole scope on that same reading rather than re-litigating it. Reversible: yes
- iter-14 · goal-evaluator — Ambiguity: a prior iteration's regression was driven by a memory-exhaustion bug; a later test showed the same concurrent-load trigger still produces a slow (211.8s) response, so whether that anti-goal counted as resolved or still open was unclear. We chose: marked it resolved — the new finding is a latency/lock-contention issue (budget territory), not the crash/memory-exhaustion pattern the anti-goal's text forbids, and three independent verifications confirmed the exhaustion defect itself is gone. Reversible: yes
- iter-14 · goal-evaluator — Ambiguity: the literal test for a journey's step 4 (induce memory pressure on the live full-deep-basis process) was not executed because the operator judged it an unjustified hardware hazard on this crash-history host; whether substitute evidence (a real synthetic-subprocess induction plus organic error-absence) is enough was left to the evaluator's judgment. We chose: ruled the two-leg evidence reasonable and did not treat the missing live induction as a hard blocker, while not upgrading it to a literal pass either — the journey stays partial, held there independently by other gaps. Reversible: yes
- iter-14 · goal-decomposer — Ambiguity: a pump note said to write a heavy full-basis warm measurement as "operator-supervised" without specifying whether that means the agent runs the confined measurement itself or the human must literally type the launch command. We chose: wrote the standard path as the developer/reviewer running the confined pass directly via the launch script, with an operator-fallback only if the session's environment blocks the process start. Reversible: yes

## Quick verify

From `reports/phase-goal-ops-hardening-iter-17-what-to-click.md`:

1. Open `http://127.0.0.1:13255/backtest` in your browser — this is the separate throwaway instance, not your main app.
2. On that same card, check that the words "run an ingest" do NOT appear anywhere in the description.
3. Refresh that page (F5).
4. Now open `http://localhost:3255/backtest` — your regular, main app — in a new tab.
5. Scroll to the very bottom of this MAIN page.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-17.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-17-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-17-review.md |
| Browser QA | FAIL | reports/phase-goal-ops-hardening-iter-17-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-17-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-17-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-17-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-17-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-17-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-ops-hardening-iter-17-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-17-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-17-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-ops-hardening-iter-17-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-17/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
