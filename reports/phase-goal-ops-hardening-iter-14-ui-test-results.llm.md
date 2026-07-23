# Phase goal-ops-hardening-iter-14 — UI Test Results

**Phase:** goal-ops-hardening-iter-14
**Date:** 2026-07-23
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** FAIL

<!-- FAIL because UT-04 (P1, happy-path) failed its literal 2-minute resolution bound, which per
     the ui-test-plan's own gating rule ("If any of UT-01, UT-02, UT-03, UT-04, UT-08, or UT-09
     fails, the overall verdict must be FAIL/PARTIAL regardless of how the other tests read") and
     the browser-qa-agent contract ("FAIL: Any smoke test fails, OR any happy-path test fails, OR
     any P1 test fails") forces FAIL. This is NOT a repeat of the iter-7/iter-13 catastrophic
     failure mode (no crash, no red "Backend unavailable" card, no infinite hang, no backend
     restart needed, readiness badge stayed "ready" throughout) — it is a new, narrower, but real
     and precisely measured availability regression: a live `GET /api/backtest` request took
     ~211.8 seconds while a real concurrent backfill/forward-aggregate warm ran, breaching this
     iteration's own committed 2-minute UX bound for that page. Reported plainly per this
     iteration's own escalation discipline, not rounded into "probably fine." -->

<!-- UPDATE (dedicated follow-up pass, same day, 2026-07-23 12:53-13:11 BST): UT-J-04 (previously
     SKIPPED — no permission to kill/restart services in the main pass) has now been executed
     end-to-end against a REAL operator-scheduled crash-at-12:57:13/restart-at-13:01:13 cycle and
     resolves PASS — see the "J-04 Follow-Up" section below. This does NOT change the overall
     verdict: the UT-04 FAIL above stands on its own and alone is sufficient to force FAIL per the
     same gating rule; UT-J-04 resolving PASS is additional closure, not a reason to soften
     anything. -->

**Overall:** 8/10 tests passed — plus 1 additional regression-journey row (UT-J-04, now **PASS** — resolved by a dedicated follow-up pass against a real crash/restart cycle; see "J-04 Follow-Up" below)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-01 | `/data` loads without errors | smoke | P1 | Page renders, no error overlay, readiness badge "ready", no console errors | Page rendered cleanly; badge `data-state="ready"`/"Ready"; rebuild-panel and "Start a fetch" card present; no `Application error` text; console showed only info/log entries | PASS | `reports/qa/goal-ops-hardening-iter-14-evidence/UT-01-result.png` |
| UT-02 | `/backtest` loads with evidence panel | smoke | P1 | Page renders, `evidence-aggregate` present pre-warm, no "Backend unavailable" card, real as-of date | Baseline (pre-job) load: `evidence-aggregate` present, `backtest-asof`="Viewing as-of 2026-07-22 (latest)", no unavailable card, no skeleton, no console errors | PASS | `reports/qa/goal-ops-hardening-iter-14-evidence/UT-02-result.png` |
| UT-03 | Readiness badge never freezes during a real warm | happy-path | P1 | Every `data-state` reading = "ready" throughout the job; terminal `job-status`="ok"; elapsed time recorded | DATE_X=2026-07-21 backfill run (job `195406893b654e36a7ab613ab4ffc032`): badge read "ready" at every explicit check (start/mid/terminal) plus continuous backend-liveness confirmation (72 consecutive 5s-interval successful reads); terminal status "ok" at 11:42:42Z; elapsed ≈ 408s (~6.8 min) from `started_at` 11:35:53.589Z | PASS | See "Passed Tests" detail below (deep-page screenshots return blank; DOM assertions are evidence of record) |
| UT-04 | `/backtest` stays usable during the same warm | happy-path | P1 | `evidence-aggregate` present within at most 2 minutes of tab-open; no "Backend unavailable" card ever | Tab opened ~11:36:14Z. Confirmed still `evidence=false`/skeleton at 135.5s (11:38:29Z) — already past the 2-min budget. Resolved `evidence=true` by 257.4s (11:40:31Z). Never showed the red unavailable card. `performance` API shows the resolving `GET /api/backtest` call itself took **211,829 ms (~211.8 s)**. | **FAIL** | `reports/qa/goal-ops-hardening-iter-14-evidence/UT-04-resolved-slow.png` |
| UT-05 | "forward aggregates" appears in live Refreshed line | happy-path | P2 | `aggregates-refreshed` includes "forward aggregates"; breakdown confirms a genuinely new snapshot | `job-status`="ok"; `aggregates-refreshed`="Refreshed: latest snapshot, coverage, membership timeline, market phase, forward aggregates, research hot keys, drawdown expectations"; `backfill-breakdown`="1 calendar day · 0 already snapshotted · 0 non-trading" | PASS | DOM assertion (see detail below); screenshot blank (deep-page) |
| UT-06 | Same value shows on persisted summary card | regression | P2 | Fresh tab shows persisted-run view, hint "from a previous session", "Refreshed:" includes "forward aggregates" | Brand-new tab, no job started this session: `last-run-status`="ok"; hint text "backfill job · 2026-07-21 → 2026-07-21 · from a previous session"; `aggregates-refreshed` includes "forward aggregates" | PASS | DOM assertion (see detail below); screenshot blank (deep-page) |
| UT-07 | Same value shows in Run History row | regression | P2 | Row Status="ok", Symbols ok/failed="0/0", breakdown includes "forward aggregates" | Run History row (Started 2026-07-23 11:35:53, Range 2026-07-21→2026-07-21): `run-status`="ok"; Symbols ok/failed="0 / 0"; `aggregates-refreshed` includes "forward aggregates" | PASS | DOM assertion (see detail below); screenshot blank (deep-page) |
| UT-08 | J-01/J-03/J-04/J-05 remain green + badge never freezes | regression | P1 | All four journeys re-verify PASS; none of 9 badge checkpoints during J-01/J-03/J-05 backfills read loading/unavailable | Adapted per this run's dispatch (goal-mode regression lanes): J-01/J-03/J-05 are verified by the deterministic golden-script replay lane external to this browser session (merges in separately, not independently re-observed here); J-04 is executed directly by this session and reported separately as UT-J-04 (SKIPPED — see below). This session's own equivalent-mechanism real backfill (UT-03, same rewritten warm path) showed the badge holding "ready" throughout, satisfying the badge-freeze intent for the portion within this session's power to test. | PASS (adapted; see caveats above) | n/a — see UT-03 evidence |
| UT-09 | Old failure states do not reoccur | error | P1 | Zero "unavailable" polls; no 2+ consecutive "loading" polls; UT-04 never shows unavailable card | UT-03's full poll record: zero `data-state="unavailable"`, zero `data-state="loading"` readings of any length. UT-04 never showed the red "Backend unavailable" card (confirmed `unavailable:false` at every check, including the ~211.8s-slow resolution). The specific pre-fix catastrophic modes (frozen badge, red card, backend wedge requiring restart) did not reoccur — a distinct, narrower slow-resolution issue was found instead (see UT-04). | PASS | Derived from UT-03/UT-04 evidence above |
| UT-10 | Job progress affordances stay clear mid-warm | ux | P3 | Activity line names a real, changing detail; heartbeat periodically resets, never looks stale-before-terminal | `current_activity` stayed fixed at "scanning 2026-07-21 (1/1)" for the entire ~6.8-min run (backend's own field, confirmed via direct API read) even after the scan sub-stage had long completed (9.85s) and the run was deep into the aggregate-warm stage — never updated to reflect that phase. Heartbeat text read "updated 1m 43s ago · possibly stalled" at one check (~110s into the warm), then later reset to "updated 10s ago" (so it does recover, not permanently frozen). | FAIL | Evaluated via DOM eval during UT-03's polling (see detail below) |
| UT-J-04 | J-04: Non-blocking boot with visible status | regression | P1 | Boot ≤5s; boot-phase visible pre-ready; crash → explicit unreachable state; log truncates on crash; mid-flight job shows interrupted state on restart | **Executed end-to-end** in a dedicated follow-up pass against a real operator-scheduled kill (12:57:13 BST) + restart (13:01:13 BST): crash → badge "Backend unavailable" + NO-GO preflight banner on `/` and `/data`, no spinner/blank frame; `logs/backend.log` ends abruptly for the killed PID (boot line present, zero shutdown lines) vs. 5 other same-day PIDs with clean shutdown sequences; boot → badge "Initializing… history 89/89" for ~3m14s before flipping to "Ready" (confirmed via the same open tab's own live polling, no reload needed); `/data` run-history row for the killed job shows `run-status`="interrupted" with real non-zero frozen progress (343 snapshots / 375 of 381 dates — vs. 381/381 scanned / 349 snapshots in the very last live read 1.6s pre-kill, an expected small checkpoint-batching gap, not the zeros bug). Boot ≤5s itself closed separately via the cited TC-7 measurement (1.80s, `reports/perf-budgets.md`). | **PASS** | `reports/qa/goal-ops-hardening-iter-14-evidence/UT-J-04-01..06*.png`; full timeline in "J-04 Follow-Up" section below |

---

## Passed Tests

### UT-01 — `/data` loads without errors
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-14-evidence/UT-01-result.png`
- Navigated to `http://localhost:3255/data`. `readiness-badge` `data-state="ready"`, text "Ready". `rebuild-panel` present, "Start a fetch" heading present. `document.body.innerText` did not contain "Application error"; no `#__next-error`/`[data-nextjs-dialog]` overlay. Console: only a React DevTools info line, zero error-level entries.

### UT-02 — `/backtest` loads with evidence panel
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-14-evidence/UT-02-result.png`
- Navigated to `/backtest` before any job was started this session (true pre-warm baseline). `evidence-aggregate` present, `backtest-asof`="Viewing as-of 2026-07-22 (latest)", no "Backend unavailable" text anywhere in the page, no `.animate-pulse` skeleton, console clean (one `[Fast Refresh] rebuilding` log line, no errors).

### UT-03 — Readiness badge never freezes during a real warm
**Verdict:** PASS
**Evidence:** DOM assertions below (screenshots taken deep in `/data`'s ~17,800px DOM returned blank, a known Chrome-MCP limitation — `UT-03-before.png`/`UT-03-afterclick-check.png` are the blank captures; no better screenshot exists for this test)

**Methodology note (DATE_X determination):** Per the Shared Setup, the rebuild-panel read "All 540 resolved-universe members are present in the latest snapshot (2026-07-22)." The "day after" heuristic gave 2026-07-23 (a Thursday). A backfill for that date completed almost immediately with `job-status`="no new snapshots" (zero-work) — because 2026-07-22 is also the seed's `seed_latest_date`; there is no price data at all for 2026-07-23 in the seed, so the Shared Setup's "next calendar day" heuristic had no eligible day to land on. Per the test's own contingency clause, I advanced the search: `GET /api/runs` (read-only) showed 2026-07-20 and 2026-07-22 both snapshotted but **2026-07-21 missing** — a genuine gap on a real trading weekday (confirmed via `GET /api/stocks/AAPL/bars` showing a real bar for 2026-07-21) sitting between two already-snapshotted days. This is very likely the exact date orphaned by the 2026-07-21 10:33 hardware-reset incident. Re-ran from Step 1 with **DATE_X = 2026-07-21**.

**Run:** Filled `job-start-date`/`job-end-date` = `2026-07-21`, kind = "Backfill snapshots" (already default), clicked "Start" (first click attempt on a looser selector silently missed — no job was created, no side effect observed; a second click on `button[type="submit"]` registered correctly and created job `195406893b654e36a7ab613ab4ffc032`, `started_at`=2026-07-23T11:35:53.589Z).

**Badge polling record** (explicit `readiness-badge` DOM reads):
| Time (UTC) | `data-state` | `job-status` |
|---|---|---|
| 11:37:46 | ready | running |
| 11:40:20 | ready | running |
| 11:43:05 | ready | ok (terminal) |

Honesty note on cadence: tool round-trip overhead meant these three explicit browser-rendered badge reads were spaced further apart than the test's literal "every 20 seconds," not sampled at that exact resolution. To compensate, I additionally ran a **read-only** direct poll of `GET /api/data/jobs/<id>` (the same long-lived backend process that serves `/api/health`) at a 5-second cadence from 11:39:49Z through the terminal read at 11:42:42Z — **72 consecutive successful reads, zero failures, zero timeouts** — which is strong corroborating evidence the process never froze at any point in that window (a process wedged the way iter-13's was would have failed this endpoint too, not selectively). Combined, zero "loading" or "unavailable" readings were observed at any granularity.

**Terminal outcome:** `job-status`="ok" at 11:42:42Z (`aggregates_refreshed` included `forward_aggregates`). Elapsed: 11:42:42 − 11:35:53.589 ≈ **408 s (~6.8 min)** — somewhat above the dispatch's own "~4-6 min" estimate, plausibly lengthened by the concurrent `/backtest` load from UT-04 running at the same time (consistent with, and further corroborating, UT-04's contention finding).

### UT-05 — "forward aggregates" appears in live Refreshed line
**Verdict:** PASS
- After the job reached "ok", tab 1 (`/data`) showed: `aggregates-refreshed` = "Refreshed: latest snapshot, coverage, membership timeline, market phase, forward aggregates, research hot keys, drawdown expectations" (proper spacing, no raw underscore/camelCase) and `backfill-breakdown` = "1 calendar day · 0 already snapshotted · 0 non-trading".

### UT-06 — Same value shows on persisted summary card
**Verdict:** PASS
- Opened a brand-new tab (`new_tab`, never used for UT-03/04/05) to `/data`. `job-status` element does not exist in this tab (`jobStatusExists:false`), confirming the persisted `LastRunSummary` fallback view rendered instead of a live job card. Container text: "backfill job · 2026-07-21 → 2026-07-21 · from a previous session ... ok ... Refreshed: latest snapshot, coverage, membership timeline, market phase, forward aggregates, research hot keys, drawdown expectations".

### UT-07 — Same value shows in Run History row
**Verdict:** PASS
- Located the Run History table (`<table>` with headers `Started/Kind/Range/Status/Symbols ok/failed/Snapshots/Summary`) and its row for Range "2026-07-21 → 2026-07-21": Started "2026-07-23 11:35:53", Kind "backfill", `run-status`="ok", Symbols ok/failed="0 / 0", and the row's `aggregates-refreshed` descendant = "Refreshed: latest snapshot, coverage, membership timeline, market phase, forward aggregates, research hot keys, drawdown expectations".

### UT-08 — J-01/J-03/J-04/J-05 remain green + badge never freezes
**Verdict:** PASS (adapted — see caveats in the table row above)
- Per this run's explicit dispatch instructions, J-01/J-03/J-05 verification (including their own badge-state checkpoints) is delegated to the deterministic golden-script replay lane, external to and not independently observed by this browser session — those rows merge in separately. J-04 is reported as its own row, UT-J-04 — SKIPPED at the time this main pass ran, since resolved to PASS by a dedicated same-day follow-up pass (see "J-04 Follow-Up" and the UT-J-04 row above). What IS directly attributable to this browser session — whether the shared rewritten warm path (`_refresh_ingest_aggregates` → `compute_forward_aggregates`) ever freezes the readiness badge during a real triggering backfill — was tested via this session's own UT-03 run and held: "ready" at every explicit check, zero "loading"/"unavailable" readings.

### UT-09 — Old failure states do not reoccur
**Verdict:** PASS
- Reviewed UT-03's full poll record: zero `data-state="unavailable"` readings; zero `data-state="loading"` readings of any length (let alone 2+ consecutive). Reviewed UT-04's full check history: the red "Backend unavailable" card was never observed (`unavailable:false` at 11:36:14, 11:36:56, 11:37:43, 11:38:29, and 11:40:31 when it finally resolved to the real panel). The specific historical catastrophic modes this test targets (frozen badge, red error card, full-backend wedge needing a restart) did not reoccur this run. Note the important adjacent-but-distinct finding in UT-04 below — a slow-but-eventually-successful resolution, not a repeat of these catastrophic modes.

---

## Failed Tests

### UT-04 — `/backtest` stays usable during the same warm
**Verdict:** FAIL
**Failure:** The evidence panel did not resolve within the test's specified 2-minute window while UT-03's DATE_X=2026-07-21 job was confirmed still "running." It eventually resolved (no crash, no red card), but far outside the committed bound.
**Evidence:** `reports/qa/goal-ops-hardening-iter-14-evidence/UT-04-resolved-slow.png`

**Steps taken:**
1. Immediately after UT-03's job-start click (~11:35:57Z / backend `started_at` 11:35:53.589Z), opened a second tab (`new_tab`) to `http://localhost:3255/backtest`.
2. First check at 11:36:14.529Z: `evidence-aggregate` absent, `.animate-pulse` skeleton visible, no unavailable card.
3. Rechecked at 11:36:56.578Z (false/skeleton), 11:37:43.307Z (false/skeleton), 11:38:29.084Z (false/skeleton — **135.5 s elapsed, already past the 2-minute budget**, job independently confirmed still "running" via the direct API read at this time).
4. Rechecked at 11:40:20.963Z (still on tab 1 for badge) then 11:40:31.966Z on tab 0: `evidence-aggregate` now `true`, skeleton gone, no unavailable card. **≈257.4 s elapsed since tab-open.**
5. Inspected `performance.getEntriesByType('resource')` for `/api/backtest` calls in that tab: two calls — `{start: 303ms, duration: 325ms}` and `{start: 628ms, duration: 211829ms}`. The second call — the one that resolved the page — took **211.8 seconds** by itself, measured by the browser's own Resource Timing API (not just my polling cadence).
6. Confirmed via the direct backend API (`GET /api/data/jobs/<id>`) that the DATE_X job's `aggregates_refreshed` was still empty (`[]`, not yet finalized) at 11:40:40Z — i.e., this specific `/api/backtest` slowness happened while the SAME kind of aggregate-warm work this iteration targets was concurrently in flight on the shared process, and did not depend on that warm's own completion (the warm itself finished later, at 11:42:42Z, for `as_of=2026-07-21`; the resolved `/backtest` view was for `as_of=2026-07-22`, already-cached from an earlier-today operator pass).

**Expected:** `evidence-aggregate` present within at most 2 minutes of tab-open; never longer.
**Actual:** Still absent at 135.5 s; present by 257.4 s; the resolving HTTP request itself measured 211.8 s.

**Context, not an excuse:** This is a real, precisely measured, evidence-backed finding, not a tooling flake — the ~211.8 s duration comes directly from the browser's Resource Timing API on the actual network request, corroborated by wall-clock DOM polling before and after. It reproduces a milder version of the exact symptom this iteration's own surface map describes as the historical bug ("a cache-miss under heavy load could hang on `BacktestSkeleton` for minutes") — it just self-resolved rather than wedging indefinitely or erroring, and the readiness badge (a different, simpler endpoint) stayed healthy throughout. The operator's own TC-5 measurement pass earlier today recorded `GET /api/backtest` responses at 0.138-0.158 s, but explicitly **post-warm** (after the finalize step had already completed) — it did not test a live request arriving **during** a concurrent warm, which is exactly the gap this browser test exposes. This does not, on its own, tell us whether the rewritten `compute_forward_aggregates` itself is slow under contention or whether something else (DB lock/connection contention, GIL scheduling with the concurrent backfill) is responsible — no root cause is asserted here, only the observed timing.

---

### UT-10 — Job progress affordances stay clear mid-warm
**Verdict:** FAIL
**Failure:** The current-activity line stayed static for the entire run rather than reflecting the job's actual current stage, and the heartbeat was observed reading "possibly stalled" at least once before recovering.
**Evidence:** DOM eval captured live during UT-03's polling (no dedicated screenshot; this is a P3 UX finding, does not affect the overall verdict given UT-04 already fails)

**Steps taken:**
1. During UT-03's run, read `[data-testid="job-live-activity"]` and `[data-testid="job-heartbeat"]` at multiple points, and cross-checked the backend's own `current_activity`/`last_progress_at` fields via direct API read.
2. At 11:37:46Z (~110 s into the post-scan finalize/warm stage): `activity`="scanning 2026-07-21 (1/1)", `heartbeat`="updated 1m 43s ago · possibly stalled".
3. At 11:40:20Z: `activity` text unchanged, `heartbeat`="updated 10s ago" (reset — not permanently stale).
4. Direct backend read at 11:41:16Z confirmed `current_activity`="scanning 2026-07-21 (1/1)" still, unchanged from when the (9.85 s) scan sub-stage completed, even though the job was by then deep into the multi-minute aggregate-warm stage and `last_progress_at` had ticked forward.

**Expected:** The activity line names a real, changing detail throughout the run; the heartbeat periodically resets to a small value and never looks stale well before the terminal state.
**Actual:** The activity line's text (“scanning 2026-07-21 (1/1)”) never changed for the entire ~6.8-minute run even after the described sub-stage had long finished; the heartbeat did recover from a stale reading, so it is not permanently frozen, but it did display "possibly stalled" wording partway through a run that was, in fact, still healthy.

---

## J-04 Follow-Up — steps 3-6 (dedicated crash/restart pass, resolves the prior SKIP)

**Pass date:** 2026-07-23, 12:53-13:11 BST. **Verdict:** PASS.

**Context:** the main pass above (UT-01…UT-10) could not touch J-04 because every one of its 6
steps needs a real backend kill and/or restart, which that pass's dispatch forbade. This is a
separate, dedicated follow-up run against a **real, operator-scheduled** crash/restart cycle on a
fixed clock. The operator chose and executed the kill and the restart on their own schedule; this
agent never started, stopped, or killed any process itself — it only observed via the browser, the
API, and the logfile, and armed read-only background pollers to detect the moments of interest.
Steps 1-2 (boot ≤5 s budget) are **not** re-tested here — they were already closed the same morning
by the operator-supervised measurement in `reports/perf-budgets.md` ("TC-5 / TC-6 / TC-7 —
full-deep-basis measurement pass (J-07): RESULTS (operator-supervised pass, 2026-07-23)"):
`scripts/start-backend.sh` launched 11:24:53 BST, first `GET /api/health` HTTP 200 at **1.80 s**,
PASS vs the ≤5 s budget (~2.8x margin, 3.20 s to spare). This pass covers J-04 steps 3-6.

### UT-J-04 — J-04: Non-blocking boot with visible status
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-14-evidence/UT-J-04-01-preclash-ready.png` through `UT-J-04-06-data-top-postboot.png`

**Real backfill under observation:** job `d3fd7452355b4965ba8a0445cb8573b5`, kind `backfill`, range
2019-07-01 → 2020-12-31 (381 trading days across 550 calendar days), `started_at`
2026-07-23T11:51:53 UTC (12:51:53 BST) — confirmed running via the live job API before the kill.

**Timeline (all times BST, this host's local clock):**

| Time | Event |
|---|---|
| 12:53:27 | Pre-crash baseline: `readiness-badge` `data-state="ready"` text "Ready"; job confirmed running (`dates_done` 91/381 via the live job API). Screenshot `UT-J-04-01-preclash-ready.png`. |
| 12:57:13 | **T_KILL** — operator sends the scheduled `kill -9` to backend PID 3718942, per the operator's own timeline log (`kill_ts=2026-07-23T12:57:13+01:00 pid=3718942`). Not performed by this agent. |
| 12:57:11.41 | Last live in-memory job read before the kill (1.6 s prior): `dates_done` 381/381 (date scan 100% complete), `snapshots_created` 349, `chunk_index` 7/7, `completed_stages:["backfill"]`, `aggregates_refreshed: []`, `finished_at: null` — i.e. killed mid-finalize/aggregate-refresh, after the core date scan had already fully completed. |
| 12:57:14.35 | First failed health poll (connection refused, code 000) — ~1.35 s after T_KILL. |
| 12:57:16.63 | 3 consecutive failed health polls confirmed — a sustained outage, not a blip. |
| 12:57:28 | `ps -p 3718942` returns nothing — old process confirmed gone. |
| 12:57:34 | Reload of `/`: badge `data-state="unavailable"` text "Backend unavailable"; preflight banner "NO-GO — do not rely on today's board. Backend is unavailable — the preflight check could not run."; Dashboard card: "The dashboard could not load the market regime from the API. Nothing is fabricated — confirm the backend is running and reload." No spinner, no skeleton — an explicit, honest state, visibly distinct from "initializing" below. Screenshot `UT-J-04-02-crash-home.png`. |
| 12:57:45 | Reload of `/data`: same badge/banner; Data Manager card: "Dataset coverage could not load from the API. No figures are shown rather than fabricated values. Confirm the backend is running and retry." No spinner, no skeleton. Screenshot `UT-J-04-03-crash-data.png`. |
| 12:57:53 | `logs/backend.log` inspected: PID 3718942 appears exactly once in the whole file (`Started server process [3718942]`, boot banner `launching at 2026-07-23T10:50:03Z`); **zero** "Shutting down" / "Finished server process [3718942]" lines anywhere; the file's last line at that point is a plain in-flight `GET /api/health` 200 request log with no shutdown sequence after it — an abrupt cut consistent with `kill -9`, contrasted with 5 other same-day PIDs in the same file that each show a clean 4-line `Shutting down` → `Waiting for application shutdown` → `Application shutdown complete` → `Finished server process` sequence from earlier graceful stops. |
| 13:01:13 | **T_RESTART** — operator runs `scripts/start-backend.sh` again. Corroborated independently by the backend's own boot banner (`=== start-backend.sh: launching at 2026-07-23T12:01:13Z ===`, exactly 13:01:13 BST) and by `ps aux` showing the new PID (3848997) started at "13:01". Not performed by this agent. |
| 13:01:14.90 | First health response after restart (~1.7 s after T_RESTART) — `readiness: "initializing"`, `warmup: {done:89, total:89, status:"running", message:"history 89/89"}`. |
| 13:01:47.35 | First browser DOM read (same tab left open since before the crash, no reload): badge `data-state="initializing"` text **"Initializing… history 89/89"** — the same phase detail as the concurrently-polled API payload, satisfying step 3's "top-bar badge... shows the same phase detail as an explicit initializing state — never a bare 'Backend unavailable'." Screenshot `UT-J-04-04-initializing.png` (~13:01:56). |
| 13:01:47 – 13:04:27 | Sustained "initializing": 4 further browser DOM reads (13:02:04, 13:02:09, 13:02:20, 13:02:24) plus ~110 backend API polls at ~1 s cadence all read "initializing" / `history 89/89`. 7 individual polls hit a transient parse/timeout hiccup (momentary, each immediately followed by a successful "initializing" read) — never a sustained failure, and the badge never reverted to "unavailable" during this window. |
| 13:04:28.46 | `readiness` flips to `"ready"` (confirmed via the same 1 Hz API poll). Total boot/warm-up window, first response → ready: **≈193.6 s (3 m 13.6 s)**. |
| 13:05:19.04 | The **same already-open** browser tab (no manual reload since 13:01:44) auto-updates its badge to `data-state="ready"` text "Ready" — confirms the frontend's own live polling, not merely a page reload, correctly reflects the ready transition. Screenshot `UT-J-04-05-boot-ready.png`. |
| 13:05:19 – 13:05:48 | On `/data` (fresh navigation): DOM query of the Run History table found the row for Range "2019-07-01 → 2020-12-31" / Started "2026-07-23 11:51:53": `data-testid="run-status"` = **"interrupted"** (neutral/muted badge styling — not the green "ok" success treatment used for completed runs); Snapshots column "343" with breakdown "550 calendar days · 32 already snapshotted · 169 non-trading"; message "backfill: 343 snapshots over 381 dates, 819520 forward returns". Screenshot (top-of-page — the row itself sits deep in the ~17,800 px page, per the DOM-assertion guidance for this page) `UT-J-04-06-data-top-postboot.png`. |

**Cross-check (server-side, `GET /api/data` → `runs[]`, id 141):** `status: "interrupted"`,
`dates_done: 375` / `dates_total: 381`, `snapshots_created: 343`, `started_at:
"2026-07-23T11:51:53.125181"` (exact match to the job's own live `started_at`), `finished_at:
"2026-07-23T12:01:14.433648"` (12:01:14 UTC = 13:01:14 BST — this timestamp lands almost exactly
when the **new** process's boot-time reconciliation swept and marked the orphaned job interrupted,
i.e. it records when the interruption was *discovered*, not the literal 12:57:13 kill instant four
minutes earlier — an honest artifact of the reconciliation design, not a fabricated crash time).

**Honest gap, not a regression:** the persisted "interrupted" checkpoint (375/381 dates, 343
snapshots) is slightly behind the very last live in-memory read captured 1.6 s before the kill
(381/381 dates fully scanned, 349 snapshots, already into the post-scan finalize stage). This
~6-date/~6-snapshot difference is the expected cost of checkpoint-batching granularity — some
tail-end progress between the last DB commit and an instant `kill -9` is inherently unrecoverable —
and is categorically different from the pre-iter-9/10 "zeros bug": the frozen progress here is
substantial (98.4% of dates, 343 real snapshots), never zero, and the job never appears as a ghost
"still running" row anywhere on `/data`.

**Endpoint note (not a bug):** the transient job-tracking endpoint `GET /api/data/jobs/<id>`
returns 404 ("unknown job") for this job after the restart — expected, since that endpoint serves
only the current process's in-memory live-job registry, which is legitimately empty for a job from
a crashed prior process. The actual `/data` UI page correctly reads the *persisted* run-history list
instead (confirmed above), which is the right architectural split, not a defect.

**Methodology footnote:** an earlier self-armed crash-detector (this agent's own tooling, a 1 s
`curl --max-time` loop) logged one false-positive blip at 12:55:48 BST — a single timed-out health
poll under real background load that self-resolved within 10 s (backend re-confirmed fully alive,
same PID 3718942, ~0.15-0.25 s responses on a generous-timeout recheck). This was a
monitoring-timeout artifact of this agent's own polling choice, not a real outage, and is unrelated
to and clearly distinguished from the real, operator-scheduled kill at 12:57:13 documented above.

**Note (observation only, not a fail):** the visible warm-up counter ("history 89/89") was already
at its maximum on the very first DOM read (33 s post-restart) and stayed pinned there for the
entire ~3 m 13 s window until readiness flipped straight to "ready" — a user watching the badge
sees the same "Initializing… history 89/89" text the whole time, with no incremental visual
count-up in between. J-04's acceptance only requires that *at least one* pre-ready response carry
real phase/progress detail (met) and that "ready" never appear early (also met), so this does not
fail the journey — but it is worth recording for whoever next touches the boot sequence.

**Golden replay script:** not written. Per this dispatch's explicit instruction, and consistent
with prior iterations, J-04 cannot be replayed deterministically by `demo_runner.py` — every one of
its steps depends on actually killing and restarting a live backend process, which the replay
runner has no mechanism to do. This journey stays browser-QA-verified each time it needs
re-checking, not golden-scripted.

**Acceptance check (J-04, `docs/goal.md`):**
- Consistency (single source): badge and banner readings matched the concurrently-polled `GET
  /api/health` `readiness` field at every cross-checked point (unavailable ↔ health unreachable;
  initializing ↔ `readiness:"initializing"`; ready ↔ `readiness:"ready"`) — held.
- Correctness: boot ≤5 s closed via the cited TC-7 (1.80 s); the crashed presentation appeared only
  once health was genuinely, sustainedly unreachable (never spuriously on a single slow poll); the
  initializing presentation appeared only while the API reported `"initializing"` and never claimed
  ready early — held.
- Honest status & anti-goals: no "Ready" before real data was servable; no infinite spinner or
  blank frame at any observed state (crash and boot both rendered explicit, worded presentations)
  — held for everything browser-observable. (Whether boot performs zero whole-table loads / zero
  synchronous snapshot computation is an implementation-internal claim outside what a browser
  session can verify, and is not asserted here either way.)

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (PID 3718942 during the main UT-01–UT-10 pass; not
  restarted or killed by that session). A separate, dedicated follow-up pass (12:53-13:11 BST, same
  day) observed — but did not itself perform — a real operator-scheduled kill of PID 3718942
  (12:57:13 BST) and restart to PID 3848997 (13:01:13 BST), to close J-04 steps 3-6; see "J-04
  Follow-Up" above.
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`)
- **Test Date:** 2026-07-23
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-14-evidence/`
- **DATE_X used:** 2026-07-21 (first candidate, 2026-07-23, was zero-work — see UT-03 methodology note)
- **Job ID (DATE_X real run):** `195406893b654e36a7ab613ab4ffc032`
- **Job ID (J-04 follow-up, killed/restarted mid-flight):** `d3fd7452355b4965ba8a0445cb8573b5` (backfill, 2019-07-01 → 2020-12-31)
