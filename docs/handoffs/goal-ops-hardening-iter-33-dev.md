# goal-ops-hardening-iter-33 Dev Handoff

**Phase:** goal-ops-hardening-iter-33
**Date:** 2026-07-29
**Agent:** developer
**Status:** complete

## What Was Built

- **`scripts/start-frontend.sh` (real file: `incredible_auto_dev/scripts/start-frontend.sh`) now genuinely
  serves production mode.** It has execed `npx next dev` unconditionally since it was written, contradicting
  its own "prod mode" label and blocking J-06's real-browser TTI sweep for the whole session (named first
  by two consecutive evaluators, iter-31 and iter-32). Lines 1-27 (the port-detection block and the
  `NEXT_PUBLIC_API_URL`/`NEXT_PUBLIC_API_PORT` export logic) are BYTE-FOR-BYTE unchanged — verified via
  `git diff` showing only the final `exec` line replaced by a new block appended after it. The new logic:
  - Computes `DIST_DIR="${NEXT_DIST_DIR:-.next}"` and `BUILD_ID_FILE="$DIST_DIR/BUILD_ID"`.
  - **Staleness check** (not a bare directory-existence check): stale/missing iff `BUILD_ID_FILE` is
    absent, OR any real file under `apps/frontend` (excluding `node_modules/` and the dist dir itself) has
    an mtime newer than `BUILD_ID_FILE`. Implemented with `find . \( -path "./node_modules" -o -path
    "./$DIST_DIR" \) -prune -o -type f -newer "$BUILD_ID_FILE" -print -quit` (stops at the first hit via
    GNU find's `-quit`). This naturally covers `package.json`/`package-lock.json` (both live directly under
    `apps/frontend`, not excluded) without a separate check.
  - When stale/missing: runs `npx next build` with its own stdout/stderr inherited (never redirected/
    suppressed, so the build's own error output is always visible). On a non-zero exit, prints a one-line
    wrapper message and exits 1 — **never** falls back to `next dev` and never execs `next start` against
    the unbuilt/broken dist dir.
  - When current: skips the rebuild and logs a one-line confirmation.
  - Either way, finally `exec npx next start -p "$FRONTEND_PORT"` — never `next dev`.
- **`scripts/measure-perf.sh` header comment corrected** (real file:
  `incredible_auto_dev/scripts/measure-perf.sh`, lines ~11-14): removed the now-moot "no reliable way to
  detect [next dev]" caveat and replaced it with a note that the launcher itself now guarantees prod mode.
  No change to any timing/measurement code.
- **New smoke-test file** `apps/backend/tests/test_start_frontend_script.py` (TC-1/TC-2/TC-3), mirroring
  `test_start_backend_script.py`'s real-subprocess-on-an-isolated-port discipline (see Tests Run below for
  the exact design).
- **`merge_ui_test_results.py`'s `_ROW_RE` widened** (real file:
  `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py`) from `UT-`-only to `(?:UT|TC)-`, so
  a `TC-`-prefixed headline FAIL from either merge input now survives into the merged output instead of
  silently falling back to a file-level verdict. Added a new `_self_test()` case,
  `tc_prefixed_fail_survives`, proving this RED-before/GREEN-after (see Tests Run).
- **No production build errors surfaced** — a real `next build` against the current `apps/frontend` tree
  compiled and type-checked cleanly on the first attempt; no `apps/frontend/**/*.tsx` source changes were
  needed.
- **No golden-script repairs needed** — all 8 golden journey-scripts replayed PASS against the fixed
  prod-mode frontend (dry run; see Golden-Script Dry-Run below). The dev/prod switch introduced no markup
  regression that broke any stored assertion.
- **J-06 step-3 code-level on-load audit** — see the table below.

## Files Changed

- `incredible_auto_dev/scripts/start-frontend.sh` -- rewrite: build-if-stale (byte-unchanged port/env
  logic) then `exec next start`; non-zero exit with the build's own error on a genuine build failure, never
  a `next dev`/stale-build fallback.
- `incredible_auto_dev/scripts/measure-perf.sh` -- header-comment correction only (~lines 11-14).
- `apps/backend/tests/test_start_frontend_script.py` -- new file: TC-1/TC-2/TC-3 real-subprocess smoke
  tests for the rewritten launcher.
- `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py` -- widened `_ROW_RE` to accept both
  `UT-` and `TC-` prefixes; added the `tc_prefixed_fail_survives` self-test case.
- No `apps/frontend/**/*.tsx` changes (prod build had no errors dev mode tolerated).
- No `runs/goal-session-ops-hardening/journey-scripts/J-0*.json` changes (all 8 replayed PASS as-is).

**Confirmed untouched (TC-9):** `git diff -- incredible_auto_dev/scripts/dev.sh
incredible_auto_dev/scripts/start-backend.sh` (the real files behind `scripts/dev.sh` /
`scripts/start-backend.sh`) and `project-extensions/host-guard/host-guard.env` all show **zero diff** —
every HOST-GUARD block is byte-unchanged. `scripts/dev.sh`'s frontend subshell is still plain `next dev`,
untouched, as scoped.

## Tests Run

### `merge_ui_test_results.py` self-test

Command: `python3 incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py self-test`
Result: **7 passed, 0 failed** (was 6/1 — the new `tc_prefixed_fail_survives` case fails against the
pre-fix `UT-`-only regex, confirmed RED by manually reverting the regex and re-running; GREEN with the fix
shipped).

### New frontend launcher smoke tests

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_start_frontend_script.py -v`
Result: **3 passed** (`test_missing_build_triggers_build_then_next_start`,
`test_current_build_skips_rebuild`, `test_broken_source_fails_build_and_leaves_no_stray_process`), ~122s
total (each real `next build` on this 4-CPU host-guard-capped host takes roughly a minute).

**Design notes for the retry-proofing (both discovered by direct live probing this session, recorded so a
future reviewer/auditor does not need to re-derive them):**

- **The dev/prod signal is process-ancestry cmdline, not `/proc/<pid>/environ`.** I initially assumed
  Next's own `NODE_ENV=production`/`development` default (set in `next/dist/bin/next`'s `preAction` hook)
  would be visible via `/proc/<pid>/environ` on the listening-socket worker. A live probe (manually booting
  the real launcher on a scratch port and dumping `/proc/*/environ` + `/proc/*/cmdline` across the whole
  process tree) showed `NODE_ENV` is **not present at all** in the environ of the "next-server (vX)" worker
  OR its `sh -c next start ...` / `npm exec next start ...` ancestors — `/proc/<pid>/environ` reflects the
  environment at `execve()` time, not a later in-process `process.env` write. The reliable signal turned
  out to be simpler: `sh -c next start -p PORT` (or `next dev`'s equivalent) literally names the subcommand
  in its own cmdline. The test file's `_resolve_dev_or_start` walks up the process ancestry from the
  listening-socket PID (found the same way `test_start_backend_script.py::_owning_pid` finds it) until an
  ancestor's cmdline names `start` or `dev`.
- **Scratch build directories are relative names directly under `apps/frontend`, never an absolute
  `tmp_path`.** `next.config.mjs`'s `NEXT_DIST_DIR` is resolved via Node's `path.join(projectDir, distDir)`,
  which does NOT treat a leading `/` in the second argument as "reset to filesystem root" (verified:
  `path.join('/a/b', '/tmp/x')` → `/a/b/tmp/x`). Passing pytest's own absolute `tmp_path` would have quietly
  built into an unintended nested directory under `apps/frontend`, not the scratch location the test
  believes it is inspecting. Every scratch dir in the new test file is therefore a short relative name
  (mirroring this repo's own pre-existing `.next-alt-qa`/`.next-verify` convention), created and
  `shutil.rmtree`'d directly under `apps/frontend`.
- **A real `next build` against a distDir name it has not seen before rewrites the committed
  `apps/frontend/tsconfig.json`** (Next auto-appends `<distDir>/types/**/*.ts` to `compilerOptions.include`
  — confirmed by direct observation; this is also why the two pre-existing entries `.next-alt-qa`/
  `.next-verify` are already present in this repo's committed `tsconfig.json`, left over from earlier
  iterations' own scratch builds). An autouse fixture in the new test file snapshots and restores
  `tsconfig.json` around every test so these test-only scratch names never leak into the committed file. I
  also hit and fixed a **real one-time false-positive** this causes: a raw `next build` into a brand-new
  distDir writes `tsconfig.json` (a real source file, correctly in scope for the staleness scan) potentially
  AFTER `BUILD_ID` within the same build, so the very next staleness check can see `tsconfig.json` as newer
  than `BUILD_ID` and rebuild once unnecessarily. This is harmless for the real default `.next` (already
  present in the committed `tsconfig.json`, so real steady-state restarts never hit it) but broke my first
  version of TC-2, which built its "setup" fixture via a raw `next build`. Fixed by having TC-2 run the
  **launcher itself twice** (first invocation absorbs the one-time settling; the second invocation is the
  true skip-rebuild proof) instead of mixing a raw build with the launcher.
- I manually reproduced the same two failures independently before fixing them (ran the suite once with the
  original NODE_ENV-based / raw-build-based design, got 2 real failures, then fixed the test design based on
  the live evidence they surfaced — not by relaxing the assertions).

### Pre-handoff live verification (not a substitute for QA's formal browser sweep)

- Started the real backend (`scripts/start-backend.sh`, port 8255) and the real frontend
  (`scripts/start-frontend.sh`, port 3255) against the committed-seed DB. The frontend correctly detected
  the checked-out `.next` as stale (dev-mode cache, no `BUILD_ID` — confirmed by direct inspection before
  this iteration), ran a real `next build` (compiled + type-checked cleanly, ~20s wall on this host), then
  `next start` came up ("Ready in 266ms").
- `curl` health-check + all 11 J-06 step-1 pages: all HTTP 200 (`/`, `/stocks`, `/stocks/AAPL`, `/sectors`,
  `/themes`, `/data`, `/evidence`, `/scanner-runs`, `/backtest`, `/watchlist`, `/research/regime-lab`).
  `GET /api/health` responded 200 in 0.092s.
- **Both services are left running** for downstream QA/browser lanes (backend :8255, frontend :3255, real
  prod-mode `next start`), per this iteration's operational note.

### Golden-script dry-run replay (all 8, against the now-live prod-mode frontend)

Command (scratch output paths, not the pipeline's own artifacts):
`python3 incredible_auto_dev/scripts/automation/lib/demo_runner.py --mode verify --scripts-dir
runs/goal-session-ops-hardening/journey-scripts --journeys "J-01,J-03,J-04,J-05,J-06,J-07,J-08,J-09"
--base-url http://localhost:3255 ...`

Result: **8/8 PASS, 0 skipped, 0 failed.** No assertion broke from the dev→prod markup switch (no dev-overlay
pill, no CSS-module class-name diff tripped anything) — so **no golden-script repairs were needed** (the
plan's "only if" condition was not triggered). This was a pre-handoff dry run for my own confidence, not the
formal dated QA sweep — that (TC-4/TC-5, appended to `reports/perf-budgets.md`) is the browser-qa-agent's
job, per the plan's own division of labor (a curl timing is not a browser TTI; this iteration's job was to
make the launcher genuinely prod-mode and hand off a verified-bootable target).

## J-06 Step 3 — Code-Level On-Load Audit

For every on-load endpoint the 11 J-06 step-1 pages call, the persisted table/cache it reads, and
confirmation that none performs an unbounded `daily_prices` scan or recomputes an already-ingest-warmed
aggregate:

| Page | On-load endpoint(s) | Reads (persisted table/cache) | Unbounded-scan / recompute check |
|---|---|---|---|
| `/` (Dashboard) | `GET /api/dashboard` | `dashboard_payload(resolved_run(...))` — the resolved `ScannerRun`'s stored regime panel + `candidate_counts_json`. Read verbatim, never re-derived. | No scan — single indexed row lookup. |
| | `GET /api/market-phase` | `market_phase_default_payload`/`market_phase_full_cached` — a derivation computed ONCE per resolved as-of and CACHED behind a `dataset_version` stamp; a repeat read serves the cached value. | No recompute on a cache hit; the underlying derivation (on a cache miss only) is bounded to the resolved as-of, not a `daily_prices` scan. |
| | `GET /api/sectors` | `sectors_payload` — the resolved `ScannerRun`'s stored `SectorScoreRow` children. | No scan — indexed by `run_id`. |
| | `GET /api/themes` | `themes_payload` — the resolved `ScannerRun`'s stored `ThemeScoreRow` children. | No scan — indexed by `run_id`. |
| `/stocks` | `GET /api/stocks` | `stocks_payload` — the resolved `ScannerRun`'s stored `ScannerResult.record_json` rows (per-stock leaderboard), rehydrated verbatim. | No scan — indexed by `run_id`; `record_json` is a stored blob, not a recompute. |
| | `GET /api/dashboard`, `GET /api/themes` | Same as above (regime banner / themes strip). | Same as above. |
| | `GET /api/methodology` | `build_catalog(get_config())` — config only, **no DB access at all**. | N/A — no persisted table read. |
| | `GET /api/evidence` | `build_evidence_payload` — the on-disk certified-claims ledger file (JSON), plus each claim's `compute_drawdown_expectations` (a documented "pure read-compose" over the stored `forward_returns`/ledger data, per-claim bounded). | No `daily_prices` involvement at all. |
| `/stocks/AAPL` (Stock Detail) | `GET /api/stocks/{ticker}` | `stock_detail_payload` — the SAME resolved `ScannerRun`'s stored `ScannerResult` row for this one ticker. | No scan — single indexed row (`run_id` + `ticker`). |
| | `GET /api/stocks/{ticker}/bars` | `bars_asof(session, symbol, asof)` — `SELECT ... FROM daily_prices WHERE symbol = :symbol AND date <= :asof ORDER BY date` (or the in-memory `bar_cache` slice when active). | Bounded to **one symbol**, not a whole-table scan; the MA series (`sma_series`) is computed over that same one-symbol series, never re-derived per request from a wider set. |
| | `GET /api/regime-history` | `get_regime_history` — the stored per-date regime series read verbatim from the immutable `scanner_runs` rows, bounded to dates `<=` the resolved as-of (or the full stored series when `full=true` — still bounded to stored snapshot rows, never a live recompute). | No `daily_prices` read at all; no recompute. |
| | `GET /api/evidence` | Same as `/stocks`'s evidence read above. | Same. |
| `/sectors` | `GET /api/sectors` | Same as Dashboard's. | Same. |
| `/themes` | `GET /api/themes` | Same as Dashboard's. | Same. |
| `/data` | `GET /api/data` | `coverage_from_storage` — the persisted `CoverageSnapshot` row for the resolved `(asof_key, dataset_version)` key (the common case is a zero-query indexed lookup; a genuinely missing row for an EXPLICIT historical `as_of` self-heals once and persists — a documented, deliberate, rare exception, not a per-request recompute) + `recent_runs` (stored `ScannerRun` rows) + `compute_provider_availability`/`compute_macro_availability` (config/env introspection, no DB) + `resumable_imports`/`unfinished_imports` (job-control table rows) + `compute_capacity` (three `SELECT COUNT(*)` scalar aggregates — bounded result, not row materialization) + `read_drift_report` (a tiny on-disk file read). | No `daily_prices` row materialization; `compute_capacity`'s counts are SQL-side scalar aggregates, not a Python-side load of the rows themselves. |
| | `GET /api/data/availability` | `compute_availability` — **one SQL-side `GROUP BY DailyPrice.date` aggregation**, bounded to the benchmark (SPY) trading-calendar's own `[min, max]` date range, returning one row per trading day (not per price row) — plus a single-column read of `ScannerRun.asof_date`. | **Honest disclosure, not a violation:** this endpoint's aggregation query does touch the full `daily_prices` history to compute the per-date distinct-symbol counts (that is what a `GROUP BY` does), but it is a single SQL-side aggregate whose RESULT is bounded (~trading-day count, a few thousand rows for the 30-year basis) — it never materializes individual `daily_prices` rows as Python/ORM objects (the specific pattern AG-8 and this codebase's own `prices.py:141` finding forbid). This is pre-existing, documented behavior (`compute_availability`'s own docstring: "ONE grouped pass over daily_prices"), untouched by this iteration, and distinct in kind from an unbounded whole-table ORM load. |
| `/evidence` | `GET /api/evidence` | Same as above. | Same. |
| `/scanner-runs` | `GET /api/runs` | Lists persisted `ScannerRun` rows (`ORDER BY asof_date DESC`) plus, per run, one `SELECT COUNT(*)` against `ScannerResult` scoped to that `run_id`. | The per-run count is an N+1-shaped loop, but each query is a bounded, indexed `WHERE run_id = :id` scalar count against `scanner_results` — never a `daily_prices` read. |
| `/backtest` | `GET /api/backtest` | `resolved_run` + `compute_run_scorecard` (reads the run's stored `forward_returns`, create-once/cached) + `evidence_by_horizon` via `resolved_forward_aggregate_evidence` — a **pure reader, structurally incapable of calling `compute_forward_aggregates`** for the LATEST view (the on-load case for this page). | For the latest/default view: **no** forward-aggregate compute is ever triggered on this request path (binding "do not redo" from iter-16/iter-20 hardening, re-verified by reading the current handler — unchanged this iteration). A historical `?as_of=` view (not the on-load default) may dispatch a background-thread compute, never on the request thread. |
| | `GET /api/dashboard`, `/api/sectors`, `/api/themes`, `/api/stocks` | Same as Dashboard/Stocks above (supporting panels). | Same. |
| `/watchlist` | `GET /api/watchlist` | Lists the (small, user-sized) `Watchlist` table, enriched via `filtered_stock_rows` — a `ScannerResult` read scoped to an indexed `func.upper(ticker).in_(wanted)` filter over the caller's OWN watchlist tickers (never the whole ~400-row leaderboard) — plus `build_xray_payload`, which reads bounded per-ticker `bars_asof_window` slices (trailing `corr_window_days` only). | No `daily_prices` whole-table read; every price read is bounded to the caller's own small ticker set and a trailing window. |
| `/research/regime-lab` | `GET /api/research/regime-lab` | `regime_lab_cached` — a derivation computed once and cached behind the `dataset_version` + schema-token key; reads already-stored `forward_returns` + stored regime score/label, "never recomputed in the view" per its own docstring. | No recompute on a cache hit; no `daily_prices` involvement (it groups already-stored forward returns, not raw bars). |

**Summary:** across all 11 pages' on-load endpoints, the only place a `daily_prices`-wide query appears at
all is `/api/data/availability`'s single `GROUP BY` aggregation (disclosed above, in kind different from the
forbidden unbounded ORM load), and the only forward-aggregate-adjacent endpoint (`/api/backtest`) is
structurally prevented from recomputing on the request path for the on-load (latest) case. Every other
on-load read is a bounded, indexed lookup against an already-persisted snapshot/cache row.

## Known Issues

- The formal, dated J-06 TC-4/TC-5 browser sweep (real-browser TTI + on-load API latencies for all 11 pages,
  appended as a new `## Iteration 33` section in `reports/perf-budgets.md`) is intentionally NOT done here —
  that is the browser-qa-agent's job per the plan (a curl timing is not a browser TTI). My pre-handoff dry
  run above (curl + golden-script replay) confirms the target is genuinely bootable and prod-mode; it is not
  a substitute for that formal sweep.
- `/api/data/availability`'s `GROUP BY` aggregation over the full `daily_prices` history (see the audit table
  above) is pre-existing, documented, and out of this iteration's scope — flagged here only for honesty per
  TC-6's own wording, not as a defect I introduced or am asking to be fixed this iteration.
- `/api/runs`'s per-run `SELECT COUNT(*)` (N+1-shaped over `scanner_results`, one query per listed run) is
  pre-existing and unrelated to this iteration's surface; noted for completeness, not flagged as a new issue.
- All previously-carried, unrelated items (per the spec's Out of Scope list) are untouched: `run_rows`
  (`forward_testing.py:1195`), the stray `GET /research/factor-lab?all=true` 404, `warmup.py:194`,
  `prices.py:141`, `J-07.json`'s `n=8869` assertion, `test_no_magic_numbers.py`'s red on
  `indicators.py`/`forward_testing.py`, UT-04's fresh-install DB fixture, and
  `test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches.
- J-07's remaining two steps (health-poll latency recording, the induced-memory-pressure abort drill) are
  deliberately deferred to iteration 34, per the spec's rule-5 split.

---

# Fix Notes — QA FAIL retry (2026-07-29)

**QA report:** `reports/qa/goal-ops-hardening-iter-33-qa.md` (verdict FAIL).
Two blockers were listed. Both are fixed below; nothing else was touched.

## Blocker 1 — UT-11 (P1): `/research/regime-lab` cold-cache load with no user feedback

**What QA saw.** On a cold cache the page showed an UNLABELLED grey loading skeleton for 40+ seconds with
zero feedback — no explanation, no elapsed time, no timeout, no retry affordance — because the backing
`GET /api/research/regime-lab?view=pooled` genuinely takes 60-90 s on its first touch per `dataset_version`
(a real CPU-bound derivation over the deep history). One of QA's two curl trials also came back as a raw
error body instead of data. A first-time visitor could not tell "still working" from "broken".

**What I changed (frontend only — no backend code path touched).**

- **New pure module `apps/frontend/lib/lab-load-panel.ts`** — `resolveLabLoadPanel(status, elapsedSeconds)`
  is now the single decision for what a lab renders before its data arrives: a *brief* wait stays a plain
  skeleton (an ordinary fast load must not flash alarming copy), a wait past a short grace window
  (`SLOW_COMPUTE_NOTICE_AFTER_SECONDS = 3`) becomes an explicit **labelled "Still computing — Ns elapsed"**
  state, and a failed fetch becomes an explicitly **retryable** error. It can no longer resolve to an
  indefinite unlabelled skeleton. `formatElapsedSeconds` renders the elapsed label ("42s" / "1m 30s").
  The module reads, recomputes and fabricates NO figure — it only picks which honest state to show.
- **`apps/frontend/app/research/_labs.tsx`**:
  - added `SlowComputeNotice` (the labelled card: what is happening, how long it has been going, that the
    table will appear by itself, and that nothing partial/fabricated is shown meanwhile) and
    `useElapsedSeconds` (ticks the page's OWN measured wait — it never predicts a completion time or
    reports backend progress, so no fabricated ETA);
  - `ResearchError` gained an **optional** `onRetry` that renders a Retry button (existing call sites that
    pass no `onRetry` render byte-identically to before);
  - `RegimeLabPage` now renders from `resolveLabLoadPanel(...)` and passes a Retry handler that re-fires
    the fetch via an `attempt` counter — no full page reload needed.
- Styling reuses existing design tokens only (`border-warn`/`text-warn` like the sibling `WarmingState`
  card; the Retry button reuses the exact button class already used by `app/error.tsx`, so it carries
  hover/focus-visible/active states).

**Deliberately NOT done:** no backend change (the spec's IN SCOPE says "Backend: None"), so QA's Option A
(warm the cache at startup / background job) was rejected — that is a new heavy-compute code path on the
boot lane, i.e. exactly the kind of risky change rule 5 keeps to one per iteration, and it is AG-10
(host-guard) relevant. QA's Option B (honest feedback) is what shipped.

**Verification (real browser, prod-mode frontend on :3255).** The slow path was reproduced deterministically
by patching `window.fetch` in the page to delay only the regime-lab request, so the UI state could be proven
without burning another 90 s CPU-bound backend compute:

| Check | Result | Evidence |
|---|---|---|
| Slow first read shows the labelled notice, not a bare skeleton | PASS — "Still computing — 6s elapsed" + explanation rendered | `reports/qa/goal-ops-hardening-iter-33-evidence/UT-11-fix-computing-notice.png` |
| Notice clears and the real table renders when the read completes | PASS — `regime-lab-by-label` table, first row `Strong risk-on +0.01% n=201789 …` | DOM assertion after the delayed fetch resolved |
| A failed read shows an error card WITH a Retry control | PASS | `reports/qa/goal-ops-hardening-iter-33-evidence/UT-11-fix-error-retry.png` |
| Retry re-fetches in place and recovers to data (no page reload) | PASS — error gone, table present | DOM assertion after clicking Retry |
| Ordinary warm load is unchanged (no notice flash) | PASS — table renders immediately | `reports/qa/goal-ops-hardening-iter-33-evidence/UT-11-fix-warm-load.png` |

## Blocker 2 — TC-01/02/03: launcher smoke tests timed out + left residue in the source tree

**Root causes (two, both in the test module — the launcher script itself is unchanged and was reviewed PASS):**

1. **Timeout too tight for a loaded host.** `_BUILD_TIMEOUT_S` was a hard 300 s. A cold scratch-dir
   `next build` measured ~20-40 s on an idle box but blew past 300 s while the live QA backend + frontend
   were running, so TC-1 and TC-2 both burned the full ceiling and reported an opaque
   "nothing answered on :PORT within 300.0s".
2. **Cleanup could not survive a hard kill.** The previous run was SIGKILLed mid-build, so no `finally`
   block and no fixture teardown ran at all: `apps/frontend/__tc3_intentionally_broken.ts` and six
   `.next-test-*` scratch dirs were left in the source tree (a broken `.ts` there would fail the next
   production build), and the NEXT run's TC-3 then failed instantly on its own
   "already exists — refusing to overwrite" guard. That is why the run showed 3 failures in 640.91 s
   (300 + 300 + an instant guard failure), not three slow builds.

**What I changed (`apps/backend/tests/test_start_frontend_script.py` only):**

- `_BUILD_TIMEOUT_S` now defaults to **900 s** and is overridable per host via
  `TRENDORA_FRONTEND_BUILD_TIMEOUT_S`; the no-build `next start` path has its own separate, deliberately
  short `_START_TIMEOUT_S` (120 s, `TRENDORA_FRONTEND_START_TIMEOUT_S`) so TC-2's skip-rebuild proof stays
  a genuinely fast assertion instead of silently tolerating a rebuild it exists to catch.
- `_wait_for_port_answering` now **fails fast** the moment the launcher process exits without binding, and
  every failure message carries the launcher's own log tail plus the name of the env knob to raise. An
  opaque timeout is no longer the first thing a future reader sees.
- **All cleanup moved into fixtures, and the same cleanup now also runs at fixture SETUP.** New
  `_purge_test_residue()` removes exactly this module's own artefacts (the TC-3 throwaway file and
  `.next-test-*` dirs — keyed to this module's naming, so it can never touch the real `.next`,
  `.next-alt-qa` or `.next-verify`). The autouse `_pristine_frontend_tree` fixture runs it on the way IN as
  well as OUT, so a hard-killed previous run self-heals instead of poisoning the next one. In-test `finally`
  blocks cannot survive SIGKILL; a setup-time purge can.
- The launcher subprocess is now owned by a new **`launcher` fixture** that kills the whole process group in
  ITS teardown, so an assertion failing anywhere in a test body (including before the body's own `try`)
  can never leave a `next build`/`next start` alive on a shared port. pytest finalises in reverse setup
  order, so processes are killed *before* the scratch dirs are removed.
- `tsconfig.json` is now restored to its original **content AND mtime**. Next rewrites that file when it
  meets a new distDir name; even a content-restoring rewrite bumps its mtime, which `start-frontend.sh`'s
  staleness check correctly reads as "sources changed" and would have triggered one gratuitous rebuild of
  the real `.next` after every test run.
- Separately, I restored `apps/frontend/tsconfig.json` to HEAD by hand: it still carried three
  `.next-test-*` include entries written by the hard-killed run. It is no longer in the working diff.

## Tests Run (fix pass)

| Command | Result |
|---|---|
| `cd apps/backend && .venv/bin/python -m pytest tests/test_start_frontend_script.py -v --durations=5` | **3 passed in 120.88s** (TC-1 21.45s, TC-2 42.24s, TC-3 17.07s) |
| `cd apps/frontend && npx tsc lib/lab-load-panel.test.ts --outDir <tmp> … && node <tmp>/lab-load-panel.test.js` | **13 passed** (RED before `lib/lab-load-panel.ts` existed: `TS2307 Cannot find module './lab-load-panel.ts'`) |
| `cd apps/frontend && npx tsc --noEmit` | clean (exit 0) |
| `python3 incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py self-test` | **7 passed, 0 failed** (unchanged) |
| `demo_runner.py --mode verify --journeys J-01,J-03,J-04,J-05,J-06,J-07,J-08,J-09` against :3255 | **8/8 PASS, 0 failed** — no golden-script repair needed |
| 11 J-06 pages + `/research`, `/research/factor-lab`, `/research/phase-severity-lab` via curl | all HTTP 200 |

The full backend suite was deliberately NOT run (project convention — the 30-year `loaded_engine` basis
makes it ~10-11 h, and nothing under `apps/backend/app/` changed this pass).

**Post-run tree/process check:** no `.next-test-*` dirs, no `__tc3_intentionally_broken.ts`, nothing
listening on the 21xxx test ports, `apps/frontend/tsconfig.json` clean against HEAD.

**Services left running** for the downstream lanes: backend `:8255` (HTTP 200 on `/api/health`) and
frontend `:3255` in genuine production mode (`next build` + `next start`, HTTP 200 on `/`).

## Known Issues (fix pass)

- **The 60-90 s cold compute itself is unchanged.** This fix makes the wait honest and escapable; it does
  not make it shorter. Warming `regime_lab_cached` at boot (or on a background job) is the durable
  remedy and is a backend change this iteration's spec puts out of scope — recommended for a future
  iteration, alongside the same treatment for the sibling labs.
- **The sibling research labs share the same shape.** `/research/phase-severity-lab`,
  `/research/regime-phase-factor` and the other all-history labs still render a bare `LabSkeleton` while
  loading. Their reads are materially faster today and none of them was in QA's blocker list, so per
  fix-mode discipline I did not touch them. `resolveLabLoadPanel` is deliberately generic enough for them
  to adopt when a future iteration measures a slow read on one.
- **QA's "Internal Server Error" trial was not reproduced.** The endpoint answered HTTP 200 in 0.267 s
  (warm) on this pass, and re-testing the cold path would mean invalidating the cache and driving two
  concurrent 90 s computes under the memory cap — a heavy-compute event this iteration's scope does not
  cover. Recorded as an open observation for the evaluator: a backend 500 during a concurrent cold compute
  would now surface to the user as the retryable error card rather than a silent stuck skeleton, but the
  underlying cause (a likely resource/lock race between two simultaneous cold computes of the same key) is
  NOT diagnosed and NOT fixed.
- `_kill_process_group` spends up to ~20 s per launched process at teardown (`next start` does not exit on
  SIGTERM within the 10 s grace, so it is SIGKILLed). That is deliberate patience, not a defect, but it is
  most of the non-build time in the 120 s suite.

## Re-verification pass (2026-07-29, later same day) — checkpoint-triggered re-dispatch

This iteration's pipeline had already reached `CLOSURE-PASS` earlier today (review PASS_WITH_NOTES, QA
PASS after the fix round above, audit PASS_WITH_GAPS) — see `reports/phase-goal-ops-hardening-iter-33-closure-verdict.md`.
The engine's own `goal-evaluator` step then started (`telemetry.jsonl`, 12:57:26Z) but the session was
interrupted before it finished and before `session.json` was updated, so on resume
(`session_start` "resume" at 19:00:41Z) the checkpoint system in `lib/checkpoint.sh` correctly treated
iteration 33 as not provably complete (its own documented safety model: "any doubt means re-run") and
re-dispatched the developer step fresh. This is expected behavior of that system, not a bug — recorded
here only so a reviewer/auditor reading this handoff understands why a "dev" step ran again against an
iteration that had already passed once.

I did not rebuild anything from scratch — the working tree already contained this iteration's complete,
correct implementation, untouched since the original pass. I re-verified it end to end rather than
trusting the prior pass's own claims:

- Re-read `incredible_auto_dev/scripts/start-frontend.sh`, `incredible_auto_dev/scripts/measure-perf.sh`'s
  header, `merge_ui_test_results.py`'s `_ROW_RE`, `apps/frontend/lib/lab-load-panel.ts`, and the
  `_labs.tsx` diff — all exactly as described above and in the Fix Notes section.
- Re-ran `merge_ui_test_results.py self-test` fresh: **11 passed, 0 failed** (module has grown more
  self-test cases since the 7/0 figure recorded above; still 0 failed).
- Re-ran `apps/backend/tests/test_start_frontend_script.py` fresh, in full, TWICE (not once) as part of
  this re-verification: **3 passed** both times (~142s each).
- Re-ran `apps/frontend/lib/lab-load-panel.test.ts` fresh via the same `tsc`-compile-then-`node` approach
  the auditor used (no test runner is configured for frontend TS in this repo; Node 22.22 on this host
  rejects a bare `.ts` import and is not compiled with `--experimental-strip-types` TypeScript support):
  **13 passed**.

### A real bug found and fixed during this pass

Comparing `git diff -- apps/frontend/tsconfig.json` after my SECOND full `test_start_frontend_script.py`
run (not the first) showed a leaked include entry: `.next-test-tc2-ayyhuted/types/**/*.ts` survived the
whole test session instead of being restored away by the module's own autouse `_pristine_frontend_tree`
fixture. This is a real defect in test-only cleanup hygiene (it would corrupt a tracked, committed source
file on an unlucky CI run) — not a product defect; `start-frontend.sh` itself and its committed behavior
are unaffected. It reproduced once in 4 full-module runs today (a timing-dependent race, most likely a
`next build` TypeScript-checker write landing between the fixture's snapshot and its restore write on a
loaded host — the exact mechanism was not pinned down deterministically despite two isolated repro
attempts, both of which came back clean).

Fixed defensively rather than chasing the exact race: added `_scrub_tsconfig_scratch_entries()`
(`apps/backend/tests/test_start_frontend_script.py`) — an idempotent, order-independent pass that reads
`tsconfig.json`, strips any `include` entry matching this module's own `.next-test-*` scratch-dist naming,
and rewrites only if something actually needed stripping (so the common clean case never touches the file
at all, never risks reformatting it). Called at both fixture SETUP (so each test's own byte-snapshot is
always captured on an already-clean file) and TEARDOWN (as a final safety net after the existing
byte-restore). Added a new fast, deterministic unit test,
`test_scrub_tsconfig_scratch_entries_removes_only_scratch_dist_entries` (0.06s, no subprocess, no real
build), proving the scrub removes only the injected scratch entry, preserves every legitimate entry
(including the repo's real `.next-alt-qa`/`.next-verify`/`.next` entries) in order, and is a true no-op —
no write, no mtime bump — once the file is already clean. Re-ran the full module a third time after this
fix (now 4 tests): **4 passed in 142.86s**, `git diff -- apps/frontend/tsconfig.json` clean afterward.

**Files changed (this pass):**
- `apps/backend/tests/test_start_frontend_script.py` -- added `import json`, `_scrub_tsconfig_scratch_entries()`,
  wired it into `_pristine_frontend_tree`'s setup and teardown, added the new regression test. No change to
  TC-1/TC-2/TC-3's own bodies or assertions.

No other file changed in this pass. `incredible_auto_dev/scripts/start-frontend.sh`,
`incredible_auto_dev/scripts/measure-perf.sh`, `merge_ui_test_results.py`, `apps/frontend/lib/lab-load-panel.ts`,
`apps/frontend/lib/lab-load-panel.test.ts`, and `apps/frontend/app/research/_labs.tsx` are byte-identical
to the prior pass.

**Known issue (this pass):** the leaked-entry race that motivated the fix above reproduced only once in 4
attempts; I could not force a deterministic repro to prove the scrub closes the exact race (as opposed to
just reducing its probability). The scrub is order-independent and idempotent by construction, so it
should close the class of bug regardless of the precise timing mechanism, but this is reasoned confidence,
not a forced repro. Flagging honestly for the reviewer/auditor rather than claiming more certainty than
the evidence supports.
