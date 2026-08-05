# Iteration 49 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

This round did the job it was given and then the app crashed for a different reason. The thing it
set out to fix is fixed: adding one old day of history now finishes inside its twenty-minute promise
on three separate live runs, and I checked those three runs myself from the raw measurement files
rather than trusting the report. But while the checks were running, the whole backend died for
twelve minutes and forty-five seconds. It died because someone opened the Factor Lab research page
while a data job was still working — three heavy jobs were running at once and the machine ran out
of memory. That is exactly what the journey "Heavy aggregates never take the service down" (J-07)
promises will never happen, so that journey drops to failing. Two journeys stay green on real work
this round's own checks caused, two more stay green on live checks I ran myself, and the round is
escalated so the next one runs at full depth.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | `reports/qa/goal-ops-hardening-iter-49-evidence/J-01-verify.png` (renders the stored 2026-05-29 snapshot) + UT-J-01 PASS row in `reports/phase-goal-ops-hardening-iter-49-ui-test-results.md`; backed by `data_provider_runs` ids 309/310 which the replay itself created at 04:40:49–04:41:07Z with exactly the asserted counts (28 calendar / 19 already snapshotted / 9 non-trading; 2 calendar / 2 non-trading) — read by me in sqlite |
| J-03 No per-run range cap | passing | passing | `reports/qa/goal-ops-hardening-iter-49-evidence/J-03-verify.png` + UT-J-03 PASS row; backed by `data_provider_runs` id 311 created 04:41:11Z — 2025-06-01→2026-07-17, 412 calendar days, 283/283 dates, `status=ok`, no cap rejection |
| J-04 Non-blocking boot with visible status | partial | partial | Two REAL executed integration rows re-run at 13:07–13:17 (after the newest product-code mtime): `apps/backend/tests/test_start_backend_script.py::test_j04_boot_serves_first_health_200_within_5s_on_warm_db` (1.29–1.50 s against a 5 s budget, honest pre-ready payload) and `::test_j04_crash_with_midflight_job_restarts_to_interrupted_row_with_last_progress`. Live crashed-state UI captured in `reports/qa/goal-ops-hardening-iter-49-evidence/UT-05-fail.png` (badge "Backend unavailable" + NO-GO banner = J-04 step 4). Browser row UT-J-04 = SKIP (that lane may not restart services). Step 3's badge-in-the-same-window assertion still unproven |
| J-05 Aggregates are precomputed at ingest, never on the fly | failing | partial | UT-02 **FAIL** (`UT-02-fail.png`, `UT-02-stuck-running-precrash.png`), UT-03 SKIP. Offsetting evidence I recomputed myself: `perf-budgets-iter49-run{1,2,3}.csv` sampler spans 1,019.6 / 1,052.5 / 1,049.2 s against the 1,200 s bound, peak VmPeak 4,577,812 / 4,243,444 / 4,281,968 kB (45.4–49.4 % margin under the 8,388,608 kB cap); and in-app job `d5637f7c` (run 312) ran a bounded tail — `forward_aggregates_warm elapsed=168.15s` with per-horizon lines 25.12/33.64/47.09/32.17/30.11 s, read by me in `logs/backend.log` at 10:24:52 |
| J-06 Pages load only what they need | partial | partial | UT-J-06 PASS row + `UT-J-06-result.png` (11 routes loaded, no error cards). Against it: UT-07 **FAIL** — `/research/factor-lab` never rendered its table and its own read raised the uncaught MemoryError at `research.py:1051`; no fresh page-load budget numbers were recorded in `reports/perf-budgets.md` this round (step 2 unmet) |
| J-07 Heavy aggregates never take the service down | partial | **failing** | UT-05 **FAIL** + `UT-05-fail.png`. Verified by me in `logs/backend.log`: line 191721 `OpenBLAS error: Memory allocation still failed after 10 retries, giving up.`, log stops, restart banner at 09:48:49Z → outage 09:36:05Z–09:48:49Z = **12 m 45 s**; run 312 reaped to `interrupted` at 09:48:50. Health ceiling: 6 / 8 / 9 polls over 2 s in 3 of 3 runs, one never-answering poll in runs 2 and 3 (`perf-budgets-iter49-run{1,2,3}-health.csv`, recomputed by me) |
| J-08 Backtest evidence serves from storage only | passing | passing | `reports/qa/goal-ops-hardening-iter-49-evidence/J-08-verify.png` + UT-09 PASS row. My own live probe on the shipped build: `GET /api/backtest` 200 in 0.106 s, 274 KB, `evidence_status: "ready"`, `n_runs: 2886`, `evidence_generated_at 2026-08-05T09:24:52Z` (i.e. produced at ingest). `resolved_forward_aggregate_evidence` has **0** mentions in this iteration's diff. `evidence_makeup: true` (UT-09's file is the blank frame) |
| J-09 The backend discloses its own background-compute activity | passing | passing | `reports/qa/goal-ops-hardening-iter-49-evidence/J-09-verify.png`. My own live probe: `GET /api/health` 200 in 0.091 s carrying `background_compute: {"active": [], "recent_outcomes": []}` — present and honestly idle. `get_background_compute_status` and `_HIST_DISPATCH_INFLIGHT` have **0** mentions in this iteration's diff (A.6 durability). UT-J-09 = SKIP (backend was down). `evidence_makeup: true` |

Deferred (`DEFERRED-BUDGET`): none. No `browser-infra.json`; no `journeys-changed.md`. All 8
`spec_hash` values match `goal_gate.py hash-journeys docs/goal.md` run by me — no goal-edit drift.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials (AG-7) | OK | `iter-49/scan-report.md` CLEAN; the whole diff is 7 files (3 engine + 4 test) — no config/env file touched |
| Paid / external SaaS (AG-9) | OK | No manifest changed (`git diff` vs `df69693c` lists no `pyproject.toml`/`requirements*`); every `data_provider_runs` row created this round (309, 310, 311, 312) is `provider='seed'` — checked by me in sqlite |
| License changes | OK | No LICENSE or license-field file in the diff |
| Fabricated / substituted data (AG-3) | OK | Byte-identity proven by pinned-reference tests and re-checked by the coherence auditor and the reviewer; my live probe returned real, varied aggregates (`n_runs 2886`). One near-miss was caught and closed in-audit: J-05's golden still targeted a date this round's own lane had consumed — a re-run would have PASSed on work it did not do. Rotated to 2012-01-04; I confirmed in the DB that 2012-01-04 has 0 snapshot rows and 480 symbols with bars (ledger `iter-49/bw`, resolved) |
| AG-8 — never crash a page or exhaust the service's memory | **VIOLATED — carried, NOT introduced by this diff** | The process died for 12 m 45 s (see J-07 above). The crashing frame, `research.py:1051` `compute_factor_lab_all`, is **untouched** by this iteration — and this diff REMOVED an unbounded full-entity read rather than adding one. Ledgered `iter-49/bp`, severity `minor` in the machine field for that reason only, with the defect scored where it belongs: J-07 = failing. Recorded as an interpretation call in `assumptions.md` |
| AG-10 — host resource ceiling | OK | `git diff` vs the snapshot over `config.yaml`, `scripts/start-backend.sh`, `scripts/dev.sh`, `project-extensions/host-guard/host-guard.env` is **EMPTY** (run by me); `config.yaml:1363-1364` still reads `memory_cap_mb: 8192` / `malloc_arena_max: 2`; every launch banner in `logs/backend.log` reads `memory_cap_mb=8192 malloc_arena_max=2`, `host-guard: cpu_list=0-15 blas_threads=8` |
| AG-1 / AG-2 / AG-4 / AG-5 / AG-6 (proven-language, no-lookahead, referee) | OK | Backend-only iteration, zero frontend files changed, no new displayed value; the coherence auditor confirms no new claim surface and no second producer |

Ledger after this round: **85 total, 35 unresolved, 0 unresolved critical.** New this round:
`iter-49/bp` (the 12 m 45 s outage), `bq` (health ceiling breached 3/3 runs), `br` (TC-7 breached a
4th consecutive round), `bs` (four PASS rows citing one blank screenshot; UT-01's file is a stale
copy of iter-48's), `bt` (the QA report contradicts its own cited artifacts), `bu` (the browser
report mis-attributed the first abort), `bv` (demo captured zero steps again), `bw` (the golden-date
near-miss, resolved in-audit). `iter-48/bj` amended, not closed.

Lane verdicts: scan **CLEAN**; coherence **COHERENCE-PASS**; review **PASS_WITH_NOTES**;
QA **PASS** (contradicts its own cited artifacts — see `iter-49/bt`); audit **FAIL**;
browser QA **FAIL** (6/15); deterministic replay **BLOCKED** (0/5); demo **NOT_YET** (0 steps).

## Next-Step Recommendation

Full depth (required by this ESCALATE verdict). Do these in order.

1. **Stop one research page from killing the whole app.** Opening the Factor Lab page while a data
   job is finishing brought the backend down for nearly thirteen minutes. Two things must change
   together, as one job: put a limit on what that page loads into memory, and stop the start-up
   warm-up from running the same heavy calculation at the same time as the data job. Five separate
   reviews have now agreed this is the next thing to do.
2. **Then run the eight journey checks, last, and let nothing touch the code afterwards.** Three
   journeys — "Non-blocking boot with visible status" (J-04), "Backtest evidence serves from
   storage only" (J-08) and "The backend discloses its own background-compute activity" (J-09) —
   produced no real check this round because the app was down. The J-05 check now points at
   2012-01-04, which I confirmed has no snapshot yet.
3. **Finish proving "aggregates are precomputed at ingest" (J-05) inside the app.** The timing
   promise is now met three times out of three, but only on an idle machine and never through the
   app's own pages. After item 1 makes the app survive normal use, run the job from the Data page
   and check the new day appears on Scanner Runs.
4. **Make the health check keep its two-second promise.** It was slower than two seconds six, eight
   and nine times in the three runs, and twice per run it did not answer at all. One of the three
   slow spots is a twenty-four-second step this round itself added.
5. Small and already written down: `_combination_observations` is now the slowest single
   calculation (about 250 seconds); the per-claim timing label can collide for two claims on the
   same factor and horizon; the timing pre-calculation runs even when there is nothing to compute.
6. Carried, untouched: iter-29/b and the badge wording after a permanently failed warm-up (22nd
   round unmade); iter-31/e; iter-32/f; iter-35/k; iter-36/n; iter-37/o; iter-37/q; iter-39/u;
   iter-46/az; iter-46/ba; iter-47/bd; iter-47/bf; iter-47/bi; iter-48/bj (amended, still open).
7. Capture only, never a round's goal: the walkthrough recording captured zero steps for the second
   round running, and five test pictures this round are blank or copied from an earlier round —
   both should be retaken as a passenger task.
8. **For the owner — nothing needs your decision, but three facts belong in front of you.** The
   twenty-minute promise for adding one old day of history is now genuinely met, three runs out of
   three, which is what this round was for. The app nevertheless went down for nearly thirteen
   minutes because a research page and a background job ran out of memory together — the same shape
   of failure as the one that stopped this session in July, and the repair is already fully written
   down and does not need you. And the round's quality report says "pass" while the round's own
   browser check says "fail"; the auditor caught that, and the next round must regenerate it.
