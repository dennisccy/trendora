# goal-mcp-loop-iter-22 Frontend Handoff

**Phase:** goal-mcp-loop-iter-22
**Date:** 2026-07-08
**Agent:** developer
**Status:** complete

## What Was Built

- **Vendor labels on the Dashboard major-indexes chart** (`components/index-regime-chart.tsx`): the
  legend now shows each series' honest data vendor next to its name (e.g. "S&P 500 Index (^SPX) (Stooq)"),
  omitted entirely when the series has no vendor record (the SPY/QQQ/IWM/RSP/DIA ETF lines — never a
  fabricated vendor). The hover tooltip shows the same vendor next to each symbol.
- **Same treatment on the J-97 two-pane cross-view chart** (`components/phase-cross-view-chart.tsx`),
  which independently renders the same `series` and had its own copy of the same palette/legend logic —
  see the dev handoff's "Deliberate scope decisions" for why this file was touched even though it wasn't
  in the plan's literal file list.
- **Extended the chart line-color palette from 5 to 10 slots** in both chart components (`globals.css`
  gained `--chart-orange`/`--chart-lime`/`--chart-blue`/`--chart-pink`; `--snapshot` — already defined but
  unused by these charts — became the 6th slot). This fixes a verified defect: once the deep index/macro
  benchmarks widen `index_chart.symbols` past 5 configured lines, the old 5-token array would wrap
  (`index % 5`) and reuse a color — e.g. a 6th line rendering in the exact same `--accent` teal as the
  1st, an indistinguishable collision. The first 5 slots are UNCHANGED (every pre-existing line keeps its
  exact color).
- **New `/data` panel** (`components/index-vendor-panel.tsx`): a small table listing every series on the
  major-indexes chart with its vendor and real first-bar date, reading the same `GET /api/indexes`
  payload the Dashboard chart reads (no new endpoint, no re-parse of the seed manifest). Has its own
  loading (skeleton), error (styled alert), and empty states, independent of the rest of `/data`. Wired
  into `app/data/page.tsx` right after the existing `MacroFeedPanel`.

## UI Evolution

- New user-facing capability: the Dashboard's major-indexes chart can now show deep equity-benchmark
  lines (`^SPX`/`^NDX`/`^DJI`) reaching back to 1996, well before the ETF lines' ~1999/2005 floors, plus
  the volatility (`^VIX`) and a macro proxy (`^TNX`) overlay.
- New information displayed: a per-series vendor label (Stooq / Yahoo / FRED-macro proxy) on the chart
  legend and tooltip (both Dashboard chart surfaces), plus a new `/data` panel listing the same per
  series with its honest first-bar date.
- New user actions: none — existing chart range/hover controls only; the `/data` panel has no controls
  of its own (a read-only disclosure table).
- UI surface changes: Dashboard `/` major-indexes & regime card and the J-97 cross-view card (more lines
  + vendor labels); `/data` gains one new small disclosure panel after `MacroFeedPanel`.
- Navigation changes: none.

## Design System Compliance

- Component library: reused `Card` for the new panel (matching `MacroFeedPanel`'s `className="p-0"` +
  a page-local `PanelTitle` header pattern, which is this codebase's established per-file convention —
  `PanelTitle` is independently defined in 4 files already, not a shared import); `Badge` (`variant="default"`,
  neutral — vendor is provenance metadata, not a pass/fail status, so no `ok`/`warn`/`danger` variant was
  used for it, keeping those reserved for genuine status).
- Colors: every new value comes from a `globals.css` CSS custom property — no arbitrary hex in any
  component. The 4 new tokens were derived via the `dataviz` skill's categorical-palette method (OKLCH
  hue-gap search + CVD-separation validated with `scripts/validate_palette.js`), not eyeballed.
- States handled: the new `/data` panel has loading (animated skeleton), error (styled `AlertTriangle`
  alert, matching `MajorIndexesCard`'s error-state convention), and empty states. The two chart
  components' existing loading/ok/empty/error states are unmodified (this iteration only touches the
  legend/tooltip/palette inside the "ok" render path).
- Responsive/interactive states: the new panel's table uses `overflow-x-auto` (matching `MacroFeedPanel`'s
  table); no new interactive controls were added (read-only), so no new hover/focus/active states were
  needed beyond the existing `Badge`/`Card` primitives'.

## Files Changed

- `apps/frontend/lib/api.ts` — `IndexSeries` gained `vendor: string | null` and `first: string`.
- `apps/frontend/app/globals.css` — added 4 new categorical chart-line tokens with full derivation
  rationale in a code comment.
- `apps/frontend/components/index-regime-chart.tsx` — palette extension; vendor label in legend + tooltip.
- `apps/frontend/components/phase-cross-view-chart.tsx` — same palette extension + vendor label.
- `apps/frontend/components/index-vendor-panel.tsx` (new) — the `/data` vendor-disclosure panel.
- `apps/frontend/app/data/page.tsx` — imports and renders `<IndexVendorPanel />`.

## Tests Run

Command: `cd apps/frontend && npx tsc --noEmit`
Result: clean, exit code 0. No frontend automated test framework exists in this project (confirmed again
this iteration); the browser-qa-agent performs the live behavioral verification (screenshots of the
legend, tooltip, and the new `/data` panel) per the plan.

## Known Issues

- The new `/data` panel and both chart legends were verified by direct code review + `tsc` only at dev
  time (no frontend test runner installed) — full live-rendering verification (does the vendor text
  actually appear, does the extended palette actually render 10 distinguishable colors on screen) is the
  browser-qa-agent's job, not self-certified here.
- See the dev handoff's "Known Issues" for a pre-existing, out-of-scope `^TNX` data-window note that
  affects the disclosed `first` date's relationship to the chart's actual rendered range.

---

## Fix Notes (audit FAIL remediation — 2026-07-08)

The audit (`goal-mcp-loop-iter-22-audit.md`, FAIL) confirmed the vendor labels and the `/data` panel are
correct; the ONE blocking gap was purely presentational and frontend-only. Full detail is in the dev
handoff's "Fix Notes"; the frontend summary:

- **F1 (CRITICAL) — deep 1996 history invisible in the live Dashboard chart's default view — FIXED.**
  The live chart is `phase-cross-view-chart.tsx` (not the dead `index-regime-chart.tsx`). lightweight-
  charts 5.2.0's default `minBarSpacing` floor (0.5 px/bar) capped `fitContent()` at the recent ~2,084
  bars (~8 yr), hiding the committed `^SPX`/`^NDX`/`^DJI` history back to 1996. **Fix:** added
  `minBarSpacing: 0.02` to the chart's `timeScale` options so `fitContent()` fits the full ~30-yr window
  by default (no new control/interaction). Live-verified at 1440×900: hovering the chart's far-left edge
  in its DEFAULT view reads date `1996-03-25` with `^SPX · Stooq` / `^NDX · Stooq` / `^DJI · Stooq` /
  `^VIX · Yahoo` rows; the legend shows all three vendor categories (incl. `10Y-2Y spread proxy (^TNX)
  (FRED-macro proxy)`).
- **F2 (MINOR) — `IndexSeries.first` typed non-nullable — FIXED.** `lib/api.ts`: `first: string` →
  `first: string | null`, matching the nullable backend contract. Its sole consumer already renders
  `null` as "—" via `formatIsoDate`. `tsc --noEmit` clean.

### Files changed this fix pass
- `apps/frontend/components/phase-cross-view-chart.tsx` — `minBarSpacing: 0.02` on `timeScale`.
- `apps/frontend/lib/api.ts` — `IndexSeries.first` → `string | null`.
