# Goal Iteration 52 — Chunk the finalize-tail warm loops so `/api/health` never goes unanswered, and close J-04/J-05/J-06/J-07's verification debt

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 52
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — the prior verdict (iter-51) was ESCALATE; full depth is mandatory this
  iteration with no exceptions, per the binding rule.
- **Frontend Present:** no
- **Target journeys:** J-04, J-05, J-06, J-07
- **Required-still-passing journeys:** J-01, J-03, J-08, J-09
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

Stop `GET /api/health` from going fully unanswered while the ingest finalize tail's longest warm phase
runs — chunk the CPU-bound warm loops with cooperative yield points — and get J-04, J-05, J-06, and J-07
each a real, executed check this round, closing verification debt carried for two to three consecutive
iterations.

## BACKGROUND

Prior verdict was ESCALATE (mandatory full depth, no exceptions — Full trigger 3). The iter-51
evaluator's own next-step item (2) names the exact defect and its shape: while the ingest finalize
tail's longest sub-phase runs, `GET /api/health` occasionally returns NO response at all — a true
connection-level non-answer, not merely a slow one. `reports/perf-budgets.md` Item T's own live
measurement (Addendum 11, solo) found 9 of 653 polls hit this failure, clustered entirely inside
`factor_lab_all_warm`'s 583.76s window (the longest phase that particular run); the browser lane's own
concurrent drill (UT-08, 1,435.87s) found 19 of 892 — the same class, but `iteration-state.md`'s digest
generalizes it past that one phase: "attaches to whichever finalize-tail sub-phase is LONGEST, not to
`factor_lab_all_warm`." Per iter-50's binding lesson ("Bounding memory cannot close a responsiveness
requirement... the cause is GIL contention between two CPU-bound Python computes in one process, not
allocation"), the fix is scheduling, not memory: interleave the already-correct computations with
periodic cooperative-yield points so the currently-longest phase periodically cedes the CPU, giving
`/api/health` (and other concurrent requests) a fair chance to be scheduled.

**Priority rubric applied:** no journey regressed since iter-51 (rule 1 N/A — the iter-51 evaluator
explicitly rejected REGRESSION). The last `coherence.md` (iter-51) was COHERENCE-PASS, not FAIL (rule 2
N/A). J-07 is the clear unblocker (rule 3) — it is the journey whose step 2 this defect directly
breaches, and it shares its finalize-tail subsystem with J-05 and J-06 (rule 5: ONE risky code change —
the yield-point scheduling fix — not three; logged to `assumptions.md`, mirroring the iter-50/iter-51
decomposer's own precedent for this exact subsystem). J-04, J-05, J-06 and J-07 are ALL listed as Target
journeys this iteration not because each gets new code, but because closing their shared verification
debt is the evaluator's explicit top priority for a second consecutive round: J-05/J-06/J-07 have zero
executed rows for two rounds running, and J-04 has been skipped for time (DEFERRED-BUDGET) for two
rounds running, last actually checked at iter-49. This is continuation of already-carried targets, not
new scope (self-check item 5) — hence 4 Target journeys rather than the usual 1-3.

**Lessons applied (Applies-to matches):** iter-50's second lesson (GIL contention, not memory) is the
direct grounds for this iteration's fix shape. Iter-51's first lesson (uvicorn access-log lines carry no
timestamp of their own; count per anchor, not by nearest-preceding-line) applies to any log-based
attribution this iteration's drills perform. Iter-51's second lesson (findings-only during audit when
the TC-8/TC-13 lane-runs-last rule is in force) is restated as the binding expectation, not left to the
auditor's judgement (TESTING REQUIREMENTS TC-9, DEFINITION OF DONE). Iter-46/47's lesson on null-test
golden scripts applies to J-05/J-06's existing goldens (`runs/goal-session-ops-hardening/journey-scripts/J-05.json`,
`J-06.json` — present but zero executed rows for two rounds; confirm they actually RUN this time, not
merely exist) and to any freshly-authored J-04/J-07 step (neither has a golden in this session's
`journey-scripts/` directory — LLM-fallback lane for both).

**Resolving a tension, stated plainly:** the iter-51 evaluator's next-step item (1) reads "First, just
check the eight journeys — change no code at all... (2) Then fix the... defect," which taken literally
asks for the full lane to run BEFORE this iteration's own code lands. The standing TC-8/TC-13 sequencing
rule (this session's own binding expectation, iter-51 lesson) has no "pre-dev checkpoint" step — the
lane runs LAST, once, after all code lands. This spec resolves the tension the same way: ONE full
8-journey lane run, at the end, against a tree carrying BOTH this iteration's scheduling fix AND
iter-51's already-landed `factor_lab_all_warm`/`_combination_cohort_members` work — verifying what both
iterations bought in a single pass (`assumptions.md`, iter-52). The load-bearing, non-negotiable part of
item (1) — that J-04/J-05/J-06/J-07 must each get a REAL executed row this round, not be skipped or
zero-rowed a third time — is preserved as a hard DEFINITION OF DONE requirement regardless of which pass
produces it.

**Honest limit, stated up front:** yield points target the CONNECTION-LEVEL non-answer failure directly
(the diagnosed cause). They are not guaranteed to fully close J-07 step 2's ≤2s LATENCY ceiling for
every poll — some residual GIL hand-off latency may remain even once zero polls go fully unanswered —
and the previously-disclosed residual (96/1,179 polls >2s in Item S's concurrent drill, before iter-51's
`factor_lab_all_warm` even existed) may not vanish entirely. Record what is actually measured; do not
round a latency improvement up to full ceiling compliance.

## IN SCOPE

### Backend
- [ ] Add periodic cooperative-yield points inside the CPU-bound per-item loops the ingest finalize tail
  drives directly or calls into: `apps/backend/app/engine/data_manager.py`'s `_refresh_ingest_aggregates`/
  `_persist_per_date_coverage_snapshots` per-date coverage and market-phase warm loops;
  `apps/backend/app/engine/research.py`'s `compute_factor_lab_all` (per-factor/per-horizon loop),
  `_combination_observations`, `_factor_decile_observations`, `_all_factor_observations_by_horizon`;
  `apps/backend/app/engine/forward_testing.py`'s `compute_forward_aggregates` per-horizon loop. Whichever
  sub-phase is currently longest is the one that starves `/api/health` (`iteration-state.md`), so
  coverage must span the whole set, not just `factor_lab_all_warm`. No change to any computed value —
  only interleaving.
- [ ] Add a new throwaway-process fault-injection test (mirrors the existing `spawned_backend_fault_injected`
  pattern already in `apps/backend/tests/test_start_backend_script.py`) that arms
  `TRENDORA_FAULT_INJECT_MEMORY_ERROR` at a finalize-tail warm site and drives it via an ACTUAL ingest job
  (`POST /api/data/jobs`) against a dedicated spawned backend, not a live request — closing J-07 step 4's
  evidence gap without needing the goal-mode harness's backend-restart permission (denied twice this
  session, UT-05).
- [ ] Add a fresh, dated `reports/perf-budgets.md` addendum recording: (a) the health-poll
  connection-level non-answer count before/after (solo and concurrent), (b) the reconciled finalize-tail
  total wall-clock against the existing 1,200s budget, (c) J-06's Factor Lab real-browser
  time-to-interactive/on-load-latency measurement (currently owed — it exists only inside a test report
  per iter-51's own finding).

### Frontend
None. No frontend file is touched — this is a pure backend scheduling change; the health badge, job
cards, and Factor Lab page are unchanged in shape and payload.

### New user-facing capability
None new. The user-visible effect is that the readiness badge / any page probing `/api/health` during a
heavy data job stops occasionally showing a dead connection — it stays live (and 200) throughout.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
No visible change to any page. What changes is reliability: `/api/health` (and by extension the
readiness badge every page polls) no longer goes fully unanswered during the longest finalize-tail phase
of a data job.

### Blueprint conformance
No new page, route, or nav entry. This iteration's fix lives entirely inside the already-registered "Job
history & per-date exclusion reasons," "Membership timeline / research hot-key caches," and "Regime
score, market phase, realized forward-returns" Data Contract rows
(`runs/goal-session-ops-hardening/state/blueprint.md`) — same computing modules, same endpoints, no
schema change. Blueprint already updated this iteration (additive changelog paragraph + a short Notes
append on the Job history row).

### Data-contract additions
None. No new displayed value, no new field, no new endpoint. `GET /api/health`'s payload shape,
`aggregates_refreshed`, and every warmed cache row keep their existing single computing module and
single serving endpoint (per the note at the foot of the Data Contract table) — this iteration only
interleaves the SAME computations with brief cooperative-yield points.

## OUT OF SCOPE

- Moving any heavy computation to a separate process/subprocess/worker boundary — the owner has not yet
  answered whether this is permitted (asked again at iter-51, still open); logged again in
  `assumptions.md`, iter-52.
- Raising or otherwise touching `server.memory_cap_mb` / `malloc_arena_max` / `host-guard.env` values —
  AG-10 frozen, never edit.
- Re-opening any "Do not redo" item from `iteration-state.md`: the `factor_lab_all_warm` finalize-tail
  phase, the `_combination_cohort_members` bound, `perf-budgets.md` Item T/Addendum 11 (append-only), the
  AG-10 surfaces, the iter-50 columnar bound / single-flight waiter cooldown / `phase_context_by_date`
  conditional skip.
- A second, pre-dev execution of the 8-journey lane distinct from its standing lane-last run — see
  BACKGROUND / `assumptions.md` for the resolution.
- The small already-diagnosed items iter-51 filed as item (5) — the honesty gap where a category can
  report "refreshed" despite a silent save failure, the missing test for the other honesty branch, the
  "possibly stalled" wording during the new warm phase, and picking a non-default date staying slow —
  explicitly deferred to a future iteration, not silently dropped (see NOTES).
- The long-carried backlog: iter-29/b (badge wording after a permanently failed warm-up); iter-31/e;
  iter-32/f; iter-33/g (Regime Lab); iter-35/k; iter-36/n; iter-37/o; iter-37/q; iter-39/u; iter-46/az;
  iter-46/ba; iter-47/bd; iter-47/bf; iter-47/bi; iter-48/bj.
- The interlock spec contradiction (`iter-50/cc`) — an explicit owner decision, restated in NOTES, not
  re-planned as agent work.
- Evidence capture / demo walkthrough retakes (leaderboard screenshot, blank frames, J-07 walkthrough) —
  never an iteration goal (rule 7); ride the make-up lane as passenger tasks only.
- Fully closing J-07 step 2's ≤2s latency ceiling for every single poll — targeted, not guaranteed; see
  the Honest limit in BACKGROUND.

## DEFINITION OF DONE

- [ ] TC-1 through TC-12 (below) all pass.
- [ ] Target journeys J-04, J-05, J-06, J-07 each produce a REAL executed row via browser-qa-agent /
      deterministic replay + LLM fallback — no "Deferred (iteration budget)", no zero-row scoring, for a
      third consecutive round.
- [ ] Required-still-passing journeys J-01, J-03, J-08, J-09 remain green (deterministic replay + LLM
      fallback where no golden exists).
- [ ] No anti-goal violation introduced: `git diff --stat` over `config.yaml`,
      `project-extensions/host-guard/host-guard.env`, `scripts/start-backend.sh`, `scripts/dev.sh`,
      `scripts/start-frontend.sh` stays EMPTY (AG-10); all ingest in any drill runs `provider='seed'` /
      `source: null` (AG-9); no committed secret (AG-7); every warmed value byte-identical to its pre-fix
      reference (AG-3/AG-5).
- [ ] Unit tests pass; no regressions (`apps/backend/tests/test_data_manager.py`,
      `test_research_streaming.py`, `test_ingest_finalize_fault_injection.py`,
      `test_start_backend_script.py`, plus the new tests this iteration adds).
- [ ] `reports/perf-budgets.md` carries a fresh, dated addendum with the health-poll result, the
      reconciled finalize-tail total, and J-06's Factor Lab browser measurement (never silently loosened
      or silently omitted).
- [ ] The full 8-journey browser/replay lane runs LAST, after every fix-mode/audit-fix pass, with no
      product-code change afterward (TC-9; the TC-8/TC-13 sequencing rule, held for the first time last
      round after 5 broken rounds — keep it held).
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-52-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-04 (all 6 steps — restart timing, phase-aware polling, crash→unreachable, logfile,
  interrupted-job state — DEFERRED twice, must run this round), J-05 (steps 1–4, especially step 2's
  health-during-heavy-ingest poll and step 4's induced-pressure abort), J-06 (step 1's full 11-page
  sweep plus step 2's budgets-table write for the Factor Lab measurement), J-07 (steps 1–4, especially
  step 2's zero-non-answer requirement and step 4's fault-injection). Regression replay: J-01, J-03,
  J-08, J-09.
- Unit/integration: the new yield-point scheduling change (byte-identical warmed values against a pinned
  pre-fix reference for every already-warmed category); the new throwaway-process ingest-warm
  fault-injection test.
- Error cases: a finalize-tail warm phase that hits injected/real memory pressure must still
  isolate-and-continue (existing per-item degrade path, unchanged), and `/api/health` must keep answering
  200 throughout — never a crash, never a silently-dropped category falsely reported as refreshed.

- TC-1: given a live backfill job whose finalize tail runs its full set of warm phases (coverage,
  membership timeline, market phase, forward aggregates, research hot keys, index series, factor lab
  all, drawdown expectations), when `GET /api/health` is polled once per second for the whole run plus
  30s past completion, then zero polls return a connection-level non-answer (no `curl` code `000`, no
  timeout) — closing Item T's 9-of-653 solo finding.
- TC-2: given the same drill as TC-1 but with a concurrent `GET /research/factor-lab?all=true` or
  `GET /research/factor-combination` request issued mid-warm (mirroring UT-08's own shape), when both
  run together, then `GET /api/health` again shows zero connection-level non-answers across the whole
  window — closing the 19-of-892 concurrent finding.
- TC-3: given TC-1/TC-2's recorded per-poll latencies, when compared against the owner-amended ≤2s
  bounded-background-compute ceiling, then the count of polls exceeding 2s and the worst-case latency are
  recorded honestly in a fresh `reports/perf-budgets.md` addendum, whether or not the ceiling is fully
  met for every poll.
- TC-4: given the SAME finalize-tail warm phases run before and after the yield-point change, when each
  warmed value is compared (the `aggregates_refreshed` list, the
  `EventStudyCache`/`MarketPhaseCache`/`ForwardAggregateCache`/`IndexSeriesCache`/coverage-snapshot
  rows), then every value is byte-identical to a pinned pre-fix reference — the change alters scheduling
  only.
- TC-5: given the yield-point change adds scheduling overhead, when TC-1's drill completes, then the
  finalize tail's total wall-clock is recorded in the same dated `reports/perf-budgets.md` addendum and
  reconciled against the existing 1,200s finalize-tail-total budget (never silently loosened or silently
  exceeded without disclosure).
- TC-6: given J-07 step 4 has no evidence this session (UT-05 SKIPPED twice), when the new
  throwaway-process fault-injection test arms `TRENDORA_FAULT_INJECT_MEMORY_ERROR` at a finalize-tail
  warm site and drives an actual ingest job on a dedicated spawned backend, then the job's terminal
  record honestly OMITS the faulted category from `aggregates_refreshed` while the other categories
  still appear, `GET /api/health` stays 200 throughout and 30s past completion, and a follow-up request
  for a category that DID warm successfully still returns the correct stored value from the SAME
  still-running process — no restart performed or required.
- TC-7: given J-06 step 2 requires the Factor Lab page's measured load time in `reports/perf-budgets.md`
  (currently owed per iter-51's finding), when the browser lane measures `/research/factor-lab`'s
  real-browser time-to-interactive and on-load `GET /api/research/factor-lab?all=true` latency
  immediately after an ingest, then both numbers are written into a fresh dated `reports/perf-budgets.md`
  section.
- TC-8: given the full 8-journey browser/replay lane must actually execute this round, when it is
  dispatched, then each of J-04, J-05, J-06, and J-07 produces at least one real executed row (a
  passing/failing golden replay, a captured screenshot, or an equivalent LLM-fallback verdict) — none
  scored "Deferred (iteration budget)" and none with zero rows.
- TC-9: given all code changes for this iteration are complete and committed, when the full 8-journey
  browser/replay lane runs, then it runs LAST — no product-code file under `apps/backend/` or
  `apps/frontend/` has an mtime later than the lane's own results-file mtime; any fix-mode/audit-fix pass
  that changes product code after the lane runs triggers a mandatory re-run before this iteration is
  scored.
- TC-10: given AG-10's frozen launch-script surfaces, when `git diff --stat` is run over `config.yaml`,
  `project-extensions/host-guard/host-guard.env`, `scripts/start-backend.sh`, `scripts/dev.sh`,
  `scripts/start-frontend.sh`, then the output is EMPTY both before and after this iteration's changes.
- TC-11: given every ingest job this iteration's own drills/tests trigger, when its persisted job record
  is inspected, then `provider` reads `"seed"` (or `source` is `null` for a backfill-only job) — no live
  network call introduced (AG-9).
- TC-12: given this iteration's yield-point scheduling change has landed, when the full 8-journey
  browser/replay lane scores the Required-still-passing set, then J-01, J-03, J-08, and J-09 each
  replay PASS (or receive an equivalent LLM-fallback passing verdict where no golden exists) with no
  new failure introduced relative to their iter-51 evidence.

## NOTES

- **Assumptions logged (`assumptions.md`, iter-52, two entries):** (1) choosing in-process scheduling
  (yield points) over an off-process/worker boundary for the health-stall fix, given the owner has not
  yet answered iter-51's question either way; (2) resolving the apparent tension between the iter-51
  evaluator's "check first, then fix" ordering and the standing TC-8/TC-13 lane-last rule by running ONE
  lane pass at the end, covering both iterations' changes.
- **Owner items, restated, not re-planned:** (1) may a future iteration move heavy compute off-process?
  Still unanswered (asked at iter-51, and in different words at iter-50). (2) The interlock spec
  contradiction (`iter-50/cc`) — "never silently drop the work" vs. "defer when the other one is
  running" — still unanswered; no agent action this iteration; do not touch
  `_try_acquire_drawdown_warm`/`_release_drawdown_warm` to "fix" this without an owner answer.
- **Carried, untouched (do not schedule as new diagnosis):** iter-29/b · iter-31/e · iter-32/f ·
  iter-33/g (Regime Lab) · iter-35/k · iter-36/n · iter-37/o · iter-37/q · iter-39/u · iter-46/az ·
  iter-46/ba · iter-47/bd · iter-47/bf · iter-47/bi · iter-48/bj.
- **Small items filed, not this round's scope (iter-51's item 5):** the honesty gap where a category can
  report "refreshed" despite a silent save failure; the missing test for the other honesty branch; the
  "possibly stalled" wording during the new `factor_lab_all_warm` phase; a non-default date staying slow
  (only the default view is pre-computed). Candidates for a future iteration once this round's scheduling
  fix and verification debt are closed.
- **Golden-script caution:** `runs/goal-session-ops-hardening/journey-scripts/J-05.json` and `J-06.json`
  exist in this session but scored zero executed rows for two consecutive rounds — confirm they actually
  RUN this time (iter-46/47's binding lesson: a script that exists but never executes buys nothing).
  Neither `J-04.json` nor `J-07.json` exists in this session's `journey-scripts/` directory — both are
  LLM-fallback-lane journeys; any freshly-authored step must assert against a NEW run's own row/log line,
  never page-wide text a stale history panel would already satisfy.
- **Sequencing note (also see BACKGROUND):** this spec deliberately does not schedule a separate pre-dev
  "check only" pass; the standing lane-last rule (TC-9) is preserved, and the one lane run this iteration
  produces is expected to cover both iter-51's and this iteration's changes.
