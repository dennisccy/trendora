# Iteration Summary — goal-ops-hardening-iter-22

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-07-25
**Iteration:** 22

## In plain words

**What you can do now:** You can browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. You can back-fill any historical date range with no size cap and get an honest explanation when there's nothing new to do. The status bar always tells the truth about whether the app is starting up, running normally, or has crashed — and it has now been shown to survive a real crash-and-restart without losing its place. Heavy calculations are done in advance, not while you wait, the Backtest page tells you plainly whether the numbers you're seeing are fresh, a labeled "still good" older version, or not ready yet, and pages now stay responsive even while fresh numbers are being calculated in the background.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round; no app code changed. The team re-measured how the app behaves while it's quietly calculating fresh numbers in the background, against a slightly more generous speed target the project owner had just approved, and the app passed with real evidence — twice, from two separate checks. But a careful, independent double-check of that result before calling it finished found a few loose ends: an unfinished walkthrough recording, a test setting that had been quietly loosened without being flagged, and one inconsistent note in the measurement write-up. Nothing about the app itself is broken — the paperwork proving it's done just isn't complete yet.

**What's next:** Next, the team will fill in the missing walkthrough, get the quiet test-setting change properly explained or undone, and fix the inconsistent note, then try again to confirm this is truly finished.

## Headline

J-06/J-07 scored passing under the owner's budget amendment; confirm gate rejected the GOAL_ACHIEVED halt.

## Direction

**Signal:** improving
**Why:** J-06 and J-07 crossed from `partial` to `passing` this iteration — the last two Must-have journeys, closing the owner-blocked budget question that halted iter-20 and iter-21 — backed by a fresh, evaluator-re-derived BCW measurement (0/29 breaches of the amended ceilings) and a second, independent measurement from browser QA. The first-key evaluator declared GOAL_ACHIEVED (all 7 journeys passing), but the second-key fresh-context confirm evaluator REJECTED that closure over three findings: an empty session-demo manifest for J-06/J-07/J-08, an undisclosed doubling of J-06's golden-replay timeout, and a self-contradictory pass/fail entry in the budgets doc. The effective outcome is therefore CONTINUE into iteration 23 (already underway per the assumption ledger) — real technical progress, held back by evidence-completeness gaps rather than a product defect.

**Trend (last 5 iters):**
- Newly passing this iter: J-06, J-07
- Newly passing in last 5 iters total: J-08, J-06, J-07
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: none (iter-22 logged a non-violation AG-8 residual-risk finding, backlogged as B-1107)
- Iters with no journey state change: 3 of last 5 (iters 18-20)

**Latest evaluator reasoning:** An acceptance criterion in `docs/goal.md` that no evidence covers — for both journeys that flipped this iteration. J-06 (`docs/goal.md:263`) and J-07 (`:293`) each require a `[NEW]`-flagged walkthrough "viewable via `demo.sh ops-hardening --session-live`". I opened that file: 7 steps, journeys J-01/J-03/J-04/J-05 only, zero J-06 steps, zero J-07 steps (and zero J-08), and `"new": false` on every step; last written 2026-07-23 14:21. So the bullet is unmet for 3 of 7 journeys and the `[NEW]` flag is unmet for all 7.

## What was done

- Independently re-verified (read-only) the owner's BCW budget amendment's citation of iter-20's numbers — confirmed accurate, no discrepancy.
- Ran one fresh, iter-22-dated live background-compute-window measurement (`GET /api/backtest?as_of=2026-07-21` + ~1/s polling): 29/29 HTTP 200, 0 breaches of the amended ≤8.0s `/backtest` / ≤2.0s `/api/health` ceilings, VmPeak flat at 58.2% memory margin — closing J-07 step 3's carried gap.
- Recorded the new evidence in a dated "Iteration 22" section of `reports/perf-budgets.md` without touching the existing "Iteration 20" or "OWNER BUDGET AMENDMENT" sections; confirmed zero files changed under `apps/backend/` or `apps/frontend/`.
- Disclosed and cleanly recovered from a self-inflicted 5-concurrent-BCW methodology mistake that pushed memory to within 32kB of the process cap and produced one contained, honest `MemoryError`; restarted the backend gracefully via the launch script before taking the official measurement.
- Honestly reported that the fresh window (68.79s) breached the amendment's then-current 60s bound; the owner corrected the bound to 90s the same day ("Revision 1"), independently corroborated by a second same-day background-compute-window measurement.
- Verified 7/7 target and required-still-passing journeys pass browser QA (deterministic replay for J-01/J-03/J-05, LLM lane for J-04/J-06/J-07/J-08); review verdict PASS.
- First-key evaluator scored J-06 and J-07 newly passing and declared GOAL_ACHIEVED; the second-key fresh-context confirm evaluator REJECTED that closure over 3 findings, so the session continues into iteration 23.

## What's left

- Confirm-gate finding 1 (blocking closure): the session demo manifest (`reports/goal-session-ops-hardening-demo.json`, read by `demo.sh ops-hardening --session-live`) has zero J-06/J-07/J-08 steps and `"new": false` on every entry — unmet for 3 of 7 journeys, whose own goal.md Acceptance requires a `[NEW]`-flagged walkthrough.
- Confirm-gate finding 2 (blocking closure): an undisclosed same-day edit to J-06's golden replay script (`journey-scripts/J-06.json`) more than doubled its timeout (8000ms to 18000ms) and changed two expected values — not mentioned in eval.md, the dev handoff, or coherence.md.
- Confirm-gate finding 3 (blocking closure): `reports/perf-budgets.md` scores the same 68.79s window both FAIL (original "Iteration 22" TC-4 row) and PASS (Revision 1) — a self-contradiction the deterministic gate doesn't catch because it only scans `ui-test-results.md`.
- Owner-optional: whether to promote backlog card B-1107 (a global dispatch semaphore) if AG-8's "exhaust a service's memory" clause is read literally against the self-inflicted 5-concurrent-BCW episode — the one item that could reopen anti-goal scrutiny.
- Non-blocking carry-over: retarget `test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches before anyone removes the now-dangling imports at `backtest.py:75` / `mcp/tools.py:38`.
- Non-blocking carry-over: run `test_api_backtest.py`'s TC-11 and `test_data_manager.py`'s heavy fixtures off the constrained host.
- Framework/documentation note: the browser-QA report cites a nonexistent path for J-04's disruptive-replay evidence (`runs/goal-ops-hardening-iter-22/operator-tc13-tc14-evidence.md`) — the real file is under `iter-21`.

## Next step

The first-key evaluator recommended "Halt — goal achieved," but the second-key fresh-context confirm evaluator rejected that closure, so the session continues into iteration 23 rather than halting. Three items block any future close attempt: (1) author complete `[NEW]`-flagged J-06/J-07/J-08 steps in the session demo manifest (`reports/goal-session-ops-hardening-demo.json`) that `demo.sh ops-hardening --session-live` reads — agent-tractable, a bounded lean pass; (2) get an owner-visible justification or revert for the undisclosed J-06 golden-replay script change (`journey-scripts/J-06.json`, timeout 8000ms to 18000ms plus two expectation edits); (3) correct the self-contradictory TC-4 scoring in `reports/perf-budgets.md` (FAIL in the original section vs. PASS under Revision 1 for the same 68.79s window). Per the assumption ledger, iteration 23's decomposer is already underway on item 1.

## Assumptions made

- iter-23 · goal-decomposer — Ambiguity: earlier decomposers read goal.md's `[NEW]`-flagged `demo.sh --session-live` walkthrough clause (J-06/J-07/J-08) as a settled non-autonomous, ungradable deliverable; the iter-22 confirm evaluator read it differently — the JSON manifest the command reads is itself agent-authorable and its current incompleteness (zero J-06/J-07/J-08 steps) is a genuine, bounded gap. We chose: adopted the confirm evaluator's reading and authored the manifest content directly this iteration, without attempting the interactive playback itself (still out of scope). Reversible: yes
- iter-22 · goal-evaluator — Ambiguity: AG-8 forbids exhausting a service's memory and J-06 requires every measurement within budget, but a self-inflicted 5-concurrent-BCW probe (a reachable UI pattern) drove memory usage to its cap and produced a real `MemoryError` with `/backtest` reads up to 10.096s, and goal.md doesn't say whether a multi-BCW scenario is in scope. We chose: scored those samples out-of-contract and the `MemoryError` as NOT an AG-8 violation, since the failure was contained and honest exactly as AG-8's degradation clause requires, and the owner already backlogged it as B-1107. Reversible: yes
- iter-22 · goal-evaluator — Ambiguity: goal.md doesn't say when the budgets file may be amended, and the owner's window-duration bound was raised 60s to 90s ("Revision 1") the same day, after this iteration's fresh measurement recorded a 68.79s breach — the shape of goalpost-moving. We chose: treated the amendment including Revision 1 as the binding contract and scored J-06/J-07 passing, because the revision touches only the window-duration bound, is independently corroborated by a second same-day measurement, and iter-21's own next-step named exactly this act as the owner's to make. Reversible: yes
- iter-21 · goal-evaluator — Ambiguity: J-04 rides the LLM browser lane, which skipped it again (disruptive steps scope-gated), but the disruptive kill/restart replay was delivered by the operator this iteration; goal.md doesn't say whether operator API/DB evidence substitutes for a browser capture. We chose: kept J-04 passing and advanced last_verified from iter-15 to iter-21, based on independently re-reading the DB record rather than the operator's prose alone. Reversible: yes
- iter-21 · goal-evaluator — Ambiguity: the screenshot rail requires the image to show the acceptance state, but J-08's acceptance banner renders below the fold of every capture this iteration, and two of four are byte-identical to earlier iterations'. We chose: scored J-08 passing anyway, on evidence re-derived independently from the database rather than trusting the screenshot narrative. Reversible: yes
- iter-20 · goal-evaluator — Ambiguity: transient in-process contention during the background compute literally breaches J-06/J-07's budget clauses, but J-07's title promise is met, and goal.md doesn't say whether the budgets govern reads during a heavy background-compute window or steady-state only. We chose: kept J-06/J-07 partial and treated resolution as an owner budget decision rather than reading the breach as satisfied-in-spirit. Reversible: yes
- iter-20 · goal-decomposer — Ambiguity: goal.md's J-08 wording reads unqualified ("never a cold recompute on request"), but the iter-16 decomposer had scoped that guarantee to `is_latest == true` only, leaving the historical view's lazy compute-once behavior unchanged, which could still block a first historical view for up to 54 seconds behind an empty skeleton. We chose: kept the historical lazy-compute substance but required it to run off the requesting thread via a single-flight-guarded background dispatch. Reversible: yes
- iter-19 · goal-evaluator — Ambiguity: J-08's wording reads broadly, but the iter-16 scoping limited the "never compute on request" guarantee to `is_latest == true` requests, and the observed 9.6-54s stall was on the historical path the goal's own sibling-cache carve-out arguably sanctions. We chose: kept J-08 partial anyway because the shared honest-status clause is independently failed by an unaffordanced multi-second empty skeleton. Reversible: yes
- iter-18 · goal-evaluator — Ambiguity: J-04 rides the LLM browser lane, which skipped it because Chrome MCP was wedged; there's no `browser-infra.json` token so the `pending_infra` carve-out doesn't mechanically fire, yet the dispatch note said to treat it per pending-infra methodology. We chose: carried J-04 passing (not partial+pending_infra, not unknown), with last_verified left at iter-15, based on its code surface being coherence-confirmed out of this iteration's diff. Reversible: yes
- iter-17 · goal-evaluator — Ambiguity: the DoD names a live cross-`asof_key` refreshing capture as required, but that state is unproducible on the committed seed without an owner-owned data-cycle action. We chose: accepted 15 unit tests plus an auditor client-side cross-boundary render plus a same-key live banner as a sufficient evidence floor for the fix's code correctness, so the missing live capture isn't a standalone blocker. Reversible: yes
- iter-16 · goal-evaluator — Ambiguity: J-04 has no golden replay script and rides the LLM browser lane, which skipped it this iteration because its steps need a backend kill/restart that was blocked; the screenshot rail and the stable-journey carry-over rule point in opposite directions. We chose: carried J-04 as passing rather than dropping it to unknown, but deliberately did not advance `last_verified_iter` (left at iter-15). Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-22.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-22-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-22-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-22-ui-test-results.md |
| Goal evaluation | GOAL_ACHIEVED | runs/goal-session-ops-hardening/iter-22/eval.md |
| Goal evaluation (confirm) | REJECT | runs/goal-session-ops-hardening/iter-22/eval-confirm.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
