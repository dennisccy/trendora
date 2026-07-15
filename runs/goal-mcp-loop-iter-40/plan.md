# goal-mcp-loop-iter-40 Execution Plan

## Context (read before building)

Goal-mode session `mcp-loop`, FULL iteration 40. Target: **J-24** (backlog **B-201**) — a
per-stock "how much can this hurt" risk-budget card. This is the 24th of 25 total Must-have
journeys; only J-25 (iter-41) remains after this before GOAL_ACHIEVED becomes reachable. J-24
carries **no Evidence Claim** (descriptive risk statistics, not a "Proven" edge) — the
post-decompose gate passes automatically; both ledgers stay 7/7 FAIL, canonical divisor stays 8.
Full binding spec: `docs/improvement-backlog.md` card **B-201** (lines ~874-911) — read it before
implementing; this plan summarizes it but B-201 is authoritative on traps/config surface.

**Pre-existing working-tree state — check before starting.** The tree currently carries
uncommitted modifications to `apps/backend/app/config.py`, `apps/backend/app/engine/prices.py`,
`apps/backend/app/engine/scoring.py`, `apps/backend/app/engine/warmup.py`, `config.yaml`, several
test files, plus an untracked `apps/backend/tests/test_scoring_window.py` and leftover
`docs/phases/goal-mcp-loop-iter-26.md` / `reports/qa/goal-mcp-loop-iter-26-test-plan.md` /
`runs/goal-mcp-loop-iter-26/`. This reads as parked iter-26 "fast-platform item F" windowing work
(the `bars_asof_window`/`max_lookback_bars` bounded-window harness) — and the CURRENT on-disk
`scoring.py`/`config.py` already reflect it (this plan was written by reading the actual files on
disk, so it accounts for this state: pass-3 already reads bars via `bars_asof_window(session,
ticker, asof, icfg.max_lookback_bars)`). The developer should confirm this diff is coherent
(review it, don't blindly discard) before layering J-24's changes on top, and keep it isolated from
iter-40's own commit if it is genuinely unrelated parked work — flag to the reviewer either way
rather than silently absorbing an unexplained pre-existing diff.

**Systemic replay-lane gap (carried from iter-39, recurring iter-33/36/38/39).** A FULL iteration
routes through `run-phase.sh`, which has no deterministic-replay lane for the required-still-passing
set. Per iter-39's precedent, either fold the closure replay in inline or expect a lean follow-up
pass. Not this plan's problem to solve, but the developer/reviewer should not claim the
required-still-passing journeys "pass" on a bare HTTP-200 smoke (the exact iter-38 TC-17 over-claim
iter-39 corrected) — a real golden replay or genuine browser-qa check is required.

## What to Build

- Two new **pure** indicator functions in `app/engine/indicators.py`: an **overnight-gap profile**
  (median / p95 / worst of `|open − prior close| / prior close` over a config window, plus the
  overnight share of 20-day return variance) and a **worst-20-trading-day-window** (most negative
  trailing 20-day return over the name's full as-of history). Both NA-graceful on short history,
  bars ≤ as-of only (no lookahead), windows from config — no inline literals.
- In `scoring.py` pass-3, compute the new risk-budget components ONCE per stock from the same as-of
  bars already in hand, **reusing** `raws_by_ticker[ticker]["atr_pct"]` (already computed in pass-1
  `_raw_components`, line ~140/164) and the **already-computed** `downside_vol` local (pass-3 line
  ~386) — do not call `ind.atr_pct` / `ind.downside_vol` a second time. Add a **new cross-sectional
  percentile step** for the new components (see "Percentile pass" note below) and **reframe
  distance-to-invalidation as a %** derived from the existing `invalidation` dict's `level` + `price`
  (no second level computation). Store values + percentiles as additive fields on the row dict — no
  weighted-score entry (Leadership / Entry Quality / Risk stay byte-identical).
- Config: `indicators.gap_window`, `indicators.worst_window_days: 20` in `IndicatorsCfg` (typed,
  validated positive, folded into the existing `max_lookback_bars` `max_needed` validator alongside
  `hv_window`/`semivol_window`/etc.); values set in `config.yaml`.
- `config.methodology` glossary entries (category `factor_stats`, same shape as the existing
  ATR%/HV/downside-vol terms at `config.yaml:1867-1886`) documenting each new component's formula +
  window, with `thresholds` `ref:`-ing the new config keys — served by the EXISTING
  `app.engine.methodology:build_catalog` (no code change needed there; it's pure config-driven).
  Note: `build_catalog`'s completeness assertion only covers `kind: setup`/`kind: pattern` — the new
  terms are glossary entries, not catalog entries, so `test_methodology_endpoint_returns_catalog`'s
  `kinds == {"setup","pattern"}` assertion is unaffected.
- **No `scanner.py` change expected.** `record_json=json.dumps(row)` already captures the whole row
  dict losslessly (scanner.py ~line 147), and `snapshot_serving.py` re-serves it verbatim — so once
  `scoring.py`'s row dict carries the new fields, `GET /api/stocks` and `GET /api/stocks/{ticker}`
  serve them automatically. Do NOT add new explicit `ScannerResult` columns (OUT OF SCOPE — no schema
  migration needed).
- **Operational step (blocking for browser-qa):** `run_scan` is immutable and `trendora.db` is built
  at boot from the seed, so the served bootstrap + latest snapshots must be regenerated by the new
  code before any UI check will see real values instead of NA everywhere. Rebuild the DB from seed
  (or clear the served snapshot runs) so bootstrap recomputes them — **bounded to bootstrap + latest
  dates only**, never a full-universe 30-year backfill (anti-goal #8 / the iter-24/26/27 OOM path).
  Verify `/api/stocks/{ticker}` carries real (non-null) new-field values before the browser lane runs.
- Frontend: extend `StockRow` in `apps/frontend/lib/api.ts` with the new nullable risk-budget fields
  (follow the existing `value`/`percentile` pairing convention already used by `ScoreComponent`
  (`raw`/`percentile`) rather than inventing a new shape).
- A new **Risk-budget card** on `apps/frontend/app/stocks/[ticker]/page.tsx`, placed near the
  existing `ThemeAndInvalidationCard` (~line 191/238), rendering ATR%, downside volatility, gap
  profile (median/p95/worst), worst-20d window, and distance-to-invalidation % verbatim from the
  server, each with its universe-percentile label. Short-history components render **NA + the
  reason** (mirror the existing `naInvalidation` warn-colored treatment), never a fabricated 0.
- New **risk-budget leaderboard columns** on `apps/frontend/app/stocks/page.tsx`, reading the SAME
  served fields (no client recomputation) — follow the existing `fwd_<horizon>`/`mdd_<horizon>`
  dynamic-column pattern (NA always sorts last) for the sortable-column plumbing.
- Additive registration in `runs/goal-session-mcp-loop/state/blueprint.md`: one Data Contract row for
  the new risk-budget components (computed once by `scoring:score_stocks`, served by the existing two
  stock endpoints, no new endpoint) and one IA-table clarification row (J-24's feature home is the
  EXISTING Stock Detail page + EXISTING leaderboard — no new surface, no nav change).

### Percentile pass — implementation note (architectural gotcha)

Pass-3's existing per-ticker loop assembles each row (bars read + patterns + hv/vcp_contraction/
downside_vol) in one iteration and cannot know a component's cross-sectional rank until every
ticker's raw value is known. Pass-2 solves this today by pre-computing raw values for ALL tickers
BEFORE calling `cross_sectional_percentiles`. For the new gap/worst-window components, the cleanest
fit is a **new pass after pass-3's row-assembly loop finishes** (rows are already collected in
`rows`, each carrying its new raw fields): build `present = {ticker: raw}` per new component from
`rows`, call the existing `cross_sectional_percentiles` (from `app.engine.normalize`, already
imported) exactly like pass-2 does, then attach each row's percentile back onto its dict — before the
final `rows.sort(...)` / rank assignment (order-independent either way). Do not try to compute
percentiles inline during the per-ticker loop itself — no ticker's peers are fully known yet at that
point.

## Agents Required

- developer: yes -- implement backend (indicators.py pure functions, scoring.py pass-3 + new
  percentile pass, config.py + config.yaml + methodology glossary, blueprint.md additive rows) AND
  frontend (StockRow extension, Risk-budget card, leaderboard columns) in one TDD pass, plus the DB
  rebuild/bootstrap-regen operational step. This project's agent catalog has a single `developer`
  agent that handles both sides (no separate backend/frontend agent types exist here).
- backend-data: yes -- `indicators.py`, `scoring.py`, `config.py`, `config.yaml`, methodology
  glossary entries, backend fixture/unit tests, DB/bootstrap regeneration.
- frontend-ux: yes -- `lib/api.ts` StockRow extension, stock-detail Risk-budget card, leaderboard
  columns.

## Frontend Present
Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/engine/indicators.py` -- add `overnight_gap_profile(...)` (median/p95/worst +
  overnight variance share) and `worst_20d_window(...)` (most negative trailing-20d return over full
  as-of history) pure functions; NA-graceful, config-windowed.
- `apps/backend/app/engine/scoring.py` -- pass-3: compute risk-budget components reusing
  `raws["atr_pct"]` + the existing `downside_vol` local, call the two new indicator functions, derive
  distance-to-invalidation % from the existing `invalidation` dict; add the post-loop cross-sectional
  percentile pass (see note above); add the new fields to each row dict (additive only).
- `apps/backend/app/config.py` -- `IndicatorsCfg`: add `gap_window: int`, `worst_window_days: int`
  fields; fold both into the `_validate` positivity check and the `max_lookback_bars` `max_needed`
  computation (mirror the existing `hv_window`/`semivol_window` treatment).
- `config.yaml` -- set `indicators.gap_window` / `indicators.worst_window_days: 20`; add
  `methodology.categories` glossary entries (category `factor_stats`) for gap profile, worst-20d
  window, and distance-to-invalidation-%, each with `thresholds` referencing the new config keys
  (mirror the ATR%/HV entries at `config.yaml:1867-1886`).
- `apps/backend/tests/test_indicators.py` -- new fixture tests for both pure functions: exact-value
  assertions (median/p95/worst, overnight variance share, worst-20d value) + the insufficient-history
  → `None` path.
- `apps/backend/tests/test_scoring.py` -- additive stored-row field assertions (new fields +
  percentiles present, cross-sectional and computed only among available peers); a byte-match spot
  check of one gap value against an independent offline recomputation; a test asserting Leadership /
  Entry Quality / Risk scores are byte-identical with the new components present (no weighted-score
  leakage); snapshot payload-shape test updates (additive fields only).
- `apps/backend/tests/test_api_methodology.py` -- extend the glossary spot-check test(s) for the new
  terms (following `test_methodology_endpoint_glossary_has_spot_check_terms` /
  `..._setups_patterns_single_sourced` precedent); confirm
  `test_methodology_endpoint_returns_catalog`'s `kinds == {"setup","pattern"}` still holds.
- `apps/frontend/lib/api.ts` -- extend `StockRow` with the new nullable risk-budget fields (a nested
  block mirroring the `Invalidation`/`ScoreComponent` field-grouping convention).
- `apps/frontend/app/stocks/[ticker]/page.tsx` -- new `RiskBudgetCard` component, placed near
  `ThemeAndInvalidationCard` (~line 191); NA-safe rendering per component.
- `apps/frontend/app/stocks/page.tsx` -- new sortable leaderboard columns re-reading the served
  fields; extend `SortKey`/comparator plumbing following the `fwd_<horizon>`/`mdd_<horizon>` pattern
  (NA always sorts last).
- `runs/goal-session-mcp-loop/state/blueprint.md` -- additive Data Contract row (risk-budget
  components) + IA-table clarification row (existing Stock Detail page + existing leaderboard;
  no nav change; no `blueprint.reapproval-requested`).
- `docs/handoffs/goal-mcp-loop-iter-40-dev.md` -- required dev handoff (DoD line item).

**Explicitly out of scope for this iteration** (do not build): feeding new components into any
weighted score; new `ScannerResult` DB columns/migration; full-universe 30-year historical backfill
of the new fields (historical rows stay honestly NA); any new endpoint; B-203 position-risk
calculator; B-202 invalidation-style evidence study; any `## Evidence Claim`, "Proven"/"Not yet
proven" badge, or position-advice language on the risk components.

## UI Evolution

- New user-facing capability: on any stock's detail page, the user can see at a glance the plausible
  downside of a name — volatility, overnight-gap exposure, worst historical 20-day drawdown, and
  distance from where the thesis is invalidated — each contextualized against the whole universe. The
  same fields appear as leaderboard columns for cross-name comparison.
- New information displayed: ATR%, downside volatility, overnight-gap median/p95/worst (+ overnight
  share of 20-day return variance), worst historical 20-day window, distance-to-invalidation %, and a
  universe-percentile label per component (e.g., "gap risk: p87 of universe").
- New user actions: none — purely descriptive, read-only. No inputs, buttons, or advice controls
  (explicitly out of scope per anti-goals #1/#2 and B-201's boundary).
- UI surface changes: one new Card section on the EXISTING `/stocks/{ticker}` detail page; new
  columns on the EXISTING `/stocks` leaderboard. No new page.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the existing `Card` / `CardHeader` / `CardTitle` / `CardContent`
  primitives exactly as `ThemeAndInvalidationCard` and `ScoreCard` already do in this file — no new
  UI primitives needed.
- Layout: place the new card in the existing stock-detail vertical stack near
  `ThemeAndInvalidationCard`; use a similar `grid gap-4 md:grid-cols-2` (or a 3-column variant if
  needed for 5-6 metrics) responsive grid. Leaderboard columns append to the existing sortable
  table's column set, following the forward-return/max-drawdown paired-column precedent (grouped,
  right-aligned numeric columns with a header sort affordance).
- Key visual effects: none new — match the codebase's existing minimal, data-dense card styling.
  Labels use `text-xs uppercase tracking-wide text-text-faint` (as `ThemeAndInvalidationCard`'s
  section labels do); numeric values use the `num` class (as `ScoreCard`'s score display does).
- States to handle: NA / short-history renders "NA" + the reason (mirror the `naInvalidation`
  warn-colored (`text-warn`) treatment) — never a fabricated 0 or blank cell. No new loading state
  needed (the existing `DetailSkeleton` already covers the whole-card skeleton since the new fields
  ride the same detail payload). No new error state (additive fields on an existing endpoint; the
  page's existing top-level error handling already covers a failed fetch).

## Key Test Scenarios

- **Browser (full-iter lane):** `/stocks/{ticker}` for a liquid name shows the full risk-budget card
  (ATR%, downside vol, gap median/p95/worst, worst-20d window, distance-to-invalidation) each with a
  percentile label. A short-history name (e.g., ARM) shows NA + reason for components lacking
  history. `/methodology` documents each new component's formula and window. A spot-checked
  leaderboard column value equals the same value on that name's detail card (single-source check).
- **Regression (required-still-passing):** J-01, J-02, J-03 (evidence badges + scores byte-identical
  on `/stocks` and detail), J-05 (evidence ledger unaffected), J-10 (deep price chart on the touched
  detail page unaffected), J-12 (universe/methodology unaffected), J-13 (`/data` unaffected), J-20
  (preflight banner still renders correctly on the touched pages).
- **Unit:** gap-profile p95/median/worst + overnight-variance-share exact-value fixtures; worst-20d
  exact-value fixture; both functions' insufficient-history → `None` path; a byte-match spot check of
  one computed gap value against an independent offline recomputation; Leadership/Entry
  Quality/Risk scores byte-identical with the new components present; methodology glossary
  completeness/spot-check test extended for the new terms; snapshot/stock payload-shape tests updated
  additively.
- **Error cases:** a name with a null invalidation level → distance-to-invalidation renders NA, never
  a divide-by-zero/crash; short-history name → NA + reason, never a fabricated 0; the served snapshot
  for the default as-of carries real (non-null) new-field values after the DB rebuild (verify via API
  before the browser lane runs, per the "Operational step" above).
