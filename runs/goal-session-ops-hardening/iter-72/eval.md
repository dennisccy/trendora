# Iteration 72 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

The app stayed up. Last round, while a long data job ran, 58 of 900 health checks got no answer at
all, including one silent stretch of 165 seconds. This round the same kind of job ran on the correct
launcher and **all 1,315 health checks were answered, none took longer than 1.7 seconds, and not a
single second went unanswered** — including the whole ten-minute stage that caused every problem
before. I recounted every one of those numbers myself from the raw file, the database and the
server's own log, and I also confirmed the check was armed 58 seconds before the job started. J-05
"Aggregates are precomputed at ingest" is back to passing, and J-07 "Heavy aggregates never take the
service down" is much better but not fully checked: this round also made the app allowed to hold
more than twice as many database connections at once, and nobody measured what that does to memory.
That one unchecked thing is why J-07 is "partly passing" and not "passing", and it is the next
round's first job.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | `reports/qa/goal-ops-hardening-iter-72-evidence/UT-J-01-result.png` + merged row UT-J-01; DB corroboration `data_provider_runs` 471/472/473 (seed/ok, 22:30:53.588 / 22:31:20.255 / 22:31:38.516 UTC) |
| J-03 No per-run range cap | passing | passing | replay PASS + `reports/qa/goal-ops-hardening-iter-72-evidence/J-03-verify.png` (opened by me — shows /data, not the acceptance state; weakest row of the round) |
| J-04 Non-blocking boot with visible status | passing | passing | replay PASS + `reports/qa/goal-ops-hardening-iter-72-evidence/J-04-verify.png` (opened: badge "Ready", provider seed, SNAPSHOT DATES 2975); step 5 improved — three `dev.sh: launching at …` headers in `logs/backend.log` at 21:45:04Z/21:45:28Z/21:45:56Z |
| J-05 Aggregates are precomputed at ingest, never on the fly | partial | **passing** | `reports/qa/goal-ops-hardening-iter-72-evidence/UT-J-05-result.png` (opened: "Immutable snapshot — as of 2008-01-03 … Scanned 2026-08-12 22:36:24"); DB `scanner_runs` id 2977 created_at 22:36:24.084611, `data_provider_runs` 474 seed/ok; step 4 from `runs/goal-session-ops-hardening/iter-72/j07-browser-qa-health-poll.csv` |
| J-06 Pages load only what they need | passing | passing | `reports/qa/goal-ops-hardening-iter-72-evidence/UT-J-06-result.png` + merged row (11 pages, real headings); replay FAIL at step 02 overturned by live re-check |
| J-07 Heavy aggregates never take the service down | failing | **partial** | `runs/goal-session-ops-hardening/iter-72/j07-browser-qa-health-poll.csv` (1,315 polls, all 200, max 1.652 s, zero gaps > 2 s — recomputed by me); `logs/backend.log` drill window 1,605 access lines all 200, factor_lab_all_warm 598.44 s; frame `…/UT-J-07-result.png` does not depict the acceptance state |
| J-08 Backtest evidence serves from storage only | passing | passing | `reports/qa/goal-ops-hardening-iter-72-evidence/UT-J-08-result.png` (opened: "Viewing as-of 2026-07-31 (historical)"); two live mid-warm "Refreshing" transitions (2915→2916, 2972→2975) |
| J-09 The backend discloses its own background-compute activity | passing | passing | `reports/qa/goal-ops-hardening-iter-72-evidence/UT-J-09-result.png` (opened: /data top crop — does not depict the panel); window 22:37:00–22:41:46 UTC inside job 474; dataset `r2977` matches DB `scanner_runs` id 2977 |

Deterministic replay lane: **2/8 PASS**; J-01, J-05, J-06, J-07, J-08, J-09 FAILed and were overturned
in the merged file (which is authoritative). I checked the overturns rather than inheriting them —
see the Anti-goal table row for iter-72/c and the Next-Step section.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven-language only from the ledger | OK | Backend/launcher-only diff; no scoring, ranking or claim surface touched. `iter-diff.md` file list: `config.yaml`, `config.py`, `readiness.py`, `health.py`, `data.py`, `data_manager.py`, `scripts/dev.sh`, tests, `perf-budgets.md`. |
| AG-2 decision-quality only | OK | No order, price-target or return-promise surface exists in the diff. |
| AG-3 displayed numbers must be correct | OK — checked at row level | UT-J-05's "Scanned 2026-08-12 22:36:24" equals `scanner_runs` id 2977 `created_at` 22:36:24.084611 in the DB; J-01's three run timestamps equal `data_provider_runs` 471/472/473 to the second; J-09's `r2977` dataset version matches the same run id. `compute_readiness`/`compute_preflight` untouched — only the cache wrapper changed. |
| AG-4 no overfit edges | OK | No referee/claim/evidence path in the diff. |
| AG-5 determinism / no lookahead | OK | No scoring or forward-return code touched; `compute_forward_aggregates` byte-unchanged (explicit OUT OF SCOPE, confirmed in the diff). |
| AG-6 referee gate | OK | No evidence-derived claims this iteration (ops/perf only, per goal.md Loop mechanics). |
| AG-7 no hard-coded credentials | OK | `scan-report.md`: **CLEAN** — no secret, dependency or license finding on added lines. |
| AG-8 resilience to data-shape/scale change | OK (with a named risk) | Data basis byte-identical, re-derived by me in the DB: `daily_prices` 1996-01-02 → 2026-08-03, 591 symbols. No new whole-table load; warm paths untouched. The pool/page-cache memory risk is logged as **iter-72/a** (minor) and carried by J-07's `partial`, not smuggled into an anti-goal row. |
| AG-9 offline-deterministic ingest | OK — checked at row level | Every `data_provider_runs` row created today (ids 432-474) is `provider='seed'`; the only non-seed rows since 2026-08-01 remain ids 297 and 369, both pre-existing. Job 474's own record is seed/ok. |
| AG-10 host resource ceiling | OK — checked at file and command level | `git status --porcelain -- config.yaml project-extensions/ scripts/` shows only `config.yaml`; its entire diff is the pool values plus two comments. `git diff HEAD -- config.yaml \| grep -E "memory_cap_mb\|malloc_arena_max\|HOST-GUARD"` is **empty**. The QA backend's own boot header reads `port=8255 memory_cap_mb=8192 malloc_arena_max=2` / `host-guard: cpu_list=0-15 blas_threads=8`. No cap removed, weakened or bypassed. I was not unsure: the ceiling is intact and enforced; what is unmeasured is the demand beneath it (iter-72/a). |
| Coherence (structural veto) | COHERENCE-PASS | 0 blocking, 2 advisory (`iter-72/coherence.md`). No consolidation pass mandated. |

New minor entries this round: **iter-72/a** (pool 30→68 with a 256 MB per-connection page cache and no
VmPeak re-measurement), **/b** (TC-10 evidence never produced yet recorded complete; an unguarded fault
hook now ships in the `GET /api/data` handler), **/c** (6 of 8 goldens overturned; the stated reason is
contradicted by the log and by the frame), **/d** (walkthroughs unrecorded and the demo lane itself
broken), **/e** (12th over-budget round; ux-regression reviewer shed), **/f** (staleness bound removed
with no disclosure at the glass and no watchdog), **/g** (a 503 cliff above the tested load).
Closed this round: **iter-71/a, /b, /c, /d** — each verified by me, not accepted on a claim.
Ledger: 245 total, 123 unresolved, **0 unresolved critical**.

## Next-Step Recommendation

Run the next round at **lean** depth. Do these in order.

1. **Measure how much memory the app can now use, and cap it if needed.** This round let the app keep
   up to 68 database connections open instead of 30, and each one is allowed a 256 MB private cache,
   while the process is still limited to 8 GB in total. Nobody measured the result. Run a test that
   opens many connections at once during a heavy job, record the peak memory in
   `reports/perf-budgets.md`, and lower the per-connection cache or the number of kept connections if
   the margin is thin. This is the one thing standing between J-07 "Heavy aggregates never take the
   service down" and a clean pass, and this machine has crashed on memory before.
2. **Show the age of the health information on screen.** The app now always answers instantly with
   whatever health information it last computed, however old, and it reports that age only inside the
   API where no page reads it. If the background refresh ever stops, the top-bar badge would keep
   saying "Ready" forever and nothing on screen would say otherwise. Displaying the age is a
   user-visible change, so it needs a **full**-depth round of its own — schedule it right after item 1.
3. **Fix the automatic replay checks.** Six of eight replays failed this round. The reason written down
   ("they ran at the same time as our own heavy test") is not true — the failed screenshots are from
   12 minutes before that test started, and one of them shows the web app serving a plain, unstyled
   page stuck on "Checking backend…". Get the test web server healthy, re-run the replays on a quiet
   machine, and write down every change made to a replay script (one script quietly lost two checks).
4. Small and written down: file the missing `/data` error-message screenshot, or remove the unused
   fault-injection line from the live `GET /api/data` handler; record J-06's page-load timings when a
   frontend round comes up (3rd round owed).
5. Rides along, never the goal: record the J-05 walkthrough (14th round unrecorded) and J-07's own
   `[NEW]` walkthrough steps. The demo recorder itself is broken this round — five of its eight steps
   failed their own clicks and typing — so it needs repair before it can be used as evidence.
6. Carried, untouched: iter-29/b + the badge wording after a permanently failed warm-up (45th round
   unmade); iter-31/e; iter-32/f; iter-35/k; iter-36/n; iter-37/o; iter-37/q; iter-39/u; iter-46/az;
   iter-46/ba; iter-47/bd; iter-47/bf; iter-47/bi; iter-48/bj; iter-57/f; iter-57/l; iter-59/g;
   iter-59/h; iter-59/k; iter-62/e; iter-62/f; iter-63/a; iter-63/b; iter-63/d; iter-64/b; iter-64/e;
   iter-64/f; iter-65/b; iter-65/c; iter-65/d; iter-66/b; iter-66/e; iter-66/f; iter-66/g; iter-67/f;
   iter-67/g; iter-68/d; iter-68/e; iter-69/e; iter-70/c; iter-70/e; iter-70/f; iter-71/e; iter-71/f;
   iter-71/g; iter-71/h. Deferred a THIRTY-NINTH time: iter-33/g, the Regime Lab.
7. **For the owner — the same question, 24th round, and this time the answer is good news.** The app
   must answer its health check within 2 seconds while a long background job runs. Last round 58 of
   900 checks got no answer at all and one stretch of silence lasted 165 seconds. This round, on the
   correct launcher and with two heavy jobs running at the same time, **every one of 1,315 checks was
   answered and the slowest took 1.7 seconds**. Please decide: (a) keep the 2-second promise for long
   jobs (the app now meets it), or apply it to short jobs only; and (b) may we limit how many heavy
   computations run at the same time (your card B-1107)? Also still waiting on you: permission to fix
   the one-line ordering bug in `scripts/automation/browser-qa-phase.sh`, and a cost decision — this
   round again ran about 4.5 times over its time budget, the twelfth in a row, and the pipeline
   dropped one of its own reviewers to save time. One thing needs no decision: the next round must
   measure the app's memory use before we call the availability work finished.
