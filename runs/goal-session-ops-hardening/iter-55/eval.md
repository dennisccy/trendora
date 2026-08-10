# Iteration 55 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The code change this round asked for was built and it works. The saved record of a data job no
longer claims it finished work it did not finish — I read the new code myself, ran its tests, and
saw a real job honestly leave one item off its list. The second aim missed: the app still went
silent to the health check 11 times during a heavy job, worse than the 6 last round, and the
report says so plainly. Nothing broke: 5 journeys still pass, 3 are still part-way. Two other
things went wrong with the paperwork rather than the product — the record of the two checks this
round existed to run was deleted by a later run of the same tool, and the check script for J-05
"Aggregates are precomputed at ingest" used up the one date it needs, so it will fail next time
for a reason that has nothing to do with the app.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | reports/qa/goal-ops-hardening-iter-55-evidence/J-01-verify.png (replay PASS); DB runs 362 (9 non-trading + 19 = 28 calendar) and 363 (weekend: 0 of 2) |
| J-03 No per-run range cap | passing | passing | reports/qa/goal-ops-hardening-iter-55-evidence/J-03-verify.png (replay PASS); DB run 364 (129 + 283 = 412 calendar days, past the retired 370-day cap) |
| J-04 Non-blocking boot with visible status | passing | passing | reports/qa/goal-ops-hardening-iter-55-evidence/J-04-verify.png — badge reads Ready; the fixed `wait_for` golden no longer races the boot |
| J-05 Aggregates are precomputed at ingest, never on the fly | partial | partial | reports/qa/goal-ops-hardening-iter-55-evidence/J-05-verify.png; DB run 356 + scanner_runs 2940 (263 rows, byte-exact vs the screenshot); step 4 fails — 11 non-answers / 1,839 polls (tc5-drill-out/health-polls.csv) |
| J-06 Pages load only what they need | partial | partial (not re-verified) | not exercised — spec OUT OF SCOPE (docs/phases/goal-ops-hardening-iter-55.md:79); prior evidence reports/qa/goal-ops-hardening-iter-54-evidence/UT-J-06-result.png carried forward |
| J-07 Heavy aggregates never take the service down | partial | partial | reports/qa/goal-ops-hardening-iter-55-evidence/J-07-verify.png; all 5 horizons logs/backend.log:237446-237702; VmPeak 4,590.3 MB = 43.9% margin (tc5-drill-out/summary.json); step 2 fails — 11 non-answers / 1,839 |
| J-08 Backtest evidence serves from storage only | passing | passing | reports/qa/goal-ops-hardening-iter-55-evidence/J-08-verify.png (replay PASS) |
| J-09 The backend discloses its own background-compute activity | passing | passing | reports/qa/goal-ops-hardening-iter-55-evidence/J-09-verify.png (replay PASS) |

Deltas: newly passing **none**; newly failing **none**; regressed **none**. Shape holds at
**5 passing / 3 partial / 0 failing**. No `browser-infra.json`, no `journeys-changed.md`; all 8
`spec_hash` values match `goal_gate.py hash-journeys` run by me. No DEFERRED-BUDGET rows.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 (no unbacked "proven" language) | OK | No evidence claims this iteration; diff is 4 files, all backend engine/test code (`iter-diff.md`: data_manager.py, forward_testing.py + their two test files). No proven-language added. |
| AG-2 (decision-quality only) | OK | No order, price-target or return-promise surface touched; `Frontend Present: no`, `git status --porcelain -- apps/frontend` empty. |
| AG-3 (displayed numbers correct) | OK — verified at the row level | I compared `J-05-verify.png`'s 15 visible leaderboard rows against `scanner_results` for `run_id=2940` (as-of 2010-11-08): every ticker, score, bucket letter and status matches exactly (e.g. rank 254 LLY 16.28 E / 71.35 C / 30.28 E "Avoid", Health Care; rank 263 NRG 5.85 / 64.22 D / 43.61, last of 263). |
| AG-4 (no overfit edges) | OK | No referee/claims surface touched. |
| AG-5 (determinism / no lookahead) | OK | The change is scheduling-only plus a completeness counter; byte-identity proven for all 5 horizons with and without `as_of` against a pinned pre-fix oracle, with the yield forced on every row (`test_forward_testing_aggregates_streaming.py`, 10/10; audit re-ran the file: 58 passed). |
| AG-6 (referee gate) | OK | J-05/J-07 carry no Evidence Claims (`docs/goal.md` Loop mechanics). |
| AG-7 (no hard-coded credentials) | OK | `scan-report.md` = **CLEAN**; no config/env/manifest file in the 4-file diff. |
| AG-8 (resilience, no unbounded loads, honest status) | Minor issue, not critical | Isolate-and-continue intact (I read `data_manager.py:4278-4302`); no new whole-table load; zero new MemoryErrors (log total 8,104, byte-identical to iter-54). But 11 connection-level `/api/health` non-answers vs 6 last round, and 2 phases previously closed to zero re-opened. Filed minor. |
| AG-9 (offline-deterministic ingest) | OK — verified at the row level | `select distinct provider from data_provider_runs where id>=352` returns exactly `[('seed',)]`; same for every `scanner_runs` row created 2026-08-10. |
| AG-10 (host resource ceiling) | OK — verified at the source | `git diff --stat` AND `git status --porcelain` over all five frozen paths are BOTH empty; `config.yaml:1363-1364` still reads 8192 / 2. |
| Lane-ordering rule (TC-11, binding this iteration) | OK — verified | Newest product-code mtime `forward_testing.py` **00:31:42**; newest touched test **00:35:21**; earliest lane artifact **02:09:47**. `find apps/backend/app apps/frontend -newermt '2026-08-10 02:09:47'` returns nothing. Third consecutive round the rule holds; the audit applied no fix at all and filed six iter-56 notes instead. |

**Ledger:** 4 closed this round (the horizon-20 completeness overstatement; the memory-pressure
explain-away; TC-7's twice-skipped J-05 golden; the iter-54 depth mismatch). **8 new open**, all
minor: the QA PASS over a BLOCKED lane citing deleted rows; the destroyed J-05/J-07 result rows;
the un-rotated J-05 golden date; the dangling profiling citation at `forward_testing.py:1124`;
TC-5 not met and worse; three lane rows sharing one byte-identical screenshot; the un-recorded
walkthrough; `test_forward_testing.py` never finishing. **123 total, 54 unresolved, 0 unresolved
critical.**

**Lane verdicts:** scan-report **CLEAN**; coherence **COHERENCE-PASS** (0 blocking, 2 advisory);
review **PASS_WITH_NOTES** (1 MINOR, `definition_of_done: partial`); QA **PASS**; audit
**PASS_WITH_GAPS**; merged browser QA **BLOCKED** (12/12 rows PASS, 2 target-missing); deterministic
replay **PASS 5/5**; demo **SKIPPED** (invalid demo script); ux-regression **SKIPPED** (wall-clock
trim); closure **CLOSURE-PASS**.

## Next-Step Recommendation

Run the next round at **full** depth. This is a recommendation, not a mandate — but the deep
review stage is the only one that found this round's two most important facts, and one of them
will break the next round if nobody acts on it. Do the work in this order.

1. **Fix the check script for J-05 "Aggregates are precomputed at ingest" before anything else
   runs.** That script needs a date the app has never processed. It used up its date this round
   (8 November 2010). If nobody changes it, the check will fail next time and it will look like
   the app broke when nothing broke. Five safe replacement dates are already found and confirmed:
   10, 11, 12, 15 or 16 November 2010. Change the date in four places in the script and confirm it
   live before the checks run.
2. **Stop the checking tool from deleting its own results.** This round it ran twice; the second,
   smaller run wrote over the first and erased the results for the two journeys this round existed
   to prove. Write each run to its own file, or merge the rows. Then run the J-05 and J-07 checks
   again so their results are on record.
3. **Make the quality report read the browser report's verdict line first.** The quality report
   said "pass" and quoted results that had already been deleted, while the browser report said
   "blocked" in its own headline. Fifth round in a row for this. It is a one-line habit change.
4. **Find out why two screens' data calls are slow.** The job-history list and the
   data-availability chart take 3 to 21 seconds because the stored data grew about fifteen times
   bigger. This is the single thing keeping J-06 "Pages load only what they need" from passing, and
   it has now been put off twice. Measure first, then fix.
5. **Do not spend another round on the "app never goes quiet" problem.** Five rounds have now tried
   the same lever — making one calculation pause more often to let the health check through — and
   this round's data shows the lever is finished: a second, unrelated calculation ran for more than
   ten minutes in the same process and starved the health check anyway. It cannot be closed without
   the owner's answer to question (a) below.
6. SMALL AND ALREADY WRITTEN DOWN: a code comment points at a measurement note that was never
   written — publish it or reword the comment; three browser checks share one identical picture and
   a fourth is blank; one test file of 93 tests has never finished and needs a run early in a
   session; the live fault drill for the relocated test switch is still owed.
7. CARRIED, untouched: iter-29/b + the badge wording after a permanently failed warm-up (28th round
   unmade); iter-31/e; iter-32/f; iter-35/k; iter-36/n; iter-37/o; iter-37/q; iter-39/u; iter-46/az;
   iter-46/ba; iter-47/bd; iter-47/bf; iter-47/bi; iter-48/bj. Deferred a TWENTY-FIRST time:
   iter-33/g, the Regime Lab.
8. CAPTURE ONLY, never a round's goal: no walkthrough was recorded at all, because the recording
   script itself is broken ("step 6 needs text"). Fixing that script is a five-minute job that
   unblocks three journeys' recordings at once.
9. OWNER: two decisions and three facts. The decisions, both asked at rounds 50, 51, 53, 54 and 55
   and still unanswered — (a) may a future round move the heavy calculation into a separate
   process? This round produced the strongest evidence yet that it is the only remaining way: one
   request was starved for more than 600 seconds inside the same process while every calculation
   was already pausing politely. (b) Does the 20-minute limit on a data job's finishing work apply
   while the app is also serving people, or only when it is idle? The facts — the app's saved job
   record no longer claims work it did not finish, proven by a real job that honestly left one item
   off its list; during a heavy job with nothing else running, the health check answered all 459
   times with no answer slower than 1.7 seconds; and the app's peak memory use was 4,590 MB against
   its 8,192 MB ceiling, a 44% margin.

## Halt Justification (if halting)

Not halting.
