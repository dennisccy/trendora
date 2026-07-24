# Iteration Summary — goal-ops-hardening-iter-19

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-24
**Iteration:** 19

## In plain words

**What you can do now:** You can browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. You can back-fill any historical date range with no size cap and get an honest explanation when there's nothing new to do. The status bar always tells the truth about whether the app is starting up, running normally, or has crashed. Heavy calculations are done in advance, not while you wait, and the Backtest page tells you plainly whether the numbers you're seeing are fresh, a labeled "still good" older version, or not ready yet.

**What changed this time:** The Backtest page (and the tool a connected assistant uses to read it) used to slow down — sometimes by more than a second — when several people loaded it at the same time, because it was quietly redoing pointless calculations on every single visit. That's now fixed: the same page loads about ten times faster under heavy traffic, with every number staying exactly the same as before. One related slow spot remains: the very first time anyone views an older, not-yet-seen date on the Backtest page, it can still take up to about a minute to appear — a separate issue the team has now pinpointed and plans to fix next.

**What's next:** Next, the team will add a visible "still loading" message for that one remaining slow first-time view, and work on moving its calculation off the page entirely so it never makes anyone wait.

## Headline

Root-caused & fixed the /backtest latency blocker (63x faster); J-06/J-07/J-08 remain partial

## Direction

**Signal:** stalling
**Why:** J-06/J-07/J-08 have sat at `partial` for four consecutive iterations (16-19) even though iter-19 root-caused and eliminated the primary latency blocker that has held this cluster since iter-11 (`backfill_forward_returns_ms` 877ms→13.9ms, 63x, all 8 gates PASS). No journey crossed because two gaps remain: a separate `ensure_loop_ms` cold-recompute stall on historical `/backtest` views (9.6-54s, no loading affordance), and the TC-7 concurrent-ingest budget re-measurement, still blocked by the AG-10 safety classifier. The evaluator explicitly rejected STALLED here (unlike iter-15) because the next step is agent-tractable rather than owner-gated — so this is a categorical plateau with real underlying momentum, not an absence of it.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: none
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 1 (minor — AG-10 operator process lapse, iter-17, disclosed and corrected the same iteration; 0 unresolved/critical)
- Iters with no journey state change: 4 of last 5 (iter-16 introduced J-08 as a new `partial` journey; iters 15, 17, 18, 19 show no status-category change)

**Latest evaluator reasoning:** The iter-19 fix is real and I verified it independently: the un-elapsed-horizon short-circuit in `backfill_run_forward_returns` collapses the request-path forward-returns phase from 877 ms to a personally re-tallied 13.9 ms mean / 73 ms max under 6× concurrency (TC-6 CSV: 4793 requests, 0 non-200, 0 breaches, mean 112 ms, max 302 ms) with byte-identity preserved three ways — closing the create-once-INSERT contention that held J-06/J-07/J-08 partial since iter-11. But it does not close those three journeys: (a) browser-QA UT-04, which I opened, shows a separate cold-recompute subsystem (`ensure_loop_ms`) still stalls the FIRST `/backtest` view of a historical as-of on an empty, no-affordance skeleton for 9.6–54 s — literally "a skeleton waiting on a fresh compute" (J-08 step 2); and (b) TC-7, the concurrent-ingest overlay that is the actual historical breach condition (11/68 @ 12.655 s), was never measured (AG-10 ingest-trigger blocked), so the ≤1.5 s budget is proven only under pure reads. Progress made, no regression, no anti-goal violated, coherence PASS, and the next blocker is agent-tractable → CONTINUE.

## What was done

- Root-caused and eliminated the `/backtest` + MCP `query_backtest` request-path latency bottleneck after 3 dev+review attempts, each corrected by a live re-measurement (skip-commit → column-projection → the real fix: an un-elapsed-horizon short-circuit ahead of the per-symbol price-fetch loop).
- Collapsed the measured `backfill_forward_returns_ms` phase from 877–881ms to 13.9ms mean / 73.4ms max under 6× concurrency (63×); client-observed load time dropped from 1083ms to 112ms mean (302ms max) across 4,793 requests, 0 breaches — DoD PASS.
- Preserved byte-identical served payloads throughout (scorecard + all `evidence_*` fields), proven by construction, unit tests, and a live before/after capture (AG-3 held).
- Added/extended concurrency and unit tests (TC-1 through TC-5 plus 3 new short-circuit tests); 57/57 scoped backend tests pass, independently rerun by reviewer, QA, and audit.
- Extended the existing timing log with a `write_taken` diagnostic field (operator log only, never served to users).
- Passed all 8 pipeline gates: review PASS, QA PASS, browser-QA PASS (9/10, 1 legitimately skipped), UX-regression PASS, audit PASS_WITH_GAPS, closure CLOSURE-PASS, coherence COHERENCE-PASS, goal-eval CONTINUE.
- Verified 0 target journeys (J-06/J-07/J-08) cross to passing via browser QA this iteration (9/10 individual test cases PASS, 1 SKIPPED); required-still-passing J-01/J-03/J-05 reconfirmed via golden replay, J-04 carried via a non-disruptive health check.
- Documented, but deliberately did not fix, two pre-existing hazards for future triage: an autoflush `IntegrityError` race inside `_insert_run_forward_returns`, and a boot-time echo of the same wasted-lookup pattern.

## What's left

- Journey J-06 (Pages load only what they need) — partial: held by the `ensure_loop_ms` cold-first-view stall (9.6–54s, no loading affordance) on historical `/backtest` views, plus an unmeasured ingest-window budget (TC-7).
- Journey J-07 (Heavy aggregates never take the service down) — partial: core memory/availability guarantee holds, but serve-responsiveness under a concurrent ingest window (TC-7) is unmeasured.
- Journey J-08 (Backtest evidence serves from storage only — never a cold recompute on request) — partial: the forward-aggregate serving clause is met, but a separate cold recompute (`ensure_loop_ms`) still stalls the first view of a historical as-of.
- TC-7 (concurrent-ingest overlay re-measurement) — the actual historical breach condition (11/68 @ 12.655s baseline) remains unmeasured; blocked this session by the AG-10 ingest-trigger safety classifier.
- A disruptive J-04 kill/restart replay is owed since iter-15 — a hard precondition for any future GOAL_ACHIEVED; owner/operator-gated.
- A pre-existing autoflush `IntegrityError`/`OperationalError` hazard inside `_insert_run_forward_returns` remains unfixed — deferred as its own follow-up with its own concurrency-test budget.
- Four regression-adjacent test files (`test_forward_testing.py`, `test_warmup.py`, `test_data_manager.py`, `test_api_backtest.py`) were not run this session (host-guard time-budget limits) — the DoD's "all pre-existing tests keep passing" bullet is not fully evidence-closed.
- A boot-time echo of the same wasted-lookup pattern (the once-per-startup walk-forward backfill) is unaddressed — a one-time startup cost, flagged for future consolidation.

## Next step

FULL depth, no new features. (1) AGENT: fix the `ensure_loop_ms` cold-first-view stall on `/backtest` (audit F1) — add an honest progress/initializing affordance so it is never a blank/frozen skeleton, and take the cold historical `ensure_loop` scan off the request path (the same compute-at-ingest/serve-from-storage pattern already applied to the forward path); this touches the frontend and serving path, so full depth is warranted. (2) OWNER-gated: re-measure TC-7 (the concurrent-ingest overlay) to prove the ≤1.5s budget holds under the actual historical breach condition, not just pure reads. (3) OWNER-gated: the disruptive J-04 kill/restart replay, owed since iter-15 and a hard precondition for any future GOAL_ACHIEVED. (4) AGENT non-blocking: the pre-existing autoflush IntegrityError hazard, the boot-time un-elapsed-horizon fetches, and running the 4 skipped regression test files off the constrained box.

## Assumptions made

- iter-19 · goal-evaluator — Ambiguity: J-08 reads broadly ("never a cold recompute on request"), but the iter-16 decomposer scoped that guarantee to `is_latest==true` requests, arguably sanctioning the historical-path `ensure_loop_ms` cold compute UT-04 found. We chose: kept J-08 `partial` anyway — the shared honest-status clause ("never a frozen or blank frame") is independently failed by the no-affordance empty skeleton, regardless of the `is_latest` carve-out. Reversible: yes
- iter-18 · goal-evaluator — Ambiguity: J-04 (required-still-passing) has no golden script and rode the LLM browser-qa lane, which SKIPPED because Chrome MCP is wedged and no `browser-infra.json` token exists to mechanically trigger the pending-infra carve-out. We chose: carried J-04 `passing` (last_verified left at iter-15), not `partial`+pending_infra or `unknown` — basis: code surface untouched, a live pass exists at iter-14, same precedent as iter-16/17. Reversible: yes
- iter-17 · goal-evaluator — Ambiguity: TC-8 (a live cross-`asof_key` refreshing capture) is unproducible on the committed seed (no ingest can advance without fabricating data), so is the unit-test + client-render evidence floor sufficient for the B1 fix's code correctness? We chose: accepted that floor as sufficient for B1; TC-8's missing live capture is not treated as a standalone blocker going forward (J-08 stays `partial` for a separate, unrelated budget reason). Reversible: yes
- iter-16 · goal-evaluator — Ambiguity: J-04 rode the LLM browser-qa lane, which SKIPPED it (kill/restart blocked this session) — does the "no fresh evidence, no fresh pass" screenshot rail or the "unchanged journeys carry over" rule govern? We chose: carried J-04 `passing` without advancing `last_verified_iter` (left at iter-15) — basis: iter-13 precedent, a live pass at iter-14, code surface confirmed untouched. Reversible: yes
- iter-16 · goal-evaluator — Ambiguity: does J-08's "last complete stored version" fallback need to cross `asof_key` boundaries, or is the iteration's own spec'd per-`asof_key` scoping (TC-6) sufficient, given goal.md never says explicitly? We chose: ruled it MUST cross boundaries and kept J-08 (with J-06/J-07) `partial` rather than accept the narrower spec scoping as goal-conformant. Reversible: yes
- iter-16 · goal-decomposer — Ambiguity: J-08 step 4 reads literally as "zero aggregate compute on ANY request," but every sibling cache in this session carves out non-default/historical parameterization, and reading it fully literally would regress the pre-existing historical time-machine view. We chose: scoped the "never compute on request" guarantee to `is_latest==true` requests only; historical views keep their existing lazy create-once-cache behavior, explicitly flagged IN/OUT OF SCOPE. Reversible: yes
- iter-15 · goal-evaluator — Ambiguity: with the stacking pathology fixed, does the residual 178.74s cold-MISS (honest skeleton, fast warm path) satisfy J-06/J-07's serve-responsiveness clause, or does it stay `partial` pending an owner decision? We chose: did NOT flip to passing on its own authority — kept both `partial` and returned STALLED to route the budget-acceptance decision to the owner (a 119x breach is a real recorded violation; iter-12 precedent). Reversible: yes
- iter-15 · goal-decomposer — Ambiguity: does J-06/J-07's acceptance require `/backtest`'s own response time to stay in budget during a concurrent warm+serve scenario, or is that outside either journey's literal step text? We chose: followed iter-14's evaluator reading (which already scored both `partial` on this basis) rather than re-litigating it — this iteration's whole scope builds on that reading. Reversible: yes
- iter-14 · goal-evaluator — Ambiguity: does AG-8 (memory-exhaustion/crash resilience) count as resolved if UT-04 shows the same concurrent-load trigger still produces a 211.8s anomaly, or does that keep AG-8 open? We chose: marked AG-8 RESOLVED — UT-04 is a latency/lock-contention issue, not the crash/memory-exhaustion/unbounded-ORM-load AG-8's text actually forbids — and kept J-06/J-07 `partial` on that finding instead. Reversible: yes
- iter-14 · goal-evaluator — Ambiguity: TC-6's literal memory-pressure induction on the live full-deep-basis process was not executed (operator judged it an AG-10 hardware hazard on this crash-history host) — is TC-3's synthetic-subprocess induction plus TC-5's organic MemoryError-absence enough for J-07 step 4? We chose: ruled the two-leg evidence reasonable without upgrading it to a literal pass — J-07 stays `partial`, held there independently by other findings. Reversible: yes

## Quick verify

From `reports/phase-goal-ops-hardening-iter-19-what-to-click.md`:

1. Open `http://localhost:3255/backtest` in your browser.
2. Scroll down to the "Forward-test scorecard" section.
3. Keep scrolling to the "Leadership cohorts" section.
4. Scroll to the very bottom of the page.
5. Reload the page (press F5) and pay attention to how quickly it comes back.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-19.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-19-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-19-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-19-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-19-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-19-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-19-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-19-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-19-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-ops-hardening-iter-19-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-19-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-19-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-ops-hardening-iter-19-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-19/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
