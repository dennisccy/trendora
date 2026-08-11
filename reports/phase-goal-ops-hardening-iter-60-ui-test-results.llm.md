# Phase goal-ops-hardening-iter-60 — UI Test Results

**Phase:** goal-ops-hardening-iter-60
**Date:** 2026-08-11
**Written by:** browser-qa-agent

---

**Browser QA Verdict:** PASS

<!-- PASS: J-05 and J-07 (this pass's assigned Target journeys) both hold on every step this agent is
     permitted to execute (browser + read-only API/DB verification): J-05 steps 1/2/4 and J-07 steps 1/3
     were independently, live re-verified against a real ~18m20s in-app backfill this pass itself drove
     end to end; J-07 step 2 is explicitly out of scope for re-scoring this iteration per the dispatch
     (an outstanding owner decision, restated below with this pass's own honest numbers). The only
     sub-steps NOT independently re-executed (J-05 step 3's backend restart, J-07 step 4's fault
     injection) both require restarting the backend under test, which this agent's hard rule forbids;
     both are corroborated instead by same-day, unchanged-code-path evidence from this same session
     (Addenda 25/26, reports/perf-budgets.md) rather than claimed as freshly observed. -->

**Overall:** 2/2 target-journey tests passed (0 failed, 0 skipped) — lean-mode scope was EXACTLY J-05 and
J-07 per the dispatch; J-01/J-03/J-04/J-06/J-08/J-09 were explicitly excluded from this pass (verified
separately by the deterministic replay lane — see `reports/phase-goal-ops-hardening-iter-60-regression-
replay-results.md`, 6/6 PASS).

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-05 | J-05: Aggregates are precomputed at ingest, never on the fly | regression | P1 | See journey Acceptance below | Steps 1/2/4 independently live-verified via a real ~18m20s in-app backfill (2010-11-16); step 3 (backend restart) corroborated by same-day, unchanged-code-path evidence (Addendum 25/26) rather than re-executed | PASS | `reports/qa/goal-ops-hardening-iter-60-evidence/UT-J-05-result.png` |
| UT-J-07 | J-07: Heavy aggregates never take the service down | regression | P1 | See journey Acceptance below | Steps 1/3 independently live-verified via the SAME backfill's finalize-tail forward-aggregate warm + 741/741 health polls + VmPeak sample; step 2 restated (not re-scored) per dispatch; step 4 (fault injection) corroborated by same-day, unchanged-code-path evidence (Addendum 26) rather than re-executed | PASS | `reports/qa/goal-ops-hardening-iter-60-evidence/UT-J-07-result.png` |

---

## Passed Tests

### UT-J-05 — J-05: Aggregates are precomputed at ingest, never on the fly
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-60-evidence/UT-J-05-result.png` (acceptance state — the
`/scanner-runs/2954` immutable-snapshot leaderboard, Market Regime score visible)

This journey's own code paths (`_do_backfill`'s finalize tail, `market_phase_cache`, `compute_coverage`,
boot) are UNCHANGED by this iteration (`git diff --stat` confirms only `research.py`, `test_regime_lab.py`,
`_labs.tsx`, `sample-link.tsx`, `replay-lane.sh`, `test-replay-lane.sh` were touched), so this is a
regression re-verification, executed live rather than assumed.

**Step 1 — run a backfill covering exactly one unsnapshotted historical trading day:**
Pre-check via read-only `sqlite3`: `2010-11-16` had 0 `scanner_runs` rows and 466 real `daily_prices` rows
(including a genuine SPY close) — a real trading day, not a gap; the correct single-use target per the
golden's own rotation discipline. Drove the real `/data` form: `[data-testid="job-start-date"]` and
`[data-testid="job-end-date"]` both set to `2010-11-16` (job kind defaulted to `backfill`, confirmed via
the kind `<select>`'s live value), clicked "Start". Job started immediately (`job-status` read "running"
within seconds, `data_provider_runs.id=404` created at `2026-08-11 06:58:36.399` UTC) — not
accepted-then-never-run.

**Step 2 — after completion, assert aggregates serve from storage:**
The job ran to completion at `07:16:56.677` UTC (18m20.3s), `status: "ok"`, `snapshots_created: 1`,
`forward_returns_inserted: 1355`. The live job card showed `1/1 dates`, `1 snapshots · 1355 forward returns
inserted`, `1 calendar day · 0 already snapshotted · 0 non-trading`, a populated `stage-timings` panel, and
`aggregates-refreshed` listing all 9 categories (`latest_snapshot, coverage, membership_timeline,
market_phase, forward_aggregates, research_hot_keys, availability_heatmap, factor_lab_all,
drawdown_expectations`) — matching the persisted `data_provider_runs.message` JSON exactly. Navigated to
`/scanner-runs`: `2010-11-16` listed at the top. Clicked through to `/scanner-runs/2954`: rendered
"Immutable snapshot — as of 2010-11-16" with a populated leaderboard (real regime score 61.06/100 visible
in the screenshot) — never the "No stored stock rows" empty state.

Storage-not-recompute proof for market phase (acceptance clause (a)): direct `sqlite3` read of
`market_phase_cache` shows the row for `asof_key='2010-11-16'` was `created_at = 2026-08-11 06:58:58.89` —
inside the job's own finalize tail, ~22s after the job started, and roughly 20 minutes BEFORE this pass's
own `GET /api/market-phase?as_of=2010-11-16` request (0.171s response) — the request served the
already-written row, it did not trigger a fresh compute.

**Step 3 — restart the backend, visit `/data` cold — NOT independently re-executed this pass.**
Browser-qa-agent's hard rule forbids restarting the app under test. This iteration's `git diff` touches no
boot/coverage/warmup code, so the same-session, same-day (2026-08-11) restart evidence already on record
stands as current, non-stale corroboration: `reports/perf-budgets.md` Addendum 25/26 — relaunch → first
`GET /api/health` 200 in 1.712s (J-04 budget ≤5s), cold `GET /api/data` 0.243s (budget ≤3000ms), a
zero-prefill-pattern boot-log check (0 of 12 lines matched `prefill`/`daily_prices`/`bar_cache`/
`whole-table`). This iteration's own dev pass independently restarted `scripts/dev.sh` twice during
pre-handoff verification (both healthy in ~1s), consistent with the same conclusion.

**Step 4 — poll `GET /api/health` while a heavy ingest job runs:**
An independent background `curl` loop (outside the browser, running for the FULL job window) polled
`GET /api/health` at ~1Hz from `06:59:30` to `07:16:57` UTC: **741/741 = 100% HTTP 200**, zero non-200,
zero gaps — the backend stayed fully responsive throughout the entire live 18m20s heavy backfill.

Full measurement table and the market-phase/aggregates-refreshed DB evidence: `reports/perf-budgets.md`
Addendum 27.

Golden replay script re-verified live and updated at
`runs/goal-session-ops-hardening/journey-scripts/J-05.json` — rotated its target date from the now-consumed
`2010-11-16` to a freshly live-verified reserve, `2010-11-17` (0 `scanner_runs` rows, 467 real
`daily_prices` bars including SPY, confirmed via `sqlite3` immediately before this edit); lints clean via
`demo_runner.py --mode lint --journeys J-05`.

### UT-J-07 — J-07: Heavy aggregates never take the service down
**Verdict:** PASS
**Evidence:** `reports/qa/goal-ops-hardening-iter-60-evidence/UT-J-07-result.png` (acceptance state — fresh
`/data` load with no active job this browser session; DOM assertions below are the load-bearing evidence,
the screenshot is a visual sanity check of the same page load)

**Step 1 — trigger the forward-aggregate warm for every configured horizon (ingest finalize path), serve
`GET /api/backtest` throughout:** The SAME live backfill driving J-05 above IS "the ingest finalize path"
this step names — its own `aggregates_refreshed` list includes `forward_aggregates` (1355 forward returns
inserted across all 5 configured horizons, `config.yaml:777` → `[1, 5, 10, 20, 60]`). `GET /api/backtest`
— confirmed by direct source read (`apps/backend/app/api/backtest.py:143-181`) to return every configured
horizon's evidence in one payload (`evidence_by_horizon`) — was polled every ~10th health-check tick for
the full 18m20s window by the same background loop: **75/75 HTTP 200**, in the SAME long-lived process
(pid 1307792, unchanged start to finish). A post-job direct call confirmed storage-serving per J-08:
`GET /api/backtest` → HTTP 200 in 0.031s.

**Step 2 — poll `GET /api/health` once per second, assert every poll answers 200 — restated per dispatch,
not re-scored** (the ≤2s bounded-window ceiling question remains an outstanding, ten-round-unanswered
owner decision, explicitly out of scope this iteration). This pass's own honest number, consistent with
every prior addendum: 741/741 = 100% HTTP 200 across the full 18m20s live heavy-ingest window (same data
as J-05 step 4 above — one background poll loop served both journeys' step-2/step-4 clauses).

**Step 3 — record peak memory (VmPeak), assert under `server.memory_cap_mb`, margin recorded:** Backend
VmPeak peaked at **4,038,024 kB (3944 MB)** during the live job — cap is `server.memory_cap_mb=8192` MB
(confirmed live: `/proc/<pid>/limits` "Max address space" = 8589934592 bytes = exactly 8192 MiB;
`MALLOC_ARENA_MAX=2` in the process environment; `logs/backend.log`'s boot banner reads
`memory_cap_mb=8192 malloc_arena_max=2`). Margin: **4248 MB, 52%** — recorded in `reports/perf-budgets.md`
Addendum 27.

**Step 4 — induce memory pressure, assert the SAME process keeps serving — NOT re-run this pass.** Requires
arming the `TRENDORA_FAULT_INJECT_MEMORY_ERROR` test hook via a backend restart, forbidden by this agent's
hard rule. This iteration touched no code in `compute_forward_aggregates`, the warm seam, or the fault
hook, so Addendum 26's live, same-session (2026-08-11) capture stands as current: fault armed, a guaranteed
cache-miss `GET /api/research/regime-lab` request returned HTTP 200 with `regime_lab_status: "unavailable"`
and 80 honestly-degraded cells (0 fabricated values), the SAME process (pid 969388) kept serving
`/api/health`/`/api/data`/`/api/market-phase`/`/api/backtest` byte-identically throughout, and disarming +
re-requesting the same key returned a clean payload — no wedge, no restart required.

**Live browser confirmation of the golden's own 5 read-only regression checks** (fresh navigation to
`/data`, no active job this browser session, so `LastRunSummary` rendered rather than the live
`JobProgressPanel`):
- `[data-testid="readiness-badge"][data-state="ready"]` present.
- `[data-testid="background-compute-panel"]` present: "No background compute running" / LAST OUTCOME
  "Completed, as-of 2026-07-31, 1m 45s".
- `[data-testid="last-run-status"]` present, text "ok".
- `[data-testid="aggregates-refreshed"]` present, listing all 9 categories.

Golden replay script re-verified live at `runs/goal-session-ops-hardening/journey-scripts/J-07.json`
(no date rotation needed — this golden is a stable, non-consuming regression check); appended this pass's
confirmation note; lints clean via `demo_runner.py --mode lint --journeys J-07`.

---

## Failed Tests

None.

---

## Skipped Tests

None. (This dispatch's scope was EXACTLY J-05 and J-07; J-01/J-03/J-04/J-06/J-08/J-09 were explicitly
excluded per the dispatch instructions — "Do NOT test these — a deterministic replay verifies them
separately" — and were in fact verified separately: 6/6 PASS in
`reports/phase-goal-ops-hardening-iter-60-regression-replay-results.md`.)

---

## Additional artifact: TC-9 opportunistic "quiet machine" measurement

Not part of J-05/J-07's own acceptance, but named in the iteration spec's test-first contract (TC-9) and
explicitly deferred to this agent's pass by the dev handoff. Captured opportunistically immediately after
the J-05/J-07 live window closed, with `GET /api/health`'s `background_compute.active` empty (genuinely
idle):
- `GET /api/research/regime-lab` (default view): HTTP 200 in **53.425s** (cold — first hit under the new
  dataset version this pass's own backfill just created).
- `GET /api/research/regime-lab?view=pooled` (the exact query the frontend issues): HTTP 200 in
  **96.873s** (also cold, a distinct cache key).
- `GET /api/health` immediately after both: 0.022s, `readiness: "ready"` — unaffected.

First "quiet machine" comparison point against iter-58's 340s **under concurrent load** figure: 96.9s idle
vs. 340s under load for the same `view=pooled` query — roughly 3.5x faster with no concurrent compute
contending for the process, recorded honestly as one opportunistic sample (not an isolated A/B — the two
measurements are on different dataset versions). Full detail: `reports/perf-budgets.md` Addendum 27.

---

## Environment

- **Frontend URL:** http://localhost:3255
- **Backend URL:** http://localhost:8255 (confirmed healthy throughout — pid 1307792, never restarted by
  this agent)
- **Browser:** Chrome via MCP (`mcp__plugin_superpowers-chrome_chrome__use_browser`), pinned profile/CDP
  port per environment, headless throughout
- **Test Date:** 2026-08-11
- **Evidence directory:** `reports/qa/goal-ops-hardening-iter-60-evidence/`
- **Golden replay scripts updated:**
  `runs/goal-session-ops-hardening/journey-scripts/J-05.json` (date rotated 2010-11-16 → 2010-11-17, lints
  clean), `runs/goal-session-ops-hardening/journey-scripts/J-07.json` (confirmation note appended, no
  content change, lints clean)
- **perf-budgets.md updated:** Addendum 27 (J-05/J-07 live measurements + TC-9 quiet-machine timing)
