# UI Test Results (merged)

**Date:** 2026-08-13
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 8/8 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work (live job card, not persisted history) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-75-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap (a >370-day span is accepted AND executes to completion in chunks) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-75-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status — regression-hardening golden (J-04's product behavior is already proven/evidenced; this asserts the readiness badge's REAL data-state attribute and a persisted data_provider_runs-backed field, never a bare page-title/heading match) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-75-evidence/J-04-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly — a live in-app backfill of ONE unsnapshotted historical trading day (2005-07-14, resolved at replay time and guaranteed to have 0 snapshot rows — see this file's _notes), waited out for its real duration, then proven from the run's OWN persisted record and its OWN /scanner-runs row | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-75-evidence/J-05-verify.png |
| UT-J-06 | Pages load only what they need | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-75-evidence/J-06-verify.png |
| UT-J-07 | Heavy aggregates never take the service down | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-75-evidence/J-07-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | happy-path | P1 | `/backtest` serves last-complete stored version instantly (≤1.5s) with a "refreshing" indicator while a version's warm is in flight, then serves the new version's fresh values with the indicator gone once the warm completes — never a skeleton, never a request-path recompute | Live-drove a real single-day backfill (2005-07-18, a genuine backfill gap); while its ~20m33s finalize warm was in flight, `/backtest` at as-of 2026-07-31 served the last-good stored version (2979 snapshots, generated 07:15:21) in 0.116-0.223s with the `evidence-refreshing` banner reading "Refreshing — showing the last complete evidence… evidence as of 2026-07-31, generated 2026-08-13 07:15:21"; after the warm completed, reload served the fresh version (2980 snapshots, generated 07:35:43) in 0.116s with the banner gone | PASS | `reports/qa/goal-ops-hardening-iter-75-evidence/J-08-fresh-settled.png` (+ `J-08-refreshing-indicator.png`, `J-08-refreshing-window.png`) |
| UT-J-09 | The backend discloses its own background-compute activity | happy-path | P1 | Top-bar badge and `/data`'s BackgroundComputePanel disclose an in-flight background-compute window (as-of, elapsed, horizons done/total, dataset version) sourced from the same `GET /api/health` poll, honest process-lifetime-only scope, and an idle/last-outcome state once the window completes — never a bare "Ready" that hides it, never a fabricated estimate | Observed a real BCW end-to-end live: badge showed "Ready" + "background compute running (1)" simultaneously while `/backtest` (as-of 2026-07-31, via `asof-step-prev`) returned instantly with partial content (1d populated, 5d/10d/20d/60d honest "— n=0"); `/data`'s `background-compute-panel` mirrored the exact same as-of/elapsed/horizons/dataset from the same poll; after 8m4s the window completed (`recent_outcomes` duration_ms=483875) and both badge and panel flipped to idle — panel showed "No background compute running." + "Completed / as-of 2026-07-31 / 8m 4s" + the verbatim process-lifetime-only disclosure; steady-state health measured 0.005s (well inside ≤0.1s) | PASS | `reports/qa/goal-ops-hardening-iter-75-evidence/J-09-idle-last-outcome.png` (+ `J-09-active-window.png`) |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-13

