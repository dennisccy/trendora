# Phase goal-i_can_see_the_wealthy_future_forever-iter-18 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-18
**Date:** 2026-06-04
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->

**Overall:** 13/13 tests passed (0 skipped)

All seven P1 gating tests (UT-01, UT-02, UT-03, UT-04, UT-06, UT-11, UT-13) passed. The
headline J-26 improvement was captured live: the **Combined (composite rank-blend)** cohort is
populated (n ≥ min_sample, numeric mean/median/hit-rate/downside-risk-adjusted) and distinct from
Baseline, the **Strict overlap (AND)** secondary row renders honest **NA + n=0** on an empty
intersection while the composite stays populated, the editor scales to all **11** catalog factors,
and toggling the global as-of leaves the lab **byte-identical with zero `/api/research/*?as_of=`
requests** (J-18).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Research page + combination section loads | smoke | P1 | Heading + "Multi-factor combination cohort" panel + comparison table with the 6 column headers; no error card | Heading "Research — Factor Lab"; `combination-section` + `combination-table` rendered; headers = Cohort / n / Mean fwd return / Median / Hit-rate / Risk-adjusted (downside); no error card | PASS | `UT-01-04-combination-fullpage.png` |
| UT-02 | Composite row populated (not NA) | happy-path | P1 | composite n ≥ 30, all cells numeric (no "NA"), distinct from Baseline, visually emphasized | composite n=244; +1.21% / +0.70% / +54.10% / +0.26 (all numeric); Baseline = n=1217 / +2.03% / +0.77% / +52.26% / +0.26 (distinct); composite row shaded `rgb(24,32,45)` + `font-semibold` label (weight 600) | PASS | `UT-01-04-combination-fullpage.png` |
| UT-03 | Strict overlap row renders as secondary | happy-path | P1 | "Strict overlap (AND)" directly below composite, muted, numeric or NA+n (never numeric with n=0, never blank) | Row present directly below composite; muted (`text-text-muted` grey, weight 400, no highlight); default selection n=49 with numeric cells (+1.83% / +1.33% / +61.22% / +0.41) | PASS | `UT-01-04-combination-fullpage.png` |
| UT-04 | Row order correct | happy-path | P1 | Baseline → singles → Combined (composite) → Strict overlap; exactly one of each; no legacy "Combined (AND)" | DOM order: Baseline → RS-vs-SPY single → ATR% single → Combined (composite rank-blend) → Strict overlap (AND); exactly one composite + one strict_overlap; no "Combined (AND)" row | PASS | `UT-01-04-combination-fullpage.png` |
| UT-05 | Section hint describes composite blend | ux | P2 | Hint names composite rank-blend + quantile label + weighting word + "NOT a fitted/ML model" + strict-overlap secondary (NA+n) | Hint contains all 5: "Combined (composite rank-blend)", "top Quintile (20%)", "equal-weighted blend", "a transparent ranking of stored values, NOT a fitted/ML model", "Strict overlap (AND) … optional secondary exact intersection (NA + n when empty)" | PASS | `UT-01-04-combination-fullpage.png` |
| UT-06 | Add condition up to 11 factors | happy-path | P1 | Add up to 11 rows, button disables at 11 (not at 3), composite stays populated (n>0) | Added 2→11; "Add condition" enabled through 10, **disabled at 11**; composite stayed populated at every step (n=244/245, numeric) incl. n=244 +2.17% at 11 conditions | PASS | `UT-06-eleven-conditions-add-disabled.png` |
| UT-07 | Remove condition down to minimum | validation | P2 | Each remove drops one row + re-renders; Remove disables at min (2); no crash/blank | Removed 11→2 one at a time, table re-rendered each step (composite stayed n=244); at 2 rows both Remove buttons `disabled=[true,true]`; all rows still present | PASS | (DOM-verified; see UT-06 shot for editor) |
| UT-08 | Empty intersection → composite populated, strict NA | validation | P2 | composite populated (n>0, numeric); strict overlap NA + n=0 (no fabricated 0) | leadership_score Top + leadership_score Bottom → composite **n=1218** (+2.03% / +0.78% / +52.30% / +0.26, populated); strict_overlap **n=0 ⚠, NA / NA / NA / NA** | PASS | `UT-08-composite-populated-strict-NA.png` |
| UT-09 | Backend error handled honestly | error | P2 | "Backend unavailable" card with no-fabrication text; no fabricated/all-zero table; no white-screen | Combination section shows **"Backend unavailable — … No figures are shown rather than fabricated values — confirm the backend is running and adjust a condition to retry."**; table/composite row removed (no fabricated figures); page heading + rest of page intact; recovered cleanly on retry (composite back to n=244) | PASS | `UT-09-backend-unavailable-card.png` |
| UT-10 | Factor/Side/Quantile change updates cohorts | happy-path | P2 | single-factor label changes to new factor; composite recomputes, stays numeric n>0 | Factor 0 leadership→rs_spy_3m: single label → "Relative strength vs SPY (3m) · top Quintile (20%)", composite recomputed (n=244, -0.01%); Quantile 0 quintile→half: label → "top Half (50%)", n 244→609; Side toggle exercised in UT-08 | PASS | `UT-01-04-combination-fullpage.png` |
| UT-11 | Single-factor Factor Lab regression | regression | P1 | Decile 10 rows (D1–D10) w/ Factor range + Mean + Risk-adjusted; Rank-IC numeric; Factor + Horizon update both | Decile table = 10 rows D1–D10, headers Decile / Factor range / Mean fwd return / Risk-adjusted (downside); Rank-IC +0.00 (numeric). Factor leadership→entry_quality re-pointed decile (D1 +1.73%→+4.40%) + Rank-IC (+0.00→-0.04). Horizon 20d→60d re-pointed decile (D10 +0.52%→+5.54%) + Rank-IC (-0.04→-0.08) | PASS | `UT-11-factorlab-decile-rankic.png` |
| UT-12 | Setup & Pattern Lab regression | regression | P2 | per-horizon table w/ numeric or honest NA+n; leaderboard link present; unaffected by combination changes | Event-study table renders 5 horizon rows; Subject Actionable→VCP re-pointed (n=2→n=27); honest NA+n for low sample (n<30); "View the names expressing this on the leaderboard→" link present | PASS | `UT-11-factorlab-decile-rankic.png` |
| UT-13 | No new date state; J-18 anti-goal guard | regression | P1 | No date input inside /research; combination figures byte-identical after global as-of toggle; 0 `?as_of=` requests; one date `<select>` (none on /research) | Zero `date` inputs; the single "View as-of date" `<select>` lives in `<header>` (not in `<main>`); 6 main selects all config-driven. After toggle "Latest"→2026-02-27 (React accepted): combination figures **byte-identical**, network spy shows **0** `/api/research/*` and **0** `?as_of=` requests | PASS | `UT-08-composite-populated-strict-NA.png` (table values), DOM/network-spy verified |

---

## Passed Tests

### UT-01 — Research page + combination section loads (smoke, P1)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-18-evidence/UT-01-04-combination-fullpage.png`
- Page heading **"Research — Factor Lab"** visible; `[data-testid="combination-section"]` panel "Multi-factor combination cohort" rendered with `[data-testid="combination-table"]`.
- Column headers (DOM): `["Cohort","n","Mean fwd return","Median","Hit-rate","Risk-adjusted (downside)"]`.
- No "Backend unavailable" card on default load; no console-blocking errors; page fully hydrated (interactive controls present).

### UT-02 — Composite row populated, not NA (happy-path, P1)
**Verdict:** PASS
- `combination-row-composite` cells: **n=244**, **+1.21%**, **+0.70%**, **+54.10%**, **+0.26** — all numeric, none "NA"; n ≥ 30.
- Distinct from Baseline (n=1217 / +2.03% / +0.77% / +52.26% / +0.26).
- Cross-checked against API `GET /api/research/factor-combination` (composite stats n=244, mean_return 0.0121, median 0.0070, hit 0.541, risk_adjusted 0.262, low_sample=false).
- Visual emphasis confirmed: row background `rgb(24,32,45)` (shaded) + label `<span class="font-semibold">` (computed weight 600) vs transparent / weight 400 on single rows.

### UT-03 — Strict overlap row renders as secondary (happy-path, P1)
**Verdict:** PASS
- "Strict overlap (AND)" (`combination-row-strict_overlap`) sits **directly below** the composite row (last table row).
- Muted styling: label `<span class="text-text-muted">` (computed color `rgb(139,152,169)`, weight 400, transparent row background) — de-emphasized vs the composite.
- Default selection: n=49 with numeric cells (+1.83% / +1.33% / +61.22% / +0.41) — never a numeric figure with n=0.

### UT-04 — Comparison table row order correct (happy-path, P1)
**Verdict:** PASS
- DOM top-to-bottom: **Baseline (all names)** → **Relative strength vs SPY (3m) · top Quintile (20%)** → **ATR % (volatility level) · bottom Tertile (33%)** → **Combined (composite rank-blend)** → **Strict overlap (AND)**.
- Exactly one composite row and exactly one strict-overlap row; **no** legacy "Combined (AND)" row anywhere.

### UT-05 — Section hint describes the composite blend (ux, P2)
**Verdict:** PASS
- Hint text contains all five required elements: the phrase **"Combined (composite rank-blend)"**, a quantile label with percentage (**"top Quintile (20%)"**), a weighting word (**"equal-weighted blend"**), the explicit **"a transparent ranking of stored values, NOT a fitted/ML model"**, and the strict-overlap description **"The Strict overlap (AND) row is the optional secondary exact intersection (NA + n when empty)"**.

### UT-06 — Add condition up to 11 factors (happy-path, P1)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-18-evidence/UT-06-eleven-conditions-add-disabled.png`
- Clicked "Add condition" from the default 2 rows up to **11** rows (all catalog factors).
- "Add condition" stayed **enabled** at 3, 4, … 10 and became **disabled** exactly at **11** (it does not disable at 3).
- The composite row stayed populated at every step (n=244–245, numeric mean/median/hit/risk-adjusted), incl. **n=244, +2.17%, +0.60%, +53.28%, +0.29** at 11 conditions — it does **not** collapse to NA beyond 3 factors.

### UT-07 — Remove condition down to minimum (validation, P2)
**Verdict:** PASS
- Removed conditions one at a time from 11 → 2; each click removed exactly one row and the comparison table re-rendered (composite remained n=244, all rows present).
- At the minimum (2 conditions) both Remove buttons are **disabled** (`[true, true]`) — cannot go below 2.
- No crash / no blank section at any step.

### UT-08 — Empty strict-intersection: composite populated while strict overlap NA (validation, P2) — **headline J-26 fix**
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-18-evidence/UT-08-composite-populated-strict-NA.png`
- Set condition 1 = leadership_score **Top**, condition 2 = leadership_score **Bottom** (opposing extremes of the same factor → exact AND-intersection is empty; membership-driven per the iter-11 lesson, not horizon-driven).
- **Combined (composite rank-blend)** stayed **populated**: n=1218, +2.03% / +0.78% / +52.30% / +0.26 (numeric).
- **Strict overlap (AND)** showed the honest empty signal: **n=0 ⚠**, NA / NA / NA / NA — no fabricated 0.00% cohort.

### UT-09 — Backend error handled honestly (error, P2)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-18-evidence/UT-09-backend-unavailable-card.png`
- **Method:** the harness-managed backend (PID on :8835, owned by the parent `run-phase.sh`) was **not** killed — stopping it would risk leaving the pipeline's backend down (the harness only auto-restarts during quota-retry sleeps) and breaking the QA/audit steps that follow. Instead the documented frontend error path was exercised by network-fault injection: `window.fetch` was wrapped to reject (`TypeError: Failed to fetch`) for `/api/research/factor-combination`, then a condition was changed to trigger the re-fetch — reproducing exactly what an unreachable backend produces in `CombinationLab`'s `catch` (page.tsx:553 → `status="error"`).
- The combination section rendered the honest card: **"Backend unavailable — The combination cohorts could not load from the API. No figures are shown rather than fabricated values — confirm the backend is running and adjust a condition to retry."**
- The comparison table and composite row were removed (no fabricated numbers, no all-zero table); the page heading and every other panel stayed rendered (no white-screen).
- Fetch was restored and a retry re-fetched successfully (composite back to n=244) — error state is transient and honest.

### UT-10 — Factor / Side / Quantile selection updates the cohorts (happy-path, P2)
**Verdict:** PASS
- **Factor:** condition 0 leadership_score → rs_spy_3m re-labelled the single row to **"Relative strength vs SPY (3m) · top Quintile (20%)"**; composite recomputed to n=244 / -0.01% (numeric, n>0, not NA).
- **Quantile:** condition 0 quintile → half re-labelled to **"top Half (50%)"** and grew n=244 → **609** (top-half ⊃ top-quintile).
- **Side:** Top↔Bottom toggle exercised in UT-08 (flipped membership, drove the empty intersection).

### UT-11 — Single-factor Factor Lab regression (regression, P1)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-18-evidence/UT-11-factorlab-decile-rankic.png`
- Decile sort table = **10 rows D1–D10** with headers Decile / Factor range / Mean fwd return / Risk-adjusted (downside).
- Rank-IC card shows a numeric value (leadership @ 20d = **+0.00**, n=1218).
- Changing **Factor** (leadership_score → entry_quality_score) re-pointed both panels: decile D1 mean +1.73% → +4.40%, Rank-IC +0.00 → **-0.04**.
- Changing **Horizon** (20d → 60d) re-pointed both panels: decile D10 mean +0.52% → **+5.54%**, Rank-IC -0.04 → **-0.08** (n 1218→1217). The combination-section changes did not break the Factor Lab.

### UT-12 — Setup & Pattern Lab regression (regression, P2)
**Verdict:** PASS
- "Setup & Pattern Lab — event study" renders the per-horizon table (Horizon / n / Mean / Median / % Positive / Dispersion / Expectancy / Mean MAE / Mean MFE / Return-downside-dev / Return-MAE), 5 horizon rows.
- Subject dropdown change (Actionable → VCP) re-pointed the table (n=2 → **n=27**); low-sample cohorts (n<30) show honest **NA + n**, never a fabricated number.
- **"View the names expressing this on the leaderboard→"** link present. Panel unaffected by the combination-section changes (no shared-component regression).

### UT-13 — No new date/as-of state; J-18 anti-goal guard (regression, P1)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-18-evidence/UT-08-composite-populated-strict-NA.png` (table values) + DOM/network-spy assertions
- **No date control inside `/research`:** zero `input[type=date]`; the only date `<select>` ("View as-of date") is a descendant of `<header>`, not `<main>` (`inMain:false, inHeader:true`). The 6 selects inside `<main>` are all config-driven: Factor, Condition 1/2 factor, Condition 1/2 quantile, Event-study subject — none is a date control.
- **Combination figures ignore the global as-of:** with a `fetch`/XHR network spy installed, toggling the global as-of from "Latest" → **2026-02-27** (React accepted the controlled value — onChange fired) left the full combination table **byte-identical** (all 5 rows unchanged), and the spy recorded **0** `/api/research/*` requests and **0** `?as_of=` requests (only a background `/api/health` poll). The combination cohort is a cross-date aggregate; no second date state was added.

---

## Failed Tests

_None._

---

## Skipped Tests

_None._

---

## Notes / Methodology

- **Authoritative assertions are DOM/network-grounded.** Every PASS is backed by reading live DOM
  via `eval` (cell text, `data-testid` rows, computed styles, `disabled`/`aria-pressed` state) and,
  for UT-13, an in-page `fetch`/XHR spy — not by screenshot inspection alone. API ground truth was
  cross-checked once against `GET /api/research/factor-combination` (composite n=244, strict_overlap
  n=49, baseline n=1217; `composite_quantile` = quintile (20%); `weighting` = equal).
- **Backend health path:** the live health endpoint is `GET /api/health` (200). The `/health` path
  named in the dispatch note returns 404 — it is the wrong path, not a dead backend.
- **Valid horizons are `[1,5,10,20,60]`** (default 20). The UI exposes 1d/5d/10d/20d/60d segmented
  buttons; the "63d"/"21d" examples in the test-plan prose were guesses and do not exist — tests used
  the real buttons.
- **Harness-interaction quirks (NOT product defects):** (a) Chrome MCP's `select` action does not
  fire React `onChange` on this frontend — native-setter + bubbling `change` event was used for all
  `<select>` changes, then live DOM was asserted (per the recorded `react-controlled-select-needs-native-setter`
  lesson). (b) The MCP `click` action did not fire React `onClick` on the segmented horizon buttons;
  a native `.click()` via `eval` was used. Both are test-driver issues — the handlers are correctly
  wired (proven by the native invocation producing the expected re-fetch and state change). Real
  users clicking these controls are unaffected.
- **UT-09 was executed via network-fault injection** rather than killing the harness-managed backend
  process, to avoid disrupting the running pipeline (see UT-09 above). The fault was fully reverted
  and the section verified to recover.
- **A transient page remount** (Next.js dev fast-refresh) reset the condition editor from 10 → 2 rows
  once during UT-06; the composite stayed populated and the add sequence was simply re-run to 11. This
  is a dev-server artifact, not a product behavior.
- **Evidence de-duplication:** fullpage screenshots are distinct per state (verified by differing
  pixel dimensions/sizes). One blank viewport capture (a known post-scroll capture artifact) was
  discarded in favour of its content-bearing fullpage equivalent.

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend:** http://localhost:8835 (health at `/api/health`, 200 before and after the run)
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser`
- **Test Date:** 2026-06-04
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-18-evidence/`
  - `UT-01-04-combination-fullpage.png` — default load: composite populated, strict-overlap secondary, row order
  - `UT-06-eleven-conditions-add-disabled.png` — 11 conditions, "Add condition" disabled
  - `UT-08-composite-populated-strict-NA.png` — empty intersection: composite n=1218 vs strict NA + n=0
  - `UT-09-backend-unavailable-card.png` — honest "Backend unavailable" card, rest of page intact
  - `UT-11-factorlab-decile-rankic.png` — Factor Lab decile (D1–D10) + Rank-IC after Factor/Horizon change
