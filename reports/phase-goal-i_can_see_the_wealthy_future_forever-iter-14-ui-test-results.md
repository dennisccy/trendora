# Phase goal-i_can_see_the_wealthy_future_forever-iter-14 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-14
**Date:** 2026-06-02
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->

**Overall:** 14/15 tests passed (1 skipped — UT-07 not reproducible with current seed, acceptable per the test plan)

All 8 P1 tests (UT-01, UT-02, UT-03, UT-04, UT-05, UT-11, UT-13, UT-14) **passed**. The single SKIP is the explicitly-allowed "no zero-occurrence subject exists in this seed" case (P2).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Research page loads with event-study section | smoke | P1 | Page renders; `event-study-section` panel with Subject selector + per-horizon table + by-regime + by-sector panels visible | All 6 testids present (`event-study-section`, `subject-select`, `event-study-horizon-table`, `event-study-regime-table`, `event-study-sector-table`, `horizon-select`); page rendered without error page | PASS | `UT-01-research-loaded.png` |
| UT-02 | Data-rich SETUP renders full per-horizon table | happy-path | P1 | One row per horizon, 11 columns in order, real numbers (not NA), meta "Breakout-watch (setup)" + pooled count | 5 rows (1/5/10/20/60d), all 11 columns in exact order, all n=99 with real %/ratios, meta "Subject: Breakout-watch (setup) … Pooled occurrences (20d): 99" | PASS | `UT-02-03-breakout-watch.png` |
| UT-03 | Best exit-horizon highlighted exactly once | happy-path | P1 | Exactly one "best exit" badge on a populated row; matches "Best exit-horizon" meta | Single `best exit` badge on the **60d** row (shaded `bg-surface-2`), row is populated (n=99, +8.47%); meta "Best exit-horizon: 60d" matches | PASS | `UT-02-03-breakout-watch.png` |
| UT-04 | Subject selector grouped Setups/Patterns | happy-path | P1 | Two optgroups; Setups = 6 setups, Patterns = VCP/Pullback-to-DMA/Flat-base; no "Loading…" | optgroup "Setups" [Actionable, Breakout-watch, Pullback-watch, Extended, Avoid, Risk-off-watchlist], optgroup "Patterns" [VCP — Volatility Contraction Pattern, Pullback to a rising DMA, Flat-base breakout]; default value "Actionable" (no Loading…) | PASS | `UT-01-research-loaded.png` |
| UT-05 | PATTERN subject re-points to distinct values | happy-path | P1 | Meta "Pullback to a rising DMA (pattern)"; table + regime + sector values change | Meta "Pullback to a rising DMA (pattern)", Pooled 163 (vs 99); 60d Mean +2.45% (vs +8.47%); regime Risk-on n=124 (vs 65); sector Technology n=63 (vs 36) | PASS | `UT-05-pullback-pattern.png` |
| UT-06 | Low-sample subject → NA + n | validation | P2 | Low-sample rows render literal "NA"; honest n with warning chip; meta NA note | VCP (n=27<30): every metric cell "NA", honest "n=27 ⚠" chip per row, "Best exit-horizon: NA", meta "Rows with n < 30 ⚠ render NA." (default Actionable n=2 ⚠ identical behaviour) | PASS | `UT-06-vcp-lowsample-NA.png` |
| UT-07 | Zero-occurrence subject → empty state | validation | P2 | Empty-state card for a 0-occurrence subject | **Not reproducible** — every selectable subject has ≥1 occurrence in this seed (smallest: Actionable n=2, Pullback-watch n=3). Plan explicitly allows marking this case "not reproducible". Empty-state code path verified present in source (`page.tsx` `!hasAny` → "No forward-tested occurrences for this subject"). | SKIP | n/a |
| UT-08 | By-regime: row per regime, ≥1 NA | validation | P2 | Title "By market regime (Hd)"; cols Regime/n/Mean/Hit-rate/Risk-adjusted; one row per regime; ≥1 NA | Title "By market regime (20d)"; correct 5 columns; 6 rows (one per configured regime); n=0 regimes (Strong risk-on / Defensive / Risk-off) render NA + "n=0 ⚠"; low-n regimes (Narrow leadership n=16, Choppy n=18) also NA | PASS | `UT-02-03-breakout-watch.png` |
| UT-09 | By-sector: members-only | validation | P2 | Title "By sector (Hd)"; cols Sector/n/Mean/Risk-adjusted; members only; low-sample sector → NA | Title "By sector (20d)"; correct 4 columns; 9 member sectors only (no padded empties); Utilities n=2 ⚠ → NA; only Technology n=36 shows numbers | PASS | `UT-02-03-breakout-watch.png` |
| UT-10 | Caveat banner inside section | ux | P2 | Survivorship + descriptive caveats; "no date control / J-18" note | Banner heading "Survivorship bias · universe-relative · descriptive"; survivorship text + "Descriptive evidence, not a predictive model" both present; "Re-uses the page's shared horizon selector above. No date control — a cross-date aggregate over every stored snapshot (J-18)." present | PASS | `UT-05-pullback-pattern.png` |
| UT-11 | Shared Horizon re-points panels | happy-path | P1 | Panel titles + values update to chosen horizon; no second horizon/date control in section | Click 20d→60d: titles → "By market regime (60d)" / "By sector (60d)"; meta → "Pooled occurrences (60d): 99"; Risk-on regime +4.33% (vs +1.74% at 20d); only `<select>` inside section is `subject-select` | PASS | `UT-11-horizon-60d-repoint.png` |
| UT-12 | Backend-unavailable error state | error | P2 | Red "Backend unavailable" block; no fabricated/blank table | Simulated event-study fetch failure → "Backend unavailable" + "The event study could not load from the API. No figures are shown rather than fabricated values…"; no distribution table rendered | PASS | `UT-12-backend-unavailable-error.png` |
| UT-13 | As-of toggle byte-identical (J-18) | regression | P1 | Event-study tables identical before/after as-of toggle; ideally no `as_of` request | Toggled Latest→2025-05-28 (badge "Viewing as-of 2025-05-28 (historical)"): all 3 tables **byte-identical**; fetch recorder shows **zero** `/api/research/event-study` requests on toggle (only `/api/health`), so none carried `as_of` | PASS | `UT-13-asof-historical-byteidentical.png` |
| UT-14 | Factor + Combination labs still render | regression | P1 | Factor Lab re-points on factor change; Combination Lab renders; order Factor→Combination→Event Study | Decile table re-pointed (D1 "2.15…19.00 +1.73%"→"0.40…0.75 +3.47%"); meta "Factor: Relative strength vs SPY (3m)… Observations: 1217"; `combination-table` renders (Baseline n=1217 +2.03%); DOM order confirmed (idx 399 < 3371 < 5093) | PASS | `UT-14-factor-combination-labs.png` |
| UT-15 | Research discoverable from sidebar | ux | P3 | Sidebar "Research" link with microscope icon → /research | Sidebar link text "Research", `href="/research"`, icon class `lucide-microscope`; clicking navigated to `http://localhost:3835/research` with the event-study section present | PASS | `UT-15-sidebar-research-nav.png` |

---

## Passed Tests

### UT-01 — Research page loads with the new event-study section
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-14-evidence/UT-01-research-loaded.png`
- `/research` rendered. All six expected testids present in the DOM: `event-study-section`, `subject-select`, `event-study-horizon-table`, `event-study-regime-table`, `event-study-sector-table`, `horizon-select`.
- Section title "Setup & Pattern Lab — event study" visible below the Factor Lab and Combination Lab.
- Console note: this Chrome MCP build does not capture console logs ("TODO: Console logging not yet implemented"), so a programmatic "no console errors" assertion was not possible. The full render of every element and the success of all subsequent interactions are strong evidence of no fatal JS error.

### UT-02 — Data-rich SETUP subject renders the full per-horizon table
**Verdict:** PASS
**Evidence:** `…/UT-02-03-breakout-watch.png`
- Selected "Breakout-watch" (Setups group). Horizon table headers, in order: Horizon, n, Mean, Median, % Positive, Dispersion, Expectancy, Mean MAE, Mean MFE, Return / downside-dev, Return / MAE.
- 5 rows (1d, 5d, 10d, 20d, 60d), every cell populated with real values (e.g. 60d Mean +8.47%, Median +2.03%, %Pos +53.54%, Return/downside-dev +0.77), all n=99 — no literal "NA".
- Meta: "Subject: Breakout-watch (setup) · Pooled occurrences (20d): 99".

### UT-03 — Best exit-horizon highlighted exactly once
**Verdict:** PASS
**Evidence:** `…/UT-02-03-breakout-watch.png`
- Exactly one row carries the accent-bordered "best exit" pill — the **60d** row — and that row alone has the shaded `bg-surface-2` background.
- Meta "Best exit-horizon: 60d" matches the badged row. The badged row is populated (n=99), not an NA/low-sample row.

### UT-04 — Subject selector is config-driven with grouped Setups / Patterns
**Verdict:** PASS
**Evidence:** `…/UT-01-research-loaded.png`
- Two `<optgroup>`s. **Setups**: Actionable, Breakout-watch, Pullback-watch, Extended, Avoid, Risk-off-watchlist (all 6). **Patterns**: VCP — Volatility Contraction Pattern, Pullback to a rising DMA, Flat-base breakout.
- Default selected value is "Actionable"; no "Loading…" placeholder remained.

### UT-05 — PATTERN subject re-points the study to distinct values
**Verdict:** PASS
**Evidence:** `…/UT-05-pullback-pattern.png`
- Selected "Pullback to a rising DMA" (Patterns). Meta now "Pullback to a rising DMA (pattern)", Pooled occurrences (20d): 163.
- Per-horizon values changed vs Breakout-watch (e.g. 60d Mean +2.45% vs +8.47%; n=163 vs 99). By-regime (Risk-on n=124 +2.09%) and by-sector (Technology n=63 +1.19%) both re-pointed.

### UT-06 — Low-sample subject renders honest NA + n
**Verdict:** PASS
**Evidence:** `…/UT-06-vcp-lowsample-NA.png`
- Selected "VCP" (n=27, below the 30 minimum). Every metric cell (Mean/Median/% Positive/Dispersion/Expectancy/Mean MAE/Mean MFE/both ratios) renders literal "NA" — no fabricated number.
- The "n" column keeps the honest sample size with the low-sample chip "n=27 ⚠" on every row; "Best exit-horizon: NA"; meta "Rows with n < 30 ⚠ render NA."
- Corroborated by the default subject Actionable (n=2 ⚠) which showed identical all-NA behaviour on first load.

### UT-08 — By-regime panel emits a row per configured regime with ≥1 NA cell
**Verdict:** PASS
**Evidence:** `…/UT-02-03-breakout-watch.png`
- Title "By market regime (20d)"; columns Regime, n, Mean, Hit-rate, Risk-adjusted (downside).
- 6 rows — one per configured regime (Strong risk-on, Risk-on, Narrow leadership, Choppy, Defensive, Risk-off). The three n=0 regimes render NA with "n=0 ⚠"; only Risk-on (n=65) shows real numbers (+1.74% / +61.54% / +0.25). No fabricated value for an empty regime.

### UT-09 — By-sector panel shows only sectors with members
**Verdict:** PASS
**Evidence:** `…/UT-02-03-breakout-watch.png`
- Title "By sector (20d)"; columns Sector, n, Mean, Risk-adjusted (downside).
- 9 sectors, all with ≥1 member (no padded empty/n=0 sector rows). The low-sample Utilities (n=2 ⚠) row renders NA; only Technology (n=36) shows numbers.

### UT-10 — Caveat banner renders inside the event-study section
**Verdict:** PASS
**Evidence:** `…/UT-05-pullback-pattern.png`
- Inside the section: banner heading "Survivorship bias · universe-relative · descriptive" with both the survivorship-bias paragraph and the descriptive ("not a predictive model") paragraph.
- The note "Re-uses the page's shared horizon selector above. No date control — a cross-date aggregate over every stored snapshot (J-18)." is present below the Subject selector.

### UT-11 — Shared Horizon selector re-points the by-regime / by-sector panels
**Verdict:** PASS
**Evidence:** `…/UT-11-horizon-60d-repoint.png`
- With Breakout-watch selected, clicked the shared Horizon 20d → 60d. Panel titles updated to "By market regime (60d)" / "By sector (60d)"; meta to "Pooled occurrences (60d): 99"; Risk-on regime value changed (+4.33% at 60d vs +1.74% at 20d).
- The only `<select>` inside the section is `subject-select` — there is no second horizon/date control; it reuses the page's shared `horizon-select` (Factor Lab's control).

### UT-12 — Backend-unavailable error state
**Verdict:** PASS
**Evidence:** `…/UT-12-backend-unavailable-error.png`
- The `/api/research/event-study` request was made to fail (client-side fetch override — the shared backend was left running and untouched). Changing the subject triggered the re-fetch.
- The section rendered the red-bordered "Backend unavailable" block with "The event study could not load from the API. No figures are shown rather than fabricated values — confirm the backend is running and adjust the subject to retry." No distribution/regime/sector table was rendered in the error state. App restored to healthy via reload afterward.

### UT-13 — As-of toggle leaves the event study byte-identical (J-18)
**Verdict:** PASS
**Evidence:** `…/UT-13-asof-historical-byteidentical.png`
- With Breakout-watch selected, captured the per-horizon / by-regime / by-sector table text. Toggled the global "View as-of date" from Latest to 2025-05-28; the amber "Viewing as-of 2025-05-28 (historical)" badge appeared.
- All three event-study tables were **byte-identical** before and after. A fetch recorder installed before the toggle captured **zero** `/api/research/event-study` requests on the as-of change (only `/api/health`), confirming the study does not refetch or time-travel and sends no `as_of` param. Subject selection was preserved.

### UT-14 — Factor Lab and Combination Lab still render after the new section
**Verdict:** PASS
**Evidence:** `…/UT-14-factor-combination-labs.png`
- "Research — Factor Lab" heading + decile table render at the top. Changing the Factor (Leadership → Relative strength vs SPY (3m)) re-pointed the decile table (D1 "2.15 … 19.00 +1.73%" → "0.40 … 0.75 +3.47%"; meta "Observations: 1217").
- The Multi-factor Combination cohort table (`combination-table`) renders (Baseline n=1217 +2.03%). DOM order confirmed: Factor Lab → Combination Lab → Setup & Pattern Lab (body-text indices 399 < 3371 < 5093). No layout break.

### UT-15 — Research feature is discoverable from the sidebar
**Verdict:** PASS
**Evidence:** `…/UT-15-sidebar-research-nav.png`
- The left sidebar has a "Research" link (`href="/research"`) carrying a microscope icon (`lucide-microscope`). Clicking it navigated to `http://localhost:3835/research` with the event-study section present. The event study lives within the discoverable Research page; no separate nav entry is expected (additive section by design).

---

## Failed Tests

None.

---

## Skipped Tests

### UT-07 — Zero-occurrence subject shows the honest empty state
**Verdict:** SKIPPED
**Reason:** Not reproducible with the current seed data — every selectable subject has ≥1 forward-tested occurrence (verified via the API: Actionable n=2, Breakout-watch n=99, Pullback-watch n=3, Extended n=45, Avoid n=827, Risk-off-watchlist n=242, VCP n=27, Pullback-to-rising-DMA n=163, Flat-base breakout n=48). The test plan explicitly states this is acceptable: *"If every selectable subject has at least one occurrence in this seed, mark this case 'not reproducible with current data' — that is acceptable."*

The empty-state code path is present and correct in source (`apps/frontend/app/research/page.tsx`: when `!hasAny` it renders the `EmptyState` titled "No forward-tested occurrences for this subject"), but cannot be exercised with the current seed. P2 — does not affect the verdict.

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend URL:** http://localhost:8835 (event-study endpoint `GET /api/research/event-study` returned 200 with data; note `/health` is a 404 — the live health route is `/api/health`)
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser` (Chrome DevTools Protocol)
- **Test Date:** 2026-06-02
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-14-evidence/`

### Notes / Caveats
- **Console capture unavailable:** this Chrome MCP build does not yet implement console-log capture, so UT-01's "no uncaught console errors" sub-assertion could not be checked programmatically. Mitigation: every element rendered and every interaction (subject change, horizon change, factor change, as-of toggle, navigation) succeeded — strong evidence of no fatal client error. Not counted as a failure.
- **UT-12 method:** the error state was induced via a client-side `window.fetch` override scoped to the event-study URL (then removed via reload), rather than stopping the shared backend on port 8835 — non-destructive and leaves the environment healthy for subsequent agents.
- **Data-honesty observation:** across all subjects, low-sample/empty cohorts consistently rendered "NA" + honest n (with a ⚠ chip) and never a fabricated number — the central anti-goal guardrail for this iteration held in every table (per-horizon, by-regime, by-sector) and in the error state.
