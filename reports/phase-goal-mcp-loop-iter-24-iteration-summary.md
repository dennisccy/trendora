# Iteration Summary — goal-mcp-loop-iter-24

**Verdict:** REGRESSION
**Iteration type:** goal-full
**Date:** 2026-07-09
**Iteration:** 24

## In plain words

**What you can do now:** On Trendora, you can browse a leaderboard of hundreds of companies with an honest "proven" or "not yet proven" status on every score, and drill into a fully auditable ledger of every trading idea the system has tested, tied to the current market mood. You can view up to thirty years of price history for any stock and switch between a recent and full view, and browse the company list as it looked on any past date. The dashboard's main chart shows three decades of the S&P 500, Nasdaq, and Dow plus a volatility gauge and a rate-spread indicator, each honestly labeled with its data source, and the Data Manager page shows a clear, color-coded calendar of what data is available across the whole company list.

**What changed this time:** The team added a new panel on the Data Manager page showing how much storage the database is using (its file size, plus how many price bars, scored results, and forward-looking test results it holds), and made several existing pages and background checks noticeably faster without changing any of the numbers shown anywhere. While testing this, they found a serious problem: right after the server restarts, opening the Data Manager page could crash the whole backend before the page even loaded. The likely cause was tracked down and fixed the same day, but a final hands-on re-check of that fix in a live browser hadn't happened yet by the end of the round, so this update isn't being signed off as finished quite yet.

**What's next:** Before anything else, the team needs to re-confirm with a real, live restart-and-reload check that the crash fix actually holds — once that's done, this round's speed work and new storage panel can be signed off, and the team will move on to either proving a fresh trading signal on the newer data or continuing the speed push.

## Headline

Fast-platform backend pass + storage card ship; critical cold-boot crash found, fix unverified

## Direction

**Signal:** regressing
**Why:** iter-24 shipped the fast-platform backend pass and a new storage-footprint card cleanly, but the canonical browser-qa lane reproduced a critical, confirmed anti-goal-#8 violation — a cold `/api/data` load crashes the backend 2 of 2 times on a fresh restart — which regressed the previously-passing J-13 (Data Manager) and kept this iteration's own target J-15 from flipping to passing. The audit root-caused and fixed the SQLite mmap/pool interaction at the source and verified it with an offline ablation (471 MB peak, no crash), but that fix has not yet been confirmed by the canonical live browser-qa lane, so per the framework's fail-closed rule for critical anti-goals the violation is still open. That is a real regression this iteration, not a stall — the fix is already applied and the very next step is a single, well-scoped verification re-run.

**Trend (last 5 iters):**
- Newly passing this iter: none
- Newly passing in last 5 iters total: J-13 (iter-21), J-14 (iter-23)
- Regressions in last 5 iters: J-13 (iter-24)
- Anti-goal violations in last 5 iters: 1 critical (iter-24, anti-goal #8 — cold `/data` OOM crash, unresolved)
- Iters with no journey state change: 0 of last 5

**Latest evaluator reasoning:** "iter-24 shipped its intended fast-platform mechanical backend pass (items B/C/D/G/H) + the item-K storage-footprint card correctly on a WARM backend, but item B's SQLite tuning introduced a critical anti-goal #8 violation: mmap_size_bytes=1 GB per connection × pool_size=10/max_overflow=20 exhausts the ulimit -v cap, OOM-crashing the backend (MemoryError → PyO3 panic that kills uvicorn) on the very first cold GET /api/data load after any restart — reproduced 2/2 by the canonical browser-qa lane. This broke required-still-passing J-13 (its /data surface crashes cold) and failed target J-15's own 'cold /api/data completes ≤60 s without OOM' acceptance criterion."

## What was done

- Landed goal.md's fast-platform mechanical backend pass: SQLite WAL/pragma tuning + a sized connection pool (item B), removed two redundant indexes and added a new date index (item C), a ticker-filtered fetch replacing whole-leaderboard deserialization for the stock-detail and watchlist pages (item D), a memoized/cheaper readiness probe (item G), and a single bulk query replacing the `/api/data` missing-data N+1 (item H).
- Added a DB capacity snapshot (item K) — file size plus row counts for daily_prices/scanner_results/forward_returns — served additively on `GET /api/data` and surfaced in a new read-only "Storage footprint" card on the Data Manager page (the iteration's only new user-facing capability).
- Committed a new measurement harness (`scripts/measure-perf.sh`) and a `reports/perf-budgets.md` baseline; every measured endpoint/page met its committed budget with wide headroom.
- Proved every optimized path byte-identical to its pre-change output (existing byte-identity tests pass unedited; 15+ new targeted unit tests added across db/data_manager/health/api_engine/api_data).
- Browser-qa ran live and reproduced, on 2 of 2 independent fresh restarts, a critical crash (MemoryError, then a fatal Rust panic) on the very first `/data` load after boot — a confirmed anti-goal-#8 violation that also regressed the required-still-passing J-13; only 11 of 14 executed checks passed, so neither this iteration's target journey (J-15) nor J-13 is confirmed passing via this canonical run.
- The audit root-caused the crash (item B's 1 GB per-connection SQLite mmap window colliding with the new 10+20 connection pool, exhausting the process's virtual-memory cap) and fixed it at the source (`mmap_size_bytes: 0`), re-verifying with a controlled ablation script (crash → 471 MB peak, OK).
- Phase-closure and ux-regression both independently blocked the iteration (CLOSURE-FAIL, UX-REGRESSION-FAIL) pending a live re-verification, and the goal-evaluator concurred with a REGRESSION verdict, halting the loop for human review.

## What's left

- Journey J-13 (Data Manager page) regressed — a cold `/data` load OOM-crashes the backend (MemoryError, then a fatal Rust panic); the `mmap_size_bytes=0` fix is applied in the working tree but not yet confirmed by a live browser re-run.
- Journey J-15 (fast platform, this iteration's target) stays partial — its own "cold `/api/data` completes ≤60s without OOM" acceptance criterion is unmet until that same re-run passes.
- Re-run the canonical browser-qa lane against a fresh restart (stop the backend, cold-start it, load `/data` at least twice) — the sole blocker per phase-closure and ux-regression.
- Live-replay the required-still-passing journeys the crash aborted (J-03, J-04, J-05, J-11, J-14) — currently carried only on byte-identity, not fresh pixels.
- Correct `implementation-summary.md` and `user-visible-changes.md` to mention the crash, its root cause, the fix, and the outstanding re-verification — both still read as if everything shipped clean.
- Regenerate `runs/goal-mcp-loop-iter-24/status.json` — its `qa_verdict: PASS` / `next_action: none` predate the browser-qa FAIL, the ux-regression FAIL, and the audit's fix.
- Journeys J-02, J-06, J-07, J-08, J-09 (evidence re-certification) remain sanctioned-partial — no staging candidate currently clears the canonical Bonferroni divisor-8 bar.
- Journey J-16 (data-jobs speed) remains unbuilt, deliberately deferred alongside item F.
- Non-blocking: add a retry/auto-retry affordance to `/data`'s error state so a future backend hiccup doesn't strand the page on a stale card next to an already-recovered green badge.
- Non-blocking: make `measure-perf.sh`'s bounded backfill-timing check pick a genuinely cadence-eligible date range instead of an honest-but-uninformative 0-date no-op.

## Next step

Halt for human review. On `--acknowledge-regression`, iter-25 (FULL) should be a fix-verification pass only — no new feature code, since the `mmap_size_bytes=0` fix is already applied and correct. Bring up both prod-mode services fresh and confirm HTTP-200 before dispatching QA, then re-run the canonical browser-qa lane specifically re-driving the UT-16 → UT-06 → UT-05 cold-path sequence (stop the backend, cold-start it, load `/data` as the first request at least twice) and confirm all flip FAIL→PASS with a non-empty, md5-distinct evidence dir. Complete the required-still-passing live replay the crash aborted (J-03, J-04, J-05, J-11, J-14), correct `perf-budgets.md`'s cold-path claim with a real fresh-restart measurement, add a crash/fix/re-verify note to `implementation-summary.md` and `user-visible-changes.md`, regenerate `status.json`, and re-run ux-regression and phase-closure. On a clean cold-path run, J-13 returns to passing and J-15 flips partial→passing; GOAL_ACHIEVED still won't be reachable that iteration since J-02/J-06/J-07/J-08/J-09 remain sanctioned-partial (no staging winner clears the Bonferroni divisor-8 bar today) and J-16 stays deliberately unbuilt.

## Quick verify

From `reports/phase-goal-mcp-loop-iter-24-what-to-click.md`:

1. Open `http://localhost:3255/data` in your browser
2. Scroll down just past "Dataset coverage"
3. Refresh the page (press F5)
4. Navigate to `http://localhost:3255/stocks`, type `AAPL` into the search box (placeholder "Search ticker or name…"), and note its **Leadership**, **Entry Quality**, **Risk**, and **Setup** column values
5. Click the **AAPL** ticker link in that row

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-mcp-loop-iter-24.md |
| Dev handoff | — | docs/handoffs/goal-mcp-loop-iter-24-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-mcp-loop-iter-24-review.md |
| Browser QA | FAIL | reports/phase-goal-mcp-loop-iter-24-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-mcp-loop-iter-24-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-mcp-loop-iter-24-user-visible-changes.md |
| What to click | — | reports/phase-goal-mcp-loop-iter-24-what-to-click.md |
| UI surface map | — | reports/phase-goal-mcp-loop-iter-24-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-mcp-loop-iter-24-ui-test-plan.md |
| UX regression | UX-REGRESSION-FAIL | reports/phase-goal-mcp-loop-iter-24-ux-regression.md |
| QA | PASS | reports/qa/goal-mcp-loop-iter-24-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-mcp-loop-iter-24-audit.md |
| Closure | CLOSURE-FAIL | reports/phase-goal-mcp-loop-iter-24-closure-verdict.md |
| Goal evaluation | REGRESSION | runs/goal-session-mcp-loop/iter-24/eval.md |
| Journey history | — | runs/goal-session-mcp-loop/state/journey-history.json |
