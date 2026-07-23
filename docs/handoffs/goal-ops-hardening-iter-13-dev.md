# goal-ops-hardening-iter-13 Dev Handoff

**Phase:** goal-ops-hardening-iter-13
**Date:** 2026-07-23
**Agent:** developer
**Status:** complete

## Continuation note (read this first)

This handoff is written by a **continuation developer turn**. A prior developer turn wrote all the
product/test code below and started two backgrounded pytest runs, then ended before writing any
deliverables (the subagent-resume channel was broken this session). This turn: (1) read and verified the
inherited diff against the plan/spec, (2) read the two completed backgrounded test logs (did NOT re-run
them — each is slow), (3) ran the one remaining targeted test file in the foreground (it turned out to be
fast — see below), (4) performed the live warm-path verification the operator requested over HTTP, with no
service start/stop, and (5) writes this handoff, the implementation summary, and the status update. Every
section below states plainly which parts were **inherited-and-verified** vs **done by this turn**.

## What Was Built (inherited, verified against plan + spec by this turn)

- **`IndexSeriesCache` model** (`apps/backend/app/models.py`) — a STANDALONE, `create_all`-managed table
  mirroring the `ForwardAggregateCache`/`EventStudyCache`/`MarketPhaseCache` docstring convention: columns
  `range_key`, `full` (bool), `dataset_version`, `payload_json`, `created_at`, unique on
  `(range_key, full, dataset_version)`. Confirmed present in the live DB (`sqlite_master` schema read) and
  matches this model exactly.
- **`app.engine.indexes.index_series_dataset_version`** — a NARROW cache stamp scoped ONLY to the
  configured `index_chart.symbols`' stored bars (`max(date)` + `count(*)`, bounded/indexed), deliberately
  not the broad `research._dataset_version` — mirrors `_membership_dataset_version`'s own narrow-stamp
  precedent, per the plan.
- **`index_series_cached_with_status` / `index_series_cached`** (same module) — the self-healing wrapper:
  HIT deserializes the stored payload with zero recompute and re-derives the echoed `asof_date` at read
  time (per goal.md's own technical note — the only as-of-dependent part of this hot key's response); MISS
  computes ONCE via the unchanged `compute_index_series`, persists, and prunes stale rows for the same
  `(range_key, full)` identity. `compute_index_series` itself is UNTOUCHED — confirmed by diff (no changes
  to its body, signature, or other call sites).
- **`GET /api/indexes` hot-key routing** (`apps/backend/app/api/indexes.py`) — routes through
  `index_series_cached` ONLY when `full=True`, `as_of` is absent, and `range` is absent or equals
  `cfg.index_chart.default_range`; every other combination calls `compute_index_series` directly,
  unchanged.
- **Ingest-time warm step** (`apps/backend/app/engine/data_manager.py`, inside
  `_refresh_ingest_aggregates`) — an unconditional single-key warm block mirroring the
  `research_hot_keys`/`forward_aggregates` shape, with its own `MemoryError`-specific isolation (stops
  immediately, calls `_release_process_memory()`, never flips the job's own terminal status) and a
  deferred, function-scoped `from app.engine import indexes` import (breaks a module-load cycle, same
  pattern as `forward_aggregates_cached`'s own deferred import). `"index_series"` is appended to
  `aggregates_refreshed` ONLY when `index_series_cached_with_status` actually persisted a row that call.
  Two docstring/comment lists updated to name the new enum member (`JobProgress` field doc,
  `_refresh_ingest_aggregates` docstring) — no behavior change there, bookkeeping only.
- **New targeted tests** — `test_indexes.py` (+6 tests: MISS computes+persists+byte-identical, HIT serves
  without recompute, invalidation on a new bar for a configured symbol, HIT re-derives current `asof_date`
  without touching the stored payload, dataset-version stamp changes on a configured-symbol bar / is
  unaffected by an unrelated symbol's bar), `test_api_indexes.py` (+3: hot key served from cache and
  byte-identical to a direct call, second request is a genuine HIT with zero recompute calls, an explicit
  `range=3M` or historical `as_of` bypasses the cache entirely and writes no row), `test_data_manager.py`
  (+3: finalize hook warms the hot key and reports it, a second run with no intervening ingest is an honest
  HIT not reported, a forced `MemoryError` in the warm step is isolated and the other five aggregate
  categories still refresh — plus the existing `test_finalize_hook_never_raises_even_when_everything_fails`
  test was extended to also monkeypatch the new function).
- **No change** to `compute_index_series`'s signature/return shape/output for any input, and no change to
  its MCP call site (`app/mcp/tools.py`/`server.py`) — confirmed: neither file appears in `git status`.

## Files Changed

- `apps/backend/app/models.py` -- new `IndexSeriesCache` table (+62 lines).
- `apps/backend/app/engine/indexes.py` -- new `index_series_dataset_version` /
  `index_series_cached_with_status` / `index_series_cached` (+119 lines); `compute_index_series` itself
  unchanged.
- `apps/backend/app/api/indexes.py` -- hot-key routing in the `GET /api/indexes` handler (+15 lines).
- `apps/backend/app/engine/data_manager.py` -- new warm block in `_refresh_ingest_aggregates` +
  `aggregates_refreshed` enum-list docstring updates (+44 lines).
- `apps/backend/tests/test_indexes.py` -- +6 new tests (+158 lines).
- `apps/backend/tests/test_api_indexes.py` -- +3 new tests (+76 lines).
- `apps/backend/tests/test_data_manager.py` -- +3 new tests, +1 extended existing test (+80 lines).
- `reports/perf-budgets.md` -- new dated section this turn: backend-side curl pre-check of the live warm
  path, idle-window cross-read for browser-qa-agent, and a collateral AG-8 observation (see below).
- `docs/handoffs/goal-ops-hardening-iter-13-dev.md` -- this handoff (new, this turn).
- `reports/phase-goal-ops-hardening-iter-13-implementation-summary.md` -- new, this turn.
- `runs/goal-ops-hardening-iter-13/status.json` -- updated, this turn.

`apps/backend/app/engine/forward_testing.py` is confirmed **byte-unchanged** (`git status`/`git diff
--stat` both empty for this path) — TC-12 holds. No file under `apps/frontend/` appears in the diff, per
the plan.

## Tests Run

Command (from `apps/backend/`): `.venv/bin/python -m pytest tests/test_api_indexes.py -v`
Result: **15 passed in 4844.71s (1:20:44)** — run by the prior turn, completed in the background, **not
re-run by this turn** (this file uses the session-scoped `loaded_engine` fixture, which builds the full
30-year DB copy once; the long duration is that one-time fixture build, not a hang). Log verified at
`/home/dennis-chan/.cache/iad/shared/claude-1000/-home-dennis-chan-Git-trendora/7c4009ca-ea36-4a73-a8de-52f50d0c2a0d/scratchpad/test_api_indexes.log`.

Command: `.venv/bin/python -m pytest tests/test_data_manager.py -k "index_series or finalize_hook" -v`
Result: **30 passed, 106 deselected in 130.26s (0:02:10)** — run by the prior turn, completed in the
background, **not re-run by this turn**. Log verified at `.../scratchpad/test_dm_finalize.log`.

Command: `taskset -c 0-3,8-11 .venv/bin/python -m pytest tests/test_indexes.py -v` (host-guard confined:
`OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=NUMEXPR_NUM_THREADS=4`, `TMPDIR`/`TMP`/`TEMP` exported
per the dispatch's environment note)
Result: **23 passed in 0.67s** — **run by this turn, in the foreground, to completion.** This file does
NOT use the slow session-scoped `loaded_engine` fixture (every test builds its own throwaway
`sqlite:///:memory:` engine via `tmp_path`/`_cfg`/`_engine_with_bars`), so the operator's caution that it
might take up to ~1.5h did not apply here — it is a small, fully isolated unit-test file and ran in under a
second.

No other test files were touched or run. The full suite was not run (out of scope, per the plan and the
standing "the suite is test-slow" note). No new failures beyond the pre-existing, documented
`tests/test_db.py::test_create_all_produces_expected_tables` failure (not touched, not re-run this turn —
per TC-10's own carve-out).

## Live Warm-Path Verification (this turn, over HTTP, no service start/stop)

Backend PID 2916728 on :8255 (operator-restarted onto this iteration's code before this turn began), host
port `:3255` frontend. This developer session neither started nor stopped either service.

**Starting state (confirmed):** `index_series_cache` table present (created via `create_all` at the
operator's restart) and **empty** — 0 rows.

1. **Three baseline curl calls** to the hot key while the table was still empty: call 1 (a genuine MISS —
   the wrapper self-heals: computes via `compute_index_series` and persists) measured **0.847s**; calls 2
   and 3 (now HITs against the row call 1 just wrote) measured **0.065s** and **0.070s**. This means the API
   route's own self-healing MISS path already warmed the table before any ingest job ran — expected,
   correct self-healing behavior, not a bug.
2. **Submitted one small, bounded backfill job** over HTTP: `POST /api/data/jobs`
   `{"kind":"backfill","start":"2025-05-30","end":"2025-05-30"}` — a single trading day, picked because it
   already has stored bars (from the committed seed) but no `ScannerRun` snapshot yet. Confirmed AG-9-safe
   before submitting: `_do_backfill` never calls an external fetch provider — it only reads already-loaded
   `daily_prices` bars and creates a snapshot + forward returns; the `source` field the job echoed back
   (`yahoo`, the configured default) is irrelevant to a `backfill` kind, which does no network fetch.
   Confirmed the host was idle and no other ingest job was in flight before submitting
   (`logs/backend.log` — only health polls; `logs/hwmon/hwmon.csv` — load1 0.21, Tctl ~44°C).
3. **Job completed** `status: "ok"` (`started_at` 2026-07-23T02:20:20Z → `finished_at` 02:24:13Z, ~4 min): 1
   snapshot created, 2,725 forward returns inserted, 0 date failures.
   `aggregates_refreshed`: `["latest_snapshot","coverage","membership_timeline","market_phase",
   "research_hot_keys","drawdown_expectations"]` — **`"index_series"` is honestly ABSENT.** This is
   CORRECT, not a defect: the backfill added no new bar to any of the 10 configured `index_chart` symbols
   (SPY/QQQ/IWM/RSP/DIA/^SPX/^NDX/^DJI/^VIX/^TNX all already carried bars through 2026-07-17 from the
   committed seed), so the narrow dataset-version stamp did not change — the warm step's own call found the
   already-self-healed row still fresh (a HIT), and TC-5's own contract says `"index_series"` is reported
   ONLY when the step actually persisted a NEW row that run. Confirmed live: the `index_series_cache` table
   still holds **exactly one row** after the job, with the SAME `dataset_version` (`d2026-07-17-c60522`) and
   the SAME `created_at` timestamp as before the job — it was never re-written.
4. **Byte-identity (AG-3), live:** ran a fresh, direct, uncached `compute_index_series(session, as_of=None,
   range_key=cfg.index_chart.default_range, config=cfg, full=True)` out-of-process against the same live DB
   file, and compared it to the live `GET /api/indexes?full=true` response. **`direct == api` → `True`** —
   full dict equality, including `asof_date: "2026-07-17"`, all 10 `series` entries, and the `range`/
   `ranges` blocks.
5. **Post-warm cached hot-key timing** — 5 further curl calls: **0.088s, 0.084s, 0.088s, 0.088s, 0.088s** —
   flat and consistent, all cache HITs.
6. **Non-hot-key comparison** (`range=3M`, an explicit non-default range — stays on the unchanged,
   uncached, lazy path): **0.575s, 0.582s** — confirms the non-hot-key path is unaffected in cost/behavior,
   and confirmed via a DB read that neither of these two calls added a row to `index_series_cache` (still 1
   row before and after).

**What this does and does NOT prove.** Per this iteration's own plan and iter-5's/iter-12's own precedent,
**curl systematically under-reports what a real Chrome page load's Resource-Timing API shows for the same
call** (call-heavy connection-queuing profile a bare curl call never experiences). The pre-fix baseline this
cache targets (iter-12 G2) was **2138.7-2257.7ms measured by real Chrome**, not curl. The curl numbers above
(0.065-0.09s cache HIT vs. 0.847s cold MISS) are a strong, consistent signal that the fix mechanically
works exactly as designed, but **they are not TC-1/TC-2's canonical control measurement.** As of this
handoff:

- **TC-1 (three independent fresh-navigation real-Chrome `/data` loads, ≤1.5s each) has NOT been produced.**
- **TC-2 (one fresh-navigation real-Chrome `/` spot-check, ≤1.5s) has NOT been produced.**

Both remain browser-qa-agent's own downstream pipeline stage (`Frontend Present: yes` was set solely to
force this real-browser pass, per the plan) — mirroring exactly how iter-12's own G2 developer-pass section
handled the identical situation (a developer-side idle-window cross-read prepares the ground; the canonical
three-load reading is a separate, later browser-qa pass). **Per iter-12's own load-bearing lesson — score
the fix on whether the post-fix control readings actually land ≤1.5s, not on whether the cache/warm-step
code was written — this handoff does NOT claim J-06 passes.** The mechanism is verified correct and live;
the DoD's own measurement instrument has not yet run.

A dated section recording all of the above (plus an idle-window cross-read for browser-qa-agent's own
pass) was added to `reports/perf-budgets.md`.

## Known Issues

**1. TC-1/TC-2's canonical real-Chrome control readings are outstanding — this is the one DoD item not
closed by this handoff, and it is NOT rounded into a "may pass."** See "What this does and does NOT prove"
above. Recommended next step: browser-qa-agent's own three-load `/data` + one-load `/` spot-check pass,
cross-checked against `logs/backend.log`/`logs/hwmon/hwmon.csv` at each reading's exact timestamp, exactly
like iter-12's G2 methodology.

**2. J-01/J-03/J-04/J-05 (required-still-passing) regression-replay evidence is not in this handoff.**
Per this project's own pipeline stage ordering (`.claude/workflow.md`, Browser QA after Dev) and every prior
iteration's own precedent (e.g. iter-9's dev handoff), this is browser-qa-agent's responsibility, not
developer's.

**3. TC-9 (spot-check the other 10 already-in-budget J-06 pages for regression) is not in this handoff** —
same reasoning as #2; this developer turn touched no code path any of those 10 pages/endpoints read.

**4. Collateral, pre-existing, NOT touched or worsened by this iteration: the AG-8
`forward_aggregates_cached` → `compute_forward_aggregates` `MemoryError` at
`apps/backend/app/engine/forward_testing.py:826` reproduced live** during this turn's own single bounded
backfill job's finalize-hook run (`logs/backend.log`, this job's own window) — the exact line this
project's own `reports/perf-budgets.md` iter-12 TC-4 audit-correction addendum already names as a standing,
documented, owner-scoped issue since iter-8, reproducible even on a trivial single-date job given the
current DB's `scanner_results` table size. The job's own pre-existing per-item isolation contract (entirely
untouched by this diff) held correctly: `"forward_aggregates"` was honestly absent from this job's
`aggregates_refreshed`, and the job still completed `status: "ok"` — this iteration's own new `index_series`
warm step follows the identical isolation convention and was unaffected. `forward_testing.py` is confirmed
byte-unchanged (TC-12). Not fixed here — explicitly out of scope (goal.md OUT OF SCOPE section, unchanged
since iter-8) — recorded for visibility only, per the pump operator's own instruction not to touch this
path.

**5. Carried forward, unchanged: `HOST_GUARD_REQUIRE_MARKERS` and the `demo.sh ops-hardening
--session-live` walkthrough** — both explicit owner decisions per goal.md, not touched this iteration.

**6. The pre-existing, documented `tests/test_db.py::test_create_all_produces_expected_tables` failure**
(stale since iter-2, missing table names in its expected set) is unchanged and was not re-run this turn —
per the plan's own carve-out, this is the one pre-existing failure TC-10 explicitly excludes.

**7. This turn did not perform the standard "stop, then start again" service-restart round-trip from
developer.md's pre-handoff checklist.** Per this iteration's own plan ("Agents in this pipeline CANNOT
start/stop services this session") and the dispatching operator's explicit instruction for this continuation
turn, no service control was performed; the operator had already restarted the backend onto this iteration's
code before this turn began (confirmed live: `GET /api/health` → 200, host-guard caps live in the launch
banner, `index_series_cache` table present via `create_all`). This turn only issued HTTP requests against
that already-running process — no independent stop/start cycle was run. No further service action is needed
right now (the live verification above already exercised the restarted process end-to-end); flagged here
only as an explicit deviation from the standard checklist item, not an oversight.
