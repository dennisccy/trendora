# goal-mcp-loop-iter-40 Frontend Handoff

**Phase:** goal-mcp-loop-iter-40
**Date:** 2026-07-15
**Agent:** developer
**Status:** complete (implementation + typecheck; live browser verification deferred — see Known Issues)

## What Was Built

J-24 / B-201's UI half: a Risk-budget card on the Stock Detail page and matching sortable columns on the
`/stocks` leaderboard, both purely descriptive re-displays of server-computed values (no client-side
computation, no new business logic).

- **`apps/frontend/lib/api.ts`**: three new exported types — `RiskBudgetComponent` (`{value, percentile}`),
  `GapProfile` (median/p95/worst/overnight_variance_share, each a `RiskBudgetComponent`), and `RiskBudget`
  (the full bundle: `atr_pct`, `downside_vol`, `gap_profile`, `worst_20d_window`,
  `distance_to_invalidation_pct`). `StockRow` gained `risk_budget?: RiskBudget` — optional because a
  scanner row persisted before this iteration carries no `risk_budget` key at all.
- **`apps/frontend/lib/risk-budget.ts`** (new file): the single formatting source shared by the card and
  the leaderboard columns —
  - `fmtRiskValue(value)` — every served `RiskBudgetComponent.value` is ALREADY a percent number (unlike
    `fmtPct`/`fmtMdd` in `forward-return.tsx`, which format raw fraction returns by multiplying by 100);
    this only rounds + appends "%".
  - `fmtRiskPercentile(percentile)` — formats the `[0,1]` percentile as "pXX of universe" (matching the
    spec's own example text), returning `null` (never a fabricated "p0") when absent.
  - `isRiskBudgetNa(component)` — true when a component has no value, for the shared NA-rendering branch.
- **`apps/frontend/app/stocks/[ticker]/page.tsx`**:
  - New `RiskMetricTile` sub-component: one metric's label + value(s) + (when present) percentile chip,
    or a warn-colored "NA — insufficient history" line — mirrors the existing `naInvalidation`
    short-history treatment already on this page (`ThemeAndInvalidationCard`).
  - New `RiskBudgetCard`: placed directly after `ThemeAndInvalidationCard` (before the VCP/pattern
    cards). Six tiles in a `sm:grid-cols-2 lg:grid-cols-3` grid: ATR%, Downside volatility, Worst
    20-day window, Distance to invalidation, Overnight gap · p95 (with median/worst as supporting text
    inside the same tile), Overnight share of 20d variance. Renders `null` (nothing) when
    `row.risk_budget` is absent — no new error/loading state needed since the field rides the same
    detail payload the existing `DetailSkeleton` already covers.
  - Purely descriptive copy: "Descriptive only; not a recommendation." — no badge, no proven-language,
    no buy/sell/trim wording anywhere (anti-goals #1/#2).
- **`apps/frontend/app/stocks/page.tsx`**:
  - New `RISK_BUDGET_COLUMNS` config array (5 entries: ATR%, Downside vol, Gap p95, Worst 20d, Dist. to
    invalidation) — mirrors the existing `PATTERNS` array convention so header/cell/comparator/sort-key
    all read one list (adding a 6th column later is one entry, not four separate edits).
  - `SortKey` extended with the 5 new literal column keys; `comparatorFor` gained a branch mirroring the
    existing `high_proximity` column exactly — NA always sorts last regardless of direction.
  - New `RiskBudgetCell` component (mirrors `HighProximityCell`): server value re-displayed verbatim,
    muted "NA" on absence.
  - Each new header's `term` prop links to its corresponding new `/methodology` glossary entry via the
    existing `TermInfo` component (graceful no-op if the term isn't found — never a crash).

## Files Changed

- `apps/frontend/lib/api.ts` — `RiskBudgetComponent`/`GapProfile`/`RiskBudget` types, `StockRow.risk_budget?`
- `apps/frontend/lib/risk-budget.ts` — new formatting-helper module
- `apps/frontend/app/stocks/[ticker]/page.tsx` — `RiskBudgetCard`, `RiskMetricTile`
- `apps/frontend/app/stocks/page.tsx` — `RISK_BUDGET_COLUMNS`, `RiskBudgetCell`, header/cell/comparator wiring

## Tests Run

Command: `cd apps/frontend && ./node_modules/.bin/tsc --noEmit -p tsconfig.json`
Result: **zero type errors** (checked twice — once after the initial card implementation, once after a
follow-up simplification of the gap-profile tile's conditional rendering).

No frontend unit-test runner exists in this project for component-level tests (confirmed via
`package.json` — `"test"` script is absent; this matches every prior iteration's frontend handoff, which
relies on the backend's data-contract tests + browser-qa for UI correctness rather than a JS test runner).

## Known Issues

- **Live browser verification NOT performed this session.** Neither `next dev`/`next build` nor the
  backend server were started in this pass — deferred to keep this turn bounded (the backend's own
  pytest verification already consumed the available time budget; see the dev handoff's Known Issues
  for the full explanation). TypeScript type-checking is clean, and the component logic was reviewed
  by hand against the exact JSON shape `scoring.py` now produces (I traced the backend's `risk_budget`
  dict shape field-by-field against the frontend types before writing them), but this is NOT a
  substitute for an actual rendered page.
- **The Risk-budget card will show NOTHING useful (or render as absent) until the backend's operational
  DB-rebuild step runs** (see dev handoff) — `apps/backend/data/trendora.db` currently holds snapshot
  rows computed by the PRE-iter-40 `scoring.py`, which carry no `risk_budget` key at all, so
  `RiskBudgetCard` will correctly (and honestly) render `null` for every stock until the rebuild
  completes and the served snapshot rows carry the new field. This is expected, honest behavior given
  the optional-field design — not a bug — but browser-qa will need the rebuild done first to see the
  actual card content.
- **Leaderboard width**: the `/stocks` leaderboard now carries 5 additional columns (bringing the total
  to roughly two dozen). This was a deliberate choice to match the existing dense, all-columns-visible
  leaderboard convention (the table already scrolls horizontally inside `overflow-x-auto`, same as
  before) rather than introducing a new column-visibility toggle, which is out of this iteration's scope.
- No new loading or error state was added (per the plan's Visual Requirements) — the existing
  `DetailSkeleton` (whole-card skeleton) and the page's existing top-level fetch-error handling already
  cover the new additive field, since it rides the same `/api/stocks/{ticker}` response.
