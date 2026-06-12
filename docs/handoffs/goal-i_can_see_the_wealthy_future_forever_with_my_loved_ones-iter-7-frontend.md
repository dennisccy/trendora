# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-7 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-7
**Date:** 2026-06-12
**Agent:** developer
**Status:** complete
**Target journeys:** J-51 (research sample-count drill-down), J-52 (sample-row → dated stock detail, new tab)

## UI Changes

### `/research` — every `N=` figure is now a link (no other change)
The eight published sample-size chips each became a `SampleLink` (same visible `n=…` text + low-sample ⚠;
now clickable, same-window):
- **Factor Lab** — the decile rows' `n` chip (drills to `slice=decile&decile=D`), the **rank-IC** card's
  `n` chip (drills to `slice=total` — the whole observation pool), and each **by-regime** row's `n` chip
  (`slice=regime&regime=…`).
- **Combination Lab** — the **baseline / each single condition / composite / strict-overlap** cohort rows'
  `n` chips (`cohort=baseline|single|composite|strict_overlap`, `single_index=i` for a single; the resolved
  `condition=<factor>:<side>:<quantile>` triples ride along).
- **Setup & Pattern Lab (event study)** — each **per-horizon** row's `n` chip (`slice=pooled` at that row's
  horizon), each **by-regime** row's `n` chip, and each **by-sector** row's `n` chip.

Chips clicked while the **Analysis-mode toggle is "As of date"** carry `scope=asof`; the global `?asof=D`
(while historical) is merged into the href by the J-50 `useAsOfHref` helper — so the drill-down pools the
same as-of-scoped window the chip was counted under. At all-history mode the chip carries no `scope` and the
href is date-free.

### New page `/research/samples` (link-reached under Research; not a top-nav tab)
- A **cohort-description header** (which lab, the slice, the horizon, the all-history-vs-as-of scope, and
  the cohort **total == the published N**), the **survivorship-bias + descriptive caveat** banner, and a
  **samples table**: ticker, snapshot date, qualifying stored value(s), realized forward return at the
  stated horizon. Dates via the shared `formatIsoDate` (J-42). Column headers carry `TermInfo` tooltips
  reading the shared J-47 glossary.
- **n=0** renders an explicit honest empty state (never a fabricated row). An invalid deep-link (422) shows
  a distinct "Unknown sample cohort" state; a backend outage shows "Backend unavailable" — never fabricated.
- **Deep-linkable + reload-safe**: the URL params fully reproduce the cohort (the fetch re-runs on any param
  change). A "Back to Research" link (same-window, carries `?asof`) returns to the labs.
- **J-52** — each row's ticker opens `/stocks/[ticker]?asof=<that row's snapshot date>` in a **new tab**
  (`target="_blank"` + `rel="noopener noreferrer"`). The asof is the ROW's snapshot date (not the page's
  global as-of), so the new tab restores exactly that observation's date through the one global control.

## Design-system conformance
- Reuses existing primitives only: `Card`, `PageHeading`, `EmptyState`, `TermInfo`, `SampleSize` (wrapped),
  `useAsOf`/`useAsOfHref`, `formatIsoDate`, the `fmtPct`/`returnClass` return formatters, and the existing
  caveat-banner pattern. Palette/spacing/typography tokens only (no arbitrary values). Hover/focus states on
  every link. Loading skeleton, empty state, and error states all handled.
- **Nested-button discipline (iter-5/iter-6 lesson)**: the `SampleLink` chips sit in the dedicated `n`
  column, structurally SEPARATE from the `TermInfo` info triggers in the column headers — no interactive
  element is nested inside another. The samples-page headers put `TermInfo` markers as siblings of the
  header label text (never wrapping a clickable affordance).

## Gate
- `cd apps/frontend && npx tsc --noEmit` → **clean (exit 0)**. ESLint is not installed — `tsc` is the gate.

## QA notes
- **Restart the backend on :8835** first so `/api/research/samples` is served (kill by port only).
- **J-51 browser check**: on `/research`, confirm chips in all three labs render as links; click a Factor
  Lab decile `N` → `/research/samples` opens parameterized to that cohort; the displayed total equals the
  clicked chip's N (assert the exact number); reload the samples URL → same cohort; click an `N=0`
  strict-overlap cohort → explicit empty state; survivorship label visible; headers carry TermInfo tooltips;
  in As-of mode the chip link carries the scope and the total matches the as-of-scoped n; **no Next
  dev-overlay error badge** anywhere (the iter-5/iter-6 nested-button check).
- **J-52 browser check**: click a samples-row ticker → NEW tab at `/stocks/[ticker]?asof=<row snapshot
  date>` showing that date's historical detail; the originating samples tab is untouched. Spot-check one
  row's displayed factor value + forward return against the stock-detail/backtest stored values.
- **Largest cohort**: the factor `total` / rank-IC chip drills into the whole pool (~20.8k rows on the full
  seed — no pagination, per spec). Confirm it still renders (worst case).
- **Driving the As-of mode / factor / subject selects during QA**: Chrome MCP `select` does not fire React
  onChange on this frontend — use the native-setter + bubbled change-event pattern, then assert live DOM.
