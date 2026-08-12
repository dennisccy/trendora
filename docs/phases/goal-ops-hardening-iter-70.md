# Goal Iteration 70 — Stop `GET /api/health` recomputing readiness/preflight on every request

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 70
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior evaluator verdict was ESCALATE (mandatory, no exceptions); independently, the hardening cadence (6 consecutive lean iterations dispatched, cadence=6) is also due (trigger 4), and the change itself is structurally cross-cutting (trigger 1: the single canonical readiness/preflight producer is read by the global badge, the preflight banner, and the `/data` panels — a coherence + UX-regression surface per the evaluator's own ESCALATE reasoning).
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
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills, full-universe rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched only via the project launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those scripts MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env` whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`, `malloc_arena_max`). Never remove, weaken, or bypass these caps: stripping a HOST-GUARD marked block from a launch script is a REGRESSION regardless of test outcomes. The ceilings are a physical constraint of the current host (two instant hardware resets under all-core vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance budget to optimize away. *(Owner amendment 2026-07-31, two corrections of record — nothing above is relaxed: `memory_cap_mb` / `malloc_arena_max` live in `config.yaml`, not in `host-guard.env`; and the 2026-07-20/21 resets were subsequently attributed to an uncorrected hardware data-fabric fault (`host-guard.env`, 2026-07-30), so the ceiling VALUES are an owner-set envelope — re-set by the dated entry in "Additional binding notes" below — while this paragraph's prohibition on agents removing, weakening, or bypassing caps is unchanged.)* *(critical)*

## GOAL

While a heavy background aggregate warm is running, `GET /api/health` answers every poll from a cached, periodically-refreshed readiness/preflight value instead of recomputing `compute_readiness`/`compute_preflight` synchronously on the request thread — closing the session's first-ever health-check non-answers and the 8.09% breach rate iter-69 measured.

## BACKGROUND

The evaluator's depth recommendation is **full and binding by trigger 3** (prior verdict ESCALATE — mandatory, no exceptions); the hardening cadence (6 consecutive lean iterations against `CHAIN_HARDENING_CADENCE=6`) is independently due, and the evaluator's own ESCALATE reasoning names this as "a design change to a canonical producer" with "a coherence and UX-regression surface, not a diagnostic add" (trigger 1) — `compute_readiness`/`compute_preflight` are re-read by the global badge, the preflight banner, and the `/data` panels, so the fix's blast radius is not covered by one journey's tests alone.

iter-69's own re-derived, independently-recounted attribution is the direct input to this iteration's scope: across 74 answered health-poll breaches, `readiness_s` (the `compute_readiness` call) dominates 43 and `preflight_s` (the `compute_preflight` call) dominates 31; neither `db_reads_s` nor `queue_wait_s`/`pre_receive_gap_s` dominate any. Live-vs-idle per component: `readiness_s` p90 0.5631s vs 0.0022s idle (~256x), `preflight_s` p90 0.5439s vs 0.0061s idle (~89x). The breaches are 96% localized to the `factor_lab_all_warm` phase (74 of 77 breaches and all 3 non-answers inside 400 of the round's 952 polls), which iter-69 also confirmed is NOT explained by a uniform concurrent-caller confound. iter-69's next-step recommendation orders exactly this: "Stop `GET /api/health` recomputing readiness and preflight on every request. ... Serve them from a stored/bounded value in the spirit of the goal's own compute-at-ingest rule, keeping `app.engine.readiness` as the single producer — no second implementation, no new endpoint."

Per the priority rubric: no journey regressed (rule 1); the last coherence.md was PASS (0 blocking, 2 advisory), so no consolidation-only pass is mandated (rule 2); J-07 is this session's only non-`passing` journey and is squarely an unblocker of its own remaining gap (rule 3); this is the smallest available fix that a lightly-evidenced round could not have chartered before iter-69's sub-span split named the two components (rule 4); the iteration carries exactly ONE risky change — the readiness/preflight request-path-to-cache redesign — and touches no other risky surface (rule 5); the remaining owner-gated items (the 2s-ceiling policy question, `browser-qa-phase.sh` sign-off, cost sanction, and arming the browser-QA lane's watchdog a 5th time) are explicitly NOT re-attempted this round, since none of them block the agent-owned work named above (rule 6); this is real code work, not an evidence-only round (rule 7).

Lessons applied: (iter-68, twice) join instruments already on disk before commissioning a new one — this iteration reuses the SAME `db_reads_s`/`readiness_s`/`preflight_s` watchdog sub-spans iter-69 already shipped to PROVE the fix worked (TC-7 below: after the change, `readiness_s`/`preflight_s` read near-zero because they are now a cache-dict read, not a compute call) rather than adding a fourth instrument. (iter-65/66/67) never re-run a suspect chain in a standalone script and always report the FULL phase-grouped breach distribution — this iteration changes the LIVE serving path itself (not a standalone re-run) and TESTING REQUIREMENTS below mandates the phase-grouped write-up iter-69's next-step item (3) ordered ("report the phase breakdown every round from now on"). (iter-69, second entry) a conditional "Do not redo" ban lapses when its own release condition is met and must be checked each round: iteration-state.md marks the `factor_lab_all_warm` bounding ban RELEASED (not banned) as a legitimate ALTERNATIVE target if this fix proves insufficient — this iteration does not bound that phase; it targets the two named components directly, per iter-69's own narrower, better-evidenced recommendation.

An assumption-ledger entry (`runs/goal-session-ops-hardening/state/assumptions.md`, iter-70) records the interpretation call on HOW to "serve from a stored/bounded value": an in-process, bounded-interval background-refresh cache (mirroring `app.engine.warmup`'s existing daemon-thread precedent) rather than a persisted DB table, since readiness/preflight are liveness state (not data that must survive a restart) and a synchronous cold-start fallback already covers that case with zero staleness risk.

## IN SCOPE

### Backend
- [ ] Add a bounded-interval background-refresh cache for `compute_readiness`/`compute_preflight`'s combined output inside `app.engine.readiness` itself (the SAME module, SAME two functions — no second producer): a new daemon thread, started from the SAME `lifespan` boot sequence that already starts `app.engine.warmup.start_warmup` (`apps/backend/main.py`), reusing that existing daemon-thread/single-flight idiom rather than introducing a second threading abstraction.
- [ ] New config knob `readiness.refresh_interval_seconds` (`config.yaml`, alongside the existing `readiness:` block) — the tick cadence, set well under the existing `startup.health_poll_interval_seconds` (2.0s) so a fresh value is always available before the badge's next poll.
- [ ] `GET /api/health` (`apps/backend/app/api/health.py`) reads the cached readiness+preflight dict instead of calling `compute_readiness`/`compute_preflight` directly on the request thread. The three existing DB reads (`func.max(DailyPrice.date)`, `_distinct_symbol_count`, `func.max(ScannerRun.asof_date)`) stay on the request path unchanged — iter-69's attribution does not implicate them, and touching them is out of scope (rule 5, one risky action).
- [ ] Cold-start fallback: before the background thread's first tick completes (boot, or a direct-call test invoking `health(session)` with no running thread), the handler computes once synchronously — the existing pre-iteration behavior — so boot-time and unit-test call shapes are unaffected.
- [ ] Immediate refresh trigger at the end of `_refresh_ingest_aggregates` (`apps/backend/app/engine/data_manager.py`), the SAME finalize hook every other ingest-time aggregate in this table already refreshes from, so a job-completion state flip (e.g. `awaiting_snapshot` → `ready`) is reflected within one tick rather than waiting up to a full `refresh_interval_seconds` period.
- [ ] `record_verdict_transition`'s existing on-transition-only write (`app.engine.readiness`) moves with `compute_preflight` into the background tick — same dedup-against-last-recorded-verdict logic, same verdict-history file; no longer invoked on the request path.
- [ ] Degrade-on-error: if a background tick's `compute_readiness`/`compute_preflight` call raises, the cache keeps serving its last-known-good value (never blanks/500s `GET /api/health`) and the thread keeps ticking — mirrors this endpoint's existing per-request degrade-on-error convention, moved to the tick.
- [ ] Concurrency: the cache read (request thread) and cache write (background thread) never produce a torn/partial read — an atomic swap or equivalent, proven by a concurrency test (mirrors `forward_aggregates_cached`'s existing single-flight/lock idiom precedent in this codebase).
- [ ] Reporting: append a new dated addendum to `reports/perf-budgets.md` (append-only — no edits to any prior addendum's text) with (a) the phase-grouped health-poll breach table for this round's live-warm drill (per iter-69's next-step item 3), and (b) a small correction fixing iter-69/b (the join paragraph's mis-stated "3 additional records" — the correct count is 83 in-window records belonging to a third client) and iter-69/c (the TC-6 scorecard label — the app and `config.yaml:777` both read `60d`, not `65d`).

### Frontend
- None. No `apps/frontend/*` file is touched — `GET /api/health`'s response body/shape is unchanged (byte-identical fields), so `HealthBadge`, `PreflightBanner`, and the `/data` `BackgroundComputePanel` need no change.

### New user-facing capability
None — this is an availability/latency fix to an existing endpoint, not a new capability.

### New information displayed
None. `readiness`/`readiness_detail`/`warmup`/`background_compute`/`preflight` keep their exact existing field names, types, and values; only the compute timing (per-request vs. cached) changes.

### New user actions
None.

### UI surface changes
None. Same badge, same banner, same panels, same polling cadence from the frontend's perspective.

### Product surface delta
No visible change to any page under normal conditions. The observable delta is availability during a heavy background warm: the global readiness badge and preflight banner keep answering within budget instead of occasionally stalling past 2s or (rarely, per iter-69) not answering at all within the poller's 5s client timeout.

### Blueprint conformance
No new page/route/nav entry. This work lives entirely under the blueprint's existing "J-07 — Heavy aggregates never take the service down" home (global readiness badge + `/backtest`) and modifies the ALREADY-registered "Backend readiness / boot phase + preflight verdict" Data Contract row's Notes in `runs/goal-session-ops-hardening/state/blueprint.md` (iter-70 narrative appended) — same computing module (`app.engine.readiness.compute_readiness`/`compute_preflight`), same serving endpoint (`GET /api/health`), no second producer, no new endpoint.

### Data-contract additions
None. `readiness`/`readiness_detail`/`warmup`/`background_compute`/`preflight` keep their existing single computing module (`app.engine.readiness.compute_readiness` / `compute_preflight`) and single serving endpoint (`GET /api/health`) — this iteration adds an in-process caching/refresh layer around those SAME two functions, never a second implementation or a second endpoint. The new `readiness.refresh_interval_seconds` config knob is an internal tuning value, not a displayed UI value, and is not a Data Contract row.

## OUT OF SCOPE

- Bounding `factor_lab_all_warm` (or `coverage_membership_timeline_refresh`) by code change — the "Do not redo" ban is RELEASED as a legitimate ALTERNATIVE target only if this iteration's fix proves insufficient on re-measurement; not attempted this round.
- Re-proving flag on/off byte-identity (`test_health_watchdog.py`) or re-deriving the pre-receive gap / watchdog write cost — closed (iter-68/a, /b, /c) and binding "Do not redo."
- Arming `TRENDORA_HEALTH_WATCHDOG` for the browser-QA/replay lane's own backend via a `scripts/automation/*` change — iter-69/e named this lever as having provably hit its ceiling after 4 rounds; it needs owner sanction (touching `scripts/automation/*`) or an accepted permanent gap, neither of which this iteration decides.
- The `scripts/automation/browser-qa-phase.sh` one-line ordering-bug fix — owner sign-off still pending.
- The owner's 21-times-asked 2-second-ceiling policy question (long jobs vs. short jobs only) and the cost-sanction decision — human-owned, stay parked; this iteration's fix is agent-owned work that improves the metric under either reading.
- Re-measuring J-07 step 3 (VmPeak margin) or step 4 (memory-pressure abort) — the warm-path code those steps test (`compute_forward_aggregates`, `research.py`, `data_manager.py`'s aggregate compute) is untouched this iteration (only `health.py`/`readiness.py`/`main.py`/the finalize hook's own trigger call change); both carry forward on evidence durability per the established iter-67 precedent.
- Any change to `config.yaml` caps, `project-extensions/host-guard/`, or the HOST-GUARD blocks in the launch scripts — binding "Do not redo," AG-10 envelope untouched.
- Recording the J-05 walkthrough (11 rounds unrecorded) as this iteration's own deliverable — rides along only if a showcase/demo lane runs anyway (rule 7: no evidence-only iteration).
- Touching `_distinct_symbol_count`, `func.max(DailyPrice.date)`, or `func.max(ScannerRun.asof_date)` (the three DB reads in the handler) — not implicated by iter-69's attribution; stay on the request path unchanged.
- iter-33/g (the Regime Lab) and the other long-carried items in iteration-state's history (iter-29/b, iter-31/e, iter-32/f, iter-35/k, iter-36/n, iter-37/o, iter-37/q, iter-39/u, iter-46/az, iter-46/ba, iter-47/bd, iter-47/bf, iter-47/bi, iter-48/bj, iter-57/f, iter-57/l, iter-59/g, iter-59/h, iter-59/k, iter-62/e, iter-62/f, iter-63/a, iter-63/b, iter-63/d, iter-64/b, iter-64/e, iter-64/f, iter-65/b, iter-65/c, iter-65/d, iter-66/b, iter-66/e, iter-66/f, iter-66/g, iter-67/f, iter-67/g, iter-68/d, iter-68/e) — none bear on this iteration's request-path caching fix; left untouched.

## DEFINITION OF DONE

- [ ] TC-1 through TC-8 all hold
- [ ] J-07 step 2's live-warm health-poll acceptance (dev drill + browser-qa lane, phase-grouped) shows zero polls over the 2.0s ceiling and zero non-answers within the poller's 5.0s client timeout this round — TC-3
- [ ] Steps 1/3/4 of J-07 remain as previously scored (step 1 fresh evidence this round; steps 3/4 carried on evidence durability, warm-path code unchanged) — status decided by the evaluator, not this spec
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-06, J-08, J-09 remain green (deterministic replay + LLM fallback) — TC-9
- [ ] No anti-goal violation introduced (AG-3 byte-identical response shape/values, AG-8 no unbounded read added, AG-9/AG-10 untouched)
- [ ] Unit tests pass; no regressions (`test_readiness.py`, `test_health.py`, `test_health_watchdog.py`, `test_data_manager.py`)
- [ ] `reports/perf-budgets.md` correction addendum appended (iter-69/b, iter-69/c) with zero deletions to any prior addendum — TC-8
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-70-dev.md`

## TESTING REQUIREMENTS

- Browser: J-07 (steps 1-2 — the crash-free warm + healthy `/api/health` sequence, measured via `scripts/qa/poll_health.py` throughout a real full-deep-basis forward-aggregate warm, with the resulting breach/non-answer counts grouped by `logs/backend.log`'s own ingest phase windows in the write-up, per iter-69's next-step item 3); regression replay/LLM fallback for J-01, J-03, J-04, J-05, J-06, J-08, J-09.
- Unit/integration: a fixture-backed test proving `GET /api/health`'s served `readiness`/`readiness_detail`/`warmup`/`background_compute`/`preflight` fields are byte-identical to a live `compute_readiness`/`compute_preflight` call taken at the same instant (cache correctness); a cold-start test (no completed tick yet) proving the synchronous fallback still returns a valid, non-empty payload; a concurrency test proving a cache read never blocks on or observes a torn write from an in-flight tick; a test proving a tick that raises degrades to the last-known-good cached value without ever producing a `GET /api/health` 5xx; a test proving `record_verdict_transition` still fires exactly once per genuine verdict change when invoked from the tick.
- Error cases: a background tick whose `compute_readiness`/`compute_preflight` call raises (e.g. DB briefly unreachable, a ledger file missing) must never crash the thread or leave `GET /api/health` serving an undefined/blank value — the cache keeps its last-known-good value and the thread keeps ticking on schedule.

Test-first contract:

- TC-1: given the backend process has just booted and the background readiness-refresh thread has not yet completed its first tick, when `GET /api/health` is polled, then the response is HTTP 200 with a `readiness.state` computed synchronously as the cold-start fallback, matching a direct `compute_readiness(session)` call taken at the same moment.
- TC-2: given the backend is idle (no ingest job running) and the background thread has ticked at least once, when `GET /api/health` is polled 100 times over 60 seconds, then every poll's `readiness`/`readiness_detail`/`warmup`/`background_compute`/`preflight` fields are byte-identical to the last completed background tick's own computed values (proves cache-read, not per-request recompute).
- TC-3: given a real full-deep-basis forward-aggregate warm job is running (exercising `factor_lab_all_warm`), when `scripts/qa/poll_health.py` polls `GET /api/health` once per second throughout (dev drill) and the browser-qa lane runs its own independent J-07 drill, then the union of both drills shows zero polls exceeding 2.0s and zero polls receiving no answer within the poller's 5.0s client timeout, reported grouped by ingest phase per `logs/backend.log`'s own phase windows.
- TC-4: given a data job's finalize hook completes and flips a state (e.g. `awaiting_snapshot` → `ready` on a new benchmark-symbol snapshot), when `GET /api/health` is polled immediately after finalize, then the served `readiness.state` reflects the post-finalize value within one `readiness.refresh_interval_seconds` tick — not the pre-finalize value for a full periodic-tick interval — because the finalize hook triggers an immediate refresh.
- TC-5: given the preflight verdict changes between two consecutive background ticks, when the tick that observes the new verdict runs, then exactly one `record_verdict_transition` entry is appended to the verdict-history log for that transition (same dedup-against-last-recorded-verdict behavior as the pre-iteration per-request call).
- TC-6: given the background refresh thread's tick raises an exception (a simulated DB/ledger read failure), when the NEXT `GET /api/health` request arrives, then it is served the last-known-good cached value with HTTP 200 (never a 5xx or blank field), and the thread's subsequent tick (once the underlying failure clears) resumes normal cache updates.
- TC-7: given `apps/backend/tests/test_health_watchdog.py`'s existing `db_reads_s`/`readiness_s`/`preflight_s` watchdog sub-spans (`TRENDORA_HEALTH_WATCHDOG=1`), when a request hits `GET /api/health` under the new cached-read path, then `readiness_s` and `preflight_s` are near-zero (a cache-dict read, not a `compute_readiness`/`compute_preflight` call) while `db_reads_s` is unaffected — proving the request path no longer performs the DB-bound computation.
- TC-8: given `reports/perf-budgets.md` is append-only, when this iteration's addendum is appended, then it states the corrected record count (83 in-window records, not 3 — iter-69/b) and the corrected scorecard label (`60d`, not `65d` — iter-69/c), and `git diff` for that file shows 0 deletions to any pre-existing line.
- TC-9: given J-01, J-03, J-04, J-05, J-06, J-08, J-09's deterministic goldens, when replayed against this iteration's built tree, then all seven remain `passing`/`already_passing` with fresh, byte-distinct evidence frames (md5-checked) and no journey moves to `failing`.

## NOTES

- If TC-3's phase-grouped result still shows breaches concentrated in `factor_lab_all_warm` after this fix, the RELEASED (not banned) alternative — bounding that phase by code change — becomes the next iteration's target; report the residual honestly rather than rounding toward "fixed" (this session's standing discipline, iter-63/65/66/67/68/69).
- Per rule 5, this iteration carries exactly ONE risky change: the readiness/preflight request-path-to-cache redesign. The `reports/perf-budgets.md` corrections and the phase-grouped reporting requirement are mechanical/write-up items, not a second risky code change.
- The owner's three still-open questions (2s-ceiling policy for long jobs, the `browser-qa-phase.sh` sign-off, the cost sanction on real-ingest rounds) are unaffected by this iteration's scope — the fix improves the measured metric under either reading of the ceiling policy, and this iteration piggybacks its live-warm drill on the SAME mandatory ingest J-01/J-03/J-05 replay coverage already needs, rather than launching a second one.
- The assumption-ledger entry for this iteration (`assumptions.md`, iter-70) documents the in-process-cache-vs-persisted-table interpretation call; it is reversible without touching the canonical producer/endpoint again if a future round needs to promote the cache to a persisted table.
