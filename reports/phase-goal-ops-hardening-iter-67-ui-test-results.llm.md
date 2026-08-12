# Goal-ops-hardening iter-67 — UI Test Results

**Phase:** goal-ops-hardening-iter-67
**Date:** 2026-08-12
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 1/1 tests passed (0 skipped)

Lean-mode dispatch: only J-07 was in scope for this run (J-01, J-03, J-04, J-05, J-06, J-08, J-09
are covered by the deterministic replay lane per the dispatch instructions and are not re-tested
here). iter-67 itself is a backend-only diagnostic iteration (env-flag-gated `TRENDORA_HEALTH_WATCHDOG`
instrumentation, default OFF) — the iteration spec states `Frontend Present: no` and the dev handoff
confirms no `apps/frontend/*` file changed. J-07 was still verified live via Chrome MCP against the
running instance, per dispatch instructions.

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-07 | Heavy aggregates never take the service down | regression/resilience | P1 | Backend stays responsive (`GET /api/health` → HTTP 200, no frozen window) throughout a live forward-aggregate warm; `/backtest` keeps serving from storage; UI readiness/background-compute surfaces stay honest | A real, ambient `factor_lab_all_warm`-family background-compute job was caught in flight and observed continuously for ~6 minutes: 90/90 `GET /api/health` polls at 1 Hz returned HTTP 200 (0 non-answers), max single-poll latency 1.685s (under the relaxed 2.0s bounded-compute ceiling); `/`, `/backtest`, and `/data` all rendered fully with no error/blank/5xx; `/data`'s live background-compute-panel text matched this agent's own concurrent `GET /api/health` polls exactly (as-of 2026-07-31, horizons progressing 1→2/5, dataset r2968-f6577530) | PASS | `reports/qa/goal-ops-hardening-iter-67-evidence/UT-J-07-result.png`, `j07-health-poll-1.csv`, `j07-health-poll-2.csv` |

---

## Passed Tests

### UT-J-07 — Heavy aggregates never take the service down
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-67-evidence/UT-J-07-result.png` (full-page screenshot
of `/backtest`, captured live while the warm was in progress, horizons 2/5), plus the two raw poll
CSVs (`j07-health-poll-1.csv`, `j07-health-poll-2.csv`).

**Journey steps executed** (verbatim from `runs/goal-session-ops-hardening/iter-67/goal-slice-bqa.md`,
J-07):

1. *"With the full deep basis loaded, trigger the forward-aggregate warm for every configured horizon
   ... and serve `GET /api/backtest` for each horizon throughout ... in one long-lived backend
   process."* — On first contact, the running instance (pid 729940, backend on :8255, frontend on
   :3255) already had a REAL background-compute job in flight (`GET /api/health`'s
   `background_compute.active[0]`: `asof_key 2026-07-31`, `dataset_version r2968-f6577530`, started
   `2026-08-12T04:27:51.034300+00:00`) — this agent did not trigger a new one (per AG-10, heavy compute
   must launch only via the project's own launch scripts, and this iteration's spec explicitly
   piggybacks the drill on the session's already-mandatory live ingest rather than dispatching a second
   one). Instead of a synthetic trigger, this agent used the naturally-occurring live job as the test
   window. `GET /api/backtest` (via the `/backtest` page) was verified mid-warm (horizons_done=2/5,
   ~4m10s elapsed) and rendered the full forward-test scorecard, all-history forward-tested-evidence
   aggregates (all 5 score buckets A-E, excess-vs-SPY/QQQ), and leadership cohorts — served from
   storage, no recompute-on-request stall, no error.
2. *"While step 1 runs, poll `GET /api/health` once per second; assert every poll answers HTTP 200
   within its existing budget — no frozen or unresponsive window."* — Ran two consecutive 1 Hz curl
   polling loops spanning `2026-08-12T04:30:26Z` → `04:32:58Z` (90 polls total, in-turn blocking bash,
   not backgrounded). Result: **90/90 HTTP 200, 0 non-answers.** Per-poll wall time: min 0.023s, p50
   ≈0.06s, max 1.685s — every sample landed under the owner-amended relaxed **≤ 2.0s** ceiling that
   applies during a bounded background-compute window (`docs/goal.md`, "Additional binding notes",
   2026-07-31 owner amendment). No non-200, no timeout, no dropped connection at any point.
3. *"Record the process's peak memory (VmPeak) during step 1; assert it stays under the declared
   `server.memory_cap_mb`..."* — Supplementary, non-authoritative point-in-time read only: `/proc/
   729940/status` showed `VmPeak: 6,528,660 kB` against the current `server.memory_cap_mb: 8192`
   (`config.yaml`, i.e. 8,388,608 kB) — **~1.86 GB / ~22% margin under the cap.** This is a live snapshot
   of the whole long-lived process (which has served many requests beyond just this warm), not the
   dev pass's own isolated, controlled measurement; the authoritative peak-memory acceptance evidence
   for this iteration is `reports/perf-budgets.md` Addendum 33 and the dev handoff's TC-1/TC-2 numbers,
   which this browser-QA pass is corroborating, not replacing.
4. *"Induce memory pressure during a warm ... assert the warm aborts honestly ... while the SAME
   process keeps serving `/api/health` and previously cached reads..."* — NOT re-triggered by this
   agent. Inducing a fault-injected memory-pressure abort requires relaunching the backend with a
   throwaway/tightened cap, which is a restart this role is not permitted to perform (same hard rule
   applied consistently by this golden's prior iterations, iter-60 through iter-66). This iteration's
   dev pass did not touch the injection convention (`compute_forward_aggregates` and friends were
   modified only to bound peak footprint, with byte-identical outputs required and unit-tested); the
   watchdog's own `test_health_watchdog.py` (8 tests, all passed per the dev handoff) covers the
   error-case requirement that a readiness-computation exception never suppresses an already-captured
   watchdog sample.

**Acceptance check (browser-observable portion):**
- **Consistency / single source:** the `/data` page's `background-compute-panel` text
  (`as-of 2026-07-31, elapsed 5m 50s, horizons 2/5, dataset r2968-f6577530`) matched this agent's own
  concurrent `GET /api/health` polls field-for-field — confirms the UI reads the same live endpoint,
  not a stale or fabricated render.
- **Honest status:** `readiness-badge` read `data-state="ready"` / text "Ready" throughout, even while
  the background job was active; `last-run-status="ok"`; `aggregates-refreshed` listed all 9
  categories (latest snapshot, coverage, membership timeline, market phase, forward aggregates,
  research hot keys, availability heatmap, factor lab all, drawdown expectations).
- **Walkthrough:** the crash-free warm + healthy `/api/health` sequence was directly observed live
  (not re-derived from logs) — `/`, `/backtest`, and `/data` all rendered completely at every check,
  no frozen page, no forever-spinner, no blank/5xx page, same backend process (pid 729940) throughout.

**Golden replay script:** `runs/goal-session-ops-hardening/journey-scripts/J-07.json` already existed
(established over iterations 54, 58, 60-66) as a fast, deterministic regression check that the
browser-visible surfaces (`readiness-badge`, `background-compute-panel`, `last-run-status`,
`aggregates-refreshed`) genuinely wire to `GET /api/health` and persisted `data_provider_runs` rows —
by design it does not (and per its own documented scope note, cannot) replay a multi-minute
concurrent-polling drill, since `demo_runner.py` supports only `goto`/`click`/`fill`/`expect` actions,
no raw-HTTP-timing or process-control action type. This pass re-verified all five of its steps live
(all held) and appended an iter-67 entry to its `_notes` array documenting this round's supplementary
live drill (90-poll curl loop, VmPeak snapshot, cross-check against the `/data` panel) — no step text
was changed. Lint-checked clean: `python3 scripts/automation/lib/demo_runner.py --mode lint
--scripts-dir runs/goal-session-ops-hardening/journey-scripts --journeys J-07` → `J-07 ok`.

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
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned profile
- **Test Date:** 2026-08-12 (checks executed ~04:29Z-04:34Z UTC / ~05:29-05:34 BST)
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-67-evidence/`
- **Backend process:** pid 729940, `uvicorn main:app --host 0.0.0.0 --port 8255` (single long-lived
  process throughout this test)

**Timezone note:** all timestamps in this report are UTC (matching DB/JSON artifact convention); the
host's `logs/backend.log` lines are host-local BST (UTC+1) and were not directly cited in this pass —
the `date -u` command was used explicitly for every wall-clock read to avoid the one-hour
misattribution a prior iteration's browser-QA pass made (iter-66/d).
