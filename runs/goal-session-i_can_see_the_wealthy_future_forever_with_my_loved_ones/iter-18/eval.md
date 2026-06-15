# Iteration 18 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

Iter-18 is the lean live browser-QA re-verification of J-74 (multi-hue availability heatmap) and J-76 (price-chart per-bar hover box) — code shipped + source-verified in iter-17, which only lacked live evidence because Chrome was down. The env came up this iteration (backend :8835, frontend :3835, Chrome :9222 — confirmed live by the genuine 09:57–10:20 captures), browser-QA ran 9/9 PASS, and the `apps/` diff is empty (no code change). Both targets upgrade `unknown → passing`; this is NOT a GOAL_ACHIEVED candidate because the appended J-72..J-78 extension still has five unbuilt journeys (J-72, J-73, J-75, J-77, J-78 — all explicitly NOT data-dependent per goal.md:2093).

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-76 | unknown | passing | reports/qa/.../iter-18-evidence/J-76-hover-inrange-final.png (082d8867) + J-76-hover-forward-final.png (3e0a7414) — both evaluator-viewed, byte-distinct, full-viewport |
| J-74 | unknown | passing | reports/qa/.../iter-18-evidence/J-74-cell-click-asof-unchanged.png (9b3427ed, live /data, J-18) + QA live computed-CSS extraction (6 distinct rgb hues == committed hex) |
| J-61 | passing | passing | live: 1356 cells from GET /api/data/availability, aria-label "2026-05-01: 159 of 159 symbols, snapshot yes" |
| J-70 | passing | passing | live: descending months 2026-05→2021-01, sm/md/lg:grid-cols-2 two-up, light text on all buckets |
| J-20 | passing | passing | reports/qa/.../iter-18-evidence/J-20-NVDA-full-path-asof-marker.png (d75da940) — evaluator-viewed, full path through 2026-05-28 + as-of marker |
| J-45 | passing | passing | regime bands behind NVDA chart (same capture as J-20), Risk-on label, Regime toggle |
| J-42 | passing | passing | 0 locale dates; hover-box dates 2023-09-15 / 2026-03-27 yyyy-MM-dd |
| J-05 | passing | passing | NVDA detail: three scores + A–E buckets + setup/reason/invalidation/theme |
| J-06 | passing | passing | reports/qa/.../iter-18-evidence/J-06-leaderboard-NVDA-scores.png (a61132bc) — leaderboard D63.22/B80.58/E31.22 == detail D63/B80/E31 |
| J-18 (critical invariant) | passing | passing | live cell-click kept URL /data + as-of "Latest"; asof-provider/switcher/calendar byte-untouched (last touched c639e57/iter-16) |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No lookahead | OK | J-76 forward bar (2026-03-27) labelled "after as-of (display only)"; scores stay on the ≤D 2026-01-15 snapshot; backend diff empty |
| No recompute in read path | OK | Hover box reads already-served bars/MA arrays (no extra request); heatmap re-renders same GET /api/data/availability payload |
| Single source of truth | OK | J-06 leaderboard==detail NVDA scores; no code change to scoring/read path |
| No magic numbers | OK | Heat scale is design tokens (--heat-0..5 the ONLY hex source in globals.css; tailwind heat/heat-text tokens; no per-cell hex — source-verified) |
| No fabricated data | OK | Hover box renders absent MA as "NA" (price-chart.tsx:372,394 source-confirmed); heatmap empty day = lowest bucket hue, never filled |
| Exactly one date selector (critical) | OK | Cell-click → onPrefillRange (job form) only, zero setAsOf in availability-heatmap.tsx; price-chart hover box holds no date state (only useState is the hover detail) |

## Evidence-hygiene defect (recorded, not verdict-changing)

The recurring blank-PNG / byte-dup capture failure struck again on exactly the J-74 surface that needed the visual:
- `J-74-heatmap-final-legend-grid.png` and its md5 cluster (6608b338: heatmap-scroll2000, heatmap-section, heatmap-two-up-months, legend-and-heatmap) are 5742-byte **fully blank** dark frames.
- `J-74-fullvp-heatmap-with-legend.png` (e47d8c28) and `J-74-cell-focused-tooltip-visible.png` (716468eb) show the per-symbol coverage TABLE / the top app bar — NOT the multi-hue heatmap grid, legend, or day numbers.
- So there is **no live screenshot frame showing the rendered multi-hue cells / legend / per-bucket day numbers**, contrary to the spec's Definition of Done ("distinct, full-viewport, md5-verified screenshots — one per claimed surface").

Why J-74 is still scored `passing` despite the blank frames: the substantive J-74 claim is positively evidenced by **live DOM computed-CSS extraction** that could only come from a running render — the QA report's six per-bucket rgb values match the committed `--heat-0..5` hex to the digit (e.g. bucket 5 rgb(240,180,41) == #f0b429; bucket 0 rgb(43,52,69) == #2b3445), plus 1357 live snapshot-ring cells, live aria-labels, and the genuine live /data J-18 capture. I independently re-derived every claim against the committed source (globals.css heat tokens, BUCKET_CLASS/BUCKET_TEXT_CLASS, legend map, onPrefillRange-only cell-click). This matches how prior iterations (3/7/9) accepted DOM/CSS-corroborated passes when screenshot frames degraded, provided the live extraction independently proved the claim. The defect is a capture-tooling failure, not a render failure — but it must not recur (see lesson).

## Next-Step Recommendation

CONTINUE. Both target journeys are now passing; the J-72..J-78 extension still has five unbuilt, NON-data-dependent Must-haves: J-72 (research perf+cache, byte-identical), J-73 (no as-of date-flash via synchronous URL hydration), J-75 (forward returns 1/5/10/20/60-day on /stocks + detail from the stored forward_returns table), J-77 (regime×setup×pattern ranked combinations study), J-78 (dashboard major-indexes defaults to All).

Per the standing plan: iter-19 **lean** — J-78 (one-line `config.yaml` `index_chart.default_range` 6M→All, ~line 305) bundled with J-73 (synchronous `?asof` URL hydration — this touches `asof-provider.tsx`, the J-18/J-43/J-50 invariant core; handle with care and re-smoke J-18/J-43/J-50). Then the backend cluster J-72 / J-75 / J-77 at **full** depth (J-72 has a hard byte-identity guard on cached vs uncached figures; J-75 reads the stored `forward_returns` table — needs the no-lookahead/no-recompute gate; J-77 is a grouping of the SAME enriched event-study observation set, never a recompute, must stay count-coherent with the J-64/J-65/J-77 N= chips — full pipeline's audit step earns its cost there).

**Evidence-hygiene directive for iter-19 QA (do NOT skip):** md5sum the evidence dir first; for the heatmap, scroll the colored grid INTO the viewport and capture full-VIEWPORT (the blank-frame trap is on close-ups/zoomed captures — the surface is below the fold on /data); reject any heatmap PASS whose only frame is the per-symbol coverage table or a blank dark image. One distinct, pixel-verified capture per claimed surface.

## Halt Justification

N/A — not halting. Five tractable, non-data-dependent Must-haves (J-72/J-73/J-75/J-77/J-78) remain unbuilt; productive next work is clearly identifiable (CONTINUE, not STALLED). No prior-passing journey regressed and no anti-goal was violated (no code change this iteration), so not REGRESSION.
