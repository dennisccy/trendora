# goal-ops-hardening-iter-70 Audit Report

**Date:** 2026-08-12
**Auditor:** Hard audit pass — skeptical, evidence-based

---

## 1. Executive Verdict

**Verdict:** PASS_WITH_GAPS

The phase goal is achieved and I verified it from the raw evidence, not from the handoff: `GET /api/health`
no longer computes readiness/preflight on the request thread, and across the drill's own 1,030-row poll CSV
there are **0 breaches of the 2.0s ceiling, 0 non-200s, max 1.226s**, with `readiness_s`/`preflight_s`
literally `0.0000s` across all 1,065 in-window watchdog records I recounted myself. The two dominant heavy
phases (`factor_lab_all_warm`, 565 polls; `drawdown_expectations_warm`, 341 polls) are fully covered and
clean — iter-69's 8.09% breach rate is genuinely closed, not rounded toward closed.

Three things were wrong and are now fixed: a re-introduced `logger.exception` escape inside the ingest
finalize hook (a class this repo's own iter-45 review already classified CRITICAL and built a guard for),
two false coverage statements in this round's own perf-budgets addendum, and the drill's raw evidence
living only in an ephemeral scratch directory. Two gaps remain and are **not** fixable inside this audit:
TC-3's browser-QA half and all of TC-9 (the 7-journey regression replay) never executed — the backend died
between lanes — and the QA report nevertheless marks both `✓`, which is not true. The residual risk is
verification coverage, not a known product defect.

---

## 2. Findings

### Backend Findings

**B1 — IMPORTANT (fixed): a tick's own failure-logging can escape the "never raises" contract, discarding
the ingest finalize's result or killing the refresh thread**

`apps/backend/app/engine/readiness.py:561` (and `:545`, `:621`) caught tick failures with a bare
`logger.exception(...)`. `apps/backend/app/engine/data_manager.py:4835` calls
`trigger_readiness_refresh(session, config=cfg)` from inside `_refresh_ingest_aggregates` — the exact
function whose isolation handlers `data_manager._log_isolation_failure` (`data_manager.py:3970`) was built
for in iter-45, after a reviewer classified this class CRITICAL. That helper's own docstring states the
rule this iteration broke: `logger.exception()` renders the full live traceback, which **allocates**; under
the exhausted `ulimit -v` cap that produced the exception being logged, that allocation can raise a second
exception, raised *inside* the `except` clause where the clause's own `try` no longer protects it — so it
propagates. The docstring is explicit that the guard is keyed "to the WHOLE exception set an incident
produces, not its headline exception"; iter-70 added a new unguarded site into that same function.

Two reachable consequences:
- Escape from `trigger_readiness_refresh` → `_refresh_ingest_aggregates` raises → at
  `data_manager.py:5671`, `prog.aggregates_refreshed = _refresh_ingest_aggregates(...)` never assigns, so a
  completed 17-minute finalize reports **zero** aggregates refreshed on `GET /api/data/jobs/{id}` — a J-05
  honesty surface, on a job whose outer handler still reports `ok`.
- Escape inside `_refresh_loop` (`readiness.py:621`) **kills the daemon thread**. Because nothing bounds
  cache staleness (see B2), `GET /api/health` then serves the frozen last-known value indefinitely with no
  error surfaced anywhere — the failure mode is silent and permanent, strictly worse than the pre-iteration
  behaviour it replaced.

It also falsified two claims already written into the tree: `trigger_readiness_refresh`'s docstring
("Non-fatal … this never raises out into the calling ingest job") and `data_manager.py:4830`'s comment
("Non-fatal -- `trigger_readiness_refresh` never raises").

**Fix applied.** Added `_log_tick_failure` (`readiness.py:484`) — full traceback first, minimal-allocation
`logger.error` fallback, silent give-up — mirroring `_log_isolation_failure`'s documented shape, and routed
all three tick-path log sites through it. Two regression tests added
(`test_tick_failure_never_escapes_even_when_its_own_logging_raises`,
`test_refresh_loop_survives_a_tick_whose_logging_raises`). **Verified failing before the guard** (reverted
the two call sites and re-ran: `2 failed`, `PytestUnhandledThreadExceptionWarning` on the loop test) **and
passing after** (`12 passed, 32 deselected in 1.99s` for the whole iter-70 cache-test group). No regression:
`tests/test_health_watchdog.py` re-run after the fix, `16 passed in 118.91s`.

**B2 — GAP (documented): cache staleness is unbounded and unobservable if the tick stops advancing**

`get_readiness_and_preflight` (`readiness.py:567`) returns `_READINESS_CACHE` (`:575`) with no age check and
no `stale_for_s` field. If a tick wedges (a long SQLite lock inside `compute_readiness`) or the thread dies,
the endpoint keeps answering 200 with a plausible-but-frozen `readiness`/`preflight`. Before iter-70 the
endpoint would have been *slow* but never *wrong*; now it can be fast and wrong. The spec chose this design
knowingly (TC-6 mandates "serve last-known-good on tick error"), so this is a limitation, not a defect —
but AG-3's "displayed numbers are correct" has a new silent failure mode. B1's fix removes the most likely
path into it. A future round could bound it cheaply: stamp each payload with a monotonic timestamp and fall
back to a synchronous compute past N × `refresh_interval_seconds`.

**B3 — GAP (documented): the cold-start path re-computes even when a fresh value has just been published**

`get_readiness_and_preflight` reads the cache (`:575`), and on a miss calls `_tick_and_cache` (`:579`), which
blocks on `_TICK_LOCK` and then computes unconditionally — it never re-checks `_READINESS_CACHE` after
acquiring the lock. During the boot window (`start_readiness_refresh` sets the cache to `None`, then the
thread's first tick runs) each arriving request performs its own full redundant compute behind the lock even
though the boot tick has already published. Bounded to the boot window and no worse than the pre-iteration
per-request cost, so it defeats nothing — a two-line double-checked read inside the lock would close it.

**B4 — OBSERVATION: the tick raises steady-state background work well above what any client asks for**

`record_verdict_transition` (`readiness.py:449`) does a full `read_entries()` of the verdict-history JSONL on
**every** tick. Pre-iteration it ran once per `/api/health` request (2s while warming, 30s idle per
`config.yaml startup.health_poll_idle_interval_seconds`, and only when a client polled); it now runs at 2 Hz
for the process's life. I measured the cost: 131 entries / 178 KB → **0.79 ms per call, ≈0.16% of one core
at 2 Hz** — negligible today, and growth is bounded by transition count (the drill added exactly one line).
Not worth changing; recorded so a future round that lets this log grow knows the read is on a 2 Hz timer.

**B5 — OBSERVATION: the preflight fallback in `health.py` fires on an implicit `NameError`**

Confirms the reviewer's MINOR at `apps/backend/app/api/health.py:181`. If line 163 raises, `cached` is never
bound and `cached["preflight"]` raises `NameError`, which the broad `except Exception` at :182 catches. It is
functionally correct and exercised by
`test_health_background_compute_degrades_honestly_when_readiness_fails`. Agreed at MINOR/OBSERVATION —
`cached = None` in the readiness except-block would make it explicit. Not fixed (scope creep).

### Frontend Findings

None. `git status --porcelain -- apps/frontend/` is empty; the response body construction
(`health.py:211-239`) is field-for-field unchanged. Spec scope ("Frontend: None") is met exactly.

### Test Findings

**T1 — GAP (documented): TC-4 is proven in two halves that are never composed**

`test_finalize_hook_triggers_immediate_readiness_refresh` proves the hook *calls* the trigger with the same
session; `test_trigger_readiness_refresh_updates_the_cache_immediately` proves the trigger *writes* the
cache. Neither proves TC-4's actual acceptance sentence — that a real state flip (`awaiting_snapshot` →
`ready`) is *served* by `GET /api/health` within one tick rather than a full period. The decomposition is
reasonable and the composition is simple, but no test would catch a regression in the join.

**T2 — OBSERVATION: `test_health.py`'s new cache tests carry no isolation fixture**

`test_readiness.py` got an autouse `_isolated_readiness_cache` that stops the thread and resets the cache
around every test; `test_health.py`'s two new tests rely on a bare `readiness.reset_readiness_refresh_cache()`
call with no such guard. This is the exact contamination class the developer already hit once mid-implementation
(documented in the handoff and Addendum 36). I traced both failure directions and they fail loud rather than
false-pass — a stale cross-engine value breaks the byte-identity assertion, and a live thread ticking through
the monkeypatched counters breaks `calls == {0, 0}` — so this is fragility, not a masked defect.

**T3 — OBSERVATION: one decorative assertion**

`test_trigger_readiness_refresh_updates_the_cache_immediately` asserts the served state is in the set of all
four legal states — a tautology. The load-bearing assertion in that test (`_READINESS_CACHE` goes from `None`
to non-`None`) is sound.

### Evidence & Verification Findings

**E1 — IMPORTANT (gap, NOT fixable in this audit): TC-3's browser-QA half and all of TC-9 never ran, and the
QA report marks both `✓`**

`reports/phase-goal-ops-hardening-iter-70-regression-replay-results.md` reads **"0/7 journeys passed (0
skipped, 7 blocked — backend unreachable)"**, every row `BLOCKED` with "backend unreachable: GET
http://localhost:8255/api/health did not answer 200". The dev handoff is honest about this: "The browser-qa
lane's own independent J-07 drill (TC-3's 'union of both drills') has not run as part of this developer
pass." But `reports/qa/goal-ops-hardening-iter-70-qa.md:85` records *"TC-9: … remain green (✓ Developer
verified via replay)"* and `:255` repeats *"✓ Developer verified via replay"* — **no such replay exists**
anywhere in the tree, and the dev handoff claims none. Per `.claude/judgment-rubrics.md` §5, "no regressions"
requires a green replay lane plus a journey-deltas table, or an explicit list of what was not re-verified;
per §6 the correct status here is `unknown`, not `✓`. The cause was infrastructure (the backend died between
lanes), not product — but the QA artifact states the opposite of its own upstream evidence, and the evaluator
must not read that `✓` as coverage.

Partially mitigating, and worth weighing: the dev drill did exercise J-05's own ingest path end-to-end
against the built tree — a real 17m20s backfill (job `22057414bbff44e2ab9141d31ae70846`) through
`_refresh_ingest_aggregates` including the new trigger, reaching `status: ok` with all 9 aggregate
categories and a clean teardown (`logs/backend.log`, "finalize-tail teardown timing … total_teardown=0.16s",
"ingest heavy-warm window CLOSED"). I also grepped the full backend log for tick failures
("readiness refresh tick failed" / "loop iteration failed" / "verdict-history write failed"): **0
occurrences** — so the zero-breach result was not achieved by a wedged tick serving a frozen value.
Independent TC-5 confirmation in production: the verdict-history file gained **exactly one** line for the
DEGRADED→GO transition despite hours of ~2 Hz ticking.

**E2 — IMPORTANT (fixed): Addendum 36 mis-stated the drill's coverage and mis-explained the gap**

`reports/perf-budgets.md` claimed *"Poller ran 2026-08-12T13:29:43Z → 13:47:24Z (1,030 polls, a few seconds
either side of the job for margin)"* and footnoted the four zero-poll phase rows as *"not a coverage gap, a
sampling-rate artifact."* Both are false. From the drill CSV itself: the first row is **13:30:15.372420Z**,
**32.1s after** the job's `started_at` 13:29:43.297634Z, and **zero** rows precede 13:30:07.357Z
(`forward_aggregates_warm`'s start). The arithmetic signature is in the table already — 99 polls over a
106.52s window. So `backfill scan stage` (14.70s), `coverage_membership_timeline_refresh` (6.49s),
`per_date_coverage_warm` (2.11s) and `market_phase_warm` (0.76s) were **not measured at all** (at 1 Hz they
would have collected ~15, ~6, ~2 and ~1 polls); the footnote's explanation only holds for `index_series_warm`
(0.02s) and `teardown` (0.16s). Separately, the 22 polls labelled "pre-finalize / boundary gaps" are
**post-completion** polls (13:47:03.101Z → 13:47:24.747Z).

This matters beyond bookkeeping: `coverage_membership_timeline_refresh` is the one heavy phase the spec's own
OUT OF SCOPE clause names alongside `factor_lab_all_warm` as the RELEASED alternative target, and it sits
entirely inside the unmeasured window — so it is **unmeasured this round, not proven clean**. In a session
whose standing discipline is "report the residual honestly rather than rounding toward 'fixed'", and in the
very addendum appended to correct two earlier write-up errors, this had to be corrected rather than noted.

**Fix applied** to Addendum 36's own new text (allowed — it is this iteration's own uncommitted addition):
corrected poller window, corrected `†` footnote with the verification method, corrected row label, each
marked as an audit correction with the original wording preserved inline. TC-8 re-verified after the edit:
`git diff --numstat` = **234 insertions, 0 deletions**, and `git diff -U0 … | grep '^-'` is empty — zero
deletions to any pre-existing line. The 0-of-1,030 headline is untouched and independently reproduced.

**E3 — IMPORTANT (fixed): the drill evidence existed only in an ephemeral scratch directory**

TC-3's entire headline rested on files under the pipeline's `TMPDIR`
(`…/iad.goal-ops-harde-3d58dfd6.27286/iter70-drill/`), which is session-scoped and disposable. Every prior
round preserved its drill under `runs/goal-ops-hardening-iter-<N>/evidence-drill/` (iter-66 … iter-69);
`runs/goal-ops-hardening-iter-70/` had no such directory. **Fix applied:** copied both poll CSVs and their
metas, the job-id/dispatch-time stamps, a 9,867-record in-window `health-watchdog-slice.jsonl`, and the job's
11 phase-timing/teardown log lines into `runs/goal-ops-hardening-iter-70/evidence-drill/`. Re-verified from
the *preserved copies*: `rows=1030 non200=0 breaches>2.0s=0 p50=0.1140 p90=0.3290 p99=0.6180 max=1.2260`;
`handler_compute=1065 readiness_s>0.5ms=0 preflight_s>0.5ms=0`.

---

## 3. Domain Assessment

The core design is sound and, unusually for a caching retrofit, genuinely does not fork the producer. I
traced it rather than trusting the handoff: `compute_readiness`/`compute_preflight` are not touched;
`_compute_tick` (`readiness.py:531`) is the single body behind all three callers (periodic thread, finalize
trigger, cold-start), so there is exactly one code path computing readiness and exactly one endpoint serving
it. The Data Contract row is honoured.

The atomicity claim holds and is not folklore: `_READINESS_CACHE` is only ever rebound to a fully-built fresh
dict, never mutated in place, so a reader gets the whole prior or whole new payload. I checked the two
composed sub-objects that could have poisoned this — `forward_testing.get_background_compute_status()` builds
fresh lists under `_HIST_DISPATCH_LOCK`, and `compute_readiness`'s return (`readiness.py:261-271`) constructs
every nested dict inline — so no live mutable structure is parked in the cache for FastAPI to serialize
mid-mutation. The torn-read test is a real test of the published-payload shape, not a timing coincidence.

Two design judgements deserve to be named. First, the trade this iteration makes is *slow-but-true* for
*fast-but-possibly-stale*; that is the right trade for a liveness badge and the spec chose it explicitly, but
it introduces a silent-wrongness mode that did not exist before (B2), which is precisely why B1's escape path
mattered enough to fix rather than log. Second, `engine` is threaded through `compute_readiness`'s signature
but unused in its body, so the finalize trigger passing `engine=None` is harmless — worth knowing, since the
docstring says otherwise and a future reader could reasonably assume the trigger's payload differs from the
thread's. It does not.

On the numbers: the fix's own instrument agrees with its claim. `readiness_s`/`preflight_s` are not merely
"near-zero" — they are exactly `0.0000s` at every percentile across all 1,065 records, while `db_reads_s`
(untouched code, correctly left on the request path) still shows real load-dependent cost (p90 0.0525s, max
0.4800s). That asymmetry is the signature of the intended change and would be very hard to fake.

---

## 4. Fixes Applied During This Audit

| # | Severity | File | Change |
|---|----------|------|--------|
| 1 | Important | `apps/backend/app/engine/readiness.py` | Added `_log_tick_failure` guard (`:484`) and routed the three tick-path log sites (`:545`, `:561`, `:621`) through it, so a failure-logging allocation that itself raises cannot escape into the ingest finalize hook or kill the refresh thread |
| 2 | Important | `apps/backend/tests/test_readiness.py` | Two regression tests for the above (`test_tick_failure_never_escapes_even_when_its_own_logging_raises`, `test_refresh_loop_survives_a_tick_whose_logging_raises`) — verified failing pre-fix, passing post-fix |
| 3 | Important | `reports/perf-budgets.md` | Corrected Addendum 36's poller window, `†` footnote, and one row label; TC-8 re-verified (234 insertions / 0 deletions, no pre-existing line touched) |
| 4 | Important | `runs/goal-ops-hardening-iter-70/evidence-drill/` | Preserved the drill's poll CSVs + metas, watchdog slice (9,867 records), and phase-timing log lines out of the ephemeral TMPDIR; re-verified the headline from the preserved copies |
| 5 | — | `docs/handoffs/goal-ops-hardening-iter-70-dev.md` | Updated the now-stale "216 insertions" claim and appended an audit addendum naming fixes 1-4 |

**Verification commands and results**
- `pytest tests/test_readiness.py -k "cache or refresh_interval or single_flight or torn or trigger or tick_failure or refresh_loop"` → **12 passed, 32 deselected in 1.99s**
- Same two new tests with the guard reverted → **2 failed** (contract escape reproduced)
- `pytest tests/test_health_watchdog.py` → **16 passed in 118.91s** (post-fix; matches the developer's 16/16)
- `git diff --numstat reports/perf-budgets.md` → `234  0`; `git diff -U0 … | grep '^-'` → empty
- Independent recount of the preserved drill CSV and watchdog slice → matches the addendum's headline

I did **not** run `test_health.py` / `test_data_manager.py`: their `loaded_engine` fixture takes ~1h on this
host and the operating note forbids it. Their results carry from the developer's run (279/280, one
pre-existing order-sensitivity artifact I independently confirmed is unrelated to this diff — it asserts
`data_manager._JOBS == {}` and trips only when `test_health.py`'s `TestClient` blocks run first, which the
default alphabetical order prevents).

---

## 5. Recommended Next Step

**Proceed** — the J-07 step-2 fix is real, measured, and independently reproducible from evidence now
preserved in-repo. Two items must travel forward honestly rather than be treated as closed:

1. **TC-9 is `unknown`, not green** (E1). The 7-journey replay was BLOCKED for infrastructure reasons and the
   QA report's two `✓ Developer verified via replay` claims are unsupported. The evaluator should score
   J-01/J-03/J-04/J-05/J-06/J-08/J-09 on carry-forward durability with the gap stated, or re-run the replay
   now that the backend can be restarted — it is the cheapest way to convert this from `unknown` to green.
   Note the backend on `:8255` is **not** currently listening (I checked: `ss -ltnp` shows no listener,
   `curl` returns connection-refused), so a re-run needs a fresh `scripts/start-backend.sh` boot.
2. **TC-3 is half-satisfied, and `coverage_membership_timeline_refresh` is unmeasured, not clean** (E2). The
   next drill should start the poller *before* dispatching the job so the head of the run is covered. If a
   later round needs the RELEASED bounding alternative, that phase — not `factor_lab_all_warm`, which is now
   demonstrably clean across 565 polls — is the one without evidence.

Nothing here blocks the iteration. The remaining GAPs (B2 staleness bound, B3 double-checked read, T1's
uncomposed TC-4) are all small, well-scoped candidates for a future hardening round and none of them
compromise this one.
