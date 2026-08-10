# Phase goal-ops-hardening-iter-55 — User-Visible Changes

**Phase:** goal-ops-hardening-iter-55
**Date:** 2026-08-10
**Written by:** ui-impact-analyst

---

## Scope note (read before the sections below)

`runs/goal-ops-hardening-iter-55/plan.md` and the phase spec both mark **Frontend Present: no**, and that
is correct at the file level — independently re-verified this session: `git diff --stat -- apps/frontend/`
and `git status --porcelain -- apps/frontend/` are both **empty**. Every changed product file is backend:
`apps/backend/app/engine/data_manager.py` (honest-status gate) and `apps/backend/app/engine/forward_testing.py`
(GIL-holding scheduling fix), plus their test files, one golden-script fix
(`runs/goal-session-ops-hardening/journey-scripts/J-04.json`), and `reports/perf-budgets.md`.

However — following this session's own established practice for this exact shape of iteration (see
`reports/phase-goal-ops-hardening-iter-53-user-visible-changes.md`, the prior "Frontend Present: no but a
real behavior is observable on an unchanged surface" case) — two already-shipped, code-unchanged UI
surfaces have their **underlying correctness/reliability** targeted this iteration, and the phase spec's
own "Product surface delta" section names both explicitly. This analyst independently re-read the current
frontend source (`components/health-badge.tsx`, `components/preflight-banner.tsx`,
`app/data/page.tsx` lines 2560-2700) to confirm both are unchanged in code and to identify exactly what each
one renders, then cross-checked both against the developer's own live drill
(`reports/perf-budgets.md` Addendum 19) and the fault-injection unit tests.

**The honest result is mixed, not a clean win — reported as such, not rounded up:**

- The `/data` run-detail "Refreshed: …" line's **correctness** for the partial-completion case is fixed
  (unit-test-proven) but **not exercised live this iteration** — the live drill's own job completed all
  five horizons normally, so the fault path was never actually observed rendering in a browser this pass.
- The health badge / preflight banner's **reliability** target (TC-5: zero connection-level `/api/health`
  non-answers during `forward_aggregates_warm`) was **NOT met** — it measured **worse**: 11 non-answers
  this run vs. the iter-54 baseline of 6, with 9 of the 11 still inside `forward_aggregates_warm`
  (Addendum 19). This iteration's own GIL-holding fix is proven byte-identical and did not itself lengthen
  the phase, but a second, independently-yielding heavy compute running concurrently in the same drill
  (`compute_factor_lab_all`/`compute_factor_combination`) starved the health-check thread anyway — a
  root-caused CPython "GIL convoy" effect, not a defect in this iteration's own diff.

---

## What Users Can Now Do

**Nothing new as a feature, page, field, or button.** Two already-shipped behaviors change under the hood:

- When a heavy backfill/rebuild job's forward-aggregate warm is interrupted mid-horizon by a memory error
  (isolate-and-continue, not a crash), the `/data` page's run-detail "Refreshed: …" line
  (`data-testid="aggregates-refreshed"`) will now correctly **omit** "forward aggregates" from that job's
  summary instead of incorrectly claiming it was refreshed. **This specific case is proven by a new unit
  test, not by anything observed in a running browser this iteration** — no fault occurred during this
  iteration's own live drill, so the omission has not yet been watched happen live end-to-end. A future
  browser session that catches a real memory-pressure abort in the wild is the first chance to see it.
- On the happy path (all five configured horizons complete, the normal case), the same line still reads
  "forward aggregates" exactly as before — confirmed both by the live drill (job `53449eb57b7948d29f734604ea324c73`,
  `data_provider_runs.id`'s row lists all eight categories including `forward_aggregates`) and by a new
  no-fault regression test.
- J-05 and J-07's already-authored browser goldens produced their **first real executed rows** in the
  regression-replay lane this iteration (previously authored but never replayed, or skipped two rounds
  running) — this is new evidence coverage of already-shipped behavior, not a new user-facing capability.
  J-04's golden also replayed for the first time this session, with its own step-2 boot-race bug fixed
  first (see "What Old Behavior Changed" below — this is a test-tooling fix, not a product behavior change).

## What Changed in the Visible UI

**Nothing in code.** Zero UI elements were added, removed, relabeled, or restyled —
`apps/frontend/` has a completely empty `git diff --stat` / `git status --porcelain` this iteration
(independently re-verified, not assumed from the plan).

The elements most relevant to this iteration's target are present and **unchanged in code**:

- `/data`'s run-detail "Refreshed: …" line (`app/data/page.tsx:2594`, `data-testid="aggregates-refreshed"`)
  — renders `"Refreshed: " + aggregatesRefreshed.map(a => a.replace(/_/g, " ")).join(", ")`, e.g.
  "Refreshed: coverage, market phase, forward aggregates, …". Its accuracy for the partial-failure case
  changed; its rendering code did not.
- The readiness pill in the top-right of every page's header (`HealthBadge`,
  `data-testid="readiness-badge"`, `components/health-badge.tsx`) — the same five states as before
  (`Checking backend…`, `Ready`, `Initializing… history n/m`, `Snapshot pending — …`,
  `Backend unavailable`). Unchanged code; only the backend's frequency of momentary non-answers during one
  specific finalize-tail phase (`forward_aggregates_warm`) was targeted, and that target was missed.
- The full-width banner directly below the header (`PreflightBanner`, `data-testid="preflight-banner"`,
  `components/preflight-banner.tsx`) — same GO / DEGRADED / NO-GO states and wording. Unchanged in code;
  reads the same shared readiness poll as `HealthBadge`, no second fetch.

## What Old Behavior Changed

- **`/data`'s "Refreshed: …" line stops over-claiming forward-aggregate completeness on a mid-horizon
  abort.** Previously: if horizons 1/5/10 succeeded and horizon 20 raised `MemoryError` (horizon 60 never
  attempted — the exact live-incident shape, run 351, `logs/backend.log:233042`), the line would still
  list "forward aggregates" as refreshed. Now: the gate requires every configured horizon
  (`cfg.walk_forward.horizons`, currently `[1, 5, 10, 20, 60]`) to complete before that word appears —
  proven by a new fault-injection unit test
  (`test_finalize_hook_forward_aggregates_live_incident_shape_omits_but_preserves_siblings`,
  `apps/backend/tests/test_data_manager.py`) and by inverting the pre-existing test that had encoded the
  buggy behavior as "honest." Every OTHER category the job legitimately refreshed that run
  (`coverage`, `market_phase`, `latest_snapshot`, etc.) still appears — the fix narrows only this one gate.
  The job's own overall status badge (`data-testid="job-status"` / `"last-run-status"`) is unaffected;
  isolate-and-continue behavior is unchanged.
- **The health badge/banner's momentary "unavailable" risk during a heavy backfill did NOT improve this
  iteration, and the measured signal got slightly worse.** The live drill recorded 11 connection-level
  `/api/health` non-answers this run vs. 6 at the iter-54 baseline — 9 of the 11 land inside
  `forward_aggregates_warm`'s horizon=10 sub-phase specifically, the same phase this iteration targeted.
  Root-caused (not assumed): the SAME drill's concurrent research-load process independently recorded its
  own `compute_factor_lab_all` request taking ≥600s and a following `compute_factor_combination` request
  taking 429.4s, both overlapping this window — a CPython "GIL convoy" effect where two independently
  well-behaved, already-yielding heavy computes running at once can still starve a third thread, something
  no amount of further scheduling tuning inside `compute_forward_aggregates` alone can fully close. An
  operator watching the badge during a job resembling this run's profile (a concurrent heavy research
  request landing during `forward_aggregates_warm`) may see the badge/banner behave no better, or
  marginally more unstable, than before this iteration — not the improvement the phase targeted.
- **J-04's golden test SCRIPT (not product behavior) had a boot-race bug fixed.** Its step 2 previously
  asserted `data-state="ready"` immediately after `goto /` with no wait, which failed against a backend
  still honestly showing "Initializing…" mid-boot. A `wait_for` on the same ready selector (20,000ms
  budget) was inserted before the assertion. This is a test-tooling correction, not a change to what a
  real user sees — J-04's actual boot/badge/banner behavior is unchanged code, already proven at
  iter-53/54.

## Not Visible Yet

- **The health-badge reliability gap during `forward_aggregates_warm` remains open, and is now better
  understood but not closed.** Closing it fully needs the still-open owner decision named in this session's
  NOTES since iter-50/51 ("may heavy compute move to a separate process/worker boundary") — not a further
  in-process scheduling tweak. Filed with full evidence in `reports/perf-budgets.md` Addendum 19, not
  attempted this iteration (out of this iteration's IN SCOPE list).
- **The `/data` "Refreshed: …" line's fault-omission behavior has not yet been observed live in a browser.**
  It is proven only by unit-level fault injection this iteration; the next live job that genuinely aborts
  mid-horizon under memory pressure is the first opportunity to confirm it visually in the running app.
- **Two new, previously-closed non-answers appeared this run outside `forward_aggregates_warm`**
  (`coverage_membership_timeline_refresh`, `per_date_coverage_warm` — both zero at iter-53/54), most likely
  continued DB-growth pressure (this run's DB measured 8.37+ GB). Disclosed in Addendum 19, not
  re-profiled or fixed this pass (1-event samples, out of this iteration's one-risky-change scope).
- **J-06's `/api/runs` / `/api/data/availability` DB-growth latency regression** (a separate, unprofiled
  defect) remains explicitly deferred — not attempted this iteration, per `assumptions.md` iter-55.
- **The Regime Lab `/research/regime-lab` MemoryError** (tracked separately) — still unresolved, unrelated
  to this iteration's scope.
