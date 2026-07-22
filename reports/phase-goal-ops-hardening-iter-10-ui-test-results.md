# UI Test Results (merged)

**Date:** 2026-07-22
**Written by:** merge_ui_test_results.py (LLM browser-qa + deterministic replay)

---

**Browser QA Verdict:** PASS

**Overall:** 4/4 journeys passed (0 skipped)

---

## Results Table

| Test ID | Name | Type | Priority | Expected | Actual | Verdict | Evidence |
|---------|------|------|----------|----------|--------|---------|----------|
| UT-J-01 | Backfill honors the requested range and explains zero-work | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-10-evidence/J-01-verify.png |
| UT-J-03 | No per-run range cap | regression | P1 | journey replays end-to-end; all expects hold | journey replayed end-to-end; all expects held | PASS | reports/qa/goal-ops-hardening-iter-10-evidence/J-03-verify.png |
| UT-J-04 | J-04: Non-blocking boot with visible status (6-step journey) | regression (target: step 6 closure) | P1 | All 6 acceptance steps hold, incl. an interrupted mid-flight job showing its last persisted (non-zero) progress, never zeros/still-"running" | Steps 1-5: carried-forward durable evidence + fresh log-level corroboration (see breakdown). Step 6: **live DOM read of `/data` Run History row for run 119** (job `bad4f8e94be8448fbb0ac5812f1005c4`, backfill 2014-01-02→2015-12-31, caught mid-flight — pre-kill poll `running, snapshots_created:162, dates_done:203/504`) — status `interrupted`, `Snapshots: 117` (non-zero), breakdown `729 calendar days · 41 already snapshotted · 225 non-trading` (non-null); corroborated by a prior cycle's run 114 (`interrupted`, `Snapshots: 59`) — contrasted live, on the same page, against 8 sibling pre-fix `interrupted` rows all showing `0`/null. `kill -9` on backend pid 2080333 at 2026-07-22T20:32:15+01:00 (19:32:15Z), restart pid 2100030 at 20:32:18+01:00, `GET /api/health` 200 at 20:32:55+01:00 — restart timestamp and new pid independently confirmed live in `logs/backend.log` and via `ps`/`ss` this turn; no clean-shutdown line for pid 2080333 anywhere in the log before the restart banner. | PASS | `reports/qa/goal-ops-hardening-iter-10-evidence/UT-J-04-step6-run119-crash-cycle-evidence.txt`, `UT-J-04-step6-run114-dom-evidence.txt`, `UT-J-04-step6-run119-data-page-top.png`, `UT-J-04-data-page-loaded.png` |
| UT-J-05 | J-05: Aggregates are precomputed at ingest, never on the fly (light non-heavy re-confirmation per TC-7) | regression (required-still-passing) | P1 | A single-day backfill's aggregates serve from storage with no on-request recompute; market phase/leaderboard render instantly from the stored snapshot; cold `/data` load stays within budget; health stays responsive around ingest — all WITHOUT running the heavy-ingest pytest test | Ran a real, fresh, single unsnapshotted-day backfill (2021-09-15, run id 117) live via the `/data` UI; confirmed the persisted run record lists 7 refreshed aggregates (`latest_snapshot, coverage, membership_timeline, market_phase, forward_aggregates, research_hot_keys, drawdown_expectations`); confirmed `/scanner-runs/1193` renders the new date's "Immutable snapshot" (Market Regime 73.02, Risk-on) instantly, stored-not-recomputed; confirmed a subsequent `/data` navigation completed in 226.9 ms (`loadEventEnd`); confirmed `GET /api/health` returned 200 in ~473 ms WHILE a second, larger ingest job (run 118) was actively running. Heavy-ingest pytest test NOT run (per BINDING instruction). | PASS | `UT-J-05-stored-snapshot-scanner-run-378.png` (pre-existing stored date, sanity check), plus the fresh run described above (see Passed Tests section for full detail; no separate screenshot of run 1193 was taken due to the scroll-screenshot capture limitation noted below — the DOM/markdown text capture is the evidentiary artifact) |

## Environment

- **Browser:** Chromium (LLM browser-qa + deterministic replay)
- **Test Date:** 2026-07-22

