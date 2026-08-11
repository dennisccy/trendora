# Iteration 59 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

This round did the best engineering work of the session and then failed to get it counted. The two open
journeys — J-05 "Aggregates are precomputed at ingest, never on the fly" and J-07 "Heavy aggregates never
take the service down" — both had checks that had never been run before, and both of those checks passed
live: the app was killed outright and came back serving its stored coverage numbers in 1.7 seconds, and
the heavy calculation now peaks at 71% of its memory limit instead of hitting the limit exactly. Across
about seven and a half hours of heavy work the app served zero errors and ran out of memory zero times —
I counted that myself in the app's own log file, not from a report. But the two journeys still do not
close, for two reasons that are both about paperwork rather than the product: no test lane produced a
result row for either one (each lane assumed the other was covering them), and the recorded walkthrough
that both journeys explicitly require was never made. So the score stays 6 passing, 2 partial, 0 failing.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 Backfill honors the requested range and explains zero-work | passing | passing | `reports/qa/goal-ops-hardening-iter-59-evidence/UT-J-01-weekend-zerowork-crop.png` (opened by me: real zero-work card, "2 calendar days · 0 already snapshotted · 2 non-trading"); merged results UT-J-01 PASS; DB rows 387/388 at 03:23:17 / 03:24:24, both `provider='seed'` (queried by me). Deterministic replay FAILED step 09; overridden by the LLM lane per the merged file's reconciliation footer. |
| J-03 No per-run range cap | passing | passing | `reports/qa/goal-ops-hardening-iter-59-evidence/J-03-verify.png`; merged results UT-J-03 PASS (replay, all expects held) |
| J-04 Non-blocking boot with visible status | passing | passing | `reports/qa/goal-ops-hardening-iter-59-evidence/J-04-verify.png`; merged results UT-J-04 PASS; corroborated by `runs/goal-ops-hardening-iter-59/evidence-drill/pass2/phase2-restart.json` (kill -9, boot-to-first-200 = 1.712 s) |
| J-05 Aggregates are precomputed at ingest, never on the fly | partial | partial | `reports/qa/goal-ops-hardening-iter-59-dev-evidence/J-05-verify.png` (opened by me: "Immutable snapshot — as of 2010-11-15 · provider seed", regime 74.65); `reports/phase-goal-ops-hardening-iter-59-dev-journey-replay.md` UT-J-05 PASS (15 steps); `evidence-drill/pass2/phase2-restart.json`. Merged results list UT-J-05 under **Missing Target Journeys**; walkthrough clause unmet. |
| J-06 Pages load only what they need | passing | passing | `reports/qa/goal-ops-hardening-iter-59-evidence/J-06-verify.png` (opened by me: real figures, +0.35% n=282050, no degrade markers); merged results UT-J-06 PASS + UT-05 PASS (raw-API byte match) |
| J-07 Heavy aggregates never take the service down | partial | partial | `reports/qa/goal-ops-hardening-iter-59-dev-evidence/J-07-verify.png` (opened by me: 2953 snapshot dates = my own sqlite count); `evidence-drill/pass2/tc4-vmpeak.csv` (max 5,977,564 kB = 71.26% of cap), `tc5-health-poll.csv` (1520/1520 HTTP 200; 12 over 2 s), `fault-drill.json` (same pid, byte-identical reads). Merged results list UT-J-07 under **Missing Target Journeys**; walkthrough clause unmet; step 2 latency half unmet. |
| J-08 Backtest evidence serves from storage only | passing | passing | `reports/qa/goal-ops-hardening-iter-59-evidence/J-08-verify.png` (spot-check, opened by me: as-of 2026-08-03, regime 66.07, honest "No elapsed forward window" NA); merged results UT-J-08 PASS |
| J-09 The backend discloses its own background-compute activity | passing | passing | `reports/qa/goal-ops-hardening-iter-59-evidence/J-09-verify.png`; merged results UT-J-09 PASS |

Shape unchanged: **6 passing / 2 partial / 0 failing**. Newly passing: none. Newly failing: none. Regressed: none.
No `browser-infra.json`, no `journeys-changed.md`, no `DEFERRED-BUDGET` row on any journey. All 8 `spec_hash`
values match `goal_gate.py hash-journeys docs/goal.md`, which I ran myself.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 unbacked values must render "not yet proven" | OK | No proven/certified language added. The 6-file diff adds a degrade marker, its tests, and two display files. `J-06-verify.png`, opened by me, still carries the "Survivorship bias · universe-relative · descriptive … never a forecast" banner. |
| AG-2 decision-quality only, no orders | OK | Every frame I opened carries the "Research-only · decision support · no orders" header. Nothing in the diff touches this. |
| AG-3 displayed numbers must be correct | **MINOR VIOLATION (iter-59/a)** | Normal path verified correct by me twice: `J-06-verify.png` renders +0.35% / n=282050, matching the LLM lane's raw-API read (`mean_return=0.0035029…`, n=282050); `J-07-verify.png` renders 2953 / 591 / 5391, matching my own sqlite counts. **But** in the NEW degrade state, `TC-11-degrade-rendered-by-label-table.png` (opened by me) shows `n=0` for cohorts the control frame proves hold 17,440 observations; only a tooltip separates degraded from empty. Scored minor — see `assumptions.md` (iter-59, 1 of 2). |
| AG-4 no overfit edges | OK | Nothing surfaced as proven; no referee-gated claim in the diff. |
| AG-5 determinism / no lookahead | OK | The change is a per-horizon loop restructure with a byte-identity test against `_compute_regime_lab_pinned_pre_iter59`, a literal copy of the old implementation that never calls the function under test (auditor traced the oracle's independence; reviewer independently re-ran 36/36 in 9.70 s). |
| AG-6 no unrefereed evidence claims | OK | Per `docs/goal.md` loop mechanics these journeys carry no Evidence Claims; none added. |
| AG-7 no hard-coded credentials | OK | `iter-59/scan-report.md` = **CLEAN**. 6-file diff, no config/env/manifest file among them (I read the file list). |
| AG-8 no unbounded loads / must degrade gracefully | **MINOR VIOLATION (iter-59/b)**, and a large net improvement | The diff strictly REDUCES retention (5 horizons held at once → ~2). VmPeak 71.26% of cap vs exactly-on-cap last round. Residual gap: `research.py:4438-4441` runs `_run_position_index`'s unbounded `.all()` BEFORE the per-horizon try, so a memory error there can still return a 500 — pre-existing, two-column projection over 2,953 rows. |
| AG-9 offline-deterministic ingest | OK | I queried sqlite: every run this iteration (ids 383–390) is `provider='seed'`. The only non-seed row since 2026-08-10 is id=369, iteration 57's already-ledgered event. The backfill-only drill rule held for a second round. |
| AG-10 host resource ceiling | OK | I ran BOTH `git diff --stat` and `git status --porcelain` over `config.yaml`, `project-extensions/host-guard/`, `start-backend.sh`, `dev.sh`, `start-frontend.sh` — all empty. `config.yaml:1363-1364` still reads 8192 / 2. This round's own boot log slice reads `memory_cap_mb=8192 malloc_arena_max=2 / host-guard: cpu_list=0-15 blas_threads=8`. |

**Severity summary:** 11 new open violations, ALL minor; 0 unresolved critical. Two prior entries CLOSED and
verified by me: iter-58/f (the memory-ceiling exhaustion — its named mechanism is now bounded and measured at
71.26% of cap) and iter-58/e (the depth mismatch — `depth-dispatched` reads `full`, matching the spec). Half of
iter-57/e is closed too (its event (1), the Regime Lab memory error); its event (2), the wedge, is a different
code path and stays open. Ledger now: **161 total, 78 unresolved, 0 unresolved critical.**

## Pipeline Facts

- Depth dispatched: **full** — matches the spec's `**Depth:** full` / `Full trigger: 3`. No mismatch this round.
- `coherence.md`: **COHERENCE-PASS** (0 blocking, 1 advisory: the Rank-IC row still uses the old generic NA
  tooltip for the same degrade cause). No structural veto.
- Review: **PASS_WITH_NOTES** (`definition_of_done: complete`, `scope_creep: none`) — no fail-open.
- Audit: **PASS_WITH_GAPS**, naming DoD 1, 2 and 8 unmet as written.
- QA: **PASS / UI-PASS**, but its "Blockers: None" headline is contradicted by its own inputs (iter-59/c).
- Merged browser QA: **BLOCKED** — 9/12 passed, 3 skipped, **2 target-missing**.
- Deterministic replay: 5/6 PASS; J-01 FAIL at step 09, overturned by the LLM lane per the merged file's footer.
- Demo: **NOT_YET**, empty step table. ux-regression: **SKIPPED** (wall-clock budget trim).
- Closure: **CLOSURE-FAIL**. Blocker 1 (BLOCKED headline / missing target-journey rows) is genuine; blocker 2
  is a false positive I traced myself to a keyword match on line 71 of the user-visible-changes file
  (iter-59/h).
- `status.json`: `blocked` / `closure_failed`, attempt 3, fix mode, `product_code_changed_this_pass: false`.

## Next-Step Recommendation

Run the next round at **full depth**. A shallow round cannot close either open journey, because both of them
require a recorded walkthrough and the recorder only runs at full depth. In order:

1. **Fix the hole that swallowed this round's work.** The app's two most important checks were run, passed,
   and then reported as "not tested", because one test lane only covers the always-check list and the other
   lane's plan had no case for them. Nobody owns the journeys a round is actually about. Fix that first, or
   the next round will lose its work the same way.
2. **Record the walkthrough** for J-05 "Aggregates are precomputed at ingest" and J-07 "Heavy aggregates never
   take the service down". Both journeys ask for one in writing, and neither can be marked done without it.
   The reason it produced nothing last time is gone. This rides along with the real work; it is never a round's
   own goal.
3. **Make the "unavailable" cells look unavailable.** When the Regime Lab page cannot compute a column, it now
   writes "n=0" — a sample count of zero — for a group that really holds 17,440 records, and only a mouse
   hover reveals the truth. Give it a visible marker and stop offering the drill-down link for a group that
   was never calculated.
4. **Close the last gap in the memory fix**: one small database read still sits outside the protected block,
   so the page can in principle still fail with a server error. The fix is to wrap the opening section.
5. **Repair or retire the J-01 check script.** The report says it was rewritten; it was not (I checked with
   git). It will fail again next round on a journey that genuinely works.
6. **Measure the new limit against the old one on a quiet machine.** The memory saving and the speed cost are
   both unmeasured, and one cold Regime Lab page took 340 seconds under load.
7. SMALL AND ALREADY WRITTEN DOWN: a blank picture cited as evidence again (this time in a different lane); a
   QA summary that says "no blockers" over a file that lists one; the closure check's false alarm about
   user-visible changes; the previous round's audit report vanishing from disk entirely.
8. CARRIED, untouched: iter-29/b and the badge wording after a permanently failed warm-up (32nd round unmade);
   iter-31/e; iter-32/f; iter-35/k; iter-36/n; iter-37/o; iter-37/q; iter-39/u; iter-46/az; iter-46/ba;
   iter-47/bd; iter-47/bf; iter-47/bi; iter-48/bj; iter-57/f; iter-57/l. Deferred a **twenty-fifth** time:
   iter-33/g, the Regime Lab backlog.
9. **OWNER — one decision is now the only thing standing between J-07 and green.** For ten rounds I have asked
   two questions. One of them no longer matters much: moving the heavy calculation into its own process is no
   longer urgent, because this round's fix already brought peak memory down to 71% of the limit and the app
   ran all night without a single error. The other one is now decisive: **the promise says the app must answer
   its health check within 2 seconds while a background job runs, and that promise was written for a job
   lasting about 30 seconds. This round's job lasted 23 minutes.** Twelve answers out of 1,520 took longer
   than 2 seconds; the slowest took 4.1 seconds; not one answer failed. Please tell me which you want: keep
   the 2-second promise for long jobs too (then J-07 stays open until the app gets faster), or say the promise
   applies to short jobs only (then J-07's last measurement gap closes next round). One sentence is enough.

## Halt Justification

Not halting.
