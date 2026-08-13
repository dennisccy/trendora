# Iteration 73 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

This round had one job: measure how much memory the app really uses now that it is allowed to hold
many more database connections at once. It did not get that number. The measurement was tried four
times. Three tries put extra load on the app and each time the app started refusing requests for a
reason we already knew about and had ruled out of scope. The fourth try ran cleanly for 26 minutes
but ran out of time before the heaviest part of the job. So J-07 "Heavy aggregates never take the
service down" stays at partial for the same one step as last round. The good news is real and I
checked it myself: while a real 17-minute data job ran, all 1,232 health checks were answered, the
slowest took 1.19 seconds, and the app's log holds no errors at all since it started. Nothing
regressed — the whole change this round is one test file, so no product behaviour could have moved.
Two journeys, J-08 "Backtest evidence serves from storage only" and J-09 "The backend discloses its
own background-compute activity", were not actually checked this round, because the automated replay
tool photographed a broken, unstyled page instead of the app.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | `reports/qa/goal-ops-hardening-iter-73-evidence/J-01-verify.png` (opened: real styled Scanner Run page, badge "Ready"); merged row UT-J-01 PASS |
| J-03 No per-run range cap | passing | passing | `reports/qa/goal-ops-hardening-iter-73-evidence/J-03-verify.png` (opened: Job progress panel reads "backfill job · 2025-06-01 → 2026-07-17" = 412 days); merged row UT-J-03 PASS |
| J-04 Non-blocking boot with visible status | passing | passing | `reports/qa/goal-ops-hardening-iter-73-evidence/J-04-verify.png` (opened: Data Manager, SNAPSHOT DATES 2977, gap range from 2005-07-12); merged row UT-J-04 PASS |
| J-05 Aggregates are precomputed at ingest | passing | passing | `reports/qa/goal-ops-hardening-iter-73-evidence/UT-J-05-result.png` (opened: "Immutable snapshot — as of 2005-07-12 … Scanned 2026-08-13 02:26:17") + `poll_health.csv` (1,232 polls, re-derived by me) |
| J-06 Pages load only what they need | passing | passing | `reports/qa/goal-ops-hardening-iter-73-evidence/UT-J-06-result.png` (opened: /research/regime-lab renders styled and real); merged row UT-J-06 PASS, 16 live steps |
| J-07 Heavy aggregates never take the service down | partial | **partial** (unchanged; step 3 still open) | `reports/qa/goal-ops-hardening-iter-73-evidence/UT-J-07-result.png` (opened: /backtest as-of 2026-08-03) + `J-07-steady-state-poll.csv` (20/20) + `reports/perf-budgets.md` Addendum 38 |
| J-08 Backtest evidence serves from storage only | passing | passing (**carried on durability — NOT verified this round**) | Prior: `reports/qa/goal-ops-hardening-iter-72-evidence/UT-J-08-result.png`. This round's `J-08-verify.png` opened by me: an unstyled, asset-less "Checking backend…" shell — a broken capture, not evidence |
| J-09 The backend discloses its own background-compute activity | passing | passing (**carried on durability — NOT verified this round**) | Prior: `reports/qa/goal-ops-hardening-iter-72-evidence/UT-J-09-result.png`. This round's `J-09-verify.png` opened by me: the same unstyled shell, and showing /backtest rather than J-09's own /data surface |

Merged browser-QA verdict: **FAIL** (5/8 passed, 2 skipped, 2 required-unverified).
Deterministic replay: 3/8 PASS; J-05, J-06, J-07, J-08, J-09 FAILed and were mass-voided by the
SPEED-22 breaker. Review: **PASS_WITH_NOTES**. Coherence: **COHERENCE-PASS**. Diff scan: **CLEAN**.
No `browser-infra.json`, no `journeys-changed.md`, no `DEFERRED-BUDGET` rows.

## Anti-goal Check

Worked from `iter-73/scan-report.md` (CLEAN) and `iter-73/iter-diff.md` (one file). Product diff
confirmed independently by me: `git diff <snapshot> -- apps/ config.yaml scripts/ project-extensions/`
returns exactly one file, `apps/backend/tests/test_start_backend_script.py` — a test file. No runtime
code, no frontend, no config.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials (AG-7) | OK | scan-report CLEAN on added lines; the diff adds no config, env or key file — I checked the file list, not just the verdict |
| Paid / external SaaS, new dependencies (AG-9) | OK | No manifest in the diff; handoff states no new dependencies. Verified in the database: all four ingest runs today (`data_provider_runs` 475-478) are `provider='seed'`, `status='ok'`. The only non-seed rows since 2026-08-01 remain ids 297 and 369 (yahoo), both predating this round |
| License changes | OK | No LICENSE or license field anywhere in the diff |
| Fabricated / substituted data (AG-3) | OK | Re-derived by me: `scanner_runs` id 2978 = as-of 2005-07-12, created 2026-08-13 02:26:17.344822, provider seed, 149 real result rows — and the frame reads "Scanned 2026-08-13 02:26:17". Price basis 1996-01-02 → 2026-08-03 / 591 symbols, byte-identical to iters 71-72. A second free cross-check: the J-04 frame taken before the backfill shows 2977 snapshots and names 2005-07-12 as the earliest gap; the database now reads 2978 |
| AG-1 / AG-2 / AG-4 / AG-6 (proven-language, buy-sell, overfit, referee) | OK | No product code, no UI change, no evidence claim this round. The frames I opened still carry the survivorship-bias disclosure verbatim on /backtest and /research/regime-lab |
| AG-5 (determinism, no lookahead) | OK | No scoring, forward-return or as-of code touched — not implicated by a test-only diff |
| AG-8 (resilience, no unbounded loads, honest degradation) | OK, with a recorded finding | Zero non-200 responses in the live backend's entire 3,016-line log since boot at 02:13:14Z; zero QueuePool, MemoryError, Traceback. Separately: 18,768 "Exceeded concurrency limit" lines from the developer's own drills, all BEFORE that boot, so no journey evidence is contaminated — but they show the known 503 cliff is much lower than recorded (logged **iter-73/b**, minor) |
| AG-10 (host resource ceiling) | OK | `git status --porcelain -- config.yaml project-extensions/ scripts/` is EMPTY — byte-unchanged. Caps still declared (`memory_cap_mb: 8192`, `malloc_arena_max: 2`, `limit_concurrency: 64`, `pool_size: 24`, `max_overflow: 44`, `cache_size: -262144`) AND enforced: `logs/backend.log:348694` reads `start-backend.sh: launching at 2026-08-13T02:13:14Z / port=8255 memory_cap_mb=8192 malloc_arena_max=2 / host-guard: cpu_list=0-15 blas_threads=8`. The three `dev.sh` headers at 02:14-02:15Z are the test module's own throwaway spawns on ports 18955/19356, and they echo the caps too. Nothing removed, weakened or bypassed |

**New minor entries this round:** iter-73/a (Addendum 38's inflated test count), iter-73/b (the 503
cliff is lower than recorded), iter-73/c (two required journeys unverified, with a false explanation
on file), iter-73/d (an over-broad `pkill` killed the drill's own backend), iter-73/e (goal.md's
ground-truth block is stale: the DB is ~8.4 GB, not 811 MiB), iter-73/f (13th over-budget round).
**Closed this round: none.** Ledger: **251 total, 129 unresolved, 0 unresolved critical.**

## Next-Step Recommendation

Keep going at **lean** depth. One product change, in this order.

1. **Get the memory number a different way.** Stop trying to run one long, uninterrupted job — this
   host is shared with other work and has defeated that plan three times. Instead, record peak memory
   phase by phase during the heavy job, using the timers that already exist in the code, so the answer
   can be assembled from short runs. This is the only thing left between J-07 "Heavy aggregates never
   take the service down" and a full pass. **Stop rule, so we do not loop:** if this next attempt also
   fails to produce the number, do not try a fourth time — ask the owner to either accept the quiet-run
   figure already on record (2,334.8 MB, 71.5% margin) as the answer, or relax what J-07's third step
   asks for.
2. **Repair the screenshot replay tool, and fix the right thing.** The tool's own note blames the
   wrong cause. I opened the pictures: the app was served without its styling, not "the script's
   selectors drifted". Regenerating the five queued scripts will therefore not fix it. Find why the
   test frontend intermittently serves a page with no styling and no data, then re-check J-09 first
   and J-08 second — those are the two journeys that went unchecked this round.
3. **Correct Addendum 38's test count** (it says 72 tests; the file has 18 and the run reported 12
   passed, 1 skipped). One line, and it protects the credibility of the round's own report.
4. **Update the goal file's "ground truth" numbers** — the database is now about 8.4 GB, not 811 MB,
   and a rebuild job always runs the whole history no matter what dates are requested. That single fact
   is why this round ran out of time.
5. Rides along, never the goal: the J-07 walkthrough recording (15th round owed) and J-05's (15th), and
   J-06's page timings written into `reports/perf-budgets.md` (4th round owed).
6. CARRIED, untouched: iter-29/b + the badge wording after a permanently failed warm-up (46th round
   unmade); iter-31/e; iter-32/f; iter-35/k; iter-36/n; iter-37/o; iter-37/q; iter-39/u; iter-46/az;
   iter-46/ba; iter-47/bd; iter-47/bf; iter-47/bi; iter-48/bj; iter-57/f; iter-57/l; iter-59/g;
   iter-59/h; iter-59/k; iter-62/e; iter-62/f; iter-63/a; iter-63/b; iter-63/d; iter-64/b; iter-64/e;
   iter-64/f; iter-65/b; iter-65/c; iter-65/d; iter-66/b; iter-66/e; iter-66/f; iter-66/g; iter-67/f;
   iter-67/g; iter-68/d; iter-68/e; iter-69/e; iter-70/c; iter-70/e; iter-70/f; iter-71/e; iter-71/f;
   iter-71/g; iter-71/h; iter-72/a; iter-72/b; iter-72/d; iter-72/e; iter-72/f; iter-72/g. Deferred a
   FORTIETH time: iter-33/g, the Regime Lab.
7. Rendering the data-freshness value on the badge (iter-72/f) stays queued and still needs a **full**
   round of its own, because it is this cycle's first change a user would see. It is not next, because
   J-07 is one step from done and this round is not it.

**OWNER — the same one sentence, 25th round, plus one new question.** The app must answer its health
check within 2 seconds while a long background job runs. This round every one of 1,232 checks during a
real 17-minute job was answered, and the slowest took 1.19 seconds. Please decide two things you have
been asked before: (a) keep the 2-second promise for long jobs, or apply it to short jobs only; and
(b) may we limit how many heavy computations run at the same time (card B-1107)? **New this round:**
we tried three times to measure how much memory the app uses when many database connections are open,
and each time other programs running on the same machine made the app start refusing requests before
the measurement finished. If you can give us one quiet hour on this machine, we can finish it. If not,
please tell us whether the quiet-run figure we already have (the app used about 2.3 GB of its 8 GB
allowance) is good enough to close the question. Still waiting on you as well: permission to fix the
one-line ordering bug in `scripts/automation/browser-qa-phase.sh`, and a cost decision — this round ran
about 3.3 times over its time budget, the thirteenth in a row.
