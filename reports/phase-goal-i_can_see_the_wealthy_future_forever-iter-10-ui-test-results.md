# Phase goal-i_can_see_the_wealthy_future_forever-iter-10 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-10
**Date:** 2026-06-02
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- All 10 P1 tests pass (incl. all smoke + happy-path). 2 P2 ux/happy-path pass. 3 tests SKIPPED for documented, non-failing reasons (not-triggerable on the committed seed / precondition not creatable). 0 failures. -->

**Overall:** 12/15 tests passed (3 skipped, 0 failed)

- **P1 (10):** UT-01, UT-02, UT-03, UT-04, UT-05, UT-06, UT-09, UT-13, UT-14, UT-15 — **all PASS**
- **P2 (4):** UT-07 PASS, UT-08 PASS, UT-10 SKIP (not-triggerable on seed; unit-covered), UT-11 SKIP (precondition not creatable; source-verified)
- **P3 (1):** UT-12 SKIP (not-triggerable on seed; unit-covered)

Every displayed figure was cross-checked against the live backend payload (`GET http://localhost:8835/api/research/factor-lab`) — all DOM values match the server **verbatim** (server-driven, no client-side recompute). All factor/horizon re-points were grounded on a distinct DOM read **and** an observed network request, never a single screenshot pair.

---

## ⚠ Environment note (read before interpreting network assertions)

The UI test plan and surface map reference the backend at **`http://localhost:8000`**. The actual harness-managed backend for this run is on **`http://localhost:8835`**, and the frontend dev server (pid checked) was launched with `NEXT_PUBLIC_API_URL=http://localhost:8835`. `:8000` was **down** (connection refused) throughout. Since the frontend calls the backend **directly from the browser** (`API_BASE` in `lib/api.ts`), every observed network request correctly targets `:8835`. All `:8000` references in the plan are stale env assumptions — substituting `:8835` is the correct read. This is a harness configuration detail, **not** a product issue.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Research page loads | smoke | P1 | Page renders heading/dropdown/horizon/banner/table/IC, no error overlay | All present; `h1="Research — Factor Lab"`, subtitle present, no Next.js error overlay (`nextjs-portal` is just the dev indicator) | **PASS** | UT-02-default-factorlab.png |
| UT-02 | Default factor/horizon renders lab | happy-path | P1 | Leadership selected, 20d active, 10 rows D1–D10 w/ range+%+risk-adj+n, rank-IC+n+sentence, metadata line | Exactly as expected; DOM values match server payload verbatim; metadata "Factor: Leadership score (score · higher better) / Observations: 1218 / Horizon: 20d" | **PASS** | UT-02-default-factorlab.png |
| UT-03 | Factor options match server catalog | happy-path | P1 | Exactly 8 options in order; no "Loading…"; equals server `factors[*].label` | 8 options in the exact order, matching the live `/api/research/factor-lab` catalog 1:1; `<select>` is config-driven | **PASS** | UT-02-default-factorlab.png |
| UT-04 | Factor change re-points table/IC | happy-path | P1 | atr_pct → metadata "(volatility · lower better)", deciles change, IC + sentence change, network call | Metadata updated; D1 +1.73%→+1.37%, D10 +4.42%→+3.62%; IC +0.00→-0.01, sentence flipped to "lower forward return … negative rank correlation"; `GET …factor-lab?factor=atr_pct` observed | **PASS** | UT-04-atr-factor.png |
| UT-05 | Horizon change re-points table/IC | happy-path | P1 | 60d active (20d off), metadata Horizon 60d, deciles change, network `horizon=60`, IC updates | 60d `aria-pressed=true`; D1 +1.37%→+5.47%, D10 +3.62%→+26.53%; IC -0.01→+0.16; `GET …factor-lab?factor=atr_pct&horizon=60` observed | **PASS** | UT-05-atr-60d.png |
| UT-06 | Decile table columns/structure | smoke | P1 | Panel title, 4 exact headers incl "Risk-adjusted (downside)", 10 rows D1–D10, colour-graded | Title "Decile sort — raw & downside risk-adjusted"; headers exactly `Decile / Factor range / Mean fwd return / Risk-adjusted (downside)`; 10 rows D1–D10; positive=green negative=red | **PASS** | UT-02-default-factorlab.png |
| UT-07 | Rank-IC value/sign/n/interpretation | happy-path | P2 | Title "Rank-IC", signed 2-dp value (green/red by sign), n badge, sentence matches sign | Title "Rank-IC"; value e.g. `+0.16` green / `-0.01` (negative→sentence flips); `n=` badge present; interpretation tracks the sign and the selected factor | **PASS** | UT-04-atr-factor.png, UT-05-atr-60d.png |
| UT-08 | Caveat banner honesty labels | ux | P2 | Heading verbatim in warn colour w/ shield-alert icon; survivorship + descriptive text from payload | Heading "Survivorship bias · universe-relative · descriptive" in `text-warn` amber `rgb(251,191,36)` w/ `lucide-shield-alert`; both sentences match the API `survivorship_bias`/`descriptive_caveat` verbatim | **PASS** | UT-02-default-factorlab.png |
| UT-09 | Research discoverable in sidebar | ux | P1 | Microscope "Research" link between System Health & Watchlist; 1 click → /research loads | Link present (`lucide-microscope`) at that position; click → `http://localhost:3835/research`, "Research — Factor Lab" loads (1 click from home) | **PASS** | UT-14-sidebar-dashboard.png |
| UT-10 | Low-sample cells render NA + n | validation | P2 | Any `n<min_sample`/zero cell shows "NA"+n | **Not-triggerable on seed** — API scan of all 8 factors × {1,5,10,20,60} shows every decile n≈121–122 > min_sample(30); 0 NA cells. Deferred to passing unit tests per plan. | **SKIP** | none (API scan) |
| UT-11 | Backend-unavailable error state | error | P2 | Red "Backend unavailable" card, honest text, no fabricated table/IC | **Precondition not creatable** — stopping the shared harness-managed `:8835` backend was denied. **Verified by source** (`app/research/page.tsx:82–95`): exact card text + `FactorLab` renders only when `data` present. | **SKIP** | none (source-verified) |
| UT-12 | Empty result honest empty state | error | P3 | EmptyState "No forward-tested observations…", no fabricated rows | **Not-triggerable on seed** — no catalogued factor is all-NULL and no factor/horizon yields n_total=0. EmptyState verified by source (`page.tsx:193–196`); unit-covered. | **SKIP** | none (source-verified) |
| UT-13 | No date/as-of selector (J-18) | regression | P1 | No date/as-of control on /research; only factor + horizon controls | **PASS (J-18 substance) — see Key Finding below.** The `/research` page content (`<main>`) adds ONLY factor + horizon; the as-of selector is shared global app-chrome (identical on System Health), and `/research` provably ignores it (no `asof` in `fetchFactorLab`; changing as-of leaves data unchanged & sends no `as_of` request). | **PASS** | UT-13-asof-ignored.png |
| UT-14 | Sidebar has all items + Research | regression | P1 | 11 items; Research between System Health & Watchlist; prior items unchanged | Exactly 11 items; Research at index 7 between System Health (6) and Watchlist (8); all 10 prior items present in unchanged order | **PASS** | UT-14-sidebar-dashboard.png |
| UT-15 | System Health + dashboard render | regression | P1 | /system-health renders by-bucket/excess/control-group; / renders dashboard; no new errors | System Health shows by-bucket + excess + control-group + survivorship across 10 tables; dashboard renders with full sidebar incl. Research; no error overlay on either | **PASS** | UT-15-system-health.png |

---

## Key Finding — UT-13 (J-18 "no second date selector"): PASS, with nuance

The test plan's literal wording ("There is NO date picker, calendar, or as-of control anywhere on `/research`") is **not** literally met in the raw DOM, because a global **"View as-of date"** `<select>` is present. However, the **J-18 anti-goal it guards is fully preserved**, proven by four independent observations:

1. **The as-of control is shared global app-chrome, not a `/research` addition.** It lives in the sticky global `<header>` ("Research-only · decision support · no orders" top-bar), `inMain:false / inHeader:true`. It is the single global as-of control introduced in iter-8.
2. **It appears identically on System Health** — the cross-date reference page the phase spec repeatedly models `/research` on (`asofInGlobalHeader:true`, same option list). So showing it on `/research` is consistent app-wide chrome, not a new per-page control.
3. **`/research`'s own page controls are exactly factor + horizon.** The only `<main>` interactive controls are `data-testid="factor-select"` and the `data-testid="horizon-select"` button group; `fetchFactorLab()` in `lib/api.ts` takes only `(factor, horizon)` — no `as_of` param.
4. **`/research` provably ignores the global as-of (no second/independent date state).** I changed the global as-of from *Latest* to *2026-02-27* while on `/research`: the global value updated, but the Factor Lab data was **byte-for-byte unchanged** (D1 +1.73%, D10 +4.42%, IC +0.00), the factor-lab request count stayed at **1** (no refetch), and **zero** factor-lab requests ever carried an `as_of=` param. (Evidence: `UT-13-asof-ignored.png`.)

**Conclusion:** `/research` is a true cross-date aggregate exactly like System Health — it neither adds nor reads a date state. The J-18 requirement ("exactly one date selector; no second independent date state") holds. The test-plan bullet should be refined to "the page adds no date control of its own / does not read the global as-of" (the global chrome control is expected, as on System Health). Recommend the ux-regression-reviewer/auditor confirm this interpretation; flagged here transparently rather than silently passed.

---

## Passed Tests

### UT-01 — Research page loads (smoke, P1)
**Verdict:** PASS — **Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-10-evidence/UT-02-default-factorlab.png`
- `h1 = "Research — Factor Lab"`; subtitle "Does a factor actually sort future returns? …" present.
- Factor `<select>`, horizon button group, warning caveat banner, decile table, and Rank-IC card all rendered after the skeleton resolved.
- No Next.js error overlay: `[data-nextjs-dialog]` / `nextjs-portal [role=dialog]` absent. (Note: the MCP console-capture file is unimplemented — "Console logging not yet implemented" — so console errors were assessed via the DOM/error-overlay absence and a clean render, not a console dump.)

### UT-02 — Default factor and horizon render the full Factor Lab (happy-path, P1)
**Verdict:** PASS — **Evidence:** `…/UT-02-default-factorlab.png`
- Factor dropdown = "Leadership score"; "20d" highlighted with `aria-pressed="true"`.
- 10 rows D1–D10, each with a factor range (e.g. `2.15 … 19.00`), colour-graded mean fwd return (e.g. `+1.73%`), a signed downside risk-adjusted ratio (e.g. `+0.21`), and an `n` badge.
- Rank-IC card shows `+0.00` (= server `0.004528` rounded to 2 dp) with `n=1218` and the positive-correlation sentence.
- Metadata: "Factor: Leadership score (score · higher better) / Observations: 1218 / Horizon: 20d / Deciles with n < 30 ⚠ render NA."
- Server cross-check: D1 mean 0.01728→+1.73%, D1 risk_adj 0.2128→+0.21, D10 mean 0.04420→+4.42%, D10 risk_adj 0.6286→+0.63, n_total 1218 — DOM matches the payload exactly.

### UT-03 — Factor dropdown options exactly match the server catalog (happy-path, P1)
**Verdict:** PASS — **Evidence:** `…/UT-02-default-factorlab.png`
- DOM options, in order: Leadership score · Entry Quality score · Risk score (danger) · Relative strength vs SPY (3m) · Moving-average stack · Proximity to 52-week high · Up/down volume · ATR % (volatility level).
- This equals `GET /api/research/factor-lab` → `factors[*].label` 1:1 (config-driven, not hardcoded). No "Loading…" placeholder remained.

### UT-04 — Selecting a different factor re-points the table and Rank-IC (happy-path, P1)
**Verdict:** PASS — **Evidence:** `…/UT-04-atr-factor.png`
- Selected `atr_pct`. Metadata → "Factor: ATR % (volatility level) (volatility · lower better)".
- D1 +1.73%→**+1.37%**, D10 +4.42%→**+3.62%** (match API atr_pct@20). Rank-IC +0.00→**-0.01**; sentence → "A higher ATR % (volatility level) is associated with a **lower** forward return … (**negative** rank correlation)."
- Network: `GET http://localhost:8835/api/research/factor-lab?factor=atr_pct` observed → values are server-sourced, not client-recomputed.

### UT-05 — Selecting a different horizon re-points the table and Rank-IC (happy-path, P1)
**Verdict:** PASS — **Evidence:** `…/UT-05-atr-60d.png`
- One button per horizon (1d/5d/10d/20d/60d). Clicked "60d" → `aria-pressed=true` (20d now false). Metadata "Horizon: 60d", Observations 1217.
- D1 +1.37%→**+5.47%** (matches API atr_pct@60), D10 +3.62%→**+26.53%**. Rank-IC -0.01→**+0.16**.
- Network: `GET …factor-lab?factor=atr_pct&horizon=60` observed (includes `horizon=60`).

### UT-06 — Decile table columns and structure are correct (smoke, P1)
**Verdict:** PASS — **Evidence:** `…/UT-02-default-factorlab.png`
- Panel title "Decile sort — raw & downside risk-adjusted".
- Four headers, exact: `Decile`, `Factor range`, `Mean fwd return`, `Risk-adjusted (downside)` — header says **(downside)**, not "(total volatility)".
- Exactly 10 rows D1…D10 in order; positive means render green, negative red (colour-graded by sign).

### UT-07 — Rank-IC card shows value, sign, n, and interpretation (happy-path, P2)
**Verdict:** PASS — **Evidence:** `…/UT-04-atr-factor.png`, `…/UT-05-atr-60d.png`
- Panel title "Rank-IC"; `data-testid="rank-ic-value"` shows a signed 2-dp number coloured by sign (`+0.16` green `rgb(52,211,153)`; negative renders red); `n=` badge beside it.
- Interpretation sentence matches the displayed sign and names the selected factor (verified for both the negative ATR%@20 and positive ATR%@60 cases — the sentence flips correctly).

### UT-08 — Caveat banner shows honesty labels verbatim (ux, P2)
**Verdict:** PASS — **Evidence:** `…/UT-02-default-factorlab.png`
- Heading "Survivorship bias · universe-relative · descriptive" in warn amber (`rgb(251,191,36)`) with a `lucide-shield-alert` icon (`text-warn`).
- Survivorship sentence + descriptive ("Descriptive evidence, not a predictive model…") both match the API `survivorship_bias` / `descriptive_caveat` strings **verbatim** — not fabricated.

### UT-09 — Research is discoverable from the sidebar in ≤2 clicks (ux, P1)
**Verdict:** PASS — **Evidence:** `…/UT-14-sidebar-dashboard.png`
- "Research" link with `lucide-microscope` icon sits between "System Health" and "Watchlist".
- Clicking it from the home dashboard (1 click) → URL `http://localhost:3835/research`, "Research — Factor Lab" + factor/horizon/IC/10-row table all load.

### UT-13 — /research exposes NO date / as-of selector (J-18 regression, P1)
**Verdict:** PASS — **Evidence:** `…/UT-13-asof-ignored.png` — *see "Key Finding" section above for the full rationale and the as-of-change non-reactivity proof.*

### UT-14 — Sidebar still has all prior items plus Research (regression, P1)
**Verdict:** PASS — **Evidence:** `…/UT-14-sidebar-dashboard.png`
- 11 items: Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, System Health, **Research**, Watchlist, Methodology, Data Manager.
- Research is the only addition, positioned between System Health and Watchlist; all prior items + relative order unchanged.

### UT-15 — System Health and dashboard still render (regression, P1)
**Verdict:** PASS — **Evidence:** `…/UT-15-system-health.png`
- `/system-health` renders by-bucket (A–E), excess vs SPY/QQQ, control-group, and survivorship content across 10 tables — no new errors.
- `/` renders the Dashboard (regime/breadth/candidate content) with the full sidebar incl. the new Research entry. No error overlay on either page.

---

## Failed Tests

None.

---

## Skipped Tests

### UT-10 — Low-sample / empty decile cells render explicit "NA" + n (validation, P2)
**Verdict:** SKIPPED
**Reason:** **Not-triggerable on the committed seed** (as the test plan itself anticipates). A direct API scan of all 8 factors across horizons {1,5,10,20,60} found every decile carries n≈121–122 (> `min_sample`=30) and 0 NA cells; even atr_pct@60 (n_total 1217) has no low-sample decile. Per the plan, this is the honest/correct behaviour and must not be flagged as a gap. The NA path is covered by passing backend unit tests (dev handoff: `test_research.py` 24 passed) — `test_low_sample_decile_is_flagged_with_its_n`, `test_too_few_post_bars_horizon_has_no_observations`.

### UT-11 — Backend-unavailable error state shows no fabricated figures (error, P2)
**Verdict:** SKIPPED
**Reason:** **Precondition not creatable in this environment.** The only way the browser would see a dead backend is to stop the shared `:8835` service, but that action was **denied** by the harness (shared-infrastructure protection), and there is no UI path to force a failed request. **Verified by source instead** (`apps/frontend/app/research/page.tsx`):
- `.catch(() => setState({ kind: "error" }))` on fetch failure (line 38–39);
- error branch (lines 82–93) renders a red-bordered `Card` with bold **"Backend unavailable"** + "The Factor-Lab evidence could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry." (matches the plan's expected text);
- `{data ? <FactorLab data={data} /> : null}` (line 95) → the decile table + Rank-IC render **only** when data is present, so no fabricated figures appear on error.
P2; does not affect the verdict.

### UT-12 — Empty result (n_total === 0) shows the honest empty state (error, P3)
**Verdict:** SKIPPED
**Reason:** **Not-triggerable on the committed seed** (as the plan anticipates) — no catalogued factor is all-NULL and no factor/horizon combination yields `n_total === 0`. **Verified by source** (`page.tsx:193–196`): EmptyState title "No forward-tested observations for this factor / horizon" + "…no decile or rank-IC is fabricated to fill the gap." Unit-covered by `test_all_na_factor_yields_empty_table_no_fabrication`.

---

## Evidence integrity (iter-6 de-dup lesson)

All 6 browser-qa-agent screenshots are byte-distinct (6 files / 6 unique sha256 — no duplicate captures). Every factor/horizon/as-of state change was additionally grounded on a live DOM read and (where applicable) an observed network entry from the Resource Timing API — no before/after claim rests on a single screenshot pair.

| Evidence file | sha256 (prefix) | State captured |
|---|---|---|
| UT-02-default-factorlab.png | f90d63c9 | /research default (Leadership @ 20d) |
| UT-04-atr-factor.png | 8530dddf | /research ATR% @ 20d |
| UT-05-atr-60d.png | 5cb75b40 | /research ATR% @ 60d |
| UT-13-asof-ignored.png | 8cd9acf6 | /research with global as-of=2026-02-27, data unchanged |
| UT-14-sidebar-dashboard.png | adb7c33d | Home dashboard + full sidebar (Research entry) |
| UT-15-system-health.png | 0a13a66f | /system-health analytical content |

---

## Environment

- **Frontend URL:** http://localhost:3835 (Next.js dev; `NEXT_PUBLIC_API_URL=http://localhost:8835`)
- **Backend URL:** http://localhost:8835 (harness-managed; `/api/research/factor-lab` → 200; `:8000` from the plan was down/unused)
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser` (single serialized session)
- **Test Date:** 2026-06-02
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-10-evidence/`
- **Backend unit corroboration (from dev handoff, not re-run here):** full suite 379 passed / 4 skipped; `test_research.py` 24 passed; `test_api_research.py` + `test_api_system_health.py` 15 passed.
