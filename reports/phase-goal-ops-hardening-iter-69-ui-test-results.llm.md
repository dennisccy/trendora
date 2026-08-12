# goal-ops-hardening-iter-69 — UI Test Results

**Phase:** goal-ops-hardening-iter-69
**Date:** 2026-08-12
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: All smoke and happy-path tests pass. Some validation/regression/UX tests may have minor failures. -->

**Overall:** 1/1 tests passed (0 skipped) — lean mode, J-07 only per dispatch; J-01/J-03/J-04/J-05/J-06/J-08/J-09 verified separately by deterministic replay (not in scope for this agent this round).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-07 | Heavy aggregates never take the service down (steps 1-2, per TESTING REQUIREMENTS scope) | regression/resilience | P1 | While a forward-aggregate warm runs across all 5 configured horizons in the live backend process, every 1 Hz `GET /api/health` poll answers HTTP 200 (no frozen/unresponsive window), and `GET /api/backtest` continues serving stored evidence throughout — no crash, no block. | A genuine forward-aggregate warm was live-observed in progress on the inherited backend (`asof_key=2026-07-31`, `dataset_version=r2972-f6583415`, all 5 configured horizons `[1,5,10,20,60]`, progressing 0/5→1/5→3/5 across the session). 120 polls of `GET http://localhost:8255/api/health` at 1 Hz: **120/120 HTTP 200**, zero non-answers, max elapsed 4.93s (6/120 over the 2.0s relaxed background-compute ceiling — reported as measured, not smoothed). `/` showed "Ready" + "background compute running (1)" (honest disclosure, not frozen). `/backtest` loaded fully mid-warm: the per-horizon "Forward-test scorecard" correctly rendered its own honest "No elapsed forward window for this date yet" empty state (every horizon row "— n=0 ⚠", latest as-of has no elapsed post-snapshot bars — this is correct behavior, not a bug), while the separate "Forward-tested evidence (expanding window)" section below it was fully populated from storage (2,911 snapshots, n=1,257,974). `TRENDORA_HEALTH_WATCHDOG` could **not** be armed for this lane — see Known Constraint below. | PASS | `reports/qa/goal-ops-hardening-iter-69-evidence/UT-J-07-result.png` |

---

## Passed Tests

### UT-J-07 — Heavy aggregates never take the service down
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-69-evidence/UT-J-07-result.png` (full-page screenshot of `/backtest` at the acceptance state, mid-warm)

**What was verified (journey steps 1-2, the scope this agent's TESTING REQUIREMENTS assign to browser-qa; steps 3-4 — peak-VmPeak recording and induced memory-pressure abort — are dev-drill scope this round, not re-verified here):**

1. **Live forward-aggregate warm in progress, all configured horizons.** `GET /api/health`'s `background_compute.active` showed one entry the whole session: `asof_key: 2026-07-31`, `dataset_version: r2972-f6583415`, `horizons_total: 5` (matches `config.yaml`'s `walk_forward.horizons: [1, 5, 10, 20, 60]`), `horizons_done` observed progressing 0 → 1 → 3 across three samples taken ~2, ~4, and ~7 minutes into the drill. This is the ingest finalize path's own forward-aggregate warm — the exact mechanism J-07 step 1 names — genuinely in flight on the same long-lived backend process (pid 1394779, up 43+ minutes at drill start) the whole time, not something this agent had to separately trigger.
2. **`GET /api/health` never froze or went non-200 during the warm.** Ran the canonical `scripts/qa/poll_health.py` (per standing correction: canonical script, not ad hoc curl/bash) against `http://localhost:8255/api/health`, 120 polls at 1 Hz (~09:53:19–09:55:34 UTC), overlapping the warm's 1/5→3/5 progress window. Result: **120/120 HTTP 200** (`tail -n +2 ... | cut -d, -f2 | sort | uniq -c` → `120 200`), zero timeouts/non-answers. 6/120 polls exceeded the owner-amended relaxed 2.0s background-compute-window ceiling (max 4.93s) — reported exactly as measured, consistent with this same round's dev-side drill (77/952, 8.09%, attributed there to `goal-iter-lean.sh`'s own concurrent polling of the same backend) rather than rounded toward "no breaches." No poll was frozen, unresponsive, or a connection failure — the acceptance condition ("every poll answers HTTP 200… no frozen or unresponsive window") held. Raw CSV: `runs/goal-ops-hardening-iter-69/browser-qa-drill/j07-health-poll.csv`.
3. **`GET /api/backtest` (via `/backtest`) served throughout, from storage, honestly.** Navigated to `/` (readiness badge: "Ready" + "background compute running (1)" — truthful disclosure of the in-flight warm, page fully interactive, not blank/frozen) and to `/backtest` mid-warm. The page rendered completely: the per-horizon "Forward-test scorecard" showed its own correct, honest **"No elapsed forward window for this date yet"** empty state (every 1d/5d/10d/20d/60d row "— n=0 ⚠" — correct because the latest as-of date, 2026-08-03, has no post-snapshot bars yet in the seed, not a defect) — this agent explicitly avoided iter-68's TC-6 mistake of conflating this empty-state panel with the separate, fully-populated "Forward-tested evidence (expanding window ≤ 2026-08-03)" section immediately below it (2,911 contributing snapshots, mean 60d fwd return +3.76% n=1,257,974, full score-bucket/regime/control breakdowns all rendered). Both sections are correctly described here as what they actually are.
4. **No wedge/deadlock/restart requirement observed.** The backend answered every request (health polls, page loads, `/backtest` load) throughout the drill without restart.

**Known constraint — `TRENDORA_HEALTH_WATCHDOG` could not be armed for this lane (TC-4):** This agent's dispatch directs exporting `TRENDORA_HEALTH_WATCHDOG=1` before triggering/relying on any backend **(re)start** for its own J-07 drill. This agent inherited an **already-running** backend (pid 1394779, started 10:06:57 local before this agent's dispatch) that was (a) mid-way through the live forward-aggregate warm described above, and (b) already the backend against which the deterministic-replay lane had produced `J-01-verify.png` … `J-09-verify.png` in `reports/qa/goal-ops-hardening-iter-69-evidence/` (timestamped 10:08–10:49, all before this agent started at ~10:49). Restarting the process to arm the flag would have killed the in-flight warm mid-computation and risked invalidating the replay lane's already-collected evidence for the other 7 required-still-passing journeys this round. Per the iteration spec's own explicit fallback ("If it inherits an already-running backend it cannot restart without disrupting other journeys' evidence this round, it must name that constraint explicitly"), this agent did **not** restart the backend. Verified directly: `/proc/1394779/environ` contains no `TRENDORA_HEALTH_WATCHDOG` entry, and `logs/health-watchdog.jsonl` contains **zero** `handler_compute` records timestamped inside this agent's own polling window (09:53:19–09:55:34 UTC) — confirming the flag was genuinely not live for this lane, not silently omitted from the report. This is the fourth consecutive round this constraint has recurred for the browser-qa lane specifically (per the iter-69 spec's own framing); the dev's own live-job/idle-control drills this same round DID run with the flag armed via a separate `scripts/start-backend.sh` launch (see `docs/handoffs/goal-ops-hardening-iter-69-dev.md` and `reports/perf-budgets.md` Addendum 35), fully closing the sub-span-attribution deliverable — only the browser-qa lane's own polling window remains unattributed this round, and that gap is a same-process-continuity constraint outside this agent's ability to resolve without disrupting concurrently-collected evidence, not a silent omission.

---

## Failed Tests

None.

---

## Skipped Tests

None. Chrome MCP was available and the frontend (http://localhost:3255) and backend (http://localhost:8255) were both reachable throughout.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255
- **Browser:** Chrome via MCP (headless, pinned profile/port per host-safety guard)
- **Test Date:** 2026-08-12 (~09:49–09:55 UTC / 10:49–10:56 BST)
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-69-evidence/`
- **Raw poll CSV:** `runs/goal-ops-hardening-iter-69/browser-qa-drill/j07-health-poll.csv` (120 rows, schema matches `scripts/qa/poll_health.py`'s canonical `timestamp,http_status,elapsed_s,breach_over_2s,load_avg_1m`)
- **Golden replay script written:** `runs/goal-session-ops-hardening/journey-scripts/J-07.json` (lint-clean via `demo_runner.py --mode lint`)
