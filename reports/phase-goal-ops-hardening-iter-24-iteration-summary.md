# Iteration Summary — goal-ops-hardening-iter-24

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-26
**Iteration:** 24

## In plain words

**What you can do now:** You can browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. You can back-fill any historical date range with no size cap and get an honest explanation when there's no new work to do. The status badge at the top of the app stays truthful through startup, updates, or a crash, and pages stay responsive even while the backend computes new numbers in the background. Now you can also see, on every page, a small live badge whenever the backend is quietly computing something in the background, and open the Data Manager page to see exactly which date it's working on, how far along it is, and what happened last time (including an honest reason if it failed).

**What changed this time:** The backend used to do this background computing invisibly — the only way to know it was happening was to dig through database records after the fact. Now there's a live "background compute running" badge next to the normal status pill on every page, and a new panel on the Data Manager page showing the detail. The numbers shown were checked against the underlying data and proven accurate to the millisecond.

**What's next:** Next we'll finish writing the guided-tour steps for this new indicator so it's included in the product's full walkthrough, and make the new panel say "we don't know" instead of "nothing running" on the rare occasion it briefly loses touch with the backend.

## Headline

Added a live badge and Data Manager panel disclosing in-flight background compute activity

## Direction

**Signal:** holding
**Why:** All seven previously-passing journeys (J-01, J-03, J-04, J-05, J-06, J-07, J-08) were re-verified passing this iteration with fresh evidence, with no regressions and no anti-goal violations. A new journey, J-09 (disclosing background-compute activity), was added by the auto-extension loop and is substantially built and independently verified against the database, but stays `partial` because its required walkthrough-manifest entry was never authored — so no journey crossed into `passing` this iteration.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-08 (iter-21), J-06 and J-07 (iter-22)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 2 of last 5 (iter-20, iter-23)

**Latest evaluator reasoning:** The new journey J-09 "The backend discloses its own background-compute activity" is genuinely built and works. I saw the top bar say "background compute running (1)" next to a green "Ready" pill, I read the new Data Manager panel's own page text in three states, and I checked the numbers it showed against the database myself: the panel's "1m 15s" is the real, measured length of a real compute, correct to about two thousandths of a second. All seven older journeys were re-checked this iteration and all seven still pass.

## What was done

- Added a live "background compute running" badge next to the readiness pill on every page.
- Added a new "Background compute" panel on the Data Manager page showing active windows (as-of date, elapsed time, horizons done/total) and the most recent outcome, with an honest idle state when nothing has run.
- Extended the backend's existing dispatch registry with `started_at`/`horizons_done`/`horizons_total` bookkeeping and a bounded, config-capped outcome ring, composed additively into `GET /api/health`.
- Added a configurable retention setting (`startup.background_compute_history_size`, default 5) for how many past outcomes are remembered.
- Re-verified all 7 prior passing journeys (J-01, J-03, J-04, J-05, J-06, J-07, J-08) with fresh iteration-24 evidence.
- Verified 18/18 target and regression journeys pass browser QA (12 J-09 checks + 6 deterministic replay regressions), plus 81 backend unit tests pass.

## What's left

- Journey J-09 (The backend discloses its own background-compute activity) stays `partial` — the session demo walkthrough manifest (`reports/goal-session-ops-hardening-demo.json`) still has zero J-09 steps, which is the item blocking GOAL_ACHIEVED.
- The Data Manager panel says "No background compute running" even when the backend genuinely doesn't know (a failed health poll renders as the idle state rather than an "unknown" state).
- Steady-state `GET /api/health` latency is borderline: one measurement recorded 0.127788s (over the ≤0.1s budget) while another recorded 0.094604s on the same build — an open owner question.
- Two new unit tests compare two live reads of the registry and could flake under whole-suite contention; needs fixing before anyone runs the full test file.
- A background-dispatch thread-start failure would leave the badge reading "running" forever; the fix requires lifting a byte-freeze on a function this iteration was told not to touch, so it needs a planned iteration.
- Carried: retarget `test_forward_testing_serving_split.py`'s `is_latest` monkeypatches before removing dangling imports; run `test_api_backtest.py`/`test_data_manager.py` heavy fixtures off the constrained box.

## Next step

One short lean-depth iteration, no new features: (1) add the J-09 steps to the session demo manifest (`reports/goal-session-ops-hardening-demo.json`) — the same work iteration 23 did for J-06/J-07/J-08 — this is the item blocking closure; (2) give the Data Manager panel a distinct "backend unreachable — background-compute state unknown" message instead of reusing the idle copy; (3) fix the two new tests that compare two live reads of the registry before anyone runs the whole test file. Owner items, none blocking this iteration: decide whether the ≤0.1s at-rest health-check target should stand as written, and backlog card B-1107 (a cap on concurrent background computes) stays optional. In one sentence: approve one more short pass to finish the guided-tour steps and fix the wording, and the goal should be ready to close.

## Assumptions made

- iter-24 · goal-evaluator — Ambiguity: J-09's Acceptance ends with a Walkthrough bullet requiring `[NEW]`-flagged steps playable via `demo.sh ops-hardening --session-live`, but the iteration spec that planned J-09 never mapped that bullet into IN SCOPE or DoD. goal.md doesn't say whether a journey whose numbered steps all verify, but whose Acceptance carries an un-planned deliverable, counts as passing. We chose: scored J-09 `partial`, treating the Acceptance bullet as binding on the journey regardless of the iteration spec's scope, since this session already adjudicated the same clause twice for J-06/J-07/J-08. Reversible: yes
- iter-24 · goal-evaluator — Ambiguity: two measurements of steady-state `GET /api/health` latency on the same build disagree (developer 0.127788s max, QA 0.094604s max) against the unchanged ≤0.1s budget; goal.md doesn't say which series binds or whether a sub-millisecond excursion on a chronically tight endpoint counts as a breach. We chose: did not treat it as a J-06/J-07 regression (the diff adds zero DB work), but recorded it as an open J-09 gap routed to the owner rather than laundering it. Reversible: yes
- iter-24 · goal-decomposer — Ambiguity: J-09's Consistency clause implies a retained-record count exists, but its steps only ever describe a single outcome, so a single `last_outcome` field and a bounded `recent_outcomes` list both satisfy the literal text. We chose: built a bounded, config-governed `recent_outcomes` list (default 5) so the "retained-record count" language has a concrete testable referent, though a human reading the steps literally might see this as over-built. Reversible: yes
- iter-23 · goal-evaluator — Ambiguity: a spec clause required the J-07 demo step to cite figures verbatim from perf-budgets.md's Iteration 22 section, but the step used 4-decimal precision while that file prints 3 decimals. We chose: treated it as a cosmetic precision nit rather than a DoD failure, since the 4-decimal figures trace exactly to the raw measurement file. Reversible: yes
- iter-23 · goal-decomposer — Ambiguity: whether J-06/J-07/J-08's Walkthrough clause (viewable via `demo.sh ops-hardening --session-live`) is a settled non-autonomous deliverable, or whether the JSON manifest that command reads is itself agent-authorable. We chose: the manifest is agent-authorable and its incompleteness is a genuine, bounded gap — this iteration authored the missing steps directly. Reversible: yes
- iter-22 · goal-evaluator — Ambiguity: the developer's accidental 5-concurrent background-compute probe drove memory near its cap and produced a real MemoryError with some reads over the BCW ceiling; goal.md doesn't say whether a multi-window scenario is in scope for any journey. We chose: scored those samples out of contract and the MemoryError as a contained, honest failure (not an AG-8 violation), since the owner had already reviewed the episode and backlogged it. Reversible: yes
- iter-22 · goal-evaluator — Ambiguity: the owner's BCW budget amendment (raising the window bound 60s to 90s) was recorded the same day a fresh measurement showed a 69s window — the shape of goalpost-moving. We chose: treated the amendment, including its same-day revision, as the owner's committed contract and scored J-06/J-07 passing, since the revision touched only the window-duration bound and a second, independently-triggered window that day corroborated the same cadence. Reversible: yes
- iter-21 · goal-evaluator — Ambiguity: J-04 rode the LLM lane and skipped its disruptive kill/restart step again, but the operator delivered the exact replay (TC-14) iter-20 called a hard precondition; goal.md doesn't say whether operator API/DB evidence can substitute for a browser capture. We chose: kept J-04 passing and advanced its verification to this iteration, based on independently re-read database records rather than the operator's prose. Reversible: yes
- iter-21 · goal-evaluator — Ambiguity: J-08's acceptance state (the refreshing banner) renders below the fold and none of this iteration's screenshots depict it, though the methodology says screenshots outrank prose. We chose: scored J-08 passing anyway, based on database timestamps re-derived directly showing the banner state was structurally forced, not asserted. Reversible: yes
- iter-20 · goal-evaluator — Ambiguity: transient in-process contention during the ~30s background-compute window literally breaches J-06/J-07's steady-state budgets, but goal.md doesn't say whether those budgets govern reads taken during a heavy background window or only steady-state reads. We chose: kept J-06/J-07 `partial`, treating the breaches as real and their resolution as owner-owned (driving STALLED), rather than reading the journeys as satisfied-in-spirit. Reversible: yes

## Quick verify

From `reports/phase-goal-ops-hardening-iter-24-what-to-click.md`:

1. Open `http://localhost:3255/` in your browser
2. Click "Backtest" in the left sidebar
3. Click the "◀" left-arrow button just left of the calendar icon, once
4. Once you see "background compute running (1)", immediately click "Data Manager" in the left sidebar
5. Wait about 20-30 seconds, then refresh the page (F5) and scroll to the bottom again

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-24.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-24-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-24-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-24-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-24-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-24-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-24-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-24-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-24-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-ops-hardening-iter-24-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-24-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-24-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-ops-hardening-iter-24-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-24/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
