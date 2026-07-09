# Iteration Summary — goal-mcp-loop-iter-25

**Verdict:** PASS
**Iteration type:** goal-full
**Date:** 2026-07-09
**Iteration:** 25

## In plain words

**What you can do now:** You can browse a leaderboard of hundreds of stocks where every score carries an honest "proven" or "not yet proven" label — never a confident number without backing. You can open any stock and view up to thirty years of price history, switching between a recent view and the full history. You can visit the Evidence page to see every trading idea the product has tested and how it turned out, and jump there directly from the dashboard's current market-mood panel. You can also open the Data Manager page to see how much data is stored, how current it is, and a clear legend explaining it, plus a dashboard chart of three decades of major stock-index history, a volatility gauge, and a rate-spread indicator, each labeled with where its numbers came from.

**What changed this time:** Nothing new to look at — this round re-tested a bug found last round. A crash risk that could take down the whole product the moment someone opened the Data Manager page right after a restart is now confirmed fixed: the team restarted the real service twice from cold and it loaded cleanly both times in about ten seconds, and a separate live browser check confirmed the same result.

**What's next:** Now that this fix is confirmed, work is expected to turn either to re-testing some previously-retired trading ideas on the newer, deeper data, or to further speeding up the behind-the-scenes data jobs — a few trading-idea checks and one speed goal are still open before everything is finished.

## Headline

Verify the /data cold-load OOM fix; recover J-13, close J-15

## Direction

**Signal:** improving
**Why:** iter-25 was a pure verification pass that live-confirmed the `mmap_size_bytes: 0` fix eliminates the iter-24 cold-path OOM crash: two independent, live cold-restart reproductions (browser-qa UT-02/UT-03) show the backend surviving and `/data` rendering in ~10s each time, recovering J-13 to passing and clearing J-15's cold-path acceptance criterion. Both gates that caught the iter-24 regression (ux-regression-reviewer, phase-closure-auditor) now PASS on fresh, live evidence with zero source-code drift, so this reads as a genuine recovery rather than new risk.

**Trend (last 5 iters):**
- Newly passing this iter: J-13, J-15
- Newly passing in last 5 iters total: J-13, J-14, J-15
- Regressions in last 5 iters: J-13 (iter-24)
- Anti-goal violations in last 5 iters: 1 critical (anti-goal #8 — cold-path OOM crash, iter-24; resolved this iteration)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** No `eval.md` exists yet for iter-25; the most recent recorded evaluator entry (iteration 24) reads: "iter-24 shipped a CRITICAL anti-goal #8 violation that the QA lane fail-opened past, and the auditor's applied fix is not verified by the canonical lane — the exact iter-18 pattern, so REGRESSION per decision-tree rule 1 (a prior-passing journey now failing AND a critical anti-goal violated)... NOT CONTINUE — a critical anti-goal was violated and a prior-passing journey broke: the framework halts for human review, it does not auto-loop (iter-18 precedent verbatim)."

## What was done

- Confirmed the already-committed `mmap_size_bytes: 0` fix (`config.yaml:108`, applied by the iter-24 audit) is still present and unmodified, with zero `apps/backend`/`apps/frontend` source drift.
- Live-drove two independent full-stop → cold-start → `/data`-as-first-request cycles against the real 30-year database, sampling backend memory throughout — both completed in ~9.4–9.5s at ~1.8–1.9GB peak (well under the 6144MB cap), backend staying alive both times.
- Re-ran the canonical browser-qa lane live over the cold-restart sequence plus the full required-still-passing set — 14/14 tests passed, 0 skipped, with md5-distinct evidence screenshots.
- Corrected `reports/perf-budgets.md` with real fresh-restart cold-path measurements (replacing the prior iteration's ablation-only estimate) and re-confirmed all warm-path budgets still hold.
- Re-ran `ux-regression-reviewer` (UX-REGRESSION-PASS) and `phase-closure-auditor` (CLOSURE-PASS), formally re-clearing the two gates that failed at iter-24.
- Verified the 2 target journeys (J-13, J-15) pass browser QA, alongside 8 required-still-passing journeys (J-01, J-03, J-04, J-05, J-10, J-11, J-12, J-14) freshly live-replayed rather than carried over.

## What's left

- J-02, J-06, J-07, J-08, J-09 remain sanctioned-partial: no staging candidate currently clears the canonical Bonferroni divisor-8 bar, so no "Proven" badge exists yet to drill into on the 30-year basis.
- J-16 (fast, honest data jobs) is still unbuilt — needs a committed measured baseline plus the prescribed optimizations, deliberately deferred out of this regression-recovery pass.
- A QA-lane evidence-hygiene defect (a mis-cited screenshot on the storage-card check) was caught and reconciled by the auditor; the underlying QA-lane rigor gaps (an over-budget health-check timing marked PASS; a same-instant storage-card-to-API byte comparison not captured with full rigor) are non-blocking carry-forwards.
- `scripts/measure-perf.sh` still hardcodes a stale iteration label in its auto-appended output — a future tidy pass should parameterize it.
- The dead-duplicate chart components (`index-regime-chart.tsx` / `major-indexes-card.tsx`, a coherence-WARN carry-forward) remain un-deleted, deferred to a dedicated tidy iteration.
- The `/data` page's no-retry desync after a backend hiccup (a pre-existing, non-blocking design gap) remains open for a future iteration.

## Next step

No `eval.md` was available yet for this iteration to carry a verbatim Next-Step Recommendation, so per the fallback rule: run the full pipeline on the next phase. The phase spec's own notes and the auditor's recommended next step both anticipate the evaluator will register CONTINUE (not GOAL_ACHIEVED) on this clean recovery, since J-02/J-06–J-09 remain sanctioned-partial and J-16 is still unbuilt; the most-ready candidates are a new-basis staging-discovery pass toward re-certifying one of those factors, or landing the deferred J-16 fast-platform work — alongside the non-blocking carry-forwards noted above (QA-lane evidence-hygiene tightening, the `/data` no-retry desync, and the dead-duplicate chart-component cleanup).

## Quick verify

From `reports/phase-goal-mcp-loop-iter-25-what-to-click.md`:

1. Fully stop the backend service, then start it fresh (a cold restart, not a reload)
2. Immediately open a new browser tab and go straight to `http://localhost:3255/data` — this must be the very first page you open against the freshly-restarted backend
3. Open `http://localhost:3255/stocks` in the same or a new tab
4. Repeat steps 1–3 one more time (restart the backend again, load `/data` first, then `/stocks`)
5. On the `/data` page, look at the "Storage footprint" panel

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-25.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-25-dev.md |
| Review | PASS | reports/reviews/goal-mcp-loop-iter-25-review.md |
| Browser QA | PASS | reports/phase-goal-mcp-loop-iter-25-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-25-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-25-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-25-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-25-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-25-ui-test-plan.md |
| UX regression | UX-REGRESSION-PASS | reports/phase-goal-mcp-loop-iter-25-ux-regression.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-25-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-mcp-loop-iter-25-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-mcp-loop-iter-25-closure-verdict.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
