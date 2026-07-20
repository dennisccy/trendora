# goal-ops-hardening-iter-4 Dev Handoff

**Phase:** goal-ops-hardening-iter-4
**Date:** 2026-07-20
**Agent:** developer
**Status:** complete

## What Was Built

Fixes the two pre-existing, out-of-scope trust-surface defects (B3, F1) that iter-3's audit/closure
identified as the reason J-05 could not pass browser-QA cleanly, exactly per
`runs/goal-ops-hardening-iter-4/plan.md`. No new user-facing capability — this is an honesty fix to the
EXISTING global readiness badge and job-progress heartbeat.

- **B3 fix — the readiness badge no longer flips to "Backend unavailable" on an ordinary fetch.**
  `compute_readiness` (`app/engine/readiness.py`) used to compare the last persisted `ScannerRun` against
  `latest_data_date`'s **whole-table** max over all 590 symbols. Landing a bar for ANY single symbol dated
  after the last run pushed that whole-table max forward and flipped the badge to the crash-identical
  `unavailable` state, even though the real snapshot was still being served correctly. **After the fix:**
  servability is compared against the **benchmark symbol's own latest bar** (`cfg.etfs.index[0]`, i.e.
  SPY — the exact symbol `forward_testing.walk_forward_asof_dates`/`warmup._warmup_dates` already use to
  define the trading calendar), via one new indexed per-symbol query, `_latest_benchmark_bar_date`
  (mirrors `latest_data_date`'s shape, filtered to one symbol — never a whole-table scan, AG-8). An
  unrelated symbol's fetch no longer touches servability at all.
  - **New state name (exact, used everywhere it is read):** `awaiting_snapshot`. Fires when a run IS
    servable (some snapshot exists) but the benchmark's own latest bar has advanced past it with no run
    yet for that later date. Distinct from `unavailable` (nothing ever servable) and `initializing`
    (cadence warm-up in flight, unchanged).
  - **Regression guard preserved exactly:** `latest_run is None` (a true never-scanned DB) still resolves
    unconditionally to `unavailable` regardless of any benchmark bar data — the new state can never mask
    genuine unavailability.
  - **New field (exact name):** `compute_readiness`'s return dict gains `"detail": Optional[str]` — `null`
    for the other three states; for `awaiting_snapshot` a human-readable sentence naming the benchmark
    symbol, the pending date, and the recovery action ("Run a backfill or rebuild on Data Manager to
    produce it.").
  - **Wiring gap (found by reading the endpoint, not named in the phase spec's own file list) — fixed:**
    `apps/backend/app/api/health.py`'s `health()` handler previously did `"readiness": readiness["state"]`
    and discarded the rest of `compute_readiness`'s dict, so `detail` was computed correctly but never
    reached the frontend. Added a new sibling top-level JSON key, `"readiness_detail"`, alongside the
    existing `"readiness"`/`"warmup"` keys (the existing `"readiness"` key itself stays the SAME bare
    string it always was — byte-identical contract, confirmed by the unedited `test_health.py` assertions
    still holding, see Tests Run).
- **F1 fix — the job-progress heartbeat no longer freezes during aggregate-refresh.**
  `_refresh_ingest_aggregates` (`app/engine/data_manager.py`) never called `prog.tick()` anywhere in its
  own body, even though the main per-date scan loop already does
  (`data_manager.py:2863`, `prog.tick(f"scanning {d.isoformat()} ...")`). Once the main scan finished,
  `JobProgress.last_progress_at` froze for the entire finalize tail (measured ~729s for a full rebuild in
  `reports/perf-budgets.md` Item L), so the frontend's stale-heartbeat flag
  (`job_progress.heartbeat_stale_seconds`) rendered "· possibly stalled" on a perfectly healthy job.
  **After the fix:** `_refresh_ingest_aggregates` calls the **bare** `prog.tick()` (no `activity` string
  argument) at its own start and at each per-date step of its market-phase warm loop
  (`data_manager.py:3082-3089`). Deliberately bare/heartbeat-only: `tick()`'s `activity` parameter defaults
  to `None`, in which case it stamps ONLY `last_progress_at` and leaves `current_activity` untouched — so
  the pre-existing, already-pinned "scanning `<date>` (N/N)" activity line from the main scan loop is never
  overwritten with a different message. This preserves
  `test_data_manager_jobs_pipeline.py::test_progress_payload_has_heartbeat_and_activity`'s existing
  `"scanning" in summary["current_activity"]` assertion unedited while still fixing the actual bug (the
  heartbeat timestamp, which is all the frontend's stale-check reads).
- **Frontend — the badge gets a 4th visual state.** `apps/frontend/lib/api.ts`'s `ReadinessState` widened
  to add the `"awaiting_snapshot"` literal; `HealthStatus` gained the new `readiness_detail: string | null`
  sibling field. `apps/frontend/components/health-badge.tsx` gained a 4th `if/else if` branch: distinct
  `data-testid="readiness-badge"` `data-state="awaiting_snapshot"`, reuses the existing `Badge
  variant="accent"` (no new color token), visible label **"Snapshot pending"** (never "Backend
  unavailable") plus the recovery-pointer detail text from the backend. The status dot is static (no
  `animate-pulse`), unlike `initializing`'s pulsing dot — this condition persists until an operator acts
  (runs a backfill/rebuild), so it deliberately reads as "needs action" rather than "resolving itself."

## Files Changed

- `apps/backend/app/engine/readiness.py` — added `AWAITING_SNAPSHOT` constant; added
  `_latest_benchmark_bar_date(session, cfg)` (one indexed per-symbol max query); rewired
  `compute_readiness`'s servability check from the whole-table `latest_data_date` comparison to
  `has_servable_run` (`latest_run is not None`, unconditional) + `awaiting_snapshot`
  (`latest_benchmark_bar > latest_run`); added the `detail` field to the return dict; module + function
  docstrings updated.
- `apps/backend/app/api/health.py` — added `"readiness_detail": readiness.get("detail")` to the `/api/health`
  response; added `"detail": None` to the exception-fallback readiness dict; docstring updated.
- `apps/backend/app/engine/data_manager.py` — `_refresh_ingest_aggregates`: added a bare `prog.tick()` at
  the function's start and inside the per-date market-phase loop; docstring updated.
- `apps/backend/tests/test_readiness.py` — updated `test_compute_readiness_shape_unchanged_by_preflight_addition`
  for the new `detail` key/state; added a new "B3 fix" section: `non_benchmark_ahead_engine` +
  `benchmark_ahead_engine` fixtures, and five new tests (`test_non_benchmark_symbol_fetch_never_affects_servability`,
  `test_awaiting_snapshot_when_benchmark_own_bar_outruns_last_run`,
  `test_awaiting_snapshot_never_masks_true_unavailability`,
  `test_preflight_servability_ok_for_awaiting_snapshot_state`,
  `test_latest_benchmark_bar_query_is_symbol_scoped_not_whole_table_scan`).
- `apps/backend/tests/test_data_manager.py` — added `timezone` to the `datetime` import; added
  `finalize_hook_multi_date_engine` fixture (two dates) + one new test,
  `test_finalize_hook_ticks_heartbeat_at_least_once_per_date_in_market_phase_loop`.
- `apps/frontend/lib/api.ts` — widened `ReadinessState`; added `readiness_detail: string | null` to
  `HealthStatus`.
- `apps/frontend/components/health-badge.tsx` — new `awaiting_snapshot` pill branch; the context-detail
  `useEffect` now re-fetches on `state` transitions (was `[]`, mount-once) — see Known Issues/Deviations
  below for why.
- `apps/backend/tests/test_health.py` — **not edited.** Verified by reading (not by a completed pytest run,
  see Tests Run): `test_health_carries_readiness_and_warmup`'s `body["readiness"] in {"ready",
  "initializing", "unavailable"}` and `test_health_carries_additive_preflight_field`'s `existing_keys <=
  set(body)` subset check both still hold — `readiness` stays a bare string, and a new sibling key is
  additive, never a removal.
- `docs/handoffs/goal-ops-hardening-iter-4-dev.md` — this file.
- `docs/handoffs/goal-ops-hardening-iter-4-frontend.md` — companion frontend handoff.

**Confirmed untouched** (per the plan's explicit "Do NOT touch" list): `apps/frontend/components/
readiness-provider.tsx` was **not** edited in the end (see Known Issues/Deviations — I considered it,
decided against, and explain why); `apps/frontend/components/preflight-banner.tsx`,
`apps/backend/app/engine/warmup.py`, `main.py`'s `ensure_latest_snapshot`, the boot warm-up loop, the
`coverage_snapshot` table/finalize gate, `aggregates_refreshed`'s nullability contract, any J-01/J-03
shipped field, `scripts/start-backend.sh`, `docs/goal.md`, `runs/goal-session-ops-hardening/state/
blueprint.md` (already pre-updated by the decomposer for this iteration — confirmed by reading it, not
touched).

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest <path> -k <filter> -v` (TMPDIR set per harness
instructions). Per this project's own established convention (iter-3's dev handoff states this
explicitly, and `MEMORY: backend-test-suite-runtime` corroborates it), **the full backend suite is not
run** — the 30-year/587-symbol fixture basis makes even single full files take minutes, and the reviewer/QA
step owns full-suite verification.

**Be honest about what happened, not just what was intended:** my first attempt ran the FULL
`test_readiness.py` file in the background to get a complete regression signal. That process was still
running (`loaded_engine`'s session-scoped fixture build — a full seed load + `bootstrap_runs` +
`backfill_forward_returns` over the real 30-year basis — is expensive) when my turn ended; per the
coordinator's correction, a background notification does not re-invoke a dispatched subagent, so that run's
output was lost (the process was gone on the next check, but its piped-through-`tail` output file was
empty — killed, not completed). I did not wait for a second full run; instead I ran ONLY the new/changed
tests with a tight `-k` filter and a bounded `timeout`, per the coordinator's explicit instruction:

| Run | Filter | Result |
|---|---|---|
| Cheap new tests (own tiny hand-built fixtures, no full seed load) | `non_benchmark_symbol_fetch_never_affects_servability or awaiting_snapshot_when_benchmark_own_bar_outruns_last_run or awaiting_snapshot_never_masks_true_unavailability or preflight_servability_ok_for_awaiting_snapshot_state or finalize_hook_ticks_heartbeat_at_least_once_per_date_in_market_phase_loop` (spans `test_readiness.py` + `test_data_manager.py`) | **5 passed, 134 deselected in 1.07s** |
| `loaded_engine`-dependent new/edited tests | `test_compute_readiness_shape_unchanged_by_preflight_addition or test_latest_benchmark_bar_query_is_symbol_scoped_not_whole_table_scan` | **Killed after a 150s bounded `timeout`** (exit 124) — `loaded_engine`'s fixture setup alone did not finish inside the budget. No pytest process left running afterward (confirmed via `ps aux`). |

**What this means, precisely:**
- The 5 passing tests directly exercise the new code path (`compute_readiness`'s benchmark-scoped
  comparison, the new `awaiting_snapshot` state + `detail` field, the preflight non-breach, and the F1
  `tick()` heartbeat fix) against hand-built fixtures constructed exactly to hit TC-1/TC-2/TC-3/TC-5/TC-6
  from the phase spec's test-first contract. This is the real correctness evidence for the fix itself.
- The 2 unconfirmed tests are not testing NEW logic beyond what the 5 already cover — one pins
  `compute_readiness`'s return-shape against the real, fully-warmed seed (`loaded_engine`), the other
  proves the new query is symbol-scoped (not a whole-table scan) against that same real seed. I reasoned
  through both by hand instead of by a green pytest run: I directly inspected every committed seed price
  CSV (`apps/backend/data/seed/prices/*.csv`) and confirmed the whole-table max end-date (2026-07-01)
  equals SPY's own end-date — so in `loaded_engine` (and in `test_warmup.py`'s `_fast_cfg()`-based
  fixtures, which load the SAME committed seed), the benchmark's own latest bar always equals the
  whole-table latest, meaning `awaiting_snapshot` can never trigger there and every pre-existing
  `compute_readiness`-based assertion in `test_health.py`/`test_warmup.py` continues to hold exactly as
  before. This is a code-level argument, not a machine-verified one — **flagged explicitly for the
  reviewer/QA step to re-run** (`pytest tests/test_readiness.py tests/test_warmup.py tests/test_health.py
  -v`, TMPDIR set, expect several minutes).
- I did **not** run the full `test_data_manager.py` file (109+ tests, ~4 minutes per iter-3's own
  precedent) or `test_warmup.py` (documented by iter-3's own handoff as 40+ minutes for a full run) or any
  browser-level check. All deferred to reviewer/QA, consistent with this project's established division of
  labor.

**Frontend:** `npx tsc --noEmit` in `apps/frontend/` — clean, zero errors (this project has no JS test
runner configured; typecheck is the closest automated frontend gate — see the frontend handoff).

**Import/syntax sanity (fast, ran to completion):** `ast.parse` on all 5 changed Python files — clean.
Direct import of `app.engine.readiness`, `app.api.health`, `app.engine.data_manager`, and `main` (the
actual `uvicorn main:app` entry point) — all import without error.

## Pre-Handoff Verification

- **Service startup:** **Not run end-to-end this iteration** (no `scripts/dev.sh`/`scripts/start-backend.sh`
  cycle) — given the coordinator's explicit time-boxing, I substituted a fast, targeted check: direct
  Python import of `main` (the exact `uvicorn main:app` entry point) succeeded cleanly, which rules out any
  import-time/wiring error in the changed modules (a real risk class for this diff, since `health.py` now
  reads a new key off `compute_readiness`'s dict). This does **not** confirm the lifespan boot sequence,
  the actual HTTP response shape at runtime, or the frontend dev server — **flagged for reviewer/QA to run
  the full service-startup check** before relying on this iteration's live behavior.
- **External integrations:** N/A — no new adapter/scraper; both fixes are pure DB-read/in-memory-state
  logic (AG-9 unaffected).
- **Native dependency binaries:** N/A — no new dependency.

## Config / Environment Changes

None. No new `config.yaml` key, no new env var, no migration (no schema change — both fixes are read-path
logic + a JobProgress in-memory heartbeat call, no new column/table).

## Known Issues / Deviations From the Plan (be honest, not defensive)

- **`apps/frontend/components/readiness-provider.tsx` — the plan said "do not touch"; I considered
  touching it and decided against it, but the reasoning is worth recording because it changes HOW the new
  `readiness_detail` field reaches the badge.** The plan's frontend section only lists `api.ts` and
  `health-badge.tsx` as touch targets and explicitly confirms `readiness-provider.tsx`'s two specific
  existing behaviors (the `=== "ready"` poll-cadence check, the failure-fallback `setState("unavailable")`)
  are correct unmodified for the new state — both true. But the provider's shared context (`state`,
  `warmup`, `preflight`) does not carry a `detail` field at all, and `HealthBadge` needs the recovery-pointer
  text to be reasonably fresh for the badge to be honest during a LIVE state transition (the realistic B3
  scenario: an operator is already looking at the badge when a fetch lands). Rather than widen the shared
  provider (which the plan says not to touch), I made a smaller, fully-contained change inside
  `health-badge.tsx` alone: the component's own existing one-shot context-detail fetch (previously
  `useEffect(..., [])`, fired once on mount, used for the provider/seed-date/symbol-count badges) now
  re-fires whenever the shared `state` value transitions (`useEffect(..., [state])`). This ties the
  recovery-pointer text's freshness to the same transitions the pill itself re-renders for, without adding
  a second polling loop or touching the protected file. Trade-off: there is a brief (one extra
  request-latency) window right at a transition where the pill's `data-state` has already flipped but the
  detail text has not yet arrived — acceptable for a secondary, non-blocking piece of text, and much better
  than the alternative (a stale/missing detail until an unrelated future reload). **Flagging this explicitly
  since it is a deviation from the plan's literal file list** (though not from its intent — `readiness-
  provider.tsx` itself has zero lines changed).
- **The `awaiting_snapshot` badge label wording ("Snapshot pending") is my own choice**, not a spec-pinned
  literal — the spec only pinned the `state` value (`awaiting_snapshot`) and the field name/shape
  (`detail: string | null`), explicitly leaving the visible label to the developer. Reviewer/QA should
  judge the wording on its own merits (calm, honest, not "Backend unavailable"), not treat it as a fixed
  contract string.
- **Two new tests are unexecuted, not merely unconfirmed** — see Tests Run above. I am highly confident in
  them from direct code-reading (the seed-CSV inspection is concrete, reproducible evidence, not a guess),
  but I want this stated plainly rather than implied: nobody has seen these two specific tests turn green
  yet. Re-run before merge.
- **Full regression for J-01/J-03/J-04 (required-still-passing) and browser-level verification of J-05 are
  entirely deferred to reviewer/QA** — no browser-qa pass was run by this developer step (consistent with
  the pipeline's own division of labor; this was not skipped due to a shortcut, it was never this step's
  job).

## Definition-of-Done Self-Check (against the phase spec)

- [x] B3 fixed: an ordinary fetch that lands a bar past the last persisted run no longer renders
  `unavailable`/NO-GO — proven by `test_non_benchmark_symbol_fetch_never_affects_servability` (green).
  True unavailability (`unscanned_engine`, no run ever persisted) still renders correctly — proven by
  `test_awaiting_snapshot_never_masks_true_unavailability` (green).
- [x] F1 fixed: the heartbeat advances through the aggregate-refresh finalize phase — proven by
  `test_finalize_hook_ticks_heartbeat_at_least_once_per_date_in_market_phase_loop` (green, asserts the
  heartbeat had advanced past a stale sentinel before EACH of 2 dates' market-phase compute, not just once
  for the whole call).
- [x] `compute_preflight`'s servability stays `ok`/verdict `GO` for the new state alone — proven by
  `test_preflight_servability_ok_for_awaiting_snapshot_state` (green).
- [x] The new query is symbol-scoped, never a whole-table scan (AG-8) — implemented
  (`_latest_benchmark_bar_date` filters on `DailyPrice.symbol == benchmark`); the dedicated SQL-capture test
  (`test_latest_benchmark_bar_query_is_symbol_scoped_not_whole_table_scan`) is written but **unexecuted**
  (see Known Issues) — reviewer should re-run it.
- [ ] Target journey J-05 passing cleanly via browser-qa-agent — **not this step's job**; next pipeline
  stage.
- [ ] Required-still-passing J-01/J-03/J-04 green — **not confirmed by a completed test run this step**;
  reasoned through for the `compute_readiness`-touching pieces (see Tests Run), deferred to reviewer/QA for
  the rest.
- [x] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-4-dev.md` (this file), documenting the
  exact state/field names (`awaiting_snapshot`, `detail` / `readiness_detail`) and the before/after badge
  behavior.

---

## Fix Notes — Attempt 2 (re-review FAIL → fix)

**Date:** 2026-07-20
**Trigger:** `reports/reviews/goal-ops-hardening-iter-4-review.md` — verdict **FAIL** (1 CRITICAL, 1 MINOR).
**Scope of this attempt:** ONLY `apps/backend/app/engine/data_manager.py` + `apps/backend/tests/test_data_manager.py`.
No frontend change this attempt — `apps/frontend/*` untouched, so `goal-ops-hardening-iter-4-frontend.md` is
unchanged and still current. `readiness.py`/`health.py`/`api.ts`/`health-badge.tsx` (attempt-1's B3 work) are
NOT re-touched.

### CRITICAL fixed — F1 was only half-done: the per-date COVERAGE loop never ticked

Attempt-1's F1 fix ticked only the market-phase warm loop plus the finalize function's start. But
`_persist_per_date_coverage_snapshots` — which runs BEFORE the market-phase loop and iterates its OWN
per-date `for d in todo` loop, calling the heavy `refresh_coverage_snapshot_for` /
`_compute_coverage_uncached` once per date (the coverage half of the ~729s finalize tail, attributed to
"per-date coverage_snapshot (378 calls)" in `reports/perf-budgets.md` Item L) — never received `prog` and
got zero `tick()` calls. So the heartbeat still froze across the whole coverage half of the finalize tail,
and "· possibly stalled" would still render on a real heavy multi-date job. The attempt-1 test only spied on
`market_phase_cached`, so it could not catch this.

**Fix (app code, `data_manager.py`):**
- Threaded `prog: JobProgress` into `_persist_per_date_coverage_snapshots`'s signature. It has exactly ONE
  caller — `_refresh_ingest_aggregates` — so the signature change is fully contained (confirmed by `grep`
  across `app/` and `tests/`).
- Added a BARE, heartbeat-only `prog.tick()` (no `activity` arg → stamps only `last_progress_at`, never
  overwrites the pinned "scanning …" activity line) as the first statement inside its `for d in todo` loop,
  firing BEFORE each date's heavy compute — mirroring the market-phase fix exactly.
- Updated the call site to pass `prog`, and updated both `_persist_per_date_coverage_snapshots`'s and
  `_refresh_ingest_aggregates`'s docstrings to state the heartbeat now advances through BOTH per-date loops
  (coverage + market-phase) — i.e. the WHOLE finalize tail. The attempt-1 ticks (function-start + per-date
  market-phase) are unchanged and preserved.

**Test added (`test_data_manager.py`):**
- New fixture `finalize_hook_triple_date_engine` (THREE stored SPY dates; the loop skips the current/latest
  stamp, leaving `todo` = the two earlier dates) + new test
  `test_persist_per_date_coverage_snapshots_ticks_heartbeat_per_date`. It calls
  `_persist_per_date_coverage_snapshots` DIRECTLY — isolating ITS loop rather than the whole finalize hook —
  and spies on `refresh_coverage_snapshot_for` (the way the existing test spies on `market_phase_cached`),
  capturing `prog.last_progress_at` at the moment EACH date's compute is about to run and asserting it had
  already advanced past a deliberately stale sentinel before EVERY date.
- **Proven to catch the bug (TDD red):** I temporarily removed the new `prog.tick()` and re-ran — the test
  FAILS ("date index 0: heartbeat had not advanced before this date's coverage compute", sentinel
  unchanged); I restored the tick — it PASSES. This is the per-date-coverage-loop regression guard the
  review said the market-phase-only spy could not provide.

### MINOR — `test_readiness.py` + `test_health.py` full run: deferred to reviewer/QA, honestly

The MINOR asked to run `pytest tests/test_readiness.py tests/test_health.py -v` to completion to confirm the
two previously-unexecuted `loaded_engine`-dependent tests
(`test_compute_readiness_shape_unchanged_by_preflight_addition` at line 268,
`test_latest_benchmark_bar_query_is_symbol_scoped_not_whole_table_scan` at line 404) pass. I launched that
run; the session-scoped `loaded_engine` fixture build (`bootstrap_runs` + `backfill_forward_returns` over the
real 30-year / 587-symbol seed) is many-minutes-to-hours of TEST-ONLY slowness (repeatedly documented for
this repo), and — as a dispatched subagent — my background run was **reaped when the turn yielded** before it
finished (0-byte output file, no surviving process on re-check). Per the coordinator's explicit direction
and this pipeline's division of labor, I am NOT re-blocking on it: reviewer/QA own full-suite verification.

**Why deferring here is safe:** this attempt-2 fix touches ONLY `data_manager.py` + `test_data_manager.py`.
It does NOT touch `readiness.py` or `health.py` (attempt-1's B3 code, unchanged), and I confirmed by reading
`tests/conftest.py:41` that the `loaded_engine` fixture path (`bootstrap_runs` / `backfill_forward_returns`)
NEVER calls `_persist_per_date_coverage_snapshots` / `_refresh_ingest_aggregates`. So my change is provably
isolated from the readiness/health suite — that suite is a clean re-run of attempt-1 code the reviewer
already reasoned should pass, and nothing in attempt 2 changes its expected outcome. (The suite's tests
already assert the new shape `{"state","detail","warmup"}` and `state in {..., "awaiting_snapshot"}` — read
directly to confirm they match attempt-1's served payload.)

### Tests run this attempt (TMPDIR set per harness; venv `apps/backend/.venv/bin/python`)

| Run | `-k` filter | Result |
|---|---|---|
| New coverage-loop F1 test + existing market-phase F1 test | `finalize_hook_ticks_heartbeat_at_least_once_per_date_in_market_phase_loop or persist_per_date_coverage_snapshots_ticks_heartbeat_per_date` | **2 passed in 0.64s** |
| Same new test with the tick temporarily removed (TDD red proof) | `persist_per_date_coverage_snapshots_ticks_heartbeat_per_date` | **1 failed** (heartbeat frozen at sentinel) → tick restored → passes |
| Full finalize-hook + related group — regression for the `prog` signature change, incl. the end-to-end `test_run_data_job_backfill_wires_finalize_hook_end_to_end` | `finalize_hook or persist_per_date_coverage or aggregates_refreshed or new_snapshot_dates` | **14 passed in 119.70s** |

### Deferred to reviewer/QA
- `pytest tests/test_readiness.py tests/test_health.py -v` to completion (the MINOR — see above; my change is
  provably isolated from it, so this is a confirmation re-run of unchanged code).
- Full J-01/J-03/J-04 regression replay + J-05 browser-qa (never this step's job).

### New consideration found while fixing (NOT fixed — flagged per fix-mode protocol)
Two SINGLE, O(1) steps in the finalize tail still do not tick: `refresh_coverage_snapshot(...)` (the
current-stamp coverage compute) and the one-time `prefilled_bar_cache` whole-table bar load at the top of
`_persist_per_date_coverage_snapshots`. These are NOT per-date (they run once regardless of date count); the
perf-budget attributes the ~729s tail to the two 378-call per-date LOOPS, not to these one-time steps, so
each is comparable to a single loop iteration (~1–2s) and is very unlikely to exceed the 20s
`heartbeat_stale_seconds` threshold alone. The review scoped the fix to the per-date loop, and per fix-mode
protocol I did NOT expand scope to these — flagging so the reviewer/auditor can decide whether a
belt-and-suspenders tick around the one-time prefill is warranted on the deepest (30y) basis.
