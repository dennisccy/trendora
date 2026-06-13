# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-14
**Date:** 2026-06-13
**Agent:** developer
**Status:** complete

## What Was Built (UI)

On `/research` → Setup & Pattern Lab (the event study):

- **Episodes ⇄ Pooled segmented toggle** (`EventStudyViewToggle`) sits next to the subject selector. It is a button group with an active pill (styled exactly like the existing `AnalysisModeToggle`), clicked directly — NOT a `<select>`. Defaults to **Episodes**. `data-testid="event-study-view-toggle"`, buttons `event-study-view-episodes` / `event-study-view-pooled` with `aria-pressed`.
- **Disclosure line** (`EventStudyDisclosure`, `data-testid="event-study-disclosure"`) beside the figures, in BOTH views: the resolved View label (with an Episode/Pooled glossary `TermInfo` tooltip), **n** (`data-testid="disclosure-n"`), **Unique symbols** (`disclosure-unique-symbols`), and **Episodes** (`disclosure-episodes`) — all read verbatim from the payload. Replaced the old "Pooled occurrences" meta figure (now folded into the view-aware disclosure).
- Every **`N=` chip** (per-horizon, by-regime, by-sector) now carries the current `view` in its samples href, and its label reads "episodes" vs "occurrences" to match the mode. Clicking opens the mode-correct drill-down in a NEW TAB (J-65 behaviour preserved).

On `/research/samples`:
- The cohort detail line states which overlap view the drill-down reproduces ("Episodes (first-trigger)" / "Pooled (per-signal-day)"). The `view` URL param flows to the backend automatically (via `samplesFetchParams`); the drill-down lists that mode's rows and its total equals the clicked N.

On `/methodology`:
- Two new glossary entries (config-backed): **Episode** and **Pooled (per-signal-day)**, also surfaced as the toggle's `TermInfo` tooltip.

## Files Changed (frontend)
- `apps/frontend/app/research/page.tsx` — `EventStudyView` type, `EventStudyViewToggle`, `EventStudyDisclosure`, local `view` state in `EventStudyLab` → `fetchEventStudy` + chip cohorts; `view` prop threaded into the horizon/regime/sector tables.
- `apps/frontend/lib/api.ts` — `fetchEventStudy(..., view?, signal?)`; `EventStudyResponse` (+`view`/`n`/`unique_symbols`/`episode_count`); `SampleCohort` (+`view`).
- `apps/frontend/lib/samples-link.ts` — `EventStudyCohortParams.view` + serialization.
- `apps/frontend/app/research/samples/page.tsx` — view-aware cohort detail line.

## Design / Constraints Honored
- Reused the existing segmented-group pattern, `Card`/`PanelTitle`, design tokens (`bg-accent`/`text-bg`/`border-border`/`text-text-muted`); no new colors or effects.
- Hover/focus/active states on the toggle (`hover:bg-surface`, `focus-visible:ring-1 focus-visible:ring-accent`, active pill).
- Loading (existing skeleton), empty/low-sample (existing honest NA + n), error (existing "Backend unavailable" banner) all preserved — the view toggle re-fetches through the same status machine.
- **No nested-interactive hazard** (iter-5): the toggle buttons contain only text; the `TermInfo` (which renders its own `<button>`) sits OUTSIDE the toggle buttons and outside any `N=` link. No Next dev-overlay error badge expected.
- **Orthogonality / J-18**: `view` is independent local state — it never touches `?asof`, the asof-provider, or the J-32 analysis-mode `scope`. The samples href adds `view` as a cohort param only; `useAsOfHref` still authors the date.

## Gate
`cd apps/frontend && node_modules/.bin/tsc --noEmit` — **exit 0**.

## Suggested Browser QA (for browser-qa-agent)
1. `/research` Setup & Pattern Lab loads in Episodes mode by default; the Episodes⇄Pooled toggle and the n / unique-symbols / episodes disclosure are visible.
2. For Risk-off-watchlist (persisting subject): episodes n < pooled n; the episode-mode per-horizon `N=` drill-down (new tab) shows ONE row for a continuous run at its first-trigger date.
3. Flip to Pooled → figures match the previously published values; the disclosure n rises to the signal-day count while Episodes stays the same.
4. Click an `N=` chip in each mode → new tab; the drill-down total equals the clicked N; the cohort line states the view.
5. `/methodology` shows the Episode and Pooled (per-signal-day) entries.
