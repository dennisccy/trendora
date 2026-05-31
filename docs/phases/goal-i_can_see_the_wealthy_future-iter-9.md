# Goal Iteration 9 — Backtest / Time-Machine workspace + per-date forward-test scorecard (J-14)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future
- **Iteration:** 9
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-14
- **Required-still-passing journeys:** J-13, J-01, J-02, J-03, J-04, J-06, J-09, J-10, J-15
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. The scan is computed once per date (bootstrap, scheduled, or first view) and then read from storage. *(extends Single source of truth)*
  - **On-demand snapshots stay immutable & lookahead-free.** Creating a snapshot for a newly selected date is create-once: an existing snapshot MUST be read, never overwritten; an as-of-D snapshot MUST use only bars with date ≤ D. *(critical)*
  - **Honest forward-test for partial windows.** The per-date forward-test scorecard and the VCP-vs-non-VCP breakdown MUST show NA/partial for horizons or cohorts lacking enough samples and MUST show sample size — never fabricate or extrapolate a return to fill a gap. *(extends No fabricated data)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **No order/execution path.** No brokerage, order-placement, or capital-deployment code may exist or be reachable; Trendora is research-only. *(critical)*
  - **No secrets in source.** No hard-coded credentials, API keys, or tokens anywhere.
  - **Honest limitations surfaced.** Walk-forward evidence MUST be labelled as carrying survivorship bias (current-membership universe) so results are never overstated.

## GOAL

A user can open a **Backtest / Time-Machine** workspace (`/backtest`), pick a historical as-of date, see that date's full as-of scan (regime, top sectors/themes, the ranked cohort), and read a **per-date forward-test scorecard** — realized 1/5/10/20/60-day returns, excess vs SPY/QQQ/sector, and a random same-sector control — computed only from seed bars *after* that date, with sample size and partial/NA horizons shown honestly.

## BACKGROUND

iter-8 landed the as-of resolver (`app.engine.scanner:resolve_run`, create-once + immutable + lookahead-free) and the global switcher (J-13); iter-6 landed the forward-testing engine (`app.engine.forward_testing`: `bars_after` date>D partition, `forward_return`, `_control_groups`, `compute_forward_aggregates`) and the append-only `forward_returns` table (J-09, J-10). J-14 is the single-date drill-down that composes both: it reuses `resolve_run` for the as-of scan and the iter-6 forward-return math for a **single run's** scorecard. The evaluator (iter-8 `eval.md`) recommended this exact next step at **full** depth. This adds the `/backtest` sidebar route → a nav-skeleton change → `blueprint.reapproval-requested` is written this iteration.

**Lessons applied (from `lessons.md`):**
- **iter-8 (explicitly names J-14):** prove "serves from storage, not recompute" with a **patch-the-compute-to-raise seam**, NOT served==stored value-equality (value-equality cannot prove a negative). Prefer **append-only** changes to the canonical compute path. → see TESTING (keystone test) and the create-once design below.
- **iter-6:** when target journeys are multiple panels of ONE page, evidence PNGs can be byte-identical full-page captures saved under two names — request **focused/distinct captures** per panel (scan-summary, full-window scorecard, partial/NA scorecard) and md5 them. → see TESTING REQUIREMENTS.
- **iter-7:** for any new frontend-facing route verified live, the backend must run with `CORS_ORIGINS=http://localhost:<frontend-port>` and `NEXT_PUBLIC_API_URL` baked to the backend port; `await_text` must target a row-only value, never a form placeholder. → see NOTES.

## IN SCOPE

### Backend

- [ ] **`app.engine.forward_testing` — factor the per-run INSERT loop into a shared helper.** Extract the body of `_backfill`'s `for run in runs:` inner loop (the per-`(symbol, horizon)` forward-return INSERT: `close_on(D)` entry, `bars_after(D, limit=max_h)` exit, `forward_return(...)`, idempotent `existing`-set guard) into a single reusable function (e.g. `_insert_run_forward_returns(session, run, symbols, horizons, max_h, existing) -> int`). `_backfill` calls it per run. This keeps **ONE** implementation of the forward-return math (single source — no second formula). Pure refactor: the iter-6 forward-testing tests MUST stay byte-green.
- [ ] **`app.engine.forward_testing:backfill_run_forward_returns(session, run, config=None) -> dict`** — create-once population of one run's forward returns. INSERTs only the missing `(run_id, symbol, horizon)` keys for the given run via the shared helper; idempotent (a 2nd call inserts 0 rows); **INSERT-only** into the append-only `forward_returns` table — never UPDATEs/overwrites a `scanner_runs`/`scanner_results`/`*_scores` row (*Snapshots immutable* critical). Frozen-seed-only. This is the "first view computes once" path the *No recompute in the read path* anti-goal explicitly permits.
- [ ] **`app.engine.forward_testing:compute_run_scorecard(session, run, config=None) -> dict`** — the SINGLE canonical per-date scorecard. **READS** the stored `forward_returns` rows for **this `run.id`** joined to the stored `scanner_results` (bucket / setup / sector / rank, read **verbatim**) and the run's stored regime label — it RECOMPUTES no score/bucket/return. For **each** horizon in `config.walk_forward.horizons` (1/5/10/20/60) it returns: the as-of **cohort** mean realized return + `n` (cohort = stocks ranked ≤ `config.walk_forward.control_group.top_n`, matching the control-group "top_ranked" definition); **excess** = cohort mean − benchmark mean for **vs_spy / vs_qqq / vs_sector** (sector = the sector-ETF cohort over the sectors the top cohort occupies), each with `n`; and the **control-group** cohorts (`top_ranked` / `random_same_sector` / `spy` / `qqq` / `sector_etf`), each with `mean_return` + `n`. A horizon (or cohort) with no stored realized return for the run → `mean_return: null` / `n: 0` (NA) — **never a fabricated 0%** (*Honest forward-test for partial windows* critical). Reuse `benchmark_symbols`, `_control_groups`, `_mean_or_none` (scope their inputs to this run's observations + this horizon) — do not duplicate that math. Payload also carries `min_sample` (`config.walk_forward.min_sample`), `horizons`, and the `SURVIVORSHIP_BIAS_LABEL` verbatim.
- [ ] **New router `app.api.backtest` → `GET /api/backtest?as_of=YYYY-MM-DD`**, registered in `main.py` (`app.include_router(backtest.router, prefix="/api")`). Resolve the date via the existing `app.engine.snapshot_serving:resolved_run(session, as_of)` (reuses the iter-8 resolver + the `_STATUS_BY_KIND` HTTP mapping — default = latest stored run; create-once for a not-yet-stored date; invalid date → explicit 4xx/503, **never** a fabricated snapshot). Then call `backfill_run_forward_returns(session, run)` (create-once) and return:
  ```
  { "asof_date": <resolved ISO date>,
    "is_latest": <bool: resolved == latest stored run date>,
    "min_sample": <int>, "horizons": [1,5,10,20,60],
    "survivorship_bias": <label verbatim>,
    "scorecard": { "by_horizon": [ {horizon, cohort:{mean_return,n},
                                    excess:{vs_spy,vs_qqq,vs_sector}, control_group:[…5 cohorts…]}, … ] } }
  ```
  The endpoint serves the per-date scorecard ONLY (the genuinely new value). It does NOT re-serve regime/sector/theme/stock values — those stay single-sourced on their existing canonical endpoints (see Frontend).

### Frontend

- [ ] **New page `apps/frontend/app/backtest/page.tsx`** — the Backtest / Time-Machine workspace. A **dedicated date picker** (the page's primary control — independent of the global top-bar switcher) whose options come from the canonical immutable run list (`fetchRuns()` → `/api/runs`, exactly as `AsOfProvider` does; default = latest). Selecting a date D drives the page's fetches. Renders two sections:
  - **As-of scan summary** — regime panel (label + 0–100 score), top sectors, top themes, candidate counts, and the ranked cohort. **Reuse the EXISTING canonical client fetchers** with `as_of=D`: `fetchDashboard(D)` (regime + breadth + candidate counts), `fetchSectors(D)` (slice top N), `fetchThemes(D)` (slice top N), `fetchStocks(D)` (the ranked Actionable/watch cohort). No new source for these values — same endpoints J-13's switcher and J-01–J-04 use → byte-identical (single source).
  - **Forward-test scorecard** — the per-horizon table from `fetchBacktest(D)`: rows = 1/5/10/20/60d; columns = cohort mean return, excess vs SPY, excess vs QQQ, excess vs sector, and the random same-sector control (+ the SPY/QQQ/sector-ETF control cohorts), each with `n`. NA renders as "—" with `n=0`; figures with `n < min_sample` flagged with the `--warn` ⚠ token (reuse the `fmtPct` / `returnClass` / `SampleSize` / `Return` patterns from `system-health/page.tsx`). A **survivorship-bias banner** and a **"Viewing as-of D"** indicator are visible. Loading / empty / error / "Backend unavailable" states styled per the established pattern — never a fabricated number.
- [ ] **`apps/frontend/components/sidebar.tsx`** — add a top-level nav entry **`{ href: "/backtest", label: "Backtest", icon: <lucide icon, e.g. FlaskConical or CalendarClock> }`**. Place it after **Scanner Runs** / before **System Health** (drill-down family). *(This is the nav-skeleton change driving `blueprint.reapproval-requested`.)*
- [ ] **`apps/frontend/lib/api.ts`** — add `fetchBacktest(asof, signal)` (uses `withAsOf("/api/backtest", asof)`) + the types `BacktestScorecardHorizonRow`, `BacktestScorecard`, `BacktestResponse` (mirror the existing `SystemHealthResponse` / `ForwardGroupRow` / `ControlGroupRow` shapes; `mean_return`/`mean_excess` are `number | null`, every figure carries `n`).

### New user-facing capability

The user can time-travel to any historical scan date in a dedicated workspace and read hard, post-hoc evidence of how that date's ranked cohort actually performed over the next 1/5/10/20/60 trading days — versus SPY/QQQ/sector and a random same-sector control — with sample sizes and honest NA for windows that haven't fully elapsed in the seed.

### New information displayed

The per-date forward-test **scorecard** (per-horizon cohort return, excess vs SPY/QQQ/sector, control-group cohorts, each with `n` and honest NA) — a NEW Data-Contract value. The as-of scan summary re-displays existing canonical values (regime, sectors, themes, ranked stocks) for the chosen date.

### New user actions

- Open **Backtest** from the sidebar (`/backtest`).
- Pick a historical as-of date from the workspace's date picker; the scan summary + scorecard re-fetch for that date.

### UI surface changes

- New page `/backtest` (App Router) with two sections (as-of scan summary, forward-test scorecard) and a date picker.
- New sidebar nav entry **Backtest**.

### Product surface delta

Trendora gains its single-date evidence drill-down: System Health stays the **cross-date aggregate**, Scanner Runs stays the immutable **run list**, and Backtest becomes the **pick-a-date, see-its-scorecard** workspace — the capability that lets the user judge whether a specific past day's ranking actually paid off.

### Blueprint conformance

New page `/backtest` is added as a **new top-level sidebar section "Backtest"** (the only nav-skeleton change this iteration). This requires re-approval → `runs/goal-session-i_can_see_the_wealthy_future/state/blueprint.reapproval-requested` is written (one-line reason) **and** the Information-Architecture skeleton + feature/journey-home table in `blueprint.md` are edited to add the Backtest row (J-14). Stock Detail / Run Detail remain row-reached; no existing home moves.

### Data-contract additions

- **Per-date forward-test scorecard (single as-of run)** — **Computed by** `app.engine.forward_testing:compute_run_scorecard` (reads stored `forward_returns` for the run + stored `scanner_results` buckets/setups/sectors/ranks **verbatim**; reuses the iter-6 `_control_groups` / `forward_return` math via the shared INSERT helper; create-once populated by `app.engine.forward_testing:backfill_run_forward_returns` into the **existing append-only `forward_returns` table** — no new table, no schema change). **Served by** `GET /api/backtest`. This is the ONLY new contract value. The `/backtest` page's as-of scan summary reads the **existing** canonical endpoints (`/api/dashboard`, `/api/sectors`, `/api/themes`, `/api/stocks` with `?as_of=`) — no second computation or serving path for regime/sector/theme/stock values. To be registered in `blueprint.md`.

## OUT OF SCOPE

- **J-16 (VCP detection)** and **J-12 (config-backed glossary)** — the next iterations after J-14, per the evaluator sequence. No VCP detector, filter, badge, glossary, or `/methodology` page this iter.
- No by-bucket / by-setup breakdown on the per-date scorecard — that cross-date aggregate is System Health's job (J-09); the per-date scorecard is cohort + excess + control-group only.
- No new persistence table and no `models.py` change — forward returns reuse the existing append-only `forward_returns` table; the snapshot tables are untouched.
- No new lifespan/boot job — the create-once population is in the request path (idempotent no-op for dates the iter-6 boot backfill already covered).
- No change to `/api/system-health`, `/api/runs`, `/api/runs/{run_id}`, or any iter-2/3/8 read endpoint's contract.
- The global top-bar as-of switcher's scope (Dashboard/Stocks/Themes/Sectors/Stock Detail) is unchanged — `/backtest` uses its own date picker.

## DEFINITION OF DONE

- [ ] **J-14 passes** via browser-qa: `/backtest` reachable from the sidebar; picking a historical date with ≥60 post-snapshot bars renders the as-of scan summary (regime label+score, ≥3 top sectors, ≥3 top themes, candidate counts, ranked cohort) AND a numeric per-horizon scorecard (1/5/10/20/60d) with excess-vs-SPY/QQQ/sector + random-same-sector-control columns + `n`; picking a recent/latest date shows partial/NA horizons (`—`, `n=0`) rather than fabricated numbers; survivorship banner visible.
- [ ] **Required-still-passing journeys remain green:** J-13 (global switcher still time-travels the 5 pages), J-01/J-02/J-03/J-04 (dashboard, stocks, themes, sectors still render — the scan summary reuses their endpoints), J-06/J-15 (single source / snapshot-served), J-09/J-10 (System Health aggregate unchanged — the forward-testing refactor is pure).
- [ ] **No anti-goal violation introduced** (all criticals above verified in source + unit-proven).
- [ ] **Unit tests pass; no regressions** — full backend pytest suite green (the iter-6 forward-testing suite byte-green after the refactor), frontend `npm run build` clean.
- [ ] **Dev handoff** written at `docs/handoffs/goal-i_can_see_the_wealthy_future-iter-9-dev.md`.
- [ ] `blueprint.md` updated (additive IA + Data Contract rows) **and** `blueprint.reapproval-requested` written for the new `/backtest` nav section.

## TESTING REQUIREMENTS

- **Browser (J-14)** — distinct, focused captures (md5-checked; do NOT save one full-page shot under two names — iter-6 lesson):
  1. The **Backtest** sidebar entry is present and routes to `/backtest`.
  2. **Full-window date** (pick an older historical run date, ≥60 post-bars): the as-of scan summary renders (regime label is one of the six + numeric score; ≥3 scored top sectors; ≥3 scored top themes; candidate counts; ranked cohort) AND the scorecard renders **numeric** mean returns for 1/5/10/20/60d with excess-vs-SPY/QQQ/sector + random-same-sector-control columns, each showing `n`. Survivorship banner visible. (Focused capture of the **scorecard** panel.)
  3. **Partial/NA date** (pick the latest / a recent date with insufficient post-bars): the longer horizons show **`—` / NA with `n=0`**, never a fabricated number. (Separate focused capture.)
  4. Re-shoot **J-13** (switch a non-backtest page, e.g. `/` or `/stocks`, to a historical date) to confirm the global switcher did not regress.
- **Unit / integration** (`apps/backend/tests/` — add `test_backtest_scorecard.py` and/or `test_api_backtest.py`):
  - **No-lookahead boundary on the per-date scorecard:** the scorecard for run D measures returns ONLY from bars with date > D (entry close ON D); assert no bar with date ≤ D contributes, reusing the iter-6 `bars_after`(date>D) vs `close_on`/`bars_asof`(date≤D) partition (analogue of `test_forward_return_uses_the_hth_post_bar` + the date>D partition).
  - **Honest partial/NA:** a run with fewer than `h` post-snapshot bars yields `mean_return: null` / `n: 0` for horizon `h` (no fabricated number), while shorter horizons that ARE observable render numerically; the latest-date run (0 post-bars) is all-NA (analogue of `test_forward_return_is_na_when_fewer_than_h_post_bars`, `test_backfill_latest_run_has_zero_post_bars`).
  - **KEYSTONE — read path recomputes nothing (iter-8 lesson, patch-to-raise seam, NOT value-equality):** after a run's forward returns are populated (first `/api/backtest` view / `backfill_run_forward_returns`), monkeypatch the forward-return math (`forward_testing.forward_return`) AND the canonical engines (`score_stocks`/`score_regime`/`score_sectors`/`score_themes` as `run_scan` references them) to **raise**, then assert `GET /api/backtest?as_of=D` (or `compute_run_scorecard`) for that already-populated date STILL serves the scorecard from stored rows. (Mirrors `test_repointed_handlers_serve_persisted_date_without_recompute`.)
  - **Create-once + immutable:** a 2nd `/api/backtest` view of the same date INSERTs **zero** new `forward_returns` rows and performs **no UPDATE** on `scanner_runs`/`scanner_results` (mirrors `test_resolve_run_create_once_then_immutable` + `test_backfill_inserts_forward_returns_without_mutating_snapshot`).
  - **Single source (read stored, don't re-bucket):** the scorecard's cohort observations group by the **stored** `leadership_bucket` / `setup_status` / `rank` / `sector` read verbatim — not a re-derivation (analogue of `test_aggregates_group_by_stored_bucket_not_rescored`); cross-check that `compute_run_scorecard` scoped to one run agrees with `compute_forward_aggregates` filtered to that run (proves the shared math).
  - **No magic numbers:** `test_no_magic_numbers` stays green — no horizon / `min_sample` / `top_n` / seed literal in `app/api/backtest.py` or the new forward-testing functions (all from `config.walk_forward`).
- **Error cases (API):** invalid `as_of` → explicit status via the existing `_STATUS_BY_KIND` map (future → 400, unparseable → 422, before_history → 400, no price data → 503); `as_of` omitted → latest stored run. Never a fabricated scorecard.

## NOTES

- **Why full depth:** new backend module + new endpoint + a new canonical Data-Contract value + a refactor of the iter-6 forward-testing INSERT path + a new frontend page + a nav-skeleton change (reapproval) + new unit tests beyond browser smoke. The evaluator (iter-8 `eval.md`) recommended full.
- **Coherence pre-empt:** the create-once `backfill_run_forward_returns` is the *No recompute in the read path* anti-goal's blessed "computed once per date / first view, then read from storage" path (it is idempotent and INSERT-only — for the dates the iter-6 boot backfill already covered it inserts 0 rows). The scorecard READ recomputes nothing; the keystone patch-to-raise test proves it. The as-of scan summary reuses the existing canonical endpoints, so no second source for regime/sector/theme/stock values — exactly the iter-8-blessed pattern (the watchlist reusing `stocks_payload`).
- **Live-verify (iter-7 lesson):** when verifying `/backtest` live, launch the backend with `CORS_ORIGINS=http://localhost:<frontend-port>` and build the frontend with `NEXT_PUBLIC_API_URL=http://localhost:8835`; `await_text` on a scorecard cell value (e.g. an `n=` or a `%`), never a page heading or a date-picker placeholder.
- **Chronic runner-script debt (NON-gating; do NOT re-attempt via this spec — proven ineffective across iters 3–8):** the dedicated browser-qa has SKIPPED on the HTTP-000/CORS flap for 8 consecutive iters, and the audit handoff has been missing 8 consecutive full-depth iters (`reports/audits/` does not exist). These are runner-owner (`scripts/automation/*.sh`) fixes, not product or spec scope. If the dedicated browser-qa SKIPs again, the evaluator should reconcile J-14 from the on-disk QA evidence PNGs + the unit/API proofs + direct source reads (the standing iters-1–5 lesson).
- **Tractability after this iter:** J-16 (VCP) then J-12 (glossary incl. the VCP catalog entry) finish the new round; a clean J-14 leaves 14/16 Must-haves passing.
