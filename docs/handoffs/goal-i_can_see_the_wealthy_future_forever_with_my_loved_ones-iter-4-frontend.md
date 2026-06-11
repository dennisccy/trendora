# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-4 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-4
**Date:** 2026-06-11
**Agent:** developer
**Status:** complete

## What Was Built

J-47 UI: a categorized, client-side-searchable Glossary on `/methodology` and inline info-tooltips on
the five dense surfaces — every tooltip and the Glossary page read the SAME served `/api/methodology`
catalog entries (single source of truth; no hardcoded copy anywhere in the frontend).

### Shared plumbing (one fetch, one lookup)
- `lib/glossary.tsx` — `GlossaryProvider` mounted in `app/layout.tsx` (inside the existing
  AsOf/Readiness providers). Fetches `/api/methodology` ONCE (config is global, independent of the as-of
  date), builds a `term → GlossaryTerm` map, exposes `useGlossary` / `useGlossaryTerm`. A failed fetch
  degrades silently (lookup returns undefined → no markers).
- `components/ui/term-info.tsx` — `<TermInfo term="…">children?</TermInfo>` wraps the existing accessible
  `InfoTooltip`. The panel renders the term's name, plain-language definition, optional where-note, and
  any resolved threshold rows — exactly the served entry. A term absent from the catalog renders the
  children with NO marker (graceful degradation; never a crash, never a fabricated fallback definition).

### Glossary page (`/methodology`)
- New **Glossary** section below the existing setup/pattern catalog: categorized cards in catalog order
  (six groups), each term showing its literal UI string, definition, where-note, and threshold rows.
- A **live search input** (`data-testid="glossary-search"`) that filters term + definition as you type
  (e.g. "IC" narrows to rank-IC); categories with no match are dropped, a match-count line shows, and a
  styled empty state (`EmptyState`) appears when nothing matches.
- The setup/pattern rows in the Glossary carry a Setup/Pattern badge and reference the same data as the
  existing catalog section (not duplicated copy).

### Inline tooltips on the five dense surfaces
- **`/research`** — Factor Lab decile table, regime effectiveness table (Rank-IC, long-short spread, n),
  combination table (Cohort→composite, Hit-rate), event-study horizon table (Horizon, Median, % Positive,
  Dispersion, Expectancy, Mean MAE, Mean MFE, Return/downside-dev, Return/MAE).
- **`/backtest`** — per-date scorecard table (Horizon, Cohort→forward return, vs SPY/QQQ/Sector→excess
  return, Random peers→control group) and the Return Attribution panels (contributors & detractors,
  by-sector, by-rank-band, distribution: hit-rate / dispersion / median / n) via
  `components/return-attribution.tsx`.
- **`/stocks`** — leaderboard headers Leadership / Entry Quality / Risk / Setup / Reason.
- **`/`** — Market Regime card, the three breadth metric cards, Candidate Counts + each setup-name count
  label.
- **`/data`** — coverage figures Universe / Symbols and per-symbol table headers In universe / Date range
  / Bars / Flag.

## Design-system conformance
- Reused the existing `InfoTooltip` (palette tokens, hover/focus/click pin, `role="tooltip"`), `Card`,
  `Badge`, `EmptyState`, and palette text/border tokens (`text-text-muted`, `border-border`,
  `text-accent`, `bg-surface`). No arbitrary colors/spacing; search input uses the existing field styling
  with accent focus ring. No new visual effects introduced.
- Loading/empty/error are handled: the methodology page keeps its existing skeleton + "Backend
  unavailable" honest-error state; the glossary search has an explicit empty state; missing-term tooltips
  render nothing rather than erroring.

## Files Changed
- `apps/frontend/lib/api.ts` -- glossary types + `glossary?` on `MethodologyCatalog`.
- `apps/frontend/lib/glossary.tsx` -- NEW provider + hooks.
- `apps/frontend/components/ui/term-info.tsx` -- NEW tooltip wrapper.
- `apps/frontend/app/layout.tsx` -- mounted `GlossaryProvider`.
- `apps/frontend/app/methodology/page.tsx` -- Glossary section + live search.
- `apps/frontend/app/stocks/page.tsx`, `app/page.tsx`, `app/research/page.tsx`, `app/backtest/page.tsx`,
  `app/data/page.tsx`, `components/return-attribution.tsx` -- inline header/label tooltips.

## Tests Run
- `cd apps/frontend && npx tsc --noEmit` → clean (exit 0). ESLint is not installed; `tsc --noEmit` is the
  gate.
- The 32 distinct `TermInfo` term keys used across the UI (plus the three dashboard setup-name labels)
  were verified against the served catalog — all resolve, so no tooltip silently renders a bare label.

## Known Issues
- The running :3835 dev server predates these edits; Next.js dev hot-reloads, but the QA pump's fresh
  start is the authoritative render. `tsc --noEmit` clean is the build gate met here.
- Tooltip-equality QA assertions are deterministic: clicking the info marker pins the panel and mounts
  `role="tooltip"` content; the same `definition` string renders on the Glossary page and in the tooltip
  (both from `useGlossaryTerm`), so they are equal by construction.
