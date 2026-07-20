# Iteration Summary — goal-ops-hardening-iter-2

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-20
**Iteration:** 2

## In plain words

**What you can do now:** You can still browse Trendora's stock rankings, sector and theme views, backtests, research tools, and evidence-backed scores exactly as before. On the Data page, you can request a backfill for any date range and see every day you asked for actually get pulled in, submit backfills of any length without hitting a size limit, and get a clear, honest explanation whenever a backfill finds nothing new to do. Restarting the app now shows clear starting-up and crash messages, including a permanent record if it ever goes down.

**What changed this time:** The Data page now shows exactly which behind-the-scenes calculations a finished backfill kept up to date (a new "Refreshed: ..." note), and reopening that page right after a restart is now nearly instant instead of taking several seconds, because those calculations happen once when new data comes in rather than every time someone looks at the page. A short-lived bug that showed wrong numbers for older dates was caught and fixed the same day it appeared. Starting the app for real now actually respects its memory limit and keeps a permanent log of what happened, so a crash leaves a trace behind.

**What's next:** Next we'll close a rare gap where a routine data refresh can briefly blank out the coverage numbers, confirm the app stays healthy during a big, heavy data job, and then start making sure every page only loads exactly what it needs.

## Headline

Aggregates are now computed when new data arrives, not when a page is viewed.

## Direction

**Signal:** improving
**Why:** J-04 (Non-blocking boot with visible status) moved from partial to passing this iteration — the persistent logfile and enforced memory cap were verified live via `/proc` reads and a real SIGKILL test. J-05 (Aggregates precomputed at ingest) advanced from failing to partial, with 3 of its 4 acceptance steps verified and only the heavy-job health/memory measurement outstanding. J-01/J-03 were re-verified non-regressed and a CRITICAL AG-3 regression introduced and caught within this same iteration was fixed and re-verified, so the trend continues upward.

**Trend (last 3 iters):**
- Newly passing this iter: J-04
- Newly passing in last 3 iters total: J-01, J-03, J-04
- Regressions in last 3 iters: none
- Anti-goal violations in last 3 iters: 3 total — 2 critical (both fixed intra-iteration and resolved: iter-1's interrupted-row fabricated breakdown, iter-2's as-of-switcher false-zero) + 1 minor (unresolved: iter-2 audit B1, fetch-triggered coverage blanking)
- Iters with no journey state change: 0 of last 3

**Latest evaluator reasoning:** J-05 (ingest-time aggregate maintenance served from a new persisted `coverage_snapshot` table) and J-04's remaining acceptance (enforced `ulimit -v`/`MALLOC_ARENA_MAX` + persistent `logs/backend.log`) are genuinely delivered: cold `/data` serves coverage from storage in 0.029–0.086 s (vs a ~9.4 s pre-fix baseline) with zero request-path whole-table loads on the default path, verified across the browser lane, a real-process launch-script test suite, live `/proc` reads, and an independent audit code-trace + test re-run. The review-pass-1 CRITICAL (as-of switcher serving false-zero coverage, AG-3) was fixed intra-iteration and re-verified byte-exact. Goal is not achieved — J-05 step 4 (health/memory during a heavy job) was never measured live, J-06 is untouched, and an out-of-scope fetch-path coverage-freshness gap (audit B1) must be closed before any GOAL_ACHIEVED.

## What was done

- Added a new persisted `coverage_snapshot` table plus an ingest finalize hook so a completed backfill/`both`/rebuild job computes coverage, market phase, membership timeline, and research hot-key caches once at ingest time, instead of recomputing them on each page view.
- Swapped `/data`'s coverage read path to serve from that stored table (with an honest "not yet computed" sentinel for a genuinely missing row) — removing the whole-table live scan from the request path.
- Added a boot-time warm-up safety net that fills in the coverage snapshot for a brand-new, never-ingested database shortly after startup.
- Added an `aggregates_refreshed` field to completed backfill/rebuild run records (gated the same way `calendar_days` already is) and surfaced it on `/data` as a new "Refreshed: ..." line.
- Made `scripts/start-backend.sh` actually enforce the configured memory cap (`ulimit -v`) and `MALLOC_ARENA_MAX`, and write a persistent, append-mode boot/crash logfile (`logs/backend.log`).
- Found and fixed, within this same iteration, a CRITICAL AG-3 regression (the as-of switcher serving false-zero coverage for historical dates) via per-date ingest persistence plus a read-path self-heal, independently re-verified byte-exact.
- Verified 11/11 browser-QA tests pass, including target journeys J-04 (promoted partial→passing) and J-05 (advanced failing→partial), plus required-still-passing J-01/J-03 (both re-verified passing, non-regressed).

## What's left

- Journey J-06 (Pages load only what they need) still failing — untouched this iteration, next in line once J-05 closes.
- Journey J-05 (Aggregates are precomputed at ingest, never on the fly) still only partial — health/memory responsiveness during a genuinely heavy backfill/rebuild (TC-11/TC-12) has not been measured live.
- Unresolved gap, top next-step (audit finding B1, AG-3 dimension): a routine "fetch" job that changes bar/symbol counts silently blanks the default `/data` coverage panel to false all-zeros until the next restart or backfill — self-heals but gives no in-UI explanation or recovery hint.
- Related storage-cleanliness gap (B2): superseded `coverage_snapshot` rows from an old dataset-version stamp are never pruned.
- The enforced memory cap and persistent logfile have no UI representation anywhere — verifiable only by inspecting the running process or the logfile directly, never by clicking through the product.
- The `computed_at` freshness timestamp stored on each coverage snapshot is not rendered anywhere in the UI (deliberately deferred, not required by any journey this iteration).

## Next step

Full-depth iteration, in priority order: (1) close audit finding B1 by refreshing `coverage_snapshot` for the current stamp at the end of any count-changing ingest kind (ingest-time, AG-8-safe), gated to skip when the dataset-version stamp is unchanged, folding in the B2 stale-stamp prune — do not fix this by extending the `as_of=None` self-heal, which would re-introduce the cold-boot whole-table regression this iteration removed; (2) close J-05's remaining step by running one real heavy rebuild/multi-day backfill and recording TC-11 (`/api/health` ≤1 s throughout) and TC-12 (VmPeak under the enforced 6144 MB cap) into `reports/perf-budgets.md` Item J, watching the new per-date coverage loop's cost on a full rebuild — this promotes J-05 partial→passing; (3) then the J-06 measurement capstone — the cross-page time-to-interactive and on-load-latency budget pass over all pages, folding in this iteration's preliminary cold-`/api/data` number. J-06 is the last failing Must-have journey.

## Assumptions made

- iter-2 · goal-evaluator — Ambiguity: AG-3 ("a journey passes ONLY if the displayed numbers are correct") can be read journey-scoped or product-wide; audit finding B1 (a fetch job silently blanking the default `/data` coverage to false zeros) is a genuine wrong-number display, but on a path no Must-have journey exercises. We chose: applied the journey-scoped reading for the verdict — B1 breaks no Must-have journey, so it does not force REGRESSION; recorded it unresolved as the #1 next-step; a human can override to REGRESSION. Reversible: yes
- iter-2 · goal-evaluator — Ambiguity: J-04's step 4 (crash → visibly distinct unreachable UI presentation) was not freshly re-screenshotted this iteration, only its logfile-abrupt-end counterpart was. We chose: scored J-04 passing (partial→passing) anyway — its badge/preflight/readiness code is unchanged this iteration and step 4 was verified working in mcp-loop iter-28/33; a future required-still-passing replay/QA pass re-exercises the crash-UI path. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: `config.yaml` claims `scripts/start-backend.sh` already wires all five `server:` fields (`memory_cap_mb`, `malloc_arena_max`, `limit_concurrency`, `timeout_keep_alive_seconds`, `graceful_timeout_seconds`), but none are actually wired, while goal.md's binding note names only three. We chose: scoped the fix to exactly the three goal.md-named items (ulimit, `MALLOC_ARENA_MAX`, persistent logfile), leaving the other three unwired and flagged as drift rather than silently expanding scope. Reversible: yes
- iter-2 · goal-decomposer — Ambiguity: goal.md's "four offenders to retire" reads as a mandate to fully retire boot's `ensure_latest_snapshot` and the warm-up loop's cadence bootstrap, but neither is exercisable this session (both dormant against the offline seed and current DB). We chose: scoped J-05 to what its own 4 acceptance steps literally exercise — the new table, finalize hooks, and boot safety net — leaving those two branches unchanged rather than risk an unverifiable retirement. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: J-01's DoD pins an exact breakdown for the May range, but that range had already been backfilled by a prior functional-QA pass before the browser session began, so no fresh live submission was captured. We chose: scored J-01 passing via three corroborating sources — the on-screen historical run row, the re-run's already-snapshotted count, and a unit test proving the fresh-run breakdown by construction. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: browser-qa scored the whole J-04 row PASS, but J-04's full acceptance also requires a persistent logfile and enforced memory cap, both explicitly out of scope and unbuilt that iteration. We chose: kept J-04 at partial rather than promoting it, treating the pass as a non-regression check of its 5 already-working sub-behaviors only, not a completion claim. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: J-03's acceptance text says the UI progress reflects the same chunk plan the engine executes, but `_do_backfill` had no date-window chunking at all. We chose: read the acceptance literally and added real date-window chunking to `_do_backfill`, not just removing the range cap. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: goal.md establishes "requested range always wins" for explicit backfill requests, but it's unstated whether the cadence bypass should also extend to the `rebuild` kind. We chose: scoped the bypass to explicit `backfill`/`both` requests only, leaving `rebuild`'s cadence gating unchanged since no Must-have journey exercises `rebuild` this cycle. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: the iter spec's notes suggested "surface not yet implemented → FAIL," but J-04 had 5 of 6 steps already working live. We chose: scored J-04 partial rather than failing, to signal only the logfile/memory-cap layer remains, while keeping J-06 failing since its passing pages were pre-existing baseline, not new progress. Reversible: yes
- iter-0 · goal-decomposer — Ambiguity: goal.md's Product Shape names only 9 nav sections as "existing nav unchanged," but the actual sidebar has 11 items (also Scanner Runs and Methodology). We chose: treated the actual 11-item sidebar as ground truth, reading goal.md's list as "these stay, at minimum," not an exhaustive list. Reversible: yes

## Quick verify

From `reports/phase-goal-ops-hardening-iter-2-what-to-click.md`:

1. Open `http://localhost:3255/data` in your browser
2. Under the coverage tiles, read the "Gap range: X → Y" line (or, if it says "no backfill gaps," use the date `2026-05-15`); in the "Start a fetch / backfill job" form, type that date into both the "Start date" and "End date" fields, leave "Job kind" set to "Backfill snapshots," then click "Start"
3. Wait for the job to finish (watch the status badge)
4. Refresh the page (press F5), then scroll down to the "Run history" table at the bottom and find the row matching the date you entered
5. In the top bar, click the as-of date button (it reads "Latest") to open the calendar, then pick an older date that already has data (not the newest one)

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-2.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-2-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-2-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-2-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-2-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-2-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-2-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-2-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-2-ui-test-plan.md |
| UX regression | UX-REGRESSION-WARN | reports/phase-goal-ops-hardening-iter-2-ux-regression.md |
| QA | PASS_WITH_NOTES | reports/qa/goal-ops-hardening-iter-2-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-2-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-ops-hardening-iter-2-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-2/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
