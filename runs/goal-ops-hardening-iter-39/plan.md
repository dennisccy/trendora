# goal-ops-hardening-iter-39 Execution Plan

## What to Build

- **J-07 step 4 (the one remaining thing this iteration must prove):** one throwaway-DB
  induced-pressure drill, launched only via `scripts/start-backend.sh` (AG-10), with
  `server.memory_cap_mb` re-tuned **upward** from the 3072 MB that killed iter-38's attempt (in
  the wrong stage — `_do_backfill`'s bar-cache prefill) so prefill completes but a per-item
  aggregate-warm sub-step (forward-aggregates or drawdown-expectations, inside
  `_refresh_ingest_aggregates`, `data_manager.py` ~3401-3407/3435-3440) raises `MemoryError`,
  caught by the existing per-item isolation `except MemoryError` handler. Seed the throwaway DB
  with `setup_status="Avoid"` (iter-34 lesson: avoids `research_hot_keys`'s generic
  non-`MemoryError`-specific except firing first and masking the target). Assert directly from a
  log/status read WHICH stage aborted — never infer it from "a `MemoryError` fired somewhere"
  (the iter-37/38 binding lesson). Do not widen the cap "so it completes gracefully" — this is a
  prove-the-failure drill, not a two-arm comparison (iter-38's own mistake, explicitly forbidden
  by NOTES).
- Remove the drill health-poll script's `MAX_SECONDS` bound so the 1 Hz `GET /api/health` poll
  covers the whole job, not a fixed wall-clock window (closes iter-38 audit finding B2's ~39s
  blind spot / TC-2).
- During the same drill, assert one previously-warmed `GET /api/backtest?as_of=<a date cached
  before the drill started>` returns HTTP 200 both during and immediately after the abort (TC-3),
  and that a follow-up `GET /api/health` answers with no process restart (TC-4).
- **Deterministic replay-lane repair** (`incredible_auto_dev/scripts/automation/lib/demo_runner.py`,
  framework/tooling code, not product code — same class of change iter-33 already made to
  `merge_ui_test_results.py`): `run_verify` probes `GET /api/health` once before replaying any
  journey; if it does not answer 200, every journey in that run is written with a new `BLOCKED`
  verdict class (never `FAIL`), and `compute_regression_verdict` (plus the reconciliation footer
  the goal-evaluator reads) must treat `BLOCKED` distinctly from a real FAIL/regression signal
  (TC-5, TC-6). Also refresh this session's stale golden selectors (the 6/7 locator-timeout
  failures iter-38's audit T1 flagged) and fix the reconciliation footer so it lists every
  overturned journey — iter-38 under-reported by omitting J-05 and J-04 (TC-7).
- **Env-toggle truthy guard**: `TRENDORA_FORCE_LEGACY_BAR_CACHE` (`data_manager.py:3123`,
  currently `if not os.environ.get(...)`) gets an explicit truthy check
  (`in ("1", "true", "yes")`) so `=0` no longer silently enables legacy mode (iter-38 audit B5).
  Add the 2-line unit test naming one truthy and one falsy value (TC-10, TC-11).
- **Root-logger config for `apps/backend`**: today there is none (confirmed live —
  `apps/backend/main.py` only does `logger = logging.getLogger(...)` calls with no
  `logging.basicConfig`/handler setup anywhere in the app; uvicorn's last-resort handler is the
  only thing writing to `logs/backend.log` and it only surfaces WARNING+). Configure a handler/
  level so routine liveness logging no longer needs to masquerade as `.warning`. Once confirmed
  (grep `logs/backend.log`), downgrade the J-07 finalize-tail `cache_ctx` liveness line
  (`data_manager.py:3361`) from `.warning` to `.info` (TC-12).
- **`read_pool()` in-situ re-measurement**: measure its real wall-clock cost during a live K>=3
  multi-date backfill (not the existing micro-benchmark-times-call-count projection iter-38's
  audit B3 flagged as prose-only), record the measured figure in `reports/perf-budgets.md`
  alongside the existing projected one (TC-13).
- **Live re-verification of J-04 and J-05 step 3** (no code change — verification only, scheduled
  LAST per the binding iter-36 lesson, after every risky drill/backend-restart step above is
  done): a coordinator-authorized `kill -9` + restart of the live dev-DB backend with a
  checkpointed in-progress/completed backfill; assert the restarted `/data` Run History panel
  shows the interrupted run's real last-checkpointed progress, not a zeroed row (TC-8), and that
  the Coverage payload panel serves a real `coverage_from_storage` value cold, not the all-zero
  sentinel (TC-9).
- Dev handoff at `docs/handoffs/goal-ops-hardening-iter-39-dev.md`.

### Explicitly out of scope (reaffirmed from the phase spec — do not touch)
- `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`,
  `ensure_historical_forward_aggregates_dispatched` — byte-frozen.
- Re-running J-07 steps 1/3 or the two-arm live-cache-vs-fallback VmPeak comparison — already
  closed with this-iteration-quality evidence in iter-38.
- iter-33/g (Regime Lab `view=pooled` dispatch), iter-29/d (the `prices.py:131-152` unbounded
  whole-table load), iter-34/j (health ≤0.1s budget — owner decision), iter-33/i
  (`start-frontend.sh` host-guard membership — owner decision), the `[NEW]` `demo.sh
  --session-live` walkthrough capture.
- No frontend code change of any kind this iteration (`Frontend Present: no` per the phase spec
  metadata) — J-04/J-05 verification reads existing rendered panels unchanged.

## Agents Required
- backend-data: yes -- all in-scope items above (drill, replay-lane fix, env-toggle guard,
  logging config, read_pool() measurement, live J-04/J-05 restart verification) are backend/
  tooling work; the `developer` agent should implement and execute the live drills/restarts
  itself (per AG-10, only via `scripts/start-backend.sh`) and capture the evidence artifacts.
- frontend-ux: no -- no frontend file changes; J-04/J-05 verification is read-only against
  already-shipped, unchanged UI panels (global readiness badge, `/data` Run History panel,
  `/data` Coverage payload panel).

## Frontend Present
no

## Files to Create/Modify
- `apps/backend/app/engine/data_manager.py` -- truthy guard for
  `TRENDORA_FORCE_LEGACY_BAR_CACHE` (~line 3123); downgrade the J-07 finalize-tail `cache_ctx`
  liveness line (~line 3361) from `.warning` to `.info` once the root-logger fix confirms it
  still reaches `logs/backend.log`
- `apps/backend/main.py` (or a new small `apps/backend/app/logging_config.py` imported from it)
  -- add a root-logger handler/level configuration so `.info`-level records from
  `trendora.data_manager` (and other app loggers) are no longer silently dropped by uvicorn's
  WARNING-only last-resort handler
- `apps/backend/tests/test_data_manager.py` -- 2-line truthy/falsy test for the env-toggle guard
  (TC-10/TC-11); a test confirming an `.info`-level liveness line reaches the configured log
  handler (TC-12)
- `incredible_auto_dev/scripts/automation/lib/demo_runner.py` -- `run_verify`: probe
  `GET /api/health` before replaying; new `BLOCKED` verdict class distinct from `FAIL`/`SKIP` in
  `compute_regression_verdict` and the written results; reconciliation-footer fix so every
  overturned journey is listed (not a subset)
- Framework self-tests covering `demo_runner.py` (wherever iter-33's `merge_ui_test_results.py`
  precedent's tests live, e.g. under `incredible_auto_dev/scripts/automation/` or its `tests/`)
  -- new `BLOCKED`-verdict + reconciliation-footer coverage (TC-5, TC-6, TC-7)
- This session's stored golden replay scripts (`<scripts-dir>/J-XX.json` — locate via
  `demo_runner.py --scripts-dir` usage in the goal-mode replay step) -- refresh stale selectors
  causing the 6/7 locator-timeout failures
- `reports/perf-budgets.md` -- new drill section (J-07 step 4 evidence: which stage aborted,
  health-poll coverage, cached-read HTTP 200 during/after abort); `read_pool()` in-situ
  measurement (TC-13); J-04/J-05 live re-verification results
- `runs/goal-ops-hardening-iter-39/mem-drill/` -- NEW: throwaway-DB seed fixture (`setup_status=
  "Avoid"`), re-tuned `memory_cap_mb` config, health-poll script (no `MAX_SECONDS`), job status/
  log excerpts, cached-`/api/backtest`-read evidence
- `runs/goal-ops-hardening-iter-39/live-restart/` (or similar) -- NEW: J-04/J-05 live kill/
  restart evidence (Run History panel state, Coverage payload panel state, logfile excerpts
  showing the truncated/no-clean-shutdown boundary)
- `docs/handoffs/goal-ops-hardening-iter-39-dev.md` -- dev handoff

## UI Evolution
N/A -- Frontend Present: no. No new user-facing capability, no new information displayed, no new
user actions, no UI surface changes, no navigation changes. J-04/J-05 verification confirms
already-shipped panels (global readiness badge, `/data` Run History, `/data` Coverage payload)
behave correctly under a genuine live restart — it does not change what they render.

## Visual Requirements
N/A -- no frontend work this iteration.

## Key Test Scenarios
(Numbered to match the phase spec's TESTING REQUIREMENTS — each must be exercised with
this-iteration evidence, not replay/inference.)

- TC-1: throwaway backend via `scripts/start-backend.sh`, `memory_cap_mb` re-tuned above 3072 MB
  so prefill completes; a real backfill's ingest-finalize aggregate warm raises `MemoryError`
  caught by the per-item isolation handler inside the aggregate-warm loop (not prefill) --
  confirmed by direct log/status read of which stage aborted.
- TC-2: same drill; the 1 Hz `GET /api/health` poll (no `MAX_SECONDS` bound) returns HTTP 200
  with no coverage gap from job start to job completion.
- TC-3: a date already aggregate-cached before the drill; `GET /api/backtest?as_of=<that date>`
  returns HTTP 200 during and immediately after the `MemoryError` abort.
- TC-4: the drilled process answers a follow-up `GET /api/health` with no restart (no wedge, no
  deadlock).
- TC-5: backend NOT running; `demo_runner.py --mode verify` writes every journey `BLOCKED` (never
  `FAIL`), merged results state the backend was unreachable.
- TC-6: backend running, a golden script has a stale selector; `demo_runner.py --mode verify`
  returns an ordinary `FAIL` distinct from `BLOCKED`.
- TC-7: at least two journeys overturned by the LLM browser-qa lane; the reconciliation footer
  names every overturned journey, not a subset.
- TC-8: live dev-DB backend with a checkpointed in-progress/completed backfill; after
  coordinator-authorized `kill -9` + restart, `/data` Run History shows the interrupted run's real
  last-checkpointed progress (not a zeroed row).
- TC-9: same live restart cycle; `/data` Coverage payload panel serves a real
  `coverage_from_storage` value cold for an already-ingested date (not the all-zero sentinel).
- TC-10: `TRENDORA_FORCE_LEGACY_BAR_CACHE=0` treated as falsy -- legacy mode NOT forced,
  `prog._shared_bar_cache` set to the real shared cache.
- TC-11: `TRENDORA_FORCE_LEGACY_BAR_CACHE=1` treated as truthy -- legacy mode forced, stash
  skipped (new 2-line test).
- TC-12: after the root-logger fix, the J-07 finalize-tail `cache_ctx` liveness line at `.info`
  still appears (grep-able) in `logs/backend.log`.
- TC-13: `read_pool()`'s wall-clock cost measured directly during a real K>=3-date backfill,
  recorded in `reports/perf-budgets.md` next to the prior projected figure.

## Notes for the developer
- AG-10 binding: the drill and all restarts must launch only via `scripts/start-backend.sh`;
  never weaken/strip its HOST-GUARD block. AG-9: throwaway DB only, no live network calls.
- Schedule order matters: do the drill and replay-lane/env-toggle/logging fixes first; run the
  J-04/J-05 live kill/restart cycle LAST (binding iter-36 lesson — any backend-down step goes at
  the end of the plan so the deterministic-replay fix built earlier in this same iteration is
  already in place to correctly classify anything it observes as `BLOCKED` rather than `FAIL`).
- Do not re-derive or touch `compute_forward_aggregates` / `resolved_forward_aggregate_evidence` /
  `ensure_historical_forward_aggregates_dispatched` -- byte-frozen this cycle.
