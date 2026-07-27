# Iteration 28 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

This iteration had one job: finish the browser checks that iteration 27 could not finish, because its
testing agent was stopped part-way by an account usage limit. That job is done. All four journeys that were
missing proof — J-05 "Aggregates are precomputed at ingest, never on the fly", J-06 "Pages load only what
they need", J-07 "Heavy aggregates never take the service down" and J-08 "Backtest evidence serves from
storage only" — now have fresh screenshots and passing test rows, and the other four journeys were replayed
and still pass. All eight journeys pass. The goal is still not finished, because one earlier problem is
still open: on the Evidence page the backend can run out of memory when it reads the whole forward-returns
table into memory at once. That problem was deliberately left for the next round, so the loop continues.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | reports/qa/goal-ops-hardening-iter-28-evidence/J-01-verify.png (replay row UT-J-01 PASS) |
| J-03 No per-run range cap | passing | passing | reports/qa/goal-ops-hardening-iter-28-evidence/J-03-verify.png (replay row UT-J-03 PASS; spot-checked) |
| J-04 Non-blocking boot with visible status | passing | passing | reports/qa/goal-ops-hardening-iter-28-evidence/J-04-verify.png (replay row UT-J-04 PASS) |
| J-05 Aggregates are precomputed at ingest, never on the fly | unknown | **passing** | reports/qa/goal-ops-hardening-iter-28-evidence/J-05-scanner-run-2018-02-15.png, J-05-cold-data-restart.png (row UT-J-05 PASS) |
| J-06 Pages load only what they need | partial | **passing** | reports/qa/goal-ops-hardening-iter-28-evidence/J-06-dashboard-market-regime.png (row UT-J-06 PASS, 11/11 steps) |
| J-07 Heavy aggregates never take the service down | unknown | **passing** | reports/qa/goal-ops-hardening-iter-28-evidence/UT-05-backtest-latest.png, UT-02-UT-08-stale-coverage.png (row UT-J-07 PASS) |
| J-08 Backtest evidence serves from storage only | unknown | **passing** | reports/qa/goal-ops-hardening-iter-28-evidence/UT-06-backtest-2018-03-15.png, UT-07-backtest-already-scanned.png (row UT-J-08 PASS) |
| J-09 The backend discloses its own background-compute activity | passing | passing | reports/qa/goal-ops-hardening-iter-28-evidence/J-09-verify.png (replay row UT-J-09 PASS; spot-checked) |

Skipped, recorded as an open gap: **UT-04** (the coverage panel's "not yet computed" state, a P3 sub-case of
J-05's Definition of Done) — unreachable on this database, which already holds 1872+ snapshot rows. It is
not one of J-05's four steps in `docs/goal.md`; the interpretation call is written down in
`runs/goal-session-ops-hardening/state/assumptions.md`.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 no unproven "proven" claims | OK | No claim language added. `UT-05-backtest-latest.png` shows the honest empty state: every horizon "— n=0" plus the printed line "No numbers are fabricated to fill the gap." |
| AG-2 decision-quality only | OK | No order, price-target or signal surface touched. Every capture's header still reads "Research-only · decision support · no orders". |
| AG-3 displayed numbers must be correct | OK | Checked against the database read-only: scanner run 1872 = 2018-02-15 / Risk-on / 75.13 / scanned 18:48:35.232536 matches `J-05-scanner-run-2018-02-15.png`; run 1873 = 2018-03-15 / Risk-on / 74.82 matches `UT-06-backtest-2018-03-15.png`. |
| AG-4 no overfit edges | OK | No pattern or claim was surfaced this iteration. |
| AG-5 determinism / no lookahead | OK | No engine file is in the diff. The only product change is one config path string in `config.yaml:1152` and `apps/backend/app/config.py:2286`. |
| AG-6 referee gate on evidence claims | OK | No evidence-derived claim shipped. |
| AG-7 no hard-coded credentials | OK | `runs/goal-session-ops-hardening/iter-28/scan-report.md` = CLEAN; I also read every changed line of the diff. |
| AG-8 resilience to deeper data | **OPEN — 1 carried, minor, unresolved** | `apps/backend/app/engine/research.py:207-217` still builds an unbounded `ret_by_run_symbol` dictionary over the whole `forward_returns` table (3,964,725 rows per this run's own Storage-footprint panel). Untouched here on purpose (iter spec "OUT OF SCOPE"). **No recurrence this window:** last MemoryError lines are `logs/backend.log:82012`/`:82063` and last ASGI-exception lines `:81850`/`:81932`, all before this iteration's first boot banner at `:82101`; from there to the file end at 83431 there are zero of either and zero non-200 responses. |
| AG-9 offline-deterministic ingest | OK | Every capture carries the "provider: seed" badge; the database rows record `provider = 'seed'`; no dependency manifest changed. |
| AG-10 host resource ceiling | OK | `scripts/` is absent from the diff. The developer ran pytest under `taskset -c 0-3,8-11` with BLAS/OMP caps; testing restarted the backend only through `scripts/start-backend.sh`. |

Coherence: `runs/goal-session-ops-hardening/iter-28/coherence.md` = **COHERENCE-PASS** (no blocking
violation; one cosmetic documentation-lag note). No `journeys-changed.md` and no `browser-infra.json` exist
for this iteration. All eight recorded `spec_hash` values match a fresh
`goal_gate.py hash-journeys docs/goal.md` run. Review verdict: PASS, with browser results present — no
fail-open signal.

## Next-Step Recommendation

Run the next iteration at **full** depth with one blocking job: stop the Evidence page from loading the
whole forward-returns table into memory at once (`apps/backend/app/engine/research.py:215`), and make
`GET /api/evidence` show an honest reduced result instead of failing, so a person never sees a broken page.
The same code also breaks the background job that finishes an import (`data_manager.py:3361`). Full depth is
right because this change puts a new message in front of the user, which `docs/goal.md` itself names as the
trigger for full depth, and because it needs the extra review, look-and-feel and closure checks.

Smaller jobs to fold into the same round: replay the corrected `J-06.json` script through the automatic
replay lane once, so that check runs by machine and not only by hand; write down that the test selector
`test_readiness.py -k drift` is NOT cheap — it pulled the 30-year data fixture and took 1 hour 37 minutes;
either build a genuinely empty test database for the skipped UT-04 check or write down that it is waived;
and ask the testing agent to report the real number of requests it fired, plus each one's `write_taken`
flag, whenever it claims a result about two things happening at once.

Still carried and unchanged: audit item B2 (the leftover rollback inside `_backfill`), and retargeting the
four `is_latest` patches in `test_forward_testing_serving_split.py` before the unused imports at
`backtest.py:75` and `mcp/tools.py:38` are removed.

For the owner, nothing blocking: opening the Backtest page on a historical date that has never been scanned
took 206 and 273 seconds in this run — much better than last round's 12 to 24 minutes, but still slow, and
there is still no written time limit for it. Backlog card B-1107 stays optional.

One sentence for approval: let the next round go ahead at full depth to fix the Evidence page's
out-of-memory problem, and nothing else needs your decision right now.

## Halt Justification (if halting)

Not halting.
