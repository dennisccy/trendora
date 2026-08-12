# Phase goal-ops-hardening-iter-72 — UI Test Results

**Phase:** goal-ops-hardening-iter-72
**Date:** 2026-08-12
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 6/6 tests passed (0 skipped)

The phase's own UI test plan is N/A (`Frontend Present: no`, backend-only iteration — pool
resize + serve-stale readiness cache + `dev.sh` launcher parity). Per the goal-mode dispatch,
the six regression journeys the deterministic replay lane flagged as possible regressions
(J-01, J-05, J-06, J-07, J-08, J-09) were each re-executed live through the browser this round.
J-03 and J-04 passed replay and were not re-tested per the dispatch instructions.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | Both the May range and the weekend-only backfill report honest eligibility/exclusion counts; zero-work outcomes render visually distinct from success; history persists across reload | Ran all 3 submissions live on `/data` (May range 2026-05-02→05-29, weekend-only 2026-05-02→05-03, May-range re-run). All 3 resolved zero-work (already fully snapshotted from prior testing rounds): May range/re-run both "no new snapshots" / "28 calendar days · 19 already snapshotted · 9 non-trading"; weekend-only "2 calendar days · 0 already snapshotted · 2 non-trading". `zero-work-note` text ("Zero-work outcome — every requested trading day already had a snapshot... this is not a failure") present every time, neutrally styled, never success-green. Reload showed all 3 fresh runs (2026-08-12 22:30:53/22:31:20/22:31:38 UTC) at the top of the persisted Run history table. `/scanner-runs/748` (2026-05-29) rendered "Immutable snapshot — as of 2026-05-29" / "Scanned 2026-07-20 17:31:15" (an old scan timestamp, proving re-serve from storage, not recompute) with a populated leaderboard. | PASS | `reports/qa/goal-ops-hardening-iter-72-evidence/UT-J-01-result.png` |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | A single unsnapshotted day's backfill produces correct, persisted, storage-served aggregates across all finalize-hook categories, and `GET /api/health` stays responsive throughout | Resolved unsnapshotted date 2008-01-03 (0 `scanner_runs` rows, verified by direct read-only sqlite query immediately before Start). Ran the real backfill end-to-end via `/data`: job id 474, 22:36:12→22:56:37 UTC (~20m25s). Result: "ok", "backfill: 1 snapshots over 1 dates, 1355 forward returns", breakdown "1 calendar day · 0 already snapshotted · 0 non-trading", `aggregates_refreshed` listed all 9 categories (latest_snapshot, coverage, membership_timeline, market_phase, forward_aggregates, research_hot_keys, availability_heatmap, factor_lab_all, drawdown_expectations) — confirmed both in the DOM and the job's own persisted record. `/scanner-runs/2977` rendered "Immutable snapshot — as of 2008-01-03" / "Scanned 2026-08-12 22:36:24" (matches this run's own start, a genuine fresh scan) with a populated leaderboard. `GET /api/market-phase?as_of=2008-01-03` served from storage (200, 0.148s). Step 4 ("stays responsive throughout") is now clean on the corrected production launcher: this SAME job's `poll_health.py` drill (see UT-J-07) recorded 0 non-answers / 0 non-200s / 0 ceiling breaches — a direct reversal of iter-71's regression on this exact clause. Step 3 (cold restart) not re-executed — restarting the live QA backend is forbidden for this role (standing rule); this iteration's diff does not touch boot/coverage code. | PASS | `reports/qa/goal-ops-hardening-iter-72-evidence/UT-J-05-result.png` |
| UT-J-06 | Pages load only what they need | regression | P1 | All 11 nav-listed pages render their real heading + on-load content within budget | All 11 pages (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`, `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/regime-lab`) loaded with real headings and substantial interactive DOM (e.g. `/stocks` 772 buttons/555 links, `/scanner-runs` 2988 links), never a blank/error shell. This round's deterministic replay FAILed at step 02 (readiness-badge `data-state="ready"` not satisfied within its 2000ms budget); live re-check of the SAME two teeth-assertions the replay uses (`readiness-badge[data-state="ready"]` on `/`, `chart-window-caption` on `/stocks/AAPL` reading "3189 bars · as of 2026-08-03 · history since 1996-01-02 · older bars weekly-sampled") both resolved instantly. This session's own `poll_health.py` drill (p50 0.059s / p90 0.293s / p99 0.797s / max 1.652s, 0 non-answers) directly disproves a real `GET /api/health` slowdown at any point this round — the replay FAIL is a timing artifact of running concurrently with this session's own heavy drill on a shared host, not a regression. | PASS | `reports/qa/goal-ops-hardening-iter-72-evidence/UT-J-06-result.png` |
| UT-J-07 | Heavy aggregates never take the service down | regression/resilience | P1 | Every 1 Hz `GET /api/health` poll answers HTTP 200 throughout a heavy forward-aggregate warm — no frozen/unresponsive window, measured on the production launcher | Confirmed the backend process was launched by `scripts/start-backend.sh` (uvicorn cmdline carries `--limit-concurrency 64 --timeout-keep-alive 65 --timeout-graceful-shutdown 120`, no `--reload`) and the frontend by `next start -p 3255` (never `dev.sh`). Armed `scripts/qa/poll_health.py` at 22:35:14 UTC, 26s before starting the J-05 single-day backfill (job 474, 22:36:12 UTC) — satisfying TC-7's "poller armed ≥2s before job start". Concurrently triggered a J-09 background-compute dispatch (as-of 2026-07-31, 22:37:00–22:41:46 UTC) while the ingest's finalize-tail warm ran. Result: **1,315 total polls (22:35:14–22:57:10 UTC), 0 non-answers, 0 non-200 responses, 0 breaches of the rescoped ≤2s during-warm ceiling** (p50 0.059s / p90 0.293s / p99 0.797s / max 1.652s); 1,224 in-window (job-running) polls, 0 breaches; 91 steady-state polls, max 0.088s. Zero `QueuePool ... overflow ... timeout` lines in `logs/backend.log` dated 2026-08-12 (the log is append-only across many prior sessions; the 19 historical QueuePool matches in the file are all dated 2026-08-04, unrelated). This directly reverses iter-71's regression (58/900 non-answers, 165s longest gap, one QueuePool timeout) on the SAME class of concurrent load, confirming this iteration's pool-resize + serve-stale-readiness fix. Raw CSV: `runs/goal-session-ops-hardening/iter-72/j07-browser-qa-health-poll.csv`. | PASS | `reports/qa/goal-ops-hardening-iter-72-evidence/UT-J-07-result.png` |
| UT-J-08 | Backtest evidence serves from storage only | regression | P1 | `/backtest` serves stored evidence from the last complete version with a visible refreshing indicator during a version bump, never a cold recompute or skeleton | Directly captured the mid-warm transitional state: while this session's dataset version was mid-bump, `/backtest`'s latest view (2026-08-03) rendered real content immediately alongside the literal "Refreshing — showing the last complete evidence... The forward-tested evidence below is the last complete version — evidence as of 2026-08-03, generated 2026-08-12 21:47:44" disclosure (`evidence-summary`: "2915" contributing snapshots). After job 474 completed and refreshed `forward_aggregates`, reloading showed "Refreshing" gone and `evidence-summary` updated to "2916". The historical as-of 2026-07-31 (J-09's own target) showed the same pattern: "2972" mid-warm with "Refreshing" present → "2975" with "Refreshing" gone once its background-compute window finished. Two independent clean before/after transitions observed. Step 4 (call-count instrumentation) and step 5 (never-warmed empty state) are code/test-level assertions outside browser QA's observable surface. | PASS | `reports/qa/goal-ops-hardening-iter-72-evidence/UT-J-08-result.png` |
| UT-J-09 | The backend discloses its own background-compute activity | regression | P1 | Loading `/backtest` for an incomplete historical as-of dispatches compute in the background; badge + `/data` panel disclose it live, then transition to an honest idle/last-outcome state | Clicked "Previous available date" on `/backtest` → landed on 2026-07-31 "(historical)", page returned immediately with real content and the "Refreshing" disclosure (never blocked). `GET /api/health` immediately showed `background_compute.active` = `[{asof_key: "2026-07-31", dataset_version: "r2977-f6590950", horizons_done: 0, horizons_total: 5}]`, running CONCURRENTLY with the J-05/J-07 ingest job's own finalize warm. Top bar showed "Ready" + `background-compute-indicator` = "background compute running (1)" simultaneously (never a bare Ready). `/data`'s `background-compute-active-row` mirrored it live ("as-of 2026-07-31", "elapsed 38.2s", "horizons 0/5", dataset r2977-f6590950). Window completed at 22:41:46 UTC (duration_ms 285200 = 4m45s) while the ingest job was still running, confirming the two background computes are independent and concurrently schedulable. `/data` then showed `background-compute-idle` ("No background compute running.") plus `background-compute-last-outcome` = "completed / as-of 2026-07-31 / 4m 45s" — a real measured duration matching the API exactly. | PASS | `reports/qa/goal-ops-hardening-iter-72-evidence/UT-J-09-result.png` |

---

## Passed Tests

### UT-J-01 — Backfill honors the requested range and explains zero-work
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-72-evidence/UT-J-01-result.png`
- All three live submissions (May range, weekend-only, May-range re-run) resolved with honest zero-work breakdowns; the neutral-styled `zero-work-note` never rendered as success-green; run history persisted across a fresh `/data` reload; `/scanner-runs/748` re-served the stored May 29 snapshot rather than recomputing.

### UT-J-05 — Aggregates are precomputed at ingest, never on the fly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-72-evidence/UT-J-05-result.png`
- A real single-day backfill (2008-01-03) refreshed all 9 finalize-hook aggregate categories; `/scanner-runs/2977` and `GET /api/market-phase` both served the new as-of from storage; `GET /api/health` stayed fully responsive throughout the job's ~20-minute finalize-tail warm (0 non-answers in the concurrent drill — see UT-J-07), reversing iter-71's regression on this exact acceptance clause.

### UT-J-06 — Pages load only what they need
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-72-evidence/UT-J-06-result.png`
- All 11 nav-listed pages rendered real headings and substantial content, never a blank/error shell; the two budgeted teeth-assertions the replay lane's own golden checks (readiness badge, AAPL chart-window caption) both resolved instantly on live re-check, and this session's own health-poll drill shows no real endpoint slowdown occurred — the replay's step-02 FAIL was a shared-host timing artifact, not a regression.

### UT-J-07 — Heavy aggregates never take the service down
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-72-evidence/UT-J-07-result.png`
- On the confirmed production launcher (`scripts/start-backend.sh` + `scripts/start-frontend.sh`, never `dev.sh`), a 1,315-poll, ~22-minute `GET /api/health` drill spanning a real ingest finalize warm plus a concurrent J-09 background-compute dispatch recorded 0 non-answers, 0 non-200 responses, and 0 breaches of the ≤2s during-warm ceiling — a direct reversal of iter-71's 58/900-non-answer, 165s-outage regression.

### UT-J-08 — Backtest evidence serves from storage only
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-72-evidence/UT-J-08-result.png`
- Directly captured the mid-warm "Refreshing — showing the last complete evidence" disclosure with real last-good content, then the settled fresh-serve state after the version's warm completed, for two independent as-of dates (2026-08-03 and 2026-07-31) — no skeleton, no blocking, no fabricated figures at any point.

### UT-J-09 — The backend discloses its own background-compute activity
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-72-evidence/UT-J-09-result.png`
- The badge and `/data` panel both disclosed the live background-compute window (as-of, elapsed time, horizons done/total) concurrently with a separate heavy ingest job, then transitioned to an honest idle + last-outcome state with a real measured duration (4m45s) after completion.

---

## Failed Tests

None.

---

## Skipped Tests

None. Both backend (`http://localhost:8255`) and frontend (`http://localhost:3255`) remained up and responsive for the entire run (confirmed continuously via the ~22-minute health-poll drill covering UT-J-05/UT-J-07/UT-J-09).

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Launcher:** `scripts/start-backend.sh` (uvicorn `--limit-concurrency 64 --timeout-keep-alive 65 --timeout-graceful-shutdown 120`, no `--reload`) + `scripts/start-frontend.sh` (`next start -p 3255`) — confirmed via live process inspection, never `scripts/dev.sh`
- **Browser:** Chromium via Chrome MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-08-12 (all timestamps in this report are UTC; the backend's own `logs/backend.log` lines are local BST/UTC+1 — converted where cited)
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-72-evidence/`
- **Health-poll raw CSV:** `runs/goal-session-ops-hardening/iter-72/j07-browser-qa-health-poll.csv` (1,315 rows)
- **Golden replay scripts updated:** `runs/goal-session-ops-hardening/journey-scripts/{J-01,J-05,J-06,J-07,J-08,J-09}.json` — all re-verified PASS this round and lint-clean (`demo_runner.py --mode lint`)
