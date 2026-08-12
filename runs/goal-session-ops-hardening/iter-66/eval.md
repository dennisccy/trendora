# Iteration 66 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** lean

## Summary

This round found the answer to the question it was chartered to ask, but not the answer it
expected. The team profiled the coverage-and-membership step twice and found nothing slow in
it, so no code was changed there — an honest empty result. It also shipped the two small
fixes it promised and one real repair: a job that dies mid-run now reuses its own history row
instead of writing a second one. The important news came from the measurement itself. Both
test lanes now use the same stopwatch, and both say the app is slower under load than any
round so far: 70 of 1,024 health checks took longer than 2 seconds (worst 4.4 s), and a
second, independent run saw 6 of 150 (worst 3.8 s). I recounted both files myself. When I
lined every slow answer up against the app's own job log, 68 of the 70 fell inside one single
job step — the "factor lab" step that last round declared clean and closed. Nothing crashed:
every one of the 1,174 checks was answered, and the app logged no errors at all.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range | passing | passing | reports/qa/goal-ops-hardening-iter-66-evidence/J-01-verify.png (opened: May 2026-05-29 snapshot page renders, "Immutable snapshot — as of 2026-05-29") |
| J-03 No per-run range cap | passing | passing | reports/qa/goal-ops-hardening-iter-66-evidence/J-03-verify.png (replay PASS) |
| J-04 Non-blocking boot with visible status | passing | passing | reports/qa/goal-ops-hardening-iter-66-evidence/J-04-verify.png (replay PASS) |
| J-05 Aggregates precomputed at ingest | passing | passing | reports/qa/goal-ops-hardening-iter-66-evidence/J-05-verify.png (opened: live leaderboard, no error boundary) + sqlite `scanner_runs` id=2966, asof 2005-06-30, created 2026-08-12 00:33:27Z by the replay's own backfill |
| J-06 Pages load only what they need | passing | passing | reports/qa/goal-ops-hardening-iter-66-evidence/J-06-verify.png (replay PASS) |
| J-07 Heavy aggregates never take the service down | partial | partial (unchanged) | reports/qa/goal-ops-hardening-iter-66-evidence/UT-J-07-result.png + J-07-verify.png (opened) · runs/goal-ops-hardening-iter-66/evidence-drill/tc1-health-poll.csv (70/1,024 over 2.0 s) · reports/qa/goal-ops-hardening-iter-66-evidence/j07-health-poll.csv (6/150) |
| J-08 Backtest evidence serves from storage only | passing | passing | reports/qa/goal-ops-hardening-iter-66-evidence/J-08-verify.png (replay PASS) |
| J-09 Backend discloses background compute | passing | passing | reports/qa/goal-ops-hardening-iter-66-evidence/J-09-verify.png · J-07-verify.png shows PRICE HISTORY 1996-01-02 → 2026-08-03 / 591 symbols, byte-equal to sqlite `daily_prices` min/max date and 591 distinct symbols |

Merged browser QA: **PASS 8/8**. Raw deterministic replay: **PASS 8/8, zero overturned rows**
(no reconciliation footer). All 9 evidence frames md5-distinct (checked by me). No
`browser-infra.json`, no `journeys-changed.md`, no `DEFERRED-BUDGET` row. All eight
`spec_hash` values match `goal_gate.py hash-journeys`, run by me.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven/confident language | OK | No evidence claim, no scoring change; diff is one job-history helper + one QA script. |
| AG-2 decision-quality only | OK | No return promise, target, or order path added. |
| AG-3 displayed numbers correct | OK | Spot-checked: J-07-verify.png PRICE HISTORY 1996-01-02 → 2026-08-03 and 591 symbols equal sqlite `daily_prices`; J-05's replay date 2005-06-30 equals `scanner_runs` id=2966. |
| AG-4 no overfit edges | OK | No referee/ledger surface touched. |
| AG-5 determinism / no-lookahead | OK | No engine compute changed; `research.py`, `universe_resolver.py`, `forward_testing.py` untouched (`git status --porcelain`). |
| AG-6 referee gate | OK | No evidence-derived claim this iteration. |
| AG-7 no hard-coded credentials | OK | `iter-66/scan-report.md` CLEAN (2 untracked files scanned). |
| AG-8 resilience / no unbounded loads | OK | No page crash or error boundary in any of the 9 frames; zero HTTP 5xx and zero MemoryErrors added (backend.log stays at 129 lifetime 500s, last one inside iteration 57; dev.log has zero). New helper writes two columns on one existing row. |
| AG-9 offline-deterministic ingest | OK | `data_provider_runs` ids 432-436 (all this round's jobs) read `provider='seed'`; the only non-seed rows since 2026-08-01 remain ids 297 and 369, both pre-existing. The `"source":"yahoo"` in `tc1-job-create.json` is a request default; its persisted row (id=432) reads `seed`. |
| AG-10 host resource ceiling | OK | `git status --porcelain -- config.yaml project-extensions/ scripts/` shows no modification; `config.yaml:1363-1364` still 8192 / 2; `host-guard.env` still `HOST_GUARD_ENABLED=1`, CPU 0-15, BLAS 8, MEMORY_HIGH 12G; `scripts/dev.sh:45-76` still carries its `ulimit -v` + HOST-GUARD taskset block. |

Seven NEW minor entries this round (iter-66/a … /g), no critical ones; three earlier entries
CLOSED (iter-64/c the wrong sentinel-window note, iter-64/d the duplicate job-history row,
iter-65/a the two disagreeing stopwatches). Ledger now **206 total, 106 unresolved, 0
unresolved critical**. Coherence: **COHERENCE-PASS** (0 blocking, 0 advisory). Review: **PASS**.

## Next-Step Recommendation

Keep the next round LEAN. Its single job should be to find out why the app answers slowly
during one particular job step, using a better method than the last two rounds used.

1. **Re-open the "factor lab" step as the target.** Last round it was declared clean and put
   on the do-not-redo list after four profiles. This round's own numbers overrule that: 68 of
   the 70 slow answers happened inside its window (15.7% of the 433 checks taken during it),
   and in the 6.4 minutes after it ended there were 382 checks and **zero** slow ones. That is
   the strongest signal this session has produced about where the delay lives.
2. **Change the measuring method, not just the target.** Every profile so far re-ran the
   computation in a separate script and found nothing. The next one must watch the *live*
   running app during a real job — for example a watchdog inside the app that records how long
   the health request waits before it is served, so the wait itself is timed rather than the
   computation. Only then decide what to fix.
3. **Stop repeating the "the machine was busy" explanation until it is tested.** This round's
   own data argues against it: slow answers happened at an average machine load of 1.77 and
   normal answers at 1.90, on a machine with 16 cores. The cheap control is one drill with no
   job running at all, on the same machine, with the same script.
4. Small and written down: fix the three reporting gaps I logged this round (iter-66/a the
   handoff's missing whole-run number, iter-66/c the mis-placed breach, iter-66/d the
   one-hour timezone error in the browser lane's cross-check).
5. Rides along, never the goal: record the J-05 walkthrough (8 rounds unrecorded).
6. CARRIED, untouched: iter-29/b and the badge wording after a permanently failed warm-up
   (39th round unmade); iter-31/e; iter-32/f; iter-35/k; iter-36/n; iter-37/o; iter-37/q;
   iter-39/u; iter-46/az; iter-46/ba; iter-47/bd; iter-47/bf; iter-47/bi; iter-48/bj;
   iter-57/f; iter-57/l; iter-59/g; iter-59/h; iter-59/k; iter-62/e; iter-62/f; iter-63/a;
   iter-63/b; iter-63/d; iter-64/b; iter-64/e; iter-64/f; iter-65/b; iter-65/c; iter-65/d.
   Deferred a THIRTY-SECOND time: iter-33/g, the Regime Lab.
7. **OWNER — the same one sentence, 18th round, and this round changes the picture.** The app
   must answer its health check within 2 seconds while a background job runs; that promise was
   written for a job of about 30 seconds and ours last 18 to 20 minutes. This round every one
   of the 1,174 checks was answered and the app served no errors, but **70 of 1,024 answers
   (6.8%) took longer than 2 seconds — the worst rate of this session**, and the second lane
   saw the same thing (6 of 150). Both lanes used the same stopwatch for the first time, so
   the two numbers finally agree. Please say which you want: keep the 2-second promise for
   long jobs (J-07 "Heavy aggregates never take the service down" stays open until the app is
   faster), or apply it to short jobs only (J-07's last gap closes now). Still also waiting on
   you: permission to fix the one-line ordering bug in
   `scripts/automation/browser-qa-phase.sh`, and a cost decision — this round again ran two
   real multi-minute data jobs and finished at 8,641 seconds against a 3,600-second budget,
   the sixth over-budget round in a row.

## Halt Justification (if halting)

Not halting.

- **REGRESSION (tree C.1) — rejected.** No journey moved `passing`/`already_passing` →
  `failing`; the raw replay is 8/8 with zero overturned rows. Nothing on the critical list is
  met: the scan is CLEAN, both AG-10 checks are empty, every ingest row this round reads
  `seed`, no page crashed, and every displayed number I checked equals the stored one. J-07's
  worsening sits inside a journey that was already `partial`, is availability-clean (1,174 of
  1,174 answers, zero 5xx, zero MemoryErrors), and shows no wrong number on any screen.
- **STALLED (tree C.2) — rejected.** C.2 needs EVERY unblock path to be human-owned. This
  round produced a concrete one that is not: 97% of the slow answers now sit inside one named
  job step, and watching the live process during that step is ordinary agent work with its own
  acceptance test. The owner's ceiling sentence and the `browser-qa-phase.sh` sign-off are
  genuinely his.
- **GOAL_ACHIEVED (tree C.3) — rejected.** J-07 is `partial`.
- **ESCALATE (tree C.4) — rejected.** No journey has status `failing`, so the "2+ consecutive
  failures" clause cannot apply; the review lane did not fail open (PASS); and what this lean
  round surfaced is a sharper, narrower target with a named next experiment, not cross-cutting
  complexity. I re-derived every decisive number myself, which is the work the audit lane would
  have been dispatched for. I will not manufacture a clause match to buy the demo lane.
