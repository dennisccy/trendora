# goal-ops-hardening-iter-4 Execution Plan

Alignment check: this iteration targets J-05 ("Aggregates precomputed at ingest") from `docs/goal.md`,
closing two pre-existing, out-of-scope trust-surface defects (B3, F1) that iter-3's audit/closure surfaced
as the reason J-05 can't pass browser-qa cleanly. No scope creep found — the phase spec's own OUT OF SCOPE
section is disciplined (explicitly defers J-06, `scripts/start-backend.sh` enforcement, `coverage_snapshot`
changes, `initializing`-state changes, and the J-05 demo walkthrough), and every in-scope item traces to a
named anti-goal (AG-3 honesty, AG-8 no whole-table scans). Confirmed against the actual codebase (not just
the spec) — see file-by-file notes below.

## What to Build
- **B3 fix** — `compute_readiness` (`app/engine/readiness.py:129`) currently flips the WHOLE global
  readiness badge to the crash-identical `unavailable` state whenever `latest_data_date(session)` (a
  **whole-table** max over all 590 symbols) outruns the latest persisted `ScannerRun`. Replace that
  comparison with the **benchmark symbol's own latest bar** (`cfg.etfs.index[0]`, i.e. SPY — the same
  symbol `forward_testing.walk_forward_asof_dates`/`warmup._warmup_dates` already use to define the trading
  calendar; confirmed at `forward_testing.py:324`, `benchmark = cfg.etfs.index[0]  # SPY defines the
  trading calendar`) via one new indexed per-symbol max query (same shape as `latest_data_date`, filtered
  to one symbol — never a whole-table scan, AG-8). An unrelated symbol's fetch no longer touches
  servability at all.
- Add a 4th readiness state (spec's committed literal: `awaiting_snapshot`) for "a servable last run exists
  but the benchmark's own latest bar has advanced past it, no run yet" — distinct from `unavailable` (true
  no-servable-snapshot) and `initializing` (cadence warm-up, unchanged). `latest_run is None` (a true
  never-scanned DB) MUST still resolve unconditionally to `unavailable` — regression guard, pins the
  existing `unscanned_engine` fixture.
- Add one new optional `detail` field to `compute_readiness`'s return (honest human-readable string, `null`
  except for the new state — mirrors the existing `PreflightComponent.detail` naming precedent already in
  this codebase). Add a pinning test that `compute_preflight`'s existing `servable = state != UNAVAILABLE`
  check already treats the new state as non-breaching — no logic change needed there, confirmed by reading
  `readiness.py:270`.
- **Wiring gap not named in the phase spec's own file list, found by reading the endpoint** —
  `apps/backend/app/api/health.py`'s `health()` handler does `"readiness": readiness["state"]` (line 84):
  it discards everything else in `compute_readiness`'s dict. The new `detail` value must be added as its
  own key on this same response, or it is computed correctly but never reaches the frontend. Add this file
  to the developer's touch-list explicitly.
- **F1 fix** — `_refresh_ingest_aggregates` (`app/engine/data_manager.py:3034`) never calls `prog.tick()`
  during its own per-date market-phase warm loop (`:3072-3078`), even though the main scan loop already
  does (`:2863`, `prog.tick(f"scanning {d.isoformat()} ...")`). Add `prog.tick(...)` at the function's start
  and inside that per-date loop so `JobProgress.last_progress_at` advances through the whole finalize tail
  (measured at ~729s for a full rebuild in `reports/perf-budgets.md` Item L) instead of freezing into the
  frontend's false "· possibly stalled" (`apps/frontend/app/data/page.tsx:2483`, vs
  `job_progress.heartbeat_stale_seconds`).
- **Frontend** — widen `ReadinessState` (`apps/frontend/lib/api.ts:115`, currently `"ready" |
  "initializing" | "unavailable"`) with the new literal; add the new optional detail field to
  `HealthStatus`. Add a 4th pill branch to `HealthBadge` (`apps/frontend/components/health-badge.tsx`):
  distinct `data-state="awaiting_snapshot"`, reuse the existing `Badge variant="accent"` (already defined,
  `border-accent bg-surface-2 text-accent` — no new color token), visible text that is NOT "Backend
  unavailable", plus the recovery-pointer detail text pointing at Data Manager (`/data`).
- **Confirmed by reading, do NOT touch:** `readiness-provider.tsx` (its `data.readiness === "ready"`
  cadence check at line 66 and its own-failure `setState("unavailable")` fallback at line 69 both already
  behave correctly for the new state — verified by inspection) and `preflight-banner.tsx` (reads only the
  composed `preflight.verdict`, never `readiness.state` directly — verified by inspection).
- Unit tests: extend `test_readiness.py`'s fixture matrix (non-benchmark-symbol-unaffected case; benchmark's
  own bar advances → new state + detail; preflight-still-ok pinning test; `unscanned_engine` regression
  guard unchanged; index-bounded-query assertion). Extend `test_data_manager.py` for the new `tick()` calls
  (assert `last_progress_at` advances across the per-date market-phase loop, not just the main scan). Check
  `test_health.py::test_health_carries_readiness_and_warmup`'s `body["readiness"] in {"ready",
  "initializing", "unavailable"}` assertion — the `loaded_engine` fixture is not expected to produce the
  new state (its latest snapshot is synced at boot), so this should keep passing unedited, but verify rather
  than assume.
- Regression: required-still-passing J-01/J-03/J-04 via browser-qa deterministic replay + LLM fallback.
  Re-run the previously-SKIPPED UT-04 (cold-boot coverage-from-storage check, TC-8) against a fresh DB copy
  — closes iter-3's one open gap (T2).
- Dev handoff at `docs/handoffs/goal-ops-hardening-iter-4-dev.md` documenting the exact state/field names
  chosen and the before/after badge behavior (DoD requirement).

## Agents Required
- developer: yes -- implements the backend fix (`readiness.py` servability widening + new state/detail
  field, `data_manager.py` heartbeat tick fix, `health.py` response wiring), the frontend fix (`api.ts` type
  widening, `health-badge.tsx` new pill branch), all associated unit tests, and the dev handoff.
- backend-data: yes -- `app/engine/readiness.py`, `app/engine/data_manager.py`, `app/api/health.py`,
  `tests/test_readiness.py`, `tests/test_data_manager.py`, `tests/test_health.py` (verify/extend).
- frontend-ux: yes -- `apps/frontend/lib/api.ts`, `apps/frontend/components/health-badge.tsx`.

## Frontend Present
yes

## Files to Create/Modify
- `apps/backend/app/engine/readiness.py` -- widen `compute_readiness`'s servability check to a
  benchmark-scoped (`cfg.etfs.index[0]`) indexed max-date query instead of `latest_data_date`'s whole-table
  scan; add the `awaiting_snapshot` state + `detail` field; keep `latest_run is None` → `unavailable`
  unconditional.
- `apps/backend/app/api/health.py` -- serve the new `detail` value from `compute_readiness`'s dict on the
  `/api/health` JSON response (currently only `readiness["state"]` is exposed at line 84).
- `apps/backend/app/engine/data_manager.py` -- `_refresh_ingest_aggregates` (~line 3034): add
  `prog.tick(...)` at function start and inside the per-date market-phase loop (~lines 3072-3078).
- `apps/backend/tests/test_readiness.py` -- new fixture-matrix cases per the phase spec's TC-2/TC-3/TC-5/
  TC-6/TC-10.
- `apps/backend/tests/test_data_manager.py` -- new test(s) for `_refresh_ingest_aggregates`'s `tick()` calls
  (TC-7).
- `apps/backend/tests/test_health.py` -- verify (extend only if actually needed) the readiness
  state-membership assertion and the additive-preflight existing-keys check.
- `apps/frontend/lib/api.ts` -- widen `ReadinessState` (line 115) with the new literal; add the new optional
  detail field to `HealthStatus`.
- `apps/frontend/components/health-badge.tsx` -- add the 4th pill branch (distinct `data-state`, `Badge
  variant="accent"`, non-"Backend unavailable" text, recovery-pointer detail).
- `docs/handoffs/goal-ops-hardening-iter-4-dev.md` -- dev handoff (required by DoD).

Do NOT touch: `apps/frontend/components/readiness-provider.tsx`, `apps/frontend/components/
preflight-banner.tsx`, `apps/backend/app/engine/warmup.py`, `ensure_latest_snapshot` (`main.py:73`), the
boot warm-up loop, the `coverage_snapshot` table/finalize gate, `aggregates_refreshed`'s nullability
contract, any J-01/J-03 shipped field, `scripts/start-backend.sh`, `docs/goal.md`.

## UI Evolution
- New user-facing capability: none new -- this is an honesty fix to the EXISTING global readiness badge and
  job-progress heartbeat (both shipped in prior iterations).
- New information displayed: a calm, visually distinct 4th badge state ("new data landed, snapshot pending"
  in effect) with a recovery-pointer detail string naming the condition and pointing at Data Manager; the
  job-progress heartbeat ("updated Ns ago") now stays fresh through a heavy job's aggregate-refresh tail
  instead of freezing into a false "possibly stalled".
- New user actions: none -- no new form/button; the new badge state's detail text reuses existing
  navigation to `/data`.
- UI surface changes: `HealthBadge` (global, top bar, every page) gains a 4th visual state. No new page or
  panel.
- Navigation changes: none.

## Visual Requirements
- Component patterns: reuse the existing `Badge` component's `accent` variant (already defined in
  `apps/frontend/components/ui/badge.tsx`: `border-accent bg-surface-2 text-accent`) for the new pill -- no
  new color token, no new component.
- Layout: no layout change -- the badge renders in its existing top-bar slot via the same `if/else if`
  chain `HealthBadge` already uses for `loading`/`ready`/`initializing`/`unavailable`.
- Key visual effects: none new -- match the existing pill treatment (small colored status dot + label),
  consistent with the other three states' styling.
- States to handle: the new `awaiting_snapshot` state must read visually and textually distinct from
  `unavailable` (never "Backend unavailable") and from `initializing` (a different condition -- new data
  landed, not cadence warm-up). No other loading/empty/error treatment changes in scope this iteration.

## Key Test Scenarios
- A servable run persisted for the benchmark's own latest bar date still yields `ready`/`initializing`
  unchanged (unaffected-baseline regression guard).
- A NON-benchmark symbol's bar landing after the last run does NOT change `state` at all (the actual B3
  reproduction case: an ordinary "Fetch EOD prices" job must no longer flip the badge).
- The BENCHMARK symbol's own latest bar advances past the last run with no run yet for that date →
  `state == "awaiting_snapshot"`, non-null `detail` naming the condition + recovery action; `HealthBadge`
  renders `data-testid="readiness-badge"` `data-state="awaiting_snapshot"`, non-danger visual treatment,
  text that is NOT "Backend unavailable".
- `compute_preflight`'s servability stays `ok` / verdict not forced to `NO-GO`/`DEGRADED` by the new state
  alone (pinning test).
- No `ScannerRun` ever persisted (`unscanned_engine` fixture) still resolves to `unavailable` -- the new
  state must never mask true unavailability.
- A real multi-date backfill/rebuild's `JobProgress.last_progress_at` advances at least once per date during
  the aggregate-refresh finalize phase; the `/data` live job card never shows "· possibly stalled" while the
  job remains healthy.
- The new benchmark-scoped query reads via the `(symbol, date)` index for one symbol only -- never a
  `daily_prices` whole-table scan (AG-8).
- Fresh/never-ingested DB cold-boot: `/data`'s coverage panel renders from the persisted payload within
  budget, no full `daily_prices` prefill (closes the previously-SKIPPED UT-04).
- Required-still-passing J-01/J-03/J-04's existing scripted acceptance (breakdown/chunking/boot/badge/
  logfile) all still pass unedited after this iteration's edits.
- Browser: J-05's full acceptance passes cleanly via browser-qa-agent -- read the raw `ui-test-results.md`
  verdict directly, not only the QA report's summary (iter-3's named lesson: the QA report previously
  overstated a clean 12/12 and buried a real browser FAIL).
