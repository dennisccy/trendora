# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-38
**Date:** 2026-06-20
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see the market's index path under two lenses simultaneously on the Dashboard by scrolling to the new "Regime × phase cross-view" chart: the top pane shows regime-coloured bands over the index lines, and the bottom pane shows phase-coloured bands, a 0–100 severity line, and a bear-probability line over the same index lines.
- Users can now synchronize zoom / scroll across both chart panes by dragging or scrolling on either pane — both panes always show the same date window (this is a view control, not a date selector; it does not change the as-of date).
- Users can now read the current Market Regime and Market Phase & Severity at a glance from the very top of the Dashboard without scrolling past any supporting charts or tables — the compact summary figures are the first thing rendered at first paint.
- Users can now expand the named component breakdown behind each compact summary figure (Market Regime and Market Phase & Severity) via an inline "details" disclosure directly below each figure, without navigating away from the Dashboard.
- Users can now expand or collapse the supporting cards (breadth metrics, Candidate Counts, Top Sectors, Top Themes, and the full Market Phase detail) using the "More detail" section header below the cross-view chart — the section defaults to collapsed.

---

## What Changed in the Visible UI

- The Dashboard (`/`) now opens with a compact two-figure summary row — **Market Regime** (stored label + 0–100 score) and **Market Phase & Severity** (stored phase badge + 0–100 severity + filtered bear-probability chip) — as the very first visible elements, before any chart.
- A new **"Regime × phase cross-view"** card now appears on the Dashboard between the Major-indexes card and the "More detail" section. It contains a single lightweight-charts chart with two stacked panes sharing one time axis.
- The top pane of the cross-view chart is the existing regime-band index chart (the J-44/J-49 view, visually unchanged); the bottom pane is new and shows: the same normalized-% index lines overlaid with phase-coloured background bands, a 0–100 severity line, and a filtered P(bear) line.
- Each summary figure (Market Regime, Market Phase & Severity) shows a collapsible "Why this regime / Why this phase — component breakdown" section that lists the named drivers behind the score, accessible without leaving the page.
- The breadth metrics, Candidate Counts, Top Sectors, Top Themes, and the full Market Phase & Severity detail card are no longer visible at first paint. They are now inside a collapsed **"More detail"** panel below the cross-view chart, expandable by clicking the section header.
- The cross-view card has a persisted hide toggle, so users who prefer to see only the summary and "More detail" can dismiss the chart and it stays hidden across page reloads.
- Phase band colours in the bottom pane and in the existing market-phase card SVG timeline now use the same shared colour mapping (design-system tokens: `--pos` / `--warn` / `--neg` / `--accent`); the card's private duplicate was removed in favour of this single source.

---

## What Old Behavior Changed

- **Dashboard first paint**: Previously, loading the Dashboard showed the full Market Regime card, breadth metrics, the Major-indexes chart, the Market Phase & Severity detail card, Top Sectors, Candidate Counts, and Top Themes all stacked in one long page. Now, first paint shows only the compact regime + phase/severity summary and the cross-view chart; all supporting detail is behind a one-click "More detail" disclosure below the chart.
- **Market Phase card colour mapping**: The phase timeline SVG inside `market-phase-card.tsx` previously used a private colour mapping. It now reads from the shared `lib/phase.ts` mapping. The displayed colours and posture associations are identical — no visual regression — but the single source now governs both the card and the cross-view chart bands.

---

## Not Visible Yet

- None. The new `GET /api/market-phase?full=true` backend capability is directly consumed by the cross-view chart on the Dashboard. All implemented capabilities in this iteration are accessible via the UI.
