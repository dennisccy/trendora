# Goal Iteration 15 — Root-cause and fix `/backtest`'s concurrent cache-miss latency (UT-04 follow-up)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 15
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-06, J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a
    **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked
    values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha
    claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation
    for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed
    out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of;
    never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the
    post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every
    existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error
    boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded
    whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only
    against the committed seed / local provider fixtures — no live external network calls or
    paid data services may be introduced without an explicit goal.md amendment. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills,
    full-universe rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched
    only via the project launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those
    scripts MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env`
    whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`,
    `malloc_arena_max`). Never remove, weaken, or bypass these caps: stripping a HOST-GUARD
    marked block from a launch script is a REGRESSION regardless of test outcomes. The ceilings
    are a physical constraint of the current host (two instant hardware resets under all-core
    vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance budget to
    optimize away. *(critical)*

## GOAL

`/backtest`'s per-horizon evidence resolves quickly and predictably even while the ingest-time
forward-aggregate warm is running concurrently, closing the 211.8-second concurrent-cache-miss finding
(UT-04) — the sole remaining agent-tractable item standing between J-06/J-07 and `passing`.

## BACKGROUND

iter-14 resolved the critical AG-8 defect (unbounded ORM reads in `compute_forward_aggregates`) with a
column-projected, `yield_per`-streamed rewrite — byte-identity proven, 61.8% VmPeak margin, 250/250
health 200 — but browser-qa's UT-04 (P1) found the SAME rewritten path resolving a `/backtest`
cache-miss in **211.8 seconds** (measured via the browser's own Resource Timing API) when it lands
concurrently with the ingest finalize hook's forward-aggregate warm, against a committed ≤1.5s budget —
honest (no crash, no frozen frame, `/api/health` stayed green throughout) but a ~140× budget overrun.
Both iter-14's evaluator and its auditor named this THE next item (audit F1: "the streamed read... may
contend more with the concurrent warm's writes than the old fast `.all()` fetch-and-release did... a
hypothesis, not a verified claim"); the pump note dispatching this iteration confirms it as "THE
agent-tractable target now." Reading `forward_aggregates_cached` (`forward_testing.py:987`) directly:
there is **no de-duplication today** — a cache MISS always calls `compute_forward_aggregates` directly,
so N concurrent same-key MISSes redundantly recompute the full aggregation. Separately, `uvicorn` runs
this app single-process (no `--workers` flag anywhere in `start-backend.sh`/`dev.sh`/`main.py`), so
concurrent heavy Python aggregation loops share one GIL, and the DB runs `journal_mode=WAL` (confirmed
live) — a long-held streamed-read transaction could plausibly overlap more WAL growth from concurrent
commits than a fast `.all()` did. All three are named candidates for this iteration's root-cause work;
none is prescribed. The tables involved have grown further since iter-14's own measurement (read
directly from `apps/backend/data/trendora.db`, read-only, no service start required):
`scanner_results` 611,689 → **775,094** rows, `forward_returns` 3,098,302 → **3,935,930** rows,
`scanner_runs` → **1,858** — most likely from the operator's post-iter-14 `demo.sh --session-live` run
(see NOTES), so the defect is if anything more pronounced now, not less.

**Depth is full — trigger 1 (structural/cross-cutting):** the fix lives in `forward_aggregates_cached`,
the SAME serving wrapper shared by `GET /api/backtest`, the MCP `query_backtest` tool, and the ingest
finalize warm, and possibly in `app.db`'s session/WAL configuration — genuinely shared infrastructure,
not one journey's private surface. This iteration's own spot-check obligation (below) spans ≥3 further
pages (`/stocks`, `/sectors`, `/scanner-runs`, `/evidence`) whose interaction with this shared layer no
single journey's own tests cover — exactly the kind of cross-agent-boundary risk iter-13/iter-14 both
needed the full pipeline's audit/closure to characterize correctly.

**Target selection (rubric):** rule 3 (unblocker) — this is the ONLY remaining agent-tractable
substantive item; the two other J-06/J-07 gaps are owner/evaluator calls (the `--session-live`
walkthrough now has fresh operator evidence to weigh — see NOTES — and TC-6's induction-sufficiency call
was already made by iter-14's evaluator). Rule 5 (never bundle two risky journeys) is respected: J-06
and J-07 share this ONE risky item (the SAME concurrency defect blocks both), not two separate risky
changes.

**Lessons applied:** iter-14 ("a memory fix and a lock-contention fix are different problems... measure
latency under concurrent load on the deep basis, not just peak memory") — this iteration must not accept
byte-identity/VmPeak proof as a substitute for a fresh concurrent-load timing measurement. iter-11
("cross-read `logs/backend.log`/`hwmon.csv` before accepting an 'ambient' explanation") — applies to
whatever the post-fix measurement shows. iter-9 ("a plausible artifact story must be verified, not
accepted") — applies equally to a plausible "concurrency overhead is expected and acceptable" narrative
if the post-fix number is still elevated: record it, do not rationalize it away.

## IN SCOPE

### Backend
- [ ] Root-cause UT-04's 211.8s finding in `app.engine.forward_testing.forward_aggregates_cached` /
  `compute_forward_aggregates` (`apps/backend/app/engine/forward_testing.py:781-1053`) and, if
  implicated, `app.db`'s SQLite session/WAL/connection handling (`apps/backend/app/db.py`) — determine
  and document, with evidence, which of the three named candidates (redundant same-key recomputation;
  GIL/CPU contention between concurrent heavy Python aggregation loops; WAL growth/contention from a
  long-held streamed-read transaction overlapping concurrent commits) is the dominant cause (may be more
  than one).
- [ ] Implement a targeted fix for the confirmed mechanism(s), scoped to `forward_aggregates_cached` (the
  existing serving/caching wrapper) and/or `app.db`'s session/connection/WAL configuration.
  `compute_forward_aggregates` keeps its exact current signature, columns read, and streamed/`yield_per`
  pattern from iter-14 (binding "Do not redo" — it stays the single canonical producer); all three
  existing call sites (`apps/backend/app/api/backtest.py:72`, `apps/backend/app/mcp/tools.py:205`, the
  ingest finalize warm at `apps/backend/app/engine/data_manager.py:3230`) keep calling it unchanged.
- [ ] Extend `test_forward_testing_aggregates_streaming.py`'s existing byte-identity fixture proof (or add
  a small sibling file, matching this module's existing per-concern-file convention) to prove the fix
  changes no computed value.
- [ ] Add a same-key concurrent-MISS test proving the heavy aggregation body cannot run redundantly for a
  single still-uncached key, regardless of the fix's exact mechanism.
- [ ] Add a concurrent-write-during-read test (sized so a single uncontended `compute_forward_aggregates`
  call measures ≥1.0s wall-clock, with a background thread issuing repeated committed writes throughout
  that call, mirroring ingest-warm write activity) and record the concurrent/baseline wall-clock ratio.
- [ ] One OPERATOR-SUPERVISED, host-guard-confined, full-deep-basis reproduction of the exact iter-14
  UT-04 trigger shape (the forward-aggregate warm across all 5 configured horizons running concurrently
  with a live `GET /api/backtest` cache-miss request, in one long-lived process) — record the resulting
  cache-miss latency in `reports/perf-budgets.md` next to the original 211.8s finding, explicitly marked
  PASS or WARN against the committed ≤1.5s `/backtest` budget.
- [ ] During that SAME pass (not a second heavy pass — AG-10 permits one), spot-check `/stocks`,
  `/sectors`, `/scanner-runs`, `/evidence` page loads under the concurrent warm and record what is
  observed honestly — name any further violation found; do not invent a fix for it unless the same
  root-cause mechanism already covers it.
- [ ] Poll `GET /api/health` at 1Hz throughout that same pass; confirm no wedge (mirrors J-07 step 2).

### Frontend
None — no frontend file is touched (Frontend Present: no). The engine still forces the browser-qa lane
this iteration because Target/Required journeys are named (framework fix, commit `d0799803`, verified) —
see TESTING REQUIREMENTS. The honest-status/graceful-degradation clause is already independently
satisfied (iter-14 confirmed `/backtest` renders fully, never frozen/blank, during the slow cache-miss) —
an elapsed-time affordance is a candidate FOLLOW-UP only if this iteration's fix does not materially
close the gap (see OUT OF SCOPE).

### New user-facing capability
None new. An existing capability (`/backtest`'s per-horizon evidence during/after a concurrent ingest
warm) becomes reliably fast instead of occasionally very slow; the page already renders honestly either
way.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
No visible surface change when the fix holds; the delta is `/backtest`'s response time under concurrent
ingest activity, measured and disclosed either way in `reports/perf-budgets.md`.

### Blueprint conformance
No new surfaces. J-06 and J-07 keep their existing cross-cutting homes per `blueprint.md`'s Feature/
journey-homes table (global readiness badge + `/backtest`; `reports/perf-budgets.md` as J-06's canonical
artifact) — no new page, route, or nav entry.

### Data-contract additions
None. `compute_forward_aggregates` stays the sole computing module and `GET /api/backtest` the sole
serving endpoint (with the MCP tool and ingest-warm call sites unchanged) for this Data Contract row —
this iteration changes only the serving wrapper's concurrency-safety behavior and/or session
configuration, never the contract's identity, shape, or values. `blueprint.md` is updated (additive) to
reflect iter-14's evaluator-confirmed AG-8 resolution and this iteration's planned follow-up.

## OUT OF SCOPE

- The `demo.sh ops-hardening --session-live` walkthrough — already executed by the operator post-iter-14
  (`runs/goal-ops-hardening-iter-14/operator-session-live-walkthrough.md`: exit 0, all 7 steps, including
  the "forward aggregates" summary line). The evaluator weighs that evidence directly; no re-run this
  iteration.
- TC-6's live induced-memory-pressure sufficiency call (TC-3 synthetic + TC-5 organic-absence vs. a fresh
  live induction) — an evaluator/owner judgment already made in iter-14; not re-litigated.
- `HOST_GUARD_REQUIRE_MARKERS` — resolved iter-14 (commit `e5624010`, verified); no further action.
- A `/backtest` elapsed-time/progress affordance — deferred; only needed if this iteration's fix does not
  materially close the latency gap (owner/evaluator call for iter-16 if so).
- Reconciling the per-horizon heartbeat cadence sizing assumption (`data_manager.py:3230` vicinity, audit
  follow-up item (d) / iter-14 eval's UT-10) — carried, non-blocking; likely shrinks as a side effect of
  this iteration's fix; revisit only if it does not.
- Raising `server.memory_cap_mb` / `malloc_arena_max`, touching `main.py`, `app/api/health.py`,
  `app/engine/readiness.py`, or `app/engine/warmup.py` — binding "Do not redo" (iteration-state.md).
- Touching `scripts/automation/*` or the dead `apps/frontend/components/major-indexes-card.tsx` — out of
  product-iteration remit (unchanged from iter-13/14).
- Re-measuring the 10 already-in-budget J-06 pages under IDLE conditions, or re-deriving the boot budget
  — settled iter-9/11; this iteration's `/stocks`/`/sectors`/`/scanner-runs`/`/evidence` spot-check is a
  NEW check under CONCURRENT load, not a repeat of the idle-host numbers.
- A full pytest suite run — targeted, host-guard-confined tests only (this session's standing
  constraint); no concurrent full-suite run.
- Any change to `compute_forward_aggregates`'s columns, signature, or return shape — it stays
  byte-identical; only `forward_aggregates_cached`'s concurrency handling and/or `app.db`'s session/WAL
  configuration may change.
- Repeating the full-deep-basis heavy measurement pass beyond the ONE authorized run this iteration
  (AG-10-class; not a drill to repeat casually).
- Any new UI page, nav entry, or displayed value.

## DEFINITION OF DONE

- [ ] UT-04's root cause is identified and documented with reproducible evidence, naming which
  mechanism(s) (same-key redundant compute / GIL contention / WAL-growth-under-long-read) actually drove
  the 211.8s finding (TC-1, TC-2).
- [ ] The fix is implemented in `forward_aggregates_cached` / `app.db` only; `compute_forward_aggregates`
  remains byte-identical to iter-14's pinned reference (TC-3).
- [ ] Same-key concurrent-MISS test passes: the heavy aggregation body does not run redundantly for one
  still-uncached key (TC-1).
- [ ] Concurrent-write-during-read test is added and its wall-clock ratio recorded (TC-2).
- [ ] One operator-supervised full-basis reproduction of the exact iter-14 UT-04 trigger is performed; the
  resulting `/backtest` cache-miss latency is recorded in `reports/perf-budgets.md`, explicitly marked
  PASS or WARN against the committed ≤1.5s budget (TC-4).
- [ ] The same pass's `/stocks`, `/sectors`, `/scanner-runs`, `/evidence` spot-check is recorded honestly
  (TC-5).
- [ ] `GET /api/health` stays HTTP 200 throughout the pass — no wedge (TC-6).
- [ ] The fix's own failure path does not deadlock a waiting caller (TC-8).
- [ ] Required-still-passing journeys J-01/J-03/J-04/J-05 remain green via deterministic replay + LLM
  fallback (TC-7).
- [ ] No anti-goal violation introduced or worsened (AG-3 byte-identity; AG-8 no unbounded load
  reintroduced; AG-10 host-guard ritual honored for the one heavy pass) — coherence-auditor confirms zero
  second producer/endpoint for the touched Data Contract row (TC-1, TC-3, TC-4).
- [ ] Unit tests pass, host-guard-confined; no regressions; no full pytest suite run.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-15-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-01, J-03, J-04, J-05 (regression replay/LLM fallback); J-06/J-07 verified via the
  operator-supervised pass's recorded numbers (TC-4/TC-5/TC-6) plus the readiness badge/`/backtest`
  render captured during the J-01/J-03/J-05 replay (mirrors iter-14's own corroborating-evidence pattern).
- Unit/integration: extend `test_forward_testing_aggregates_streaming.py` (byte-identity) and
  `test_forward_testing_concurrency.py` (same-key MISS dedup + concurrent-write-during-read +
  failure-path/no-deadlock); all host-guard-confined (`taskset -c 0-3,8-11`, BLAS/OMP/numexpr threads=4);
  never the full suite concurrently.
- Error cases: the fix's own failure path (a caller waiting on an in-flight computation whose owner
  errors, or the equivalent failure mode for whatever mechanism is chosen) must degrade to a clean,
  bounded-time error or an independent recompute — never an indefinite wait.

Test-first contract:

- TC-1: given N ≥ 5 concurrent callers of `forward_aggregates_cached` requesting the SAME never-yet-cached
  `(horizon, asof_key, dataset_version)` key against a shared engine, when all N calls execute
  concurrently, then the underlying heavy aggregation body (`compute_forward_aggregates`'s row-scan) is
  invoked exactly once for that key (asserted via a call-count instrumentation/monkeypatch counter) and
  all N callers return byte-identical payloads.
- TC-2: given a fixture sized so a single uncontended `compute_forward_aggregates` call measures at least
  1.0 second wall-clock, and a background thread issuing repeated committed writes throughout that call's
  execution (mirroring ingest-warm write activity — e.g., inserting new rows or updating `JobProgress`),
  when the read runs concurrently with those writes, then its wall-clock completion time and the
  no-concurrent-write baseline are both recorded, and the ratio (concurrent ÷ baseline) is asserted to be
  ≤ 5.0x (a smoke guard against gross regression; TC-4 is the full-scale proof).
- TC-3: given the existing pinned pre-rewrite reference implementation in
  `test_forward_testing_aggregates_streaming.py`, when the iter-15 fix lands, then
  `compute_forward_aggregates`'s output for all 5 configured horizons, with and without `as_of`, remains
  `==` to the reference (unchanged from iter-14's own proof).
- TC-4: given the backend is started fresh under host-guard confinement (`scripts/start-backend.sh`,
  operator-supervised) against the current full deep-basis DB (`scanner_results` 775,094+ rows,
  `forward_returns` 3,935,930+ rows), when the ingest finalize warm triggers all 5 configured horizons
  while a `GET /api/backtest` request for a not-yet-warmed horizon is issued concurrently (the exact UT-04
  trigger shape), then the resolving request's wall-clock duration is measured via server-side timing and
  recorded in `reports/perf-budgets.md` immediately below the original 211.8s finding, labeled PASS if it
  is at or under the committed ≤1.5s `/backtest` budget or WARN with the measured number if not.
- TC-5: given the same pass as TC-4, when `/stocks`, `/sectors`, `/scanner-runs`, and `/evidence` are
  loaded (or their on-load endpoints called) while the warm is still running, then each page's response is
  recorded — either within its own committed budget (PASS) or as a named WARN with the measured duration
  — and none renders a blank or frozen frame.
- TC-6: given the same pass as TC-4, when `GET /api/health` is polled at 1Hz throughout, then every poll
  returns HTTP 200 within its existing committed budget (no wedge, no restart needed).
- TC-7: given J-01/J-03/J-04/J-05 are currently `passing`, when the deterministic golden-script replay
  runs against this iteration's build, then all four re-verify PASS (or, for any journey without a
  current golden, the LLM browser-qa fallback returns PASS), with none moving from passing to failing.
- TC-8: given a same-key MISS where the fix's own in-flight-computation mechanism fails with an exception,
  when a second concurrent same-key caller is waiting on that outcome, then the second caller does not
  block past a bounded timeout (e.g., 45s, mirroring `test_forward_testing_concurrency.py`'s existing
  `BOUNDED_TIMEOUT_S`) — it either raises a clean, isolated error or independently computes and returns a
  correct payload.

## NOTES

- **Operational protocol for TC-4/5/6 (AG-10-class, ONE supervised pass):** launch via
  `scripts/start-backend.sh` only, host-guard caps active (`HOST_GUARD_CPU_LIST`, BLAS/OMP thread caps,
  `HOST_GUARD_REQUIRE_MARKERS=1`), 1Hz hwmon sampler + thermal watchdog armed — mirrors the iter-3/8/9/14
  protocol. Standard path: developer/reviewer runs it directly under confinement. Fallback (pump note
  constraint — agents cannot start/stop services this session): the operator starts/monitors and reports
  console output, pids, and timestamps verbatim for attributed recording — never fabricate or omit a
  number. Services are CURRENTLY up (backend :8255 and frontend :3255 both returned HTTP 200 as of this
  dispatch) — since TC-4 needs a clean, freshly-started process to correctly attribute timing/VmPeak to
  THIS iteration's build, a restart is required regardless of who performs it; do not reuse the
  currently-running pre-fix process's numbers.
- **Root-cause candidates named for the developer's investigation (not a prescribed implementation):**
  (a) `forward_aggregates_cached` (`forward_testing.py:987`) has NO de-duplication today — a MISS always
  calls `compute_forward_aggregates` directly, so concurrent same-key MISSes redundantly recompute
  (confirmed by reading the function); (b) `uvicorn` runs this app single-process with no `--workers` flag
  (confirmed: no such flag in `scripts/start-backend.sh`, `scripts/dev.sh`, or `main.py`) — concurrent
  heavy Python aggregation loops share one GIL; (c) the audit's own F1 hypothesis — the `yield_per`
  streamed read holds its transaction open longer in wall-clock time than the old `.all()` did, so it may
  overlap more WAL growth from concurrent commits (the DB runs `journal_mode=WAL`, confirmed live via
  `PRAGMA journal_mode`). Any of these, or a combination, may be the dominant cause — determine which via
  evidence, not by adopting the first plausible story (iter-9's lesson).
- **Lesson applied (iter-14):** a memory fix and a lock-contention fix are different problems — proving
  byte-identity/VmPeak-margin again (TC-3) does not substitute for measuring latency under the SAME
  concurrent trigger shape (TC-4); do not let a passing TC-3 stand in for TC-4.
- **Lesson applied (iter-11):** cross-read `logs/backend.log` and `logs/hwmon/hwmon.csv` for the TC-4
  measurement window before attributing any remaining slowness to "ambient load."
- **Lesson applied (iter-9):** a "concurrency overhead is expected and acceptable" narrative is not a
  substitute for the recorded number — if TC-4's post-fix latency is still above budget, record it as
  WARN, not as an accepted rationale.
- **Table depths as of this dispatch** (`apps/backend/data/trendora.db`, read-only, no service start
  required): `scanner_results` 775,094 rows, `forward_returns` 3,935,930 rows, `scanner_runs` 1,858,
  `daily_prices` 3,301,686 — all materially larger than iter-14's own measurement, most likely from the
  operator's post-iter-14 `demo.sh --session-live` run (its step 6 exercised an "eleven-year span" with no
  range cap). UT-04's defect is, if anything, more pronounced on the current DB than when first measured.
- **Operator evidence to weigh, not redo:** `runs/goal-ops-hardening-iter-14/operator-session-live-walkthrough.md`
  records a full, successful `demo.sh ops-hardening --session-live` run (exit 0, all 7 steps, including
  the forward-aggregates summary line) performed AFTER iter-14's own evaluation. Neither iter-14's eval nor
  this spec re-plans producing it; the next evaluator scores it directly.
- **Carried, unrelated:** `tests/test_db.py::test_create_all_produces_expected_tables` pre-existing
  failure, unaffected by this iteration (no schema change).
- **Escalation flag:** if the root-cause investigation concludes the latency is a hard architectural
  single-process/GIL limit that cannot be meaningfully reduced without a bigger redesign (e.g., a separate
  worker process for the ingest warm), name that plainly as a scoped finding for the evaluator/owner rather
  than forcing an inadequate fix — "accept this as a permanent constraint and add a `/backtest` affordance
  instead" is an owner call, not something to decide silently mid-iteration.
