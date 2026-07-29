# Iteration 31 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

This iteration had one job, and it did it. The Factor Lab page — the one that showed an error box
instead of numbers for the last two iterations — now loads and shows real figures for all 11 factors.
I checked this myself in the backend log rather than trusting the report: zero out-of-memory errors
after this run's own start-up line, and 23 successful page requests. Both remaining journeys, J-06
"Pages load only what they need" and J-07 "Heavy aggregates never take the service down", are still
partly done. Neither got worse. J-06 closed a long-standing missing-test-record gap; J-07's own main
promise still rests on a piece of code this iteration deliberately did not touch.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range | passing | passing | reports/phase-goal-ops-hardening-iter-31-regression-replay-results.md (UT-J-01 PASS) + reports/qa/goal-ops-hardening-iter-31-evidence/J-01-verify.png (opened — spot-check 1 of 2) |
| J-03 No per-run range cap | passing | passing | same replay file (UT-J-03 PASS) + .../J-03-verify.png (md5 eff8f9ad — byte-identical to J-04/J-07) |
| J-04 Non-blocking boot with visible status | passing | passing | same replay file (UT-J-04 PASS) + .../J-04-verify.png (md5 eff8f9ad — no independent capture) |
| J-05 Aggregates precomputed at ingest | passing | passing | same replay file (UT-J-05 PASS) + .../J-05-verify.png |
| J-06 Pages load only what they need | partial | **partial** | reports/phase-goal-ops-hardening-iter-31-j06-ridealong-replay-results.md (UT-J-06 PASS, 11/11 steps) + .../J-06-verify.png (opened) + .../TC-1-factor-lab-all-factors.png (opened) |
| J-07 Heavy aggregates never take the service down | partial | **partial** | reports/phase-goal-ops-hardening-iter-31-j07-ridealong-replay-results.md (UT-J-07 PASS, 2 steps) + .../J-07-verify.png (opened — capture defective) |
| J-08 Backtest evidence serves from storage only | passing | passing | same replay file (UT-J-08 PASS) + .../J-08-verify.png (opened — spot-check 2 of 2) |
| J-09 Backend discloses background compute | passing | passing | same replay file (UT-J-09 PASS) + .../J-09-verify.png |

Newly passing: none. Newly failing: none. Regressed: none. Unknown: none.
No `journeys-changed.md` and no `browser-infra.json` exist for this iteration; all 8 recorded
`spec_hash` values match `goal_gate.py hash-journeys docs/goal.md` exactly, so no goal-edit drift.

## Anti-goal Check

Worked from `runs/goal-session-ops-hardening/iter-31/scan-report.md` (CLEAN) and `iter-diff.md`
(5 product files: `research.py`, `config.py`, `config.yaml`, 2 test files — no frontend file at all).

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 unproven values must read "not yet proven" | OK | I opened TC-1-factor-lab-all-factors.png: every one of the 11 factors carries a "Not yet proven" chip at every horizon. No proven-language added. |
| AG-2 decision-quality only | OK | No return promise, target, or order path in the diff. Page copy still reads "Descriptive evidence, not a predictive model". |
| AG-3 displayed numbers correct | OK | Byte-identity is pinned by `test_shared_pools_chunked_equal_the_pinned_unchunked_reference` against the untouched pre-fix oracle; the dev handoff's two independent cold-MISS runs returned byte-identical 117,289-byte bodies; browser-qa cross-checked the rendered table against a raw curl of the same endpoint. |
| AG-4 no overfit edges | OK | No referee/ledger code in the diff; no claim promoted. |
| AG-5 determinism / no lookahead | OK | Same byte-identity oracles; the change is a memory representation, not a date or filter change. |
| AG-6 evidence claims need a referee verdict | OK | No evidence-derived claim introduced (spec: ops/performance work, no Evidence Claims). |
| AG-7 no hard-coded credentials | OK | scan-report.md: CLEAN, no secret findings on added lines. |
| AG-8 data-scale resilience | **1 finding CLOSED, 4 open (all minor)** | **Closed:** iter-29/a, the Factor Lab crash — verified below. **Open:** iter-29/b `warmup.py:194`; iter-29/c `stock_obs` at `forward_testing.py:988`; iter-29/d `prices.py:141` whole-table `daily_prices` prefill — all three untouched by this diff and deliberately deferred by the spec. **New:** iter-31/e — the fix is a 2.63x constant-factor reduction, not a bound (audit B2), so the same crash class returns at ~2.5–3x today's data scale. |
| AG-9 offline-deterministic ingest | OK | `git diff --stat` over `requirements.txt`, `pyproject.toml`, `package.json`: empty. No network call added. |
| AG-10 host resource ceiling | OK | `git diff --stat -- scripts/ project-extensions/`: empty. No launch script or host-guard value touched. Dev and reviewer both ran pytest under `taskset -c 0-3,8-11` with BLAS caps. |

**Why the open AG-8 findings stay `minor` and not `critical`.** Nothing crashed this run: I counted
`MemoryError` in `logs/backend.log` from this run's own start-up line 132546 to the end and got
exactly 0, with the file's last such error at line 132302 belonging to an earlier process. The page
renders real numbers. The three carried findings did not fire. This is the same reading iterations
26 through 30 used and it has not been overruled. A person who reads "exhaust a service's memory"
literally would call the residual scale limit critical, which would mean stopping for a human review
instead of another agent iteration.

## Coherence

`runs/goal-session-ops-hardening/iter-31/coherence.md`: **COHERENCE-PASS**. No blocking violation.
It independently confirms the byte-frozen functions show zero diff and that no new page, route, nav
entry, or second computing path was introduced.

## Pipeline Health

Review PASS (after one fix round that correctly rejected a 45-second wait against a 300-second
compute). Audit PASS_WITH_GAPS. UX regression PASS. Closure gate CLOSURE-PASS. The merged
`ui-test-results.md` (PASS 9/9) does **not** disagree with its `.llm.md` source this time — I
compared them. The row-id merge bug that hid a failure at iteration 30 did not fire, because
browser-qa used `UT-` ids. That framework bug is still unfixed and still needs fixing before any
final success run.

## Five things I state plainly rather than round away

1. **The frontend is served by `next dev`, not a production build.** `scripts/start-frontend.sh`
   line 28 runs `npx next dev`, and `ps aux` confirms `next dev -p 3255` is the process serving
   every screenshot in this iteration. J-06 step 1 names that exact script as the "prod mode"
   launcher. Next.js dev mode builds pages on demand, so any page-speed number measured through it
   is a development-build number, not a real one. J-06's never-run speed sweep is the one remaining
   piece of that journey, and running it as things stand would produce numbers that mean nothing.
   Nobody has flagged this in 31 iterations.
2. **The QA report claims "zero console errors", and its own screenshot shows a red "1 error"
   badge.** I saw the badge in `TC-1-factor-lab-all-factors.png` before reading the audit; the
   auditor found the same thing (F1) and could not reproduce it across two clean browser sessions.
   In the backend log I found a likely cause: two requests to `/research/factor-lab?all=true`
   **without** the `/api` prefix, both answered 404. That is a small, pre-existing frontend stray
   request, not something this iteration caused — but the Definition of Done asks for zero console
   errors, and that box is not cleanly ticked.
3. **The memory fix is headroom, not a bound, and the audit measured it.** 769 MB projected versus
   2,025 MB before, at the live data size — a 2.63x reduction. All five horizons are still held in
   memory at once. The same failure returns at roughly 2.5 to 3 times today's data. The spec asked
   for this to be recorded honestly instead of called "fixed", so it is now its own open finding.
4. **The QA report declared PASS before two of its own blocking checks had run** (audit T2): it
   marked the six required journeys and the J-06 replay "PENDING / deferred" and substituted an
   expectation. The replays did run afterwards and did pass — I opened both artifacts — but the
   verdict was written ahead of its evidence.
5. **J-03, J-04 and J-07's screenshots are the same file** (md5 `eff8f9ad`) — the 11th recurrence,
   independently caught by the audit (T3), and this time the spec had explicitly instructed
   browser-qa to check for it. So three journeys have no picture of their own this run, and J-07's
   "picture" shows the top of the Data page rather than the panel its test actually checked.

## Next-Step Recommendation

Run the next iteration at **full** depth. In order:

1. **Fix the memory problem in the background aggregate job.** The code called `stock_obs` inside
   `forward_testing.py` (line 988) still builds one giant list in memory. This is the last piece
   standing between J-07 "Heavy aggregates never take the service down" and a clean pass, and it has
   been deferred three times. Doing it means deliberately changing a function signature that several
   tests currently pin, so the planner must say so out loud rather than let it happen by accident.
   While in there, write down the job's peak memory and how far it sits below the declared limit in
   `reports/perf-budgets.md` — J-07 step 3 has never been done.
2. **Settle how the frontend is started before measuring page speed.** Either change
   `scripts/start-frontend.sh` to build once and serve the built site, or write into the goal that
   the speed numbers are development-mode numbers. Until that is decided, J-06 "Pages load only what
   they need" cannot honestly finish, because its one remaining step is a page-speed measurement.
3. **Then run J-06's page-speed sweep over all 11 pages in a real browser and write the numbers into
   `reports/perf-budgets.md`.** That file was not touched this iteration even though the data path
   changed, which J-06's own wording asks for.
4. **Track down the stray request** to `/research/factor-lab?all=true` with no `/api` prefix that
   returns 404 and puts an error badge on the page. Small, but it is the only thing keeping the
   Factor Lab page from being clean.
5. **Carried, unchanged:** the start-up warm-up failure (`warmup.py:194`) and the whole-table price
   scan during data refresh (`prices.py:141`); deciding what the status badge should say if start-up
   work fails for good; the report-merging bug that can hide a failure; the fresh-install database
   case (UT-04); the four `is_latest` test patches in `test_forward_testing_serving_split.py`.
6. **For the owner, not blocking:** the health check measures 0.128 seconds against a 0.1 second
   budget. Until that line is amended or re-scoped, J-06 and J-07 can never both say "every
   measurement is within budget". There is no agent fix for this.

In one sentence: the next round should fix the last memory hot spot in the background aggregate job
and decide how the website is started before measuring page speeds, then measure them.
