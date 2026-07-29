# UI Test Results (merged)

**Date:** 2026-07-29
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 7/7 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-33-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-33-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-33-evidence/J-04-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-33-evidence/J-05-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-33-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-33-evidence/J-09-verify.png |
| UT-J-06 | Pages load only what they need | regression/performance | P1 | All 11 J-06 pages load within budget in genuine prod mode (`next start`), on-load API latencies recorded in `reports/perf-budgets.md`, honest status (never frozen/blank) for any slower-than-budget path, dev-handoff code audit present | All 11 pages loaded with correct heading, zero console errors, no dev-mode overlay pill, TTI well under budget (`loadEventEnd` 28–70ms observed this pass); prod-mode `next-server` process independently reconfirmed (no HMR/webpack markers in served HTML); `/research/regime-lab`'s previously-flagged cold-cache stall now shows the honest `lab-load-panel.ts` computing-notice/retry UX (code-reviewed, PASS, 13/13 automated assertions) and its warm path renders the full, correct decile/label tables; `reports/perf-budgets.md`'s `## Iteration 33` section + auditor addendum hold the full TTI/latency table and fresh boot-to-health reading; dev handoff's step-3 per-endpoint code audit confirmed present | PASS | `reports/qa/goal-ops-hardening-iter-33-evidence/J-06-regime-lab-warm.png` |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-29

