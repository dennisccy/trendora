# Iteration 57 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

This round moved the scoreboard for the first time in four rounds: J-06 "Pages load only what they need"
is now passing. Six of the eight must-have journeys pass; two do not. The Data page no longer tells the
operator "there is no data" while a data job is running — it now shows the real calendar with an honest
"updating" note, and I saw that in the picture myself. Two slow calls that had held this journey open for
twelve rounds are fixed and I re-measured one of them directly against the database. The round also found
two real problems and said so plainly: a health check during a data job went unanswered for ten seconds,
and the written record claimed the opposite; and after the app ran out of memory it kept saying "Ready"
while four other pages returned errors.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | `reports/qa/goal-ops-hardening-iter-57-evidence/J-01-verify.png` (opened by me — "Immutable snapshot — as of 2026-05-29", provider seed); replay row UT-J-01 PASS; `data_provider_runs` 374/375/376 all `seed` |
| J-03 No per-run range cap | passing | passing | `.../J-03-verify.png`; replay row UT-J-03 PASS ("412 calendar days · 283 already snapshotted · 129 non-trading", chunk 5/5) |
| J-04 Non-blocking boot with visible status | passing | passing | `.../J-04-verify.png` (opened by me — green Ready badge; 2946 snapshot dates / 591 symbols / 5391 trading days, each matching my own sqlite read); replay row UT-J-04 PASS |
| J-05 Aggregates are precomputed at ingest, never on the fly | partial | partial | `.../J-05-verify.png` (opened by me — "Immutable snapshot — as of 2010-11-10 · Scanned 2026-08-10 09:16:41 · provider seed"); results row UT-J-05 PASS; `data_provider_runs` id=370 + `scanner_runs` id 2946 read by me. Step 4 fails: `runs/goal-ops-hardening-iter-57/tc7-health-poll.log` line 1,212 = `000` after 10.0s inside this job's own heavy-warm window |
| J-06 Pages load only what they need | partial | **passing** | `.../J-06-verify.png`; replay row UT-J-06 PASS; `.../UT-03-result.png` (opened by me — "Data as of r2945-… — updating" over a real 5,391-cell grid); `.../UT-06-result.png`, `.../UT-07-result.png`; `reports/perf-budgets.md` Addenda 21/22; my own live query check 591 == 591 at 0.002s vs 0.175-0.241s |
| J-07 Heavy aggregates never take the service down | partial | partial (not re-verified — out of scope this iteration) | Prior evidence `reports/qa/goal-ops-hardening-iter-55-evidence/J-07-verify.png` carried; new adverse evidence in `logs/backend.log` (MemoryError count 8,104 → 8,127; four endpoints returning 500 while `/api/health` answered 200) |
| J-08 Backtest evidence serves from storage only | passing | passing | `.../J-08-verify.png`; replay row UT-J-08 PASS |
| J-09 The backend discloses its own background-compute activity | passing | passing | `.../J-09-verify.png`; replay row UT-J-09 PASS (two live background windows, badge + `/data` panel + honest idle state) |

Deterministic replay: PASS 6/6 (`reports/phase-goal-ops-hardening-iter-57-regression-replay-results.md`).
Merged browser QA: PASS, 16/17 (1 skipped — UT-05 needs a request-blocking primitive the browser tool does
not have). The lane's first replay attempt FAILed 0/6 on a frontend port mismatch and is preserved at
`runs/goal-ops-hardening-iter-57/regression-replay-results.first-pass.md`; the re-run against the
port-corrected build is the authoritative one. No `DEFERRED-BUDGET` rows. No `browser-infra.json`. No
`journeys-changed.md`; all eight `spec_hash` values match `goal_gate.py hash-journeys` run by me.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven-language | OK | No evidence-ledger or certified-claim code in the 14-file diff; the Regime Lab frame in `J-06-verify.png` still carries its survivorship-bias and "descriptive, never a forecast" disclosures |
| AG-2 decision-quality only | OK | No order, price-target or return-promise text added; diff touches health, data_manager, indexes, indicators, mcp/tools, the heatmap component and `api.ts` only |
| AG-3 displayed numbers correct | OK, with two minor residuals | Checked at the row level: `/data` shows 2946 / 591 / 5391, matching my own sqlite reads; `availability_cache` holds exactly 1 row with 591 symbols and 5,391 cells; the banner's stamp in `UT-03-result.png` is the prior warm's while the stored row carries the new one. This iteration CLOSES an AG-3 hole (`persisted_this_call` no longer reports True after a rolled-back commit). Residuals: the "updating" wording fires on any stamp mismatch even with no job running (iter-57/c); the committed TC-7 record contradicts its own log (iter-57/b) |
| AG-4 no overfit edges | OK | No referee, ledger or claim path touched |
| AG-5 determinism / no lookahead | OK | Availability serves a stored blob; `sma_series` byte-identical by construction (verified in source); the health count is still a live read |
| AG-6 referee gate | n/a | No Evidence Claims — goal.md exempts J-01…J-06 |
| AG-7 no hard-coded credentials | OK | `scan-report.md` CLEAN; no config/env/manifest/LICENSE file in the diff |
| AG-8 resilience / no unbounded loads | **violated (minor, pre-existing)** | This iteration's own paths are strict reductions. But `/api/research/regime-lab`'s un-chunked `forward_returns` read raised a live MemoryError, and after a later MemoryError the process wedged — `/api/health` 200 "ready" while `/api/data`, `/api/data/availability`, `/api/runs` and `/api/stocks/AAPL/bars` returned 500 (500s counted by me in `logs/backend.log`). Not introduced by this diff; scored minor, logged as an interpretation call (iter-57/e) |
| AG-9 offline-deterministic ingest | **violated (minor)** | `data_provider_runs` id=369 — `provider='yahoo'`, 591 live outbound requests, `bars_fetched: 0` — from a manual drill click on the pre-existing "Fetch real EOD prices" button. Verified by me in sqlite; the other 18 rows created on 2026-08-10 are all `seed`. Sixth occurrence of the class, first one caught; two process rules adopted. Scored minor on the same grounds this ledger used for the strictly worse iter-47 event (iter-57/a) |
| AG-10 host resource ceiling | OK | `git status --porcelain` AND `git diff --stat` over all five frozen paths are both empty (run by me); `config.yaml:1363-1364` still reads 8192 / 2 |

Coherence: **COHERENCE-PASS** (0 blocking, 1 advisory — the new banner's wording differs from the sibling
coverage banner). Scan report: **CLEAN**. Review: **PASS_WITH_NOTES** (`definition_of_done: complete`,
`scope_creep: none`) after a FAIL that was properly fix-passed. Audit: **PASS_WITH_GAPS** after a FAIL that
was fix-passed with no product-code change (TC-14). QA: **PASS**, UI Evolution **UI-PASS**. UX regression:
**UX-REGRESSION-PASS**. Closure: **CLOSURE-PASS**. Depth dispatched: **full**, matching the spec — the
two-round depth mismatch did not recur.

Ledger after this round: **143 total, 66 unresolved, 0 unresolved critical** — 7 iter-56 items closed
(the during-a-job untruth, the depth mismatch, the "all within budget" claim over a 241 ms health reading,
the `persisted_this_call` rollback lie, the mislabelled calendar span, the heading-only J-06 golden, the
MCP `list_runs` duplicate) and 12 new ones opened, all minor.

## Next-Step Recommendation

Run the next round at full depth and give it this order.

1. **Correct the health-check record before anything else is built on it.** The written record says every
   one of 1,211 checks answered; the raw log has 1,212 lines and the last one got no answer for ten
   seconds, during a data job. The correction text is already written word-for-word in the audit report —
   paste it in, fix the same sentence in the round's handoff and status file, then re-run the drill so it
   counts every line, including failures, and uses the app's own job start/end markers.
2. **Stop the Data page from saying "updating" when nothing is running.** Right now the notice appears
   whenever the saved calendar is a version behind, even with no job in flight, and a skipped refresh can
   leave it saying that forever. The page already knows when a job is running — use that. While in the
   same file, only show the "no data yet" message when the data really has never been saved.
3. **Change the date in the J-05 check script before it is replayed.** It uses 10 November 2010, and this
   round used that day up. The next replay would fail for a reason that has nothing to do with the app.
4. **Plan the two "app runs out of memory" events together, not separately.** One health check went
   unanswered for ten seconds during a data job, and after a later out-of-memory error the app kept saying
   "Ready" while four pages returned errors and would not shut down cleanly. These are the same underlying
   problem and they are what keeps J-07 "Heavy aggregates never take the service down" open.
5. Small, already written down: a comment in `apps/backend/app/models.py` still says the saved calendar can
   never be served late, which is now the opposite of what the app does; `/api/regime-history` was measured
   at 1.2-3.0 seconds on a busy machine against a 1.5-second promise and should be measured again on a
   quiet one before it becomes the next slow page; and one test file has now failed to finish four times in
   a row while another test written this round has never run at all — both are ticketed in
   `docs/test-infra-tickets.md`.
6. Capture only, never a round's goal: five of the eight walkthrough frames recorded this round are the
   same picture, and four browser-check rows share one screenshot that shows neither the calendar nor the
   notice they claim to prove. Re-record as a passenger task.
7. Carried, untouched: iter-29/b and the badge wording after a permanently failed warm-up (30th round
   unmade); iter-31/e; iter-32/f; iter-35/k; iter-36/n; iter-37/o; iter-37/q; iter-39/u; iter-46/az;
   iter-46/ba; iter-47/bd; iter-47/bf; iter-47/bi; iter-48/bj. The Regime Lab item (iter-33/g) is deferred
   a twenty-third time.
8. **For the owner — two decisions, asked at rounds 50, 51, 53, 54, 55, 56 and now 57, still unanswered.**
   (a) May a future round move the heavy calculation into its own separate process? Every remaining piece
   of evidence points to this being the only lever left for J-07. (b) Does the twenty-minute limit on a
   data job's finishing work apply while the app is also serving people, or only when it is idle? One more
   thing you should know: during this round's drills, one click on the "Fetch real EOD prices" button made
   591 live requests to an outside data service. Nothing was saved from it and no other job used anything
   but the committed offline data, but that button is not allowed to be used during checks, and a rule was
   written this round to stop it happening again.

The single sentence to act on: approve full depth for the next round and answer decision (a) — whether the
heavy calculation may run in its own process — because that is the only thing standing between J-07 and a
pass.
