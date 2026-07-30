# Goal Iteration 38 — Close J-07: make the induced-pressure drill's shared cache genuinely live, and run step 1 through its own named path

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 38
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — Prior evaluator verdict (iter-37) was `ESCALATE`; per the binding rule this makes full depth mandatory, not advisory, with no escape condition needed — ESCALATE itself is the trigger.
- **Frontend Present:** no
- **Target journeys:** J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-05, J-06, J-08, J-09
- **Anti-goal reminders:**
  - **AG-1:** A score, ranking, or "edge" MUST NOT be presented as proven/confident unless it is backed by a **passing certified-claim entry** in the evidence ledger (out-of-sample, control-beating). Unbacked values MUST render a "not yet proven" state. *(critical)*
  - **AG-2 — Decision-quality only:** never present return promises, price targets, "buy/sell" signals, or alpha claims; never place or simulate orders. *(critical)*
  - **AG-3:** A journey passes ONLY if the **displayed numbers are correct** — they match the engine's computation for the same as-of date — not merely that the page renders. *(critical)*
  - **AG-4 — No overfit edges:** any pattern surfaced as "proven" must have survived the referee (sealed out-of-sample holdout + controls + multiple-testing correction), never in-sample fit alone. *(critical)*
  - **AG-5 — Preserve determinism and no-lookahead:** scoring uses bars ≤ as-of; forward returns use bars > as-of; never introduce lookahead anywhere. *(critical)*
  - **AG-6:** No iteration ships if its evidence-derived claims (if any) lack a passing referee verdict from the post-decompose gate. *(critical)*
  - **AG-7:** No hard-coded credentials, API keys, or tokens in source files. *(critical)*
  - **AG-8 — Resilience to data-shape and data-scale change:** widening the data basis (new nulls, broader pools, deeper history) must never crash an existing page or exhaust a service's memory — every existing consumer of a widened field is re-validated, the UI degrades gracefully (contained error boundary, honest "—"/NA placeholder, never a blank application-error page), and unbounded whole-table ORM loads are forbidden on the deep basis. *(critical)*
  - **AG-9 — Offline-deterministic ingest:** ingest jobs (fetch/backfill/rebuild) run only against the committed seed / local provider fixtures — no live external network calls or paid data services may be introduced without an explicit goal.md amendment. *(critical)*
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills, full-universe rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched only via the project launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those scripts MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env` whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`, `malloc_arena_max`). Never remove, weaken, or bypass these caps: stripping a HOST-GUARD marked block from a launch script is a REGRESSION regardless of test outcomes. The ceilings are a physical constraint of the current host (two instant hardware resets under all-core vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance budget to optimize away. *(critical)*

## GOAL

Close J-07 ("Heavy aggregates never take the service down") by fixing the two measurement gaps
ledger finding iter-37/o identified: make the induced-pressure drill's backfill target real (K≥3
trading days, not a 0-date no-op) so the ~1.13 GB shared bar cache is genuinely held resident across
the whole finalize tail, measure whether that raises or lowers peak memory versus a forced-fallback
run, and re-run J-07 step 1 through the ingest-finalize path its own text names instead of
`GET /api/backtest`.

## BACKGROUND

J-07 is the session's ONE remaining non-`passing` journey — `partial` for a third consecutive
iteration (iter-35, iter-36, iter-37), `last_passing_iter=iter-34`. Per the priority rubric it is
both the only non-passing journey (rule 3, unblocker — closing it reaches 8/8 journeys passing) and
the smallest remaining scope (rule 4) — no tie to break. Prior verdict was `ESCALATE`, which makes
`Depth: full` mandatory with no escape condition needed.

**The gap (iter-37/o, stated plainly by the iter-37 evaluator):** iter-37 shipped a real fix — sharing
one `prefilled_bar_cache` across `_do_backfill` and the ingest-finalize tail instead of opening two —
and then ran all four of J-07's steps live for the first time. But BOTH live drills exercised paths
where the new behavior is inert: step 1/3's warm was triggered by `GET /api/backtest` (a daemon-thread
path with no `JobProgress`, so `prog._shared_bar_cache` is never set), and step 4's induced-pressure
drill submitted a backfill with `dates_total: 0` (a deliberate 0-target no-op, by design, from the
iter-34 seed script — see below), so `cache_ctx` resolved to `nullcontext()` — the new
`with cache_ctx:` wrap was lexically present and semantically a no-op. The one state this session's
own change creates (the shared cache held resident across the *entire* finalize tail, not just the
compute stage) has therefore never been measured, and the iter-37 auditor's own reading is that the
direction may be REVERSED there (a resident cache could raise, not lower, peak VmPeak versus the
old two-separate-loads baseline). This iteration measures exactly that, on both dimensions the
iter-37 next-step recommendation names: (1) a real K≥3-date throwaway-DB drill with the cache
genuinely live, sampled across the whole tail and compared against a forced fallback; (2) a live
full-deep-basis backfill/rebuild whose finalize hook — not `GET /api/backtest` — triggers the
5-horizon warm, with the 1Hz health poll running throughout.

**Applying binding lessons from this session's ledger** (all directly load-bearing on this
iteration's scope, not just historically interesting): (1) **iter-37's own lesson** — a drill on a
conditional code path (a stashed reference, an attach/fallback context, an early return) must ASSERT
the condition was live (log the cache identity, assert `cache_ctx is not nullcontext()`, assert a
non-zero target count) or its evidence is vacuous; this iteration's drill-target fix is exactly that
assertion made real instead of assumed. (2) **iter-34's lesson** — the throwaway-DB approach
(launched only via `scripts/start-backend.sh` so every host-guard cap still applies) is how a specific
failure mode gets isolated safely, without needing to break the real 4.97 GB live basis; the iter-37
next-step recommendation explicitly warns NOT to inherit the auditor's "hours of all-core compute on
the live basis" framing for the cache-liveness question — it is answerable on the small throwaway
basis. (3) **iter-36's lesson** — a test plan that deliberately takes the backend down must schedule
those tests LAST, so a denied restart cannot strand a later assertion; this iteration's induced-
pressure drill (step 4) is inherently a "break the process" test and must sit at the end of any
browser/QA sequence touching J-07. (4) **iter-34's other lesson** — a saved log EXCERPT is not the
log; every claim from this iteration's drills must be corroborated against a bounded line range in
the LIVE `logs/backend.log`, not a trimmed file.

**Deliberately deferred (rule 5 — one risky item per iteration):** iter-33/g — Regime Lab's cold
`view=pooled` background dispatch and the undiagnosed HTTP 200 carrying an "Internal Server Error"
body. The iter-37 next-step ranked it item 3 (after the two J-07 measurement items), but it is a
genuine structural code change to a DIFFERENT surface (`/research/regime-lab`, already-passing J-06's
domain) with no dependency on and no blocking relationship to J-07's remaining gap. Bundling it here
would risk exactly what rule 5 exists to prevent — an undiagnosable joint failure between two
unrelated risky changes — for zero benefit toward this iteration's one target. It is next in queue.

**Explicitly OUT of dev scope, both owner decisions carried unchanged:** iter-34/j (the
`GET /api/health` ≤0.1s budget, missed a fourth time under live host contention — three dispositions
on record, all the owner's) and iter-33/i (whether `start-frontend.sh` should join
`HOST_GUARD_MARKER_FILES`). Also out of scope: `closure_gate.py`'s backend-only regex false-positive
— it lives in the vendored `incredible_auto_dev` framework tree, outside this product's tracked
`apps`/`scripts`/`project-extensions`/`config.yaml` scope, and the iter-37 evaluator already
downgraded it to "latent rather than recurring, lower priority."

## IN SCOPE

### Backend
- [ ] Widen the throwaway-DB drill fixture (the `runs/goal-ops-hardening-iter-34/mem-drill/
      seed_throwaway_db.py` lineage, reused per the iter-34 lesson) so a submitted backfill targets a
      REAL K≥3-trading-day range not already snapshotted — `dates_total >= 3` in the job's final
      status, not the prior 0-target no-op. This makes `_do_backfill` genuinely stash
      `prog._shared_bar_cache`, and the finalize tail's `cache_ctx` (`data_manager.py:3337-3338`)
      resolve to a real `attach_shared_cache(...)`, never `nullcontext()`.
- [ ] Add an explicit liveness assertion/log line proving `cache_ctx` was the live
      `attach_shared_cache` branch for this drill run (per the binding iter-37 lesson — the evidence
      must assert the condition was live, not merely execute the lexical wrap).
- [ ] Sample VmPeak continuously across the WHOLE finalize tail during that live-cache drill run (not
      only inside the per-item aggregate-warm sub-loops, which is all iter-34/37's monitor scripts
      covered) — a throwaway process, launched only via `scripts/start-backend.sh` (AG-10), with a
      tightened `server.memory_cap_mb` mirroring iter-34/37's calibrated boundary.
- [ ] Produce a comparable forced-fallback measurement of the SAME finalize-tail work with the shared
      cache attach forced off (`cache_ctx` = `nullcontext()`, mirroring pre-iter-37 behavior) so the
      "does holding the cache across the tail raise the peak?" question is answered by a genuine
      two-arm comparison, not one run's number read in isolation.
- [ ] Re-run J-07 step 1 on the real, full-deep-basis live seed DB: trigger the forward-aggregate warm
      for every configured horizon through a genuine backfill/rebuild job's ingest-finalize hook (not
      `GET /api/backtest`'s daemon-thread dispatch, which has no `JobProgress`/`prog._shared_bar_cache`
      at all) — select or create a target as-of date confirmed NOT yet cached under the current
      `dataset_version` so the warm performs real work. No code change to `compute_forward_aggregates`
      / `resolved_forward_aggregate_evidence` / `ensure_historical_forward_aggregates_dispatched` —
      byte-frozen (binding, iteration-state.md "Do not redo").
- [ ] Run J-07 step 2's 1Hz `GET /api/health` poll concurrently for the full duration of that warm; the
      standing ≤0.1s steady-state budget stays the separately-tracked owner item (iter-34/j) — not
      amended here, disclosed as an honest WARN if missed, same convention as iter-37.
- [ ] Record the two-arm cache comparison and the real-trigger step-1 VmPeak margin as new dated
      sections in the SAME `reports/perf-budgets.md` artifact — no second file, no code change to any
      already-registered row's computing module or serving endpoint.
- [ ] Add a dedicated unit test for `_do_backfill`'s whole-stage `except Exception:` branch
      (`data_manager.py:3162`) confirming it releases `prog._shared_bar_cache`, calls
      `_release_process_memory()`, and re-raises the original exception (reviewer MINOR, iter-37).
- [ ] Strengthen `test_run_data_job_backfill_wires_finalize_hook_end_to_end`
      (`test_data_manager.py:2167`) to compare the `aggregates_refreshed` category list against a
      forced-fallback run of the same job shape (audit T2, iter-37 — those warm loops swallow
      non-`MemoryError` exceptions, so a break there shows up only as a silently shorter list).
- [ ] Fix the stale `membership_timeline_cached` docstring (`data_manager.py:650-654`) — it still
      describes a per-date grouped-count round-trip cost the code no longer pays (audit B7, iter-37).
- [ ] Fix `reports/perf-budgets.md:4466`'s stale "591 symbols" → "548 symbols" (audit B8, iter-37).
- [ ] Measure and record `read_pool()`'s now-per-(batch × date) re-read wall-clock cost (~20,680 calls
      against 1,880 dates versus 1,880 before the iter-37 shared-cache change) as a new row/section in
      `reports/perf-budgets.md` (audit B6, iter-37 — a real added constant on the cold path, never
      measured in wall-clock).

### New user-facing capability
None — this iteration is verification/measurement plus small correctness/hygiene fixes on an
already-shipped capability. No new UI surface.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None — backend-only.

### Product surface delta
No visible product surface change. The user-visible delta is confidence: J-07's own availability
guarantee is now measured through the path its own Acceptance text names (a real backfill's
ingest-finalize hook, not a proxy request), and the ~1.13 GB shared-cache-across-the-tail behavior
iter-37 shipped is now known to raise or lower peak memory — not merely assumed safe because no crash
was observed on an inert path.

### Blueprint conformance
No new page/nav. This iteration's work lives entirely under J-07's existing cross-cutting home
(global readiness badge + `/backtest`, `GET /api/backtest`) and the `/data` Coverage payload /
Backfill run-summary contract / Job history homes (Data Manager nav section) per
`runs/goal-session-ops-hardening/state/blueprint.md`'s Information Architecture table — both already
registered, no change to either home this iteration. The blueprint's narrative section has an
appended "iter-38 update" paragraph recording this scope (additive only).

### Data-contract additions
None. This iteration only changes test/drill fixtures and adds measurement evidence for two
already-registered computing paths (`app.engine.data_manager`'s `_do_backfill` /
`_refresh_ingest_aggregates`, serving `GET /api/data`'s Coverage payload / Backfill run-summary
contract / Job history rows) — no new field, no new endpoint, no second producer, no change to any
served value's shape. `blueprint.md` was updated additively (a new narrative paragraph only); no
Information Architecture change, so no `blueprint.reapproval-requested` file was written.

## OUT OF SCOPE

- iter-33/g — Regime Lab's cold `view=pooled` background dispatch + the undiagnosed HTTP 200
  carrying "Internal Server Error" body (deliberately deferred, rule 5 — next in queue).
- iter-34/j — the `GET /api/health` ≤0.1s budget, missed under live host contention; owner decision
  (ratify honest-WARN, rescope the budget for the bounded compute window, or commission the agent
  fix), not agent-settleable.
- iter-33/i — whether `start-frontend.sh` should join `HOST_GUARD_MARKER_FILES`; owner decision, new
  input on record (the `dev.sh` SIGTERM trap orphaning the grandchild `next-server`).
- `warmup.py:194` and the badge wording after a permanently failed warm-up (8 iterations unmade) —
  carried, non-blocking.
- iter-29/b, iter-31/e, iter-32/f (watch only), iter-36/n — carried, unresolved, non-blocking; do not
  re-open.
- The `closure_gate.py` backend-only regex false-positive — vendored framework tree, outside this
  product's tracked dev scope; framework-maintainer follow-up, not a goal-mode dev task.
- J-07's `[NEW]` walkthrough capture, the J-01/J-03 identical-screenshot collision, and the rewritten
  `J-07.json` golden's DB-dependent literals — ride-alongs only, never an iteration's goal (rule 7);
  if the demo lane produces the walkthrough as a side effect of this iteration finally passing J-07,
  good, but it is not a Definition-of-Done item.
- No new UI, no new nav entry, no new Data Contract value.

## DEFINITION OF DONE

- [ ] J-07 passes via browser-qa/live verification: all four steps carry THIS-iteration evidence
      through the paths their own text names (step 1 via a real backfill/rebuild's ingest-finalize
      hook, not `GET /api/backtest`), and the induced-pressure drill (step 4, an inherently
      backend-down-adjacent test) is scheduled strictly LAST in any test plan touching J-07.
- [ ] The throwaway-DB drill's final job status shows `dates_total >= 3` and an explicit assertion
      that `cache_ctx` resolved to the live `attach_shared_cache` branch (not `nullcontext()`).
- [ ] `reports/perf-budgets.md` gains new dated sections for: (a) the two-arm cache-liveness
      comparison (live-cache vs forced-fallback VmPeak across the whole finalize tail), (b) the
      real-trigger step-1 VmPeak margin, and (c) `read_pool()`'s measured re-read wall-clock cost.
- [ ] The new `_do_backfill` `except Exception:` branch test and the strengthened
      `test_run_data_job_backfill_wires_finalize_hook_end_to_end` both pass.
- [ ] The stale docstring (`data_manager.py:650-654`) and the "591 symbols" → "548" correction
      (`perf-budgets.md:4466`) are both fixed.
- [ ] Required-still-passing journeys (J-01, J-03, J-04, J-05, J-06, J-08, J-09) remain green
      (deterministic replay + LLM fallback).
- [ ] No anti-goal violation introduced; AG-8/AG-10 respected throughout (all heavy compute launched
      only via `scripts/start-backend.sh`).
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-38-dev.md`.

## TESTING REQUIREMENTS

- Browser/live: J-07 (all 4 steps, this-iteration evidence, induced-pressure drill scheduled LAST);
  smoke replay of J-01, J-03, J-04, J-05, J-06, J-08, J-09.
- Unit/integration: new `_do_backfill` `except Exception:` branch test; strengthened
  `test_run_data_job_backfill_wires_finalize_hook_end_to_end`; existing `test_bar_cache.py` /
  `test_data_manager.py` shared-cache coverage re-run for regressions.
- Error cases: a `MemoryError` raised mid-warm under a tightened `server.memory_cap_mb` (step 4) must
  be caught by the existing per-item handler and must NOT propagate to a crash, wedge, or restart
  requirement; a whole-stage exception inside `_do_backfill`'s `with prefilled_bar_cache(...)` block
  must release `prog._shared_bar_cache` and re-raise, never leaving a stale reference.

Test-first contract:

- TC-1: given a throwaway DB launched via `scripts/start-backend.sh` with a tightened
  `server.memory_cap_mb`, when a backfill job targeting a real K≥3-trading-day range (none already
  snapshotted) is submitted, then the job's final status shows `dates_total >= 3` (not 0) and the
  drill's own log/assertion confirms `cache_ctx` resolved to `attach_shared_cache` (not
  `nullcontext()`).
- TC-2: given TC-1's job running with the shared `_BarCache` genuinely attached across the whole
  finalize tail, when VmPeak is sampled continuously from `/proc/<pid>/status` throughout that tail
  (not only during the per-item aggregate-warm sub-loops), then the peak is recorded in a new dated
  section of `reports/perf-budgets.md` alongside a forced-fallback run of the same job shape
  (`cache_ctx` forced to `nullcontext()`), showing whether the live-cache peak is higher or lower than
  the fallback peak.
- TC-3: given the real, full-deep-basis live seed DB and a fresh backend process launched via
  `scripts/start-backend.sh`, when a genuine backfill/rebuild job's ingest-finalize hook triggers the
  forward-aggregate warm for every configured horizon (target as-of confirmed NOT cached under the
  current `dataset_version`), then the warm completes without crashing, the triggered date's
  `GET /api/backtest` evidence reaches `evidence_status: "ready"` for all configured horizons, and the
  process's peak memory (VmPeak) during the warm is recorded under `server.memory_cap_mb` in a new
  dated section of `reports/perf-budgets.md`.
- TC-4: given TC-3's warm is running, when `GET /api/health` is polled once per second for the full
  duration, then every poll returns HTTP 200 with no gap between consecutive polls exceeding ~2.15s
  (no frozen or unresponsive window); any steady-state ≤0.1s latency miss is recorded as an honest WARN
  against the separately-tracked owner item (iter-34/j), not scored as a J-07 failure.
- TC-5: given a browser/QA test plan touching J-07, when the plan is assembled, then the induced-
  pressure drill (step 4, an inherently disruptive test) appears strictly AFTER every other J-07
  assertion, so a denied restart after it cannot strand any earlier assertion.
- TC-6: given `_do_backfill`'s whole-stage `except Exception:` branch (`data_manager.py:3162`), when a
  whole-stage exception (e.g. a faulted `read_pool()`/`prefill`) is raised inside the
  `with prefilled_bar_cache(...)` block, then the new test asserts `prog._shared_bar_cache` is set back
  to `None`, `_release_process_memory()` is called, and the original exception is re-raised (not
  swallowed).
- TC-7: given a completed backfill job compared against a forced-fallback (`cache_ctx = nullcontext()`)
  run of the same job shape, when `test_run_data_job_backfill_wires_finalize_hook_end_to_end` runs,
  then it asserts the `aggregates_refreshed` category list for the live-cache run is complete while the
  forced-fallback run's list correctly reflects the degraded/shorter set where applicable.
- TC-8: given `data_manager.py:650-654`'s docstring, when it is read after this iteration's fix, then
  it accurately describes `membership_timeline_cached`'s current cost shape with no reference to the
  removed per-date grouped-count round-trip.
- TC-9: given `reports/perf-budgets.md:4466`, when the file is read after this iteration's fix, then
  the figure reads "548 symbols" (matching the live pool count), not "591 symbols".
- TC-10: given `read_pool()`'s now-per-(batch × date) re-read pattern, when a wall-clock measurement is
  taken on the live basis during a representative multi-date backfill, then the added constant-time
  cost is recorded as a new row/section in `reports/perf-budgets.md` (audit B6 closure).
- TC-11: given this iteration's backend-only diff, when the deterministic golden replay runs for
  J-01, J-03, J-04, J-05, J-06, J-08, J-09, then all seven replay with zero FAIL rows and zero
  reconciliation overturns against their last-verified evidence (no journey moves `passing` ->
  `failing`).

## NOTES

- This is the fourth consecutive dispatch targeting J-07's completion (iter-35 built nothing due to an
  `evidence`-depth mis-dispatch; iter-36 built the code but never ran the browser lane because a
  mid-plan backend-down test stranded it; iter-37 ran all four steps live but through paths where the
  new behavior was inert). TC-1/TC-2/TC-3 exist specifically to close that exact gap a fourth time,
  not to repeat the same measurement through the same wrong door.
- Per the iter-37 next-step recommendation: do NOT inherit a framing that the cache-liveness question
  (TC-1/TC-2) needs hours of all-core compute on the 4.97 GB live basis — it is answerable safely on
  the small throwaway basis, inside AG-10, launched only via `scripts/start-backend.sh`. TC-3/TC-4 (the
  real-trigger step-1 re-run) IS on the live basis, matching J-07 step 1's own literal wording ("with
  the full deep basis loaded"), but is bounded to one warm cycle (iter-37's own precedent measured a
  comparable scenario in well under 5 minutes wall-clock).
- If, despite TC-5's ordering, a live drill still cannot get permission to restart the backend
  afterward, record that as a NEW, distinct finding rather than silently re-attempting — the iter-36
  evaluator already established this is session-specific rather than environmental (the auditor
  booted the backend himself with the ordinary launch script).
- Corroborate every drill claim against a bounded line range in the LIVE `logs/backend.log`, not a
  saved excerpt (binding iter-34 lesson) — a prior iteration's excerpt was proven to omit the single
  most important corroborating line class for its own claim.
