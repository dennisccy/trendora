# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-50 Execution Plan

Restructure `/research/factor-lab` (J-107) into an **all-factors table** — one row per config-catalog
factor (family, Rank-IC value+N, downside risk-adjusted at the selected horizon), client-side sortable
NA-last, each row click-to-expand to its D1..D10 decile sort — superseding the single-factor dropdown.
Every value byte-identical to the per-factor lab, served from a derived-once cached, bounded read path.
This is the **last unbuilt buildable Must-have**; it is a GOAL_ACHIEVED-candidate iteration.

Aligns with goal.md:2400/2407/2418. No scope drift; no new value/endpoint/table/date-state. The
existing Factor-Lab Data Contract row was annotated additively in `blueprint.md` (no re-approval filed).

## What to Build

- **Backend — all-factors aggregate on the EXISTING `GET /api/research/factor-lab`.** Add an additive
  flag (e.g. `view=all` / `all=true`) — **NO new endpoint**. When set, return a `factors_table` block:
  one entry per catalog factor `{key, label, family, rank_ic: {value, n}, risk_adjusted, deciles: [...]}`
  at the resolved horizon, plus the resolved `horizon`/`horizons`/`default_horizon`/`min_sample`/
  `deciles_count`/`asof_date`/caveats. Each factor's `deciles` is the existing `FactorDecileRow` shape
  (D1..D10 `mean_return`, downside `risk_adjusted`, `n`, `low_sample`, `factor_min/max`).
- **One shared pool, one computation path (byte-identity is load-bearing).** Build the observation pool
  ONCE — a single streamed/column-projected read carrying every catalog factor's value per observation —
  then for EACH factor derive its deciles/rank-IC/risk-adjusted from that shared pool using the SAME
  `_deciles` / `_rank_ic` / `_risk_adjusted` builders and the SAME `ordered` sort key
  `(o["factor"], o["ticker"], o["run_id"])` that `compute_factor_lab` uses. Result MUST equal
  `compute_factor_lab(session, factor, horizon, cfg, as_of=cutoff)` per factor. (See Risks #1.)
- **Bounded read (J-105).** No unbounded `select(...).all()` in the all-factors builder — stream
  column-projected rows in `config.research.read_batch_size` batches via `yield_per`; order any
  `ScannerResult`/`ScannerRun` read by `(run_id, id)` (NOT bare `id`). Fire ONE heavy read, not N.
- **Derived-once cache.** Serve from the existing `EventStudyCache` + `_dataset_version` idiom via a new
  `subject`/`view` namespace (e.g. `subject="__all_factors__"`, `view="factors_table"`), keyed on
  `dataset_version` + `asof_key` + `horizon` (reuse `_cache_asof_key`, the `event_study_cached` HIT/
  MISS/prune pattern). **Reuse `EventStudyCache` — add NO `table=True` model** (test_db.py guard stays
  unchanged). `as_of` is a pure observation-set FILTER folded into the cache key.
- **Keep `_regime_effectiveness` computing** in `compute_factor_lab` (byte-identical) — only the
  frontend retires the per-regime table from this view; the backend per-factor output is untouched.
- **Frontend — replace `FactorSelector` dropdown with the all-factors table** in `FactorLabPage`
  (`apps/frontend/app/research/_labs.tsx`): rows = catalog factors (family, Rank-IC value+N, risk-
  adjusted at horizon); HorizonSelector + As-of mode toggle REMAIN (single global as-of, no 2nd date
  state). Client-side sortable NA-last (mirror the `SortHeader`/`comparatorFor` pattern from
  `app/sectors/page.tsx` / `app/stocks/page.tsx`; resolve headers by `aria-label`; NA predicate =
  `low_sample || n===0 || value===null`). Each row click-to-expand via the keyboard-accessible
  `aria-expanded` pattern Sectors uses (the `expanded: Set` + `onToggle` + separate panel `<tr>`),
  revealing the existing `DecileTable` (hidden by default). Each decile `N=` chip keeps its existing
  `SampleLink` (`cohort={{ kind:"factor", factor, horizon, slice:"decile", decile }}`, new tab).
  **Remove `RegimeEffectivenessTable` / `data.by_regime`** from this view. Preserve honest states
  (WarmingState / ResearchError / honest empty / survivorship+descriptive caveats).
- **API client + types.** Extend `fetchFactorLab` to send the all-factors flag and add the
  `factors_table` type to `FactorLabResponse` in `apps/frontend/lib/api.ts`.

## Agents Required

- backend-data (developer): yes -- all-factors aggregate over the shared streamed pool, derived-once
  `EventStudyCache` namespace, byte-identity + cache + bounded-read tests.
- frontend-ux (developer): yes -- replace dropdown with sortable NA-last expandable all-factors table;
  remove the per-regime table; keep horizon + as-of controls and decile N= drill-downs.

(Single `developer` agent handles both backend and frontend per the framework.)

Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/engine/research.py` -- shared all-factors observation pool (streamed, `(run_id,id)`-
  ordered) + `factor_lab_all_cached` (reuse `EventStudyCache` namespace, `_dataset_version`/`asof_key`
  HIT/MISS/prune); reuse `_deciles`/`_rank_ic`/`_risk_adjusted`; NO second derivation path.
- `apps/backend/app/api/research.py` -- additive `view=all`/`all` param on `GET /research/factor-lab`;
  same validation (unknown factor/horizon 422, no data 503, shared `resolved_date` for `as_of`).
- `apps/backend/tests/test_api_research.py` (or `test_research.py`) -- deep-equality byte-identity test
  (all-factors per factor == `compute_factor_lab` per factor across all-history + as-of + zero-N/low-
  sample); cache HIT==MISS==fresh + stale-`dataset_version` pruned (against a real populated row);
  bounded-read assertion (no unbounded `.all()`; `(run_id,id)` order); error cases.
- `apps/frontend/app/research/_labs.tsx` -- `FactorLabPage`: all-factors sortable expandable table;
  drop `FactorSelector`; remove `RegimeEffectivenessTable` from this view; keep HorizonSelector +
  AnalysisModeToggle; reuse `DecileTable` + decile `SampleLink`.
- `apps/frontend/lib/api.ts` -- `factors_table` type + `fetchFactorLab` all-factors flag.
- `docs/handoffs/goal-...-iter-50-dev.md` -- dev handoff.

## UI Evolution

- New user-facing capability: see EVERY factor at once on `/research/factor-lab` — a sortable comparison
  of each factor's predictive edge (Rank-IC + N) and downside risk-adjusted figure at the chosen horizon
  — and expand any factor in place to inspect its full D1..D10 decile sort (was one-at-a-time dropdown).
- New information displayed: one-row-per-factor family + Rank-IC (value + N) + risk-adjusted across the
  whole config catalog at the selected horizon (re-presented existing canonical values, not new values).
- New user actions: click a column header to sort the table (NA-last); click a factor row/expander to
  expand/collapse its decile sort; click a decile `N=` chip to open that cohort in Research Samples.
- UI surface changes: `/research/factor-lab` only — dropdown replaced by the all-factors expandable
  table; the per-regime effectiveness table removed from this view. No other page changes.
- Navigation changes: none (existing Research → Factor Lab home, hub-linked, <=2 clicks).

## Visual Requirements

- Component patterns: reuse the existing `Card` lab shell, `ResearchControls`/`ResearchCaveat`, the
  `SortHeader` sortable-header pattern (sectors/stocks), the Sectors `aria-expanded` expandable-row
  pattern, the existing `DecileTable` + `SampleLink` chips. No new component library primitives.
- Layout: the existing Research lab page layout (controls bar + caveat + the table); decile detail
  renders in a full-width expanded panel `<tr>` beneath its factor row.
- Key visual effects: match the established research-table styling (border/surface tokens, num font,
  `returnClass` colour grading, accent active states) — no ad-hoc styles.
- States to handle: warming (`WarmingState`), load error (`ResearchError`), honest empty observation set
  (no fabricated row), low-sample/zero-N cells render NA + n; loading skeleton (`LabSkeleton`).

## Test Strategy

- **Backend unit/integration (load-bearing for GOAL_ACHIEVED):**
  - Deep-equality byte-identity: all-factors aggregate per factor == `compute_factor_lab` per factor,
    across all-history + as-of + zero-N/low-sample cohorts (assert exact dict equality, incl. deciles).
  - Cache correctness: a seeded already-populated `EventStudyCache` all-factors row returns byte-
    identical to a fresh compute (HIT==MISS); a stale-`dataset_version` row is a MISS and is pruned.
  - Bounded read: assert NO unbounded `select(...).all()` in the all-factors builder; ScannerResult/
    ScannerRun reads ordered by `(run_id, id)`.
  - Guards: `test_db.py::test_create_all_produces_expected_tables` UNCHANGED (no new table);
    `test_no_magic_numbers` green (catalog, `walk_forward.horizons`, decile count, `read_batch_size`
    all config-sourced).
  - Errors: unknown factor/horizon 422; no price data 503; `as_of` before-history/future/unparseable
    400/422 via the shared resolver; zero-N/low-sample → NA + n; empty set → honest empty.
  - Run the FULL suite **nohup-async via the pump**; gate candidacy on the flushed `0 failed, EXIT 0`
    line. Re-run isolated `test_warmup.py` / `test_watchlist_persistence.py` /
    `test_data_manager_jobs_pipeline.py` before attributing a suite failure (known slow-boot flakes).
- **Frontend:** `tsc --noEmit` exit 0; the lib unit-test pattern for any new pure helper.
- **Browser QA (live, on a freshly-restarted, warmed, single-fetch-at-a-time backend; Playwright
  fallback PRE-PLANNED — Chrome MCP CDP has emptied the evidence dir on this host):**
  - J-107: all-factors table renders (rows = catalog factors; columns = family / Rank-IC value+N /
    risk-adjusted at horizon); column sort reorders NA-last — capture TWO byte-DISTINCT frames (resolve
    headers by `aria-label`); a factor row expands to its decile table and collapses (byte-distinct
    frames); a decile `N=` chip opens Research Samples in a NEW TAB with total == published N (count-
    coherent); confirm the per-regime effectiveness table is ABSENT.
  - Smoke re-verify required-still-passing on the SAME quiet backend: J-25 (single-factor decile/rank-IC
    == the all-factors row, byte-identical), J-26, J-29, J-77, J-91, J-103, J-104; CRITICAL J-06, J-18
    (0 native date inputs), J-07 (Risk-Off → 0 Actionable); J-106, J-108.
  - `md5sum` the evidence dir FIRST; reject blank/skeleton/"Backend unavailable"/byte-identical frames.
  - Allow ~50-120s for the Factor-Lab cold compute (~598K rows) before the first cache hit.
  - Cheap carry-over hygiene if reachable: J-106 NA-last at a short-history as-of (UT-05 was skipped);
    a distinguishable J-108 LAN-IP Ready frame (UT-08 was a localhost byte-dup).

## Risks / Watch-outs

1. **BYTE-IDENTITY (highest risk).** Do NOT reuse `_combination_observations`' "drop the observation if
   ANY referenced factor is null" logic — that would change each factor's N/deciles and break byte-
   identity vs `compute_factor_lab`. The shared pool MUST keep per-factor values with NULL allowed; each
   factor's derivation filters to ITS OWN non-null subset and sorts with the exact
   `(factor, ticker, run_id)` key. Prove with the deep-equality test before any browser work.
2. **Cold-miss OOM.** The all-factors view is one heavy read over ~598K `scanner_results` / ~3.08M
   `forward_returns`. Stream with `yield_per`; order `ScannerResult`/`ScannerRun` by `(run_id, id)` (bare
   `id` forces a temp B-tree → `500 disk is full` on this ~93%-full host). Prove the bounded fix on the
   UNCACHED path probed COLD — a cache hit masks the OOM. Grep EVERY `.all()` in the touched builder.
3. **No second computation path / no new value.** The all-factors block re-presents existing
   `compute_factor_lab` outputs only — no new served field, no new endpoint, no new `table=True` model,
   no second rank-IC/decile/risk-adjusted derivation. Coherence-auditor will hard-fail a contract value
   recomputed via a new path.
4. **As-of is a MODE, not a 2nd date state (J-18).** The table reads the single global as-of via the
   existing `useResearchControls`; the All-history/As-of toggle stays a mode. Verify As-of IN THE
   BROWSER (toggle → N values change); the endpoint param is `as_of` (underscore).
5. **Resource discipline.** NEVER run the full pytest suite concurrently with the heavy-lab browser
   probes (RAM → OOM/contention). Fetch one heavy lab at a time on a freshly-restarted, warmed backend.
6. **Sort + expand regression hygiene.** Resolve sort buttons by `aria-label` (labels live in nested
   `<span>`); a differential leg needs TWO byte-DISTINCT frames. Confirm the comparator/onSort/sorted-
   memo path is intentional in the diff before calling a sort change a regression.

## Out of Scope (excluded)

- `/research/factor-combination` (J-26) — untouched.
- Any change to `compute_factor_lab`'s per-factor output shape, `_regime_effectiveness` computation, or
  any canonical decile/rank-IC/risk-adjusted value (must stay byte-identical).
- Any new `table=True` model, new endpoint, new served field on a scored payload, or second date state.
- Re-running the J-85 `kind:rebuild` (~11h destructive — data is correct).
- J-22/J-23/J-24 (data-walled, non-halting — stay honestly blocked-NA, non-vetoing).
