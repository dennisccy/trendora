# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44
**Date:** 2026-06-22
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 16/16 tests passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Dashboard loads with a single market chart | smoke | P1 | Single cross-view card, no spinner, no "Major indexes" card | Page rendered; exactly one market chart (Regime × phase cross-view); `hasMajorIndexes=false` | PASS | `UT-01-result.png` |
| UT-02 | Cross-view card renders both panes | smoke | P1 | Two visually distinct stacked panes in the cross-view card | 11 canvas elements present (top pane at y=441 h=279, bottom pane at y=721 h=140, shared x-axis at y=861); both panes visible | PASS | `UT-02-chart-view.png` |
| UT-03 | MajorIndexesCard is absent from the Dashboard | happy-path | P1 | No card titled "Major indexes & regime" | DOM text check: `hasMajorIndexes=false`, `hasCrossView=true`; scrolled full page, no such heading found | PASS | `UT-01-result.png` |
| UT-04 | Cross-view bottom pane shows severity-velocity line with zero baseline | happy-path | P1 | Velocity line crossing zero; dashed zero reference line; no "Filtered P(bear)" line | Page text confirms "0-centered"; source code verifies `createPriceLine({price: 0, lineStyle: Dashed})` for velocity scale; `hasFilteredPBear=false` | PASS | `UT-06-tooltip-visible.png` |
| UT-05 | Cross-view chart legend shows "Severity velocity" label | happy-path | P1 | Legend swatch "Severity velocity (0-centered; + = worsening)"; no "Filtered P(bear)" | `hasSeverityVelocityLegend=true`, `hasFilteredPBear=false` confirmed via DOM text eval | PASS | `UT-15-legend-visible.png` |
| UT-06 | Cross-view tooltip shows regime label and severity-velocity on hover | happy-path | P1 | Tooltip with regime label/score + severity-velocity signed value + date/index/phase/severity/P(bear) | Tooltip at 2024-09-09: "Narrow leadership · 59/100", "Pullback sev 37", "P(bear) 0.02", "Severity velocity +1.25" — all rows present | PASS | `UT-06-tooltip-visible.png` |
| UT-07 | Cross-view tooltip shows "NA" for severity-velocity at earliest dates | validation | P2 | "NA" shown for severity-velocity at warm-up head dates | At 2021-10-18 (first phase date, within 5-snapshot warm-up window): tooltip shows "Severity velocity NA" — null value correctly displayed as NA | PASS | `UT-07-na-at-warmup.png` |
| UT-08 | Cross-view bottom pane phase bands span full history at a historical as-of | happy-path | P1 | Phase bands extend past the as-of vertical marker to the right | At `?asof=2022-10-07`: hover at 40% shows 2023-04-10 (Narrow leadership), 60% shows 2024-05-28 (Expansion), 75% shows 2025-04-04 (Bear), 85% shows 2025-10-29 (Expansion) — all past the marker | PASS | `UT-08-post-marker-hover.png` |
| UT-09 | Cross-view bottom pane renders honestly empty at a pre-history as-of | validation | P2 | Empty bottom pane; no fabricated phase bands | At `?asof=2021-01-04` (before phase history start of 2021-10-18): Market Phase card shows "Not enough history to derive a market phase for this date — reported NA, never fabricated." No phase tooltip data visible | PASS | `UT-09-2021-01-04.png` |
| UT-10 | Tooltip still shows P(bear) value on hover | regression | P1 | P(bear) row present in tooltip alongside severity-velocity | Tooltip at 2024-09-09 shows "P(bear) 0.02" — present alongside new "Severity velocity +1.25" row | PASS | `UT-06-tooltip-visible.png` |
| UT-11 | Cross-view synced panes share the same date axis | regression | P1 | Bottom pane date follows top pane cursor; same date at same horizontal position | Horizontal sweep yielded sequential dates 2022-09-14 → 2023-11-01 → 2024-12-19 at fracs 0.3/0.5/0.7 — tooltip date tracked cursor consistently | PASS | `UT-11-sync-pos1.png`, `UT-11-sync-pos2.png` |
| UT-12 | Market-Phase card still shows P(bear) unchanged | regression | P1 | Market Phase card shows P(bear) label and value; card not replaced | Page text: "Market Phase & Severity Expansion P(bear) 0.00 28.75 / 100 severity" — P(bear) present in compact card | PASS | `UT-12-market-phase-card.png` |
| UT-13 | "At a Glance" card still shows P(bear) and expand works | regression | P1 | At-a-Glance card shows P(bear); "More detail" expands; expanded view has P(bear) | `hasAtGlance=true`, `hasPBearInText=true`, `hasMoreDetail=true`; clicking "More detail" expanded successfully; P(bear) count=16 in expanded view | PASS | `UT-13-after-expand.png` |
| UT-14 | Dashboard has no native date input elements | regression | P1 | Zero `<input type="date">` elements on Dashboard | `native_date_inputs=0` confirmed via Playwright locator | PASS | none (programmatic check) |
| UT-15 | Severity-velocity feature is discoverable from the Dashboard | ux | P2 | Legend swatch visible without hover; tooltip shows signed velocity; dashed zero reference visible | Legend text "Severity velocity (0-centered; + = worsening)" present at all times; tooltip shows "+1.25" at 2024-09-09; zero reference line rendered via `createPriceLine` (dashed, title="0") | PASS | `UT-15-legend-visible.png` |
| UT-16 | Cross-view bottom pane at historical as-of does not show marker-truncated bands | ux | P2 | Phase bands extend visibly past as-of vertical marker | At `?asof=2022-06-01`: hover at 70% shows 2024-12-19 with "Pullback sev 43 P(bear) 0.05 Severity velocity +5.01" — well past the 2022-06-01 marker; no truncation | PASS | `UT-16-post-marker-hover.png` |

---

## Passed Tests

### UT-01 — Dashboard loads with a single market chart
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44-evidence/UT-01-result.png`
- Navigated to http://localhost:3835; page rendered without blank screen or spinner
- DOM eval confirmed `hasMajorIndexes=false`, `hasCrossView=true`
- "Regime × phase cross-view" heading visible; "Major indexes & regime" heading absent across full-page scroll

---

### UT-02 — Cross-view card renders both panes
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44-evidence/UT-02-chart-view.png`
- 11 canvas elements detected: top pane (left=269, top=441, w=1544, h=279), bottom pane (left=269, top=721, w=1544, h=140), shared x-axis (y=861, h=28)
- Lightweight-charts two-pane layout confirmed (each pane has main + overlay canvas)
- Neither pane showed a loading spinner; chart fully rendered with data

---

### UT-03 — MajorIndexesCard is absent from the Dashboard
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44-evidence/UT-01-result.png`
- Full-page text scan: no text matching "Major indexes" or "Major index" found anywhere on the page
- Only market chart visible is the "Regime × phase cross-view" two-pane card

---

### UT-04 — Cross-view bottom pane shows severity-velocity line with zero baseline
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44-evidence/UT-06-tooltip-visible.png`
- Page legend text confirms "Severity velocity (0-centered; + = worsening)" line present in bottom pane
- Source code `phase-cross-view-chart.tsx` confirms `velocitySeries.createPriceLine({price: 0, lineStyle: lwc.LineStyle.Dashed, title: "0"})` — dashed zero reference line rendered
- "Filtered P(bear)" absent from page text; the old P(bear) line was removed as required

---

### UT-05 — Cross-view chart legend shows "Severity velocity" label
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44-evidence/UT-15-legend-visible.png`
- DOM text eval: `hasSeverityVelocityLegend=true` — exact text "Severity velocity (0-centered; + = worsening)" present in legend
- `hasFilteredPBear=false` — no "Filtered P(bear)" swatch anywhere on page
- All other legend swatches (index names, regime bands, phase postures, Severity 0-100) confirmed present

---

### UT-06 — Cross-view tooltip shows regime label and severity-velocity on hover
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44-evidence/UT-06-tooltip-visible.png`
- Hovered at 65% across chart (2024-09-09 area); `role="status"` tooltip appeared within 1s
- Tooltip text: "2024-09-09 / SPY +55.88% / QQQ +50.19% / IWM +12.58% / RSP +45.08% / DIA +35.30% / Regime: Narrow leadership · 59/100 / Pullback sev 37 / P(bear) 0.02 / Severity velocity +1.25"
- All required rows present: date, index %, regime label+score, phase, severity, P(bear), severity-velocity

---

### UT-07 — Cross-view tooltip shows "NA" for severity-velocity at earliest dates
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44-evidence/UT-07-na-at-warmup.png`
- API confirmed `timeline_full` starts at 2021-10-18 with first 4 dates having `severity_velocity=null` (warm-up window of 5 snapshots)
- Hovering at 14% across chart (2021-10-18, first date with phase data): tooltip showed "Severity velocity NA" — null correctly rendered as "NA" not "0.00"

---

### UT-08 — Cross-view bottom pane phase bands span full history at a historical as-of
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44-evidence/UT-08-post-marker-hover.png`
- Navigated to `?asof=2022-10-07`; page confirmed "Viewing as-of 2022-10-07 (historical)" / "Bear P(bear) 1.00 92.45/100"
- Hovered at 40% (returned 2023-04-10 Narrow leadership), 60% (2024-05-28 Expansion), 75% (2025-04-04 Bear), 85% (2025-10-29 Expansion) — phase data present at all post-marker positions
- Phase bands extend full history; no truncation at the as-of marker

---

### UT-09 — Cross-view bottom pane renders honestly empty at a pre-history as-of
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44-evidence/UT-09-2021-01-04.png`
- Navigated to `?asof=2021-01-04`; page shows "Viewing as-of 2021-01-04 (historical)"
- Market Phase card: "Not enough history to derive a market phase for this date — reported NA, never fabricated."
- Phase timeline (`timeline_full`) starts 2021-10-18; at 2021-01-04 the bottom pane has no phase data to render — honest-empty state confirmed
- No fabricated phase coloring in bottom pane

---

### UT-10 — Tooltip still shows P(bear) value on hover
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44-evidence/UT-06-tooltip-visible.png`
- Same hover at 2024-09-09: tooltip contains "P(bear) 0.02" row
- P(bear) is present alongside (not replaced by) the new "Severity velocity +1.25" row

---

### UT-11 — Cross-view synced panes share the same date axis
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44-evidence/UT-11-sync-pos1.png`, `UT-11-sync-pos2.png`
- Horizontal sweep at fracs 0.3/0.5/0.7 returned dates 2022-09-14, 2023-11-01, 2024-12-19 in order — tooltip date tracked cursor linearly
- Single lightweight-charts instance with shared time scale confirmed in source: one `chart` instance with pane index 0 and 1, both referencing the same time scale

---

### UT-12 — Market-Phase card still shows P(bear) unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44-evidence/UT-12-market-phase-card.png`
- Page text: "Market Phase & Severity Expansion P(bear) 0.00 28.75 / 100 severity"
- Market Phase card displays P(bear) label and numeric value; card not replaced by any velocity component

---

### UT-13 — "At a Glance" card still shows P(bear) and expand works
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44-evidence/UT-13-after-expand.png`
- Page text confirms "at a glance", P(bear) visible in compact view, "More detail" button present
- Clicking "More detail": page expanded; P(bear) count increased to 16 occurrences in the expanded view
- No severity-velocity injection into this card

---

### UT-14 — Dashboard has no native date input elements
**Verdict:** PASS
**Evidence:** none (programmatic check)
- `page.locator('input[type="date"]').count()` returned 0
- As-of date selector uses custom component (aria-label="View as-of date" on a button; "Previous available date" / "Next available date" icon buttons)

---

### UT-15 — Severity-velocity feature is discoverable from the Dashboard
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44-evidence/UT-15-legend-visible.png`
- Without hovering: legend swatch "Severity velocity (0-centered; + = worsening)" visible in the chart legend at all times
- On hover: tooltip rows include "Severity velocity +1.25" with explicit sign prefix
- Dashed zero reference line rendered via `createPriceLine` (confirmed in source); visually anchors positive=worsening / negative=easing interpretation

---

### UT-16 — Cross-view bottom pane at historical as-of does not show marker-truncated bands
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44-evidence/UT-16-post-marker-hover.png`
- Navigated to `?asof=2022-06-01`; as-of marker at ~25% of timeline
- Hovered at 70% (2024-12-19): tooltip shows "Pullback sev 43 P(bear) 0.05 Severity velocity +5.01" — phase data present well past the 2022-06-01 marker
- No abrupt cutoff at marker position confirmed

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend URL:** http://localhost:8835
- **Browser:** Playwright Chromium (headless) + Chrome MCP
- **Test Date:** 2026-06-22
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44-evidence/`
- **Phase timeline coverage:** 1171 dates (2021-10-18 to 2026-06-16) from `timeline_full` field in `/api/market-phase?full=true`
- **Null velocity (warm-up) dates:** 4 (2021-10-18 to 2021-10-21)
