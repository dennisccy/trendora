# goal-ops-hardening-iter-74 — UI Test Results (LLM fallback, J-05/J-06)

**Phase:** goal-ops-hardening-iter-74
**Date:** 2026-08-13
**Written by:** browser-qa-agent (Chrome MCP, LLM-fallback dispatch)

---

**Browser QA Verdict:** PASS

---

**Overall:** 2/2 tests passed (0 skipped)

**Dispatch context:** the deterministic replay lane (`reports/phase-goal-ops-hardening-iter-74-regression-replay-results.md`)
reported FAIL for J-05 (step 13: expected `2005-07-13` did not appear) and J-06 (step 02: readiness-badge
expect not satisfied). This dispatch is the LLM fallback for those two journeys only — J-07 (target journey,
non-browser memory drill) and J-08/J-09 are out of scope for this dispatch. Both FAILs were investigated and
did **not** reproduce on live re-verification; root causes below.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | Backfill of one unsnapshotted day computes and persists aggregates from storage; health stays responsive throughout | Ran a full independent live backfill (2019-01-31, job data_provider_runs.id=484); completed in 17m43s with all 9 finalize-tail aggregates refreshed; `/scanner-runs` and market-phase served correctly from storage; health responsive throughout (38 direct polls, 0 non-200s) | PASS | `reports/qa/goal-ops-hardening-iter-74-evidence/J-05-verify-final.png` |
| UT-J-06 | Pages load only what they need | regression | P1 | All 11 nav pages load with expected content and budgeted on-load API latency; readiness badge shows `ready` | All 11 pages loaded with correct headings/content; readiness badge `data-state="ready"` immediately (domInteractive 52ms); all budgeted endpoints (`/api/health`, bars, availability, `/api/runs`) responded well within their gates | PASS | `reports/qa/goal-ops-hardening-iter-74-evidence/J-06-pages-load.png` |

---

## Passed Tests

### UT-J-05 — Aggregates are precomputed at ingest, never on the fly

**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-74-evidence/J-05-job-completed.png`, `reports/qa/goal-ops-hardening-iter-74-evidence/J-05-verify-final.png`

**Replay FAIL investigated first (before running a fresh drill):** the deterministic replay's own sentinel
resolved to `2005-07-13` and the replay reported FAIL at step 13 ("expected `2005-07-13` did not appear").
Checked directly via a read-only sqlite query against `apps/backend/data/trendora.db`: `scanner_runs` DOES
carry a row for `2005-07-13` (id 2979) — the replay's own backfill completed successfully; live browser
re-inspection confirmed `2005-07-13` present on `/scanner-runs` with a real regime score ("Strong risk-on",
80.46). This matches a pattern this session has documented at iter-64 and iter-72 (see `journey-scripts/J-05.json`
`_notes`): the replay's own runner process gets reaped by this environment mid-wait before the ~18-minute job
finishes, so the backend job completes correctly but the replay never observes it. Not a product regression.

**Independent live drill (steps 1/2/4 of the journey), run end-to-end via Chrome MCP:**
1. On `/data`, selected a fresh unsnapshotted historical trading day directly via a read-only sqlite query
   (`daily_prices` has bars, `scanner_runs` has 0 rows, >400 symbols present): **2019-01-31**.
2. Filled the backfill start/end date fields (via a native-setter + `input`/`change` event dispatch, since the
   plain-text date inputs don't tolerate simulated keystroke typing cleanly), confirmed `kind=backfill`, clicked
   **Start**. `job-status` read `running` immediately, confirming the job actually started (not
   accepted-then-never-run).
3. Job `6dddbd368a2b42b3a087b83cfc5848cf` (`data_provider_runs.id=484`) ran **2026-08-13T05:20:15.747Z →
   05:37:58.568Z (1062.8s / ~17m43s)**, comfortably inside the golden's 40-minute wait budget. Final record:
   `status: "ok"`, `snapshots_created: 1`, `forward_returns_inserted: 2295`, `aggregates_refreshed`: all 9
   categories (`latest_snapshot, coverage, membership_timeline, market_phase, forward_aggregates,
   research_hot_keys, availability_heatmap, factor_lab_all, drawdown_expectations`) — matched byte-for-byte by
   the live UI's `aggregates-refreshed` badge and `backfill-breakdown` text ("1 calendar day · 0 already
   snapshotted · 0 non-trading").
4. **Step 2(a) — served from storage:** `/scanner-runs` lists `2019-01-31` (link to `/scanner-runs/2980`,
   matching the `scanner_runs.id` from a direct sqlite read). That page renders "Immutable snapshot — as of
   2019-01-31" / "Stored exactly as scanned; never recomputed for today. Scanned 2026-08-13 05:20:31" with a
   "Market Regime · as of 2019-01-31" panel (59.30/100, Narrow leadership) and a populated leaderboard (Entry
   Quality column, hundreds of ranked rows — never the "No stored stock rows" empty state).
   `GET /api/market-phase?as_of=2019-01-31` served in **0.013s** (`available:true`, phase `Recovery`, severity
   45.73) — far too fast to be a whole-history recompute. `GET /api/runs/2980` served in 0.213s.
5. **Step 4 — health stays responsive during the ingest job:** two independent samples spanning the job —
   a canonical `scripts/qa/poll_health.py` 1 Hz run of 25 polls at job start (0.004–0.408s, 25/25 HTTP 200) and
   a paired job-status+health curl loop covering the job's final ~2 minutes (13/13 HTTP 200, 0.022–0.612s,
   including the exact completion instant at 0.05s). `logs/backend.log` corroborates continuous 200s on
   `/api/health`, `/api/data/jobs/<id>`, `/api/data`, `/api/runs`, `/api/data/availability` throughout the
   window (log-local BST timestamps cross-checked against the job record's UTC `last_progress_at` — BST=UTC+1,
   consistent, per the session's clock-matching lesson).
6. **Step 3 (backend restart) — NOT re-executed.** Per this role's standing operating rule, browser-qa-agent
   never restarts the live backend. This iteration's own diff (per the iter-74 spec) is test-side
   telemetry-joining only (`test_start_backend_script.py` + documentation corrections) and does not touch
   boot/coverage code, so no regression risk to this step was introduced this round.

Golden replay script updated: `runs/goal-session-ops-hardening/journey-scripts/J-05.json` (notes appended,
steps/selectors unchanged; lint clean).

---

### UT-J-06 — Pages load only what they need

**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-74-evidence/J-06-pages-load.png`

**Replay FAIL investigated first:** the deterministic replay reported FAIL at step 02 (readiness-badge
`data-state="ready"` not satisfied within its 2000ms budget). This iteration's own J-07 VmPeak measurement
drill (`runs/goal-ops-hardening-iter-74/live-drill.log`, `drill.pid`) was running heavy forward-aggregate warms
concurrently with the replay attempt, saturating the shared host — this is the same environmental pattern this
session's `J-06.json` golden documented at iter-72. By the time this pass ran (the drill had already finished),
three direct `curl` checks against `GET /api/health` answered in **0.003–0.009s**, and load average had
settled to 1.15 — confirming the drill was the transient cause, not a product regression.

**All 16 golden steps re-verified live via Chrome MCP against the confirmed-live production-launcher backend
(port 8255/3255):**
- `/` — "Dashboard" heading; `[data-testid="readiness-badge"][data-state="ready"]` present immediately;
  `performance.timing` showed `domInteractive=52ms`, `loadEventEnd=59ms`.
- `/stocks` — "Stocks" heading, 772 buttons / 555 links.
- `/stocks/AAPL` — "AAPL" heading; chart-window-caption present ("3189 bars · as of 2026-08-03 · history since
  1996-01-02 · older bars weekly-sampled"); the gated `through=latest` bars call answered in 0.9ms (cached); a
  separate, ungated `range=full` call measured 1418.1ms.
- `/sectors`, `/themes`, `/evidence`, `/backtest`, `/watchlist` — real headings, substantial interactive DOM.
- `/data` — "Data Manager" heading; availability-cell present (text "3"); `/api/data/availability` answered in
  47.9ms after the page's own 2500ms fetch stagger.
- `/scanner-runs` — "Scanner Runs" heading; `table tbody tr` present; `/api/runs` calls measured 731.3ms /
  774.6ms (above the prior 203–464ms baseline but still well inside the golden's 2500ms+2000ms=4.5s end-to-end
  gate; no page-level budget was breached).
- `/research/regime-lab` — "Research — Regime Lab" heading.

The frontend served fully styled content throughout this pass (CSS linked, real nav, no "Checking backend…"
stuck state) — the session's known intermittent asset-less-QA-frontend defect did not reproduce this round.

Golden replay script updated: `runs/goal-session-ops-hardening/journey-scripts/J-06.json` (notes appended,
steps/selectors/budgets unchanged; lint clean).

---

## Failed Tests

None.

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chromium via `mcp__plugin_superpowers-chrome_chrome__use_browser` (Chrome MCP)
- **Launcher:** confirmed production launcher (`scripts/start-backend.sh` / `scripts/start-frontend.sh`), never `dev.sh`
- **Test Date:** 2026-08-13
