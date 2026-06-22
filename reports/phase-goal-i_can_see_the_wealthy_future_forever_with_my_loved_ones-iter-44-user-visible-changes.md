# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-44
**Date:** 2026-06-22
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now see market stress momentum at a glance on the Dashboard: the cross-view chart's bottom pane draws a zero-centered "severity velocity" line — above the dashed zero means stress is worsening, below means it is easing.
- Users can now read the stored market-regime label and its 0–100 score for any hovered date directly in the cross-view chart tooltip, without leaving the Dashboard.
- Users can now see the full stored history of market-phase bands in the cross-view bottom pane at any historical "as-of" date — selecting an older date only moves the vertical marker; the phase coloring no longer truncates at the marker.

---

## What Changed in the Visible UI

- **Dashboard `/` — card removed:** The standalone "Major indexes & regime" card no longer appears on the Dashboard. The two-pane "Regime x phase cross-view" card (already present above it) renders the same index lines and regime bands, so nothing is lost — the layout is now one card shorter.
- **Cross-view chart bottom pane — line replaced:** The bottom pane previously drew a "Filtered P(bear)" probability line. It now draws a zero-centered "severity velocity" line with a dashed zero reference. The line uses the accent color; points above zero indicate worsening stress, points below zero indicate easing.
- **Cross-view chart legend — label updated:** The legend swatch previously labeled "Filtered P(bear)" is now labeled "Severity velocity (0-centered; + = worsening)".
- **Cross-view hover tooltip — two new rows added:** When hovering over any date on the cross-view chart, the tooltip now shows two additional rows: the market-regime label with its 0–100 score, and the severity-velocity value (formatted as +X.XX or -X.XX, or "NA" at the earliest dates where there is not yet enough history to measure a slope). All existing tooltip rows (date, index %, phase, severity, P(bear)) are still present.
- **Cross-view bottom pane — phase bands now span full history:** At a historical as-of date, the phase color bands in the bottom pane now extend across the full stored history. Previously the bands stopped at the selected as-of date; now the selected date is marked only by a vertical line while the bands continue past it as display-only context.

---

## What Old Behavior Changed

- **Cross-view bottom pane line:** Previously plotted the filtered P(bear) probability as a line overlay. Now plots the zero-centered severity-velocity line. The P(bear) numeric value is still shown on hover in the tooltip — only the plotted line was replaced.
- **Cross-view phase bands at a historical date:** Previously the phase bands in the bottom pane were clipped to the as-of date. Now they span the full stored timeline at any as-of, with the as-of shown as a vertical marker only.
- **Dashboard card count:** Previously the Dashboard showed two market charts side by side (the standalone Major-indexes card and the cross-view card). Now only the cross-view card is shown.
- **Severity-velocity NA at earliest dates:** For the first few dates in the stored history (where fewer than 5 prior snapshots exist), the severity-velocity line does not yet begin and the tooltip shows "NA" for that value. This is intentional — no fabricated slope is shown.

---

## Not Visible Yet

- The severity-velocity signal has no corresponding forward-return research study yet — that analysis (J-103, studying severity-velocity x regime x forward returns) is scheduled for the next iteration (iter-45) and will surface on a new `/research/severity-velocity` page.
- The research section's performance and page-split work (J-104) is also deferred to iter-45; the Research page is unchanged this iteration.
