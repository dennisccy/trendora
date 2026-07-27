# Iteration 27 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

This iteration fixed the two problems the last round flagged, and the code fixes look right. But the
browser check that was supposed to prove them was cut off part-way by an account usage limit. So the three
journeys this iteration exists to fix — J-05 "Aggregates are precomputed at ingest", J-07 "Heavy aggregates
never take the service down", and J-08 "Backtest evidence serves from storage only" — have no test result
at all this round. They are marked "not known" rather than pass or fail. Five other journeys were replayed;
four passed, and the one that reported a failure (J-06 "Pages load only what they need") failed on a stale
line in its own test script, not on anything the product does. Separately, the app ran out of memory twice
while serving the Evidence page during this round's own testing.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | `reports/phase-goal-ops-hardening-iter-27-ui-test-results.md` (UT-J-01 PASS) + `reports/qa/goal-ops-hardening-iter-27-evidence/J-01-verify.png` (opened: /data shows 1996-01-02 → 2026-07-22, universe 540, 1869 snapshot dates) |
| J-03 No per-run range cap | passing | passing | UT-J-03 PASS + `reports/qa/goal-ops-hardening-iter-27-evidence/J-03-verify.png` (byte-identical to J-01's — known capture nit, 7th recurrence) |
| J-04 Non-blocking boot with visible status | passing | passing | UT-J-04 PASS + `reports/qa/goal-ops-hardening-iter-27-evidence/J-04-verify.png`; corroborated by "Ready" badge in every capture and continuous `GET /api/health` 200s in `logs/backend.log` |
| J-05 Aggregates are precomputed at ingest | passing | **unknown** | No row in `reports/phase-goal-ops-hardening-iter-27-ui-test-results.md`; `reports/qa/goal-ops-hardening-iter-27-evidence/UT-01-data-page-top.png` opened — shows only the loading skeleton. Dev self-verification exists: `runs/goal-ops-hardening-iter-27/coverage-stale-panel.png` (opened; real figures + stale label) |
| J-06 Pages load only what they need | passing | **partial** | UT-J-06 FAIL ("step 01 expected DEGRADED did not appear") + `reports/qa/goal-ops-hardening-iter-27-evidence/J-06-verify.png` (opened: healthy dashboard, banner "GO — today's board is current.") |
| J-07 Heavy aggregates never take the service down | passing | **unknown** | No row in the merged results file; TC-2's full-page race capture does not exist. `reports/qa/goal-ops-hardening-iter-27-evidence/UT-05-backtest-latest-fullpage.png` opened — genuine full-page /backtest, but the latest view, not the historical race |
| J-08 Backtest evidence serves from storage only | passing | **unknown** | No row in the merged results file; none of J-08's own steps were exercised |
| J-09 The backend discloses its own background-compute activity | passing | passing | UT-J-09 PASS + `reports/qa/goal-ops-hardening-iter-27-evidence/J-09-verify.png` (opened: badge reads "background compute running (1)") |

## Anti-goal Check

Worked from `runs/goal-session-ops-hardening/iter-27/scan-report.md` (CLEAN) and
`runs/goal-session-ops-hardening/iter-27/iter-diff.md`, plus my own `git diff HEAD -- apps/ scripts/
project-extensions/ config.yaml` (7 files: 2 engine, 3 backend tests, 2 frontend) and `git status
--porcelain` (no untracked product files).

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials (AG-7) | OK | scan-report CLEAN on added lines; no new config/env file in the 7-file list |
| Paid / external SaaS (AG-9) | OK | No manifest changed (`package.json`, `requirements*.txt`, `pyproject.toml` all absent from the diff); no new adapter or network call; every capture shows `provider: seed` |
| License changes | OK | scan-report CLEAN; no LICENSE or license-field file in the diff |
| Fabricated / substituted data (AG-3) | OK **and one iter-26 finding CLOSED** | The audit caught and fixed a real fabrication risk in the first cut of the AG-8 guard (a transaction-wide rollback destroyed earlier rows while still counting them, so `/data` could read "2 forward returns inserted" with 0 persisted) — fixed via accumulating `staged_keys`, with a new regression test. The iter-26 all-zero coverage panel is closed: I opened `coverage-stale-panel.png` and the panel now shows real figures under the label "Coverage as of a prior scan (version r1868-…) — refreshes on the next data job" |
| AG-1 / AG-2 / AG-4 / AG-6 (proven-language, orders, overfit, referee) | OK | No evidence-derived claim, no ranking/proven copy, no order surface in the diff; the only new UI string is the coverage staleness label |
| AG-5 (no-lookahead / determinism) | OK | `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, `ensure_historical_forward_aggregates_dispatched` and J-08's serving split are untouched (confirmed in the diff); the coverage change adds no compute and persists nothing new |
| AG-8 (resilience / no unbounded loads) | **iter-26 finding CLOSED; ONE NEW MINOR FINDING, unresolved** | Closed: the concurrent `/backtest` 500 is fixed and I re-derived the live proof from `logs/backend.log` (an as_of=2015-09-09 pair, write_taken True/False, both 200; the only IntegrityError in the file is still iter-26's at `:81004`). New: two unhandled `MemoryError`s reached uvicorn on `GET /api/evidence` (`logs/backend.log:81850`, `:81932`, both after this window's boot at `:81466`), plus the same failure inside the ingest finalize path (`data_manager.py:3361`). Root cause read directly at `apps/backend/app/engine/research.py:215` — `ret_by_run_symbol` accumulates an unbounded in-RAM dict over the whole `forward_returns` scan. Pre-existing code, absent from this diff. Scored minor, not critical (see Halt Justification wording in the log entry) |
| AG-10 (host resource ceiling) | OK | `scripts/` and `project-extensions/` have zero diff, tracked and untracked; `logs/backend.log` shows the HOST-GUARD block applied at each boot marker |

Coherence: `runs/goal-session-ops-hardening/iter-27/coherence.md` = **COHERENCE-PASS** (no structural veto).
Goal-edit drift: no `journeys-changed.md`; all 8 `spec_hash` values match `goal_gate hash-journeys`.

## Next-Step Recommendation

Run one more round at full depth. No new features. In priority order:

1. **Re-run the browser checks for J-05, J-07 and J-08.** This is the only thing blocking closure. The test
   plan already exists — the missing cases are UT-02 (the /data panel showing prior-scan coverage with its
   honest label), UT-06 (two people opening the Backtest page for the same never-used past date at the same
   moment, captured as a full page, on a date not yet used — 2011-03-10 and 2015-09-09 are now consumed),
   and the regression cases UT-03, UT-04, UT-07, UT-08. Merge the rows into
   `reports/phase-goal-ops-hardening-iter-27-ui-test-results.md`-equivalent for the new iteration.
2. **Fix the J-06 test script, not the product.** Remove the "DEGRADED" line from step 1 of
   `runs/goal-session-ops-hardening/journey-scripts/J-06.json`, and move `readiness.drift.report_path` in
   `config.yaml:1152` out of another session's folder so one session's data job cannot flip another
   session's test result. Until this is done, J-06 will report a false failure every round.
3. **Stop the Evidence page from running out of memory.** `research.py:215` builds one in-memory table of
   every stored forward return before it starts filtering. Give it a bound, and make the page show a calm
   "not available right now" state instead of a server error if it still fails. This is real backend work
   and should be planned by the decomposer, not patched opportunistically.
4. **For the owner, not urgent:** opening the Backtest page on a past date that was never scanned took 12
   to 24 minutes in this round's logs, against the 16-to-23-second figure the earlier budget question was
   based on. Please decide whether that wait is acceptable or whether that work should move off the page
   load. Backlog card B-1107 (a cap on how many heavy jobs may run at once) stays optional and is related.

What should happen next: approve one more round of work whose main job is simply to re-run the browser
checks that were cut short, fix one stale test script line, and stop the Evidence page from crashing.
