# UI Test Results (merged)

**Date:** 2026-08-11
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 7/7 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | Backfill of 2026-05-02→2026-05-29 reports dates_total=19 with exclusion reasons; a weekend-only span (05-02→05-03) reports 0/0 with a per-reason breakdown; both zero-work outcomes render an explicit, visually-distinct explanatory note (not a fabricated success); results persist across reload; `/scanner-runs/748` shows the stored 2026-05-29 leaderboard | Both backfills resolved as honest zero-work (data already fully backfilled from many prior iterations): job progress showed "no new snapshots", "19/19 dates", "28 calendar days · 19 already snapshotted · 9 non-trading", and a `zero-work-note` element with text "Zero-work outcome — every requested trading day already had a snapshot... this is not a failure", styled with neutral `border-border bg-surface-2 text-text-muted` classes (never a success-green treatment). Weekend-only run showed "0/0 dates" / "2 calendar days · 0 already snapshotted · 2 non-trading". Reload of `/data` showed both new runs at the top of the persisted Run history table (2026-08-11 14:12:11 and 14:10:58 entries), never "no job started this session". `/scanner-runs/748` rendered "Immutable snapshot — as of 2026-05-29" with a populated leaderboard (component breakdown, candidate counts, ticker rows led by MU 97.06) — stored values, not a recompute. | PASS | `reports/qa/goal-ops-hardening-iter-62-evidence/UT-J-01-result.png` |
| UT-J-03 | No per-run range cap (a >370-day span is accepted AND executes to completion in chunks) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-62-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | Readiness badge reads `data-state="ready"`; preflight banner shows a real verdict; `/data`'s persisted `last-run-status` field renders; persistent backend logfile contains boot events | `[data-testid="readiness-badge"]` read `{text:"Ready", state:"ready"}` immediately, no wait needed; `[data-testid="preflight-banner"]` read "GO — today's board is current."; on a fresh `/data` navigation `[data-testid="last-run-status"]` read "no new snapshots" (a real `data_provider_runs`-backed value, matching the zero-work backfill run just completed under UT-J-01); `logs/backend.log` directly confirmed to contain repeated "Uvicorn running on http://0.0.0.0:8255" boot lines including one immediately preceding the currently-running process's 2026-08-11 14:24:30 start. Crash/kill-9/interrupted-job re-simulation (goal steps 4-6) NOT re-executed this pass — restarting the live backend is forbidden for this role (standing hard rule, same as iter-58/60/61's J-04 handling); that exact behavior remains evidenced live by iter-53's UT-05/06/07 captures, unaffected by this iteration's diff. | PASS | `reports/qa/goal-ops-hardening-iter-62-evidence/UT-J-04-result.png` |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly — a live in-app backfill of ONE unsnapshotted historical trading day (2010-11-17 must have 0 snapshot rows before this runs; re-verify and rotate if a prior lane consumed it), waited out for its real duration, then proven from the run's OWN persisted record and its OWN /scanner-runs row | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-62-evidence/J-05-verify.png |
| UT-J-06 | Pages load only what they need | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-62-evidence/J-06-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-62-evidence/J-09-verify.png |
| UT-J-07 | Heavy aggregates never take the service down | regression | P1 | Readiness badge `ready`; background-compute panel discloses real (non-fabricated) state; persisted `last-run-status` and `aggregates-refreshed` fields render from `data_provider_runs` | `[data-testid="readiness-badge"]` read `data-state="ready"`; `[data-testid="background-compute-panel"]` present (no active warm at check time — 5 direct `GET /api/health` samples at ~1s apart all answered HTTP 200 in 9-19ms with `background_compute.active=[]`, i.e. an earlier warm this same long-lived process had run at ~14:06 had already finished cleanly by this pass, itself supporting evidence the process survives heavy compute without wedging); `[data-testid="last-run-status"]` read "no new snapshots"; `[data-testid="aggregates-refreshed"]` read "Refreshed: forward aggregates, research hot keys, factor lab all, drawdown expectations". Fault-injected memory-pressure abort (goal step 4) NOT re-run this pass — requires a backend restart, forbidden for this role (same standing rule as iter-60/61); this iteration's diff does not touch the warm/aggregate code path, so no new risk to that acceptance clause. | PASS | `reports/qa/goal-ops-hardening-iter-62-evidence/UT-J-07-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-11

