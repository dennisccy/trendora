# goal-ops-hardening-iter-4 Audit Report

**Date:** 2026-07-20
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

Both trust-surface defects are genuinely fixed and live-evidenced: B3 (an ordinary fetch no longer flips the global badge to a false "Backend unavailable") and F1 (the job heartbeat stays honest through the ~719s aggregate-refresh finalize tail). J-05's browser story is complete — the badge/heartbeat scenarios (UT-03/04/07) and the required-still-passing journeys (UT-J-01/03/04) all pass, true unavailability is preserved (UT-05/06), and the previously-skipped cold-boot check (TC-8) executed. All 7 DEFINITION OF DONE items are met and no anti-goal is violated. The documented gaps are all pre-existing, out-of-scope, or evidence-pipeline concerns — none is critical or important, and none compromises the phase goal.

---

## 2. Findings

### Backend Findings

**B1 — GAP (observation): two O(1) one-time finalize-tail steps still do not tick the heartbeat**
`data_manager.py` — the current-stamp `refresh_coverage_snapshot(...)` and the one-time `prefilled_bar_cache(...)` bar-cache preload at the top of `_persist_per_date_coverage_snapshots` (~`data_manager.py:3033`) run once (not per-date) and carry no `prog.tick()`. Between the function-start tick (`_refresh_ingest_aggregates`, `data_manager.py:3053`) and the first per-date tick inside the coverage loop (`:3037`), the one-time prefill is uncovered. The dev and reviewer both flagged this; the estimated cost is ~1–2s each vs the 20s `heartbeat_stale_seconds` threshold, and the per-date loops (the ~729s bulk of the tail) ARE now ticked. Live UT-07 (a real ~953s rebuild) showed no "possibly stalled" artifact. Not fixed: TC-7's contract is explicitly per-date ("advances at least once per date processed"), which is satisfied; ticking the one-time steps is outside this iteration's scope. Worth a footnote for whoever next touches the finalize tail on the deepest (30y) basis.

**B2 — OBSERVATION: a pre-existing "Live-vs-seed drift" DEGRADED preflight surfaced during the browser session (orthogonal to B3)**
`readiness.py:381` (the `drift` component of `compute_preflight`, shipped iter-35/J-21). UT-04's default fetch range (2005-03-15→2005-03-21) is empirically a window where the offline fixture provider differs from the committed seed CSV, so the drift-detector correctly fired and held the overall preflight verdict at `DEGRADED` for the rest of the session — which is why UT-03's screenshot shows `DEGRADED`, not `GO`. I confirmed this is NOT a B3 regression: the browser-qa raw log verified the `reasons` array contained only the drift bullet (never servability), and `preflight.components.servability.ok === true` throughout — exactly what TC-5 requires ("not forced to NO-GO/DEGRADED **by this condition alone**"). The isolated unit test `test_preflight_servability_ok_for_awaiting_snapshot_state` (clean ledgers) independently pins `awaiting_snapshot` → verdict `GO`. Pre-existing and out of scope; noted only because an operator running the default fetch range will see a DEGRADED banner — worth a separate look at the fixture-vs-seed inconsistency for that 2005 window in a future iteration.

### Frontend Findings

**F1 — OBSERVATION: the `awaiting_snapshot` pill shares its accent color with the adjacent "provider" badge**
`health-badge.tsx:82` — the new pill uses `variant="accent"` (per the plan's explicit instruction), but `HealthBadge` also renders the `provider:` metadata badge in that same `variant="accent"` immediately after it. In the new state — unlike ready/initializing/unavailable — color alone no longer separates "status" from "metadata." Position (pill renders first) and the long explanatory sentence still make it identifiable, so this is cosmetic, not functional. No new color token introduced. The spec left the exact accent choice to the developer; not fixed (scope creep). The ux-regression reviewer's one-line suggestion (move the provider badge to `variant="default"`) is reasonable for a future polish pass.

**F2 — OBSERVATION: an undocumented `apps/frontend/tsconfig.json` change slipped in (benign QA tooling)**
`tsconfig.json` `include` gained `.next-alt-qa/types/**/*.ts` (the browser-qa alt-instance build dir from the session's Notes item 1). Not listed in either handoff. It only adds a generated-types glob for a gitignored QA build directory — zero product-runtime impact. Not reverted (harmless; reverting risks breaking the QA typecheck lane).

### Test Findings

**T1 — GAP (mitigated to effectively closed): two `loaded_engine`-dependent tests remain unexecuted**
`test_readiness.py:268` (`test_compute_readiness_shape_unchanged_by_preflight_addition`) and `test_readiness.py:404` (`test_latest_benchmark_bar_query_is_symbol_scoped_not_whole_table_scan`) never completed a green run — the session-scoped `loaded_engine` fixture (bootstrap + forward-return backfill over the 30y/587-symbol seed) exceeds every reasonable time budget (dev, reviewer, and QA all hit the same wall; a documented repo-wide constraint). **I independently verified their substance without the fixture** (see §3): a standalone SQL-capture proved `_latest_benchmark_bar_date` emits exactly one `... WHERE daily_prices.symbol = ?` query returning SPY's own bar (not the later unrelated-symbol bars), and a standalone shape check reproduced `{state, detail, warmup}` with `detail=None` on a caught-up DB. I also verified the load-bearing transitivity claim from the seed directly (SPY's latest bar `2026-07-01` == the whole-table latest `2026-07-01`; `bootstrap_runs` persists a run for the latest date), which guarantees `awaiting_snapshot` can never fire in warmed fixtures and therefore that `test_health.py`/`test_warmup.py` are unperturbed. Residual risk is essentially closed; a completed run in a longer-budget CI lane remains the only thing that would fully retire it.

**T2 — GAP (evidence pipeline): the merged `ui-test-results.md` silently drops its `## Notes` section**
`reports/phase-goal-ops-hardening-iter-4-ui-test-results.md` references "(see Notes for the one caveat)" three times (UT-03, UT-04, UT-07) but contains no `## Notes` section — it ends at `## Environment`. This directly undercuts this session's own iter-3 lesson (the DoD's item #1 says "read the raw `ui-test-results.md` browser verdict directly"). **The content is not lost:** the raw browser-qa output (`...ui-test-results.llm.md`) contains the complete, thorough, self-critical 8-item Notes section, which I read in full. All caveats are benign (environment/tooling issues found-and-fixed, honest methodology adjustments where the assertions still hold, and the pre-existing drift condition of B2). The defect is in the framework merge step (`merge_ui_test_results.py`), not the product and not the browser-qa-agent's honesty. Not fixed: it is framework tooling, and editing the QA report to backfill Notes would be fabricating evidence. Recommend the pipeline owner fix the merge script so the DoD's "read the raw verdict" instruction points at a complete artifact (the ux-regression reviewer independently raised the same recommendation).

---

## 3. Domain Assessment

The core domain logic is correct and the fixes are surgical.

**B3 (readiness servability).** The rewrite is sound. Servability is now `has_servable_run = latest_run is not None` (the sole unconditional case — a true never-scanned DB always resolves `unavailable`, regression-guarded), and the new `awaiting_snapshot` fires only when the **benchmark's own** latest bar (`_latest_benchmark_bar_date`, `readiness.py:78`) outruns the last run. Critically, the state ordering preserves `initializing` **byte-identically**: `awaiting_snapshot` is checked before `initializing`, but in the OLD code the same "benchmark bar > latest_run" condition produced `unavailable` (whole-table `latest_data ≥ benchmark_bar > latest_run` failed the old `latest_run >= latest_data` servable check), so the new branch only ever preempts what was previously the false `unavailable`, never a legitimate `initializing`. I verified this three ways: (1) direct code read; (2) a standalone run of `compute_readiness` on a caught-up tiny DB returned `initializing`/`detail=None`, and on SPY-advance returned `awaiting_snapshot` with the exact honest detail naming SPY + the pending date + the recovery action (AG-3 satisfied); (3) live browser UT-04 (a real "Fetch EOD prices" job landing 60 new bars) kept the badge on "Ready," and UT-05/UT-06 kept true unavailability rendering.

**AG-8 (no whole-table scan) is airtight.** `EXPLAIN QUERY PLAN` on the benchmark query yields `SEARCH daily_prices USING COVERING INDEX sqlite_autoindex_daily_prices_1 (symbol=?)` — a covering-index seek with **zero table-row reads**, bounded to one symbol, backed by the `UniqueConstraint("symbol","date")` (`models.py:92`). This is stronger than the reviewer's "index-bound" claim.

**F1 (heartbeat).** Complete after the re-review CRITICAL fix: the bare `prog.tick()` (which stamps only `last_progress_at`, leaving the pinned "scanning …" activity line honest — verified against `tick()`'s body at `data_manager.py:1945`) now fires at the finalize-hook start, once per date in the coverage loop (the half the first attempt missed), and once per date in the market-phase loop. The frontend `stale` flag reads `last_progress_at` directly (`app/data/page.tsx:2481-2483`), so the per-date ticks correctly reset it. The two F1 tests assert per-date advancement past a stale sentinel (not "somewhere in the call"), and live UT-07 confirmed the heartbeat advanced across the ~719s tail with no "possibly stalled."

**Data-contract cleanliness.** Both `readiness.state` and the new `readiness_detail` are served from the single `compute_readiness` call in the single `/api/health` handler (`health.py:91,95`) — no second computing module, no second endpoint, purely additive. The coherence concern the spec flagged for this row does not materialize.

**DoD scorecard:** J-05 browser-clean (UT-03/04/07 pass, UT-08/TC-8 executed) ✓ · B3 fixed + evidenced live ✓ · F1 fixed + evidenced live ✓ · J-01/J-03/J-04 green (UT-J-01/03/04) ✓ · no anti-goal violation (AG-3/AG-8/AG-9) ✓ · unit tests pass (6/6 re-run green by me, 1.00s) ✓ · dev handoff written and honest ✓.

---

## 4. Fixes Applied During This Audit

None. Every finding is GAP- or OBSERVATION-level; per the auditor protocol these are documented as known limitations, not fixed (fixing them would be scope creep). No CRITICAL or IMPORTANT issue was found that would compromise the phase goal.

---

## 5. Recommended Next Step

**Proceed.** J-05 is materially complete — B3 and F1 are genuinely fixed with converging unit, standalone, query-plan, and live-browser evidence, and the required journeys are green. The goal-evaluator can score J-05 `passing` and advance to J-06 (the measurement capstone), per goal.md's suggested build order and the iter-3 eval's sequencing.

Two non-blocking follow-ups for the session/framework owner, neither gating J-05:
1. Fix `merge_ui_test_results.py` so the merged `ui-test-results.md` stops dropping its `## Notes` section (T2) — the DoD's own "read the raw verdict directly" instruction depends on that artifact being complete.
2. Capture a completed `pytest tests/test_readiness.py tests/test_health.py -v` in a longer-budget CI lane to formally retire T1 (substance already verified this audit).
