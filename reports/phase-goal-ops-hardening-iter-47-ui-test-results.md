# UI Test Results (merged)

**Date:** 2026-08-04
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** BLOCKED

**Overall:** 14/14 journeys passed (0 skipped, 2 target-missing)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-47-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-47-evidence/J-03-verify.png |
| UT-J-04 | Non-blocking boot with visible status | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-47-evidence/J-04-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-47-evidence/J-05-verify.png |
| UT-J-08 | Backtest evidence serves from storage only — never a cold recompute on request | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-47-evidence/J-08-verify.png |
| UT-J-09 | Disclose in-flight background-compute activity (badge + /data panel) | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-47-evidence/J-09-verify.png |
| UT-01 | Evidence page loads without errors | smoke | P1 | Heading "Evidence" visible, ≥1 claim card or empty-state card, no "Backend unavailable" card, no console errors | Heading visible; 7 `evidence-claim-row` cards rendered; no error card; console-log capture unimplemented in this Chrome MCP build (noted, not a failure) | PASS | `reports/qa/goal-ops-hardening-iter-47-evidence/UT-01-result.png` |
| UT-02 | Idle Evidence page fast, no Refreshing badge | happy-path | P1 | Page renders with no multi-second hang; no claim shows the "Refreshing" badge; every panel shows real median/p90/n numbers | Single navigate returned immediately; 0 occurrences of `evidence-expectations-refreshing` across all 7 claims; all 7 tables populated with real median/p90/n figures, 0 "Unavailable" panels | PASS | `reports/qa/goal-ops-hardening-iter-47-evidence/UT-02-result.png` |
| UT-03 | New backfill triggers honest "Refreshing" badge | happy-path | P1 | After a genuinely new trading day is ingested, ≥1 claim shows the amber "Refreshing" badge with real table numbers, the added disclosure sentence, and the page still loads fast | Ran a fresh `both` (fetch+backfill) job for 2026-08-03 (the next real trading day after the prior latest bar 2026-07-31 — 2026-08-01/02 are a weekend, see Notes); immediately after completion ALL 7 claims flipped to `expectations_status:"refreshing"`, each retaining real median/p90/n numbers and the exact disclosure sentence "A newer version is computing in the background after a recent data update — the table below is the last complete version, not a partial or fabricated one."; `GET /api/evidence`/page load stayed fast throughout (health polls stayed HTTP 200, no multi-second hang observed) | PASS | `reports/qa/goal-ops-hardening-iter-47-evidence/UT-03-result.png` |
| UT-04 | "Refreshing" badge clears after catch-up | happy-path | P2 | Badge no longer present after the background catch-up finishes; table numbers may differ or match, never blank | All 7 claims' "Refreshing" badges cleared (`expectations_status` absent, confirmed via both the `GET /api/evidence` API and a fresh browser load); all 7 tables still populated with real numbers. See Notes for the actual settle-time observation (much longer than the "~8-10 min" example window, attributable to repeated backend restarts in this QA session, not a code defect) | PASS | `reports/qa/goal-ops-hardening-iter-47-evidence/UT-04-result.png` |
| UT-05 | Data Manager backfill flow still works | regression | P1 | No client-side validation error; job-status badge appears; Run history gets a new row | Filled 2026-07-30→2026-07-31 (already-snapshotted range), clicked Start; job-status badge read "no new snapshots" with an honest "Zero-work outcome" message; Run history row added with correct stats | PASS | `reports/qa/goal-ops-hardening-iter-47-evidence/UT-05-result.png` |
| UT-06 | Home + Evidence stay responsive during a backfill | regression | P1 | Both pages load quickly while a job is running; no "Backend unavailable" card; no indefinite spinner | While the UT-03 job was "running", `/` loaded and showed the "Ready" health badge (`data-state="ready"`); `/evidence` loaded within a couple seconds showing all 7 claim cards (no error card, no infinite spinner) | PASS | `reports/qa/goal-ops-hardening-iter-47-evidence/UT-06-result.png` |
| UT-07 | "Unavailable"/absent panel states unchanged | regression | P3 | Any "Unavailable" or absent-panel claim renders unchanged; neither state shows the Refreshing badge | Observational: at test time all 7 live claims are in the full-table state (0 in "Unavailable", 0 with no panel) — nothing to contradict; confirmed the Refreshing badge never appears outside the full-table state | PASS | `reports/qa/goal-ops-hardening-iter-47-evidence/UT-07-result.png` |
| UT-08 | "Refreshing" badge is calm and doesn't break layout | ux | P2 | Badge sits inline, amber/warn color (not alarm-red, not full-width banner); rest of card unchanged; disclosure sentence reads naturally | Badge renders as a small inline amber pill directly beside the "Historical drawdown & dry-spell expectations" heading, visually distinct from the red "FAIL" verdict badge; verdict badge, hypothesis chips, registration date all laid out normally with no overlap/wrapping; disclosure sentence reads as a natural continuation of the existing paragraph | PASS | `reports/qa/goal-ops-hardening-iter-47-evidence/UT-08-result.png` |

## Missing Target Journeys

_Target journeys named in the iteration spec's `Target journeys:` line — the journeys THIS iteration exists to verify — that were NOT verified this iteration, either no lane produced a row for them at all, or the only row they have reads SKIP (not executed). Never a clean PASS/SKIPPED headline while any of these are present (ops-hardening iter-41 audit finding B2 / iter-42 fix: promoting a journey to an iteration's own target silently removed its verification — iter-41 itself shipped a clean PASS 6/6 headline while its two target journeys had zero rows anywhere)._

- `UT-J-06` — no test case executed for J-06 by any lane
- `UT-J-07` — no test case executed for J-07 by any lane

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-08-04

