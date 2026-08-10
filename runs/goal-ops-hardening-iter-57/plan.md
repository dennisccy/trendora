# goal-ops-hardening-iter-57 Execution Plan

## What to Build

- **Honest during-a-job availability serving.** Extend `availability_from_storage`
  (`app.engine.data_manager`) so a `_membership_dataset_version` stamp mismatch (an ingest is
  mid-flight) serves the MOST RECENT persisted `AvailabilityCache` row (if any exists) with two
  new additive response fields — `stale: true`, `served_dataset_version: "<prior stamp>"` —
  instead of the not-yet-computed empty sentinel. The empty sentinel (`stale: false,
  served_dataset_version: null`) is reserved strictly for a DB where no `AvailabilityCache` row
  has EVER been persisted. No schema change; `AvailabilityCache` already stores exactly one row
  (pruned-on-write) so "most recent" today just means "the one row, whatever its stamp." No
  change to `compute_availability`, `availability_cached_with_status`, or the
  `GET /api/data/availability` endpoint signature.
- **Frontend stale banner.** `apps/frontend/components/availability-heatmap.tsx`: when the
  response carries `stale: true`, render the existing heatmap cells (never the empty state) plus
  a visible "Data as of `<served_dataset_version>` — updating" banner. `stale: false` +
  non-empty `cells` renders unchanged. `stale: false` + empty `cells` keeps today's "No
  availability yet" empty state (the only case it is still honest for).
- **`GET /api/health` steady-state latency fix.** Profile first (candidate per spec: the
  per-request `count(distinct(symbol))` scan in `apps/backend/app/api/health.py` has no
  supporting fast-DISTINCT index) and remove its per-call DB cost so steady-state reads return to
  the committed ≤0.1s ceiling — currently measuring 0.16-0.241s. The separate owner-amended ≤2s
  bounded-background-compute-window ceiling is unchanged; this is a steady-state-only fix.
- **`GET /api/stocks/{ticker}/bars?through=latest` latency fix.** Profile
  `app.engine.prices.bars_through_latest` first (query plan / row count / wall-clock, recorded in
  the dev handoff), then fix the named bottleneck. Keep the existing lazy-indexed-query
  convention — no precompute, no whole-table load (this endpoint is explicitly
  user-parameterized, on goal.md's "cannot be precomputed" list). Target: ≤1.5s, down from the
  6.2s Addendum 18 reading.
- **`persisted_this_call` rollback honesty fix.** `availability_cached_with_status`
  (`data_manager.py:1660-1663`, the `try: session.commit() / except: session.rollback()` block)
  and its sibling `index_series_cached_with_status` (`indexes.py:277-281`) both currently return
  `True` even when the commit raised and rolled back. Fix both to return `persisted_this_call =
  False` on that path — closes an AG-3 honesty gap feeding the existing `aggregates_refreshed`
  field. No field/schema change; fix both siblings together (documented as mirror-image
  contracts).
- **MCP `list_runs` dedup.** `app.mcp.tools.list_runs` (`tools.py`, ~line 706-731) currently runs
  its own per-run `ScannerResult` COUNT-in-a-loop — the exact N+1 pattern `app.api.runs.runs`
  already fixed in iter-56 with one grouped `GROUP BY ScannerResult.run_id` query. Repoint
  `list_runs` at that same grouped-query approach (read the counts into a dict once, same as
  `runs.py`), same response shape, byte-identical `n_stocks`. Closes the coherence-auditor's
  iter-56 advisory finding (stale duplicate).
- **`reports/perf-budgets.md` calendar-span correction.** Addendum 20 mislabels
  `compute_availability`'s SPY-benchmark trading calendar as "1996-2026"; read the actual
  `_trading_days` source and its live min/max, and append a new dated correction note (the file
  is append-only — do not edit the historical Addendum 20 entry).
- **`journey-scripts/J-06.json` real budget assertions.** Rewrite the steps that hit
  `/api/runs`, `/api/data/availability`, `/api/health`, and
  `/api/stocks/AAPL/bars?through=latest` so each asserts a measured latency at or under its
  committed budget, in addition to the existing heading-text match — closes the "golden asserts a
  heading, not a value" defect class (iter-52 lesson).
- **Test-ordering discipline.** Run `apps/backend/tests/test_api_runs.py` ALONE, FIRST — before
  any other test file or dev work this iteration — and record its result honestly in the dev
  handoff (it has been killed twice at 30+ minutes inside the full suite; iter-56 flagged this
  explicitly as unresolved).
- **New/extended unit tests:** byte-identity for the availability stale-serving fallback (TC-1,
  TC-2, TC-3), the fixed `/api/health` field (TC-5, TC-9-style byte-identity), the fixed
  `bars_through_latest` path (TC-9), a fault-injection test for the `persisted_this_call`
  rollback fix in both `data_manager.py` and `indexes.py` (TC-10), and a byte-identity test for
  the `list_runs` MCP fix (TC-11) — add to `test_mcp_window.py` (the file that already exercises
  `tools.list_runs`, since a dedicated `test_mcp_tools.py` does not exist in this codebase) unless
  the developer judges a new file cleaner.

## Agents Required

- backend-data: yes — all of the above except the frontend banner (availability serving fallback,
  health/bars profiling+fixes, rollback honesty fix ×2, MCP dedup, perf-budgets correction note,
  golden rewrite, ordered test run, unit tests).
- frontend-ux: yes — the `AvailabilityHeatmap` stale-banner rendering (small, additive,
  presentation-only change to one existing component; verify `apps/frontend/app/data/page.tsx`
  passes the new `stale`/`served_dataset_version` fields through to the component's `state` prop
  if the page currently narrows the API response shape before handing it to
  `AvailabilityHeatmap`).

## Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/engine/data_manager.py` -- extend `availability_from_storage`'s MISS-fallback
  to serve the existing `AvailabilityCache` row with `stale`/`served_dataset_version` on a stamp
  mismatch; fix `availability_cached_with_status`'s rollback branch to return
  `persisted_this_call=False`.
- `apps/backend/app/engine/indexes.py` -- fix `index_series_cached_with_status`'s rollback branch
  (~line 277-281) to return `persisted_this_call=False`.
- `apps/backend/app/api/health.py` -- remove/replace the per-request `count(distinct(symbol))`
  scan (or whatever profiling names) so steady-state latency returns to ≤0.1s; no field/shape
  change to the response.
- `apps/backend/app/engine/prices.py` -- fix `bars_through_latest`'s profiled bottleneck; keep
  lazy/indexed, no precompute.
- `apps/backend/app/api/stocks.py` -- touch only if the fix requires a call-site change (unlikely
  given `bars_through_latest` is the compute boundary).
- `apps/backend/app/mcp/tools.py` -- `list_runs` (~line 706-731): replace the per-run COUNT loop
  with the same grouped-aggregate approach `app.api.runs.runs` uses.
- `apps/frontend/lib/api.ts` -- extend `AvailabilityResponse` (~line 2719-2723) with `stale:
  boolean` and `served_dataset_version: string | null`.
- `apps/frontend/components/availability-heatmap.tsx` -- add the `stale`-banner render path; keep
  the existing empty-state / ok-state branches otherwise unchanged.
- `apps/frontend/app/data/page.tsx` -- pass the two new fields through to
  `AvailabilityHeatmap`'s `state` prop if the page's `AvailabilityState` type currently narrows
  the fetched response (check `fetchDataAvailability` call site, ~line 295/344).
- `apps/backend/tests/test_data_manager.py` -- new tests for the stale-serving fallback (TC-1,
  TC-2, TC-3) and the `persisted_this_call` rollback fix (TC-10).
- `apps/backend/tests/test_indexes.py` -- new fault-injection test for the `persisted_this_call`
  rollback fix (TC-10).
- `apps/backend/tests/test_api_health.py` -- byte-identity / latency test for the fixed endpoint
  (TC-5).
- `apps/backend/tests/test_api_stocks.py` -- byte-identity test for the fixed `bars` path (TC-9).
- `apps/backend/tests/test_mcp_window.py` (or a new `test_mcp_tools.py` if the developer prefers
  a dedicated file) -- byte-identity test for the `list_runs` fix (TC-11).
- `apps/backend/tests/test_api_runs.py` -- run alone, first; no code change expected (already
  fixed at iter-56), but confirm the full file (not just the 3 new fast tests) completes and
  record the result.
- `reports/perf-budgets.md` -- new dated addendum for TC-5/TC-6/TC-7 (health) and TC-8 (bars)
  measurements, plus the append-only calendar-span correction note (TC-17).
- `runs/goal-session-ops-hardening/journey-scripts/J-06.json` -- add real budget assertions to
  the steps touching `/api/runs`, `/api/data/availability`, `/api/health`,
  `/api/stocks/AAPL/bars?through=latest`.
- `runs/goal-session-ops-hardening/state/blueprint.md` -- already pre-annotated by the decomposer
  (iter-57 update paragraph + the Availability heatmap row's `[TARGET, iter-57 building]` Notes
  extension exist already); retag to BUILT once the evaluator confirms, per this session's
  existing convention — no new row, no Information Architecture change.
- `docs/handoffs/goal-ops-hardening-iter-57-dev.md` -- dev handoff naming both profiling results,
  the availability stale-serving mechanism, and all small items closed (met or not met, honestly).

## UI Evolution

- New user-facing capability: during an active ingest job, `/data`'s availability heatmap keeps
  showing the real previous chart (never a false "no data" message) while a job runs.
- New information displayed: a "Data as of `<served_dataset_version>` — updating" banner on the
  availability heatmap, shown only during a stamp-mismatch (in-progress ingest) serve.
- New user actions: none — passive display-honesty fix only, no new buttons/forms.
- UI surface changes: the existing `AvailabilityHeatmap` component on `/data` gains one
  conditional banner state. No new page, route, or nav entry.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the existing `Card`/`EmptyState` components already used by
  `AvailabilityHeatmap`; the new banner is a small inline notice row inside the existing
  `state.kind === "ok"` branch (above or beside the legend), not a new component/dialog.
- Layout: no layout change — the heatmap card keeps its current position on `/data` near the
  coverage panel.
- Key visual effects: match the existing calm/factual tone of this page's other status text (e.g.
  the `availability-loading`/`availability-error` treatments) — no alarm styling; this is a
  routine "updating" state, not an error.
- States to handle: `stale: true` + non-empty cells (new banner + existing grid); `stale: false` +
  non-empty cells (unchanged today); `stale: false` + empty cells (unchanged "No availability
  yet" empty state); existing `loading`/`error` states untouched.

## Key Test Scenarios

- TC-1/TC-2/TC-3: `GET /api/data/availability` during a mid-flight ingest (stamp mismatch, prior
  row exists) returns `stale: true` + the PRIOR row's `served_dataset_version`/non-empty cells;
  a DB that has never persisted a row returns the honest empty sentinel (`stale: false,
  served_dataset_version: null`); an idle/matching-stamp read stays byte-identical to iter-56's
  already-verified values (regression guard).
- TC-4: the `/data` availability heatmap renders the previous cells + the "updating" banner when
  `stale: true`, and never renders "No availability yet" while cells are non-empty.
- TC-5/TC-6/TC-7: `GET /api/health` at rest (curl + real-browser, ≥3 readings) is ≤0.1s; during a
  bounded background-compute window every poll still answers HTTP 200 within the unchanged
  relaxed ≤2s ceiling (regression guard for J-05/J-07/J-09).
- TC-8/TC-9: `GET /api/stocks/AAPL/bars?through=latest` is profiled, fixed, answers ≤1.5s
  (curl + real-browser), and is byte-identical to the pre-fix computation.
- TC-10: a forced commit failure in `availability_cached_with_status` and
  `index_series_cached_with_status` both yield `persisted_this_call=False` after rollback.
- TC-11: MCP `list_runs`'s `n_stocks` is byte-identical to the pre-fix per-run-COUNT loop for
  every stored run, and answers under the ≤1.5s budget.
- TC-12/TC-15: the rewritten `journey-scripts/J-06.json` asserts real budgets (an artificially
  slowed endpoint must FAIL the golden, not silently pass); J-06 passes via browser-qa /
  deterministic replay against real measurements, and J-01/J-03/J-04/J-05/J-08/J-09 all remain
  green with no journey regressing.
- TC-13: `test_api_runs.py` run alone and first completes (pass or fail reported honestly) with
  its result recorded before any other test file or dev work proceeds.
- TC-14/TC-16: the 8-journey replay+browser-qa lane is dispatched LAST against a code-frozen tree
  (any audit-found defect needing a code change is filed for iter-58, not applied as a
  code-changing audit-fix); AG-9/AG-10's five frozen launch-script/config surfaces
  (`config.yaml`, `host-guard.env`, `scripts/start-backend.sh`, `scripts/dev.sh`,
  `scripts/start-frontend.sh`) show empty `git diff`/`git status --porcelain`.
- TC-17: a new dated append-only correction note in `reports/perf-budgets.md` records the
  verified SPY-benchmark calendar span, without editing the existing Addendum 20 entry.

## Out of Scope (flagged, per phase spec)

- J-07's per-compute-yield lever (session-declared "finished," per iter-56 evaluator).
- J-05 as a Target (its remediation is "Do not redo"-complete; rides Required-still-passing only —
  note its golden consumes the 2010-11-10 date again and will need rotation before its next
  replay).
- Moving heavy compute to a separate process/worker boundary; whether the 20-minute finalize-tail
  budget applies while serving traffic — both still open owner decisions, not this iteration's
  job.
- The vendored framework-level replay-lane/QA-verdict-reading defects (confirmed to live only in
  `incredible_auto_dev/scripts/automation/`, not this product's code).
- The broken demo-recorder script — capture-only, not this round's job.
- A third `status` value or new completeness field on `data_provider_runs` beyond the existing
  `persisted_this_call`/`aggregates_refreshed` mechanism.
