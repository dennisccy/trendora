# Iteration 74 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

This round did the one thing it was for. The app's memory use during a heavy background job was
finally measured end to end: the highest it reached was 4,724 MB out of an allowed 8,192 MB, which
leaves 42.3% spare. I checked that number myself in the raw measurement file, not in the report.
During the same 33-minute job, all 1,795 health checks were answered, the slowest in 1.99 seconds.
That closes the last open step of J-07 "Heavy aggregates never take the service down", so J-07 is now
passing for the first time since iteration 34, and all eight journeys are passing.

Two things stop this from being finished work. J-08 "Backtest evidence serves from storage only" and
J-09 "The backend discloses its own background-compute activity" went a second round in a row with no
test evidence of their own: the picture-taking part of the test system served pages without their
styling and data, so five replays failed for a reason that has nothing to do with the app. I opened
all five pictures to confirm that. There are also 131 small open items on the defect list. Either one
of those blocks declaring the goal reached.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | `reports/phase-goal-ops-hardening-iter-74-ui-test-results.md` row UT-J-01 PASS; frame opened: `reports/qa/goal-ops-hardening-iter-74-evidence/J-01-verify.png` (styled Scanner Run, badge "Ready", provider seed); DB runs 479/480 carry the 19-of-28 and 0-of-2 partitions |
| J-03 No per-run range cap | passing | passing | Row UT-J-03 PASS; frame opened: `.../J-03-verify.png` — Job progress "backfill job · 2025-06-01 → 2026-07-17" = 412 days accepted; DB runs 477/481 dates_total 283 over calendar_days 412 |
| J-04 Non-blocking boot with visible status | passing | passing | Row UT-J-04 PASS (real data-state attribute + persisted run field); boot header `logs/backend.log:351993-351995` shows caps applied |
| J-05 Aggregates are precomputed at ingest, never on the fly | passing | passing | Row UT-J-05 PASS; frame opened: `.../J-05-verify-final.png` ("as of 2019-01-31 … Scanned 2026-08-13 05:20:31"); DB `data_provider_runs` 484 seed/ok 05:20:15→05:37:58, `scanner_runs` 2980 created 05:20:31.202585 |
| J-06 Pages load only what they need | passing | passing | Row UT-J-06 PASS (11 pages, badge ready, domInteractive 52 ms); frame opened: `.../J-06-pages-load.png`; replay frame `.../J-06-verify.png` opened and is a broken unstyled shell |
| **J-07 Heavy aggregates never take the service down** | **partial** | **passing** | Row UT-J-07 PASS; `runs/goal-session-ops-hardening/iter-74/phase-vmpeak-samples.csv` (peak 4,837,420 kB = 4,724.0 MB, 42.33% margin, recomputed by me), `...-phase-vmpeak.json` (job ok, 9/9 phases + 5 horizons), `...-health.csv` (1,795/1,795 HTTP 200, max 1.987 s), `reports/perf-budgets.md` Addendum 39, frame `.../J-07-backtest-live.png` |
| J-08 Backtest evidence serves from storage only | passing | passing (carried, NOT verified) | No lane row — SKIP/required-unverified. Frame opened: `.../J-08-verify.png` is an unstyled asset-less shell. Held on durability; `last_verified_iter` stays `goal-ops-hardening-iter-72` |
| J-09 The backend discloses its own background-compute activity | passing | passing (carried, NOT verified) | No lane row — SKIP/required-unverified. Frame opened: `.../J-09-verify.png` is the same broken shell and shows `/backtest`, not `/data`. Held on durability; `last_verified_iter` stays `goal-ops-hardening-iter-72` |

Goal-edit drift: `journeys-changed.md` absent, and I re-verified it myself — all eight `spec_hash`
values recomputed from the edited `docs/goal.md` are byte-identical to the recorded ones, and the
goal.md diff contains zero changed lines mentioning any journey or anti-goal. The edit is confined to
the "Ground truth" facts block.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 unproven values never shown as proven | OK | No product code and no UI changed; diff is one test file + the Ground-truth block. No proven-language added. |
| AG-2 decision-quality only | OK | No return promise, price target, order or simulation added anywhere in the diff. |
| AG-3 displayed numbers must be correct | OK | Checked, not assumed: the J-05 frame's "Scanned 2026-08-13 05:20:31" equals `scanner_runs` 2980 `created_at` 05:20:31.202585; goal.md's new DB size 8,365,871,104 bytes equals the live file exactly; basis unchanged (1996-01-02 → current, 591 symbols). |
| AG-4 no overfit edges | OK | No new claim, no referee-facing change this round. |
| AG-5 determinism / no lookahead | OK | No engine or scoring code in the diff. |
| AG-6 referee gate on evidence claims | OK | No evidence-derived claim shipped. |
| AG-7 no hard-coded credentials | OK | `iter-74/scan-report.md` CLEAN (tracked + 1 untracked file scanned). |
| AG-8 resilience / no unbounded whole-table loads | OK, one note | No application code changed. From the drill boot onward `logs/backend.log` holds 8,932 requests with only two non-200s (404 `/api/jobs`, 405 `/api/data/jobs` — client-side path/method mistakes), and zero MemoryError / QueuePool / Traceback / "Exceeded concurrency limit" lines. Note: the app's own contained error boundary fired once on Scanner Runs at ~05:08 UTC (`J-05-verify.png`) — that is the graceful shape AG-8 asks for, not a blank error page, but it is a real render failure and is logged as iter-74/a. |
| AG-9 offline-deterministic ingest | OK | All ten of today's `data_provider_runs` (475-484) are `provider='seed'`; the only non-seed rows since 2026-08-01 remain 297 (08-04) and 369 (08-10), both pre-existing. The drill's own job carries `"source": null`. |
| AG-10 host resource ceiling | OK | `git status --porcelain -- config.yaml project-extensions/ scripts/` is EMPTY. `config.yaml` still declares `memory_cap_mb: 8192`, `malloc_arena_max: 2`, `pool_size: 24` + `max_overflow: 44` = 68 ≥ `limit_concurrency: 64`. Enforcement verified live in the drill's own boot header (`logs/backend.log:351993-351995`: `start-backend.sh … port=18755 memory_cap_mb=8192 malloc_arena_max=2` / `host-guard: cpu_list=0-15 blas_threads=8`) — launched via `start-backend.sh`, never `dev.sh`. |

New minor ledger entries: iter-74/a (a fourth round of false replay-failure explanations), iter-74/b
(J-08/J-09 unverified a second round), iter-74/c (stray zero-byte `=` file in the repo root),
iter-74/d (14th over-budget round). Two prior entries closed: iter-73/a (Addendum 38's test count) and
iter-73/e (goal.md's stale ground truth). Ledger: 255 total, 131 unresolved, 0 unresolved critical.
Coherence: COHERENCE-PASS. Review: PASS. Scan: CLEAN.

## Next-Step Recommendation

Run the next round at **lean** depth and give it one job: repair the test system's web front end so it
stops serving pages without their styling and data, then re-verify J-09 "The backend discloses its own
background-compute activity" first and J-08 "Backtest evidence serves from storage only" second, on
fresh pictures. Do not regenerate the five queued replay scripts — I opened the pictures and the cause
is the broken front end, so a new script cannot fix it. Ride-alongs, never the goal: record the
walkthrough steps that J-07 and J-05 have been owed for sixteen rounds, and write J-06's page timings
into `reports/perf-budgets.md` (owed a fifth round). Keep the badge freshness display (iter-72/f)
queued for its own **full**-depth round afterwards, because it is the first change a user would see.
In one sentence: fix the picture-taking web server, re-check the two journeys that have gone two
rounds without their own evidence, and this session is one clean round from being finished.

**Owner — the same question, 26th round, plus the news.** The app must answer its health check within
2 seconds while a long background job runs. This round every one of 1,795 checks during a real
33-minute job was answered and the slowest took 1.99 seconds. Please decide two things you have been
asked before: (a) keep the 2-second promise for long jobs, or apply it to short jobs only; and (b) may
we limit how many heavy computations run at the same time (B-1107)? Also still waiting on you:
permission to fix the one-line ordering bug in `scripts/automation/browser-qa-phase.sh`, and a cost
decision — this round again ran about 2.7 times over its time budget, the fourteenth in a row. One
piece of good news needing no decision: the memory question you were asked about last round is
answered — the app used 4,724 MB of the 8,192 MB it is allowed, with 42% to spare.

## Halt Justification (if halting)

Not halting. All eight journeys are passing, but GOAL_ACHIEVED is blocked on three separate grounds,
any one of which is enough: 131 unresolved (all minor) items on the defect ledger; J-08 and J-09 have
had no evidence of their own for two consecutive rounds; and the deterministic replay lane cannot
currently produce trustworthy evidence at all.
