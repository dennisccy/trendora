# Iteration 37 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

This was a strong iteration and the code work is sound. The one code defect it targeted is
closed: a big multi-date data-backfill job now loads the price history into memory **once**
instead of twice, proven by a test that was red before and is green now, plus a
"same-answer-as-before" check that a second test proves is real and not a rubber stamp. All
four of J-07 "Heavy aggregates never take the service down" steps were actually run live for
the first time in three tries, and I re-checked the raw numbers myself: 130 out of 130 health
checks answered OK during a 69-second heavy computation, and the process used only 43% of its
memory limit.

But J-07 still does not fully pass, and the reason is not a code defect — it is that **the
measurements avoided the exact path this iteration changed**. The heavy computation was
started from the Backtest page instead of from the end of a data-import job (which is the path
J-07's own text names), and the memory-pressure drill used a job with zero dates to process,
so the new code never actually ran during either test. An independent audit found this, and
also found and fixed a real defect the code review and QA both missed: the change could have
left 1.1 GB of memory held forever after a rare failure. Nothing worse shipped; the fix is in
the tree with a test that fails if the fix is removed.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | `reports/phase-goal-ops-hardening-iter-37-ui-test-results.md` row UT-J-01 (deterministic replay PASS) · `reports/qa/goal-ops-hardening-iter-37-evidence/J-01-verify.png` |
| J-03 No per-run range cap | passing | passing | row UT-J-03 (replay PASS) · `.../J-03-verify.png` |
| J-04 Non-blocking boot with visible status | passing | passing | row UT-J-04 (replay PASS) · `.../J-04-verify.png` |
| J-05 Aggregates are precomputed at ingest, never on the fly | passing | passing | row UT-J-05 (replay PASS) · `.../J-05-verify.png` |
| J-06 Pages load only what they need | passing | passing | row UT-J-06 (replay PASS) · `.../J-06-verify.png` — **spot-check opened by me**: Regime Lab renders the full "By regime label" table with real forward returns and n counts, badge "Ready", no blank or frozen frame |
| J-07 Heavy aggregates never take the service down | partial | **partial** (3rd consecutive; `last_passing_iter` stays iter-34) | rows UT-J-07a / UT-J-07b · `.../UT-J-07a-backtest-readiness.png`, `.../UT-J-07b-data-runsummary.png` (**both opened by me**) · raw measurements re-derived by me from `runs/goal-ops-hardening-iter-37/j07-warm/health-latency.csv` (130/130 HTTP 200, max gap 1.9996 s, max latency 0.980 s), `.../monitor.csv` (VmPeak flat 2,693,672 kB, 11/11 byte-identical baseline re-reads), `logs/backend.log:140405-140634` (192/192 HTTP 200, zero MemoryError), `runs/goal-ops-hardening-iter-37/mem-drill/final-job-status.json` (`dates_total: 0`) · gap: `capture-defect` (walkthrough recording still absent, 7th iteration) — `evidence_makeup` kept |
| J-08 Backtest evidence serves from storage only | passing | passing | row UT-J-08 (replay PASS) · `.../J-08-verify.png` |
| J-09 The backend discloses its own background-compute activity | passing | passing | row UT-J-09 (replay PASS) · `.../J-09-verify.png` — **spot-check opened by me**: `/data` renders real coverage figures with the truthful idle readiness badge |

**J-07 step-by-step (why `partial` and not `passing`):**

| Step | This-iteration evidence | Verdict |
|------|------------------------|---------|
| 1 — full-horizon warm in one long-lived process, `/api/backtest` served throughout | 5/5 horizons warmed in 69.44 s, PID 3900321 launched via `scripts/start-backend.sh`, 11/11 concurrent baseline re-reads byte-identical, zero errors in the live log window | **substance met, named path NOT used** — the warm was started by `GET /api/backtest?as_of=2026-07-17`, not by "the ingest finalize path" the step names (`perf-budgets.md:4632-4636`, audit B2) |
| 2 — poll `/api/health` 1 Hz; every poll HTTP 200 within its budget | 130/130 HTTP 200, max inter-poll gap 1.9996 s | **HTTP-200 and no-freeze halves met; budget half missed** — 0 of 130 polls inside the committed ≤ 0.1 s budget (max 0.980 s). Carried owner item iter-34/j, 4th measurement round |
| 3 — record VmPeak during step 1, assert under the cap, margin written to `reports/perf-budgets.md` | 2,693,672 of 6,291,456 kB = 42.81% used, 57.19% margin, written into the new "Iteration 37" section | **MET — first time in the session** (two prior evaluators named this as missing) |
| 4 — induce memory pressure; warm aborts honestly, SAME process keeps serving | caught MemoryError at `data_manager.py:3416`, `forward_aggregates` honestly omitted from the refreshed list, health 200 on every later poll, same PID, no restart | **substance met, but on the OLD path** — the drill job had `dates_total: 0`, so the new shared-cache wrapper was an inert no-op; "previously cached reads" was substituted with the job-status record (disclosed) |

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 unproven values must not read as proven | OK | Backend-only diff; no UI change; `/backtest` frame shows the honest "No elapsed forward window for this date yet … No numbers are fabricated to fill the gap" card |
| AG-2 decision-quality only, no orders | OK | No new surface; frames carry "Research-only · decision support · no orders" |
| AG-3 displayed numbers must be correct | OK | `git show HEAD`-pinned byte-identity oracle + its mutation test (auditor re-verified the pinned body and re-ran both); 11/11 live byte-identical re-reads; `/data` frame internally consistent (540 universe of 548 pool / 122 candidates, 591 symbols, 1880 snapshot dates, 3508 gaps) |
| AG-4 no overfit "proven" claims | OK | No evidence claims introduced; no referee-gated language in the diff |
| AG-5 determinism / no lookahead | OK | `compute_forward_aggregates` byte-frozen (coherence.md Data Contract table); the drill's dataset-version discipline correctly refused stale pre-cached values |
| AG-6 referee gate | OK | No evidence-derived claims this iteration |
| AG-7 no hard-coded credentials | OK | `scan-report.md` CLEAN (1 untracked file scanned); diff is 2 files, no config/env file added |
| AG-8 resilience / no memory exhaustion | **3 findings** | **NEW iter-37/o (minor, open)** — the one behavioural change is unmeasured; both drills ran paths where the new code is inert, and the finalize-tail peak may be ~1.13 GB HIGHER than pre-fix. **NEW iter-37/p (minor, RESOLVED in-iteration)** — audit B1: the deferred release could pin ~1.13 GB forever; fixed at `data_manager.py:4327-4341`, mutation-proven. **NEW iter-37/q (minor, open)** — three uncaught HTTP 500s in the 970 MB drill process; the first one precedes any abort, so the handoff's "already at the cap" explanation does not hold for it. **iter-36/l RESOLVED** (double whole-table load closed, `test_kdate_backfill_loads_each_symbol_at_most_once` green at max 1). **iter-29/d STAYS OPEN** — I read the code: `data_manager.py:3098` still prefills, `prices.py:131-152` still selects `daily_prices` with no WHERE clause, so one path still streams the whole table into RAM once per job. No exhaustion at the production cap this iteration (zero MemoryError, 57.19% headroom) |
| AG-9 offline-deterministic ingest | OK | No manifest touched; all compute ran against the committed seed DB and a local throwaway DB; no network provider added |
| AG-10 host resource ceiling | OK, **iter-36/m RESOLVED** | `scripts/start-backend.sh`, `scripts/dev.sh`, `scripts/start-frontend.sh`, `project-extensions/host-guard/` all byte-unchanged (git status empty). Both heavy processes carry the host-guard banner in the LIVE log: `logs/backend.log:140405` (8255, cap 6144 MB) and `:140635` (8256, cap 970 MB). Checked live at evaluation time: PID 2944679 is gone, no uvicorn/next process alive, no listener on 8255/8256/3255 — the leftover 4.1 GB process from iter-36 was reaped and did not recur |

Coherence: **COHERENCE-PASS** (one non-blocking advisory about golden-script text updates). Review: PASS_WITH_NOTES. QA: PASS. Audit: PASS_WITH_GAPS. Closure: CLOSURE-PASS. ux-regression: SKIPPED (budget shed — credited nothing). No `journeys-changed.md`, no `browser-infra.json`, no `DEFERRED-BUDGET` row. All 8 `spec_hash` values match `goal_gate hash-journeys`.

**No critical violation. I considered critical twice** — for iter-37/o (an unmeasured possible +1.13 GB on a memory-critical path) and iter-37/q (uncaught out-of-memory errors on two pages' data paths) — and chose minor both times, on grounds I checked rather than assumed: nothing crashed at the real 6144 MB limit this iteration (a genuine improvement on iter-35, which hit the limit exactly, and iter-36, which came within ~100 KB), the 500s happened only at an artificially tiny 970 MB limit in a throwaway process, the app's own error card ("Backend unavailable … No figures are shown rather than fabricated values") is the user-facing remedy and was proven working last iteration, and the one real regression this iteration created was found and fixed inside the same iteration.

## Next-Step Recommendation

Run the next iteration at **full depth** (this is mandatory because the verdict is ESCALATE).
Keep the same single target — finish J-07 "Heavy aggregates never take the service down" — but
this time measure the path the change actually touched.

1. **Measure the changed path (the whole point).** Re-run the memory-pressure drill on a
   throwaway database with a **real 3-or-more-date backfill** instead of a zero-date one, so
   the new shared price cache is genuinely active, and sample peak memory across the whole
   end-of-import warm. Compare it against a run forced onto the old behaviour. This answers
   the one open question — does holding the price data in memory across the whole warm raise
   the peak? It is cheap and safe on a small throwaway database; it does not need the big
   4.97 GB live database, and it must still be started only through `scripts/start-backend.sh`.
2. **Run J-07 step 1 the way its own text says** — start the heavy warm from the end of a real
   data-import job, not from the Backtest page, with the once-per-second health check running
   during it.
3. **Then the next code item, already queued twice:** the Regime Lab "All history" view still
   does its slow first computation inside the web request instead of in the background, and one
   of its requests answers with the text "Internal Server Error". This iteration added fresh
   evidence of the same shape (finding iter-37/q).
4. **Small, already written down:** a test for the new failure branch in the backfill code
   (reviewer MINOR); strengthen the end-to-end test so it proves each warm category still
   succeeds when the shared cache is attached (audit T2); the stale comment at
   `data_manager.py:650-654`; "591 symbols" → 548 at `perf-budgets.md:4466`; the unmeasured
   cost of re-reading the symbol pool once per batch and date (audit B6).
5. **Capture only, never an iteration's goal:** J-07's walkthrough recording is still missing
   for the 7th iteration in a row (`demo.json` says `not_yet` with zero steps and
   `reports/demo/goal-ops-hardening-iter-37/` is empty). Also worth a note: the two golden
   replay scripts for J-01 and J-03 produce byte-identical screenshots again, and the rewritten
   J-07 script now checks numbers that change as the database grows.
6. **Owner decisions, both still waiting, and both should be settled before any
   goal-achieved run:** (a) the ≤ 0.1 second health-check budget — missed for the fourth time,
   and this time in exactly the situation the journey describes (0 of 130 checks inside it,
   slowest 0.98 s); the three choices are unchanged: accept the current honest-warning
   behaviour as meeting the journey, rewrite the budget for the short heavy-computation window,
   or ask for the code fix that serves readiness from a saved snapshot. (b) whether
   `start-frontend.sh` should join the host-protection marker list — with new input this
   iteration: `scripts/dev.sh`'s stop signal left the frontend process running and holding its
   port until it was killed directly.

One sentence for the owner: approve one more full-depth round that re-runs the memory drill
with real work in it (so the change this iteration made is finally measured), and please pick
one of the three options for the 0.1-second health-check budget — that budget is now the only
thing in J-07 that no agent can settle.
