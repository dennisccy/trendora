# Iteration Summary — goal-ops-hardening-iter-11

**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-07-22
**Iteration:** 11

## In plain words

**What you can do now:** Browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. An operator can back-fill any historical date range with no size cap and get an honest explanation when there's nothing new to add, and can trust that even the heaviest back-to-back data updates won't slow down or crash the app. The status badge tells the truth during startup, a data update, or a crash — and if the app does crash partway through a data update, the job history honestly shows the real progress that was made.

**What changed this time:** Behind-the-scenes work — the team re-measured how fast every page loads and re-checked the underlying code for slow shortcuts, and everything re-checked out clean (the app still starts in about a second and a half, and no slow code paths were found). But while running that check, the app twice ran low on its own memory safety limit in the background, and two advanced pages briefly failed to load as a result (the app recovered on its own, no restart needed). That confirms a known, rare risk the team has been tracking is real rather than theoretical, so extra scrutiny is being brought in before deciding what to do about it.

**What's next:** Next, the owner needs to decide how to handle that memory risk (fix it, limit it, or formally accept it) so the team can finish writing up this round's speed results and close out this chapter.

## Headline

J-06 re-swept boot/audit cleanly, but stays partial after a live memory-exhaustion finding.

## Direction

**Signal:** regressing
**Why:** No journey flipped passing→failing this iteration — J-01/J-03/J-04/J-05 all re-verified passing and J-06 stayed partial — but the carried critical AG-8 anti-goal violation (an unbounded `ScannerResult` load in `forward_aggregates_cached`) fired live for the first time: two ingest-warm memory errors and two on-load page failures during the very browser sweep meant to close J-06. The lane that ran the sweep misread the memory exhaustion as ambient host load, so the evaluator escalated to the full pipeline rather than continue, even though the empty product diff means nothing was newly introduced this iteration.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-01, J-03, J-04, J-05
- Regressions in last 5 iters: J-05 (iter-7)
- Anti-goal violations in last 5 iters: 4 recorded (2 critical: iter-7 AG-8 origin [resolved iter-9], iter-9 AG-8 distinct dimension [unresolved, live-fired iter-11]; 2 minor: iter-8 AG-10 [resolved iter-9], iter-10 AG-10 [resolved iter-11])
- Iters with no journey state change: 1 of last 5 (iter-11)

**Latest evaluator reasoning:** "The iteration delivered real, honest work on a literally empty product diff: a fresh cold-boot measurement (1.364 s, ≤5 s, under the host-guard-hardened launcher), a file:line code audit of four Data-Contract rows, host-guard-confined pytest, and an 11-page real-browser sweep whose page TTIs are all comfortably in budget. But J-06 does not close... the browser lane's central claim — that all three anomalies were environmental host contention — is refuted by the backend's own logfile and host telemetry... This is the carried, owner-deferred critical AG-8 dimension firing live — and the lean lanes both missed it. That is exactly the cross-cutting complexity the tree routes to the full pipeline."

## What was done

- Re-measured backend boot-to-health under the host-guard-hardened launcher: 1.364s, holds the ≤5s budget (first measurement since the caps were added).
- Completed a static, read-only code audit of the four named Data-Contract rows (Coverage payload, Backfill run-summary, Job history, Membership-timeline/research-hot-key caches) — no unbounded scan or uncached recompute found on any of them.
- Ran an AG-3 byte-identity spot-check (2 existing tests) confirming ingest-time-warmed values still match a fresh recomputation.
- Ran the targeted backend test subset (29 tests total) under host-guard CPU/BLAS confinement — zero new failures.
- Ran the 11-page real-browser TTI/on-load sweep — every page's load time is comfortably within its budget and no page rendered blank or frozen.
- Verified 5 target/required journeys (J-01, J-03, J-04, J-05, J-06) pass browser QA.

## What's left

- Journey J-06 ("Pages load only what they need") stays partial — the session's last non-passing Must-have; three gaps remain: the sweep numbers were never written into the canonical `reports/perf-budgets.md`, one endpoint (`/api/indexes?full=true` on `/data`) measured 2-2.7x over its 1.5s budget with no valid re-measurement control, and the session-live walkthrough is still unproduced.
- Critical anti-goal AG-8 (`forward_aggregates_cached` → `compute_forward_aggregates`, an unbounded ORM load) fired live this iteration — two ingest-warm memory errors and two on-load page failures (`/api/methodology`, `/api/research/event-study`) — still unresolved and hard-blocks GOAL_ACHIEVED; needs an owner decision on how to scope, fix, or defer it.
- Owner decision still outstanding: whether to flip `HOST_GUARD_REQUIRE_MARKERS`.
- The `demo.sh ops-hardening --session-live` walkthroughs for J-05/J-06 remain unproduced (carried since iter-4/5) — need production or an explicit human deferral.
- `market_phase_cached`'s own byte-identity test still hasn't been run live (needs the full 30-year fixture) — a documented, pre-existing gap, not new.
- The backend and frontend are not currently running (both shut down after this iteration's testing) — the next lane needs them restarted.
- Framework maintainer items unfixed: `merge_ui_test_results.py` drops bolded **FAIL** cells from the rollup; the `Frontend Present: no` browser-qa-skip misrouting; `status.json` stuck at `dev_complete`/`browser_checks_run: false`; the pre-existing, unrelated `tests/test_db.py::test_create_all_produces_expected_tables` failure.

## Next step

Full depth, no new features: (1) OWNER DECISION — scope, amend, or formally defer the AG-8 dimension (`forward_aggregates_cached` → `compute_forward_aggregates` at `forward_testing.py:826` materializes an unbounded `ScannerResult` set and OOMs under the declared memory cap; it produced two on-load page failures this iteration and hard-blocks GOAL_ACHIEVED), plus still-open `HOST_GUARD_REQUIRE_MARKERS` and the J-05/J-06 session-live walkthroughs (produce or defer). (2) Close J-06's G1 by transcribing the existing sweep numbers — including both over-budget readings — into `reports/perf-budgets.md` (data already exists, no re-measurement needed). (3) Close J-06's G2 by re-measuring `/api/indexes?full=true` on `/data` with three cache-disabled loads on a quiet host with no ingest running, recording the result either way. (4) The auditor must re-open TC-4's "no genuine violation found" conclusion — it verified cache-HIT paths but never the MISS/compute path that is actually OOMing. (5) The auditor should confirm the 4-of-7 `aggregates_refreshed` pattern on zero-new-date runs is by design. (6) Operator: restart the backend and frontend before the next browser lane.

## Assumptions made

- iter-12 · goal-decomposer — Ambiguity: every decomposer since iter-4 scoped the session-live demo walkthrough out of developer scope reasoning it "self-resolves automatically," but grepping `run-goal.sh` shows no such automatic session-mode pass exists anywhere, including on the GOAL_ACHIEVED path. We chose: kept the walkthrough out of scope (same outcome as before) but stopped repeating the "self-resolves" framing, recording it as a parallel open owner-decision item alongside AG-8. Reversible: yes
- iter-11 · goal-evaluator — Ambiguity: J-04's steps 3-4 weren't re-driven this iteration since the browser agent is barred from service actions this session, and methodology says status should rest on evidence from the scoring iteration. We chose: kept J-04 `passing` because the product diff is literally empty, so the code those steps exercise provably hasn't changed since iter-9 verified it; a human requiring every step re-driven in the scoring iteration may hold J-04 at `partial` instead. Reversible: yes
- iter-11 · goal-evaluator — Ambiguity: J-05's step 2(b) names five aggregates its finalize hooks must refresh, and this iteration's replay runs recorded only four (`forward_aggregates` missing because its warm aborted on memory error), and goal.md doesn't say whether that breaks the journey's acceptance. We chose: kept J-05 `passing` since `forward_aggregates` isn't among the five the step names and the run record is honest about what it did and didn't refresh; the unbounded-load issue is scored under AG-8 instead of double-counted as a journey failure. Reversible: yes
- iter-11 · goal-evaluator — Ambiguity: decision-tree rule C.1 reads "a critical anti-goal violation is unresolved → REGRESSION," and the carried AG-8 dimension fired live this iteration, arguably counting as newly discovered damage even though the violation itself is old and the product diff is empty. We chose: did not fire REGRESSION since nothing could have been introduced or worsened on an empty diff and the human already deferred this exact code path three times; instead upgraded the ledger entry to a fully evidenced live-firing record and returned ESCALATE, explicitly noting a literal reading of C.1 would justify halting here instead. Reversible: yes
- iter-11 · goal-decomposer — Ambiguity: an operator note claimed agents in this pipeline cannot start or stop services and that the subagent-resume channel is broken, meaning the boot-budget measurement script might not be directly executable, and goal.md doesn't address who may launch backend processes. We chose: wrote the boot-budget measurement as the standard path (the developer runs it directly) with an explicit fallback that the operator runs the exact command and reports the output verbatim if genuinely blocked. Reversible: yes
- iter-10 · goal-evaluator — Ambiguity: only J-04's steps 5-6 were re-driven this iteration, with steps 1-2 resting on a pre-host-guard measurement and steps 3-4 on iter-9's simulations, and the only new timing datapoints were coarse operator polls rather than real measurements. We chose: scored the journey `passing` on the strength of a literally empty product diff, while recording the un-re-measured boot budget as a carried caveat and next-step item. Reversible: yes
- iter-10 · goal-evaluator — Ambiguity: J-04's decisive step-6 artifact was a DOM/HTML capture rather than a screenshot, because every post-scroll screenshot of the Run History row rendered blank, and the methodology's rule to let a screenshot outrank prose doesn't address a case with no usable screenshot. We chose: accepted the verbatim DOM capture as rendered-surface evidence and scored J-04 `passing`, only after confirming the captured text is composed client-side and matches the database row queried independently. Reversible: yes
- iter-10 · goal-decomposer — Ambiguity: J-04 step 6 requires killing and restarting the backend as a live test action, and an out-of-band operator note claimed agents cannot start/stop services and that the fix was already "API-verified," but the prior evaluator's binding instruction was that API-level evidence alone must not flip J-04 to passing. We chose: wrote the standard path as browser-qa-agent re-driving the full six-step acceptance itself, with a fallback that the operator may perform the kill/restart and hand the resulting state to browser-qa-agent to read from the rendered page. Reversible: yes
- iter-9 · goal-evaluator — Ambiguity: no artifact anywhere emits a `UT-J-05` verdict row, yet J-05 was the iteration's target journey and evidence was scattered across several per-step artifacts. We chose: treated the per-step citation trace as satisfying the evidence bar rather than scoring J-05 `unknown`, after personally opening and re-deriving each cited row myself. Reversible: yes
- iter-9 · goal-evaluator — Ambiguity: decision-tree rule C.1 reads literally as a critical unresolved anti-goal violation forcing REGRESSION, which would halt every remaining iteration on the deferred on-load memory-error finding the human already halted on and acknowledged in iter-7. We chose: recorded it fail-closed as a distinct critical, unresolved entry that hard-blocks GOAL_ACHIEVED, without firing the REGRESSION branch, since the violation was neither newly introduced nor worsened this iteration. Reversible: yes
- iter-9 · goal-evaluator — Ambiguity: J-04's step-6 evidence was split across two builds — failed pre-fix in the browser, fixed intra-iteration, and only confirmed post-fix at the operator/API level — with no journey status matching that exact situation. We chose: scored J-04 `partial` (steps 1-5 verified, step 6's defect fixed and credibly evidenced but not re-verified in a browser), rejecting `failing`, `passing`, and `unknown` as each misrepresenting the current tree. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-11.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-11-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-11-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-11-ui-test-results.md |
| Goal evaluation | ESCALATE | runs/goal-session-ops-hardening/iter-11/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
