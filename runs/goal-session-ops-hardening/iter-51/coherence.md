# Iteration 51 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-51
**Date:** 2026-08-07
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Scope of this iteration (context for the tables below)

Backend-only. `git diff 45d3e64c712459e3c3ee5edd82bc8840bf8951a1 --stat` (noise-excluded) touches exactly
four files: `apps/backend/app/engine/data_manager.py`, `apps/backend/app/engine/research.py`,
`apps/backend/tests/test_data_manager.py`, `apps/backend/tests/test_research_streaming.py` (377
insertions / 13 deletions total). Zero files under `apps/frontend/` changed — independently confirmed by
`reports/phase-goal-ops-hardening-iter-51-ui-surface-map.md` ("Frontend surfaces changed (code): 0"). The
excluded-paths stat shows only harness/report bookkeeping (`runs/*`, `reports/*`) plus a 4-line additive
edit to `runs/goal-session-ops-hardening/state/blueprint.md` itself (the decomposer's own documentation
catch-up, verified below) — no lockfile, no `config.yaml`/`host-guard.env`/launch-script change (AG-10
surface stays empty, consistent with the spec's own DoD claim, though AG-10 itself is the evaluator's
call, not mine).

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Factor Lab all-factors default view (`compute_factor_lab_all` / `factor_lab_all_cached`) | OK | New ingest-time warm call at `apps/backend/app/engine/data_manager.py:4290` (`factor_lab_all_cached(session, cfg, as_of=None)`) invokes the SAME pre-existing canonical function defined at `apps/backend/app/engine/research.py:3799`, whose only other two callers are unchanged: `GET /api/research/factor-lab?all=true` (`apps/backend/app/api/research.py:126`) and the MCP `query_backtest`-sibling tool (`apps/backend/app/mcp/tools.py:344`). No second implementation, no second endpoint — this is the ingest-time-warm-then-serving-cache-HIT pattern the blueprint's Membership-timeline row already documents for `research_hot_keys`/`index_series`. |
| `aggregates_refreshed` (Backfill run-summary contract / Job history rows) | OK | `apps/backend/app/engine/data_manager.py:4258-4309` appends `"factor_lab_all"` to the SAME `list[str]` field via the SAME `_run_detail()`/`JobProgress` mechanism every other member already uses (honesty-gated: omitted on `MemoryError`, generic exception, or an internally-degraded non-raising payload — `test_finalize_hook_factor_lab_all_memory_error_isolated_and_not_reported` / `..._generic_failure_isolated...` / `..._never_reported_on_whole_response_degrade`, `apps/backend/tests/test_data_manager.py`). Served unchanged by `GET /api/data` + `GET /api/data/jobs/{job_id}`. |
| `_combination_cohort_members`'s `strict` cohort (Factor Combination lab, same row) | OK | `apps/backend/app/engine/research.py:1557-1573` — a pure allocation-strategy change (starts the AND-intersection from a copy of `single_members[0]` instead of unconditionally allocating `set(range(pool_n))`); byte-identity against a pinned pre-iter-51 reference oracle is asserted by `test_combination_cohort_members_strict_matches_pinned_pre_iter51_reference` and a no-full-range-allocation proof by `test_combination_cohort_members_strict_no_full_range_allocation` (both `apps/backend/tests/test_research_streaming.py`). Same function, same two callers, no served value changes. |
| `by_horizon[].status` / `factors_status` (Factor Lab degrade signals, code shipped iter-50) | OK — documentation catch-up, not new code | `apps/backend/app/engine/research.py:1324`, `:1339`, `:3910` — unchanged this iteration. Now formally registered in `runs/goal-session-ops-hardening/state/blueprint.md:419`'s Data Contract row Notes, closing the iter-50 coherence-auditor's "UNREGISTERED (advisory)" finding. No code path exercises a registration by itself. |

No duplicate computation, no non-canonical serving source, and no new displayed value shipped without
registration this iteration.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/research/factor-lab` (existing page; only its load-timing/cache-hit behavior changes) | OK | `apps/frontend/components/sidebar.tsx` and every file under `apps/frontend/app/research/` are untouched (`git diff --stat` against the snapshot SHA returns zero `apps/frontend/` hits). Keeps its existing home under the Research nav item per `blueprint.md:381`/`:397`-`:398` (IA table), unchanged. |
| `/data` ("Refreshed: …" line gains `factor_lab_all`; job duration lengthens) | OK | Same — no frontend file changed; existing Data Manager nav home (`blueprint.md:385`) unchanged. |

Zero new pages, routes, components, or nav entries this iteration — independently confirmed by
`reports/phase-goal-ops-hardening-iter-51-ui-surface-map.md`'s own summary ("New pages/routes: 0",
"Navigation changes: no"). Part B is trivially satisfied: there is nothing new to place.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Prior WARN fully closed, verified by diff (not just asserted).** iter-50's coherence audit
  (`runs/goal-session-ops-hardening/iter-50/coherence.md`) issued three advisories; this iteration's
  `blueprint.md` diff closes all three with precise edits: (1) `by_horizon[].status`/`factors_status`
  are now registered in the Membership-timeline row (`blueprint.md:419`); (2) a new correction paragraph
  (`blueprint.md:359`, "iter-50 AUDIT-FIX addendum CORRECTION") explicitly fixes the prior "no new
  field ... the Data Contract row below is unchanged" misstatement; (3) the row's own `iter-50 (TARGETED,
  not yet built)` tag was replaced with `iter-50 (BUILT -- see the iter-50 AUDIT-FIX addendum above and
  iteration-state.md 'Do not redo')` (confirmed via the raw `-`/`+` diff lines, not just the current
  file). No new advisory is being carried forward in its place.
- **Disclosed, not a coherence issue:** the new warm phase measurably lengthens ingest job wall-clock
  (dev-measured ~12min -> ~18min per the ui-impact-analyst's surface map) and the "Refreshed: …" /
  job-duration values on `/data` will read differently post-iteration. This is a single value from a
  single producer either way (no second source appears) and is an explicitly reasoned, disclosed
  trade-off in the iteration spec's own NOTES ("Budget tension, stated plainly") and in
  `reports/perf-budgets.md`'s new addendum — flagged here only for completeness, not as a defect.
