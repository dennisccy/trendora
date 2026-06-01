# Phase goal-i_can_see_the_wealthy_future_forever-iter-3 — UI Test Results

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-3 (J-17 — Data Manager: grow the dataset by date / date range)
**Date:** 2026-06-01
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->

**Overall:** 15/16 tests passed (0 failed, 0 skipped, 1 N/A by design)

All 9 P1 tests passed: UT-01, UT-02, UT-03, UT-05, UT-06, UT-07, UT-08, UT-11, UT-15.
The full J-17 multi-step acceptance flow was exercised end-to-end (coverage → start backfill → live progress → final summary → new as-of date selectable without reload → resolves across dashboard → System Health `n` grew). The critical anti-goals were verified at the UI layer (live fetch real-data-only with explicit error + zero fabrication; invalid range rejected; `/data` date inputs do NOT touch the global as-of — J-18 intact).

---

## Environment

- **Frontend URL:** http://localhost:3835
- **Backend URL:** http://localhost:8835 (committed seed: 158 symbols; quarterly bootstrap snapshots)
- **Browser:** Chrome via MCP (superpowers-chrome), viewport 1440×900
- **Test Date:** 2026-06-01
- **Evidence directory:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-3-evidence/`

### Note on concurrent backend activity (does not affect verdict)
During this browser-QA session, additional fetch/backfill runs appeared on the shared `:8835` backend that this agent did **not** start (run history grew from 4 → 10 rows; `TC-16*/TC-17*/TC-18*` screenshots in the evidence directory confirm the **functional QA suite** was exercising the same backend). This is expected pipeline activity, not a product defect. To keep results unambiguous, each browser-driven job used a **unique date range** (backfill `2021-01-11→2021-01-15`; fetch `2021-01-19→2021-01-25`) and every assertion was cross-checked against the backend API. The concurrent runs explain (a) the Job-progress panel occasionally showing a job started elsewhere and (b) `n` growing by more than this agent's job alone — neither changes any verdict, because every claim below is tied to this agent's own uniquely-ranged job and confirmed via `/api/data` + `/api/runs`.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | Data Manager page loads | smoke | P1 | `/data` renders, heading + 4 panels, no error card | Heading "Data Manager"; all 4 panels (Dataset coverage / Start a fetch-backfill job / Job progress / Run history) present; no "Backend unavailable" card | PASS | UT-01-data-page-loaded.png |
| UT-02 | Coverage shows real metrics | smoke | P1 | Price range, ~158 symbols, trading days, snapshot dates, gaps (amber + gap range when >0) | Price `2021-01-04 → 2026-05-28`, Symbols `158`, Trading days `1356`, Snapshot dates `21`, Backfill gaps `1335` + "Gap range: 2021-01-11 → 2026-05-27"; no NaN/undefined/0 | PASS | UT-01-data-page-loaded.png |
| UT-03 | Job form pre-fills gap range | smoke | P1 | Start/End date pre-filled within gap range; kind defaults; Start enabled | Start `2021-01-11`, End `2021-01-15` (within gap range); Job kind = "Backfill snapshots"; Start enabled | PASS | UT-01-data-page-loaded.png |
| UT-04 | Job kind dropdown options | happy-path | P2 | Exactly 3 options, no empty/dupes; selection sticks | Options: "Backfill snapshots" / "Fetch EOD prices" / "Fetch + backfill"; selecting "Fetch EOD prices" → value `fetch` reflected | PASS | UT-10-fetch-honest-failure.png |
| UT-05 | Backfill job live progress (PRIMARY) | happy-path | P1 | Button busy "Job running…"; progress bar advances A/B; ends "ok" + summary | Button "Job running…" disabled; progress "snapshots 2/5 dates" + "1280 forward returns inserted" advancing; job id=8 ended **ok**, 5 snapshots, "3200 forward returns" (API-confirmed) | PASS | UT-05-job-running.png |
| UT-06 | Run history records job | happy-path | P1 | New row: Started, Kind, Range, Status, ok/failed, Snapshots, Summary | Row `11:04:29 · backfill · 2021-01-11 → 2021-01-15 · ok · 0/0 · 5 · "backfill: 5 snapshots over 5 dates, 3200 forward returns"` (2nd row only because a concurrent fetch was appended 20s later) | PASS | UT-07-UT-06-after-backfill.png |
| UT-07 | Backfilled date selectable w/o reload | happy-path | P1 | New dates appear in global switcher without hard reload; current selection unchanged | Same page instance (no reload since nav): switcher grew 21 → 36 options; all of `2021-01-11..15` present; selection unchanged ("Latest · 2026-05-28") | PASS | UT-07-UT-06-after-backfill.png |
| UT-08 | Backfilled date resolves on dashboard | regression | P1 | Selected backfilled date renders valid content on `/stocks` and `/` | Selected `2021-01-13`; `/stocks` shows full leaderboard ("122/122", ranked table); `/` shows Dashboard (regime "Choppy 45.02", net new highs, VIX gate); 50/200-DMA breadth correctly "NA" (insufficient look-back, not fabricated); as-of consistent on both | PASS | UT-08-stocks-backfilled-date.png, UT-08-dashboard-backfilled-date.png |
| UT-09 | System Health n grows | regression | P2 | `n` after backfill strictly greater; no error | Overall `n` 2368 → 4143; control SPY/QQQ `n` 20 → 35; bucket E `n` 1692 → 3066. No error on page | PASS | UT-09-systemhealth-before.png, UT-09-systemhealth-after.png |
| UT-10 | Fetch job honest provider failure | error | P2 | Ends failed/partial (not fake ok); per-symbol errors; "(no data fabricated)"; no claimed bars/snapshots | Fetch `2021-01-19→2021-01-25` ended **failed**: "0/158 ok, 158 failed, 0 new bars", "20 errors (no data fabricated)", per-symbol Stooq apikey errors; API: run id=10 failed, **0 bars, 0 snapshots**, coverage unchanged | PASS | UT-10-fetch-honest-failure.png, UT-10-fetch-failed-terminal.png |
| UT-11 | Form dates don't move global as-of (J-18) | validation | P1 | Changing form date changes only local form value; global as-of unchanged | End date `2021-01-15 → 2021-01-22` (change registered); global as-of stayed "" / "Latest · 2026-05-28" | PASS | UT-11-form-date-changed-asof-unchanged.png |
| UT-12 | Invalid range rejected, no fake job | validation | P2 | Explicit error, not a fake "ok" run; no bogus reversed-date row | `role=alert` "start date 2021-02-10 must be on or before end date 2021-01-20" (text-neg); no new job started; no reversed-date run (API: 0); backend POST → **HTTP 400**, malformed → **HTTP 422** | PASS | UT-12-invalid-range-rejected.png |
| UT-13 | Run history empty state | smoke | P3 | Empty-state card on a fresh DB | N/A — the seed/prior runs make history non-empty **by design** (seed-load row + backfill runs present). Empty-state component exists in source but this DB cannot be empty | N/A | UT-07-UT-06-after-backfill.png |
| UT-14 | Backend-unavailable error card | error | P2 | Styled "Backend unavailable" card; states no fabrication; no crash | Card shown (`border-neg`): "Backend unavailable — Dataset coverage could not load from the API. No figures are shown rather than fabricated values…"; no coverage numbers shown; page did not crash | PASS | UT-14-backend-unavailable-card.png |
| UT-15 | Data Manager discoverable in sidebar | ux | P1 | "Data Manager" w/ icon, last sidebar entry, on every page, routes + active highlight | Last of 10 nav items, has icon, present on all pages; click routes to `/data`; active (`aria-current="page"` + `bg-surface-2 font-medium` vs inactive `text-text-muted`) | PASS | UT-01-data-page-loaded.png |
| UT-16 | Loading skeleton on coverage load | ux | P3 | Skeleton while loading; replaced by real numbers; no flash of 0/undefined | `DataSkeleton` (animate-pulse) renders on `state.kind==="loading"` (verified in source); every load resolved to real numbers with no flash of 0/undefined; transient frame too brief to screenshot against the fast local backend | PASS | UT-01-data-page-loaded.png |

---

## Passed Tests

### UT-01 — Data Manager page loads (smoke, P1)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-i_can_see_the_wealthy_future_forever-iter-3-evidence/UT-01-data-page-loaded.png`
- Navigated to `http://localhost:3835/data`; `main h1` = "Data Manager".
- All four panels rendered: **Dataset coverage**, **Start a fetch / backfill job**, **Job progress** ("No job has been started this session…" idle placeholder), **Run history**.
- No "Backend unavailable" card; page not blank/404.

### UT-02 — Coverage panel shows real dataset metrics (smoke, P1)
**Verdict:** PASS
**Evidence:** `UT-01-data-page-loaded.png`
- Price history `2021-01-04 → 2026-05-28`; Symbols `158`; Trading days `1356`; Snapshot dates `21`; Backfill gaps `1335` with "Gap range: 2021-01-11 → 2026-05-27" line. No NaN/undefined/0. Cross-checked against `GET /api/data`.

### UT-03 — Job form pre-fills date range from gap dates (smoke, P1)
**Verdict:** PASS
**Evidence:** `UT-01-data-page-loaded.png`
- `Job start date` input = `2021-01-11`, `Job end date` = `2021-01-15` — real dates, both inside the coverage gap range. Job kind defaulted to "Backfill snapshots" (`backfill`). Start button enabled.
- Also confirmed dynamic: after backfilling `2021-01-11..15`, a later page mount re-prefilled the form to the next gap `2021-01-19 → 2021-01-25`, proving coverage is descriptive/live.

### UT-04 — Job kind dropdown exposes all three kinds (happy-path, P2)
**Verdict:** PASS
**Evidence:** `UT-10-fetch-honest-failure.png`
- Exactly three options: "Backfill snapshots" (`backfill`), "Fetch EOD prices" (`fetch`), "Fetch + backfill" (`both`) — no empty/duplicate. Selecting "Fetch EOD prices" set the value to `fetch` and the control reflected it.

### UT-05 — Start a backfill job and watch live progress to completion (happy-path, P1, PRIMARY)
**Verdict:** PASS
**Evidence:** `UT-05-job-running.png`, `UT-07-UT-06-after-backfill.png`
- Clicked Start (kind=backfill, range `2021-01-11→2021-01-15`). Button immediately became "Job running…" and disabled.
- Job progress panel went live: "backfill job · 2021-01-11 → 2021-01-15", status "running", "snapshots 2/5 dates", progress bar "Snapshots backfilled 2/5 dates", "2 snapshots · 1280 forward returns inserted" — counters advancing.
- Terminal state confirmed via API (run id=8): status **ok**, 5 snapshots created, "3200 forward returns"; all 5 dates `2021-01-11..15` present in `/api/runs`. Button returned to enabled "Start".

### UT-06 — Run history records the completed job (happy-path, P1)
**Verdict:** PASS
**Evidence:** `UT-07-UT-06-after-backfill.png`
- Row present: `2026-06-01 11:04:29 | backfill | 2021-01-11 → 2021-01-15 | ok | 0/0 | 5 | "backfill: 5 snapshots over 5 dates, 3200 forward returns"`. All columns correct; matches the live progress observed. History non-empty (no empty-state card).
- (Row sits 2nd, not top, only because a concurrent fetch job was appended 20s after mine — see concurrency note.)
- The history also shows create-once immutability in action: a `2021-01-04 → 2021-01-08` re-run row recorded `0 snapshots` (no-op on an already-snapshotted range).

### UT-07 — Backfilled date becomes selectable without reload (happy-path, P1)
**Verdict:** PASS
**Evidence:** `UT-07-UT-06-after-backfill.png`
- **No hard reload** occurred between job completion and this check (same page instance throughout). The global as-of switcher (`View as-of date`) grew from 21 → 36 options, now including all of `2021-01-11`, `…12`, `…13`, `…14`, `…15`.
- Current selection unchanged ("Latest · 2026-05-28") and "Latest" still `2026-05-28` — backfilling older dates did not switch the user's selection. Confirms the iter-1 `refresh()` additive behavior.

### UT-08 — Newly backfilled date resolves across the dashboard (regression, P1)
**Verdict:** PASS
**Evidence:** `UT-08-stocks-backfilled-date.png`, `UT-08-dashboard-backfilled-date.png`
- Selected `2021-01-13` in the global switcher; navigated via in-app links (no reload).
- `/stocks`: "as of 2021-01-13", full leaderboard "122 / 122", ranked table (AAPL…) — no error/empty/blank.
- `/`: "Data as-of 2021-01-13", Market Regime "Choppy 45.02/100", net new highs, VIX gate all compute. The 50-DMA/200-DMA breadth components correctly show **"NA"** (an early date with insufficient look-back) — honest, not a fabricated number. As-of consistent across both pages.

### UT-09 — System Health sample size (n) grows after backfill (regression, P2)
**Verdict:** PASS
**Evidence:** `UT-09-systemhealth-before.png`, `UT-09-systemhealth-after.png`
- Before (recorded first): bucket totals summed to 2368; control SPY/QQQ `n=20`; API overall `n=2368`, `n_runs=20`.
- After backfill: bucket E `n` 1692→3066, control SPY/QQQ `n=35`, overall `n=4143` (page max n = 4143). Strict increase; no error on page. This agent's 5 dates contributed; concurrent QA backfills added the remainder (the assertion `n_after > n_before` holds regardless).

### UT-10 — Fetch EOD prices job surfaces an honest provider failure (error, P2)
**Verdict:** PASS
**Evidence:** `UT-10-fetch-honest-failure.png`, `UT-10-fetch-failed-terminal.png`
- Started "Fetch EOD prices" for the unique range `2021-01-19→2021-01-25`. Job ended with a **failed** badge (not a fake "ok"): "fetch: 0/158 symbols ok, 158 failed, 0 new bars", "0 new price bars", "**20 errors (no data fabricated)**", with a per-symbol error list (NVDA/AMD/AVGO/MRVL/ANET: "stooq returned no usable data … Get your apikey…").
- A matching `failed` row was appended to Run history.
- Anti-goal verified via API: run id=10 = failed, **0 bars_fetched, 0 snapshots_created**; coverage unchanged (price_end still `2026-05-28`, 158 symbols); **zero snapshots** for the fetch-failed dates. No fabrication.

### UT-11 — /data date inputs do not change the global as-of date (validation, P1, J-18 guard)
**Verdict:** PASS
**Evidence:** `UT-11-form-date-changed-asof-unchanged.png`
- Changed the job-form End date `2021-01-15 → 2021-01-22` (change registered in the input). The global "View as-of date" switcher stayed at "" / "Latest · 2026-05-28" — unchanged. The form date inputs are job parameters only; J-18 "exactly one date selector" preserved. The page even states this explicitly: "These date inputs are job parameters — they do NOT change the global as-of viewing date."

### UT-12 — Invalid date range is rejected without a fake job (validation, P2)
**Verdict:** PASS
**Evidence:** `UT-12-invalid-range-rejected.png`
- Set Start `2021-02-10` > End `2021-01-20` and clicked Start. An explicit `role="alert"` message (text-neg styling) appeared: "start date 2021-02-10 must be on or before end date 2021-01-20". No new job started (progress panel kept the prior job); no reversed-date row in history (API confirmed 0).
- Backend also rejects defensively: `POST /api/data/jobs` with start>end → **HTTP 400** (same message); malformed date → **HTTP 422**.

### UT-14 — Backend-unavailable error card on /data (error, P2)
**Verdict:** PASS
**Evidence:** `UT-14-backend-unavailable-card.png`
- The shared backend is supervised by `run-phase.sh`, so rather than kill it, the "backend unreachable" condition was reproduced **non-destructively** at the browser layer: `window.fetch` was overridden to reject `/api/data`, then the `/data` route was remounted via client-side navigation (away → back) so its mount-time coverage fetch failed — exactly the network condition of a down backend, from the frontend's perspective.
- Result: a styled `border-neg` card with `AlertTriangle` rendered: "**Backend unavailable** — Dataset coverage could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry." No coverage numbers shown (no zeros/placeholders as real); page did not crash. The override was then cleared by a hard reload and the page recovered (coverage `2021-01-04 → 2026-05-28`, 158 symbols, 36 snapshot dates) — confirming the real backend was never touched and remained healthy (`/api/data` → HTTP 200).

### UT-15 — Data Manager is discoverable from the sidebar (ux, P1)
**Verdict:** PASS
**Evidence:** `UT-01-data-page-loaded.png`
- Sidebar NAV order: Dashboard, Stocks, Themes, Sectors, Scanner Runs, Backtest, System Health, Watchlist, Methodology, **Data Manager** (last). Has an icon; present on every page checked (`/`, `/stocks`, `/system-health`, `/data`). Clicking routes to `/data`; while on `/data` the link is active (`aria-current="page"` + `bg-surface-2 font-medium text-text`, vs inactive links' `text-text-muted`).

### UT-16 — Loading skeleton appears while coverage loads (ux, P3)
**Verdict:** PASS
**Evidence:** `UT-01-data-page-loaded.png`
- The `DataSkeleton` component (animate-pulse placeholders) is rendered while `state.kind === "loading"` (verified in `apps/frontend/app/data/page.tsx:144,487-500`). Across every load in this session, coverage resolved to real numbers with **no flash of `0`/`undefined`/NaN**. The skeleton frame itself is too brief to capture against the fast local backend, but the requirement (clean load, no flash, no permanent skeleton) is met.

---

## Failed Tests

None.

---

## Not Applicable

### UT-13 — Run history empty state on a fresh DB (smoke, P3)
**Verdict:** N/A (by design)
**Reason:** This test requires a DB with **no** fetch/backfill runs. The committed seed records a seed-load run and the environment already contains backfill runs (history had ≥4 rows at first load), so the run history cannot be empty here. The test plan itself flags this case as "informational/N/A if the seed already logs a run." The empty-state card ("No fetch / backfill runs yet") exists in the implementation but its condition is unreachable in this seeded environment.

---

## Summary of P1 outcomes (gate)

| P1 Test | Verdict |
|---------|---------|
| UT-01 Data Manager page loads | PASS |
| UT-02 Coverage shows real metrics | PASS |
| UT-03 Job form pre-fills gap range | PASS |
| UT-05 Backfill job live progress (PRIMARY) | PASS |
| UT-06 Run history records job | PASS |
| UT-07 Backfilled date selectable w/o reload | PASS |
| UT-08 Backfilled date resolves on dashboard | PASS |
| UT-11 Form dates don't move global as-of (J-18) | PASS |
| UT-15 Data Manager discoverable in sidebar | PASS |

**All P1 tests passed → Browser QA Verdict: PASS.**
