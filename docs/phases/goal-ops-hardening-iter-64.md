# Goal Iteration 64 — Harden the verification substrate: self-renewing J-05 golden, a demo-lane mutation guard, and the J-07 latency attribution

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 64
- **Mode:** next
- **Depth:** lean
- **Frontend Present:** no
- **Target journeys:** J-05, J-07
- **Required-still-passing journeys:** J-01, J-03, J-04, J-06, J-08, J-09
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

Fix the two verification-substrate defects the last two rounds surfaced — J-05's golden self-consuming its own reserved date, and the showcase lane clicking a mutating control after its own precondition steps failed — and separately attribute (without a second heavy ingest job) whether J-07's 1→53 health-latency-breach jump is a reproducible regression or host noise.

## BACKGROUND

Evaluator depth recommendation for iteration 64 is **lean**, and it is binding: the prior verdict (iter-63) was CONTINUE, not ESCALATE/REGRESSION; iter-63's coherence was PASS; consecutive-lean count is 0 of a 6-cadence (not due); and this iteration adds no user-visible capability (no brand-new full-stack journey — goal.md's own Loop Mechanics rule reads "full when an iteration first lands user-visible UI changes", and nothing here does). No full trigger holds — needing tests is never a valid trigger, and this scope is entirely test-harness/tooling maintenance with a nameable blast radius (`scripts/automation/lib/demo_runner.py`, one journey-script JSON, two test-file edits).

Four consecutive rounds (iter-58, iter-59 ×2, iter-62/63, iter-63-audit) have hand-rotated J-05's golden onto a date that the SAME round's own replay lane then consumed, arming a guaranteed false FAIL on a currently-passing required journey next round — the standing lesson from iter-62/iter-63 is explicit that the durable fix is a run-time self-selecting mechanism, not another hand rotation (`journey-scripts/J-05.json`'s own `_notes` say so verbatim; iteration-state's "Do not redo" forbids re-rotating by hand). Separately, iter-63's own demo lane clicked "Start" after its precondition-fill steps failed and launched a real, un-narrated 5-date backfill (iter-63 lesson: "the showcase/demo lane is not read-only"). Both defects live in `demo_runner.py`, which is invoked as a fresh `python3` subprocess each call — unlike `lib/common.sh`/`lib/replay-lane.sh` (sourced once at `goal-iter-lean.sh` startup, per the iter-60 lesson), so both fixes CAN self-verify within this same iteration's own replay/showcase passes. The one item in scope that IS in a sourced bash library (raising `CHAIN_BACKEND_READY_WAIT_S` 60→90 in `lib/common.sh` + `lib/replay-lane.sh`, per iter-63/f and the "Do not redo" note "only its 60s default needs raising") explicitly CANNOT self-verify this round — the spec states that up front per the iter-60 lesson, and iteration 65 must confirm it from its own engine log before the item is closed.

J-07's own metric got materially worse last round (1→53 breaches out of ~1,000, p99 1.259s→3.002s) with the cause explicitly unattributed by the auditor. Availability itself (the journey's actual acceptance clause) was met outright (983/983 HTTP 200, zero 500s/MemoryErrors) both rounds, so this is not a regression on the journey's own tree-level status (iter-63's own assumption-ledger entry reasons this through); it is scored `partial`, unchanged, with the attribution work as the dev-actionable next step (iter-63 next-step item 1). Per the priority rubric's rule 6, the OWNER's 2-second-ceiling policy question stays out of scope — it blocks only the final close, not this attribution step.

## IN SCOPE

### Backend / verification-substrate (tooling only — no product backend code changes)
- [ ] `scripts/automation/lib/demo_runner.py`: add a run-time sentinel-date resolver (token e.g. `{{AUTO_UNSNAPSHOTTED_DATE}}`) usable by `--mode verify`/`--mode record`/`--mode live`. Before a script's steps run, if any step's `fill.text` or `expect.text` equals the token, resolve it ONCE via a read-only query against `apps/backend/data/trendora.db` for a trading day (real `daily_prices` rows present) with 0 `scanner_runs` rows for that as-of, drawn from a bounded historical window; substitute the SAME resolved date string into every step of that script carrying the token (fill targets, expect text, click-target text, and the script's own `name` field). If no eligible date exists in the window, fail the resolution explicitly (never silently reuse a consumed date).
- [ ] `runs/goal-session-ops-hardening/journey-scripts/J-05.json`: replace the hardcoded `2010-11-22` in steps 2/3/13/14 and the `name` field with the sentinel token; append one closing `_notes` entry documenting the switch (existing rotation history stays intact, untouched).
- [ ] `scripts/automation/lib/demo_runner.py`'s `run_record`: once any step's `_do_action` raises (already recorded as a soft note), skip PERFORMING any later `click` step in the same script whose target is a `role: button` (still take its screenshot and log a distinct soft note naming the skip reason) — never invoke a mutating control after a precondition step in the same script has already failed.
- [ ] `scripts/automation/lib/common.sh` (line ~1434) and `scripts/automation/lib/replay-lane.sh` (line ~341): raise the `CHAIN_BACKEND_READY_WAIT_S` default from 60 to 90 at both sites. Self-verification explicitly deferred to iteration 65 (this iteration's own pipeline run sourced the OLD value before the edit lands — iter-60 lesson).
- [ ] `apps/backend/tests/test_data_manager.py::test_missing_data_diagnostic_cooperative_yield_byte_identical`: correct the docstring's "Proven against a PINNED pre-fix reference oracle... the SAME query consumed with NO cooperative yield" claim — only the row-count sanity check (fixture shape, 11 rows) is pre-fix-equivalent; the byte-identical assertion itself compares two POST-fix calls (tiny vs. default batch size, both with the yield present). No assertion/logic change.
- [ ] Execute the opt-in named fault-injection drill, unrun for 4 consecutive rounds: `TRENDORA_RUN_HEAVY_INGEST_TEST=1 pytest apps/backend/tests/test_start_backend_script.py::test_factor_lab_all_survives_repeated_memory_pressure_live -x` (own dedicated spawned backend, separate ports, never the shared dev DB). Record the verbatim result in the dev handoff.
- [ ] Piggyback a 1 Hz `GET /api/health` poll on THIS iteration's own live J-05 backfill (the ingest already required to prove the sentinel mechanism — no separate/duplicate heavy ingest job requested) covering the same heavy-warm finalize window iter-63's drill measured. Record the full distribution (count > 1.0s, count > 2.0s, p50/p90/p99/max, reconciled against `wc -l` of the raw log and the job's own OPEN/CLOSED markers per the iter-57 lesson) as a new dated addendum in `reports/perf-budgets.md`, and state plainly whether the 53-breach count reproduces (real regression) or reverts toward iter-61's near-zero baseline (host noise). No code fix to `factor_lab_all_warm`/`data_manager.py`/`research.py` is attempted this round — this item is attribution only.

### Frontend
- None. No product UI, endpoint, or page changes this iteration.

### New user-facing capability
None — this iteration is entirely verification-substrate/test-harness maintenance plus a diagnostic measurement; product behavior is unchanged.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None. The deliverable is: a self-renewing J-05 golden (no more hand-rotation), a demo-lane guard against mutating on a failed precondition, a raised readiness-wait constant (not yet self-verified), an executed fault-injection drill, a corrected test docstring, and a documented attribution of J-07's latency-breach jump — none of it product-facing.

### Blueprint conformance
No new surfaces — no edit to `runs/goal-session-ops-hardening/state/blueprint.md` this iteration (nothing in scope introduces a page, nav entry, or displayed value).

### Data-contract additions
None.

## OUT OF SCOPE

- Any code fix to `factor_lab_all_warm` / `data_manager.py` / `research.py` for the 1→53 latency jump — this iteration attributes only; a fix (if warranted) is a future iteration's scope, contingent on what the attribution finds.
- The OWNER's 2-second-health-ceiling policy decision (15 rounds asked; J-07 cannot fully close without it) — still pending, not this iteration's to resolve.
- `scripts/automation/browser-qa-phase.sh` line-286-before-272 ordering fix — still OWNER-gated per iteration-state's Active blockers.
- The cost decision on the replay lane's real 15-18 minute ingest every round — still pending owner sign-off; this iteration does not add a SECOND heavy ingest job (the health-poll attribution piggybacks on J-05's own mandatory replay instead of running its own drill).
- A second live J-05 replay within this same iteration to prove the sentinel mechanism is self-renewing end-to-end — proven at the unit level instead (TC-3) to avoid a second ~20-minute ingest job in one lean round; the SAME live proof rides on iteration 65's own natural replay of J-05.
- The Regime Lab (iter-33/g) — deferred again; no capacity this round.
- All other CARRIED backlog items (iter-29/b + badge wording, iter-31/e, iter-32/f, iter-35/k, iter-36/n, iter-37/o, iter-37/q, iter-39/u, iter-46/az, iter-46/ba, iter-47/bd, iter-47/bf, iter-47/bi, iter-48/bj, iter-57/f, iter-57/l, iter-59/g, iter-59/h, iter-59/k, iter-62/e, iter-62/f) — none are small enough to add without breaching lean's nameable blast radius.

## DEFINITION OF DONE

- [ ] J-05's golden replays PASS via the new run-time sentinel-date mechanism, with no hand-edited date in the checked-in file (TC-2)
- [ ] The sentinel resolver is proven self-renewing at the unit level (TC-3)
- [ ] `run_record` never performs a mutating click after a preceding step in the same script failed (TC-4, TC-5)
- [ ] `CHAIN_BACKEND_READY_WAIT_S` default raised to 90 at both sites, with self-verification explicitly deferred to iteration 65 (TC-6)
- [ ] The opt-in named fault-injection test executes and its result is recorded verbatim (TC-7)
- [ ] The docstring correction lands with no assertion/logic change (TC-8)
- [ ] A fresh J-05 walkthrough capture lands, clearing the standing `evidence_makeup` flag (TC-9)
- [ ] Required-still-passing journeys (J-01, J-03, J-04, J-06, J-08, J-09) replay PASS via deterministic replay + LLM fallback (TC-10)
- [ ] AG-9 and AG-10 checked clean; no anti-goal violation introduced (TC-11)
- [ ] The 1→53 health-latency jump is attributed (reproduced or reverted) with the full distribution recorded, piggybacked on J-05's own ingest — no separate heavy job (TC-1)
- [ ] Touched test files pass under pytest with 0 failures (TC-12)
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-64-dev.md`, documenting each item's verbatim result (TC-13)

## TESTING REQUIREMENTS

- Browser: J-05 (deterministic replay of the rewritten golden); required-still-passing set J-01, J-03, J-04, J-06, J-08, J-09 via deterministic replay + LLM fallback. J-07 carries no browser PASS requirement this round (diagnostic-only; stays `partial`).
- Unit/integration: new `_t_`-prefixed cases in `demo_runner.py`'s self-test harness (`python3 scripts/automation/lib/demo_runner.py self-test`) for the sentinel resolver and the `run_record` mutation guard; `apps/backend/tests/test_data_manager.py` (docstring fix, unchanged assertions); `apps/backend/tests/test_start_backend_script.py::test_factor_lab_all_survives_repeated_memory_pressure_live` (opt-in, executed this round).
- Error cases: sentinel resolution with zero eligible dates in the window must fail explicitly (raise/skip with a named reason), never silently reuse a consumed date or an already-snapshotted date.

Test-first contract:

- TC-1: given J-05's own live backfill runs this iteration (required for TC-2) and a 1 Hz `GET /api/health` poll runs for its full duration, when the poll log is reconciled against the job's own OPEN/CLOSED markers and `wc -l`, then `reports/perf-budgets.md` gains a new dated addendum stating the count over 1.0s, count over 2.0s, p50/p90/p99/max, and an explicit conclusion — "reproduces iter-63's 53-breach jump" or "reverts toward iter-61's near-zero baseline" — with no code change to `factor_lab_all_warm` attempted this round.
- TC-2: given `runs/goal-session-ops-hardening/journey-scripts/J-05.json` no longer contains a hardcoded date in steps 2/3/13/14, when the deterministic replay lane runs J-05's golden, then the sentinel resolves to a single trading day with 0 pre-existing `scanner_runs` rows, every step carrying the token receives that SAME date, and the golden reports PASS end to end (steps 1-15, including step 10's "0 already snapshotted" and step 14's "Immutable snapshot — as of <resolved date>").
- TC-3: given a throwaway sqlite fixture seeded with a `scanner_runs` row for the date the resolver most recently returned, when the resolver is invoked again against that fixture, then it returns a DIFFERENT date (not the just-consumed one) with 0 `scanner_runs` rows for it — proven by a new unit test, not a second live 20-minute browser replay.
- TC-4: given a fake `page`/script fixture in `demo_runner.py`'s self-test harness where step N's `fill` raises and step N+1 is a `click` on `role: button`, when `run_record` executes that script, then step N+1's click is NEVER invoked (asserted via a call-count spy), a screenshot is still captured for step N+1, and the results write-up carries a soft note naming the skip.
- TC-5: given this iteration's own showcase/demo lane runs for J-05, when it completes, then querying `data_provider_runs` for rows with `started_at` inside the demo lane's own wall-clock window shows ZERO rows whose corresponding script step had a preceding failed precondition (cross-checked against the lane's own soft-notes log).
- TC-6: given `CHAIN_BACKEND_READY_WAIT_S` currently defaults to 60 in both `lib/common.sh:1434` and `lib/replay-lane.sh:341`, when both defaults are changed to 90, then `grep -n "CHAIN_BACKEND_READY_WAIT_S:-" scripts/automation/lib/*.sh` shows `90` at both sites, and the dev handoff states explicitly that THIS iteration's own replay/showcase passes still ran under the old 60s value (sourced before the edit) — iteration 65 must confirm the new value fired live from its own engine log before this item is marked closed.
- TC-7: given `test_factor_lab_all_survives_repeated_memory_pressure_live` is opt-in and unrun for 4 consecutive rounds, when `TRENDORA_RUN_HEAVY_INGEST_TEST=1 pytest apps/backend/tests/test_start_backend_script.py::test_factor_lab_all_survives_repeated_memory_pressure_live -x` runs against its own dedicated spawned backend, then its PASS/FAIL result and console output are recorded verbatim in the dev handoff, and the shared dev-server `logs/backend.log`'s MemoryError count (excluding lines tagged `injected at fault-injection site`) is confirmed UNCHANGED before/after (the drill's own separate process never touches the shared backend).
- TC-8: given `test_missing_data_diagnostic_cooperative_yield_byte_identical`'s docstring currently claims a "PINNED pre-fix reference oracle" for its byte-identical comparison, when the docstring is corrected to state that only the row-count sanity check (11 rows) is pre-fix-equivalent and the byte-identical assertion compares two post-fix calls, then `pytest apps/backend/tests/test_data_manager.py::test_missing_data_diagnostic_cooperative_yield_byte_identical` still PASSES with its 3 original assertions (grouping shape, byte-identity across batch sizes, `sleep_calls == [0] * 5`) unchanged.
- TC-9: given the showcase/demo lane runs for iteration 64, when it captures J-05, then at least one PNG under `reports/demo/goal-ops-hardening-iter-64/` is tagged `journey: J-05` in the recorded script metadata and its rendered page shows the text "Immutable snapshot — as of" followed by the resolved date, clearing the `evidence_makeup` flag currently held on J-05 in `journey-history.json`.
- TC-10: given J-01, J-03, J-04, J-06, J-08, J-09 are all currently `passing`, when the deterministic replay lane runs their goldens this iteration, then all 6 report PASS with a fresh, byte-distinct evidence frame each (no reuse of a stale screenshot).
- TC-11: given this iteration runs one real ingest job (J-05's backfill) and one opt-in fault-injection drill (its own throwaway backend), when `data_provider_runs` rows created since this iteration's start are queried, then every row shows `provider='seed'` (AG-9), and `git status --porcelain -- config.yaml project-extensions/ host-guard.env` is EMPTY with `config.yaml`'s `memory_cap_mb`/`malloc_arena_max` and `host-guard.env`'s `HOST_GUARD_MEMORY_HIGH`/`BLAS_THREADS` unchanged from their currently-committed values (AG-10).
- TC-12: given `apps/backend/tests/test_data_manager.py` and `apps/backend/tests/test_start_backend_script.py` are the two files touched this iteration, when `pytest apps/backend/tests/test_data_manager.py apps/backend/tests/test_start_backend_script.py` runs (heavy/opt-in cases addressed separately per TC-7), then it reports 0 failures.
- TC-13: given all of TC-1 through TC-12 have run, when the developer writes `docs/handoffs/goal-ops-hardening-iter-64-dev.md`, then it names each item's verbatim result (PASS/FAIL, the attribution conclusion, the fault-injection test's outcome) rather than a summary judgment.

## NOTES

- **Lesson applied (iter-60):** a fix to a `source`d shell library (`lib/common.sh`, `lib/replay-lane.sh`) cannot take effect in the SAME run that edits it. The readiness-wait bump is scoped and flagged accordingly (TC-6); do not mark it closed until iteration 65's own engine log shows `backend readiness == ready` inside a ≥60s (pre-bump-consistent) window with the new constant confirmed live.
- **Lesson applied (iter-62/iter-63):** hand-rotating a state-mutating golden's date cannot hold while the SAME golden is replayed every round by the lane — this is the FOURTH consecutive round the prior fix was only a rotation, not a mechanism; this iteration builds the run-time mechanism the notes in `journey-scripts/J-05.json` have called for since iter-63-audit.
- **Lesson applied (iter-57):** any drill claiming "N polls, zero/K failures" must reconcile its segment counts against the raw log's own `wc -l` and the job's OPEN/CLOSED markers before being written up — apply this to TC-1's addendum, not hand-picked windows.
- **Lesson applied (iter-63, 2 of 2):** the demo/showcase lane is not read-only; a failed precondition step must not be followed by a mutating click. TC-4/TC-5 close this at the source rather than relying on the lane never failing its own fills again.
- **Owner items carried, unchanged this round:** the 2-second health-ceiling policy question (15th round asked); the `browser-qa-phase.sh` line-286-before-272 fix; the cost/cadence of running a real heavy ingest job every round. None are in scope here.
