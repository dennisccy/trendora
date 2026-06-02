# Phase goal-i_can_see_the_wealthy_future_forever-iter-12 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-12
**Date:** 2026-06-02
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->

**Overall:** 15/16 tests passed (1 skipped, 0 failed)

- **All 9 P1 tests pass** (UT-01, 02, 03, 06, 07, 10, 13, 14, 15) → verdict PASS per the test plan rule.
- **P2:** UT-04, 05, 08, 09, 12 PASS; **UT-11 SKIP** (empty-pool path not reproducible with the current seed — every horizon has forward-tested data; the empty-state branch is verified in source).
- **P3:** UT-16 PASS.
- **Target J-26 confirmed:** the multi-factor combination cohort renders Baseline + per-single + Combined (AND); the Combined `n` is smaller than each single (interaction visible); a deliberately thin combined cohort renders honest **NA + n** (never a fabricated number).
- **Principal-risk regression J-18 confirmed (UT-15):** toggling the global as-of date leaves the decile, rank-IC, regime AND the new combination tables **byte-identical**, with **zero** `as_of`-parameterised requests.

---

## Methodology & evidence integrity

- **Chrome MCP** (`mcp__plugin_superpowers-chrome_chrome__use_browser`) drove every test against the running frontend.
- Every PASS/FAIL is grounded in a **structured DOM read** (exact cell text, `aria-pressed`/`disabled` states, computed styles) **plus an observed network assertion** — not on screenshots. A `window.fetch`/XHR interceptor recorded every request URL so each "re-points" / "fired a request" / "zero as_of" claim rests on the actual URL list, and every DOM cell value was cross-checked against a direct `GET /api/research/factor-combination?…` call with the *same* condition set (DOM == API).
- **Screenshot de-dup (iter-6 lesson):** all 11 `UT-*.png` evidence shots were sha256-hashed; an initial pass found 3 colliding viewport shots (a stale-frame artifact of screenshot-immediately-after-scroll). Those three were re-captured with `fullpage:true` and re-verified — **all 11 are now byte-distinct**.
- **UT-12 method note:** to avoid disrupting the shared backend managed by `browser-qa-phase.sh`, the "backend unavailable" state was exercised by injecting a client-side `fetch` rejection for the `factor-combination` endpoint (a rejected promise — indistinguishable to the app from a down backend) and triggering a re-fetch. This drives the **identical** error code-path (`.catch → status="error"` → the "Backend unavailable" card). The shared backend was never stopped; a fresh reload restored the section.
- **Console capture:** the MCP tool's console-capture is a stub ("not yet implemented"), so the console could not be inspected directly. No functional/render errors were observed: every DOM `eval` executed without exception and the React app rendered/re-rendered correctly across all interactions.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Page + combination section load | smoke | P1 | `combination-section` Card renders with controls + table, no error/skeleton | Section present, heading "Multi-factor combination cohort", 2 condition rows + populated table; no error card, no permanent skeleton | PASS | `UT-02-default-combination.png` |
| UT-02 | Default Baseline + 2 singles + Combined | happy-path | P1 | 6 columns; Baseline + 2 single rows + Combined(AND) shaded; values not blank; J-29 note | 6 cols exactly; Baseline n=1217 (+2.03%/+0.77%/+52.26%/+0.26), RS·top quintile n=244, ATR%·bottom tertile n=406, **Combined(AND) shaded** n=49 (+1.83%/+1.33%/+61.22%/+0.41) — **DOM==API exactly**; J-29 downside-only note present | PASS | `UT-02-default-combination.png` |
| UT-03 | Change factor re-points table | happy-path | P1 | Row 1 label + stats update; new request fires | factor-0 → leadership_score: Row1 → "Leadership score · top Quintile (20%)" n=244 +2.33%/+0.55%/+52.87%/+0.31 (==API); baseline shifted 1217→1218 (pool honesty); Combined n=79; request `condition=leadership_score:top:quintile&condition=atr_pct:bottom:tertile`, **no as_of** | PASS | `UT-03-factor-changed.png` |
| UT-04 | Toggle side updates cohort | happy-path | P2 | Bottom highlighted; label "bottom"; stats change | Bottom `aria-pressed=true`, Top `false`; Row1 → "… · bottom Quintile (20%)" n=244 +3.79%/+1.25%/+53.69%/+0.49 (==API); Combined n=40; request `rs_spy_3m:bottom:quintile&…`, no as_of | PASS | `UT-04-side-bottom.png` |
| UT-05 | Change quantile grows/shrinks n | happy-path | P2 | Quantile label updates; n grows for wider quantile; Combined n ≤ single n | quantile-0 quintile→half: Row1 → "… · top Half (50%)" **n 244→609** (grew) +1.60%/+0.36%/+51.56%/+0.20 (==API); Combined n=226 ≤ 609; request `rs_spy_3m:top:half&…`, no as_of | PASS | `UT-05-quantile-half.png` (fullpage) |
| UT-06 | Add 3rd condition | happy-path | P1 | 3rd control row + 3rd single row; Combined n ≤ min single ≤ baseline; Add disabled | 3 condition rows, 3 single rows (RS, ATR, Leadership); Combined n=39 ≤ min single(244) ✓; each single ≤ baseline 1217 ✓; 3-condition request fired; **Add disabled** at max | PASS | `UT-06-09-three-conditions-add-disabled.png` |
| UT-07 | Remove condition reverts to 2 | happy-path | P1 | 3rd row disappears; 2 singles; Add enabled; Remove disabled | remove-2 clicked → 2 condition rows, 2 single rows; Add re-enabled; both Remove `disabled=true` | PASS | `UT-07-08-reverted-two-conditions.png` (fullpage) |
| UT-08 | Remove disabled at min (2) | validation | P2 | Both Remove dimmed (opacity ~50%, not-allowed); click no-op | Both Remove `disabled=true`, `opacity:0.5`, `cursor:not-allowed`; clicking remove-0 → count stays 2 | PASS | `UT-07-08-reverted-two-conditions.png` (fullpage) |
| UT-09 | Add disabled at max (3) | validation | P2 | Add dimmed; click no-op | At 3 conditions Add `disabled=true`; clicking → count stays 3, no 4th row | PASS | `UT-06-09-three-conditions-add-disabled.png` |
| UT-10 | Thin combined cohort → NA + n | error | P1 | Combined n small/0; Mean/Median/Hit/Risk = "NA" (not fabricated); honest tooltip | rs_spy_3m top quintile AND rs_spy_3m bottom quintile (opposing extremes) → both singles populated (n=244 each) but Combined **n=0 ⚠**, all 4 stat cells **"NA"** with tooltip "Low sample — n below the 30 minimum; NA, not a fabricated number" | PASS | `UT-10-thin-cohort-NA.png` (fullpage) |
| UT-11 | Empty pool → honest empty state | error | P2 | `pool_n===0` → empty-state message | Longest horizon (60d) still has `pool_n=1216` (4 rows); empty-pool path **not reachable with current seed** (data at all 5 horizons). Empty-state branch verified in source (`page.tsx` `pool_n === 0` → `EmptyState "No forward-tested observations for these conditions / horizon"`). Test plan: "not reproducible … rather than a failure" | SKIP | `UT-13-horizon-60-repoint.png` (shows 60d pool populated) |
| UT-12 | Backend down → honest error card | error | P2 | Red "Backend unavailable" card with exact copy; no fabricated table | Injected fetch failure for `factor-combination` + re-fetch → red-bordered card, heading "Backend unavailable", exact body text "…No figures are shown rather than fabricated values — confirm the backend is running and adjust a condition to retry."; **table not rendered**; recovered on reload | PASS | `UT-12-backend-unavailable.png` |
| UT-13 | Horizon re-points combination table | regression | P1 | All 4 tables re-fetch & update for new horizon; conditions preserved | horizon 20d→60d: rankIC ✓ decile ✓ regime ✓ combination ✓ all changed; `factor-lab?horizon=60` + `factor-combination?horizon=60` fired; conditions preserved; **zero as_of** | PASS | `UT-13-horizon-60-repoint.png` |
| UT-14 | Decile/Rank-IC/regime still work | regression | P1 | Decile D1–D10 + Rank-IC render; regime 7 cols; re-point on factor change | Decile 10 rows D1–D10, Rank-IC card, regime **7 columns** all render; factor-select leadership_score→rs_spy_3m re-points decile (D1 range "2.15…19.00"→"0.40…0.75", mean +1.73%→+3.47%) + rank-IC (+0.00→-0.04); combination section independent (no re-fetch) — no regression | PASS | `UT-14-factorlab-repoint.png` |
| UT-15 | As-of toggle byte-identical (J-18) | regression | P1 | All 4 tables byte-identical; zero as_of requests | as-of Latest→2025-11-28 (badge → "historical"): **all_four_byte_identical=true** (rankIC, decile, regime, combination); Combined row unchanged n=49 +1.83%…; **0** research API requests on toggle (only unrelated `/api/health`); **0** `as_of` params | PASS | `UT-15-asof-historical-byte-identical.png` (fullpage) |
| UT-16 | Section discoverable | ux | P3 | Reachable by scrolling below regime table; hint + control labels + notes self-explanatory | Section is the last Card below the regime table (no hidden tab); panel hint "Combine 2–3 factor conditions … does combining factors beat either alone?"; Factor/Side/Quantile labels present; downside-only + J-29 notes under table | PASS | `UT-02-default-combination.png` |

---

## Passed Tests

### UT-01 — Page + combination section load
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-12-evidence/UT-02-default-combination.png`
- `[data-testid="combination-section"]` present with heading "Multi-factor combination cohort", 2 condition control rows and a populated comparison table. No error card and no permanent skeleton. The page heading "Research — Factor Lab" is present at top.

### UT-02 — Default Baseline + 2 singles + Combined
**Verdict:** PASS
**Evidence:** `…/UT-02-default-combination.png`
- Header row has exactly 6 columns: Cohort / n / Mean fwd return / Median / Hit-rate / Risk-adjusted (downside).
- Rows (DOM, verified == `GET /api/research/factor-combination`):
  - Baseline (all names): n=1217, +2.03%, +0.77%, +52.26%, +0.26
  - Relative strength vs SPY (3m) · top Quintile (20%): n=244, +1.38%, +0.08%, +50.82%, +0.16
  - ATR % (volatility level) · bottom Tertile (33%): n=406, +0.92%, +0.80%, +53.45%, +0.18
  - **Combined (AND)** (shaded `bg-surface-2`): n=49, +1.83%, +1.33%, +61.22%, +0.41
- The J-29 honest-limitation note ("downside-deviation only … return/MAE and MAE/MFE excursion measures arrive with the event-study lab (J-29)") is present below the table. Factor dropdown lists 8 config-driven factors; quantile dropdown lists 4 (quintile/quartile/tertile/half) — no hard-coded list.

### UT-03 — Change factor re-points table
**Verdict:** PASS
**Evidence:** `…/UT-03-factor-changed.png`
- condition-factor-0 leadership_score: Row 1 → "Leadership score · top Quintile (20%)" n=244 +2.33%/+0.55%/+52.87%/+0.31 (exactly matches the API for that condition set). Combined recomputed (n=79). Baseline shifted 1217→1218 (the pool requires both referenced factors non-null — honest pool behavior). Observed request: `…factor-combination?condition=leadership_score:top:quintile&condition=atr_pct:bottom:tertile`, no `as_of`. Distinct before/after DOM (was RS·top quintile +1.38%).

### UT-04 — Toggle side updates cohort
**Verdict:** PASS
**Evidence:** `…/UT-04-side-bottom.png`
- Bottom `aria-pressed=true`, Top `false`. Row 1 → "… · bottom Quintile (20%)" n=244 +3.79%/+1.25%/+53.69%/+0.49 (==API). Combined n=40. Request `…?condition=rs_spy_3m:bottom:quintile&condition=atr_pct:bottom:tertile`, no `as_of`.

### UT-05 — Change quantile grows/shrinks n
**Verdict:** PASS
**Evidence:** `…/UT-05-quantile-half.png` (fullpage)
- condition-quantile-0 quintile→half: label → "… · top Half (50%)", single **n 244 → 609** (wider quantile ⇒ larger cohort), +1.60%/+0.36%/+51.56%/+0.20 (==API). Combined n=226 ≤ 609. Request `…?condition=rs_spy_3m:top:half&…`, no `as_of`.

### UT-06 — Add a 3rd condition
**Verdict:** PASS
**Evidence:** `…/UT-06-09-three-conditions-add-disabled.png`
- Add → 3rd control row + 3 single rows (RS, ATR, Leadership). Combined n=39 ≤ min single (244); every single ≤ baseline 1217. 3-condition request fired. **Add button disabled** at max=3; all 3 Remove buttons enabled.

### UT-07 — Remove condition reverts to 2
**Verdict:** PASS
**Evidence:** `…/UT-07-08-reverted-two-conditions.png` (fullpage)
- Remove on condition 3 → 2 condition rows, 2 single rows + Baseline + Combined. Add re-enabled; both Remove buttons disabled.

### UT-08 — Remove disabled at minimum (2)
**Verdict:** PASS
**Evidence:** `…/UT-07-08-reverted-two-conditions.png` (fullpage)
- At 2 conditions both Remove buttons: `disabled=true`, computed `opacity:0.5`, `cursor:not-allowed`. Attempting to click remove-0 was a no-op (count stayed 2). Confirmed both at the default load and after the UT-07 revert.

### UT-09 — Add disabled at maximum (3)
**Verdict:** PASS
**Evidence:** `…/UT-06-09-three-conditions-add-disabled.png`
- At 3 conditions Add `disabled=true`. Attempting to click it was a no-op — count stayed 3, no 4th row.

### UT-10 — Thin combined cohort → NA + n
**Verdict:** PASS
**Evidence:** `…/UT-10-thin-cohort-NA.png` (fullpage)
- Conditions set to RS·top·quintile AND RS·bottom·quintile (mutually-exclusive extremes of the same factor). Both single cohorts populated (n=244 each), but the Combined (AND) intersection is genuinely empty: **n=0 ⚠**, and all four stat cells (Mean/Median/Hit-rate/Risk-adjusted) render **"NA"** with tooltip "Low sample — n below the 30 minimum; NA, not a fabricated number". No fabricated 0.00%/+0.00 anywhere. This is the J-26 honesty acceptance.

### UT-12 — Backend unavailable → honest error card
**Verdict:** PASS
**Evidence:** `…/UT-12-backend-unavailable.png`
- With a client-side fetch failure injected for the `factor-combination` endpoint (faithful simulation of a down backend — see Methodology), a re-fetch produced a red-bordered (`border-neg`) card: heading "Backend unavailable", body exactly "The combination cohorts could not load from the API. No figures are shown rather than fabricated values — confirm the backend is running and adjust a condition to retry." The combination table was **not** rendered (no fabricated figures). A fresh reload restored the table (Combined n=49) and removed the card.

### UT-13 — Horizon re-points combination table
**Verdict:** PASS
**Evidence:** `…/UT-13-horizon-60-repoint.png`
- Horizon 20d→60d: the decile table, rank-IC card, regime table **and** the combination table all changed. Observed requests `…factor-lab?horizon=60` and `…factor-combination?horizon=60` (both re-fetched); **zero** `as_of` params. The two condition rows + selections were preserved across the horizon change. At 60d the combination values updated (Baseline +10.57% n=1216, Combined n=50 +1.52%).

### UT-14 — Existing Factor Lab still works
**Verdict:** PASS
**Evidence:** `…/UT-14-factorlab-repoint.png`
- Decile table renders D1–D10; Rank-IC card renders a value; regime-effectiveness table renders its **7 columns** (Regime / n / Rank-IC / Top-decile mean / Bottom-decile mean / Spread (top − bottom) / Risk-adjusted spread). Changing the top-right Factor select (leadership_score → rs_spy_3m) re-points the decile (D1 range "2.15…19.00"→"0.40…0.75", mean +1.73%→+3.47%) and rank-IC (+0.00 → -0.04); `factor-lab?factor=rs_spy_3m` fired. The combination section did NOT re-fetch on this change (independent `conditions` state — correct). No regression after the new section was added.

### UT-15 — Global as-of toggle leaves `/research` byte-identical (J-18)
**Verdict:** PASS (principal-risk regression)
**Evidence:** `…/UT-15-asof-historical-byte-identical.png` (fullpage)
- Captured a full snapshot of rank-IC + the entire decile, regime, and combination tables; cleared the request log; changed the global as-of select Latest (2026-05-28) → 2025-11-28 (badge changed to "Viewing as-of 2025-11-28 (historical)", proving the global state genuinely changed).
- After the toggle: **all four surfaces byte-identical** (`all_four_byte_identical=true`); the Combined row was unchanged (n=49 +1.83%/+1.33%/+61.22%/+0.41). The only request observed during the toggle was an unrelated background `/api/health` poll — **zero** `/api/research/*` requests and **zero** `as_of`-parameterised requests. The combination section adds no date state. J-18 holds across the new table.

### UT-16 — Section discoverable on the Factor Lab
**Verdict:** PASS
**Evidence:** `…/UT-02-default-combination.png`
- The "Multi-factor combination cohort" Card is reachable by scrolling below the regime-effectiveness table (no hidden tab, no extra navigation). The panel hint explains the purpose ("Combine 2–3 factor conditions … does combining factors beat either alone?"). Factor / Side / Quantile control labels are present and self-explanatory; the downside-deviation scope note and the J-29 honest-limitation note are visible under the table.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-11 — Empty pool → honest empty-state message
**Verdict:** SKIPPED
**Reason:** Not reproducible with the current seed. The empty-pool branch fires only when `pool_n === 0`, but the seed has forward-tested observations at every available horizon — at the longest horizon (60d) the pool is still `pool_n=1216` (the table renders 4 populated rows; confirmed in the browser and via the API). The UI test plan explicitly directs that this be noted as "not reproducible with current seed rather than a failure." The empty-state code path exists and is correct in source (`apps/frontend/app/research/page.tsx`: `data.pool_n === 0 ? <EmptyState title="No forward-tested observations for these conditions / horizon" … />`). P2 — does not affect the overall verdict.

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend:** http://localhost:8835 (running; `GET /api/research/factor-combination` → 200 throughout)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), viewport 1440×1100
- **Test Date:** 2026-06-02
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-12-evidence/`
- **Evidence shots (11, all sha256-distinct):** UT-02, UT-03, UT-04, UT-05, UT-06-09, UT-07-08, UT-10, UT-12, UT-13, UT-14, UT-15
- **Serialization:** ran after the `qa` agent on the shared Chrome (the `qa` agent's `TC-*` shots coexist in the evidence dir); browser-qa shots are namespaced `UT-*`.
