# Iteration 63 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

Seven of the eight journeys were re-tested by machine this round and all seven passed, each with its own
fresh picture. The eighth, J-07 "Heavy aggregates never take the service down", stays part-done — and this
round its own measurement got worse, not better. The app answered every one of 983 health checks during an
18-minute background job (no errors at all, all day), but 53 of those answers took longer than the
2-second promise, against 1 slow answer in the same test last round. Nobody has explained why, and the
small speed fix this round is not a plausible cause. The team was honest about it: the developer, the
reviewer and the auditor all wrote plainly that the round's main goal was not met.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | reports/qa/goal-ops-hardening-iter-63-evidence/J-01-verify.png (replay PASS; real jobs `data_provider_runs` id=416/417, read from sqlite) |
| J-03 No per-run range cap | passing | passing | reports/qa/goal-ops-hardening-iter-63-evidence/J-03-verify.png (replay PASS; id=418, 283 dates over a >370-day span) |
| J-04 Non-blocking boot with visible status | passing | passing | reports/qa/goal-ops-hardening-iter-63-evidence/J-04-verify.png (replay PASS) |
| J-05 Aggregates are precomputed at ingest, never on the fly | passing | passing (evidence_makeup) | reports/qa/goal-ops-hardening-iter-63-evidence/J-05-verify.png (replay PASS; real 18m13s backfill id=419 created `scanner_runs` id=2960 for 2010-11-18) |
| J-06 Pages load only what they need | passing | passing | reports/qa/goal-ops-hardening-iter-63-evidence/J-06-verify.png (replay PASS) |
| J-07 Heavy aggregates never take the service down | partial | partial | reports/qa/goal-ops-hardening-iter-63-evidence/UT-J-07-result.png (UI row PASS) + runs/goal-ops-hardening-iter-63/evidence-drill/tc5-health-poll.csv (983/983 HTTP 200; **53 answers over 2.0 s**, max 4.181 s) |
| J-08 Backtest evidence serves from storage only | passing | passing | reports/qa/goal-ops-hardening-iter-63-evidence/J-08-verify.png (replay PASS) |
| J-09 The backend discloses its own background-compute activity | passing | passing | reports/qa/goal-ops-hardening-iter-63-evidence/J-09-verify.png (replay PASS; in-flight warm cross-checked to `forward_aggregate_cache` rows 826/827, asof 2026-07-31, dataset r2960-f6568295) |

No status changed this iteration. No `journeys-changed.md`, no `browser-infra.json`, no `DEFERRED-BUDGET`
row. All eight `spec_hash` values match `goal_gate.py hash-journeys`, which I ran myself. Raw deterministic
replay 7/7 PASS with no overturned rows (last round needed a reconciliation footer for two false failures;
this round needed none). All 11 evidence pictures are byte-distinct (md5 run by me) — last round's
"one photograph cited for two journeys" defect did not recur.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials (AG-7) | OK | `iter-63/scan-report.md` CLEAN over a 5-file diff; no config or env file in the diff list |
| Paid / external SaaS | OK | no manifest, lockfile or dependency file in `iter-diff.md`'s complete file list |
| License changes | OK | no LICENSE or license field in the diff |
| Fabricated / substituted data (AG-9) | OK | I queried the DB: every `data_provider_runs` row since 2026-08-01 is `provider='seed'` (152 rows); the only non-seed rows are id=297 (2026-08-04) and id=369 (2026-08-10), both pre-existing |
| AG-3 displayed numbers correct | OK | `UT-J-07-result.png` renders SNAPSHOT DATES 2960; sqlite `count(distinct asof_date)` in `scanner_runs` = 2960; `coverage_snapshot` dataset_version `r2960-…`. Rendered = persisted = live table |
| AG-5 determinism / no lookahead | OK | the diff is a 3-line scheduling change (`time.sleep(0)` at chunk boundaries) — same query, same WHERE, same order; no date logic touched |
| AG-8 resilience / no unbounded loads | OK | the own-dates scan is still `.yield_per`-streamed; no new whole-table materialization; zero MemoryErrors this iteration (whole-file total unchanged at 8,211, last real one in iteration 58) |
| AG-10 host resource ceiling | OK | `git status --porcelain` is empty for `config.yaml`, `project-extensions/` and `host-guard.env`; `config.yaml:1363-1364` still reads `memory_cap_mb: 8192` / `malloc_arena_max: 2`; `HOST_GUARD_MEMORY_HIGH="12G"`, `HOST_GUARD_BLAS_THREADS=8` unchanged |
| AG-1 / AG-2 / AG-4 / AG-6 proven-language | OK | no evidence claim, score, ranking or proven-language introduced; the diff touches one backend function, one test, one comment and two pipeline scripts |
| Coherence | COHERENCE-PASS | `iter-63/coherence.md`: 0 blocking, 3 advisory notes; no new producer, endpoint or displayed value |

Seven new **minor** ledger entries this round (iter-63/a…g): the unexplained 1 → 53 latency change; the
demo lane starting a real 5-date data job after its own steps failed and narrating an outcome that never
happened; the golden's date being eaten by its own round for the fourth time; the QA write-up saying
"Blockers: None" over a round that missed its main goal; a test docstring that over-claims; a readiness
wait shorter than the situation it guards; and a named error test that was never run. Four iter-62 entries
are closed (a/b/c/d). Ledger now: **189 total, 97 unresolved, 0 unresolved critical.**

## Next-Step Recommendation

Run the next round at **lean** depth and give it this order.

1. **Find out why the app answered slowly 53 times when it answered slowly once last time.** Re-run the
   same 18-minute health-check drill on today's code with nothing changed, and compare. One control run
   tells us whether this is a real slowdown or just a busy machine. Do this before any more speed work.
2. **Make the check script pick its own fresh date.** For the fourth round running, the date written into
   `runs/goal-session-ops-hardening/journey-scripts/J-05.json` was used up by the same round that wrote it.
   The script should choose an unused day when it runs, instead of a person guessing one each time.
3. **Stop the showcase recorder from pressing Start when its own setup steps failed** — this round it began
   a real 5-day data job by accident, then described it as finishing in seconds.
4. **Small and written down:** make the "wait for the app to be ready" step wait 90 seconds instead of 60
   (the situation it protects against lasted longer than 60 seconds); run the memory-failure test the plan
   named and never ran (fourth round); correct the new test's description; record a walkthrough step for
   J-05 "Aggregates are precomputed at ingest" (it rides along, it is never the round's own goal).
5. **Carried, untouched:** iter-29/b and the badge wording after a failed warm-up (36th round unmade);
   iter-31/e; iter-32/f; iter-35/k; iter-36/n; iter-37/o; iter-37/q; iter-39/u; iter-46/az; iter-46/ba;
   iter-47/bd; iter-47/bf; iter-47/bi; iter-48/bj; iter-57/f; iter-57/l; iter-59/g; iter-59/h; iter-59/k;
   iter-62/e; iter-62/f. Deferred a twenty-ninth time: iter-33/g, the Regime Lab.

**Owner — the same one-sentence decision, now for the 15th round, and this round makes it sharper.** The
app must answer its health check within 2 seconds while a background job runs. That promise was written for
a job lasting about 30 seconds; ours last 15 to 20 minutes. This round the app answered every single one of
983 checks and served no errors at all, but 53 answers took longer than 2 seconds (the slowest 4.2
seconds). Please say which you want: keep the 2-second promise for long jobs (J-07 stays open until the app
is faster), or apply it only to short jobs (J-07's last gap closes). Two other things still wait for you:
permission to fix the one-line ordering bug in the test-lane file `scripts/automation/browser-qa-phase.sh`,
and a cost decision — the automatic check now runs a real 15-to-18-minute data job every round.
