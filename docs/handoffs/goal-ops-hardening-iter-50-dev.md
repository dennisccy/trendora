# goal-ops-hardening-iter-50 Dev Handoff

**Phase:** goal-ops-hardening-iter-50
**Date:** 2026-08-05
**Agent:** developer
**Status:** complete (code + unit/integration tests + one live drill against the real committed DB; several DEFINITION OF DONE items are explicitly owned by browser-qa-agent/QA per the phase spec — see Known Issues)

## What Was Built

- **`compute_factor_lab_all`'s per-(factor,horizon) obs-build + sort is bounded and isolated (J-07, the
  confirmed iter-49 crash frame).** `apps/backend/app/engine/research.py:1051`'s `sorted(obs, ...)` — the
  exact site iter-49's own traceback named as the uncaught `MemoryError` that killed the backend for
  12m45s — is fixed two ways:
  1. **Bound:** the per-(factor,horizon) observation list now holds `_FactorLabAllObs` (`__slots__`)
     instances instead of 4/5-key dicts — roughly a third of the per-item memory footprint, no hash table,
     just slot pointers — while still answering `o["key"]` / `o.get("key")` exactly the way the SHARED
     `_deciles` builder (untouched, still used by `compute_factor_lab` / `_regime_effectiveness` / the
     Regime & Phase-Severity labs) expects. `_all_factor_observations_by_horizon` (the shared, already-
     bounded/streamed pool read, iter-31/iter-52) is untouched, per the spec's explicit carve-out.
  2. **Isolate:** a `MemoryError` raised inside that per-(factor,horizon) block is now caught — mirroring
     `evidence.py`'s per-claim isolate-and-continue convention (NOT the ingest warm loops'
     break-on-MemoryError convention, which is for a background loop that can defer; this is a live
     request that must still answer). THAT one `(factor, horizon)` entry degrades to an honest
     `status: "unavailable"` (`deciles: []`, `n_total: 0`); every OTHER entry still renders normally —
     never a blanked whole-response. `factor_lab_all_cached` (the request-path cache wrapper) gains a
     SECOND, outer catch for a `MemoryError` raised anywhere else in the call chain (the shared pool
     builder, `_deciles`'s own aggregation), degrading the WHOLE response to
     `{"factors_table": [], "factors_status": "unavailable"}` instead of propagating to FastAPI. **Neither
     degrade path is ever persisted to the `EventStudyCache`** — a payload with any degraded entry is
     detected and skipped before the cache write, so a later request under the same dataset-version stamp
     gets a fresh attempt once the memory pressure has actually cleared, rather than being served a stale
     degraded payload until the next ingest.
  3. Both catches use a new test-only fault-injection site (`"factor_lab_all"`, added to
     `data_manager._FAULT_INJECT_SITES`) reached via a lazy `from app.engine import data_manager` import
     inside `compute_factor_lab_all` (research.py sits below data_manager in the import graph — a
     module-level import back would be circular).
- **Shared warm-in-progress guard (J-07, the SECOND proven-concurrent crash contributor).** A new
  module-level lock + flag in `data_manager.py` (`_DRAWDOWN_WARM_LOCK` / `_DRAWDOWN_WARM_IN_PROGRESS`,
  `_try_acquire_drawdown_warm(caller)` / `_release_drawdown_warm()`) ensures the boot/re-warm path
  (`warmup._warm_drawdown_expectations`) and the ingest finalize tail's own drawdown-expectations warm
  phase (inside `data_manager._refresh_ingest_aggregates`) never run their heavy per-claim loops
  concurrently in the same process. Whichever tries to start SECOND finds the slot held and defers
  entirely (zero claims attempted, one log line naming which caller deferred and why) — non-fatal either
  way: the boot re-warm retries on the next boot/restart, the ingest finalize tail retries on the next
  ingest job. Mirrors the existing `_COVERAGE_LOCK` single-flight SHAPE but a different policy (defer, not
  wait-and-share). Verified in BOTH trigger orders (TC-4 boot-first, TC-5 ingest-first).
- **`phase_context_by_date` skipped when nothing needs it (J-05, small same-subsystem companion fix).**
  `_refresh_ingest_aggregates`'s `drawdown_expectations_warm` phase used to call
  `market_phase.phase_context_by_date(session, as_of=None, config=cfg)` unconditionally before the
  per-claim loop, even when every ledger claim was already a cache HIT for the current dataset version —
  measured live at ~23.6-23.9s (`reports/perf-budgets.md` Item R Addendum 6, the MID health-poll-stall
  cluster). A new `_drawdown_expectations_ledger_needs_recompute(session, ledger_entries, cfg)` helper
  mirrors the SAME `(subject, view, asof_key, dataset_version, horizon)` cache-HIT check
  `compute_drawdown_expectations_cached` itself performs (one indexed row lookup per claim, no compute);
  when it reports nothing needs it, the precompute is skipped entirely (not invoked) and the per-claim loop
  proceeds unconditionally as before (a HIT claim's own cached-read cost is unaffected by `phases`). The
  `phases` parameter's existing per-claim fallback semantics are untouched — byte-identical when a claim
  does need it.

## Files Changed

- `apps/backend/app/engine/research.py` — `_FactorLabAllObs` (`__slots__` obs stand-in); the bounded +
  isolated per-(factor,horizon) loop inside `compute_factor_lab_all`; the outer `MemoryError` catch +
  "never cache a degraded payload" guard inside `factor_lab_all_cached`.
- `apps/backend/app/engine/data_manager.py` — `EventStudyCache` added to the model imports; `"factor_lab_all"`
  added to `_FAULT_INJECT_SITES`; new `_DRAWDOWN_WARM_LOCK`/`_DRAWDOWN_WARM_IN_PROGRESS`/
  `_try_acquire_drawdown_warm`/`_release_drawdown_warm`/`_drawdown_expectations_ledger_needs_recompute`;
  `_refresh_ingest_aggregates`'s `drawdown_expectations_warm` phase now acquires/releases the guard around
  its own heavy-loop window and gates the `phase_context_by_date` precompute on the new needs-recompute
  check. No other phase in `_refresh_ingest_aggregates` changed.
- `apps/backend/app/engine/warmup.py` — `_warm_drawdown_expectations` acquires the SAME guard before its
  ledger read / per-claim loop and releases it on every exit path (ledger-read failure, normal completion,
  or any caught exception).
- `apps/backend/tests/test_research_streaming.py` — TC-3 byte-identity test against a pinned pre-iter-50
  reference oracle (`_compute_factor_lab_all_pinned_pre_iter50`, a literal copy of the old dict-based obs
  build); a fast/deterministic fault-injection isolation test (control + armed legs); an outer-catch test
  (fault outside the per-entry loop); a "never cache a degraded payload" test.
- `apps/backend/tests/test_data_manager.py` — TC-4/TC-5 guard tests (both trigger orders, with recovery
  after release); TC-6 tests (a real two-call finalize-tail proving the skip, plus a direct unit test of
  the needs-recompute helper).
- `apps/backend/tests/test_start_backend_script.py` — TC-2's live leg: a new `spawned_backend_fault_injected`
  fixture (launches the real `scripts/start-backend.sh` with `TRENDORA_FAULT_INJECT_MEMORY_ERROR=factor_lab_all`
  set) and `test_factor_lab_all_survives_repeated_memory_pressure_live`, hitting
  `GET /api/research/factor-lab?all=true` 5 consecutive times against the real committed DB and asserting
  `GET /api/health` stays 200 throughout. Opt-in (`TRENDORA_RUN_HEAVY_INGEST_TEST=1`), matching this
  module's existing heavy-test gating.

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest <paths> -q` (via `.venv/bin/python`, per the
existing established venv path — `.claude/project-template.md` itself is the unfilled generic template in
this checkout, so the actual commands were inferred from this suite's own existing fixtures/paths, all of
which already assume `apps/backend/.venv`).

- `tests/test_research_streaming.py` — **78 passed** (includes 6 new tests for this iteration).
- `tests/test_data_manager.py` — **183 passed** (full module; includes 4 new tests for this iteration).
- `tests/test_ingest_finalize_fault_injection.py` — **5 passed** (unchanged; confirms the new
  `_FAULT_INJECT_SITES` entry did not disturb the existing site-membership tests).
- `tests/test_warmup.py -k drawdown` — **3 passed** (the three drawdown-related tests in that module).
- `tests/test_start_backend_script.py --collect-only` — 15 tests collected, 0 errors (confirms the new
  fixture/test parse and collect cleanly).
- `tests/test_start_backend_script.py -k test_factor_lab_all_survives_repeated_memory_pressure_live`
  (`TRENDORA_RUN_HEAVY_INGEST_TEST=1`, real spawned backend via `scripts/start-backend.sh`, real committed
  ~7.8 GB DB, the deterministic fault armed on every call) — **1 passed in 1130.35s (0:18:50)**. 5
  consecutive `GET /api/research/factor-lab?all=true` calls, ~3m46s average each (consistent with the
  documented ~2-4 min cold-MISS range) — every response HTTP 200 with every entry honestly marked
  `status: "unavailable"`, `GET /api/health` answered 200 after every one of the 5 attempts, and the
  spawned process was torn down cleanly (no crash, no leaked process). Full detail:
  `reports/perf-budgets.md` Item R Addendum 7.
- Combined re-run for final regression confidence — `tests/test_data_manager.py` +
  `tests/test_research_streaming.py` + `tests/test_ingest_finalize_fault_injection.py` together —
  **266 passed in 374.41s**.

`git diff --stat` over `config.yaml`, `project-extensions/host-guard/host-guard.env`,
`scripts/start-backend.sh`, `scripts/dev.sh` — **empty**, confirming the frozen launch-script files are
byte-identical before and after this pass (TC-10/AG-10).

## Pre-handoff service verification

`scripts/start-backend.sh` launched detached on port 8255 (`CHAIN_BACKEND_PORT=8255`), confirmed
`GET /api/health` returns HTTP 200 (`readiness: "initializing"`, `warmup: {"done": 89, "total": 89,
"status": "running"}`, `preflight.verdict: "DEGRADED"` — the DEGRADED verdict is a **pre-existing,
unrelated** live-vs-seed adjustment-seam drift finding on ~590 symbols, not caused by this iteration's
diff). **Left running** for the downstream review/QA/browser-qa lanes, per this session's own binding
"leave the backend up" lesson from the last several rounds.

## Known Issues

- **The full 8-journey browser/replay lane, the concurrent TC-1 drill (ingest finalize-tail warm running
  WHILE a live `/research/factor-lab` view happens), TC-7/TC-8/TC-9 (full-horizon forward-aggregate warm's
  health-poll cadence + VmPeak margin under the 8192 MB cap + an induced-pressure abort test), TC-10/TC-11
  (J-05's in-app defining case — a live `/data` backfill of one unsnapshotted historical day), and TC-12
  (`/research/factor-lab`'s time-to-interactive + on-load API latency) have NOT been run this pass.** These
  are explicitly named in the phase spec's own DEFINITION OF DONE as browser-qa-agent's / the browser-
  replay lane's responsibility, not this development pass's — and per the binding "browser lane must be
  the genuinely LAST product-code-adjacent event" lesson (violated four consecutive rounds, iter-46
  through iter-49), no further product-code change should land between this handoff and that lane's run.
  What WAS proven this pass, and stands as strong (though not identical) evidence for the SAME crash frame:
  the live TC-2 drill above proves the exact confirmed crash site survives 5 consecutive real HTTP
  requests against the real DB without taking the process down, and the deterministic in-process tests
  (TC-4/TC-5) prove the warm-in-progress guard holds in both trigger orders. TC-1's specific "concurrent
  with an ingest finalize-tail warm" condition was not reproduced live — only the Factor Lab crash frame in
  isolation.
- **TC-6's live numeric before/after (does the `phase_context_by_date` skip actually close the ~23.6-23.9s
  MID health-poll-stall cluster in a real ingest) was not re-measured live this pass.** The MECHANISM is
  proven correct by a real two-call `_refresh_ingest_aggregates` run against a real DB (the precompute is
  invoked exactly once on a genuine cache MISS, zero times once every claim is a HIT) — see
  `reports/perf-budgets.md` Addendum 7 and `tests/test_data_manager.py`'s new TC-6 tests. Closing the loop
  with a live ingest + health-poll re-drill (comparable to Addendum 6's own methodology) is left to the
  browser/QA lane.
- **`tests/test_warmup.py`'s full module was NOT re-run this pass** (it takes over an hour end-to-end per
  Addendum 4/T3's own measurement, and re-running the FULL suite was explicitly out of scope for this
  dispatch). The three drawdown-related tests in that module (`-k drawdown`) were confirmed passing before
  this session's coordinator correction (`3 passed in 241.00s`), and `warmup.py`'s only change this
  iteration (the guard acquire/release around `_warm_drawdown_expectations`) is directly covered by
  `test_data_manager.py`'s new TC-4 test, which exercises the REAL `warmup._warm_drawdown_expectations`
  function end-to-end against a real DB fixture.
- **No frontend work this iteration** (`Frontend Present: no` per the phase spec) — no companion frontend
  handoff was written, matching the developer dispatch instructions.
- The pre-existing `preflight.verdict: "DEGRADED"` (live-vs-seed adjustment-seam drift across ~590
  symbols) observed on the port-8255 backend left running for downstream lanes is unrelated to this
  iteration's diff — it is a data-freshness finding on the committed seed vs. a live reference, not a code
  defect this iteration introduced or is scoped to fix.

---

# Fix Notes — audit-fix pass (2026-08-06)

**Trigger:** `docs/handoffs/goal-ops-hardening-iter-50-audit.md`, verdict **FAIL**.
**Mode:** fix mode. Only the audit's listed findings were touched.

## What the audit found, and what this pass did about each

| # | Audit finding | Status after this pass |
|---|---|---|
| **B1** | CRITICAL — the phase GOAL was not achieved: the exact TC-1 scenario reproduced a 12–15 min total service outage | **Addressed** via B2+B3+B4 below and re-measured live: the outage class did not reproduce (see "Live verification") |
| **B2** | The warm-in-progress interlock guards only the drawdown pair; the phase that actually overlapped (`forward_aggregates_warm`) is unguarded | **Fixed** — interlock widened to the whole ingest finalize tail |
| **B3** | The "bound" was a ~3× constant-factor shrink of a transient; the real peak (and all five live `MemoryError` tracebacks) is `_all_factor_observations_by_horizon`'s resident pool build | **Fixed** — columnar accumulators at that exact site |
| **B4** | "Never cache a degraded payload" removed the only termination condition; compounded by a single-flight ceiling that sat inside the real compute duration | **Fixed** — per-key memory-pressure cooldown + re-tuned single-flight ceiling |
| **B5** | A deferred ingest warm can be lost for a dataset version when the slot-holder then aborts | **Improved, not closed** — see Known Issues |
| **B6** | OBSERVATION — the AG-8 disclosure net never fires before the crash it pre-announces | **Not fixed** — the audit itself scopes it out (pre-existing, iter-31); see Known Issues |
| **T1** | The QA report's PASS is stale and contradicts the browser lane | **Not hand-edited, deliberately** — the spec's remedy is regeneration from a re-run, which this pass now mandates (TC-13) |
| **T2** | DoD item 4 unmet — J-04 has no executed row; J-05's in-app half unverified | **Lane work** — covered by the mandatory re-run |
| **T3** | The TC-2 drill polls health only AFTER each request, so it cannot see the failure that occurred | **Fixed** — health is now polled on a background thread FOR THE DURATION of each request |
| **T5** | The rotated J-05 golden is self-declared infeasible and asserts on page-wide text | **Not fixed** — see Known Issues (out of this pass's product-code scope, flagged for the lane) |

## Scope note the reviewer must read first

The audit's §4 declined to apply fixes because they were "out of surgical reach" **for an audit pass** —
its own reasoning is that an auditor is licensed only for surgical edits, and that touching product code
after the browser lane voids the round (TC-13). This is a **developer fix-mode pass**, which is exactly
the agent licensed to make these changes, and TC-13's consequence is accepted explicitly: **product code
changed, so the full 8-journey browser/replay lane MUST be re-run before this iteration is scored, and the
QA report MUST be regenerated from that run** (never hand-edited — the iter-46 lesson the spec binds).

One deliberate scope lift, called out because it contradicts the phase spec's own text: the spec's IN SCOPE
bullet 1 says *"Do NOT touch `_all_factor_observations_by_horizon` … (already bounded, unaffected by this
defect)"*. The audit's B3 lifts that carve-out on live evidence — five real, un-injected `MemoryError`s,
all with the identical traceback ending at `research.py:966` inside that function, none at the frame the
spec named — and its Recommended Next Step item 1 is explicit: *"Lift the spec's 'already bounded'
carve-out first — it is factually wrong at the current data scale."* This pass follows the audit.
`_all_fr_slice_map`, `_combination_observations`, `compute_drawdown_expectations`'s retention bound and
`samples.py`'s slices were NOT touched (the "Do not redo" list holds).

## Changes

### 1. B3 (critical) — columnar accumulators at the real allocation site

`apps/backend/app/engine/research.py`

- New `_FactorCoreRecords` and `_FactorObsPool` (struct-of-arrays): fixed-width `array`/`bytearray` buffers
  replacing `list[tuple]`, with 1-byte presence masks carrying `None` exactly (never a 0.0 or NaN
  sentinel). A pool row costs 8+8+1+8+1 = 26 raw bytes against ~128 as a boxed 3-tuple.
- Both implement the sequence protocol (`__len__`/`__getitem__`/`__iter__`/`__bool__`), materialising the
  historical tuple shape on demand — so every existing caller, oracle and test that walks the returned
  structure is unchanged. `compute_factor_lab_all`'s hot loop reads the columns directly, so the hot path
  never pays that materialisation and no longer builds a transient object per pool row.
- **Byte-identity (AG-3) is preserved by construction**: same rows, same order, same values. The columns
  are IEEE-754 doubles, which is what a Python `float` already is. Proven by the pinned pre-iter-50 oracle
  (`test_research_streaming.py`), the pinned pre-iter-31 unchunked oracle
  (`test_shared_pools_chunked_equal_the_pinned_unchunked_reference`), and the chunk-independence proof —
  all unchanged in substance and all passing.

### 2. B4 — a termination condition for the degrade path

`apps/backend/app/engine/research.py`

- `_FACTOR_LAB_ALL_MEASURED_COLD_MISS_S` re-based **300 → 875** (the worst observed live cold compute,
  Addendum 8), so the single-flight wait ceiling moves **900s → 2625s**. The old ceiling sat *inside* the
  real 780–875s compute band, which is why five waiters timed out mid-compute in 2m16s during the outage
  and each started an additional independent multi-GB compute.
- New per-key, in-process memory-pressure **cooldown** (`_degraded_cooldown_get/_set/_clear`): once a
  compute degrades, that key's honest degraded payload is served directly for one cooldown window instead
  of launching another doomed compute. Never persisted to `EventStudyCache` (the audit's "never cache a
  degraded payload" rule is untouched); per key, so a different as-of or a dataset change is never masked;
  cleared immediately by the first clean compute, so recovery never waits out a stale window.

### 3. B2 — the interlock widened to the phase that actually overlapped

`apps/backend/app/engine/data_manager.py`, `apps/backend/app/engine/warmup.py`

- New `_enter_/_exit_/_ingest_heavy_warm_active()` (a depth counter on the SAME `_DRAWDOWN_WARM_LOCK`)
  declaring an ingest heavy-warm window across the **whole** `_refresh_ingest_aggregates` tail — including
  `coverage_membership_timeline_refresh` (82.04s live) and `forward_aggregates_warm` (337–385s live), the
  phase that was actually running during the outage while the narrow guard fired and did not help.
- Deliberately **asymmetric**: the finalize tail is the priority producer (its warms *are* the J-05
  contract — deferring them would push the cost onto a live request) and never defers; the boot re-warm,
  already "non-fatal, retried next boot", yields — at entry **and before every claim**, because one claim
  can run for minutes and a start-only check would leave the rest of the loop inside the overlap.
- The original narrow drawdown slot and its TC-4/TC-5 both-trigger-order semantics are unchanged.

### 4. T3 — the drill's blind spot

`apps/backend/tests/test_start_backend_script.py` — `test_factor_lab_all_survives_repeated_memory_
pressure_live` now runs a background `_HealthPoller` FOR THE DURATION of each Factor Lab request and
asserts every poll (200 within the owner-amended ≤2s ceiling), instead of one check after the request had
already returned. It also keys each run to a **distinct real as-of** read from the instance's own
`GET /api/runs`, so the 3 consecutive runs are genuinely independent full-scale computes rather than
repeats the new cooldown would (correctly) short-circuit — and then asserts the cooldown explicitly on a
repeat of an already-degraded key.

## Files Changed (this pass)

- `apps/backend/app/engine/research.py` — columnar accumulators + hot-loop rewrite (B3); cooldown registry
  and helpers, re-tuned single-flight ceiling, cooldown wired into `factor_lab_all_cached` (B4).
- `apps/backend/app/engine/data_manager.py` — ingest heavy-warm window enter/exit/active (B2).
- `apps/backend/app/engine/warmup.py` — boot re-warm yields to the window at entry and per claim (B2).
- `apps/backend/tests/test_factor_lab_all.py` — `_deep_size` descends into `__slots__` (without it the
  existing projection assertion would pass vacuously against the new structures); 2 new tests pinning the
  columnar encoding structurally and by measured cost, and pinning exact NULL round-tripping.
- `apps/backend/tests/test_research_streaming.py` — 3 new cooldown/ceiling tests + an autouse registry
  reset; 2 existing degrade tests updated to expire the cooldown explicitly so they keep measuring the
  cache (their subject) rather than the cooldown; `_materialize_shared_pools` so the chunk-independence
  proof compares DATA, not object `repr()`s.
- `apps/backend/tests/test_data_manager.py` — 4 new tests for the widened interlock (defers for the whole
  window with the narrow slot deliberately free; yields mid-loop; the window spans
  `forward_aggregates_warm` and the coverage/membership refresh; the window unwinds to zero even when a
  phase raises) + an autouse depth reset.
- `reports/perf-budgets.md` — Addendum 9 (append-only).

## Tests Run (this pass)

Command: `cd apps/backend && .venv/bin/python -m pytest <paths> -q -p no:randomly`

| Suite | Result |
|---|---|
| `tests/test_research_streaming.py` | **81 passed** (incl. 3 new B4 tests; both pinned byte-identity oracles green) |
| `tests/test_factor_lab_all.py` | **28 passed** (incl. 2 new B3 tests) |
| `tests/test_research.py` | **93 passed** |
| `tests/test_data_manager.py` | **187 passed** (full module, incl. 4 new B2 tests) |
| `tests/test_ingest_finalize_fault_injection.py` | **5 passed** |
| `tests/test_warmup.py` (8 targeted: every drawdown/evidence-warm/readiness test my change touches) | **8 passed** in 859.53s |
| `tests/test_start_backend_script.py --collect-only` | 15 collected, 0 errors |

One pre-existing failure, **proven not mine**:
`tests/test_warmup.py::test_warmup_loads_each_symbol_at_most_once_across_cadence_and_forward_returns`
fails identically (`^VIX: 8, SPY: 7`) with this pass's changes **stashed**, i.e. at `HEAD` — before
iter-50's own dev pass and before this one. Recorded in Known Issues, not fixed (out of scope).

## Live verification (the proof that matters)

Backend restarted via `scripts/start-backend.sh` on port 8255 — host-guard cap confirmed live from
`/proc/2163532/limits` (`Max address space 8589934592` = 8192 MB). Boot warm-up settled
(`readiness: ready`, `warmup 89/89 ok`). Then `GET /api/research/factor-lab?all=true` (all-history — a
guaranteed cache MISS at the current stamp) over real HTTP, with `GET /api/health` polled once per second
on a background thread **for the duration** and `/proc/<pid>/status` sampled once per second. Raw samples:
`reports/qa/goal-ops-hardening-iter-50-evidence/iter50-auditfix-live-factorlab-measurement.json`.

| | Addendum 8 (pre-fix) | Addendum 9 (this pass) |
|---|---|---|
| Wall clock | 780.2s / 874.7s | **578.87s** |
| Payload | `factors_status: unavailable`, 5/5 attempts | **200, 11 real factors, 0 of 55 entries degraded** |
| Cached afterwards? | No (degraded is never cached → every viewer recomputes) | **Yes — repeat served in 43ms** |
| `/api/health` during | connection-level non-response, 12–15 min | **249/249 HTTP 200; 0 non-200, 0 timeouts** |
| Health latency | n/a | median 0.327s, p90 4.028s, max 5.807s |
| VmPeak | (wedged) | **3,133 MB** — 5,059 MB (62%) margin under the 8192 MB cap |
| VmRSS during | 7.76 → 5.89 GB | **1,196 → 1,703 MB** |

**TC-1 both clauses met live.** **TC-8 margin recorded.** The 12–15 minute outage class did not reproduce.

## Known Issues (honest)

- **The ≤2s bounded-background-compute health ceiling is still breached: 62 of 249 polls between 2.0s and
  5.807s during the compute.** Every one answered HTTP 200 — this is latency, not unavailability, and not
  the outage/wedge class this pass targeted. Cause is GIL contention (tight CPU-bound Python in the
  per-(factor,horizon) sort/decile loops starving the event loop), which bounding memory cannot address.
  **Do not score J-07 step 2 / TC-7 as met on this measurement.** The honest next moves are the audit's own
  next-step (1): take the request-path compute off the event loop, or serve this endpoint from an
  ingest-time artifact per `docs/goal.md`'s compute-at-ingest principle.
- **The cooldown's recovery bound is one window (875s).** Under sustained pressure this caps the doomed-
  compute duty cycle at roughly one attempt per attempt-duration instead of one per viewer; the cost is
  that after pressure clears, a key can serve its honest `unavailable` for up to one window before the
  next viewer retries (immediately shorter if any clean compute lands first, which clears it). A smarter
  backoff (or a pressure-cleared signal) is future work, deliberately not invented here.
- **B5 is improved but not closed.** The widened window makes "both sides skip for a dataset version"
  less likely (the boot re-warm now yields to ingest rather than racing it for the slot), but a boot
  re-warm that yields mid-loop still leaves its remaining claims cold until the next boot. `aggregates_
  refreshed` remains honest about it. The spec sanctions defer-and-retry; unchanged in kind.
- **B6 not fixed** (`research.factor_pool_max_observations: 2000000` never fires before the crash it
  pre-announces). Pre-existing since iter-31, explicitly scoped out by the audit itself; it wants
  re-tuning alongside B3's new footprint, which is a config change and `config.yaml` is a frozen file
  this pass must not touch.
- **T5 not fixed** — `journey-scripts/J-05.json`'s rotated golden still waits 15,000ms against a ~189s
  live sub-stage and still asserts partly on page-wide text. Reshaping it is lane/artifact work, not
  product code, and doing it here would not have been verifiable this round. Flagged for the mandatory
  re-run.
- **T1/T2 are deliberately untouched artifacts.** The stale QA `PASS`, `status.json`'s
  `browser_checks_run: false`, J-04's missing executed row and J-05's unverified in-app `/scanner-runs`
  half are all closed by regeneration from the mandatory re-run — hand-editing them is exactly what the
  spec's NOTES forbid.
- **`tests/test_forward_testing.py` and the remaining ~8 slow `tests/test_warmup.py` tests were not run to
  completion** (individual tests there run 20+ minutes on the 30-year basis; the full suite is ~10h and
  the dispatch forbids running it). Neither module's subject code was changed by this pass; the 8 warmup
  tests that exercise the changed function all passed.
- **No frontend work** (`Frontend Present: no`).
- The backend was left **running on port 8255 with this pass's code loaded**, health 200, as the
  coordinator requires for the downstream lanes.

---

# Fix Notes — audit-fix pass 2 (2026-08-06)

**Trigger:** `docs/handoffs/goal-ops-hardening-iter-50-audit.md`, verdict **FAIL** (second audit pass).
**Mode:** fix mode. Only the audit's own listed findings were touched.

## Correction of record, first

The previous pass's handoff (above) says **"TC-1 both clauses met live."** That claim is **withdrawn**. The
audit's B1 is right: the measurement it rested on had **no ingest job running**, and TC-1's given-clause is
*"with an ingest job's finalize-tail warm running"*. `reports/perf-budgets.md` Addendum 9 now carries an
additive, dated CORRECTION block saying the same thing (its measured numbers stand — they are a valid
record of a *solo* Factor Lab request, just not of TC-1). The scenario has since been executed **as
written**; see "The TC-1 drill" below and `reports/perf-budgets.md` **Addendum 10**.

## What this pass did about each audit finding

| # | Audit finding | Status after this pass |
|---|---|---|
| **B1** | CRITICAL — the phase GOAL's first clause is unproven; the "TC-1 met live" claim omits TC-1's defining precondition | **Claim withdrawn AND the scenario executed as written.** Real `/data` backfill + a live Factor Lab page load issued *during* its finalize tail + 1 Hz health polling through and 420 s past the tail. Result below. |
| **B2** | IMPORTANT — the wedge's proximate frame (the finalize-tail teardown) was never timed | **Instrumented (log-only).** The frame now reports 0.11 s under this drill's footprint. Mechanism *not supported* at 2.4 GB RSS; explicitly **not** claimed as "the wedge is fixed" (the outage ran at 7.76 GB). |
| **B3** | GAP — the 2,625 s single-flight ceiling trades a proven amplification for an unmeasured thread-hold | **Not changed, by design** — the audit itself scopes it to "the next round's measurement plan, not a claim of closure". The drill had a single caller, so the waiter regime is still unmeasured; said so in Addendum 10. |
| **B4** | GAP — the columnar encoding narrows AG-8 data-shape tolerance; neither handler catches the resulting `TypeError`, so it 500s the whole endpoint | **Fixed, both halves**, with 5 new regression tests that all fail without the fix. |
| **B5** | OBSERVATION — the widened interlock deliberately does not satisfy TC-5 as literally written | No action; already disclosed in code and handoff. Confirmed still disclosed. |
| **T1** | CRITICAL — the QA report asserts a re-run that never happened and returns PASS against a FAIL lane | **Deliberately NOT hand-edited.** The spec's remedy is regeneration from the re-run; hand-correcting the verdict is the prohibited act. This pass changed product code, so the re-run is mandatory either way — recorded as a hard blocker in `status.json`. |
| **T2** | IMPORTANT — DoD item 4 unmet; items 1/2 have no evidence | **Lane work**, closed by that same mandatory re-run. |
| **T3** | IMPORTANT — the J-05 golden is structurally incapable of passing | **Fixed.** Rewritten with a real wait and run-specific assertions; see below. |
| **T4** | OBSERVATION (positive) — the unit evidence is strong | Re-confirmed: 367 passed across the four affected modules. |

## Changes

### 1. B4 — AG-8 data-shape tolerance restored at the columnar append site

`apps/backend/app/engine/research.py`

- `_FactorCoreRecords.append` now coerces each non-`None` factor value with **`float(v)`** before storing
  it into the `array("d")` column — the *same* coercion the pre-columnar consumer applied downstream. A
  component factor's value is `record_json[<block>]["components"][i]["raw"]`, i.e. free-form JSON: a record
  shape writing `"raw": "3.5"` served fine before the columnar rewrite (`float("3.5") → 3.5`) and, after
  it, raised `TypeError: must be real number, not str` out of `_all_factor_observations_by_horizon`. Verified
  empirically in this checkout's venv, not assumed. `3 → 3.0`, `True → 1.0`, `"3.5" → 3.5`, `3.5 → 3.5` —
  every shape the old path served is byte-identical.
- A value that is **not a real number at all** (`"n/a"`, a list, a dict) is now recorded as ABSENT via the
  existing presence mask — the module's own `_extract_factor_value` convention ("an excluded factor-NULL
  observation, never fabricated") — never a fabricated `0.0`, and never an exception out of the shared pool
  builder. Counted and disclosed by one AG-8 WARNING per sweep.
- `_FactorObsPool` is deliberately **left alone**, with the reason in its docstring: its two columns come
  from the *typed* `ForwardReturn.realized_return` / `max_drawdown` Float columns, not from free-form JSON,
  so no data-shape tolerance is available to buy there — and that `append` runs millions of times per sweep
  where `_FactorCoreRecords.append` runs once per core record.
- **Second half:** `compute_factor_lab_all`'s per-`(factor, horizon)` loop carried **only**
  `except MemoryError`, so any other exception from one entry still propagated and 500'd the whole
  `?all=true` response for all 11 factors — which AG-8 forbids ("never a blank application-error page"). It
  now pairs that catch with the broader one `evidence.py`'s per-claim convention already uses (the
  precedent this loop itself cites), degrading **that one entry** to an honest `status: "unavailable"` and
  continuing. Nothing wrong is ever displayed by this path: the degraded entry carries no deciles and no n.

### 2. B2 — the finalize-tail teardown frame instrumented (log-only, zero behavior change)

`apps/backend/app/engine/data_manager.py`

- `_release_process_memory()` logs a **START** line *before* `gc.collect()` (so a process killed or
  restarted mid-teardown still leaves the entry boundary in `logs/backend.log` — the exact 2026-08-05
  situation) and a **DONE** line carrying `gc_collect` / `malloc_trim` / `total` wall clocks.
- `_refresh_ingest_aggregates`'s `finally` additionally logs `J-05 finalize-tail teardown timing` with the
  shared-bar-cache drop time and the total teardown time.
- The function signature is **unchanged on purpose**: several test modules monkeypatch a zero-argument spy
  over it, and ~15 call sites pass nothing. Each line pair is attributed by the caller's own surrounding
  log lines instead of a label argument.

### 3. T3 — the J-05 golden rewritten so it can actually pass

`runs/goal-session-ops-hardening/journey-scripts/J-05.json`

Two things were **verified rather than assumed** before rewriting it:

- **`demo_runner.py`'s 20,000 ms hard cap applies to a step's locator/`expect` timeout, NOT to
  `wait_for {ms}`** — `_do_action` passes that value straight to `page.wait_for_timeout(...)`. Proven with a
  throwaway `J-99` golden carrying `wait_for {ms: 45000}`: the verify run took **47 s** wall and returned
  PASS. The iter-49 conclusion recorded in the phase spec's OUT OF SCOPE ("no wait value can cover an
  11-minute job") generalised the locator cap too far. This reopens the deterministic lane for J-05.
- **Wait sizing 1,140,000 ms (19 min):** the same in-app backfill measured **11 m 16 s** standalone in the
  iter-50 lane and **18 m 18 s** in this pass's own drill while a full Factor Lab compute ran concurrently.

Golden discipline (iter-47/48 lessons): the assertions no longer rest on page-wide text a persisted history
panel could satisfy regardless of outcome. New step 10 asserts **this run's own breakdown counts**
(`1 calendar day · 0 already snapshotted · 0 non-trading` — a re-run over an already-snapshotted day renders
`1 already snapshotted` and FAILS, so the assertion has teeth); new step 12 asserts TC-10's
`aggregates-refreshed` list, never asserted before; step 14 CLICKS the date's own link through to
`/scanner-runs/<run_id>`; new step 15 asserts the stored leaderboard table actually rendered rather than the
"No stored stock rows" empty state. Steps 8–12 deliberately stay in the same page session, because
`stage-timings` / `job-status` belong to the LIVE job panel and a reload drops to the reduced persisted-run
view. The file carries a `_notes` block recording all of the above plus the rotation rule.

**Target date left clean:** `2010-11-08` still has **0 snapshot rows** (verified live after the drill). This
pass's own TC-1 drill deliberately consumed `2010-11-09` instead so as not to burn the golden's target.

## The TC-1 drill (the evidence that was missing)

Backend restarted via `scripts/start-backend.sh` on port 8255 (AG-10; `/proc/<pid>/limits`
`Max address space 8589934592` = 8192 MB confirmed live), boot warm-up allowed to settle first
(`readiness: ready`, `warmup 89/89 ok`) so the boot re-warm is not a third actor. Then: a **real
`POST /api/data/jobs` backfill** of `2010-11-09`; the **Factor Lab page load fired 12.5 s in, while the
finalize tail was already running**; `GET /api/health` polled once per second for the whole **1,522 s**,
**through the overlap and 420 s past the job's completion** (the audit's explicit instruction — the
2026-08-05 silence began at the `finally` boundary *after* the last phase finished).

| | Result |
|---|---|
| Overlap achieved | Factor Lab t=12.5 s → 754.6 s; ingest tail t≈12 s → 1,100.0 s — full containment |
| `compute_factor_lab_all` | **HTTP 200**, 11 factors, 55 entries, **0 degraded**, 13,883,204 observations, no `factors_status` |
| Uncaught `MemoryError` | **None** — zero `MemoryError`/`Traceback`/ERROR/WARNING lines in the whole run |
| `GET /api/health` immediately after | **200 in 0.095 s** |
| Health over 1,522 s | **1,179 polls, 1,179 HTTP 200**; zero non-200, zero timeouts, zero connection-level non-responses; longest gap between polls 10.06 s |
| Health after the tail ended (421 polls) | all 200, **max 0.133 s, zero over 2 s** |
| VmPeak | **3,129 MB** vs the 8192 MB cap → **5,063 MB (61.8 %) margin** |
| Persisted run record | `ok`, 1 snapshot / 1 date / 1 calendar day / 0 already-snapshotted / 0 non-trading, `aggregates_refreshed` = 7 categories, "1370 forward returns" |
| Teardown frame (B2) | `gc_collect=0.06s malloc_trim=0.05s total=0.11s`, `shared_bar_cache_drop=0.00s` |

Raw samples: `reports/qa/goal-ops-hardening-iter-50-evidence/iter50-auditfix2-tc1-live-drill.json`
(every poll, every memory sample, every event). Full write-up: `reports/perf-budgets.md` **Addendum 10**.

**TC-1's both clauses are met with the given-clause established** — the first time this iteration.
**TC-8 recorded.** **TC-9 — no wedge, no deadlock, no restart requirement** across 1,522 s.

## Tests Run (this pass)

Command: `cd apps/backend && .venv/bin/python -m pytest <paths> -q -p no:randomly`

| Suite | Result |
|---|---|
| `tests/test_factor_lab_all.py` | **33 passed** (28 pre-existing + **5 new B4 tests**) |
| `tests/test_data_manager.py` + `tests/test_research_streaming.py` + `tests/test_ingest_finalize_fault_injection.py` + `tests/test_research.py` | **367 passed in 390.79 s** (includes the new B2 instrumentation test) |

**Teeth check on the new tests** (not just "they pass"): with the B4 changes reverted in a scratch copy of
`research.py`, all 5 new tests FAIL — three with the exact `TypeError: must be real number, not str` /
excluded-value assertions, and the isolation test with the injected `RuntimeError` propagating straight out
of `compute_factor_lab_all`, which is the 500 this fix exists to prevent. The file was restored from the
backup immediately afterwards and `git diff --stat` re-checked.

`git diff --stat` over `config.yaml`, `project-extensions/host-guard/host-guard.env`,
`scripts/start-backend.sh`, `scripts/dev.sh` — **EMPTY** (AG-10 / TC-10 frozen files unchanged).

## Known Issues (honest)

- **TC-13 / DoD item 7 — this pass changed product code, so the FULL 8-journey browser/replay lane MUST be
  re-run before closure, and `reports/qa/goal-ops-hardening-iter-50-qa.md` MUST be regenerated from that
  run, never hand-edited.** The lane has still never run against this iteration's current code, so the
  re-run was already mandatory before this pass; nothing here made the sequencing worse, but nothing here
  discharges it either. Audit findings **T1 and T2 are closed by that re-run, not by this pass.**
- **TC-7 / J-07 step 2 is NOT met, and by a wider margin than before.** 96 of 1,179 health polls exceeded
  2.0 s, worst **10.063 s** (the solo run in Addendum 9 peaked at 5.807 s). That is the expected direction:
  this run finally has the concurrency TC-1 asks for, and the extra latency is GIL contention between two
  CPU-bound Python computes in one process. Every poll still answered HTTP 200 — latency, not
  unavailability — and the breach vanishes entirely once the tail ends. **Score J-07 step 2 as failing.**
- **The wedge/outage class is `unproven-either-way`, not fixed.** The 17-minute silence did not reproduce,
  but the outage's own footprint did not either (7.76 GB RSS then vs 2.40 GB peak here), and a
  `gc.collect()`'s cost scales with the heap it walks. What changed is falsifiability: a recurrence will
  now show either a `START` with no `DONE` (the teardown IS the frame) or a small `DONE` before the silence
  (it is not). **Do not take J-07 credit for the wedge.**
- **B3's waiter thread-hold remains unmeasured.** The drill had a single Factor Lab caller, so no waiter
  ever occupied an anyio threadpool worker for the re-based 2,625 s ceiling. Carried, as the audit scoped it.
- **`forward_aggregates_warm` h20 cost 448.09 s against 79–81 s for every other horizon** in this drill —
  the same GIL-contention signature, on the horizon whose window the Factor Lab compute overlapped. It is
  the *cost* of the concurrency, paid without a single non-200. Not a memory effect, not a new defect.
- **The J-05 golden is single-use by construction.** Its target must have 0 snapshot rows when it runs.
  `2010-11-08` is clean now; `2010-11-09` (this drill), `2012-01-04` and `2013-02-14` are consumed. If a
  later lane burns `2010-11-08`, rotate steps 2/3/13/14 to another 0-row trading day and verify live with
  `GET /api/runs` first.
- **Carried unchanged from the previous pass:** B5 (a boot re-warm that yields mid-loop leaves its remaining
  claims cold until the next boot), B6 (`research.factor_pool_max_observations` wants re-tuning against
  B3's new footprint — a `config.yaml` change, and `config.yaml` is frozen), the cooldown's one-window
  recovery bound, and the pre-existing
  `test_warmup.py::test_warmup_loads_each_symbol_at_most_once_across_cadence_and_forward_returns` failure
  (proven not ours: it fails identically at `HEAD` with this iteration's changes stashed).
- **`tests/test_warmup.py` and `tests/test_forward_testing.py` were not re-run to completion this pass**
  (individual tests there run 20+ minutes on the 30-year basis; the full suite is ~10 h and the dispatch
  forbids running it). Neither module's subject code was changed by this pass.
- **No frontend work** (`Frontend Present: no`). No frontend handoff written.
- The backend was left **running on port 8255 with this pass's code loaded**, `GET /api/health` 200
  (0.095 s), `readiness: ready`; the frontend is up on 3255 — as the coordinator requires for the lane.
