# Iteration 21 Evaluation

**Verdict:** STALLED
**Depth Recommendation For Next Iteration:** full

## Summary

The owner's direction-1 authorization paid off: TC-13 (0/4096 `/backtest` breaches, max 429 ms under a real
concurrent-ingest overlay) and TC-14 (kill -9 → restart → ready; checkpoint survived at `dates_done 1366/2904`)
both PASS, and this zero-code iteration added the literal small-single-day `ready → refreshing → ready`
confirmation. **J-08 crosses to `passing`** — the first new pass since iter-16 — and J-04's disruptive replay,
owed since iter-15, is freshly evidenced. Five of seven journeys now pass. But **J-06 and J-07 stay `partial` on
exactly one unchanged item**, and every path from it to a pass is owner-owned: the transient in-process
contention during the bounded ~30 s *historical* background-compute window (3.0–6.3 s `/backtest`, 1.60 s
`/api/health`), whose only in-scope resolution is the owner's still-open budget-treatment decision. Decision
tree C.2 fires → STALLED, not CONTINUE.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| J-01 | passing | **passing** (re-verified) | Golden replay UT-J-01 PASS · spot-checked `reports/qa/goal-ops-hardening-iter-21-evidence/J-01-verify.png` (Data Manager landing, coverage tiles 1996-01-02→2026-07-22 / universe 540 / candidate 122) |
| J-03 | passing | **passing** (re-verified) | Golden replay UT-J-03 PASS · `reports/qa/goal-ops-hardening-iter-21-evidence/J-03-verify.png` |
| J-04 | passing (last verified iter-15) | **passing** (freshly evidenced; `last_verified` advances to iter-21) | `reports/perf-budgets.md` §TC-14 + `runs/goal-ops-hardening-iter-21/operator-tc13-tc14-evidence.md`. **Evaluator-corroborated from the DB:** `data_provider_runs` id 164 = `status: interrupted`, `dates_done 1366/2904`, `finished_at` stamped. UT-J-04 SKIPPED (disruptive steps scope-gated OUT) — see caveat below |
| J-05 | passing | **passing** (re-verified) | Golden replay UT-J-05 PASS · spot-checked `reports/qa/goal-ops-hardening-iter-21-evidence/J-05-verify.png` ("Immutable snapshot — as of 2025-05-15 … never recomputed for today") |
| J-06 | partial | **partial** (unchanged, not targeted) | `reports/perf-budgets.md` §"Iteration 20" line 3358 — 3.0–6.3 s `/backtest` vs the committed ≤1.5 s budget. Not re-measured this iteration |
| J-07 | partial | **partial** (unchanged; step-1 half advanced) | Step 2 still unmet: `perf-budgets.md` line 3368 — 4/16 `/api/health` samples over the ≤0.1 s budget, max 1.60 s. TC-13 adds step-1 `/backtest` evidence only (no health samples in the CSV) |
| J-08 | partial | **PASSING** | `reports/phase-goal-ops-hardening-iter-21-ui-test-results.md#UT-J-08` + `reports/perf-budgets.md` §TC-13 + evaluator's independent DB derivation (below) |

### Why J-08 passes — what I verified myself, not what the report claimed

The four UT-J-08 screenshots do **not** show the acceptance states (see the caveat), so I re-derived the state
machine from the database instead of trusting the narrative:

1. The `dataset_version` stamp is `(scanner_runs count, forward_returns count)` — I confirmed the live counts
   are 1865 / 3,954,530, matching the stamp `r1865-f3954530` exactly.
2. Run 167 (`provider: "seed"`, backfill `2025-05-27 → 2025-05-27`, `snapshots_created: 1`,
   `forward_returns_inserted: 2725`) committed `scanner_runs` id 1865 at **01:58:01.125359Z**, bumping
   `r1864-f3951805 → r1865-f3954530`.
3. The first NEW `forward_aggregate_cache` row for `asof_key 2026-07-22` was not written until
   **01:59:26.747706Z**.
4. `UT-J-08-03-refreshing.png` was captured at **01:59:21.06Z** — inside that gap. So at capture time the
   version stamp had already bumped while zero new aggregates existed: the resolver *could only* have served
   the prior COMPLETE version as `refreshing`. The claimed state is structurally forced by the data, not
   asserted.
5. Post-warm `evidence_generated_at = 2026-07-25T02:00:31.176595` equals `max(created_at)` of the new complete
   5-horizon `r1865` version **to the microsecond**; exactly ONE `dataset_version` exists per `asof_key`, so the
   payload cannot mix versions (J-08 correctness clause).
6. Budget clause (steps 2–3): I re-tallied `tc13-backtest-poll.csv` myself — 4096 rows, **0 breaches > 1.5 s**,
   max 0.4288 s, mean 0.1855 s, p99 0.3868 s, all HTTP 200 / `ready`, 6 workers over a 150 s window that run
   163 (`2026-06-01→2026-07-22`, `aggregates_refreshed` includes `forward_aggregates`) overlapped exactly.
7. Step 4: `test_forward_testing_serving_split.py` 25/25 green including the four `is_latest`-never-computes
   tests. Step 5: iter-17's TC-09 never-warmed empty state carries validly — the diff is `(no changes)`.

### Evidence caveat recorded against J-08 (does not change the status; logged in assumptions.md)

This iteration's own captures are viewport screenshots that miss the acceptance state:
`RefreshingEvidenceBanner` renders at the page **bottom** (`apps/frontend/app/backtest/page.tsx:241-274`, after
AsOfScanSummary → Scorecard → ReturnAttribution → LeadershipLists), far below the 1681×1252 frame.
`UT-J-08-01-before-ready.png` and `UT-J-08-04-ready-after-warm.png` are **byte-identical** (md5
`67e7793a4c73a73604ab670cb52100f8`) — and also byte-identical to iter-17's `TC-07-backtest-page.png` and
iter-20's `TC-12-historical-view-loaded.png`. `UT-J-08-03-refreshing.png` differs from `-01` in a single 14-row
band (rows 363–376) of the unrelated DEGRADED ticker list. The banner's *rendering* is carried from iter-20's
`UT-05-refreshing-banner.png`, which I opened: banner visible with the correct copy, AG-5 older-complete
(2005-07-01 for a 2005-07-15 request) fallback, full evidence panel populated below it — on a byte-unchanged
build. **Framework note:** iter-20's `TC-12-historical-view-loaded.png` shows "Viewing as-of 2026-07-22
(latest)", so it was mislabeled; it is not load-bearing for any current status.

## Anti-goal Check

Diff basis: `iter-diff.md` = **"(no changes)"**; `scan-report.md` = **CLEAN** (0 untracked files scanned);
coherence independently re-ran `git diff --stat -- apps/*` and `git status --porcelain -- apps/` — both empty.

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| AG-1 (no unbacked "proven") | OK | No code change, no new displayed value; coherence Data Contract table shows no new producer/field. |
| AG-2 (decision-quality only) | OK | Unchanged surfaces; "Research-only · decision support · no orders" header present in every screenshot I opened. |
| AG-3 (displayed numbers correct) | OK | Post-warm `evidence_generated_at` matches the stored row to the microsecond; exactly one `dataset_version` per `asof_key` (no mixed payload); refreshing state served the prior COMPLETE version labeled with its as-of + generation time; `UT-J-08-01` shows the honest "No elapsed forward window for this date yet … No numbers are fabricated to fill the gap" empty state. |
| AG-4 (no overfit edges) | OK | No new claims; referee surface untouched. |
| AG-5 (no lookahead) | OK | Zero diff; fallback serves a complete OLDER version, never partially newer (iter-20 UT-05 opened and confirmed). |
| AG-6 (referee verdict on claims) | OK | No evidence-derived claims this iteration (goal.md loop mechanics: J-01…J-06 carry none). |
| AG-7 (no hard-coded credentials) | OK | scan-report CLEAN; zero added lines to scan. |
| AG-8 (resilience / no unbounded loads) | OK | `compute_forward_aggregates` byte-unchanged; the run-167 finalize warm (6 m 47 s under host-guard caps) completed with the service answering `/api/data` polls throughout — no crash, no OOM, no wedge. |
| AG-9 (offline-deterministic ingest) | OK | **Evaluator-verified in the DB, not from prose:** runs 163, 164 and 167 all carry `provider = "seed"`. No live network fetch. |
| AG-10 (host resource ceiling) | OK | Zero diff means no launch script could have been weakened. Operator pass `/proc`-verified (affinity `0-3,8-11`, 6144 MB, watchdog armed, peak 89 °C < 95); dev's pytest ran `taskset`-confined with 4-thread BLAS caps; browser-QA launched no process itself. Full-universe `rebuild` remained classifier-blocked. |

**No violations this iteration.** All 9 historical records stay `resolved: true` (0 unresolved).
`coherence.md` = **COHERENCE-PASS** (no blocking violations; it also closes the iter-20 dangling-import
advisory as correctly *not* applied). `journeys-changed.md` absent, and `goal_gate.py hash-journeys` returns
hashes identical to those already stored for all 7 journeys — no goal-edit drift. Review verdict: **PASS**
(no fail-open signal).

## Next-Step Recommendation

**HALT for one owner decision.** Everything agent-tractable on this surface is now done: the latency arc that
ran from iter-11 is complete (create-once INSERT off the read path, iter-19; historical compute off the request
thread, iter-20), both owner-gated measurements are delivered, and J-08 + J-04 are closed. The single remaining
blocker is the **transient in-process contention during the bounded ~30 s historical background-compute
window**, which fails J-06 step 2 and J-07 step 2 on latency alone (never on availability — no wedge, readiness
never drops, all polls 200).

The owner picks one of:

1. **Accept-and-log** — a conscious, dated `reports/perf-budgets.md` amendment covering reads taken *during* a
   bounded background-compute window (never a silent loosening). Under this, the next evaluator can score
   J-06/J-07 `passing` → **GOAL_ACHIEVED is one iteration away (5 of 7 already passing).**
2. **Sanction an off-process / precompute redesign** — the only mitigations that would actually remove the
   spikes; both were rejected earlier as unbounded (iter-15, iter-20), so re-opening either needs explicit
   sanction.
3. **Rescope** ≤1.5 s / ≤0.1 s to steady-state (non-background-window) reads, as a recorded contract change.

**Why no fourth, agent-side option exists:** `/api/health` already consumes ~98.6 % of its ≤0.1 s budget *at
rest* (`perf-budgets.md:553`; 0.090–0.099 s across every prior measurement), leaving essentially zero headroom
for any concurrent load. No bounded pacing of a background thread can create 98 % headroom — the budget *number*
is what has to move, and that is the owner's to move. A CONTINUE here would only produce the "holding spec" the
iter-21 decomposer itself predicted, burning host cycles on a box with a documented hard-reset history.

Then `--resume` at **full** depth: the next iteration is goal-closing (audit + closure + ux-regression before
the two-key confirm), and if the owner picks option 2 it touches the shared serving path, which mandates full
anyway. If the owner picks option 1 or 3 and the next iteration is a pure re-score with zero diff, lean is a
defensible override.

Non-blocking carry-overs (none closes a journey alone):
- Test-hardening: `test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches no longer trap the
  post-iter-20 dispatch path (the real call resolves through `forward_testing.py`'s own module-local name).
  Retarget them *before* anyone removes the now-dead imports at `backtest.py:75` / `mcp/tools.py:38`.
- Browser-QA capture depth: use a full-page or element-scoped screenshot for `/backtest`'s evidence states —
  the current viewport frames cannot show the banner (see caveat above).
- `demo.sh ops-hardening --session-live` walkthrough: settled non-autonomous owner deliverable since iter-12.
- Off the constrained box: `test_api_backtest.py`'s TC-11 + `test_data_manager.py` heavy fixtures (audit T1).
- J-07 step 3: VmPeak margin was not re-recorded for the TC-13 pass.

## Halt Justification

**STALLED** under decision tree C.2 — every unblock path for the current blocker is a human-owned action
(options 1–3 above), and I established that no agent-owned fourth path exists on the engineering merits (the
≤0.1 s health budget has ~1.4 % headroom at rest), not merely because this iteration's spec put mitigations out
of scope.

- **Rejected REGRESSION (C.1):** no journey moved `passing`/`already_passing` → `failing`; zero product diff;
  no unresolved anti-goal violation.
- **Rejected GOAL_ACHIEVED (C.3):** J-06 and J-07 are `partial`, not `passing` — their committed budgets are
  breached and unamended. I declined the available "satisfied-in-spirit" reading (service stayed up, only
  slower) that the iter-20 evaluator logged as the alternative: this session's human-ratified precedent
  (iter-12/15/16/20) does not launder a recorded budget breach into a green check, and granting that
  acceptance is the owner's act, not mine.
- **Rejected ESCALATE (C.4):** review = PASS with browser results present (no fail-open), no journey has failed
  twice, and the lean iteration executed cleanly rather than surfacing new cross-cutting ambiguity.
- **Rejected CONTINUE (C.5):** real progress was made (J-08 newly passing, J-04 freshly evidenced), which would
  normally match C.5 — but C.2 precedes it and fires, and the decomposer's own spec says the honest next move
  while J-06/J-07 are owner-blocked is a holding spec, not manufactured scope.

**Same class as the iter-15 and iter-20 halts, with the smallest residual yet: one budget decision, two
journeys, five already passing.**
