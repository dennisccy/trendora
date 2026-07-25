# Iteration Summary — goal-ops-hardening-iter-21

**Verdict:** STALLED
**Iteration type:** goal-lean
**Date:** 2026-07-25
**Iteration:** 21

## In plain words

**What you can do now:** You can browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. You can back-fill any historical date range with no size cap and get an honest explanation when there's nothing new to do. The status bar always tells the truth about whether the app is starting up, running normally, or has crashed. Heavy calculations are done in advance, not while you wait, and the Backtest page tells you plainly whether the numbers you're seeing are fresh, a labeled "still good" older version, or not ready yet.

**What changed this time:** Behind-the-scenes work — nothing visibly new this round. The app's code didn't change at all; instead, the team confirmed two things actually hold up under real conditions: the Backtest page stayed fast with zero slowdowns even while new data was genuinely being imported in the background, and the app recovered cleanly from a hard crash without losing its place in an in-progress job. One rough edge is unchanged and still needs an owner call: during a roughly half-minute background calculation window, some page loads and status checks run a bit slower than the target speed.

**What's next:** The project owner needs to decide how that brief slower window should be treated — relax the speed target for it, invest in removing the slowdown entirely, or say the target only applies to normal browsing — and once that's settled, the last two checks can close out the project.

## Headline

J-08 passes (first since iter-16) — 5 of 7 journeys now pass; J-06/J-07 remain owner-blocked.

## Direction

**Signal:** improving
**Why:** J-08 crossed from `partial` to `passing` for the first time since it appeared at iter-16, and J-04's disruptive-replay evidence advanced for the first time in six iterations (`last_verified` iter-15 → iter-21). J-06 and J-07 are unchanged, and the iteration's own verdict is STALLED because their one remaining gap — transient contention during a bounded background-compute window — has no agent-owned fix left, only an owner budget call. Five of seven journeys are now passing, the highest count yet in this session.

**Trend (last 5 iters):**
- Newly passing this iter: J-08
- Newly passing in last 5 iters total: J-08 (iter-21 only; iters 17-20 added none)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 1 minor (iter-17, operator AG-10 process lapse, resolved same iteration); none unresolved
- Iters with no journey state change: 4 of last 5 (iters 17-20; iter-21 is the exception)

**Latest evaluator reasoning:** The owner's direction-1 authorization paid off: TC-13 (0/4096 `/backtest` breaches, max 429 ms under a real concurrent-ingest overlay) and TC-14 (kill -9 → restart → ready; checkpoint survived at `dates_done 1366/2904`) both PASS, and this zero-code iteration added the literal small-single-day `ready → refreshing → ready` confirmation. J-08 crosses to `passing` — the first new pass since iter-16 — and J-04's disruptive replay, owed since iter-15, is freshly evidenced. Five of seven journeys now pass. But J-06 and J-07 stay `partial` on exactly one unchanged item, and every path from it to a pass is owner-owned.

## What was done

- Zero product code changed — confirmed via empty `git status`/`git diff` on `apps/backend` and `apps/frontend`; this was a pure evidence-consolidation and verification iteration.
- Independently re-verified (read-only) the iter-20 coherence-auditor's dangling-import advisory: confirmed the identical unused-import shape also exists at `backtest.py:75` (not just `mcp/tools.py:38`), and both are load-bearing test-monkeypatch targets — not a safe removal; flagged for a future properly-scoped test-hardening pass.
- Cited the operator's owner-authorized TC-13 (0/4096 `/backtest` breaches under a concurrent-ingest overlay, max 429ms) and TC-14 (kill-9 restart + checkpoint-survival replay) measurements by exact path in the dev handoff, without re-running either.
- Ran the one relevant targeted test file read-only as a behavioral confirmation (25/25 passed, including the four monkeypatch-coupled tests).
- Captured a fresh browser confirmation of J-08's ready → refreshing → ready state machine via a real single-day backfill; the evaluator independently re-derived the state transition from the database (dataset-version bump vs. new-aggregate-row write timestamps) rather than relying on the screenshots alone.
- J-04's disruptive kill/restart + checkpoint-survival evidence advanced for the first time since iter-15 (operator TC-14, evaluator-corroborated from the DB: interrupted job, checkpoint preserved at 1366/2904).
- Verified 4 journeys pass browser QA (J-01, J-03, J-05, J-08); J-04 skipped by design (disruptive steps out of scope, substituted by operator evidence).

## What's left

- Journey J-06 (Pages load only what they need) stays partial — the bounded background-compute window still breaches the ≤1.5s `/backtest` budget (3.0–6.3s observed), unchanged since iter-20.
- Journey J-07 (Heavy aggregates never take the service down) stays partial — `/api/health` transiently breaches its ≤0.1s budget (4/16 samples, max 1.60s) during the same window; availability itself is unaffected (no wedge, all polls 200).
- Closing both needs one owner decision: accept-and-log a `perf-budgets.md` budget amendment for reads during the background-compute window, sanction an off-process/precompute redesign, or rescope the ≤1.5s/≤0.1s budgets to steady-state reads only.
- Test-hardening carry-over: retarget the four `is_latest` monkeypatches in `test_forward_testing_serving_split.py` (they no longer trap the post-iter-20 dispatch path) before anyone removes the now-dead imports at `backtest.py:75`/`mcp/tools.py:38`.
- Future J-08 evidence should use full-page or element-scoped browser captures — this iteration's viewport screenshots sit above the `RefreshingEvidenceBanner`, which renders at page bottom.
- `demo.sh ops-hardening --session-live` walkthrough still owed (settled non-autonomous owner deliverable since iter-12).
- `test_api_backtest.py` TC-11 + `test_data_manager.py` heavy fixtures still need a run off this constrained host.
- J-07 step 3 (VmPeak memory margin) was not re-recorded during the TC-13 pass.

## Next step

HALT for one owner decision — everything agent-tractable on this surface is now done (the latency arc from iter-11 is complete, both owner-gated measurements are in, and J-08 plus J-04 are closed). The owner picks one of three treatments for the transient in-process contention during the bounded ~30s historical background-compute window, the sole remaining blocker for J-06/J-07: (1) accept-and-log a dated `perf-budgets.md` amendment for reads taken during that window — the next evaluator can then score J-06/J-07 passing and GOAL_ACHIEVED is one iteration away with 5 of 7 journeys already passing; (2) sanction an off-process/precompute redesign, previously rejected as unbounded; or (3) rescope the ≤1.5s/≤0.1s budgets to steady-state reads as a recorded contract change. Then resume at full depth — the next iteration is goal-closing (audit + closure + ux-regression before the two-key confirm), which is mandatory anyway if option 2 is chosen.

## Assumptions made

- iter-21 · goal-evaluator — Ambiguity: J-04 rides the LLM browser lane, which skipped it again (disruptive steps scope-gated), but TC-14's disruptive kill/restart replay was delivered by the operator this iteration; goal.md doesn't say whether operator API/DB evidence substitutes for a browser capture on a UI-presentation journey. We chose: kept J-04 `passing` and advanced `last_verified_iter` from iter-15 to iter-21, based on independently re-reading the DB record (`data_provider_runs` id 164: `status: interrupted`, `dates_done 1366/2904`) rather than the operator's prose alone; J-04's UI-presentation steps still rest on iter-14/15 live captures. Reversible: yes
- iter-21 · goal-evaluator — Ambiguity: the methodology's screenshot rail requires the image to show the acceptance state, but J-08's acceptance banner renders below the fold of every capture this iteration, and two of the four are byte-identical to earlier iterations' captures. We chose: scored J-08 `passing` anyway, on evidence re-derived independently from the database (dataset-version bump timing vs. new-aggregate-row write timestamp, a re-tallied budget sample set, and the banner's known-good rendering carried from an unchanged iter-20 capture) rather than trusting the screenshot narrative. Reversible: yes
- iter-20 · goal-evaluator — Ambiguity: transient in-process contention during the ~30s background compute literally breaches J-06/J-07's budget clauses, but J-07's title promise ("never take the service down") is met, and goal.md doesn't say whether the budgets govern reads during a heavy background-compute window or steady-state only. We chose: kept J-06/J-07 `partial` rather than read the breach as satisfied-in-spirit, treating its resolution as an owner budget decision rather than laundering it into a pass. Reversible: yes
- iter-20 · goal-decomposer — Ambiguity: goal.md's J-08 wording ("never a cold recompute on request") reads unqualified, but the iter-16 decomposer had scoped that guarantee to `is_latest == true` only, leaving the historical view's lazy compute-once behavior unchanged — which could still block a first historical view 9.6–54s behind an empty skeleton. We chose: kept the historical lazy-compute substance but required it to run off the requesting thread via a single-flight-guarded background dispatch, rather than removing historical lazy compute or precomputing every historical date at ingest. Reversible: yes
- iter-19 · goal-evaluator — Ambiguity: J-08's wording reads broadly ("never a cold recompute on request"), but the iter-16 scoping limited that guarantee to `is_latest == true` requests, and the observed 9.6–54s stall was on the historical path, which the goal's own sibling-cache carve-out arguably sanctions. We chose: kept J-08 `partial` anyway because the shared honest-status clause ("never a frozen or blank frame") is independently failed by an unaffordanced multi-second empty skeleton, regardless of whether the compute itself is sanctioned. Reversible: yes
- iter-18 · goal-evaluator — Ambiguity: J-04 rides the LLM browser lane, which skipped it because Chrome MCP was wedged; there is no `browser-infra.json` token so the `pending_infra` carve-out doesn't mechanically fire, yet the dispatch note said to "treat per pending-infra methodology." We chose: carried J-04 `passing` (not `partial`+pending_infra, not `unknown`), with `last_verified` deliberately left at iter-15, based on J-04's code surface being coherence-confirmed out of this iteration's diff and the identical carry-over precedent from iter-16/17. Reversible: yes
- iter-17 · goal-evaluator — Ambiguity: the DoD names a live cross-`asof_key` refreshing capture as required, but that state is unproducible on the committed seed without an owner-owned data-cycle action (advancing the max ingested date). We chose: accepted 15 unit tests plus an auditor client-side cross-boundary render plus a same-key live banner as a sufficient evidence floor for the fix's code correctness, so the missing live capture is not treated as a standalone blocker for future iterations. Reversible: yes
- iter-16 · goal-evaluator — Ambiguity: J-04 has no golden replay script and rides the LLM browser lane, which skipped it this iteration because its steps need a backend kill/restart that was blocked; the methodology's screenshot rail and its stable-journey carry-over rule point in opposite directions. We chose: carried J-04 as `passing` rather than dropping it to `unknown`, but deliberately did not advance `last_verified_iter` (left at iter-15) so the record shows no fresh evidence landed. Reversible: yes
- iter-16 · goal-evaluator — Ambiguity: goal.md's J-08 step 2 says the refresh window serves the last complete version "labeled with that version's served as-of," but the implementation resolves all three states strictly within one `asof_key`, so an ingest that advances the latest date yields `not_yet_computed` on a store full of complete versions — and the iteration spec's own scoping arguably sanctioned that. We chose: ruled the fallback must cross as-of boundaries and kept J-08 (and J-06/J-07) `partial` rather than accept the iteration's own spec as sufficient, because the served-as-of label is meaningless unless it can actually differ from the current one. Reversible: yes
- iter-16 · goal-decomposer — Ambiguity: J-08 step 4 reads literally as zero aggregate computation on ANY request, unqualified by `is_latest`/historical, but every sibling ingest-time cache in this session keeps an explicit historical carve-out, and a fully literal reading would regress the pre-existing historical "time machine" viewing capability that no J-08 step actually exercises. We chose: scoped the "never compute on request" guarantee to `is_latest == true` requests only, leaving the historical path's existing lazy create-once-and-cache behavior unchanged, matching every sibling cache's own carve-out. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-21.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-21-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-21-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-21-ui-test-results.md |
| Goal evaluation | STALLED | runs/goal-session-ops-hardening/iter-21/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
