# UI Test Results (merged)

**Date:** 2026-07-25
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 4/5 journeys passed (1 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-21-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-21-evidence/J-03-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-21-evidence/J-05-verify.png |
| UT-J-08 | J-08: Backtest evidence serves from storage only — never a cold recompute on request | functional (target journey) | P1 (target) | A literal small single-day backfill bumps the dataset version; `/backtest` (is_latest view) serves the last-complete stored version labeled "refreshing" within ≤1.5s while the finalize warm is in flight, then serves the freshly-warmed version "ready" within the same budget once `aggregates_refreshed` includes `forward_aggregates` — never a request-path recompute | Submitted a real single-day backfill (2025-05-27, a confirmed never-snapshotted trading day) via the `/data` UI. Caught the live "refreshing" window via Chrome MCP: `evidence-refreshing` banner present, exact expected copy, `/api/backtest` HTTP 200 in 0.061s with `evidence_status=refreshing`, `evidence_generated_at` unchanged (stale/prior version correctly served). ~6m47s later (host-guard-throttled finalize hook; run 167's `aggregates_refreshed` now included `forward_aggregates`), reloaded `/backtest` again: banner gone, HTTP 200 in 0.054s, `evidence_status=ready`, `evidence_generated_at` now a NEW timestamp (genuine fresh compute). See narrative below for the full evidence chain and one honest caveat on `evidence_asof`'s literal value | PASS | `reports/qa/goal-ops-hardening-iter-21-evidence/UT-J-08-01-before-ready.png`, `UT-J-08-02-data-manager-top.png`, `UT-J-08-03-refreshing.png`, `UT-J-08-04-ready-after-warm.png` |
| UT-J-04 | J-04: Non-blocking boot with visible status (required-still-passing regression lane) | regression | P1 (required-still-passing) | Journey's 6 numbered steps (backend restart timing, ≤250ms health polling through a second restart, kill→crashed presentation, logfile boot/abrupt-end evidence, restart→interrupted-job presentation) executed as a test case | NOT EXECUTED — steps 1, 3, 4, 6 all require restarting or forcibly killing the live, pump-verified backend. This iteration's spec puts re-triggering that exact disruptive replay explicitly OUT OF SCOPE (TC-14 already supplies fresh, owner-authorized 2026-07-25 evidence: Part A kill -9 → restart → ready in ~25s; Part B wide-backfill checkpoint survived a mid-run kill -9, `status: interrupted`, `dates_done` preserved) and its Definition of Done / Testing Requirements state the browser-qa lane is "expected to SKIP the disruptive steps as it always has." No non-disruptive partial substitute was attempted (matching this session's deliberate iter-17/19/20 precedent, which found no browser-observable subset of J-04's own acceptance criteria that doesn't require an actual restart/kill event) | SKIP | n/a — see Skipped Tests section below |

## Skipped Tests

### UT-J-04 — J-04: Non-blocking boot with visible status (required-still-passing regression lane)

**Verdict:** SKIPPED
**Reason:** NOT EXECUTED — steps 1, 3, 4, 6 all require restarting or forcibly killing the live, pump-verified backend. This iteration's spec puts re-triggering that exact disruptive replay explicitly OUT OF SCOPE (TC-14 already supplies fresh, owner-authorized 2026-07-25 evidence: Part A kill -9 → restart → ready in ~25s; Part B wide-backfill checkpoint survived a mid-run kill -9, `status: interrupted`, `dates_done` preserved) and its Definition of Done / Testing Requirements state the browser-qa lane is "expected to SKIP the disruptive steps as it always has." No non-disruptive partial substitute was attempted (matching this session's deliberate iter-17/19/20 precedent, which found no browser-observable subset of J-04's own acceptance criteria that doesn't require an actual restart/kill event)

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-25

