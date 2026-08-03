# Goal Iteration 44 — J-07: wire the unused shutdown/concurrency guards + live-diagnose the horizon-warm stall; J-05: real unsnapshotted-day retest

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 44
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — the prior iteration's verdict was ESCALATE; per the binding rule ("If the prior
  evaluator log emitted `ESCALATE`, you MUST set depth to `full` for this iteration"), this is
  mandatory, no exceptions. It is independently the evaluator's own bound-by-default recommendation
  for this iteration.
- **Frontend Present:** no
- **Target journeys:** J-05, J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-06, J-08, J-09 (full regression of the
  entire currently-passing set — the prior evaluator returned ESCALATE, which this session's own
  widening guidance treats the same as a periodic full-regression trigger; iter-42 and iter-43 both
  widened to the full six-journey set for the same reason)
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
    optimize away. *(Owner amendment 2026-07-31, two corrections of record — nothing above is
    relaxed: `memory_cap_mb` / `malloc_arena_max` live in `config.yaml`, not in `host-guard.env`;
    and the 2026-07-20/21 resets were subsequently attributed to an uncorrected hardware
    data-fabric fault (`host-guard.env`, 2026-07-30), so the ceiling VALUES are an owner-set
    envelope — re-set by the dated entry in "Additional binding notes" below — while this
    paragraph's prohibition on agents removing, weakening, or bypassing caps is unchanged.)*
    *(critical)*

## GOAL

Stop J-07's heavy warm from taking the whole service unreachable — by closing a concrete, previously
undiscovered launcher gap and, for the first time, live-diagnosing WHY the warm stalls at
`horizons_done: 0/5` — and re-test J-05's own defining case (a genuinely unsnapshotted day) that three
prior iterations have skipped.

## BACKGROUND

iter-43's owner-directed memory raise worked (VmPeak flat at 32.4% of the 8192 MB cap for 1,001 s), but
uncovered a second, independent failure: the browser lane found the port fully connection-refused for
several minutes while a background historical forward-aggregate warm sat at `horizons_done: 0/5` after
137 s and never advanced; the process needed `kill -9`. Separately, 63.6% of 272 `/api/health` polls
during a heavy warm exceeded the owner's rescoped ≤2 s bounded-compute-window budget, worsening across
the window. J-05 was re-verified against an already-snapshotted date, so its own defining case — an
ingest that produces genuinely NEW aggregates — has still never run to completion; the one live attempt
at it ran 1,001 s without finishing. This is the SEVENTH consecutive ESCALATE; the iter-43 auditor found
the load-bearing defects that review (PASS_WITH_NOTES), QA (PASS, "no blockers"), and the deterministic
closure gate all missed, so this iteration is full depth both because it must be (prior ESCALATE, Full
trigger 3) and because the audit lane has been this session's only reliable catch six iterations running.

**A concrete, previously undiscovered lever exists for the shutdown problem.** Direct code reading
(not inherited from any prior report) shows `apps/backend/app/config.py`'s `ServerOpsCfg` — introduced
in the mcp-loop session (J-100) and already declaring `limit_concurrency: int = 64`,
`timeout_keep_alive_seconds: int = 65`, and `graceful_timeout_seconds: int = 120` — documents itself as
"the SINGLE source of the uvicorn concurrency cap, the keep-alive + graceful-shutdown timeouts... the
start script (`scripts/start-backend.sh`) enforces." A direct read of that script's `exec` line
(`incredible_auto_dev/scripts/start-backend.sh:95`, the exact site the iter-43 audit named as B2's
"concrete lead") shows it passes only `--host`/`--port`/`--app-dir` to uvicorn — none of the three
`ServerOpsCfg` values ever reach the process. This is the SAME class of gap iter-2 closed for
`memory_cap_mb`/`malloc_arena_max` (a config value that already existed but a script that never
enforced it) — small, mechanical, config-driven, and it directly gives a stuck shutdown a deadline
instead of holding the process hostage forever. Wiring it does not, by itself, explain WHY the warm
stalls — that root cause is diagnosed live this iteration via the `TRENDORA_DIAG_FAULTHANDLER_SIGUSR1`
all-thread dump tool armed at iter-40 and never yet fired at a genuine freeze (iter-43 eval's explicit
next-step item 2).

Per rule 3 (unblockers) and rule 5 (never bundle two risky journeys): J-05 and J-07 are targeted
together because they share one underlying question — does a heavy, correctly-triggered background
compute actually terminate? — not because this iteration takes two separate risky actions. Of this
iteration's deliverables, the launcher-flag wiring, the Retry-endpoint parity fix, the job-message-honesty
fix, and the stray-diff revert are all small and mechanical; J-05's retest is pure verification (no code
change anticipated); the ONE genuinely risky lever is the live stall diagnosis and whatever targeted fix
it points to — kept proportional to what the diagnostic actually finds, per the binding iter-39 lesson
("three probes without hitting the target means you're diagnosing the wrong thing — go read what
allocates/blocks FIRST") and the binding iter-42/iter-40 lessons on measuring the whole job, never a
narrowed function or the absence of a name in one traceback. If the diagnostic implicates something
outside this iteration's evidenced reach, the DoD accepts an honestly-documented, unresolved finding
over a speculative rewrite — this iteration does not repeat iter-38's mistake of shipping a fix for a
failure mode it never actually reproduced.

Applies the binding iter-43 (first) lesson verbatim: raising a resource ceiling proves headroom, not
termination — this iteration measures whether the warm actually FINISHES, not just whether it fits.
Applies the binding iter-43 (second) lesson: any new guard/except clause this iteration adds must be
keyed to the whole exception set the diagnosed incident actually produces, not its headline exception.

## IN SCOPE

### Backend

- [ ] `incredible_auto_dev/scripts/start-backend.sh` — wire `server.limit_concurrency`,
      `server.timeout_keep_alive_seconds`, and `server.graceful_timeout_seconds` (all already declared
      in `ServerOpsCfg`, currently read by nothing) into the uvicorn `exec` line as
      `--limit-concurrency` / `--timeout-keep-alive` / `--timeout-graceful-shutdown`, read from
      `get_config()` exactly like the existing `memory_cap_mb`/`malloc_arena_max` block two sections
      above it — no magic numbers, no change to `scripts/dev.sh` (out of scope, see below).
- [ ] Live-reproduce J-07 step 1's stall (the full-deep-basis historical forward-aggregate warm) via
      `scripts/start-backend.sh` (AG-10: a load drill, launched only through the sanctioned script)
      with `TRENDORA_DIAG_FAULTHANDLER_SIGUSR1=1` set. When `background_compute.active[].horizons_done`
      has not advanced for a bounded window past `started_at` (reusing the already-disclosed
      `get_background_compute_status()` fields — no new polling mechanism), send `kill -USR1 <pid>` and
      capture the resulting all-thread stack dump verbatim in the dev handoff, naming the exact blocked
      call/lock — not a guess, not a re-citation of iter-43's unconfirmed candidates.
- [ ] Apply the smallest correct fix at the identified blocking site so a fresh reproduction of the
      same warm either advances and reaches a terminal outcome, or — if the true fix needs materially
      larger, unevidenced work — document the exact finding for evaluator/owner disposition instead of
      re-claiming it fixed (mirrors the iter-42 precedent for an inconclusive AG-8 attempt). Any new
      except/guard clause added here must be keyed to the diagnosed incident's WHOLE exception set
      (binding iter-43 lesson), not its headline exception.
- [ ] Re-measure J-07's rescoped ≤2 s bounded-compute-window `/api/health` budget and the concurrent
      cached `GET /api/backtest` read with ONE clean, single trigger — no manual mid-run probing
      (closing the dev's own disclosed iter-43 confound).
- [ ] `apps/backend/app/api/data.py` (`retry_job`, currently line ~309) — wrap
      `data_manager.retry_run(...)` in the SAME `(RuntimeError, MemoryError)` → 503 handling
      `start_job`/`resume_job` already carry (audit B4), so all three job-launch endpoints share one
      honest-error contract.
- [ ] `apps/backend/app/engine/data_manager.py` (`_run_job`'s `finally` block, currently line ~4543) —
      stop unconditionally overwriting `prog.message` with `_final_summary(prog)` for a job that failed
      via the outer exception handler; preserve `_record_error`'s captured reason so a `failed` job's
      persisted message names the real cause instead of a generic "no work performed"-style summary
      (reviewer MINOR, carried; this is also the reason the iter-43 audit's own B2 `_run_detail` fix is
      currently a no-op on this path — B5 proved the two expressions are identical strings today).

### Frontend

- [ ] `apps/frontend/tsconfig.json` — revert the unattributed `include`-array reordering (audit F1), or
      confirm and state in the dev handoff why it is load-bearing. No product-facing frontend change.

### New user-facing capability

None. This iteration closes a launcher enforcement gap, diagnoses and (where evidenced) fixes an
availability defect, and re-verifies J-05's already-shipped ingest-time-aggregation mechanism against
its own genuinely-new-data case. No new feature, page, or control.

### New information displayed

None planned. Conditional only: IF the live diagnostic's fix requires disclosing a genuine
non-advancing background compute, the ONLY authorized shape is one new field,
`background_compute.active[].stalled: bool`, on the ALREADY-served `GET /api/health` payload (see
Data-contract additions below). If the diagnosed fault is resolved outright, or is disclosed without a
code fix, no new field ships this iteration.

### New user actions

None.

### UI surface changes

None — no new component. The global readiness badge and `/data`'s `BackgroundComputePanel` keep their
existing shape unless the conditional field above ships, in which case it renders as an additive
existing-component detail, not a new surface.

### Product surface delta

None visible in shape for a healthy run. If the stall recurs less (or not at all) and the health budget
holds, the observable delta is that the app stays reachable and honest during a heavy warm instead of
going silent — a reliability change, not a new feature.

### Blueprint conformance

J-05 and J-07 keep their existing cross-cutting homes per
`runs/goal-session-ops-hardening/state/blueprint.md`'s Information Architecture table (J-05: Data
Manager / Scanner Runs / Dashboard / Research / Evidence; J-07: global readiness badge + `/backtest`)
— no new page/nav/route this iteration. Blueprint updated with an iter-44 narrative paragraph recording
this scope and the conditional Data Contract note.

### Data-contract additions

None unconditionally. CONDITIONAL: if (and only if) the live diagnostic's fix requires disclosing a
non-advancing background compute, this iteration may add exactly one new field —
`background_compute.active[].stalled: bool` (`true` once the in-flight entry has shown zero
`horizons_done` progress past a config-driven bound; absent/`false` otherwise) — to the
ALREADY-registered "Backend readiness / boot phase + preflight verdict" row: computed by
`app.engine.forward_testing.get_background_compute_status()`, composed by
`app.engine.readiness.compute_readiness`, served by the SAME `GET /api/health` endpoint. No new
endpoint, no second producer. If this field ships, remove this "conditional" qualifier from the
blueprint row's Notes in the SAME iteration (the decomposer does not pre-certify it as built — the
evaluator does).

## OUT OF SCOPE

- `scripts/dev.sh`'s uvicorn invocation — the concurrency/timeout wiring targets
  `start-backend.sh` only, the site the iter-43 audit named and the one the QA/demo/browser-qa lanes
  actually launch; `dev.sh` is a manual `--reload` dev convenience, lower stakes, not this iteration's
  evidenced gap.
- A sixth `_BarCache.prefill` bound attempt, or any further change to `_SymbolColumns`/`bars_asof`'s
  70-80× slowdown, UNLESS the live diagnostic in this iteration directly implicates it as the stall's
  blocking call — no speculative rewrite absent a proven mechanism (binding iter-38/iter-39/iter-42
  lessons).
- Any warm-seam rewrite (`compute_forward_aggregates` et al.) beyond what the live diagnostic's named
  blocking call actually requires — no repeat of a fix aimed at an unconfirmed candidate.
- The same thread-launch-guard class gap in `warmup.start_warmup` (`forward_testing.py:1691`) — same
  class, no evidenced incident there, deliberately deferred (rule 5, carried from iter-43).
- iter-33/g — Regime Lab's cold `view=pooled` background dispatch (deferred a tenth time).
- iter-29/b and the badge wording after a permanently failed warm-up; iter-31/e; iter-32/f; iter-35/k;
  iter-36/n; iter-37/o; iter-37/q; iter-39/u — carried, untouched, none blocking J-05/J-07.
- J-07's `[NEW]` walkthrough recording and J-05's real acceptance frames — capture-only, never an
  iteration's own goal (rule 7); ride along with whichever iteration lands the passing evidence.
- Any further `docs/goal.md` edit or `memory_cap_mb`/host-guard cap change — both standing owner items
  (iter-33/i, iter-34/j) are already closed; nothing outstanding to re-litigate.

## DEFINITION OF DONE

- [ ] `start-backend.sh` passes `--limit-concurrency`/`--timeout-keep-alive`/`--timeout-graceful-shutdown`
      to uvicorn, sourced from `ServerOpsCfg` with no magic numbers (TC-1).
- [ ] A backend process launched via `start-backend.sh` with a stuck in-flight background task
      self-terminates within its configured graceful-shutdown window, without requiring a manual
      `kill -9` (TC-2).
- [ ] The live stall is diagnosed via a genuine SIGUSR1 all-thread reproduction, naming the exact
      blocked call (TC-3), and is either fixed with a clean re-reproduction advancing/terminating, or
      honestly disclosed as unresolved with the named blocking call (TC-4).
- [ ] J-07's rescoped ≤2 s bounded-compute-window `/api/health` budget and the concurrent cached
      `/api/backtest` read are re-measured with one clean single trigger (TC-5, TC-6); the service never
      goes fully connection-refused during the warm (TC-7).
- [ ] The existing induced-pressure abort (J-07 step 4) still holds — no regression (TC-8).
- [ ] `POST /data/jobs/{run_id}/retry` returns HTTP 503 (not 500) on a thread-launch failure, matching
      its two siblings (TC-9).
- [ ] A job that fails via `_run_job`'s outer exception handler persists a message naming the real
      captured reason, not the generic `_final_summary` text; a job that completes normally still gets
      `_final_summary`'s descriptive summary unchanged (TC-10).
- [ ] `apps/frontend/tsconfig.json`'s stray diff is reverted or explicitly justified (TC-11).
- [ ] J-05 is retested against a historical trading day CONFIRMED absent from `/scanner-runs` before the
      run, through to a terminal or honestly-reported in-flight state (TC-12).
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-06, J-08, J-09 all report PASS with unique,
      dated evidence — no two journeys sharing one screenshot file (TC-13, closing iter-43/ai).
- [ ] No anti-goal violation introduced; AG-10's caps stay enforced end-to-end (the new
      concurrency/timeout flags are additive to, never a replacement for, the existing `ulimit`/
      host-guard enforcement).
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-44-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-05 (`journey-scripts/J-05.json`, re-triggered against a confirmed-unsnapshotted date, not
  the golden script's default date if that date is already snapshotted), J-07
  (`journey-scripts/J-07.json`, all 4 steps); full regression replay of J-01, J-03, J-04, J-06, J-08,
  J-09. Evidence capture MUST produce a distinct screenshot per journey (unique file, verified by
  checksum) — no two journeys sharing one capture (closes iter-43/ai).
- Unit/integration: a subprocess test asserting `start-backend.sh`'s launched uvicorn process's
  `/proc/<pid>/cmdline` (or equivalent) carries the three new flags with values matching
  `get_config().server`; a mocked `POST /data/jobs/{run_id}/retry` test asserting 503 on
  `(RuntimeError, MemoryError)`; a `_run_job` failure-path test asserting the persisted `message`
  contains the real exception text (not `_final_summary`'s generic string) for a `failed` job, and an
  unchanged `_final_summary` string for a normally-completed job; a fixture-backed byte-identity test
  for any diagnostic-driven fix (TC-4), if one ships.
- Error cases: a thread-launch failure on Retry must never return a bare 500; `_run_job`'s message
  fix must not regress the iter-43 audit's B5-verified no-op paths (`_create_run_record`/
  `_checkpoint_run_record` serializing a still-`running` job stay unaffected).

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps
to at least one concrete scenario line below.

- TC-1: given `start-backend.sh` after this iteration, when it launches uvicorn, then the exec
  command's arguments include `--limit-concurrency <server.limit_concurrency>`,
  `--timeout-keep-alive <server.timeout_keep_alive_seconds>`, and
  `--timeout-graceful-shutdown <server.graceful_timeout_seconds>`, each matching the value
  `get_config().server` returns (default 64 / 65 / 120) — verified against the running process's own
  command line, not merely the script's source text.
- TC-2: given a backend process launched via `start-backend.sh` with an in-flight background task that
  does not yield control, when the process receives SIGTERM, then it exits (process no longer present)
  within its configured `graceful_timeout_seconds` window, without a manual `kill -9`.
- TC-3: given the backend launched via `start-backend.sh` with `TRENDORA_DIAG_FAULTHANDLER_SIGUSR1=1`
  and a live-reproduced full-deep-basis historical forward-aggregate warm whose
  `background_compute.active[].horizons_done` stays at 0 for a bounded window past `started_at`, when
  `kill -USR1 <pid>` is sent, then the process remains alive (still present in `/proc`) and an
  all-thread stack dump is captured and recorded verbatim in the dev handoff, naming the exact
  blocked call/lock.
- TC-4: given TC-3's identified blocking call, when the targeted fix (or an honest documented finding,
  if the true fix is out of this iteration's evidenced reach) is applied, then a fresh reproduction of
  the same warm either (a) advances `horizons_done` past 0 and reaches a terminal outcome within its
  observation window, with byte-identical output to the pre-fix reference for any touched producer, or
  (b) is disclosed in the dev handoff as unresolved, naming the exact blocked call — never silently
  re-claimed as fixed.
- TC-5: given the backend running the deep basis with `memory_cap_mb: 8192` and this iteration's
  fixes, when the full-horizon forward-aggregate warm is triggered via ONE single ingest-finalize
  trigger (no manual mid-run probing) while `GET /api/health` is polled at 1Hz throughout, then every
  poll returns HTTP 200 within the rescoped ≤2 s bounded-compute-window budget, recorded in a fresh
  dated `reports/perf-budgets.md` section.
- TC-6: given the same single-trigger warm, when a previously-cached `GET /api/backtest` read is
  issued exactly once concurrently (not a manual repeated probe), then it returns HTTP 200 throughout
  (J-07 step 1's "served ... throughout" clause).
- TC-7: given the backend under the same single-trigger warm, when the browser-qa/replay lane polls
  `GET /api/health` throughout, then the port never returns connection-refused and never goes fully
  unreachable — the iter-43 total-outage failure mode does not recur.
- TC-8 (regression): given J-07 step 4's existing sanctioned induced-pressure test hook (a tightened
  `server.memory_cap_mb` in a throwaway process, launched only via `start-backend.sh`), when memory
  pressure is induced during a warm, then the warm aborts honestly via the existing per-item
  `MemoryError` isolation handler while the SAME process's `/api/health` and cached reads keep
  responding HTTP 200 — no deadlock, wedge, or restart.
- TC-9: given `POST /data/jobs/{run_id}/retry` when `data_manager.retry_run` raises `RuntimeError` or
  `MemoryError` on thread-launch failure, then the endpoint returns HTTP 503 with a descriptive
  `detail`, matching `start_job`/`resume_job`'s existing contract (never a bare 500).
- TC-10: given a job that fails via `_run_job`'s outer exception handler (a real captured exception),
  when the run-history record is persisted, then its `message` field contains the real captured
  exception text (via `_record_error`), not `_final_summary`'s generic string; given a job that
  completes normally (status `ok`/`partial`/`resumable`), when its record is persisted, then
  `_final_summary`'s descriptive summary is unchanged from before this iteration.
- TC-11: given `apps/frontend/tsconfig.json`'s current working-tree `include`-array reordering (audit
  F1), when this iteration's diff is reviewed, then the file matches its pre-iter-43 content, or the
  dev handoff explicitly states why the reordering is load-bearing.
- TC-12: given a historical trading day confirmed absent from `/scanner-runs` immediately before the
  run (checked via the UI or API, not assumed), when a backfill covering exactly that one day is run
  via `/data` to a terminal state, then either (a) it reaches `ok`, `/scanner-runs` lists the new date
  with a rendered leaderboard, and the run record's `aggregates_refreshed` names the finalize hook's
  refreshed aggregates, or (b) if it does not terminate within a bounded observation window, the run's
  honest in-flight state (never a fabricated success) is captured and reported in the dev handoff.
- TC-13: given the full required-still-passing set (J-01, J-03, J-04, J-06, J-08, J-09), when the full
  regression replay runs against this iteration's build, then all six journeys report PASS with dated
  evidence, and an `md5sum` check over the evidence directory confirms no two journeys share one
  screenshot file.

## NOTES

- Applies the binding iter-39 lesson: a drill that has probed the same target three times without
  hitting it is diagnosing the wrong thing — this iteration's diagnostic step reads the LIVE all-thread
  stack rather than guessing at T2/`_SymbolColumns` again on no new evidence.
- Applies the binding iter-40 (second) lesson: `.yield_per()` bounds the cursor, not the accumulator —
  relevant if TC-4's fix touches any streamed read.
- Applies the binding iter-42 (second) lesson: a memory/performance measurement that only measures the
  work REMOVED or a narrowed function is not a measurement — TC-5/TC-6's re-measurement is against the
  WHOLE single-trigger warm, not an isolated sub-call.
- Applies the binding iter-43 (first) lesson: raising a resource ceiling proves headroom, not
  termination — TC-4's acceptance criterion is the warm actually advancing/terminating, not merely
  staying under the memory cap.
- Applies the binding iter-43 (second) lesson: any new except/guard clause this iteration's TC-4 fix
  adds must be keyed to the diagnosed incident's WHOLE exception set, not its headline exception —
  confirm by reading the live dump/log for every distinct failure signature it actually produced.
- `ServerOpsCfg`'s three previously-unwired values were introduced in the mcp-loop session (J-100) and
  have never been enforced by any launch script since — this is a genuine, previously undiscovered gap,
  not a regression introduced by this session's own work.
- See `runs/goal-session-ops-hardening/state/assumptions.md` iter-44 for the reasoning on choosing the
  launcher-config-wiring lever over inventing a new watchdog mechanism, and on keeping TC-4's outcome
  conditional rather than mandating a specific fix shape upfront.
