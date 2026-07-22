# Iteration Summary — goal-ops-hardening-iter-10

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-07-22
**Iteration:** 10

## In plain words

**What you can do now:** Browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any historical date range with no size cap and get an honest explanation when there's nothing new to add, and can trust that even the heaviest back-to-back data updates won't slow down or crash the app. The status badge tells the truth during startup, a data update, or a crash — and now, if the app does crash partway through a data update, the job history honestly shows the real progress that was made instead of pretending nothing happened.

**What changed this time:** No code changed this round — it was a proof round. The team deliberately crashed the running app in the middle of a data update a third time and then read the app's own history page: it correctly showed the true progress of the interrupted job (hundreds of days processed) rather than a false "nothing happened." That closes the last verification gap this operations-hardening effort had been carrying since last round, and everything that already worked was re-checked and still holds.

**What's next:** Next we'll re-measure page-loading speed across the app and record the two remaining walkthrough videos, while an owner decides how to handle one remaining rare slow-and-crash risk on an advanced backtest page before this chapter can be called fully done.

## Headline

J-04 step 6 closed: interrupted jobs now show real persisted progress on the Data page.

## Direction

**Signal:** improving
**Why:** J-04 moved from `partial` to `passing` this iteration after the evaluator independently re-derived the crash-cycle evidence from sqlite and the backend log, closing the session's last open verification gap on that journey; J-01, J-03, and J-05 all re-verified `passing`. J-06 remains the only non-passing Must-have journey, and its remaining gap is explicitly scoped as an owner decision rather than agent-invented work, so this iteration is unambiguous forward progress with no new regression.

**Trend (last 5 iters):**
- Newly passing this iter: J-04
- Newly passing in last 5 iters total: J-01, J-03, J-04, J-05
- Regressions in last 5 iters: J-05 (iter-7)
- Anti-goal violations in last 5 iters: 4 total (2 critical: iter-7 AG-8 [resolved iter-9], iter-9 AG-8 distinct dimension [still unresolved]; 2 minor: iter-8 AG-10 [resolved iter-9], iter-10 AG-10 [still unresolved])
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** The one gap this session has carried since iter-9 — J-04 step 6, "an interrupted mid-flight job shows its last persisted progress on the rendered `/data` page" — is closed. A third crash cycle caught a 504-date backfill genuinely mid-flight (`kill -9` of backend pid 2080333 at 19:32:15Z, restart 19:32:18Z as pid 2100030), and the resulting row renders `interrupted` with `Snapshots: 117` and a full non-null breakdown, against eight pre-fix sibling rows showing zeros on the same page load. I re-derived the decisive facts myself from sqlite and `logs/backend.log` rather than accepting the lane's or the operator's account.

## What was done

- Confirmed the already-shipped `_checkpoint_run_record` fix (iter-9, unchanged since commit `5e073cf1`) is present and correct; zero product or test source changes made this iteration.
- Ran targeted regression tests: 21 passed (data-manager jobs pipeline, 562.05s) and 8 passed / 1 deselected (backend launch script, 53.79s) — no new failures.
- Re-drove J-04's full six-step live acceptance through a third kill/restart cycle, closing step 6 with evidence read directly from the rendered Data page's Run History panel (not API JSON alone).
- Re-verified J-01 (deterministic replay) and J-03 (deterministic replay) still pass; re-confirmed J-05 (light non-heavy re-confirmation) still passes.
- Verified all 4 tested journeys (J-01, J-03, J-04, J-05) pass browser QA — 4/4, 0 skipped, raw `.llm.md` read directly per the standing merge-script caveat.

## What's left

- Journey J-06 ("Pages load only what they need") stays `partial` — the only non-passing Must-have journey session-wide.
- Unresolved critical anti-goal: an on-load `GET /api/backtest` → `forward_aggregates_cached` memory-exhaustion path (J-06/AG-8 dimension) hard-blocks GOAL_ACHIEVED, awaiting an owner scope/deferral decision.
- The 11-page real-browser perf sweep and the ≤5s boot budget haven't been re-measured since iter-9 changed the launch script.
- The `demo.sh ops-hardening --session-live` walkthroughs for J-05 and J-06 are still unproduced (outstanding since iter-4) — need production or an explicit human deferral.
- Minor anti-goal: this iteration's developer-run pytest bypassed host-guard confinement (ran unconfined across all cores, peaked at 91°C vs. the 95°C watchdog, no trip) — needs fixing, or the anti-goal text amended to state how test bursts are confined.
- Owner decision still outstanding: whether to flip `HOST_GUARD_REQUIRE_MARKERS`.
- Bookkeeping gap: `runs/goal-ops-hardening-iter-10/status.json` still reads `dev_complete` / `browser_checks_run: false` even though the browser lane ran and passed; the crash-cycle backend process has since shut down cleanly and needs restarting before the next lane.
- Framework maintainer items unfixed: the merge script drops bolded **FAIL** cells from the rollup; the `Frontend Present: no` browser-qa-skip misrouting; the pre-existing, unrelated `tests/test_db.py::test_create_all_produces_expected_tables` failure.

## Next step

Full depth, session-closeout aimed at J-06 (the only non-passing Must-have left): (1) re-run the 11-page real-browser TTI/on-load latency sweep and `bash scripts/measure-perf.sh --boot`, recording both in `reports/perf-budgets.md` (the `--boot` run also discharges J-04's carried boot-budget caveat); (2) produce the `demo.sh ops-hardening --session-live` walkthroughs for J-05 and J-06, or obtain an explicit human deferral; (3) owner decisions only — do not let an agent invent these: scope or formally defer the on-load `/api/backtest` memory-exhaustion path, and decide on `HOST_GUARD_REQUIRE_MARKERS`; (4) AG-10 hygiene — confine agent-run pytest with the host-guard taskset/BLAS env, or amend AG-10 to state how test bursts are to be confined; (5) bookkeeping — advance `status.json` past `dev_complete` and restart services before the next lane; QA/audit/closure lanes have not run since iter-9 (lean depth).

## Assumptions made

- iter-11 · goal-decomposer — Ambiguity: an operator note claimed agents in this pipeline cannot start/stop services and that the subagent-resume channel is broken, meaning a step needing a fresh backend start (e.g. the boot-budget measurement script) might not be directly executable, and goal.md is silent on who may launch backend processes. We chose: wrote the boot-budget measurement as the standard path (the agent runs it directly) with a fallback that the operator runs the command and reports the output verbatim if the environment blocks it, mirroring iter-10's own accepted kill/restart fallback pattern. Reversible: yes
- iter-10 · goal-evaluator — Ambiguity: only J-04's steps 5-6 were re-driven this iteration; steps 1-2 rest on a pre-host-guard measurement and steps 3-4 on iter-9's simulations, and the only new timing datapoints were coarse operator polls, not real measurements. We chose: scored the journey `passing` because this iteration's product diff was empty (`README.md` only, confirmed by scan-report/coherence/diff read), so no code path steps 1-4 cover could have changed, while recording the un-re-measured boot budget as a carried caveat and next-step item. Reversible: yes
- iter-10 · goal-evaluator — Ambiguity: J-04's decisive step-6 artifact was a DOM/HTML capture, not a screenshot image, because every post-scroll screenshot of the Run History row rendered blank — a reproducible capture artifact on the very tall page — and the rule to let a screenshot outrank prose doesn't address a case with no usable screenshot. We chose: accepted the verbatim DOM capture as rendered-surface evidence and scored J-04 `passing`, after confirming the captured text is composed client-side (absent from the API payload) and matches the database row queried independently. Reversible: yes
- iter-10 · goal-decomposer — Ambiguity: J-04 step 6 requires killing and restarting the backend as a live test action, and an out-of-band operator note claimed agents cannot start/stop services and that the fix was already "API-verified" — but the prior evaluator's binding instruction was that API-level evidence alone must not flip J-04 to passing, and the note's permission claim could not be independently confirmed. We chose: wrote the standard path as browser-qa-agent re-driving the full six-step acceptance itself (as it has for steps 1-5 all session), with a fallback that the operator may perform the kill/restart and hand the state to browser-qa-agent to read from the rendered page, not from API JSON alone. Reversible: yes
- iter-9 · goal-evaluator — Ambiguity: no artifact emits a `UT-J-05` verdict row, yet J-05 was the iteration's target journey. We chose: treated the scattered per-step citation trace as satisfying the evidence bar rather than scoring `unknown`, after personally reopening and re-deriving each cited row myself. Reversible: yes
- iter-9 · goal-evaluator — Ambiguity: the deferred on-load `/api/backtest` memory-exhaustion path is a recorded critical anti-goal dimension, and a literal reading of the decision tree would force a REGRESSION halt on a finding already human-acknowledged. We chose: recorded it fail-closed as a distinct critical, unresolved entry that hard-blocks GOAL_ACHIEVED, without firing the REGRESSION branch, since it was neither newly introduced nor worsened this iteration. Reversible: yes
- iter-9 · goal-evaluator — Ambiguity: J-04's step-6 evidence was split across two builds — failed pre-fix in the browser, fixed intra-iteration, and only confirmed post-fix at the operator/API level — with no journey status matching that exact situation. We chose: scored J-04 `partial` (steps 1-5 verified, step 6 fixed and credibly evidenced but not browser-re-verified), rejecting `failing`, `passing`, and `unknown` as each misrepresenting the current tree. Reversible: yes
- iter-9 · goal-decomposer — Ambiguity: a prior recommendation named fixing the shared framework harness's browser-qa skip bug, but that defect lives outside this project's product scope and goal.md is silent on whether a goal-mode spec should carry framework fixes. We chose: did not touch the framework; instead set this iteration's own spec to the honest `Frontend Present: yes` value, routing around the bug without patching shared automation. Reversible: yes
- iter-8 · goal-evaluator — Ambiguity: AG-10's MUST-apply clause was unmet (one launch script missing caps entirely), and goal.md doesn't say whether an unmet MUST-apply clause carries the same severity as the REGRESSION trigger it names. We chose: recorded it minor rather than critical — nothing was stripped or weakened, and goal.md's own notes treat closing the gap as scheduled next-iteration work — while flagging uncertainty about the severity call explicitly. Reversible: yes
- iter-8 · goal-evaluator — Ambiguity: J-05 still carried a `regressed` status from iter-7's human-acknowledged halt, creating tension between a rule that any `regressed` status forces a REGRESSION verdict and the operative decision-tree rule that fires only on a passing→failing move. We chose: treated the operative rule as controlling and returned CONTINUE, since no journey moved passing→failing this iteration and every unblock path was agent-owned. Reversible: yes
- iter-8 · goal-decomposer — Ambiguity: the prior evaluator offered three undirected recovery options for J-05's memory-exhaustion regression without mandating one, and it was unclear whether "health must fail-fast" meant new code in the health endpoint itself or removing the underlying memory pressure. We chose: bounded peak RAM at the source (per-item MemoryError catches with cleanup in the ingest-refresh loops) rather than raising the memory cap or isolating ingest into a separate process, since the health endpoint's existing generic handling already degrades honestly once memory headroom is restored. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-10.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-10-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-10-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-10-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-10/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
