# Phase goal-i_can_see_the_wealthy_future_forever-iter-2 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-2
**Date:** 2026-06-01
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 12/12 tests passed (0 failed, 0 skipped)

All P1 tests (UT-01–07, UT-10, UT-11) and all P2 tests (UT-08, UT-09, UT-12) passed.
The new read-only "Return attribution" section (J-19) renders four populated panels on both
`/system-health` (aggregate, riding the existing Horizon selector) and `/backtest` (per-date, with a
client-side Horizon view selector), shows honest NA on too-recent dates, and the Backtest horizon
selector triggers **no** data refetch and **no** date-state change (J-18 preserved). Browser-rendered
figures matched the canonical API byte-for-byte at every horizon checked.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | System Health loads with attribution section | smoke | P1 | "Return attribution" + 4 panel headings render below "Control-group comparison"; no console errors | Heading at DOM index 7, directly below Control-group (index 6); 4 panel headings present; runtime-error collector empty | **PASS** | UT-01-02-03-system-health-attribution.png |
| UT-02 | Attribution shows real figures | happy-path | P1 | Contributors/Detractors columns with ticker+sector+colored mean+`(n=…)`; Distribution 5 rows; hit-rate & σ neutral | 5 contributors + 5 detractors named (PLTR…/BLDR…), each w/ sector + colored return + n=10 ⚠; Distribution 5 rows; Mean/Median signed+graded, hit-rate 52.30% & σ 13.83% neutral | **PASS** | UT-01-02-03-system-health-attribution.png |
| UT-03 | Distribution Mean equals header "Mean stock fwd return" | happy-path | P1 | Dist Mean == header mean; Sample size == header n; no divergent mean | Header **+2.03% (n=1218)** == Distribution Mean **+2.03% / n=1218**; API confirms exact float equality `dist.mean==overall.mean` at 5d & 20d | **PASS** | UT-01-02-03-system-health-attribution.png |
| UT-04 | Horizon change re-renders attribution | happy-path | P1 | Clicked horizon active; panels + header update; intro matches; no errors | 20d→5d: active=5d, Dist Mean +2.03%→**−0.51%**, header→−0.51%, intro→"Open the 5-day…"; collector empty | **PASS** | UT-01-02-03-system-health-attribution.png |
| UT-05 | Backtest loads with section + view selector | smoke | P1 | "Return attribution" below scorecard; Horizon buttons 1d–60d; 4 panels; no error card | Section below "Forward-test scorecard"; buttons 1d/5d/10d/20d/60d present; 4 panels populated; no "Backend unavailable" | **PASS** | UT-05-06-backtest-2024-08-28-1d.png |
| UT-06 | Horizon view selector switches slice | happy-path | P1 | Default = first horizon with observed window; click 10d updates panels + intro; scorecard & badge unchanged | Default **1d** (`aria-pressed=true`, n=122 not all-NA); click 10d → panels=10d slice (−0.54%), intro→"10-day"; scorecard (1d +0.23%) & badge unchanged | **PASS** | UT-06-07-backtest-10d-switch.png |
| UT-07 | Selector triggers no refetch / no date change | regression | P1 | No new `/api/backtest` on horizon clicks; badge & dropdown unchanged | Network interceptor: **0** `/api/backtest` (or `/api/system-health`) calls; only 1 background `/api/health` poll (timer-based, unrelated); badge=2024-08-28 & dropdown unchanged | **PASS** | UT-06-07-backtest-10d-switch.png |
| UT-08 | Honest NA on too-recent date | validation | P2 | NA horizon: em-dash Mean/Median/hit-rate/σ + n=0; per-stock/sector empty copy; ⚠ marker; no fabricated 0% | At Latest (2026-05-28): Distribution all "—", n=0 ⚠; "No ticker had a measurable forward return…"; "No sector…"; bands all "—" n=0 ⚠; **no** "0.00%" anywhere | **PASS** | UT-08-09-backtest-latest-NA.png |
| UT-09 | Empty bands listed; per-stock empty copy | validation | P2 | Every config band listed even when empty (em-dash NA); per-stock empty side copy; labels match config | All 3 bands (1–10/11–50/51+) listed with "—" n=0 at Latest; per-stock empty-state copy shown; labels == config.yaml `rank_bands` | **PASS** | UT-08-09-backtest-latest-NA.png |
| UT-10 | Existing System Health panels unchanged | regression | P1 | Six pre-existing panels render with values+n; section at bottom only | All 6 present (score bucket, excess, setup, regime, VCP, control-group); "Return attribution" sits last (index 7, after control-group index 6) | **PASS** | UT-01-02-03-system-health-attribution.png |
| UT-11 | Backtest single global date control intact | regression | P1 | Exactly one date selector; horizon buttons = view not date; global date updates scorecard+badge+attribution together; no page-local date state | `selectCount==1` (top-bar "View as-of date"); horizon buttons labelled 1d–60d (not dates); Latest→2024-08-28 updated scorecard+badge+attribution together; in-app nav preserved as-of | **PASS** | UT-11-12-backtest-inapp-nav-asof-preserved.png |
| UT-12 | Discoverable from sidebar | ux | P2 | Both sidebar links exist; section reachable within one click+scroll; clear copy | Sidebar has "System Health" & "Backtest"; in-app click reached each; section present with plain-language intro copy | **PASS** | UT-11-12-backtest-inapp-nav-asof-preserved.png |

---

## Passed Tests

### UT-01 — System Health loads with the new attribution section
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-2-evidence/UT-01-02-03-system-health-attribution.png`
- Page rendered fully (no blank screen, no "Backend unavailable" card).
- Heading order via DOM: …`Control-group comparison — selection vs sector beta` (index 6) → **`Return attribution`** (index 7) → `Top contributors & detractors`, `Distribution & hit-rate`, `Forward return by sector`, `Forward return by rank band`. The section sits **below** the control-group panel as specified.
- Intro copy present: "Open the 20-day forward return: which tickers drove or dragged it, which sectors and rank bands carried it, and its distribution shape. Read-only — derived from the stored per-observation returns, never recomputed."
- No console/runtime errors (injected error + `console.error` collector returned `[]`).

### UT-02 — Attribution shows real per-stock / distribution / group figures
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-2-evidence/UT-01-02-03-system-health-attribution.png`
- **Top contributors & detractors** (20d): CONTRIBUTORS — PLTR (Technology) +16.45%, CIEN +13.38%, MU +10.93%, AVGO +10.40%, LEU (Energy) +10.12%; DETRACTORS — BLDR (Industrials) −9.65%, S −7.74%, TEAM −7.44%, MDB −7.38%, LEN (Consumer Discretionary) −7.06%. Each row shows the ticker, a sector label, a sign/colour-graded mean return, and `n=10 ⚠`. Contributors sorted descending, detractors ascending.
- **Distribution & hit-rate** shows exactly five rows: Mean +2.03%, Median +0.78%, % positive (hit rate) 52.30%, Dispersion (σ) 13.83%, Sample size n=1218. Mean/Median are signed and colour-graded; **% positive and σ are neutral** (no sign, no green/red), shown as percentages — matching the spec.
- **Forward return by sector**: one row per stored sector (9 rows), each with mean + n (Technology +2.70% n=579 … Communication Services +1.68% n=30). Sum of n = **1218** = overall n.
- **Forward return by rank band**: all three config bands — 1–10 +5.47% (n=100), 11–50 +1.59% (n=400), 51+ +1.80% (n=718). Sum of n = **1218** = overall n. Higher band → higher return (ranking efficacy visible).

### UT-03 — Distribution Mean equals the header "Mean stock fwd return"
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-2-evidence/UT-01-02-03-system-health-attribution.png`
- Header strip: "Mean stock fwd return: **+2.03%** (n=1218)".
- Distribution → Mean: **+2.03%**, Sample size: **n=1218** — identical value, sign and sample size; no second divergent mean for the horizon.
- Cross-checked against the canonical API at horizon 5 and 20: `dist.mean == overall.mean` returned **True** (exact float equality) and `dist.n == overall.n` **True** in both cases. The UI serves the single source with no recomputation drift.

### UT-04 — Horizon change re-renders the System Health attribution
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-2-evidence/UT-01-02-03-system-health-attribution.png`
- Before: active=20d, Distribution Mean +2.03%, header +2.03% (n=1218), top contributor PLTR +16.45%.
- Clicked **5d** in the top-right Horizon selector → `aria-pressed` moves to 5d.
- After: Distribution Mean **−0.51%**, Median −0.64%, hit-rate 45.32%, σ 7.35%, n=1218; header → "−0.51% (n=1218)"; intro → "Open the **5-day** forward return…"; top contributor PLTR → +4.95%.
- Both 5d browser values match the API exactly (dist.mean −0.51%, median −0.64%, pct_pos 45.32%, disp 7.35%, PLTR +4.95%). Error collector remained `[]`; no blank section.

### UT-05 — Backtest loads with the attribution section and Horizon view selector
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-2-evidence/UT-05-06-backtest-2024-08-28-1d.png`
- At as-of 2024-08-28 (historical): "Return attribution" heading renders **below** the "Forward-test scorecard" card.
- Horizon segmented button group present in the section header: buttons **1d / 5d / 10d / 20d / 60d**.
- All four panels populate with real numbers; no "Backend unavailable" error card.

### UT-06 — Backtest Horizon view selector switches the displayed slice
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-2-evidence/UT-06-07-backtest-10d-switch.png`
- **Default selection** at 2024-08-28 is **1d** (`aria-pressed=true`) — the first horizon with an observed window (n=122, a real-numbers panel, not all-NA). Intro: "Open the 1-day forward return…".
- Clicked **10d** → button becomes active; four panels update to the 10d slice: Mean −0.54%, Median −0.60%, hit-rate 43.44%, σ 6.53%, n=122 (matches API h10 −0.54%). Intro → "Open the **10-day** forward return…".
- The **Forward-test scorecard above did NOT change** (first row still 1d cohort +0.23% / n=20 ⚠). The "Viewing as-of 2024-08-28" badge did NOT change.

### UT-07 — Backtest Horizon selector triggers NO refetch and NO date change (J-18 guard)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-2-evidence/UT-06-07-backtest-10d-switch.png`
- Installed a `window.fetch` + `XMLHttpRequest.open` interceptor, reset its log, then switched horizons (1d→10d).
- Captured calls since reset: **0** `/api/backtest` requests, **0** `/api/system-health` requests, 0 other data requests. The only network call observed was a single background `/api/health` poll (the app-wide health-status indicator, which fires on a timer independent of the click). No data payload was refetched.
- The "Viewing as-of {date}" badge value and the top-bar dropdown selection were both unchanged before and after; only the attribution panels changed. The horizon selector consumes already-fetched `by_horizon[*].attribution` data — no new fetch, no reintroduced date state.

### UT-08 — Honest NA on a too-recent date
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-2-evidence/UT-08-09-backtest-latest-NA.png`
- At "Latest" (2026-05-28), where forward windows have not elapsed, every horizon is NA.
- Distribution & hit-rate: Mean **—**, Median **—**, % positive **—**, Dispersion **—**, Sample size **n=0 ⚠**.
- Top contributors & detractors: "**No ticker had a measurable forward return at this horizon.**"
- Forward return by sector: "**No sector had a measurable forward return at this horizon.**"
- Forward return by rank band: all three bands present, each "—" with n=0 ⚠.
- No fabricated "0%" / "0.00%" anywhere; low-sample ⚠ marker present on n=0 rows.

### UT-09 — Empty rank bands still listed; per-stock empty side renders copy
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-2-evidence/UT-08-09-backtest-latest-NA.png`
- In the all-NA state, every configured rank band (1–10, 11–50, 51+) still appears as a row with an em-dash "—" mean and n=0 ⚠ — no band is dropped and none shows a fabricated 0.
- The band label set exactly matches the config (`config.yaml → walk_forward.attribution.rank_bands`: "1–10", "11–50", "51+") — no missing or invented band.
- When the per-stock panel has no observations it renders the explicit empty-state copy ("No ticker had a measurable forward return at this horizon.") rather than disappearing.
- Note: the finer sub-case "only one of Contributors/Detractors is empty → single '—' placeholder" was not reproducible with the seed data, because the two columns are the top-k and bottom-k of the **same** observation set — they are populated or empty together. The whole-panel empty-state path was verified instead. This does not affect the P2 verdict.

### UT-10 — Regression: existing System Health panels unchanged
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-2-evidence/UT-01-02-03-system-health-attribution.png`
- All six pre-existing panels render above the new section: "Forward return by score bucket", "Excess vs benchmarks", "Forward return by setup type", "Forward return by market regime", "Forward return: VCP vs non-VCP", "Control-group comparison — selection vs sector beta".
- The additive "Return attribution" section is appended at the bottom only (heading index 7, after the control-group panel at index 6). No panel removed or visually broken.

### UT-11 — Regression: Backtest single global date control intact (J-13 / J-14 / J-18)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-2-evidence/UT-11-12-backtest-inapp-nav-asof-preserved.png`
- Exactly **one** date control on the page (`document.querySelectorAll('select').length === 1`): the top-bar "View as-of date" dropdown. No second in-page date picker.
- The in-section "Horizon" buttons are labelled 1d/5d/10d/20d/60d (a **view** selector), not dates.
- Changing the global as-of (Latest → 2024-08-28 via the dropdown) updated the "Forward-test scorecard", the "Viewing as-of {date}" badge, **and** the attribution figures together.
- In-app navigation (Backtest → System Health → Backtest via sidebar) **preserved** the in-memory as-of (badge still "2024-08-28 (historical)", dropdown still 2024-08-28) — confirming no page-local/independent date state was introduced by the J-19 additions (the iter-1 J-18 consolidation holds).

### UT-12 — Feature is discoverable from existing navigation
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-2-evidence/UT-11-12-backtest-inapp-nav-asof-preserved.png`
- The left sidebar contains both "System Health" and "Backtest" links (full nav: Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, System Health, Watchlist, Methodology). No new nav item was needed.
- A single in-app sidebar click reaches each page; the "Return attribution" section is then reachable by scrolling (one click + scroll).
- The section's heading and one-line explanatory copy ("Open the N-day forward return: which tickers drove or dragged it…") make the purpose clear without developer knowledge.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Notes / Methodology / Caveats

1. **Concurrent browser-driving agent (environmental).** During this run, a second Claude agent — the
   functional **qa** agent (PID 145993, in QA-validation mode, also doing Chrome MCP checks at
   `:3835`) — was driving the **same** shared Chrome instance (`--remote-debugging-port=9222`) for its
   own TC-01…TC-16 plan. Initially this navigated my page mid-test (System Health → Backtest →
   Dashboard) because both MCP servers attached to the same single tab. I isolated my work by creating
   a **dedicated tab** (id `895EB8FE…`, index 0) and targeting every action with an explicit
   `tab_index`; the other agent stayed on its own tab. All UT results above were captured in my
   isolated tab and are unaffected. (The `TC-*.png` files in the evidence dir are the other agent's
   captures, not mine.)

2. **Console-error verification method.** The Chrome MCP build in use (superpowers-chrome 1.6.1) writes
   a placeholder `*-console.txt` ("Console logging not yet implemented"), so captured console files are
   not a reliable error source. I instead injected a runtime collector
   (`window.addEventListener('error'…)`, `unhandledrejection`, and a `console.error` wrapper) before
   interacting and read it back after each click/horizon-change — it returned `[]` (empty) for UT-01,
   UT-04, UT-06/07, and the UT-12 navigations. Combined with the fact that every dynamic panel rendered
   real data (a render-time JS error would have broken the React subtree), "no console errors" is
   substantiated.

3. **UT-07 background `/api/health` poll.** The single network request observed during horizon
   switching was `/api/health`, the app's periodic health-status indicator (timer-based, fires
   independent of the click). No `/api/backtest` / `/api/system-health` data refetch occurred, which is
   the actual intent of the J-18 regression guard. Reported transparently rather than filtered out.

4. **Data-contract cross-checks (read-only / no-recompute anti-goal).** Browser-rendered figures were
   compared to the canonical API on the same endpoints:
   - System Health: `dist.mean == overall.mean` and `dist.n == overall.n` exactly True at horizons 5
     and 20; by-sector n and by-rank-band n each sum to overall n (1218).
   - Backtest @ 2024-08-28: for **all** horizons (1d/5d/10d/20d/60d), `sector_n_sum == band_n_sum ==
     dist.n` (122) — the four slices partition the same stored observation set as the aggregate (no
     recomputed return). Per-stock lists 5 contributors + 5 detractors (= config `top_contributors_k:
     5`); band labels exactly match `config.yaml → walk_forward.attribution.rank_bands` (no magic
     numbers in calc code).

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend URL:** http://localhost:8835 (health at `/api/health`; `/health` returns 404 by design — the real APIs `/api/system-health`, `/api/backtest` returned 200)
- **Browser:** Chrome via superpowers-chrome MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), dedicated isolated tab
- **Test Date:** 2026-06-01
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-2-evidence/`
  - `UT-01-02-03-system-health-attribution.png` — System Health attribution (20d) + consistency
  - `UT-05-06-backtest-2024-08-28-1d.png` — Backtest historical date, default 1d slice
  - `UT-06-07-backtest-10d-switch.png` — Backtest after 10d view switch (scorecard unchanged)
  - `UT-08-09-backtest-latest-NA.png` — Backtest "Latest", honest all-NA state
  - `UT-11-12-backtest-inapp-nav-asof-preserved.png` — single date control + in-app-nav as-of preserved
  - `UT-01-system-health-firstload.png` — System Health first-load (supporting)
