# Iteration 15 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-15
**Date:** 2026-07-23
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Scope note (diff provenance)

No bounded `iter-diff.md` existed for this iteration, so I used the exact snapshot-SHA commands from
the invocation prompt: `git diff c7fd90ce9805507ffa3dcc47ad2ddfead06013b5` (noise-excluded) plus the
`--stat` of the excluded paths. The excluded-paths stat contains only `runs/*`/`reports/*` harness
churn (no lockfiles) — nothing to reconcile there. The noise-excluded main diff is 463 lines and touches
exactly 3 non-harness files: `README.md`, `apps/backend/app/engine/forward_testing.py`, and
`apps/backend/tests/test_forward_testing_concurrency.py`. I traced the `README.md` hunk to a prior
iteration's leftover: `c7fd90ce` is a WIP snapshot on top of `8fecf587` ("iter 14 — CONTINUE"), taken
*before* `2b2a291c` ("chore(goal): iter 14 showcase artifacts (demo/summary/README/renders)") — so that
README prose (describing iter-14's AG-8 streamed-read fix) is iter-14's already-audited showcase output
sitting between the snapshot and HEAD, not new iter-15 product content; `git status` confirms `README.md`
is not in this iteration's working-tree changes. I also read the full (non-excluded) diffs of
`reports/perf-budgets.md` and `runs/goal-session-ops-hardening/state/blueprint.md` directly, since both
are named Data Contract artifacts/the contract document itself, not incidental harness noise.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Regime score, market phase, realized forward-returns — specifically `compute_forward_aggregates` / `forward_aggregates_cached` (blueprint.md row 3) | OK | `apps/backend/app/engine/forward_testing.py:1058-1176` (new single-flight lock/in-flight-event/bounded-wait wrapper added entirely *inside* `forward_aggregates_cached`, around the unchanged `compute_forward_aggregates(session, horizon, cfg, as_of=as_of)` call, diff line ~1146). `compute_forward_aggregates` itself has zero touched lines — the new module-level globals (`_FORWARD_AGG_LOCK`, `_FORWARD_AGG_INFLIGHT`, `_FORWARD_AGG_WAIT_TIMEOUT_S`) are inserted *after* that function's closing `}` (diff hunk `@@ -984,6 +985,34 @@ def compute_forward_aggregates(`). All three existing call sites still call the SAME wrapper, unchanged: `apps/backend/app/api/backtest.py:72`, `apps/backend/app/mcp/tools.py:205`, `apps/backend/app/engine/data_manager.py:3230` (confirmed via direct grep — none of these three files appear in the diff). No second producer, no second endpoint. |
| Page performance budgets (blueprint.md row "Page performance budgets") | OK | `reports/perf-budgets.md` gained one new dated section (`## UT-04 — /backtest concurrent cache-miss latency...` through the TC-4/5/6 RESULTS subsection, ~403 added lines) in the SAME canonical file — no second budgets artifact created. |
| No new displayed value / entity | N/A — none introduced | Iter spec confirms "New information displayed: None"; ui-surface-map confirms "Modified components: 0"; frontend diff is empty (`Frontend Present: no`, 0 files under `apps/frontend/` in the diff). |

`blueprint.md`'s own diff (42 lines) is a pure Notes-column append to 4 existing rows (Regime/forward-
aggregates, Backend readiness, Job history, Page performance budgets) plus one new top-of-file changelog
paragraph — every removed line has a corresponding added line with **columns 2 and 3 (computing
module / serving endpoint) byte-identical**; only column 4 (Notes) grew. No row's canonical
module/endpoint identity changed.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| (none — no new page/route/feature this iteration) | OK | `apps/frontend/` has zero touched files (confirmed via `git status` and the noise-excluded diff); `/backtest`'s existing route/nav entry is unmodified. The independent phase-closure-auditor's own handoff (`docs/handoffs/goal-ops-hardening-iter-15-audit.md:83`) states the same conclusion verbatim: "No UI surface, page, nav entry, or displayed value changed. Correct per spec." |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- The dev handoff's Known Issue #5 (`docs/handoffs/goal-ops-hardening-iter-15-dev.md:178-190`) discloses
  that the same "no lock/in-flight de-dup on a concurrent same-key MISS" shape this iteration fixed in
  `forward_aggregates_cached` also exists, unverified as a live problem, in four sibling ingest-time
  caches: `research.event_study_cached`, `market_phase.market_phase_cached`,
  `forward_testing.compute_drawdown_expectations_cached`, and `indexes.index_series_cached_with_status`.
  None of these were touched this iteration (correctly out of scope — UT-04 only measured
  `forward_aggregates_cached`), so this is not a violation today, but if a future iteration patches one
  of them ad hoc without reusing this iteration's now-established single-flight idiom (or
  `data_manager.compute_coverage`'s original J-100 version of it), that would start scattering the same
  fix pattern three different ways. Worth the next decomposer/developer touching any of those four
  reusing the same idiom rather than inventing a fourth variant.
- Two open measurement discrepancies remain in `reports/perf-budgets.md`'s new section (a second,
  unflagged 5.37s `/backtest` latency spike at epoch 1784818231, and a Tctl thermal reading materially
  higher than the operator's reported figure) — both already surfaced honestly by the developer's own
  recomputation and by the general auditor (`docs/handoffs/goal-ops-hardening-iter-15-audit.md`,
  finding B1, marked fixed) as open evaluator/owner items. These are evidence-honesty and
  goal-achievement questions, not Data Contract or IA violations, so they are noted here for context
  only and left to the goal-evaluator.
