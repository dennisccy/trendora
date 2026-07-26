# Iteration Summary — goal-ops-hardening-iter-25

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-07-26
**Iteration:** 25

## In plain words

**What you can do now:** You can browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. You can back-fill any historical date range with no size cap and get an honest explanation when there's no new work to do. The status badge at the top of the app stays truthful through startup, updates, or a crash, and pages stay responsive even while the backend computes new numbers in the background. A small live badge shows on every page whenever the backend is quietly computing something in the background, and the Data Manager page shows exactly which date it's working on, how far along it is, what happened last time, and — now — an honest "we don't know" message on the rare occasions it briefly loses touch with the backend.

**What changed this time:** This round finished the guided walkthrough for that background-compute indicator, so it's now included in the product's full tour. The "we don't know" wording added last time was also double-checked and confirmed working. A closer, independent second check then found two loose ends in the evidence behind this work: the speed measurement for the status check hasn't been cleanly re-recorded on a quiet computer (two readings disagree about whether it's within target), and nobody has actually shown the panel correctly displaying a genuine failure with its reason. So the finish line moved slightly further out than first thought.

**What's next:** Next, a small planned round will record a clean speed measurement for the status check on an idle computer and add a safe way to prove the panel correctly shows a failed background job with its reason, then take another look at whether every requirement is truly met.

## Headline

Closed J-09's walkthrough gap and audit findings F1/T1, but second-key confirm rejected GOAL_ACHIEVED

## Direction

**Signal:** improving
**Why:** J-09 ("the backend discloses its own background-compute activity") crossed partial → passing this iteration — its Walkthrough-manifest gap and audit findings F1/T1 were both closed, and all 8 must-have journeys carry fresh iter-25 evidence with zero regressions and no anti-goal violations. But the second-key fresh-context CONFIRM run rejected the resulting GOAL_ACHIEVED call: J-09's ≤0.1s health-check clause was credited by interpretation rather than by a quiet-host measurement recorded in `perf-budgets.md`, and J-09 step 4's failure-branch has no citable evidence (every captured panel shows only "completed"). The effective session verdict is therefore CONTINUE, and iter-26 is already scoped to close exactly those two gaps.

**Trend (last 5 iters):**
- Newly passing this iter: J-09
- Newly passing in last 5 iters total: J-08 (iter-21), J-06 and J-07 (iter-22), J-09 (iter-25)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none
- Iters with no journey state change: 1 of last 5 (iter-23)

**Latest evaluator reasoning:** A criterion cannot be simultaneously an open owner question and a certified pass. J-09 step 4's failure branch has no citable evidence — every captured panel in the iter-24 and iter-25 evidence directories renders only "completed"; no capture, and no case in the 8-case resolver test, exercises the failure path. Neither item is a regression and no anti-goal is breached — but the last unmet clause of the last journey is being closed by judgement rather than by the evidence its own acceptance text names. Default-to-reject applies.

## What was done

- Rewrote two background-compute-registry tests (`test_health.py`, `test_readiness.py`) to compare identity/shape excluding the volatile `elapsed_ms` field, closing audit T1's flake risk.
- Added a pure resolver (`resolveBackgroundComputePanelBranch`) so the Data Manager panel shows an honest "state unknown — the backend is unreachable" message on a failed readiness poll instead of falling through to the idle message, closing audit F1.
- Appended 4 new `[NEW]`-flagged, verified J-09 steps (n=13-16) to the session demo manifest that `--session-live` reads, closing J-09's Walkthrough acceptance clause.
- Added an 8-case frontend unit test for the new resolver.
- Re-verified all 8 must-have journeys with fresh iter-25 evidence (deterministic replay for 6, LLM lane for J-07, live browser walkthrough for J-09).
- Verified 8 of 8 target journeys pass browser QA (0 skipped).

## What's left

- The second-key CONFIRM rejected GOAL_ACHIEVED on two J-09 gaps: (1) the ≤0.1s `/api/health` steady-state clause is credited by interpretation, not by a quiet-host re-measurement recorded in `perf-budgets.md` (the recorded max is 0.127788s / mean 0.103597s, above budget; a clean 0.094604s reading from iter-24 QA on the same build was never written into that file).
- (2) J-09 step 4's "shows a failed background compute with the recorded reason" clause has no citable evidence — every captured panel renders only "completed"; the two rewritten registry tests were never run to a pass/fail line on this iteration's host.
- Owner question audit B5 still open: whether the at-rest ≤0.1s `/api/health` target should stand as written, given the endpoint has sat at ~98.6% of budget since iter-16.
- A failed warm-up leaves the readiness badge reading "Initializing... history 89/89" indefinitely — never a false "Ready", but not one of the three states the goal names; no journey step covers it yet.
- Audit B2 (a `Thread.start()` failure would leave the badge reading "running" forever) remains deferred — needs the `ensure_historical_forward_aggregates_dispatched` freeze lifted deliberately in its own scoped iteration.
- Carried: retarget `test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches before removing dangling imports at `backtest.py:75`/`mcp/tools.py:38`; run `test_api_backtest.py` TC-11 and `test_data_manager.py`'s heavy fixtures off the constrained box.
- Backlog card B-1107 (global background-compute concurrency cap) stays owner-optional.

## Next step

iter-26 is already scoped (per the goal-decomposer's logged assumption) to close exactly the two gaps the second-key CONFIRM named: (1) add a backend test that monkeypatches a crafted `failed` background-compute outcome and asserts `GET /api/health` serves it verbatim, plus a frontend unit test proving the panel renders the failure `reason` and a danger badge — closing J-09 step 4's citable-evidence gap without re-triggering the unsafe live-failure pattern; (2) settle J-09's ≤0.1s health-check clause with a quiet-host re-measurement recorded in `perf-budgets.md`, since the recorded max (0.127788s) sits above budget while a clean same-build reading (0.094604s) was never written into that file. Once both are closed, re-run the pipeline for a fresh two-key confirm.

## Assumptions made

- iter-26 · goal-decomposer — Ambiguity: the iter-25 GOAL_ACHIEVED second-key CONFIRM rejected J-09 step 4's "shows a failed background compute with the recorded reason" clause for having no citable evidence; goal.md doesn't say whether that requires an actual witnessed live-triggered failure or a deterministic code-level round-trip suffices, and the only known way to trigger a genuine failure on this host reproduces the unsafe 5-concurrent-BCW pattern already tracked as backlog card B-1107. We chose: scoped iter-26 to close the gap with a backend test (a crafted `failed` outcome served verbatim by `GET /api/health`) and a frontend pure-function unit test (rendering shows the `reason` and a danger badge) — never re-triggering the unsafe live-failure pattern. Reversible: yes
- iter-25 · goal-evaluator — Ambiguity: the deterministic replay lane returned FAIL for J-07 (golden step expects "Ready") but the engine's merge overturned it as a "false positive"; goal.md doesn't say whether a required-still-passing journey verified while the host was under our own test harness's memory pressure counts as verified. We chose: accepted the overturn and scored J-07 passing after independently tracing the cause to a one-off warm-up MemoryError under two detached pytest builds, then checking J-07's substance live in the LLM lane's post-restart run. Reversible: yes
- iter-25 · goal-evaluator — Ambiguity: J-09's steady-state `GET /api/health` ≤0.1s clause is measured on both sides of the line across sources (recorded max 0.127788s / mean 0.103597s vs QA's 0.094604s vs this iteration's own ~0.10-0.18s under pytest load); goal.md doesn't say which series binds, or whether this excursion on an endpoint documented at ~98.6% of budget since iter-16 counts as a breach. We chose: scored the clause met at the same bar this session already applied to J-06/J-07, since the tightness is pre-existing and this iteration's diff adds zero backend work, and routed the standing question to the owner as audit B5. Reversible: yes
- iter-24 · goal-evaluator — Ambiguity: the same J-09 health-budget disagreement, one iteration earlier (developer 0.127788s max vs QA 0.094604s max against the unchanged ≤0.1s budget); goal.md doesn't say which series binds. We chose: did not treat it as a J-06/J-07 regression since the diff adds zero DB work, but logged it as an open J-09 gap routed to the owner rather than laundering it. Reversible: yes
- iter-24 · goal-evaluator — Ambiguity: J-09's Acceptance ends with a Walkthrough bullet requiring `[NEW]`-flagged steps playable via `demo.sh ops-hardening --session-live`, but the iteration spec that planned J-09 never mapped that bullet into IN SCOPE or DoD; goal.md doesn't say whether a journey whose numbered steps all verify, but whose Acceptance carries an unplanned deliverable, counts as passing. We chose: scored J-09 partial, treating the Acceptance bullet as binding on the journey regardless of the iteration spec's scope, since this session had already adjudicated the identical clause twice for J-06/J-07/J-08. Reversible: yes
- iter-24 · goal-decomposer — Ambiguity: J-09's Consistency clause implies a retained-record count exists, but its steps only ever describe a single outcome, so a single `last_outcome` field and a bounded `recent_outcomes` list both satisfy the literal step text. We chose: built a bounded, config-governed `recent_outcomes` list (default 5) so the "retained-record count" phrase has a concrete testable referent, though a literal reading of the steps could see this as over-built. Reversible: yes
- iter-23 · goal-evaluator — Ambiguity: a spec clause required the J-07 demo step to cite figures verbatim from `perf-budgets.md`'s Iteration 22 section, but the step used 4-decimal precision ("7.1191s"/"0.2530s") where that file prints 3 decimals. We chose: treated it as a cosmetic precision nit rather than a DoD failure or evidence-integrity problem, since the 4-decimal figures trace exactly to the raw measurement file and no second source was involved. Reversible: yes
- iter-23 · goal-evaluator — Ambiguity: two of J-06/J-07/J-08's new walkthrough scenes narrate transient states (a refreshing banner, a health-polling sequence) that can't be reproduced live at an arbitrary playback; goal.md doesn't say whether "viewable via --session-live" requires the viewer to actually SEE the state on screen or only that the step exists and plays. We chose: scored the clause met since the manifest artifact --session-live actually reads now holds complete, accurate, live-checked steps for all three journeys — the limit of what an agent can produce without an owner-gated ingest. Reversible: yes
- iter-23 · goal-decomposer — Ambiguity: whether J-06/J-07/J-08's Walkthrough clause (viewable via `demo.sh ops-hardening --session-live`) is a settled non-autonomous deliverable (iter-12's original reading, inherited through iter-22), or whether the JSON manifest that command actually reads is itself agent-authorable. We chose: the confirm evaluator's reading — the manifest is agent-authorable and its incompleteness is a genuine, bounded gap, not evidence the whole capability is out of reach; this iteration authored the missing content directly, without attempting the interactive playback itself. Reversible: yes
- iter-22 · goal-evaluator — Ambiguity: the developer's accidental 5-concurrent-BCW probe drove memory near the ulimit cap and produced a real MemoryError with some /backtest reads above the BCW ceiling; goal.md doesn't say whether a multi-window scenario is in scope for any journey's budget. We chose: scored those samples out of contract and the MemoryError as a contained, honest failure rather than an AG-8 violation, since it was logged non-fatal with no wedge/crash and the owner had already reviewed and backlogged the episode (card B-1107). Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-25.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-25-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-25-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-25-ui-test-results.md |
| Goal evaluation (first key) | GOAL_ACHIEVED | runs/goal-session-ops-hardening/iter-25/eval.md |
| Goal evaluation (second-key confirm) | REJECT | runs/goal-session-ops-hardening/iter-25/eval-confirm.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
