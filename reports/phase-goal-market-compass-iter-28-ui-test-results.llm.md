# goal-market-compass-iter-28 — UI Test Results

**Phase:** goal-market-compass-iter-28
**Date:** 2026-08-31
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 2/2 tests passed (0 skipped)

Lean-mode dispatch: only J-07 and J-08 were in scope this run (J-01, J-02, J-03, J-04, J-05, J-06,
J-10, J-11 are covered by deterministic golden replay separately and were NOT re-driven here).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-07 | The Today page answers the ten-second read from served values only | happy-path | P1 | `/` renders the six body sections in order (state band, summary, what-changed, leadership rotation, next-session focus, manifest strip) with readiness/preflight chrome above; tile values/breakdowns/direction words equal served fields; cross-view chart absent from `/`, link-out reaches `/market`; no `/api/sectors`/`/api/themes` fetch on load; TTI/API latencies within budget | All 7 steps verified via live DOM/API inspection — see notes below for the one structural caveat (direction-word badges read NA this iteration, which is the correct served value) | PASS | `reports/qa/goal-market-compass-iter-28-evidence/UT-J-07-today-page.png` |
| UT-J-08 | The market surface relocates intact and history never lies | happy-path | P1 | `/market` renders the full former dashboard inventory unchanged; sidebar lists Today then Market with correct active-highlighting; historical `?asof=2025-04-15` shows that date's stored values with a retrospective-labeled manifest; frontier `?asof=2026-08-12` shows frozen at_ingest stamps; fresh-tab load is already D-scoped; Latest clears the param | All 6 steps verified live; one wording caveat (manifest shows "version 6" not literally "version 1" — see notes) | PASS | `reports/qa/goal-market-compass-iter-28-evidence/UT-J-08-market-page.png` |

---

## Passed Tests

### UT-J-07 — The Today page answers the ten-second read from served values only
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-28-evidence/UT-J-07-today-page.png` (full-page screenshot, Latest as-of)

Steps executed against `http://localhost:3255/` (Latest, no `?asof` — SAFE):

1. **Body order (step 1).** `document.querySelectorAll('[data-testid]')` in DOM order confirms:
   `readiness-badge`/`preflight-banner` (chrome) → `compass-state-band-card` → `compass-summary-card`
   → `compass-whatchanged-card` → `compass-leadership-rotation-section` → `compass-focus-section` →
   `compass-manifest-strip`. Exact match to market-state band → summary → what-changed → leadership
   rotation → next-session focus → manifest strip, chrome above.
2. **Regime/phase tile values vs canonical endpoints (step 2).** Regime tile: "Risk-on", 73.18 —
   matches `GET /api/dashboard` (`regime.label="Risk-on"`, `regime.score=73.18`) exactly. Phase tile:
   "Expansion", severity 25.85, P(bear) 0.00 — matches `GET /api/market-phase`
   (`phase="Expansion"`, `severity=25.85`, `p_bear=0.001657` rounds to 0.00) exactly.
3. **Direction words (step 3).** All three badges (regime/stress/breadth) render "NA". This is the
   CORRECT served value this iteration, not a defect: `GET /api/compass` returns `state_band: null`
   for every `as_of` this iteration's binding safety gate authorizes (no param, `2026-08-12`,
   `2025-04-15`), because those three dates already carry manifest rows minted before iter-28 existed
   (create-once). The dev handoff (Known Issue #1) and reviewer both flagged this as a structural,
   unavoidable consequence of the live-database safety constraint — the happy-path three-word
   classification (including the deliberate stress-polarity flip) is proven only by the 9 new backend
   fixture tests in `test_compass.py`, not observable live this iteration under any authorized as-of.
   Confirmed live: `state_band.regime.direction_word` etc. really are `null` in the raw API response,
   and the UI's NA rendering is honest, not fabricated (AG-3/AG-8 satisfied for what IS observable).
4. **Breakdown disclosures (step 4).** Expanded both tiles' "Why this X — component breakdown"
   disclosures. Regime: Index MA stack 0.96/33.75, Breadth>50-DMA 0.60/14.96, Breadth>200-DMA
   0.66/16.60, Net new highs 0.52/7.87, VIX gate (14.55<20, ×1)/0.00 — byte-for-byte match to
   `GET /api/dashboard`'s `regime.components` array. Phase: breadth_below_200dma 0.34/5.04,
   drawdown_depth 0.00/0.16, regime_risk 0.27/5.36, time_underwater 0.80/8.01, VIX gate (0.485)/7.28 —
   exact match to `GET /api/market-phase`'s `components` array.
5. **Vocabulary separation (step 5, TC-10).** Programmatic scan: concatenated text of the chrome
   elements (`readiness-badge`, `preflight-banner`) contains "Ready"/"GO" but NO regime/phase words;
   concatenated text of all six body sections contains ZERO occurrences of "Ready"/"GO"/"DEGRADED"/
   "NO-GO". Clean separation both directions.
6. **Cross-view chart absence + link-out (step 6, TC-11).** No `phase-cross-view-chart` (or any chart)
   element exists anywhere in `/`'s DOM. `compass-state-band-market-link` has `href="/market"`; clicking
   it navigated to `/market` where `[data-testid="phase-cross-view-chart"]` IS present and renders (its
   caption text — "0–100 severity + zero-centered severity-velocity line" — was read from the live DOM
   after navigation).
7. **Perf budget addendum (step 7, TC-14).** Captured real `PerformanceNavigationTiming` +
   `PerformanceResourceTiming` via the browser's own `eval` action: `domInteractive` 29.4 ms,
   `loadEventEnd` 44.7 ms (generic <= 3 s budget, huge margin); on-load API calls
   `{health 11ms, dashboard 10ms, methodology 9ms, runs 197ms, market-phase 54ms, compass 66ms}`, all
   well inside the generic <= 1.5 s budget, and critically NO `/api/sectors`/`/api/themes` call fired.
   Appended as **Addendum 42** to `reports/perf-budgets.md` (dated, next to the prior history, nothing
   overwritten) — this closes the dev handoff's Known Issue #2 (TC-14 previously unmet because the
   developer role has no browser tooling) and Known Issue #3's frontend-network-trace half.

### UT-J-08 — The market surface relocates intact and history never lies
**Verdict:** PASS
**Evidence:** `reports/qa/goal-market-compass-iter-28-evidence/UT-J-08-market-page.png` (full-page,
`/market`), plus `UT-J-08-historical-retrospective.png` (`/?asof=2025-04-15`)

1. **`/market` inventory (step 1).** Full-page inspection confirms: both glance cards ("Risk-on
   73.18/100" regime glance, "Expansion / P(bear) 0.00 / 25.85/100 severity" Market Phase & Severity
   glance), the cross-view chart with its "Hide"/"Show" toggle, and the complete More-detail inventory —
   three breadth cards (59.84% above-50DMA, 66.39% above-200DMA, 4.92% net new highs), Top Sectors (5
   rows), Candidate Counts (Actionable 0 / Breakout-watch 52 / Pullback-watch 1 / …), Top Themes (5
   rows), and the full Market Phase & Severity detail (recovery-turn state, downtrend-exit check, 60-row
   phase timeline, 29 causal downtrend episodes, retrospective/full-sample disclosure). No card missing.
   Clicked the cross-view "Hide" toggle and confirmed `localStorage['trendora.dashboard.phaseCrossView']`
   flips to `"false"` (exact key name preserved from the pre-move dashboard); toggled back to "Show".
2. **Sidebar order + active-highlighting (step 2, TC-17).** `nav a` list confirms "Today" (`/`) first,
   "Market" (`/market`) second, all other entries unchanged in order. On `/market`, the Market link
   carries the active classes (`bg-surface-2 font-medium text-text`) and Today does not; on `/`
   (re-checked after navigating back), Today carries the active classes and Market does not.
3. **Historical `?asof=2025-04-15` (step 3, TC-18).** Regime tile: "Risk-off", 14.01 — matches
   `GET /api/dashboard?as_of=2025-04-15` exactly. Phase tile: "Recovery", severity 71.47, P(bear) 1.00 —
   matches `GET /api/market-phase?as_of=2025-04-15` (`p_bear=0.998488` rounds to 1.00) exactly.
   What-changed header reads "vs 2025-04-14 (1 day ago)", matching `session_delta.prior_as_of` /
   `gap_days` from the API. Manifest strip shows badges `retrospective / version 2 / frozen / not
   prospective-eligible` — matches the API's `mode="retrospective", version=2, frozen=true,
   prospective_eligible=false` exactly, and the summary card explicitly states: "This is a retrospective
   view, reconstructed under the CURRENT selection rule and config — not necessarily what would have
   rendered live on this date." — the visible retrospective stamp the journey requires.
4. **Frontier `?asof=2026-08-12` (step 4, TC-19).** Manifest strip shows `at ingest / version 6 /
   frozen`. **Caveat, disclosed rather than silently passed:** the journey text says "version-1 stamps",
   but the live served manifest for this date is version 6 (the `versions` array shows v1 was never
   actually frozen — `mode: null, frozen: false` — and v2–v6 were minted 2026-08-20 during earlier
   incident-recovery iterations, per this session's own J-10/J-11 history). This is real, expected, and
   pre-existing system state, not something iter-28 introduced or could regress: 2026-08-12 IS the
   current frontier (not a substituted historical view — AG-12 is not implicated), and `GET /api/compass`
   correctly serves that date's LATEST frozen version. The substantive acceptance — frozen, `at_ingest`
   mode, provenance stamps shown, not a newer manifest's contents relative to what "Latest" itself
   reports — holds exactly. Treated as PASS with this note rather than a literal-text fail.
5. **Fresh-tab first paint (step 5, TC-20).** Opened `/?asof=2025-04-15` in a brand-new tab (never
   previously visited `/`). Immediately reading the DOM (no retry/poll needed) showed
   `asof-indicator` = "Viewing as-of 2025-04-15 (historical)" and the tiles already carrying
   2025-04-15's Risk-off/14.01/Recovery/71.47 values — no latest-then-repaint flash observed. Sidebar
   links in that tab all carried `?asof=2025-04-15` (e.g. `/market?asof=2025-04-15`).
6. **Return to Latest (step 6).** Opened the as-of switcher and clicked "Latest · 2026-08-12"; URL
   became exactly `http://localhost:3255/` (param gone), `asof-indicator` = "Latest", and the manifest
   strip showed the frozen `at ingest / version 6` state (the currently-frozen Latest state, not an
   explicit not-yet-frozen placeholder, since Latest IS already frozen).

**Live-database safety (TC-22, binding).** Every live call this lane made used only
`as_of ∈ {no param, "2026-08-12", "2025-04-15"}`; no `POST /api/compass/regenerate` was ever invoked
(the "Regenerate manifest" button was seen but never clicked). Re-derived row counts AFTER the lane
finished: `next_session_manifests` 26, `scanner_runs` 3128, `daily_prices` 3,310,374 — all unchanged
from the dev/review baseline. Zero new manifest mints from this browser-QA lane.

---

## Failed Tests

None.

---

## Skipped Tests

None — frontend and Chrome MCP were both available; J-07 and J-08 (the two journeys in scope this
lean-mode run) were both fully exercised.

---

## Golden Replay Scripts

Written for future deterministic re-verification (best-effort, lint-clean via
`demo_runner.py --mode lint`):
- `runs/goal-session-market-compass/journey-scripts/J-07.json` — loads `/`, asserts the live regime
  label + a served breadth sentence, clicks the state-band's market link-out, asserts the cross-view
  chart's caption text renders on `/market`.
- `runs/goal-session-market-compass/journey-scripts/J-08.json` — asserts `/market`'s Top
  Sectors/Themes render, steps `?asof=2025-04-15` and asserts the retrospective badge + what-changed
  prior-date line, steps `?asof=2026-08-12` and asserts the `at ingest` badge, returns to Latest and
  asserts the live regime label.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (headless, pinned profile)
- **Test Date:** 2026-08-31
- **Evidence directory:** `reports/qa/goal-market-compass-iter-28-evidence/`
