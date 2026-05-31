# goal-i_can_see_the_wealthy_future-iter-10 Execution Plan

**Journey:** J-14 — Backtest / Time-Machine workspace + per-date forward-test scorecard.
**Mode:** full-depth IMPLEMENTATION. This is a **re-execution** of the iter-9 plan, which silently no-op'd
(zero product code). Verified at plan time from git + filesystem: `apps/backend/app/api/backtest.py` absent,
`apps/frontend/app/backtest/page.tsx` absent, `grep -rln backtest apps/` empty, and `forward_testing.py`'s
def list ends at `compute_forward_aggregates` (iter-6) — none of `compute_run_scorecard` /
`backfill_run_forward_returns` / `_insert_run_forward_returns` exist. **The developer MUST treat this as
greenfield for J-14 and actually write the code — do NOT assume any of it exists.**

**Goal alignment:** Directly advances `docs/goal.md` capability #17 and Must-have journey J-14; `/backtest` is
already in the goal's Product Shape and the session blueprint IA (rows added + human-approved in iter-9). **No
goal drift.** The blueprint already carries the Backtest IA row, the J-14 feature-home row, the *Per-date
forward-test scorecard* Data-Contract row, AND the iter-10 provenance note — so **no contract value, computing
module, or serving path changes** this iter, and **no new `blueprint.reapproval-requested`** is written (the
nav approval was consumed on the iter-9→iter-10 resume).

## What to Build

- **Refactor (no behaviour change):** factor the per-run forward-return INSERT loop out of `_backfill` into
  one shared helper `_insert_run_forward_returns(session, run, symbols, horizons, max_h, existing) -> int`.
  ONE forward-return math implementation — the iter-6 `test_forward_testing.py` suite must stay **byte-green**.
- **`backfill_run_forward_returns(session, run, config=None) -> dict`** — create-once, INSERT-only population
  of one run's forward returns into the existing append-only `forward_returns` table (idempotent: 2nd call
  inserts 0 rows; never UPDATEs a `scanner_runs`/`scanner_results`/`*_scores` row). Frozen-seed-only.
- **`compute_run_scorecard(session, run, config=None) -> dict`** — the SINGLE canonical per-date scorecard.
  READS stored `forward_returns` for `run.id` joined to stored `scanner_results` (bucket/setup/sector/rank
  **verbatim**) + the run's stored regime label; recomputes nothing. Per horizon (1/5/10/20/60): cohort mean
  return + `n` (cohort = rank ≤ `control_group.top_n`); excess vs SPY / QQQ / sector (each + `n`); and the 5
  control-group cohorts (each `mean_return` + `n`). No data for a horizon/cohort → `mean_return: null` / `n: 0`
  (honest NA — **never a fabricated 0%**). Reuse `benchmark_symbols` / `_control_groups` / `_mean_or_none`
  scoped to this run's observations; carry `min_sample`, `horizons`, `SURVIVORSHIP_BIAS_LABEL` verbatim.
- **New router `GET /api/backtest?as_of=YYYY-MM-DD`** (mirror `app/api/system_health.py`): resolve via the
  iter-8 `snapshot_serving.resolved_run` (latest when omitted; create-once for a new date; invalid → explicit
  4xx/503 via `_STATUS_BY_KIND` — never fabricated), call `backfill_run_forward_returns(session, run)`, return
  the payload below. Serves the **scorecard only** — NOT regime/sector/theme/stock (those stay single-sourced).
- **New page `/backtest`** with its own date picker (options from `fetchRuns()`, default latest), an **as-of
  scan summary** (reusing existing `fetchDashboard/fetchSectors/fetchThemes/fetchStocks` with `?as_of=D`), and
  a **forward-test scorecard** table from `fetchBacktest(D)`, plus survivorship banner + "Viewing as-of D".
- **Sidebar entry** `{ href: "/backtest", label: "Backtest", icon: FlaskConical }` after Scanner Runs / before
  System Health. **`lib/api.ts`** `fetchBacktest` + the three Backtest types.
- **Unit/integration tests** (see Key Test Scenarios) + **dev handoff**.

API payload shape:
```
{ "asof_date", "is_latest": bool, "min_sample": int, "horizons": [1,5,10,20,60],
  "survivorship_bias": <label verbatim>,
  "scorecard": { "by_horizon": [ {horizon, cohort:{mean_return,n},
                 excess:{vs_spy,vs_qqq,vs_sector}, control_group:[…5 cohorts…]}, … ] } }
```

## Agents Required

- developer: **yes** — backend-data: **yes** (forward-testing refactor + 2 new engine fns + `_insert_run_forward_returns` + new `app/api/backtest.py` + main.py wiring + tests); frontend-ux: **yes** (new `/backtest` page, sidebar entry, `lib/api.ts` client + types).

## Frontend Present

Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/engine/forward_testing.py` — **modify**: add `_insert_run_forward_returns` (factored from `_backfill`'s inner loop; `_backfill` calls it), `backfill_run_forward_returns`, `compute_run_scorecard`. Reuse `forward_return`/`close_on`/`bars_after`/`_control_groups`/`benchmark_symbols`/`_mean_or_none`/`SURVIVORSHIP_BIAS_LABEL`. No new literals — pull horizons/min_sample/top_n from `config.walk_forward`.
- `apps/backend/app/api/backtest.py` — **create**: `GET /api/backtest`, mirrors `system_health.py` structure; resolves via `snapshot_serving.resolved_run`.
- `apps/backend/main.py` — **modify**: import `backtest`, `app.include_router(backtest.router, prefix="/api")`.
- `apps/backend/tests/test_backtest_scorecard.py` and/or `test_api_backtest.py` — **create** (engine + API tests).
- `apps/frontend/app/backtest/page.tsx` — **create**: the workspace (own date picker + scan summary + scorecard).
- `apps/frontend/components/sidebar.tsx` — **modify**: add the `/backtest` NAV entry (after Scanner Runs).
- `apps/frontend/lib/api.ts` — **modify**: add `fetchBacktest(asof, signal)` via `withAsOf("/api/backtest", asof)` + types `BacktestScorecardHorizonRow` / `BacktestScorecard` / `BacktestResponse` (`mean_return`/`mean_excess` are `number | null`; every figure carries `n` — mirror `SystemHealthResponse`/`ForwardGroupRow`/`ControlGroupRow`).

## UI Evolution (Frontend Present: yes)

- **New user-facing capability:** time-travel to any historical scan date in a dedicated workspace and read post-hoc evidence of how that date's ranked cohort actually performed over 1/5/10/20/60 days vs SPY/QQQ/sector and a random same-sector control, with sample sizes and honest NA.
- **New information displayed:** the per-date forward-test scorecard (per-horizon cohort return, excess vs SPY/QQQ/sector, the 5 control-group cohorts, each with `n` and honest NA). The scan summary re-displays existing canonical values (regime/sectors/themes/ranked stocks) for the chosen date.
- **New user actions:** open Backtest from the sidebar; pick a historical as-of date from the workspace's own picker (re-fetches scan summary + scorecard).
- **UI surface changes:** new `/backtest` page (two sections + date picker); new **Backtest** sidebar entry.
- **Navigation changes:** one new top-level sidebar link `Backtest` (already in the approved blueprint IA).

## Visual Requirements (Frontend Present: yes)

- **Component patterns:** reuse `Card`, `PageHeading`, `EmptyState`, `Badge`/`bucketVariant`, and the System Health table idiom. **Reuse the exact `fmtPct` / `returnClass` / `SampleSize` / `Return` helpers** from `system-health/page.tsx` (lift to a shared module or mirror them) — `n < min_sample` flags the `--warn` ⚠ token; NA renders as `—` with `n=0`. Date picker mirrors the `asof-switcher` styling.
- **Layout:** sidebar + main content; scan-summary panels in a grid, scorecard as a dense monospace (`num`/tabular-nums) table (rows = horizons; columns = cohort, excess vs SPY/QQQ/sector, random-same-sector control + the SPY/QQQ/sector-ETF controls, each with `n`).
- **Key visual effects:** dark analytical workstation tokens only; green/red return grading via `returnClass`; survivorship-bias warn banner (mirror `SurvivorshipBanner`); a clear "Viewing as-of D" indicator.
- **States to handle:** loading skeleton, empty (no scorecard yet), error / "Backend unavailable" (never a fabricated number), and partial/NA horizons for recent dates.

## Key Test Scenarios

Backend unit/integration (every figure from `config.walk_forward` — `test_no_magic_numbers` must stay green; iter-6 `test_forward_testing.py` must stay **byte-green** after the refactor):
- **No-lookahead boundary:** scorecard for run D measures returns only from bars date > D (entry close ON D); no bar date ≤ D contributes — reuse the iter-6 `bars_after`(>D) vs `close_on`/`bars_asof`(≤D) partition.
- **Honest partial/NA:** a run with fewer than `h` post-snapshot bars → `mean_return: null` / `n: 0` for horizon `h` while observable shorter horizons render numerically; the latest-date run (0 post-bars) is all-NA.
- **KEYSTONE (no recompute — patch-to-raise seam, NOT value-equality):** after a date is populated, monkeypatch `forward_testing.forward_return` AND `app.engine.scanner.{score_stocks,score_regime,score_sectors,score_themes}` to **raise**, then assert `GET /api/backtest?as_of=D` (or `compute_run_scorecard`) still serves the scorecard from stored rows. (Mirrors `test_api_engine.py::test_repointed_handlers_serve_persisted_date_without_recompute`, extended to patch the forward-return math too.)
- **Create-once + immutable:** 2nd `/api/backtest` view of the same date INSERTs **zero** new `forward_returns` rows and performs **no UPDATE** on `scanner_runs`/`scanner_results` (mirror `test_backfill_inserts_forward_returns_without_mutating_snapshot` + `test_backfill_is_idempotent`).
- **Single source (read stored, don't re-bucket):** cohort observations group by the **stored** bucket/setup/rank/sector verbatim; cross-check `compute_run_scorecard` scoped to one run agrees with `compute_forward_aggregates` filtered to that run (proves the shared math).
- **Error cases:** invalid `as_of` → explicit status via `_STATUS_BY_KIND` (future→400, unparseable→422, before_history→400, no_data→503); omitted → latest stored run. Never a fabricated scorecard.

Browser (J-14) — **distinct, md5-checked, focused captures** (do NOT save one full-page shot under two names):
1. **Backtest** sidebar entry present and routes to `/backtest`.
2. **Full-window date** (older run, ≥60 post-bars): scan summary renders (regime label ∈ six + numeric score; ≥3 top sectors; ≥3 top themes; candidate counts; ranked cohort) AND the scorecard renders **numeric** 1/5/10/20/60d cohort returns with excess-vs-SPY/QQQ/sector + random-same-sector-control columns, each with `n`; survivorship banner visible. (Focused capture of the scorecard panel.)
3. **Partial/NA date** (latest/recent): longer horizons show `—` / NA with `n=0`, never fabricated. (Separate focused capture.)
4. Re-shoot **J-13** (switch `/` or `/stocks` to a historical date) to confirm the global switcher did not regress.

Frontend: `npm run build` clean (compile + typecheck). Live-verify (iter-7 lesson): backend with `CORS_ORIGINS=http://localhost:<frontend-port>`, frontend built with `NEXT_PUBLIC_API_URL=http://localhost:8835`; `await_text` on a scorecard cell value (an `n=` or a `%`), never a heading or the date-picker placeholder.

## Definition of Done (gating)

- Implementation actually present (git + filesystem shows real `apps/` changes); dev handoff at `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-10-dev.md`.
- J-14 passes (per browser scenarios above, or reconciled from on-disk QA PNGs + unit/API proofs + source if the dedicated browser-qa SKIPs — see Out of scope).
- Required-still-passing green: J-13, J-01/02/03/04 (scan summary reuses their endpoints), J-06/J-15 (single source / snapshot-served), J-09/J-10 (System Health aggregate unchanged — refactor is pure).
- No anti-goal violation; full backend pytest green; frontend build clean.

## Out of Scope / Scope Flags

- **J-16 (VCP)** and **J-12 (glossary / `/methodology`)** — next iterations; no VCP detector/filter/badge, no glossary page this iter.
- No by-bucket / by-setup breakdown on the per-date scorecard (that cross-date aggregate is System Health's job, J-09) — scorecard is cohort + excess + control-group only.
- **No `models.py` change, no new table** — forward returns reuse the existing append-only `forward_returns`. No new lifespan/boot job (create-once lives in the request path). No change to `/api/system-health`, `/api/runs`, `/api/runs/{run_id}`, or any iter-2/3/8 read endpoint contract. The global top-bar switcher's scope is unchanged (`/backtest` uses its own picker). **No new `blueprint.reapproval-requested`.**
- **Chronic runner-script debt (NON-gating — do NOT chase via this spec):** the dedicated browser-qa has SKIPPED on the HTTP-000/CORS flap and the audit handoff has been missing for 8+ iters, and iter-9 was a silent dev-step no-op. These are **runner-owner (`scripts/automation/*.sh`) issues, not product/spec scope** — do not re-litigate them here. If browser-qa SKIPs again, the evaluator reconciles J-14 from the on-disk evidence PNGs + unit/API proofs + direct source reads.
