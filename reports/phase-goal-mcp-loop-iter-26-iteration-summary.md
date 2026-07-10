# Iteration Summary — goal-mcp-loop-iter-26

**Verdict:** REGRESSION
**Iteration type:** goal-lean
**Date:** 2026-07-10
**Iteration:** 26

## In plain words

**What you can do now:** On Trendora you can browse a leaderboard of hundreds of companies with an honest "proven" or "not yet proven" status on every score, open the full evidence ledger to see every trading idea the system has tested (right now every one honestly reads "FAIL" while the deeper thirty-year history is being re-proven), and follow the market-regime panel through to the evidence backing it. You can view up to thirty years of price history for any stock in a recent or full view, browse the company list as it looked on any past date, see three decades of major-index history plus a volatility gauge and a rate indicator on the dashboard chart (each labeled by source), and check the Data Manager page's color-coded calendar of data availability across the whole company list.

**What changed this time:** The team tried to make the background data-refresh jobs noticeably faster, and the speed-up genuinely worked — roughly 80% faster with no change to any number shown on screen. But while testing the full company-wide refresh, the app crashed under heavy memory load and stayed down — a pre-existing weak spot the speed-up did not fully solve, and one the team could not confidently rule out having made worse. Because a real crash is a serious problem this system is specifically built to avoid, this round is being rolled back to "needs human review" rather than moving forward.

**What's next:** Next, the team needs a dedicated round to harden the app's memory handling so the full company-wide data refresh can no longer crash the backend, before the faster data jobs can be confirmed safe and finished.

## Headline

Backfill/warm-up jobs now compute 80%+ faster from a bounded price window — full-universe rebuild still crashes the backend

## Direction

**Signal:** regressing
**Why:** The live browser check of the sanctioned J-16 path (a full 322-date × 541-company "Rebuild snapshots" job) reproduced a `MemoryError` that took the entire backend down for the rest of the session — an unresolved, reproduced violation of the critical anti-goal against exhausting a service's memory. Because this is a live, unresolved critical anti-goal violation, J-16 is scored failing and all 8 required-still-passing journeys (J-01/03/04/05/10/12/13/15) went unverified behind the outage, so the evaluator halts the loop for human review rather than continuing unattended.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-14 (iter-23), J-13 recovered (iter-25), J-15 (iter-25)
- Regressions in last 5 iters: J-13 (iter-24, recovered iter-25)
- Anti-goal violations in last 5 iters: 2 critical — anti-goal #8 (iter-24, resolved iter-25) and anti-goal #8 again (iter-26, unresolved)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** The live browser lane, running the sanctioned J-16 path ("Rebuild snapshots for current universe", 322 dates × 541 members), reproduced a `MemoryError` that took the ENTIRE backend down — every data endpoint returned HTTP 500 and never recovered. This is a live, reproduced, still-unresolved violation of critical anti-goal #8. The target journey J-16 FAILED at its direct proof (UT-02) and all eight required-still-passing journeys were SKIPPED behind the outage. Per decision-tree rule 1 (an unresolved critical anti-goal violation) the loop halts for human review — the iter-24 precedent verbatim.

## What was done

- Added `indicators.max_lookback_bars` (committed 320) and bounded both scoring `bars_asof` call sites to a recent window before indicator/pattern computation — proven byte-identical by a new harness (`test_scoring_window.py`, 0 diffs across 3 dates × the full pool + a short-history date).
- Moved the warm-up forward-return backfill inside the shared bar cache and made `close_on`/`bars_after` cache-aware, cutting redundant per-symbol database round-trips.
- Measured real before/after performance on the committed 30-year database: per-date backfill 81% faster, a 12-date warm-up subset 78% faster, forward-return reads 89% faster — all clearing the ≥30% target, peak RSS 1,330.6 MB under the 6,144 MB cap.
- Post-audit fix-mode pass removed the one memory-allocation regression iter-26 itself introduced (`close_on`/`bars_after` transient list-slice allocations), byte-identically, verified via a 3,000-pair OLD-vs-NEW spot-check (0 mismatches).
- Verified 0 target journey(s) pass browser QA — J-16's direct proof (UT-02) crashed the backend with a `MemoryError` (VSZ pinned at the 6,144 MB `ulimit -v` ceiling) mid-job; 14 of 16 planned browser checks were SKIPPED behind the outage.

## What's left

- Journey J-16 (data jobs fast + honest about progress) is failing — its direct browser proof (UT-02) reproduced a backend-wide crash before reaching a verifiable completed state.
- Root-cause full-universe VSZ crash (audit finding B1, unresolved anti-goal #8): the regime path's unwindowed `full[:cut]` allocations plus the whole-universe up-front bar prefill exhaust the 6,144 MB `ulimit -v` ceiling on the real 322-date × 541-member job — needs its own dedicated memory-hardening iteration.
- All 8 required-still-passing journeys (J-01, J-03, J-04, J-05, J-10, J-12, J-13, J-15) are unverified this iteration — carried at their last-good passing status, not re-confirmed live behind the outage.
- The performance measurement does not yet cover the full-universe, full-cadence job shape under the live memory cap, and measured RSS rather than VSZ — the metric that actually failed (audit finding B2).
- `test_scoring.py`, `test_sectors.py`, `test_themes.py`, and `test_data_manager.py` were not executed this iteration — deferred to the full-suite lane on an idle box.
- The measured performance numbers (81%/78%/89% faster) are not surfaced anywhere in the product UI yet — only recorded in `reports/perf-budgets.md`.
- Journeys J-02, J-06, J-07, J-08, J-09 remain sanctioned-partial (unchanged) — the 30-year ledgers stay all-FAIL and no staging winner currently clears the canonical Bonferroni divisor-8 bar.
- The backend was left unresponsive at the end of the QA run and needs a supervised restart before further work can proceed.

## Next step

Halt for human review; on `--acknowledge-regression`, iter-27 (FULL) is a dedicated memory-hardening + fix-verification pass, no new feature/evidence work: (1) restart the wedged harness-owned backend and confirm HTTP-200 before QA; (2) reproduce the full-universe 322-date Rebuild under the real `ulimit -v 6144MB`, sampling both VSZ and RSS, and add it to `reports/perf-budgets.md` as a before→after never-regress budget; (3) fix the root allocation (bound/stream the regime path's `full[:cut]` allocations and/or the full-universe prefill), byte-identity-gated via `test_scoring_window.py` + `test_forward_testing.py`; (4) re-run the full browser lane live — J-16 to a verified completed state plus the mandatory cold-`/data` OOM repro, and a genuine PASS on all 8 required journeys; (5) non-blocking: harden the false-positive `/api/health` 200-before-death probe. GOAL_ACHIEVED remains out of reach afterward regardless: J-02/06/07/08/09 stay sanctioned-partial (no staging winner clears divisor-8) — the separate priority-2 work.

## Assumptions made

- iter-26b · goal-evaluator — Ambiguity: J-16's target proof (UT-02) was executed and the backend crashed, but its perf/byte-identity half is real and one honest-progress sub-criterion showed positive (counter ticked 0→117→246 with no premature "done"), so J-16 could be read as `partial` (capability landed, verification incomplete) rather than `failing`. We chose: `failing`, because there is a verified negative outcome (a reproduced backend-wide crash) and J-16's own definition of done explicitly requires no-OOM/no-crash under the cap plus a browser-qa pass — both violated; this session reserves `partial` for "correct-but-not-cleanly-verified," not for a verified failure. Reversible: yes
- iter-26 · goal-evaluator — Ambiguity: decision-tree rule 1 says an unresolved critical anti-goal violation means REGRESSION, but the crash frame (regime `full[:cut]` + the pre-existing full-universe prefill) is unmodified by iter-26's diff, so it is genuinely uncertain whether iter-26 caused the violation or merely surfaced a pre-existing latent memory bomb. We chose: scored REGRESSION on the ground that a critical anti-goal is demonstrably, reproducibly violated on the current tree and is unresolved — the verdict does not depend on this-iteration causation, matching the auditor's and ux-regression reviewer's explicit reasoning and the iter-24 memory-crash precedent. Reversible: yes

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-26.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-26-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-mcp-loop-iter-26-review.md |
| Browser QA | FAIL | reports/phase-goal-mcp-loop-iter-26-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-26-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-26-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-26-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-26-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-26-ui-test-plan.md |
| UX regression | UX-REGRESSION-FAIL | reports/phase-goal-mcp-loop-iter-26-ux-regression.md |
| QA | FAIL | reports/qa/goal-mcp-loop-iter-26-qa.md |
| Audit | FAIL | docs/handoffs/goal-mcp-loop-iter-26-audit.md |
| Goal evaluation | REGRESSION | runs/goal-session-mcp-loop/iter-26/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
