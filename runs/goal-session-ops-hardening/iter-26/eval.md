# Iteration 26 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

This iteration did the job it was given. Both problems that blocked the last sign-off are now
closed with real evidence: the health-check speed test was re-run on a quiet machine and all four
numbers are inside the limit, and the "a background job failed" case is now covered by a backend
test and a front-end test that I ran myself. All eight journeys still pass.

But while checking the evidence I found two problems that nobody had recorded before, both on old
code this iteration did not touch. First, one page request to the backtest data service died with a
server error. Second, right after a user opens the Backtest page for an old date that was never
scanned before, the Data Manager page reports an empty dataset (price history "—", universe 0)
even though the database holds thirty years of prices. Because of these two open items I cannot
sign the goal off yet, and because they cross the backend, the Data Manager screen, and an
anti-goal question, the next round should run at full depth with an auditor.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | reports/qa/goal-ops-hardening-iter-26-evidence/J-01-verify.png (replay PASS) |
| J-03 No per-run range cap | passing | passing | reports/qa/goal-ops-hardening-iter-26-evidence/J-03-verify.png (replay PASS) |
| J-04 Non-blocking boot with visible status | passing | passing | reports/qa/goal-ops-hardening-iter-26-evidence/J-04-verify.png (replay PASS); four `start-backend.sh` boots with host-guard banners in logs/backend.log |
| J-05 Aggregates are precomputed at ingest, never on the fly | passing | passing | reports/qa/goal-ops-hardening-iter-26-evidence/J-05-verify.png (replay PASS) |
| J-06 Pages load only what they need | passing | passing | reports/qa/goal-ops-hardening-iter-26-evidence/J-06-verify.png (replay PASS); reports/perf-budgets.md new dated section, 11/11 readings ≤ 0.1 s |
| J-07 Heavy aggregates never take the service down | passing | passing | reports/qa/goal-ops-hardening-iter-26-evidence/J-07-verify.png (opened: green "Ready", coverage 1996-01-02 → 2026-07-22, universe 540) |
| J-08 Backtest evidence serves from storage only | passing | passing | reports/qa/goal-ops-hardening-iter-26-evidence/J-08-verify.png (opened: /backtest fully populated, "Viewing as-of 2026-07-22 (latest)") |
| J-09 The backend discloses its own background-compute activity | passing | passing | UT-J-09-data-panel-completed-lastoutcome.outerHTML.txt + UT-J-09-health-snapshot.json (panel "completed / as-of 1999-11-02 / 1.6s" == payload `duration_ms 1623`); UT-J-09-01-data-page-top-badge.png |

No journey changed status. All 8 `spec_hash` values match `goal_gate.py hash-journeys` byte-for-byte;
no `journeys-changed.md`, no `browser-infra.json`.

**What I re-derived rather than inherited**

- Ran the new front-end test myself: `npx tsx lib/background-compute-last-outcome.test.ts` → `2 passed`.
- Confirmed the new backend test is not vacuous: `readiness.py:252-255` imports the module and calls
  `forward_testing.get_background_compute_status()` by attribute at call time, so the monkeypatch really
  takes effect.
- Confirmed the perf-budgets change is append-only (`@@ -3797,3 +3797,73 @@`, 70 insertions, 0 deletions)
  and that its measurement window sits inside a real `scripts/start-backend.sh` boot at 18:11:43Z.
- Cross-checked the panel DOM against the same-moment `/api/health` payload (AG-3).
- Queried the database read-only: `scanner_runs` = 1867, `forward_returns` = 3,955,480 — matching the
  served `dataset_version r1867-f3955480` exactly; every run's provider is `seed`.
- Read `logs/backend.log` around the browser lane's own window — that is where both new findings came from.

**What I could NOT verify.** Both services were stopped before this evaluation (a `curl` to
`/api/health` returns nothing), so I could not take my own latency reading; the ≤ 0.1 s result rests on the
recorded readings plus the boot record that corroborates when they were taken. Per the coordinator's
instruction I did not run pytest, so the backend "3 passed, 1:25:51" line rests on the dev handoff and the
reviewer. And nobody photographed the browser at the moment of the server error, so what the user saw is
unknown — that is item 1 of the next round.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven-language only when certified | OK | Diff adds one test file, one pure function + its test, a README sentence and an appended budgets section. No claim/badge/evidence copy touched. |
| AG-2 decision-quality only | OK | No returns, targets, signals or order paths anywhere in the diff. |
| AG-3 displayed numbers correct | **OPEN (minor, unresolved)** | Panel vs `/api/health` matched exactly. BUT UT-J-09-01-data-page-top-badge.png (18:33Z) shows Data Manager reading PRICE HISTORY "— → —" and UNIVERSE 0 while the same frame's top bar reads "591 symbols"; J-07-verify.png (18:25Z) shows the true 1996-01-02 → 2026-07-22 / universe 540. Cause traced by me in the DB: two never-scanned `/backtest` dates created `scanner_runs` 1866/1867 outside any ingest job, bumping the dataset version, while `coverage_snapshot` still holds only the old key, so `/api/data` fell back to `_coverage_not_yet_computed_payload` (data_manager.py:908). |
| AG-4 no overfit edges | OK | No referee, ledger or scoring path touched. |
| AG-5 determinism / no-lookahead | OK | Zero files under `apps/backend/app/**` except one test file; scoring and forward-return windows untouched. |
| AG-6 referee gate | OK | No evidence-derived claim introduced (spec: "New user-facing capability: None"). |
| AG-7 no hard-coded credentials | OK | `iter-26/scan-report.md` = CLEAN (2 untracked files scanned); no config/env file in the diff. |
| AG-8 resilience on the deep basis | **OPEN (minor, unresolved)** | `logs/backend.log:81004` "ERROR: Exception in ASGI application" → `sqlite3.IntegrityError: UNIQUE constraint failed: forward_returns.run_id, forward_returns.symbol, forward_returns.horizon`, frames `api/backtest.py:171` → `forward_testing.backfill_run_forward_returns:1667` → `_insert_run_forward_returns:390`. Two concurrent requests for the same never-scanned deep-history date raced the same INSERT-only write. Scored minor: the service stayed up (every later request in the log answers 200 through a clean shutdown) and no whole-table load occurred; but nobody captured the browser at that moment, so "the UI degrades gracefully" is unverified. First occurrence in the entire logfile. |
| AG-9 offline-deterministic ingest | OK | Read-only DB check: `scanner_runs` 1863-1867 all `provider = 'seed'`; no manifest/dependency change (scan-report CLEAN); captures show the `provider: seed` badge. |
| AG-10 host resource ceiling | OK | `scripts/` and `project-extensions/` do not appear in the diff. All four backend boots this iteration carry the launcher banner `port=8255 memory_cap_mb=6144 malloc_arena_max=2` + `host-guard: cpu_list=0-3,8-11 blas_threads=4`. Per the coordinator note I did not launch pytest. |

Coherence: `iter-26/coherence.md` = **COHERENCE-PASS** (no new value, no new surface, byte-frozen modules
confirmed untouched). Review: **PASS**, browser results present — no fail-open. Scan report: **CLEAN**.

## Next-Step Recommendation

Run one more round at **full** depth. It should not add features. Three things, in order:

1. Find out what a person actually sees when the Backtest page is opened twice at once on an old date
   that was never scanned. Capture the whole page. If it shows a calm error message, record that and
   close the anti-goal question. If it shows a blank error page, that is a real break and must be fixed.
2. Stop the server error itself: two requests for the same old date must not both try to write the same
   forward-return rows. This touches `forward_testing.backfill_run_forward_returns`, which earlier
   iterations froze, so the freeze must be lifted on purpose by the planner, not patched in passing.
3. Make Data Manager honest after a time-machine visit: it currently shows an empty dataset (price
   history "—", universe 0) for a full database until the next data job or restart. Either refresh the
   stored coverage figures when a run is created this way, or label the screen plainly as
   "coverage not yet computed for this dataset version — run a data job", instead of showing zeros.

Smaller items to fold in, not blocking: the browser-QA report says the Backtest requests "returned
immediately" when the log shows 16.7 s, 21.9 s and 23.2 s — correct that sentence; the new
perf-budgets section labels one time as `19:14:25Z` when the readings are `18:14Z` (local time written
as UTC); the background-compute check should be re-run on a date that already has a snapshot so the
"returns immediately" and "in-flight badge" steps get fresh proof; `J-01-verify.png` and
`J-03-verify.png` are one identical image again (sixth time). Owner-optional, unchanged: backlog card
B-1107, and whether the cold historical Backtest load (16-23 seconds today) should get its own written
budget or move to the background.

In one sentence: approve one more full-depth round to check what users see when an old-date Backtest
page fails, fix that failure, and stop Data Manager from reporting an empty dataset after a
time-machine visit.
