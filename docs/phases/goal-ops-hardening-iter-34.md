# Goal Iteration 34 — Close J-07: health-poll latency during its own warm + the induced-memory-pressure abort drill

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 34
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — Structural/cross-cutting: closing J-07 step 4 requires coordinating a config-level memory-cap override, the existing cross-module MemoryError-abort/isolation handling (`data_manager.py`/`forward_testing.py`, iter-8), the AG-10 host-guard cap application inside `scripts/start-backend.sh`, and the readiness/health endpoint's liveness guarantee for the SAME process — a cross-process failure mode no single module's unit tests cover, gated behind a *critical* anti-goal (AG-10) on a host that has already forced two hardware resets under uncapped compute.
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

Close J-07's last two unexecuted acceptance steps — record `GET /api/health`'s real LATENCY (not just its 200 rate) during its own live full-deep-basis forward-aggregate warm, and run the induced-memory-pressure abort drill deferred since iter-14 — so the session's last `partial` Must-have journey has direct, first-hand evidence for every one of its four steps.

## BACKGROUND

J-07 has been `partial` since iter-28 (six iterations): steps 1 and 3 (byte-identical bounded compute, VmPeak margin) are evaluator-confirmed done; step 2 has a poll-count (77/77 HTTP 200) but no latency figure, ever, against its own ≤0.1s budget; step 4 (induce memory pressure, assert an honest abort with the SAME process still serving `/api/health`) has never run in 20 iterations. The iter-33 evaluator named this the sole target for iter-34 ("FIRST AND ONLY TARGET"), and the dispatch's binding depth recommendation is `full`. Per priority rubric rule 3 (unblockers next) this is the clear pick — J-07 is the ONLY non-passing Must-have journey, and closing it is a precondition for GOAL_ACHIEVED. Per rule 5/6 (never bundle two risky changes), this iteration deliberately excludes the two OTHER items the iter-33 evaluator flagged as "THEN"/"CHEAP AND STRUCTURAL" (iter-33/g's Regime Lab background-dispatch fix, iter-33/h's sibling-lab wiring) — both are separate, real backend/frontend changes with their own blast radius, and this iteration's one risky change stays confined to the memory-pressure drill.

Lessons applied: (iter-26) diff `logs/backend.log` and DB tables after any browser/drill lane runs, before crediting a narrative as evidence — apply this to the drill's abort claim, not just a QA report's prose. (iter-28, second entry) a QA account of a concurrency/timing result can be right about the outcome while wrong about which requests it observed — verify the drill's timeline (which process, which requests) from `logs/backend.log`, not from a summary. (iter-30, second entry) when bounding/testing a memory failure mode, name the EXACT frame/mechanism under test — here, the existing per-item `MemoryError` catch in `_refresh_ingest_aggregates` (iter-8) is the mechanism step 4 must exercise; do not substitute a different, easier-to-trigger failure mode and call it equivalent.

Binding "Do not redo" (iteration-state.md): `scripts/start-frontend.sh` is settled prod mode; J-06's sweep is done; `merge_ui_test_results.py`'s `_ROW_RE` fix is done; the UT-11 honest-wait fix is Regime-Lab-only (extend later, don't rewrite); `stock_obs`/`compute_forward_aggregates`/`resolved_forward_aggregate_evidence` stay byte-frozen; `/api/health`'s ≤0.1s budget is recorded with an honest WARN under load, never amended; AG-10 marker files stay zero-diff.

## IN SCOPE

### Backend
- [ ] During a live full-deep-basis forward-aggregate warm (J-07 step 1's own scenario — trigger the warm for every configured horizon in one long-lived backend process, serving `GET /api/backtest` throughout), extend the existing 1Hz `/api/health` poll to record each response's round-trip LATENCY, not just its HTTP status.
- [ ] Write the resulting latency distribution (poll count, max, and whether it stays inside the ≤0.1s budget) into `reports/perf-budgets.md` under a J-07-step-2-labeled section, using the SAME honest-WARN convention already on record for this endpoint (PASS at rest, honest WARN under concurrent load) — do not amend the budget line itself (binding, "Do not redo").
- [ ] Add or use a config/launch-time override so `server.memory_cap_mb` can be tightened for ONE throwaway backend process, launched only via `scripts/start-backend.sh` (so host-guard's CPU-affinity mask, BLAS/OMP caps, `ulimit -v`, and `MALLOC_ARENA_MAX` still apply — AG-10).
- [ ] Trigger the SAME full-horizon forward-aggregate warm inside that throwaway process and confirm the EXISTING per-item `MemoryError`-abort handling (`_refresh_ingest_aggregates`, iter-8) catches the induced pressure and stops that warm loop honestly — no deadlock, no wedge.
- [ ] Confirm, in the SAME throwaway process, that `GET /api/health` keeps responding normally during and after the induced abort, and that at least one previously-cached read (e.g., an already-warmed horizon's `GET /api/backtest`) still serves its stored value without a restart.
- [ ] Record the drill's full outcome (process stayed alive / abort was honest / no restart required / which log lines evidence it) in `reports/perf-budgets.md`, cross-checked against `logs/backend.log` for the throwaway process (per the iter-26/28 lessons — verify from the log, not from a narrative summary).
- [ ] Do not touch `compute_forward_aggregates`, `resolved_forward_aggregate_evidence`, or `ensure_historical_forward_aggregates_dispatched` — all three stay byte-frozen (binding).

### Frontend (if applicable)
- None. J-07 has no dedicated page; it is proven via the global readiness badge (unchanged) and `/backtest`'s existing evidence display (unchanged). No UI code change is anticipated.

### New user-facing capability
None — this iteration proves an existing reliability guarantee (the service demonstrably survives a memory-pressure event without going down) rather than adding new capability.

### New information displayed
None — the two new measurements (health-poll latency during the warm; the drill's outcome) are written to `reports/perf-budgets.md`, a measurement artifact, not a UI-displayed value.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None — no page, panel, or card changes. The deliverable is first-hand evidence that J-07's own four acceptance steps are all now true, closing the session's last `partial` Must-have journey.

### Blueprint conformance
J-07's existing home (unchanged): global readiness badge (top bar, every page) + `/backtest` (`GET /api/backtest` per-horizon evidence) — a cross-cutting availability guarantee with no dedicated page, per the Information Architecture's "Feature / journey homes" table in `runs/goal-session-ops-hardening/state/blueprint.md`. No new page, nav entry, or route.

### Data-contract additions
None. Both new measurements ride the ALREADY-registered "Page performance budgets" Data Contract row (`reports/perf-budgets.md`, not a served runtime value, no computing module/endpoint of its own) — no new row, no second producer, no second serving path for any existing value.

## OUT OF SCOPE

- **iter-33/g** — Regime Lab's cold `view=pooled` background dispatch (mirroring `/api/backtest`'s iter-32 async pattern) and diagnosing the one HTTP 200 that carried the body "Internal Server Error." A separate, real backend change; deferred to keep this iteration's one risky change confined to the memory-pressure drill (rule 5/6).
- **iter-33/h** — wiring `resolveLabLoadPanel` into the four sibling research labs (`phase-severity-lab`, `regime-phase-factor`, `factor-lab`, `severity-velocity`). Frontend-only, unrelated to J-07; deferred to a dedicated iteration.
- `J-07.json`'s literal `n=8869` stable-assertion / provenance line — framework/test-infra hygiene, non-blocking, carried.
- Any amendment to `docs/goal.md`'s `/api/health` ≤0.1s budget line — settled per "Do not redo": record the honest WARN, never amend.
- `warmup.py:194` badge wording, `prices.py:141`'s whole-`daily_prices` prefill, iter-31/e's Factor-Lab constant-factor residual, iter-32/f's `run_rows` watch item, `test_no_magic_numbers.py` red on `indicators.py`/`forward_testing.py`, UT-04's fresh-install DB fixture, `test_forward_testing_serving_split.py`'s four `is_latest` monkeypatches — all carried, minor, none firing today, none re-planned this iteration.
- `ui-surface-map.md` / `user-visible-changes.md` / demo auto-regeneration after fix-mode UI rounds — framework improvement, out of product scope this iteration.
- Whether `scripts/start-frontend.sh` should join `HOST_GUARD_MARKER_FILES` — explicit owner decision item, non-blocking, not re-planned.

## DEFINITION OF DONE

- [ ] J-07 passes via evaluator scoring: step 2's latency figure is recorded against the ≤0.1s budget with an honest verdict, and step 4's induced-memory-pressure drill has run with the SAME-process liveness confirmed.
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-06, J-08, J-09 remain green — deterministic golden replay + LLM fallback for any journey without a golden on file.
- [ ] No anti-goal violation introduced — specifically AG-10 (the throwaway process is launched only via `scripts/start-backend.sh`, host-guard caps intact, no marker-file diff) and AG-8 (no unbounded ORM load reintroduced anywhere touched).
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-34-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-07 (all four steps, capturing the "Forward-tested evidence" by-group tables per the standing evidence-capture ask, not a top-of-page frame); smoke/regression replay of J-01, J-03, J-04, J-05, J-06, J-08, J-09.
- Unit/integration: a dedicated test that tightens `server.memory_cap_mb` to a level below what a full-horizon warm requires and asserts the existing `MemoryError`-catch-and-continue behavior in `_refresh_ingest_aggregates` fires (not a different, easier failure mode); a control assertion that the SAME override, if set too high to trigger the error, is caught as a test-setup failure rather than silently passing.
- Error cases: the drill's cap-override mechanism must fail loudly (not silently no-op) if the throwaway process cannot actually be launched through `scripts/start-backend.sh`'s host-guard path.

Test-first contract:

- TC-1: given the full deep-basis forward-aggregate warm is running (J-07 step 1) in a live backend process, when `GET /api/health` is polled once per second throughout, then each poll's HTTP status and round-trip latency are recorded and `reports/perf-budgets.md` states plainly whether the max latency stayed ≤0.1s (PASS) or exceeded it (WARN with the measured range), matching the honest-WARN convention already on record for this endpoint.
- TC-2: given a throwaway backend process launched via `scripts/start-backend.sh` with `server.memory_cap_mb` tightened below the level required to complete a full-horizon forward-aggregate warm, when the SAME warm is triggered inside that process, then the warm aborts with a caught `MemoryError` (per the existing `_refresh_ingest_aggregates` per-item handling), not a crash or an unresponsive hang.
- TC-3: given the throwaway process's warm aborted per TC-2, when `GET /api/health` is requested against the SAME process immediately after, then it returns HTTP 200 with no restart performed.
- TC-4: given the throwaway process's warm aborted per TC-2, when a previously-cached read (e.g. `GET /api/backtest` for an already-warmed horizon/asof) is requested against the SAME process, then it returns its previously stored value, not an error or a hang.
- TC-5: given the drill's full sequence (TC-2 through TC-4) completed, when the outcome is written to `reports/perf-budgets.md`, then the record states plainly that the process stayed alive, the abort was honest, and no restart was required — closing J-07 step 4.
- TC-6: given the required-still-passing journeys' golden scripts, when deterministic replay runs against this iteration's build, then J-01, J-03, J-04, J-05, J-06, J-08, J-09 all PASS with zero FAIL rows.
- TC-7: given this iteration makes no code change to `compute_forward_aggregates` / `resolved_forward_aggregate_evidence` / `ensure_historical_forward_aggregates_dispatched`, when their existing byte-identity/AG-3 regression tests are re-run, then they pass unchanged, confirming no accidental scope creep into frozen code.
- TC-8: given the throwaway drill process and its logs, when `logs/backend.log` is inspected for the throwaway process's PID/session, then the log lines independently corroborate the abort and the continued `/api/health` responses (per the iter-26/iter-28 lesson: verify from the log, not from a narrative summary alone).

## NOTES

- If step 4's drill cannot be made to trigger a genuine `MemoryError` reliably within the throwaway process (e.g., because the live data basis's per-horizon warm no longer allocates enough to exceed any safely-tightened cap), the dev handoff must say so explicitly and propose a concrete, still-real mechanism (a lower but still safe cap, or a documented test hook) rather than silently declaring the step done on a non-reproducing run.
- This iteration deliberately does not attempt a GOAL_ACHIEVED verdict — that is the evaluator's call once J-07's evidence is complete and re-scored, per its own methodology.
- Blueprint updated in place: an `iter-34 update (...)` paragraph was appended to `runs/goal-session-ops-hardening/state/blueprint.md`'s narrative history, and the "Page performance budgets" Data Contract row's Notes cell gained one additive sentence for this iteration's two measurements — no Information Architecture change, no new Data Contract row, no `blueprint.reapproval-requested` needed.
