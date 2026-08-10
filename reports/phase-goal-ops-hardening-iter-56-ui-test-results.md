# UI Test Results (merged)

**Date:** 2026-08-10
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 6/6 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work (live job card, not persisted history) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-56-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap (a >370-day span is accepted AND executes to completion in chunks) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-56-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status — regression-hardening golden (J-04's product behavior is already proven/evidenced; this asserts the readiness badge's REAL data-state attribute and a persisted data_provider_runs-backed field, never a bare page-title/heading match) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-56-evidence/J-04-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request (payload-gated) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-56-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-56-evidence/J-09-verify.png |
| UT-J-06 | Pages load only what they need | regression/perf | P1 | All 11 nav-listed pages load with expected heading + content on a warm prod-mode backend; every on-load API call answers within budget (specifically `GET /api/runs` and `GET /api/data/availability`, this iteration's fix targets, must be far under the ≤1.5s budget in real-browser conditions) | All 11 pages loaded cleanly with correct headings and substantial interactive DOM content, no error-boundary/blank shell. Real-browser `performance` API confirms `GET /api/runs` 216-433ms (was 3.2-7.5s WARN pre-fix) and `GET /api/data/availability` 90ms (was 15.1-21.2s WARN pre-fix) — both now comfortably inside budget | PASS | `reports/qa/goal-ops-hardening-iter-56-evidence/J-06-result.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-10

