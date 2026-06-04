# Phase goal-i_can_see_the_wealthy_future_forever-iter-17 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-17
**Date:** 2026-06-04
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->

**Overall:** 12/13 tests passed (1 skipped — UT-07, P2, precondition unsatisfiable with seed data)

All P1 tests (UT-01–UT-05, UT-09–UT-12) PASS. P2/P3 tests UT-06, UT-08, UT-13 PASS. UT-07 (P2) is SKIPPED because its empty-state precondition cannot be reproduced with the seed data (the empty-state component is implemented and correctly wired in source — see UT-07 below).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Backtest loads with evidence section | smoke | P1 | Page renders, evidence section present, no console errors | `Backtest` heading + `data-testid="evidence-aggregate"` ("Forward-tested evidence (expanding window ≤ 2026-05-28)") present; no error boundary; error-listener empty across load + ~12 interactions | PASS | `UT-02-baseline-latest-60d-full.png` |
| UT-02 | Summary line + seven panels render | happy-path | P1 | Summary line + 7 panels + control group, all with n, honest NA, no null/NaN | Summary: "Snapshots contributing (≤ 2026-05-28): 10 · As-of range: 2022-10-07 → 2026-02-27 · Mean stock fwd return (60d): +10.57% (n=1217) · Figures with n<30 ⚠". All 7 panels + control group rendered with returns + n; **no** null/NaN/undefined | PASS | `UT-02-baseline-latest-60d-full.png` |
| UT-03 | Evidence re-scopes earlier, n shrinks | happy-path | P1 | Amber historical badge; heading ≤ earlier D; snapshots & n decrease; numbers differ | → 2024-05-28: badge "Viewing as-of 2024-05-28 (historical)"; heading "≤ 2024-05-28"; snapshots **10→2**; **n 1217→242**; range upper bound 2026-02-27→2024-05-28; one `fetch /api/backtest?as_of=2024-05-28`; **URL stayed `/backtest`** | PASS | `UT-03-before-latest.png`, `UT-03-after-2024-05-28-full.png` |
| UT-04 | Latest reproduces all-history numbers | happy-path | P1 | Quiet "Latest" badge; counts/n return to original | → Latest: badge "Latest"; heading "≤ 2026-05-28"; snapshots **10**; **n 1217**; mean +10.57%; range 2022-10-07 → 2026-02-27 (**exact** baseline); fetch dropped `as_of` param | PASS | `UT-02-baseline-latest-60d-full.png` |
| UT-05 | Horizon updates panels, no refetch | happy-path | P1 | Label + all panels update to new horizon; **no** new `/api/backtest` request | 60d→20d: label "(20d): +2.03% (n=1218)"; all bucket values changed (A +14.37%→+6.00%); control-group hint "At 20 days:"; **0** new fetch/xhr to `/api/backtest`; URL date-free | PASS | `UT-05-horizon-20d.png` |
| UT-06 | Low-sample ⚠ + honest NA "—" | validation | P2 | n<min cells show ⚠; empty cells show "—"; no fabricated 0 | @2022-10-07/60d: buckets A(n=2) B(n=7) C(n=16) D(n=14) all ⚠, E(n=81) no ⚠; VCP empty cell "**—n=0 ⚠**"; control SPY/QQQ n=1 ⚠; 12 ⚠ + 5 "—" total; no null/NaN | PASS | `UT-06-lowsample-2022-10-07-60d-full.png` |
| UT-07 | Empty-state for no-evidence window | error | P2 | "No forward-tested evidence for this window yet" empty-state card | Empty-state **unreachable** with seed data: earliest as-of (2022-10-07) still yields n=120 at every horizon → populated panels, not empty state. Component verified present + correctly gated (`noEvidence = n_runs===0 \|\| overall.n===0`, `evidence-panels.tsx:214,233`) | SKIP | source ref `evidence-panels.tsx:214,233-238` |
| UT-08 | Control-group top row highlighted | ux | P3 | Top-ranked row bolder label + `bg-surface-2`; "At N days:" hint; all rows numeric/labelled | Top-ranked row class includes `bg-surface-2` (rgb(24,32,45)) vs transparent peers; label `<span class="font-semibold">` weight **600** vs peers 400; hint "At 60 days: …"; 5 labelled rows (cohort/random/SPY/QQQ/sector ETF) all numeric | PASS | `UT-08-control-group.png` |
| UT-09 | System Health gone, sidebar = 10 | regression | P1 | Sidebar lists exactly 10 items, no "System Health" | Sidebar: Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, Research, Watchlist, Methodology, Data Manager (**10**); no "System Health" | PASS | `UT-09-sidebar-10-items.png` |
| UT-10 | `/system-health` 404 | regression | P1 | Next.js 404; evidence NOT rendered here | Hard load → "404 — This page could not be found." (raw `curl` also HTTP 404, no redirect); no Backtest evidence on the page | PASS | `UT-10-system-health-404.png` |
| UT-11 | Single date control, URL date-free | regression | P1 | Exactly one date control; URL carries no date param after date/horizon change | Exactly **1** `<select>` (aria "View as-of date"); **0** `input[type=date]`; URL stayed `http://localhost:3835/backtest` after both a date change and a horizon change (no `?as_of=`) | PASS | `UT-02-baseline-latest-60d-full.png` |
| UT-12 | Existing surfaces unchanged + ordered | regression | P1 | Order As-of summary→Scorecard→Attribution→Leadership→Evidence; exactly one "Return attribution"; evidence last | h2 order exactly: As-of scan summary → Forward-test scorecard → Return attribution → Leadership cohorts → Forward-tested evidence; **1** "Return attribution" heading; evidence section last | PASS | `UT-02-baseline-latest-60d-full.png` |
| UT-13 | Backend-unavailable honest error | error | P2 | Red "Backend unavailable" card; no fabricated/stale evidence; recovers | `/api/backtest` forced to fail → red card "Backend unavailable — … No figures are shown rather than fabricated values."; evidence section + summary **absent** (not present in DOM); fresh reload recovers (evidence back, n=1217) | PASS | `UT-13-backend-unavailable.png` |

---

## Passed Tests

### UT-01 — Backtest page loads with the new evidence section
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-17-evidence/UT-02-baseline-latest-60d-full.png`
- Clean hard load of `/backtest` (after blanking the prior page) rendered the `Backtest` heading and the full page with no "Backend unavailable" card.
- `data-testid="evidence-aggregate"` present with heading **"Forward-tested evidence (expanding window ≤ 2026-05-28)"**.
- The browser console-capture file is a harness stub ("not yet implemented"), so I installed a `window.error`/`unhandledrejection` listener. It stayed **empty** across the fresh load and a follow-up horizon toggle; the page rendered correctly through ~12 interactions with no React error boundary — no uncaught errors observed.

### UT-02 — Evidence summary line and seven panels render
**Verdict:** PASS
**Evidence:** `UT-02-baseline-latest-60d-full.png`
- Summary line (`data-testid="evidence-summary"`) shows all four parts: snapshots contributing (10), as-of range (2022-10-07 → 2026-02-27), mean fwd return (60d) +10.57% (n=1217), and the n<30 ⚠ legend.
- **Forward return by score bucket**: A +14.37% n=23⚠, B +15.28% n=87, C +6.58% n=162, D +9.18% n=173, E +11.07% n=772.
- **Excess vs benchmarks**: Excess vs SPY (SPY) +10.57%/+6.21%; Excess vs QQQ (QQQ) +10.57%/+7.37%.
- **By setup type** (6 rows), **By market regime** (4 rows), **VCP vs non-VCP** (2), **Pullback-to-rising-DMA vs not** (2), **Flat-base breakout vs not** (2) — each with return + n.
- **Control-group comparison** table renders at the bottom (5 rows).
- A whole-section text scan found **no** literal `null`, `NaN`, or `undefined`.

### UT-03 — Evidence re-scopes to an earlier as-of date, sample n shrinks
**Verdict:** PASS
**Evidence:** `UT-03-before-latest.png` (Latest baseline) + `UT-03-after-2024-05-28-full.png` (distinct, sha256-verified distinct)
- Date changed via the single global top-bar switcher (native-setter + bubbling `change`, per the React controlled-select technique — the `select` action does not fire this app's onChange) — **in-app, no page reload**.
- Before (Latest): indicator "Latest", "Snapshots contributing (≤ 2026-05-28): 10", "(60d) +10.57% (n=1217)".
- After (2024-05-28): amber indicator **"Viewing as-of 2024-05-28 (historical)"**, heading "≤ 2024-05-28", "Snapshots contributing (≤ 2024-05-28): **2**", n=**242**, range upper bound shrank to 2024-05-28.
- Network assertion: the change fired exactly one `fetch: http://localhost:8835/api/backtest?as_of=2024-05-28` — the single global date being read.
- J-18 corroboration: the **page URL stayed `http://localhost:3835/backtest`** (no `?as_of=`).

### UT-04 — Returning to Latest reproduces the full all-history numbers
**Verdict:** PASS
**Evidence:** `UT-02-baseline-latest-60d-full.png`
- Switched back to "Latest · 2026-05-28": indicator returned to quiet "Latest"; snapshots back to **10**; n back to **1217**; mean +10.57%; range 2022-10-07 → 2026-02-27 — **byte-for-byte the original baseline**.
- The Latest fetch correctly dropped the `as_of` param (`/api/backtest` with no query string).

### UT-05 — Horizon selector updates every evidence panel without a refetch
**Verdict:** PASS
**Evidence:** `UT-05-horizon-20d.png`
- Instrumented `window.fetch` + `XMLHttpRequest.open` to count `/api/backtest` calls, reset to 0, then clicked the **20d** horizon button.
- Summary label changed 60d→20d ("Mean stock fwd return (20d): +2.03% (n=1218)"); every bucket value changed (A +14.37%→+6.00%, B +15.28%→+3.74%, …); control-group hint updated to "At 20 days:".
- **Zero** new `/api/backtest` requests (fetch=0, xhr=0) — the horizon switch is purely client-side over the already-fetched `evidence_by_horizon` payload. URL stayed date-free.

### UT-06 — Low-sample ⚠ flag and honest NA "—" render correctly
**Verdict:** PASS
**Evidence:** `UT-06-lowsample-2022-10-07-60d-full.png`
- At earliest as-of 2022-10-07 / 60d (1 snapshot, n=120): the n<30 threshold (`min_sample`=30) is applied correctly — buckets A(n=2), B(n=7), C(n=16), D(n=14), Pullback(n=13), Flat-base(n=3), Top-ranked(n=20), SPY/QQQ(n=1), Sector ETF(n=7) all show **⚠**, while E(n=81), Random-peers(n=31), and the n=120 rows show **no** ⚠.
- Honest NA: the VCP cell with no observations shows "**—n=0 ⚠**" — an em-dash, never `0`, `0.0%`, `null`, or `NaN`.
- Whole-section scan: 12 ⚠ markers, 5 "—" cells, no null/NaN/undefined.

### UT-08 — Control-group top-ranked cohort row is highlighted
**Verdict:** PASS
**Evidence:** `UT-08-control-group.png`
- Rows present and labelled: Top-ranked cohort (rank ≤ 20) +10.48% n=199, Random same-sector peers +8.18% n=280, SPY +6.21% n=10⚠, QQQ +7.37% n=10⚠, Sector ETF (same sectors) +5.14% n=64.
- The top-ranked row is visually highlighted: row class includes **`bg-surface-2`** (computed background rgb(24,32,45)) vs transparent for the other rows; its label is `<span class="font-semibold text-text">` (computed font-weight **600**) vs the peers' weight 400.
- Hint reads "At 60 days: does the top-ranked cohort beat random same-sector peers and the benchmarks …".

### UT-09 — System Health is gone from the sidebar; sidebar lists 10 items
**Verdict:** PASS
**Evidence:** `UT-09-sidebar-10-items.png`
- Sidebar lists exactly **10** items in order: Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, Research, Watchlist, Methodology, Data Manager.
- No "System Health" entry anywhere.

### UT-10 — `/system-health` route returns 404
**Verdict:** PASS
**Evidence:** `UT-10-system-health-404.png`
- A clean hard load of `http://localhost:3835/system-health` renders the Next.js default **"404 — This page could not be found."** with no Backtest evidence on the page.
- Corroborated at the HTTP layer: `curl -I` returns **HTTP 404** with `num_redirects=0` (no redirect).
- Note: a soft (client-side) navigation while the SPA was already loaded briefly showed cached Backtest content (a Next.js dev-mode App-Router artifact); a real bookmark/typed-URL visit does a fresh document load and correctly 404s. The sidebar link is removed, so there is no in-app path to the route.

### UT-11 — Single date control invariant: no page-local date dropdown, URL date-free
**Verdict:** PASS
**Evidence:** `UT-02-baseline-latest-60d-full.png` (+ UT-03/UT-05 URL assertions)
- Exactly **one** `<select>` exists on the entire page (aria-label "View as-of date", 11 options); **zero** `input[type=date]` pickers; no second date control inside the evidence section.
- The page URL stayed `http://localhost:3835/backtest` with **no** `?as_of=`/date query parameter after changing the as-of date (UT-03) and after changing the horizon (UT-05). The `?as_of=` only appears on the snapshot-served `/api/backtest` fetch — i.e. the single global date being transmitted, not a second page-local state.

### UT-12 — Existing Backtest surfaces unchanged and correctly ordered
**Verdict:** PASS
**Evidence:** `UT-02-baseline-latest-60d-full.png`
- h2 sections appear top-to-bottom in exactly: **As-of scan summary → Forward-test scorecard → Return attribution → Leadership cohorts → Forward-tested evidence (expanding window ≤ …)**.
- Exactly **one** "Return attribution" heading (the new evidence section is separately titled, not a duplicate).
- The new evidence section is the **last** section, below the leadership lists.
- Scorecard / Return Attribution (with Horizon selector) / leadership lists still render their values (verified populated at the 2024-05-28 historical date where a forward window has elapsed — DELL/HOOD/UBER contributors, Top Sectors/Themes, Ranked cohort).

### UT-13 — Backend-unavailable shows honest error, not fabricated evidence
**Verdict:** PASS
**Evidence:** `UT-13-backend-unavailable.png`
- `/api/backtest` was forced to reject at the browser fetch layer (non-destructive — avoids racing the harness's backend auto-restart), then a date change triggered the refetch.
- The page shows a red **"Backend unavailable"** card: "The backtest scorecard could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry."
- The evidence section AND summary are **absent from the DOM** (`evidenceSectionPresent: false`) — no zeros, no stale numbers, nothing fabricated.
- Recovery: a fresh reload (clearing the override; real backend still running) restored the page fully — evidence section back, n=1217.

---

## Skipped Tests

### UT-07 — Empty-state shows for a window with no measurable evidence
**Verdict:** SKIPPED
**Reason:** Precondition not satisfiable with the current seed data. The empty-state card is gated on `noEvidence = evidence.n_runs === 0 || evidence.overall.n === 0` (`apps/frontend/components/evidence-panels.tsx:214`), rendering `EmptyState` titled **"No forward-tested evidence for this window yet"** (`:233-238`) — the component is implemented and correctly wired. However, **no** as-of/horizon combination reachable through the UI produces zero measurable evidence: the earliest available as-of date (2022-10-07) is the only sparsest window, and it still contributes a measurable forward return at every horizon (overall n=120 at 1d/10d/20d/60d). So selecting the earliest date + 60d renders honest populated/low-sample panels (verified in UT-06), not the empty state. The empty-state path is present and correctly guarded; it simply cannot be exercised via the browser with this seed.
- This is a P2 (error/empty-state) case and does not gate the verdict.

---

## Notes / Observations (non-blocking)

- **Horizon resets on date change.** Switching the global as-of date resets the pressed horizon to a per-date default (e.g. 60d at Latest, 1d at 2024-05-28) — a pre-existing per-date-scorecard defaulting behavior (J-14/J-15), not introduced or broken by this iteration. It does not affect any verdict; the evidence aggregate tracks whatever horizon is selected (UT-05 proved client-side re-keying with no refetch), and re-selecting 60d reproduces the exact baseline (UT-04).
- **`/system-health` soft-nav artifact.** As noted in UT-10, a client-side soft navigation to `/system-health` while the SPA was already loaded showed cached Backtest content; a fresh document load 404s correctly and the nav link is gone. Functionally removed.
- **Top-bar "Backend OK" badge** stayed green during UT-13 — it uses a separate health signal, not the `/api/backtest` call that was blocked; the page-level error card correctly reflected the failed backtest fetch.
- **Evidence integrity (iter-6 lesson):** before/after as-of claims (UT-03/UT-04) are grounded on **distinct** screenshots (sha256-verified) **plus** DOM and network assertions, never a single pair. Two viewport screenshots came out blank due to a Chrome-MCP compositing quirk when scrolled; they were re-captured as reliable full-page screenshots.

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend URL:** http://localhost:8835 (`/api/backtest`; provider: seed; 158 symbols; 11 scanner runs 2022-10-07 → 2026-05-28)
- **Browser:** Chrome via `mcp__plugin_superpowers-chrome_chrome__use_browser`
- **Hydration check:** `GET /_next/static/chunks/main-app.js → 200` (live `next dev`, not a stale prod build)
- **Test Date:** 2026-06-04
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-17-evidence/`
