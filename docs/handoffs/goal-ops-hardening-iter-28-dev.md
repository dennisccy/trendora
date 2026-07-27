# goal-ops-hardening-iter-28 Dev Handoff

**Phase:** goal-ops-hardening-iter-28
**Date:** 2026-07-27
**Agent:** developer
**Status:** complete

## What Was Built

This is a pure evidence-closure + test-hygiene iteration — zero new product surface, zero new
Data-Contract value. Three changes, exactly matching the iter spec's IN SCOPE list:

- **Drift-report path relocation** — `config.yaml`'s `data_quality.drift.report_path` and
  `apps/backend/app/config.py`'s `_DEFAULT_DRIFT_REPORT_PATH` constant moved, byte-identically, from
  another (closed/archived) goal session's folder (`runs/goal-session-mcp-loop/state/drift-report.json`)
  to this session's own `runs/goal-session-ops-hardening/state/drift-report.json`. `app.engine.drift`'s
  computation, `resolve_drift_report_path()`'s env-override-then-config-default resolution order, and
  both existing consumers (`readiness.severity.drift` / `GET /api/health`'s preflight; the additive
  `drift` field on `GET /api/data`) are byte-unchanged — only the artifact's file-system location moved.
- **Artifact file itself relocated** (`git mv`, history-preserving) rather than left to regenerate
  inert, so the drift preflight component keeps reporting its real, already-computed `"clean"` status
  instead of resetting to the absent/inert state. Content verified byte-identical to the pre-move
  committed blob.
- **J-06 golden script self-poisoning fix** — `runs/goal-session-ops-hardening/journey-scripts/J-06.json`
  step 1's assertion on `/` changed from the incidental, preflight-derived string `"DEGRADED"` to stable
  Dashboard content (`"Market Regime"`, confirmed present in `apps/frontend/app/page.tsx` regardless of
  the preflight verdict). Steps 2-11 untouched.

No other backend file was changed — the iter-27 AG-8 (`_insert_run_forward_returns`) and AG-3
(`coverage_from_storage`) fixes stayed byte-frozen this iteration; only their independent browser
verification was outstanding (that verification is the browser-qa-agent's job, not developer scope, per
the iter spec's lean cycle: developer -> reviewer -> browser-qa).

## Files Changed

- `config.yaml` -- `data_quality.drift.report_path` moved from `runs/goal-session-mcp-loop/state/drift-report.json` to `runs/goal-session-ops-hardening/state/drift-report.json` (1-line value change only)
- `apps/backend/app/config.py` -- `_DEFAULT_DRIFT_REPORT_PATH` moved to the same new value, byte-identical to the config.yaml default (1-line value change only)
- `runs/goal-session-mcp-loop/state/drift-report.json` -> `runs/goal-session-ops-hardening/state/drift-report.json` (git rename, byte-identical content: `{"affected": [], "overlap_days": 20, "reference": "2024-01-03", "status": "clean"}`)
- `runs/goal-session-ops-hardening/journey-scripts/J-06.json` -- step 1's `expect.text` changed from `"DEGRADED"` to `"Market Regime"`

## Tests Run

Pre-flight: confirmed no test anywhere pins the literal string `goal-session-mcp-loop` for the drift
path (full-repo grep) before making the change, matching the spec's own pre-confirmed claim.

Command (ONE combined invocation, host-guard taskset/BLAS-thread-capped per
`project-extensions/host-guard/host-guard.env`, launched via `setsid nohup` + polled in bounded
foreground loops to completion — never run concurrently with any other pytest process):

```
cd apps/backend && taskset -c 0-3,8-11 env OMP_NUM_THREADS=4 OPENBLAS_NUM_THREADS=4 MKL_NUM_THREADS=4 \
  NUMEXPR_NUM_THREADS=4 .venv/bin/python -m pytest \
  tests/test_drift.py \
  tests/test_readiness.py::test_drift_component_ok_when_artifact_absent \
  tests/test_readiness.py::test_drift_component_ok_when_artifact_clean \
  tests/test_readiness.py::test_drift_component_breached_on_drift_status_names_affected_symbols \
  tests/test_readiness.py::test_drift_component_breached_on_unreadable_artifact \
  tests/test_readiness.py::test_drift_breach_composes_with_other_breaches_worst_severity_wins \
  tests/test_api_data.py::test_get_data_overview_carries_absent_drift_on_a_cold_db \
  tests/test_api_data.py::test_get_data_overview_drift_field_equals_read_drift_report_verbatim \
  tests/test_config.py -k drift \
  -v
```

(The four DoD-named selectors — `test_drift.py`, `test_config.py -k drift`, `test_readiness.py -k
drift`, `test_api_data.py -k drift` — are realized here as: the full `test_drift.py` file passed as a
bare path plus explicit node-IDs for the drift-named tests in the other files. This avoids a single
global `-k drift` incorrectly narrowing `test_drift.py`'s own file — in practice pytest's keyword
matching also checks the enclosing module name, so `-k drift` alone would in fact have kept all of
`test_drift.py` too since its module name contains "drift"; explicit node-IDs were used regardless for
certainty. `test_config.py -k drift` matched zero tests, consistent with the spec's pre-confirmed claim
that no test in that file pins the drift path by name.)

**Result: reached a pass/fail line — 20 passed, 71 deselected in 5846.47s (1:37:26).** Zero failures,
zero errors. This DOES fulfil TC-11.

Runtime note: `test_readiness.py`'s 5 drift-component tests depend on the session-scoped `loaded_engine`
fixture (30-year historical warm-up via `bootstrap_runs` + `backfill_forward_returns`) — despite the
iter spec's TESTING REQUIREMENTS framing these four selectors as not needing it, `test_readiness.py -k
drift` does trigger it. This cost the bulk of the ~1h37m wall time (single fixture build, shared across
all 5 readiness tests in this one process — CPU pegged ~100% the whole run, RSS plateaued ~727MB, `free
-h` checked periodically with no swap pressure), consistent with legitimate compute, not a hang. Flagging
this discrepancy for the record since the next iteration's decomposer should know this specific selector
is not actually fixture-free.

## Pre-handoff verification

- **Service startup:** `scripts/start-backend.sh` and `scripts/start-frontend.sh` launched cleanly (both
  via `setsid nohup`, backend port 8255, frontend port 3255 — this checkout's deterministic offset).
  `GET /api/health` returned 200 with `preflight.components.drift == {"ok": true, "severity": "degraded",
  "detail": "The most recent fetch matched the committed seed over the overlap window."}` — proof
  `resolve_drift_report_path()` correctly resolves and reads the RELOCATED artifact (the real `"clean"`
  status survived the move, not a reset to absent/inert). Frontend returned 200 on `/`.
  `logs/backend.log` for this specific boot (the lines after this run's own `"=== start-backend.sh:
  launching at ..."` banner) carries zero errors/exceptions — the pre-existing `research.py:215`
  MemoryError signature only appears in earlier, unrelated boots, confirmed by comparing line numbers
  against the banner boundaries.
  Both processes were stopped afterward (`pkill` + `fuser -k` for a stuck frontend child); confirmed via
  `lsof`/`ss` that ports 8255 and 3255 are free and no trendora process remains.
- **External integrations:** N/A — no adapter/scraper/external-API change this iteration.
- **Native dependency binaries:** N/A — no new dependency this iteration.

## Known Issues

- **Browser-QA re-verification (J-05, J-06, J-07, J-08 + golden replay of J-01/J-03/J-04/J-09) was NOT
  run by this developer agent.** Per the iter spec's own depth justification ("the lean cycle (developer
  -> reviewer -> browser-qa)"), that is the browser-qa-agent's job in the next pipeline step, not
  developer scope — this handoff covers only the three in-scope code/config/test-script changes and the
  unit-test line (TC-11), which reached a clear PASS. TC-1 through TC-10 (all the browser/golden-replay
  acceptance criteria) remain to be exercised by that step.
- **`test_readiness.py -k drift` is NOT actually fixture-free**, contrary to the iter spec's TESTING
  REQUIREMENTS framing (see Runtime note above) — it pulls in the expensive session-scoped `loaded_engine`
  fixture (~1h37m wall time this run, in line with the ~1h+ iter-26 precedent for that same fixture).
  This did not block completion (the run reached a clean pass/fail line), but future lean-iteration specs
  reusing this exact selector should budget for it, or the decomposer should re-verify the "fixture-free"
  claim before repeating it.
- No product-code regressions found; no new anti-goal finding surfaced during this iteration's own work.
  The AG-8 `research.py:215` finding and the four ledger-family `_DEFAULT_*_PATH` constants
  (`config.py:2215-2286`) were deliberately left untouched, per the iter spec's OUT OF SCOPE section.
