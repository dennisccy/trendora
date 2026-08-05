# Iteration 48 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

Two journeys moved up: "Backfill honors the requested range and explains zero-work" (J-01) and
"No per-run range cap" (J-03) now pass, and for the first time in this session I could match each
replayed click to a real job row in the database, so these are genuine end-to-end checks rather
than page-text checks. The round's own main job is not done: "Aggregates are precomputed at
ingest" (J-05) failed for the fifth round in a row. The slow step this round fixed is genuinely
fixed — one real historical backfill finished in 13 minutes 52 seconds with a complete outcome
record — but a different, older step in the same clean-up tail took 22 minutes on its own, so the
job the browser lane ran never finished at all. Nothing broke: no journey went from passing to
failing, the app never went dark (454 health checks answered, none failed), and the code scan is
clean.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | partial | **passing** | `reports/phase-goal-ops-hardening-iter-48-ui-test-results.md` UT-J-01 PASS + `reports/qa/goal-ops-hardening-iter-48-evidence/J-01-verify.png`; corroborated by me in `apps/backend/data/trendora.db`: `data_provider_runs` id=305 (19/19 dates, 28 calendar · 19 already snapshotted · 9 non-trading, `ok`, 0.25 s) and id=306 (weekend, 0/0 dates, 2 calendar · 2 non-trading, `ok`, 0.20 s), both created at the replay's own timestamps |
| J-03 No per-run range cap | partial | **passing** | UT-J-03 PASS + `.../J-03-verify.png` (live job card "backfill job · 2025-06-01 → 2026-07-17"); `data_provider_runs` id=307: 283/283 dates over 412 calendar days, `ok`, 0.24 s — the whole span completed, which is the step that failed at iter-46 |
| J-04 Non-blocking boot with visible status | partial | partial (**not tested — DEFERRED-BUDGET**) | `.../ui-test-results.md` "Deferred (iteration budget)" table, UT-J-04 `DEFERRED-BUDGET`; prior status and prior `last_verified_iter` (iter-46) carried unchanged |
| J-05 Aggregates are precomputed at ingest | failing | **failing (5th consecutive)** | UT-02 FAIL row + `.../UT-02-fail.png`; `data_provider_runs` id=308 (2012-06-15) read by me: `aggregates_refreshed` null, `stages` {}, non-terminal from 22:50:27Z until the 01:33:04Z restart stamped it `interrupted` — 2 h 43 m against a 20-minute bound |
| J-06 Pages load only what they need | partial | partial | UT-J-06 PASS + `.../J-06-verify.png`; BUT `logs/backend.log:183953` and `:184049` are two new `MemoryError`s on `/research/regime-lab` (`research.py:3640`/`:3630`, entered from `api/research.py:421`) inside that same replay window, and UT-07 records the Factor Lab's first read unfinished after 26+ minutes |
| J-07 Heavy aggregates never take the service down | partial | partial | UT-05 PASS (readiness `ready` and health 200 through a 31+ min heavy job) + UT-06 PASS (`.../UT-06-result.png`, drawdown-expectations table populated, no error); `samples.py` `total`/`regime` bound with 5/5 pressure runs; no UT-J-07 row in any lane (target journey, zero rows) |
| J-08 Backtest evidence serves from storage only | passing | passing (spot-checked) | UT-J-08 PASS + `.../J-08-verify.png`; its producer `apps/backend/app/engine/forward_testing.py` is untouched by this diff (`git diff --stat` against the snapshot lists only `data_manager.py`, `research.py`, `samples.py` + tests + `perf-budgets.md`) |
| J-09 The backend discloses its own background-compute activity | passing | passing (spot-checked) | UT-J-09 PASS + `.../J-09-verify.png`; `get_background_compute_status` (`forward_testing.py:1700`) unchanged this iteration |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven/confident language backed by the ledger | OK | Zero frontend files changed (coherence audit + ui-surface-map both confirm), no claim wording touched anywhere in the diff |
| AG-2 decision-quality only | OK | No new user-facing copy, no order/price-target surface; diff is three backend engine modules plus tests |
| AG-3 displayed numbers are correct | OK | The reuse path's byte-identity was mutation-proven inside the audit: with a deliberate mis-keying injected at `data_manager.py:580-583` the NEW test fails and the OLD one passes (audit T1), so the proof is no longer vacuous. `research._factor_regime_observations` carries a pinned-reference equality test (`test_research_streaming.py`, +105 lines) |
| AG-4 no overfit edges | OK | No referee/ledger/claim path touched |
| AG-5 determinism and no-lookahead | OK | The new regime filter reads the stored `regime` field inside the same chunked join; no date-window logic changed. `entries`/`exits` still recomputed fresh in full date order (verified in the `data_manager.py` diff and by the reviewer) |
| AG-6 evidence claims need a referee verdict | OK (n/a) | No evidence-derived claim introduced |
| AG-7 no hard-coded credentials | OK | `scan-report.md`: CLEAN — no secret, dependency, or license findings on added lines |
| AG-8 memory / unbounded loads | **MINOR, open (recurrence)** | This iteration CLOSED the last two of the three sites named at iter-46 (`samples.py` `total`/`regime`), and iter-46/au is now marked resolved. But `logs/backend.log` went 7,077 → 7,079 `MemoryError`s: two new ones on `/research/regime-lab` (`research.py:3630`/`:3640`), a pre-existing site this iteration's spec explicitly deferred (15th deferral). Filed iter-48/bk. Not introduced here; the process kept serving throughout |
| AG-9 offline-deterministic ingest | OK | Every `data_provider_runs` row created this iteration (ids 298-308) reads `provider='seed'`. The one `yahoo` row, id=297, predates this iteration (it is the iter-47 item bh) |
| AG-10 host resource ceiling | OK | `git diff` against the snapshot over `config.yaml`, `scripts/`, `project-extensions/` is EMPTY. Every launch banner in the log reads `port=8255 memory_cap_mb=8192 malloc_arena_max=2` with `host-guard: cpu_list=0-15 blas_threads=8` |
| Paid/external SaaS · license | OK | No manifest and no LICENSE file in the diff; `scan-report.md` CLEAN |
| Fabricated/substituted data | OK | No fixture appears on a production path; the two changed read paths are proven byte-identical to their pre-fix versions |

**Coherence:** `COHERENCE-PASS` — one already-registered Data Contract row touched, no new
producer, table, endpoint, page or nav entry; zero blocking violations and zero advisories.

**Ledger after this iteration:** 77 total, 28 unresolved, **0 unresolved critical**. One carried
item closed (iter-46/au). Five new open (bj, bk, bl, bm, bn) and one new resolved-in-audit (bo).

## Next-Step Recommendation

Full depth again, and this order.

1. **Make the historical backfill actually finish.** This is the fifth round J-05 has failed and it
   is now the only remaining product fault on a must-have journey. The step this round fixed is
   fixed — one real backfill finished in under 14 minutes with a complete outcome record. What is
   left is the older clean-up work that runs after every data job: measured at 102 seconds, 153
   seconds, and 1,334 seconds on three runs of the same thing. The longest one alone is over the
   whole 20-minute promise. Put a bound on that step first (the auditor names it as the largest
   measured cost), then on the last step, which never even reported on the failing run.
2. **Run J-05's own check afterwards.** Its script was repaired this round and pointed at
   2012-01-05, which I confirmed has no snapshot yet, but nobody ever ran it. J-05 has had no
   picture of its own for four rounds.
3. **Re-run the check for "Non-blocking boot with visible status" (J-04).** It was dropped this
   round for lack of time, so its status is carried over untested.
4. **Stop the Regime Lab page from eating the whole machine.** It hit the 8 GB ceiling twice more
   this round, during the very replay that scored "Pages load only what they need" (J-06) as a
   pass. Until that page is bounded, J-06 cannot honestly move up. This is the fifteenth round this
   item has been put off.
5. Small and already written down: the Factor Lab's first read did not finish in 26 minutes; the
   `total`/`regime` bound needs a live page measurement to go with its test-bench one; the shared
   "warm in progress" flag; the health check's 2-second promise; the background worker that does
   not appear on the page listing background work.
6. Carried, untouched: iter-29/b plus the badge wording after a permanently failed warm-up (21st
   round), iter-31/e, iter-32/f, iter-35/k, iter-36/n, iter-37/o, iter-37/q, iter-39/u, iter-46/az,
   iter-46/ba, iter-47/bd, iter-47/bf, iter-47/bi.
7. Capture only, never a round's goal: this round's demo recorded zero steps, so J-07's walkthrough
   is 18 rounds unrecorded and J-05's acceptance frames are still missing; UT-05's picture was a
   copy of an earlier one and should be retaken.
8. For the owner: nothing needs your decision. Three facts are worth knowing — two more journeys
   now pass on real, checkable job records; the app stayed up and answered every one of 454 health
   checks with no memory failures on its own work; and adding one old day of history still does not
   finish, because of slow clean-up steps that pre-date this round's fix.

The next round should bound those two slow clean-up steps and then re-run all eight journey checks.
