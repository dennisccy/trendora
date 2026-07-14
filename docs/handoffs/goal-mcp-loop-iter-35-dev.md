# goal-mcp-loop-iter-35 Dev Handoff

**Phase:** goal-mcp-loop-iter-35
**Date:** 2026-07-14
**Agent:** developer
**Status:** BLOCKED — implementation complete, verification incomplete (environment outage, see below)

## READ THIS FIRST — verification status

Implementation is complete and has been thoroughly reviewed line-by-line (including a full manual trace
of every new code path against the actual runtime data structures), but **the backend test suite,
frontend typecheck, and service-startup checks could not be executed** because the sandbox's `Bash` tool
stopped working partway through this session and never recovered despite ~16 retries over an extended
period, plus two independent confirmations via a fresh sub-agent dispatch (same environment, same
failure). Every single Bash invocation — including bare `echo`, `true`, `pwd` — returned exit code 1 with
zero output. A `Write` call to the harness scratchpad under `/tmp` failed with `EDQUOT` (disk quota
exceeded), while a `Write` to a file under the repo itself succeeded — so the failure is isolated to the
filesystem backing `/tmp` (which is also where the Bash tool's own exec wrapper appears to write), not the
repo checkout. The most likely root cause: this session ran several `_fresh_seed_engine`-based pytest
fixtures (each materializes the full 30-year/590-symbol committed seed into a fresh SQLite file under
`$TMPDIR`), and the pipeline's per-phase isolated `TMPDIR` (`/tmp/iad.goal-mcp-loop-iter-35.2778307`) is
almost certainly size-capped — cumulative usage across those fixture instantiations plus a full run of
`test_data_manager_jobs_pipeline.py -v` (which itself failed with a SQLite "disk I/O error" partway
through) most plausibly exhausted it.

**What this means for the reviewer/QA stage:** treat this phase as **NOT YET GREEN**. The code below is
implemented per spec and per the blueprint's own iter-35 Data Contract row (which independently confirms
every module/function name, config path, and wiring point I used — see "Blueprint conformance" below), but
the following have **NOT been confirmed by execution** and MUST be run before this phase can be considered
passing:

- `cd apps/backend && .venv/bin/python -m pytest tests/test_readiness.py -v`
- `cd apps/backend && .venv/bin/python -m pytest tests/test_data_manager_jobs_pipeline.py -v`
- `cd apps/backend && .venv/bin/python -m pytest tests/test_health.py tests/test_themes.py tests/test_sectors.py tests/test_indexes.py tests/test_config.py tests/test_config_engine.py -v`
- `cd apps/frontend && npx tsc --noEmit` (or the project's usual frontend build/typecheck)
- `scripts/dev.sh` service-startup check (backend + frontend both start cleanly, no port conflicts)
- The regression-replay script from NOTES (`scripts/automation/lib/demo_runner.py --mode verify`)

Three harmless diagnostic probe files were created during outage triage and **must be deleted before this
branch is considered clean**: `.iter35-diskprobe.tmp`, `.iter35-diskprobe2.tmp`, and `.iter35-probe3.tmp`
at the repo root (all trivial placeholder content, not referenced anywhere, safe to `rm`). Bash itself
returned successfully exactly once mid-outage (a single `echo`), which is why cleanup was attempted then,
but a `Write` to `/tmp` immediately afterward still failed with `EDQUOT`, confirming `/tmp` was still
exhausted at that moment — the one success looks like a fluke, not a real recovery, and Bash went back to
failing on every subsequent call for the rest of the session.

**What WAS actually verified by real execution before the outage began** (not just reviewed):
- `apps/backend/tests/test_drift.py` — **13/13 passed** (full run, see below).
- `apps/backend/tests/test_api_data.py` — **45/45 passed** (full run, including the 2 new drift-field
  tests), confirming the additive `GET /api/data` `drift` field end-to-end against a real FastAPI-router
  call.
- `apps/backend/app/config.py` config loading — confirmed via a direct `load_config()` call that the new
  `data_quality.drift` block and the extended `readiness.severity` (now including `drift: degraded`) parse
  correctly against the real `config.yaml`.

Everything else below was implemented following this project's exact established patterns (mirroring
`app.engine.evidence`'s path-resolution idiom, `app.engine.readiness`'s `_apply`/worst-severity
composition, and `StorageCapacityPanel`/`RebuildPanel`'s frontend Card/PanelTitle shape) and was manually
traced end-to-end against the actual runtime types (`Bar`, `JobProgress`, `ImportCheckpoint`) line by line,
but I am flagging it as unverified rather than claiming a pass I could not observe.

## What Was Built

J-21 (backlog B-304, overlap check only): a live-vs-seed drift monitor. When a Fetch/Expand/`both` job's
provider returns bars for dates already covered in the committed seed, the platform byte/fixed-precision
compares the last `overlap_days` common dates against `data/seed/prices/{symbol}.csv`; a mismatch is
classified an "adjustment seam" and named (symbol + exact dates). The result is a single persisted
drift-report artifact, re-read verbatim by both the daily preflight verdict (a new 4th `drift` component,
alongside servability/freshness/integrity) and an additive `/data` UI section.

- **New PURE module `app/engine/drift.py`**: `build_drift_report(fetched_bars, seed_bars, *, overlap_days,
  reference)` (byte/fixed-precision compare, 6-decimal fixed formatting — never a tolerance window),
  `resolve_drift_report_path()` (env `TRENDORA_DRIFT_REPORT_PATH` else `config.data_quality.drift.report_path`,
  mirrors `evidence.resolve_ledger_path` exactly), `write_drift_report()` / `read_drift_report()` (single
  writer/reader; missing artifact -> `None` inert; unparseable -> honest `status: "unreadable"`, never
  raises).
- **Fetch-pipeline wiring** (`app/engine/data_manager.py`):
  - `_run_chunked_fetch` gained two new optional kwargs (`overlap_sink`, `overlap_days`, both default
    inert) — when given, it accumulates each "ok" result's RAW fetched bars per symbol (bounded to the
    tail `overlap_days` as they arrive), captured BEFORE the existing INSERT-new-only `_existing_dates`
    filter (because a date already stored is exactly the "overlap" the drift check needs to see — the
    INSERT-new-only DB write would otherwise silently discard a re-adjusted value for an already-covered
    date, which is the whole point of this feature).
  - New `_check_drift(cfg, seed_dir, fetched_bars, prog, scrub)` helper: loads the committed seed via the
    EXISTING `SeedProvider` (no second CSV parser), calls `build_drift_report`, writes the artifact. Every
    failure inside is caught and recorded (scrubbed) — a validation-stage problem can never crash the
    primary fetch job.
  - `_run_job` now initializes `overlap_sink` (or `None` when `config.data_quality.drift.enabled` is
    False), threads it into `_run_chunked_fetch`, and calls `_check_drift` immediately after the existing
    `prog.complete_stage("fetch")` guard — strictly inside the fetch-only branch, so it never runs on a
    `resumable` pause (bars were discarded, nothing to honestly compare) or on the `skip_fetch`
    resume-at-backfill path (zero provider calls, nothing new fetched).
- **`app/engine/readiness.py::compute_preflight`**: a 4th `_apply("drift", ok, detail)` component after
  `integrity` — `ok` when the artifact is absent (no fetch has run yet) or `status == "clean"`; breached
  (naming affected symbols) when `status == "drift"`; breached with an honest reason when the artifact
  exists but is unreadable. A tiny-file read only, never a DB scan on the ~2s health poll. The existing
  servability/freshness/integrity components are untouched.
- **`app/config.py`**: new `DriftCfg` (`enabled: bool = True`, `overlap_days: int = 20` validated `>= 1`,
  `report_path`) + `DataQualityCfg` (wraps `drift`), default-populated on the `Config` aggregator so a
  config predating this block still loads. `ReadinessCfg._validate`'s `required_components` extended from
  `{servability, freshness, integrity}` to include `drift`.
- **`GET /api/data`** (`app/api/data.py::data_overview`): additive `"drift": read_drift_report()` field,
  same reader `compute_preflight` uses — no recompute, no second parse path.
- **`config.yaml`**: new `data_quality.drift` block (`enabled: true`, `overlap_days: 20`, `report_path`)
  + `drift: degraded` added to `readiness.severity`.
- **Frontend** (`apps/frontend/app/data/page.tsx`): new `DriftReportPanel` component (mirrors
  `StorageCapacityPanel`'s `Card`/`PanelTitle` shape) reading the additive `drift` field from the EXISTING
  `/api/data` client call — no new fetch. Four states: absent (quiet, "no fetch has run yet"), clean
  (quiet, `--pos`), drift (loud amber `border-warn bg-warn/10 text-warn`, lists every affected symbol +
  dates + "adjustment seam"), unreadable (same loud treatment, honest fallback message). `lib/api.ts`
  gained `DriftReport` / `DriftAffectedSymbol` types and the `drift` field on `DataOverviewResponse`.
  `preflight-banner.tsx` / `readiness-provider.tsx` / `layout.tsx` were confirmed (by the orchestrator's
  plan and re-confirmed by me reading `preflight-banner.tsx` in full) to need ZERO changes — the banner
  already renders `preflight.reasons` generically, so a new `drift` reason string surfaces automatically.

## Blueprint conformance

`runs/goal-session-mcp-loop/state/blueprint.md` already carried the full iter-35 Data Contract row (line
118) and IA row (line 89) before I started, written by the goal-decomposer — no developer edit was needed
(confirmed by reading both). Notably, the blueprint independently specifies the exact same module names,
config keys, and wiring point I arrived at (`app.engine.drift:build_drift_report`,
`resolve_drift_report_path()`, the `_apply("drift", …)` component, `config.data_quality.drift.*`) — strong
corroborating evidence that the design choices I had to work out myself (the plan did not specify the
`overlap_sink` accumulator mechanism) are aligned with the architecture's own intent.

## Files Changed

Backend:
- `apps/backend/app/engine/drift.py` -- NEW. `build_drift_report`, `resolve_drift_report_path`,
  `write_drift_report`, `read_drift_report`.
- `apps/backend/app/engine/data_manager.py` -- `_run_chunked_fetch` gains `overlap_sink`/`overlap_days`
  kwargs + accumulation; new `_check_drift` helper; `_run_job` wiring (init + call site); new imports
  (`Bar`, `SeedProvider`, `drift` module).
- `apps/backend/app/engine/readiness.py` -- `compute_preflight` gains the 4th `drift` component; new
  import.
- `apps/backend/app/config.py` -- new `DriftCfg`/`DataQualityCfg`; `Config.data_quality` field;
  `ReadinessCfg._validate` required-component set extended.
- `apps/backend/app/api/data.py` -- additive `"drift"` key on `data_overview`; new import.
- `config.yaml` -- new `data_quality:` block; `drift: degraded` added to `readiness.severity`.
- `apps/backend/tests/test_drift.py` -- NEW, 13 tests (build_drift_report fixture matrix incl. the
  byte-vs-tolerance trap and the overlap-window-boundary case; path resolution; write/read round-trip +
  missing/unparseable resilience). **VERIFIED: 13/13 passed.**
- `apps/backend/tests/test_api_data.py` -- +2 tests (additive `drift` field absent-on-cold-DB, equals
  `read_drift_report()` verbatim). **VERIFIED: 45/45 passed (whole file).**
- `apps/backend/tests/test_readiness.py` -- `_point_ledgers_at` extended to isolate the new drift-path env
  var; `test_preflight_fixture_matrix` + `test_preflight_components_always_carry_configured_severity`
  updated for the 4-component shape; the two `ReadinessCfg(...)` direct-construction tests that predated
  `drift` fixed (severity dict now includes it so they still exercise their OWN intended failure mode); one
  new test added for "missing drift alone is rejected"; one new test for "all four components accepted";
  5 new dedicated tests for the drift component's behavior in `compute_preflight` (absent/clean -> ok;
  drift -> breached naming symbols; unreadable -> breached; worst-severity composition holds with 4
  components). **NOT YET RUN — see verification status above.**
- `apps/backend/tests/test_data_manager_jobs_pipeline.py` -- new imports (`csv`, `Path`, `RateLimitError`,
  `symbol_to_filename`, `read_drift_report`); new `_light_fetch_engine` helper (a schema-only engine,
  deliberately NOT `_fresh_seed_engine`, to avoid a 5th full 30-year seed load in this already-heavy file);
  new `_FixedBarsProvider` + `_write_seed_csv` helpers; 4 new end-to-end wiring tests (writes report on a
  completed fetch — both a drift and a clean case; does not run on a resumable pause; does not re-run on
  a skip-fetch/backfill-only resume, proven via a call-counting "telltale" provider). **NOT YET RUN.**
- `apps/backend/tests/test_health.py` -- the additive-`preflight`-field test's exact component-set
  assertion extended to include `drift`. **NOT YET RUN.**
- `apps/backend/tests/test_themes.py`, `test_sectors.py`, `test_indexes.py`, `test_config.py`,
  `test_config_engine.py` -- each carries an inline synthetic `readiness.severity` config dict (used to
  construct a full `Config(...)` for engine-isolated unit tests unrelated to readiness); each now includes
  `"drift": "degraded"` so `ReadinessCfg._validate`'s extended required-component check doesn't break
  config construction for these UNRELATED test files. **NOT YET RUN** (these files' OWN test suites, not
  just the readiness-specific ones, need a green run to confirm this didn't regress anything).

Frontend:
- `apps/frontend/lib/api.ts` -- new `DriftReport`, `DriftAffectedSymbol` types; additive `drift` field on
  `DataOverviewResponse`.
- `apps/frontend/app/data/page.tsx` -- new `GitCompare` icon import; new `DriftReportPanel` component;
  wired into the `state.kind === "ok"` render tree right after `StorageCapacityPanel`.

Confirmed untouched (per the plan's explicit "Do NOT touch" list, verified by reading each in full):
`apps/frontend/components/preflight-banner.tsx`, `readiness-provider.tsx`, `apps/frontend/app/layout.tsx`,
`runs/goal-session-mcp-loop/state/blueprint.md`, `app/engine/evidence.py`, `app/engine/referee.py`,
`app/engine/ledger.py`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_drift.py -v`
Result: **13 passed, 0 failed** (confirmed by real execution).

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_api_data.py -v`
Result: **45 passed, 0 failed** (confirmed by real execution; includes the 2 new drift-field tests).

Command: `cd apps/backend && .venv/bin/python -c "from app.config import load_config; cfg = load_config(); ..."`
Result: confirmed the real `config.yaml` loads with `data_quality.drift = enabled=True overlap_days=20
report_path='runs/goal-session-mcp-loop/state/drift-report.json'` and
`readiness.severity = {'servability': 'no-go', 'freshness': 'degraded', 'integrity': 'no-go', 'drift':
'degraded'}`.

**NOT RUN (environment outage — Bash tool stopped responding for the remainder of the session):**
`test_readiness.py`, `test_data_manager_jobs_pipeline.py`, `test_health.py`, `test_themes.py`,
`test_sectors.py`, `test_indexes.py`, `test_config.py`, `test_config_engine.py`, any frontend
typecheck/build, service startup (`scripts/dev.sh`), and the regression-replay script from NOTES.

## Known Issues

1. **Verification incomplete — environment outage, not a code defect I'm aware of.** See "READ THIS
   FIRST" above for the full explanation, root-cause hypothesis, and the exact commands still needed. This
   is the single most important thing for whoever picks this up next: **do not merge/release this without
   running the listed commands first.**
2. **Two stray diagnostic files at the repo root** (`.iter35-diskprobe.tmp`, `.iter35-diskprobe2.tmp`) —
   harmless placeholder content, created to isolate the outage to `/tmp` vs. the repo filesystem. Delete
   before considering the tree clean; I could not `rm` them myself without a working Bash tool.
3. **`test_data_manager_jobs_pipeline.py`'s new "skip-fetch resume" test uses a lightweight synthetic
   engine** (`_light_fetch_engine`, schema-only, no committed-seed load) rather than the file's usual
   `_fresh_seed_engine` (full 30-year seed), specifically to avoid materializing a 5th heavy SQLite DB in
   an already fixture-heavy file. To keep the resumed backfill's outcome irrelevant to a fixture with no
   real universe/sector data, the resume is ALSO wrapped in the same harmless `compute_run_payload` fault
   stub as the original run — the test asserts only that zero provider calls happen on resume and the
   drift artifact is byte-identical, not that the backfill itself succeeds. This is a deliberate,
   documented scoping choice, not an oversight — flagging it so a reviewer doesn't need to re-derive the
   reasoning.
4. **The regression-replay closure requirement from NOTES was not attempted** — the environment outage
   hit before I reached that step. If this iteration cannot complete it, the spec's own documented fallback
   applies (a lean verify-only iter-36, the iter-34 precedent).
5. **Not verified live:** this iteration adds no new external API integration (the drift check reads the
   ALREADY-committed seed CSVs and whatever bars a job's existing provider — real or test-injected —
   returns; no new provider, no new network call), so there is no separate "live external check" beyond
   what the existing Fetch job already exercises. The end-to-end wiring tests in
   `test_data_manager_jobs_pipeline.py` are the closest equivalent (unverified, per above).
6. **Service startup was NOT verified this session** (blocked by the same outage). The change surface
   (one new pure module, additive config, additive API field, additive fetch-pipeline stage gated
   defensively, additive frontend card) is deliberately low-risk for a boot-time regression, but this is
   an unverified claim, not a confirmed one, until `scripts/dev.sh` is actually run.
