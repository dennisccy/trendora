# Goal Iteration 68 — Time the health handler's own body, run the skipped test module, and fix two iter-67 write-up defects

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 68
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

Extend the live health-watchdog with a third timing sample around the handler body's own compute (the ~2.55 s of the one recorded breach that neither `queue_wait_s` nor `loop_lag_s` explains), run the previously-skipped `test_health.py` module, correct two disclosed iter-67 write-up defects (a misattributed loop-lag sample and a distribution conclusion that omits its own phase-level evidence), and unify the browser-QA lane onto the canonical poll script.

## BACKGROUND

The evaluator's depth recommendation is **lean and binding**: iter-67's verdict was CONTINUE (not ESCALATE/REGRESSION), its coherence pass was COHERENCE-PASS (not FAIL), consecutive lean iterations dispatched is 4 against a cadence of 6, and this round adds no new user-visible capability or brand-new full-stack journey — one more additive, env-flag-gated timing sample plus test/documentation work. No full trigger holds.

J-07 is the only non-passing journey and iter-67's own next-step recommendation (evaluator, iter-67 eval.md) orders exactly this scope: (1) name the handler-body component of the one breach — iter-67's watchdog explained `queue_wait_s` (~11% of the breach) but left ~2.55 s inside the readiness/preflight computation and its DB reads untimed; (2) run `test_health.py`, decoupled from any drill — the module for the exact file this session keeps changing was skipped again this round and the review recorded no issue (iter-67/e); (3) correct two write-up statements — the 1.382 s loop-lag sample belongs to the boot warm-up thread at 03:13:54 Z, not `factor_lab_all_warm` (iter-67/a), and the "location moves, so no phase-specific hold" conclusion must also state that `factor_lab_all_warm` still holds 120 of 131 polls over 1.0 s (iter-67/b); (4) put one stopwatch in every lane — the browser lane reverted to its own curl loop this round after using the canonical script last round (iter-67/c), and separately claimed an unverified code change to `compute_forward_aggregates` (iter-67/d). Per priority rubric rule 3 (unblockers) J-07 remains the target since it is the session's only open journey; per rule 4 this is the smallest available increment (one more additive sample type on an existing, already-tested module, plus test/documentation fixes, not a new instrument); per rule 5 the iteration carries exactly one risky action (the `health_watchdog.py` extension); per rule 6 the owner's still-open ceiling question, the `browser-qa-phase.sh` sign-off, and the cost sanction stay parked — none of this round's scope depends on the owner's answer.

Lessons applied: (iter-67, twice) group the FULL sub-threshold distribution by phase before concluding a hold moved or vanished, and re-read a "whole-run max" sample's own timestamp before naming its phase — both drive the two write-up corrections below (TC-5, TC-6). (iter-66) `dev.log`/`logs/backend.log` are host-local BST while every CSV/JSONL/DB row is UTC — the correction must show the conversion explicitly, not just assert the new phase. (Binding "Do not redo," iteration-state.md) never re-run a suspect compute chain in a standalone script — the new sample wraps the LIVE handler body during the same live drill this session already runs, not a fresh standalone profile; never build a second health-poll counter or a second JSONL writer — the new sample extends the existing `health_watchdog.py` and writes through the existing `logs/health-watchdog.jsonl`; never re-derive iter-66's already-closed attribution/timezone work (settled, Addendum 33's TC-5 section, untouched here). This iteration does not re-prove the existing byte-identity test (`test_health_watchdog.py:422-443`) — that fact is unaffected because the new sample is written only to the diagnostic log, never to the `GET /api/health` response body.

## IN SCOPE

### Backend
- [ ] Extend `apps/backend/app/engine/health_watchdog.py` with a third sample type, `handler_compute_s`: measured from `t_handler_start` (already recorded, iter-67) to the point immediately before the route returns its response (after readiness/preflight computation and any DB reads, before serialization). Gated behind the SAME existing `TRENDORA_HEALTH_WATCHDOG=1` flag; written to the SAME `logs/health-watchdog.jsonl` via the SAME `app.engine.ledger.append_entry` writer — no second flag, no second writer.
- [ ] Add a unit test asserting: (a) flag unset — no `handler_compute_s` entry is written, response unchanged; (b) flag set — a request to `GET /api/health` produces exactly one `handler_compute_s` record with `handler_compute_s >= 0`, alongside the existing `queue_wait_s` record for the same request.
- [ ] Run `apps/backend/tests/test_health.py` (the existing module for `app/api/health.py`, disclosed-skipped in iter-67's Known Issues) as an ordinary test step this round — not piggybacked on any drill, not skipped. Record its pass/fail result in the dev handoff's first paragraph, whichever it is.

### Live drills (dev evidence, piggybacked / cheap — no product-code risk)
- [ ] **Live-job drill:** with `TRENDORA_HEALTH_WATCHDOG=1` set, run this session's already-mandatory live finalize-tail ingest (the one exercising `factor_lab_all_warm`) while `scripts/qa/poll_health.py` polls `GET /api/health` once per second throughout. Join `tc1-health-poll.csv` against `logs/health-watchdog.jsonl` by UTC timestamp; for every 2.0 s-breaching poll, report the matched `queue_wait_s`, `loop_lag_s`, AND (new) `handler_compute_s` samples, and state what fraction of the breach's total elapsed time each component accounts for.
- [ ] **Idle-control drill:** same host, same flag + `scripts/qa/poll_health.py`, ≥5 minutes against the SAME already-warm backend with NO job running. Report this drill's own `handler_compute_s` distribution (p50/p90/p99/max) alongside the live-job drill's.
- [ ] Report honestly whether `handler_compute_s` accounts for the remaining ~2.55 s the breach's `queue_wait_s`/`loop_lag_s` did not explain, or whether a further gap remains unnamed even after three sample types — a null/partial result is reported as such, not rounded toward "explained."

### Documentation / write-up corrections (mechanical, not product code)
- [ ] Correct `reports/perf-budgets.md` Addendum 33's claim that the drill's whole-run max `loop_lag_s` (1.382 s) was "recorded later during `factor_lab_all_warm`" — restate, with the raw JSONL timestamp shown (03:13:54.529811 Z, ~2 minutes before `factor_lab_all_warm`'s own start) and the phase's own actual max loop-lag (0.240 s across 3,848 samples) stated alongside it, that the 1.382 s sample belongs to the boot warm-up thread's cache-warm window, not `factor_lab_all_warm` (closes iter-67/a).
- [ ] Correct Addendum 33's conclusion that a moving >2.0 s breach location argues against a phase-specific hold — add, in the SAME paragraph, that the FULL >1.0 s distribution still puts 120 of the drill's 131 over-1.0 s polls inside `factor_lab_all_warm` (22.2% of its own 541 polls, mean 0.596 s vs. 0.080 s in the next phase), so the >2.0 s crossing moved but the phase-level signal did not (closes iter-67/b).
- [ ] This iteration's own dev handoff states the whole-run breach count/rate for BOTH the live-job and idle-control drills in its first/summary paragraph (continues the iter-66/a-closed convention).

### Browser-QA lane direction (TESTING REQUIREMENTS lever, not a framework-file edit)
- [ ] Direct the browser-qa-agent's own J-07 test case (via TESTING REQUIREMENTS below) to invoke `scripts/qa/poll_health.py` — the canonical script this session already checked in at iter-66 — rather than an ad hoc curl/subprocess loop, and to write its polling-window claim only from the script's own start/end timestamps (no gap-spanning "observed continuously" language unless the polling was in fact continuous). This is the second consecutive round making this direction explicit in the spec (iter-66's assumption-ledger entry chose the TESTING-REQUIREMENTS lever over a framework-instruction edit; iter-67's lane reverted anyway) — if the browser lane again does not use the canonical script this round, that fact belongs in the next evaluator's ledger as a THIRD occurrence, not silently repeated.
- [ ] The browser lane's own report states only code changes it directly confirmed from the diff (e.g. `git diff -- apps/backend/app/engine/research.py apps/backend/app/engine/data_manager.py`), never an inferred or assumed change (closes iter-67/d's pattern for this round).

### Frontend
- None. No `apps/frontend/*` file is touched this iteration.

### New user-facing capability
None — this iteration extends diagnostic instrumentation (off by default) and corrects documentation/test coverage; it does not change what any user sees or can do.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
No visible change to any page. The global readiness badge and `/backtest`'s per-horizon evidence answer exactly as they do today; `TRENDORA_HEALTH_WATCHDOG` is unset in normal operation and changes nothing a user can observe.

### Blueprint conformance
No new page/route/nav entry. This work lives entirely under the blueprint's existing "J-07 — Heavy aggregates never take the service down" home (global readiness badge + `/backtest`) and reads/serves the already-registered "Backend readiness / boot phase" Data Contract row unchanged (`runs/goal-session-ops-hardening/state/blueprint.md`). An additive iter-68 narrative note has been appended to the blueprint (before the Information Architecture section) describing this iteration's scope — no row, computing module, or endpoint changes.

### Data-contract additions
None. `app.engine.readiness` keeps its existing single computing module and `GET /api/health` its existing single serving endpoint. `handler_compute_s` is written only to `logs/health-watchdog.jsonl` (a QA/diagnostic artifact, per the session's standing iter-18/23/33/39/42/66/67 precedent), never to the `GET /api/health` response body — the existing byte-identity test already proves the response is unaffected by the watchdog flag, and this iteration adds no new field to that response.

## OUT OF SCOPE

- Any code change to `compute_factor_lab_all_warm`, `coverage_membership_timeline_refresh`, or their call chains — still diagnostic-only work; a bound (if the full three-sample instrument ever names an exact wait component with a fix shape) is a future iteration's work, per this session's own profile-before-bound discipline.
- Re-running any suspect compute chain in a standalone script — binding "Do not redo" (iteration-state.md).
- The owner's 19-times-asked 2-second-ceiling policy question (long jobs vs. short jobs only) — human-owned, stays parked.
- The `scripts/automation/browser-qa-phase.sh` line-286-before-272 ordering fix — owner sign-off still pending.
- The cost-sanction decision on the replay lane's real ~17-20 minute ingest every round — owner-gated; this iteration's live-job drill piggybacks on the SAME live ingest the session already needs to trigger for J-01/J-03/J-05 replay coverage, rather than launching a second one; the idle-control drill runs no job at all.
- The J-05 walkthrough capture (unrecorded for 9 rounds) — rides along only if a showcase/demo lane happens to run; not this iteration's own goal (rule 7: no evidence-only iteration).
- iter-67/f (an instrument that perturbs what it measures without saying so) and iter-67/g (a seventh consecutive over-budget round) — ledger entries about measurement/cost discipline, not a code or instrumentation fix this iteration makes; left open on the ledger, folded into the owner's still-open cost question.
- iter-33/g (the Regime Lab) and the other long-carried items in iteration-state's history (iter-29/b, iter-31/e, iter-32/f, iter-35/k, iter-36/n, iter-37/o, iter-37/q, iter-39/u, iter-46/az, iter-46/ba, iter-47/bd, iter-47/bf, iter-47/bi, iter-48/bj, iter-57/f, iter-57/l, iter-59/g, iter-59/h, iter-59/k, iter-62/e, iter-62/f, iter-63/a, iter-63/b, iter-63/d, iter-64/b, iter-64/e, iter-64/f, iter-65/b, iter-65/c, iter-65/d, iter-66/b, iter-66/e, iter-66/f, iter-66/g) — none bear on this iteration's diagnostic/test/write-up scope; left untouched.

## DEFINITION OF DONE

- [ ] Target journey J-07 re-verified via the canonical health-poll drill pair (TC-1/TC-2/TC-3) plus the completed three-component breach report and browser-qa; status decided by the evaluator, not this spec
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-06, J-08, J-09 remain green (deterministic replay + LLM fallback)
- [ ] No anti-goal violation introduced (AG-3 byte-identity of the readiness value/response shape, AG-8 resilience/no-unbounded-load, AG-9 offline-deterministic ingest, AG-10 host caps all hold)
- [ ] `test_health.py` executed as an ordinary step this round, result recorded (not skipped, not silently absent from the review's issues list) — TC-4
- [ ] `reports/perf-budgets.md` Addendum 33 corrected for iter-67/a and iter-67/b — TC-5, TC-6
- [ ] Browser-QA lane's J-07 test case invokes `scripts/qa/poll_health.py` and reports only its directly-observed polling window and confirmed code diffs — TC-7
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-68-dev.md`

## TESTING REQUIREMENTS

- Browser: J-07 (steps 1-2, the crash-free warm + healthy `/api/health` sequence, measured via `scripts/qa/poll_health.py` with `TRENDORA_HEALTH_WATCHDOG=1` set on the backend launch — the browser-qa-agent MUST use this canonical script, not an ad hoc curl/subprocess loop); regression replay/LLM fallback for J-01, J-03, J-04, J-05, J-06, J-08, J-09
- Unit/integration: the watchdog's new `handler_compute_s` flag-off/flag-on test (backend); `apps/backend/tests/test_health.py` run as an ordinary step (not skipped)
- Error cases: with the flag set, a request to `/api/health` that itself errors (e.g. a readiness-computation exception) must still be logged with whatever `t_received`/`t_handler_start`/partial `handler_compute_s` samples were captured before the error — the watchdog must never suppress, delay, or alter the route's own error response (AG-8: never a wedge)

Test-first contract:

- TC-1: given a live backend process launched with `TRENDORA_HEALTH_WATCHDOG=1` running the mandatory finalize-tail live ingest that exercises `factor_lab_all_warm`, when `scripts/qa/poll_health.py` polls `GET /api/health` once per second throughout, then `logs/health-watchdog.jsonl` contains a `handler_compute_s` record (alongside the existing `queue_wait_s` record) for every poll whose UTC timestamp falls inside the drill window — no missing sample.
- TC-2: given the SAME live-job drill's `tc1-health-poll.csv` and `logs/health-watchdog.jsonl`, when every 2.0 s-breaching poll is joined against its nearest `queue_wait_s`/`loop_lag_s`/`handler_compute_s` samples within ±1 s, then the report states each component's share of the breach's total elapsed time, and whether the three together account for the breach or a residual gap remains — a null/partial result is reported as such.
- TC-3: given one idle-control drill (same host, `TRENDORA_HEALTH_WATCHDOG=1`, no job running, ≥5 minutes), when compared against the live-job drill's `handler_compute_s` distribution, then the report states both drills' p50/p90/p99/max side by side.
- TC-4: given `apps/backend/tests/test_health.py` (skipped in iter-67, disclosed in that round's Known Issues), when run this round as an ordinary test step, then its pass/fail result is stated in the dev handoff's first paragraph and, if it fails, the review's `issues` list names it — never `issues: []` over a skipped or failing module for the file this iteration changed.
- TC-5: given `reports/perf-budgets.md` Addendum 33's claim that the 1.382 s max `loop_lag_s` sample was "recorded later during `factor_lab_all_warm`", when re-derived from the raw JSONL's own timestamp (03:13:54.529811 Z) compared against `factor_lab_all_warm`'s logged start time, then the corrected addendum states the sample belongs to the boot warm-up thread's cache-warm window (~2 minutes before the phase opened) and states the phase's own actual max loop-lag (0.240 s) — closes iter-67/a.
- TC-6: given Addendum 33's conclusion that the moving >2.0 s breach location argues against a phase-specific hold, when the full >1.0 s distribution is regrouped by phase from the same CSV, then the corrected write-up states BOTH the moving->2.0s-crossing observation AND `factor_lab_all_warm`'s 120-of-131-over-1.0s-polls share (22.2% of its own 541 polls) in the same paragraph — closes iter-67/b.
- TC-7: given the browser-qa-agent's own J-07 test case execution, when it produces its polling CSV/report, then the CSV's schema matches `scripts/qa/poll_health.py`'s canonical columns (not a separate ad hoc curl-loop schema) and the report's stated polling window matches the script's own start/end timestamps with no unstated gap, and any code-change claim in the report is backed by a cited `git diff` line — closes iter-67/c and iter-67/d.
- TC-8: given the watchdog's env-flag gate, when a request hits `GET /api/health` with `TRENDORA_HEALTH_WATCHDOG` unset, then no `handler_compute_s` (or any watchdog) entry is written for it and its response body/status is byte-identical to the pre-iteration behavior.
- TC-9: given J-01, J-03, J-04, J-05, J-06, J-08, J-09's deterministic goldens, when replayed against this iteration's built tree, then all seven remain `passing`/`already_passing` with fresh, byte-distinct evidence frames (md5-checked) and no journey moves to `failing`.

## NOTES

- If the three-sample instrument (queue-wait + loop-lag + handler-compute) together account for the breach's full elapsed time, that is the first complete positive attribution in this session's J-07 work — the evaluator, not this spec, decides what that means for J-07's status. If a residual gap remains even after all three, say so plainly rather than rounding toward "explained."
- Owner's 2-second-ceiling policy question (asked 19 times) is orthogonal to this iteration's work: under either reading (long jobs vs. short jobs only), completing the breach's time-budget attribution is real diagnostic progress, not wasted effort.
- Per the priority rubric's rule 5, this iteration carries exactly ONE risky change (the `health_watchdog.py` third-sample extension) — running `test_health.py`, the two write-up corrections, and the browser-lane stopwatch/claim direction are mechanical/investigative/test-execution, not a second risky code change.
- If the browser-QA lane again does not adopt `scripts/qa/poll_health.py` this round despite this being the second consecutive spec directing it, that is itself a finding for the next evaluator to weigh (a spec-level lever with a demonstrated ceiling on effectiveness) — not silently repeated a third time without comment.
