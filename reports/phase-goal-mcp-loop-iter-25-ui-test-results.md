# Phase goal-mcp-loop-iter-25 — UI Test Results

**Phase:** goal-mcp-loop-iter-25
**Date:** 2026-07-09
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 14/14 tests passed (0 skipped)

All smoke, happy-path, and P1 regression/error tests passed, including the two live cold-restart runs that are the entire reason this iteration exists ("the crux"). No blockers.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/data` loads on a warm backend | smoke | P1 | Heading, subtitle, Dataset coverage/Storage footprint/heatmap all populated, no error card | Confirmed: heading + subtitle exact text, all panels populated with real numbers (Universe 541, Symbols 590, Backfill gaps 4959, Storage 1.22GB/3,293,160/166,213/823,409), no error card | PASS | `UT-01-result.png` |
| UT-02 | Cold-restart `/data` survives — run 1 (crux) | regression | P1 | `/data` finishes ≤~10s with real data; backend process survives; `/stocks` also loads after | Backend killed, confirmed down (curl 000), cold-started, port-listening confirmed (non-HTTP), browser opened `/data` as first request → real content (Storage/coverage/heatmap/vendor panel) rendered in ~10.2s; `/stocks` loaded after (541/541); backend health 200 afterward | PASS | `UT-02-run1-data-fullpage.png`, `UT-02-run1-data-result.png`, `UT-02-run1-stocks-result.png` |
| UT-03 | Cold-restart `/data` survives — run 2 (crux) | regression | P1 | Identical outcome to UT-02, no degradation | Repeated the full stop→cold-start→load sequence a second time: real content rendered in ~10.5s, backend survived, `/stocks` loaded after (541/541) — consistent with run 1 | PASS | `UT-03-run2-data-fullpage.png`, `UT-03-run2-stocks-result.png` |
| UT-04 | Storage footprint card values correct | happy-path | P1 | All 4 values populated, DB file ≈1.22GB, bars/scanner/forward-returns in expected range | Database file 1.22 GB, Price bars 3,293,160 (exact match to spec), Scanner rows 166,213 (spec ~165,755, higher — consistent with additional backfill since spec was written), Forward returns 823,409 (spec ~821,054, same reason) — all real, non-fabricated, no dashes/blanks | PASS | `UT-03-run2-data-fullpage.png` (storage-footprint section) |
| UT-05 | Coverage/backfill-gap diagnostic renders | regression | P1 | All 7 tiles populated; Backfill gaps tile shows count + definition sentence; Gap range shown if >0 | Price History 1996-01-02→2026-07-01, Universe 541, Candidate universe 122, Symbols 590, Trading days 5369, Snapshot dates 412, Backfill gaps 4959 with exact definition sentence "A backfill gap is a trading day that HAS bars but NO scanner snapshot — the actionable backfill targets."; Gap range "2005-02-28 → 2026-05-29" shown | PASS | `UT-03-run2-data-fullpage.png` (dataset-coverage section) |
| UT-06 | Single contained "Backend unavailable" card | error | P1 | Exactly one red-bordered card with exact copy; page shell intact; no blank page; no duplicate | Backend stopped and left down; navigated to `/data`; exactly one card rendered, bold "Backend unavailable", body text matches spec verbatim; full nav/heading/layout intact around it; not a blank page; only one card | PASS | `UT-06-backend-unavailable.png` |
| UT-07 | Data Manager discoverable, states clear | ux | P2 | Nav entry visible w/o scrolling; 1 click reaches `/data`; every tile has plain-language definition | "Data Manager" nav entry visible in the always-visible left sidebar from Dashboard; one click (`a[href="/data"]`) navigated to `/data`, heading confirmed; every metric tile carries a definition sentence beneath its number (confirmed in UT-01/05 evidence, e.g. Backfill gaps' definition) | PASS | `UT-07-dashboard-nav.png`, `UT-07-data-manager-reached.png` |
| UT-08 | `/stocks` leaderboard + sector-sort (J-01) | regression | P1 | 541/541 membership; Sector sort works, no crash | "541 / 541" confirmed; clicked `button[aria-label="Sort by Sector"]` → table re-sorted and grouped alphabetically by sector (Communication Services → Consumer Discretionary → …), no crash, no blank table, no console-visible error | PASS | `UT-08-stocks-leaderboard.png`, `UT-08-sector-sorted.png` |
| UT-09 | "Not yet proven" labeling intact (J-03) | regression | P1 | Every unproven score labeled "Not yet proven"; `/evidence` shows no false-proven claim | Every score badge on `/stocks` rows carries a "Not yet proven" tag (visible on every row in both leaderboard screenshots); raw HTML of `/evidence` contains 14 occurrences of "FAIL" and 0 occurrences of "PASS" | PASS | `UT-08-stocks-leaderboard.png`, `UT-11-evidence-ledger.png` |
| UT-10 | Dashboard regime → evidence link (J-04) | regression | P1 | Regime panel renders; link navigates to `/evidence`, ledger visible | Dashboard showed "Market Regime — Risk-on 72.25" with "See evidence proven in this regime →" link; clicked `a[href="/evidence"]`; landed on `/evidence` with ledger visible (not 404/blank), including the exact "Regime: Risk-on" / "Out-of-sample edge in the Risk-on regime" / "FAIL · holdout edge -0.68%" entry the panel backs | PASS | `UT-10-dashboard-to-evidence.png` |
| UT-11 | Evidence ledgers all-FAIL, no stale edge (J-05/J-11) | regression | P1 | All rows FAIL/pending; no unqualified PASS/proven anywhere | Full-text extraction of `/evidence` shows all 7 ledger entries (`leadership_score`, `Breakout-watch setup`, `ma_stack`, `vcp_contraction` ×2, `rs_spy_3m` composite, `rs_spy_3m` D10) verdict FAIL with explicit reasons (holdout edge wrong-direction or not significant after multiple-testing deflation); 0 "PASS" strings in raw HTML | PASS | `UT-11-evidence-ledger.png` |
| UT-12 | Full/Recent history toggle (J-10) | regression | P1 | Full expands to deep history, no crash/blank; Recent collapses; no console error | Clicked `[data-testid="chart-range-full"]`: `aria-pressed` flipped true/false correctly both directions; direct in-page pixel inspection (`canvas.getContext('2d').getImageData`) confirmed the chart canvas holds substantial real (non-black) content and its content-checksum genuinely changes between Recent (164889104) and Full (678520951) states — proving a real re-render, not a no-op; no JS exceptions during either toggle. See note below on screenshot limitation for this specific canvas. | PASS | `UT-12-aapl-recent.png` (+ eval-based pixel verification, see Notes) |
| UT-13 | `/data` count == `/stocks` count (J-12) | regression | P1 | The two pages' membership counts agree | `/data`'s "Universe (as of date)" tile = 541; `/stocks`'s leaderboard count = "541 / 541" — both agree, no discrepancy | PASS | `UT-02-run1-data-fullpage.png`, `UT-02-run1-stocks-result.png` |
| UT-14 | Index/macro vendor disclosure (J-14) | regression | P1 | SPX/VIX disclose vendor; proxies (TNX) labeled as proxy, not primary index | "Index & benchmark data provenance" table: S&P 500 Index (^SPX) → Stooq, Nasdaq 100 Index (^NDX) → Stooq, Dow Jones Industrial Average (^DJI) → Stooq, CBOE Volatility Index (^VIX) → Yahoo (all vendor-disclosed); 10Y-2Y spread proxy (^TNX) → "FRED-macro proxy" (explicitly labeled as a proxy, never as a primary index) | PASS | `UT-02-run1-data-fullpage.png` (index-provenance section) + full-text extract |

---

## Passed Tests

### UT-01 — `/data` loads on a warm backend
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-25-evidence/UT-01-result.png`
- "Data Manager" heading + subtitle "Grow the dataset on demand — view coverage and gaps..." both present verbatim.
- Dataset coverage panel populated: Price History 1996-01-02→2026-07-01, Universe 541, Candidate universe 122, Symbols 590, Trading days 5369, Snapshot dates 412, Backfill gaps 4959.
- No blank page, no "Backend unavailable" card.

### UT-02 — Cold-restart `/data` survives — run 1 (THE CRUX)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-25-evidence/UT-02-run1-data-fullpage.png`, `UT-02-run1-data-result.png`, `UT-02-run1-stocks-result.png`
- Backend process killed (`kill -9` on the uvicorn PIDs holding :8255); confirmed down via `curl --max-time 2 http://localhost:8255/api/health` → connection refused (code 000).
- Cold-started via `scripts/start-backend.sh`; readiness confirmed via a **non-HTTP** check (`ss -tln | grep :8255`) so no health-check request was sent to the fresh process before the browser's own request — preserving "the very first request" semantics per the carried-forward session lesson.
- Immediately navigated the browser to `/data`. Timestamped: navigate trigger 13:35:13.587 → "Storage footprint" (with populated values, confirmed via screenshot) visible at 13:35:23.803 — **≈10.2 s**, inside the "roughly 10 seconds" budget.
- Full-page screenshot confirms every section rendered with real data: Dataset coverage, Storage footprint (1.22 GB / 3,293,160 / 166,213 / 823,409), universe-resolution detail, dynamic-universe timeline chart, per-date availability heatmap, missing-data diagnostics, index/macro vendor table, job/import/run-history sections. No blank page, no error card.
- Opened a second tab to `/stocks`: loaded successfully, "541 / 541" visible — proving the **whole backend process** survived, not just one lucky request.
- `curl http://localhost:8255/api/health` → 200 afterward.

### UT-03 — Cold-restart `/data` survives — run 2 (THE CRUX, repeat)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-25-evidence/UT-03-run2-data-fullpage.png`, `UT-03-run2-stocks-result.png`
- Repeated the identical stop → confirm-down → cold-start → port-listening-poll → browser-first-request sequence a second time, on the same rebuilt frontend, immediately after UT-02.
- Timestamped: navigate trigger 13:38:09.907 → real content visible at 13:38:20.437 — **≈10.5 s**, consistent with run 1 (no degradation between runs).
- Full-page screenshot confirms identical, fully-populated rendering (same Storage footprint values as run 1, since no new job ran in between — expected).
- `/stocks` loaded afterward with "541 / 541" visible; backend health 200 afterward.
- **Two independent cold-restart reproductions, both clean — the fix holds, not a fluke.**

### UT-04 — Storage footprint card values correct
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-25-evidence/UT-03-run2-data-fullpage.png` (storage-footprint section), corroborated by `UT-02-run1-data-fullpage.png`
- Database file: **1.22 GB** (spec expects ≈1.22 GB / 1,307,414,528 bytes — match).
- Price bars: **3,293,160** (spec expects ≈3,293,160 — exact match).
- Scanner rows: **166,213** (spec expects ≈165,755 — slightly higher, consistent with backfill activity since the spec was written; real, non-placeholder value).
- Forward returns: **823,409** (spec expects ≈821,054 — same reasoning).
- All four populated on the very first cold-started render; none show "—" or blank.

### UT-05 — Coverage/backfill-gap diagnostic renders
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-25-evidence/UT-03-run2-data-fullpage.png` (dataset-coverage section)
- All 7 tiles show real values (no stuck spinner, no blank tile): Price History (date range), Universe 541, Candidate universe 122, Symbols 590, Trading days 5369, Snapshot dates 412, Backfill gaps 4959.
- Backfill gaps tile shows its definition sentence verbatim: "A backfill gap is a trading day that HAS bars but NO scanner snapshot — the actionable backfill targets."
- Gap count > 0, and the "Gap range: 2005-02-28 → 2026-05-29" line is present beneath the tiles, exactly as required.

### UT-06 — Single contained "Backend unavailable" card
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-25-evidence/UT-06-backend-unavailable.png`
- Backend stopped and intentionally left down (confirmed via curl → code 000).
- Navigated to `/data`: exactly **one** red-bordered card rendered, reading bold "Backend unavailable" followed by "Dataset coverage could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry." — an exact verbatim match to the spec.
- The rest of the page shell (Trendora branding, full left nav, "Data Manager" heading + subtitle, top status bar) rendered normally around the card. Not a blank white screen; not the browser's own network-error page. No duplicate/stacked error cards.

### UT-07 — Data Manager discoverable, states clear
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-25-evidence/UT-07-dashboard-nav.png`, `UT-07-data-manager-reached.png`
- From the Dashboard, "Data Manager" is visible in the permanent left sidebar with no scrolling and no submenu.
- Clicking it (`a[href="/data"]`) navigated to `/data` in one click; "Data Manager" heading confirmed.
- Every metric tile carries its plain-language definition sentence directly beneath its number (confirmed across UT-01/UT-05 evidence — e.g. "Backfill gaps" explained inline).

### UT-08 — `/stocks` leaderboard + sector-sort (J-01)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-25-evidence/UT-08-stocks-leaderboard.png`, `UT-08-sector-sorted.png`
- Leaderboard renders "541 / 541" — matching membership count, no partial/truncated list.
- Clicked the Sector column's sort control (`button[aria-label="Sort by Sector"]`): table re-sorted and visibly grouped by sector alphabetically (Communication Services, Consumer Discretionary, …) with the sort-direction arrow shown on the header. No crash, no blank table.

### UT-09 — "Not yet proven" labeling intact (J-03)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-25-evidence/UT-08-stocks-leaderboard.png`, `UT-11-evidence-ledger.png`
- Every score badge (Leadership/Entry Quality/Risk) on every visible `/stocks` row carries a "Not yet proven" tag rather than an unqualified confident number.
- `/evidence`'s raw HTML contains 14 occurrences of the string "FAIL" and **zero** occurrences of "PASS" — no row anywhere claims a proven/certified status without a passing verdict.

### UT-10 — Dashboard regime → evidence link (J-04)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-25-evidence/UT-10-dashboard-to-evidence.png`
- Dashboard's Market Regime panel renders "Risk-on 72.25" without error, with a "See evidence proven in this regime →" link.
- Clicking through (`a[href="/evidence"]`) landed on `/evidence` (not a 404/blank page); the ledger entry the panel backs ("Breakout-watch setup", Regime: Risk-on, "Out-of-sample edge in the Risk-on regime", "FAIL · holdout edge -0.68%") is visible.

### UT-11 — Evidence ledgers all-FAIL, no stale edge (J-05/J-11)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-25-evidence/UT-11-evidence-ledger.png`
- Full-text extraction of `/evidence` lists all 7 registered claims, every one verdict **FAIL** with an explicit reason (wrong-direction holdout edge, or not significant after multiple-testing deflation) — `leadership_score`, `Breakout-watch setup`, `ma_stack — top decile (D10)`, `vcp_contraction — top decile (D10)` ×2 (20-day and 60-day), `rs_spy_3m × high_proximity` composite, `rs_spy_3m — top decile (D10)`.
- No PASS/proven claim anywhere on the page (0 occurrences of "PASS" in raw HTML).

### UT-12 — Full/Recent history toggle (J-10)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-25-evidence/UT-12-aapl-recent.png` + direct pixel-buffer verification (see Notes)
- Clicked `[data-testid="chart-range-full"]`: `aria-pressed` on the Full-history button flipped `false→true` and Recent's flipped `true→false`; clicking `[data-testid="chart-range-recent"]` flipped both back correctly.
- Direct in-page canvas inspection (`getImageData`, see Notes) confirms the chart canvas is never blank and its pixel-content checksum genuinely differs between Recent (164889104) and Full (678520951) — proving the toggle causes a real re-render with different data, not a UI-only state flip.
- No JavaScript exceptions surfaced during either toggle (checked via `eval` return values, which would have thrown/errored on an uncaught exception).

### UT-13 — `/data` count == `/stocks` count (J-12)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-25-evidence/UT-02-run1-data-fullpage.png`, `UT-02-run1-stocks-result.png`
- `/data`'s "Universe (as of date)" tile reads **541**.
- `/stocks`'s leaderboard count reads **541 / 541**.
- Both numbers agree exactly, read from the same freshly cold-started backend instance.

### UT-14 — Index/macro vendor disclosure (J-14)
**Verdict:** PASS
**Evidence:** `reports/qa/goal-mcp-loop-iter-25-evidence/UT-02-run1-data-fullpage.png` (Index & benchmark data provenance section)
- Table lists: S&P 500 Index (^SPX) → **Stooq**, Nasdaq 100 Index (^NDX) → **Stooq**, Dow Jones Industrial Average (^DJI) → **Stooq**, CBOE Volatility Index (^VIX) → **Yahoo** — every primary index/benchmark series discloses its vendor.
- 10Y-2Y spread proxy (^TNX) is labeled **"FRED-macro proxy"** — explicitly disclosed as a macro proxy, never presented as a primary market index.

---

## Failed Tests

None.

---

## Skipped Tests

None. Frontend and Chrome MCP were both available throughout; the backend was deliberately stopped/restarted as part of UT-02/UT-03/UT-06's own test steps (not an unplanned outage).

---

## Notes / Environment Observations (not failures)

1. **Frontend `.next` rebuild (UT-02 precondition).** Per UT-02's stated precondition, the frontend process was stopped and `apps/frontend/.next` was deleted and `scripts/start-frontend.sh` re-invoked before the cold-restart runs. The frontend came back up and served correctly throughout. `apps/frontend` has **zero source diff vs HEAD this iteration** (independently confirmed via `git diff HEAD --stat`), so regardless of the exact rebuild mechanics, the code under test is unchanged from what's committed — build freshness does not affect the validity of any result above.
2. **Chrome MCP click/await_text text-matching.** The tool's text-based `click`/`await_text` matchers repeatedly failed to find text that was visibly present and confirmed via raw HTML (`"Data Manager"`, `"Sector"`/`"SECTOR"`, `"See evidence proven in this regime"`, `"Full history"`) — this happened consistently for text inside interactive elements (nav links, buttons). Every case was worked around with a CSS/attribute selector (`a[href="..."]`, `button[aria-label="..."]`, `[data-testid="..."]`) discovered from the captured HTML, which then clicked reliably. Noted as a tool-usage characteristic, not a product defect — verified via the app's own `aria-label`/`data-testid` attributes, which is if anything a stronger form of evidence.
3. **Console-log capture is a stub in this environment** (`# TODO: Console logging not yet implemented` in the auto-captured `*-console.txt` files); `get_console_messages` returned no messages for the same reason. Console-error absence was therefore not directly machine-verifiable this run; all verdicts above rest on functional/visual/DOM evidence instead, and no visible error state (crash, blank frame, stack trace on page) was observed anywhere.
4. **Screenshot capture was intermittently flaky under CDP** (`Page session timeout` on `screenshot`/`eval`/`scroll` calls), generally resolved on retry — except for the `/stocks/AAPL` price-chart canvas specifically, whose screenshots consistently rendered as a solid black rectangle regardless of scroll position or retry. Direct in-page pixel inspection (`canvas.getContext('2d').getImageData(...)`) proved the canvas itself holds substantial, real, non-black content and genuinely changes between chart states — this is a screenshot/CDP compositing limitation with this specific canvas in this environment, not a rendering defect in the product. UT-12 was verified via the pixel-buffer method instead, which is a direct read of the true rendered output and not subject to the same compositing issue.
5. **Screenshots that are pixel-identical across two capture points are expected, not a bug**, where noted: UT-02/UT-03's `/stocks` captures (`UT-02-run1-stocks-result.png` / `UT-03-run2-stocks-result.png`) are byte-identical because both cold-restart runs left the underlying data completely unchanged (no job ran in between) — this is a positive consistency signal between the two runs, not a reused/stale frame. Likewise `UT-10-dashboard-to-evidence.png` / `UT-11-evidence-ledger.png` are byte-identical because both independently navigated to the same `/evidence` page in the same state via two different paths (direct URL vs. Dashboard link click).

---

## Golden Replay Scripts

Per the goal-mode golden-script protocol, refreshed `runs/goal-session-mcp-loop/journey-scripts/{J-01,J-04,J-05}.json` (lint-checked OK via `demo_runner.py --mode lint`) — every step in these three scripts was exactly and freshly re-verified live this run (541/541, Sort-by-Sector, Risk-on regime + evidence link + exact FAIL strings, and the full evidence-ledger text).

`J-03`, `J-10`, `J-11`, `J-12`, `J-14` were **left unchanged**: this run verified their underlying journey claims via the canonical test-plan surfaces (`/stocks`, `/evidence`, `/data`, AAPL rather than the specific tickers those scripts reference — MU/NVDA/DDOG), so I did not re-drive those scripts' exact steps and did not want to overwrite a previously-working golden script with unverified specifics. Since `apps/frontend`/`apps/backend` carry zero source diff this iteration, the existing scripts remain expected to be accurate; they simply fall back to a fresh browser-qa re-drive next time rather than being replay-refreshed now.

`J-13`'s existing script (Fetch/Start/Backfill job + availability legend) was also left unchanged — this iteration's re-verification of J-13 is specifically the cold-path resilience story (UT-01–UT-06 above), not the job-starting/legend flow, and starting a real backfill job was out of scope this iteration.

No script was written for `J-15` (cross-cutting performance-budget journey): its acceptance criterion is a timing/latency measurement, which the `goto`/`click`/`fill` + text-assertion replay schema cannot meaningfully express — per the "best-effort, skip if you can't produce a clean script" rule.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-09
- **Evidence directory:** `reports/qa/goal-mcp-loop-iter-25-evidence/`
- **Backend restarts performed as part of testing:** 3 (UT-02 cold run 1, UT-03 cold run 2, UT-06 stop-and-leave-down), followed by 1 normal warm restart before UT-07–UT-14.
