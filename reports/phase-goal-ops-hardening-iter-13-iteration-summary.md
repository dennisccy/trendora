# Iteration Summary — goal-ops-hardening-iter-13

**Verdict:** REGRESSION
**Iteration type:** goal-full
**Date:** 2026-07-23
**Iteration:** 13

## In plain words

**What you can do now:** Browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. You can back-fill any historical date range with no size cap and get an honest explanation when there's nothing new to add, trust that back-to-back heavy data updates won't slow the app down, see the status badge tell the truth during startup, a data update, or a crash, and trust that a mid-update crash leaves an honest record of real progress rather than a false "nothing happened."

**What changed this time:** The page listing index and benchmark data sources, and the home page's chart, now load about ten times faster than before — a previously-confirmed slow spot (a bit over two seconds) is now well under half a second. But while testing that fix, the same rare background memory problem seen in earlier rounds got dramatically worse: it froze the entire app for about ten minutes with nothing responding, and needed a manual restart to recover. That's a real step backward from the smaller, contained hiccups seen before, so the team is treating this round as a setback rather than a finished win.

**What's next:** Next, the owner needs to decide how to permanently fix or clearly limit that memory problem — now that it's proven capable of freezing the whole app — before this chapter can be marked complete.

## Headline

Index-page cache fix confirmed in budget, but testing exposed a ~12-minute full backend outage.

## Direction

**Signal:** regressing
**Why:** The iter-13 IndexSeriesCache fix closed the last agent-owned J-06 gap — real-Chrome readings fell from iter-12's confirmed 2138.7-2257.7ms to 218.7/218.7/219.2ms on `/data` and 70.5ms on `/`, all comfortably in budget — and J-01/J-03/J-05 re-verified passing via golden replay. But the critical AG-8 anti-goal (the unbounded `forward_testing.py:826` load, byte-unchanged this iteration) escalated under concurrent test load from a caught internal abort into a ~12-minute full backend availability outage requiring an operator hard-restart, corroborated by the audit, the closure verdict, and a screenshot of the frozen UI — the evaluator fired REGRESSION under decision-tree C.1 even though no journey moved passing→failing.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-01, J-03, J-04, J-05 (iter-9: J-01/J-03/J-05; iter-10: J-04)
- Regressions in last 5 iters: iter-13 (anti-goal REGRESSION — no journey moved passing→failing; the standing critical AG-8 violation escalated to a full-outage severity)
- Anti-goal violations in last 5 iters: 3 recorded — 2 critical (iter-9 AG-8 unresolved, still open; iter-13 AG-8 new escalation record, same underlying dimension, now proven full-outage-capable), 1 minor (iter-10 AG-10, resolved iter-11)
- Iters with no journey state change: 3 of last 5 (iter-11, iter-12, iter-13 — J-06 stayed `partial` in its status label each time, despite real underlying progress)

**Latest evaluator reasoning:** "The iteration's own target succeeded decisively... The specific over-budget finding that held J-06 at `partial` is genuinely closed. BUT this iteration also demonstrated the standing critical AG-8 `MemoryError` (`forward_testing.py:826`, byte-unchanged) firing at full-availability-outage severity: ... it wedged the entire backend into a ~12-minute futex deadlock — `GET /api/health` unresponsive, UI frozen on 'Checking backend…' with blank cards — requiring an operator hard-restart. Decision-tree C.1 (unresolved critical anti-goal, this iteration escalated to newly-discovered full-outage damage) → REGRESSION."

## What was done

- Implemented `IndexSeriesCache`, an ingest-time-warmed cache for the index-chart's default hot key (`GET /api/indexes?full=true`), serving the Dashboard and Data Manager pages from a precomputed store instead of recomputing on every request.
- Confirmed the fix on real-Chrome measurement, not just on the code: hot-key latency fell from iter-12's 2138.7-2257.7ms to 218.7/218.7/219.2ms on `/data` and 70.5ms on `/`, all within the 1.5s budget with ~7x margin on a verifiably idle host.
- Added 68 new backend tests (cache hit/miss/self-heal, invalidation on new bars, byte-identity, honest `aggregates_refreshed` gating, MemoryError isolation) — all passing; confirmed `forward_testing.py` byte-unchanged (TC-12).
- Verified 3 journeys (J-01, J-03, J-05) pass browser QA via deterministic golden replay; carried J-04 passing on the byte-unchanged boot-path argument (not re-driven live this iteration).
- Audit and closure both independently traced the routing/invalidation/honesty logic line-by-line and scored the fix on the number, not the code — no CRITICAL or IMPORTANT defects found.
- During this iteration's own testing, the standing critical AG-8 memory bug escalated from a silent internal abort to a ~12-minute full backend availability outage (health unresponsive, UI frozen on "Checking backend…", operator hard-restart required) — driving the REGRESSION verdict under the anti-goal clause.

## What's left

- Journey J-06 ("Pages load only what they need") stays `partial` — the over-budget blocker is genuinely closed, but `reports/perf-budgets.md` doesn't yet carry the passing readings, the AG-8 outage produced exactly the frozen/blank frame its honest-status clause forbids, and the session-live walkthrough is unproduced.
- Critical anti-goal AG-8 (unbounded `forward_testing.py:826` load) remains unresolved and is now proven capable of a full ~12-minute availability outage requiring a manual restart — hard-blocks GOAL_ACHIEVED and drove this iteration's REGRESSION.
- Owner decision needed on AG-8: scope a bounded/streamed rewrite, amend goal.md to accept the graceful-abort behavior explicitly while requiring fail-fast to an honest "Backend unavailable" plus automatic recovery, or raise the cap — a sixth silent deferral is no longer defensible.
- Owner decisions still outstanding: `HOST_GUARD_REQUIRE_MARKERS`, and the `demo.sh --session-live` walkthrough for J-05/J-06 (no autonomous mechanism produces it).
- J-04 was not re-verified live this iteration (carried passing on the byte-unchanged boot-path argument) — needs a live kill/restart spot-check.
- Small agent-tractable cleanup: transcribe the passing 218.7/218.7/219.2/70.5ms readings into `reports/perf-budgets.md`; retire or rewire the dead `major-indexes-card.tsx` so UT-07 stops failing OVERALL against unreachable code.
- Framework maintainer items unfixed: `merge_ui_test_results.py` drops the raw `.llm.md`'s emphasised `**FAIL**` cell; the `Frontend Present: no` browser-qa-skip misrouting.

## Next step

Halt for human review, then resume with `--acknowledge-regression` into a full-depth recovery iteration. Owner decisions (each independently hard-blocks GOAL_ACHIEVED): (1) AG-8 — scope a bounded/streamed rewrite of `forward_testing.py:826`, OR amend goal.md to accept the graceful-abort behavior explicitly while requiring fail-fast to an honest "Backend unavailable" with automatic worker-pool recovery (never a 12-minute wedge), OR raise the cap (does not fix the pattern) — a sixth silent deferral is no longer defensible now that the bug is proven to cause a full outage. (2) `HOST_GUARD_REQUIRE_MARKERS`. (3) The `demo.sh --session-live` walkthrough for J-05/J-06. Agent-tractable, non-blocking cleanup for the recovery iteration: transcribe the passing readings into `reports/perf-budgets.md`, add a live J-04 boot spot-check, and retire/rewire the dead `major-indexes-card.tsx` component.

## Assumptions made

- iter-13 · goal-evaluator — Ambiguity: decision-tree C.1 reads "an unresolved critical anti-goal → REGRESSION," but iters 11/12 established a doctrine that the halt only fires for damage introduced/worsened/newly-discovered by this iteration's own code, and the AG-8 code path is byte-unchanged here — the trigger was concurrent test load, not this iteration's diff, so whether the severity escalation counts as "newly discovered" was a genuine call. We chose: fired REGRESSION, treating the escalation from a silent internal abort (iter-12) to a full ~12-minute outage (iter-13) as newly-discovered damage that materially changes the deferred decision's stakes, corroborated by three independent artifacts. Reversible: yes
- iter-12 · goal-evaluator — Ambiguity: decision-tree C.1 says an unresolved critical anti-goal violation halts on REGRESSION; AG-8 was unresolved and fired live again this iteration. We chose: did not fire REGRESSION (same reading as iters 8-11), since the product diff was literally empty and the blast radius was smaller than iter-11's; recorded it critical + unresolved so it still hard-blocks GOAL_ACHIEVED. Reversible: yes
- iter-12 · goal-evaluator — Ambiguity: J-06's step 2 requires "assert every measurement is within budget," but the Acceptance's honest-status clause allows degrading gracefully even if over budget — pulling in opposite directions on whether J-06 can pass. We chose: read the budget assertion as the primary gate and scored J-06 `partial`, not `passing`, rejecting the audit's "may be scored passing" recommendation. Reversible: yes
- iter-12 · goal-decomposer — Ambiguity: every decomposer since iter-4 assumed the session-live demo walkthrough would "self-resolve automatically," but grepping `run-goal.sh` shows no automatic session-mode pass exists anywhere, including on the GOAL_ACHIEVED path. We chose: kept the walkthrough out of scope (same outcome as before) but stopped the "self-resolves" framing, recording it as an explicit parallel owner-decision item alongside AG-8. Reversible: yes
- iter-11 · goal-evaluator — Ambiguity: J-04's steps 3-4 weren't re-driven this iteration since the browser agent is barred from service actions, and methodology says status should rest on evidence from the scoring iteration. We chose: kept J-04 `passing` because the product diff is literally empty, so the code those steps exercise provably hasn't changed since iter-9 verified it. Reversible: yes
- iter-11 · goal-evaluator — Ambiguity: J-05's step 2(b) names five aggregates its finalize hooks must refresh, and replay runs recorded only four (`forward_aggregates` missing to a memory error), with goal.md silent on whether that breaks acceptance. We chose: kept J-05 `passing` since `forward_aggregates` isn't among the five named aggregates and the run record is honest about what it did and didn't refresh; the unbounded-load issue is scored under AG-8 instead. Reversible: yes
- iter-11 · goal-evaluator — Ambiguity: decision-tree rule C.1 reads "a critical anti-goal violation is unresolved → REGRESSION," and the carried AG-8 dimension fired live this iteration for the first time (two on-load 500s). We chose: did not fire REGRESSION since nothing could have been introduced or worsened on an empty diff and the human already deferred this exact code path three times; returned ESCALATE instead, noting a human reading C.1 literally should halt. Reversible: yes
- iter-11 · goal-decomposer — Ambiguity: an operator note claimed agents cannot start or stop services and the subagent-resume channel is broken, so the boot-budget measurement script might not be directly executable, and goal.md doesn't address who may launch backend processes. We chose: wrote the boot-budget measurement as the standard path with an explicit fallback that the operator runs the exact command and reports the output verbatim if genuinely blocked, mirroring iter-10's own accepted J-04 fallback pattern. Reversible: yes
- iter-10 · goal-evaluator — Ambiguity: only J-04's steps 5-6 were re-driven this iteration, with steps 1-2 resting on a pre-host-guard measurement and steps 3-4 on iter-9's simulations. We chose: scored the journey `passing` on the strength of a literally empty product diff, while recording the un-re-measured boot budget as a carried caveat. Reversible: yes
- iter-10 · goal-evaluator — Ambiguity: J-04's decisive step-6 artifact was a DOM/HTML capture rather than a screenshot, because every post-scroll screenshot of the Run History row rendered blank on this ~1,800-row page. We chose: accepted the verbatim DOM capture as rendered-surface evidence and scored J-04 `passing`, after confirming the captured text is composed client-side and matches the database row queried independently. Reversible: yes
- iter-10 · goal-decomposer — Ambiguity: an operator note (received alongside a dispatch) asserted agents in this pipeline cannot start or stop services and that J-04's fix was already "API-verified," implying only a rendered-surface observation remained — a claim that could not be independently verified from any agent-facing artifact, and the prior evaluator's own instruction was explicit that API-level evidence alone must not flip J-04 to passing. We chose: wrote the standard path as browser-qa-agent re-driving J-04's full six-step live acceptance itself, with a fallback allowing the operator to perform the kill/restart and hand the resulting state to browser-qa-agent to read from the rendered page, not API JSON alone. Reversible: yes

## Quick verify

From `reports/phase-goal-ops-hardening-iter-13-what-to-click.md`:

1. Open Chrome DevTools (F12), go to the Network tab, and check "Disable cache." Then, in a new tab, navigate to `http://localhost:3255/data`
2. In the Network tab, find the request row named `indexes?full=true` and read its Time column
3. Close that tab completely, open a fresh new tab, and repeat step 1–2 two more times (three total fresh loads of `/data`)
4. Open one more new tab (cache still disabled) and navigate to `http://localhost:3255/`
5. On that same Dashboard page, click the range dropdown in the top-right of the "Major indexes & regime" card and select "3M"

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-13.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-13-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-13-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-13-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-13-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-13-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-13-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-13-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-13-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-ops-hardening-iter-13-ux-regression.md |
| QA | PASS_WITH_NOTES | reports/qa/goal-ops-hardening-iter-13-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-13-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-ops-hardening-iter-13-closure-verdict.md |
| Goal evaluation | REGRESSION | runs/goal-session-ops-hardening/iter-13/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
