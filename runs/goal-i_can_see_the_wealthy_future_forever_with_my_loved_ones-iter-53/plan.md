# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-53 Execution Plan

Target journey: **J-110** — new **Research → Regime Lab** at `/research/regime-lab`. Descriptive,
survivorship-biased cross-sectional evidence of how realized forward returns + paired max-drawdowns relate
to the market regime, grouped (a) by the six canonical regime labels and (b) by deciles of the 0–100
regime score, at every configured horizon, with rank-IC and count-coherent `N=` drill-downs.

This is the **direct structural twin of iter-52 / J-109 (Factor Lab all-horizon)** — mirror that work,
swapping the grouping key from "factor decile" to "regime label / regime-score decile". Read-only
re-surfacing of already-stored canonical values; **recomputes nothing**.

## What to Build
- Backend engine `research:compute_regime_lab(session, *, view, as_of, config)` in `apps/backend/app/engine/research.py`:
  pool the SAME cross-sectional per-observation forward returns the Factor Lab / event study already build
  (stock × snapshot), each observation tagged with its run's stored `regime_score` + `regime_label` read
  VERBATIM from the immutable `ScannerRun` (J-80) joined to the append-only `forward_returns`
  (`realized_return` + J-86 `max_drawdown`, read verbatim). Reuse `_regime_by_run_projected` for the
  per-run regime read.
- Group two ways (mirror Factor Lab): (a) the six canonical regime labels; (b) deciles D1…D10 of the
  regime score via the EXISTING generic `_deciles` / `_decile_member_slice`. Per `config.walk_forward.horizons`
  horizon and per bucket: mean realized forward return, paired mean max-drawdown (`_group_mdd`/`mean_max_drawdown`
  NA convention), n; decile view additionally carries the score range and the `_rank_ic` of regime score vs
  forward return per horizon.
- Bounded read: build the observation pool over the J-105 streamed / column-projected path — NO unbounded
  `select(...).all()` over `ForwardReturn` / `ScannerResult`; ScannerResult reads ordered **`(run_id, id)`**
  (rides `ix_scanner_results_run_id`; bare `id` order spilled `disk is full` on this host).
- Cache: NEW study `kind` on the EXISTING `EventStudyCache` + `_dataset_version` idiom (new `regime_lab_cached`
  helper mirroring `factor_lab_all_cached`), with a **folded schema token** in the dataset-version slot
  (new `_REGIME_LAB_SCHEMA_TOKEN`, e.g. `"regimelab-v1"`), so any old-schema cache row is a guaranteed MISS +
  prune. REUSE the `event_study_cache` table — add **NO** `table=True` model (keeps `test_db.py` guard unchanged).
- API: NEW read-only `GET /api/research/regime-lab` in `apps/backend/app/api/research.py` with `view`
  (Episodes/Pooled, J-63) + `as_of` (J-32 FILTER-only) params, mirroring `/api/research/event-study`. No
  `horizon` selector (all-horizons paired shape). 503-no-data behaviour like siblings.
- Samples: NEW `regime-lab` cohort `kind` in `apps/backend/app/engine/samples.py` (`KIND_REGIME_LAB`,
  add to `ALL_KINDS`; new `_regime_lab_samples` mirroring `_regime_setup_pattern_samples`) reproducing the
  exact `(regime label | regime-score decile, horizon)` cohort from the SAME shared observation builder;
  add the needed selectors to the `/research/samples` handler and widen validation vocabulary so EVERY
  displayable bucket resolves without a 4xx.
- All thresholds from config: `config.walk_forward.min_sample` (NA threshold), decile count + horizons from
  config — **NO** numeric literal in `research.py` CALC code (`test_no_magic_numbers` blanket-forbids inline
  literals, even a `0.0` sentinel; use the J-21 boolean-sentinel idiom for any NA-last sort key).
- Frontend page `apps/frontend/app/research/regime-lab/page.tsx` (+ a `RegimeLabPage` in `app/research/_labs.tsx`)
  rendering the by-label table (six rows) and the regime-score decile table (D1…D10): paired
  (forward-return, max-drawdown) columns per horizon, n, score range (decile), rank-IC; colour-graded
  (return tokens + `lib/mdd-color`). Columns client-side sortable NA-last both directions (J-48 view
  transform; recomputes/refetches nothing; J-82 NA-last predicate). As-of vs All-history toggle (J-32) that
  only FILTERS (single global as-of, J-18 — no second date control). `N=` chip on each cell opens
  `/research/samples` in a NEW tab (J-65) for the exact cohort, carrying `?asof` in the href (J-50).
  Survivorship-bias / descriptive-evidence labels + honest empty/NA state for thin / at-latest buckets.
- New **Regime Lab** tile in the `LABS` array of `apps/frontend/app/research/page.tsx` (deep-linkable, ≤2
  clicks from nav). `fetchRegimeLab` (+ types) in `apps/frontend/lib/api.ts` calling `GET /api/research/regime-lab`
  (send `as_of=` via the existing `withAsOf` helper — correct param spelling, NOT `asof=`).

## Agents Required
- developer: yes -- implement all backend + frontend changes below with TDD (this framework's single
  developer agent handles both layers).
- backend-data: yes -- engine `compute_regime_lab` + bounded observation builder, cache schema-token helper,
  `GET /api/research/regime-lab`, `regime-lab` samples cohort kind + validation; full pytest gate.
- frontend-ux: yes -- `/research/regime-lab` page + hub tile, `fetchRegimeLab` + types, sort/As-of/`N=`
  controls, honest states.

## Frontend Present
yes

## Files to Create/Modify
- `apps/backend/app/engine/research.py` -- add `compute_regime_lab`, the streamed regime-lab observation
  builder, `regime_lab_cached` + `_REGIME_LAB_SCHEMA_TOKEN` (reuse `_deciles`/`_rank_ic`/`_group_mdd`/`_regime_by_run_projected`).
- `apps/backend/app/api/research.py` -- new `GET /research/regime-lab` route (view + as_of); extend
  `/research/samples` selectors/validation for the `regime-lab` kind.
- `apps/backend/app/engine/samples.py` -- `KIND_REGIME_LAB` + `ALL_KINDS`; `_regime_lab_samples`; wire into `compute_samples`.
- `apps/frontend/app/research/regime-lab/page.tsx` -- new lazy sub-route page (mirror existing `/research/*` pages).
- `apps/frontend/app/research/_labs.tsx` -- new `RegimeLabPage` (by-label + decile tables, paired columns, sort, As-of, `N=` chips).
- `apps/frontend/app/research/page.tsx` -- add the Regime Lab tile to `LABS`.
- `apps/frontend/lib/api.ts` -- `fetchRegimeLab` + response/row types (via `withAsOf`).
- `apps/backend/tests/test_regime_lab.py` (new) -- byte-identity, cache schema-token MISS-then-prune,
  samples count-coherence; plus updates to `test_research_streaming.py` (bounded/cold builder),
  `test_api_research.py` (new endpoint shape), `test_samples.py` (new kind). `test_db.py` /
  `test_no_magic_numbers` MUST stay green unchanged.

## UI Evolution
- New user-facing capability: open a new **Regime Lab** from the Research hub and see how forward returns and
  downside risk (max-drawdown) have differed across market-regime labels and regime-score deciles at
  1/5/10/20/60-day horizons; drill any bucket into its exact underlying observations.
- New information displayed: cross-sectional mean realized forward return + paired mean max-drawdown per
  horizon, per regime label and per regime-score decile; per-bucket n; per-decile regime-score range;
  rank-IC of regime score vs forward return per horizon; survivorship-bias / descriptive-evidence labels.
- New user actions: click the Regime Lab hub tile; sort any column (NA-last, both directions); toggle As-of
  vs All-history; click an `N=` chip to open the cohort in Research Samples (new tab).
- UI surface changes: one new page `/research/regime-lab` + one new tile on the `/research` hub. No other page changes.
- Navigation changes: none to the top-level nav skeleton — additive tile + lazy sub-route under the EXISTING
  Research section (no `blueprint.reapproval-requested` marker filed; the page is registered with a nav path +
  Data-Contract row, satisfying the coherence "has nav path / no duplicate home" checks).

## Visual Requirements
- Component patterns: reuse the existing `/research` lab building blocks from `app/research/_labs.tsx` and the
  shared Card/table primitives the sibling labs use (e.g. `LabSkeleton`, `ResearchError`, `EmptyState`,
  `returnClass`/`fmtPct`, `mddClass`/`fmtMdd` from `lib/mdd-color`, the `N=` chip pattern, the As-of mode toggle).
  Match the Factor Lab (iter-52) table treatment exactly.
- Layout: hub-linked sub-route page (page title + descriptive-evidence subtitle), then two stacked Cards — the
  by-label summary table and the regime-score decile table. Wide paired-column tables scroll horizontally
  (`overflow-x-auto`) rather than dropping columns (the iter-52 precedent).
- Key visual effects: colour-grade forward-return cells via the return tokens and max-drawdown cells via the
  `lib/mdd-color` severity scale; design tokens only, no hardcoded hex. Keep with the existing dark research aesthetic.
- States to handle: loading skeleton; backend-unavailable card; empty state; explicit muted **NA + n** for any
  `n < min_sample` / empty / null-value cell or at/near-latest horizon — never a fabricated number.

## Key Test Scenarios
- **J-110 (live, freshly-restarted/warmed backend, one heavy fetch at a time; Playwright fallback planned up
  front; md5sum the evidence dir first):** hub Regime Lab tile → `/research/regime-lab` renders the by-label
  table (6 rows) + regime-score decile table (D1…D10) with paired forward-return + max-drawdown columns per
  horizon + rank-IC + n + score range; survivorship-bias label present; **NO native `input[type=date]`** on the
  page (J-18).
- **J-110 sort:** toggling a column sort yields a BYTE-DISTINCT frame (md5 before ≠ after), NA-last; resolve the
  header by `aria-label`.
- **J-110 As-of:** toggling As-of (or arriving at a historical `?asof=`) FILTERS the observation set so rendered
  n values DECREASE; confirm the outgoing param is `as_of=` (sent automatically by the frontend); no second
  date control appears.
- **J-110 drill-down:** an `N=` chip opens `/research/samples` in a new tab for the exact `(regime label |
  regime-score decile, horizon)` cohort; the Samples "Total observations" EQUALS the clicked n (J-51/J-65
  count-coherence).
- **pytest:** `compute_regime_lab` per-(bucket, horizon) mean return / mean MDD / n byte-identical to a
  reference aggregation over the SAME observation set across Episodes/Pooled and All-history/As-of; bounded-read
  assertion (no unbounded `.all()`; ScannerResult ordered `(run_id, id)`); cache schema-token MISS on a seeded
  ALREADY-POPULATED old-schema row then repopulate + HIT byte-identical + refresh on `_dataset_version` change;
  samples `regime-lab` cohort `total` == published bucket n in BOTH Episodes+Pooled and BOTH All-history+As-of,
  every displayable bucket resolves without a 4xx; `test_db.py` expected-tables guard UNCHANGED;
  `test_no_magic_numbers` green. Launch the FULL suite **nohup-async** (its flushed `0 failed, EXIT 0` is owed
  by the next GOAL_ACHIEVED candidacy, not a gate this iter).
- **Required-still-passing (deterministic replay + live smoke where rendered):** J-109, J-25, J-26, J-29, J-107,
  J-104, J-105, J-86, J-51, J-65, J-77, J-103, J-80, **J-06 (CRITICAL, single-source)**, **J-18 (CRITICAL, 0
  native date inputs)**, **J-07 (CRITICAL, Risk-Off → 0 Actionable)**.
- **Error cases:** thin / zero-n buckets and at/near-latest horizons show NA + n (never fabricated); an
  unknown/empty regime label or out-of-range decile request returns an honest empty state; a malformed cohort
  param is rejected (4xx).

## Constraints, Discipline & Notes (heeded lessons / anti-goals)
- **No new table / no migration / no new canonical value:** reuse `event_study_cache`; READ existing
  `forward_returns.realized_return` + J-86 `max_drawdown` and stored `ScannerRun` `regime_score`/`regime_label`
  (J-80) verbatim. Single source of truth + No recompute in read path preserved.
- **No magic numbers:** every threshold/horizon/decile-count from config; no inline literal in `research.py`
  CALC code (use the J-21 boolean-sentinel idiom for any sort key).
- **Cache schema drift (iter-38/39/44):** fold a schema token into the cache key; UNIT-TEST it against an
  already-populated OLD-schema cache row (a real HIT path), not a fresh compute.
- **OOM-sensitive read path (iter-46/47/48):** stream / column-project; ScannerResult ordered `(run_id, id)`;
  probe the lab COLD (a cache HIT masks a cold-miss OOM). NEVER run the full pytest suite concurrently with the
  heavy-lab browser probes.
- **Live render evidence (iter-36/39/40/42/43/49/52):** keep BOTH servers up THROUGH the browser-qa-agent step;
  plan the Playwright fallback UP FRONT; `md5sum` the evidence dir FIRST and reject skeleton / "Backend
  unavailable" / byte-identical before/after frames; resolve sort / `N=` controls by `aria-label`, not visible text.
- **No duplicate home (coherence-critical):** J-110 must be DISTINCT from J-77 (regime × setup × pattern) and
  J-103 (severity-velocity sign vs SPY) — it studies the regime score/label ALONE against cross-sectional stock
  returns, on its own `/research/regime-lab` home.
- **Out of scope (excluded — do NOT build):** J-111 (Market Phase & Severity Lab) and J-112 (Regime × Phase ×
  Factor) — iters 54/55; any change to how regime score/label, realized return, or max-drawdown are
  COMPUTED/STORED; any new `table=True` model / stored column / DB migration; the destructive J-85 snapshot
  rebuild (~11h — do NOT trigger); any live data fetch; J-22/J-23/J-24 (data-walled — leave honestly
  blocked-NA, non-vetoing); any top-level nav-skeleton change.
- **Not a GOAL_ACHIEVED candidate:** J-111 and J-112 remain unbuilt buildable Must-haves after this iter; the
  every-buildable-Must-have gate stays unmet until iter-55. Spec is fully aligned with `docs/goal.md`; no drift
  to flag.
