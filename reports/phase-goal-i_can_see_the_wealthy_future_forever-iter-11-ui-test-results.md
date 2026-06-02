# Phase goal-i_can_see_the_wealthy_future_forever-iter-11 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-11
**Date:** 2026-06-02
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 11/12 tests passed (1 N/A-skipped; 0 failed)

All 7 P1 tests pass (UT-01, UT-02, UT-03, UT-06, UT-07, UT-08, UT-09). UT-10 is N/A (the
`n_total === 0` empty state is not reachable in the current dataset — the gate logic was verified
present in code instead). No smoke, happy-path, or P1 test failed.

---

## Methodology

Each test was executed in Chrome via MCP against the running frontend (`http://localhost:3835`,
targeting backend `http://localhost:8835` — confirmed via the frontend process env
`NEXT_PUBLIC_API_URL=http://localhost:8835`). For every numeric assertion the rendered DOM text was
cross-checked against the raw `/api/research/factor-lab` payload to confirm the UI **re-formats** the
backend values and never fabricates them. Re-point and as-of behaviour was verified by reading the
browser `performance.getEntriesByType('resource')` request history (full URLs incl. query params).
Screenshots are full-page captures.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Research page loads | smoke | P1 | Heading + caveat banner + Factor/Horizon controls render, no error | Heading "Research — Factor Lab", amber caveat "Survivorship bias · universe-relative · descriptive", Factor dropdown (8 options) + Horizon group (1d/5d/10d/20d/60d, 20d active) all present; no error card | PASS | `UT-01-02-research-loaded.png` |
| UT-02 | Regime table renders (6 rows, 7 cols) | smoke | P1 | Table titled "Factor effectiveness by market regime", 7 columns, 6 regime rows in order, every row an `n=<num>` chip | Exactly 7 headers in order (Regime, n, Rank-IC, Top-decile mean, Bottom-decile mean, Spread (top − bottom), Risk-adjusted spread); exactly 6 rows in order (Strong risk-on, Risk-on, Narrow leadership, Choppy, Defensive, Risk-off); n chips n=0/n=732/n=122/n=122/n=0/n=242 | PASS | `UT-01-02-research-loaded.png` |
| UT-03 | High-sample regime numeric | happy-path | P1 | A regime with n≥30 (no ⚠) shows signed numeric Rank-IC, Top/Bottom-decile mean, and Spread (not NA) | At 5d, Risk-on (n=732, no ⚠) → Rank-IC +0.04, Top −0.05%, Bottom −0.03%, Spread −0.02% (all signed numeric). Risk-off (n=242) & Narrow leadership (n=122) also numeric. Matches backend exactly | PASS | `UT-03-highsample-5d.png` |
| UT-04 | Low-sample regime NA + n | validation | P2 | Low-sample row's Rank-IC/Spread/Risk-adjusted render literal "NA"; n column shows honest count incl. n=0; NA tooltip present | At 60d, Strong risk-on & Defensive (n=0 ⚠) → all metric cells render muted "NA"; n chip shows honest `n=0 ⚠`; NA-cell `title` = "Low sample — n below the minimum; NA, not a fabricated number" | PASS | `UT-04-lowsample-NA-60d.png` |
| UT-05 | Risk-adjusted NA vs numeric spread | validation | P2 | A row exists where raw Spread is numeric but Risk-adjusted spread is "NA" (downside-only honesty) | At up_down_vol/20d, Risk-off (n=242, NOT low-sample) → Spread **+16.50%** (numeric) but Risk-adjusted spread **NA** (tooltip "No value for this regime"); matches backend (spread=0.165, risk_adjusted=null) | PASS | `UT-05-riskadj-NA-numeric-spread.png` |
| UT-06 | Re-point on factor change | happy-path | P1 | New factor-lab request with new factor param; regime + decile + rank-IC values change; no error | risk_score→up_down_vol fired `?factor=up_down_vol&horizon=60`; rank-IC card +0.15→+0.07, decile D1 range "23.02…36.19"→"0.29…0.76" (+1.69%→+9.96%), Risk-on regime spread +6.78%→−0.89%, Narrow leadership +55.63%→−17.05% | PASS | `UT-06-factor-changed-updownvol.png` |
| UT-07 | Re-point on horizon change | happy-path | P1 | New factor-lab request with new horizon; clicked button active; regime Spread/Rank-IC values update | 5d→60d clicks fired `?...&horizon=5` then `?...&horizon=60`; clicked button gets `aria-pressed="true"`; Risk-on spread −0.02%→+6.78%, Narrow leadership Rank-IC −0.34→+0.37, Risk-off spread −8.72%→−19.00%. (n chips are ~stable across horizons in this dataset — see note) | PASS | `UT-03-highsample-5d.png`, `UT-04-lowsample-NA-60d.png` |
| UT-08 | As-of switcher no effect (J-18) | regression | P1 | Decile + rank-IC + regime table identical before/after as-of change; zero requests carry `as_of` | as-of 2025-11-28→2025-08-28: badge changed to "Viewing as-of 2025-08-28 (historical)" but rank-IC, all 10 decile rows, and all 6 regime rows **byte-identical**; factor-lab request count unchanged (7, no new request fired); **zero** requests ever carried `as_of` | PASS | `UT-08-asof-no-effect.png` |
| UT-09 | Decile + rank-IC still work (J-25) | regression | P1 | Decile table (D1…D10, 4 cols) + rank-IC card present and re-point on factor change; no overlap/errors | Decile table: 10 rows D1…D10, columns Decile / Factor range / Mean fwd return / Risk-adjusted (downside); rank-IC card numeric; both re-pointed on factor change (UT-06). New regime panel sits cleanly below — no overlap | PASS | `UT-06-factor-changed-updownvol.png`, `UT-01-02-research-loaded.png` |
| UT-10 | Empty state, no fabricated table | error | P2 | When n_total=0: empty-state panel shown, no decile/rank-IC/regime tables | **Not reachable in current data** — swept all 8 factors × 5 horizons (1/5/10/20/60d): every combination has n_total ≥ 1217, none is 0. Gate logic verified in code: `FactorLab` returns `<EmptyState>` when `data.n_total === 0`; decile, rank-IC, and the new regime table all render only in the `n_total > 0` branch | SKIP (N/A) | code-verified (`page.tsx:196`) |
| UT-11 | Backend-down error card | error | P2 | Red "Backend unavailable" card; no decile/rank-IC/regime numbers; no fabricated NA rows; no crash | Simulated backend-down (factor-lab fetch forced to reject), then horizon change → error card "Backend unavailable — The Factor-Lab evidence could not load from the API. No figures are shown rather than fabricated values." Regime table, rank-IC, decile table all **absent**; **0 NA cells**; page did not crash (heading + caveat still render) | PASS | `UT-11-backend-down-error-card.png` |
| UT-12 | Discoverable + self-explaining | ux | P3 | Reachable in one sidebar click; panel hint explains purpose + NA convention | Sidebar "Research" click → `/research` (heading "Research — Factor Lab"); panel hint: "Does this factor still sort 20-day forward returns WITHIN each market regime? … regimes with n < 30 show NA + n, never a fabricated number." | PASS | `UT-12-discoverable-hint.png` |

---

## Passed Tests

### UT-01 — Research page loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-11-evidence/UT-01-02-research-loaded.png`
- Heading **"Research — Factor Lab"** rendered; amber caveat banner **"Survivorship bias · universe-relative · descriptive"** present.
- Factor dropdown (`data-testid="factor-select"`, 8 options) and Horizon button group (`data-testid="horizon-select"`: 1d/5d/10d/20d/60d, 20d `aria-pressed="true"`) both visible.
- No error card, no empty state, page fully rendered. (Browser console capture is not implemented by this MCP build; full render + absence of an error/empty state is used as the no-fatal-error proxy.)

### UT-02 — Regime table renders with all 6 regimes and 7 columns
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-11-evidence/UT-01-02-research-loaded.png`
- Header row, left→right: **Regime · n · Rank-IC · Top-decile mean · Bottom-decile mean · Spread (top − bottom) · Risk-adjusted spread** (exactly 7).
- Body rows top→bottom: **Strong risk-on, Risk-on, Narrow leadership, Choppy, Defensive, Risk-off** (exactly 6, correct order).
- Every row carries an `n=<number>` chip (n=0 ⚠, n=732, n=122, n=122, n=0 ⚠, n=242).

### UT-03 — A high-sample regime shows numeric rank-IC and spread
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-11-evidence/UT-03-highsample-5d.png`
- Clicked **5d**; the button became active and a `?factor=risk_score&horizon=5` request fired (whole page re-pointed: rank-IC card +0.04→−0.04).
- **Risk-on** (n=732, faint colour, no ⚠): Rank-IC **+0.04**, Top **−0.05%**, Bottom **−0.03%**, Spread **−0.02%** — all signed, none "NA".
- Backend cross-check (`?factor=risk_score&horizon=5`) matched the rendered values exactly → no fabrication.

### UT-04 — Low-sample regime renders honest "NA" with the true n
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-11-evidence/UT-04-lowsample-NA-60d.png`
- Clicked **60d**. **Strong risk-on** and **Defensive** both show `n=0 ⚠` and render the muted literal **"NA"** in Rank-IC, Top, Bottom, Spread, and Risk-adjusted spread — never blank, `0`, or `—`.
- NA-cell `title` attribute = **"Low sample — n below the minimum; NA, not a fabricated number"** (the test plan's expected tooltip).
- The honest count is preserved (`n=0`), confirming the table does not hide empty regimes. Backend cross-check matched.

### UT-05 — Risk-adjusted spread shows NA while raw spread is numeric
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-11-evidence/UT-05-riskadj-NA-numeric-spread.png`
- At **up_down_vol / 20d**, **Risk-off** (n=242, NOT low-sample, no ⚠): raw **Spread = +16.50%** (numeric) while **Risk-adjusted spread = NA**.
- The NA tooltip here is **"No value for this regime"** — distinct from the low-sample tooltip — correctly signalling the downside-only honesty case (no downside in the top decile ⇒ undefined ratio ⇒ NA, not a total-volatility number masquerading as downside-adjusted).
- Backend cross-check: `spread=0.165`, `risk_adjusted_spread=null` → exact match.

### UT-06 — Regime table re-points when the Factor changes
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-11-evidence/UT-06-factor-changed-updownvol.png`
- Changed Factor risk_score→up_down_vol; a `?factor=up_down_vol&horizon=60` request fired.
- Regime table changed (Risk-on spread +6.78%→−0.89%, Narrow leadership +55.63%→−17.05%), **and** the decile table (D1 range "23.02…36.19"→"0.29…0.76", mean +1.69%→+9.96%) and rank-IC card (+0.15→+0.07) re-pointed together. No error card.

### UT-07 — Regime table re-points and n chips update when the Horizon changes
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-11-evidence/UT-03-highsample-5d.png`, `UT-04-lowsample-NA-60d.png`
- 5d→60d: each click fired a new factor-lab request with the matching `horizon=` param; the clicked button became `aria-pressed="true"`.
- Regime Spread/Rank-IC values updated (Risk-on spread −0.02%→+6.78%, Narrow leadership Rank-IC −0.34→+0.37, Risk-off spread −8.72%→−19.00%), consistent with the simultaneously updated decile table.
- **Note (data-dependent):** the per-regime `n` chips are nearly stable across horizons in this seed dataset (e.g. Risk-on n=732 at both 5d and 60d; Narrow leadership 122→121) because forward-return observations exist for almost the same snapshots at every horizon (n_total 1218 at 5d vs 1217 at 60d). The test plan's "generally smaller counts at 60d → more ⚠" is therefore only minimally exercised, but the core re-point signal (values change + correct request fires + button active) is unambiguous.

### UT-08 — As-of switcher does NOT affect the Factor Lab (J-18)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-11-evidence/UT-08-asof-no-effect.png`
- Recorded full state, then changed the global top-bar as-of (2025-11-28 → 2025-08-28). Badge updated to **"Viewing as-of 2025-08-28 (historical)"**, confirming the global state changed.
- The rank-IC value, all **10** decile rows, and all **6** regime rows were **byte-identical** before and after (incl. the n=0 NA rows and the Risk-off +16.50%/NA cell).
- The factor-lab request count did **not** increase on the as-of change (no re-fetch), and **zero** `/research` requests carried an `as_of` param across the entire session. J-18 preserved.

### UT-09 — Existing decile table + rank-IC card still render and re-point (J-25)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-11-evidence/UT-06-factor-changed-updownvol.png`, `UT-01-02-research-loaded.png`
- Decile table present with rows **D1…D10** and columns **Decile / Factor range / Mean fwd return / Risk-adjusted (downside)**; rank-IC card (`data-testid="rank-ic-value"`) renders a numeric value.
- Both re-point on factor change (see UT-06). The new regime panel was added **below** the decile/rank-IC grid without displacing or overlapping them.

### UT-11 — Backend-down error card; no fabricated regime numbers
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-11-evidence/UT-11-backend-down-error-card.png`
- **Methodology note:** rather than physically stopping the shared QA backend on :8835 (which the harness keeps alive for the run), the exact error branch was reproduced non-destructively by forcing the page's `factor-lab` fetch to reject (simulated backend-unreachable) and then triggering a re-fetch via a horizon change. The rendered branch is identical to a real backend-down (`state.kind === "error"` ⇒ `data` becomes `null` ⇒ all tables unmount).
- Result: red **"Backend unavailable"** card with "The Factor-Lab evidence could not load from the API. No figures are shown rather than fabricated values…". The regime table, rank-IC card, and decile table are all **absent**; **zero** "NA" cells were rendered (no fabricated rows); the page did not crash to blank (heading + caveat still present).

### UT-12 — Regime table is discoverable and self-explaining
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-11-evidence/UT-12-discoverable-hint.png`
- From the dashboard, a single click on the **"Research"** sidebar link lands on `/research` (heading "Research — Factor Lab").
- The panel hint reads: *"Does this factor still sort 20-day forward returns WITHIN each market regime? Per configured regime: the rank-IC and the long-short (top-minus-bottom-decile) spread — raw and downside-risk-adjusted. A factor strong in the pooled table can be regime-dependent here; regimes with n < 30 show NA + n, never a fabricated number."* — purpose and the NA + n convention are both documented in plain language.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-10 — Empty state: no regime table fabricated when there are no observations
**Verdict:** SKIPPED (N/A — not reachable in current data)
**Reason:** A `(factor, horizon)` combination with `n_total === 0` is required to render the empty state. A backend sweep of all **8 factors × 5 horizons** (1d/5d/10d/20d/60d) found **no** combination with `n_total === 0` — every combination has `n_total ≥ 1217` in the current seed dataset (the longest horizon, 60d, still has realized forward returns for nearly every snapshot). The test plan explicitly permits marking this N/A when unreachable.
**Gate verified in code instead:** `FactorLab` (`apps/frontend/app/research/page.tsx:196`) returns `<EmptyState icon={Microscope} title="No forward-tested observations for this factor / horizon" …/>` when `data.n_total === 0`, and the decile table, rank-IC card, **and** the new `RegimeEffectivenessTable` (line 233) are all rendered only in the `n_total > 0` branch — so all three are gated together and none would be fabricated with zero observations.

---

## Non-blocking Observations

1. **Default factor on first load.** The page's no-param factor-lab request resolves the backend default to `leadership_score`, but the page settles on **`risk_score`** at first paint (the `performance` request log shows an early `?factor=risk_score` request issued during mount, alongside the no-param requests). The displayed data always matched the backend for whichever factor was shown, so this is not a fabrication or a J-27 regime-table defect; it is pre-existing factor-selector/initial-load behaviour (the selector shipped with J-25 in a prior iteration), not introduced by iter-11. Worth a glance from the dev/UX owner but does not affect any verdict here.
2. **UT-07 n-chip stability** — documented inline above; the seed dataset's forward observations are nearly horizon-independent, so per-regime `n` barely shifts across horizons. Re-point correctness is otherwise fully demonstrated.

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend URL:** http://localhost:8835 (frontend env `NEXT_PUBLIC_API_URL=http://localhost:8835`; `GET /api/research/factor-lab` → 200)
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser` (HeadlessChrome 146)
- **Viewport:** 1440×1100 (full-page screenshots)
- **Test Date:** 2026-06-02
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-11-evidence/`
