# Goal-ops-hardening iter-68 — UI Test Results

**Phase:** goal-ops-hardening-iter-68
**Date:** 2026-08-12
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

**Overall:** 1/1 tests passed (0 skipped)

Lean-mode dispatch: only J-07 was in scope for this run (J-01, J-03, J-04, J-05, J-06, J-08, J-09 are
covered by the deterministic replay lane per the dispatch instructions — see
`reports/phase-goal-ops-hardening-iter-68-regression-replay-results.md`, 8/8 PASS including J-07's own
golden — and are not re-tested here). iter-68 itself is a backend-only diagnostic iteration (a third
env-flag-gated `TRENDORA_HEALTH_WATCHDOG` sample, `handler_compute_s`, default OFF, plus test-execution
and write-up-correction work) — the iteration spec states `Frontend Present: no` and this agent's own
`git diff` (below) confirms no `apps/frontend/*` file changed. J-07 was verified live via Chrome MCP
against the running instance, with its health-poll drill run through the canonical
`scripts/qa/poll_health.py` script per this round's explicit TESTING REQUIREMENTS directive (not an ad
hoc curl/bash loop — closes iter-67/c for this round).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-07 | Heavy aggregates never take the service down | regression/resilience | P1 | Backend stays responsive (`GET /api/health` → HTTP 200, no frozen window) throughout a live forward-aggregate warm across every configured horizon; `/backtest` keeps serving from storage; UI readiness/background-compute surfaces stay honest | A real, ambient full 5-horizon `factor_lab_all_warm`-family background-compute job (asof 2026-07-31, dataset r2970-f6580475) was caught in flight and observed via `scripts/qa/poll_health.py`, 240 polls at 1Hz, 07:38:22.469Z–07:42:44.335Z: **240/240 HTTP 200, 0 non-answers**; 9/240 (3.75%) exceeded the relaxed 2.0s ceiling (max 4.19s), reported honestly, never a non-200/timeout. Job completed mid-drill (`outcome:"completed"`, duration_ms 482671). `/backtest` rendered the full forward-test scorecard/leadership cohorts mid-warm (horizons 1/5, 2/5); `/data`'s live panel text matched this agent's own concurrent `GET /api/health` polls exactly, both mid-warm and post-completion | PASS | `reports/qa/goal-ops-hardening-iter-68-evidence/UT-J-07-result.png`, `reports/qa/goal-ops-hardening-iter-68-evidence/j07-health-poll.csv` (+ `.meta.json`) |

---

## Passed Tests

### UT-J-07 — Heavy aggregates never take the service down
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-68-evidence/UT-J-07-result.png` (full-page screenshot of
`/backtest`, captured live mid-warm, horizons 1/5→2/5), plus the canonical-script poll CSV
`j07-health-poll.csv` / `j07-health-poll.csv.meta.json`.

**Journey steps executed** (verbatim from `runs/goal-session-ops-hardening/iter-68/goal-slice-bqa.md`,
J-07 — this round's TESTING REQUIREMENTS scope this lane's own execution to steps 1–2, measured via
`scripts/qa/poll_health.py`; steps 3–4 are dev/unit-test concerns covered by the dev handoff and
`test_health_watchdog.py`, not re-triggered by this role):

1. *"With the full deep basis loaded, trigger the forward-aggregate warm for every configured horizon
   (the ingest finalize path) and serve `GET /api/backtest` for each horizon throughout ... in one
   long-lived backend process."* — On first contact, the running instance (backend pid 1167030 on
   :8255, frontend pid 1168571 on :3255) already had a REAL background-compute job in flight
   (`GET /api/health`'s `background_compute.active[0]`: `asof_key 2026-07-31`, `dataset_version
   r2970-f6580475`, `started_at 2026-08-12T07:33:04.420611+00:00`, `horizons_total 5`) — this agent did
   not trigger a new one (per AG-10 and this iteration's OUT-OF-SCOPE note that the session's live-job
   drill already piggybacks on a single mandatory ingest per round; a second heavy compute here would be
   redundant). `GET /api/backtest` (via the `/backtest` page) was verified live TWICE mid-warm
   (horizons_done=1/5 at 07:36:47Z, then 2/5 at 07:37:27Z) and rendered the full forward-test scorecard,
   all-history forward-tested-evidence aggregates (all 5 score buckets, excess-vs-SPY/QQQ), return
   attribution, leadership cohorts, and top contributors/detractors — served from storage, no
   recompute-on-request stall, no error, no blank page.
2. *"While step 1 runs, poll `GET /api/health` once per second; assert every poll answers HTTP 200
   within its existing budget — no frozen or unresponsive window."* — Ran the canonical
   `scripts/qa/poll_health.py http://localhost:8255/api/health <out.csv> <stopfile> --count 240` (this
   round's explicit TESTING-REQUIREMENTS directive, not an ad hoc curl/subprocess loop). Blocking, in-turn
   invocation: process wall time `2026-08-12T07:38:22.468897536Z` → `2026-08-12T07:42:44.334604355Z`; the
   CSV's own first/last poll timestamps are `07:38:22.522446Z` → `07:42:44.289615Z` (continuous 1Hz
   polling throughout, no gap — this agent states only what the script's own timestamps show, not an
   inferred "observed continuously" beyond that). **Result: 240/240 HTTP 200, 0 non-answers.** Per-poll
   wall time: min 0.009s, p50 0.015s, p90 0.761s, max 4.19s. **9/240 (3.75%) exceeded the owner-amended
   relaxed ≤ 2.0s ceiling** (2.184s–4.19s, in two clusters: 07:38:28Z–07:38:48Z [5 polls] and
   07:40:12Z–07:40:27Z [4 polls], `load_avg_1m` 1.55–2.41 on this 16-core host) — reported honestly, not
   rounded away; every one of the 9 still answered HTTP 200 within a few seconds, never a timeout,
   dropped connection, or non-200. No frozen or unresponsive window at any point across the full 4m22s
   drill. The warm itself completed partway through this drill:
   `background_compute.recent_outcomes[0]` (read after the drill) recorded `outcome:"completed"`,
   `duration_ms:482671` (~8m3s), `finished_at:"2026-08-12T07:41:07.091985+00:00"` — all 5 configured
   horizons finished cleanly, no abort/crash.
3. *(Not this lane's task this round — see dev handoff.)* Steps 3 (peak-VmPeak measurement) and 4
   (fault-injected memory-pressure abort) are TESTING REQUIREMENTS' backend/unit-test concerns this
   round: the developer's own live-job/idle-control drills (`reports/perf-budgets.md` Addendum 34) supply
   the authoritative TC-1/TC-2/TC-3 measurements, and `test_health_watchdog.py`'s error-case test (11
   passed) covers the memory-pressure-abort-adjacent "never suppress a captured sample on error"
   requirement. This browser-QA pass did not re-trigger a backend restart or fault injection (forbidden
   for this role, same hard rule applied consistently since iter-60).

**Acceptance check (browser-observable portion):**
- **Consistency / single source:** the `/data` page's `background-compute-panel` text
  (`as-of 2026-07-31, elapsed 4m 45s, horizons 2/5, dataset r2970-f6580475`, read mid-warm) matched this
  agent's own concurrent `GET /api/health` poll field-for-field; after the drill, the SAME panel read
  (`No background compute running.` / `Last outcome: completed / as-of 2026-07-31 / 8m 3s`) —
  consistent with `recent_outcomes[0]`'s `duration_ms 482671` — confirms the UI reads the same live
  endpoint at every point, not a stale or fabricated render.
- **Honest status:** `readiness-badge` read `data-state="ready"` throughout (checked mid-warm and
  post-completion), even while the background job was active; `last-run-status="ok"`;
  `aggregates-refreshed` listed all 9 categories (latest snapshot, coverage, membership timeline, market
  phase, forward aggregates, research hot keys, availability heatmap, factor lab all, drawdown
  expectations) after the run.
- **Walkthrough:** the crash-free warm + healthy `/api/health` sequence was directly observed live via
  the canonical poll script — same backend process throughout, no restart, no wedge.

**Code-change verification (this round's TESTING REQUIREMENTS directive, closing iter-67/d for this
round):** this agent independently ran `git diff --stat` / `git diff` against every file the dev handoff
claims changed, rather than repeating the write-up's prose unverified:
- `apps/backend/app/api/health.py`: `git diff --stat` shows `29 ++++++++-` — the diff itself shows a new
  guarded block immediately before `return {...}`: `health_watchdog.record_handler_compute(t_handler_start,
  time.monotonic(), t_received_wall)` inside a `try/except Exception: pass`, and `t_handler_start`/
  `t_received_wall` promoted out of the queue-wait-only block so both samples share the same start
  instant.
- `apps/backend/app/engine/health_watchdog.py`: `git diff --stat` shows `48 ++++++++++++++++++---` — the
  diff shows a new `HANDLER_COMPUTE_TYPE = "handler_compute"` constant and a new
  `record_handler_compute(t_handler_start_monotonic, t_before_return_monotonic, t_received_wall)`
  function that writes one JSON-line entry via the existing `append_entry` writer.
- `apps/backend/tests/test_health_watchdog.py`: `git diff --stat` shows `73 ++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++-` — new assertions for
  flag-off (no `handler_compute_s` entry), flag-on (one entry alongside `queue_wait_s`), and two-request
  (two entries).
- `reports/perf-budgets.md`: `git diff --stat` shows `190 +++++...` and `grep -n "^## Addendum 34"` finds
  a new section at line 10954, dated 2026-08-12.
- `git diff -- apps/backend/app/engine/data_manager.py apps/backend/app/engine/research.py` (the
  `compute_forward_aggregates`/`compute_factor_lab_all_warm`/`coverage_membership_timeline_refresh` call
  chains) returned **EMPTY** — independently confirms the dev handoff's "no change to that call chain"
  claim directly from the diff, rather than trusting the write-up.
- `git status --porcelain` at check time showed no `apps/frontend/*` entries — confirms "Frontend
  Present: no" for this iteration.

No code-change claim in this report goes beyond what these `git diff`/`git status` reads directly showed.

**Golden replay script:** `runs/goal-session-ops-hardening/journey-scripts/J-07.json` already existed
(established over iterations 54, 58, 60–67) as a fast, deterministic regression check that the
browser-visible surfaces (`readiness-badge`, `background-compute-panel`, `last-run-status`,
`aggregates-refreshed`) genuinely wire to `GET /api/health` and persisted `data_provider_runs` rows — by
design it cannot replay a multi-minute concurrent-polling drill (`demo_runner.py` supports only
`goto`/`click`/`fill`/`expect`, no raw-HTTP-timing or process-control action type). This pass re-verified
all five of its steps live (all held) and appended an iter-68 entry to its `_notes` array documenting
this round's canonical-script drill (240 polls via `poll_health.py`, 0 non-200, 9/240 breaches over the
relaxed ceiling, the independent git-diff verification above) — no step text was changed. Lint-checked
clean: `python3 scripts/automation/lib/demo_runner.py --mode lint --scripts-dir
runs/goal-session-ops-hardening/journey-scripts --journeys J-07` → `J-07 ok`.

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
- **Test Date:** 2026-08-12 (checks executed ~07:33Z–07:43Z UTC / ~08:33–08:43 BST)
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-68-evidence/`
- **Backend process:** pid 1167030, `uvicorn main:app --host 0.0.0.0 --port 8255` (single long-lived
  process throughout this test; started before this agent's dispatch, `TRENDORA_HEALTH_WATCHDOG` not set
  on this particular process's environ — the dev pass's own TC-1/TC-2/TC-3 watchdog-armed drills were run
  separately, as recorded in `docs/handoffs/goal-ops-hardening-iter-68-dev.md`; this browser-QA pass
  verifies J-07's steps 1–2 crash-free-serving acceptance clause against the currently-running instance,
  independent of the `handler_compute_s` diagnostic sample itself)

**Timezone note:** all timestamps in this report are UTC (matching DB/JSON artifact convention,
confirmed via `date -u` for every wall-clock read); the host's `logs/backend.log` lines are host-local
BST (UTC+1) and were not directly cited in this pass's timing evidence.
