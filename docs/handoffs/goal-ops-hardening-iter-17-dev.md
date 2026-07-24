# goal-ops-hardening-iter-17 Dev Handoff

**Phase:** goal-ops-hardening-iter-17
**Date:** 2026-07-24
**Agent:** developer
**Status:** complete (backend/frontend code + tests); four TCs are OPERATOR-performed, see below

## What Was Built

1. **The load-bearing fix (audit B1): `resolved_forward_aggregate_evidence` now crosses `asof_key`
   boundaries.** Previously the completeness search was filtered to exactly the ONE requested
   `asof_key` (`forward_testing.py:1209` pre-fix); when that identity had zero forward-aggregate rows
   (the common single-latest-date backfill shape — a brand-new latest `ScannerRun` lands before its
   ingest-finalize warm runs), the resolver fell straight through to `not_yet_computed` instead of
   serving yesterday's still-good evidence. Now: if the SAME `asof_key` has no complete version at all
   (0 rows or an in-flight partial warm), the resolver widens its search to STRICTLY OLDER `asof_key`s
   (never a later one — AG-5) and serves the most recent one that IS complete, labeled `refreshing`.
   `not_yet_computed` is now reserved for the true fresh-install shape: no `asof_key` at or before the
   request has EVER had a complete version.
2. **New `evidence_asof` field**, threaded through the SAME returned dict and both serving endpoints
   (`GET /api/backtest`, MCP `query_backtest`) — `ready` → the requested as-of itself; `refreshing` →
   either the same date (a same-identity older-version case, unchanged from iter-16) or a genuinely
   OLDER date (the new cross-boundary case); `not_yet_computed` → `null`.
3. **Audit B5 (cheap win, taken regardless):** the historical (`is_latest == False`) branch in both
   endpoints previously called `forward_aggregates_ingest_cached` unconditionally for every horizon
   (each a cache-hit read+`json.loads`, discarded), then the resolver re-read and re-parsed the same
   rows a second time. Now gated on the resolver's own first read (`evidence_status != "ready"`): an
   already-warmed historical date short-circuits straight to one resolver read; a cold date still
   ensures every horizon is cached and re-resolves once. Byte-identical output either way.
4. **Audit B3 (non-blocking hygiene):** `evidence_generated_at`'s ISO-8601 serialization now carries an
   explicit UTC designator (`+00:00`) instead of a naive, timezone-less string — scoped to this one
   field via a small `_utc_isoformat` helper, not a codebase-wide change to the naive-UTC convention.
5. **Frontend:** `RefreshingEvidenceBanner` (`/backtest`) gains an `evidenceAsof` prop and now displays
   which as-of's evidence is being shown, not only the generation timestamp. The `not_yet_computed`
   `EmptyState` copy was reworded (audit F2/F3): no longer repeats its own title verbatim, and no longer
   tells the user to "run an ingest" (a word used nowhere else in the UI, and a command that presumed
   the user hadn't already started one).
6. **Latency root-cause investigation** (item 4 of the plan): the 11/68 `/backtest` latency breaches
   from iter-16's TC-16 pass were investigated using existing evidence (`tc16-backtest-poll.csv`,
   `logs/backend.log`, `logs/hwmon/hwmon.csv`) plus source-code inspection. Thermal causes and a single
   long-held write transaction were both RULED OUT with direct evidence; two remaining mechanisms (SQLite
   writer/checkpoint contention vs. GIL/threadpool scheduling contention from the ingest's background
   thread) could not be distinguished with available telemetry (`logs/backend.log` carries **zero**
   timestamped lines — confirmed by grep — so no request can be aligned to a wall-clock second). No code
   change was made to the ingest/read write pattern this iteration; recorded as a disclosed,
   not-safely-fixable-blind residual. Full write-up: `reports/perf-budgets.md`'s new dated section.

## Files Changed

- `apps/backend/app/engine/forward_testing.py` -- widened `resolved_forward_aggregate_evidence`'s
  completeness search across older `asof_key`s (grouped by `(asof_key, dataset_version)` pair, never
  `dataset_version` alone — the version stamp is global and can collide across different dates); added
  `evidence_asof` to its returned dict; added `_utc_isoformat` (audit B3).
- `apps/backend/app/api/backtest.py` -- added `evidence_asof` to the `/backtest` response; gated the
  historical ensure-loop on the resolver's own first read (audit B5); updated module docstring.
- `apps/backend/app/mcp/tools.py` -- mirrored both changes in `query_backtest` exactly.
- `apps/backend/tests/test_forward_testing_serving_split.py` -- added 5 new tests (iter-17 TC-1, TC-2,
  TC-4, TC-5, TC-6 per this iteration's own numbering); added `evidence_asof` assertions to 6 existing
  tests; fixed one existing test's expected-value computation for the B3 timezone change; module
  docstring updated.
- `apps/backend/tests/test_api_backtest.py` -- updated the one exact-top-level-key-set assertion
  (`test_backtest_does_not_reserve_regime_or_stock_values`, `loaded_engine`-dependent) to include
  `evidence_asof`. Edited, not run, per this session's standing `loaded_engine` constraint (see below).
- `apps/frontend/app/backtest/page.tsx` -- `RefreshingEvidenceBanner` gains `evidenceAsof` prop;
  `not_yet_computed` `EmptyState` copy reworded (F2/F3).
- `apps/frontend/lib/api.ts` -- `BacktestResponse.evidence_asof: string | null` added.
- `reports/perf-budgets.md` -- new dated section: the latency root-cause investigation, the B5 fix
  write-up, and a PENDING/operator-supervised TC-10 placeholder (mirrors iter-16's own TC-16 template).
- `apps/backend/app/engine/data_manager.py` -- **investigated, not modified.** Traced every commit
  boundary in `_refresh_ingest_aggregates` / `_persist_per_date_coverage_snapshots` /
  `_upsert_coverage_snapshot`: writes commit frequently (per date, per horizon), never one long-held
  transaction. No bounded, verifiable-this-session mitigation was found; see `reports/perf-budgets.md`.

## Tests Run

All commands host-guard-confined (`taskset -c 0-3,8-11`,
`OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=NUMEXPR_NUM_THREADS=4`):

```
cd apps/backend && .venv/bin/python -m pytest tests/test_forward_testing_serving_split.py -v
```
Result: **15 passed** (2.22s) — includes all 5 new tests (TC-1/2/4/5/6) plus the 10 pre-existing tests,
all updated assertions green.

```
cd apps/backend && .venv/bin/python -m pytest \
  tests/test_forward_testing_concurrency.py tests/test_forward_testing.py \
  --deselect tests/test_forward_testing.py::test_walk_forward_asof_dates_are_real_trading_days_with_full_horizon
```
Result: **88 passed, 1 deselected** (653.75s / 10:53 — this pair of files legitimately takes ~11 minutes:
`test_forward_testing_concurrency.py` deliberately rebuilds 60,000-row fixtures per test to induce real
memory-pressure/concurrency conditions, unrelated to anything in this diff). The one deselected test
needs the `loaded_engine` fixture (~80 min, out of scope this session per the standing constraint) — cited
per the phase spec's own instruction, not run.

```
cd apps/backend && .venv/bin/python -m pytest \
  tests/test_data_manager.py::test_finalize_hook_persists_coverage_snapshot_and_warms_aggregates \
  tests/test_data_manager.py::test_finalize_hook_warms_forward_aggregates_for_every_configured_horizon \
  tests/test_data_manager.py::test_finalize_hook_forward_aggregate_warm_avoids_recompute_on_subsequent_read \
  tests/test_data_manager.py::test_finalize_hook_never_raises_even_when_everything_fails \
  tests/test_data_manager.py::test_finalize_hook_forward_aggregates_memory_error_on_first_horizon_aborts_loop \
  tests/test_data_manager.py::test_finalize_hook_forward_aggregates_memory_error_after_partial_success_reports_honestly
```
Result: **6 passed** (1.67s) — the finalize-hook tests that exercise forward-aggregate warming, mirroring
iter-16's own targeted selection exactly (this diff does not touch `data_manager.py`, so this is a
regression check, not new coverage). The FULL `test_data_manager.py` (136 tests, 4689 lines) was NOT run
in its entirety — it was not touched by this diff and a full run would cost significant additional
wall-clock time for zero additional code-path coverage; the 6 tests above are every test in that file
that actually exercises the code this iteration's change interacts with (confirmed by grepping the whole
file for `forward_aggregate`/`evidence` references).

**Total: 109 passed, 1 deselected (cited), 0 failed.**

Frontend:
```
cd apps/frontend && npx tsc --noEmit -p tsconfig.json
```
Result: **0 errors.**

**Not run this session (by design):**
- `test_api_backtest.py::test_backtest_evidence_by_horizon_shape_and_keys` and its `loaded_engine`
  siblings — the ~80-minute fixture; cited, not run, per the spec's own out-of-scope instruction. One
  assertion in this file (`test_backtest_does_not_reserve_regime_or_stock_values`) was still fixed by
  reading, since it would otherwise silently break the first time someone does run it.
- The full `test_data_manager.py` suite (see above).
- A full pytest suite run (standing session constraint).
- `test_db.py::test_create_all_produces_expected_tables` — the pre-existing, unrelated failure carried
  from prior iterations (no schema change this iteration); not re-run, not touched.

## Known Issues

1. **TC-8, TC-9, TC-10, TC-11 status as of this developer session's original pass: not performed — services
   were down and this session could not start them.** Confirmed directly at investigation time:
   `curl localhost:8255/api/health` and `curl localhost:3255/` both refused, no matching `uvicorn`/`next`
   process found (`pgrep` empty). No service was started or stopped to make this determination.
   **UPDATE (2026-07-24, operator pass):** the operator subsequently ran all four and reported results with
   attribution; see "Operator Results (2026-07-24)" below for the transcribed, cross-checked outcome —
   TC-8 not reachable on this DB (an honest data-availability limit, not a code defect), TC-9 closed on the
   DB-level contract (with one process-identity finding flagged for operator follow-up), TC-10 still not
   run (a deliberate, reasoned decision, not an oversight), TC-11 passed and independently reproduced.
2. **The `/backtest` latency root cause is narrowed but not conclusively pinned to one mechanism.**
   Thermal causes and a single long-held write transaction are both ruled out with direct evidence; the
   remaining two candidates (SQLite writer/checkpoint contention vs. GIL/threadpool scheduling
   contention) cannot be distinguished with the logging this codebase currently emits (`logs/backend.log`
   has zero per-request timestamps of any kind, confirmed by direct grep). No code change was made; see
   `reports/perf-budgets.md` for the full evidence trail and a recommendation for what future
   instrumentation would resolve this.
3. **`refreshing`'s no-self-heal behavior (audit B2) is unchanged** — an explicit, documented trade-off
   carried from iter-16, not built this iteration (a page reload is still the only way to pick up a newly
   completed version; no journey step asks for auto-refresh).
4. **The historical (`is_latest == False`) branch's audit-B5 gate depends on `evidence_status != "ready"`,
   deliberately not `== "not_yet_computed"`** — this distinction matters now that the iter-17 widened
   fallback can return `"refreshing"` for a historical date whose OWN evidence has never been computed
   but an unrelated older date's has. Regression-tested directly
   (`test_historical_asof_still_computes_once_even_when_older_fallback_evidence_exists`).

## Operator Hand-off — exactly what to run

Nothing below was attempted this session (agents cannot start/stop services this session, and TC-9/TC-10
are operator-only regardless per the phase spec).

### 1. TC-8 + TC-11 (restart normal services, then two agent/QA-performable checks)

```bash
bash scripts/start-backend.sh    # prod mode, :8255 (same derived port as before)
bash scripts/start-frontend.sh   # prod mode, :3255
```

Then either the operator or a re-dispatched QA/browser agent can:
- **TC-8:** submit a small single-day backfill through the `/data` job form for a date that ADVANCES the
  latest stored run (e.g., the next trading day after whatever `/scanner-runs` currently shows as
  latest — NOT a historical gap date, per this iteration's own lesson), then load `/backtest` while that
  date's forward-aggregate warm is still incomplete. Expect: renders within budget, `refreshing` banner
  showing the PRIOR date's `evidence_asof`, never `not_yet_computed`. Screenshot for the record.
- **TC-11:** `curl -s localhost:8255/api/health` once (expect HTTP 200, `readiness: "ready"`); tail
  `logs/backend.log` for a crash/restart banner since the last recorded one (expect none — this is a
  non-disruptive sanity check, no kill/restart).

### 2. TC-9 (throwaway disposable-DB instance — operator-only, new process boot)

```bash
# 1. A full copy of config.yaml with ONLY database.url repointed at a fresh, never-ingested file:
cp config.yaml /tmp/trendora-tc9-config.yaml
# edit /tmp/trendora-tc9-config.yaml: database.url -> "sqlite:////tmp/trendora-tc9-throwaway.db"
# (an absolute path outside apps/backend/data/ -- cannot collide with the real trendora.db; TRENDORA_CONFIG
# skips the committed-universe merge for a non-default config, which is fine -- this instance only needs
# to boot and serve /backtest's empty state, not a real universe)

# 2. Boot a throwaway backend on an unused port against that config (schema auto-creates on boot --
#    app/main.py calls create_db_and_tables() at startup, confirmed by direct read; no migration step
#    needed):
TRENDORA_CONFIG=/tmp/trendora-tc9-config.yaml CHAIN_BACKEND_PORT=18255 bash scripts/start-backend.sh

# 3. Confirm the empty state (backend-only capture, sufficient per the spec's own documented fallback):
curl -s http://localhost:18255/api/backtest | python3 -m json.tool
# expect: HTTP 200, "evidence_status": "not_yet_computed", "evidence_by_horizon": {}, "evidence_asof": null

# 4. (optional, full browser capture) point a throwaway frontend at the same backend:
CHAIN_BACKEND_PORT=18255 CHAIN_FRONTEND_PORT=13255 bash scripts/start-frontend.sh
# load http://localhost:13255/backtest, screenshot the EmptyState (title "Backtest evidence not yet
# computed", description "No forward-tested evidence exists yet for this date. ...")

# 5. Tear down both throwaway processes. Confirm the REAL apps/backend/data/trendora.db's row counts are
#    unchanged (it was never opened by the throwaway instance -- different file entirely):
sqlite3 apps/backend/data/trendora.db "SELECT COUNT(*) FROM scanner_runs;"   # before vs. after, should match
rm -f /tmp/trendora-tc9-config.yaml /tmp/trendora-tc9-throwaway.db
```

### 3. TC-10 (deep-basis latency re-measurement — operator-only, AG-10-class, ONE pass)

Mirrors iter-16's TC-16 protocol exactly (cooled host, 1 Hz `hwmon` sampler live, thermal watchdog armed,
`taskset -c 0-3,8-11`, `OMP_NUM_THREADS=OPENBLAS_NUM_THREADS=MKL_NUM_THREADS=NUMEXPR_NUM_THREADS=4`): boot
the real backend, trigger a single-date backfill as the warm-trigger job, poll `/backtest` at ~5s
intervals across before/during/after the job (~68 polls), record breach count + max latency in a new
dated `reports/perf-budgets.md` section directly comparable to the existing baseline (11/68, max
12.655s). No code in this diff is expected to move this number in either direction (B1/B5 change which
serving branch is taken and how many times a cache is re-read, not the write pattern implicated by the
investigation) — this pass re-confirms the iter-16 baseline still holds, it does not validate a fix.

## Operator Results (2026-07-24) — transcribed with attribution, cross-checked by developer

The operator ran what was runnable from "Operator Hand-off" above and reported console output, PIDs, ports,
and timestamps verbatim. This developer pass independently re-checked every claim still checkable at
transcription time (read-only DB queries, live endpoint reads, `/proc` process introspection, log
cross-reads) **without** re-running any timed measurement and **without** starting, stopping, or restarting
any of the four services live at transcription time (backend :8255 pid 1079840, frontend :3255, throwaway
backend :18255, throwaway frontend :13255). Full evidence trail, tables, and exact figures are in
`reports/perf-budgets.md`'s new "TC-8 / TC-9 / TC-10 / TC-11 — operator hand-off RESULTS (iter-17,
2026-07-24)" section — this is a summary with attribution; read that section for the complete write-up.

- **TC-8 (as-of-advancing `refreshing`): NOT REACHABLE on this DB, honestly reported as such by the
  operator, confirmed by this pass.** `MAX(daily_prices.date)` = `MAX(scanner_runs.asof_date)` =
  `2026-07-22` (re-verified read-only against the committed DB, exact match) — the price basis has no
  future trading day to backfill, so the live as-of-advancing shape cannot be produced without fabricating
  data (`/api/data/availability`'s 5,383 cells confirm zero cells past `2026-07-22`). The substitute the
  operator tried (`GET /api/backtest?as_of=2026-07-17`, a naturally mixed-version historical key) HEALED via
  the historical create-once carve-out instead of exercising B1's cross-`asof_key` fallback — confirmed
  live (re-requested ~20 minutes later: byte-identical `evidence_asof`/`evidence_generated_at` down to the
  microsecond, `...T00:44:13.188442+00:00`, confirming a cache re-serve, not a fresh recompute). **B1's fix
  rests on its 5 unit tests; it has no live TC-8 exercise this iteration.**
- **TC-9 (`not_yet_computed` on a disposable DB copy): CLOSED on the DB-level contract, independently
  re-confirmed — and one new finding.** Re-read `/tmp/trendora-tc9-throwaway.db` directly (read-only):
  `forward_aggregate_cache` = **0 rows** after the operator's 4 requests — confirms zero computation on a
  cold cache, the strongest evidence this iteration produced for J-08's empty-state contract.
  **New finding, not in the operator's report:** the process currently listening on :18255 (pid **1101499**)
  is NOT the one `logs/backend.log` shows being launched via `scripts/start-backend.sh` (pid **1089510**,
  banner at `00:44:47Z`, which took **121.8 s** to ready — not "~10 s" — and which no longer exists per
  `/proc`). Pid 1101499 was started with a raw `uvicorn ... --host 127.0.0.1` invocation, is missing the
  `memory_cap_mb` `ulimit -v` cap (`unlimited` vs. the main backend's 6144 MB) and `MALLOC_ARENA_MAX`, and
  has no entry in `logs/backend.log` at all. The operator's specific timing figures (1.358/1.612/1.894/
  1.879 s; 1.314 s frontend render) cannot be independently attributed to either process from available
  telemetry (no per-request timestamps anywhere in this stack) and are transcribed as reported, not
  verified. **Flagged for the operator: the throwaway backend currently serving :18255 is running this
  session's largest loaded DB copy (561 MB) without the memory ceiling that protects every other process in
  this project against this exact host's documented OOM/hard-reset failure mode — restart it properly via
  the script or tear it down now that the DB-level evidence is captured.** A real, unflagged 84-90 °C
  thermal spike (peak 90 °C, ~40 s) landed within about a minute of this untracked process's start — still
  under the 95 °C abort threshold with no watchdog trip, but disclosed given this host's history.
- **TC-10 (deep-basis latency re-measurement): still not run — confirmed a deliberate decision, not an
  oversight.** No code change this iteration touches the ingest/read write pattern the iter-16 baseline
  measured, so a re-measurement would only re-measure that baseline (11/68 breaches, max 12.655 s), per the
  operator's own stated reasoning, which matches this iteration's own root-cause section. Remains
  OPERATOR-performed, AG-10-class, outstanding for a future iteration.
- **TC-11 (non-disruptive J-04 sanity): PASS, independently reproduced by this pass.** Re-polled
  `GET /api/health` on :8255 directly: HTTP 200, `readiness: "ready"`, `preflight.verdict: "DEGRADED"` (the
  pre-existing live-vs-seed drift, unrelated to this iteration) — identical to the operator's report.
  `logs/backend.log`'s last 3 launch banners are clean (no crash/traceback immediately following); the
  `MemoryError` lines the file does contain all predate this session's boots by roughly a day and a half (a
  historical incident, not a new crash).

## Pre-Handoff Verification

- [ ] **Service startup** — NOT performed. Services are down and this session cannot start or stop them
  (permission classifier); the phase spec's own operational notes designate this an operator action this
  iteration. See "Operator Hand-off" above.
- [x] **External integrations** — N/A. No adapter, scraper, or external API call was added or changed
  this iteration (AG-9 unaffected).
- [x] **Native dependency binaries** — N/A. No new dependency was added.
