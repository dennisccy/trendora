# Phase goal-mcp-loop-iter-27 — UI Surface Map

**Phase:** goal-mcp-loop-iter-27
**Date:** 2026-07-11
**Written by:** ui-impact-analyst

---

## Context

No frontend file changed this iteration (`git diff --stat` against `apps/frontend/` is empty). The
changed files are all backend: `apps/backend/app/engine/prices.py`, `regime.py`, `scoring.py`,
`data_manager.py`, `apps/backend/app/config.py`, `config.yaml`,
`incredible_auto_dev/scripts/start-backend.sh`, `apps/backend/tests/test_scoring_window.py`, and
`reports/perf-budgets.md`. This is a two-pass memory-hardening fix for the `MemoryError` crash that
iter-26 introduced when the full-universe "Rebuild snapshots" job ran to completion — an unresolved
critical anti-goal #8 violation. The first pass (read-side windowing in `regime.py`/`scoring.py`) was
audited and found **insufficient** on its own (a live second consecutive rebuild still crashed); the
second pass (glibc `MALLOC_ARENA_MAX` cap + a `gc.collect()`/`malloc_trim` cleanup in `data_manager.py`)
specifically targets cross-job memory accumulation.

Because no UI code moved, this map is built around **regression re-verification**: the `/data` rebuild
job (now including a required **second consecutive run**, per the coordinator's framing and the audit's
own B1 finding), the surface that re-displays the changed calculation's output (Dashboard's Market
Regime card), and the 8 required-still-passing journeys carried SKIPPED (not regressed) through iter-26's
outage.

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | `RebuildPanel` — "Rebuild snapshots for current universe" button + confirm dialog (`apps/frontend/app/data/page.tsx:799`) | Changed behavior (backend fix beneath unchanged UI code) | Target journey J-16 / anti-goal #8: this exact job, run over the full universe, crashed the backend with a `MemoryError` in iter-26. `regime.py`'s three `bars_asof` call sites and `scoring.py`'s two slice sites now read a bounded trailing window instead of the whole multi-decade history. | Stop the backend, cold-start it, open `/data`, click "Rebuild snapshots for current universe", confirm the modal, and let the job run over the full 322-date × 541-member universe. Confirm the backend stays reachable through the deep-history dates that previously crashed it (dot-com ~2000-2003, 2008 GFC, COVID 2020, most recent dates) and the job reaches a genuinely-completed (`status: ok`) state — not a hung/wedged backend, not a crash. |
| `/data` | `RebuildPanel` — **second consecutive rebuild**, same session, no backend restart | Changed behavior (backend fix beneath unchanged UI code; this is the specific scenario the first dev pass FAILED and the second pass targets) | Audit finding B1: a first full-universe rebuild barely survived (212 MB margin) but a **second** consecutive rebuild pinned the process at the `ulimit -v` ceiling and crashed with `MemoryError` — proving the read-side windowing alone did not clear cross-job memory accumulation. The second pass (`MALLOC_ARENA_MAX=2` + `gc.collect()`/`malloc_trim(0)` in `data_manager._do_backfill`'s `finally`) targets exactly this. | Immediately after the rebuild in the row above reaches `status: ok`, click "Rebuild snapshots for current universe" again on the same `/data` session (no backend restart in between) and let it run to completion. Confirm the backend survives this second run too, `/api/health` stays 200 throughout, and the job reaches `status: ok` a second time — not merely that the first run succeeded. |
| `/data` | `JobProgressPanel` (the live job card the rebuild polls into, `apps/frontend/app/data/page.tsx:2400`) | Changed behavior (backend fix beneath unchanged UI code) | Anti-goal requirement "never report done early" / iter-26b lesson: a verified crash on the driven path is a journey failure regardless of causation, and the panel's honesty must hold through both the first and second full runs, not just a short one. | While each rebuild run from the two rows above is in progress, watch the job card's progress counter and "updated Ns ago" heartbeat text. Confirm the counter advances monotonically (never jumps backward, never resets, never shows "done" before all 322 dates are processed) and the heartbeat keeps updating (not stale) for the full duration of both runs. |
| `/data` | Whole page — cold-start path, contained "Backend unavailable" card | Regression check (iter-24 lesson: a fix must be re-verified via the cold-start-first repro, not just a warm health check) | `GET /api/data`'s availability computation is on the changed read path; a cold first request is the historically fragile case (iter-24/25), and if the memory fix were incomplete this is the boundary the page must degrade to instead of crashing blank. | Stop the backend, cold-start it, and load `/data` as the very FIRST request (before hitting any other route or `/api/health`). Confirm the page renders populated coverage/availability data (not a blank crash). Repeat the stop → cold-start → `/data`-first sequence a second time. Then load `/stocks` and confirm it loads, and `GET /api/health` returns 200. If the backend is instead deliberately kept stopped, confirm `/data` shows exactly one contained "Backend unavailable" card with nav/shell intact — not a blank application-error page. |
| `/` (Dashboard) | `RegimeGlanceCard` — "Market Regime" badge, 0–100 score, and the component-breakdown disclosure | Changed behavior (backend fix beneath unchanged UI code) | This card re-displays `regime.score_regime`'s output verbatim — the exact function whose three `bars_asof` call sites (`_index_ma_stack`, `_universe_stats`, `_latest_vix`) this iteration's first pass rewrote to use `bars_asof_window`/`close_on`. A byte-identity unit test asserts no value drift, but that must be re-confirmed live. | Load `/`, note the Market Regime badge label, the 0–100 score value, and expand the component breakdown to note each named component's value. Confirm none renders as blank, "—", or a stale/frozen value, and cross-check the score against the API's regime output for the same as-of date. |
| `/stocks` | Leaderboard rows + evidence-status badges ("Proven" / "Not yet proven") | Required-still-passing journeys J-01, J-03, J-12 (re-verify live; code unaffected by this diff, carried SKIPPED behind iter-26's outage) | These journeys were carried SKIPPED (not regressed) through iter-26 because the outage blocked the canonical browser-qa lane from running at all; they must now be re-driven on the fixed, live build. | Visit `/stocks`. Confirm every leaderboard row's score area shows an evidence badge reading either "Proven" or "Not yet proven" (J-01) — none blank. Confirm at least one unproven signal reads "Not yet proven" rather than a confident-looking number (J-03). Confirm a mid-history IPO name appears only from its real listing date onward, and a delisted name exits the leaderboard cleanly with no fabricated late rows (J-12). |
| `/stocks/{ticker}` (e.g. `/stocks/AAPL`) | Detail page — price chart / Full-history toggle | Required-still-passing journey J-10 (re-verify live) | Deep (~30-year) price-history display; code path is separate from the changed `regime.py`/`scoring.py` accessors, but was carried SKIPPED behind iter-26's outage. | Open `/stocks/AAPL`, toggle to full history, and confirm the chart extends back toward AAPL's real historical span with no discontinuous price jump. Then open a post-IPO name and confirm it honestly shows only its real short history, not a fabricated extension. |
| `/evidence` | Certified-claims ledger list | Required-still-passing journey J-05 (re-verify live) | Code unaffected by this diff; carried SKIPPED behind iter-26's outage. | Click "Evidence" in the nav. Confirm the ledger list renders with, for each claim, a hypothesis, out-of-sample verdict, control comparison, registration date, and forward-walk score-to-date. Click one claim and confirm it links back to the surface whose "Proven" status it backs. |
| `/`, `/stocks`, `/stocks/{ticker}`, `/data`, `/evidence` (+ their APIs) | Time-to-interactive / warm API latency | Required-still-passing journey J-15 (re-verify live) | Perf budgets are a "never-regress" contract; the memory-hardening change (bounded windowing + allocator cap + GC/trim) should not have slowed anything, but must be re-measured, not assumed. | With a warm backend started via `start-backend.sh` (not `dev.sh`, which is intentionally left uncapped/unhardened this iteration), time page loads for `/stocks`, `/stocks/AAPL`, `/data`, and `/evidence`, plus warm latency of `GET /api/stocks`, `/api/stocks/{ticker}`, `/api/data`, and `/api/health`. Confirm every measurement still sits within the committed budgets in `reports/perf-budgets.md`. |
| `/research/*` (regime-conditioned evidence surface) | Regime-scoped evidence labeling | Required-still-passing journey J-04 (re-verify live) | Code unaffected by this diff; carried SKIPPED behind iter-26's outage. | From `/`, note the current Market Regime/phase, then open the Evidence surface or a research lab and confirm the evidence shown there is scoped to and explicitly labeled with that same regime. |

<!-- Change Type key used above: "Changed behavior (backend fix beneath unchanged UI code)" = the
     component's source file is untouched, but a backend module it depends on (compute path or process
     lifecycle) was edited this iteration, so its output/behavior must be re-verified even though nothing
     in the diff touched the frontend. "Required-still-passing journey (re-verify live)" = the surface's
     code is entirely unaffected by this diff, but the journey was carried SKIPPED through iter-26's
     outage and must be re-driven live to close that gap, per the plan. -->

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/prices.py` — new `_BarCache.bars_asof_window` + module-level
  `bars_asof_window(session, symbol, d, lookback)`. A purely additive, internal bounded-trailing-window
  bar accessor. Not exposed through any API route; no UI surface calls it directly. `bars_asof` itself
  and every other existing function/consumer in this file is unchanged.
- `apps/backend/app/engine/regime.py` — `_index_ma_stack`/`_universe_stats` now read through
  `bars_asof_window`; `_latest_vix` now reads through the existing `close_on`. No UI surface calls this
  module directly; its output (regime score) is proven byte-identical.
- `apps/backend/app/engine/scoring.py` — `_raw_components` and the pass-3 slice sites now call
  `bars_asof_window(..., lookback=icfg.max_lookback_bars)` instead of `bars_asof(...)` followed by a
  Python-level `[-N:]` slice. Mathematically identical output (byte-identity gated); no UI-visible effect
  beyond the per-stock scores it already fed, which are proven unchanged.
- `apps/backend/app/engine/data_manager.py` — new `_release_process_memory()` (`gc.collect()` +
  `malloc_trim(0)`), called in a `try/finally` wrapped around `_do_backfill`'s compute loop. Purely a
  process-memory-hygiene step (returns freed memory to the OS between jobs) — no UI surface affected, no
  computed value changes.
- `apps/backend/app/config.py` / `config.yaml` — new `server.malloc_arena_max` config field (default
  `2`). Read only by the backend launch script at process-start time; not served to or rendered by any
  page or API response.
- `incredible_auto_dev/scripts/start-backend.sh` — reads `malloc_arena_max` from config and exports it
  as the `MALLOC_ARENA_MAX` environment variable before the `ulimit -v` + uvicorn `exec`. A process
  launch-time setting, invisible to the browser. (`dev.sh`, the local dev launcher, is explicitly left
  unchanged/uncapped — this hardening applies only to the prod/browser-qa launch path.)
- `apps/backend/tests/test_scoring_window.py` — new test cases only
  (`test_score_regime_windowed_equals_unwindowed_across_dates`,
  `test_bars_asof_window_matches_tail_slice_default_and_cached`); test files have no UI surface.
- `reports/perf-budgets.md` — new dated sections "Item G" (first-pass isolated-harness measurement) and
  "Item H" (second-pass live two-consecutive-rebuild measurement, the authoritative evidence). Internal
  engineering reports, not pages a user visits.

---

## Summary

- **Frontend surfaces changed:** 0
- **New pages/routes:** 0
- **Modified components:** 0 (all rows above are re-verification of unchanged UI code against a changed
  backend compute/process-lifecycle path, not component edits)
- **Navigation changes:** no
- **Backend-only changes:** 8 (`prices.py`, `regime.py`, `scoring.py`, `data_manager.py`, `config.py`,
  `config.yaml`, `start-backend.sh`, `test_scoring_window.py`, plus the `perf-budgets.md` report)
