# Iteration Summary — goal-ops-hardening-iter-35

**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-07-30
**Iteration:** 35

## In plain words

**What you can do now:** Browse stock rankings, sector and theme pages, backtests, and research tools including Factor Lab and Regime Lab. Back-fill any historical date range, with an honest explanation whenever there's nothing new to fetch. The status badge at the top of every page stays truthful through startup, updates, and even a crash, heavy calculations are ready ahead of time, and the Backtest page always shows saved results instantly, never a live recalculation. The app also tells you plainly whenever background number-crunching is happening.

**What changed this time:** Behind-the-scenes work — no code changed this round, but the team took a hard look at the app under real heavy load and found two problems worth fixing. Four research pages (Market Phase & Severity, Regime × Phase & Factor, Factor Lab, and Severity-Velocity) can sit on a blank, unlabelled loading screen with no message while they're still working, instead of the honest "still computing" notice Regime Lab already shows. And during a busy background job, the app's memory use climbed all the way to its safety limit with zero room to spare — it did not crash and kept answering every request, but it came right up to the edge.

**What's next:** Next, the team plans to actually build the plan that was already written for this round: stop the app from loading its entire price history into memory during background housekeeping, and add the honest "still loading" message to the four research pages that currently go blank.

## Headline

Evidence-only iteration: no code changes were planned or made.

## Direction

**Signal:** holding
**Why:** This round built nothing — it was run at a lighter "capture evidence" depth against a spec that needed real code — but the evidence it gathered proved two problems for real: J-06 ("Pages load only what they need") and J-07 ("Heavy aggregates never take the service down") both slipped from passing to partial, the first because four sibling research labs render a blank unlabelled screen under a genuine slow load, the second because a heavy background job pushed memory use to exactly the declared cap with zero margin. Neither is a code regression — the product tree is byte-identical to iteration 34, and the evaluator explicitly rejected classifying either drop as a REGRESSION or the memory issue as a critical anti-goal violation — so the signal is coded "holding" rather than "regressing," but this is a real step back from all-8-passing that needs closing before any goal-achieved attempt.

**Trend (last 3 iters):**
- Newly passing this iter: none
- Newly passing in last 3 iters total: J-06 (iter-33, "Pages load only what they need"), J-07 (iter-34, "Heavy aggregates never take the service down") — both since dropped back to partial at iter-35
- Regressions in last 3 iters: none by the evaluator's own classification (no journey crossed passing→failing and no critical anti-goal violation fired); note that J-06 and J-07 did drop from passing to partial at iter-35 and are tracked above, not here
- Anti-goal violations in last 3 iters: 5 new findings, all minor (iter-33/g, iter-33/h, iter-33/i, iter-34/j, iter-35/k); zero critical
- Iters with no journey state change: 0 of last 3

**Latest evaluator reasoning:** "This iteration built nothing. The planner wrote a full work plan (bound the price load that eats memory; add the honest 'still computing' panel to four Research lab pages), but the engine ran the iteration in evidence mode, so no developer and no reviewer were ever started. The dev note says it plainly: 'no code changes were planned or made.' I checked the code myself and it is byte-for-byte the same as after iteration 34."

## What was done

- No product change this iteration. (`git diff 8233429b..HEAD -- apps scripts project-extensions config` is empty; `git status --porcelain` over the same paths is empty.)
- Ran at "evidence" depth despite the iter-35 spec's own metadata calling for full-depth code work — only the decomposer and browser-qa steps ran; no developer, reviewer, QA, audit, ux-regression, or closure lane.
- Captured fresh browser evidence of J-06 (all 4 sibling research labs) and J-07 (a live heavy background-compute window) rather than re-testing already-proven behavior.
- Found and documented two real, previously-unproven problems: a bare unlabelled blank skeleton on all 4 sibling research lab pages during a genuine slow load, and memory use peaking exactly at the declared cap (6,291,456 kB, zero margin) with 4 memory-pressure aborts (2 background, 2 on the user-facing `/api/evidence` path — both self-healing, both showing an honest "unavailable" marker rather than a wrong number).
- Re-verified J-01, J-03, J-04, J-05, J-08, J-09 via deterministic golden replay — 6/6 PASS, zero FAIL rows, zero reconciliation overturns.
- Downgraded J-06 ("Pages load only what they need") and J-07 ("Heavy aggregates never take the service down") from passing to partial based on this first-hand evidence, not any code change.
- Logged one new anti-goal finding (iter-35/k, AG-8, minor, unresolved) for the live-observed memory exhaustion; confirmed all 8 previously carried findings are still unresolved but the code behind them is byte-identical.
- Merged browser-QA/replay results: 6 of 8 journeys pass (the 2 non-passes are exactly J-06 and J-07).

## What's left

- Journey J-06 ("Pages load only what they need") is partial — 4 sibling research lab pages (Market Phase & Severity, Regime × Phase & Factor, Factor Lab, Severity-Velocity) show a bare unlabelled blank/loading skeleton with no Retry button during a slow load, instead of the honest "still computing" panel Regime Lab already has.
- Journey J-07 ("Heavy aggregates never take the service down") is partial — peak memory reached exactly the declared cap with zero margin during a heavy background job, and that margin has never been recorded in `reports/perf-budgets.md`.
- Root cause of both: the whole `daily_prices` table still loads fully into RAM on J-07's own warm path (`prices.py:131-152`) — a verbatim contradiction of a `docs/goal.md` Success Criterion; the largest open gap, carried since iteration 29.
- A newly-found second memory risk: an unbounded per-claim lookup on the user-facing `/api/evidence` drawdown path (`forward_testing.py:2325`) failed twice today.
- Regime Lab's cold "pooled" view still lacks background dispatch and once returned an HTTP 200 whose body read "Internal Server Error" — undiagnosed (iter-33/g).
- Readiness badge wording after a permanently failed warm-up still undecided (`warmup.py:194`, six iterations unmade).
- `/api/health`'s ≤0.1s budget still misses on every poll during a live warm — owner decision needed on how to treat it (iter-34/j).
- Owner decision still open: should `start-frontend.sh` join the host-guard capped-launch list now that it runs a full production build inside automated lanes (iter-33/i)?
- The "[NEW]"-flagged walkthrough recordings J-06 and J-07 both call for are still uncaptured — the fifth consecutive iteration (this round's demo recorder produced zero steps).

## Next step

Run iteration 36 at full depth, using the plan that was already written for iteration 35 (`docs/phases/goal-ops-hardening-iter-35.md`) — it does not need rewriting, it needs running, and it already targets exactly the two problems proven real today. First and biggest: stop loading the whole price table into memory on J-07's warm path (`prices.py:131-152`), proven with a before/after memory measurement recorded in `reports/perf-budgets.md` and a test that fails if the fix is undone. Second: wire the already-built honest "still loading" panel into the four Research lab pages that currently show a blank skeleton. Third: write down today's memory-margin reading, then re-measure after the first fix so the two numbers sit side by side. Also worth a look: the unbounded per-claim lookup on the `/api/evidence` path that failed twice today. Carried, unchanged: the Regime Lab background-dispatch item, `warmup.py:194`, and the two owner-only decisions (the `/api/health` budget disposition and whether `start-frontend.sh` joins the host-guard list).

## Assumptions made

- iter-35 · goal-evaluator — Ambiguity: memory was genuinely exhausted this iteration (peak hit the declared cap exactly) — AG-8 is a critical anti-goal, but its remedy half (graceful degradation, no crash, no blank page) held in full. We chose: filed it as a new minor finding (iter-35/k) and returned ESCALATE rather than REGRESSION, since the framework's critical-severity list is reserved for secrets/paid-dependencies/license/security-backdoor/fabricated-data, none of which apply, and every unblock path is agent work already written into an unrun spec. Reversible: yes
- iter-35 · goal-evaluator — Ambiguity: browser-qa failed J-06 on the ground that "the iteration's own unbuilt scope wasn't implemented" (guaranteed true, since no developer ran), but its own screenshots show all 4 sibling labs rendering a bare blank skeleton during a genuinely slow live load. We chose: rejected browser-qa's stated failure ground but scored J-06 partial anyway on the screenshot evidence, since a screenshot outranks prose and this matches J-06's own honest-status Acceptance clause. Reversible: yes
- iter-34 · goal-evaluator — Ambiguity: J-07's health-check responsiveness held (185/185 HTTP 200) but its numeric ≤0.1s budget was missed on every single poll during a live warm. We chose: scored J-07 passing and filed the miss as a new unresolved finding (iter-34/j), since J-07's own Acceptance block names the memory-abort step and "truthful health" but never the budget number, and raising the bar after the work was already done would be goalpost-moving. Reversible: yes
- iter-33 · goal-evaluator — Ambiguity: the host-protection rule forbids launching heavy compute outside capped launch scripts, and `start-frontend.sh` now runs a full multi-worker production build inside automated lanes without being on the host-guard capped-script list. We chose: recorded it as a new minor finding and an explicit owner decision item, not a critical violation, since the capped-script list is byte-unchanged and the build measurably inherits the CPU-affinity mask in practice. Reversible: yes
- iter-33 · goal-evaluator — Ambiguity: J-06's steps all ran for the first time, but the required "[NEW]"-flagged walkthrough recording was never captured and the health-check budget read over-budget under load. We chose: scored J-06 passing with an evidence-substitution flag, since a missing walkthrough capture is a documented capture defect that must never block, and the honest-status clause is about showing truthful on-screen states, which two screenshots proved. Reversible: yes
- iter-33 · goal-decomposer — Ambiguity: J-06's speed-test step names `start-frontend.sh` as "production mode," but the script had actually been running slower developer mode the whole session. We chose: fixed the launcher to genuinely run production mode rather than loosening the goal text, since the goal's own wording already asserted the fact the script contradicted. Reversible: yes
- iter-32 · goal-evaluator — Ambiguity: a developer-disclosed list of scanner runs is unbounded and grows with run count, but an earlier iteration had accepted this same list as "bounded, small." We chose: recorded it as a new minor watch-item finding, not a blocking violation, explicitly stating it must not become the next iteration's goal, keeping the fact checkable without moving the goalposts on previously-accepted work. Reversible: yes
- iter-32 · goal-evaluator — Ambiguity: J-07's headline promise (the service never goes down) was strongly proven, but two of its four enumerated steps (the health-latency figure, the memory-pressure drill) had never actually been executed. We chose: scored J-07 partial, not passing, since the two steps are literal and unexecuted, and this session had twice rejected a goal-achieved confirmation for accepting a substitute artifact. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-35.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-35-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-35-review.md |
| Browser QA | FAIL | reports/phase-goal-ops-hardening-iter-35-ui-test-results.md |
| Goal evaluation | ESCALATE | runs/goal-session-ops-hardening/iter-35/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
