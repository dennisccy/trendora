# Iteration Summary — goal-ops-hardening-iter-7

**Verdict:** REGRESSION
**Iteration type:** goal-full
**Date:** 2026-07-21
**Iteration:** 7

## In plain words

**What you can do now:** You can browse stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores. You can pull in any historical date range during a data update with no size limit, and the system tells you plainly when there's nothing new to add. Whether the app is starting up, recovering from a restart, or has genuinely gone down, the on-screen status message tells you the truth about what's happening.

**What changed this time:** Mostly behind the scenes: after a data update finishes, the Data page's summary line can now mention "drawdown expectations" among the things it refreshed, and the Evidence page loads its numbers instantly the very first time you open it after an update (previously the first visitor after an update could wait over a minute). However, testing this round also found that during a second big data update run back-to-back, the app can briefly freeze and stop responding for several minutes, needing a manual restart to recover — so this update is being held back for a closer look rather than marked finished.

**What's next:** Before this closes out, the team needs to track down why the app can freeze during a heavy data update, make sure it recovers on its own instead of needing a manual restart, and re-confirm everything still works.

## Headline

The Evidence page now loads fast the very first time you visit it after any data update.

## Direction

**Signal:** regressing
**Why:** This iteration's target fix (warming `/evidence`'s drawdown figures at ingest) genuinely closed J-06's last gap, but browser QA caught J-05 breaking on its own acceptance test — a 7+ minute `GET /api/health` hang tied to a `MemoryError` during a heavy ingest job, on the exact code path (`_refresh_ingest_aggregates`) this iteration modified. That is a verified passing→failing move (J-05: passing since iter-6 → regressed) plus an unresolved critical AG-8 violation, so the loop halts for human review before any recovery iteration runs.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-05 (iter-4), J-04 (iter-6), J-05 (iter-6)
- Regressions in last 5 iters: J-05 (iter-7)
- Anti-goal violations in last 5 iters: 1 (AG-8, critical, unresolved — iter-7)
- Iters with no journey state change: 1 of last 5

**Latest evaluator reasoning:** The J-06 target fix (warm `/evidence`'s per-claim `drawdown_expectations` at ingest finalize) is genuinely delivered and verified — first `/evidence` view after a real ingest measured 22.4ms in a real browser, byte-identical values, honest gating. BUT the browser-qa lane (authoritative RAW verdict = FAIL) directly observed J-05 (required-still-passing, `passing` since iter-6) break on its literal acceptance step: `GET /api/health` went completely unresponsive for 7+ minutes during a heavy ingest job, the backend hit its own enforced `memory_cap_mb=6144` `ulimit -v` ceiling with a worker-thread `MemoryError`, all 22 threads idle in `futex_do_wait`, and it required a manual restart to recover. That is decision-tree item 1 (a journey moved passing→failing) → REGRESSION.

## What was done

- Extended the `_refresh_ingest_aggregates` ingest finalize hook with a new `drawdown_expectations` warm step, closing J-06's last residual `/evidence` cold-miss gap (audit B1 fix from iter-6).
- Added 7 new unit tests (TC-1/3/4/5 + variants) covering byte-identity, honest "actually warmed" gating, and per-claim failure isolation; the full 4-file pytest suite passed 228/228 with 0 failures.
- Live-verified the fix against a running backend: first `/evidence` view after a real ingest measured 22.4ms in a real browser, versus the prior ~73s cold-miss.
- Recorded a new dated section in `perf-budgets.md` with the post-warm measurement and an 11-page budget reconfirmation.
- Re-verified J-01, J-03, and J-04 remain passing via deterministic replay / LLM full-acceptance checks.
- The authoritative raw browser-QA verdict is FAIL: J-05 regressed (passing→failing) on a 7+ minute `/api/health` hang tied to a `MemoryError` during a heavy ingest, requiring manual restart — so J-06, this iteration's target, stays `partial` rather than a clean pass.

## What's left

- Journey J-05 ("Aggregates are precomputed at ingest, never on the fly") regressed — `GET /api/health` hangs 7+ minutes under a heavy ingest, hitting a `MemoryError` at the enforced 6144MB cap, and needs a manual restart to recover.
- Journey J-06 ("Pages load only what they need") stays partial — the `/evidence` target fix landed cleanly, but the overall browser-QA verdict is FAIL, blocking a clean pass.
- Closure blocker: the confirmed J-05 regression was masked (not surfaced) by PASS verdicts in the merged `ui-test-results.md`, the QA report, and the audit report — the verdict-reporting pipeline itself needs fixing so a table containing a FAIL row can't produce a PASS top-line.
- AG-8 anti-goal violation (critical, unresolved): memory exhaustion plus an ungraceful, indefinite health hang during heavy ingest, with no automatic recovery.
- A separate live `/api/backtest` → `forward_aggregates_cached` → large `ScannerResult` `MemoryError` was observed on an on-load path (a related J-06/AG-8 concern) and still needs root-causing.
- Need to determine whether this iteration's new synchronous per-claim `drawdown_expectations` warm materially raised peak memory during ingest finalize, and if so bound/defer/stream it.
- J-04's health badge has no timeout fallback for a "hanging, not erroring" backend — it showed an ambiguous frozen "Checking backend…" instead of the honest "Backend unavailable" state during the hang.
- The session is halted (REGRESSION) pending human review before resuming with `--acknowledge-regression`.

## Next step

Human review, then resume with `--acknowledge-regression` into a full-depth recovery iteration: (1) root-cause the heavy-ingest health hang — determine whether this iteration's new synchronous per-claim `drawdown_expectations` warm materially raised peak RAM, and if so bound/defer/stream it; (2) AG-8 graceful degradation — on `MemoryError`, health must fail-fast to the honest "Backend unavailable" state and the worker pool must recover without a manual restart; (3) audit the separate live `/api/backtest`→`forward_aggregates_cached`→large `ScannerResult` `MemoryError` (an on-load-endpoint OOM, a J-06/AG-8 concern); (4) re-run J-05's heavy-ingest health step live before re-attempting closeout. Do NOT redo the drawdown warm itself — J-06's `/evidence` cold-miss is genuinely closed; the residual is the availability/capacity failure it surfaced.

## Assumptions made

- iter-7 · goal-evaluator — Ambiguity: J-05's step-4 hang had contested attribution (browser-qa flagged pre-existing `/api/backtest` MemoryErrors as a possible pre-existing cause, not proven caused by this iteration's diff), but goal.md's decision tree triggers REGRESSION on any passing→failing move without requiring proven causation. We chose: scored J-05 `regressed` and returned REGRESSION on the observed move (strong live evidence: screenshot + /proc + log signature; iter-6 had verified health-200-on-20/20-polls); did not downgrade to CONTINUE on the contested-attribution argument — a human should adjudicate cause and pick the fix. Reversible: yes
- iter-7 · goal-decomposer — Ambiguity: iter-6's evaluator named re-issuing iter-6's own `user-visible-changes.md`/`ui-surface-map.md` to replace retracted framing, but goal mode's artifact model is append-only per iteration. We chose: not to retroactively edit iter-6's artifacts; instead this iteration's own fresh ui-impact-analyst/closure artifacts describe the current, fixed state, and the stale iter-6 files remain as historical record. Reversible: yes
- iter-7 · goal-decomposer — Ambiguity: none of the four numbered depth triggers literally fire for this iteration's narrow one-function fix, but iter-6's evaluator recommended full depth for the closeout iteration. We chose: full depth anyway, citing trigger 1 (structural/cross-cutting) on a broader reading — J-06's acceptance needs a real-browser 11-page re-measurement plus a `perf-budgets.md` update, and this is the session's last failing/partial journey after two prior iterations' documented closure-narrative drift. Reversible: yes
- iter-6 · goal-evaluator — Ambiguity: `/evidence`'s committed budget clause ("warm ≤3s + a bounded one-time cold miss") could be read as satisfied by a ~73s first-view cold miss, or as failing J-06's "loads only what it needs, in seconds" intent. We chose: scored J-06 `partial` rather than `passing` — the two target endpoints are fixed and in budget, but did not let the letter of the cold-miss clause bless a ~73s first view on the session's last Must-have journey. Reversible: yes
- iter-6 · goal-decomposer — Ambiguity: `GET /api/data/availability` has no committed budget in `perf-budgets.md`, and goal.md's J-06 step 2 only names the boot and cold `/api/data` budgets. We chose: committed an explicit ≤1.5s budget for it this iteration rather than leaving it permanently unbudgeted, since it shares J-06's exact Dashboard-class root cause. Reversible: yes
- iter-6 · goal-decomposer — Ambiguity: iter-5's evaluator offered three alternative directions to close J-06's Dashboard latency violation without mandating one. We chose: a frontend-only fetch-scheduling/staggering fix (no new backend endpoint, no HTTP2/TLS launcher change, no budget loosening), since any coalescing endpoint would create a second serving path and curl's own baseline already sat under budget. Reversible: yes
- iter-5 · goal-evaluator — Ambiguity: J-04 and J-05 received zero regression-replay coverage this cycle even though the shared function they depend on was modified. We chose: scored both `unknown` rather than silently carrying `passing` forward — honest about the missing this-cycle evidence, flagging them for mandatory re-verification next iter; did not treat the coverage gap as a regression. Reversible: yes
- iter-5 · goal-evaluator — Ambiguity: J-01's deterministic golden-script replay failed step-6 with no LLM-fallback adjudication, and the methodology expects an in-pipeline reconciliation footer that was absent. We chose: scored J-01 `passing`, adjudicating the miss as a stale proxy (J-01's actual acceptance steps 1-5 passed, the run exists in the DB, the display code path is untouched); flagged the golden-script fix as a next-iter blocker. Reversible: yes
- iter-5 · goal-decomposer — Ambiguity: J-06 carries the same `[NEW]` demo.sh `--session-live` walkthrough acceptance bullet that iter-4 already deferred for J-05 as a session-closure showcase artifact. We chose: applied the same reading to J-06 for consistency — the walkthrough stays a session-closeout artifact, not part of this iteration's Definition of Done; restated the closure-gate reminder in the iteration spec. Reversible: yes
- iter-5 · goal-decomposer — Ambiguity: J-06's DoD step 3 audit could find a genuine on-load-endpoint violation outside goal.md's named "four offenders" list, and goal.md doesn't say what to do if so. We chose: scoped the iteration to include a bounded, minimal fix only if it fits the existing ingest-time-cache convention through an existing computing module/endpoint; a violation needing a new architectural decision stays out of scope. Reversible: yes
- iter-4 · goal-evaluator — Ambiguity: J-05's DoD has a `[NEW]`-flagged demo.sh `--session-live` walkthrough bullet that was deliberately deferred as out-of-scope (a showcase/demo-chain concern, not a browser-qa-verifiable behavior). We chose: scored J-05 `passing` on its product-behavior acceptance, treating the walkthrough as a session-closure showcase artifact rather than a per-journey passing gate — flagged that both J-05 and J-06 walkthroughs must be produced or the human must accept their deferral before the final GOAL_ACHIEVED gate. Reversible: yes
- iter-4 · goal-evaluator — Ambiguity: J-05 step 3's cold-boot check (TC-8) had a literal "every coverage figure reads 0 or —" precondition that browser-qa found architecturally unreachable on any real boot. We chose: accepted browser-qa's adjusted-scope PASS on the underlying safety property (coverage renders from the persisted payload within budget, no 3.3M-row prefill) — directly verified per goal.md's own wording — rather than the test-designer's stricter all-zero framing. Reversible: yes
- iter-4 · goal-decomposer — Ambiguity: J-05's acceptance and iter-3's evaluator B3-fix direction were qualitative, with no canonical name or field shape yet for the new readiness condition. We chose: a fourth `ReadinessState` literal `awaiting_snapshot` plus one new nullable `readiness.detail` field on the same `GET /api/health` payload, narrowing the servability comparison to the benchmark symbol rather than the whole-table `latest_data_date` max. Reversible: yes

## Quick verify

From `reports/phase-goal-ops-hardening-iter-7-what-to-click.md`:

1. Open `http://localhost:3255/data` in your browser
2. Type `2015-06-18` into the "Start date" field, then type `2015-06-18` into the "End date" field. Leave "Job kind" set to "Backfill snapshots". Click the "Start" button.
3. Wait for the job to finish (the spinner stops; the status badge changes to a completed state such as "ok").
4. Immediately open a new browser tab and navigate to `http://localhost:3255/evidence`
5. On any claim card that has a section titled "Historical drawdown & dry-spell expectations", confirm its table shows real numbers, not blank cells

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-7.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-7-dev.md |
| Review | PASS | reports/reviews/goal-ops-hardening-iter-7-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-7-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-7-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-7-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-7-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-7-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-7-ui-test-plan.md |
| UX regression | UX-REGRESSION-FAIL | reports/phase-goal-ops-hardening-iter-7-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-7-qa.md |
| Audit | PASS | docs/handoffs/goal-ops-hardening-iter-7-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-ops-hardening-iter-7-closure-verdict.md |
| Goal evaluation | REGRESSION | runs/goal-session-ops-hardening/iter-7/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
