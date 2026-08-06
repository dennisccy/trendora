# goal-ops-hardening-iter-50 Execution Plan

## What to Build

One risky backend change (per goal.md's "one risky change per iteration" loop mechanic, and the
iter-49 evaluator's explicit instruction that these two land as ONE job), plus one small same-subsystem
companion fix, plus two verification-only riders (J-05, J-06):

- **Bound `compute_factor_lab_all`'s crash frame (J-07, the top-priority target).**
  `apps/backend/app/engine/research.py:1051` — inside the per-`(factor, horizon)` loop (lines ~1034-1053),
  `obs = [...]` builds a full transient list-of-dicts (one dict per observation, ~4 keys) and then
  `sorted(obs, key=lambda o: (o["factor"], o["ticker"], o["run_id"]))` sorts it. This is the confirmed
  crash frame from iter-49's own live traceback (evaluator log: "raised an **uncaught** MemoryError at
  `research.py:1051` (`sorted(obs, ...)`" — NOT a log-message inference, an actual traceback read, per the
  iter-49 lesson this spec binds to). The shared pool it's built from (`_all_factor_observations_by_horizon`,
  already iter-31/iter-52 bounded per the spec's own explicit carve-out) is NOT the site to touch. Two
  sub-requirements:
  1. Bound the obs-build + sort so a live page view cannot allocate an unbounded transient structure on
     top of concurrent ingest/warm work, with every `(factor, horizon, decile)` figure byte-identical to a
     pinned pre-fix reference (TC-3). `factor_lab_all_cached` (research.py:3439) and its caller
     `GET /research/factor-lab?all=true` (`apps/backend/app/api/research.py:76-126`) are the request path
     this closes.
  2. Wrap the call so a `MemoryError` raised inside the bounded loop is caught by the module's existing
     isolation convention and degrades the request honestly instead of crashing the process — mirror
     `evidence.py`'s per-claim "isolate-and-continue" convention (`evidence.py:171-189`: catch
     `MemoryError` distinctly, log via the module's `_log_isolation_failure`-style helper, set an honest
     status field, never let it propagate) rather than the ingest warm loops' break-on-MemoryError
     convention (that one is for a background loop that can defer; this is a live request that must still
     answer). `factor_lab_all_cached` currently has NO exception handling around
     `compute_factor_lab_all(session, cfg, as_of=as_of)` (research.py:3505) — today it propagates straight
     up to FastAPI, which is how iter-49's crash reached OpenBLAS's own allocation abort and killed the
     process. A dedicated regression test under a tightened `ulimit -v` drill proves this (TC-2), run 3-5
     consecutive times (iter-44 lesson: one green run proves nothing).

- **Warm-in-progress guard between the boot re-warm and the ingest finalize-tail warm (J-07).**
  `apps/backend/app/engine/warmup.py:198` (`_warm_drawdown_expectations`, called from `_run_warmup` at
  line ~303) and `apps/backend/app/engine/data_manager.py`'s `_refresh_ingest_aggregates` (line 3756,
  specifically its `drawdown_expectations_warm` phase at ~4106-4203) must never run their heavy per-claim
  loops concurrently in the same process — this is the SECOND of the two proven-concurrent crash
  contributors from iter-49's own traceback read (three heavy loops were live at once: the finalize tail,
  the boot re-warm, and the Factor Lab request; the boot re-warm and finalize tail both "aborted
  gracefully" that time, but nothing PREVENTS them running concurrently — they just happened not to
  collide fatally with each other). Add a shared in-process guard (a lock/flag on the `data_manager`
  module, following the SAME single-flight/guard shape already established by `_COVERAGE_LOCK` /
  `_COVERAGE_INFLIGHT` at `data_manager.py:978-980`, or the `_JOBS` registry at line 2480 if a running-job
  check is simpler) so whichever of the two tries to start second DEFERS (logs + retries on its own next
  natural trigger — boot re-warm retries on the next boot/restart; ingest finalize retries on the next
  ingest job), non-fatal either way. Required in BOTH trigger orders (TC-4 boot-first, TC-5 ingest-first —
  the guard must not be a one-directional check).

- **Skip the unconditional `phase_context_by_date` precompute when nothing needs it (small companion fix,
  same subsystem iter-49 itself modified).** `data_manager.py:4108-4117`'s
  `_dd_phases = market_phase.phase_context_by_date(session, as_of=None, config=cfg)` runs unconditionally
  before the per-claim `drawdown_expectations_warm` loop, even when the ledger has zero claims needing
  (re)computation. Measured live cost: **23.6-23.9s**, confirmed by `reports/perf-budgets.md` Item R
  Addendum 6's mid-cluster health-poll-stall attribution (13 of the ≤2s-ceiling breaches, 3/3 runs, fall
  exactly inside this precompute's window). Skip the precompute call entirely when no claim in the ledger
  needs it, closing that stall cluster (TC-6). Do NOT touch the `phases` parameter's existing per-claim
  fallback semantics (byte-identical when a claim does need it).

- **Verification-only riders — no new code, live re-drill only:**
  - **J-05**: the in-app defining case (a live in-app backfill of exactly one unsnapshotted historical
    day, via `/data`, never an isolated drill) has never completed because the crash kept interrupting it.
    Once the crash source above is removed, re-run it live and capture real evidence (TC-10, TC-11). Golden
    discipline (iter-47/48 lesson): read `journey-scripts/J-05.json`'s actual step content before trusting
    it, confirm it asserts against the NEW run's own row/testid, not page-wide text.
  - **J-06**: `/research/factor-lab`'s page load has never had a clean, in-budget measurement for the same
    reason (the page kept crashing the backend). Measure time-to-interactive + on-load API latency on a
    warm backend in prod mode and record in `reports/perf-budgets.md` (TC-12).

- **Required-still-passing verification (no code change expected):** J-01, J-03, J-04, J-08, J-09 each
  need a real executed row (PASS or FAIL, never SKIP/blank) via deterministic replay + LLM fallback,
  because the backend must now stay continuously available for the FULL iteration (this is what the
  Factor Lab bound + warm-in-progress guard directly enable — J-04/J-08/J-09 recorded SKIP for the last
  several rounds specifically because the backend had crashed before their check ran).

## Out of Scope (per phase spec — do not touch)

- The health-poll EARLY cluster (`coverage_membership_timeline_refresh`) and LATE cluster
  (`combination:composite:h20`, `_combination_observations`'s ~250s cost) — both real, both named in
  Addendum 6, both separate diagnosis efforts. Only the MID cluster (`phase_context_by_date`) is this
  iteration's to close.
- Raising `memory_cap_mb` / `malloc_arena_max` (AG-10) — the fix must work inside the existing 8192MB
  envelope.
- Re-opening `_all_factor_observations_by_horizon`, `_all_fr_slice_map`, `_combination_observations`, or
  any iter-31/46/47/48 already-confirmed bound.
- `journey-scripts/J-05.json` rotation — only if THIS iteration's own live drills consume the golden's
  configured target date (confirm live, before running, that it still has 0 snapshot rows).
- `config.yaml`, `project-extensions/host-guard/host-guard.env`, `scripts/start-backend.sh`, `scripts/dev.sh`
  — frozen files, must stay byte-identical (`git diff` empty before and after every change, TC-10/AG-10).
- Everything in the phase spec's own OUT OF SCOPE list (iter-31/e, iter-32/f, iter-35/k, iter-36/n,
  iter-37/o, iter-37/q, iter-39/u, iter-46/az, iter-46/ba, iter-47/bd, iter-47/bf, iter-47/bi, iter-48/bj;
  the Regime Lab's separate 8192MB-cap hit; the permanently-failed-warmup badge wording).

## Agents Required

- developer: yes -- backend-only implementation of the three code changes above (Factor Lab bound +
  isolation wrapper, warm-in-progress guard, `phase_context_by_date` conditional skip), plus the required
  unit/integration tests (byte-identity, `ulimit -v` pressure drill x3-5, guard test in both trigger
  orders, skip-when-nothing-to-do test). No frontend/UI work — `Frontend Present: no` per the phase spec.
  (backend-data: yes; frontend-ux: no.)

## Frontend Present
no

## Files to Create/Modify

- `apps/backend/app/engine/research.py` -- bound `compute_factor_lab_all`'s per-`(factor,horizon)`
  obs-build + sort (~line 1034-1053); the `MemoryError` isolation wrapper likely lands in
  `factor_lab_all_cached` (~line 3439-3528) around its `compute_factor_lab_all(...)` call (~line 3505), or
  inside `compute_factor_lab_all` itself — developer's call, following the evidence.py precedent.
- `apps/backend/app/engine/warmup.py` -- `_warm_drawdown_expectations` (line 153) gains the shared
  warm-in-progress guard check/defer before it starts its per-claim loop.
- `apps/backend/app/engine/data_manager.py` -- `_refresh_ingest_aggregates`'s `drawdown_expectations_warm`
  phase (~line 4106-4203) gains the SAME guard (set/clear around its own heavy-loop window) and the
  conditional `phase_context_by_date` skip (~line 4108-4117) when zero claims need (re)computing. New
  module-level lock/flag near the existing `_COVERAGE_LOCK`/`_JOBS` precedent (~line 978 or 2480).
- `apps/backend/tests/test_research_streaming.py` -- TC-3 byte-identity test for the bounded
  `compute_factor_lab_all` against a pinned pre-iter-50 reference, every `(factor, horizon, decile)` figure.
- `apps/backend/tests/test_data_manager.py` -- TC-4/TC-5 warm-in-progress guard tests (both trigger orders);
  TC-6 test proving `phase_context_by_date` is not invoked when zero claims need recomputation.
- `apps/backend/tests/test_start_backend_script.py` or a new/existing test module -- TC-2 tightened
  `ulimit -v` memory-pressure drill against `compute_factor_lab_all`'s bounded loop, run 3-5 consecutive
  times, proving the `MemoryError` is caught and degrades honestly (never escapes to kill the process).
- `reports/perf-budgets.md` -- append-only: TC-1 live re-drill results (finalize-tail warm concurrent with
  a `/research/factor-lab` view, no uncaught `MemoryError`, health stays 200), J-06's Factor Lab page-load
  budget measurement, J-07's VmPeak margin, TC-6's before/after mid-cluster stall closure.
- `docs/handoffs/goal-ops-hardening-iter-50-dev.md` -- required dev handoff (Definition of Done item 8).
- `runs/goal-session-ops-hardening/state/blueprint.md` -- iter-50 changelog paragraph (Data Contract row
  unchanged — no new served value, per the spec's own "Data-contract additions: None").

## UI Evolution
N/A — `Frontend Present: no`. No new UI surface, no changed rendering, no new controls or displayed
values (per the phase spec's own "New user-facing capability: None new" / "New information displayed:
None" / "New user actions: None" / "UI surface changes: None").

## Key Test Scenarios

(Mirrors the phase spec's TC-1 through TC-14 verbatim — see `docs/phases/goal-ops-hardening-iter-50.md`
for full text. Highlights the developer must not skip:)

- TC-1/TC-9: live committed DB, ingest finalize-tail warm running, a user loads `/research/factor-lab` —
  `compute_factor_lab_all` completes without an uncaught `MemoryError`, and an immediately-following
  `GET /api/health` still answers 200 (this is the exact iter-49 crash scenario, now must survive it).
- TC-2: tightened `ulimit -v` drill via `scripts/start-backend.sh` against a full-scale live-shaped
  fixture — any `MemoryError` in the bounded sort loop is caught and degrades honestly, 3-5 consecutive
  runs, no new escape site on any run.
- TC-3: bounded `compute_factor_lab_all` vs a pinned pre-iter-50 reference oracle — every
  `(factor, horizon, decile)` figure byte-identical (AG-3).
- TC-4/TC-5: guard holds in BOTH trigger orders (boot-re-warm-first, ingest-finalize-first) — never two
  heavy warms live at once in one process; the later one defers, logs, and resumes on its own next
  natural trigger (never silently drops the work).
- TC-6: a real live ingest finalize-tail run where zero drawdown-expectation claims need recomputing —
  `phase_context_by_date` is skipped entirely, not invoked.
- TC-7/TC-8: J-07 step 1's full-horizon forward-aggregate warm running live, `GET /api/health` polled once
  per second — every poll HTTP 200 within the owner-amended ≤2s bounded-background-compute ceiling, zero
  non-200/timeouts, 3 consecutive live runs; peak VmPeak stays under `server.memory_cap_mb=8192` with
  margin recorded.
- TC-10/TC-11: J-05's in-app defining case — live backfill of one unsnapshotted historical day (re-verify
  live that the target date still has 0 snapshot rows before running — do not assume 2012-01-04 is still
  clean), `/scanner-runs` renders the stored snapshot, `aggregates_refreshed` lists what actually refreshed;
  restart cold, coverage renders from the persisted payload within budget, no whole-table `daily_prices`
  prefill.
- TC-12: `/research/factor-lab` loaded warm in prod mode — time-to-interactive + on-load API latency
  recorded in `reports/perf-budgets.md`, within budget.
- TC-13/TC-14: the full 8-journey browser/replay lane runs LAST, strictly after all code lands (no
  product-code change follows it — any audit-fix pass that touches product code triggers a mandatory
  re-run); J-04/J-08/J-09 each produce a real executed row (PASS or FAIL, never SKIP/blank) because the
  backend stays continuously available throughout.

## Notes for Downstream Agents

- **Attribution discipline (iter-49 lesson, binding):** confirm the actual crash frame/traceback during
  implementation, not just a log message. The crash frame is `research.py:1051`'s `sorted(obs, ...)` —
  verified above by reading research.py directly, not inferred from the spec text alone.
- **Live-proof discipline (iter-49 lesson, binding):** a bound proven on an idle host with a throwaway DB
  copy is not proven in the product. J-05's TC-10/TC-11 require a live in-app measurement.
- **Sequencing discipline (iter-46 lesson, binding):** the browser/replay lane (TC-13) must be the
  genuinely LAST product-code-adjacent event. Any audit-fix pass touching product code after it voids the
  round and requires a mandatory re-run — this session has violated this rule four consecutive rounds
  (iter-46 through iter-49); do not make it five.
- **QA report discipline (iter-46 lesson, binding):** if any fix-mode/audit-fix pass changes product code
  after the browser lane has run, the QA report must be regenerated from that re-run, never hand-edited to
  reconcile a stale PASS against a browser FAIL (iter-49 shipped exactly that contradiction).
- This spec bundles three sub-fixes under ONE "risky change" per the spec's own logged assumption (the
  evaluator's own words call the Factor Lab bound + warm guard "ONE job"; the `phase_context_by_date` skip
  is a small companion fix inside the SAME subsystem iter-49 itself just modified). Flagged, not disputed —
  consistent with `docs/goal.md`'s "Suggested build order" being advisory ("the decomposer may re-order
  with reasons") and this session's own precedent (iter-49 bundled comparable-sized sub-fixes).
- This plan advances `docs/goal.md`'s J-05, J-06, J-07 (target journeys) and does not touch the Data
  Contract, navigation, or any canonical value — consistent with the "Improvement direction" section's
  compute-at-ingest/serve-from-storage principle (the warm-in-progress guard is control-flow, not a new
  served value) and introduces no scope beyond the phase spec. No drift from `docs/goal.md` detected.
