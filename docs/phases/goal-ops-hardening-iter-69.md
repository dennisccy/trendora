# Goal Iteration 69 — Decompose `handler_compute_s` into its parts, arm the watchdog on the QA lane, and report the pre-receive gap already on disk

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 69
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

Split the existing `handler_compute_s` health-watchdog sample into its three constituent spans (DB reads, `compute_readiness`, `compute_preflight`), arm the watchdog on the browser-QA/replay lane's own backend for the first time this session so the lane that has caught the worst breaches finally records their components, and report the pre-receive gap that is already recoverable from artifacts this session already produces — with zero new instrument.

## BACKGROUND

The evaluator's depth recommendation is **lean and binding**: iter-68's verdict was CONTINUE (not ESCALATE/REGRESSION), its coherence pass was COHERENCE-PASS (not FAIL), consecutive lean iterations dispatched entering this round is 5 against a cadence of 6 (not yet met), and this round adds no new user-visible capability or brand-new full-stack journey — one more additive, env-flag-gated sub-timing plus a same-artifacts analysis pass. No full trigger holds.

J-07 is the only non-passing journey and iter-68's own next-step recommendation (evaluator, iter-68 eval.md) orders exactly this scope: (1) split `handler_compute_s` into its parts — the handler body does three DB reads (`func.max(DailyPrice.date)`, `_distinct_symbol_count`, `func.max(ScannerRun.asof_date)`), `compute_readiness`, and `compute_preflight`; time each with the SAME flag, writer, and file — the first target in this session that is a specific piece of the project's own code rather than a phase name; (2) arm `TRENDORA_HEALTH_WATCHDOG=1` for the whole iteration, including the replay/browser lane's own backend, so the lane that has caught this session's worst breaches (9 of the round's 10, per iter-68's own union count) finally records their components (closes iter-68/d); (3) report the pre-receive gap from artifacts already produced — the poller's own send timestamp vs. `t_received_wall` — no new instrument, closing most of the "unnamed 19.6%" (iter-68/b, itself printed but never converted into a share in Addendum 34); (4) two small write-up items — iter-68/a (a results row calling an all-`n=0` forward-test scorecard "the full" scorecard) and iter-68/c (state that the watchdog's own second synchronous write sits inside the time it does not measure). Per priority rubric rule 3 (unblockers) J-07 remains the target since it is the session's only open journey; per rule 4 this is the smallest available increment (three named sub-spans of an already-existing, already-tested sample, plus a same-artifacts join, not a new instrument); per rule 5 the iteration carries exactly one risky action (the `health_watchdog.py` extension, itself additive and flag-gated); per rule 6 the owner's still-open ceiling question, the `browser-qa-phase.sh` sign-off, and the cost sanction stay parked — none of this round's scope depends on the owner's answer.

Lessons applied: (iter-68, twice) before commissioning a new instrument, join the instruments already on disk — this iteration's pre-receive-gap item is exactly that: differencing `scripts/qa/poll_health.py`'s own send timestamp against `logs/health-watchdog.jsonl`'s `t_received_wall`, no new code; and the instrument was armed on only one lane last round, so the browser lane's 9 worst breaches carry no attribution — this iteration's item 2 is the direct fix attempt. (iter-67, twice) group the FULL sub-threshold distribution by phase, and re-read a "whole-run max" sample's own timestamp before naming its phase — both remain settled (Addendum 34) and are not re-derived here. (Binding "Do not redo," iteration-state.md) never re-run a suspect compute chain in a standalone script — the three new sub-spans wrap the LIVE handler body during the same live drill this session already runs; never build a second health-poll counter, JSONL writer, or env flag — the three sub-spans extend the EXISTING `handler_compute` record type through the EXISTING `health_watchdog.py`/`logs/health-watchdog.jsonl`/`TRENDORA_HEALTH_WATCHDOG`; never bound `factor_lab_all_warm` / `coverage_membership_timeline_refresh` by code change — this iteration adds sub-timing only, it does not bound anything.

## IN SCOPE

### Backend
- [ ] Extend `apps/backend/app/engine/health_watchdog.py`'s `record_handler_compute` (or an equivalent internal helper it calls) to additionally record three named sub-spans inside the SAME `handler_compute` record type, written through the SAME `TRENDORA_HEALTH_WATCHDOG=1` flag and the SAME `logs/health-watchdog.jsonl` writer (`app.engine.ledger.append_entry`) — no second flag, no second writer, no second record type: `db_reads_s` (wall time across the three existing reads `func.max(DailyPrice.date)`, `_distinct_symbol_count(session)`, `func.max(ScannerRun.asof_date)` in `apps/backend/app/api/health.py`), `readiness_s` (wall time of the `compute_readiness(session, engine=get_engine())` call), `preflight_s` (wall time of the `compute_preflight(session, config=cfg)` call, including its own existing nested `record_verdict_transition` write — do not separate that out into a fourth span this round).
- [ ] `db_reads_s + readiness_s + preflight_s` must be internally consistent with the existing `handler_compute_s` total for the SAME request (the three sub-spans partition the same measured window; no unaccounted time between spans beyond negligible instrumentation overhead).
- [ ] Add/extend a unit test asserting: (a) flag unset — no `handler_compute` entry (with or without the new sub-fields) is written, response byte-identical; (b) flag set — a request to `GET /api/health` produces exactly one `handler_compute` record whose `db_reads_s`, `readiness_s`, `preflight_s` are each `>= 0` and whose sum equals the record's own `handler_compute_s` within a small fixed tolerance (e.g. 1ms), alongside the existing `queue_wait_s` record for the same request.
- [ ] No change to `GET /api/health`'s response body/shape — the three new sub-fields are diagnostic-log-only, mirroring the existing treatment of `queue_wait_s`/`loop_lag_s`/`handler_compute_s`.

### Live drills (dev evidence, piggybacked / cheap — no product-code risk)
- [ ] **Live-job drill:** with `TRENDORA_HEALTH_WATCHDOG=1` set, run this session's already-mandatory live finalize-tail ingest (the one exercising `factor_lab_all_warm`) while `scripts/qa/poll_health.py` polls `GET /api/health` once per second throughout. Join `tc1-health-poll.csv` against `logs/health-watchdog.jsonl` by UTC timestamp; for every 2.0 s-breaching poll (if any occurs this round), report the matched `db_reads_s`, `readiness_s`, and `preflight_s` shares of the breach's total elapsed time, naming whichever sub-component dominates. If no breach occurs this round, report that plainly (a null result, not rounded toward "fixed").
- [ ] **Idle-control drill:** same host, same flag + `scripts/qa/poll_health.py`, ≥5 minutes against the SAME already-warm backend with NO job running. Report this drill's own `db_reads_s`/`readiness_s`/`preflight_s` distributions (p50/p90/p99/max) alongside the live-job drill's, for a live-vs-idle comparison per component.
- [ ] **Pre-receive gap (no new instrument):** for both drills, difference `scripts/qa/poll_health.py`'s own per-poll send timestamp against `logs/health-watchdog.jsonl`'s matched `t_received_wall` (already recorded since iter-67) and report the resulting gap's p50/p90/p99/max for both drills; if a >2.0 s breach occurs this round, state that specific poll's own pre-receive share of its total elapsed time. This closes iter-68/b — it recovers most of Addendum 34's "genuinely unnamed ~19.6%" residual using artifacts both drills already produce, no code change.

### Arm the watchdog on the browser-QA/replay lane (TESTING REQUIREMENTS lever, not a framework-file edit)
- [ ] Direct the browser-qa-agent's own J-07 test case (via TESTING REQUIREMENTS below) to export `TRENDORA_HEALTH_WATCHDOG=1` into the environment BEFORE it triggers or relies on any backend (re)start for its own J-07 polling drill this round, then confirm (e.g. by reading back `logs/health-watchdog.jsonl` for entries timestamped inside its own polling window) that the flag was in fact live for its lane, not just the dev's own drill — closing iter-68/d (the lane that caught the round's 9 worst breaches ran with the timer off). If it inherits an already-running backend it cannot restart without disrupting other journeys' evidence this round, it must name that constraint explicitly in its own report rather than silently posting zero-attribution breaches a fourth consecutive round.
- [ ] No change to `scripts/automation/browser-qa-phase.sh` or any other `scripts/automation/*` file — the one-line ordering-bug fix stays owner-gated per prior rounds; this item is a spec-level direction to the executing agent only.

### Documentation / write-up (mechanical, not product code)
- [ ] Add a new dated section to `reports/perf-budgets.md` (Addendum 35) reporting: the `db_reads_s`/`readiness_s`/`preflight_s` breakdown from both drills; the pre-receive-gap distribution from both drills; and whether the three sub-spans plus the pre-receive gap together account for the whole of any breach observed this round (or state plainly that no breach occurred).
- [ ] Correct the browser-QA/showcase results write-up that called an all-`n=0` per-horizon Forward-test scorecard "the full forward-test scorecard" (iter-68/a, the second occurrence of the iter-66/e pattern): the corrected wording states the scorecard rendered its own honest "no elapsed forward window yet — no numbers fabricated" empty state, not a populated scorecard.
- [ ] Add one sentence (to Addendum 35 or the module's own docstring) stating that `health_watchdog.py`'s two synchronous JSONL writes per watched request (`record_queue_wait`, `record_handler_compute`) each cost their own real wall-clock time that falls OUTSIDE the window each write measures — since the write happens after its own stop-timestamp is captured — so end-to-end client-observed latency can exceed the sum of the recorded components by that (small, unmeasured) amount (closes iter-68/c).

### Rides along, not this iteration's goal (rule 7 — no evidence-only iteration)
- [ ] IF a showcase/demo lane runs this round anyway, it captures J-05's forward-aggregate walkthrough (unrecorded for 10 rounds) as `[NEW]` steps — this is not this iteration's own deliverable and must not become the reason the round is scored.

### Frontend
- None. No `apps/frontend/*` file is touched this iteration.

### New user-facing capability
None — this iteration extends diagnostic instrumentation (off by default) and corrects documentation/reporting accuracy; it does not change what any user sees or can do.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
No visible change to any page. The global readiness badge and `/backtest`'s per-horizon evidence answer exactly as they do today; `TRENDORA_HEALTH_WATCHDOG` stays unset in normal operation and changes nothing a user can observe.

### Blueprint conformance
No new page/route/nav entry. This work lives entirely under the blueprint's existing "J-07 — Heavy aggregates never take the service down" home (global readiness badge + `/backtest`) and reads/serves the already-registered "Backend readiness / boot phase" Data Contract row unchanged (`runs/goal-session-ops-hardening/state/blueprint.md`). An additive iter-69 narrative note has been appended to the blueprint (before the Information Architecture section) describing this iteration's scope — no row, computing module, or endpoint changes.

### Data-contract additions
None. `app.engine.readiness` keeps its existing single computing module and `GET /api/health` its existing single serving endpoint. `db_reads_s`/`readiness_s`/`preflight_s` are written only to `logs/health-watchdog.jsonl` (a QA/diagnostic artifact, per the session's standing iter-18/23/33/39/42/66/67/68 precedent), never to the `GET /api/health` response body — the existing byte-identity test already proves the response is unaffected by the watchdog flag, and this iteration adds no new field to that response.

## OUT OF SCOPE

- Any code change to `compute_factor_lab_all_warm`, `coverage_membership_timeline_refresh`, or their call chains — still diagnostic-only work; a bound is a future iteration's work only once a component the sub-timing names has an exact fix shape, per this session's own profile-before-bound discipline.
- Re-running any suspect compute chain in a standalone script — binding "Do not redo" (iteration-state.md).
- The owner's 20-times-asked 2-second-ceiling policy question (long jobs vs. short jobs only) — human-owned, stays parked.
- The `scripts/automation/browser-qa-phase.sh` line-286-before-272 ordering fix — owner sign-off still pending; this iteration's TESTING REQUIREMENTS direction to the browser-qa-agent works around it at the spec level, not by editing the file.
- The cost-sanction decision on the replay lane's real ~17-20 minute ingest every round — owner-gated; this iteration's live-job drill piggybacks on the SAME live ingest the session already needs to trigger for J-01/J-03/J-05 replay coverage, rather than launching a second one; the idle-control drill runs no job at all.
- Making the J-05 walkthrough capture this iteration's own goal — rides along only if a showcase/demo lane happens to run (rule 7: no evidence-only iteration).
- A fourth sub-span separating `record_verdict_transition`'s own write out of `preflight_s` — `preflight_s` includes it this round; if a future round's breakdown shows `preflight_s` dominating, that internal split becomes the next named target, not this one.
- iter-33/g (the Regime Lab) and the other long-carried items in iteration-state's history (iter-29/b, iter-31/e, iter-32/f, iter-35/k, iter-36/n, iter-37/o, iter-37/q, iter-39/u, iter-46/az, iter-46/ba, iter-47/bd, iter-47/bf, iter-47/bi, iter-48/bj, iter-57/f, iter-57/l, iter-59/g, iter-59/h, iter-59/k, iter-62/e, iter-62/f, iter-63/a, iter-63/b, iter-63/d, iter-64/b, iter-64/e, iter-64/f, iter-65/b, iter-65/c, iter-65/d, iter-66/b, iter-66/e, iter-66/f, iter-66/g, iter-67/f, iter-67/g) — none bear on this iteration's diagnostic/reporting scope; left untouched.

## DEFINITION OF DONE

- [ ] Target journey J-07 re-verified via the canonical health-poll drill pair (TC-1/TC-2/TC-3) plus the completed sub-component breach report and browser-qa; status decided by the evaluator, not this spec
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-06, J-08, J-09 remain green (deterministic replay + LLM fallback) — TC-9
- [ ] No anti-goal violation introduced (AG-3 byte-identity of the readiness value/response shape, AG-8 resilience/no-unbounded-load, AG-9 offline-deterministic ingest, AG-10 host caps all hold)
- [ ] `handler_compute_s` decomposed into `db_reads_s`/`readiness_s`/`preflight_s`, unit-tested for both flag states — TC-1, TC-8
- [ ] `TRENDORA_HEALTH_WATCHDOG=1` armed for the browser-QA/replay lane's own backend this round, or the constraint preventing it is named explicitly — TC-4
- [ ] Pre-receive gap reported from existing artifacts, no new instrument — TC-5
- [ ] iter-68/a write-up defect corrected — TC-6
- [ ] iter-68/c write-up note added — TC-7
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-69-dev.md`

## TESTING REQUIREMENTS

- Browser: J-07 (steps 1-2, the crash-free warm + healthy `/api/health` sequence, measured via `scripts/qa/poll_health.py` with `TRENDORA_HEALTH_WATCHDOG=1` exported by the browser-qa-agent itself before it triggers/relies on any backend (re)start for this drill — confirm via `logs/health-watchdog.jsonl` that the flag was live for this lane's own polling window, not just the dev's); regression replay/LLM fallback for J-01, J-03, J-04, J-05, J-06, J-08, J-09
- Unit/integration: the watchdog's new `db_reads_s`/`readiness_s`/`preflight_s` sub-span test (flag-off produces no record; flag-on produces a record whose three sub-fields sum to `handler_compute_s` within tolerance)
- Error cases: with the flag set, a request to `/api/health` that itself errors (e.g. a readiness-computation exception) must still be logged with whatever sub-span samples were captured before the error — the watchdog must never suppress, delay, or alter the route's own error response (AG-8: never a wedge)

Test-first contract:

- TC-1: given a live backend process launched with `TRENDORA_HEALTH_WATCHDOG=1` running the mandatory finalize-tail live ingest that exercises `factor_lab_all_warm`, when `scripts/qa/poll_health.py` polls `GET /api/health` once per second throughout, then `logs/health-watchdog.jsonl` contains a `handler_compute` record carrying `db_reads_s`, `readiness_s`, and `preflight_s` (alongside the existing `handler_compute_s` total) for every poll whose UTC timestamp falls inside the drill window — no missing sample.
- TC-2: given the SAME live-job drill's `tc1-health-poll.csv` and `logs/health-watchdog.jsonl`, when every 2.0 s-breaching poll (if any) is joined against its nearest `handler_compute` record, then the report states each of `db_reads_s`/`readiness_s`/`preflight_s`'s share of the breach's total elapsed time and names whichever sub-component dominates — a null result (no breach this round) is reported as such, not rounded toward "explained."
- TC-3: given one idle-control drill (≥5 minutes, same flag, no job running), when compared against the live-job drill's `db_reads_s`/`readiness_s`/`preflight_s` distributions, then the report states both drills' p50/p90/p99/max for each of the three sub-components side by side.
- TC-4: given `TRENDORA_HEALTH_WATCHDOG=1` exported before the browser-QA/replay lane's own backend (re)start this round, when the browser-qa-agent runs its J-07 polling drill, then `logs/health-watchdog.jsonl` contains `handler_compute` records timestamped inside that lane's own polling window (not only the dev's drill window) — or, if the flag could not be armed for that lane, the report names the constraint explicitly rather than posting zero-attribution breaches with no explanation for a fourth consecutive round.
- TC-5: given the live-job and idle-control drills' `scripts/qa/poll_health.py` CSVs (each row's own send timestamp) and `logs/health-watchdog.jsonl`'s `t_received_wall` for matched requests, when the two are differenced per poll, then the report states the pre-receive gap's p50/p90/p99/max for both drills and, if a breaching poll exists this round, states that poll's own pre-receive share of its total elapsed time — closes iter-68/b.
- TC-6: given the browser-QA/showcase lane's own J-07 evidence write-up naming a per-horizon Forward-test scorecard, when the scorecard's frame shows only `— n=0` placeholder cells, then the results row states the scorecard rendered its honest "no elapsed forward window yet" empty state — never "rendered the full forward-test scorecard" — closes iter-68/a.
- TC-7: given `health_watchdog.py`'s two synchronous JSONL writes per watched request (`record_queue_wait`, `record_handler_compute`), when reporting `handler_compute_s`'s own measured span in Addendum 35, then the write-up states explicitly that each write's own wall-clock cost sits OUTSIDE the window it measures — closes iter-68/c.
- TC-8: given the watchdog's env-flag gate, when a request hits `GET /api/health` with `TRENDORA_HEALTH_WATCHDOG` unset, then no `handler_compute` entry (including the new `db_reads_s`/`readiness_s`/`preflight_s` sub-fields) is written for it, and its response body/status stays byte-identical to pre-iteration behavior.
- TC-9: given J-01, J-03, J-04, J-05, J-06, J-08, J-09's deterministic goldens, when replayed against this iteration's built tree, then all seven remain `passing`/`already_passing` with fresh, byte-distinct evidence frames (md5-checked) and no journey moves to `failing`.

## NOTES

- If the three sub-spans plus the pre-receive gap together account for the whole of any breach observed this round, that is the first fully-closed time budget in this session's J-07 work — the evaluator, not this spec, decides what that means for J-07's status. If a residual gap remains even after all four components, say so plainly rather than rounding toward "explained."
- Owner's 2-second-ceiling policy question (asked 20 times) is orthogonal to this iteration's work: under either reading (long jobs vs. short jobs only), completing the time-budget attribution is real diagnostic progress, not wasted effort.
- Per the priority rubric's rule 5, this iteration carries exactly ONE risky change (the `health_watchdog.py` sub-span extension) — arming the flag on the QA lane, the pre-receive-gap analysis, and the two write-up corrections are additive/investigative/mechanical, not a second risky code change.
- If arming `TRENDORA_HEALTH_WATCHDOG=1` on the browser-QA/replay lane's own backend again fails to produce attributed samples for that lane's polls despite this being the first round explicitly directing it, that is itself a finding for the next evaluator to weigh — it may indicate the spec-level lever has a ceiling here (the lane's backend restart is orchestrated outside any agent's direct control) and that a future round needs an actual `scripts/automation/*`-adjacent fix made with explicit owner awareness, mirroring how iter-66's assumption ledger closed the analogous canonical-script question.
