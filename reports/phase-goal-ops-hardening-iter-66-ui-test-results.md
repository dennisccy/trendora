# UI Test Results (merged)

**Date:** 2026-08-12
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 8/8 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work (live job card, not persisted history) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-66-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap (a >370-day span is accepted AND executes to completion in chunks) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-66-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status — regression-hardening golden (J-04's product behavior is already proven/evidenced; this asserts the readiness badge's REAL data-state attribute and a persisted data_provider_runs-backed field, never a bare page-title/heading match) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-66-evidence/J-04-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly — a live in-app backfill of ONE unsnapshotted historical trading day (2005-06-30, resolved at replay time and guaranteed to have 0 snapshot rows — see this file's _notes), waited out for its real duration, then proven from the run's OWN persisted record and its OWN /scanner-runs row | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-66-evidence/J-05-verify.png |
| UT-J-06 | Pages load only what they need | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-66-evidence/J-06-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request (payload-gated) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-66-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-66-evidence/J-09-verify.png |
| UT-J-07 | Heavy aggregates never take the service down | regression/reliability | P1 | During a real forward-aggregate warm (the ingest finalize path), `GET /api/health` keeps answering HTTP 200 with no frozen/unresponsive window, `/backtest` keeps serving per-horizon evidence, and the UI honestly discloses the in-flight compute — no crash, wedge, or restart | Caught the tail of the dev pass's own real TC-1 backfill job's finalize-tail warm already in flight (asof_key 2026-07-31, started 01:14:10Z). Ran this agent's own supplementary drill through the NOW-canonical `scripts/qa/poll_health.py` (first time this golden's own history used it instead of an ad hoc curl/bash loop) — 150 polls, 01:17:29Z–01:20:17Z: **150/150 HTTP 200, 0 non-answers**. 6/150 (4%) exceeded the relaxed 2.0s ceiling (max 3.786s); cross-checked against the dev's own `dev.log` phase-timing lines and confirmed NONE fall inside this iteration's named target phase (`coverage_membership_timeline_refresh`, which had already completed cleanly 12 minutes earlier at 01:02:26Z) — they fall inside the later `drawdown_expectations_warm` sub-phase instead. Navigated `/` mid-warm (rendered fully, badge honestly read "background compute running (1)") and `/backtest` post-warm (`recent_outcomes[0].outcome:"completed"`, no crash — full forward-tested-evidence aggregates for all 5 horizons rendered, served from storage per J-08). Re-checked `/data`: all 5 golden assertions held live. | PASS | `reports/qa/goal-ops-hardening-iter-66-evidence/UT-J-07-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-12

