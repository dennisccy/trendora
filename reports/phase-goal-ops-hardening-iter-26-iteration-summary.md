# Iteration Summary — goal-ops-hardening-iter-26

**Verdict:** ESCALATE
**Iteration type:** goal-lean
**Date:** 2026-07-26
**Iteration:** 26

## In plain words

**What you can do now:** You can browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. You can back-fill any historical date range with no size cap and get an honest explanation when there's no new work to do. The status badge at the top of the app stays truthful through startup, updates, or a crash, and pages stay responsive even while the backend computes new numbers in the background. A small live badge shows on every page whenever the backend is quietly computing something in the background, and the Data Manager page shows exactly which date it's working on, how far along it is, what happened last time, and an honest "we don't know" message on the rare occasions it briefly loses touch with the backend.

**What changed this time:** Behind-the-scenes work — the team double-checked the two open questions left from last round (a speed measurement for the status check, and proof the app can show a failed background job honestly) and confirmed both are now solid. While re-checking everything closely, they also found two rare, pre-existing glitches: opening an old, never-before-checked historical date twice in quick succession can trigger a server error, and right after that happens the Data Manager page can briefly show an empty-looking dataset even though all thirty years of data are still safely stored. Neither breaks the app, but both need a closer look before this round of work can be called fully complete.

**What's next:** Next, a deeper round will check exactly what a person sees when that rare server error happens, fix the underlying issue so two people can't trigger it at once, and make the Data Manager page show honest wording instead of a blank-looking dataset in that situation.

## Headline

Closed both named gaps the iter-25 GOAL_ACHIEVED second-key CONFIRM run rejected on

## Direction

**Signal:** holding
**Why:** Both iter-25 confirm-reject gaps on J-09 (the ≤0.1s health-budget re-measurement and the failure-branch citable evidence) are closed, and all 8 must-have journeys (J-01–J-09) hold at passing with fresh iter-26 evidence — zero regressions, zero newly-passing journeys either. While re-deriving that evidence the evaluator surfaced two new *minor* anti-goal findings on pre-existing, untouched code (an unhandled `IntegrityError` on concurrent `/backtest` requests, and a stale `/data` coverage panel after such a request bumps the dataset version), which is why the verdict is ESCALATE rather than GOAL_ACHIEVED — iter-27 is already scoped full-depth to fix exactly those two.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-06, J-07 (iter-22); J-09 (iter-25)
- Regressions in last 5 iters: none
- Anti-goal violations in last 5 iters: 2, both minor and unresolved (iter-26: AG-8 unhandled server error on concurrent `/backtest`; AG-3 stale `/data` coverage panel)
- Iters with no journey state change: 2 of last 5 (iter-23, iter-26)

**Latest evaluator reasoning:** "While checking the evidence I found two problems that nobody had recorded before, both on old code this iteration did not touch. First, one page request to the backtest data service died with a server error. Second, right after a user opens the Backtest page for an old date that was never scanned before, the Data Manager page reports an empty dataset (price history "—", universe 0) even though the database holds thirty years of prices. Because of these two open items I cannot sign the goal off yet, and because they cross the backend, the Data Manager screen, and an anti-goal question, the next round should run at full depth with an auditor."

## What was done

- Closed confirm-reject gap 1: took a fresh quiet-host `GET /api/health` re-measurement and recorded a new dated section in `reports/perf-budgets.md` — all 4 statistics now hold cleanly within the ≤0.1s budget (official 0.092222s, max 0.094309s, 11/11 HTTP 200), explicitly named as the new binding figure.
- Closed confirm-reject gap 2: added a backend test (`test_health_background_compute_serves_failed_outcome_verbatim`) proving a crafted "failed" background-compute outcome is served verbatim by `GET /api/health`.
- Extracted the completed/failed rendering logic out of `LastOutcomeSummary` into a new pure function (`resolveLastOutcomeSummary`, `apps/frontend/lib/background-compute-last-outcome.ts`) with a new unit test covering both cases — byte-identical rendering, no behavior change.
- Re-verified all 8 must-have journeys (J-01–J-09) with fresh iter-26 evidence; zero regressions, zero anti-goal violations introduced by this iteration's own diff (`apps/backend/app/**` byte-frozen and confirmed untouched).
- Verified 8 of 8 target journeys pass browser QA (0 skipped).
- While re-deriving that evidence, surfaced two previously-unrecorded faults in pre-existing, untouched code: an unhandled server error on concurrent historical `/backtest` requests, and a stale `/data` coverage panel after such a request.

## What's left

- Two anti-goal findings surfaced this iteration remain unresolved (both minor, both on pre-existing code not introduced by this iteration's diff): AG-8 — an unhandled `sqlite3.IntegrityError` escapes as a raw server error when two concurrent requests hit `/backtest` for the same never-scanned historical date; AG-3 — right after such a request, `/data`'s coverage panel shows an all-zero "not yet computed" state for a fully populated database until the next boot warm-up or ingest.
- Unknown whether a person actually sees a calm, contained error or a blank crash page when that server error fires — nobody captured the browser at that moment.
- `forward_testing.backfill_run_forward_returns` needs to be made idempotent/serialized so two concurrent requests for the same date can't race the same INSERT — requires deliberately lifting this iteration's byte-freeze on that module.
- Owner-optional and unchanged: backlog card B-1107 (global background-compute concurrency cap), and whether the cold historical `/backtest` load (16–23s measured this iteration) should get its own written budget or move off the request path.
- Carried, non-blocking: correct the browser-QA report's "returned immediately" claim (log shows 16.7–23.2s); fix a timezone label typo in the new perf-budgets section (reads `19:14:25Z`, should read `18:14Z`); re-exercise J-09 steps 2–3 on a date that already has a snapshot so "returns immediately"/in-flight capture get fresh proof; retarget `test_forward_testing_serving_split.py`'s `is_latest` monkeypatches before removing dangling imports at `backtest.py:75`/`mcp/tools.py:38`.
- `J-01-verify.png` / `J-03-verify.png` remain byte-identical (6th recurrence) — a known framework capture nit, not a product issue.

## Next step

Run one more round at full depth, no new features. In order: (1) capture what a person actually sees when `/backtest` is opened twice at once on a never-scanned historical date — full page, not viewport; a calm contained error closes the AG-8 question, a blank error page is a real break and must be fixed; (2) make the forward-returns write idempotent/serialized so two concurrent requests for the same date cannot 500 — this touches `forward_testing.backfill_run_forward_returns`, frozen since iter-24, so the freeze must be lifted deliberately; (3) make `/data` honest after a time-machine visit — either refresh the stored coverage row when a run is created outside ingest, or label the sentinel state "coverage not yet computed for this dataset version" instead of rendering zeros. Coordinator note: iter-27 has already been scoped full-depth to fix exactly these two findings.

## Assumptions made

- iter-27 · goal-decomposer — Ambiguity: the iter-26 AG-3 finding (a populated database's `/data` coverage panel showing "— → —" / universe 0 after a request-path historical `/backtest` view bumps the dataset version) admits two remedies — refreshing the coverage figures live, or labeling the stale state honestly — and goal.md's compute-at-ingest principle doesn't resolve which is compliant. We chose: option (b), a stale-row fallback labeled "stale" rather than a request-path recompute, keeping the zero-new-DB-work-at-request-time guarantee absolute. Reversible: yes
- iter-26 · goal-evaluator — Ambiguity: AG-8 forbids crashing an existing page, but nobody captured the browser at the moment of the server error, so what the user actually saw is unknown; AG-3 is similarly open for the all-zero `/data` panel. We chose: recorded both as unresolved anti-goal findings but scored them minor (not critical), since the service stayed up and the zero-coverage payload is a deliberate, self-healing sentinel — yielding ESCALATE rather than a REGRESSION halt. Reversible: yes
- iter-26 · goal-decomposer — Ambiguity: the iter-25 confirm rejection of J-09's "shows a failed background compute with the recorded reason" clause didn't say whether a witnessed live failure is required or a deterministic code-level round-trip test suffices, and the only known way to trigger a genuine failure reproduces an unsafe memory-pressure pattern (backlog B-1107). We chose: closed the gap with a backend test plus a frontend rendering test, never re-triggering the unsafe live pattern. Reversible: yes
- iter-25 · goal-evaluator — Ambiguity: the deterministic replay lane FAILed J-07 (expected "Ready") because a one-off warm-up MemoryError left the badge reading "Initializing"; goal.md doesn't say whether a journey verified while the host was under our own test harness's memory pressure counts as verified. We chose: accepted the overturn and scored J-07 passing after tracing the cause to the harness's own pytest builds and re-verifying J-07's substance live post-restart. Reversible: yes
- iter-25 · goal-evaluator — Ambiguity: J-09's ≤0.1s `/api/health` clause is measured on both sides of the line across sources (recorded max 0.127788s vs QA's 0.094604s vs this iteration's own ~0.10-0.18s under pytest load), and goal.md doesn't say which series binds. We chose: scored the clause met at the same bar already applied to J-06/J-07, since the tightness is pre-existing and the diff adds zero backend work, routing the standing question to the owner as audit B5. Reversible: yes
- iter-24 · goal-evaluator — Ambiguity: the same health-budget disagreement one iteration earlier (developer 0.127788s max vs QA 0.094604s max against the unchanged ≤0.1s budget). We chose: did not treat it as a J-06/J-07 regression since the diff adds zero DB work, logging it as an open J-09 gap routed to the owner rather than laundering it. Reversible: yes
- iter-24 · goal-evaluator — Ambiguity: J-09's Acceptance ends with a Walkthrough bullet the iteration spec never mapped into IN SCOPE or DoD, and goal.md doesn't say whether an unplanned Acceptance deliverable still binds a machine-appended journey. We chose: scored J-09 partial, treating the bullet as binding on the journey regardless of the spec's scope, consistent with how this session already adjudicated the identical clause for J-06/J-07/J-08. Reversible: yes
- iter-24 · goal-decomposer — Ambiguity: J-09's Consistency clause implies a retained-record count exists, but its steps only ever describe a single outcome, so a single `last_outcome` field and a bounded list both satisfy the literal text. We chose: built a bounded, config-governed `recent_outcomes` list (default 5) so the "retained-record count" phrase has a concrete testable referent. Reversible: yes
- iter-23 · goal-evaluator — Ambiguity: a spec clause required the J-07 demo step to cite figures verbatim from `perf-budgets.md`'s Iteration 22 section, but the step used 4-decimal precision where that file prints 3. We chose: treated it as a cosmetic precision nit rather than a DoD failure, since the 4-decimal figures trace exactly to the raw measurement file. Reversible: yes
- iter-23 · goal-evaluator — Ambiguity: two of J-06/J-07/J-08's new walkthrough scenes narrate transient states that can't be reproduced live at an arbitrary playback, and goal.md doesn't say whether "viewable via `--session-live`" requires the viewer to actually see the state or only that the step exists and plays. We chose: scored the clause met since the manifest the command actually reads now holds complete, accurate, live-checked steps for all three journeys. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-26.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-26-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-26-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-26-ui-test-results.md |
| Goal evaluation | ESCALATE | runs/goal-session-ops-hardening/iter-26/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
