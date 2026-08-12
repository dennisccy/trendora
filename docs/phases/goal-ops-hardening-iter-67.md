# Goal Iteration 67 — Watch the live serving process during `factor_lab_all_warm`, run an idle-control drill, fix three small iter-66 write-up defects

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 67
- **Mode:** next
- **Depth:** lean
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

Directly observe, from inside the live serving process while a real `factor_lab_all_warm` job runs, whether `GET /api/health` requests actually wait on the ASGI event loop / GIL during that phase — with a cheap idle-control drill settling whether the phase specifically or the process merely being busy at all is the cause — while correcting three small write-up defects from the round that produced the correlation (iter-66/a, iter-66/c, iter-66/d).

## BACKGROUND

The evaluator's depth recommendation for this iteration is **lean**, and it is binding: the prior verdict (iter-66) was CONTINUE, not ESCALATE/REGRESSION; iter-66's own coherence pass is COHERENCE-PASS; "Consecutive lean iterations dispatched: 3" is nowhere near the 6-iteration hardening cadence; and this iteration lands no new user-visible capability or brand-new full-stack journey — it adds an env-flag-gated diagnostic probe with zero default-path behavior change. No full trigger holds; needing tests is never a valid trigger, and this scope has a nameable blast radius (`app/api/health.py`'s middleware chain plus one new diagnostic log writer).

iter-66's own drill aligned 68 of its 70 health-poll breaches to `factor_lab_all_warm` (15.7% of the 433 polls taken during it) with ZERO breaches in the 382 polls immediately after it closed — overturning iter-65's four-profile "no further hold" finding for that exact phase. But the METHOD that produced both of the session's two most recent null results (iter-65 on `factor_lab_all_warm`, iter-66 on `coverage_membership_timeline_refresh`) was the same in both cases: re-running the suspect compute chain in a **standalone script**, isolated from the real concurrent load a live serving process experiences. iter-66's own next-step recommendation is explicit that repeating that method a third time has low expected value and orders a genuinely different one instead: **watch the live serving process** — "an in-app watchdog timing how long a health request waits before it is served" — plus **one idle-control drill** (same host, same script, no job at all) to test whether an idle machine also breaches, which is "the cheap test that decides the contention question the load column was meant to answer." This iteration builds exactly that instrument and runs exactly that drill pair; it deliberately does NOT re-profile either phase in a standalone script again (binding "Do not redo," iteration-state.md) and does NOT attempt to bound `factor_lab_all_warm`'s code this round — a fix is premature before the live-process instrument has named (or failed to name) an exact wait component, mirroring this session's own repeated "profile before bounding" discipline (iter-52/53, iter-65, iter-66).

Lessons applied: (iter-66) two traps — `dev.log`/`logs/backend.log` timestamps are host-local BST while every CSV/DB row is UTC (the browser-QA lane's own cross-check this round was wrong by exactly one hour, iter-66/d), and a newly added metric (`load_avg_1m`) can refute the theory it was added to support unless BOTH groups' values are compared, not just cited (iter-66/b's pattern — this iteration's TESTING REQUIREMENTS make the two-group comparison a checked step, TC-4). (iter-63) recount any latency claim from the raw CSV as a full distribution, never a single-poll headline. (iter-64) open the evidence artifact directly rather than trusting a prose summary of it — applies to reading `logs/health-watchdog.jsonl` and `tc1-health-poll.csv` directly, not a write-up's characterization of them.

Per priority rubric rule 6, this iteration does not touch either OWNER-gated item (the 18-times-asked 2-second-ceiling policy question; the `browser-qa-phase.sh` ordering fix; the replay-lane cost sanction) — all three stay parked in NOTES/OUT OF SCOPE, unanswered again this round. Per rule 5, this iteration carries exactly ONE risky action — the env-flag-gated health-watchdog instrumentation add (additive, zero behavior change when the flag is unset); the idle-control drill and the three write-up corrections (iter-66/a, iter-66/c, iter-66/d) are cheap/mechanical/investigative, not a second risky change.

Cost discipline: the live-job half of this iteration's drill piggybacks on the SAME live ingest this session already runs every round for its mandatory J-01/J-03/J-05 replay coverage, rather than launching a second one; the idle-control drill runs no job at all (a few minutes of `scripts/qa/poll_health.py` against an otherwise-idle already-warm backend), so this round's total live-ingest count does not increase — the owner's still-open cost-sanction question is not made worse by this scope.

## IN SCOPE

### Backend
- [ ] Add an optional, env-flag-gated health-request-wait watchdog around the existing `GET /api/health` route (`app/api/health.py`): at the top of the middleware/dispatch chain, record `t_received` (a high-resolution monotonic + wall-clock UTC timestamp pair) before any routing; inside the route handler body, record `t_handler_start` before the readiness computation runs. Compute `queue_wait_s = t_handler_start - t_received` per request.
- [ ] Add a periodic in-process event-loop-lag probe (an asyncio task sleeping a fixed short interval, e.g. 0.1s, comparing actual vs. expected wake time) that runs on the SAME event loop the health route is served from.
- [ ] Gate BOTH additions behind a new env var, `TRENDORA_HEALTH_WATCHDOG=1` (unset/`0` = today's exact behavior, no timestamps recorded, no probe task started, zero added overhead on the default path). Write watchdog samples (queue-wait records and loop-lag records, both UTC-timestamped) as JSON lines to a new file, `logs/health-watchdog.jsonl`.
- [ ] `app.engine.readiness`'s computed value and `GET /api/health`'s response body/shape are byte-identical whether the flag is set or unset — the watchdog observes timing only, never alters what is computed or returned.
- [ ] Add a unit test asserting: (a) with the flag unset, no `logs/health-watchdog.jsonl` entries are written and the route's response is unchanged; (b) with the flag set, a request produces exactly one queue-wait record with `queue_wait_s >= 0`; (c) the loop-lag probe writes at least N records over a short synthetic interval.

### Live drills (dev evidence, piggybacked / cheap — no product-code risk)
- [ ] **Live-job drill:** with `TRENDORA_HEALTH_WATCHDOG=1` set, run this session's already-mandatory live finalize-tail ingest (the one that exercises `factor_lab_all_warm`) while `scripts/qa/poll_health.py` polls `GET /api/health` once per second throughout. Join the resulting `tc1-health-poll.csv` against `logs/health-watchdog.jsonl` by UTC timestamp; for every 2.0s-breaching poll, report the nearest `queue_wait_s`/`loop_lag_s` sample(s) within ±1s.
- [ ] **Idle-control drill:** same host, same `TRENDORA_HEALTH_WATCHDOG=1` + `scripts/qa/poll_health.py`, run for ≥5 minutes against the SAME already-warm backend with NO job running. Report this drill's own breach count/rate and `queue_wait_s`/`loop_lag_s` distribution.
- [ ] Report, honestly, whether the live-job drill's breaches correlate with elevated `queue_wait_s`/`loop_lag_s` (naming the exact wait component) or not (a third null result, disclosed plainly rather than rounded toward a conclusion) — mirrors iter-65/66's own null-result discipline.

### Documentation / write-up corrections (mechanical, not product code)
- [ ] Correct `reports/perf-budgets.md` Addendum 32's phase attribution for the breach iter-66/c placed in the wrong phase — re-derive the correct phase from each breach's own UTC timestamp against `dev.log`'s phase lines (converted from host-local BST, per iter-66/d) and state it plainly.
- [ ] Correct the browser-QA lane's cross-check note from iter-66 (iter-66/d, the one-hour timezone error) — restate the corrected phase window and job identity in the SAME artifact, with the UTC conversion shown explicitly.
- [ ] This iteration's own dev handoff states the whole-run breach count and rate (e.g., "N of M polls over 2.0s, X%") in its FIRST/summary paragraph, not only in a later addendum — closes iter-66/a's pattern for THIS round's own write-up.
- [ ] Any host-load-based explanation this round's write-up offers states BOTH the breaching-poll group's and the non-breaching-poll group's `load_avg_1m` mean/min/max side by side before drawing a conclusion — closes iter-66/b's pattern.

### Frontend
- None. No `apps/frontend/*` file is touched this iteration.

### New user-facing capability
None — this iteration adds diagnostic instrumentation (off by default) to observe an already-shipped guarantee (the app stays responsive during a heavy background job); it does not change what any user sees or can do.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
No visible change to any page. The global readiness badge and `/backtest`'s per-horizon evidence answer exactly as they do today; `TRENDORA_HEALTH_WATCHDOG` is unset in normal operation and changes nothing a user can observe.

### Blueprint conformance
No new page/route/nav entry. This work lives entirely under the blueprint's existing "J-07 — Heavy aggregates never take the service down" home (global readiness badge + `/backtest`) and reads/serves the already-registered "Backend readiness / boot phase" Data Contract row unchanged (`runs/goal-session-ops-hardening/state/blueprint.md`). `blueprint.md` already carries an additive iter-67 narrative note (appended before the Information Architecture section) — no row, computing module, or endpoint changes.

### Data-contract additions
None. `app.engine.readiness` keeps its existing single computing module and `GET /api/health` its existing single serving endpoint — the watchdog's own unit test exists specifically to prove the computed value and response shape are byte-identical with the flag on or off. `logs/health-watchdog.jsonl` and `scripts/qa/poll_health.py` are QA/diagnostic artifacts, not served or displayed values, per this session's standing iter-18/23/33/39/42/66 precedent that pipeline/QA-tooling scripts and logs are not Data Contract rows.

## OUT OF SCOPE

- Any code change to `compute_factor_lab_all_warm`, `coverage_membership_timeline_refresh`, or their call chains — this iteration is diagnostic only; a bound (if the watchdog names an exact wait component) is the NEXT iteration's work, not this one's, per this session's own profile-before-bound discipline.
- Re-running either suspect compute chain in a standalone script — binding "Do not redo" (iteration-state.md): two consecutive null results from that exact method.
- The owner's 18-times-asked 2-second-ceiling policy question (long jobs vs. short jobs only) — human-owned, stays parked.
- The `scripts/automation/browser-qa-phase.sh` line-286-before-272 ordering fix — owner sign-off still pending.
- The cost-sanction decision on the replay lane's real ~17-20 minute ingest every round — owner-gated; this iteration's live-job drill piggybacks on the same job it already needs to trigger rather than adding a second one, and the idle-control drill runs no job at all.
- The J-05 walkthrough capture (unrecorded for 8 rounds) — rides along only if a showcase/demo lane happens to run; not this iteration's own goal.
- iter-66/e (a results-row claim not matching its own screenshot) and iter-66/f (a review summary that omitted a missed acceptance bar) — ledger entries for a different agent's write-up discipline, not a code or instrumentation fix this iteration can make; left open on the ledger.
- iter-66/g (a sixth consecutive over-budget round) — a cost-tracking observation, not an action item; carried to the owner's still-open cost-sanction question above.
- iter-33/g (the Regime Lab) and the other long-carried items in iteration-state's history (iter-29/b, iter-31/e, iter-32/f, iter-35/k, iter-36/n, iter-37/o, iter-37/q, iter-39/u, iter-46/az, iter-46/ba, iter-47/bd, iter-47/bf, iter-47/bi, iter-48/bj, iter-57/f, iter-57/l, iter-59/g, iter-59/h, iter-59/k, iter-62/e, iter-62/f, iter-63/a, iter-63/b, iter-63/d, iter-64/b, iter-64/e, iter-64/f, iter-65/b, iter-65/c, iter-65/d) — none bear on this iteration's diagnostic scope; left untouched.

## DEFINITION OF DONE

- [ ] Target journey J-07 re-verified via the canonical health-poll drill (TC-1/TC-2/TC-3) plus the new watchdog correlation report and browser-qa; status decided by the evaluator, not this spec
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-06, J-08, J-09 remain green (deterministic replay + LLM fallback)
- [ ] No anti-goal violation introduced (AG-3 byte-identity of the readiness value/response shape, AG-8 resilience/no-unbounded-load, AG-9 offline-deterministic ingest, AG-10 host caps all hold)
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-67-dev.md`, with the whole-run breach count/rate stated in its first/summary paragraph (TC-6)

## TESTING REQUIREMENTS

- Browser: J-07 (steps 1-2, the crash-free warm + healthy `/api/health` sequence, measured via `scripts/qa/poll_health.py` with `TRENDORA_HEALTH_WATCHDOG=1` set on the backend launch); regression replay/LLM fallback for J-01, J-03, J-04, J-05, J-06, J-08, J-09
- Unit/integration: the watchdog's flag-off/flag-on/loop-lag-probe test (backend); a byte-identity test proving `GET /api/health`'s computed value and response shape are unchanged whether the flag is set or unset
- Error cases: with the flag set, a request to `/api/health` that itself errors (e.g. a readiness-computation exception) must still be logged with whatever `t_received`/`t_handler_start` samples were captured before the error — the watchdog must never suppress, delay, or alter the route's own error response (AG-8: never a wedge)

Test-first contract:

- TC-1: given a live backend process launched with `TRENDORA_HEALTH_WATCHDOG=1` running the mandatory finalize-tail live ingest that exercises `factor_lab_all_warm`, when `scripts/qa/poll_health.py` polls `GET /api/health` once per second throughout, then `logs/health-watchdog.jsonl` contains a `queue_wait_s` record for every poll whose UTC timestamp falls inside `factor_lab_all_warm`'s own logged start→end window (converted from `logs/backend.log`'s host-local BST timestamp to UTC) — no missing sample inside the window.
- TC-2: given the SAME live-job drill's `tc1-health-poll.csv` and `logs/health-watchdog.jsonl`, when every 2.0s-breaching poll is joined against its nearest watchdog sample(s) within ±1s, then the report states, per breach, the matched `queue_wait_s`/`loop_lag_s` value(s) and whether they are elevated relative to the drill's own non-breaching-window baseline — a positive correlation names the exact wait component; a null result is reported as a null result, not rounded toward "fixed" or "explained."
- TC-3: given one idle-control drill (same host, same `scripts/qa/poll_health.py` + `TRENDORA_HEALTH_WATCHDOG=1`, NO ingest job running, ≥5 minutes), when compared against the live-job drill's numbers, then the report states the idle drill's own breach count, breach rate, and `queue_wait_s`/`loop_lag_s` distribution (p50/p90/p99/max) alongside the live-job drill's equivalent numbers, settling whether breaches occur with no job running at all.
- TC-4: given this round's own `tc1-health-poll.csv` breaching and non-breaching polls, when their `load_avg_1m` values are grouped by breach/non-breach, then the report states BOTH groups' mean/min/max side by side before drawing any host-contention conclusion — no single-value citation stands alone as evidence (closes iter-66/b's pattern).
- TC-5: given `reports/perf-budgets.md` Addendum 32's existing phase attribution, when re-derived using each breach's own UTC timestamp compared against `dev.log`'s phase lines correctly converted from host-local BST, then the corrected addendum states the right phase for every breach, including the one iter-66 misplaced (iter-66/c), and the browser-QA lane's cross-check note is corrected to the right UTC window and job identity (iter-66/d).
- TC-6: given this iteration's own dev handoff, when its summary/opening section is written, then it states the whole-run breach count and rate (e.g., "N of M polls over 2.0s, X%") in the FIRST paragraph a reader reaches — not only in a later addendum (closes iter-66/a's pattern).
- TC-7: given the watchdog's env-flag gate, when a request hits `GET /api/health` with `TRENDORA_HEALTH_WATCHDOG` unset, then no `logs/health-watchdog.jsonl` entry is written for it and its response body/status is byte-identical to the pre-iteration behavior (fixture-backed equality test).
- TC-8: given J-01, J-03, J-04, J-05, J-06, J-08, J-09's deterministic goldens, when replayed against this iteration's built tree, then all seven remain `passing`/`already_passing` with fresh, byte-distinct evidence frames (md5-checked) and no journey moves to `failing`.

## NOTES

- If the watchdog correlation (TC-1/TC-2) DOES name an elevated `queue_wait_s`/`loop_lag_s` component during `factor_lab_all_warm`, that is the exact target the NEXT iteration bounds — do not attempt the bound this round; this round's job is to name it, not fix it.
- If the watchdog correlation finds NOTHING elevated even while watching the live process — a third consecutive null result across three different methods on two different phases — say so plainly in the dev handoff's first paragraph, alongside the idle-control drill's own numbers; the evaluator, not this spec, decides what that pattern means for J-07's status and next steps.
- Owner's 2-second-ceiling policy question (asked 18 times) is orthogonal to this iteration's work: under either reading (long jobs vs. short jobs only), localizing the exact wait component is real diagnostic progress, not wasted effort.
- Per the priority rubric's rule 5, this iteration carries exactly ONE risky change (the env-flag-gated watchdog instrumentation add) — the idle-control drill and the three write-up corrections (TC-4, TC-5, TC-6) are cheap/mechanical/investigative, not a second risky code change.
- An interpretation call was made on the watchdog's exact implementation (ASGI-layer timestamp pair + event-loop-lag probe, rather than thread-stack interrupt sampling or a full tracing tool) — logged at `runs/goal-session-ops-hardening/state/assumptions.md` (iter-67 entry).
