# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20 Execution Plan

Goal-mode iteration 20 — **full depth**. The remaining backend research cluster (J-72, J-75, J-77).
All three are buildable OFFLINE against the committed seed with byte-identity + count-coherence
property gates (per goal.md, NOT data-dependent). After they close green + COHERENCE-PASS + full
suite green, the next evaluation is a GOAL_ACHIEVED candidate. J-22/J-23/J-24 stay honestly
blocked-NA (non-vetoing, no code change).

## What to Build

- **J-72 — event-study perf + cache (figures byte-identical):**
  - In `research.py::compute_event_study`, replace the per-horizon re-scan of stored `forward_returns`
    with a SINGLE batched read of the subject's observation pool + a run-position index computed once
    for ALL configured horizons (no `ForwardReturn` scan per horizon). Output MUST be byte-identical to
    today in BOTH `episodes` (default) and `pooled` views, and for `as_of=None` (all-history) AND an
    `as_of`-scoped window. The `pooled` path stays the unchanged byte-identical route; the episode
    collapse stays a pure in-memory grouping (`_collapse_to_episodes`, J-63 untouched).
  - Derive the aggregate ONCE per `(subject, view, resolved as-of)` and serve it from a
    **standalone create_all-managed cache table** (key = subject + view + resolved as-of + a
    dataset-version stamp derived from stored state; value = serialized derived aggregate). The cache
    MUST refresh after dataset changes (backfill add / removal) via the dataset-version key — never a
    stale read. Prefer a standalone table to avoid the iter-12 `_ADDITIVE_COLUMNS` trap.
  - `GET /api/research/event-study` payload unchanged in shape and value; reads serve the cached/derived
    aggregate, never recompute per request.
  - Frontend `/research`: each lab section (Factor Lab, Combination Lab, Setup & Pattern Lab, and the new
    J-77 study) fetches independently with its OWN loading/skeleton state — no single slow query blocks
    the page (J-15 warm-load discipline). No figure changes (speed/UX only).

- **J-75 — per-stock forward returns (1/5/10/20/60-day), served VERBATIM from stored data:**
  - Extend `snapshot_serving.py` (`stored_stock_rows` / `stocks_payload` / `stock_detail_payload`) so
    each stock row ADDITIVELY carries its FIVE realized forward returns read VERBATIM from the stored
    `forward_returns` table (keyed by `run_id` + `symbol` + `horizon`) for the resolved as-of run — the
    SAME data Backtest/J-21 reads, NEVER recomputed in API or view; only bars dated > D (no-lookahead
    intrinsic to the stored rows).
  - A horizon with no stored row renders **NA** (so at/near latest all five are honestly NA — never
    fabricated). Leaderboard and detail values IDENTICAL for the same ticker/date/horizon (J-06).
  - The five horizons come from `config.walk_forward.horizons` — NO hardcoded `[1,5,10,20,60]` literal in
    serving code (No magic numbers).
  - Frontend: `/stocks` renders five forward-return columns (colour-graded by sign), sortable under the
    J-48 view-transform contract (re-orders only — no refetch/recompute; default order stays the stored
    rank; NA cells render honest "NA"). Stock Detail shows the SAME five for the resolved as-of date.
    Single global as-of drives the date (J-18); `?asof` href-stamping (J-50) unchanged. Reuse the
    existing `forward-return.tsx` component where it fits.

- **J-77 — Regime × Setup × Pattern ranked combinations study:**
  - ADDITIVELY enrich the event-study per-observation pool (`_event_study_members` /
    `_event_study_observation_set`) so each observation also carries its STORED `regime_label`
    (`ScannerRun`) + `setup_status` + pattern flags (`ScannerResult`), read VERBATIM. Enrichment MUST be
    additive: existing J-29/J-63 figures + existing samples drill-downs stay BYTE-IDENTICAL (asserted).
    Note: `_event_study_members` already carries `regime` + `sector`; add `setup_status` + pattern flags.
  - Add `research.py::compute_regime_setup_pattern_study(...)` grouping the SAME enriched observation set
    by the (regime, setup, pattern) key (same builders, one membership rule) reporting per the selected
    horizon each combination's `n`, mean, median, %positive (hit-rate), expectancy, and the downside-only
    risk-adjusted figure(s) (return/downside-dev AND return/MAE — downside only, never total volatility).
    Honors `view` (Episodes default / Pooled, J-63) and `as_of` (J-32 FILTER only). Combinations below
    `config.walk_forward.min_sample` show NA + n (reuse EXISTING `min_sample` — no new magic number).
  - Serve via NEW endpoint `GET /api/research/regime-setup-pattern` mirroring `/api/research/event-study`
    param style (`horizon`, `view`, `as_of`; default ranking by the risk-adjusted figure). Unknown
    subject/horizon/view → explicit 4xx (never silent empty 200).
  - Extend `samples.py` + `GET /api/research/samples` with a NEW cohort selector for a
    (regime, setup, pattern) combination so a row's `N=` chip drills through the SAME observation builder;
    the drill-down `total` MUST EQUAL the row's published `n` in BOTH Episodes and Pooled modes
    (count-coherence keystone, asserted SAME-INSTANT). Vocabularies come from the EXISTING config-backed
    catalog (no hardcoded lists in code).
  - Frontend: a NEW **Regime × Setup × Pattern** study section on `/research` — a ranked, client-side
    sortable table (J-48 contract), default ranked by risk-adjusted return; honors the horizon selector,
    Episodes ⇄ Pooled toggle (J-63), As-of vs All-history toggle (J-32); each row's `N=` chip opens
    `/research/samples` for that exact cohort in a NEW tab (J-65, `?asof` href-stamped J-50); low-sample/
    empty cells show NA + n; survivorship-bias label persists; column headers read the SAME J-47 glossary.

## Agents Required

- developer: yes — implements the full backend cluster (research engine + serving + cache table +
  samples cohort selector + new endpoint) AND the frontend (`/research` per-section loading + new study
  table, `/stocks` + Stock Detail forward-return columns), following TDD. Both backend-data and
  frontend-ux work land in this single developer agent.
- backend-data: yes
- frontend-ux: yes

## Frontend Present: yes

## Files to Create/Modify

Backend:
- `apps/backend/app/engine/research.py` — J-72 single-batched-read refactor of `compute_event_study` +
  cache-table read/write/invalidate; J-77 additive enrichment of `_event_study_members` /
  `_event_study_observation_set` + new `compute_regime_setup_pattern_study(...)`.
- `apps/backend/app/engine/snapshot_serving.py` — J-75: add five stored forward returns to
  `stored_stock_rows` / `stocks_payload` / `stock_detail_payload` (read VERBATIM from `forward_returns`,
  horizons from `config.walk_forward.horizons`, NA where no stored row).
- `apps/backend/app/engine/samples.py` — J-77: new (regime, setup, pattern) combination cohort selector
  over the enriched `_event_study_members` set (count-coherent in both modes).
- `apps/backend/app/api/research.py` — J-77: new `GET /api/research/regime-setup-pattern` endpoint +
  `/research/samples` new cohort params (mirror existing validation/4xx patterns).
- `apps/backend/app/models.py` — J-72: a NEW standalone create_all-managed event-study cache table
  (key = subject+view+resolved-as-of+dataset-version; value = serialized aggregate). (Preferred over a
  new column to avoid the `_ADDITIVE_COLUMNS` trap.)
- `apps/backend/app/db.py` — ONLY if J-72 cache is implemented as a new column on an existing table
  (NOT preferred): register it in `_ADDITIVE_COLUMNS` + the guard test. A standalone table needs no
  `_ADDITIVE_COLUMNS` entry.
- `apps/backend/tests/...` — J-72 byte-identity (both views × all-history/as-of) + single-batched-read
  assertion + cache-refresh-after-dataset-change; J-75 leaderboard==detail==stored row per (ticker,
  horizon) + NA-where-no-row + no-lookahead + config-driven horizons; J-77 byte-identity of existing
  figures after enrichment + group-by correctness + count-coherence SAME-INSTANT in both modes +
  config-backed vocabulary + min-sample NA honesty; error-case 4xx tests for the new endpoint + samples
  cohort selector.
- Frontend:
  - `apps/frontend/app/research/page.tsx` — per-section independent loading/skeleton states + the new
    Regime × Setup × Pattern study section.
  - `apps/frontend/app/stocks/page.tsx` — five forward-return columns (colour-graded, J-48-sortable, NA
    honest).
  - `apps/frontend/app/stocks/[ticker]/page.tsx` — same five forward returns for the resolved as-of date.
  - `apps/frontend/components/forward-return.tsx` — reuse/extend for the five-column rendering if it fits;
    a small new study-table component may be added under `apps/frontend/components/` if the section is large.
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-20-dev.md` — dev handoff.

## UI Evolution

- New user-facing capability: Research loads section-by-section without a single blocking spinner; the
  leaderboard and stock detail expose realized forward returns at 1/5/10/20/60 days; a new ranked
  Regime × Setup × Pattern evidence table shows which regime/setup/pattern combinations historically led
  to the strongest (risk-adjusted) forward returns, drillable to the exact observations.
- New information displayed: five per-stock forward-return columns (1/5/10/20/60d) on `/stocks` + Stock
  Detail; a ranked combinations table on `/research` (n, mean, median, hit-rate, expectancy,
  risk-adjusted, per horizon).
- New user actions: sort the forward-return columns (`/stocks`) and the combinations table (`/research`);
  flip Episodes/Pooled + As-of/All-history on the new study; click a combination row's `N=` chip to open
  its samples drill-down in a new tab.
- UI surface changes: `/research` gains a new study section + per-section independent loading states;
  `/stocks` and `/stocks/[ticker]` gain forward-return columns.
- Navigation changes: none (all land on EXISTING IA homes — Research / Stocks / Stock Detail; the
  `/research/samples` drill-down is reused, not duplicated; no new page, no new top-level nav section —
  no `blueprint.reapproval-requested`).

## Visual Requirements

- Component patterns: dense data tables (the existing leaderboard/research table style — monospace/tabular
  numerics); colour-graded numeric cells by sign for forward returns; the existing `N=` chip + glossary
  info-tooltip patterns; skeleton loaders for per-section loading. Reuse `forward-return.tsx`.
- Layout: dark analytical workstation — `/stocks` extends the existing leaderboard table with five new
  columns; `/research` adds a new study section below the existing labs, each lab section independently
  loaded. No new page layout.
- Key visual effects: colour-graded leaderboard cells (positive/negative return tint within the palette);
  consistent with the existing dense dark tables — no flashy effects. Numbers monospace/tabular.
- States to handle: loading (per-section skeletons — J-72/J-15); empty / NA (honest "NA" cells where no
  stored forward-return row, low-sample combinations show NA + n — never fabricated); error (the existing
  research error treatment); survivorship-bias label persists on the new study.

## Key Test Scenarios

- **J-72:** event-study output byte-identical to before in BOTH views AND all-history + as-of-scoped
  (committed assertion); the per-horizon computation issues a SINGLE batched read, not one scan per
  horizon (committed assertion); the cache refreshes after a dataset change (no stale figures). Browser:
  each `/research` lab section shows its own loading state and the event study reaches interactive without
  a full-page block; figures unchanged.
- **J-75:** leaderboard and detail forward returns IDENTICAL for the same ticker/date/horizon; near-latest
  horizons are NA (never fabricated); columns are view-transform sortable (no refetch/recompute); only
  bars dated > D contributed (no-lookahead, inherited from stored rows); horizons config-driven. Browser:
  five columns render at a historical as-of with post-D bars, sort re-orders, Stock Detail shows the same
  five, latest → all NA, further-back populates more horizons.
- **J-77:** every figure derives from the SAME enriched observation set; existing J-29/J-63 figures
  byte-identical (asserted); the `N=` drill-down total EQUALS the published n SAME-INSTANT in BOTH
  Episodes and Pooled; vocabularies config-backed; low-sample cells NA + n; survivorship-bias label
  present. Browser: the ranked table renders, sort re-orders, flipping Episodes/Pooled + As-of/All-history
  re-points the figures, the `N=` chip opens `/research/samples` in a new tab with total == row n.
- **Error cases:** unknown subject/horizon/view on `/api/research/regime-setup-pattern` → explicit 4xx
  (never silent empty 200); unknown combination cohort selector on `/research/samples` → 4xx; an n=0
  combination → honest empty drill-down (total 0, no fabricated row); a horizon lacking post-D bars → NA.
- **Required-still-passing (browser smoke + suite):** J-29, J-63, J-25, J-26, J-32 (other research labs +
  event study unchanged), J-51, J-64, J-65 (samples count-coherence), J-05, J-06 (detail/leaderboard
  score coherence), J-21 (Backtest reads the same stored forward_returns), J-48 (view-transform sorting),
  J-18 (single date control), J-50 (?asof href stamping). md5sum the evidence dir first; capture
  below-the-fold study tables full-viewport.
- **Suite gate:** the FULL backend pytest suite (~790 tests, ~50 min) is GREEN — handed to the pump as a
  `nohup` background run; the goal-evaluator gates on the flushed terminal summary line and MUST NOT block
  on the in-flight suite. `tsc --noEmit` clean (frontend gate; ESLint not installed).

## Assumptions & Notes

- **Cache store choice:** plan assumes a standalone create_all-managed cache table for J-72 (blueprint +
  spec + iter-12 lesson all prefer it to avoid the `_ADDITIVE_COLUMNS` trap). If the developer instead
  adds a column to an existing table, it MUST be registered in `db.py::_ADDITIVE_COLUMNS` + the guard
  test and exercised against a non-fresh live DB.
- **No new validated config section for J-77** (spec NOTES + iter-11/12 lesson): derive the
  regime/setup/pattern vocabularies from the EXISTING `config.research` catalog + reuse
  `walk_forward.min_sample`. If a new validated `config.yaml` section is unavoidable, it MUST be pruned at
  EVERY config-narrowing site (grep, do not trust a fixed list): `apps/backend/scripts/build_qa_fixture_db.py`,
  `apps/backend/scripts/apply_universe_to_config.py`, AND every inline test config dict under
  `apps/backend/tests/`.
- **Count-coherence is same-instant** (iter-7 lesson): the published N per row MUST be asserted against
  the live `/research/samples` drill-down total at the SAME instant — Ns drift between backend boots as
  warm-up matures forward returns. Never assert against a hardcoded N from an earlier capture.
- **J-72 is a perf property, not a displayed number** (iter-8 lesson): the binding gates are byte-identity
  of figures + the single-batched-read assertion, NOT a wall-clock ratio in a capture.
- **Frontend `/research` is a single `page.tsx`** with inline lab sections (no separate per-lab files) —
  per-section loading + the new study section land there. The existing `forward-return.tsx` component is
  reused for the five-column rendering.
- **Operational timeouts** (session memory): budget the full dev turn and the long suite against the
  long-dispatch / heartbeat / inflight timeouts; the suite runs nohup-async and the evaluator answers
  promptly on the flushed summary line.
- **Out of scope (excluded):** any change to canonical scores/buckets/setup statuses/pattern flags/regime
  labels (read VERBATIM; J-72 byte-identical); any new computation of forward returns/excursions; a new
  top-level nav section or a second `/research/samples`-style page; any predictive/fitted/ML model over
  the combinations (descriptive evidence only); the data-walled J-22/J-23/J-24 (no code change);
  J-44 persistent toggle-off-persistence debt (non-gating, carried). `/backtest` is not in scope (QA may
  optionally capture its console to confirm the iter-19 dev-overlay "1 error" badge is pre-existing).
- **Date constants for QA** (from iter-19 handoff): latest = `2026-06-12`; a historical run date =
  `2026-05-28`; oldest = `2021-01-04`.
- No drift from goal.md detected: all three journeys are named Must-haves (Capabilities 22/27/29,
  canonical "Per-stock forward returns", and the Research IA), and the spec conforms to the approved
  blueprint (existing IA homes, additive data contracts, no second compute path).
