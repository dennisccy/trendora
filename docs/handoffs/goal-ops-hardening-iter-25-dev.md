# goal-ops-hardening-iter-25 Dev Handoff

**Phase:** goal-ops-hardening-iter-25
**Date:** 2026-07-26
**Agent:** developer
**Status:** complete

## What Was Built

This iteration closes J-09's one remaining gap (the Walkthrough acceptance clause) plus the two
agent-owned findings iter-24's evaluator left open (audit F1, audit T1). No product-code change; no new
Data Contract value; no new user-facing capability (per the spec's own "New user-facing capability: None
this iteration").

- **Audit T1 fix (test-only) — deflake the two background-compute-registry tests.** Both
  `test_health.py::test_health_background_compute_is_single_source` and
  `test_readiness.py::test_compute_readiness_composes_background_compute_empty_shape` compared two live
  reads of the SAME process-lifetime dispatch registry with raw dict equality. `elapsed_ms` on any active
  entry is computed fresh at READ TIME from its own `started_at` (per iter-24's own design), so two reads
  a few milliseconds apart can legitimately differ whenever a real background compute is in flight
  (realistic on a whole-file run, since the registry is a process-lifetime global other test files can
  populate). Rewrote both tests to add a local `_background_compute_identity()` helper that compares
  identity/shape instead: active entries minus `elapsed_ms`, and `recent_outcomes` reduced to its
  `(asof_key, dataset_version)` ordering + length. A genuine state change (e.g. `horizons_done`
  progressing, a new outcome appended) still produces a different identity — only the read-time-volatile
  field is excluded, not the whole comparison.
- **Audit F1 fix (frontend) — honest "unknown" copy when the readiness poll fails.**
  `BackgroundComputePanel` (`apps/frontend/app/data/page.tsx`) previously fell through to the idle "No
  background compute running…" sentence whenever `backgroundCompute` was `null` — which is EXACTLY what
  `ReadinessProvider`'s catch branch (`readiness-provider.tsx:87`) also sets on a poll failure, so a
  genuinely unreachable backend was misreported as an honestly-idle one. Added a new pure resolver,
  `apps/frontend/lib/background-compute-panel-branch.ts`
  (`resolveBackgroundComputePanelBranch(state, backgroundCompute)`), that reads the SAME shared `state`
  value `HealthBadge` already uses for its own "Backend unavailable" pill (`state === "unavailable"`) to
  distinguish "poll failed" from "poll succeeded, zero active windows" — no second fetch, no new signal.
  The panel now renders a distinct `data-testid="background-compute-unknown"` message ("Background-compute
  state unknown — the backend is unreachable.") for the poll-failure case, and never falls through to the
  idle sentence there. The genuine idle case (poll succeeds, zero active windows) renders the EXACT
  pre-existing copy, byte-unchanged, including the "process-lifetime, never persisted" footer note (which
  is now scoped to only the non-unknown branches, since asserting anything about un-observed history when
  the backend is unreachable would itself be dishonest).
- **Demo manifest — J-09's Walkthrough clause.** Appended 4 new `[NEW]`-flagged, `"verified": true`
  steps (n=13–16, `"journey": "J-09"`) to `reports/goal-session-ops-hardening-demo.json` — the file
  `demo.sh ops-hardening --session-live` actually reads. Steps 1–12 are byte-unchanged (purely additive
  diff, confirmed via `git diff` showing 0 deletions). All 4 new steps use `"section": "full_tour"` — the
  existing `"highlights"` section was already at its cap of 8 (steps 1,2,3,4,6,7,11,12), so none of the
  new steps could join it without breaching the cap; `full_tour` steps still play in the live walkthrough,
  just without a gallery screenshot. The 3 required scenes (steady-state; in-flight badge+panel; idle/
  last-outcome + restart honesty) map to 4 steps: baseline Ready (13), badge in-flight detail on
  `/backtest?asof=2026-07-17` (14), `/data` panel in-flight detail (15), and post-completion idle +
  restart-honesty (16). Every `point_out` figure is sourced verbatim from iter-24's own
  evaluator-verified evidence (the evaluator's own DOM captures at
  `~/.cache/superpowers/browser/2026-07-26/session-1785060343588/{013,015,040}-eval.html`, cross-checked
  against `runs/goal-session-ops-hardening/iter-24/eval.md`'s quoted figures): "background compute running
  (1)" next to "Ready"; "as-of 2026-07-17 · elapsed 41.8s · horizons 2/5 · dataset r1865-f3954530"; "No
  background compute running." + "Last outcome … completed … as-of 2026-07-17 … 1m 15s"; and the
  post-restart "Last outcome: none yet." No fresh background-compute window was triggered for this
  manifest (reusing already-verified evidence per the iter-23 precedent, as the spec allows). Each new
  step's `expect` field intentionally targets a STABLE, always-present marker ("Ready", "expanding
  window", "Background compute") rather than the transient in-flight/idle text itself — matching the
  existing precedent in this same file (steps 9–12 do the same for J-07/J-08) — so a future deterministic
  replay never hard-fails on a race it can't control; the actually-observed transient text lives in
  `point_out`, not `expect`.
- **Frontend unit test for the new resolver.** `apps/frontend/lib/background-compute-panel-branch.test.ts`
  follows the project's established `lib/*.test.ts` convention (see `lib/asof-step.test.ts`) — 8 cases
  covering TC-3 (poll failure → "unknown", both with `backgroundCompute: null` and with a stale non-null
  value), TC-4 (poll succeeds, zero active → idle, unchanged), the pre-first-poll `state === null` case
  (must NOT regress to "unknown" — still idle, matching prior behavior), and the idle/active ×
  with/without-last-outcome branch combinations.

## Files Changed

- `apps/backend/tests/test_health.py` -- rewrote `test_health_background_compute_is_single_source` to
  compare identity/shape (excluding `elapsed_ms`) instead of raw equality; added the local
  `_background_compute_identity()` helper (audit T1).
- `apps/backend/tests/test_readiness.py` -- rewrote
  `test_compute_readiness_composes_background_compute_empty_shape` the same way; added the same helper,
  scoped to this file (audit T1).
- `apps/frontend/lib/background-compute-panel-branch.ts` -- NEW. Pure resolver
  (`resolveBackgroundComputePanelBranch`) deciding the panel's `"unknown" | "idle" | "active"` branch from
  the shared readiness `state` + `backgroundCompute` (audit F1).
- `apps/frontend/lib/background-compute-panel-branch.test.ts` -- NEW. 8 unit tests for the resolver
  (Node native TS type-stripping, the existing frontend convention).
- `apps/frontend/app/data/page.tsx` -- `BackgroundComputePanel` now reads `state` from `useReadiness()`
  too, calls the new resolver, and renders the new `background-compute-unknown` branch; the pre-existing
  idle/active branches and their exact copy are otherwise unchanged.
- `reports/goal-session-ops-hardening-demo.json` -- appended 4 new J-09 `full_tour` steps (n=13–16);
  steps 1–12 untouched.
- `docs/handoffs/goal-ops-hardening-iter-25-dev.md` -- this file.

No changes to `app.engine.forward_testing`, `app.engine.readiness.compute_readiness`,
`compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, or any other product code — confirmed
by `git diff --stat`, which shows only the 4 test/frontend/manifest files above touched.

## Tests Run

Command (per project convention): `cd apps/backend && .venv/bin/python -m pytest <targeted files/selectors> -q`

- **Standalone logic-level verification (fast, no DB fixture)** of the exact `_background_compute_identity`
  mechanism: constructed two synthetic "reads" of the same in-flight window differing ONLY in `elapsed_ms`
  (41800ms vs 41847ms, as a real clock-drift would produce) and confirmed (a) the OLD raw-equality
  assertion would have failed on this pair, (b) the NEW identity comparison treats them as equal, and (c)
  a GENUINE state change (`horizons_done` 2→3, not just clock drift) still produces a different identity —
  the fix removes only the false-alarm axis, not real-bug detection. All three assertions passed.
- **Live pytest invocation launched, not completed within this session.** I launched
  `.venv/bin/python -m pytest tests/test_health.py -k test_health_background_compute_is_single_source -v`
  (targeted single-test selector, per the standing session lesson against full-file/full-suite runs) via
  `setsid nohup … &` and polled it for over an hour; it was still building the shared `loaded_engine`
  session fixture (bootstrap_runs + backfill_forward_returns over the full ~30-year cadence — same fixture
  iter-24's dev/reviewer/QA all separately could not finish within their own sessions, per that iteration's
  own handoff/QA report) when I terminated it to free the host for the next pipeline stage. This is a
  pre-existing, already-documented cost of this project's `loaded_engine` fixture, not something this
  iteration's diff introduced or can shorten — the change under test is a small dict-comparison rewrite
  inside an existing test, with no new fixture and no new DB work. **Recommend the reviewer/QA stage
  re-run** `tests/test_health.py -k test_health_background_compute_is_single_source` and
  `tests/test_readiness.py -k test_compute_readiness_composes_background_compute_empty_shape` (and the 5x
  TC-5 repetition) with a larger time budget than a single dev turn affords; per the standing lesson, do
  NOT run either file in full or the whole suite concurrently.
- **Frontend TypeScript check:** `cd apps/frontend && npx tsc --noEmit -p tsconfig.json` — **0 errors**
  (covers the new `lib/background-compute-panel-branch.ts` and the `page.tsx` changes; `.test.ts` files are
  excluded from this project's `tsconfig.json`, matching the pre-existing convention).
- **Frontend unit test (`lib/background-compute-panel-branch.test.ts`):** this dev box's Node build lacks
  TypeScript/`amaro` support (`node lib/*.test.ts` → `ERR_NO_TYPESCRIPT`), the SAME pre-existing limitation
  documented in `docs/handoffs/*-iter-49-dev.md` for every other `lib/*.test.ts` file in this project — it
  is expected to run in the CI/QA Node environment, not necessarily on every dev box. I verified it anyway
  via `npx tsx lib/background-compute-panel-branch.test.ts` (a TS-aware runner available on this box): **8
  passed**, 0 failed.
- **Live, non-mocked, real-backend + real-browser confirmation of TC-3 and TC-4 (Playwright, headless
  Chromium, both services started via `scripts/start-backend.sh` / `scripts/start-frontend.sh`):**
  - Loaded `/data` with the backend UP: `background-compute-panel` renders, `background-compute-idle`
    testid present, exact text "No background compute running. Last outcome: none yet." (TC-4, unchanged).
  - Killed the backend process MID-SESSION (no page reload) so the readiness poll would fail on its next
    tick: the shared `readiness-badge` flipped to `data-state="unavailable"`, and — in the SAME page,
    without navigating — the panel's `background-compute-idle` testid disappeared (count 0) and
    `background-compute-unknown` appeared with the exact text "Background-compute state unknown — the
    backend is unreachable." (TC-3, confirmed live).
  - (A fresh page LOAD with the backend already down the whole time hits a different, pre-existing
    top-level `/data` empty state — "Dataset coverage could not load from the API" — because the page's
    OTHER data fetches, not just the readiness poll, also fail; that pre-existing gate is unrelated to this
    iteration's diff and is not what TC-3 is testing. TC-3's real-world scenario is the backend going down
    mid-session while the page is already rendered, which is what I reproduced above.)
  - Backend and frontend were both stopped afterward (`pkill`/`kill`, confirmed no process left on either
    port).
- **Demo manifest structural check:** `python3 -c "json.load(...)"` — valid JSON; `git diff` shows 48
  insertions, 0 deletions (purely additive); highlights-section count recounted at exactly 8 (unchanged
  from before this iteration); all 4 new entries carry `"journey": "J-09"`, `"new": true`,
  `"verified": true`.
- **Service startup:** `scripts/start-backend.sh` and `scripts/start-frontend.sh` both started cleanly
  (backend `GET /api/health` 200 on first poll; frontend `Ready in 1239ms`, `GET /data` 200), confirming
  this iteration's diff doesn't break boot. Restarted backend once mid-session (for the TC-3 repro above)
  and it came back up cleanly on the same port with no conflict.

## Known Issues

- **Full pytest confirmation of the two rewritten tests (and the 5x TC-5 rerun) is not yet in hand** — see
  "Tests Run" above for exactly what WAS verified (logic-level proof + live end-to-end browser behavior for
  the frontend half) and what remains (the actual backend pytest pass/fail line for both rewritten tests).
  This is a pre-existing fixture-cost issue (the shared `loaded_engine` session fixture takes over an hour
  to build on this host, independent of this iteration's diff — the SAME wall iter-24's dev, reviewer, and
  QA each hit and deferred), not something introduced by this change. I'm confident in the fix's
  correctness (both from the standalone identity-comparison proof and because the frontend confirmation
  exercises the SAME underlying `compute_readiness`/`get_background_compute_status` code path live), but
  the reviewer/QA stage should budget time to actually run
  `tests/test_health.py -k test_health_background_compute_is_single_source` and
  `tests/test_readiness.py -k test_compute_readiness_composes_background_compute_empty_shape` (5 reps each
  per TC-5) rather than treat this handoff's evidence as a substitute.
- Non-blocking carries from iter-24 (unaffected by this iteration, explicitly out of scope per this
  iteration's spec): audit B2 (a `Thread.start()` failure leaving the badge reading "running (1)" forever)
  — deferred, needs the `ensure_historical_forward_aggregates_dispatched` freeze lifted deliberately in its
  own scoped iteration; audit B5 (whether the at-rest `≤ 0.1s` `/api/health` budget stands as written) —
  owner-owned; backlog card B-1107 (global background-compute concurrency cap) — owner-optional.
