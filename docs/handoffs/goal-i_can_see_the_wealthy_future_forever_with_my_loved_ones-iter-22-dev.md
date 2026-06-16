# goal-iter-22 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-22
**Date:** 2026-06-16
**Agent:** developer
**Status:** complete

## What Was Built

Two **frontend-only, zero-backend-diff** journeys (lean depth), both re-displays/re-uses of already-served canonical values:

### J-79 — Step the as-of date with the calendar popover closed (amends J-71 / J-62)
- **Always-visible ◀ / ▶ stepper buttons** in the top bar beside the as-of control. Each steps the single global as-of to the previous / next **available snapshot date** (snapshot-only — never an arbitrary calendar ±1), bounded (◀ disabled at the oldest; ▶ disabled at the newest, which rests at Latest). They drive the SAME `setAsOf` the calendar already calls, so the historical badge and `?asof` serialization (J-43/J-50) stay in sync. No second/page-local date state.
- **Opt-in "← → steps date" checkbox** in the top bar — **persisted** (localStorage `asof-arrow-steps`, via the existing `usePersistedToggle` pattern) and **default-off**. When on, a **field-guarded global key handler** steps the as-of with ← / → exactly like the buttons. The handler:
  - is installed ONLY while the checkbox is on (never hijacks arrows / scrolling when off),
  - is a no-op while the calendar popover is open (the popover's own `onKeyDown` from J-71 owns arrows then — unchanged),
  - is **field-guarded**: it never fires while focus is in an `input` / `textarea` / `select` / `contenteditable` (the caret moves instead — goal.md J-79 step 5),
  - calls `e.preventDefault()` only when it actually steps (so scrolling is never hijacked otherwise).
- **Calendar Year + Month quick-jump dropdowns** (`asof-calendar.tsx`) that navigate the **viewed month only** (a presentation cursor, clamped to the stored `[oldest, newest]` month range — NOT a second date state, never serialized). The selectable-day / disabled-day / "Latest" / Escape / click-to-commit affordances (J-62) are unchanged.
- The bounded snapshot-only stepping logic and the field-guard predicate were extracted into one pure, unit-tested authority (`lib/asof-step.ts`) used by the buttons, the opt-in keys, AND the existing J-71 popover scrub — so stepping is identical everywhere and there is exactly one implementation.

### J-80 — Stocks leaderboard shows the selected date's market regime + theme ranking
- `/stocks` header now renders the resolved as-of date's **market-regime label + 0–100 score**, read from `/api/dashboard` (`regime.label` / `regime.score`) — the SAME stored canonical regime the Dashboard shows (J-06), never recomputed. The label→colour mapping was extracted to one shared module (`lib/regime-variant.ts`) reused by the Dashboard and Stocks so the same label renders the same colour. Honest empty state ("No regime for this date") when absent.
- `/stocks` header now renders a **ranked Top-Themes strip** (top 5, mirroring the Dashboard's Top Themes slice) read from `/api/themes` (`rank` / `score`, the SAME descending order the Themes page uses) — `#rank · Name` chips, each linking to `/themes` with `?asof` href-stamping (J-50). Honest empty state ("No ranked themes for this date") when a date has none — never a fabricated `#1`.
- **`#n` rank badges** (from the same `/api/themes` rank) added to each leaderboard row's theme chips (J-56) and to the theme-filter `<option>` labels. A chip / option with no served rank shows no badge (never fabricated).
- The `/api/dashboard` + `/api/themes` fetches are keyed to the SAME `[asOf]` as the leaderboard fetch and are **non-blocking + independent** (each failure clears only its own header section; the leaderboard is unaffected). Existing rows, scores, buckets, setups, filters, symbol search (J-55), column sorting (J-48), theme chips (J-56), and forward-return columns (J-75) are all unchanged.

## Files Changed

- `apps/frontend/lib/asof-step.ts` — **new**. Pure authority for J-79: `resolveStep` (bounded, snapshot-only stepping; newest→Latest/null), `canStepPrev` / `canStepNext`, and the `isFieldEditingTarget` field-guard predicate. No React/DOM deps → unit-testable under `node`.
- `apps/frontend/lib/asof-step.test.ts` — **new**. 13 assertions (exact values) for bounded/snapshot-only stepping, Latest normalisation, empty/single-date lists, the `canStep*` bounds, and the field-guard across input/textarea/select/contenteditable vs steppable targets. Runs with `node lib/asof-step.test.ts`.
- `apps/frontend/lib/regime-variant.ts` — **new**. The single stored-regime-label → Badge-variant mapping, shared by the Dashboard (J-06) and the Stocks header (J-80).
- `apps/frontend/components/asof-provider.tsx` — added `useAsOfStep()` (stepPrev/stepNext/canPrev/canNext driving the existing `setAsOf` via `resolveStep`); imports the shared step helpers. The provider remains the sole owner of the as-of state and its `?asof` serialization.
- `apps/frontend/components/asof-switcher.tsx` — added the ◀ / ▶ buttons, the persisted default-off "← → steps date" checkbox, and the field-guarded global key handler (installed only when the checkbox is on, no-op while the popover is open).
- `apps/frontend/components/asof-calendar.tsx` — added the Year + Month quick-jump dropdowns (viewed-month cursor only, clamped to stored history); refactored the J-71 `stepAsOf` to use the shared `resolveStep` so it shares the one stepping authority.
- `apps/frontend/app/page.tsx` (Dashboard) — replaced the local `regimeVariant` with the shared `lib/regime-variant` import (behaviour identical).
- `apps/frontend/app/stocks/page.tsx` — added the `/api/dashboard` + `/api/themes` fetches (keyed `[asOf]`, non-blocking), the `RegimeThemeHeader` (regime band + ranked Top-Themes strip), the served `themeRank` map, the `#n` chip badges (threaded through `StockTableRow` → `ThemeChips`), and the `#n` theme-filter option labels.
- `apps/frontend/tsconfig.json` — added `**/*.test.ts` to `exclude` so the node-run unit test is not typechecked/bundled by `next build`.

## Tests Run

- **Frontend unit tests (new):** `cd apps/frontend && node lib/asof-step.test.ts` → **13 checks passed** (asserts exact values; covers bounded no-ops at oldest/newest, snapshot-only landing skipping a non-snapshot calendar day, Latest normalisation, empty/single-date lists, and the field-guard predicate).
- **Type check (authoritative):** `cd apps/frontend && npx tsc --noEmit` → **exit 0**, no errors.
- **Dev-server boot verify:** launched `next dev -p 3835` (against `NEXT_PUBLIC_API_URL=http://localhost:8835`); `/` → HTTP 200 (Compiled), `/stocks` → HTTP 200 (Compiled), `/themes` → HTTP 200; **no errors/warnings** in the dev log. Server killed **by port** (3835) only, per session convention — no `next`/`next-server` processes remain, port free.
- **Backend pytest:** **not run** — there is **zero** backend diff (confirmed: `git status` shows no `apps/backend` change). Both endpoints used by J-80 (`/api/dashboard`, `/api/themes`) already shipped (`lib/api.ts`). Per session memory the full suite is ~34 min and a subagent can't complete it; the git-diff confirmation is the targeted sanity the spec asks for.

## Known Issues

- **No browser test harness exists in this frontend** (no Vitest/Jest/Testing-Library configured), so the React component behaviour (button clicks, the global key handler, the controlled `<select>` dropdowns) is covered by (a) the pure-logic unit tests in `lib/asof-step.test.ts` and (b) the upcoming browser-qa-agent pass — not by component-render unit tests. The stepping/field-guard *logic* itself is fully unit-tested in isolation.
- **ESLint is not configured by the project** (`next lint` prompts to set it up; there is no eslintrc). It was therefore not run; `tsc --noEmit` is the authoritative static check and passes clean.
- **Browser-QA note for the controlled `<select>`s** (Year/Month dropdowns + the theme filter): per the `react-controlled-select-needs-native-setter` lesson, drive them via the native-setter + bubbling `change` event in `eval`, then assert the live DOM — the Chrome MCP `select` action does not fire React `onChange` on this frontend.
- **Browser-QA test IDs** added for verification: `asof-step-prev`, `asof-step-next`, `asof-arrow-toggle`, `asof-cal-year`, `asof-cal-month-select`, `stocks-regime-theme-header`, `stocks-regime`, `stocks-regime-score`, `stocks-regime-empty`, `stocks-top-themes`, `stocks-top-theme`, `stocks-top-themes-empty`, `theme-chip-rank`.
- **Top-Themes strip is capped at 5** (mirrors the Dashboard's Top Themes slice). The `#n` badges on row chips / filter options use the FULL served ranking (not capped), so a theme ranked outside the top 5 still shows its true `#n` on a row chip.

## Suggested Next Phase

Plan the two deferred, backend-touching journeys at **full depth** (each needs a pytest gate): **J-81** (forward-return columns on the Themes and Sectors leaderboards, read from the stored `forward_returns` table via the same `_leadership_returns` builder Backtest uses) and **J-82** (the Regime × Setup × Pattern NA-sort fix + Regime/Setup/Pattern filters + the `N=` drill-down 422 fix + the Pooled default — a sort/filter view fix plus a samples-validation reconciliation over the stored event-study observation set). Both are NOT data-dependent and verifiable offline against the committed seed.
