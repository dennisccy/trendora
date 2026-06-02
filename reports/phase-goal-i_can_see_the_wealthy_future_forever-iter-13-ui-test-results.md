# Phase goal-i_can_see_the_wealthy_future_forever-iter-13 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-13
**Date:** 2026-06-02
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->

**Overall:** 13/13 tests passed (0 failed, 0 skipped)

- **P1 tests (all must pass):** UT-01, UT-02, UT-03, UT-04, UT-08, UT-10, UT-11 — **all PASS**.
- **Critical post-DB-regen gates:** UT-10 (Risk-Off → Actionable=0) and UT-11 (NVDA byte-identical leaderboard↔detail) — **both PASS**.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Factor Lab loads | smoke | P1 | Heading, amber caveat, Factor dropdown + Horizon toggle, decile table + Rank-IC render with data; no "Backend unavailable" | `/research` loaded: heading "Research — Factor Lab"; caveat title + both lines present; Factor select (default "Leadership score") + horizon `1d/5d/10d/20d*/60d`; decile table (10 rows) + Rank-IC card (`+0.00 n=1218`) rendered; error card absent | PASS | `UT-01-02-research-loaded.png` |
| UT-02 | Dropdown grouped, 4 Volatility entries | happy-path | P1 | Options under family sub-headings; "Volatility" group lists exactly 4 entries in order | optgroups = **Score / Momentum / Trend / Volatility** (not flat); Volatility group = exactly `ATR % (volatility level)`, `Historical volatility (HV)`, `Volatility contraction (VCP-style)`, `Downside volatility (semivol)`; no volatility entry outside the group | PASS | `UT-01-02-research-loaded.png` |
| UT-03 | HV re-points + header `volatility · lower better` | happy-path | P1 | Header `volatility · lower better`; numeric Rank-IC ≈ +0.03 + n; sentence references HV; decile re-populates | Header = `Factor: Historical volatility (HV) (volatility · lower better)`; Rank-IC `+0.03 n=1218`; sentence references "Historical volatility (HV)"; decile table re-populated for HV (10 rows, matches API) | PASS | `UT-03-hv-selected.png` |
| UT-04 | VCP decile raw + risk-adjusted + n | happy-path | P1 | Columns Decile/Factor range/Mean fwd return/Risk-adjusted (downside); D1–D10; signed % + signed ratio + per-row n; header correct | Header = `Factor: Volatility contraction (VCP-style) (volatility · lower better)`; 4 columns present; D1–D10; D1 `+5.85% / +0.89`, D4 `-0.98% / -0.10` (signed); every row has `n` chip; values match API | PASS | `UT-04-vcp-decile.png` |
| UT-05 | Downside semivol honest NA + n | validation | P2 | A cell shows literal "NA" (muted), not 0/blank; n chip beside it; tooltip "Low sample…/No observations"; downside-only risk | Deciles fully sampled at 20d (documented fallback → regime table): "Strong risk-on" & "Defensive" (n=0) rows show **NA** (muted) + `n=0 ⚠` chip; NA tooltip = "Low sample — n below the minimum; NA, not a fabricated number"; risk-adjusted column is downside-only (signed: D4 −0.06, D7 +0.93) | PASS | `UT-05-downside-regime-NA.png` |
| UT-06 | By-regime split + empty-regime NA | happy-path | P2 | One row per regime; ≥1 populated row numeric; ≥1 empty regime NA + n (not fabricated 0) | VCP regime table: 7 columns, 6 regime rows; 4 populated numeric (Risk-on −0.15/−6.25%, Risk-off +0.29/+15.99%, all match API); "Strong risk-on" & "Defensive" (n=0) show NA + `n=0 ⚠` | PASS | `UT-06-vcp-regime-split.png` |
| UT-07 | Caveat banner still visible | regression | P2 | Caveat card title + both lines remain visible with a new volatility factor | With "Downside volatility (semivol)" selected: caveat title "Survivorship bias · universe-relative · descriptive" + survivorship line + "Descriptive evidence, not a predictive model…" line all present and visible | PASS | `UT-07-caveat-downside.png` |
| UT-08 | As-of toggle does not re-point lab | regression | P1 | Factor-Lab decile + Rank-IC byte-identical before/after as-of change; no as_of request from lab | As-of changed Latest → 2025-04-04 (indicator → "Viewing as-of 2025-04-04 (historical)"); HV decile table (all 10 rows) + Rank-IC `+0.03 n=1218` **byte-identical** before & after. (Structural: `fetchFactorLab(factor, horizon)` carries no as_of param.) | PASS | `UT-08-asof-historical-lab-unchanged.png` |
| UT-09 | Factor switch re-renders, no stale data | regression | P2 | Decile/Rank-IC/regime re-render each selection; Rank-IC changes between factors; re-select ATR% returns original | Rank-IC sequence ATR% `-0.01` → HV `+0.03` → downside `+0.12` → ATR% `-0.01` (distinct, no frozen value); re-select ATR% returned byte-identical (Rank-IC `-0.01 n=1218`, D1 `+1.37% / +0.43`); decile + Rank-IC + 6-row regime re-rendered each time | PASS | `UT-09-atr-reselected.png` |
| UT-10 | Risk-Off Actionable=0 after regen | regression | **P1 (critical)** | Zero stocks "Actionable" under Risk-Off | Risk-Off run (as-of 2025-04-04): **all 122 rows "Risk-off-watchlist", Actionable = 0**; regime banner "Risk-off regime gates every name to watchlist-only — no Actionable setups while the market is risk-off." | PASS | `UT-10-riskoff-actionable-zero.png` |
| UT-11 | NVDA scores byte-identical across views | regression | **P1 (critical)** | Leadership 47.48/E, Entry Quality 66.24/D, Risk 33.79/E identical on leaderboard & detail | Leaderboard NVDA row = `E 47.48 / D 66.24 / E 33.79`; detail = `Leadership E 47.48 / Entry Quality D 66.24 / Risk E 33.79` — **byte-identical**, matching expected exactly | PASS | `UT-11-12-nvda-detail.png`, `UT-11-leaderboard-top.png` |
| UT-12 | Volatility values not on detail breakdown | ux | P3 | hv/vcp_contraction/downside_vol NOT displayed on `/stocks/NVDA`; 3 scores match leaderboard | No "Historical volatility", "Downside volatility", "semivol", "VCP-style", `vcp_contraction`/`downside_vol` keys, or new-factor values anywhere on detail. Score cards show only pre-existing components (incl. legit `Volatility contraction` = −ATR entry-quality component, and `ATR %` risk component). 3 scores match leaderboard | PASS | `UT-11-12-nvda-detail.png` |
| UT-13 | Volatility family discoverable | ux | P3 | 4 volatility measures collected under one "Volatility" sub-heading; self-describing labels | The 4 measures appear under a single `<optgroup label="Volatility">`; labels self-describing (`ATR % (volatility level)`, `Historical volatility (HV)`, `Volatility contraction (VCP-style)`, `Downside volatility (semivol)`) | PASS | `UT-01-02-research-loaded.png` |

---

## Passed Tests

### UT-01 — Factor Lab page loads without errors (smoke)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-13-evidence/UT-01-02-research-loaded.png`
- `/research` rendered with heading **"Research — Factor Lab"**, the amber **"Survivorship bias · universe-relative · descriptive"** caveat card (both lines), the **Factor** dropdown (default "Leadership score") and **Horizon** toggle (`1d / 5d / 10d / 20d*(active) / 60d`).
- Decile table ("Decile sort — raw & downside risk-adjusted", D1–D10 populated) and Rank-IC card (`+0.00 n=1218`) both rendered with data; the by-regime table rendered below.
- No "Backend unavailable" error card; no blank screen. (Note: console capture is not implemented in this Chrome MCP build — see Environment notes — so console-error absence is inferred from the clean render + absent error card.)

### UT-02 — Factor dropdown grouped by family with a 4-entry Volatility group (happy path)
**Verdict:** PASS
**Evidence:** `…/UT-01-02-research-loaded.png` (grouping read from live DOM)
- `<select data-testid="factor-select">` options are organized under `<optgroup>` family sub-headings: **Score**, **Momentum**, **Trend**, **Volatility** — not a flat list.
- The **Volatility** group lists exactly four entries, in order: `ATR % (volatility level)`, `Historical volatility (HV)`, `Volatility contraction (VCP-style)`, `Downside volatility (semivol)`. No volatility entry appears outside the group.

### UT-03 — Selecting HV re-points the lab and shows correct header (happy path)
**Verdict:** PASS
**Evidence:** `…/UT-03-hv-selected.png`
- Factor header line = `Factor: Historical volatility (HV) (volatility · lower better)`.
- Rank-IC card = `+0.03` with `n=1218` chip (matches API +0.0276); explanatory sentence references "Historical volatility (HV)".
- Decile table re-populated for HV (10 rows; e.g. D9 `+5.53% / +0.63`, D1 `+0.35% / +0.08`) — did not stay on the previous factor.

### UT-04 — VCP-contraction decile table shows raw + downside-risk-adjusted columns with n (happy path)
**Verdict:** PASS
**Evidence:** `…/UT-04-vcp-decile.png`
- Columns: Decile / Factor range / Mean fwd return / Risk-adjusted (downside). Rows D1–D10.
- Signed mean (D1 `+5.85%`, D4 `-0.98%`) and signed risk-adjusted ratio (D1 `+0.89`, D4 `-0.10`); each row carries an `n` chip (121/122). Header = `Factor: Volatility contraction (VCP-style) (volatility · lower better)`. Values match API.

### UT-05 — Downside semivol risk-adjusted shows honest NA + n, never a fabricated 0 (validation)
**Verdict:** PASS
**Evidence:** `…/UT-05-downside-regime-NA.png`
- At the default 20d horizon all deciles are well-sampled (per the iter-11 lesson, NA is exercised via genuinely empty regimes, not horizon shrinkage). The "Factor effectiveness by market regime" table shows **"Strong risk-on"** and **"Defensive"** (n=0) rows with literal **NA** in muted grey across all numeric columns, each with an `n=0 ⚠` chip.
- NA tooltip = "Low sample — n below the minimum; NA, not a fabricated number"; n-chip tooltip = "Low sample — n below the 30 minimum; treat as indicative only".
- The decile risk-adjusted column is downside-only (signed values incl. negatives like D4 −0.06 and positives like D7 +0.93), never penalising healthy upside.

### UT-06 — By-regime split renders for a new factor with NA on empty regimes (happy path)
**Verdict:** PASS
**Evidence:** `…/UT-06-vcp-regime-split.png`
- VCP-contraction regime table: 7 columns (Regime / n / Rank-IC / Top-decile mean / Bottom-decile mean / Spread / Risk-adjusted spread), one row per configured regime (6 rows).
- Populated rows numeric (Risk-on `n=731, −0.15, +0.16% / +6.42%, −6.25%, −1.44`; Risk-off `n=242, +0.29, … +15.99%`; Narrow leadership; Choppy) — all match API.
- "Strong risk-on" and "Defensive" (n=0) show NA + `n=0 ⚠` — not a fabricated 0.

### UT-07 — Caveat banner stays visible with a new volatility factor selected (regression)
**Verdict:** PASS
**Evidence:** `…/UT-07-caveat-downside.png`
- With "Downside volatility (semivol)" selected, the caveat card titled "Survivorship bias · universe-relative · descriptive" remains visible (offsetHeight > 0), with both the survivorship-bias line and the "Descriptive evidence, not a predictive model…" line present.

### UT-08 — As-of date toggle does NOT re-point the Factor Lab (regression / J-18 guard)
**Verdict:** PASS
**Evidence:** `…/UT-08-asof-historical-lab-unchanged.png`
- Selected HV, recorded decile values + Rank-IC. Changed the global as-of control to **2025-04-04**; the indicator updated to **"Viewing as-of 2025-04-04 (historical)"** (the control genuinely changed).
- The Factor-Lab decile table (all 10 rows) and Rank-IC (`+0.03 n=1218`) were **byte-identical** before and after — the lab is a cross-date aggregate that does not move with as-of. Structurally confirmed: `fetchFactorLab(factor, horizon)` sends no `as_of` parameter.

### UT-09 — Switching factors re-renders cleanly with no stale data (regression / J-25 + J-27)
**Verdict:** PASS
**Evidence:** `…/UT-09-atr-reselected.png`
- Rank-IC across the sequence: ATR% `-0.01` → HV `+0.03` → downside `+0.12` → ATR% `-0.01`. The value changes between distinct factors (no frozen/stale carry-over), and the decile table + Rank-IC card + 6-row regime table re-render on every selection.
- Re-selecting ATR% returned byte-identical to the first ATR% reading (Rank-IC `-0.01 n=1218`; D1 `1.00 … 1.97 +1.37% n=121 +0.43 n=121`).

### UT-10 — Risk-Off run shows zero Actionable after DB regen (regression / J-07 CRITICAL)
**Verdict:** PASS
**Evidence:** `…/UT-10-riskoff-actionable-zero.png`
- Opened the seeded Risk-Off run via the global as-of control (2025-04-04, regime Risk-off). Counted every leaderboard row's setup status: **122/122 = "Risk-off-watchlist", Actionable = 0**.
- Regime gate banner present: "Risk-off regime gates every name to watchlist-only — no Actionable setups while the market is risk-off." The Risk-Off→Actionable gate is intact after the DB regeneration.

### UT-11 — NVDA scores byte-identical across leaderboard and detail after DB regen (regression / J-06 CRITICAL)
**Verdict:** PASS
**Evidence:** `…/UT-11-12-nvda-detail.png`, `…/UT-11-leaderboard-top.png`
- Leaderboard NVDA row (Latest): `Leadership E 47.48 / Entry Quality D 66.24 / Risk E 33.79`.
- Detail `/stocks/NVDA`: `Leadership E 47.48 / Entry Quality D 66.24 / Risk E 33.79`.
- Byte-identical across the two views and matching the expected values exactly (47.48/E, 66.24/D, 33.79/E). Detail subtitle reads "…the three explainable scores (identical to the leaderboard); single source of truth". Cross-checked against `GET /api/stocks` and `GET /api/stocks/NVDA` — identical.

### UT-12 — New volatility values are NOT shown on the stock detail breakdown (ux / scope guard)
**Verdict:** PASS
**Evidence:** `…/UT-11-12-nvda-detail.png`
- Full component enumeration of all three score cards on `/stocks/NVDA`:
  - **Leadership:** RS vs SPY·1m, RS vs SPY·3m, RS vs sector, RS vs theme, MA stack, Proximity to 52w high, Volume trend.
  - **Entry Quality:** Proximity to 20-DMA, **Volatility contraction**, Proximity to 50-DMA, Trend structure, Reward/risk room.
  - **Risk:** Extension above 50-DMA, **ATR %**, Liquidity, Market regime, Sector strength, Earnings gap/climax (NA), Below moving averages, RS deterioration.
- None of the three NEW factors (`hv`, `vcp_contraction`, `downside_vol`) is displayed: no "Historical volatility", no "Downside volatility", no "semivol", no "VCP-style" suffix, no `vcp_contraction`/`downside_vol` keys, and none of the new-factor raw values (e.g. HV 2.45, vcp_contraction 1.04, downside_vol 0.0144).
- The only volatility-named items are the **pre-existing** `contraction` entry-quality component (rendered "Volatility contraction" = −ATR%, contribution 12.89) and the `atr_pct` risk component ("ATR %") — both long-standing weighted-score components, not the new read-only factors. The "VCP PATTERN" section (separate legit feature) reads "No VCP pattern detected." The 3 displayed scores match the leaderboard (consistent with UT-11).

### UT-13 — Volatility family is discoverable in the dropdown (ux)
**Verdict:** PASS
**Evidence:** `…/UT-01-02-research-loaded.png`
- The four volatility measures are visually collected under a single `<optgroup label="Volatility">` heading (proven via live DOM), making the family obvious at a glance versus the old flat list. Labels are self-describing: "ATR % (volatility level)", "Historical volatility (HV)", "Volatility contraction (VCP-style)", "Downside volatility (semivol)".

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Cross-checks & Methodology Notes

- **All numeric UI values were cross-checked against backend API ground truth** and matched exactly: `GET /api/research/factor-lab?factor={atr_pct,hv,vcp_contraction,downside_vol}` (rank-IC, deciles, by-regime), `GET /api/runs` (Risk-off candidate_counts), `GET /api/stocks` and `GET /api/stocks/NVDA` (NVDA scores/buckets, all 122 Risk-off statuses).
  - hv rank-IC API +0.0276 → UI `+0.03`; vcp_contraction −0.0150 → `-0.02`; downside_vol +0.1159 → `+0.12`; atr_pct −0.0064 → `-0.01`.
- **Honest-NA path:** per the iter-11 lesson, NA was exercised through genuinely empty regimes ("Strong risk-on", "Defensive" at n=0 for every volatility factor), not horizon shrinkage. Decile NA was not present at the default 20d horizon (all deciles n≈121–122), which the test plan anticipates and falls back to the regime table for.
- **Read-only / single-source-of-truth seams verified behaviorally:** the Factor Lab is invariant to the global as-of control (UT-08), and the new volatility values are absent from every weighted-score breakdown (UT-12) — consistent with the iteration's HARD CONSTRAINT that they never enter `_build_score`.

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend:** http://localhost:8835 (API served under `/api`; `/health` returns 404 by design — `/api/stocks` and `/api/research/factor-lab` both 200)
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser`
- **Test Date:** 2026-06-02
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-13-evidence/`
- **Tooling limitations encountered (worked around, did not affect verdicts):**
  1. **Console capture not implemented** in this Chrome MCP build (capture files contain a "Console logging not yet implemented" placeholder) — console-error checks were satisfied by clean renders + absence of the "Backend unavailable" card rather than console inspection.
  2. **Deep-scroll viewport screenshots render blank** on this build (e.g. NVDA at leaderboard rank 65) — authoritative verification used live-DOM `eval` reads (every eval embeds `location.pathname` + the selected factor to self-verify the page under test); top-of-page screenshots were used where rendering is reliable.
  3. **Shared Chrome instance / concurrent QA process** (pre-existing `TC-*` tabs and evidence from another run caused initial tab drift) — mitigated by closing stale tabs, running tight navigate→await→read sequences, and re-navigating on any URL mismatch.
  4. Screenshots de-duplicated by sha256 (one distinct shot per claim; the leaderboard-top shot is a deterministic re-render identical to a prior run's, and the verdict rests on live-DOM reads).
