# Iteration 41 Evaluation

**Verdict:** ESCALATE
**Depth Recommendation For Next Iteration:** full

## Summary

This is the best iteration in six, and I want that said before the verdict is read. For the first
time in five tries, real people-facing checks ran again: six journeys were driven through a live
browser today and each left a dated picture I opened myself. Three journeys that were untested last
time are now confirmed working. Nothing broke.

But the iteration's own two main targets — J-05 "Aggregates are precomputed at ingest" and J-07
"Heavy aggregates never take the service down" — were never checked in the browser at all, and the
results file still announces a clean "PASS, 6 of 6 passed" without mentioning them. That is the same
kind of blind spot this iteration existed to remove: it was closed for the "must stay working" list
and left open for the "what we are working on" list. Separately, the safety net built this iteration
did not catch last iteration's actual failure until the auditor tested it against last iteration's
own file — a problem the code review and the QA check had both passed.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | unknown | **passing** | `reports/phase-goal-ops-hardening-iter-41-ui-test-results.md` row `UT-J-01` PASS; `reports/qa/goal-ops-hardening-iter-41-evidence/J-01-verify.png` (run-748 immutable snapshot, as of 2026-05-29, stored leaderboard + regime card); golden script asserts "2 non-trading" and "19 already snapshotted" |
| J-03 No per-run range cap | passing | **passing** | row `UT-J-03` PASS; `.../J-03-verify.png`; golden script asserts "412 calendar days" |
| J-04 Non-blocking boot with visible status | unknown | **passing** | row `UT-J-04` PASS; `.../J-04-verify.png` (top bar "Ready / provider: seed / seed 2026-07-22 / 591 symbols") — covers the ready state + persisted job history only; crash/restart half rests on iter-39 |
| J-05 Aggregates are precomputed at ingest | unknown | **unknown** | NO ROW ANYWHERE, no screenshot. Target journey; test plan lines 24-29 say J-05/J-07 are "intentionally NOT given `UT-J-XX` rows"; LLM lane ran 0/0; replay lane covered only the required six |
| J-06 Pages load only what they need | unknown | **passing** | row `UT-J-06` PASS; `.../J-06-verify.png` (Regime Lab honest "Still computing — 16s elapsed" state); golden script walks all 11 routes |
| J-07 Heavy aggregates never take the service down | partial | **partial** (7th consecutive) | No browser row. Non-browser evidence: `runs/goal-ops-hardening-iter-41/wedge-drill/run1-monitor.csv` (58/58 health polls HTTP 200, max 1.73 s), VmPeak 2,446,836 kB = 9.8% under the 2650 MB cap, 8/8 aggregates refreshed, `reports/perf-budgets.md` Iteration 41 |
| J-08 Backtest evidence serves from storage only | passing | **passing** | row `UT-J-08` PASS; `.../J-08-verify.png` |
| J-09 The backend discloses its own background-compute activity | passing | **passing** | row `UT-J-09` PASS; `.../J-09-verify.png` shows the green "background compute running (1)" chip — J-09's own assertion |

Spot-checks (stable journeys, per methodology A.4): I opened `J-03-verify.png` and `J-09-verify.png`.
Neither contradicts its row; J-09's frame positively shows the asserted chip.

Screenshot integrity: I checked md5s. Three of six (`J-04`, `J-06`, `J-08`) are byte-identical to
iter-39's captures. File mtimes (05:33:22, :26, :30, 05:34:22, :25, :33 — spread over 71 s in journey
order) prove a real sequential replay wrote them, not a bulk copy, and the auditor independently
confirmed the run in `engine.log` 05:33:16→05:34:33. For `J-04`/`J-08` the frames carry no clock or
elapsed value, so identity on an unchanged database is expected. For `J-06` the frame contains a live
"16s elapsed" counter, and I could not explain its exact reproduction two days apart; I record that as
unresolved rather than treat it as proof of anything beyond the replay row.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| Secrets / credentials (AG-7) | OK | `iter-41/scan-report.md` CLEAN. I also grepped the drill's `config.scratch.yaml` myself: it carries env-var NAMES only (`TIINGO_API_KEY`, `FRED_API_KEY`, …), never values |
| Paid / external SaaS | OK | No manifest changed — `git status --porcelain` over `requirements.txt`, `pyproject.toml`, `package.json` returns zero lines. Every new import is stdlib (`array`, `faulthandler`, `collections.abc`, `signal`) |
| License changes | OK | scan-report CLEAN; no LICENSE file in the diff's 23-file list |
| Fabricated / substituted data (AG-3) | OK | The six replayed journeys assert displayed values. On `J-01-verify.png` I re-added the regime components myself: 35.00+17.21+14.75+8.24+0.00 = 75.20, matching the headline score exactly |
| AG-1 / AG-2 / AG-4 / AG-6 (proven-language, orders, overfit, referee) | OK | No evidence-ledger, referee, or claim-rendering file in the diff; no new user-facing capability (`Frontend Present: no`, zero `apps/frontend/` files changed) |
| AG-5 (determinism / no-lookahead) | OK | `_SymbolColumns` preserves row order and values; `_dates_by_symbol[symbol] = cols.dates` aliases one list so the bisect boundary and the served bars cannot drift apart. Byte-identity proven by `test_bar_cache.py::test_prefill_old_vs_new_implementation_byte_identical` and traced independently by the auditor (T1) |
| AG-8 (unbounded whole-table loads) | **IMPROVED, NOT CLOSED — open** | `_BarCache.prefill` fell a measured 51.5% (VmPeak 1,371,032 → 664,580 kB) but is a compression, not a bound: the whole table is still resident, memory still O(row count). goal.md's "no code path streams the full `daily_prices` table into RAM" is still not literally true. Pre-existing (iter-29/d, 12 iterations), improved this iteration, so **minor/open, not a new critical violation**. New ledger item iter-41/ab records that the QA report's AG-8 row claims "✓ PASS — no whole-table loads", which its evidence does not support |
| AG-9 (offline-deterministic ingest) | OK | No network call added (`grep` for `requests`/`urllib`/`httpx`/`aiohttp` in the changed backend files returns nothing); the drill ran offline on a throwaway DB whose 570 MB `drill.db` is gitignored (`.gitignore:66`, confirmed via `git check-ignore -v`) |
| AG-10 (host resource ceiling) | OK | I verified by hand: `git status --porcelain` over `scripts/start-backend.sh`, `scripts/dev.sh`, `scripts/start-frontend.sh` and `project-extensions/host-guard/host-guard.env` returns ZERO lines — byte-untouched. `config.yaml` unchanged (`memory_cap_mb: 6144`). The drill passed its diagnostic through as an env var rather than editing the launch script, and used the same tightened 2650 MB cap, never widened |

Coherence: `iter-41/coherence.md` = **COHERENCE-PASS**, zero advisory notes. No structural veto.
Ledger after this iteration: **40 total, 14 unresolved, 0 critical.** Three resolved/new this
iteration: iter-40/y resolved (required-journey verification lane genuinely repaired and
demonstrated); iter-41/z new+open (the same hole is still open for target journeys); iter-41/aa
new+resolved-in-audit (the guard did not catch last iteration's real shape); iter-41/ab new+open
(the QA report's inaccurate AG-8 claim).

No `journeys-changed.md` (all 8 `spec_hash`es match `goal_gate hash-journeys`). No
`browser-infra.json`. No `DEFERRED-BUDGET` rows. Review PASS, QA PASS, audit PASS_WITH_GAPS
(one CRITICAL found and fixed in-audit), closure CLOSURE-PASS, ux-regression SKIPPED (budget-shed,
credited nothing).

## Next-Step Recommendation

Run the next round at **full** depth. Do these, in this order:

1. **Make the two journeys being worked on get checked too.** Right now a journey gets tested
   because it is on the "must keep working" list. The moment we pick a journey to improve, it drops
   off that list and nothing tests it — which is why J-05 "Aggregates are precomputed at ingest" has
   less proof today than it had three rounds ago, even though a ready-made replay script for it is
   already sitting on disk. The fix has two halves and both are needed: write a test case for target
   journeys too on backend-only rounds, then teach the results merger to refuse a clean "PASS" when a
   target journey has no row. Do not do the second half alone — on a normal round a target journey is
   checked under a different row name and would be wrongly flagged.
2. **Re-check J-05 and J-07 in the browser** using the scripts that already exist
   (`runs/goal-session-ops-hardening/journey-scripts/J-05.json`, `J-07.json`).
3. **Decide what "no whole-table load" is going to mean, then act on it.** The memory work this round
   halved the cost per row but the whole price table is still held in memory at once. Either write the
   real fix (load per symbol, on demand) or amend the goal text to a per-row budget the current design
   meets. Leaving it ambiguous has cost twelve rounds. Also correct the QA report's claim that this is
   already done.
4. Small and already written down: correct the QA report's AG-8 row; add one line of tolerance for
   missing numbers in the new columnar store (audit B6 — it would now crash rather than degrade);
   record a before/after page-speed number for the new store (audit T2 — nothing measured it).
5. Carried, untouched: iter-29/b (badge wording after a failed warm-up, 11 rounds unmade); iter-31/e;
   iter-32/f (watch only); iter-35/k; iter-36/n; iter-37/o; iter-37/q; iter-39/u (the freeze did not
   come back and stays undiagnosed — the diagnostic tool is now in place for next time).
6. Deferred a sixth time: iter-33/g — Regime Lab's cold "All history" view still takes a minute to
   compute, visible in this round's own J-06 picture.
7. Capture only, never a round's goal: J-07's `[NEW]` walkthrough, unrecorded for an 11th round.
8. **Two decisions only the owner can make, and both should be settled before any "goal achieved"
   attempt:** (a) the `/api/health` response-time budget of 0.1 s was missed for the eighth round
   running (this time the slowest answer took 1.73 s while heavy work ran in the background) — accept
   the honest slow-answer behaviour, relax the budget for that background window, or order the cached
   readiness fix; (b) whether `start-frontend.sh` should join the host-guard file list.

In one sentence: approve one more full round whose job is to make the two journeys under active work
get tested like every other journey, then settle what "no whole-table load" means.

## Halt Justification

Not halting. ESCALATE only makes the next round run the full pipeline; it does not stop the loop.
