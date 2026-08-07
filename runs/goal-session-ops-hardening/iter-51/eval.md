# Iteration 51 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

This round did what it set out to do. The Factor Lab page's data call used to take twelve to fifteen
minutes the first time anyone opened it after a data job; it now answers in eight milliseconds,
because the result is worked out during the data job and saved. I checked the saved result in the
database myself and it is the current one. The app also stayed up and healthy this time: no crash, no
freeze, no restart needed, and no memory failures, through a twenty-four-minute heavy job with two
research pages open. But none of the three journeys this round existed to prove were actually
checked — no lane produced a row for any of them, for the second round in a row — and a fourth
journey was skipped for lack of time, also for the second round in a row. One real defect was found
and measured twice: while a data job runs its heaviest step, the health check occasionally stops
answering for a few seconds.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | `reports/qa/goal-ops-hardening-iter-51-evidence/J-01-verify.png` (opened — immutable snapshot as of 2026-05-29, regime 75.20, badge "Ready", provider seed); UT-J-01 PASS; `data_provider_runs` 321 (`dates_total=19`, `already_snapshotted=19`) + 322 (`dates_total=0`) read by me in sqlite |
| J-03 No per-run range cap | passing | passing | UT-J-03 PASS, `reports/qa/goal-ops-hardening-iter-51-evidence/J-03-verify.png`; `data_provider_runs` 323 = 2025-06-01→2026-07-17, `dates_total=283` over 412 calendar days — far past the retired 370-day cap — read by me in sqlite |
| J-04 Non-blocking boot with visible status | partial | partial (DEFERRED-BUDGET — NOT tested; prior status and `last_verified_iter`=iter-49 carried per SPEED-15) | `reports/phase-goal-ops-hardening-iter-51-ui-test-results.md` "Deferred (iteration budget)" table + "Missing Required Journeys" |
| J-05 Aggregates are precomputed at ingest, never on the fly | partial | partial | `reports/demo/goal-ops-hardening-iter-51/step-02.png` (opened — run 325's job card reads "Refreshed: … **factor lab all** …"); byte-identical to run 325's stored `aggregates_refreshed` (all 8 categories) read by me in sqlite; UT-03 PASS. NO `UT-J-05` row in any lane; steps 2(a)/3 unexercised; step 4 fails |
| J-06 Pages load only what they need | partial | partial | `reports/qa/goal-ops-hardening-iter-51-evidence/UT-02-result.png` (opened — 11 real factor rows, decile grids, no "still computing" card); UT-02 terminal cross-check `GET /api/research/factor-lab?all=true` → **200 in 0.0078 s** vs iter-50's 780.2/874.7/742.07 s; one `__all_factors__` cache row at stamp `r2913-…` = current `max(scanner_runs.id)`, read by me. NO `UT-J-06` row; 11-page sweep never ran; step 2's budgets entry still unwritten |
| J-07 Heavy aggregates never take the service down | failing | **partial** | `reports/qa/goal-ops-hardening-iter-51-evidence/UT-08-factorlab-result.png` (opened — page resolved with real data after the concurrent warm); UT-08 PASS (1,435.87 s drill, zero MemoryError/500); `reports/perf-budgets.md` Addendum 11 (VmPeak 3,652.4 MB vs 8,192 MB cap = 55.4 % margin); `logs/backend.log` — both restarts clean, zero ERROR lines in the lane segment, MemoryError total unchanged at 7,862. Step 2 FAILS (9/653 + 19/892); step 4 unproven (UT-05 SKIPPED) |
| J-08 Backtest evidence serves from storage only | passing | passing | UT-J-08 PASS, `reports/qa/goal-ops-hardening-iter-51-evidence/J-08-verify.png` |
| J-09 The backend discloses its own background-compute activity | passing | passing | `reports/qa/goal-ops-hardening-iter-51-evidence/J-09-verify.png` (opened — top-bar badge "background compute running (1)", 2,912 snapshot dates, one below the DB's current 2,913 as expected for a pre-run-325 capture); UT-J-09 PASS |

Deferred (`DEFERRED-BUDGET`): J-04 — second consecutive round. No `browser-infra.json`; no
`journeys-changed.md`; all 8 `spec_hash`es match `goal_gate hash-journeys` run by me.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 unproven values must render "not yet proven" | OK | Every factor row in `UT-08-factorlab-result.png` and `UT-02-result.png` carries "Not yet proven" chips per horizon; no proven-language introduced. No evidence claims this iteration (goal.md loop mechanics). |
| AG-2 decision-quality only | OK | Zero frontend files in the diff; no order/price-target surface touched. |
| AG-3 displayed numbers must be correct | OK | The one new displayed value cross-checked at the source by me: run 323's stored `aggregates_refreshed` = `['forward_aggregates','research_hot_keys','factor_lab_all','drawdown_expectations']`, byte-identical to the UI text; run 325's 8-category list matches `step-02.png`. UT-06's Factor Combination figures cross-checked byte-identical against the raw API. |
| AG-4 no overfit edges | OK | No referee/ledger path touched. |
| AG-5 determinism / no-lookahead | OK | `_combination_cohort_members` is an allocation-strategy change only (full range is the identity element under `&`), byte-identical against a pinned pre-fix oracle; the auditor independently confirmed the monkeypatch proof is not vacuous. |
| AG-6 evidence claims need a referee verdict | OK | No evidence-derived claims this iteration. |
| AG-7 no hard-coded credentials | OK | `iter-51/scan-report.md` **CLEAN**; diff is 4 files, all under `apps/backend/`, no new config/env file. |
| AG-8 resilience / no unbounded whole-table loads / never exhaust memory | **Minor violation — `iter-51/ce`** | The diff REMOVES an unconditional `set(range(pool_n))`. Zero new MemoryErrors (total unchanged at 7,862, verified by me); VmPeak 3,652.4 MB vs 8,192 MB cap. BUT two live drills recorded connection-level `/api/health` non-answers — 9/653 solo, 19/892 concurrent — which the owner amendment calls a failure. Scored on the journey (J-07 step 2 / J-05 step 4); machine-severity **minor** because there was NO outage, NO wedge and NO restart requirement this round, verified by me in `logs/backend.log`. |
| AG-9 offline-deterministic ingest | OK | Every run created this round (320-325) is `provider='seed'`, read by me in sqlite; job records show `"source": null`; no manifest/lockfile changed. |
| AG-10 host resource ceiling | OK | `git diff` AND `git status` over `config.yaml`, `project-extensions/host-guard/host-guard.env`, `scripts/start-backend.sh`, `scripts/dev.sh`, `scripts/start-frontend.sh` — BOTH empty (run by me). `config.yaml:1363-1364` still reads `memory_cap_mb: 8192` / `malloc_arena_max: 2`; every launch banner prints `memory_cap_mb=8192 malloc_arena_max=2` and `host-guard: cpu_list=0-15 blas_threads=8`. |
| License / paid SaaS | OK | `git diff --stat` over `LICENSE*`, `requirements*.txt`, `package.json`, `pyproject.toml`, lockfiles — empty (run by me). |

Also opened this round: `iter-51/cf` (the DoD line "TC-1 through TC-9 all pass" is false — TC-5
breached, TC-6 failed, TC-3 unrecorded — while the review recorded `definition_of_done: complete` and
QA recorded PASS), `iter-51/cg` (all three target journeys with zero executed rows; J-04 deferred
twice), `iter-51/ch` (capture defect: two byte-identical blank 2,061-byte frames, and `UT-03-result.png`
does not show the line it is cited for), `iter-51/ci` (J-07's `[NEW]` walkthrough, 21st round
unrecorded). Closed: `iter-50/by` (lane-runs-last held — verified by mtime, no product file newer than
the lane) and `iter-50/cb` (demo recovered: 5 real steps, `[NEW]` on J-05/J-06). Ledger: **97 total,
42 unresolved, 0 unresolved critical.** Coherence: **COHERENCE-PASS** — no veto.

## Next-Step Recommendation

Run the eight journey checks first, and change no code while doing it. Three journeys were never
checked this round — "Aggregates are precomputed at ingest" (J-05), "Pages load only what they need"
(J-06) and "Heavy aggregates never take the service down" (J-07) — and a fourth, "Non-blocking boot
with visible status" (J-04), has been skipped for time twice in a row and last checked in round 49.
The change that landed this round should make several of these look better, and nobody has looked. A
checking-only pass cannot break anything.

Then fix the one real defect this round found and measured twice: while a data job runs its longest
step, the health check occasionally stops answering for about five seconds. It happened nine times in
one drill and nineteen in another. It is not caused by the new step specifically — it attaches to
whichever step runs longest — so the fix is about scheduling, not memory: break the long calculations
into pieces so the server can answer between them. Also write the Factor Lab page's measured load
time into the budgets table (it exists only inside a test report today), and retry the one skipped
test — checking that a data job survives running out of memory needed a backend restart with a
special setting, and the permission system refused it twice.

Smaller items already written down: the new step reports "refreshed" whenever the result looks clean
even if saving it silently failed; one of its two honesty branches has no test; the job card reads
"possibly stalled" for the ten minutes the new step runs; and only the default view is pre-computed,
so picking a specific date can still be slow.

The owner has one decision to make: the only other way to stop the health check stalling is to run
the heavy calculation in a separate process, which this round's plan ruled out — please say whether
the next round may do it. (The question from round 50, about two rules that cannot both hold, is
still open too.) In one sentence: approve a checking-only round next, and say yes or no to moving the
heavy calculation into its own process.
