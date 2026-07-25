# Iteration 22 Evaluation

**Verdict:** GOAL_ACHIEVED
**Depth Recommendation For Next Iteration:** lean

## Summary

The owner's dated BCW budget amendment (`reports/perf-budgets.md` § "OWNER BUDGET AMENDMENT", present in the
pre-iteration snapshot; window bound corrected 60 s → 90 s by "Revision 1" the same day) resolves the single
blocker that has held **J-06** and **J-07** `partial` since iter-11 — a human-owned budget decision, taken
through exactly the mechanism `docs/goal.md` J-06's Acceptance designates as the single source of budget
numbers. This iteration ships **zero product diff** and adds two independent live background-compute-window
(BCW) measurements, both inside the amended ceilings, plus J-07 step 3's overdue `VmPeak` margin. I re-derived
the load-bearing numbers myself from the raw CSV, the database, and `logs/backend.log` rather than accepting
the handoff — and in doing so found three documentation errors (below) that change no journey's status but
must be corrected. All 7 Must-have journeys are now `passing`; scan CLEAN, coherence PASS, no unresolved
anti-goal violation.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing | Deterministic replay UT-J-01 PASS (`reports/phase-goal-ops-hardening-iter-22-regression-replay-results.md`, 3/3; merged file agrees, no reconciliation footer). Evaluator opened `reports/qa/goal-ops-hardening-iter-22-evidence/J-01-verify.png` = `/data` landing, `Ready` badge, live coverage tiles. Corroborated in DB: replay submitted runs 170–172 (`provider: seed`, `ok`) at 07:16 UTC, all zero-work over already-snapshotted dates. |
| J-03 | passing | passing | Replay UT-J-03 PASS; `J-03-verify.png`. All 8 iter-22 frames carry distinct md5s and none matches an iter-21 frame (evaluator-hashed) — fresh captures. |
| J-05 | passing | passing | Replay UT-J-05 PASS; `J-05-verify.png`. |
| J-04 | passing | passing (`last_verified` advances iter-21 → iter-22) | UT-J-04 PASS, non-disruptive steps live. Evaluator opened `J-04-no-crash-banner.png` (`Ready` / `provider: seed`, no "Backend unavailable", full Dashboard) and `J-04-data-page-top.png` (Data Manager coverage tiles; `snapshot dates 1865` == DB `scanner_runs` count). Disruptive kill/restart steps carried on iter-21's owner-authorized TC-14 (scope-gated out again this pass). |
| J-08 | passing | passing | UT-J-08 PASS with three **full-page** captures (iter-21's "captures can't show the state" finding closed). Evaluator opened `J-08-refreshing-2026-07-20.png` (banner + "evidence as of 2026-07-17, generated 2026-07-24 00:44:13", full evidence panel below it — never a blank/skeleton wait) and `J-08-ready-after-warm-2026-07-20.png` (banner gone, "expanding window ≤ 2026-07-20", "Snapshots contributing: 1863"). AG-3 cross-check in DB: `COUNT(scanner_runs WHERE asof_date <= 2026-07-20) = 1863` — exact match; the refreshing view's 1858 is the stored 2026-07-17 payload as generated on 2026-07-24, honestly labelled. |
| **J-06** | **partial** | **passing** | `reports/perf-budgets.md` § "Iteration 22" TC-2/TC-3/TC-5 + raw `runs/goal-ops-hardening-iter-22/bcw-measure.csv`, **re-tallied by the evaluator**: 29 samples, 29/29 HTTP 200, `/backtest` max **7.119 s** (≤ 8.0 s BCW ceiling), `/api/health` max **0.253 s** (≤ 2.0 s), `readiness: ready` on all 28 health polls, trigger request 87.9 ms. Window 68.79 s ≤ amended 90 s — **verified independently in the DB**: the five `forward_aggregate_cache` rows for `(2026-07-21, r1865-f3954530)` commit at 06:53:36.523790 → 06:54:32.266617 (13.7–14.3 s apart), trigger 06:53:23.474051. UT-J-06 PASS: all 11 J-06 pages rendered real content, no blank/frozen/error frame. |
| **J-07** | **partial** | **passing** | Same series (availability half): 28/28 `/api/health` 200 + truthful `ready` throughout a real background compute; **step 3 closed** — `VmPeak` flat 2,631,612 kB, margin 3,659,844 kB ≈ 3574 MB (58.2 %) under the 6144 MB cap. Second, independent BCW by browser-qa (`?asof=2026-07-20`, different date): 11/11 HTTP 200 on both endpoints, worst `/backtest` 7.551 s, worst `/api/health` 0.411 s. Step 4 (isolation convention) gains its first **organic** live evidence: `logs/backend.log:76796-76808` — a background compute raised `MemoryError` under the self-inflicted 5-way probe and aborted honestly ("non-fatal, will re-dispatch on the next request for this identity"), while the SAME process served 32/32 `/backtest` + 32/32 `/api/health` 200 with `readiness: ready` for 179 s (`drain-monitor.csv`, evaluator-tallied) — no wedge, no restart requirement. |

Statuses I did **not** change: none dropped; nothing `regressed`; nothing `unknown`.

## Anti-goal Check

Source: `iter-22/scan-report.md` (**CLEAN**), `iter-22/iter-diff.md` (1 file: `docs/improvement-backlog.md`,
card B-1107), and my own `git diff` vs snapshot `583e3188` (6 files total: backlog card, `perf-budgets.md`,
`blueprint.md`, 3 harness-bookkeeping). Zero files under `apps/backend/` or `apps/frontend/` — independently
confirmed.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 (no unproven "proven" claims) | OK | No product diff; B-1107 card states `★ Evidence Claim: N/A — must not introduce proven-language`. Screenshots show the unchanged "not fabricated" / survivorship-bias disclosures. |
| AG-2 (decision-quality only) | OK | No new copy; `/backtest` header still reads "Research-only · decision support · no orders". |
| AG-3 (displayed numbers correct) | OK | Dev's deep-equality served-vs-stored check, plus my own independent check: on-screen "Snapshots contributing to 2026-07-20: 1863" == DB count; `evidence_generated_at` 06:54:32.266617 == horizon-60 row `created_at` to the microsecond. |
| AG-4 (no overfit edges) | OK | No referee/ledger surface touched; zero product diff. |
| AG-5 (determinism / no lookahead) | OK | Refreshing view serves a strictly-OLDER complete version (2026-07-17 for a 2026-07-20 request) labelled with its served as-of — verified in the full-page capture. No compute code changed (`compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, `ensure_historical_forward_aggregates_dispatched` byte-unchanged). |
| AG-6 (referee gate) | OK | No evidence-derived claims this iteration (ops/measurement only). |
| AG-7 (no hard-coded credentials) | OK | scan-report CLEAN on added lines; diff is 3 markdown files. |
| AG-8 (resilience / no memory exhaustion) | OK — **with a recorded residual risk** | No violation introduced (zero product diff; no unbounded whole-table load added). **But**: under the developer's self-inflicted 5-concurrent-BCW probe the process reached its `ulimit -v` cap (`VmPeak` 6,291,424 kB = 32 kB under 6,291,456 kB) and one background compute raised `MemoryError` inside `_attribution_slices` (`logs/backend.log:76796-76808`). AG-8's required degradation shape held completely — contained, honest, non-fatal, zero non-200, zero untruthful readiness, no blank application-error page, no wedge (I verified: today's log has exactly ONE `MemoryError` and NO `Exception in ASGI application` / HTTP 500; the 11 such events in the log are all from 2026-07-20/21/22). Pre-existing since iter-20, owner-reviewed, backlogged as **B-1107**. See Halt Justification item 2. |
| AG-9 (offline-deterministic ingest) | OK | No ingest submitted by the measurement (plain `GET`s). Every `data_provider_runs` row today (162–172) is `provider: "seed"` — evaluator-queried from the DB. No live network call. |
| AG-10 (host resource ceiling) | OK | No launch script changed (zero product diff). Backend for the official pass (PID 807942) launched via `scripts/start-backend.sh`; `/proc`-verified `Cpus_allowed_list 0-3,8-11`, address space 6442450944 B, `MALLOC_ARENA_MAX=2`, BLAS/OMP=4; the launcher banner is in `logs/backend.log` at 06:52:09Z. The mid-iteration restart was a graceful `SIGTERM` (clean `Shutting down` / `Application shutdown complete` in the log — I read it), not a `kill -9`. |

Historical records: all 9 prior entries stay `resolved: true`; **0 unresolved**. Coherence: **COHERENCE-PASS**
(`iter-22/coherence.md`) — no structural veto. `journeys-changed.md` absent; all 7 `spec_hash` values match
`goal_gate.py hash-journeys` exactly, so no goal-edit drift.

## Next-Step Recommendation

Halt — goal achieved. Follow-ups below are documentation corrections and owner-owned items; none blocks a
journey. If the confirm gate or the owner re-opens the loop, a **lean** iteration suffices (all of it is
zero-product-diff work).

1. **Correct three inaccuracies in `reports/perf-budgets.md`** (all in non-scored prose; none changes a number
   any journey is scored on):
   - § "Incidental finding" says *"no exception/traceback logged (`logs/backend.log` checked for 'historical
     forward-aggregate background dispatch failed' and any traceback — none found)"*. **False** — that exact
     string, plus a `MemoryError` traceback, is at `logs/backend.log:76796-76808`, inside that episode's own
     06:47–06:51 UTC window. The honest statement is: the cap was reached, one compute aborted, and the abort
     was contained and honest.
   - The same section omits that `/backtest` latencies reached **10.096 s** during that episode
     (`drain-monitor.csv`, 32 samples, min 0.493 s) — above the 8.0 s single-BCW ceiling, in a scenario the
     amendment explicitly does not cover.
   - The browser-qa lane reports its independent window as **"28.06 s"**; that is its *poller's* elapsed time,
     not the window. The DB shows the `(2026-07-20, r1865-f3954530)` horizons committing 07:31:59.453 →
     07:32:56.164 (56.71 s first→last, ~14 s cadence), so with the same ~13 s trigger→first-commit lead the
     real window was **≈ 69.8 s** — inside the 90 s bound, but NOT inside the superseded 60 s one.
2. **Owner call, optional:** promote **B-1107** if AG-8's "exhaust a service's memory" is read literally (see
   Halt Justification item 2).
3. Carried, unchanged and non-blocking: a fresh `demo.sh ops-hardening --session-live` walkthrough (J-06/J-07's
   walkthrough acceptance bullet still rests on the iter-14 run, which predates J-08 and the BCW states —
   settled non-autonomous owner deliverable since iter-12); retarget
   `test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches **before** anyone removes the
   imports at `backtest.py:75` / `mcp/tools.py:38` (B-1107's card repeats this warning); run
   `test_api_backtest.py`'s TC-11 + `test_data_manager.py`'s heavy fixtures off the constrained box.
4. Framework note: the browser-qa report cites
   `runs/goal-ops-hardening-iter-22/operator-tc13-tc14-evidence.md` for J-04's disruptive coverage — that file
   does not exist; the evidence is at `runs/goal-ops-hardening-iter-**21**/operator-tc13-tc14-evidence.md`
   plus `perf-budgets.md` § "Post-STALL owner-authorized measurements". Path typo only.

## Halt Justification

**Why GOAL_ACHIEVED (decision tree C.3).** All 7 Must-have journeys are `passing`; no journey went
`passing → failing` (C.1 does not fire); the blocker that drove the iter-20 and iter-21 STALLs is resolved by
the owner, so C.2 no longer fires; coherence is PASS, `scan-report` CLEAN, zero unresolved anti-goal
violations, and no goal-edit drift. I did not inherit the pass — I re-tallied `bcw-measure.csv` (29 rows),
re-queried both BCWs' `forward_aggregate_cache` commit timestamps, cross-checked a displayed number against
the DB, read the launcher/`SIGTERM`/`MemoryError` sequences in `logs/backend.log`, and opened five
screenshots.

**1. The pass depends on the owner's amendment, including Revision 1 — stated plainly.** Under the
un-amended steady-state budget, 4 of this iteration's 29 `/backtest` samples breach ≤ 1.5 s (max 7.119 s), so
J-06/J-07 pass **only** because the owner amended the budgets file that `docs/goal.md` names as the single
source. I verified the amendment's core (the 8.0 s / 2.0 s ceilings, the "what does NOT relax" clauses, the
expiry clause) predates this iteration in commit `583e3188`, and that Revision 1's diff touches **only** the
window-duration bound (60 → 90 s, three occurrences) plus its own dated narrative — no ceiling, no
steady-state budget, no ingest-overlay carve-out was loosened. Revision 1 was made after the developer
honestly reported the 68.79 s breach, which is the shape of goalpost-moving; I checked it on the merits and
found the correction sound and, in fact, **independently corroborated**: the second BCW of the day (different
date, browser-qa's) shows the same ~14 s/horizon cadence and a ≈ 69.8 s window, so iter-20's "~30 s" figure
that produced the original 60 s bound was indeed unrepresentative. A human who treats any post-measurement
bound revision as illegitimate would keep J-06/J-07 `partial`; logged in `assumptions.md`.

**2. The one finding an owner should read before accepting this halt.** The developer's accidental 5-way
concurrent probe drove the process to its memory cap and produced a real `MemoryError`
(`logs/backend.log:76796-76808`), which the product handled exactly as J-07 step 4 requires — honest
non-fatal abort, same process kept serving, 32/32 polls HTTP 200 / `readiness: ready` over 179 s, no restart
required. I score it as strengthening J-07 rather than violating AG-8, because AG-8 targets data-basis
widening and unbounded whole-table loads with a crash/wedge outcome, and because the owner already reviewed
this episode and chose to backlog it (B-1107). **If the owner instead reads AG-8's "exhaust a service's
memory" literally, this is the one item that would re-open the goal** — resume with `--resume`, promote
B-1107, and the fix is bounded (a global dispatch semaphore). Logged in `assumptions.md`.

**3. What this halt does not claim.** The `demo.sh --session-live` walkthrough bullet in J-06/J-07's
Acceptance rests on the iter-14 operator run (owner-owned, settled precedent since iter-12); J-04's
UI-presentation steps rest on iter-14/15 captures over a byte-unchanged surface plus iter-21's TC-14
operator API/DB evidence; and the multi-BCW scenario (10.096 s reads) is outside every budget row and every
journey step's scenario — accepted as out-of-contract, not as within budget.
