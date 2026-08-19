# Goal Session Summary — ops-hardening

**Final verdict:** GOAL_ACHIEVED
**Total iterations:** 80
**Wall time (seconds):** 12320
**Quota pauses:** 0
**Started:** 2026-07-19T13:57:02.848410Z
**Finished:** 2026-08-14T02:07:10.133170Z

## Branch

This session pushed iteration commits to `goal/ops-hardening`. Open a PR with:

    gh pr create --base main --head goal/ops-hardening \
      --title "feat: ops-hardening — GOAL_ACHIEVED" \
      --body-file runs/goal-session-ops-hardening/summary.md

## Final journey state

| Journey | Status | Last passing iter |
|---|---|---|
| J-01 | passing | goal-ops-hardening-iter-79 |
| J-03 | passing | goal-ops-hardening-iter-79 |
| J-04 | passing | goal-ops-hardening-iter-79 |
| J-05 | passing | goal-ops-hardening-iter-79 |
| J-06 | passing | goal-ops-hardening-iter-79 |
| J-07 | passing | goal-ops-hardening-iter-79 |
| J-08 | passing | goal-ops-hardening-iter-79 |
| J-09 | passing | goal-ops-hardening-iter-79 |

## Anti-goal violations

- [critical] AG-3: A journey passes ONLY if the displayed numbers are correct — they match the engine's computation for the same as-of date — not merely that the page renders. (iter goal-ops-hardening-iter-1)
- [critical] AG-3: A journey passes ONLY if the displayed numbers are correct — they match the engine's computation for the same as-of date — not merely that the page renders. (iter goal-ops-hardening-iter-2)
- [minor] AG-3 (dimension): displayed numbers must be correct — a fetch that landed zero rows must not present as a success. (iter goal-ops-hardening-iter-2)
- [critical] AG-8 — Resilience to data-shape and data-scale change: widening the data basis must never crash an existing page or exhaust a service's memory; unbounded whole-table ORM loads are forbidden on the deep basis. (iter goal-ops-hardening-iter-7)
- [minor] AG-10 — Host resource ceiling (hardware protection): heavy compute MUST be launched only via the project launch scripts, which must apply the declared host caps. (iter goal-ops-hardening-iter-8)
- [critical] AG-8 (distinct dimension) — Resilience to data-shape and data-scale change: unbounded whole-table ORM materialization on the forward-aggregate warm path. (iter goal-ops-hardening-iter-9)
- [minor] AG-10 — Host resource ceiling: heavy compute (backfills, full-universe rebuilds, measurement passes) MUST be launched only via the project launch scripts. (iter goal-ops-hardening-iter-10)
- [critical] AG-8 (iter-9 forward_aggregates dimension) — observed-severity escalation: the unbounded load wedged the service on the deep basis. (iter goal-ops-hardening-iter-13)
- [minor] AG-10 — Host resource ceiling: heavy compute MUST be launched only via the project launch scripts (operator process lapse: raw uvicorn on a throwaway port; disclosed and corrected via start-backend.sh, no launch script modified). (iter goal-ops-hardening-iter-17)
- [minor] AG-8 — Resilience to data-shape and data-scale change: widening the data basis (deeper history) must never crash an existing page; the UI degrades gracefully, never a blank application-error page. (iter goal-ops-hardening-iter-26)
- [minor] AG-3: A journey passes ONLY if the displayed numbers are correct — they match the engine's computation for the same as-of date — not merely that the page renders. (iter goal-ops-hardening-iter-26)
- [minor] AG-8 - Resilience to data-shape and data-scale change: widening the data basis (deeper history) must never crash an existing page or exhaust a service's memory - the UI degrades gracefully (contained error boundary, honest '-'/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. (iter goal-ops-hardening-iter-27)
- [minor] AG-8 - Resilience to data-shape and data-scale change: widening the data basis must never crash an existing page or exhaust a service's memory - the UI degrades gracefully (contained error boundary, honest '-'/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. (iter goal-ops-hardening-iter-29)
- [minor] AG-8 - Resilience to data-shape and data-scale change: widening the data basis must never exhaust a service's memory; unbounded whole-table ORM loads are forbidden on the deep basis. (Also goal.md Success Criteria: 'No unbounded whole-table loads: no code path streams the full daily_prices table into RAM'.) (iter goal-ops-hardening-iter-29)
- [minor] AG-8 - Resilience to data-shape and data-scale change: widening the data basis must never exhaust a service's memory; unbounded whole-table ORM materialization is forbidden on the warm or serving path. (iter goal-ops-hardening-iter-29)
- [minor] goal.md Success Criteria + Compute-at-ingest constraint: 'No unbounded whole-table loads: no code path streams the full daily_prices table into RAM' (AG-8's deep-basis clause). (iter goal-ops-hardening-iter-29)
- [minor] AG-8 - Resilience to data-shape and data-scale change: widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory; unbounded whole-table ORM loads are forbidden on the deep basis. (iter goal-ops-hardening-iter-31)
- [minor] AG-8 - Resilience to data-shape and data-scale change: unbounded whole-table ORM loads are forbidden on the deep basis. (iter goal-ops-hardening-iter-32)
- [minor] AG-8 - Resilience to data-shape and data-scale change: widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory - every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest '-'/NA placeholder, never a blank application-error page). (iter goal-ops-hardening-iter-33)
- [minor] AG-8 - Resilience to data-shape and data-scale change: the UI degrades gracefully (contained error boundary, honest '-'/NA placeholder, never a blank application-error page). (iter goal-ops-hardening-iter-33)
- [minor] AG-10 - Host resource ceiling (hardware protection): heavy compute - backfills, full-universe rebuilds, measurement passes, load drills, test-suite bursts - MUST be launched only via the project launch scripts, and those scripts MUST apply the host caps declared in project-extensions/host-guard/host-guard.env whenever that file is present. (iter goal-ops-hardening-iter-33)
- [minor] J-07 step 2 (docs/goal.md, Must-have journeys) + the committed `GET /api/health` <= 0.1 s budget in reports/perf-budgets.md: 'While step 1 runs, poll GET /api/health once per second; assert every poll answers HTTP 200 within its existing budget - no frozen or unresponsive window.' (iter goal-ops-hardening-iter-34)
- [minor] AG-8 - Resilience to data-shape and data-scale change: widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory. Also J-07 step 3 (docs/goal.md, Must-have journeys): 'Record the process's peak memory (VmPeak) during step 1; assert it stays under the declared server.memory_cap_mb, with the margin recorded in reports/perf-budgets.md.' (iter goal-ops-hardening-iter-35)
- [minor] AG-8 - Resilience to data-shape and data-scale change: unbounded whole-table ORM loads are forbidden on the deep basis. Also docs/goal.md Success Criteria: 'No unbounded whole-table loads: no code path streams the full daily_prices table into RAM', and J-07's own Acceptance clause 'no unbounded whole-table ORM materialization remains on the warm or serving path'. (iter goal-ops-hardening-iter-36)
- [minor] AG-10 - Host resource ceiling (hardware protection): the ceilings are a physical constraint of the current host (repeated instant hardware resets under vectorized ingest bursts), not a performance budget to optimize away. Also AG-8's 'must never exhaust a service's memory' clause. (iter goal-ops-hardening-iter-36)
- [minor] AG-3: A journey passes ONLY if the displayed numbers are correct - they match the engine's computation for the same as-of date - not merely that the page renders. (iter goal-ops-hardening-iter-36)
- [minor] AG-8 — Resilience to data-shape and data-scale change: widening the data basis must never crash an existing page or exhaust a service's memory; unbounded whole-table ORM loads are forbidden on the deep basis. Also J-07 step 1 (docs/goal.md): 'trigger the forward-aggregate warm for every configured horizon (the ingest finalize path)' and step 4: re-verify the induced-pressure drill against the paths bounded by this iteration. (iter goal-ops-hardening-iter-37)
- [minor] AG-8 — Resilience to data-shape and data-scale change: widening the data basis must never crash an existing page or exhaust a service's memory. (J-07's own headline: heavy aggregates never take the service down.) (iter goal-ops-hardening-iter-37)
- [minor] AG-8 — Resilience to data-shape and data-scale change: ... the UI degrades gracefully (contained error boundary, honest '—'/NA placeholder, never a blank application-error page). Also J-07 step 4: the SAME process 'keeps serving GET /api/health and previously cached reads'. (iter goal-ops-hardening-iter-37)
- [minor] docs/goal.md Success Criteria ('measured, recorded in reports/perf-budgets.md') + .claude/core.md evidence honesty: a number presented as measured must be the number the instrument actually produced. (iter goal-ops-hardening-iter-38)
- [minor] docs/goal.md J-07 step 4 (verbatim): 'Induce memory pressure during a warm (test hook or a tightened cap in a throwaway process); assert the warm aborts honestly per the existing isolation convention while the SAME process keeps serving GET /api/health and previously cached reads - never a deadlock, wedge, or restart requirement.' (iter goal-ops-hardening-iter-38)
- [minor] docs/goal.md Must-have user journeys (the required-still-passing set must stay green) + the iteration spec's TC-11 ('zero FAIL rows and zero reconciliation overturns'). (iter goal-ops-hardening-iter-38)
- [minor] docs/goal.md J-07 Acceptance (verbatim): 'a memory-pressure abort never leaves the process wedged (step 4)'; and AG-8 - Resilience to data-shape and data-scale change: widening the data basis must never exhaust a service's memory. (iter goal-ops-hardening-iter-39)
- [minor] AG-8 - Resilience to data-shape and data-scale change: unbounded whole-table ORM loads are forbidden on the deep basis; and docs/goal.md J-07 Acceptance: 'no unbounded whole-table ORM materialization remains on the warm or serving path'. (iter goal-ops-hardening-iter-39)
- [minor] AG-3: A journey passes ONLY if the displayed numbers are correct - they match the engine's computation for the same as-of date - not merely that the page renders. (iter goal-ops-hardening-iter-39)
- [minor] docs/goal.md Must-have user journeys (the required-still-passing set must stay green) - the evidence artifacts the evaluator reads must not report a run as passing when its journeys were never verified. (iter goal-ops-hardening-iter-39)
- [minor] docs/goal.md Must-have user journeys — the required-still-passing set must stay green, and the evidence artifacts must actually carry that claim (same family as iter-38/t and iter-39/x) (iter goal-ops-hardening-iter-40)
- [minor] docs/goal.md Must-have user journeys - the evidence artifacts the evaluator reads must not report a run as passing when its journeys were never verified (same family as iter-38/t, iter-39/x, iter-40/y). (iter goal-ops-hardening-iter-41)
- [minor] docs/goal.md Must-have user journeys - a guard written to prevent a specific past failure must actually be tested against that failure's own artifact. (iter goal-ops-hardening-iter-41)
- [minor] AG-8 - Resilience to data-shape and data-scale change: unbounded whole-table ORM loads are forbidden on the deep basis. (critical anti-goal; this entry records an inaccurate CLAIM about it, not a new violation) (iter goal-ops-hardening-iter-41)
- [minor] AG-8 - Resilience to data-shape and data-scale change: widening the data basis ... must never crash an existing page or exhaust a service's memory ... unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)* (iter goal-ops-hardening-iter-42)
- [minor] AG-8 - Resilience to data-shape and data-scale change: widening the data basis ... must never crash an existing page or exhaust a service's memory. *(critical)* (iter goal-ops-hardening-iter-42)
- [minor] AG-8 (critical) + docs/goal.md Success Criteria: 'Backend process start -> first GET /api/health HTTP 200 in <= 5 seconds' and 'Zero silent zero-work jobs: every job outcome shows date counts and per-date exclusion reasons'. (iter goal-ops-hardening-iter-42)
- [minor] AG-8 - Resilience to data-shape and data-scale change: widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory ... (critical) - here the 'never take the service down' half, plus docs/goal.md J-07 acceptance 'a memory-pressure abort never leaves the process wedged' (iter goal-ops-hardening-iter-43)
- [minor] docs/goal.md J-07 step 2 + the owner's 2026-07-31 rescoped GET /api/health budget ('during a bounded background-compute window ... every poll answers HTTP 200 under a relaxed <=2s ceiling') (iter goal-ops-hardening-iter-43)
- [minor] Framework honesty rail (.claude/core.md / judgment-rubrics.md): every claim cites evidence; a lane must not report a criterion PASS against another criterion's evidence, nor 'no blockers' over its own populated blockers[] (iter goal-ops-hardening-iter-43)
- [minor] Framework evidence rail (goal-evaluation-methodology A.3): a journey's cited screenshot must show that journey's acceptance state (iter goal-ops-hardening-iter-43)
- [minor] docs/goal.md Success Criteria: 'Zero silent zero-work jobs: every job outcome shows date counts and per-date exclusion reasons, persisted across page reloads' (iter goal-ops-hardening-iter-43)
- [minor] AG-8 - Resilience to data-shape and data-scale change: ... must never crash an existing page or exhaust a service's memory (critical) - the 'never take the service down' half; plus docs/goal.md J-07 acceptance 'a memory-pressure abort never leaves the process wedged' and this iteration's own DoD TC-2/TC-7 (iter goal-ops-hardening-iter-44)
- [minor] docs/goal.md Success Criteria: 'No unbounded whole-table loads: no code path streams the full daily_prices table into RAM; ingest-maintained aggregates serve every heavy read' + AG-8's unbounded-load ban (iter goal-ops-hardening-iter-44)
- [minor] docs/goal.md J-07 acceptance: 'a memory-pressure abort never leaves the process wedged' - the _refresh_ingest_aggregates 'log + continue, never raise' contract (iter goal-ops-hardening-iter-44)
- [minor] docs/goal.md Success Criteria: 'Zero silent zero-work jobs: every job outcome shows date counts and per-date exclusion reasons, persisted across page reloads' (iter goal-ops-hardening-iter-44)
- [minor] AG-8 - Resilience to data-shape and data-scale change: widening the data basis ... must never crash an existing page or exhaust a service's memory (critical) (iter goal-ops-hardening-iter-45)
- [minor] AG-8 - ... unbounded whole-table ORM loads are forbidden on the deep basis (critical) + J-05 acceptance: 'no code path streams the full daily_prices table into RAM (AG-8's unbounded-load ban enforced on serving paths)' (iter goal-ops-hardening-iter-45)
- [critical] AG-3: A journey passes ONLY if the displayed numbers are correct - they match the engine's computation for the same as-of date (critical) (iter goal-ops-hardening-iter-45)
- [minor] Iteration spec TC-11 + docs/goal.md AG-3 evidence discipline: 'an md5sum check over the evidence directory confirms no two journeys share one screenshot file (closes/keeps closed iter-43/ai)' (iter goal-ops-hardening-iter-45)
- [minor] docs/goal.md J-07 acceptance: 'a memory-pressure abort never leaves the process wedged' - the log-and-continue contract for failure handlers that run under pressure (iter goal-ops-hardening-iter-45)
- [minor] AG-8 - Resilience to data-shape and data-scale change: '... unbounded whole-table ORM loads are forbidden on the deep basis' + goal.md Success Criteria 'No unbounded whole-table loads' (iter goal-ops-hardening-iter-46)
- [minor] goal.md Success Criteria: 'Page loads stay within committed never-regress budgets in reports/perf-budgets.md' + J-06 acceptance (iter goal-ops-hardening-iter-46)
- [minor] docs/goal.md J-07 acceptance: 'a memory-pressure abort never leaves the process wedged' + the module-wide isolation-logging convention (iter goal-ops-hardening-iter-46)
- [minor] goal.md Success Criteria: 'Backend process start -> first GET /api/health HTTP 200 in <= 5 seconds on the warm committed-seed DB' + J-04 step 2 (iter goal-ops-hardening-iter-46)
- [minor] AG-8 - '... the UI degrades gracefully (contained error boundary, honest '--'/NA placeholder, never a blank application-error page)' (iter goal-ops-hardening-iter-46)
- [minor] goal.md Success Criteria: 'Zero silent zero-work jobs: every job outcome shows date counts and per-date exclusion reasons' + J-01 zero-work honesty (iter goal-ops-hardening-iter-46)
- [minor] Framework honesty rail (.claude/core.md / judgment-rubrics.md): a lane may not record a DoD item as met without the evidence its acceptance names (iter goal-ops-hardening-iter-46)
- [minor] AG-8 — Resilience to data-shape and data-scale change: '... must never crash an existing page or exhaust a service's memory' (iter goal-ops-hardening-iter-47)
- [minor] AG-8 — Resilience to data-shape and data-scale change: '... must never crash an existing page or exhaust a service's memory' (iter goal-ops-hardening-iter-47)
- [minor] AG-8 — '... unbounded whole-table ORM loads are forbidden on the deep basis' (critical) / J-06 acceptance: page loads within committed budgets (iter goal-ops-hardening-iter-47)
- [minor] goal.md Additional binding notes (owner amendment 2026-07-31): 'During a bounded background-compute window ... every poll answers HTTP 200 under a relaxed <=2 s ceiling' / J-07 step 2 (iter goal-ops-hardening-iter-47)
- [minor] Framework honesty rail (.claude/core.md / judgment-rubrics.md) + this iteration's own TC-7/TC-8: a journey may not be scored on evidence that predates the build it describes (iter goal-ops-hardening-iter-47)
- [minor] AG-9 — Offline-deterministic ingest: 'ingest jobs (fetch/backfill/rebuild) run only against the committed seed / local provider fixtures — no live external network calls ... may be introduced without an explicit goal.md amendment' (critical) (iter goal-ops-hardening-iter-47)
- [minor] docs/goal.md J-09 step 3: the background-activity field names 'what is running ... never a bare Ready that hides it' (iter goal-ops-hardening-iter-47)
- [minor] docs/goal.md J-05 acceptance + this iteration's own GOAL: 'a historical-day backfill ... reaches a real, honest outcome ... instead of appearing to run forever' (iter goal-ops-hardening-iter-48)
- [minor] AG-8 — '... must never crash an existing page or exhaust a service's memory' / 'unbounded whole-table ORM loads are forbidden on the deep basis' (critical) (iter goal-ops-hardening-iter-48)
- [minor] This iteration's own TC-7 + framework honesty rail: 'the full 8-journey browser-qa/replay pass is the LAST product-code-adjacent event before this iteration is scored' (iter goal-ops-hardening-iter-48)
- [minor] Framework evidence rail (.claude/core.md): every claim cites evidence; a screenshot must show the state it is offered as proof of (iter goal-ops-hardening-iter-48)
- [minor] docs/goal.md J-07 acceptance: 'the crash-free warm + healthy /api/health sequence appended as [NEW] steps viewable via demo.sh ops-hardening --session-live' (iter goal-ops-hardening-iter-48)
- [minor] Framework honesty rail (.claude/core.md / judgment-rubrics.md): a lane may not issue a verdict before the evidence its acceptance names exists (iter goal-ops-hardening-iter-48)
- [minor] AG-8 — 'widening the data basis ... must never crash an existing page or exhaust a service's memory ... unbounded whole-table ORM loads are forbidden on the deep basis' (critical) (iter goal-ops-hardening-iter-49)
- [minor] docs/goal.md J-07 step 2 + the owner's 2026-07-31 amendment: 'during a bounded background-compute window every poll answers HTTP 200 under a relaxed <=2 s ceiling' (iter goal-ops-hardening-iter-49)
- [minor] This iteration's own TC-7 + framework honesty rail: 'the full 8-journey browser-qa/replay pass is the LAST product-code-adjacent event before scoring; any later fix pass forces a re-run' (iter goal-ops-hardening-iter-49)
- [minor] Framework evidence rail (.claude/core.md): every claim cites evidence; a screenshot must show the state it is offered as proof of (iter goal-ops-hardening-iter-49)
- [minor] Framework honesty rail (.claude/core.md / judgment-rubrics.md): a lane's verdict must be consistent with the artifacts it cites (iter goal-ops-hardening-iter-49)
- [minor] Framework evidence rail (.claude/core.md): a report's causal attribution must match the artifact it is derived from (iter goal-ops-hardening-iter-49)
- [minor] docs/goal.md J-05 + J-07 acceptance: 'a [NEW]-flagged walkthrough ... viewable via demo.sh ops-hardening --session-live' (iter goal-ops-hardening-iter-49)
- [minor] Binding iter-48 lesson + this iteration's TC-8: 'a journey's PASS must rest on a row the work itself caused' (iter goal-ops-hardening-iter-49)
- [minor] AG-8 - Resilience to data-shape and data-scale change: widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory (iter goal-ops-hardening-iter-50)
- [minor] Iteration spec TC-13 / DoD item 7: the full 8-journey browser/replay lane is the LAST product-code-adjacent event before this iteration is scored (iter goal-ops-hardening-iter-50)
- [minor] Iteration spec NOTES (QA report discipline): if any pass changes product code after the browser lane has run, the QA report must be regenerated from that re-run, never hand-edited (iter goal-ops-hardening-iter-50)
- [minor] Iteration spec DoD item 4: required-still-passing journeys each produce a real executed row (PASS or FAIL, never SKIP/blank); target journeys are verified (iter goal-ops-hardening-iter-50)
- [minor] goal.md J-05/J-06/J-07 acceptance: a [NEW]-flagged walkthrough viewable via demo.sh ops-hardening --session-live (iter goal-ops-hardening-iter-50)
- [minor] goal.md Constraint 'Compute-at-ingest': heavy aggregation happens inside ingest jobs and is persisted; request paths serve stored values (iter goal-ops-hardening-iter-50)
- [minor] AG-8 - unbounded whole-table ORM loads are forbidden on the deep basis; a memory-pressure abort never leaves the process wedged (iter goal-ops-hardening-iter-50)
- [minor] goal.md AG-8 (critical) / owner amendment: during a bounded background-compute window every GET /api/health poll must answer HTTP 200 under a relaxed <=2s ceiling; 'a frozen or unresponsive window, any non-200, or an untruthful readiness value remains a failure' (iter goal-ops-hardening-iter-51)
- [minor] goal.md loop discipline / .claude/judgment-rubrics.md honesty floor: a Definition-of-Done checkbox and a lane verdict must not be recorded as met when the cited artifacts show otherwise (iter goal-ops-hardening-iter-51)
- [minor] goal.md Must-have user journeys: each iteration's target journeys must be scored against executed evidence; required-still-passing journeys must remain verified (iter goal-ops-hardening-iter-51)
- [minor] goal.md Design Direction / evidence discipline: a cited screenshot must show the state it is cited for (iter goal-ops-hardening-iter-51)
- [minor] goal.md J-07 acceptance: 'the crash-free warm + healthy /api/health sequence appended as [NEW] steps viewable via demo.sh ops-hardening --session-live' (iter goal-ops-hardening-iter-51)
- [minor] goal.md Loop mechanics / iteration spec TC-9: the 8-journey browser/replay lane must run LAST, with no product-code change afterward (iter goal-ops-hardening-iter-52)
- [minor] goal.md Success Criteria / iteration spec Definition of Done: a DoD checkbox must be true when it is checked (iter goal-ops-hardening-iter-52)
- [minor] goal.md J-06 'Pages load only what they need' step 1 / iter-46-47 null-test-golden lesson: a golden must assert the journey's behaviour, not page-shell text (iter goal-ops-hardening-iter-52)
- [minor] goal.md J-04/J-05/J-06/J-07 'Walkthrough' acceptance clause: a [NEW]-flagged walkthrough must be viewable via demo.sh (iter goal-ops-hardening-iter-52)
- [minor] AG-8 -- Resilience to data-shape and data-scale change: widening the data basis must never crash an existing page or exhaust a service's memory (iter goal-ops-hardening-iter-52)
- [minor] AG-3: a journey passes ONLY if the displayed numbers are correct -- they match the engine's computation for the same as-of date (iter goal-ops-hardening-iter-53)
- [minor] goal.md Success Criteria / iteration spec Definition of Done: a DoD checkbox must be true when it is checked, and a lane's negative verdict must not be silently overridden (iter goal-ops-hardening-iter-53)
- [minor] ops-hardening iter-41/B2 + iter-42 fix: promoting a journey to an iteration's own target must not silently remove its verification (iter goal-ops-hardening-iter-53)
- [minor] .claude/core.md honesty baseline: a handoff must disclose what it removed, not only what it added (iter goal-ops-hardening-iter-53)
- [minor] apps/backend/app/engine/data_manager.py:3248-3250 _FAULT_INJECT_SITES contract: each site 'is the exact per-item boundary whose except MemoryError handler J-07's acceptance names' (iter goal-ops-hardening-iter-53)
- [minor] goal.md J-04/J-05/J-06/J-07 'Walkthrough' acceptance clause: a [NEW]-flagged walkthrough must be viewable via demo.sh (iter goal-ops-hardening-iter-53)
- [minor] AG-8 -- unbounded whole-table/whole-history ORM loads are forbidden on the deep basis, especially on serving paths (iter goal-ops-hardening-iter-53)
- [minor] AG-3 -- a journey passes ONLY if the displayed numbers are correct, and AG-8's honest-status clause: the UI/persisted record must tell the truth about what actually happened. (iter goal-ops-hardening-iter-54)
- [minor] AG-8 -- widening the data basis must never exhaust a service's memory; and the evidence-honesty convention (a lane must not explain away a signal it did not check). (iter goal-ops-hardening-iter-54)
- [minor] Iteration Definition of Done / TC-7: 'given journey-scripts/J-05.json already exists, when this iteration's regression-replay lane runs, then it is EXECUTED (not skipped) and its result row appears in regression-replay-results.md for J-05.' (iter goal-ops-hardening-iter-54)
- [minor] Pipeline-depth integrity: the iteration spec's own machine-readable metadata binds the depth the engine runs. (iter goal-ops-hardening-iter-54)
- [minor] Iteration Definition of Done: 'B2 fixed: the fault-injection site's name matches the phase it fires from, verified by a live drill that isolates the named phase using this site' (TC-6's live GET /api/health-after-fault clause). (iter goal-ops-hardening-iter-54)
- [minor] J-06 acceptance step 2: 'Record the measurements in the committed budgets table reports/perf-budgets.md ... and assert every measurement is within budget.' (iter goal-ops-hardening-iter-54)
- [minor] AG-3/AG-8 evidence-honesty: a lane's blocking verdict must not be overridden downstream by a report citing rows that do not exist. (iter goal-ops-hardening-iter-55)
- [minor] Iteration Definition of Done items 1 and 7 (TC-8/TC-9): 'journey-scripts/J-05.json, J-04.json, J-07.json each produce a real executed row (never SKIPPED/BLOCKED) in regression-replay-results.md this iteration'. (iter goal-ops-hardening-iter-55)
- [minor] Verification-fixture integrity: a single-use golden's target date must be rotated after it is consumed, or the next replay fails for a non-product reason. (iter goal-ops-hardening-iter-55)
- [minor] Iteration Definition of Done / spec line 44: 'profile the per-horizon compute call chain ... do not assume the cause or force-fit a prior iteration's specific mechanism' (binding iter-48/50/53 profile-first discipline). (iter goal-ops-hardening-iter-55)
- [minor] Iteration Definition of Done / TC-5: 'a live, >=1,800-poll (1 Hz) concurrent health drill spanning forward_aggregates_warm records zero connection-level non-answers (http_code=000), down from the iter-54 baseline of 6/1,821'. (iter goal-ops-hardening-iter-55)
- [minor] Evidence hygiene: distinct assertions must not be evidenced by one image. (iter goal-ops-hardening-iter-55)
- [minor] J-05/J-07 acceptance 'Walkthrough: a [NEW]-flagged walkthrough ... viewable via demo.sh ops-hardening --session-live'; capture-only, never an iteration goal. (iter goal-ops-hardening-iter-55)
- [minor] Iteration Definition of Done: 'Unit tests pass; no regressions'. (iter goal-ops-hardening-iter-55)
- [minor] AG-8 / goal.md vision: 'the UI tells the truth about the backend's own state' and 'the UI degrades gracefully (contained error boundary, honest —/NA placeholder)'. (iter goal-ops-hardening-iter-56)
- [minor] Iteration spec Goal Mode Metadata: '**Depth:** full' with an explicit 'Full trigger: 1' justification. (iter goal-ops-hardening-iter-56)
- [minor] J-06 acceptance step 2: 'assert every measurement is within budget' - a lane must not report a measurement as in-budget when its own recorded number exceeds the committed ceiling. (iter goal-ops-hardening-iter-56)
- [minor] Iteration Definition of Done: 'Unit tests pass; no regressions'. (iter goal-ops-hardening-iter-56)
- [minor] AG-8 honest status: a run record must not report an aggregate as refreshed unless it was. (iter goal-ops-hardening-iter-56)
- [minor] Evidence hygiene: a committed measurement record must describe what it measured. (iter goal-ops-hardening-iter-56)
- [minor] Verification integrity: a golden must assert the journey's acceptance, never a bare page-title/heading match (the standard J-04.json's own name sets). (iter goal-ops-hardening-iter-56)
- [minor] Canonical values (single source of truth): a value must have one computing module. (iter goal-ops-hardening-iter-56)
- [minor] AG-9 — Offline-deterministic ingest: 'ingest jobs (fetch/backfill/rebuild) run only against the committed seed / local provider fixtures — no live external network calls ... may be introduced without an explicit goal.md amendment' (critical) (iter goal-ops-hardening-iter-57)
- [minor] Verification integrity: a committed measurement record must not state the opposite of its own raw log. (iter goal-ops-hardening-iter-57)
- [minor] AG-3 / honest status: a status message must not assert a condition the system has not observed. (iter goal-ops-hardening-iter-57)
- [minor] AG-8 honest degradation: the false 'no data' empty state must be reachable only when the data genuinely does not exist. (iter goal-ops-hardening-iter-57)
- [minor] AG-8 — Resilience to data-scale change: 'must never crash an existing page or exhaust a service's memory ... unbounded whole-table ORM loads are forbidden on the deep basis' (critical anti-goal; this instance scored minor, see grounds) (iter goal-ops-hardening-iter-57)
- [minor] Verification integrity (TC-12, partially met): a golden must assert the journey's committed budget, not a looser proxy. (iter goal-ops-hardening-iter-57)
- [minor] Documentation honesty: a docstring must not assert the opposite of the shipped, tested behavior. (iter goal-ops-hardening-iter-57)
- [minor] Evidence hygiene: each test row's screenshot must show that row's own asserted state. (iter goal-ops-hardening-iter-57)
- [minor] Evidence hygiene: a walkthrough step must record the frame it names. (iter goal-ops-hardening-iter-57)
- [minor] Iteration Definition of Done (TC-13): 'test_api_runs.py runs alone, first, and completes with its result recorded'. (iter goal-ops-hardening-iter-57)
- [minor] Test integrity: a test written to prove a claim must actually execute. (iter goal-ops-hardening-iter-57)
- [minor] J-06 acceptance step 2: 'assert every measurement is within budget' — a measurement taken must be recorded and resolved, not left in prose. (iter goal-ops-hardening-iter-57)
- [minor] Verification integrity: a committed measurement record must not state the opposite of its own raw log. (iter goal-ops-hardening-iter-58)
- [minor] Verification integrity: a slow or failed sample must be counted, never re-labelled as a boundary artifact. (iter goal-ops-hardening-iter-58)
- [minor] Evidence hygiene: each test row's screenshot must show that row's own asserted state. (iter goal-ops-hardening-iter-58)
- [minor] Journey-scoring integrity: a results headline must not report closure the journey's own steps did not reach. (iter goal-ops-hardening-iter-58)
- [minor] Pipeline discipline: an iteration must run at the depth its own spec declares. (iter goal-ops-hardening-iter-58)
- [minor] AG-8 — Resilience to data-scale change: 'must never ... exhaust a service's memory ... unbounded whole-table ORM loads are forbidden on the deep basis'. (iter goal-ops-hardening-iter-58)
- [minor] Honest degradation: an aborted heavy compute must record WHY it aborted. (iter goal-ops-hardening-iter-58)
- [minor] AG-3: 'A journey passes ONLY if the displayed numbers are correct - they match the engine's computation for the same as-of date'. (critical) (iter goal-ops-hardening-iter-59)
- [minor] AG-8 - Resilience to data-scale change: 'unbounded whole-table ORM loads are forbidden on the deep basis'. (critical) (iter goal-ops-hardening-iter-59)
- [minor] Verification integrity: a QA verdict artifact must not state things its own inputs contradict. (iter goal-ops-hardening-iter-59)
- [minor] Evidence hygiene: each test row's screenshot must show that row's own asserted state. (iter goal-ops-hardening-iter-59)
- [minor] Verification integrity: a results file must not claim a repair that was not made. (iter goal-ops-hardening-iter-59)
- [minor] J-07 acceptance step 2: 'assert every poll answers HTTP 200 within its existing budget' (owner amendment: relaxed <=2s during a bounded background-compute window). (iter goal-ops-hardening-iter-59)
- [minor] Framework/verification coverage: an iteration's TARGET journeys must be verified by a lane. (iter goal-ops-hardening-iter-59)
- [minor] Iteration Definition of Done item 8: a [NEW]-flagged walkthrough recorded via demo.sh --session-live. (iter goal-ops-hardening-iter-59)
- [minor] Measurement integrity: a bound shipped for memory must be measured against a pre-fix counterpart. (iter goal-ops-hardening-iter-59)
- [minor] Framework/tooling: the closure gate's backend-only claim guard must not block on a keyword match. (iter goal-ops-hardening-iter-59)
- [minor] Framework durability: the audit-hardening loop's own input artifact must survive the loop. (iter goal-ops-hardening-iter-59)
- [minor] AG-3: 'A journey passes ONLY if the displayed numbers are correct - they match the engine's computation for the same as-of date' (critical) (iter goal-ops-hardening-iter-60)
- [minor] Framework/verification coverage: an iteration's TARGET journeys must be verified by a lane that actually executes them. (iter goal-ops-hardening-iter-60)
- [minor] Verification integrity: a review verdict must not record 'definition_of_done: complete' over an unmet DoD item. (iter goal-ops-hardening-iter-60)
- [minor] UI evolution: a user-visible change must be shown rendering before it is claimed done. (iter goal-ops-hardening-iter-60)
- [minor] Process: the dispatched depth must match the iteration spec's declared depth. (iter goal-ops-hardening-iter-60)
- [minor] Measurement integrity: a drill must publish its raw artifact, its window, and its slowest answer - not only a success count. (iter goal-ops-hardening-iter-60)
- [minor] Verification integrity: a results headline must not overstate what its own rows say. (iter goal-ops-hardening-iter-60)
- [minor] Verification integrity: every journey an iteration targets must actually be executed by some lane. (iter goal-ops-hardening-iter-61)
- [minor] Diagnostic integrity: a defect must be confirmed against a common clock before a round is spent fixing it. (iter goal-ops-hardening-iter-61)
- [minor] Reporting integrity: a headline must be re-derived from the artifact it summarizes. (iter goal-ops-hardening-iter-61)
- [minor] Walkthrough acceptance: J-05 and J-07 each carry a [NEW]-flagged walkthrough clause. (iter goal-ops-hardening-iter-61)
- [minor] Evidence hygiene: one screenshot must not be cited as three distinct pieces of evidence. (iter goal-ops-hardening-iter-61)
- [minor] AG-10 evidence: a host-cap compliance claim must be backed by the artifact it cites. (iter goal-ops-hardening-iter-61)
- [minor] Honest status: GET /api/health advertises last_run_date but always returns null. (iter goal-ops-hardening-iter-61)
- [minor] Test coverage: a shipped behaviour change must have some automated protection. (iter goal-ops-hardening-iter-61)
- [minor] AG-3: A journey passes ONLY if the displayed numbers are correct (evidence-integrity corollary: a cited frame must show what its row claims) (iter goal-ops-hardening-iter-62)
- [minor] AG-8: honest degrade / never a false failure state (verification-substrate corollary) (iter goal-ops-hardening-iter-62)
- [minor] AG-3: displayed numbers correct (golden-integrity corollary: an assertion must follow THIS run's own row) (iter goal-ops-hardening-iter-62)
- [minor] Framework honesty: a documented command must actually run (iter goal-ops-hardening-iter-62)
- [minor] AG-8: the UI degrades gracefully and honestly (iter goal-ops-hardening-iter-62)
- [minor] AG-3: displayed numbers correct (unverifiable-disclosure corollary) (iter goal-ops-hardening-iter-62)
- [minor] AG-3 / J-07 acceptance: the promise the journey measures got worse, with no explanation (iter goal-ops-hardening-iter-63)
- [minor] Framework honesty: a showcase lane must not mutate the dataset, and its narration must match what happened (iter goal-ops-hardening-iter-63)
- [minor] AG-3 golden-integrity corollary: an assertion pinned to a date the same round consumes is a false failure waiting to fire (iter goal-ops-hardening-iter-63)
- [minor] Framework honesty: a summary must not contradict the file it summarises (iter goal-ops-hardening-iter-63)
- [minor] Test honesty: a test's docstring must describe what the test asserts (iter goal-ops-hardening-iter-63)
- [minor] Verification substrate: a gate whose budget is shorter than the condition it guards can still expire (iter goal-ops-hardening-iter-63)
- [minor] Spec compliance: a named error case must actually be executed (iter goal-ops-hardening-iter-63)
- [minor] AG-8: the UI degrades gracefully and honestly (never an unexplained page-level render error) (iter goal-ops-hardening-iter-64)
- [minor] AG-3 / J-07 acceptance: the promise the journey measures got worse again, and for the first time a health check went unanswered (iter goal-ops-hardening-iter-64)
- [minor] Framework honesty: a note must describe the code it documents (iter goal-ops-hardening-iter-64)
- [minor] AG-3 job-history integrity corollary: one job must produce one persisted run record (iter goal-ops-hardening-iter-64)
- [minor] Framework honesty: a lane verdict must not claim work that no lane ran (iter goal-ops-hardening-iter-64)
- [minor] Loop economy: an iteration must fit its own wall-clock budget (iter goal-ops-hardening-iter-64)
- [minor] Measurement integrity: a journey's acceptance number must not depend on which counter measured it (iter goal-ops-hardening-iter-65)
- [minor] Loop economy: an iteration must fit its own wall-clock budget (iter goal-ops-hardening-iter-65)
- [minor] Supply-chain policy: the install-decision hook must evaluate every install command it is handed (iter goal-ops-hardening-iter-65)
- [minor] Evidence framing: a screenshot must show the state its own results row claims (iter goal-ops-hardening-iter-65)
- [minor] Reporting honesty: a handoff's own summary must carry the number its addendum discloses (iter goal-ops-hardening-iter-66)
- [minor] Measurement integrity: an explanation must be supported by the data offered for it (iter goal-ops-hardening-iter-66)
- [minor] Reporting accuracy: a breach must be attributed to the phase whose window actually contains it (iter goal-ops-hardening-iter-66)
- [minor] Measurement integrity: a cross-check must compare timestamps in the same timezone and the same process (iter goal-ops-hardening-iter-66)
- [minor] Evidence framing: a screenshot must show the state its own results row claims (iter goal-ops-hardening-iter-66)
- [minor] Framework honesty: a lane verdict must record the acceptance bar its own iteration missed (iter goal-ops-hardening-iter-66)
- [minor] Loop economy: an iteration must fit its own wall-clock budget (iter goal-ops-hardening-iter-66)
- [minor] Reporting accuracy: a timing sample must be attributed to the phase whose window actually contains it (iter goal-ops-hardening-iter-67)
- [minor] Measurement integrity: a conclusion must account for the distribution, not only the threshold crossings (iter goal-ops-hardening-iter-67)
- [minor] Measurement integrity: every lane must measure a shared claim with the shared instrument (iter goal-ops-hardening-iter-67)
- [minor] Reporting accuracy: a lane must not describe code changes the iteration did not make (iter goal-ops-hardening-iter-67)
- [minor] Framework honesty: a review verdict must record the test gap its own iteration disclosed (iter goal-ops-hardening-iter-67)
- [minor] Measurement integrity: an instrument must disclose how it perturbs what it measures (iter goal-ops-hardening-iter-67)
- [minor] Loop economy: an iteration must fit its own wall-clock budget (iter goal-ops-hardening-iter-67)
- [minor] AG-3 / evidence honesty: a results row must not claim more than its own screenshot shows (iter goal-ops-hardening-iter-68)
- [minor] Measurement completeness: a residual must not be called unnamed when the artifacts already on disk name most of it (iter goal-ops-hardening-iter-68)
- [minor] Measurement integrity: an instrument must disclose how it perturbs what it measures (iter goal-ops-hardening-iter-68)
- [minor] Instrument coverage: the lane most likely to catch the failure ran without the instrument built to explain it (iter goal-ops-hardening-iter-68)
- [minor] Loop economy: an iteration must fit its own wall-clock budget (iter goal-ops-hardening-iter-68)
- [minor] Measurement completeness: a round must group its own breaches by the phase they fall in before offering an external explanation for them (iter goal-ops-hardening-iter-69)
- [minor] Measurement integrity: a join's own description must match the record counts it actually worked with (iter goal-ops-hardening-iter-69)
- [minor] AG-3 / evidence honesty: a correction must itself be correct (iter goal-ops-hardening-iter-69)
- [minor] J-07 step 2 / AG-8: every health poll must be answered while heavy aggregates run -- no unresponsive window (iter goal-ops-hardening-iter-69)
- [minor] Instrument coverage: the lane most likely to catch the failure ran without the instrument built to explain it (iter goal-ops-hardening-iter-69)
- [minor] Loop economy: an iteration must fit its own wall-clock budget (iter goal-ops-hardening-iter-69)
- [minor] Honesty of pipeline artifacts: a report must not assert verification it does not have (iter goal-ops-hardening-iter-70)
- [minor] Verification coverage: every iteration must leave journey-level evidence (iter goal-ops-hardening-iter-70)
- [minor] J-07 step 2 measurement coverage: the acceptance drill must cover the whole job window (iter goal-ops-hardening-iter-70)
- [minor] AG-3 (displayed numbers correct): a new silent failure mode was introduced (iter goal-ops-hardening-iter-70)
- [minor] J-07 Walkthrough acceptance clause: the crash-free warm sequence must be viewable via demo.sh (iter goal-ops-hardening-iter-70)
- [minor] Loop economy: an iteration must fit its own wall-clock budget (iter goal-ops-hardening-iter-70)
- [minor] J-04/J-06 measurement conditions: prod mode via scripts/start-backend.sh, never dev.sh (iter goal-ops-hardening-iter-71)
- [minor] goal.md binding note: launch scripts must enforce the declared caps and write a persistent backend logfile (iter goal-ops-hardening-iter-71)
- [minor] J-07: heavy aggregates never take the service down; no frozen or unresponsive window (iter goal-ops-hardening-iter-71)
- [minor] Iter-71 spec TC-5: the drill's first poll must precede the job start command by >= 2 s (iter goal-ops-hardening-iter-71)
- [minor] Evidence citations must be openable and must contain what they are cited for (iter goal-ops-hardening-iter-71)
- [minor] Each journey's Walkthrough clause: viewable via demo.sh ops-hardening --session-live (iter goal-ops-hardening-iter-71)
- [minor] Loop economy: an iteration must fit its own wall-clock budget (iter goal-ops-hardening-iter-71)
- [minor] J-06 steps 2-3: record measurements in reports/perf-budgets.md and a code-level on-load audit in the handoff (iter goal-ops-hardening-iter-71)
- [minor] AG-10 / J-07 step 3: peak process memory must be measured against the declared server.memory_cap_mb with the margin recorded in reports/perf-budgets.md (iter goal-ops-hardening-iter-72)
- [minor] DoD item 8 / TC-10: the /data honest-fallback screenshot must be filed as evidence (iter goal-ops-hardening-iter-72)
- [minor] The deterministic replay lane must provide a trustworthy regression baseline, and a lane's 'false positive'/'transient' label must be checked against the actual frame (iter goal-ops-hardening-iter-72)
- [minor] Each journey's Walkthrough clause: viewable via demo.sh ops-hardening --session-live (iter goal-ops-hardening-iter-72)
- [minor] Loop economy: an iteration must fit its own wall-clock budget (iter goal-ops-hardening-iter-72)
- [minor] goal.md vision: the UI tells the truth about the backend's own state (iter goal-ops-hardening-iter-72)
- [minor] J-07: heavy aggregates never take the service down; every poll answers HTTP 200 with no frozen or unresponsive window (iter goal-ops-hardening-iter-72)
- [minor] Project honesty standard: every figure in an evidence artifact is accurate (reports/perf-budgets.md is this round's sole deliverable) (iter goal-ops-hardening-iter-73)
- [minor] AG-8 / J-07: heavy aggregates never take the service down; every poll answers HTTP 200 with no frozen or unresponsive window (iter goal-ops-hardening-iter-73)
- [minor] Evidence floor: every required-still-passing journey named in the iteration spec is re-verified with its own fresh evidence (iter goal-ops-hardening-iter-73)
- [minor] AG-10 -- host resource ceiling / operational safety of heavy compute runs (iter goal-ops-hardening-iter-73)
- [minor] docs/goal.md 'Improvement direction -- Ground truth (measured 2026-07-18)' must describe the system as it actually is (iter goal-ops-hardening-iter-73)
- [minor] Owner-facing cost discipline: iterations run within their declared wall-clock budget (iter goal-ops-hardening-iter-73)
- [minor] Replay-lane failures must be explained by the artifact, never by an assumed cause (iter goal-ops-hardening-iter-74)
- [minor] Every Required-still-passing journey named by the spec gets its own fresh evidence each round (iter goal-ops-hardening-iter-74)
- [minor] Repo hygiene: no stray files left in the working tree (iter goal-ops-hardening-iter-74)
- [minor] Owner-facing cost discipline: iterations run within their declared wall-clock budget (iter goal-ops-hardening-iter-74)
- [minor] Process: the dispatched depth must match the iteration spec's declared depth, and every Definition-of-Done item must have a lane able to execute it. (iter goal-ops-hardening-iter-75)
- [minor] Each journey's Walkthrough acceptance clause: a [NEW]-flagged walkthrough viewable via demo.sh ops-hardening --session-live must record the frames it names. (iter goal-ops-hardening-iter-75)
- [minor] Verification integrity: a golden must assert the journey's own acceptance, not merely that a page renders. (iter goal-ops-hardening-iter-75)
- [minor] Loop economy: an iteration must fit its own declared wall-clock budget. (iter goal-ops-hardening-iter-75)
- [minor] Loop integrity: an iteration must actually execute its own Definition of Done. (iter goal-ops-hardening-iter-76)
- [minor] Diagnostic honesty: a failure explanation must be consistent with the timestamps of its own evidence. (iter goal-ops-hardening-iter-76)
- [minor] Harness hygiene: stale queue files must not point later rounds at the wrong remedy. (iter goal-ops-hardening-iter-76)
- [minor] Each journey's Walkthrough acceptance clause: a [NEW]-flagged walkthrough must record the frames it names. (iter goal-ops-hardening-iter-76)
- [minor] J-09 step 3: the background-compute detail must read alongside 'Ready', never in place of it. (iter goal-ops-hardening-iter-76)
- [minor] Loop economy: an iteration must fit its own declared wall-clock budget. (iter goal-ops-hardening-iter-76)
- [minor] Artifact integrity: the merged browser-QA file is the artifact of record; a journey verified by a later lane must be represented in it. (iter goal-ops-hardening-iter-77)
- [minor] Pipeline completion: an iteration must pass its own deterministic closure gate. (iter goal-ops-hardening-iter-77)
- [minor] Launcher safety: no test may leave the live frontend tree in a state where the launch script refuses to serve. (iter goal-ops-hardening-iter-77)
- [minor] Honest status: a disclosed staleness figure should not understate real staleness. (iter goal-ops-hardening-iter-77)
- [minor] Each journey's Walkthrough acceptance clause: a [NEW]-flagged walkthrough must record the state it names. (iter goal-ops-hardening-iter-77)
- [minor] Diagnostic honesty: a failure explanation must be consistent with the evidence it cites. (iter goal-ops-hardening-iter-77)
- [minor] Loop economy: an iteration must fit its own declared wall-clock budget. (iter goal-ops-hardening-iter-77)
- [minor] Artifact accuracy: delivered reports must describe their own run correctly. (iter goal-ops-hardening-iter-77)
- [minor] Closure discipline: an iteration must not end recorded `blocked` on its own deterministic gate. (iter goal-ops-hardening-iter-78)
- [critical] Evidence honesty: an artifact of record must never present reconstructed content as captured output. (iter goal-ops-hardening-iter-78)
- [minor] Definition of Done: a named DoD item must be met by the lane that owns it, not rescued at audit. (iter goal-ops-hardening-iter-78)
- [minor] Do no harm: a fix must not introduce a new way to take the service down. (iter goal-ops-hardening-iter-78)
- [minor] Walkthrough honesty: a captured frame must show what its own narration points at. (iter goal-ops-hardening-iter-78)
- [minor] Evidence floor: 'verified by a unit test' must mean the shipped module was executed. (iter goal-ops-hardening-iter-78)
- [minor] Measure what you change: a new always-on client behaviour should be measured, not assumed cheap. (iter goal-ops-hardening-iter-78)
- [minor] Loop economy: an iteration must fit its own declared wall-clock budget. (iter goal-ops-hardening-iter-78)
- [minor] Residue defence must cover every artifact the same residue leaves. (iter goal-ops-hardening-iter-78)
- [minor] Budget honesty: a served page must meet its committed budget, and any breach is disclosed, not absorbed. (iter goal-ops-hardening-iter-79)
- [minor] Every capture cited as evidence must actually show what it claims. (iter goal-ops-hardening-iter-79)
- [minor] Reported counts must match the artifact they cite. (iter goal-ops-hardening-iter-79)
- [minor] Iteration bookkeeping must reflect what the pipeline actually ran. (iter goal-ops-hardening-iter-79)
- [minor] Loop economy: an iteration must fit its own declared wall-clock budget. (iter goal-ops-hardening-iter-79)
- [minor] Walkthrough acceptance: each journey's walkthrough must be [NEW]-flagged in the session demo. (iter goal-ops-hardening-iter-79)
- [minor] Service shutdown must not cancel work without a record. (iter goal-ops-hardening-iter-79)

## Telemetry

See `runs/goal-session-ops-hardening/telemetry.jsonl` for the structured event log.

## Iteration timing

```
== Wall-time report: session ops-hardening
  goal-ops-hardening-iter-0  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer              0.3m  calls=1  failures=1
      pump-wait                  0.3m
  goal-ops-hardening-iter-0  depth=lean  verdict=?  wall=?  (incomplete/interrupted attempt)
      browser-qa-agent            37.5m  calls=1
      goal-decomposer             10.4m  calls=1
      developer                    9.1m  calls=1
      reviewer                     4.2m  calls=1
      goal-evaluator               0.0m  calls=1  failures=1
      pump-wait                  0.4m
  goal-ops-hardening-iter-0  depth=lean  verdict=CONTINUE  wall=9.3m
      goal-evaluator               9.3m  calls=1
      (resume-skipped: goal-decomposer, developer, reviewer, browser-qa)
      pump-wait                  0.1m
      unattributed (glue)        0.0m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-1  depth=full  verdict=CONTINUE  wall=241.5m
      goal-decomposer             16.4m  calls=1
      goal-evaluator              12.1m  calls=1
      coherence-auditor            6.3m  calls=1
      iteration-summarizer         6.3m  calls=1
      pump-wait                 18.9m
      unattributed (glue)      200.4m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-2  depth=full  verdict=CONTINUE  wall=646.9m
      goal-decomposer             18.5m  calls=1
      iteration-summarizer        18.5m  calls=1
      goal-evaluator              15.5m  calls=1
      coherence-auditor            6.4m  calls=1
      readme-maintainer            3.4m  calls=1
      pump-wait                226.9m
      unattributed (glue)      584.5m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-3  depth=full  verdict=CONTINUE  wall=259.8m
      goal-evaluator              15.6m  calls=1
      iteration-summarizer        14.1m  calls=1
      goal-decomposer             14.1m  calls=1
      readme-maintainer            7.7m  calls=1
      coherence-auditor            4.0m  calls=1
      pump-wait                  1.7m
      unattributed (glue)      204.3m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-4  depth=full  verdict=CONTINUE  wall=276.2m
      iteration-summarizer        16.0m  calls=1
      goal-decomposer             16.0m  calls=1
      goal-evaluator              12.1m  calls=1
      readme-maintainer            6.9m  calls=1
      coherence-auditor            4.4m  calls=1
      pump-wait                  2.7m
      unattributed (glue)      220.8m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-5  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer             14.5m  calls=1
      iteration-summarizer        14.5m  calls=1
      readme-maintainer            3.4m  calls=1
      pump-wait                 26.3m
  goal-ops-hardening-iter-5  depth=full  verdict=CONTINUE  wall=32.6m
      goal-evaluator              10.6m  calls=1
      coherence-auditor            2.8m  calls=1
      (resume-skipped: goal-decomposer)
      pump-wait                  0.7m
      unattributed (glue)       19.3m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-6  depth=full  verdict=CONTINUE  wall=252.8m
      goal-evaluator              12.0m  calls=1
      iteration-summarizer         9.9m  calls=1
      goal-decomposer              9.9m  calls=1
      coherence-auditor            3.9m  calls=1
      readme-maintainer            1.5m  calls=1
      pump-wait                  1.2m
      unattributed (glue)      215.6m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-7  depth=full  verdict=REGRESSION  wall=304.9m
      iteration-summarizer        15.3m  calls=2
      goal-evaluator              10.9m  calls=1
      goal-decomposer             10.2m  calls=1
      readme-maintainer            4.0m  calls=2
      coherence-auditor            2.8m  calls=1
      pump-wait                  1.6m
      unattributed (glue)      261.7m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-8  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer             11.5m  calls=1
      pump-wait                  0.6m
  goal-ops-hardening-iter-8  depth=full  verdict=CONTINUE  wall=130.4m
      goal-evaluator              11.1m  calls=1
      coherence-auditor            3.2m  calls=1
      (resume-skipped: goal-decomposer)
      pump-wait                  1.7m
      unattributed (glue)      116.1m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-9  depth=full  verdict=CONTINUE  wall=648.7m
      goal-evaluator              11.6m  calls=1
      goal-decomposer              7.8m  calls=1
      coherence-auditor            4.3m  calls=1
      pump-wait                  8.4m
      unattributed (glue)      625.0m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-10  depth=lean  verdict=CONTINUE  wall=110.6m
      browser-qa-agent            62.3m  calls=1
      developer                   20.1m  calls=1
      goal-evaluator              13.1m  calls=1
      goal-decomposer              9.8m  calls=1
      iteration-summarizer         9.8m  calls=1
      reviewer                     2.3m  calls=1
      readme-maintainer            2.0m  calls=1
      coherence-auditor            2.0m  calls=1
      (resume-skipped: coherence-auditor)
      pump-wait                  1.7m
      overlap saved             10.9m  (parallel steps)
  goal-ops-hardening-iter-11  depth=lean  verdict=ESCALATE  wall=81.3m
      developer                   25.5m  calls=1
      browser-qa-agent            17.5m  calls=1
      goal-evaluator              17.2m  calls=1
      goal-decomposer             10.4m  calls=1
      iteration-summarizer         4.7m  calls=1
      coherence-auditor            2.4m  calls=1
      reviewer                     1.9m  calls=1
      readme-maintainer            1.4m  calls=1
      (resume-skipped: coherence-auditor)
      pump-wait                  3.1m
      unattributed (glue)        0.3m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-12  depth=full  verdict=CONTINUE  wall=179.2m
      goal-decomposer             11.5m  calls=1
      goal-evaluator              11.0m  calls=1
      iteration-summarizer         4.8m  calls=1
      coherence-auditor            2.6m  calls=1
      pump-wait                  1.9m
      unattributed (glue)      149.3m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-13  depth=full  verdict=REGRESSION  wall=279.7m
      iteration-summarizer        19.4m  calls=2
      goal-decomposer             14.2m  calls=1
      goal-evaluator              12.2m  calls=1
      coherence-auditor            3.3m  calls=1
      readme-maintainer            2.0m  calls=1
      pump-wait                  1.6m
      unattributed (glue)      228.4m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-14  depth=full  verdict=CONTINUE  wall=251.4m
      goal-evaluator              22.7m  calls=1
      goal-decomposer             21.6m  calls=1
      coherence-auditor            4.4m  calls=1
      [engine] full-pipeline     202.6m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  4.8m
      unattributed (glue)      202.7m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-15  depth=full  verdict=STALLED  wall=217.7m
      iteration-summarizer        29.9m  calls=2
      goal-decomposer             21.9m  calls=1
      goal-evaluator              15.9m  calls=1
      readme-maintainer            8.7m  calls=2
      coherence-auditor            6.1m  calls=1
      [engine] full-pipeline     156.9m  (contains agent time above)
      [engine] showcase-join       5.7m  (contains agent time above)
      pump-wait                  2.9m
      unattributed (glue)      135.2m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-16  depth=full  verdict=CONTINUE  wall=212.6m
      goal-decomposer             21.8m  calls=1
      goal-evaluator              12.3m  calls=1
      coherence-auditor            7.3m  calls=1
      [engine] full-pipeline     171.2m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  3.1m
      unattributed (glue)      171.2m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-17  depth=full  verdict=CONTINUE  wall=517.3m
      iteration-summarizer        18.8m  calls=1
      goal-decomposer             18.8m  calls=1
      goal-evaluator              15.9m  calls=1  failures=1
      readme-maintainer            8.8m  calls=1
      coherence-auditor            4.5m  calls=1  failures=1
      [engine] full-pipeline     469.2m  (contains agent time above)
      [engine] showcase-join       8.9m  (contains agent time above)
      pump-wait                  1.5m
      unattributed (glue)      450.5m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-18  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer             13.2m  calls=1  failures=1
  goal-ops-hardening-iter-18  depth=lean  verdict=CONTINUE  wall=119.8m
      developer                   35.2m  calls=1
      goal-evaluator              30.9m  calls=1
      coherence-auditor           25.6m  calls=1
      browser-qa-agent            20.6m  calls=1
      goal-decomposer             15.4m  calls=1
      reviewer                    12.6m  calls=1
      [engine] lean-pipeline      73.5m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                 32.4m
      overlap saved             20.6m  (parallel steps)
  goal-ops-hardening-iter-19  depth=full  verdict=CONTINUE  wall=296.2m
      goal-decomposer             26.7m  calls=1
      goal-evaluator              14.8m  calls=1
      coherence-auditor            4.1m  calls=1
      [engine] full-pipeline     235.4m  (contains agent time above)
      [engine] showcase-join      15.1m  (contains agent time above)
      pump-wait                 23.0m
      unattributed (glue)      250.6m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-20  depth=full  verdict=STALLED  wall=219.2m
      iteration-summarizer        35.1m  calls=2
      goal-decomposer             22.1m  calls=1
      goal-evaluator              16.6m  calls=1
      coherence-auditor            4.8m  calls=1
      readme-maintainer            4.5m  calls=2
      [engine] full-pipeline     158.0m  (contains agent time above)
      [engine] showcase-join      14.7m  (contains agent time above)
      pump-wait                  9.0m
      unattributed (glue)      136.1m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-21  depth=lean  verdict=STALLED  wall=109.0m
      browser-qa-agent            36.0m  calls=1
      goal-decomposer             19.5m  calls=1
      goal-evaluator              18.8m  calls=1
      developer                    9.1m  calls=1
      iteration-summarizer         8.8m  calls=1
      reviewer                     4.1m  calls=1
      coherence-auditor            3.8m  calls=1
      [engine] lean-pipeline      49.6m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  4.2m
      unattributed (glue)        8.9m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-22  depth=lean  verdict=CONTINUE  wall=109.0m
      browser-qa-agent            28.8m  calls=1
      developer                   27.2m  calls=1
      goal-evaluator              17.3m  calls=1
      goal-decomposer             15.3m  calls=1
      reviewer                    10.9m  calls=1
      coherence-auditor            5.0m  calls=1
      [engine] lean-pipeline      67.3m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                 12.0m
      unattributed (glue)        4.5m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-23  depth=lean  verdict=GOAL_ACHIEVED  wall=138.3m
      browser-qa-agent            24.3m  calls=1
      developer                   22.1m  calls=1
      iteration-summarizer        18.1m  calls=2
      goal-decomposer             18.1m  calls=1
      goal-evaluator              16.3m  calls=1
      reviewer                     8.4m  calls=1
      coherence-auditor            5.8m  calls=1
      readme-maintainer            3.5m  calls=1
      [engine] lean-pipeline      55.3m  (contains agent time above)
      [engine] showcase-join      13.3m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  6.4m
      unattributed (glue)       21.8m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-24  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)
  goal-ops-hardening-iter-24  depth=full  verdict=CONTINUE  wall=202.9m
      goal-evaluator              14.3m  calls=1
      goal-decomposer              8.9m  calls=1
      coherence-auditor            2.8m  calls=1
      [engine] full-pipeline     176.8m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  1.9m
      unattributed (glue)      176.8m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-25  depth=lean  verdict=CONTINUE  wall=140.7m
      developer                   79.4m  calls=1
      browser-qa-agent            27.5m  calls=1
      goal-evaluator              13.4m  calls=1
      goal-decomposer              6.1m  calls=1
      iteration-summarizer         6.1m  calls=1
      reviewer                     4.8m  calls=1
      coherence-auditor            2.6m  calls=1
      readme-maintainer            1.8m  calls=1
      [engine] lean-pipeline     113.0m  (contains agent time above)
      [engine] showcase-join       1.9m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  2.1m
      overlap saved              1.1m  (parallel steps)
  goal-ops-hardening-iter-26  depth=lean  verdict=ESCALATE  wall=155.3m
      developer                   99.8m  calls=1
      goal-evaluator              19.0m  calls=1
      browser-qa-agent            11.3m  calls=1
      goal-decomposer              9.6m  calls=1
      iteration-summarizer         5.5m  calls=1
      reviewer                     3.5m  calls=1
      coherence-auditor            2.2m  calls=1
      readme-maintainer            1.5m  calls=1
      [engine] lean-pipeline     115.5m  (contains agent time above)
      [engine] showcase-join      11.2m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                 11.4m
      unattributed (glue)        3.0m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-27  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer             12.5m  calls=1
      iteration-summarizer         4.7m  calls=1
      readme-maintainer            1.2m  calls=1
      [engine] full-pipeline    1204.1m  (contains agent time above)
      [engine] showcase-join      13.2m  (contains agent time above)
      pump-wait                 12.9m
  goal-ops-hardening-iter-27  depth=full  verdict=CONTINUE  wall=57.7m
      goal-evaluator              14.8m  calls=1
      coherence-auditor            2.6m  calls=1
      [engine] full-pipeline      40.3m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer)
      pump-wait                  0.8m
      unattributed (glue)       40.4m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-28  depth=lean  verdict=?  wall=?  (incomplete/interrupted attempt)
      developer                  111.4m  calls=1
      browser-qa-agent            62.9m  calls=1
      iteration-summarizer         8.9m  calls=1
      goal-decomposer              8.9m  calls=1
      coherence-auditor            3.1m  calls=1
      reviewer                     2.9m  calls=1
      readme-maintainer            1.6m  calls=1
      [engine] lean-pipeline     177.8m  (contains agent time above)
      [engine] showcase-join       1.7m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  3.0m
  goal-ops-hardening-iter-28  depth=lean  verdict=CONTINUE  wall=16.5m
      goal-evaluator              16.4m  calls=1
      [engine] lean-pipeline       0.0m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer, developer, reviewer, coherence-auditor, browser-qa, coherence-auditor)
      unattributed (glue)        0.1m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-29  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer             20.6m  calls=1
      [engine] showcase-join      15.1m  (contains agent time above)
      pump-wait                 26.8m
  goal-ops-hardening-iter-29  depth=lean  verdict=CONTINUE  wall=46.8m
      browser-qa-agent            25.4m  calls=1
      goal-evaluator              18.5m  calls=1
      coherence-auditor            3.5m  calls=1
      demo-narrator                1.9m  calls=1
      [engine] evidence-pipeline    28.2m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer, developer, reviewer, coherence-auditor)
      pump-wait                  3.1m
      overlap saved              2.5m  (parallel steps)
  goal-ops-hardening-iter-30  depth=full  verdict=CONTINUE  wall=152.0m
      developer                   48.9m  calls=1
      browser-qa-agent            32.3m  calls=1
      auditor                     15.8m  calls=1
      goal-evaluator              15.7m  calls=1
      iteration-summarizer         9.1m  calls=1
      goal-decomposer              9.1m  calls=1
      qa                           7.0m  calls=2
      ux-regression-reviewer       5.7m  calls=1
      ui-impact-analyst            5.4m  calls=1
      orchestrator                 5.0m  calls=1
      reviewer                     4.6m  calls=1
      coherence-auditor            3.1m  calls=1
      readme-maintainer            1.4m  calls=1
      demo-narrator                1.3m  calls=1
      ui-test-designer             1.2m  calls=1
      [engine] full-pipeline     122.6m  (contains agent time above)
      [engine] showcase-join       1.5m  (contains agent time above)
      pump-wait                  0.8m
      overlap saved             13.6m  (parallel steps)
  goal-ops-hardening-iter-31  depth=full  verdict=CONTINUE  wall=172.4m
      developer                   83.4m  calls=2
      auditor                     21.9m  calls=1
      goal-evaluator              13.8m  calls=1
      iteration-summarizer        10.8m  calls=1
      goal-decomposer             10.8m  calls=1
      reviewer                    10.2m  calls=2
      browser-qa-agent             9.8m  calls=1
      qa                           7.3m  calls=2
      ui-impact-analyst            5.8m  calls=1
      orchestrator                 4.8m  calls=1
      ux-regression-reviewer       3.0m  calls=1
      coherence-auditor            2.8m  calls=1
      demo-narrator                1.3m  calls=1
      ui-test-designer             1.3m  calls=1
      readme-maintainer            1.0m  calls=1
      [engine] full-pipeline     143.8m  (contains agent time above)
      [engine] showcase-join       1.1m  (contains agent time above)
      pump-wait                  0.9m
      overlap saved             15.7m  (parallel steps)
  goal-ops-hardening-iter-32  depth=full  verdict=CONTINUE  wall=166.2m
      developer                   72.4m  calls=1
      auditor                     20.9m  calls=1
      iteration-summarizer        15.5m  calls=1
      goal-decomposer             15.5m  calls=1
      goal-evaluator              14.5m  calls=1
      browser-qa-agent            11.9m  calls=1
      reviewer                     8.0m  calls=1
      qa                           6.7m  calls=2
      ui-impact-analyst            5.0m  calls=1
      orchestrator                 4.3m  calls=1
      coherence-auditor            4.0m  calls=1
      ux-regression-reviewer       2.9m  calls=1
      ui-test-designer             1.6m  calls=1
      readme-maintainer            1.4m  calls=1
      demo-narrator                1.4m  calls=1
      [engine] full-pipeline     130.8m  (contains agent time above)
      [engine] showcase-join       1.5m  (contains agent time above)
      pump-wait                  1.2m
      overlap saved             19.6m  (parallel steps)
  goal-ops-hardening-iter-33  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      developer                   88.4m  calls=2
      qa                          53.6m  calls=4
      browser-qa-agent            43.0m  calls=1
      ui-impact-analyst           41.1m  calls=1
      auditor                     18.2m  calls=1
      reviewer                    17.0m  calls=2
      goal-decomposer             10.3m  calls=1
      iteration-summarizer        10.3m  calls=1
      orchestrator                 5.8m  calls=1
      ui-test-designer             5.6m  calls=1
      ux-regression-reviewer       5.2m  calls=1
      coherence-auditor            2.9m  calls=1
      demo-narrator                1.6m  calls=1
      readme-maintainer            1.4m  calls=1
      [engine] full-pipeline     239.8m  (contains agent time above)
      [engine] showcase-join       1.4m  (contains agent time above)
      pump-wait                  1.6m
  goal-ops-hardening-iter-33  depth=lean  verdict=CONTINUE  wall=192.2m
      browser-qa-agent           142.1m  calls=1
      developer                   27.2m  calls=1
      goal-evaluator              14.9m  calls=1
      reviewer                     7.8m  calls=1
      coherence-auditor            4.5m  calls=1
      browser-qa-replay            1.1m  calls=1
      [engine] lean-pipeline     177.3m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer, coherence-auditor)
      pump-wait                  4.8m
      OVER BUDGET at coherence-auditor: 10639s > 3600s (mode=trim)
      overlap saved              5.4m  (parallel steps)
  goal-ops-hardening-iter-34  depth=lean  verdict=CONTINUE  wall=113.2m
      developer                   72.5m  calls=1
      goal-evaluator              14.7m  calls=1
      goal-decomposer             12.2m  calls=1
      browser-qa-agent            10.1m  calls=1
      iteration-summarizer         4.4m  calls=1
      reviewer                     3.5m  calls=1
      coherence-auditor            2.4m  calls=1
      browser-qa-replay            1.2m  calls=1
      [engine] lean-pipeline      86.2m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  7.1m
      OVER BUDGET at browser-qa: 5299s > 3600s (mode=trim)
      overlap saved              7.7m  (parallel steps)
  goal-ops-hardening-iter-35  depth=lean  verdict=ESCALATE  wall=55.1m
      browser-qa-agent            24.0m  calls=1
      goal-evaluator              14.7m  calls=1
      iteration-summarizer        14.0m  calls=1
      goal-decomposer             13.9m  calls=1
      demo-narrator                1.7m  calls=1
      [engine] evidence-pipeline    26.4m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: developer, reviewer, coherence-auditor)
      pump-wait                  0.1m
      overlap saved             13.2m  (parallel steps)
  goal-ops-hardening-iter-36  depth=full  verdict=ESCALATE  wall=404.3m
      browser-qa-agent           214.4m  calls=1
      developer                   87.3m  calls=1
      auditor                     47.4m  calls=1
      qa                          37.0m  calls=1
      goal-evaluator              17.4m  calls=1
      reviewer                    15.0m  calls=1
      goal-decomposer              8.2m  calls=1
      iteration-summarizer         8.2m  calls=1
      orchestrator                 4.7m  calls=1
      ui-impact-analyst            3.7m  calls=1
      coherence-auditor            3.7m  calls=1
      demo-narrator                1.4m  calls=1
      [engine] full-pipeline     374.9m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                 37.2m
      OVER BUDGET at post-dev-fanout: 6921s > 3600s (mode=trim)
      overlap saved             44.2m  (parallel steps)
  goal-ops-hardening-iter-37  depth=full  verdict=ESCALATE  wall=195.9m
      developer                  106.3m  calls=1
      auditor                     21.2m  calls=1
      goal-evaluator              16.4m  calls=1
      iteration-summarizer        11.8m  calls=1
      goal-decomposer             11.8m  calls=1
      qa                          11.4m  calls=1
      reviewer                    10.1m  calls=1
      ui-test-designer            10.0m  calls=1
      orchestrator                 6.7m  calls=1
      browser-qa-agent             6.4m  calls=1
      coherence-auditor            3.0m  calls=1
      ui-impact-analyst            1.6m  calls=1
      demo-narrator                1.2m  calls=1
      [engine] full-pipeline     164.6m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ux-regression)
      pump-wait                  4.2m
      OVER BUDGET at post-dev-fanout: 8101s > 3600s (mode=trim)
      overlap saved             21.9m  (parallel steps)
  goal-ops-hardening-iter-38  depth=full  verdict=ESCALATE  wall=223.7m
      developer                   89.2m  calls=1
      browser-qa-agent            61.3m  calls=1
      auditor                     16.8m  calls=1
      qa                          15.2m  calls=1
      ui-test-designer            13.8m  calls=1
      goal-evaluator              12.1m  calls=1
      iteration-summarizer        10.6m  calls=1
      goal-decomposer             10.6m  calls=1
      reviewer                     6.7m  calls=1
      orchestrator                 4.4m  calls=1
      coherence-auditor            2.8m  calls=1
      ui-impact-analyst            1.4m  calls=1
      demo-narrator                1.1m  calls=1
      [engine] full-pipeline     198.1m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ux-regression)
      pump-wait                  2.2m
      OVER BUDGET at post-dev-fanout: 6659s > 3600s (mode=trim)
      overlap saved             22.4m  (parallel steps)
  goal-ops-hardening-iter-39  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      iteration-summarizer         8.2m  calls=1
      goal-decomposer              8.2m  calls=1
      orchestrator                 3.2m  calls=1
      [engine] showcase-join       0.1m  (contains agent time above)
      pump-wait                  0.1m
  goal-ops-hardening-iter-39  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      developer                   39.7m  calls=1
      reviewer                     0.0m  calls=1  failures=1
      [engine] full-pipeline      39.7m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer)
      pump-wait                  0.2m
  goal-ops-hardening-iter-39  depth=full  verdict=ESCALATE  wall=119.3m
      auditor                     29.5m  calls=2
      developer                   25.9m  calls=1
      reviewer                    20.7m  calls=2
      qa                          18.7m  calls=2
      goal-evaluator              14.8m  calls=1
      ui-test-designer             6.1m  calls=1
      coherence-auditor            3.0m  calls=1
      ux-regression-reviewer       2.0m  calls=1
      browser-qa-agent             1.7m  calls=1
      ui-impact-analyst            1.4m  calls=1
      demo-narrator                1.0m  calls=1
      [engine] full-pipeline     101.5m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer)
      pump-wait                  2.4m
      OVER BUDGET at coherence-auditor: 6090s > 3600s (mode=trim)
      overlap saved              5.5m  (parallel steps)
  goal-ops-hardening-iter-40  depth=full  verdict=ESCALATE  wall=122.7m
      developer                   46.2m  calls=1
      qa                          21.4m  calls=1
      browser-qa-agent            19.8m  calls=1
      auditor                     17.1m  calls=1
      goal-evaluator              15.7m  calls=1
      iteration-summarizer         6.5m  calls=1
      goal-decomposer              6.5m  calls=1
      reviewer                     5.4m  calls=1
      orchestrator                 3.6m  calls=1
      ui-impact-analyst            2.7m  calls=1
      coherence-auditor            2.5m  calls=1
      demo-narrator                1.1m  calls=1
      [engine] full-pipeline      97.8m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                 20.6m
      OVER BUDGET at post-dev-fanout: 3712s > 3600s (mode=trim)
      overlap saved             25.9m  (parallel steps)
  goal-ops-hardening-iter-41  depth=full  verdict=ESCALATE  wall=178.1m
      developer                   93.5m  calls=2
      reviewer                    17.9m  calls=2
      goal-evaluator              14.7m  calls=1
      auditor                     13.7m  calls=1
      qa                          13.1m  calls=1
      iteration-summarizer        11.8m  calls=1
      goal-decomposer             11.8m  calls=1
      browser-qa-agent             9.3m  calls=1
      ui-impact-analyst            6.8m  calls=1
      orchestrator                 4.3m  calls=1
      coherence-auditor            2.1m  calls=1
      demo-narrator                1.5m  calls=1
      [engine] full-pipeline     149.3m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                 12.4m
      OVER BUDGET at post-dev-fanout: 7670s > 3600s (mode=trim)
      overlap saved             22.6m  (parallel steps)
  goal-ops-hardening-iter-42  depth=full  verdict=REGRESSION  wall=171.0m
      developer                   43.9m  calls=1
      auditor                     32.2m  calls=1
      browser-qa-agent            29.1m  calls=1
      goal-evaluator              17.1m  calls=1
      iteration-summarizer        15.3m  calls=2
      qa                          12.4m  calls=1
      ui-test-designer            10.5m  calls=1
      goal-decomposer             10.0m  calls=1
      reviewer                     5.6m  calls=1
      coherence-auditor            4.6m  calls=1
      orchestrator                 3.9m  calls=1
      demo-narrator                2.0m  calls=1
      ui-impact-analyst            2.0m  calls=1
      [engine] full-pipeline     133.8m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ux-regression)
      pump-wait                  2.7m
      OVER BUDGET at post-dev-fanout: 3810s > 3600s (mode=trim)
      overlap saved             17.6m  (parallel steps)
  goal-ops-hardening-iter-43  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      developer                   71.7m  calls=1
      browser-qa-agent            30.2m  calls=1
      goal-decomposer             19.1m  calls=1
      qa                          17.9m  calls=1
      ui-test-designer            15.3m  calls=1
      reviewer                    11.8m  calls=1
      orchestrator                 6.4m  calls=1
      ui-impact-analyst            2.7m  calls=1
      demo-narrator                1.7m  calls=1
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: ux-regression)
      pump-wait                  3.7m
      OVER BUDGET at post-dev-fanout: 6540s > 3600s (mode=trim)
  goal-ops-hardening-iter-43  depth=full  verdict=ESCALATE  wall=73.1m
      auditor                     53.1m  calls=1
      goal-evaluator              15.3m  calls=1
      coherence-auditor            4.7m  calls=1
      [engine] full-pipeline      53.1m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer)
      pump-wait                  1.6m
      unattributed (glue)        0.0m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-44  depth=full  verdict=ESCALATE  wall=233.4m
      developer                   75.5m  calls=2
      browser-qa-agent            48.2m  calls=1
      auditor                     45.2m  calls=1
      reviewer                    18.4m  calls=2
      goal-evaluator              14.7m  calls=1
      qa                          14.5m  calls=2
      iteration-summarizer        11.2m  calls=1
      goal-decomposer             11.1m  calls=1
      ui-impact-analyst            5.5m  calls=1
      orchestrator                 3.3m  calls=1
      coherence-auditor            2.7m  calls=1
      demo-narrator                1.5m  calls=1
      [engine] full-pipeline     204.8m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                  9.5m
      OVER BUDGET at post-dev-fanout: 5135s > 3600s (mode=trim)
      overlap saved             18.5m  (parallel steps)
  goal-ops-hardening-iter-45  depth=full  verdict=ESCALATE  wall=309.7m
      developer                  143.9m  calls=2
      browser-qa-agent            67.5m  calls=1
      auditor                     33.4m  calls=1
      qa                          21.7m  calls=2
      goal-evaluator              15.2m  calls=1
      reviewer                    14.8m  calls=2
      iteration-summarizer        10.2m  calls=1
      goal-decomposer             10.2m  calls=1
      ui-impact-analyst            9.1m  calls=1
      demo-narrator                4.2m  calls=1
      coherence-auditor            3.4m  calls=1
      orchestrator                 2.8m  calls=1
      [engine] full-pipeline     280.9m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                 21.9m
      OVER BUDGET at post-dev-fanout: 7442s > 3600s (mode=trim)
      overlap saved             26.5m  (parallel steps)
  goal-ops-hardening-iter-46  depth=full  verdict=ESCALATE  wall=366.5m
      developer                  147.9m  calls=3
      qa                         114.2m  calls=4
      browser-qa-agent            61.2m  calls=1
      auditor                     35.9m  calls=1
      goal-evaluator              22.8m  calls=1
      reviewer                    21.6m  calls=3
      ui-impact-analyst           18.6m  calls=1
      iteration-summarizer        12.2m  calls=1
      goal-decomposer             12.2m  calls=1
      orchestrator                 4.8m  calls=1
      coherence-auditor            4.1m  calls=1
      demo-narrator                1.4m  calls=1
      [engine] full-pipeline     327.3m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                 19.5m
      OVER BUDGET at post-dev-fanout: 4267s > 3600s (mode=trim)
      overlap saved             90.3m  (parallel steps)
  goal-ops-hardening-iter-47  depth=full  verdict=ESCALATE  wall=428.6m
      developer                  205.6m  calls=2
      browser-qa-agent            75.9m  calls=1
      auditor                     57.2m  calls=2
      qa                          56.3m  calls=2
      goal-evaluator              19.4m  calls=1
      reviewer                    17.3m  calls=2
      goal-decomposer             16.1m  calls=1
      ui-impact-analyst            6.5m  calls=1
      iteration-summarizer         6.0m  calls=1
      coherence-auditor            5.3m  calls=1
      orchestrator                 4.9m  calls=1
      demo-narrator                1.4m  calls=1
      [engine] full-pipeline     387.6m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                 46.2m
      OVER BUDGET at post-dev-fanout: 9141s > 3600s (mode=trim)
      overlap saved             43.2m  (parallel steps)
  goal-ops-hardening-iter-48  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer             13.9m  calls=1
      iteration-summarizer        13.9m  calls=1
      orchestrator                 5.2m  calls=1
      [engine] showcase-join       0.1m  (contains agent time above)
      pump-wait                  0.1m
  goal-ops-hardening-iter-48  depth=full  verdict=ESCALATE  wall=300.5m
      developer                  157.5m  calls=2
      browser-qa-agent            73.9m  calls=1
      qa                          51.6m  calls=2
      auditor                     21.0m  calls=1
      goal-evaluator              15.2m  calls=1
      reviewer                    12.7m  calls=2
      ui-impact-analyst            9.0m  calls=1
      coherence-auditor            2.8m  calls=1
      demo-narrator                1.1m  calls=1
      [engine] full-pipeline     282.4m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer, ui-test-design, ux-regression)
      pump-wait                 45.5m
      OVER BUDGET at post-dev-fanout: 3795s > 3600s (mode=trim)
      overlap saved             44.4m  (parallel steps)
  goal-ops-hardening-iter-49  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      developer                  132.7m  calls=1
      iteration-summarizer        12.1m  calls=1
      goal-decomposer             12.1m  calls=1
      ui-impact-analyst            7.6m  calls=1
      reviewer                     6.5m  calls=1
      orchestrator                 4.6m  calls=1
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design)
      pump-wait                  0.2m
      OVER BUDGET at post-dev-fanout: 9370s > 3600s (mode=trim)
  goal-ops-hardening-iter-49  depth=full  verdict=ESCALATE  wall=243.3m
      developer                   90.8m  calls=2
      auditor                     57.2m  calls=3
      browser-qa-agent            39.5m  calls=1
      goal-evaluator              20.2m  calls=1
      qa                          16.2m  calls=2
      reviewer                     9.5m  calls=2
      ui-impact-analyst            8.7m  calls=1
      ux-regression-reviewer       5.2m  calls=1
      coherence-auditor            2.5m  calls=1
      demo-narrator                1.3m  calls=1
      [engine] full-pipeline     220.6m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer, ui-test-design)
      pump-wait                  1.1m
      OVER BUDGET at coherence-auditor: 13234s > 3600s (mode=trim)
      overlap saved              7.8m  (parallel steps)
  goal-ops-hardening-iter-50  depth=full  verdict=ESCALATE  wall=1070.6m
      reviewer                   445.1m  calls=3
      developer                  403.7m  calls=3
      browser-qa-agent           122.7m  calls=1
      auditor                     41.0m  calls=3
      qa                          38.4m  calls=2
      goal-decomposer             15.6m  calls=1
      goal-evaluator              14.4m  calls=1
      ui-impact-analyst            9.5m  calls=1
      iteration-summarizer         5.8m  calls=1
      coherence-auditor            4.7m  calls=1
      orchestrator                 4.0m  calls=1
      demo-narrator                1.7m  calls=1
      [engine] full-pipeline    1035.9m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                 41.8m
      OVER BUDGET at post-dev-fanout: 28696s > 3600s (mode=trim)
      overlap saved             35.8m  (parallel steps)
  goal-ops-hardening-iter-51  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      iteration-summarizer        13.6m  calls=1
      goal-decomposer             13.6m  calls=1
      orchestrator                 2.9m  calls=1
      [engine] showcase-join       0.1m  (contains agent time above)
      pump-wait                  0.0m
  goal-ops-hardening-iter-51  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      browser-qa-agent           105.2m  calls=1
      developer                   42.5m  calls=1
      qa                          37.6m  calls=1
      reviewer                    13.7m  calls=1
      ui-impact-analyst           13.5m  calls=1
      demo-narrator                1.2m  calls=1
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer, ui-test-design, ux-regression)
      pump-wait                 37.3m
      OVER BUDGET at qa-loop: 10671s > 3600s (mode=trim)
  goal-ops-hardening-iter-51  depth=full  verdict=ESCALATE  wall=40.9m
      auditor                     20.2m  calls=1
      goal-evaluator              15.2m  calls=1
      coherence-auditor            5.4m  calls=1
      [engine] full-pipeline      20.2m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer)
      pump-wait                  0.3m
      unattributed (glue)        0.1m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-52  depth=?  verdict=?  wall=?  (incomplete/interrupted attempt)
  goal-ops-hardening-iter-52  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer             17.6m  calls=1
      orchestrator                 8.2m  calls=1
      [engine] showcase-join       0.0m  (contains agent time above)
      pump-wait                  0.3m
  goal-ops-hardening-iter-52  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer)
  goal-ops-hardening-iter-52  depth=full  verdict=ESCALATE  wall=413.9m
      developer                  208.4m  calls=3
      browser-qa-agent            81.8m  calls=1
      qa                          52.6m  calls=4
      reviewer                    40.8m  calls=3
      goal-evaluator              17.1m  calls=1
      ui-impact-analyst           12.4m  calls=1
      auditor                     12.1m  calls=1
      coherence-auditor            6.8m  calls=1
      demo-narrator                1.2m  calls=1
      [engine] full-pipeline     390.0m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer, ui-test-design, ux-regression)
      pump-wait                 22.3m
      OVER BUDGET at post-dev-fanout: 4772s > 3600s (mode=trim)
      overlap saved             19.4m  (parallel steps)
  goal-ops-hardening-iter-53  depth=full  verdict=CONTINUE  wall=262.6m
      developer                   95.1m  calls=1
      browser-qa-agent            53.7m  calls=1
      qa                          29.2m  calls=1
      goal-decomposer             28.7m  calls=1
      ui-impact-analyst           21.7m  calls=1
      goal-evaluator              16.3m  calls=1
      reviewer                    15.1m  calls=1
      auditor                     14.3m  calls=1
      iteration-summarizer        11.4m  calls=1
      orchestrator                10.1m  calls=1
      coherence-auditor            5.3m  calls=1
      demo-narrator                1.2m  calls=1
      [engine] full-pipeline     212.2m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                 23.8m
      OVER BUDGET at post-dev-fanout: 8949s > 3600s (mode=trim)
      overlap saved             39.6m  (parallel steps)
  goal-ops-hardening-iter-54  depth=lean  verdict=?  wall=?  (incomplete/interrupted attempt)
      developer                  100.3m  calls=1
      goal-decomposer             26.9m  calls=1
      reviewer                    20.0m  calls=1
      iteration-summarizer         9.0m  calls=1
      coherence-auditor            4.1m  calls=1
      browser-qa-replay            1.1m  calls=1
      [engine] showcase-join       0.1m  (contains agent time above)
      pump-wait                  9.2m
      OVER BUDGET at browser-qa: 8844s > 3600s (mode=trim)
  goal-ops-hardening-iter-54  depth=lean  verdict=ESCALATE  wall=135.2m
      developer                   81.7m  calls=1
      browser-qa-agent            34.4m  calls=1
      goal-evaluator              15.3m  calls=1
      reviewer                     3.6m  calls=1
      coherence-auditor            3.0m  calls=1
      browser-qa-replay            1.4m  calls=1
      [engine] lean-pipeline     119.9m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer, coherence-auditor)
      pump-wait                  3.1m
      OVER BUDGET at browser-qa: 5122s > 3600s (mode=trim)
      overlap saved              4.2m  (parallel steps)
  goal-ops-hardening-iter-55  depth=full  verdict=CONTINUE  wall=254.2m
      developer                  121.3m  calls=1
      browser-qa-agent            59.3m  calls=1
      goal-evaluator              17.5m  calls=1
      goal-decomposer             14.7m  calls=1
      auditor                     14.1m  calls=1
      qa                          13.1m  calls=1
      reviewer                    11.4m  calls=1
      ui-impact-analyst            6.0m  calls=1
      iteration-summarizer         4.7m  calls=1
      coherence-auditor            3.6m  calls=1
      orchestrator                 3.5m  calls=1
      demo-narrator                1.5m  calls=1
      [engine] full-pipeline     218.4m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                 17.5m
      OVER BUDGET at post-dev-fanout: 9072s > 3600s (mode=trim)
      overlap saved             16.6m  (parallel steps)
  goal-ops-hardening-iter-56  depth=lean  verdict=ESCALATE  wall=145.8m
      developer                   96.1m  calls=1
      goal-evaluator              17.5m  calls=1
      goal-decomposer             17.1m  calls=1
      browser-qa-agent             9.8m  calls=1
      reviewer                     4.9m  calls=1
      iteration-summarizer         4.1m  calls=1
      coherence-auditor            4.1m  calls=1
      browser-qa-replay            1.0m  calls=1
      [engine] lean-pipeline     111.0m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  8.4m
      OVER BUDGET at browser-qa: 7098s > 3600s (mode=trim)
      overlap saved              8.9m  (parallel steps)
  goal-ops-hardening-iter-57  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      developer                  175.2m  calls=3
      browser-qa-agent            69.2m  calls=1
      qa                          31.2m  calls=2
      reviewer                    20.2m  calls=3
      goal-decomposer             18.9m  calls=1
      auditor                     12.9m  calls=1
      ui-impact-analyst            5.7m  calls=1
      iteration-summarizer         5.5m  calls=1
      orchestrator                 2.8m  calls=1
      demo-narrator                1.4m  calls=1
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                 14.8m
      OVER BUDGET at post-dev-fanout: 10378s > 3600s (mode=trim)
  goal-ops-hardening-iter-57  depth=full  verdict=CONTINUE  wall=44.3m
      goal-evaluator              22.7m  calls=1
      auditor                     13.4m  calls=1
      coherence-auditor            4.5m  calls=1
      ux-regression-reviewer       3.7m  calls=1
      [engine] full-pipeline      17.1m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer)
      pump-wait                  1.8m
      unattributed (glue)        0.1m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-58  depth=lean  verdict=ESCALATE  wall=156.1m
      developer                   67.7m  calls=1
      browser-qa-agent            50.9m  calls=1
      coherence-auditor           26.4m  calls=1
      goal-decomposer             18.5m  calls=1
      goal-evaluator              14.9m  calls=1
      readme-maintainer           13.4m  calls=1
      iteration-summarizer         5.1m  calls=1
      reviewer                     3.7m  calls=1
      browser-qa-replay            1.9m  calls=1
      [engine] lean-pipeline     122.5m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                 10.9m
      OVER BUDGET at browser-qa: 5409s > 3600s (mode=trim)
      overlap saved             46.4m  (parallel steps)
  goal-ops-hardening-iter-59  depth=full  verdict=?  wall=?  (incomplete/interrupted attempt)
      goal-decomposer             14.9m  calls=1
      iteration-summarizer         4.9m  calls=1
      orchestrator                 3.2m  calls=1
      [engine] showcase-join       0.1m  (contains agent time above)
      pump-wait                  5.0m
  goal-ops-hardening-iter-59  depth=full  verdict=CONTINUE  wall=398.3m
      developer                  291.2m  calls=3
      browser-qa-agent            35.8m  calls=1
      qa                          34.5m  calls=2
      auditor                     22.9m  calls=2
      goal-evaluator              16.4m  calls=1
      reviewer                    11.8m  calls=3
      ui-impact-analyst            6.2m  calls=1
      coherence-auditor            2.7m  calls=1
      demo-narrator                2.0m  calls=1
      [engine] full-pipeline     379.1m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: goal-decomposer, ui-test-design, ux-regression)
      pump-wait                 27.4m
      OVER BUDGET at post-dev-fanout: 12962s > 3600s (mode=trim)
      overlap saved             25.3m  (parallel steps)
  goal-ops-hardening-iter-60  depth=lean  verdict=ESCALATE  wall=119.1m
      developer                   40.6m  calls=1
      browser-qa-agent            37.7m  calls=1
      goal-evaluator              18.8m  calls=1
      goal-decomposer             18.1m  calls=1
      iteration-summarizer         4.8m  calls=1
      reviewer                     3.6m  calls=1
      coherence-auditor            2.9m  calls=1
      browser-qa-replay            1.4m  calls=1
      [engine] lean-pipeline      82.1m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  8.0m
      OVER BUDGET at browser-qa: 3746s > 3600s (mode=trim)
      overlap saved              8.8m  (parallel steps)
  goal-ops-hardening-iter-61  depth=full  verdict=CONTINUE  wall=180.3m
      developer                   61.3m  calls=1
      browser-qa-agent            54.8m  calls=1
      qa                          19.4m  calls=1
      goal-evaluator              17.1m  calls=1
      auditor                     14.8m  calls=1
      iteration-summarizer        10.1m  calls=1
      goal-decomposer             10.1m  calls=1
      ui-impact-analyst            5.6m  calls=1
      orchestrator                 4.5m  calls=1
      reviewer                     4.4m  calls=1
      coherence-auditor            3.3m  calls=1
      demo-narrator                2.8m  calls=1
      [engine] full-pipeline     149.7m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                 19.1m
      OVER BUDGET at post-dev-fanout: 4830s > 3600s (mode=trim)
      overlap saved             27.7m  (parallel steps)
  goal-ops-hardening-iter-62  depth=lean  verdict=ESCALATE  wall=230.2m
      developer                  135.5m  calls=1
      browser-qa-replay           42.8m  calls=1
      goal-decomposer             21.3m  calls=1
      goal-evaluator              16.3m  calls=1
      browser-qa-agent            14.0m  calls=1
      iteration-summarizer         4.1m  calls=1
      coherence-auditor            2.8m  calls=1
      reviewer                     2.4m  calls=1
      [engine] lean-pipeline     192.5m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  4.8m
      OVER BUDGET at browser-qa: 9561s > 3600s (mode=trim)
      overlap saved              9.1m  (parallel steps)
  goal-ops-hardening-iter-63  depth=full  verdict=CONTINUE  wall=195.7m
      developer                   86.6m  calls=1
      auditor                     14.8m  calls=1
      goal-decomposer             14.3m  calls=1
      goal-evaluator              14.2m  calls=1
      qa                           7.6m  calls=1
      ui-test-designer             6.4m  calls=1
      iteration-summarizer         4.2m  calls=1
      reviewer                     4.2m  calls=1
      orchestrator                 3.2m  calls=1
      coherence-auditor            2.7m  calls=1
      browser-qa-agent             2.7m  calls=1
      demo-narrator                2.5m  calls=1
      ui-impact-analyst            1.3m  calls=1
      [engine] full-pipeline     164.3m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ux-regression)
      pump-wait                  6.1m
      OVER BUDGET at post-dev-fanout: 6508s > 3600s (mode=trim)
      unattributed (glue)       30.9m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-64  depth=lean  verdict=CONTINUE  wall=155.0m
      developer                   71.1m  calls=1
      browser-qa-replay           42.9m  calls=1
      goal-decomposer             17.2m  calls=1
      goal-evaluator              15.1m  calls=1
      reviewer                    10.7m  calls=1
      browser-qa-agent             8.4m  calls=1
      iteration-summarizer         4.7m  calls=1
      coherence-auditor            2.4m  calls=1
      [engine] lean-pipeline     122.5m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  4.9m
      OVER BUDGET at browser-qa: 5950s > 3600s (mode=trim)
      overlap saved             17.4m  (parallel steps)
  goal-ops-hardening-iter-65  depth=lean  verdict=CONTINUE  wall=153.4m
      developer                   71.3m  calls=1
      browser-qa-replay           42.4m  calls=1
      goal-evaluator              16.0m  calls=1
      browser-qa-agent            13.8m  calls=1
      goal-decomposer              9.7m  calls=1
      reviewer                     4.7m  calls=1
      iteration-summarizer         4.2m  calls=1
      [engine] lean-pipeline     127.6m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  4.4m
      OVER BUDGET at browser-qa: 5151s > 3600s (mode=trim)
      overlap saved              8.6m  (parallel steps)
  goal-ops-hardening-iter-66  depth=lean  verdict=CONTINUE  wall=158.8m
      developer                   77.5m  calls=1
      browser-qa-replay           42.5m  calls=1
      goal-evaluator              14.8m  calls=1
      goal-decomposer             12.2m  calls=1
      browser-qa-agent            11.6m  calls=1
      reviewer                     4.0m  calls=1
      iteration-summarizer         3.8m  calls=1
      coherence-auditor            3.0m  calls=1
      [engine] lean-pipeline     131.7m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  4.0m
      OVER BUDGET at browser-qa: 5634s > 3600s (mode=trim)
      overlap saved             10.6m  (parallel steps)
  goal-ops-hardening-iter-67  depth=lean  verdict=CONTINUE  wall=189.8m
      developer                  113.0m  calls=1
      browser-qa-replay           42.4m  calls=1
      goal-evaluator              14.1m  calls=1
      goal-decomposer             11.5m  calls=1
      browser-qa-agent             8.5m  calls=1
      reviewer                     6.7m  calls=1
      iteration-summarizer         4.3m  calls=1
      coherence-auditor            1.8m  calls=1
      [engine] lean-pipeline     164.1m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  4.6m
      OVER BUDGET at browser-qa: 7883s > 3600s (mode=trim)
      overlap saved             12.5m  (parallel steps)
  goal-ops-hardening-iter-68  depth=lean  verdict=CONTINUE  wall=191.4m
      developer                  109.8m  calls=1
      browser-qa-replay           42.5m  calls=1
      goal-evaluator              15.7m  calls=1
      browser-qa-agent            13.1m  calls=1
      goal-decomposer             10.0m  calls=1
      reviewer                     5.1m  calls=1
      iteration-summarizer         4.7m  calls=1
      coherence-auditor            2.1m  calls=1
      [engine] lean-pipeline     165.6m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  5.1m
      OVER BUDGET at browser-qa: 7506s > 3600s (mode=trim)
      overlap saved             11.8m  (parallel steps)
  goal-ops-hardening-iter-69  depth=lean  verdict=ESCALATE  wall=133.8m
      developer                   51.3m  calls=1
      browser-qa-replay           42.4m  calls=1
      goal-evaluator              17.3m  calls=1
      goal-decomposer             13.3m  calls=1
      browser-qa-agent             9.2m  calls=1
      reviewer                     5.8m  calls=1
      iteration-summarizer         4.9m  calls=1
      coherence-auditor            2.2m  calls=1
      [engine] lean-pipeline     103.0m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  5.2m
      OVER BUDGET at browser-qa: 4233s > 3600s (mode=trim)
      overlap saved             12.7m  (parallel steps)
  goal-ops-hardening-iter-70  depth=full  verdict=CONTINUE  wall=307.2m
      developer                  204.9m  calls=1
      auditor                     23.4m  calls=1
      reviewer                    16.9m  calls=1
      browser-qa-agent            15.2m  calls=1
      goal-evaluator              15.1m  calls=1
      goal-decomposer             13.8m  calls=1
      qa                           7.7m  calls=1
      ui-test-designer             6.3m  calls=1
      iteration-summarizer         5.2m  calls=1
      coherence-auditor            2.8m  calls=1
      demo-narrator                2.7m  calls=1
      orchestrator                 2.3m  calls=1
      ui-impact-analyst            1.5m  calls=1
      [engine] full-pipeline     275.4m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ux-regression)
      pump-wait                  8.8m
      OVER BUDGET at post-dev-fanout: 14285s > 3600s (mode=trim)
      overlap saved             10.6m  (parallel steps)
  goal-ops-hardening-iter-71  depth=lean  verdict=ESCALATE  wall=194.0m
      developer                   93.0m  calls=1
      browser-qa-agent            63.8m  calls=2
      goal-evaluator              19.4m  calls=1
      goal-decomposer             11.5m  calls=1
      coherence-auditor            8.5m  calls=1
      reviewer                     6.0m  calls=1
      iteration-summarizer         3.1m  calls=1
      browser-qa-replay            1.0m  calls=1
      [engine] lean-pipeline     162.9m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  3.6m
      OVER BUDGET at browser-qa: 6639s > 3600s (mode=trim)
      overlap saved             12.3m  (parallel steps)
  goal-ops-hardening-iter-72  depth=full  verdict=CONTINUE  wall=310.1m
      developer                  156.9m  calls=1
      browser-qa-agent            41.0m  calls=1
      goal-evaluator              22.9m  calls=1
      goal-decomposer             15.8m  calls=1
      auditor                     14.0m  calls=1
      qa                           8.9m  calls=1
      reviewer                     5.5m  calls=1
      iteration-summarizer         4.4m  calls=1
      orchestrator                 3.3m  calls=1
      coherence-auditor            3.0m  calls=1
      demo-narrator                2.1m  calls=1
      ui-impact-analyst            1.3m  calls=1
      [engine] full-pipeline     268.2m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                  6.2m
      OVER BUDGET at post-dev-fanout: 10902s > 3600s (mode=trim)
      unattributed (glue)       31.0m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-73  depth=lean  verdict=CONTINUE  wall=205.4m
      developer                  132.6m  calls=1
      browser-qa-agent            37.6m  calls=2
      coherence-auditor           28.2m  calls=1
      goal-evaluator              15.2m  calls=1
      goal-decomposer             12.7m  calls=1
      reviewer                     7.0m  calls=1
      iteration-summarizer         4.7m  calls=1
      browser-qa-replay            3.4m  calls=1
      [engine] lean-pipeline     177.4m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  5.1m
      OVER BUDGET at browser-qa: 9148s > 3600s (mode=trim)
      overlap saved             35.9m  (parallel steps)
  goal-ops-hardening-iter-74  depth=lean  verdict=CONTINUE  wall=177.4m
      developer                   57.3m  calls=1
      browser-qa-agent            44.2m  calls=2
      browser-qa-replay           43.3m  calls=1
      goal-evaluator              16.6m  calls=1
      goal-decomposer             15.7m  calls=1
      reviewer                     4.6m  calls=1
      iteration-summarizer         4.5m  calls=1
      coherence-auditor            2.2m  calls=1
      [engine] lean-pipeline     144.9m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  4.8m
      OVER BUDGET at browser-qa: 4667s > 3600s (mode=trim)
      overlap saved             11.0m  (parallel steps)
  goal-ops-hardening-iter-75  depth=lean  verdict=CONTINUE  wall=117.2m
      browser-qa-agent            38.5m  calls=1
      goal-evaluator              19.6m  calls=1
      goal-decomposer             14.2m  calls=1
      iteration-summarizer         4.5m  calls=1
      demo-narrator                1.8m  calls=1
      [engine] evidence-pipeline    83.3m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: developer, reviewer, coherence-auditor)
      pump-wait                  4.7m
      OVER BUDGET at coherence-auditor: 5853s > 3600s (mode=trim)
      unattributed (glue)       38.6m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-76  depth=lean  verdict=ESCALATE  wall=93.7m
      browser-qa-agent            19.4m  calls=1
      goal-evaluator              18.7m  calls=1
      iteration-summarizer         9.6m  calls=1
      goal-decomposer              9.6m  calls=1
      demo-narrator                1.9m  calls=1
      [engine] evidence-pipeline    65.3m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: developer, reviewer, coherence-auditor)
      pump-wait                  0.3m
      OVER BUDGET at coherence-auditor: 4504s > 3600s (mode=trim)
      unattributed (glue)       34.6m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-77  depth=full  verdict=ESCALATE  wall=357.9m
      developer                  185.1m  calls=2
      auditor                     54.9m  calls=2
      qa                          27.0m  calls=2
      goal-evaluator              17.5m  calls=1
      browser-qa-agent            11.6m  calls=1
      reviewer                    10.9m  calls=2
      iteration-summarizer         9.0m  calls=1
      goal-decomposer              9.0m  calls=1
      ui-impact-analyst            6.0m  calls=1
      orchestrator                 4.2m  calls=1
      coherence-auditor            3.5m  calls=1
      demo-narrator                2.5m  calls=1
      [engine] full-pipeline     327.7m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                  6.9m
      OVER BUDGET at post-dev-fanout: 7210s > 3600s (mode=trim)
      unattributed (glue)       16.6m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-78  depth=full  verdict=STALLED  wall=235.8m
      developer                   88.5m  calls=1
      auditor                     25.6m  calls=1
      qa                          23.1m  calls=1
      browser-qa-agent            20.1m  calls=1
      goal-evaluator              18.4m  calls=1
      goal-decomposer             13.4m  calls=1
      iteration-summarizer         8.2m  calls=2
      orchestrator                 5.7m  calls=1
      reviewer                     5.4m  calls=1
      ui-impact-analyst            5.0m  calls=1
      coherence-auditor            3.6m  calls=1
      demo-narrator                3.1m  calls=1
      [engine] full-pipeline     195.4m  (contains agent time above)
      [engine] showcase-join       0.1m  (contains agent time above)
      (resume-skipped: ui-test-design, ux-regression)
      pump-wait                  9.2m
      OVER BUDGET at post-dev-fanout: 6794s > 3600s (mode=trim)
      unattributed (glue)       15.5m  (wall − agents(active) − quota)
  goal-ops-hardening-iter-79  depth=lean  verdict=GOAL_ACHIEVED  wall=110.4m
      browser-qa-replay           42.3m  calls=1
      browser-qa-agent            24.2m  calls=1
      goal-evaluator              18.2m  calls=1
      goal-decomposer             10.2m  calls=1
      goal-evaluator-confirm       7.3m  calls=1
      developer                    4.2m  calls=1
      iteration-summarizer         3.8m  calls=1
      reviewer                     3.2m  calls=1
      [engine] lean-pipeline      70.8m  (contains agent time above)
      [engine] showcase-join       0.0m  (contains agent time above)
      (resume-skipped: coherence-auditor)
      pump-wait                  4.5m
      OVER BUDGET at coherence-auditor: 4864s > 3600s (mode=trim)
      overlap saved              3.0m  (parallel steps)
  session: 80 completed iteration(s), mean wall 215.3m
      total developer                 5813.3m
      total browser-qa-agent          2477.9m
      total goal-evaluator            1279.5m
      total goal-decomposer           1140.4m
      total reviewer                  1002.2m
      total auditor                    855.8m
      total qa                         826.7m
      total iteration-summarizer       642.5m
      total browser-qa-replay          397.1m
      total coherence-auditor          349.0m
      total ui-impact-analyst          240.3m
      total orchestrator               140.7m
      total readme-maintainer           82.7m
      total ui-test-designer            78.0m
      total demo-narrator               60.9m
      total ux-regression-reviewer      27.8m
      total goal-evaluator-confirm       7.3m
      total AWAITING_PUMP paused gaps: 12.4m
      halts: AWAITING_PUMP, AWAITING_PUMP, REGRESSION_HALT, BUDGET_EXHAUSTED, REGRESSION_HALT, STALLED, DECOMPOSER_FAILED, STALLED, STALLED, AWAITING_PUMP, machine_reset, AWAITING_PUMP, REGRESSION_HALT, machine_reset, machine_reset, machine_reset, machine_reset, machine_reset, machine_reset, machine_reset, machine_reset, STALLED
```
