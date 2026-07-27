# goal-ops-hardening-iter-27 Execution Plan

## What to Build

Hardening-only iteration closing the two ESCALATE-flagged anti-goal findings from iter-26. No new
journey, page, endpoint, or user-facing capability — J-05/J-07/J-08 become more robust and more honest
under conditions this session's own QA already proved occur live.

- **Fix 1 (AG-8, `apps/backend/app/engine/forward_testing.py`):** extend `_insert_run_forward_returns`'s
  per-symbol loop so a mid-loop `session.exec(...)` autoflush (the `close_on`/`bars_after` reads for the
  *next* symbol) that raises `IntegrityError` on a still-pending, now-colliding `ForwardReturn` insert
  from an *earlier* symbol in the same call is caught, rolled back to discard only the duplicate row(s),
  and the loop continues for the remaining symbols/horizons. This is the SAME tolerant-duplicate reasoning
  `_commit_forward_returns_concurrency_safe` already applies at the *final* commit (iter-28/J-41 legacy) —
  extended to cover the autoflush point the iter-26 traceback actually fired at
  (`_insert_run_forward_returns:390` is the `close_on(...)` read, not an INSERT). Freeze on
  `app.engine.forward_testing` is lifted ON PURPOSE for this one function only —
  `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`,
  `ensure_historical_forward_aggregates_dispatched`'s keying/single-flight semantics, and J-08's serving
  split stay byte-frozen. The catch must be narrow enough that an `IntegrityError` from any OTHER
  constraint still propagates unchanged (TC-4) — never a blanket try/except around the loop.
- **Fix 2 (AG-3, `apps/backend/app/engine/data_manager.py`):** in `coverage_from_storage`, add one new
  fallback branch tried AFTER the existing exact-match `CoverageSnapshot` lookup and the existing
  explicit-`as_of` self-heal (both unchanged): one bounded, indexed lookup by `asof_key` alone (never a
  `daily_prices`/`scanner_runs` scan) for a row under ANY older `dataset_version`. If found, serve that
  row's payload plus three new sibling fields: `coverage_status: "stale"`, `stale_dataset_version`
  (the older row's version), `stale_computed_at` (that row's own `computed_at`, ISO-8601 UTC). The
  existing exact-match hit gets `coverage_status: "current"` (both null stale fields); the true
  no-row-under-any-version case keeps `_coverage_not_yet_computed_payload`'s all-zero shape plus
  `coverage_status: "not_yet_computed"` (both null stale fields) — payload shape otherwise unchanged
  (TC-7 regression guard). Root cause: `_membership_dataset_version` is a GLOBAL stamp bumped by ANY new
  `ScannerRun` row (including a request-path historical `/backtest` create-once view), so a real,
  previously-computed row for the same `asof_key` can exist under an older stamp while the exact-match
  lookup misses. **Note for developer:** `_upsert_coverage_snapshot` (line ~1003) deletes every row whose
  `dataset_version != current` at the end of every ingest — the stale row this fix must find is one that
  survives *because no ingest ran* between the request-path `ScannerRun` creation and the read (only
  ingest deletes old-version rows). Confirm this mechanics directly against `scanner_runs`/
  `coverage_snapshot` state during TC-1's live reproduction, per the spec's own root-cause note — don't
  assume the diagnosis, re-verify it.
- **API plumbing (`apps/backend/app/api/data.py`):** `data_overview`'s `"coverage"` key already embeds
  `coverage_from_storage(...)`'s full return dict verbatim (no field allowlist/pick in the route today) —
  confirm the three new fields flow through unchanged with no route code change needed; if any
  intermediate shaping is found, wire it through additively. No new endpoint, no new route.
- **Frontend (`apps/frontend/app/data/page.tsx`, `CoveragePanel`):** when `data.coverage.coverage_status
  === "stale"`, render the disclosed prior-snapshot figures (already what `c.price_start`/`c.price_end`/
  `c.universe_count` etc. will hold — no client derivation) together with a calm, honest label:
  "Coverage as of a prior scan (version {stale_dataset_version}) — refreshes on the next data job".
  Distinct from — and does not touch — the existing `not_yet_computed` empty-state copy, which stays
  byte-unchanged for the true fresh-install case.
- **`reports/perf-budgets.md` correction:** the "Iteration 26" section's `uptime` line reads
  `2026-07-26T19:14:25Z` but the table above it labels the same reading window
  `2026-07-26T18:14:25Z–18:14:42Z` — a one-hour mismatch (`reports/perf-budgets.md:3817` vs. the table
  header at `:3825`). Re-derive the true UTC timestamp from `logs/backend.log`'s own timezone-stamped
  boot-log line (not from either conflicting label already in the file) and correct whichever label is
  wrong to match it verbatim. Append/correct-only — no other content in that section changes (TC-10).
- **Backend tests** (bundle into ONE combined pytest invocation per the coordinator constraint — see
  Testing section below):
  - New test in/extending `apps/backend/tests/test_forward_testing_concurrency.py`: stage a competing
    `ForwardReturn` row via a separate committed session/connection to simulate a concurrent writer's
    already-inserted key, then call `backfill_run_forward_returns`/`_insert_run_forward_returns` and
    assert no exception propagates and exactly one row survives for that key (TC-3).
  - New test proving an unrelated `IntegrityError` (any constraint other than the targeted
    `(run_id, symbol, horizon)` uniqueness) still propagates unchanged (TC-4).
  - New tests in `apps/backend/tests/test_api_data.py` (or `test_data_manager.py` — developer's choice,
    keep all three in ONE file): (a) stale-fallback serves the older row's figures +
    `coverage_status: "stale"` + `stale_dataset_version` when exact-match misses but an older row exists
    (TC-5); (b) `coverage_status: "not_yet_computed"` + unchanged payload shape when no row exists for
    any version — regression guard (TC-7); (c) `coverage_status: "current"` after a normal ingest
    finalize refreshes the row for the new `dataset_version` — regression guard (TC-8).

## Agents Required

- backend-data: yes — both fixes are backend engine changes (`forward_testing.py`, `data_manager.py`),
  plus the `perf-budgets.md` timestamp correction and the combined pytest run.
- frontend-ux: yes — `CoveragePanel` in `apps/frontend/app/data/page.tsx` needs the new `stale` label
  state.

Frontend Present: yes

## Files to Create/Modify

- `apps/backend/app/engine/forward_testing.py` -- extend `_insert_run_forward_returns` to tolerate a
  mid-loop autoflush collision (TC-1, TC-2, TC-3, TC-4)
- `apps/backend/app/engine/data_manager.py` -- add the stale-fallback branch to `coverage_from_storage`
  plus the `coverage_status`/`stale_dataset_version`/`stale_computed_at` fields (TC-5, TC-7, TC-8)
- `apps/backend/app/api/data.py` -- confirm/wire the three new coverage fields through `GET /api/data`'s
  existing response (no new route)
- `apps/backend/tests/test_forward_testing_concurrency.py` -- new staged-collision test (TC-3) + new
  unrelated-IntegrityError-propagates test (TC-4)
- `apps/backend/tests/test_api_data.py` (or `test_data_manager.py`) -- new stale/not_yet_computed/current
  coverage_status tests (TC-5, TC-7, TC-8)
- `apps/frontend/app/data/page.tsx` -- `CoveragePanel` renders the new "stale" label + prior-snapshot
  figures when `coverage_status === "stale"` (TC-6)
- `reports/perf-budgets.md` -- correct the Iteration 26 section's mislabeled boot timestamp only (TC-10)
- `docs/handoffs/goal-ops-hardening-iter-27-dev.md` -- dev handoff (required, Definition of Done)

Already updated this iteration (decomposer, additive-only — verify no drift, do not re-edit unless a
genuine mismatch is found): `runs/goal-session-ops-hardening/state/blueprint.md` (TC-12).

Explicitly OUT OF SCOPE (do not touch): audit finding B2 (`Thread.start()` badge-stuck issue), backlog
card B-1107, the cold historical `/backtest` load's owner budget decision, the
`test_forward_testing_serving_split.py` monkeypatch retargeting / dangling imports at `backtest.py:75`
and `mcp/tools.py:38`, any change to `compute_forward_aggregates` / `resolved_forward_aggregate_evidence`
/ `ensure_historical_forward_aggregates_dispatched`'s keying/single-flight semantics / J-08's serving
split, re-triggering a live memory-pressure J-09 failure, the "OWNER BUDGET AMENDMENT" / Revision 1 /
TC-13 / TC-14 sections of `perf-budgets.md`, `resolved_run`'s concurrent-create-once behavior, and
`reports/goal-session-ops-hardening-demo.json`.

## UI Evolution

- New user-facing capability: none — hardening/honesty fix on an already-shipped panel.
- New information displayed: the Data Manager coverage panel now discloses a `coverage_status` label
  ("current" / "stale, as of version X" / "not yet computed") instead of silently rendering the same
  all-zero empty state for two different underlying conditions (a real prior snapshot vs. a genuine
  never-computed DB).
- New user actions: none.
- UI surface changes: `/data`'s existing coverage panel gains one new labeled state (`stale`); no new
  page/panel/route.
- Navigation changes: none.

## Visual Requirements

- Component patterns: reuse the existing `CoveragePanel`/`DefinedMetric`/`Card`/`PanelTitle` components
  already in `apps/frontend/app/data/page.tsx` — no new component library usage, add the stale label as
  additional text/badge content within the existing panel structure (consistent with how the panel
  already handles the `gap_count > 0` warn-tone branch).
- Layout: no layout change — the label slots into the existing coverage panel's metric grid / footer
  prose area.
- Key visual effects: match the panel's existing calm, factual tone (e.g. the `text-warn`/`text-pos`
  tone pattern already used for `gap_count`) — never an alarming/red treatment; this is a routine,
  expected state, not an error.
- States to handle: `current` (unchanged today's rendering), `stale` (new — prior-snapshot figures +
  the disclosed label), `not_yet_computed` (unchanged today's all-zero empty state, byte-identical
  copy).

## Key Test Scenarios

- TC-1/TC-2: two concurrent `/backtest` requests targeting the same never-scanned historical `as_of`
  both return HTTP 200; `logs/backend.log` shows zero "Exception in ASGI application" for that window;
  a full-page (not viewport) browser capture shows normal evidence content, never blank/frozen.
- TC-3/TC-4: staged mid-loop collision is caught and rolled back, loop continues, exactly one row
  survives per key; an unrelated `IntegrityError` still propagates unchanged (narrow catch, not a
  blanket try/except).
- TC-5/TC-6: a `CoverageSnapshot` row under an older `dataset_version` serves `coverage_status: "stale"`
  with non-zero figures + `stale_dataset_version`; the `/data` panel renders the disclosed prior-snapshot
  figures and the exact label text specified in the spec.
- TC-7/TC-8: genuinely-never-computed DB still serves `coverage_status: "not_yet_computed"` with the
  unchanged all-zero shape (regression guard); a normal ingest finalize still serves
  `coverage_status: "current"` with no stale label (regression guard).
- TC-9: J-01, J-03, J-04, J-06, J-09 all replay PASS via golden/smoke (J-09's regression pick must be a
  date that already has a `scanner_runs` snapshot but incomplete aggregates — never a never-scanned
  date, per iteration-state.md "Do not redo").
- TC-10: `perf-budgets.md`'s Iteration 26 timestamp label matches the boot log's own UTC-stamped line
  verbatim; no other content in that section changes.
- TC-11: all new backend tests (TC-3, TC-4, TC-5, TC-7, TC-8) pass in ONE combined pytest invocation,
  building the shared `loaded_engine` fixture at most once — see Testing Notes below.
- TC-12: the actual served JSON field names (`coverage_status`, `stale_dataset_version`,
  `stale_computed_at`) match `blueprint.md`'s Coverage payload row verbatim.

## Testing Notes (host constraint)

The shared 30-year `loaded_engine` pytest fixture costs 1h+ per build on this box and concurrent pytest
invocations fork-lock the host (iter-26 precedent: 3 selectors, one fixture build, 1:25:51). The
developer/reviewer must run ALL new backend selectors for TC-3/TC-4/TC-5/TC-7/TC-8 in a SINGLE combined
`pytest ... -k "..."` invocation — never split across multiple runs, never run the full suite, never run
a second concurrent pytest process. Launch via `setsid nohup ... &` and poll to completion in-turn
(iter-26's pattern) rather than backgrounding across a turn boundary, per the accumulated pump lesson
about subagent-background pytest getting reaped.
