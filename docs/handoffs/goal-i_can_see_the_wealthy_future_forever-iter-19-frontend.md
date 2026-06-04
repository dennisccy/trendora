# goal-i_can_see_the_wealthy_future_forever-iter-19 Frontend Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-19
**Date:** 2026-06-04
**Agent:** developer
**Status:** complete

## What Was Built (UI)

A single page-level **All history ⟷ As of date** analysis-mode toggle on `/research`, driving all three labs
(Factor Lab, Multi-factor combination cohort, Setup & Pattern event study). It is a **mode, not a date
control** — As-of mode reads the existing single global top-bar as-of switcher; the page introduces **no
second date state and no date picker** (J-18, the principal anti-goal risk).

### New user-facing capability
The user can switch `/research` between **All history** (default — pools every snapshot) and **As of date**
(pools only snapshots dated ≤ the global as-of date). In As-of mode, setting the global switcher to an earlier
trading day re-points every decile / rank-IC / combination-cohort / event-study figure to that point-in-time
walk-forward window (smaller n, honest NA at early dates).

### New information displayed
An inline context label (`data-testid="analysis-mode-context"`): in As-of mode it reads e.g. "Point-in-time:
pooling only snapshots dated ≤ {date} …"; at the latest date it explains As-of equals all history; in All
history it reads "Pooling every snapshot — all history". The resolved as-of date is shown as the mode's
context label.

### New user action
One **All history ⟷ As of date** segmented toggle at the top of `/research` (`data-testid="analysis-mode-toggle"`,
with `analysis-mode-all` / `analysis-mode-asof` buttons). No new date control.

## Components / Files

- `apps/frontend/app/research/page.tsx`
  - `AnalysisModeToggle` — new segmented button-group control (`role="group"`, `aria-pressed`, button
    `data-testid`s), styled exactly like the existing `HorizonSelector`/`SideToggle` (palette tokens only:
    accent active segment, muted inactive). Clicked directly — **not** a `<select>` — so browser QA clicks it
    without the native-setter workaround.
  - `ModeContext` — new inline context line.
  - `ResearchPage` — adds `mode` state (default `"all"`), reads `useAsOf()`, computes one resolved
    `asofCutoff = mode === "asof" ? asOf : null`, threads it into the Factor-Lab effect + `<CombinationLab>` +
    `<EventStudyLab>`. All three fetch `useEffect`s now key on the **resolved `asofCutoff`** (not raw `asOf`).
  - `CombinationLab` / `EventStudyLab` — gain an `asofCutoff` prop; fetch through it; effect dep arrays include
    `asofCutoff`. Stale "NO as-of/date control (J-18)" docstrings + the event-study inline copy updated to the
    mode-aware truth.
- `apps/frontend/lib/api.ts` — `fetchFactorLab`/`fetchFactorCombination`/`fetchEventStudy` gain an `asof?: string`
  arg routed through the existing `withAsOf(...)` (appends `?as_of=` only when a historical cutoff is active);
  the three response types gain optional `asof_date?: string | null`.

## Design-system compliance

- Toggle reuses the established segmented-control pattern (border + `bg-surface-2`, accent active segment,
  `hover`/`focus-visible` states) — no new colors, no arbitrary spacing, monospace tabular-nums untouched.
- Loading / empty / error states per lab are preserved under both modes (the labs re-point; their state
  machines are unchanged).
- The survivorship / universe-relative / descriptive `CaveatBanner` renders in **both** modes (not gated on
  mode).

## Key UI behaviors to verify (for browser QA / J-32)

1. `/research` defaults to **All history**; the toggle shows All history active; figures match the prior
   all-history aggregate.
2. Click **As of date**; set the global top-bar switcher to one of the **earliest** dates; each lab's figures
   change and `n` **drops**; early-date low-sample cells show NA + n (never a fabricated number). (The mode
   toggle is a button — click it directly; the global switcher is the React `<select>` that needs the
   native-setter + bubbling change event per MEMORY `react-controlled-select-needs-native-setter`.)
3. Click back to **All history**; the full-sample figures (larger `n`) return.
4. **J-18 live:** exactly one date `<select>` on the page, a descendant of `<header>` (not `<main>`); in As-of
   mode the research fetch carries the single global `?as_of=` (expected); in **All-history mode**, moving the
   global date leaves the research figures unchanged with **no** research refetch (network-asserted).

## Build

`cd apps/frontend && npm run build` → compiled successfully, types valid, 13/13 pages generated; `/research`
builds clean (10.6 kB). Browser QA should start a fresh `next dev` (regenerates `.next`); do not run a prod
build against a live dev server (MEMORY `browser-qa-dead-shell-next-cache`).
