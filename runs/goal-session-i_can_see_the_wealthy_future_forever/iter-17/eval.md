# Iteration 17 Evaluation

**Verdict:** CONTINUE
**Depth Recommendation For Next Iteration:** full

## Summary

The target journeys **J-09** (as-of-scoped Backtest forward-tested evidence, expanding window ≤ D) and
**J-10** (control-group, riding the same aggregate) were delivered exactly as the operator's re-scope
(commit `d723133`) requires: `compute_forward_aggregates` gained a single `as_of` cutoff, the aggregate
relocated off the retired `/system-health` onto `/backtest` under the single global as-of switcher, and
System Health was fully retired (route/router/page/nav/client/test). I verified every critical seam in
**source** (not on the QA table): the as-of filter is one membership clause on `ScannerRun.asof_date ≤ D`
with `as_of=None` byte-identical; the scoring/scanner/regime/patterns/buckets path is untouched (J-06/J-07
byte-identical, no DB regen); and `/backtest` adds **no** page-local date state (J-18 — the principal
anti-goal risk — holds in source and live). **Not GOAL_ACHIEVED:** the same re-scope raised **J-26**'s bar
(now a non-empty composite percentile-rank blend, still strict-AND in code → `partial`) and added **J-32**
(Research as-of toggle, unbuilt → `failing`); both are scheduled (iter-18, iter-19) and tractable. J-22/23/24
stay honestly blocked (NA) and are **non-halting** per the re-scoped goal.

## Journey Results This Iteration

| Journey | Prior Status | This Iteration | Evidence |
|---------|--------------|----------------|----------|
| **J-09** Backtest forward-tested evidence (as-of-scoped, expanding window) | passing (old `/system-health` home) | **passing** (delivered at new `/backtest` home, as-of-scoped) | `reports/qa/…-iter-17-evidence/UT-02-baseline-latest-60d-full.png`, `UT-03-after-2024-05-28-full.png` |
| **J-10** Control-group honesty | passing (old home) | **passing** (relocated, same aggregate) | `reports/qa/…-iter-17-evidence/UT-08-control-group.png` |
| J-14 Per-date scorecard | passing | passing (renders alongside aggregate) | UT-12 |
| J-15 Fast loads / no per-request recompute | passing | passing (horizon change = 0 refetch; 1 fetch keyed `[asOf]`) | UT-05 |
| J-16 VCP-vs-non-VCP breakdown | passing | passing (renders on `/backtest`) | UT-02 |
| J-18 One date control (**principal risk**) | passing | passing (1 `<select>`, 0 `input[type=date]`, URL date-free; source-confirmed no date state) | UT-11 / TC-14 + source |
| J-19 Attribution | passing | passing (aggregate slice relocated; consistency invariant test moved not deleted) | UT-12 |
| J-21 Leadership lists below attribution | passing | passing (order: summary→scorecard→attribution→leadership→evidence) | UT-12 |
| J-28 Pattern breakdowns | passing | passing (pullback/flat-base on `/backtest`) | UT-02 |
| J-13 Global as-of re-points other pages | passing | passing (in-app nav to `/stocks` preserved date) | TC-15 |
| J-06 Score consistency | passing | passing (scoring path byte-identical — git-verified untouched) | source (no scoring diff) |
| J-07 Risk-Off gates Actionable | passing | passing (scoring/regime untouched, no DB regen) | source (no scoring diff) |
| **J-26** Multi-factor combination cohorts | passing (iter-14, strict-AND) | **partial** (re-scope raised bar to composite blend; still strict-AND in code) | `research.py:479` (`combined_members &= members`) — composite blend pending iter-18 |
| **J-32** Research point-in-time toggle | *(new journey)* | **failing** (unbuilt — `/api/research/*` has no `as_of` param) | source — iter-19 target |
| J-22 Expanded universe (~500) | failing | failing (data-walled, **non-halting**; not re-probed) | BLOCKED (Yahoo-429) |
| J-23 Multi-timeframe bars | failing | failing (data-walled, **non-halting**) | UNBUILT/data-walled |
| J-24 Timeframe selector | failing | failing (data-walled, **non-halting**) | UNBUILT/data-walled |
| J-01–J-05, J-08, J-11, J-12, J-17, J-20, J-25, J-27, J-29, J-30, J-31 | passing | passing (carried — additive diff; serving paths untouched) | prior evidence |

**Board: 27 passing · 1 partial (J-26) · 4 failing (J-22/J-23/J-24 data-walled & non-halting + J-32 unbuilt) → 27/32 passing, 1 partial, 4 failing.**

## Anti-goal Check

| Anti-goal | Status | Notes |
|-----------|--------|-------|
| No lookahead *(critical)* | OK | `as_of` filter restricts to `ScannerRun.asof_date ≤ D`; no >D leak (unit-tested `test_aggregates_as_of_no_future_run_leak`; live "As-of range" capped at D). Chart carve-out untouched. |
| Snapshots immutable *(critical)* | OK | No `scanner_run`/result mutation; `forward_returns` append-only untouched; no DB regen. |
| Single source of truth *(critical)* | OK | Exactly ONE `compute_forward_aggregates`; ONE serving home `/api/backtest`. No score recompute. |
| No magic numbers | OK | `config.yaml` change is a comment only (`default_horizon` value stays 20); no literal in calc code. |
| No fabricated data | OK | Empty cohort → `mean=None, n=0` (em-dash, never 0); invalid `as_of` → 422 (UT-06, UT-13). |
| No recompute in read path *(critical)* | OK | Read-only grouping over persisted `forward_returns`, filtered to ≤ D — the model the anti-goal permits. |
| Exactly one date selector (J-18) *(critical)* | OK | `/backtest` adds NO page-local date state (source + UT-11); horizon is a client-side view selector. **The principal risk — held.** |
| Attribution is read-only | OK | Aggregate attribution slice rides the same read-only grouping; consistency invariant relocated, not deleted. |
| Risk-Off gates Actionable *(critical)* | OK | Scoring/scanner/regime byte-identical (git-verified). |
| Honest limitations surfaced | OK | Survivorship-bias / universe-relative label carried on the evidence aggregate. |
| No order/execution path; no secrets | OK | None added. |

No new anti-goal violation. The single historical minor one ("Exactly one date selector", baseline iter-0)
stays **RESOLVED** and was the exact seam most at risk this iter — re-confirmed holding in source **and**
browser. **Coherence: COHERENCE-PASS** — and this iteration actively *resolves* a latent invariant-#12 risk
by consolidating the evidence onto a single home rather than creating a second one.

## Next-Step Recommendation

**Operator gate first:** this is a **nav-skeleton change** — `state/blueprint.reapproval-requested` is
written, so `run-goal.sh` will **pause at iter-18's pre-decomposer** for human confirmation of the System
Health retirement / single Backtest evidence home before any new feature work. Approve to proceed.

**iter-18 → J-26 (full depth).** Replace the strict AND-intersection (`research.py:479
combined_members &= members`) with the re-scoped **composite percentile-rank blend** (a config-weighted
rank-blend across any number of selected factors, oriented by side, taking the top config-quantile of the
composite) so the Combined cohort is **non-empty and clears `min_sample`** and scales to all catalog
factors; keep the strict-AND as an optional secondary "strict overlap" column. Full depth — it touches the
critical read-only research-lab path, needs real unit tests (composite is non-empty for a sensible
selection; blend weights/quantile from config — no magic numbers; recomputes no factor/return), and a
coherence/closure pass. Reuse the iter-17 read-only pattern: verify in source that the cohort math is a
pure grouping of stored factor values + stored returns.

**iter-19 → J-32 (full depth).** Add the Research **All-history ⟷ As-of-date** toggle reusing this
iteration's `asof_date ≤ D` scoping seam on `compute_factor_lab` / `compute_factor_combination` /
`compute_event_study` — as a **MODE, not a second date control** (J-18: it reads the single global as-of;
add no `input[type=date]`, no page-local date state).

**After J-26 + J-32 land and nothing regresses, GOAL_ACHIEVED is reachable** on the buildable set:
J-22/J-23/J-24 are recorded as honestly blocked (NA) and **non-halting per the re-scoped goal** — they do
NOT veto completion and **must not be autonomously re-probed** (re-confirmed pointless iters 7–8; auto-heal
via the committed runbook only on operator confirmation of a reachable no-key egress).

**Watch-item (non-blocking):** `/api/backtest` now calls `compute_forward_aggregates` 5× per request (one
per horizon). Fine for the committed seed (browser QA showed no wall-clock issue across ~12 interactions),
but if the universe expands (J-22) or horizons grow, memoize per `(as_of, horizon)`. J-15's substantive
criteria (snapshot-served, no score/return/bucket recompute, one fetch keyed `[asOf]`) are met.

**Minor advisory (non-blocking):** `apps/frontend/app/data/page.tsx:141` subtitle still says "grow the
System Health evidence" — stale user-facing prose (no dangling link; not a coherence/anti-goal issue).
Update to "Backtest evidence" in a future touch.
