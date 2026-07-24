# Iteration 20 Evaluation

**Verdict:** STALLED
**Depth Recommendation For Next Iteration:** full

## Summary

iter-20 correctly and completely closed the last agent-tractable latency blocker on the
`/backtest` cluster: the historical (`is_latest == False`) cold forward-aggregate compute is off
the request thread (single-flight-guarded background dispatch), so a first-ever historical view
went from a 9.6–54 s blocking, no-affordance skeleton to **0.082 s** with an honest interim state
(`ensure_loop_ms` 9288–54281 ms → ~1.67–3.34 ms). I verified this live-measured record and opened
the screenshots (UT-02/UT-03/UT-05) myself. **But no journey crossed to `passing`.** J-08's literal
"never a request-path recompute / never a skeleton waiting on a fresh compute" is now met on both
cold paths — yet J-06/J-07/J-08 stay `partial`, and **every remaining path to closing them is a
human-owned action** (owner-authorize the AG-10-gated ingest for the TC-13 budget proof + TC-14
disruptive J-04 replay; owner-decide how the ≤1.5 s / ≤0.1 s budgets treat the transient
in-process contention whose only in-scope fix the spec itself rejects). Decision tree C.2 → STALLED,
the same class as iter-15's halt — the tractable engineering work is exhausted and the ball is in
the owner's court.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | passing | golden replay UT-J-01 PASS + spot-check `reports/qa/goal-ops-hardening-iter-20-evidence/J-01-verify.png` (Data Manager landing, badge Ready) |
| J-03 | passing | passing | golden replay UT-J-03 PASS (`.../J-03-verify.png`) |
| J-04 | passing | passing (CARRIED, last_verified left at iter-15) | UT-J-04 SKIPPED (no golden, disruptive kill/restart blocked, no browser-infra token); code surface out of the 7-file diff (coherence + ux-regression confirmed) |
| J-05 | passing | passing | golden replay UT-J-05 PASS + spot-check `.../J-05-verify.png` (immutable 2025-05-15 snapshot, never recomputed) |
| J-06 | partial | partial | `.../UT-02-historical-empty-state.png` (honest interim, full page, never frozen) + perf-budgets.md iter-20 (transient 3.0–6.3 s contention; oldest-date 1.3–1.9 s scorecard out-of-scope) |
| J-07 | partial | partial | `.../UT-05-refreshing-banner.png` (badge Ready during interim) + perf-budgets.md iter-20 (16/16 health ready = no wedge; but 4/16 health polls to 1.60 s > 0.1 s budget) |
| J-08 | partial | partial | `.../UT-03-ready-evidence.png` (revisit → real ready) + `.../UT-05-refreshing-banner.png` (older complete fallback, AG-5 preserved); TC-13 ingest-overlay budget UNMEASURED (owner-gated) |

Statuses come from the merged `reports/phase-goal-ops-hardening-iter-20-ui-test-results.md`
(Browser QA PASS, 14/15, UT-J-04 the only SKIP) cross-read against the operator's live
`reports/perf-budgets.md` "Iteration 20" numbers, the audit (PASS_WITH_GAPS), and screenshots I
opened directly. No journey moved to `failing`/`regressed`; no journey moved to `passing`.

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 (proven-language) | OK | ops/latency work, carries no Evidence Claims (goal Loop-mechanics); no proven-language introduced |
| AG-2 (no orders/targets) | OK | none introduced; page copy is decision-support disclosure only |
| AG-3 (correct numbers, not fabricated) | OK | dispatch serves the PRE-dispatch resolver read (last-good or `{}`), never a synthesized value; byte-identity proven (30 streaming tests + TC-4/TC-10); UT-02/UT-05 render "No numbers are fabricated in the meantime" |
| AG-4 (no overfit) | OK | no claim surfaced; referee untouched |
| AG-5 (no-lookahead) | OK | UT-05 fallback serves OLDER complete snapshot 2005-07-01 ≤ requested 2005-07-15, never partially newer; resolver logic byte-unchanged (coherence). TC-11 (no-lookahead unit) edited but not executed this session (deep-basis fixture, audit T1) — property holds by byte-identity of the unchanged compute |
| AG-6 (referee gate) | OK | no evidence-derived claim this iteration |
| AG-7 (no secrets) | OK | scan-report CLEAN; no config/env files in the 7-file diff |
| AG-8 (data-scale resilience) | OK | `compute_forward_aggregates` byte-unchanged (110 ins / 0 del, coherence PASS, one producer); background worker reuses the SAME bounded/streamed path; no new unbounded ORM load; service never DOWN (16/16 health ready) — the contention is CPU/GIL latency, not memory-exhaustion/wedge |
| AG-9 (offline-deterministic ingest) | OK | scan-report: no dependency/manifest change; new code is stdlib `threading`/`logging` only; no live-network/paid path |
| AG-10 (host resource ceiling) | OK | new dispatch is an in-process daemon thread inheriting the host-guard-confined process (launched via `scripts/start-backend.sh`, peak 79 °C < 95); no `scripts/` file in the diff; the ingest-trigger safety classifier correctly BLOCKED TC-13/TC-14 (fail-closed) |

**Result: no anti-goal violation, critical or minor, this iteration.** scan-report CLEAN;
coherence COHERENCE-PASS; all 10 historical records stay `resolved: true`.

## Next-Step Recommendation

HALT for an owner decision. The agent-tractable latency-fix chain that drove iters 16–19 is
COMPLETE — both `/backtest` cold-recompute paths are off the request thread and the honest interim
states are shipped and live-verified. The remaining path to `passing` on J-06/J-07/J-08 (and thus
GOAL_ACHIEVED) is owner-owned. The owner picks from this menu, then `--resume` at FULL depth:

1. **Authorize the AG-10-gated ingest trigger for TC-13** — re-measure the `/backtest` ≤1.5 s
   budget under the actual concurrent-INGEST overlay (the original historical breach condition,
   iter-16's 11/68 @ 12.655 s). This is J-08's OWN step-1-2 scenario (a single-day backfill bumps
   the version + schedules the warm, then load `/backtest` during the warm). Proven so far only
   under pure reads (TC-3); the spec is explicit TC-3 does not prove it.
2. **Authorize the AG-10-gated ingest trigger for TC-14** — the disruptive J-04 kill/restart
   checkpoint-survival replay, a hard GOAL_ACHIEVED precondition every evaluator since iter-15 has
   named (a non-disruptive `/api/health` sanity check is not a substitute).
3. **Decide the transient-contention budget treatment.** During the bounded ~30 s background
   compute, concurrent `/backtest` requests spike to 3.0–6.3 s and `/api/health` to 1.60 s — real
   recorded breaches of the ≤1.5 s / ≤0.1 s budgets that I did NOT launder green. Fully removing
   them needs the compute off-process or precomputed-at-ingest, BOTH spec-rejected as unbounded.
   The owner's fork (iter-15 option-3 precedent): (a) accept it as a disclosed bounded-window
   constraint via a **logged** `perf-budgets.md` amendment (never a silent loosening) → the
   evaluator can then score J-06/J-07 `passing`; or (b) sanction an off-process/precompute redesign
   despite the unbounded-cost concern; or (c) read ≤1.5 s / ≤0.1 s as governing steady-state,
   non-background-window reads only.

Optional, agent-tractable, but closes NO journey alone (do not let it masquerade as the unblock):
the oldest-date (2005) cold view totals ~1.3–1.9 s from `scorecard_ms + resolved_run_ms`
(`backtest.py:162–177`, pre-existing, explicitly OUT OF SCOPE this iteration — iter-20's own
`ensure_loop_ms` contribution is 3.34 ms). A future targeted iteration could apply the
compute-at-ingest/serve-from-storage pattern there, but even a full success leaves J-06/J-07/J-08
blocked on items 1–3. Also carried before final closure (audit T1): run
`test_api_backtest.py::test_backtest_evidence_is_as_of_scoped_expanding_window` and
`test_data_manager.py` off the constrained box (edited/relied-upon, deep-basis fixtures unrun this
session — low risk, genuinely unverified).

## Halt Justification

**Why STALLED, not CONTINUE.** iter-20 made real, verified PROGRESS but moved NO journey to
`passing` — so the CONTINUE "≥1 journey newly passing" trigger does not fire. What remains is not
tractable agent work: the decisive blocker for each target journey is human-owned.
- J-08 → passing needs the ≤1.5 s budget proven under its own ingest-overlay scenario (TC-13) —
  **owner-gated** (AG-10 ingest-trigger classifier blocks the trigger; the agent cannot
  self-authorize without itself committing an AG-10 REGRESSION).
- J-07 → passing needs the health-latency budget met throughout, breached only by the transient
  in-process contention whose sole in-scope resolution is an **owner budget-acceptance decision**
  (off-process/precompute are spec-rejected); plus the **owner-gated** TC-14 disruptive replay.
- J-06 → passing needs the same transient-contention **owner budget decision**; its one
  agent-tractable residual (oldest-date scorecard, a separate pre-existing out-of-scope subsystem)
  closes no journey on its own.

The one genuinely agent-tractable item (scorecard optimization) does not, by itself, move any
journey to `passing`, because the owner-gated proofs (TC-13/TC-14) and the owner budget decision
still bind. Therefore **every unblock path for the current blocker is a human-owned action**
(methodology decision tree C.2) — structurally the same situation as iter-15's STALLED, now with a
far smaller residual and J-08's literal requirement met. I did not choose STALLED to escalate
(there is genuinely no agent step that reaches a `passing`), nor CONTINUE to avoid surfacing the
decision (surfacing it to the owner is exactly what is owed).

**Why not the other verdicts.** REGRESSION (C.1): no journey passing→failing; no unresolved
anti-goal (scan CLEAN, coherence PASS, byte-identity + AG-5/AG-8/AG-10 all confirmed). GOAL_ACHIEVED
(C.3): three journeys `partial`, and J-04 owes a fresh disruptive replay — positive `passing`
evidence is absent for all three targets. ESCALATE (C.4): already full depth; review
PASS_WITH_NOTES (not fail-open — browser results exist and the review did not FAIL); no journey
failed twice in a row as `failing`. The loop halts for the owner; `--resume` at full depth once a
direction above is chosen.
