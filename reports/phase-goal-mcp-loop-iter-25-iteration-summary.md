# Iteration Summary — goal-mcp-loop-iter-25

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-09
**Iteration:** 25

## In plain words

**What you can do now:** On Trendora you can browse a leaderboard of hundreds of companies with an honest "proven" or "not yet proven" status on every score, open the full evidence ledger to see every trading idea the system has tested (right now every one honestly reads "FAIL" while the deeper thirty-year history is being re-proven), and follow the market-regime panel through to the evidence backing it. You can view up to thirty years of price history for any stock in a recent or full view, browse the company list as it looked on any past date, and check the Data Manager page's color-coded calendar of data availability across the whole company list — including in the moment right after the app restarts, which is now confirmed safe.

**What changed this time:** Nothing new to see — but a serious problem discovered last round is now confirmed fixed: opening the Data Manager page immediately after the app restarts no longer risks crashing the whole app. The team restarted the real service from a cold stop twice, and an independent live check in an actual browser confirmed the page loads normally in about ten seconds each time, safely under the memory limit, with every other page rechecked and working normally afterward.

**What's next:** Next, the team will either speed up the background data-refresh jobs or try to certify a new trading edge on the updated thirty-year data — whichever line of work is ready first.

## Headline

Cold-load OOM fix verified live — J-13 recovers, J-15 passes; iter-24 regression closed

## Direction

**Signal:** improving
**Why:** iter-25 was the fix-verification recovery pass iter-24's REGRESSION demanded — J-13 recovered from regressed to passing and target J-15 flipped from partial to passing after two independent live cold-restart reproductions confirmed the `mmap_size_bytes: 0` fix holds, and the critical anti-goal #8 violation is now resolved. All eight required-still-passing journeys (J-01, J-03, J-04, J-05, J-10, J-11, J-12, J-14) were freshly live-replayed clean, and iter-26 already has a clear, scoped next target (J-16 perf, or J-02/06-09 evidence re-certification).

**Trend (last 5 iters):**
- Newly passing this iter: J-13, J-15
- Newly passing in last 5 iters total: J-13 (iter-21, recovered iter-25), J-14 (iter-23), J-15 (iter-25)
- Regressions in last 5 iters: J-13 (iter-24)
- Anti-goal violations in last 5 iters: 1 critical (iter-24, anti-goal #8 — cold `/data` OOM crash; resolved iter-25)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** "iter-25 is the fix-VERIFICATION recovery pass the iter-24 REGRESSION asked for, and it landed cleanly. The already-committed `config.yaml:108 mmap_size_bytes: 0` fix (mmap disabled, zero source diff this iteration) was re-verified LIVE by the canonical browser-qa lane with two independent cold-restart reproductions: `/data` now renders fully populated as the first request after a cold backend boot (~10.2s / ~10.5s), the backend survives, and downstream pages load — so **J-13 recovers regressed -> passing** and target **J-15 flips partial -> passing**, with the iter-24 CRITICAL anti-goal #8 violation now RESOLVED. Not GOAL_ACHIEVED: J-02/J-06/J-07/J-08/J-09 remain sanctioned-partial (30-year data-basis reset, ledgers all-FAIL, no staging winner clears Bonferroni divisor-8) and J-16 is deliberately unbuilt."

## What was done

- Re-confirmed the iter-24 audit fix (`config.yaml:108 mmap_size_bytes: 0`) is intact at HEAD with zero source diff across backend, frontend, and config this iteration.
- Live-drove two full cold-restart cycles via HTTP-level RSS sampling: both completed in ~9.4–9.5s with peak RSS ~1.8–1.9GB (well under the 6144MB cap), backend survived both times.
- Canonical browser-qa lane independently reproduced the same result twice in a live browser (~10.2s/~10.5s), confirmed the contained "Backend unavailable" error card and downstream `/stocks` survival, and verified 14/14 test cases pass with 0 skipped.
- Freshly live-replayed all 8 required-still-passing journeys (J-01, J-03, J-04, J-05, J-10, J-11, J-12, J-14), closing the iter-24 crash-aborted replay gap.
- Corrected `reports/perf-budgets.md` with real fresh-restart cold-path measurements, replacing the prior iteration's ablation-only estimate; all warm budgets re-confirmed holding.
- Ran the DoD-named byte-identity backend test selection unedited: 123 passed, 0 failed.
- Auditor caught and fixed a QA-lane evidence mis-citation (a storage-card claim had cited what was actually the error-card screenshot) without touching the canonical evidence.
- `ux-regression-reviewer` and `phase-closure-auditor` both flipped from FAIL (iter-24) to PASS/CLOSURE-PASS on this rebuilt evidence, formally clearing the iter-24 regression and confirming anti-goal #8 resolved.

## What's left

- Journeys J-02, J-06, J-07, J-08, J-09 (evidence re-certification — drill-into-proof, vcp_contraction, multi-horizon, multi-factor combination, and rs_spy_3m 60-day edges) remain sanctioned-partial: the 30-year data-basis reset means every previously-certified edge honestly recomputes to FAIL, and no staging candidate currently clears the tightened Bonferroni bar (divisor 8).
- Journey J-16 (Data jobs — Fetch/Backfill/warmup speed and honesty) remains unknown/unbuilt — deliberately deferred out of this recovery pass (rubric rule 5: never bundle a risky journey into a regression-recovery iteration).
- The same-instant storage-card ↔ `/api/data` byte-diff wasn't rigorously captured this iteration (non-blocking) — flagged for the next `/data`-touching iteration.
- The `/data` page still lacks an auto-retry when a transient backend hiccup strands it beside an already-recovered status badge (non-blocking, P3 follow-up).
- QA-lane rigor gap: its `/api/health` warm-budget figure (0.210s) exceeded the ≤0.1s budget yet was marked PASS; the authoritative warm figure (0.090s) lives in `perf-budgets.md`.
- Dead-duplicate `index-regime-chart.tsx` / `major-indexes-card.tsx` components remain undeleted (coherence-WARN carry-forward), deferred to a dedicated tidy iteration.

## Next step

iter-26 (FULL). Two remaining gaps to GOAL_ACHIEVED, in priority order: (1) J-16 — fast-platform data-jobs perf (goal.md item F + A/B warmup-cache): commit the measured baseline, land the byte-identity-gated scoring-window change, and re-measure per-date backfill + full warmup ≥30% improvement as never-regress budgets, gated on a byte-identical harness (any per-(symbol,date) diff means fix the window, never accept drift) — the most tractable unbuilt work, self-contained; (2) J-02/J-06/J-07/J-08/J-09 — evidence re-certification on the 30-year basis via a new pre-registered staging exploration, promoting only a winner that clears the canonical Bonferroni divisor-8 with margin (explicit `"ledger":"canonical"`), honoring the honest-stop guard since no staging winner clears divisor-8 today (report, don't force). FULL depth either way — J-16 needs the audit/ux-regression/closure guards and must not be bundled with the evidence work (rubric rule 5). Non-blocking carry-forwards: the `/data` no-retry desync (F1), a clean same-instant storage-card↔API byte-diff (T3), deleting the dead-duplicate chart components, and hardening the non-terminal QA lane's evidence rigor.

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
| Goal evaluation | CONTINUE | runs/goal-session-mcp-loop/iter-25/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
