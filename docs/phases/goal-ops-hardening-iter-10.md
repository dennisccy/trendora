# Goal Iteration 10 — Close J-04 step 6 with a live browser re-verification (no source changes)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 10
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** yes
- **Target journeys:** J-04
- **Required-still-passing journeys:** J-01, J-03, J-05
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

Score J-04 ("Non-blocking boot with visible status") fully `passing` by re-driving its step-6
acceptance — a backend `kill -9`/restart during a mid-flight backfill, then reading the RENDERED
`/data` Run History panel — through a live browser lane against the already-shipped, already-committed
`_checkpoint_run_record` fix, closing the single verification gap standing between this session and
all five Must-have ops-hardening journeys passing.

## BACKGROUND

Per the priority rubric: no journey regressed (rule 1 — none apply), the last coherence verdict was
COHERENCE-PASS so no consolidation mandate (rule 2), and J-04 is the only failing/partial journey with
a concrete, fully agent-doable path (rule 3/6) — J-06's remaining gap (the deferred on-load
`/api/backtest` MemoryError, plus the J-05/J-06 `demo.sh --session-live` walkthroughs) is explicitly an
owner-decision item per iter-9's eval, so it is excluded this iteration rather than re-planned. J-04's
own fix, `_checkpoint_run_record` (`apps/backend/app/engine/data_manager.py:3677-3712`), already shipped
and is committed (iter-9, commit `5e073cf1`); it was verified at the API level by the operator
(`runs/goal-ops-hardening-iter-9/pump-j04-crash-recovery-evidence.md`: killed-job row 114 froze at 59
snapshots / 64-of-84 dates vs. the pre-fix all-zero control row 113), but per the round-3 auditor's and
iter-9 evaluator's explicit instruction, that API-level evidence must NOT by itself flip J-04 to
`passing` — nobody has re-driven the rendered `/data` page since the fix landed. That single browser
cycle is this iteration's entire scope; this applies the iter-9 lesson directly ("a fix that lands after
its own verification lane has run schedules a re-verification, it does not close the journey").

Depth is **lean**: none of the four full-depth triggers fire — no structural/cross-cutting refactor (this
iteration plans zero source changes), no data-model/Data-Contract change, the last verdict was CONTINUE
not ESCALATE, and the hardening-cadence counter is 0/4 (last iteration was full, so the counter reset;
"Consecutive lean iterations dispatched: 0" per dispatch). The evaluator's own iter-9 recommendation
suggested full again, but that recommendation is non-binding (established precedent, iter-7/iter-8
assumption entries) and "needing tests" is never a valid full trigger — this iteration needs only a
regression-relevant re-verification, which a lean developer→reviewer→browser-qa cycle covers.

Two lessons applied directly: (1) iter-8's lesson — this spec sets **Frontend Present: yes** explicitly
even though no frontend code changes, because TESTING REQUIREMENTS name browser journeys and the
`Frontend Present: no` misrouting bug (still unfixed in the framework harness) would otherwise skip
browser-qa outright and verify nothing, exactly as it did in iter-8. (2) iter-3/iter-4's lesson — score
J-04 from the RAW `.llm.md` browser-qa artifact, never the merged `ui-test-results.md` rollup alone
(`merge_ui_test_results.py` is documented to drop emphasised `**FAIL**` cells).

Two small documentation-only items are folded in because they cost no extra code and were flagged by
the last coherence pass: `blueprint.md`'s Data Contract "Job history" row now names
`_checkpoint_run_record` explicitly (it shipped iter-9 but the iter-9 paragraph omitted it — coherence
advisory, closed in this dispatch's blueprint edit, not left for a developer step). The stale
`reports/qa/goal-ops-hardening-iter-9-qa.md` (written before both the browser lane and the heavy run it
now mis-describes as "DEFERRED") is NOT hand-edited this iteration — per the established iter-7
precedent, a past iteration's point-in-time artifacts stay as historical record and are superseded by
this iteration's own fresh dev/QA/closure artifacts, not retroactively patched.

## IN SCOPE

### Backend
- [ ] None. `_checkpoint_run_record` (`data_manager.py:3677-3712`) already shipped and is committed
      (iter-9, `5e073cf1`). No source changes planned this iteration.

### Frontend (if applicable)
- [ ] None. `apps/frontend/app/data/page.tsx`'s `LastRunSummary`/`BackfillBreakdown` components already
      read the existing `_run_detail()` fields (`snapshots_created`, `dates_done`/`dates_total`,
      `calendar_days`, `non_trading_days`, `already_snapshotted`, `error_other`) this iteration verifies.
      No source changes planned.

### New user-facing capability
None new. This iteration proves an already-shipped capability — an interrupted mid-run backfill shows
its real last-checkpointed progress, not "0 snapshots · 0 trading days in range" — renders correctly on
the live `/data` page after a kill/restart cycle.

### New information displayed
None new. Same fields as above; only their POST-KILL rendering is being re-observed.

### New user actions
None.

### UI surface changes
None. Same `/data` Run History / Job progress panel (already registered below).

### Product surface delta
None — a verification-only iteration. The product surface is unchanged; only its trustworthiness under
a crash/restart is being re-confirmed live.

### Blueprint conformance
No new surfaces. The re-verified behavior lives entirely under the existing "J-04 — Non-blocking boot,
visible status" home (global readiness badge + `/data` Data Manager, per `blueprint.md`'s Information
Architecture table) and the existing "Job history & per-date exclusion reasons" Data Contract row.

### Data-contract additions
None. `blueprint.md`'s "Job history & per-date exclusion reasons" row has been amended (by this
dispatch, additive edit) to name `_checkpoint_run_record` explicitly — a documentation completion of an
already-registered row, not a new value, module, or endpoint.

## OUT OF SCOPE

- The deferred on-load `/api/backtest` → `forward_aggregates_cached` MemoryError (J-06/AG-8 dimension) —
  owner decision still outstanding per iter-9's eval; not re-planned here.
- The unproduced J-05/J-06 `demo.sh ops-hardening --session-live` walkthroughs — owner decision.
- Any change to `app/api/health.py`, `app/engine/readiness.py`, `main.py` boot sequence, `warmup.py`,
  `max_range_days`/`snapshot_cadence`, the `/evidence` drawdown warm, or `server.memory_cap_mb` — all
  BINDING "Do not redo" items from iteration-state.
- Re-running the 18-minute heavy-ingest pytest test (`test_start_backend_survives_back_to_back_heavy_
  ingest_under_memory_cap`) — its iter-9 result (1092.93s, 439/439 health-200, VmPeak 24.7% under cap)
  is settled/BINDING "do NOT re-run" per iteration-state; this iteration's kill/restart cycle uses a
  small, bounded date range instead (see TESTING REQUIREMENTS), never the full-universe heavy job.
- Hand-editing `reports/qa/goal-ops-hardening-iter-9-qa.md` or any other past iteration's point-in-time
  artifact — superseded by this iteration's own fresh artifacts (established iter-7 precedent), not
  retroactively patched.
- Flipping `HOST_GUARD_REQUIRE_MARKERS` — owner decision.
- Framework-harness fixes (`merge_ui_test_results.py`'s FAIL-cell drop; the `Frontend Present: no`
  browser-qa-skip misrouting) — maintainer-owned, out of a product iteration's remit; routed around
  this iteration via the explicit `Frontend Present: yes` metadata field above, not fixed at the source.

## DEFINITION OF DONE

- [ ] J-04 passes all six acceptance steps via browser-qa-agent, reading the RAW `.llm.md` artifact —
      step 6 specifically shows the post-fix kill/restart cycle's `/data` Run History panel rendering
      real persisted progress on the interrupted row.
- [ ] Required-still-passing journeys J-01, J-03, J-05 remain green (deterministic replay for J-01/J-03
      via their golden scripts; LLM fallback for J-05, per the BINDING "do not re-run the heavy-ingest
      test" note — a light re-confirmation of J-05's non-heavy acceptance steps only).
- [ ] No anti-goal violation introduced (AG-10 host-ceiling watched explicitly given this session's
      hard-reset history — see TC-8).
- [ ] Existing backend test suite passes with no NEW failures (the pre-existing, documented
      `tests/test_db.py::test_create_all_produces_expected_tables` failure, stale since iter-2 and
      unrelated to this iteration, is not a new regression).
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-10-dev.md`, explicitly stating no
      source changes were made and pointing to the browser-qa evidence that closes J-04 step 6.

## TESTING REQUIREMENTS

- Browser: J-04 (target, full six-step acceptance per `docs/goal.md`), J-01 and J-03 (required-still-
  passing, deterministic golden replay with LLM fallback), J-05 (required-still-passing, light
  re-confirmation of its non-heavy acceptance steps only — do NOT re-run the heavy-ingest pytest test).
- Unit/integration: run the existing backend suite excluding the opt-in
  `TRENDORA_RUN_HEAVY_INGEST_TEST` lane; confirm no new failures beyond the one documented pre-existing
  failure named above.
- Error cases: N/A — no new input surface; the "error case" this iteration exercises is the crash path
  itself (an ungracefully killed process), covered by TC-1/TC-2 below.

Test-first contract:

- TC-1: given a backend restarted from the current committed tree (post-iter-9, includes
  `_checkpoint_run_record`) via `scripts/start-backend.sh`, when a bounded-range backfill job (e.g. a
  multi-month span such as 2019-03-01 → 2019-06-28, not a multi-year/full-universe job) is submitted and
  allowed to run for at least one 10-second checkpoint interval, then the process is killed with
  `kill -9` (no clean shutdown) and the backend is restarted, then the rendered `/data` Run History panel
  shows that job's row with status "interrupted" and a non-zero `snapshots_created` value and a non-zero
  `dates_done` value (never "0 snapshots · 0 trading days in range").
- TC-2: given the same rendered `/data` page and the same interrupted row from TC-1, when the
  breakdown fields (`calendar_days`, `non_trading_days`, `already_snapshotted`, `error_other`) are read
  from the panel, then they are non-null and satisfy `non_trading_days + dates_total = calendar_days`
  and `snapshots_created + already_snapshotted + error_other = dates_total` (not all-null/zero
  creation-time defaults).
- TC-3: given the two backend restarts performed in TC-1 (initial start, and the post-kill restart),
  when `GET /api/health` is polled immediately from each process start, then the first HTTP 200 response
  for each restart arrives within 5 seconds (J-04 steps 1-2 re-confirmation).
- TC-4: given the frontend open during the second (post-kill) restart in TC-1, when the top-bar
  readiness badge and preflight banner are observed in the window before `/api/health` reports ready,
  then they display an explicit initializing/boot-phase state with progress detail, and after the
  `kill -9` they display an explicit crashed/unreachable presentation — never a bare "Backend
  unavailable" during the initializing window and never a blank or frozen frame (J-04 steps 3-4
  re-confirmation).
- TC-5: given the persistent backend logfile path documented in the dev handoff, when the log is
  inspected after the `kill -9` in TC-1, then it contains the prior boot event entries and ends
  abruptly with no clean-shutdown entry (J-04 step 5 re-confirmation).
- TC-6: given J-01's and J-03's stored golden replay scripts (`runs/goal-session-ops-hardening/
  journey-scripts/J-01.json`, `J-03.json`), when they are executed via deterministic replay against the
  current build, then both record a PASS outcome in the regression-replay-results artifact (falling
  back to LLM acceptance for either only if its replay produces an adjudicated non-pass).
- TC-7: given J-05 is `passing` on the current build per iter-9's settled, BINDING heavy-ingest evidence
  (do not re-run), when this iteration's regression sweep checks J-05's non-heavy acceptance steps
  (ingest-time aggregate status/badge, stored run-detail values, market-phase-at-as-of with no spinner,
  cold `/data` load from the persisted payload) via deterministic replay or LLM fallback, then each step
  is recorded PASS without executing the heavy-ingest pytest test.
- TC-8: given the bounded-range backfill job in TC-1 is a small, chunked job (not the full-universe
  heavy rebuild), when host telemetry (`logs/hwmon/hwmon.csv`, the 1 Hz sampler) is checked across the
  cycle, then temperatures stay within the documented idle/safe band with no thermal-watchdog trip and
  no host reset — confirming AG-10 is respected.
- TC-9: given the current backend test tree, when `pytest apps/backend/tests/` is run excluding the
  opt-in `TRENDORA_RUN_HEAVY_INGEST_TEST` test, then it completes with zero failures other than the
  pre-existing, documented `tests/test_db.py::test_create_all_produces_expected_tables` failure.
- TC-10: given this iteration reaches completion, when `docs/handoffs/goal-ops-hardening-iter-10-dev.md`
  is inspected, then it exists, states explicitly that no source changes were made, and cites the
  specific browser-qa evidence (raw `.llm.md` UT row / screenshot) that closes J-04 step 6.

## NOTES

- **Operational constraint on who performs the kill/restart.** The browser-qa lane has already executed
  restart/crash cycles for J-04 steps 3-4-5 in iter-9 (UT-11/UT-12), so it has a working mechanism for
  this; the standard path is for browser-qa-agent to re-drive J-04's full six-step live acceptance
  itself, exactly as before. If the harness genuinely cannot manage a backend kill/restart in this
  environment, the operator may perform the documented sequence (mirroring
  `runs/goal-ops-hardening-iter-9/pump-j04-crash-recovery-evidence.md`'s already-proven steps) and hand
  the resulting live state to browser-qa-agent to read and score FROM THE RENDERED PAGE — API-level JSON
  alone is explicitly insufficient per the round-3 auditor's and iter-9 evaluator's instruction not to
  let this fix be flipped to passing on API evidence alone. See `assumptions.md` iter-10 entry.
- **Session state entering this iteration:** J-01/J-03/J-05 passing, J-04 partial (steps 1-5 pass, step 6
  is this iteration's entire scope), J-06 partial (out of scope, owner-decision pending). Iteration
  budget is no longer a blocker — `session.json`'s `max_iterations` is now `0` (unlimited).
  `HOST_GUARD_REQUIRE_MARKERS` flip and the J-05/J-06 `--session-live` walkthroughs remain open owner
  decisions, unaffected by this iteration.
- If J-04 scores `passing` this iteration, only J-06 remains non-passing session-wide, and its remaining
  gap is an owner-decision item (not agent-plannable without that decision) — flagging this so the next
  decomposer pass (or the evaluator, if it reaches GOAL_ACHIEVED-adjacent territory) does not
  artificially manufacture new scope against J-06 without that decision being made first.
- Framework maintainer (unchanged, still unfixed, carried from iter-9's eval): `merge_ui_test_results.py`
  drops emphasised `**FAIL**` verdict cells from the merged rollup; always score from the raw
  `.llm.md`. The `Frontend Present: no` → browser-qa-skip misrouting is routed around here via the
  explicit `Frontend Present: yes` field, not fixed at the source.
