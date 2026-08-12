# Goal Iteration 72 — Fix the connection-pool starvation + the readiness cache's blocking fallback; re-measure J-07 on the production launcher

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 72
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior evaluator verdict was ESCALATE (mandatory, no exceptions). Independently also trigger 1 (structural/cross-cutting): the connection-pool sizing fix touches every DB-backed endpoint's own connection budget, the readiness-cache fallback lives in the SAME module three journeys (J-04/J-07/J-09) and the global badge/preflight banner all read, and the launcher-parity fix touches both `scripts/dev.sh` and the drill scripts that depend on it — none of this is covered by one journey's own tests.
- **Frontend Present:** no
- **Target journeys:** J-05, J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-06, J-08, J-09 (widened to the full passing set this round — prior verdict was ESCALATE, and this iteration's connection-pool resize is process-wide, touching every DB-backed endpoint, not just J-05/J-07's own surfaces)
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
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills, full-universe rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched only via the project launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those scripts MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env` whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`, `malloc_arena_max`). Never remove, weaken, or bypass these caps: stripping a HOST-GUARD marked block from a launch script is a REGRESSION regardless of test outcomes. The ceilings are a physical constraint of the current host (two instant hardware resets under all-core vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance budget to optimize away. *(Owner amendment 2026-07-31, two corrections of record — nothing above is relaxed: `memory_cap_mb` / `malloc_arena_max` live in `config.yaml`, not in `host-guard.env`; and the 2026-07-20/21 resets were subsequently attributed to an uncorrected hardware data-fabric fault (`host-guard.env`, 2026-07-30), so the ceiling VALUES are an owner-set envelope — re-set by the dated entry in "Additional binding notes" below — while this paragraph's prohibition on agents removing, weakening, or bypassing caps is unchanged.)* *(critical)*

## GOAL

Under the same concurrent heavy-load conditions that produced iter-71's 165-second, 58-of-900-non-answer outage, `GET /api/health` answers every poll — by sizing the DB connection pool to the concurrency the server actually admits and by serving an aged readiness-cache entry (with its true age disclosed) instead of blocking on a synchronous recompute — measured this time on the production launcher, never `scripts/dev.sh`.

## BACKGROUND

iter-71 (lean, re-verifying all 8 journeys after iter-70's infra death) found six journeys newly passing but also the session's first measured multi-minute availability failure: a real live drill on `scripts/dev.sh` recorded 58 of 900 health polls with NO answer at all (longest unbroken gap 165 s) and one `GET /api/data` 500 from `sqlalchemy.exc.TimeoutError: QueuePool limit of size 10 overflow 20 reached, timeout 30.00`. iter-71 named the root cause precisely: `config.yaml`'s DB pool (`pool_size: 10` + `max_overflow: 20` = 30) is smaller than `server.limit_concurrency` (64) — the comment claiming it "comfortably covers" 64 concurrent connections is arithmetically false. It also found a second, self-inflicted ingredient in its OWN prior change: `get_readiness_and_preflight`'s staleness bound (iter-71) falls back to a SYNCHRONOUS `compute_readiness`/`compute_preflight` call past 1.5 s of cache age, serialized behind `_TICK_LOCK` with no post-lock recheck — so as the pool starved DB reads and readiness ticks alike, the cache aged, the fallback fired, requests queued behind the one lock, and the stall self-amplified. iter-71's own lesson (2nd entry) states the fix directly: "prefer serving the aged value WITH its age disclosed over blocking on a recompute, and always double-check the cache after acquiring the lock." A third, orthogonal finding: the whole drill ran on `scripts/dev.sh`, which — unlike `scripts/start-backend.sh` — applies none of `--limit-concurrency`/`--timeout-keep-alive`/`--timeout-graceful-shutdown` and writes no persistent `logs/backend.log`, so J-04/J-06's own "never `dev.sh`" acceptance text was violated by the measurement itself (iter-71's 1st lesson entry). J-07 scored `failing` (real non-200 served, first time since iter-69 held `partial` on "no non-200 anywhere"); J-05 dropped to `partial` because its own step 4 is textually the identical health-responsiveness assertion.

Prior verdict was **ESCALATE**, which makes this iteration's depth **full, mandatory, no exceptions** (trigger 3) — independently reinforced by the change's cross-cutting blast radius (trigger 1: a process-wide pool resize plus a module three journeys share plus two launcher scripts). Coherence's last verdict was PASS (0 blocking, 2 advisory — both already accounted for: the `stale_for_s` UI-deferral note and a naming-consistency confirmation), so this is not a consolidation-only pass; it targets the two journeys the ESCALATE was actually about. Per the depth section's guidance to widen the regression set on an ESCALATE, Required-still-passing covers all 6 currently-passing journeys, not a rotating smoke subset — the pool resize is process-wide and could plausibly shift the timing of any DB-backed endpoint.

**Lessons applied:** iter-71's two same-round lessons, verbatim-adjacent — (1) verify which launcher produced a measurement before trusting its size (drives this round's "never `dev.sh`" requirement on the re-measurement, TC-7); (2) prefer disclosed-stale-serve over blocking-recompute, and recheck the cache after acquiring a lock (drives the `readiness.py` fix, TC-3/TC-4). iter-64's lesson — a lane's "false positive"/"transient" label must be checked against the actual frame, not trusted — applies to how this round's QA report and evaluator must read J-05/J-07's evidence. iter-63's lesson — recount the raw poll CSV into a full distribution (breach count, p90, p99, non-answers), never a single before/after headline — applies to this round's `reports/perf-budgets.md` addendum (TC-11).

## IN SCOPE

### Backend
- [ ] `config.yaml`: resize `database.pool_size`/`max_overflow` so their sum is ≥ `server.limit_concurrency` (64) — the arithmetic mismatch iter-71 found. Correct the now-false "comfortably covers" comment. `database.pragmas.mmap_size_bytes` stays `0` (iter-24 audit) — the per-connection VSZ reservation that motivated disabling it does not reappear at a larger pool size.
- [ ] `app.engine.readiness.get_readiness_and_preflight`: past `max_stale_intervals × refresh_interval_seconds`, serve the aged cache entry AS-IS with its real (now-uncapped) `stale_for_s`, instead of falling back to a synchronous `compute_readiness`/`compute_preflight` call — removes the self-amplifying single-lock stall iter-71 introduced. The cold-start path (no cache entry has EVER been published in this process) is unchanged: still a synchronous compute, still `stale_for_s: 0.0`.
- [ ] `app.engine.readiness._tick_and_cache`: add a post-lock recheck (re-read `_READINESS_CACHE`'s freshness immediately after acquiring `_TICK_LOCK`) so a caller queued behind another thread's in-flight tick reuses the entry that thread just published instead of recomputing redundantly. Same producers, same lock, no interface change.
- [ ] `apps/backend/app/engine/readiness.py` (near the `_tick_and_cache` call site, ~line 623): add the reviewer NOTE documenting the honesty-over-availability choice — why disclosed-stale-serve beats block-and-recompute when the synchronous fallback itself would be slow. Doc-only.
- [ ] `scripts/dev.sh`'s backend subshell (never the frontend subshell): mirror `scripts/start-backend.sh`'s `--limit-concurrency`/`--timeout-keep-alive`/`--timeout-graceful-shutdown` (read from the SAME `get_config()` values — no magic numbers) and its append-only persistent logfile pattern, so a dev-mode drill's boot/error log is discoverable at a fixed path instead of a harness temp file.

### Frontend
None. The `/data` page already renders an honest "Dataset coverage could not load from the API. No figures are shown rather than fabricated" message on a `GET /api/data` failure (`apps/frontend/app/data/page.tsx:528`, pre-existing) — this round captures evidence of that existing behavior (TC-10), it does not change it.

### New user-facing capability
None. This round hardens an existing availability guarantee (the service must never stop answering `GET /api/health` during a heavy job) and re-measures it under the correct launcher; it adds nothing a user can newly do.

### New information displayed
None. `stale_for_s` already exists in the `GET /api/health` response (iter-71); only the condition under which it can grow large (and the endpoint's behavior when it does) changes.

### New user actions
None.

### UI surface changes
None — no page, badge, or banner changes.

### Product surface delta
None visible to a user this round in steady state. The delta is availability under load: the same global readiness badge and `/data`/`/backtest` surfaces that already read this endpoint stop going unresponsive during a heavy background compute.

### Blueprint conformance
No new pages or nav entries. Lives entirely inside the ALREADY-registered "Backend readiness / boot phase + preflight verdict" row (Data Contract) and its existing homes (global readiness badge + preflight banner, `/backtest`) — no Information Architecture change. The `scripts/dev.sh` guard-mirroring is launcher/operational scaffolding, mirroring iter-9's precedent for the SAME kind of change — not a Data Contract row.

### Data-contract additions
None. The connection-pool resize is infrastructure config, not a displayed value. The readiness-cache fallback change is implementation-only to the already-registered "Backend readiness / boot phase + preflight verdict" row — same two producers (`compute_readiness`/`compute_preflight`), same one endpoint (`GET /api/health`), no field added or removed, no second producer or endpoint.

## OUT OF SCOPE

- **B-1107** (bounding how many heavy background computes may run at once) — owner-deferred; this iteration's next-step asks the owner about it again rather than building it. The fixes in scope here (pool sizing, serve-stale) are chosen specifically because they are agent-owned and do not require that decision.
- Rendering `stale_for_s` on the readiness badge or preflight banner — still deferred. This would be this cycle's first user-visible UI change; bundling it with a live-availability root-cause fix in the SAME iteration would stack a UI-review surface onto an already cross-cutting change. A future iteration can ship it standalone.
- The owner's standing 2-second-ceiling-for-long-jobs-vs-short-jobs policy answer, the `scripts/automation/browser-qa-phase.sh` one-line ordering-bug sign-off, and the cost-sanction decision (12 consecutive over-budget rounds if this one runs over too) — human-owned (rule 6), not re-litigated here.
- Any change to `compute_forward_aggregates` or the warm-path computation itself — byte-identical, untouched; only the request-path availability mechanism around it changes.
- Any AG-10 cap VALUE change (`memory_cap_mb`, `malloc_arena_max`, `host-guard.env`) — untouched, owner-set.
- A background-refresh-thread watchdog/restart mechanism — the serve-stale fix bounds what is honestly DISCLOSED when the cache ages, not whether the periodic tick thread itself is alive; if a future drill shows the thread genuinely dying (not just slowing under pool contention), that is separate follow-on work (see the assumption-ledger entry this iteration logs).
- The Regime Lab (iter-33/g) — deferred again, not this round's scope (38th round).
- iter-71/e (a QA report's citation to a file that doesn't contain the cited line) — a QA-pipeline/tooling defect, not product scope, per this session's standing framework-scope boundary.

## DEFINITION OF DONE

- [ ] `database.pool_size + database.max_overflow >= server.limit_concurrency` holds in `config.yaml`, enforced by a unit test.
- [ ] J-07 passes via browser-qa-agent, measured against `scripts/start-backend.sh` + `scripts/start-frontend.sh` (never `scripts/dev.sh`), reproducing the SAME concurrent load iter-71 measured (full-horizon forward-aggregate warm + a J-09-triggered background compute dispatched during it).
- [ ] J-05 returns to `passing` — steps 1-3 carried on iter-71's own DB-verified evidence, step 4 (health responsiveness during the SAME heavy job) re-verified live this round.
- [ ] Required-still-passing journeys (J-01, J-03, J-04, J-06, J-08, J-09) remain green — deterministic replay + LLM fallback.
- [ ] No anti-goal violation introduced; `git status --porcelain -- config.yaml project-extensions/ scripts/` shows only the pool-sizing lines in `config.yaml` and the guard-mirroring lines in `scripts/dev.sh` — no HOST-GUARD block or cap value touched.
- [ ] Unit/integration tests pass; no regressions. The iter-71 test asserting synchronous-fallback-past-threshold is rewritten to assert the new serve-stale behavior.
- [ ] `logs/backend.log` receives a boot line when launched via `scripts/dev.sh`, and the launched uvicorn process carries `--limit-concurrency`/`--timeout-keep-alive`/`--timeout-graceful-shutdown` matching `scripts/start-backend.sh`'s values.
- [ ] Evidence captured: `/data` rendering its existing honest fallback when `GET /api/data` fails (fault-injected via a test hook, mirroring J-07 step 4's existing convention) — screenshot filed.
- [ ] `reports/perf-budgets.md` gains a new dated addendum recording this round's prod-launcher poll statistics against iter-71's 58-of-900/165s figures, plus J-06's outstanding page-timing carry item (iter-71/h).
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-72-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-05, J-07 (primary); J-01, J-03, J-04, J-06, J-08, J-09 (regression).
- Unit/integration: `test_config.py`/`test_db.py` pool-sizing invariant test; `test_readiness.py`'s staleness-fallback test rewritten for serve-stale + a new post-lock-recheck test; `test_start_backend_script.py` gains `scripts/dev.sh` guard-mirroring tests mirroring its existing `test_start_backend_wires_server_ops_cfg_flags_into_uvicorn_cmdline` / `test_start_backend_writes_persistent_logfile_with_boot_events`.
- Error cases: DB pool exhausted under a simulated concurrent load must never leave `GET /api/health` with no answer; a killed/wedged tick thread (test hook) must still serve a real (if stale) payload, never raise; `scripts/dev.sh` with `host-guard.env` absent or `HOST_GUARD_ENABLED=0` must still start cleanly with no caps applied (mirrors the existing `start-backend.sh` precedent).

Test-first contract:

- TC-1: given `config.yaml`'s `server.limit_concurrency` = 64, when the backend config loads, then `database.pool_size + database.max_overflow >= 64`, asserted by a unit test.
- TC-2: given the backend launched via `scripts/start-backend.sh` with the corrected pool sizing, when the SAME concurrent load iter-71 measured is reproduced (a full-horizon `factor_lab_all_warm` finalize plus a J-09 on-demand background compute dispatched during it) and `GET /api/health` is polled once per second throughout, then zero polls receive no answer and zero `QueuePool ... overflow ... timeout` lines appear in `logs/backend.log` for the drill window.
- TC-3: given a readiness cache entry whose age exceeds `readiness.max_stale_intervals × readiness.refresh_interval_seconds` (a test hook backdates `computed_at`; no live wedge required), when `get_readiness_and_preflight` is called, then the response returns immediately with the cached payload and a real, uncapped `stale_for_s` reflecting the entry's true age, and call-count instrumentation shows `compute_readiness`/`compute_preflight` were NOT invoked synchronously.
- TC-4: given two callers race `get_readiness_and_preflight` while the cache is aged and the periodic tick thread is mid-tick, when both requests are served, then neither blocks waiting on `_TICK_LOCK` for the other's compute to finish — both return within the SAME budget as a fresh-cache read, and the post-lock recheck is proven to skip a redundant compute when another thread already refreshed the cache first.
- TC-5: given `scripts/dev.sh` launches the backend subshell, when the process starts, then the launched uvicorn command line carries `--limit-concurrency 64 --timeout-keep-alive 65 --timeout-graceful-shutdown 120` (config-derived, matching `scripts/start-backend.sh`'s values) and a persistent logfile receives the boot line.
- TC-6: given `scripts/dev.sh`'s frontend (`next dev`) subshell, when the backend subshell above changes, then the frontend subshell's command line and environment are byte-unchanged — no `--limit-concurrency` or logfile redirect applied to it (backend-only, mirrors the existing `MALLOC_ARENA_MAX`/`ulimit` backend-only convention).
- TC-7: given the app is launched via `scripts/start-backend.sh` + `scripts/start-frontend.sh` (never `scripts/dev.sh`), when browser-qa-agent runs J-07's drill (steps 1-2: full-horizon warm + 1 Hz health poll for the duration, concurrent with a J-09 background dispatch) with the poller armed ≥2 seconds before the job-start command (closes iter-71's TC-5 gap, missed twice), then every poll receives an HTTP response, zero polls exceed the rescoped ≤2s during-warm ceiling, and zero non-200 responses are served.
- TC-8: given the SAME drill as TC-7, when `/data`'s job-history panel and `/backtest`'s per-horizon evidence are read throughout, then both continue serving from storage with no interruption (J-05 steps 1-3 durability, J-08 durability — both carried on iter-71's own re-verified evidence, re-confirmed live this round).
- TC-9: given the SAME drill as TC-7 scored against J-05 step 4's literal text ("while a heavy ingest job runs, poll `GET /api/health`; assert it stays responsive throughout"), when the drill completes, then J-05 returns to `passing`.
- TC-10: given a test hook forces `GET /api/data` to raise (mirrors J-07 step 4's existing throwaway-process/test-hook convention — no live pool exhaustion required), when `/data` is loaded in the browser, then the page renders the existing honest "Dataset coverage could not load from the API. No figures are shown rather than fabricated" message, never a blank Next.js crash overlay, and a screenshot is filed as evidence.
- TC-11: given the prod-launcher drill (TC-7) completes, when `reports/perf-budgets.md` is updated, then a new dated addendum records the poll-count/non-answer/ceiling-breach statistics against iter-71's 58-of-900/165s figures, states the launcher used, and separately records J-06's outstanding page-timing carry item (iter-71/h).
- TC-12: given this iteration's full diff, when `git status --porcelain -- config.yaml project-extensions/ scripts/` is inspected, then only `config.yaml`'s `database.pool_size`/`max_overflow` values and `scripts/dev.sh`'s guard-mirroring lines change — no `memory_cap_mb`/`malloc_arena_max`/HOST-GUARD block value is touched.

## NOTES

- **Human-owned items still open, not re-litigated here** (rule 6): the owner's 2-second health-ceiling policy choice (24th round asked); whether heavy background computes may be bounded to run one-at-a-time (B-1107 — the mechanism this round's fixes deliberately do NOT require); permission to fix the one-line ordering bug in `scripts/automation/browser-qa-phase.sh`; the cost-sanction decision (11 consecutive over-budget rounds before this one).
- **Carried, untouched:** iter-29/b, iter-31/e, iter-32/f, iter-35/k, iter-36/n, iter-37/o, iter-37/q, iter-39/u, iter-46/az, iter-46/ba, iter-47/bd, iter-47/bf, iter-47/bi, iter-48/bj, iter-57/f, iter-57/l, iter-59/g, iter-59/h, iter-59/k, iter-62/e, iter-62/f, iter-63/a, iter-63/b, iter-63/d, iter-64/b, iter-64/e, iter-64/f, iter-65/b, iter-65/c, iter-65/d, iter-66/b, iter-66/e, iter-66/f, iter-66/g, iter-67/f, iter-67/g, iter-68/d, iter-68/e, iter-69/e, iter-70/c, iter-70/e, iter-70/f, iter-71/e (QA citation defect — framework scope), and iter-33/g (the Regime Lab, deferred a 38th time this round makes it).
- **Addressed this round, not carried:** iter-71/a (dev-mode stack on journeys forbidding it — TC-7's launcher requirement), iter-71/b (`dev.sh` missing prod's guards + persistent logfile — this round's `scripts/dev.sh` fix), iter-71/c (the 500 + 165s outage — this round's pool + readiness fixes), iter-71/d (TC-5 missed a second round — this round's TC-5), iter-71/f (walkthroughs unrecorded — J-05/J-07's re-measurement is directed to record `[NEW]`-flagged walkthrough steps via `demo.sh ops-hardening --session-live`, piggybacked on this round's real work, never the goal itself), iter-71/h (J-06 page timings — TC-11).
- An assumption-ledger entry (`runs/goal-session-ops-hardening/state/assumptions.md`, iter-72 — goal-decomposer) records the interpretation call made for the readiness-cache fix: choosing "serve-stale-with-disclosure" as the definitive fix (plus the post-lock recheck as a complementary hardening) rather than an instrumented A/B between it and the pool-sizing fix, and bundling both in the SAME iteration.
