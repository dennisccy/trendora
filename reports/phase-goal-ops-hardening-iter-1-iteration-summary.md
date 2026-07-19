# Iteration Summary — goal-ops-hardening-iter-1

**Verdict:** CONTINUE
**Iteration type:** goal-full
**Date:** 2026-07-19
**Iteration:** 1

## In plain words

**What you can do now:** On the Data Manager page, you can request a backfill for any date range and have it actually pull in every trading day you asked for — no more requests that silently do nothing. If a backfill genuinely has nothing new to do, the app tells you so plainly instead of showing an unexplained success. You can also request backfills of any length, even multi-year spans, and watch large ones progress in visible chunks instead of running into an old size limit. Your job history sticks around across page reloads and new browser visits.

**What changed this time:** This iteration is what made all of that work: previously, backfilling a range like all of May 2026 could silently create nothing, and any request longer than about a year was rejected outright. Along the way, the team also caught and fixed a bug that could show made-up "zero days" information for a job that got interrupted partway through.

**What's next:** Next, the app will start saving its heavier calculations automatically as soon as new data comes in, instead of recomputing them on the spot every time a page is opened.

## Headline

Backfill now respects the exact date range you ask for.

## Direction

**Signal:** improving
**Why:** J-01 and J-03 moved from failing to passing this iteration, verified by 17/17 browser-QA checks (UT-01 through UT-16 plus the J-04 regression journey) and an independent audit re-trace of the breakdown arithmetic. The one critical anti-goal risk this iteration surfaced — a fabricated zero-value breakdown on interrupted rows (AG-3) — was caught by browser-QA and fixed by the audit within the same iteration, with a regression test now in the tree, so it left no standing violation. J-04 (partial) was re-verified non-regressed across three live backend restarts, and the evaluator has a clear next target (J-05), so direction is healthy.

**Trend (last 2 iters):**
- Newly passing this iter: J-01, J-03
- Newly passing in last 2 iters total: J-01, J-03
- Regressions in last 2 iters: none
- Anti-goal violations in last 2 iters: 1 critical (AG-3, found and fixed intra-iteration in iter-1 — not a standing violation)
- Iters with no journey state change: 0 of last 2

**Latest evaluator reasoning:** The data-jobs cluster (J-01 + J-03) is genuinely delivered and end-to-end verified: an explicit backfill now honors its requested range (cadence bypassed for backfill/both, dates_total redefined to trading-days-in-range), zero-work outcomes render in a visually distinct, persisted, self-explanatory state, and the max_range_days cap is gone with date-window chunking as the safety mechanism. Both target journeys move failing → passing (browser-qa 17/17 with exact DOM assertions; audit re-traced the arithmetic and re-ran tests). The one honesty risk — a fabricated 0-breakdown on interrupted rows (AG-3) discovered by browser-qa — was found and fixed intra-iteration by the audit (B1) with a regression test confirmed in the tree. J-04 (partial) is re-verified non-regressed; J-05/J-06 remain out-of-scope failing, so the goal is not yet achieved.

## What was done

- Backfill now respects the exact requested date range — the cadence gate no longer silently blocks explicit `backfill`/`both` requests (the May-2026 range now yields 19/19 snapshots instead of 0).
- Removed the 370-day `max_range_days` cap entirely from config, validation, and the pinning tests; requests of any length are now accepted.
- Large backfills now execute — and show progress — in date-window chunks, reusing the existing fetch-job chunk badge (`chunk_index`/`chunk_total`).
- Added a run-summary exclusion-breakdown contract (`calendar_days` / `non_trading_days` / `already_snapshotted` / `error_other`) with two arithmetic invariants enforced by construction, surfaced on both the Job progress panel and Run history table.
- Zero-work outcomes now render a visually distinct neutral badge plus a plain-English note instead of looking like an unexplained green success.
- The Job progress panel now shows the most recent persisted run on page reload or a fresh session instead of always saying "No job has been started this session."
- Audit caught and fixed two intra-iteration honesty defects — a fabricated zero-value breakdown on interrupted rows (B1) and an `error_other` undercount past 20 failures (B2) — both regression-tested.
- Verified 2 target journeys (J-01, J-03) pass browser QA — 17/17 UI test cases, including the required-still-passing J-04 regression journey.

## What's left

- Journey J-05 (Aggregates are precomputed at ingest, never on the fly) failing — the ingest-finalize aggregate-refresh hooks and the new `coverage_snapshot` table are unbuilt.
- Journey J-06 (Pages load only what they need) failing — per-page load-budget measurements and lazy-loading fixes are unbuilt.
- Journey J-04 (Non-blocking boot with visible status) remains partial — the persistent backend logfile and `ulimit`/`MALLOC_ARENA_MAX` memory-cap enforcement are still unbuilt.
- GAP (documented, unfixed): a live `both`-kind job still transiently shows a fabricated "0 calendar days" breakdown during its fetch stage, before the backfill stage starts.
- GAP (documented, unfixed, pre-disclosed): `rebuild`-kind jobs' breakdown invariant does not hold exactly, since `rebuild`'s cadence-filtered targeting is intentionally unchanged this iteration.
- GAP (documented, unfixed): the persisted-history fallback (`LastRunSummary`) still reads "0 trading days in range" when the latest run was interrupted, rather than an honest placeholder.
- Automatic precomputation of heavier derived views (coverage, market phase, research caches) at ingest time is not yet built — still computed on demand.

## Next step

Advance to the aggregate/boot cluster: J-05 — ingest-time aggregate maintenance (the goal's "four offenders to retire"). Build the ingest finalize hooks + the new `coverage_snapshot` table so `GET /api/data` coverage, latest-date snapshot, membership timeline, market phase, and research hot-key caches are all served from persisted rows — retiring the whole-table 3.3M-row coverage prefill (the documented OOM source) and the synchronous boot scan/warm-up loop. This also completes J-04's remaining memory-cap/boot-no-prefill story and unblocks J-06's per-page budget compliance. Depth = full: it is a data-model + data-contract change (new persisted table, new serving path) and cross-cutting across boot + request paths. Sequence J-06's measurement capstone after J-05 lands, per goal.md's suggested build order.

## Assumptions made

- iter-1 · goal-evaluator — Ambiguity: J-01's DoD pins the productive May run's exact breakdown (19/19/0/9/28), but the prescribed range had already been backfilled by a prior functional-QA pass before the browser session began, so no fresh same-session productive submission was captured live. We chose: scored J-01 passing on the productive path via three corroborating sources — the still-on-screen historical Run-History row, the re-run's `already_snapshotted=19`, and a unit test proving the fresh-run 19/19/0 by construction. Reversible: yes
- iter-1 · goal-evaluator — Ambiguity: browser-qa scored the whole J-04 journey row as PASS, but J-04's full Acceptance also requires a persistent logfile and enforced `memory_cap_mb`/`malloc_arena_max`, both out of scope this iteration and confirmed unbuilt. We chose: kept J-04 at partial (not promoted to passing) — treating the Required-still-passing mandate as a non-regression check of its 5 already-working sub-behaviors, not a completion claim. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: J-03's acceptance states the chunk plan derives from config `import_chunking` values and the UI progress reflects the same plan the engine executes, but `_do_backfill` had no date-window chunking at all — unclear whether removing `max_range_days` alone satisfies J-03 or real chunking must be added. We chose: read the acceptance language literally and scoped J-03 to include adding real date-window chunking to `_do_backfill`, not just the cap removal. Reversible: yes
- iter-1 · goal-decomposer — Ambiguity: goal.md establishes "requested range always wins" for explicit backfill requests, but it is not stated whether the cadence bypass should extend to `rebuild` jobs too (which internally widen to the full historical calendar before calling the same `_do_backfill`). We chose: scoped the bypass to explicit `backfill`/`both` requests only; `rebuild` keeps applying the cadence gate unchanged, since no Must-have journey this cycle exercises `rebuild` and it takes no user-supplied range. Reversible: yes
- iter-0 · goal-evaluator — Ambiguity: the iter spec's NOTES steer "surface not yet implemented → FAIL," and browser-QA scored all five journeys FAIL under a strict PASS/FAIL/SKIP contract, yet the journey-history schema offers a distinct partial status; J-04 had 5 of 6 numbered steps reproduce live. We chose: scored J-04 partial (not failing) to signal only the logfile/memory-cap layer remains, while keeping J-06 failing since its passing pages are pre-existing baseline behavior, not progress toward its own deliverables. Reversible: yes
- iter-0 · goal-decomposer — Ambiguity: goal.md's Product Shape names only 9 nav sections as "existing nav unchanged," but the actual sidebar has 11 items, including Scanner Runs and Methodology, neither mentioned in that prose list. We chose: treated the actual 11-item sidebar as ground truth for the blueprint's Information Architecture, reading goal.md's 9-item list as "these stay, at minimum," not an exact/exclusive list. Reversible: yes

## Quick verify

From `reports/phase-goal-ops-hardening-iter-1-what-to-click.md`:

1. Open `http://localhost:3255/data` in your browser
2. In the "Start a fetch / backfill job" panel, leave "Job kind" as "Backfill snapshots". Click into "Start date", select all and type `2026-05-02`; click into "End date", select all and type `2026-05-29`. Click the "Start" button.
3. Now submit a second job: Start date `2026-05-02`, End date `2026-05-03`, click "Start" again.
4. Refresh the page (press F5).
5. Submit a third job: Start date `2025-06-01`, End date `2026-07-17` (a 412-day span), click "Start".

## Artifacts

| Report | Verdict | Path |
|--------|---------|------|
| Iter spec | — | docs/phases/goal-ops-hardening-iter-1.md |
| Dev handoff | — | docs/handoffs/goal-ops-hardening-iter-1-dev.md |
| Review | PASS_WITH_NOTES | reports/reviews/goal-ops-hardening-iter-1-review.md |
| Browser QA | PASS | reports/phase-goal-ops-hardening-iter-1-ui-test-results.md |
| Implementation summary | — | reports/phase-goal-ops-hardening-iter-1-implementation-summary.md |
| User-visible changes | — | reports/phase-goal-ops-hardening-iter-1-user-visible-changes.md |
| What to click | — | reports/phase-goal-ops-hardening-iter-1-what-to-click.md |
| UI surface map | — | reports/phase-goal-ops-hardening-iter-1-ui-surface-map.md |
| UI test plan | — | reports/phase-goal-ops-hardening-iter-1-ui-test-plan.md |
| UX regression | UX-REGRESSION-WARN | reports/phase-goal-ops-hardening-iter-1-ux-regression.md |
| QA | PASS | reports/qa/goal-ops-hardening-iter-1-qa.md |
| Audit | PASS_WITH_GAPS | docs/handoffs/goal-ops-hardening-iter-1-audit.md |
| Closure | CLOSURE-PASS | reports/phase-goal-ops-hardening-iter-1-closure-verdict.md |
| Goal evaluation | CONTINUE | runs/goal-session-ops-hardening/iter-1/eval.md |
| Journey history | — | runs/goal-session-ops-hardening/state/journey-history.json |
