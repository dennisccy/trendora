# Iteration Summary — goal-ops-hardening-iter-14

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-23
**Iteration:** 14

## In plain words

**What you can do now:** Browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. Back-fill any historical date range with no size cap and get an honest explanation when there's no new work to do. Trust the status badge to tell the truth while the app is starting up, updating its data, or recovering from a crash — and see an honest record of real progress even if an update gets interrupted mid-way. Two pages (the Data page's index/benchmark list, and the home page's chart) load quickly rather than sluggishly.

**What changed this time:** Behind-the-scenes work — nothing new to click. The team rewrote the background calculation that had twice caused the whole app to freeze up for minutes during heavy data updates (once needing a manual restart) so it uses far less memory, and proved with real stress tests — including running the heaviest possible update on the actual full-size dataset — that it no longer runs out of memory or freezes. They also proved, with a real scheduled crash-and-restart, that the status badge keeps telling the truth through a crash. One rough edge turned up while testing: opening the Backtest page during that same heavy update can still take a few minutes to show results (it never shows an error, just a wait).

**What's next:** Next, the team will track down why the Backtest page is slow to load during heavy background updates, while the product owner decides on a recorded walkthrough video and whether the freeze-fix needs one more, tougher stress test before this chapter is considered finished.

## Headline

Memory-safe rewrite of forward-aggregate reads resolves the AG-8 outage defect (iter-13 REGRESSION recovery)

## Direction

**Signal:** holding
**Why:** This iter resolved the critical AG-8 anti-goal that drove iter-13's REGRESSION halt — the unbounded `ForwardReturn`/`ScannerResult` reads in `forward_testing.py` are now streamed, and the exact full-deep-basis warm that failed 3-for-3 in iters 11-13 completed cleanly (250/250 health checks, 61.8% memory margin). No journey newly crossed into "passing" this iteration (J-01/J-03/J-04/J-05 were already passing; J-06 and the new J-07 both stay "partial" on an unproduced walkthrough plus a fresh UT-04 latency finding), so the strict newly-passing signal reads as holding even though the session's worst blocker is now cleared and the next step is a concrete engineering fix (root-causing UT-04) rather than a stalled wait on the owner.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-04 (at iter-10)
- Regressions in last 5 iters: iter-13 (REGRESSION verdict — AG-8 escalated to a ~12-min full availability outage; no journey itself flipped passing→failing)
- Anti-goal violations in last 5 iters: 1 critical (AG-8 — active/firing iters 10-13, escalated to a full outage at iter-13, RESOLVED at iter-14) + 1 minor (AG-10 — fired iter-10, resolved iter-11)
- Iters with no journey state change: 3 of last 5

**Latest evaluator reasoning:** "The REGRESSION-recovery iteration succeeded at its stated purpose: the session-long critical AG-8 defect (unbounded whole-partition ORM reads in compute_forward_aggregates that wedged the backend into full availability outages in iter-7 and iter-13) is resolved — the two .all() reads are now column-projected yield_per-streamed in place, byte-identity is proven (32/32), and the first successful full-deep-basis 5-horizon warm at this basis size completed with /api/health 250/250 HTTP 200 and a flat VmPeak of 2,404,408 KB (61.8% margin under the 6,291,456 KB cap) — all three headline numbers recomputed by me directly from the retained CSVs. J-04 was additionally re-verified LIVE end-to-end this iteration."

## What was done

- Rewrote `compute_forward_aggregates`'s two whole-partition ORM reads to column-projected, `yield_per`-streamed access — proven byte-identical to the prior output across all 5 horizons and both as-of variants (32/32 tests).
- Proved the fix closes the memory problem with a real (non-monkeypatched) tightened-memory-cap induction test: the old unbounded read fails honestly under the cap; the rewrite succeeds under the identical cap.
- Proved the fix survives concurrent load: a 4-thread-plus-diagnostic-read concurrency test (mirroring iter-13's actual outage trigger shape) completes in ~7-10s with zero hangs and byte-identical results.
- Ran an operator-supervised full-deep-basis warm: 250/250 health polls HTTP 200, peak VmPeak 2,404,408 KB (61.8% margin under the 6144 MB cap) — the first time this data size has completed this warm (iters 11-13 failed 3-for-3 with MemoryError).
- Re-verified J-04 live end-to-end via a real operator kill/restart cycle, closing the "carried, not re-verified" gap open since iter-12.
- Transcribed iter-13's already-confirmed J-06 page-load readings into the canonical `reports/perf-budgets.md`.
- Verified 4 target journey(s) (J-01, J-03, J-04, J-05) pass browser QA this iteration; J-06 and J-07 remain partial.

## What's left

- Journey J-06 (Pages load only what they need) partial — the `demo.sh --session-live` walkthrough is still unproduced, and the new UT-04 finding (`/backtest` cache-miss resolving in 211.8s under concurrent load) leaves its budget question open.
- Journey J-07 (Heavy aggregates never take the service down) partial — TC-6's live-process induced-pressure test was not literally executed (judged an unjustified hazard on this crash-history host); UT-04's 211.8s concurrent-warm cache-miss and the unproduced walkthrough also keep it open.
- Root-cause UT-04's 211.8s `/backtest` resolution under a concurrent forward-aggregate warm (hypothesis: the new streamed read may hold a longer cursor/lock window than the old read) — the substantive item between J-07 and passing.
- Spot-check `/stocks`, `/sectors`, `/scanner-runs`, `/evidence` for the same latency pattern under a concurrent warm — only `/backtest` was measured live this iteration.
- Owner decision: produce or formally waive the `[NEW] demo.sh --session-live` walkthrough that J-05/J-06/J-07's Acceptance names — no autonomous mechanism exists to produce it.
- Owner/evaluator follow-up: decide whether a live-process memory-pressure induction is still owed for TC-6, beyond the synthetic-subprocess plus organic-absence evidence already ruled reasonable.
- Non-blocking: the per-horizon heartbeat cadence (`data_manager.py:3220`) is outpaced ~9x by data growth, causing a self-recovering "possibly stalled" reading during long warms (UT-10, P3).
- Carried, unrelated: `tests/test_db.py::test_create_all_produces_expected_tables` pre-existing failure.

## Next step

FULL depth, focused follow-up — no new features. (1) AGENT: root-cause UT-04's 211.8s `/backtest` cache-miss during a concurrent forward-aggregate warm (hypothesis: the streamed read holds a longer read-lock/cursor window under concurrent writes than the old fetch-and-release read) — the exact iter-13 trigger shape neither TC-4 nor TC-5 reproduces; also spot-check `/stocks`/`/sectors`/`/scanner-runs`/`/evidence` under a concurrent warm, and consider an elapsed-time affordance on `/backtest`'s skeleton. This is what stands between J-07 and passing. (2) OWNER DECISIONS (each independently blocks GOAL_ACHIEVED): the `[NEW] demo.sh --session-live` walkthrough J-05/J-06/J-07 Acceptance names (no autonomous mechanism); whether TC-3's synthetic-subprocess induction plus TC-5's organic absence suffice for TC-6, or an operator-authorized live-process induction is still owed. (3) AGENT non-blocking cleanup: the UT-10 per-horizon heartbeat cadence, and reconciling a stale line in `implementation-summary.md`. Carried: the pre-existing `test_db.py::test_create_all_produces_expected_tables` failure (unrelated).

## Assumptions made

- iter-14 · goal-evaluator — Ambiguity: UT-04 shows the same concurrent-load trigger that caused iter-13's REGRESSION still produces a 211.8s `/backtest` anomaly, so whether AG-8 is fully resolved is unclear. We chose: marked AG-8 RESOLVED — UT-04 is a latency/lock-contention issue (self-resolving, no crash, no memory exhaustion), a distinct non-critical follow-up, not a continuation of the memory-exhaustion/crash defect the anti-goal forbids; kept J-06/J-07 partial on it instead. Reversible: yes
- iter-14 · goal-evaluator — Ambiguity: TC-6's literal test (induce memory pressure on the live TC-5 process) was not executed — the operator judged it an unjustified hazard on this crash-history host; is a real induction on a synthetic fixture plus TC-5's organic absence of failure enough for J-07 step 4? We chose: ruled the two-leg evidence reasonable and did not treat it as a hard blocker, but also did not upgrade it to a literal pass — J-07 stays partial (independently held there by UT-04 and the unproduced walkthrough too). Reversible: yes
- iter-14 · goal-decomposer — Ambiguity: whether "operator-supervised" for the J-07 heavy measurement pass means the agent runs the confined measurement itself or the human must literally type the launch command. We chose: the standard path is the developer/reviewer running the confined pass directly (mirroring iter-3/8/9's own precedent), with an explicit operator-fallback only if the environment blocks the process start. Reversible: yes
- iter-14 · goal-decomposer — Ambiguity: J-07 step 4 permits a test hook OR a monkeypatched cap, but the repo's existing monkeypatch-only tests already missed iter-11's live 500s and iter-13's live wedge — does goal.md require a stricter real induction and concurrent-caller test? We chose: required BOTH a real (non-monkeypatched) tightened-`ulimit -v` subprocess test AND a concurrent-caller (N>=4) test mirroring iter-13's actual trigger shape — a stricter reading than the letter of step 4. Reversible: yes
- iter-13 · goal-evaluator — Ambiguity: whether escalating AG-8 from a "silent internal abort" (iter-12) to a "full ~12-minute outage requiring a hard restart" counts as newly-discovered damage (fire REGRESSION) or just a re-observation of the same carried, already-deferred bug (continue, as iters 11/12 did). We chose: fired REGRESSION — the specific "blast radius smaller, mitigation holds" rationale iters 11/12 used to withhold the halt is directly falsified this iteration, and availability is the exact guarantee this goal exists to protect. Reversible: yes
- iter-12 · goal-evaluator — Ambiguity: decision-tree C.1 says an unresolved critical anti-goal fires REGRESSION; AG-8 is unresolved and fired live again (3-for-3) this iteration. We chose: did not fire REGRESSION — the product diff is literally empty and the blast radius was smaller than iter-11 (caught internally, zero client-facing 500s), so nothing was introduced or worsened; recorded it critical+unresolved so it still blocks GOAL_ACHIEVED. Reversible: yes
- iter-12 · goal-evaluator — Ambiguity: J-06's "assert every measurement is within budget" success criterion conflicts with its "honest status" clause, which tolerates a slow-but-honest degrade; `/api/indexes` is 43-51% over budget on an idle host but the page still renders fully. We chose: read the budget requirement as the primary gate and the honest-status clause as a defensive fallback, so scored J-06 partial, not passing, rejecting the audit's "may be scored passing" recommendation. Reversible: yes
- iter-12 · goal-decomposer — Ambiguity: every decomposer since iter-4 scoped the `demo.sh --session-live` walkthrough out of developer scope on the belief it "self-resolves automatically," but no such automatic session-mode pass exists anywhere in `run-goal.sh`. We chose: kept it out of developer scope (same outcome) but stopped repeating the disproven "self-resolves" framing, and logged it as a standing owner-decision item instead. Reversible: yes
- iter-11 · goal-evaluator — Ambiguity: J-04's steps 3-4 (crash/boot behavior) were not re-driven this iteration — only carried from iter-9's simulations — while the methodology calls for evidence from the scoring iteration itself. We chose: kept J-04 passing, since the entire code surface those steps exercise is provably byte-unchanged since iter-9 and the other steps were freshly re-run this iteration. Reversible: yes
- iter-11 · goal-evaluator — Ambiguity: J-05's replay runs recorded only four of the five named inventory-aggregate categories (forward_aggregates missing due to its MemoryError abort) — does an aggregate outside the named five failing to warm break J-05's contract? We chose: kept J-05 passing — forward_aggregates isn't one of the five the step names and the run record is honestly labeled; scored the unbounded-load issue under AG-8 instead of double-counting it as a journey failure. Reversible: yes
- iter-11 · goal-evaluator — Ambiguity: whether AG-8 firing live this iteration (two ingest-warm MemoryErrors, two on-load HTTP 500s), unlike iters 8-10 where it was merely carried, counts as "newly discovered damage" that should fire the literal REGRESSION halt. We chose: did not fire REGRESSION — the product diff is literally empty so nothing could have been introduced/worsened, and the human already deferred this exact code path three times; returned ESCALATE instead so a full-pipeline auditor could adjudicate the blast radius. Reversible: yes

## Quick verify

From `reports/phase-goal-ops-hardening-iter-14-what-to-click.md`:

1. Open `http://localhost:3255/data` in your browser
2. Scroll to the card titled "Rebuild snapshots for current universe." Read the date shown in parentheses after "...in the latest snapshot"
3. Scroll back up to "Start a fetch / backfill job." Type DATE_X into both the "Start date" and "End date" fields, choose "Backfill snapshots" from the "Job kind" dropdown, then click "Start"
4. For the next several minutes, glance at the top-bar readiness badge every 30 seconds or so (it's on every page, so you don't need to stay on `/data`)
5. While that job is still running, open a second browser tab and navigate to `http://localhost:3255/backtest`

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-14.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-14-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-14-review.md |
| Browser QA | FAIL | reports/phase-goal-ops-hardening-iter-14-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-14-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-14-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-14-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-14-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-14-ui-test-plan.md |
| UX regression | UX-REGRESSION-WARN | reports/phase-goal-ops-hardening-iter-14-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-14-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-14-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-ops-hardening-iter-14-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-14/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
