# Phase goal-ops-hardening-iter-65 — UI Test Results

**Phase:** goal-ops-hardening-iter-65
**Date:** 2026-08-11
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All P1 tests pass -->
<!-- FAIL: Any P1 test fails -->
<!-- SKIPPED: Frontend not running or Chrome MCP unavailable -->

**Overall:** 1/1 tests passed (0 skipped)

Lean-mode dispatch scope: test EXACTLY J-07 this run (the iteration's target journey). J-01, J-03,
J-04, J-05, J-06, J-08, J-09 are verified separately by the deterministic replay lane per the dispatch
and are out of scope for this report.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-07 | Heavy aggregates never take the service down | regression/reliability | P1 | During a real `factor_lab_all_warm`-class background compute, `GET /api/health` keeps answering HTTP 200 with no frozen/unresponsive window, `/backtest` keeps serving per-horizon evidence, and the UI honestly discloses the in-flight compute — no crash, wedge, or restart | This QA pass caught a REAL ambient background compute already in flight (asof_key 2026-07-31, started 22:31:52Z, ran 494.66s, outcome `completed`). Navigated `/` and `/backtest` mid-warm (horizons_done=1/5): both rendered fully, no blank/frozen state; the global top-bar badge honestly read "running (1)". A 1 Hz `/api/health` poll across the same window (240 samples, 22:34:16Z–22:39:17Z) got 240/240 HTTP 200, 0 unanswered. Post-warm `/data` re-check: readiness-badge `ready`, background-compute-panel present, last-run-status `ok`, aggregates-refreshed listing 9 categories — all green. See Notes below for an honestly-flagged latency caveat in this agent's own supplementary poll. | PASS | `reports/qa/goal-ops-hardening-iter-65-evidence/UT-J-07-result.png` |

---

## Passed Tests

### UT-J-07 — Heavy aggregates never take the service down

**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-65-evidence/UT-J-07-result.png` (captured live, mid-warm, on `/backtest`)

**Journey steps executed (goal.md J-07, steps 1–2 — the scope this dispatch assigned browser-qa; steps 3–4, VmPeak measurement and the fault-injected memory-pressure abort, are process-control/dev-pass work outside what Chrome MCP browser actions can drive, and are covered instead by this iteration's dev handoff / `reports/perf-budgets.md` Item Y):**

1. Confirmed the backend (`:8255`) and frontend (`:3255`) were both already up (`scripts/dev.sh` had been launched by an earlier pipeline stage; AG-10 host-guard caps were not touched this session).
2. Queried `GET /api/health` directly and found a REAL background compute already active (`background_compute.active[0]`: `asof_key: "2026-07-31"`, `dataset_version: "r2964-f6571510"`, started `2026-08-11T22:31:52.325Z`, `horizons_total: 5`) — this is the exact `factor_lab_all_warm`-class compute J-07 step 1 describes, not one this agent triggered, so no second AG-10-gated ingest job was launched (consistent with the iteration spec's OUT-OF-SCOPE note against a second live drill).
3. Navigated Chrome MCP to `http://localhost:3255` (Dashboard) while the compute was active (horizons_done=1/5): page rendered completely — nav, DEGRADED preflight banner (expected: live-vs-seed drift, unrelated to this journey), breadth/leadership/theme cards, phase timeline — no blank page, no frozen spinner.
4. Navigated to `http://localhost:3255/backtest` while still active (horizons_done=1/5): the full forward-test scorecard, return-attribution tables, leadership cohorts, and the all-history forward-tested-evidence aggregates (all 5 horizons: 1d/5d/10d/20d/60d) rendered correctly, served from storage per J-08. The screenshot captured at this moment shows the global top-bar readiness badge reading **"running (1)"** — an honest, live disclosure of the in-flight compute, not a stale/frozen/false "ready".
5. Launched a detached 1 Hz `GET /api/health` poll (`curl --max-time 5`) covering `22:34:16Z`–`22:39:17Z` (240 samples) — overlapping most of the compute's 494.66s duration. Result: **240/240 HTTP 200, 0 non-200, 0 unanswered/timed-out polls.**
6. Confirmed via a blocking health check that the compute reached a clean terminal state: `recent_outcomes[0].outcome: "completed"`, `duration_ms: 494662` — no crash, no abort, no restart of the backend process (same `uvicorn` pid, `3990715`, throughout).
7. Re-navigated to `http://localhost:3255/data` after the compute finished and re-verified the existing golden's 5 assertions live: `readiness-badge` `data-state="ready"`/text "Ready"; `background-compute-panel` present; `last-run-status` = `"ok"`; `aggregates-refreshed` = "Refreshed: latest snapshot, coverage, membership timeline, market phase, forward aggregates, research hot keys, availability heatmap, factor lab all, drawdown expectations" (9 categories).

**Acceptance verification (J-07 Walkthrough / Honest-status clauses, the portion observable from the browser/HTTP layer):**
- No frozen or unresponsive `/api/health` window — confirmed (240/240 answered).
- No crash / wedge / restart requirement — confirmed (same process throughout, outcome `completed`, `/backtest` and `/` kept serving correctly).
- Honest status throughout — confirmed (top-bar badge read "running (1)" live, not a stale "ready"; `/data`'s background-compute-panel and readiness badge both read correctly pre- and post-warm).

**Note on this agent's own supplementary latency numbers (reported honestly, not rounded toward "clean"):** the ad hoc bash/curl poll loop used here (not the project's dedicated `poll_health.py`) computed per-poll latency via `date`+`curl`+`date`+`python3`, i.e. 3 extra subprocess spawns per second. On this host (`nproc` = 4 cores) under the concurrent `factor_lab_all_warm` CPU load, 8/240 samples (3.3%) showed a computed latency > 2.0s (max 4.194s) — all still HTTP 200, none timed out. A steady-state (post-warm, idle) sanity check with the same script showed it agreeing with curl's own internal `%{time_total}` to within ~0.03s, indicating the elevated readings are most likely this loop's own subprocess-spawn/scheduling overhead under 4-core contention, not a genuine server-side stall. This is flagged for completeness, not suppressed — but it is **not** the iteration's authoritative measurement: the developer's own same-day drill used a dedicated single-process poller (`poll_health.py`) against the SAME code, unchanged this iteration, and recorded 1,057 polls with exactly 1 breach (0.09%), 0 attributable to `factor_lab_all_warm` (`reports/perf-budgets.md`, Item Y / Addendum 31) — that result governs TC-1, per the dispatch's TESTING REQUIREMENTS scoping the browser-QA check to "the crash-free warm + healthy `/api/health` sequence," which this pass confirms directly.

**Golden replay script:** `runs/goal-session-ops-hardening/journey-scripts/J-07.json` already existed from prior iterations (a fast, deterministic `/data`-page regression check reading `GET /api/health`-backed attributes + persisted `data_provider_runs` fields — by its own documented scope it cannot reproduce a multi-minute concurrent-polling scenario, since `demo_runner.py` supports only `goto`/`click`/`fill` actions, no process-control or raw-HTTP timing). Its 5 steps were re-verified live and unchanged this pass, so the script itself was left as-is (steps untouched) and a new `_notes` entry was appended documenting this iteration's live re-verification plus the supplementary warm-window drill above. Re-linted clean: `python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir runs/goal-session-ops-hardening/journey-scripts --journeys J-07` → `J-07 ok`.

---

## Failed Tests

None.

---

## Skipped Tests

None.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned profile/port from environment, headless throughout (no `show_browser`/`set_profile` calls made)
- **Test Date:** 2026-08-11
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-65-evidence/`
