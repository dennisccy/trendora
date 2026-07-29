# Iteration 32 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

This iteration fixed the biggest memory problem left in the app, and the fix is real. The part of
the code that builds the backtest evidence used to hold one record in memory for every single
observation — about 800,000 of them at once. It now keeps only small running totals. Measured on the
real data, memory use dropped from 981 MB to 170 MB, the answers it produces are identical
byte-for-byte, and the app stayed healthy through two full live rebuilds. Six journeys were re-checked
and all still pass. J-07 "Heavy aggregates never take the service down" still does not fully pass:
two of its own four checks were never carried out — nobody measured how fast the health check answers
against its written speed limit, and nobody ran the deliberate "run the app low on memory" drill.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | reports/phase-goal-ops-hardening-iter-32-regression-replay-results.md (UT-J-01 PASS) · reports/qa/goal-ops-hardening-iter-32-evidence/J-01-verify.png |
| J-03 No per-run range cap | passing | passing | replay UT-J-03 PASS (step 5 asserts "412 calendar days") · reports/qa/goal-ops-hardening-iter-32-evidence/J-03-verify.png |
| J-04 Non-blocking boot with visible status | passing | passing | replay UT-J-04 PASS · reports/qa/goal-ops-hardening-iter-32-evidence/J-04-verify.png (opened — spot-check 1 of 2) |
| J-05 Aggregates are precomputed at ingest | passing | passing | replay UT-J-05 PASS · reports/qa/goal-ops-hardening-iter-32-evidence/J-05-verify.png |
| J-06 Pages load only what they need | partial | partial (carried, not tested) | no iter-32 evidence — not a target, not in the Required-still-passing set; last evidence reports/qa/goal-ops-hardening-iter-31-evidence/J-06-verify.png |
| J-07 Heavy aggregates never take the service down | partial | partial (target) | reports/phase-goal-ops-hardening-iter-32-ui-test-results.md (UT-J-07 PASS) · reports/qa/goal-ops-hardening-iter-32-evidence/J-07-backtest-forward-aggregates.png (opened) · reports/perf-budgets.md:4023-4098 |
| J-08 Backtest evidence serves from storage only | passing | passing | replay UT-J-08 PASS · reports/qa/goal-ops-hardening-iter-32-evidence/J-08-verify.png |
| J-09 The backend discloses its background-compute activity | passing | passing | replay UT-J-09 PASS · reports/qa/goal-ops-hardening-iter-32-evidence/J-09-verify.png (opened — spot-check 2 of 2) |

## Anti-goal Check

Worked from `runs/goal-session-ops-hardening/iter-32/scan-report.md` (CLEAN) and `iter-diff.md`.
Product diff this iteration is exactly three files — `apps/backend/app/engine/forward_testing.py`,
`apps/backend/tests/test_forward_testing.py`,
`apps/backend/tests/test_forward_testing_aggregates_streaming.py` — plus `reports/perf-budgets.md`
and the `J-07.json` golden. Confirmed with `git diff --stat <snapshot>`; zero untracked product files.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets/credentials (AG-7) | OK | scan-report CLEAN on added lines; no config/env file in the diff |
| Paid/external SaaS (AG-9) | OK | no manifest touched; no new dependency; the live warms read only the committed local seed DB |
| License changes | OK | scan-report CLEAN; no LICENSE file in the diff |
| Fabricated/substituted data (AG-3) | OK | audit re-derived byte-identity at live scale: recomputing horizon 20 for `as_of=2026-07-21` (771,129 observations) yields a payload whose SHA-256 equals the row the OLD code cached for that key. I opened J-07's capture: the empty scorecard shows an honest "No elapsed forward window for this date yet" with n=0, not invented figures |
| AG-1 / AG-2 / AG-4 / AG-6 (proven-language, order placement, overfit, referee) | OK | no new claim, score, ledger entry, or UI text; frontend untouched |
| AG-5 (determinism / no-lookahead) | OK | control-group draw order preserved by construction (runs walked in the same ascending id order, one shared RNG); audit ran 30 chunked differential trials with 0 mismatches |
| AG-10 (host resource ceiling) | OK | `scripts/`, `project-extensions/host-guard/` absent from the diff; both live warms ran through `scripts/start-backend.sh` under `ulimit -v 6291456` + `taskset -c 0-3,8-11` |
| AG-8 (resilience to data-scale) | 1 CLOSED, 4 open (all minor) | **iter-29/c CLOSED** — the `stock_obs` finding this iteration targeted. Still open: iter-29/b (`warmup.py:194`), iter-29/d (`prices.py:141`), iter-31/e (Factor-Lab constant-factor residual), and one new watch item iter-32/f (`run_rows` at `forward_testing.py:1195`, run-count-proportional, developer-disclosed, explicitly not a blocker) |

Coherence: `runs/goal-session-ops-hardening/iter-32/coherence.md` = **COHERENCE-PASS**. No structural veto.
Pipeline health: review PASS_WITH_NOTES, audit PASS_WITH_GAPS, QA PASS, ux-regression UX-REGRESSION-PASS,
closure CLOSURE-PASS. No lane failed and no lane was skipped, so there is no fail-open this iteration.
No `journeys-changed.md` and no `browser-infra.json`. All eight `spec_hash` values match
`goal_gate.py hash-journeys` — `docs/goal.md` was not edited.

## Next-Step Recommendation

Run the next iteration at **full** depth and put J-06 "Pages load only what they need" first. It has
one decision blocking it that no agent should make alone: the script the goal calls the "production"
launcher actually starts the website in development mode, so any page-speed number measured through it
today would be a development-mode number, not a real one. Either change the script to build-then-serve,
or change `docs/goal.md` to say the numbers are development-mode numbers. Once that is settled, load
all eleven pages in a real browser, write the timings into `reports/perf-budgets.md`, and write the
short code-level check that no page loads more data than it needs. That closes J-06.

Second, finish J-07 "Heavy aggregates never take the service down". Two small things are left. (a) While
a heavy rebuild is running, record how long the health check takes to answer, not just that it answers —
and say plainly whether it is inside its written limit. (b) Run the deliberate low-memory drill: start a
throwaway copy of the app with a tight memory limit, start a rebuild, and show that the rebuild gives up
honestly while the same app keeps answering. Add both to the walkthrough recording as `[NEW]` steps —
the current recording has no `[NEW]` step at all.

Two things for the owner, not for an agent. First, the health check answers in about 0.128 seconds while
the written limit says 0.1 seconds. Until that line is either changed or accepted, J-06 and J-07 can
never both read fully true; the simplest fix is to record it honestly as a warning, the way the budgets
file already does elsewhere. Second, a tool in the build machinery (`merge_ui_test_results.py`) can
silently drop failures from the combined test report. It did not misfire this time — I compared the
merged file with its source and they agree — but four evaluators in a row have now flagged it, and it
must be fixed before any run that declares the goal finished.

One caution for whoever touches the J-07 test script next: it now checks for the literal number
`n=8869` on the backtest page. That number will change the moment more history is loaded, and the test
will then fail for a reason that is not a defect.

## Halt Justification (if halting)

Not halting. Nothing moved from passing to failing, no critical anti-goal violation is unresolved, and
every remaining work item has a clear owner — most of them agents, two of them the human owner and
neither of those two blocking. Two Must-have journeys (J-06, J-07) are still incomplete, so the goal is
not achieved yet.
