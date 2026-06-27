# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-55 Execution Plan

Target journey: **J-112** — the new **Research → Regime × Phase × Factor** 3-way decile lab at
`/research/regime-phase-factor`. This is the **LAST unbuilt buildable Must-have** and the
**GOAL_ACHIEVED-candidate iteration**.

J-112 is the structural cousin of the iter-53 Regime Lab (J-110) and iter-54 Phase & Severity Lab (J-111),
but it follows the **J-77/J-82 ranked-combination pattern** (ranked, filterable, paginated table) instead of
the two-table layout. It is a read-only re-surfacing of already-stored canonical values — it **recomputes
nothing**. It UNIQUELY reads BOTH source paths in the same observation: (a) the run's stored
`ScannerRun.regime_score` (the J-80/J-110 path, verbatim) AND (b) the snapshot date's served 0-100 severity
from the `market_phase` causal timeline (the J-87/J-111 path, verbatim, joined by snapshot date) AND (c) the
selected factor's stored value. Mirror the iter-53/iter-54 code paths closely.

The spec is fully aligned with `docs/goal.md` (J-112, goal.md:2471-2488) and the blueprint's J-109..J-112
extension; the blueprint IA line + Data-Contract row are already registered for J-112. **No scope creep, no
contradiction with the goal detected.** No `blueprint.reapproval-requested` is filed (additive page under the
existing Research nav section — same call the COHERENCE-PASS iter-53/54 labs made).

## What to Build
- A ranked, filterable, paginated **combination table**: for a SELECTED factor, one row per
  `(regime-score decile × severity-score decile × factor decile)` triple, showing **n** and per
  `config.walk_forward.horizons` horizon the combination's **mean realized forward return + paired mean
  max-drawdown** (read verbatim from stored `forward_returns`: `realized_return` + the J-86 `max_drawdown`).
- The three dimensions are bucketed into **deciles** via the EXISTING generic `_deciles` /
  `_decile_member_slice` machinery and grouped by the triple key. Combinations below
  `config.walk_forward.min_sample` show **NA + n** (never dropped into a fabricated number).
- A NEW read-only endpoint, a NEW cached study `kind` on the EXISTING `event_study_cache` table, a NEW
  `regime-phase-factor` samples cohort `kind`, and a NEW frontend page + Research-hub tile.
- Controls: a **factor selector** (config-backed factor catalog), **filters** (regime/severity/factor decile,
  each default All), **column sort** (NA-last both directions), **pagination at 30 rows/page**, an
  **As-of vs All-history** FILTER toggle, and count-coherent **`N=` chip** drill-downs to Research Samples.

## Agents Required
- backend-data: yes -- engine (`compute_regime_phase_factor_study` + bounded observation builder + cache),
  API endpoint, samples cohort kind, and pytest (byte-identity, provenance, bounded-read, cache-schema,
  count-coherence, no-magic-numbers, db-guard-unchanged).
- frontend-ux: yes -- the new lazy sub-route page, hub tile, factor selector, ranked table with
  filter/sort/pagination, As-of toggle, `N=` chips, `fetchRegimePhaseFactor` + types, samples-link params.
- developer: yes -- this project uses a single `developer` agent that covers BOTH backend-data and
  frontend-ux work above, TDD, closely mirroring iter-53/iter-54.

Frontend Present: yes

## Files to Create/Modify
- `apps/backend/app/engine/research.py` -- add `compute_regime_phase_factor_study(session, *, factor, view,
  as_of, config)` + its cache wrapper + a bounded all-horizons observation builder
  (`_regime_phase_factor_members_by_horizon`) and the byte-identical single-horizon
  `_regime_phase_factor_observation_set` (the samples keystone). Each observation carries: verbatim
  `ScannerRun.regime_score` (reuse `_regime_meta_by_run`), the snapshot-date served severity off the
  `market_phase` timeline (reuse the iter-54 `_phase_severity_meta_by_run` / `_timeline_series` reader,
  joined by snapshot date), and the selected factor's stored value (reuse the Factor-Lab observation source).
  Reuse `_deciles`/`_decile_member_slice`/`_mean_or_none`/`_collapse_to_episodes`/`_dataset_version`/
  `_cache_asof_key`/`factor_catalog`. Add a `_REGIME_PHASE_FACTOR_SUBJECT` sentinel + a folded
  `_REGIME_PHASE_FACTOR_SCHEMA_TOKEN`, fold the market-phase stamp
  (`f"{_dataset_version}|{market_phase.SCHEMA_VERSION}"`, currently `s2`) into the cache key, AND fold the
  selected `factor` into the cache key (no cross-factor cache bleed). REUSE `event_study_cache` — add NO new
  `table=True` model. Source min-sample/horizons/decile-count/page-size from config — NO inline literal.
- `apps/backend/app/api/research.py` -- new `GET /api/research/regime-phase-factor` route (params `factor` +
  `view` Episodes/Pooled served+unit-proven + `as_of` FILTER-only; NO `horizon` selector — all-horizons
  paired shape), mirroring `/api/research/event-study`; import the new cohort kind; widen the samples
  view-validation set + `slice`/decile param docs so every emitted combination resolves (no 4xx).
- `apps/backend/app/engine/samples.py` -- new `KIND_REGIME_PHASE_FACTOR` + `_regime_phase_factor_samples`
  reproducing the exact `(regime-decile, severity-decile, factor-decile, horizon)` cohort from the SAME
  shared observation builder; wire into `compute_samples` + `ALL_KINDS`; widen vocabulary to accept every
  displayable triple. NO inline literal in this CALC_FILE.
- `apps/backend/app/config.py` -- add a named **page-size** value (e.g. a `regime_phase_factor` research
  sub-block or a shared research page-size field, default 30 per goal.md) so the 30-rows/page constant is
  config-sourced, not an inline literal; serve it in the endpoint payload for the frontend to read.
- `apps/backend/tests/test_regime_phase_factor.py` (new) -- byte-identity vs a reference over the
  single-horizon builder (≥2 distinct factors, both views, both scopes), read-verbatim provenance
  (regime_score == `ScannerRun`; severity == `market_phase._timeline_series`/`timeline_full` by snapshot
  date; factor == stored value), NA-honesty, bounded-read source guard (no unbounded `.all()`; ScannerResult
  ordered `(run_id, id)`), cache schema-token + market-phase-stamp + per-factor-key invalidation against an
  ALREADY-POPULATED old-schema row (real HIT, not fresh compute), samples count-coherence, invalid-selector
  4xx. Mirror `test_regime_lab.py` / `test_phase_severity_lab.py`.
- `apps/backend/tests/test_api_research.py` -- new endpoint shape + factor switch + view validity + as-of
  scoping + HTTP samples count-coherence + invalid-selector 4xx.
- `apps/backend/tests/test_samples.py` -- `regime-phase-factor` triple-cohort count-coherence.
- `apps/frontend/app/research/_labs.tsx` -- new `RegimePhaseFactorPage` (factor selector + ranked combination
  table + filters + client-side sort/pagination + As-of toggle + `N=` chips), reusing the iter-53/54 cell,
  sort-header (resolve by `aria-label`), and NA-last (J-82) predicate helpers. Pin `view=pooled` on the lab
  fetch AND every `N=` chip; expose NO Episodes/Pooled toggle. Page size is a named constant (read from the
  payload / config — NOT an inline literal scattered in the component).
- `apps/frontend/app/research/regime-phase-factor/page.tsx` (new) -- the lazy sub-route page.
- `apps/frontend/app/research/page.tsx` -- new **Regime × Phase × Factor** tile in the hub `LABS` list
  (pick an unused lucide icon, e.g. `Boxes`/`Grid3x3`), with a distinct one-line description.
- `apps/frontend/app/research/samples/page.tsx` -- `describeCohort` branch for the regime-phase-factor kind.
- `apps/frontend/lib/api.ts` -- `fetchRegimePhaseFactor` + response/row/factor-catalog types; send `as_of=`
  via the existing `withAsOf` helper (correct spelling — NOT `asof=`).
- `apps/frontend/lib/samples-link.ts` -- `RegimePhaseFactorCohortParams` + its `buildSamplesHref` branch.

## UI Evolution
- New user-facing capability: open a new **Regime × Phase × Factor** lab from the Research hub, pick any
  factor, and see how forward returns + downside risk (max-drawdown) differ across the three-way interaction
  of regime-score decile × severity-score decile × factor decile, at the 1/5/10/20/60-day horizons.
- New information displayed: per `(regime-decile, severity-decile, factor-decile)` combination — mean realized
  forward return + paired mean max-drawdown per horizon, sample size **n**, and survivorship-bias /
  descriptive-evidence labels (descriptive, never a forecast).
- New user actions: click the hub tile; pick a factor; filter by regime/severity/factor decile; sort any
  column (NA-last); paginate (30 rows/page); toggle As-of vs All-history; click an `N=` chip to open the
  exact triple cohort in Research Samples (new tab).
- UI surface changes: one new page `/research/regime-phase-factor` + one new hub tile. No other page changes.
- Navigation changes: one new tile under the EXISTING Research hub (no top-level nav-skeleton change).

## Visual Requirements
- Component patterns: reuse the existing research-lab `Card` shell + the J-77/J-82 ranked-combination table
  components, the Regime/Phase-Severity lab cell/sort-header helpers, the `Select` control for the factor +
  decile filters, and the existing `N=` chip + As-of toggle controls. Mirror the iter-53/54 lab look exactly.
- Layout: standard research sub-route — shared controls bar (page heading + factor selector + As-of toggle)
  above a single full-width, horizontally-scrollable (`overflow-x-auto`) ranked table with the prev/next
  pagination footer (wide table: n + 5 forward-return + 5 max-drawdown columns).
- Key visual effects: colour-graded return cells (existing return tokens) + `lib/mdd-color` for drawdown
  columns; hub tile uses the same hover/border treatment as the existing tiles.
- States to handle: loading (skeleton/dim, mirror siblings), empty/NA (thin / below-min-sample combinations
  and at/near-latest show NA + n — never fabricated), error ("could not load from the API; no figures shown"
  rather than synthesized data).

## Key Test Scenarios
- **J-112 (live, browser-qa)**: Research hub shows the Regime × Phase × Factor tile → `/research/regime-phase-factor`
  renders the factor selector + the ranked combination table (`(regime-decile, severity-decile, factor-decile)`
  rows, paired forward-return + max-drawdown columns per horizon + n); survivorship label present;
  **0 native `input[type=date]`** (J-18); NO Episodes/Pooled toggle (pinned Pooled).
- **J-112 factor switch**: changing the factor re-fetches and re-renders (the `factor` param is sent; rows change).
- **J-112 filter + paginate**: a regime/severity/factor decile filter narrows rows; pagination shows 30
  rows/page and the next-page control advances (pure view transform — no refetch).
- **J-112 sort**: toggling a column sort produces a BYTE-DISTINCT frame (md5 before ≠ after), NA-last; resolve
  the header by `aria-label`.
- **J-112 As-of**: toggling As-of (or arriving at a historical `?asof=`, mid-history e.g. 2024-06-01 — NOT
  the warm-up head) FILTERS the observation set so rendered n values DECREASE; confirm the param is `as_of=`;
  no second date control appears.
- **J-112 drill-down**: an `N=` chip opens `/research/samples` in a new tab for the exact triple+horizon
  cohort; Samples "Total observations" equals the clicked n (pinned `view=pooled`).
- **Required-still-passing live smoke**: J-06 (single-source), J-18 (0 native date inputs), J-07 (Risk-Off →
  0 Actionable), J-110 + J-111 (sibling labs still render real figures), J-80 (Stocks header regime), J-87
  (Dashboard Market-Phase panel renders the same severity this lab joins on).
- **Unit/integration (pytest)**: `compute_regime_phase_factor_study` byte-identity (≥2 factors, both views,
  both scopes); provenance verbatim (regime/severity/factor); bounded-read source guard; cache schema-token +
  market-phase-stamp + per-factor invalidation on an already-populated old-schema row; samples count-coherence
  (`total == published n`, no 4xx); `test_db.py` expected-tables guard **UNCHANGED**; `test_no_magic_numbers`
  **green**. Launch the FULL suite **nohup-async**; GOAL_ACHIEVED candidacy gates on its flushed
  `0 failed, EXIT 0` line (re-confirm the known `test_api_data` async-backfill flake green in isolation).
- **Error cases**: thin/below-min-sample combinations + at/near-latest → NA + n (never fabricated); unknown/
  empty factor or out-of-range decile → honest empty state; malformed cohort param → 4xx, but every emitted
  combination resolves; a snapshot date with no `market_phase` value (warm-up head) → honest unclassified/NA,
  never a fabricated severity.

## Critical Constraints & Lessons (heed — these are where this session regressed before)
- **OOM-sensitive read path (iter-46/47/48)**: read the observation pool over the J-105 streamed/
  column-projected BOUNDED path — NO unbounded `select(...).all()` over `ForwardReturn`/`ScannerResult`;
  order ScannerResult by `(run_id, id)` (rides `ix_scanner_results_run_id`; bare `id` spilled "disk is full").
  Probe the lab **cold** (a cache HIT masks a cold-miss OOM). Reuse the shared sibling observation builder —
  one membership pass. The 3-way grouping can emit ~10×10×10 combinations/factor — most low-sample; rely on
  config min-sample NA + pagination.
- **NEVER run the full pytest suite concurrently with the heavy-lab browser probes** (RAM pressure caused the
  iter-47 OOM). Suite is nohup-async; run heavy live probes one fetch at a time on a freshly-restarted,
  warmed backend (`scripts/dev.sh`: backend `:8255`, frontend `:3255`).
- **Live render evidence (iter-36/38/39/40/42/52)**: keep BOTH servers up THROUGH the dedicated
  browser-qa-agent step; **plan the Playwright fallback UP FRONT** (Chrome MCP CDP has emptied the evidence
  dir before); `md5sum` the evidence dir FIRST and reject skeleton / "Backend unavailable" / byte-identical
  before/after frames.
- **No new table / no magic numbers (iter-12/20/21)**: REUSE `event_study_cache` (db-guard UNCHANGED);
  write NO float/int literal into `research.py`/`samples.py` (use the J-21 boolean-sentinel idiom for a
  sort-key sentinel); factor vocabulary from `factor_catalog(cfg)` — no hardcoded list.
- **Cache staleness (iter-38/39/44)**: fold the schema token AND the market-phase `SCHEMA_VERSION`/dataset
  stamp AND the selected `factor` into the cache key; unit-test the MISS against an ALREADY-POPULATED
  old-schema row (a real HIT), not a fresh compute.
- **Pin Pooled (iter-53)**: whole-cross-section labs degenerate under the J-63 Episodes collapse — pin
  `view=pooled` on the lab fetch AND every `N=` chip; expose NO Episodes/Pooled toggle.
- **Full pipeline MUST complete THROUGH the AUDIT step and the audit handoff MUST be written** — it was
  MISSING in iter-53 AND iter-54; the GOAL_ACHIEVED candidacy depends on the audit handoff existing this iter.
- Dev handoff at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-55-dev.md`.

## Out of Scope (excluded — flag if attempted)
- Any change to HOW regime score, severity, forward return, max-drawdown, or factor values are computed/stored
  (all read verbatim from canonical sources).
- Any new `table=True` model / new stored column / DB migration; the J-85 destructive snapshot rebuild
  (~11h — do NOT trigger); any live data fetch.
- J-22/J-23/J-24 (data-walled, non-vetoing — leave honestly blocked-NA).
- Any top-level nav-skeleton change; re-styling/restructuring the sibling labs (stay byte-identical).
