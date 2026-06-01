# Goal Iteration 2 — Return attribution / contribution analysis (J-19)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever
- **Iteration:** 2
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-19
- **Required-still-passing journeys:** J-09, J-10, J-14, J-18, J-13, J-01
- **Opportunistic re-verify (no code — convert iter-0 partials on healthy browser tooling):** J-02, J-06, J-11, J-15, J-16
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **Attribution is read-only.** The forward-return attribution slices (per-stock contribution, by-sector, by-rank-band, distribution/hit-rate) MUST be derived from the stored per-observation forward returns; the API and frontend MUST NOT recompute returns to build them. *(extends No recompute in the read path)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. *(extends Single source of truth)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Honest forward-test for partial windows.** The per-date forward-test scorecard … MUST show NA/partial for horizons or cohorts lacking enough samples and MUST show sample size — never fabricate or extrapolate a return to fill a gap. *(extends No fabricated data)*
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. *(critical)*

## GOAL

A user diagnosing a weak forward-test number can, on **System Health** (aggregate) and **Backtest**
(single date), read four attribution layers — **per-stock top contributors & detractors**, a
**by-sector** breakdown, a **by-rank-band** breakdown (1–10 / 11–50 / 51+), and a
**distribution & hit-rate** panel (median, % positive, dispersion alongside the mean) — each with its
sample size `n`, so a weak mean is explainable (concentration, outliers, ranking efficacy) rather than
taken at face value.

## BACKGROUND

This is the iter-1 evaluator's explicitly recommended next step (`iter-1/eval.md` → "Proceed to J-19 …
at full depth"). J-17 (Data Manager) and J-19 (attribution) are the only two `failing` journeys left;
J-19 is chosen because Backtest now reads the clean single global as-of control (J-18 resolved iter-1),
so the per-date attribution surface is unblocked.

The work is well-conditioned: `app.engine.forward_testing` **already** builds the exact
per-observation list this journey needs. `compute_forward_aggregates` (aggregate, at one horizon) and
`compute_run_scorecard` (per-date, per horizon) each construct a `stock_obs` list of
`{ticker, return, bucket, setup, sector, rank, regime}` rows by joining stored `forward_returns` to
stored `scanner_results`/`scanner_runs` **verbatim**. The four attribution slices are derived **from
that same list** — no second formula, no new bar access — which is exactly how the critical anti-goal
**"Attribution is read-only"** is satisfied. The existing `_group_means(...)` helper already produces
mean+`n` per stored group value; by-sector and by-rank-band reuse it.

Depth is **full** (not lean): new registered Data-Contract value spanning two pages, backend derivation
+ new config keys + new unit tests, and a critical-family anti-goal (Attribution is read-only / No
recompute in the read path). The iter-1 evaluator concurred.

**Lessons applied** (`lessons.md`): both lessons are about the as-of date control (iter-0: confirm
date-control claims in source; iter-1: the global as-of lives in an in-memory provider, drive date
journeys via in-app nav not hard reload). They bear on the **regression set** here (J-13/J-18/J-14 must
stay green and the page reads the global `useAsOf()` switcher) — so the required-still-passing checks on
`/backtest` must use in-app navigation, not a hard reload, and must confirm the page still holds no
independent date state after the J-19 additions.

## IN SCOPE

### Backend

- [ ] **config.yaml** — add a `walk_forward.attribution` block (no magic numbers): the **rank-band
      edges** (e.g. bands `1–10`, `11–50`, `51+`, each as `{label, min, max}` with `max: null` for the
      open top band) and `top_contributors_k` (how many contributors / detractors to list, e.g. 5).
      No band edge or list size literal may live in calculation code. Add the matching typed accessor
      in `app/config.py` (mirror the existing `walk_forward.control_group` typing).
- [ ] **`app/engine/forward_testing.py`** — add ONE shared attribution helper (e.g.
      `_attribution_slices(stock_obs, cfg)`) that takes the **already-built** per-observation
      `stock_obs` list and returns the four slices, recomputing no return:
  - **`per_stock`** — `contributors` (top-`k`) and `detractors` (bottom-`k`) named tickers. Aggregate
    a ticker's stored realized returns over the same observations (mean realized return + `n` per
    ticker), sort descending for contributors / ascending for detractors, take `top_contributors_k`
    each. Each row: `{ticker, mean_return, n, sector}`.
  - **`by_sector`** — reuse `_group_means(stock_obs, "sector", "sector", <order>, pad=False)`.
  - **`by_rank_band`** — map each observation's stored `rank` to its config band label, then
    `_group_means(..., "rank_band", "rank_band", <band order>, pad=True)` so every band shows (n=0 →
    mean None). Observations with `rank is None` are excluded (not bucketed into a band).
  - **`distribution`** — `{mean_return, median, pct_positive, dispersion, n}` over the same
    `[o["return"] for o in stock_obs]` list (`pct_positive` = share of observations with return > 0;
    `dispersion` = standard deviation; `median` via `statistics.median`). `n < 2` → `dispersion: null`;
    empty → all-None with `n: 0`.
  - Call it from **`compute_forward_aggregates`** (pass the full `stock_obs`) → add an `attribution`
    key to that payload (so it is keyed to the requested `horizon`).
  - Call it from **`compute_run_scorecard`** for each horizon (pass that horizon's `stock_obs`) → add
    an `attribution` key to each `by_horizon` entry.
- [ ] The helper MUST be **consistent with the existing aggregate mean** (same underlying
      observations): the by-sector / by-rank-band row `n`s sum to `overall.n`, and the distribution
      `mean_return` equals the existing `overall.mean_return` for the aggregate. Assert this in tests.

### Frontend

- [ ] **`apps/frontend/lib/api.ts`** — extend `SystemHealthResponse` and the per-horizon scorecard type
      inside `BacktestResponse` with the new `attribution` object; add the supporting row types
      (`PerStockRow`, by-sector/by-rank-band reuse the existing `ForwardGroupRow`, a `Distribution`
      type). No fetcher signature change (the data rides the existing payloads).
- [ ] **`apps/frontend/app/system-health/page.tsx`** — add a **"Return attribution"** section (below
      the existing panels) with four panels for the currently-selected horizon, reusing the existing
      `Return` / `fmtPct` / `returnClass` / `BreakdownPanel` primitives and palette tokens:
      per-stock contributors & detractors (named tickers + realized return + `n`); by-sector; by-rank
      band; distribution & hit-rate (mean / median / % positive / dispersion, each with `n`).
- [ ] **`apps/frontend/app/backtest/page.tsx`** — add the same four-panel attribution section for the
      resolved as-of date, for a **selected horizon**. Add a small horizon selector that picks which
      `by_horizon[*].attribution` block to display from data the page already has (NO refetch, NO new
      fetch param). The page MUST continue to hold **no independent date state** — it still reads only
      the global `useAsOf()` switcher (preserve the iter-1 J-18 consolidation; the horizon selector is
      not a date control).
- [ ] Honest empty/NA states for every new panel: a slice with `n=0` shows "—" (NA), figures with
      `n < min_sample` carry the existing `⚠` low-sample treatment, and a date/horizon with no elapsed
      forward window shows the existing empty-state copy — never a fabricated number.

### New user-facing capability

On `/system-health` and `/backtest` the user can read, for a chosen horizon, **which individual tickers
drove or dragged** the cohort, **which sectors** and **which rank bands** carried the return, and the
return's **shape** (median, hit-rate, dispersion) next to the mean — turning a single headline number
into a diagnosable breakdown.

### New information displayed

Per-stock top contributors & detractors (ticker + realized return + n + sector); by-sector mean
forward return (+ n); by-rank-band mean forward return for the config bands 1–10 / 11–50 / 51+ (+ n);
and a distribution panel: mean, median, % positive (hit rate), dispersion, with n.

### New user actions

A horizon selector on `/backtest` to choose which horizon's per-date attribution to view (System
Health already has its horizon selector; the new aggregate attribution rides it). No other new control.

### UI surface changes

A new "Return attribution" section (four panels) appended to `/system-health` and to `/backtest`. No
new page, no nav change.

### Product surface delta

The forward-test evidence stops being a set of opaque means: every weak (or strong) number can be
opened up to see concentration (one ticker?), sector beta vs selection (by-sector / by-rank-band), and
distribution honesty (median vs mean, hit-rate, dispersion) — reinforcing the product's skeptical,
evidence-driven mood.

### Blueprint conformance

Both surfaces already exist in the Information Architecture under their canonical homes — **System
Health** (`/system-health`) and **Backtest** (`/backtest`) — both already present in the nav skeleton.
**No nav-skeleton change → no re-approval requested.** The blueprint's existing J-19 Data-Contract row
(currently `⛔ NOT BUILT — target`) is refined in place (additive) to the concrete names below.

### Data-contract additions

No NEW canonical value and **no second computation or endpoint** for any existing value. The J-19
attribution slices are a **read-only derivation** of the already-registered per-observation
`forward_returns` ⋈ `scanner_results` data, computed by the **same** `app.engine.forward_testing` code
that builds `compute_forward_aggregates` / `compute_run_scorecard` (one shared helper over the existing
`stock_obs`), and served on the **existing** endpoints `GET /api/system-health` (aggregate, keyed to
the selected horizon) and `GET /api/backtest` (per-date, inside each `by_horizon` entry). New config
keys: `walk_forward.attribution.{rank_bands, top_contributors_k}`. Registered as a refinement of the
existing J-19 blueprint row.

## OUT OF SCOPE

- **J-17 Data Manager** (`/data`, `/api/data`, fetch/backfill job) — the other failing journey; a
  separate, larger iteration. Do not start it here.
- Any change to how a forward return, score, bucket, setup, or regime is **computed** — attribution
  only *reads and groups* the stored per-observation returns.
- Any new endpoint, any new `?param` on `/api/system-health` beyond the existing `horizon`, and any
  refetch on `/backtest` for the horizon selector (use data already in the payload).
- Re-pointing or persisting the as-of date (the iter-1 lesson: the global as-of is an in-memory
  provider by design — do not add URL/localStorage persistence here).
- Tuning scoring weights / thresholds (journeys assert structural properties, not exact numbers).

## DEFINITION OF DONE

- [ ] **J-19** passes via browser-qa-agent: on `/system-health` and `/backtest` all four attribution
      layers render numbers with `n`; the per-stock list names individual tickers with their realized
      return; low-sample / empty slices show `n` and NA honestly (no fabricated number).
- [ ] Required-still-passing journeys remain green: **J-09, J-10** (System Health aggregates/control
      group unchanged), **J-14, J-18, J-13** (Backtest scorecard + single global date control intact),
      **J-01**.
- [ ] No anti-goal violation introduced — in particular **Attribution is read-only** (slices derived
      from stored per-observation returns; no recomputed return in engine/API/view) and **No magic
      numbers** (rank-band edges + list size from config).
- [ ] Unit tests pass; no regressions (backend pytest suite stays green — was 248/0 at iter-1).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever-iter-2-dev.md`.

## TESTING REQUIREMENTS

- **Browser (by ID):**
  - **J-19** (primary) — `/system-health`: read the four attribution panels at a horizon with samples;
    confirm named tickers + realized returns, by-sector and by-rank-band numbers with n, and the
    distribution panel (mean/median/% positive/dispersion). `/backtest`: pick a historical date with
    ≥60 post-snapshot bars, read the same four panels for a selected horizon; then pick a recent date
    and confirm low/empty horizons show NA + n, not fabricated numbers.
  - **Regression:** J-09, J-10 (System Health existing panels + control group still correct), J-14 +
    J-18 + J-13 (Backtest scorecard unchanged; the single global as-of switcher still drives the page;
    **drive date changes via in-app nav, not a hard reload** — iter-1 lesson), J-01.
  - **Opportunistic re-verify (no code):** J-02, J-06, J-11, J-15, J-16 — the iter-0 `partial`s the
    iter-1 evaluator flagged as likely convertible on healthy browser tooling. Capture fresh evidence;
    the evaluator decides conversion.
- **Unit/integration (backend):** add to the existing `test_forward_testing.py` /
  `test_api_system_health.py` / `test_api_backtest.py` / `test_backtest_scorecard.py`:
  - **Read-only / consistency:** by-sector and by-rank-band row `n`s sum to `overall.n`; the
    distribution `mean_return` equals the aggregate `overall.mean_return`; the slices use the same
    observation set as the existing aggregate (no extra `forward_returns`/bars query introduced).
  - **Config-driven bands (no magic numbers):** rank-band labels/edges come from
    `walk_forward.attribution.rank_bands`; changing config changes the bands; `top_contributors_k`
    controls the list length.
  - **No-lookahead inheritance:** attribution reads only stored `forward_returns` (date > D) and
    `scanner_results` — it accesses no price bar directly, so the existing no-lookahead guarantee is
    unaffected (assert no new bar access / same rows as the aggregate).
- **Error / honesty cases:** empty `stock_obs` → all slices NA with `n=0` (no fabricated 0%); a
  single-observation slice → `dispersion: null` (no spurious 0 stdev); a rank-band with no members →
  padded row with `mean_return: None, n: 0`; per-date attribution at a horizon with no elapsed window
  → NA, not a number.

## NOTES

- **Why no new endpoint:** `GET /api/system-health` returns `compute_forward_aggregates(...)` verbatim
  and `GET /api/backtest` returns `compute_run_scorecard(...)` (+ `is_latest`). Attaching `attribution`
  to those engine payloads surfaces it on both pages with zero new API surface — exactly the
  blueprint's J-19 row ("served by `GET /api/backtest` and `GET /api/system-health`").
- **Why the read-only seam is safe:** the four slices are pure functions of the existing per-observation
  `stock_obs` rows (which themselves are stored `forward_returns` joined to stored `scanner_results`
  read verbatim). No realized return is recomputed; consistency with the aggregate mean is asserted in
  tests. This is the same pattern `_control_groups` / `_group_means` already use.
- **Per-stock contribution definition:** list each ticker's mean realized return over the same stored
  observations with its `n`; contributors = highest, detractors = lowest. This is the honest reading of
  "which tickers drove or dragged the cohort" and stays derived-from-stored (no per-request return math).
- Reference: iter-1 evaluator recommendation (`runs/goal-session-i_can_see_the_wealthy_future_forever/iter-1/eval.md`),
  blueprint J-19 Data-Contract row + coherence invariant #9 ("Attribution is read-only").
