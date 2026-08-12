# goal-ops-hardening-iter-71 Dev Handoff

**Phase:** goal-ops-hardening-iter-71
**Date:** 2026-08-12
**Agent:** developer
**Status:** complete

## What Was Built

- **A staleness bound on the readiness/preflight background-refresh cache** (`app.engine.readiness`),
  closing the gap iter-70 itself named: "before this round the endpoint could be slow but never wrong; it
  can now be fast and wrong." Every cache tick (`_tick_and_cache`) now stamps its published payload with
  `computed_at` (`time.monotonic()` — never wall-clock, so a system clock adjustment can never manufacture
  or hide staleness). The single read accessor `get_readiness_and_preflight` measures the served entry's
  age against `computed_at`; when that age would exceed a new bounded config knob,
  `readiness.max_stale_intervals` (default `3`) × `readiness.refresh_interval_seconds` (`0.5`, default
  threshold `1.5s`), it falls back to a **synchronous** `compute_readiness`/`compute_preflight` call —
  mirrors the EXISTING cold-start fallback exactly (same two producers, same one endpoint, no second
  implementation) — instead of ever serving the stale entry. A wedged/dead background-refresh tick thread
  can therefore never serve an ever-more-frozen "ready" state forever: past the bound, every request pays
  one fresh synchronous compute instead.
- **`GET /api/health` gains one additive field, `stale_for_s: float>=0`** — seconds since the served
  readiness/preflight payload was computed (`0.0` when computed synchronously for the current request,
  either via the pre-existing cold-start path or the new staleness-bound fallback). Read straight off the
  SAME cached payload `health()` already fetches — no second call, no new DB work.
- **`apps/backend/app/api/health.py:174`-area fix (reviewer/audit MINOR from iter-70):** the
  readiness-fetch `except` block now assigns `cached = None` explicitly before the preflight-fallback
  branch reads `cached` next, instead of relying on an incidental `UnboundLocalError` being silently
  swallowed by that branch's own broad `except Exception`. Same degrade-on-error behavior; just explicit,
  not implicitly-unbound.
- **One integration test composing TC-4's two previously-separate halves** (audit T1 from iter-70):
  `test_finalize_hook_state_flip_served_by_health_within_one_tick` (in `test_data_manager.py`, alongside
  the existing mocked-trigger test) drives a REAL `readiness.state` transition
  (`awaiting_snapshot` → a servable state) through the actual finalize hook
  (`data_manager._refresh_ingest_aggregates`) and asserts `GET /api/health`, called immediately after,
  serves the NEW state — not the stale pre-finalize one. The prior tests only proved the trigger *fires*
  (mocked) or that the cache accessor itself updates on a direct `trigger_readiness_refresh` call; this one
  proves the full real path end-to-end.
- **Config:** `ReadinessCfg.max_stale_intervals: int = 3` (back-compat default, `extra="allow"` — mirrors
  `refresh_interval_seconds`'s own convention), boot-validated `> 0`. `config.yaml`'s `readiness:` block
  gets the explicit `max_stale_intervals: 3` entry with an inline comment naming the resulting 1.5s bound.

## Files Changed

- `apps/backend/app/engine/readiness.py` -- `_tick_and_cache` stamps `computed_at` on every published
  payload; `get_readiness_and_preflight` measures staleness against it and falls back to a synchronous
  tick past `max_stale_intervals × refresh_interval_seconds`, always returning `stale_for_s`; the
  cold/failure fallback shape moved into a `_unavailable_fallback()` helper (fresh dict per call, never a
  shared mutable reference) and now also carries `stale_for_s: 0.0`.
- `apps/backend/app/api/health.py` -- `cached = None` explicit in the readiness-fetch except block; reads
  `stale_for_s` off the same cached payload and serves it as a new additive top-level response field.
- `apps/backend/app/config.py` -- `ReadinessCfg.max_stale_intervals: int = 3` + `> 0` boot validation.
- `config.yaml` -- `readiness.max_stale_intervals: 3`.
- `apps/backend/tests/test_readiness.py` -- 2 new `ReadinessCfg` tests (default value, non-positive
  rejection); 3 new staleness-bound tests (TC-2 fresh-serve with call-count instrumentation, TC-1
  synchronous-fallback-past-the-bound with call-count instrumentation, and a fallback-also-fails
  degrade-honestly test); updated 2 PRE-EXISTING iter-70 tests
  (`test_readiness_cache_steady_state_reads_do_not_recompute`,
  `test_readiness_cache_degrades_to_last_known_good_on_tick_failure`) whose literal whole-dict-equality
  assertions broke against the new, legitimately-time-varying `stale_for_s` field — now compare the
  `readiness`/`preflight` sub-dicts for content equality instead (same original intent, unaffected by the
  new field's real elapsed-time nature).
- `apps/backend/tests/test_health.py` -- TC-3 unit test for the `cached = None` fix; 3 new `stale_for_s`
  handler-level tests (additive-field presence via `TestClient`, real-age-within-bound, and
  synchronous-fallback-past-the-bound with call-count instrumentation); a new `tiny_engine` fixture (one
  bar + one run, direct `health(session)` calls) so these new tests don't require the ~1h `loaded_engine`
  committed-seed fixture; added the missing `pytest`/`time`/`datetime` imports the new fixture/tests need.
- `apps/backend/tests/test_data_manager.py` -- new `state_flip_engine` fixture (a benchmark bar already
  landed for a later date with no run yet — the real `awaiting_snapshot` condition) and
  `test_finalize_hook_state_flip_served_by_health_within_one_tick` (the composed TC-4 integration test,
  audit T1).
- `docs/handoffs/goal-ops-hardening-iter-71-dev.md` -- this handoff.
- `runs/goal-ops-hardening-iter-71/status.json` -- `current_step: dev_complete`.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest <paths> -q` (TMPDIR/TMP/TEMP set per the pipeline's
isolated-temp-dir note).

- Fast targeted run (new/changed tests only, no `loaded_engine`): 9 tests -- 9 passed.
- `test_readiness.py` minus the 18 pre-existing `loaded_engine`-dependent tests: 31 passed (confirms no
  regression among everything runnable without the ~1h fixture, including the two updated pre-existing
  tests).
- `test_health.py` minus the 16 `loaded_engine`-dependent tests: 7 passed.
- `test_config.py` (full file): 71 passed.
- `test_data_manager.py::test_finalize_hook_triggers_immediate_readiness_refresh` +
  `::test_finalize_hook_state_flip_served_by_health_within_one_tick`: 2 passed.
- Full `test_health.py tests/test_readiness.py` (both files, unfiltered — pays the ~1h `loaded_engine`
  fixture build cost once): **72 passed in 4138s (1:08:58)**, zero failures. This is the authoritative
  confirmation that nothing among the 18+16 `loaded_engine`-dependent pre-existing tests regressed, and
  that the new `test_health_carries_additive_stale_for_s_field` (the one new test that genuinely needs a
  full `TestClient(main.app)` lifespan round-trip against real seed data) passes.
- Live verification: `scripts/dev.sh` started cleanly (backend `GET /api/health` HTTP 200 within 3s;
  `stale_for_s` present and varying realistically across repeated polls, e.g. `0.0059` → `0.44` → `0.0015`,
  well under the 1.5s bound); frontend served `/` and `/data` (HTTP 200 both). Killed and restarted
  `dev.sh` a second time -- no port conflicts, same clean boot, `stale_for_s` present again. All dev
  processes stopped before finishing (verified no lingering listeners on :8255/:3255).

Result: all runs green, no regressions found.

## Known Issues

- The J-07 TC-3 health-poll drill's opening-window timing fix (poller must start before the ingest job's
  start command is issued) is NOT touched by this handoff -- it is not in this iteration's IN SCOPE Backend
  list (only 3 backend items: the staleness bound, the `cached = None` fix, and the composed TC-4
  integration test), and the spec's own OUT OF SCOPE section reserves `scripts/automation/*` edits as
  owner-gated. This is QA/drill-execution-lane work for whichever agent runs the J-07 re-verification this
  round.
- Re-verifying all 8 journeys (J-01, J-03, J-04, J-05, J-06, J-07, J-08, J-09) against a confirmed-live
  backend is the browser-qa-agent's job this round (per the spec's pending-infra make-up target), not
  developer-lane work -- this handoff only closes the backend product gap (the staleness bound) and the
  two smaller fixes/tests the spec assigned to the developer.
- `stale_for_s` is intentionally not surfaced anywhere in the frontend this round (spec's own Out of
  Scope: rendering it would be this cycle's first user-visible UI change, which ties to full depth per
  goal.md's Loop Mechanics rule, and this round's depth is binding lean).
