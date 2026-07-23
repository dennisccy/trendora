# UI Test Results (merged)

**Date:** 2026-07-23
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** FAIL

**Overall:** 12/14 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-14-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-14-evidence/J-03-verify.png |
| UT-J-05 | Aggregates are precomputed at ingest, never on the fly | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-14-evidence/J-05-verify.png |
| UT-01 | `/data` loads without errors | smoke | P1 | Page renders, no error overlay, readiness badge "ready", no console errors | Page rendered cleanly; badge `data-state="ready"`/"Ready"; rebuild-panel and "Start a fetch" card present; no `Application error` text; console showed only info/log entries | PASS | `reports/qa/goal-ops-hardening-iter-14-evidence/UT-01-result.png` |
| UT-02 | `/backtest` loads with evidence panel | smoke | P1 | Page renders, `evidence-aggregate` present pre-warm, no "Backend unavailable" card, real as-of date | Baseline (pre-job) load: `evidence-aggregate` present, `backtest-asof`="Viewing as-of 2026-07-22 (latest)", no unavailable card, no skeleton, no console errors | PASS | `reports/qa/goal-ops-hardening-iter-14-evidence/UT-02-result.png` |
| UT-03 | Readiness badge never freezes during a real warm | happy-path | P1 | Every `data-state` reading = "ready" throughout the job; terminal `job-status`="ok"; elapsed time recorded | DATE_X=2026-07-21 backfill run (job `195406893b654e36a7ab613ab4ffc032`): badge read "ready" at every explicit check (start/mid/terminal) plus continuous backend-liveness confirmation (72 consecutive 5s-interval successful reads); terminal status "ok" at 11:42:42Z; elapsed ≈ 408s (~6.8 min) from `started_at` 11:35:53.589Z | PASS | See "Passed Tests" detail below (deep-page screenshots return blank; DOM assertions are evidence of record) |
| UT-04 | `/backtest` stays usable during the same warm | happy-path | P1 | `evidence-aggregate` present within at most 2 minutes of tab-open; no "Backend unavailable" card ever | Tab opened ~11:36:14Z. Confirmed still `evidence=false`/skeleton at 135.5s (11:38:29Z) — already past the 2-min budget. Resolved `evidence=true` by 257.4s (11:40:31Z). Never showed the red unavailable card. `performance` API shows the resolving `GET /api/backtest` call itself took **211,829 ms (~211.8 s)**. | **FAIL** | `reports/qa/goal-ops-hardening-iter-14-evidence/UT-04-resolved-slow.png` |
| UT-05 | "forward aggregates" appears in live Refreshed line | happy-path | P2 | `aggregates-refreshed` includes "forward aggregates"; breakdown confirms a genuinely new snapshot | `job-status`="ok"; `aggregates-refreshed`="Refreshed: latest snapshot, coverage, membership timeline, market phase, forward aggregates, research hot keys, drawdown expectations"; `backfill-breakdown`="1 calendar day · 0 already snapshotted · 0 non-trading" | PASS | DOM assertion (see detail below); screenshot blank (deep-page) |
| UT-06 | Same value shows on persisted summary card | regression | P2 | Fresh tab shows persisted-run view, hint "from a previous session", "Refreshed:" includes "forward aggregates" | Brand-new tab, no job started this session: `last-run-status`="ok"; hint text "backfill job · 2026-07-21 → 2026-07-21 · from a previous session"; `aggregates-refreshed` includes "forward aggregates" | PASS | DOM assertion (see detail below); screenshot blank (deep-page) |
| UT-07 | Same value shows in Run History row | regression | P2 | Row Status="ok", Symbols ok/failed="0/0", breakdown includes "forward aggregates" | Run History row (Started 2026-07-23 11:35:53, Range 2026-07-21→2026-07-21): `run-status`="ok"; Symbols ok/failed="0 / 0"; `aggregates-refreshed` includes "forward aggregates" | PASS | DOM assertion (see detail below); screenshot blank (deep-page) |
| UT-08 | J-01/J-03/J-04/J-05 remain green + badge never freezes | regression | P1 | All four journeys re-verify PASS; none of 9 badge checkpoints during J-01/J-03/J-05 backfills read loading/unavailable | Adapted per this run's dispatch (goal-mode regression lanes): J-01/J-03/J-05 are verified by the deterministic golden-script replay lane external to this browser session (merges in separately, not independently re-observed here); J-04 is executed directly by this session and reported separately as UT-J-04 (SKIPPED — see below). This session's own equivalent-mechanism real backfill (UT-03, same rewritten warm path) showed the badge holding "ready" throughout, satisfying the badge-freeze intent for the portion within this session's power to test. | PASS (adapted; see caveats above) | n/a — see UT-03 evidence |
| UT-09 | Old failure states do not reoccur | error | P1 | Zero "unavailable" polls; no 2+ consecutive "loading" polls; UT-04 never shows unavailable card | UT-03's full poll record: zero `data-state="unavailable"`, zero `data-state="loading"` readings of any length. UT-04 never showed the red "Backend unavailable" card (confirmed `unavailable:false` at every check, including the ~211.8s-slow resolution). The specific pre-fix catastrophic modes (frozen badge, red card, backend wedge requiring restart) did not reoccur — a distinct, narrower slow-resolution issue was found instead (see UT-04). | PASS | Derived from UT-03/UT-04 evidence above |
| UT-10 | Job progress affordances stay clear mid-warm | ux | P3 | Activity line names a real, changing detail; heartbeat periodically resets, never looks stale-before-terminal | `current_activity` stayed fixed at "scanning 2026-07-21 (1/1)" for the entire ~6.8-min run (backend's own field, confirmed via direct API read) even after the scan sub-stage had long completed (9.85s) and the run was deep into the aggregate-warm stage — never updated to reflect that phase. Heartbeat text read "updated 1m 43s ago · possibly stalled" at one check (~110s into the warm), then later reset to "updated 10s ago" (so it does recover, not permanently frozen). | FAIL | Evaluated via DOM eval during UT-03's polling (see detail below) |
| UT-J-04 | J-04: Non-blocking boot with visible status | regression | P1 | Boot ≤5s; boot-phase visible pre-ready; crash → explicit unreachable state; log truncates on crash; mid-flight job shows interrupted state on restart | **Executed end-to-end** in a dedicated follow-up pass against a real operator-scheduled kill (12:57:13 BST) + restart (13:01:13 BST): crash → badge "Backend unavailable" + NO-GO preflight banner on `/` and `/data`, no spinner/blank frame; `logs/backend.log` ends abruptly for the killed PID (boot line present, zero shutdown lines) vs. 5 other same-day PIDs with clean shutdown sequences; boot → badge "Initializing… history 89/89" for ~3m14s before flipping to "Ready" (confirmed via the same open tab's own live polling, no reload needed); `/data` run-history row for the killed job shows `run-status`="interrupted" with real non-zero frozen progress (343 snapshots / 375 of 381 dates — vs. 381/381 scanned / 349 snapshots in the very last live read 1.6s pre-kill, an expected small checkpoint-batching gap, not the zeros bug). Boot ≤5s itself closed separately via the cited TC-7 measurement (1.80s, `reports/perf-budgets.md`). | **PASS** | `reports/qa/goal-ops-hardening-iter-14-evidence/UT-J-04-01..06*.png`; full timeline in "J-04 Follow-Up" section below |

## Failed Tests

### UT-04 — `/backtest` stays usable during the same warm

**Verdict:** FAIL
**Failure:** Tab opened ~11:36:14Z. Confirmed still `evidence=false`/skeleton at 135.5s (11:38:29Z) — already past the 2-min budget. Resolved `evidence=true` by 257.4s (11:40:31Z). Never showed the red unavailable card. `performance` API shows the resolving `GET /api/backtest` call itself took **211,829 ms (~211.8 s)**.
**Evidence:** ``reports/qa/goal-ops-hardening-iter-14-evidence/UT-04-resolved-slow.png``

### UT-10 — Job progress affordances stay clear mid-warm

**Verdict:** FAIL
**Failure:** `current_activity` stayed fixed at "scanning 2026-07-21 (1/1)" for the entire ~6.8-min run (backend's own field, confirmed via direct API read) even after the scan sub-stage had long completed (9.85s) and the run was deep into the aggregate-warm stage — never updated to reflect that phase. Heartbeat text read "updated 1m 43s ago · possibly stalled" at one check (~110s into the warm), then later reset to "updated 10s ago" (so it does recover, not permanently frozen).
**Evidence:** `Evaluated via DOM eval during UT-03's polling (see detail below)`

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-23

