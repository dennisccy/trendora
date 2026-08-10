# Iteration 56 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

This round did what it promised. The two slow screens' data calls are genuinely fast again: the run
list went from 3.2-7.5 seconds to about a quarter of a second, and the data-availability chart went
from 15-21 seconds to under a tenth of a second. I checked both by hand — in the code, in the
database, and in the picture the test took — and they hold. But J-06 "Pages load only what they need"
still does not pass, because two other measurements on the same list are still over their promised
limit and nobody looked at them this round. And while checking the new caching, I found a problem no
report mentioned: while a data job is running, the availability chart on the Data page will say
"There are no stored trading days to chart. Fetch real EOD prices" — on a database holding 3.3
million rows. That message is untrue, it lasts as long as the job (about twenty minutes), and it was
introduced by this round's own fix. The round also ran at the wrong depth: its own plan asked for the
deep pipeline and the engine ran the shallow one, so the audit stage — the one that catches this kind
of thing — never ran, for the second time in three rounds.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | `reports/qa/goal-ops-hardening-iter-56-evidence/J-01-verify.png` (replay UT-J-01 PASS); sqlite `data_provider_runs` id 366 (19 of 28) + id 367 (0 of 2, weekend) |
| J-03 No per-run range cap | passing | passing | `reports/qa/goal-ops-hardening-iter-56-evidence/J-03-verify.png` (replay UT-J-03 PASS); sqlite id 368 — 283 trading + 129 non-trading = 412 calendar days |
| J-04 Non-blocking boot with visible status | passing | passing | `reports/qa/goal-ops-hardening-iter-56-evidence/J-04-verify.png` (replay UT-J-04 PASS, step 2 `data-state="ready"` held — no overturn needed this round) |
| J-05 Aggregates are precomputed at ingest | partial | partial (not re-verified — out of this iteration's target and required set) | iter-55 evidence carried: `reports/qa/goal-ops-hardening-iter-55-evidence/J-05-verify.png` |
| J-06 Pages load only what they need | partial | partial (two of four over-budget readings closed) | `reports/qa/goal-ops-hardening-iter-56-evidence/J-06-result.png` (merged UT-J-06 PASS); `reports/perf-budgets.md` Addendum 20; sqlite `availability_cache` (1 row, 5,391 cells) |
| J-07 Heavy aggregates never take the service down | partial | partial (not re-verified — explicitly out of scope) | iter-55 evidence carried: `reports/qa/goal-ops-hardening-iter-55-evidence/J-07-verify.png` |
| J-08 Backtest evidence serves from storage only | passing | passing | `reports/qa/goal-ops-hardening-iter-56-evidence/J-08-verify.png` (replay UT-J-08 PASS; opened by me — as-of 2026-08-03, Ready, survivorship disclosure) |
| J-09 The backend discloses its own background-compute activity | passing | passing | `reports/qa/goal-ops-hardening-iter-56-evidence/J-09-verify.png` (replay UT-J-09 PASS) |

Shape: **5 passing / 3 partial / 0 failing**, unchanged for the third round running. No journey newly
passing, none newly failing, none regressed. No `browser-infra.json`, no `journeys-changed.md`; all
eight `spec_hash` values match `goal_gate.py hash-journeys`, run by me.

### Why J-06 is still `partial`

My own iter-54 record lists **four** over-budget readings as J-06's gap, not two. Two are now closed
and I verified both myself:

- `/api/runs` — `apps/backend/app/api/runs.py:38-44` now issues ONE `GROUP BY ScannerResult.run_id`
  query instead of one `COUNT` per stored run. Measured 216-433 ms in the real browser, 1.010-1.229 s
  by curl. Was 3.2-7.5 s.
- `/api/data/availability` — served from one indexed `availability_cache` row. Measured 90 ms in the
  browser, 0.014-0.402 s by curl. Was 15.1-21.2 s. I read the row in sqlite: stamp
  `r2945-rc2945-b2026-08-03-bc3306390-h200`, 5,391 cells, `total_symbols=591`, last cell 2026-08-03 —
  the database's own newest bar date. `J-06-result.png` shows the heatmap with real coloured cells.

Two remain, untouched this round:

- `GET /api/health` — measured **241/243/245 ms** in this round's own browser run and **0.16 s** at
  rest in the developer's own pre-handoff check, against a committed **≤0.1 s** ceiling that the
  owner's 2026-07-31 amendment explicitly kept binding for steady-state reads.
- `/api/stocks/AAPL/bars?through=latest` — last measured 6.2 s (Addendum 18); not re-measured this
  round, so its status is unknown rather than fixed.

Step 2 of J-06 asks the iteration to "assert every measurement is within budget". Two of four is real
progress, and I say so plainly, but it is not that assertion.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 proven/confident claims need a ledger entry | OK | Grepped every added line of the backend diff for `proven` / `certified` / `alpha`: no matches. The diff adds a cache table and changes a query plan; no evidence-status surface touched. |
| AG-2 decision-quality only | OK | No return promise, price target, buy/sell signal or order path in the 7-file diff. |
| AG-3 displayed numbers correct | **Minor violation (new)** | The numbers themselves are right: `n_stocks` byte-identical across all 2,945 stored runs (0 mismatches), cache payload `==` a live `compute_availability`. But during any ingest that lands a bar or a snapshot the availability chart displays "No availability yet — There are no stored trading days to chart" (`components/availability-heatmap.tsx:230-238`) on a 3.3M-row database. A wrong status message, not a wrong number — scored minor, and the call is logged in `assumptions.md`. |
| AG-4 no overfit edges | OK | Nothing in this diff surfaces or re-labels a pattern as proven. |
| AG-5 determinism / no-lookahead | OK | `compute_availability` is byte-unchanged and the cache stores its output verbatim; the stamp is derived from stored bars and stored runs only. No forward-looking input added. |
| AG-6 referee gate | OK | `docs/goal.md` loop mechanics: J-01…J-06 carry no Evidence Claims, so the post-decompose referee gate passes automatically. |
| AG-7 no hard-coded credentials | OK | `iter-56/scan-report.md`: **CLEAN** — no secret, dependency or license finding on added lines. |
| AG-8 resilience / no unbounded loads | **Minor violation (new)**, otherwise strongly positive | This iteration REMOVES an unbounded full-history `GROUP BY daily_prices.date` from a request path — exactly what AG-8 asks for, and `_availability_not_yet_computed_payload()` issues zero queries. The graceful-degradation half is what fails: the honest-empty fallback renders as a false "no data, go fetch prices" message (see AG-3 row). |
| AG-9 offline-deterministic ingest | OK | Checked at the row level by me: `select distinct provider from data_provider_runs where id>=360` returns exactly `[('seed',)]`. No new dependency or network call — no manifest, lockfile or LICENSE file appears anywhere in the diff or the working tree. |
| AG-10 host resource ceiling | OK | Checked at the source by me: `git status --porcelain` AND `git diff --stat` over all five frozen paths (`config.yaml`, `host-guard.env`, `start-backend.sh`, `dev.sh`, `start-frontend.sh`) are BOTH empty. `config.yaml:1363-1364` still reads 8192 / 2. `logs/backend.log` records `host-guard: cpu_list=0-15 blas_threads=8` on this round's launches. |

Ledger after this round: **131 total, 61 unresolved, 0 unresolved critical.** One closed (J-05's
single-use golden date, rotated and re-verified). Eight new, all minor: the availability empty-state
message; the depth mismatch; the browser lane's "all within budget" claim over its own 241 ms health
reading; `test_api_runs.py`'s full file never completing; `persisted_this_call=True` after a rolled-back
commit; Addendum 20's "1996-2026" label against a calendar that starts 2005-02-25; the new J-06 golden
being heading-only; and the MCP `list_runs` duplicate the coherence auditor raised.

## Pipeline health

`coherence.md` = **COHERENCE-WARN** (no blocking violation; one advisory — `app/mcp/tools.py:706-731`
still uses the per-run COUNT loop the router just dropped). Not a veto. Review =
**PASS_WITH_NOTES**, `definition_of_done: complete`, `scope_creep: none`, 1 MINOR + 1 NOTE. Merged
browser QA = **PASS 6/6**; deterministic replay = **PASS 5/5**, no overturns, all six screenshots
distinct (hashed by me). Audit, QA, closure, demo and ux-regression **did not run** — lean depth.
`status.json` is stale at `in_progress` / `dev_complete` / `next_action: reviewer`, written 05:00,
while the lane finished at 06:17.

Lane-ordering rule (TC-11) **held, fourth round running** and I re-derived it: newest product-code
mtime 04:34:48, newest touched test 05:18:33, earliest lane artifact 06:03:08;
`find apps/backend/app apps/frontend -newermt '2026-08-10 06:03:00'` returns nothing.

Memory check: `logs/backend.log` holds **8,104** `MemoryError` lines — byte-identical to iter-54's and
iter-55's counts, so **zero new MemoryErrors this round**, and no abort/isolation line carries a
2026-08-10 date.

## Verdict reasoning

**Rejected REGRESSION (C.1):** no journey moved `passing`/`already_passing` → `failing`. J-05, J-06
and J-07 were already `partial` and keep it. No violation meets the critical list: the scan is CLEAN,
no manifest/lockfile/LICENSE is touched, both AG-10 checks are empty, every ingest row reads `seed`,
and no market number is wrong — I compared the cache payload against the database's own bar range and
the rendered heatmap. The new availability message is a false *status*, not fabricated data; I
considered failing it closed to critical and scored it minor, and I say so rather than bury it.

**Rejected STALLED (C.2):** almost nothing here is human-owned. The false empty-state message is a
few lines (serve the previous row with an "as of" marker, or an explicit computing state); the health
endpoint's per-call database work is named and unprofiled; `/api/stocks/AAPL/bars` has never been
measured once; the J-06 golden needs real assertions; the MCP duplicate has a named finite fix. Two
questions remain genuinely the owner's, and owner items among many agent items are not a stall.

**Rejected GOAL_ACHIEVED (C.3):** three journeys are `partial`.

**Chose ESCALATE (C.4).** Its third clause fires plainly and mechanically: this was a **lean**
iteration (`iter-56/depth-dispatched` = `lean`) — run against its own spec's `**Depth:** full` with an
explicit "Full trigger: 1" justification — **and it surfaced cross-cutting complexity no lane
reported**: a fix that spans the engine (`data_manager.availability_from_storage`), the API
(`api/data.py`) and the frontend widget (`availability-heatmap.tsx`) leaves a user-visible untrue
message on screen for the length of every ingest job, and a new golden was written that would report
J-06 PASS forever without measuring a budget. ESCALATE's only mechanical effect is to pin the next
round to full depth. This session has now shown twice that a depth *recommendation* is not honoured
(iter-55 recommended full on the merits; iter-56 was dispatched lean anyway) while an ESCALATE
*mandate* was (iter-54 → iter-55). That is precisely the lever this round needs.

## Five things I state plainly rather than round away

1. **This round delivered, and I verified all of it in the source rather than in the handoff.** The
   profile came before the fix, both hypotheses were confirmed exactly, the N+1 is gone, the cache row
   exists and is honest, `J-05.json` was rotated to a date I confirmed has zero rows, AG-9 and AG-10
   were re-checked at the row and source level, and the lane-ordering rule held a fourth round.
2. **And the scoreboard still did not move — third round running.** J-06's gap list had four items;
   this round closed two, and the plan never named the other two.
3. **The round's own fix introduced a new untruth on screen**, and no lane caught it, because the lane
   that would have — the audit — did not run. Every browser check ran against a warm, idle system; no
   check has ever loaded `/data` during a job.
4. **The report honesty stayed high.** The developer disclosed the unfinished test file, kept the
   residual 1.0-1.2 s on `/api/runs` visible rather than rounding it, and disclosed a concurrent
   pytest process rather than calling the measurement clean. The reviewer filed the unfinished tests as
   MINOR. The coherence auditor found the MCP duplicate on its own.
5. **The browser lane wrote "All within budget" over its own 241 ms health reading** against a 100 ms
   committed ceiling. That single sentence is the difference between J-06 reading as done and J-06
   reading as two-thirds done.

## Next-Step Recommendation

FULL depth (mandatory, via ESCALATE). Give the next round this order.

1. **Stop the Data page from telling the user there is no data while a job is running.** Right now,
   the moment a data job saves its first price row, the availability chart empties and says "There are
   no stored trading days to chart. Fetch real EOD prices" — and it says that for the whole job, about
   twenty minutes. Show the previous chart with an honest "as of <date>" note, or an explicit
   "updating" state. This is small, it is on screen, and this round created it.
2. **Close the last two over-budget page calls, so J-06 can actually pass.** The health check answers
   in about a fifth of a second against a promised tenth — it still does real database work on every
   call, which has been written down since round 54. And the single-stock price call was last measured
   at 6.2 seconds and has not been measured since. Measure both first, then fix.
3. **Give the J-06 check script real teeth.** The one written this round only checks that each page
   shows its title. It must also assert the two fixed calls stay under their limit, or it will report
   success every round while measuring nothing.
4. **Finish the one test file that did not finish**, on its own, early in the round, before anything
   else runs — the same treatment last round gave its own slow file.
5. **Run the round at the depth its own plan asks for.** This round's plan said deep and the engine ran
   shallow, so the audit never happened — for the second time in three rounds — and this round's real
   defect reached me unreported.
6. SMALL AND ALREADY WRITTEN DOWN: the tool-side run list still uses the slow one-query-per-run loop
   the web side just dropped (`app/mcp/tools.py:706-731`); a cache write that fails can still be
   recorded as if it succeeded; the measurement note labels a 2005-2026 calendar as 1996-2026.
7. CARRIED, untouched: iter-29/b + the badge wording after a permanently failed warm-up (29th round
   unmade); iter-31/e; iter-32/f; iter-35/k; iter-36/n; iter-37/o; iter-37/q; iter-39/u; iter-46/az;
   iter-46/ba; iter-47/bd; iter-47/bf; iter-47/bi; iter-48/bj. Deferred a TWENTY-SECOND time:
   iter-33/g, the Regime Lab.
8. CAPTURE ONLY, never a round's goal: no walkthrough exists for J-04, J-05, J-06 or J-07 — the demo
   stage does not run at shallow depth and the recorder script bug is still unfixed.
9. OWNER: two decisions and three facts. The decisions, asked at rounds 50, 51, 53, 54, 55 and 56 and
   still unanswered — (a) may a future round move the heavy calculation into a separate process?
   (b) does the twenty-minute limit on a job's finishing work apply while the app is also serving
   people, or only when it is idle? The facts — the run list and the availability chart are genuinely
   fast again, proven three ways; nothing ran out of memory this round for the first time in a while;
   and one line in a test report ("all within budget") is currently the only thing standing between
   J-06 reading as finished and J-06 reading as two-thirds finished. If you would rather I treat the
   browser lane's PASS as binding, say so in one sentence and J-06 becomes green next round.
