# goal-ops-hardening-iter-3 Execution Plan

Session: `ops-hardening` · Iteration 3 · Depth: full · Target journey: J-05 (partial → passing) ·
Required-still-passing: J-01, J-03, J-04. Backend-only correctness fix (closes iter-2 audit findings
B1/B2) plus J-05's last unmeasured acceptance step (a live health/memory measurement). No new UI, no
new Must-have journey content, no `docs/goal.md` edit.

**Alignment check:** this iteration is a direct, tightly-scoped continuation of goal.md's "compute at
ingest, serve from storage" principle and the iter-2 evaluator's own declared #1 blocker to
GOAL_ACHIEVED. No drift, no scope creep — the spec itself already deviates deliberately from the
evaluator's suggested bundling (deferring J-06) with a clearly stated, sound reason (don't mix two
risky changes in one diff). Nothing here contradicts an anti-goal.

## What to Build
- Widen the ingest finalize trigger so a successful `fetch` or `expand` job (today only
  `backfill`/`both`/`rebuild`) also refreshes the current-stamp `coverage_snapshot` row — closes audit
  finding **B1**: a `fetch`/`expand` that changes the bars manifest currently leaves `/data`'s default
  coverage view silently showing a false all-zero "not yet computed" sentinel until an unrelated
  restart or backfill/rebuild.
- Gate that new refresh so a zero-work `fetch`/`expand` (the common offline case) pays **zero extra
  compute and writes nothing** — the check is a cheap `_membership_dataset_version` comparison + one
  row lookup, never a call into `_compute_coverage_uncached`.
- Reclaim stale `coverage_snapshot` rows left under a superseded `dataset_version` via **one bounded
  SQL `DELETE`**, not a per-row Python scan — closes audit finding **B2**.
- Touch nothing else: the `as_of=None` cold-boot no-whole-table sentinel, `aggregates_refreshed`'s
  null-for-fetch/expand contract, and every J-01/J-03/J-04 shipped field stay exactly as shipped.
- Live-measure J-05's one remaining unmeasured acceptance step: dispatch one real heavy ingest job
  against a `scripts/start-backend.sh`-launched process, poll `GET /api/health` at ≤250ms intervals
  for the job's duration, sample `/proc/<pid>/status` `VmPeak`/`VmSize`, record both in
  `reports/perf-budgets.md` (TC-8/TC-9).
- Dev handoff documenting the B1/B2 before/after and the measured numbers.

## Agents Required
- developer: yes -- implement the B1/B2 backend fix in `apps/backend/app/engine/data_manager.py`
  (TDD, extending `test_data_manager.py`), then run the live TC-8/TC-9 heavy-job measurement and record
  it in `reports/perf-budgets.md` + the dev handoff. No frontend files touched.
- backend-data: yes -- 100% of this iteration's code change is backend (ingest finalize hook +
  `coverage_snapshot` persistence/reclaim).
- frontend-ux: no -- zero frontend file changes; the existing `/data` coverage panel (built iter-2)
  already renders whatever `GET /api/data` serves.

## Frontend Present
yes

Frontend Present: yes — set because the fix's correctness is user-visible on the existing `/data` page
and must be confirmed live via browser-qa (TC-11), exactly as the phase spec itself states — **not**
because any frontend file changes this iteration.

## Files to Create/Modify
- `apps/backend/app/engine/data_manager.py` --
  1. Widen `_run_job`'s finalize gate (currently `:3759-3761`: `if final_status in ("ok","partial") and
     (prog.kind in _BACKFILL_KINDS or prog.kind in _REBUILD_KINDS):`) with a **new, separate** branch
     for pure `fetch`/`expand` kinds. See "Implementation gotchas" below — this is the exact surface
     that produced an undetected regression once already this session.
  2. Add a cheap "already fresh" gate (new helper near `refresh_coverage_snapshot`, `:1042`) comparing
     the current `_membership_dataset_version` (`app.engine.research`) against the existing
     current-stamp `coverage_snapshot` row, without invoking `_compute_coverage_uncached`.
  3. Widen the stale-row prune: today's `_upsert_coverage_snapshot` (`:985-1023`) only deletes a stale
     row for the *same* `asof_key` (`:994-999`). Add a bulk `DELETE ... WHERE dataset_version !=
     :current` (across all `asof_key`s) in the same shared path so every caller (finalize hook +
     `warmup.py`'s boot safety net, which calls through the same upsert) benefits automatically. `delete`
     is already imported from `sqlalchemy` at line 46 — no new import needed.
- `apps/backend/tests/test_data_manager.py` -- extend for TC-1/TC-2/TC-3/TC-4/TC-6/TC-7, reusing the
  existing `finalize_hook_engine` fixture and the patterns already at
  `test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates` (~:1041),
  `test_finalize_hook_coverage_snapshot_byte_identical_to_fresh_compute` (~:1063), and
  `test_finalize_hook_makes_no_network_call` (~:1163).
- `apps/backend/tests/test_api_data.py` -- re-run (do not rewrite) TC-5's existing cold-sentinel/
  zero-prefill coverage; touch only if the new code path affects an assertion already there.
- `reports/perf-budgets.md` -- append one new dated, lettered section (next letter after Item K)
  recording TC-8 (health polled ≤250ms throughout, all responses 200 within 1s) and TC-9 (peak
  VmPeak/VmSize vs the 6144 MB `ulimit -v` cap, with margin) — match Items J/K's measurement rigor and
  format.
- `docs/handoffs/goal-ops-hardening-iter-3-dev.md` -- new dev handoff: B1/B2 before/after + the
  TC-8/TC-9 measured numbers (required by DEFINITION OF DONE).

**Not modified (confirm untouched):** `docs/goal.md` (lint-final); `apps/frontend/**` (no frontend
scope); `config.yaml`'s `max_range_days`/`import_chunking` and `scripts/start-backend.sh`'s
`ulimit`/`MALLOC_ARENA_MAX`/logfile mechanics (J-01/J-03/J-04 shipped — "do not redo" per
`iteration-state.md`); `runs/goal-session-ops-hardening/state/blueprint.md` (already updated by the
goal-decomposer for this iteration — Coverage payload row retagged `[TARGET, iter-3 building]`, stale
iter-2 tags removed — no further edit needed); `apps/backend/app/models.py` (no schema change — the
existing `CoverageSnapshot(asof_key, dataset_version, payload_json, computed_at)` already has
everything B1/B2 need).

## Implementation gotchas (read before coding)
- `_FETCH_KINDS = ("fetch", "both")` and `_EXPAND_KINDS = ("expand",)` — but `"both"` is **also** in
  `_BACKFILL_KINDS = ("backfill", "both")`, so `"both"` already runs through the existing rich
  `_refresh_ingest_aggregates` path today. The new branch must fire **only** for a job whose kind is
  pure `"fetch"` or `"expand"` — explicitly excluding `"both"` — or `"both"` would run the coverage
  refresh twice in one job. Write it as `elif` (or an explicit `and prog.kind not in _BACKFILL_KINDS`),
  never a bare additional `or`.
- Per IN SCOPE's literal wording ("via the existing `refresh_coverage_snapshot` — no second
  derivation") and per OUT OF SCOPE's ban on changing `aggregates_refreshed`'s nullability contract,
  the new branch should call `refresh_coverage_snapshot(...)` directly — **not** the full
  `_refresh_ingest_aggregates(...)` — and must not set `prog.aggregates_refreshed`. (The served field is
  already gated to `None` for non-backfill-like kinds via `_breakdown_computed`, `:3351`/`:3375-3376`,
  but calling the narrower function keeps the diff surgical and avoids incidentally running the
  per-date/market-phase/research-hot-key warm loops for a fetch/expand — not asked for here.)
- The "skip when unchanged" gate must run **before** anything that could invoke
  `_compute_coverage_uncached` — TC-2 asserts a call-count of zero for a zero-bar fetch.
- Do not extend the `as_of is not None` self-heal to the default path — that reopens the CRITICAL
  cold-boot whole-table-compute regression J-05 exists to remove (named explicitly by both the spec and
  the iter-2 audit as the wrong fix).

## Live measurement task (developer-owned, TC-8/TC-9)
- Launch via `scripts/start-backend.sh` (never `dev.sh`) so the real 6144 MB `ulimit -v` /
  `MALLOC_ARENA_MAX=2` are live.
- Dispatch one real heavy job — a full `rebuild`, or (likely faster and equally "heavy" for this
  measurement) a large multi-day `backfill` such as J-03's own >370-day example range
  (`2025-06-01` → `2026-07-17`) — while polling `GET /api/health` at ≤250ms intervals and sampling
  `/proc/<pid>/status` `VmPeak`/`VmSize` on the same cadence, for the job's full duration.
- Record every health poll's status (assert all 200 within 1s) and the peak VmPeak/VmSize with margin
  under the 6144 MB cap; append to `reports/perf-budgets.md` and summarize in the dev handoff.
- Run targeted tests only (`test_data_manager.py`, `test_api_data.py` subsets) — do not run the full
  backend suite (this project's 30-year-basis full pytest run takes hours; broader regression
  confidence comes from the reviewer/QA stage, not a full local run here).
- Before running tests or the measurement harness: `export TMPDIR TMP TEMP` to
  `/home/dennis-chan/.cache/iad/iad.goal-ops-harde-9378d91d.95478` (this pipeline run's isolated
  temp-file directory).

## UI Evolution
- New user-facing capability: none new — the existing `/data` coverage panel (Universe/Symbols/
  Trading-days/Snapshot-dates, built iter-2) simply stops going stale/false-zero after a `fetch`/
  `expand` job.
- New information displayed: none — no new field or panel.
- New user actions: none.
- UI surface changes: none — same `/data` page, same coverage panel, same job form.
- Navigation changes: none.

## Visual Requirements
- Component patterns: N/A — no component changes; the existing coverage panel/cards on `/data` are
  reused unmodified.
- Layout: N/A — unchanged.
- Key visual effects: N/A — unchanged.
- States to handle: the panel's existing states must keep rendering correctly — the honest "not yet
  computed" zero sentinel (TC-5, on a genuinely fresh DB) and populated real values (TC-11, after a
  fetch that lands a bar) must each show their correct, distinct state; no new loading/error treatment
  is introduced.

## Key Test Scenarios
- TC-1: committed DB with a current `coverage_snapshot` row; a `fetch` lands ≥1 new bar and completes →
  a fresh row is persisted for the current stamp; `GET /api/data`'s default block matches a fresh
  independent `_compute_coverage_uncached` call.
- TC-2: same setup, fetch lands zero new bars (common offline no-op) → `_compute_coverage_uncached`
  never invoked (call-count assertion), no row written or re-timestamped.
- TC-3: an `expand` job that changes the bars manifest → same fetch-path finalize behavior, byte-
  identical to a fresh compute.
- TC-4: multiple stale-`dataset_version` rows across different `asof_key`s → all deleted in one bounded
  SQL delete when the dataset version next changes, leaving only current-stamp rows.
- TC-5 (regression): backend just booted, zero ingest this session, default `GET /api/data` → still
  HTTP 200 honest all-zero sentinel, zero `daily_prices` queries beyond the pool file read (iter-2's
  TC-6/TC-9 unregressed).
- TC-6: fetch/expand-triggered refresh's `payload_json` byte-identical field-by-field to an independent
  fresh `_compute_coverage_uncached` call.
- TC-7: zero outbound network/socket activity during the widened finalize trigger (AG-9).
- TC-8/TC-9 (live): real heavy job against a `start-backend.sh` process — `/api/health` all-200 within
  1s throughout; peak VmPeak/VmSize under the 6144 MB cap, margin recorded.
- TC-10 (regression): full J-01/J-03/J-04 test suites (breakdown/chunking/boot/readiness/logfile) pass
  unedited.
- TC-11 (browser-qa, target journey): a fetch that lands a new bar completes via `/data`'s job form →
  reloading the default `/data` page shows real non-zero Universe/Symbols/Trading-days/Snapshot-dates,
  not the all-zero sentinel (the literal B1 regression, now fixed).
- TC-12: `docs/handoffs/goal-ops-hardening-iter-3-dev.md` documents the TC-8/TC-9 numbers and a concrete
  before/after description of the B1 fix.
- Required-still-passing regression (browser-qa): J-01 (backfill honors range + zero-work honesty),
  J-03 (no per-run range cap, chunked execution), J-04 (non-blocking boot, visible status, crash/
  interrupted-job presentation) — re-exercise per goal.md's own acceptance steps; must remain green.
