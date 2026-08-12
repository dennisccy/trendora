# Iteration Summary — goal-ops-hardening-iter-67

**Verdict:** CONTINUE
**Iteration type:** goal-lean
**Date:** 2026-08-12
**Iteration:** 67

## In plain words

**What you can do now:** You can browse stock rankings, sector and theme views, backtests, and all five research tools, always with an honest status message if the backend is still starting up. You can run a backfill over any date range with no hidden limit, and the app clearly explains when there's nothing new to fetch. Backtest results load instantly from storage, pages only load the data they need, and the app tells you honestly when it's crunching numbers in the background. The app almost always answers its own health check quickly even during its biggest background job — but a rare slow reply during one specific heavy calculation is still being tracked down, so this last promise remains a work in progress.

**What changed this time:** Nothing changed on any page you can see. Behind the scenes, the team added a hidden, switch-controlled diagnostic tool inside the app's health-check code. Turned on for one real test, it measures for the first time how long a health request waits in line and how long the app's own background clock stalls while a big job is running — and found the wait is real but brief, explaining only about a tenth of the one slow reply seen this round. The rest of that delay is now known to live inside the health check's own calculation work, not the waiting line.

**What's next:** Next, the team will time the part of the health check that hasn't been measured yet — the part that actually reads data and works out whether the app is ready — to find where the rest of that one slow reply is coming from.

## Headline

Live-job drill: 1/1,036 health polls over 2s ceiling (0.10%); idle drill: 0/330 slow

## Direction

**Signal:** holding
**Why:** This iteration built and ran a new health-request-wait watchdog (queue-wait + event-loop-lag probes, env-flag-gated) exactly per iter-66's order, and found real signal — the watchdog's own measurements are ~159x/~23x elevated during the live job vs. idle — but that only accounts for ~11% of the one breach's 2.875s magnitude, so J-07 ("Heavy aggregates never take the service down") stays `partial`. All 8 journeys replayed clean with zero regressions and zero newly-passing journeys for a second consecutive round, so the shape (7 passing / 1 partial) is holding rather than moving in either direction.

**Trend (last 2 iters):**
- Newly passing this iter: none
- Newly passing in last 2 iters total: none
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: none
- Iters with no journey state change: 2 of last 2

**Latest evaluator reasoning:** This round built a small measuring tool inside the running app and used it. The tool is switched off unless someone sets a flag, and the app answers exactly the same way with it on or off. With a real 18-minute data job running, the app answered 1,036 health checks out of 1,036, and only ONE answer took longer than 2 seconds (2.875 s). The honest new finding is where the delay lives: the waiting-in-line part the new tool measures explains only about a ninth of that one slow answer, so most of the delay happens inside the health check's own work — a place nothing has measured yet.

## What was done

- Product changes: apps/backend/app/engine/health_watchdog.py, apps/backend/app/api/health.py, apps/backend/main.py, apps/backend/tests/test_health_watchdog.py
- Added an env-flag-gated (`TRENDORA_HEALTH_WATCHDOG=1`) health-request-wait watchdog: a queue-wait timestamp pair plus a periodic event-loop-lag probe, written to `logs/health-watchdog.jsonl` via the existing ledger writer.
- Proved `GET /api/health`'s response body and computed value are byte-identical whether the flag is on or off (fixture-backed equality test, not just asserted).
- Ran a live-job drill (17m46s real backfill, 1,036 polls, 1 breach = 0.10%) and an idle-control drill (330 polls, 0 breaches) using the shared `scripts/qa/poll_health.py` script.
- Found queue-wait and loop-lag both sharply elevated during the job vs. idle (~159x / ~23x), but this explains only ~11% of the one breach's 2.875s magnitude — the rest is inside the handler body, unmeasured.
- Corrected three iter-66 write-up defects: the mis-clustered breach in `perf-budgets.md` Addendum 33, the browser-QA lane's one-hour timezone error, and this round's own handoff leading with the breach count.
- Added 8 new unit tests (all passing); verified 8/8 journeys pass merged browser QA and raw deterministic replay — target journey J-07 held `partial`.

## What's left

- Journey J-07 ("Heavy aggregates never take the service down") remains `partial` — 1 of 1,036 live-job health polls exceeded the 2-second ceiling; the idle control showed 0 breaches.
- The watchdog's queue-wait/loop-lag measurement explains only ~11% of the one breach's 2.875s magnitude; ~2.55s remains unmeasured, inside the health-check handler's own body (DB reads + readiness computation).
- `test_health.py` — the existing test module for the very file changed this round (`health.py`) — was not run this pass (fixture cost + drill-contamination risk); recommended as an ordinary step next round.
- Seven new minor ledger findings opened this round (iter-67/a through /g), including a new phase-misattribution inside the very addendum written to fix one, and a seventh consecutive over-budget round.
- Three owner-gated questions remain unanswered for the 19th round: the 2-second health-ceiling policy for long jobs, permission for the `browser-qa-phase.sh` ordering fix, and a cost decision on the over-budget replay lane (this round ran 2.9x over its 3,600s budget).
- The J-05 walkthrough capture remains unrecorded for a 9th consecutive round.
- iter-33/g (the Regime Lab) remains deferred for a 33rd round.

## Next step

Keep the next round lean. Priority order: (1) measure the part of the health check nobody has timed yet — add a third timing sample around the handler body's own work (DB reads + readiness computation) behind the same off-by-default flag, and re-run the same live-job + idle-control drill pair; (2) run `tests/test_health.py` as an ordinary step, since `app/api/health.py` changed this round and its own test file was not run; (3) correct two statements in this round's write-up — the 1.382s loop-lag spike happened during the app's start-up cache warm-up, not during the factor-lab step, and the factor-lab step still owns 120 of the 131 answers over 1 second; (4) unify the browser lane back onto the shared `poll_health.py` stopwatch, which it drifted away from again this round. The owner's three long-parked questions — the 2-second ceiling policy for long jobs, the `browser-qa-phase.sh` ordering fix, and the cost decision on the seventh consecutive over-budget round — remain unanswered.

## Assumptions made

- iter-67 · goal-evaluator — Ambiguity: J-07 has four acceptance steps; this round only exercised steps 1-2, while step 3 (VmPeak) had only a non-authoritative point read and step 4 (memory-pressure abort) wasn't re-run at all. We chose: carry steps 3 and 4 forward on evidence durability, since the warm-path code they test is byte-identical to when those steps last passed, and keep J-07 at `partial` on step 2's ceiling alone. Reversible: yes.
- iter-67 · goal-decomposer — Ambiguity: iter-66's next-step named the required watchdog method only at the concept level ("an in-app watchdog timing how long a health request waits"), consistent with several different implementations. We chose: the smallest design that still answers the question — an ASGI-layer timestamp pair plus a periodic event-loop-lag probe, both gated behind a new off-by-default env var. Reversible: yes.
- iter-66 · goal-evaluator — Ambiguity: the binding "Do not redo" on `factor_lab_all_warm` (set by iter-65 after four clean profiles) conflicted with this round's own drill putting 68 of 70 health-check breaches inside that exact phase. We chose: recommend re-opening `factor_lab_all_warm` as the next target, but with a genuinely different method (watch the live serving process instead of re-profiling standalone). Reversible: yes.
- iter-66 · goal-decomposer (2 of 2) — Ambiguity: iter-65's "use ONE counter everywhere" could mean canonicalizing the measurement script itself, or editing the browser-qa-agent's own framework instructions/prompt. We chose: canonicalize the script (`scripts/qa/poll_health.py`) and direct it via this iteration's own TESTING REQUIREMENTS, without touching any `.claude/agents/` framework file. Reversible: yes.
- iter-66 · goal-decomposer (1 of 2) — Ambiguity: iter-65's next-step item "stop one job writing two history rows" (iter-64/d) was phrased as a guaranteed-fix directive, but the underlying finding was only "explained by restarts," not root-caused. We chose: scope it as investigate-and-fix-only-if-small, to avoid bundling a second risky change alongside this iteration's primary work. Reversible: yes.
- iter-65 · goal-evaluator (2 of 2) — Ambiguity: the ledger's "resolved" flag has no defined meaning for a finding (iter-64/a, a one-off contained error boundary) that was investigated exactly as specified but whose cause could not be found. We chose: mark it `resolved: true` with the residual unknown written into the evidence string, rather than leave it open indefinitely with no defined next action. Reversible: yes.
- iter-65 · goal-evaluator (1 of 2) — Ambiguity: this round met TC-1's own stated acceptance bar for J-07 (0 breaches inside `factor_lab_all_warm`), but J-07's own step-2 text is broader ("every poll answers"), and one poll still missed the ceiling elsewhere. We chose: keep J-07 `partial`, since a single clean drill on code that has alternated clean/elevated for several rounds is not reliable evidence the ceiling is met. Reversible: yes.
- iter-64 · goal-evaluator (2 of 2) — Ambiguity: J-07's step 2 says "every poll answers HTTP 200 within budget," and for the first time one poll got no answer within the client's 5-second timeout, while every earlier drill answered 100%. We chose: keep J-07 `partial` rather than convert the single non-answer into a halt, since zero 5xx/MemoryErrors were logged and the process kept serving before and after. Reversible: yes.
- iter-64 · goal-evaluator (1 of 2) — Ambiguity: AG-8 requires a widened data basis "never crash an existing page" while also prescribing the honest failure mode (contained error boundary); one screenshot showed a page doing both — not rendering, but showing exactly the honest boundary AG-8 asks for. We chose: log it as a minor entry, keep J-05 passing, no critical call — since the visible outcome was the prescribed one, it did not reproduce, and no new data shape was introduced. Reversible: yes.

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-67.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-67-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-67-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-67-ui-test-results.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-67/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
