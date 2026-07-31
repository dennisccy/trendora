# Goal Iteration 42 — Close the target-journey verification gap; re-check J-05/J-07; a fifth, differently-leveraged AG-8 bound attempt

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 42
- **Mode:** next
- **Depth:** full
- **Full trigger:** 3 — prior verdict was ESCALATE (mandatory full depth, no exceptions)
- **Frontend Present:** no
- **Target journeys:** J-05, J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-06, J-08, J-09 (widened to the full passing set — ESCALATE cadence guidance)
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

Every future iteration's `Target journeys:` get the same fresh-evidence guarantee `Required-still-passing journeys:` already has (no more clean `PASS`/`SKIPPED` headlines over an unverified target), and J-05/J-07 are re-checked against the current build with that guarantee in force — while J-07's remaining AG-8 finding (`_BarCache.prefill`'s whole-table resident load) gets one more, differently-leveraged bound attempt.

## BACKGROUND

Prior verdict was ESCALATE for the sixth consecutive iteration (mandatory full depth, no exceptions
— see Full trigger above). iter-41's own audit found the load-bearing defect: an iteration whose
purpose was making an unverified journey impossible to report as clean shipped a merged `PASS 6/6`
headline while its own two TARGET journeys (J-05, J-07) had **zero rows anywhere** — every coverage
gate in the chain (`ui-test-designer`'s backend-only carve-out, `merge_ui_test_results.py`'s
missing/skipped-row guard, `goal_gate.py`, `closure_gate.py`) keys off the spec's
`Required-still-passing journeys:` line only, with no notion of `Target journeys:` (iter-41 lesson,
binding: "Promoting a journey to an iteration's target silently REMOVES its verification"). J-05
"Aggregates are precomputed at ingest" is `unknown` and has **less proof now than at iter-39**, with
golden scripts `J-05.json`/`J-07.json` sitting unused on disk the whole time. This iteration closes
that gap first (item 1 of the iter-41 evaluator's next-step order), then re-checks J-05 and J-07
through it (item 2).

J-07 "Heavy aggregates never take the service down" has missed `passing` for eight consecutive
iterations. Two blockers remain: (a) the `GET /api/health` ≤0.1s budget (missed 8 times, five
evaluators have called it owner-only — **not** re-planned here, per rule 6); (b) whether
`_BarCache.prefill` (`app.engine.prices:132-142`) still streams the full `daily_prices` table into
RAM. Four prior iterations (35, 36, 37, 41) each attempted a narrower fix at this exact code and each
fell short — iter-41's own columnar rewrite is, in its evaluator's words, "a COMPRESSION, not a
BOUND: the whole table is still resident, memory still strictly O(row count)." Applying the binding
iter-40 lesson (**`.yield_per()` bounds the DB cursor, not your accumulator** — the same distinction
this session already learned once about `_missing_data_diagnostic`), this iteration takes a lever the
prior four attempts did NOT take: `prefill`'s SELECT has no `WHERE symbol IN (...)` filter at all,
unlike its own sibling `load_only` (same file, same query shape) which already streams a
symbol-filtered read. See `runs/goal-session-ops-hardening/state/assumptions.md` iter-42 for the full
reasoning on why this is a fifth attempt worth making rather than an immediate owner escalation, and
the explicit fallback if it isn't.

Per the settled broad-reading precedent in this session (assumptions.md iter-39: goal.md's Success
Criteria name `daily_prices` explicitly, without the J-07 acceptance clause's narrower parenthetical),
"no unbounded whole-table load" is scored against `daily_prices` generally, not only the two
parenthetical-named tables — the developer must not re-argue the narrow reading.

Small, already-written-down items travel with this iteration because they sit in the same two files
already being touched: B4 (the frontend-readiness race that actually voided iter-40's browser lane,
still open after iter-41's B1 guard made its failure loud instead of fixing it), B6 (a NULL-tolerance
gap in the new columnar store that would now crash rather than degrade — AG-8), and T2 (no
before/after latency figure exists for the `_SymbolColumns` read-path change). Per this session's
ESCALATE-cadence guidance, Required-still-passing widens to a full regression of all six currently
passing journeys this iteration, refreshing golden scripts and catching selector drift.

Deliberately NOT this iteration's scope (rule 6, human-owned, unchanged across 5+ evaluators):
iter-34/j (the ≤0.1s health budget disposition) and iter-33/i (`start-frontend.sh` →
`HOST_GUARD_MARKER_FILES`). Also deliberately deferred (rule 5, one risky product-code action per
iteration; queued a seventh time): iter-33/g (Regime Lab's cold `view=pooled` background dispatch).
J-07's `[NEW]` walkthrough stays capture-only, never an iteration's own goal (rule 7).

## IN SCOPE

### Backend

- [ ] `incredible_auto_dev/agents/ui-test-designer/body.md` — "Backend-only phase handling": emit
      one `UT-<journey-id>` regression test case per journey named on the spec's `Target journeys:`
      line too, not only `Required-still-passing journeys:`, so a backend-only spec's own targets
      always get a row.
- [ ] `incredible_auto_dev/scripts/automation/lib/merge_ui_test_results.py` — add a
      `target_journeys` parameter to `merge()` (and equivalents of
      `missing_required_journeys`/`skipped_required_journeys`) that forces the merged headline to
      `BLOCKED` whenever ANY target journey has zero rows or an all-SKIP-only row — additive to the
      existing `required_journeys` guard, never replacing it. Add a sibling `--target` CLI flag.
- [ ] `incredible_auto_dev/scripts/automation/lib/replay-lane.sh`,
      `incredible_auto_dev/scripts/automation/browser-qa-phase.sh`,
      `incredible_auto_dev/scripts/automation/goal-iter-lean.sh` — thread the already-parsed
      `TARGET_JOURNEYS`/`_bqa_targets` locals into the new `--target` flag at every merge call site,
      mirroring the existing `--required` wiring exactly.
- [ ] `incredible_auto_dev/scripts/automation/lib/common.sh` (`ensure_services_running`) — B4: after
      a backend/frontend restart, wait for or re-probe the frontend within a bounded window instead
      of the whole regression run going silently all-SKIP on one premature timeout.
- [ ] `apps/backend/app/engine/prices.py` (`_BarCache.prefill`) — bound the resident bar-cache
      footprint to what each caller's resolver loop actually needs: reuse `load_only`'s already-proven
      `WHERE symbol IN (...)`-filtered, `yield_per`-streamed query shape for `prefill` when
      `expected_symbols` is given, AND audit whether `_compute_coverage_uncached`'s /
      `_membership_timeline`'s resolver loops read a symbol's FULL history or only a bounded trailing
      window — apply whichever bound(s) apply. Byte-identical `Bar` output required within whatever
      window each existing consumer actually reads. If analysis shows a caller genuinely needs full
      history across the full universe (no bound reachable without a caller-semantics redesign),
      document that precise finding in the dev handoff and `perf-budgets.md` for evaluator/owner
      disposition instead of re-claiming AG-8 resolved.
- [ ] `apps/backend/app/engine/prices.py` — B6: `_SymbolColumns`'s columnar accumulation (and
      `prefill`'s row loop) tolerates a NULL numeric column with an honest NA sentinel or documented
      skip instead of raising `TypeError`.
- [ ] `reports/perf-budgets.md` — T2: a before/after latency figure for representative
      `bars_asof`/`bars_asof_window` reads over `_SymbolColumns` vs. the pre-iter-41 baseline, plus a
      fresh dated section for this iteration's own peak-memory measurement (TC-6 below).
- [ ] Correct the QA report's AG-8 disposition row to the accurate current state (bounded / partially
      bounded with the specific gap named / still open), never an unqualified "✓ PASS / no whole-table
      loads" unless literally true.

### Frontend

None — backend/tooling only (`Frontend Present: no`).

### New user-facing capability

None — this iteration is verification-infrastructure repair plus a backend memory-bound attempt; no
new user-visible feature.

### New information displayed

None.

### New user actions

None.

### UI surface changes

None.

### Product surface delta

None visible to the end user; J-05/J-07's existing surfaces (Data Manager, global readiness badge,
Backtest) are unchanged in shape — only their underlying verification and (for J-07) memory footprint
change.

### Blueprint conformance

No new Information Architecture. J-05 keeps its existing cross-cutting homes (Data Manager, Scanner
Runs, Dashboard, Research, Evidence); J-07 keeps its existing global-badge + `/backtest` home — both
per `runs/goal-session-ops-hardening/state/blueprint.md`'s Information Architecture table. See the
blueprint's iter-42 update paragraph for the full accounting of this iteration's changes.

### Data-contract additions

None. No new displayed value; the Coverage payload row's canonical computing module
(`app.engine.data_manager`, `_compute_coverage_uncached`) and endpoint (`GET /api/data`) are
unchanged — only `_BarCache.prefill`'s internal loading mechanism changes, byte-identically served.

## OUT OF SCOPE

- The `GET /api/health` ≤0.1s budget disposition (iter-34/j) — owner decision, unchanged.
- Whether `start-frontend.sh` joins `HOST_GUARD_MARKER_FILES` (iter-33/i) — owner decision, unchanged.
- iter-33/g — Regime Lab's cold `view=pooled` background dispatch (deferred a seventh time; rule 5).
- J-07's `[NEW]` walkthrough recording (capture-only; never an iteration's own goal, rule 7).
- Any docs/goal.md edit, including amending the "no unbounded whole-table loads" wording — stays
  available to the human owner only (see assumptions.md iter-42).
- Any change to `resolved_forward_aggregate_evidence`, `ensure_historical_forward_aggregates_dispatched`,
  or `compute_forward_aggregates` — byte-frozen (iteration-state.md "Do not redo").
- Any re-tuning of `server.memory_cap_mb` — byte-frozen (iteration-state.md "Do not redo").

## DEFINITION OF DONE

- [ ] A backend-only spec's `Target journeys:` each get a `UT-<journey-id>` row from
      `ui-test-designer`, and `merge_ui_test_results.py` refuses a clean PASS/SKIPPED headline when a
      target journey has zero rows or an all-SKIP row (TC-1, TC-2).
- [ ] J-05 is re-verified live via the existing `journey-scripts/J-05.json` golden script (TC-3, TC-4).
- [ ] J-07 steps 1-2 are re-verified live via the existing `journey-scripts/J-07.json` golden script
      (TC-5).
- [ ] `_BarCache.prefill`'s resident memory footprint is measured against the actual symbol/window
      subset each caller needs, and either a genuine reduction lands with byte-identical served values
      (TC-6), or the specific remaining gap is documented for evaluator/owner disposition — never
      silently re-claimed as resolved.
- [ ] The QA report's AG-8 row states the accurate current disposition (TC-7).
- [ ] `_SymbolColumns`/`prefill` tolerates a NULL numeric column without crashing (TC-8).
- [ ] The browser-qa/replay lane waits for or re-probes a restarting frontend instead of going
      silently all-SKIP on one premature timeout (TC-9).
- [ ] A before/after `bars_asof`-family latency figure is recorded in `reports/perf-budgets.md` (TC-10).
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-06, J-08, J-09 remain green via full
      regression replay (TC-11).
- [ ] No anti-goal violation introduced.
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-42-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-05 (`journey-scripts/J-05.json`), J-07 steps 1-2 (`journey-scripts/J-07.json`); full
  regression replay of J-01, J-03, J-04, J-06, J-08, J-09.
- Unit/integration: `merge_ui_test_results.py`'s target-journey guard; `ui-test-designer` backend-only
  target-emission; `_BarCache.prefill`'s bound (byte-identity fixture within the actually-used
  window); `_SymbolColumns`/`prefill`'s NULL-tolerance; `common.sh`'s bounded frontend-reprobe.
- Error cases: a spec whose target journey is entirely missing from the merged results must produce
  `BLOCKED`, never `PASS`/`SKIPPED`; a NULL numeric column in `daily_prices` must not raise
  `TypeError` from `_BarCache.prefill`/`_SymbolColumns`.

Test-first contract: every DEFINITION OF DONE checkbox and every Data-contract addition above maps
to at least one concrete scenario line below.

- TC-1: given a spec with `Frontend Present: no` and `Target journeys: J-05`, when
  `ui-test-designer` generates the test plan, then the plan contains at least one `UT-J-05` row (not
  only `Required-still-passing` rows).
- TC-2: given a merged UI test results run where a target journey's `UT-<journey-id>` row is entirely
  missing (zero executed cases), when `merge_ui_test_results.py` computes the headline, then the
  merged file's verdict reads `BLOCKED`, never a clean `PASS` or `SKIPPED`.
- TC-3: given the backend and frontend running the current build, when the browser-qa agent replays
  `journey-scripts/J-05.json`'s step covering a fresh single-day backfill, then `/scanner-runs` lists
  the ingested date and its leaderboard renders the stored snapshot with zero recompute-on-read.
- TC-4: given a cold restart against the fully-ingested seed DB, when `/data` is loaded, then the
  coverage payload renders from storage within its committed budget and no 3.3M-row bar prefill
  trace appears in `logs/backend.log` for that request.
- TC-5: given the backend running the deep basis with a live forward-aggregate warm triggered via the
  ingest finalize path, when `GET /api/health` is polled at 1Hz throughout, then every poll returns
  HTTP 200 within its existing budget — replay of `journey-scripts/J-07.json` steps 1-2, zero frozen
  windows.
- TC-6: given `_BarCache.prefill` is invoked for a job whose `expected_symbols` pool is a strict
  subset of the full universe, when peak resident memory (VmPeak) for that job is measured live and
  compared against an equivalent full-universe run, then the comparison is recorded in a fresh dated
  `reports/perf-budgets.md` section showing whether peak memory now scales with the requested subset
  or still with the full table.
- TC-7: given this iteration's `_BarCache.prefill` outcome (bound landed, partially landed, or not
  reachable), when the QA report's AG-8 row is written, then it states that exact disposition with
  the specific gap named — never an unqualified "✓ PASS / no whole-table loads" unless the
  measurement in TC-6 literally supports it.
- TC-8: given a `daily_prices` row with a NULL numeric column, when `_BarCache.prefill` processes it,
  then the cache records an honest NA sentinel (or documented skip) for that field instead of raising
  `TypeError`.
- TC-9: given the browser-qa/replay lane restarts the frontend mid-run, when it next probes
  readiness, then it waits for or re-probes the frontend within a bounded window instead of marking
  the whole run all-SKIP after a single premature timeout.
- TC-10: given a representative `bars_asof`/`bars_asof_window` read over `_SymbolColumns`, when timed
  before and after this iteration's prefill changes, then both figures are recorded in a new dated
  section of `reports/perf-budgets.md`.
- TC-11: given the full required-still-passing set (J-01, J-03, J-04, J-06, J-08, J-09), when the
  full regression replay runs against this iteration's build, then all six journeys report PASS with
  dated evidence (screenshot or replay row), refreshing any golden script found to have selector
  drift.

## NOTES

- Applies the binding iter-41 lesson verbatim: promoting a journey to `Target journeys:` must never
  silently remove its verification — this iteration is that fix.
- Applies the binding iter-40 (second) lesson: `.yield_per()` bounds the DB cursor, not the
  accumulator — `_BarCache.prefill`'s remaining gap is exactly this shape one file over from
  `_missing_data_diagnostic`, which this session already fixed once.
- Applies the binding iter-37 lesson: any drill measuring a conditional code path (here, the
  symbol-subset vs. full-universe prefill comparison, TC-6) must assert the condition was actually
  live (log which query shape ran, assert the subset was genuinely smaller) — an absence of a
  particular allocation in a trace is not proof it didn't happen if the code path was never reached.
- See `runs/goal-session-ops-hardening/state/assumptions.md` iter-42 for the full reasoning behind
  attempting a fifth `_BarCache.prefill` pass now (a genuinely different lever) rather than escalating
  straight to an owner goal.md amendment, and the explicit honest-disposition fallback if it still
  falls short.
- Five consecutive iterations (37-41) had their most substantive defect caught only by the audit
  lane, not review or QA — full depth (mandatory here regardless) keeps that lane active.
