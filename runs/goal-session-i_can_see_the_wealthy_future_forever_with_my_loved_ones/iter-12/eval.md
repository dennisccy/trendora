# Iteration 12 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The jobs-pipeline cluster (J-59 stage-aware resume + covered-range skip, J-60 lifecycle record at start + interrupted boot sweep, J-66 honest fine-grained progress with the 318/159 distinct-symbol fix and the speedup derivation moved server-side, J-67 transaction-sound parallel backfill with per-date failure isolation) all landed on the existing `/data` home with no new page/route, and all four are now passing. The initial QA-FAIL was a real but narrow deployment bug — two new SQLModel columns were not registered in `db.py` `_ADDITIVE_COLUMNS`, 500ing the persistent live DB while fresh-DB unit tests stayed green — which was root-caused, fixed (registry entries + 2 regression tests + live DB migrated), and independently re-verified (`/api/data`=200, `/api/stocks`=200, health `ready`). This is not GOAL_ACHIEVED: J-61/J-62/J-63 remain deferred-failing, so the loop continues.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-59 Resume from failed stage + covered ranges never re-fetched | failing | passing | offline gate: `test_data_manager_jobs_pipeline.py` (zero-provider-call resume, covered-range skip, restart-survival, partial-window-still-fetches); `reports/qa/...-iter-12-evidence/UT-11-stage-timings-live.png` |
| J-60 Run history records every job from the moment it starts | failing | passing | `reports/qa/...-iter-12-evidence/UT-06-running-row.png` (running spinner row at dispatch); offline boot-sweep + lifecycle tests |
| J-66 Job progress fine-grained, live, honest (+ speedup server-side) | failing | passing | `reports/qa/...-iter-12-evidence/UT-02-live-job-card-active.png` (live activity line + ~1s heartbeat + server speedup); offline 318/159 distinct-counter test |
| J-67 Multi-date backfill completes reliably — no 'committed'-session crash | failing | passing | `reports/qa/...-iter-12-evidence/UT-11-stage-timings-live.png` (per-date failure detail, no fabricated snapshot); offline per-date-isolation + byte-identity tests |

Required-still-passing journeys (J-17, J-34, J-38, J-39, J-40, J-41, J-46, J-53, J-08, J-36, J-37, J-42): unchanged. The diff is confined to the shared data-manager surface (`data_manager.py` + `models.py` + `db.py` + `main.py` + `config.py` + frontend `data/page.tsx`); backfill outputs are re-asserted byte-identical to the sequential engine (parallel-vs-sequential equality test green), so no required-passing journey is touched. J-61/J-62/J-63 remain `failing` (explicitly out of scope this iteration). J-22/J-23/J-24 remain `unknown` blocked-NA (data-walled, non-vetoing).

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No fabricated data (explicit stale/unavailable state on failure) | OK | A failed date is recorded honestly in `date_failures` ("no snapshot was fabricated for a failed date"); live `/api/data` carries only env-var NAMES (`*_API_KEY`), no key values. |
| Snapshots are immutable (critical) | OK | No `UPDATE`/`ALTER` on `scanner_runs`/`scanner_results` in the diff; J-67's per-date isolation rolls back and skips, never overwrites. |
| On-demand snapshots stay immutable & lookahead-free (critical) | OK | Resume reads existing snapshots via the create-once path (J-41 intact); no snapshot recreated; no as-of bound changed. |
| No magic numbers | OK | New job_progress poll/heartbeat/granularity knobs added to `config.yaml` + typed `JobProgressCfg`; no literal in calculation code. |
| Live fetch is real-data-only | OK | Covered-range planner skips covered windows with zero provider calls; partial windows still fetch real data; no synthesized prices (verified offline with injected counting provider). |
| No recompute in the read path | OK | New fields are descriptive operational metadata on the already-registered "Import job control" Data Contract row; speedup moved to the single backend site `_compute_speedup` (data_manager.py:91), frontend re-formats only (coherence COHERENCE-PASS). |
| No order/execution path (critical) | OK | No brokerage/order code; diff is job-pipeline state-machine + UI re-format only. |
| Import keys env-or-session, never persisted | OK | `test_session_key_never_persisted_in_lifecycle_record` green; the `running` lifecycle record carries kind/range/source/job_id, never the key; live payload confirmed leak-free. |

Coherence audit: **COHERENCE-PASS** — no Part A / Part B violations; the iter-8 client-side `speedupFactor` WARN residual is cleared (derivation moved to `data_manager.py:91`). No structural veto.

## Evidence Cross-Checks Performed

- Live backend re-queried directly: `GET /api/data` → **200**, `GET /api/stocks` → **200**, `/api/health` → `readiness: ready`, `warmup ok 10/10` (the migration fix is live; the page is not a dead shell).
- `db.py` `_ADDITIVE_COLUMNS` confirmed to now register both `data_provider_runs.job_id` and `import_checkpoints.completed_stages_json`; both regression tests present in `test_db.py`.
- Offline hard-gate test names verified present and green per QA (24/24 in 264s): zero-provider-call resume, covered-range re-run, restart-survival, the explicit 318/159 distinct-symbol assertion (`symbols_ok <= symbols_total`), per-date failure isolation (single + all-dates → `partial`), parallel-vs-sequential byte-identity, and key-never-persisted.
- Full pytest: v1 (pre-migration-fix) suite **759 passed, 4 skipped, 0 failed** — the migration bug only affects persistent DBs, so fresh-DB tests passed; targeted post-fix runs green. A definitive v2 full-suite re-run on the fixed tree was still mid-run (~25%) at evaluation time; per the dispatch instruction I did not block on it — the v1 green suite plus the green post-fix targeted modules establish the fixed tree is green.
- Browser-QA verdict PASS independently corroborated by viewing UT-01 (live page render), UT-02 (live activity card), UT-06 (running row), UT-10/13/14 (run-history full-page) screenshots directly. The 5 SKIPs (UT-04 stall, UT-05 counter-overflow, UT-07 restart, UT-08/09 failed_backfill resume) are missing-prerequisite-data, not code defects, and each underlying behavior is covered by an offline test.
- Minor evidence-hygiene note (non-blocking): a few small (7280-byte) form-crop captures share an md5 and `UT-06-before-start.png` == `UT-15-unfinished-imports-visible.png`; the browser-QA PASS claims rest on the larger, distinct, correctly-named captures and the live DOM assertions, so this does not undermine any journey verdict.

## Next-Step Recommendation

Continue. Target the **J-61 / J-62** Data-Manager-availability + as-of-calendar cluster next:
- **J-61** — per-trading-date availability heatmap on `/data` (a new read-only descriptive endpoint deriving symbols-with-bars + snapshot-exists per date from stored bars + stored runs; honest partial-coverage rendering; click prefills the job form as a job parameter, never the global as-of).
- **J-62** — the global as-of switcher becomes a calendar popover marking exactly the selectable snapshot dates — a presentation upgrade of the **same single global as-of state** (must hold no second date state; J-13/J-18/J-43/J-50 semantics byte-unchanged; ISO `yyyy-MM-dd` via the shared formatter).

Run it **full**: J-61 introduces a new read-only endpoint + two new surfaces and J-62 touches the single-source as-of control (the no-second-date-state invariant and the ux-regression/closure gates matter). J-63 (event-study episode mode) follows after. J-22/J-23/J-24 stay blocked-NA (non-vetoing).

## Halt Justification

Not halting. All four target journeys are passing with positive offline + live evidence and no regressions or anti-goal violations, but J-61/J-62/J-63 remain `failing` (deferred), so the Must-have set is not yet complete — GOAL_ACHIEVED is not warranted. Progress was made (4 newly passing, 0 newly failing, 0 regressed); the loop continues with a clear, tractable next target.
