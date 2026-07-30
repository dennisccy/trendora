# Phase goal-ops-hardening-iter-38 — UI Test Results

**Phase:** goal-ops-hardening-iter-38
**Date:** 2026-07-30
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke and happy-path tests pass. J-04's restart/crash steps were SKIPPED (not failed) per an
     explicit pipeline-coordinator safety instruction; every journey that WAS executed passed. -->

**Overall:** 5/6 regression journeys fully passed live verification, 1/6 (J-04) partially SKIPPED by explicit
instruction (0 failures). This iteration's own UI test plan (`reports/phase-goal-ops-hardening-iter-38-ui-test-plan.md`)
contributes zero UT-XX rows — it is a backend-only iteration (`Frontend Present: no`) with no new/changed UI
surface, confirmed by the ui-surface-map. All rows below are goal-mode regression-lane re-confirmations of
Required-still-passing journeys.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | Weekend-only range shows 0 trading-day targets / 2 non-trading; full May re-run shows 0 created / 19 already-snapshotted + 9 non-trading; both persist across reload; zero-work renders as an explanatory state visually distinct from a productive run's success badge; `/scanner-runs` renders stored leaderboards for in-range dates | Both live backfills submitted and completed exactly as expected (JSON: `calendar_days:2, non_trading_days:2, already_snapshotted:0` then `calendar_days:28, already_snapshotted:19, non_trading_days:9`); `/data` "Run history" table (post-reload) shows both runs with muted `border-border` "no new snapshots" badges alongside an older `border-pos` green "ok" run in the SAME table — clear visual distinction confirmed; `/scanner-runs/748` (2026-05-29) renders the immutable stored leaderboard | PASS | `reports/qa/goal-ops-hardening-iter-38-evidence/UT-J-01-result.png` |
| UT-J-03 | No per-run range cap | regression | P1 | A >370-day backfill request (2025-06-01→2026-07-17, 412 calendar days) is accepted with no "date range too large" rejection; executes in visible chunks derived from `import_chunking.date_window_days`; completes without any cap-related failure | Job accepted (`POST /api/data/jobs` 200); `config.yaml` confirmed to no longer contain `max_range_days` (comment records its removal); job resolved `dates_total:283, chunk_index:5, chunk_total:5` (283 trading days ÷ 90-day `date_window_days` chunks = 5, matching config); completed with `412 calendar days · 283 already snapshotted · 129 non-trading` (283+129=412 ✓); `GET /api/health` stayed 200/~130ms throughout | PASS | `reports/qa/goal-ops-hardening-iter-38-evidence/UT-J-03-result.png` |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | Backfilling one unsnapshotted day serves its aggregates from storage (scanner-run leaderboard, market-phase/regime) with the persisted run record listing which inventory aggregates were refreshed; `GET /api/health` stays responsive throughout a heavy ingest; (step 3, cold-boot coverage-from-storage check, requires a backend restart) | Backfilled genuinely-new gap date 2005-04-12 (`dates_total:1, already_snapshotted:0, snapshots_created:1`); `/scanner-runs/1882` renders the stored leaderboard ("Stored exactly as scanned; never recomputed"); `GET /api/dashboard?as_of=2005-04-12` (regime/breadth/market-phase inputs) answered in 2.4ms — storage-speed, not compute-on-read; run record's `aggregates_refreshed` = `[latest_snapshot, coverage, membership_timeline, market_phase, forward_aggregates, research_hot_keys, drawdown_expectations]`; `GET /api/health` polled repeatedly during the ~5.5 min ingest, always 200. Step 3 (backend restart + cold `/data` load) was NOT executed — see UT-J-04 note; folding it into a live restart was judged unsafe this run per the explicit "do not restart services" instruction | PASS (steps 1,2,4 verified live; step 3 not executed, see UT-J-04) | `reports/qa/goal-ops-hardening-iter-38-evidence/UT-J-05-result.png` |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | regression | P1 | While a new dataset version's finalize warm is running, `/backtest` serves the last COMPLETE stored version within its ≤1.5s budget with a visible "refreshing" indicator; once the warm completes (run record lists `forward_aggregates`), a reload serves the new version's values within the same budget with the indicator gone | Triggered a version bump via a small 1-day backfill (2005-04-13); mid-warm, `GET /api/backtest` answered in 124ms (well under 1.5s) with `evidence_status:"refreshing"`, `evidence_asof:"2026-07-22"` — same figure as the pre-trigger baseline; frontend rendered the `evidence-refreshing` banner: "Refreshing — showing the last complete evidence... evidence as of 2026-07-22, generated 2026-07-30 13:26:04... no partial or fabricated figures are shown in the meantime"; after the warm finished (`aggregates_refreshed` included `forward_aggregates`), a reload answered in 19ms with `evidence_status:"ready"`, "Snapshots contributing" incremented 1821→1822 and n=750657→750809 (new snapshot now folded in), `evidence-refreshing` element gone. (Steps 4-5 are explicitly "API/test-layer" / fresh-install-fixture assertions per the journey's own text — outside browser-QA scope) | PASS | `reports/qa/goal-ops-hardening-iter-38-evidence/UT-J-08-result.png` |
| UT-J-09 | The backend discloses its own background-compute activity | regression | P1 | Steady state shows bare `Ready` + empty `background_compute`; triggering a BCW via `/backtest` for a historical as-of returns immediately while dispatching compute in the background; `GET /api/health` carries an explicit active-window field (as-of, elapsed, horizons done/total); the top-bar badge shows a "background compute running" detail alongside `Ready` in that same window; `/data` renders the same field plus the last completed/failed outcome; after completion the field returns to idle and `/data` shows the last-outcome row with a real duration; disclosure is honestly scoped (process-lifetime only, no fabricated ETAs) | Confirmed steady-state baseline (`background_compute:{active:[],recent_outcomes:[]}`). Triggered 6 independent live BCWs (2010-06-15, 2011-10-17/21, 2011-11-01, 2012-02-01/03-01/03-14, 2013-04-01/22, 2014-05-01) via the as-of calendar on `/backtest`; each returned in 58-261ms (non-blocking, unchanged J-08 behavior) while `background_compute.active` populated with `{asof_key, dataset_version, started_at, elapsed_ms, horizons_done, horizons_total}` progressing 0→5; `/data`'s "Background compute" panel rendered the SAME live in-flight row (`as-of 2013-04-17 · elapsed 3.5s · horizons 2/5`) and correctly flipped to `No background compute running` + `Last outcome: completed, as-of X, N.Ns` after each window closed, with no reload needed; the top-bar carries a SEPARATE `background-compute-indicator` element (sibling to `readiness-badge`) reading "background compute running (1)" — captured live in a single-tab, continuously-foregrounded 250ms-interval sample set (47/153 samples matched a backend-timestamp-confirmed active window) and in a same-page-load DOM capture showing `readiness-badge="Ready"` + `background-compute-indicator="background compute running (1)"` together. Copy explicitly states "no fabricated finish-time estimate or completion percentage" and "process-lifetime only, never persisted". *(An earlier pass of this same check mis-queried only the `readiness-badge` element in isolation and, combined with a cross-tab timer-throttling artifact, produced a false "badge never discloses" reading; corrected upon finding the correct sibling element and re-verifying cleanly on a single foregrounded tab across two further independent live windows — noted here for the next QA pass.)* | PASS | `reports/qa/goal-ops-hardening-iter-38-evidence/UT-J-09-result.png` |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | Backend restart → first `GET /api/health` 200 within 5s; a second restart's pre-ready polls carry boot phase + progress with the badge matching; a simulated crash shows an explicit unreachable/crashed presentation, distinct from initializing; the persistent logfile shows boot events and (post-crash) an abrupt ending; after restart, any job mid-flight at the kill shows an explicit interrupted state | NOT executed live. The dispatch's pipeline-coordinator note states explicitly: "Do NOT restart services yourself — if one dies mid-run, record that honestly instead." J-04's own steps require deliberately killing and restarting the shared backend process this whole QA session (and every already-passed journey above) depends on, and this agent's Bash environment does not have `CHAIN_BACKEND_PORT`/`CHAIN_FRONTEND_PORT` set, so invoking `scripts/start-backend.sh` directly risked relaunching on the wrong port and stranding the session — judged unsafe to attempt under that instruction. Performed the safe, read-only checks instead: `logs/backend.log` contains a persistent, multi-restart boot history (`=== start-backend.sh: launching ...` → host-guard line → `Application startup complete` → `Uvicorn running`), each PRECEDED by a clean `Shutting down`/`Application shutdown complete` pair — i.e., the logfile mechanism itself is confirmed working, with no abrupt/crash-style ending anywhere in the current log; the present session (booted 2026-07-30T13:11:46Z) served `Ready` continuously and correctly for the ~2 hours of this entire QA run; current `/data` job/run history shows zero orphaned `running` rows (all recent runs terminal `ok`), consistent with no stranded mid-flight job. This is historical/indirect corroboration only, not a fresh live-fire crash test this iteration | SKIPPED (partial — see Actual) | `reports/qa/goal-ops-hardening-iter-38-evidence/UT-J-04-result.png` |

---

## Passed Tests

### UT-J-01 — Backfill honors the requested range and explains zero-work
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-38-evidence/UT-J-01-result.png` (immutable `/scanner-runs/748` leaderboard, as of 2026-05-29)
- Submitted a weekend-only backfill (2026-05-02 → 2026-05-03) via `/data`'s job form; final job status: `dates_total:0, calendar_days:2, non_trading_days:2, already_snapshotted:0` — matches the contract's `non_trading + dates_total = calendar_days`.
- Submitted the full May range (2026-05-02 → 2026-05-29); final job status: `dates_total:19, snapshots_created:0, already_snapshotted:19, non_trading_days:9, calendar_days:28` (19+9=28 ✓; 0+19+0=19 ✓).
- Reloaded `/data`: the "Run history" table (server-persisted, survives reload) lists both runs with a neutral `border-border/bg-surface-2/text-text-muted` "no new snapshots" badge, alongside an older backfill run rendered with the distinct positive `border-pos/text-pos` "ok" badge in the same table — the zero-work vs. productive visual distinction required by the journey is present.
- `/scanner-runs` lists May 2026 dates (2026-05-04…2026-05-29); opened `/scanner-runs/748` (2026-05-29) — leaderboard (MU, ARM, MRVL, DELL, HPE, AMD, STX, NTAP, DDOG) renders from the immutable stored snapshot, labeled "Stored exactly as scanned; never recomputed for today."
- Golden replay script refreshed: `runs/goal-session-ops-hardening/journey-scripts/J-01.json` (lints clean).

### UT-J-03 — No per-run range cap
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-38-evidence/UT-J-03-result.png`
- Confirmed `config.yaml` no longer defines `max_range_days` (comment at line 57-59 records its removal in favor of `import_chunking.date_window_days`).
- Submitted a 412-calendar-day backfill (2025-06-01 → 2026-07-17) via `/data`; accepted with HTTP 200, no rejection of any kind.
- Job resolved `dates_total:283` trading days, `chunk_index:5, chunk_total:5` — 283 ÷ `date_window_days:90` ⇒ 5 chunks, confirming the chunk plan is config-derived.
- Completed cleanly: `412 calendar days · 283 already snapshotted · 129 non-trading` (283+129=412 ✓; this exact range has been run identically across many prior iterations per the persisted Run History, all consistently zero-work — corroborating stability, not a fluke).
- `GET /api/health` polled throughout, always 200, ~130ms.
- Golden replay script `runs/goal-session-ops-hardening/journey-scripts/J-03.json` unchanged (already accurate, lints clean).

### UT-J-05 — Aggregates are precomputed at ingest, never on the fly
**Verdict:** PASS (steps 1, 2, 4 of 4; step 3 not executed — see UT-J-04)
**Evidence:** `reports/qa/goal-ops-hardening-iter-38-evidence/UT-J-05-result.png`
- Selected a confirmed backfill-gap date (2005-04-12, from `GET /api/data`'s `coverage.gap_first`) and backfilled it; job result: `dates_total:1, already_snapshotted:0, snapshots_created:1, forward_returns_inserted:815` — genuinely new work, not a replay of already-done data.
- `/scanner-runs/1882` (run created by this job) renders the stored leaderboard immediately.
- `GET /api/dashboard?as_of=2005-04-12` (market-phase/regime/breadth) answered in 2.4ms — storage-speed serving, not a fresh compute.
- The job's `aggregates_refreshed` list: `[latest_snapshot, coverage, membership_timeline, market_phase, forward_aggregates, research_hot_keys, drawdown_expectations]` — matches the journey's named inventory.
- `GET /api/health` polled repeatedly (every 3-20s) across the job's ~5.5-minute finalize tail (this backfill happened to exercise the iter-38 shared-cache path live — backend log recorded `cache_ctx liveness ... resolved=attach_shared_cache(live shared cache)` for this job, confirming real, non-trivial ingest work was underway) — every poll returned 200.
- Step 3 ("restart the backend and visit `/data` cold") requires killing/restarting the shared backend process — not executed this run; see UT-J-04's note for the reasoning (same explicit safety instruction applies).
- Golden replay script refreshed: `runs/goal-session-ops-hardening/journey-scripts/J-05.json` (lints clean).

### UT-J-08 — Backtest evidence serves from storage only
**Verdict:** PASS (steps 1-3 of 5; steps 4-5 are explicitly API/test-layer or fresh-install-fixture assertions, outside browser-QA scope per the journey's own text)
**Evidence:** `reports/qa/goal-ops-hardening-iter-38-evidence/UT-J-08-result.png`
- Baseline: `/backtest` showed "Viewing as-of 2026-07-22 (latest)".
- Triggered a version bump via a 1-day backfill (2005-04-13) on `/data`.
- Mid-warm, loaded `/backtest`: `GET /api/backtest` responded in 124ms (budget ≤1.5s) with `evidence_status:"refreshing"`, `evidence_asof:"2026-07-22"` (the last complete version, unchanged); frontend rendered the `data-testid="evidence-refreshing"` banner verbatim: "Refreshing — showing the last complete evidence ... evidence as of 2026-07-22, generated 2026-07-30 13:26:04 ... no partial or fabricated figures are shown in the meantime."
- After the warm finished (job's `aggregates_refreshed` included `forward_aggregates`), reloaded `/backtest`: `GET /api/backtest` responded in 19ms with `evidence_status:"ready"`; "Snapshots contributing (≤2026-07-22)" moved 1821→1822 and the 60d mean-return sample size moved n=750657→n=750809 — the new snapshot's data is now folded into the served aggregate; the `evidence-refreshing` element was gone.

### UT-J-09 — The backend discloses its own background-compute activity
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-38-evidence/UT-J-09-result.png` (top bar shows `● Ready` and `● background compute running (1)` together)
- Steady state confirmed: `GET /api/health` → `background_compute:{active:[],recent_outcomes:[]}`, ~110-180ms.
- Triggered BCWs by picking historical as-of dates on `/backtest`'s calendar (dates confirmed via the calendar's own enabled/disabled state to already have a scanner run, so navigation succeeds, but not yet warmed for the current `dataset_version`). Each `GET /api/backtest?as_of=...` returned in 58-261ms — non-blocking, matching J-08.
- `GET /api/health`'s `background_compute.active` correctly carried `{asof_key, dataset_version, started_at, elapsed_ms, horizons_done, horizons_total}`, with `horizons_done` progressing 0→5 and `elapsed_ms` climbing across repeated polls of the SAME window — this is the single canonical field, read by both surfaces below.
- Top-bar: found the disclosure lives in a `data-testid="background-compute-indicator"` element, a SIBLING of `readiness-badge` (not merged into it) — reading "background compute running (1)" whenever a window is active. Verified via (a) a same-page-load DOM capture showing both elements together mid-window, and (b) a clean single-tab, 250ms-interval, 153-sample continuous poll spanning a backend-timestamp-confirmed 8.05s active window, in which 47 consecutive samples correctly showed the indicator.
- `/data`'s "Background compute" panel rendered the identical in-flight data (`as-of 2013-04-17 · elapsed 3.5s · horizons 2/5 · dataset r1883-f3978455`) live, without needing a page reload, and correctly flipped to `No background compute running.` + `Last outcome: completed · as-of X · N.Ns` once each window closed.
- Honest-scope copy present verbatim: "Read-only disclosure — no fabricated finish-time estimate or completion percentage, only real observed horizon counts and elapsed time" and "Since the last backend restart — this history is process-lifetime only, never persisted."
- Golden replay script `runs/goal-session-ops-hardening/journey-scripts/J-09.json` unchanged (already accurate — checks static/idle-state text only, which is timing-independent and lints clean).

---

## Skipped Tests

### UT-J-04 — Non-blocking boot with visible status
**Verdict:** SKIPPED (partial)
**Reason:** The dispatch's pipeline-coordinator note states explicitly: *"the backend had been left stopped by this iteration's memory drills... The pump has restarted it... Do NOT restart services yourself — if one dies mid-run, record that honestly instead."* J-04's own steps require this agent to deliberately restart (twice) and then `kill -9` the single shared backend process that every other journey in this run depends on, for the remainder of this session. This agent's shell also does not have `CHAIN_BACKEND_PORT`/`CHAIN_FRONTEND_PORT` set (confirmed empty), so an un-parameterized `scripts/start-backend.sh` invocation would very likely relaunch on the wrong port and strand the whole QA session — a real risk the coordinator's instruction is reasonably read to guard against. Given J-04 is a regression re-confirmation of an already-passing journey (not first-time proof), and the coordinator's own note attributes the replay-lane flag to an already-resolved infra hiccup (not an app-logic defect), this agent chose not to attempt the restart/kill sequence.

What WAS verified (safe, read-only): the persistent backend logfile (`logs/backend.log`) contains a clean, repeated boot-event history — every `=== start-backend.sh: launching ...` line is immediately followed by the host-guard config line, `Application startup complete`, and `Uvicorn running on http://0.0.0.0:8255`, and every one of these is PRECEDED by a clean `Shutting down` / `Application shutdown complete` pair, confirming the logfile mechanism (step 4's "persistent backend logfile" requirement) is genuinely working and that no abrupt/crash-style ending exists anywhere in the current log. The present session (booted 2026-07-30T13:11:46Z) served `readiness-badge="Ready"` continuously and correctly across roughly two hours of this QA run (dozens of independent checks above). Current `/data` job/run history shows zero rows with a `running` status (all recent runs are terminal `ok`), consistent with no job stranded mid-flight by a past crash. None of this is fresh evidence of THIS iteration's restart/crash UX (steps 1, 2, 3, 5, and the "abrupt log ending" half of step 4) — it is historical/indirect corroboration only.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), headless, pinned profile
- **Test Date:** 2026-07-30
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-38-evidence/`

### Note on screenshot capture

`/data` is an extremely tall page in this dataset shape (~24,800px document height, dominated by the
591-symbol per-symbol coverage table and the drift-report symbol list). Chrome's headless screenshot capture
returned a blank image whenever the target content ("Job progress" / "Run history") required scrolling more
than roughly 2,000px down that specific page — reproduced consistently across `scrollIntoView`, a discrete
`scroll` action, and varying pre-screenshot delays, so it is a capture-layer limitation on this page's height,
not a product defect. Worked around by using shorter, un-scrolled pages (`/scanner-runs/<id>`, `/data` above
the fold, `/backtest` above the fold) for the visual evidence, while the specific numeric assertions
("19 already snapshotted", "412 calendar days", "chunk 5/5", etc.) were independently confirmed via the same
`GET /api/data/jobs/<id>` payloads the page itself renders from, and via the extracted page markdown/HTML
(not just the screenshot).
