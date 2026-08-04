# Iteration State — ops-hardening

**After iteration:** 46 · **Date:** 2026-08-04 · **Verdict:** ESCALATE

## Journeys

2 passing (J-08 J-09) · 5 partial (J-01 J-03 J-04 J-06 J-07) · 1 failing (J-05) — 8 total.

## Active blockers

- **NO journey has browser evidence against the build that SHIPPED** (dev/QA lane). Lane ran 05:49Z;
  `warmup.py` changed 06:17Z, `data_manager.py` 08:38Z. `status.json` `next_action:
  rerun_browser_lane_then_audit`; audit T1; review MINOR #2. **Re-run the lane BEFORE new code.**
- **dev — `GET /api/evidence` 163.3 s idle / >300 s loaded.** Cache key
  `r{max(scanner_runs.id)}-f{count(forward_returns)}` (`forward_testing.py:2475`): ONE new row misses
  all 7 claims, and only the slow finalize tail re-warms them. TC-4 unmet. iter-46/av.
- **dev — third unbounded site, same page:** `samples.py:145`/`:156`. Audit B3. iter-46/au.
- **dev — J-05 cannot finish ONE old day** (all remaining gaps predate the newest snapshot — the shape
  iter-45's path excluded; run 284: 0/1 in 21 min), **no J-05 screenshot, 3rd round** (iter-45/ar).
  **No owner blockers.**

## Last 2 verdicts

- iter 46: ESCALATE — J-05 failing 3 rounds; outage + OOM modes closed, but the browser lane predates
  the shipped build so nothing could score on it.
- iter 45: ESCALATE — the membership fix never ran live; ~42-min outage; review FAIL (CRITICAL).

## Do not redo

- **Both evidence-path accumulators are BOUNDED and proven** (`research.py:783-818`,
  `forward_testing.py:2270-2286`/`:2381-2404`): byte-identity + size-bound tests green, reviewer AND
  auditor re-derived it, zero MemoryErrors since. iter-44/al closed.
- **Zero-work ingest tail FIXED** — gate `data_manager.py:3768-3820` + audit B1's
  `not prog.new_snapshot_dates` at `:3803`. Verified in sqlite: 29 min → 0.19 s (runs 280 vs 290).
- **`data_manager.py:5058`/`:5091` guards DONE** (TC-5), only `warmup.py:205`/`:212` remain; **health
  budget CLOSED** (iter-43/ag: 34/34 loaded, 120/120 max 104 ms; VmPeak 3,123 MB vs the 8192 MB cap,
  perf-budgets Item O). **AG-10 intact**, never re-tune caps. No sixth `_BarCache.prefill`.
- **The golden replay is a NULL TEST for J-01/J-03** — it asserts page-wide text that persisted Run
  History already satisfies, and created no job at all at iter-45. `J-07.json` anchors verified live.
  Capture-only: J-07 `[NEW]` walkthrough, J-05 frames. iter-33/g deferred 12x.
