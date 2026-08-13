# Goal Iteration 74 — Assemble J-07's VmPeak margin phase-by-phase, no uninterrupted run required

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 74
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
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills, full-universe rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched only via the project launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those scripts MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env` whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`, `malloc_arena_max`). Never remove, weaken, or bypass these caps: stripping a HOST-GUARD marked block from a launch script is a REGRESSION regardless of test outcomes. The ceilings are a physical constraint of the current host (two instant hardware resets under all-core vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance budget to optimize away. *(Owner amendment 2026-07-31, two corrections of record — nothing above is relaxed: `memory_cap_mb` / `malloc_arena_max` live in `config.yaml`, not in `host-guard.env`; and the 2026-07-20/21 resets were subsequently attributed to an uncorrected hardware data-fabric fault (`host-guard.env`, 2026-07-30), so the ceiling VALUES are an owner-set envelope — re-set by the dated entry in "Additional binding notes" — while this paragraph's prohibition on agents removing, weakening, or bypassing caps is unchanged.) *(critical)*

## GOAL

Get J-07 step 3's real peak-memory (VmPeak) margin by joining telemetry the codebase already produces — the `_MemSampler` background poller and `_refresh_ingest_aggregates`'s existing per-phase timing log lines — into a phase-by-phase profile, so the answer no longer requires one uninterrupted end-to-end hour this shared host has now defeated four times running.

## BACKGROUND

Three full-length pressure attempts (10, 8, 5 workers) and one pressure-free clean arm all failed to
produce a completed, realistic-pressure VmPeak reading last round (`reports/perf-budgets.md` Addendum 38):
each pressure attempt collided with the separately-disclosed uvicorn admission-control 503 cliff before
the job finished, and the clean arm ran 26 minutes without a single breach (VmPeak 2,390,872 kB /
2,334.8 MB, 71.5% margin) but never reached the memory-heaviest finalize-tail phase before its own 1,800s
bound — the live dev DB has grown to ~8.4 GB and the `rebuild` job kind this drill uses runs the FULL
2005-2026 basis regardless of the requested date range, so a single clean pass now takes far longer than
the historical 16-34 minute figures on record. The binding "Do not redo" list already forbids retrying
"one uninterrupted full-`rebuild` run on this host" a further time. The iter-73 evaluator's own next-step
item (1) orders exactly the alternative this iteration builds: "record peak memory phase by phase during
the heavy job, using the timers that already exist in the code, so the answer can be assembled from short
runs" — with a **binding stop rule**: if this attempt also fails, do not try a fourth method; put the
choice to the owner (accept the 2,334.8 MB / 71.5% quiet-run figure as the record, or relax step 3's bar).

This is directly iter-68's lesson applied to memory instead of latency: "before commissioning a new
instrument, join the instruments you already have." Two instruments already exist and need no new code:
`_MemSampler` (`apps/backend/tests/test_start_backend_script.py`) independently polls
`/proc/<pid>/status` every 0.25s with a wall-clock `time.time()` timestamp per sample, and survives an
interrupted/killed/timed-out run because `_write_run_evidence` persists its CSV from a `finally` block
(the SAME instrument iter-32/38/73 already used — no second sampler). `_refresh_ingest_aggregates`
(`apps/backend/app/engine/data_manager.py`) already logs a wall-clock-timestamped line at each of its
~9 finalize-tail phase boundaries — `logger.info("J-05 finalize-tail phase timing: job=%s phase=%s
elapsed=%.2fs", prog.job_id, "<phase_name>", time.monotonic() - _phase_t0)` — for
`coverage_membership_timeline_refresh`, `per_date_coverage_warm`, `market_phase_warm`,
`forward_aggregates_warm` (per horizon), `research_hot_keys_warm`, `index_series_warm`,
`availability_heatmap_warm`, `factor_lab_all_warm`, and `drawdown_expectations_warm`. Joining the two —
`_MemSampler`'s epoch-stamped samples against `logs/backend.log`'s phase-timer lines — lets a phase-level
VmPeak-at-completion figure be read off even a run that gets cut short mid-way, so a full continuous
completion is no longer required to get real, usable numbers: whatever phases DID complete before any
interruption still leave a durable, attributable reading. iter-66's lesson (log timestamps can be
host-local while other artifacts are UTC) applies here too — confirm both timestamp sources share the
same clock/timezone before joining them, since this join is new even though neither instrument is.

Per the priority rubric: no journey regressed (rule 1); the last coherence verdict (iter-73) was PASS, so
no consolidation is mandated (rule 2); J-07 is this session's sole non-passing Must-have journey and this
is the evaluator's own ranked item (1) — the last thing standing between it and `passing` (rule 3); this
is the smallest available spec that could move J-07's status, reusing existing instruments rather than
building anything new (rule 4). Rule 5 (never bundle two risky changes) is why this spec deliberately
excludes the evaluator's item (2), repairing the QA frontend that intermittently serves unstyled,
asset-less pages (the reason J-08/J-09 have carried two rounds without fresh verification) — that is a
different risk domain (frontend/harness serving) from this round's one risky action (a new
telemetry-joining measurement technique, and a possible `config.yaml` pool/cache tune), and bundling them
would make a joint failure undiagnosable. It stays queued for its own round, per the evaluator's own
ordering. Two small, zero-risk companion corrections ride along, matching this session's own discipline
of not letting a wrong number sit on record once found: Addendum 38's inflated test count (states "72
… all still pass"; the module collects 18 tests, 12 passed, 1 skipped — confirmed in Addendum 38's own
"What was built" section) and `docs/goal.md`'s stale "Ground truth (measured 2026-07-18)" block (DB size
now ~8.4 GB, not ~811 MiB; `rebuild` ignores the requested date range — see assumptions.md `## iter-74 —
goal-decomposer` for why this factual-appendix correction is treated as ordinary developer documentation
work, distinct from the owner-gated journeys/anti-goals).

Depth is LEAN, matching the evaluator's binding recommendation. No full trigger holds: the prior verdict
was CONTINUE (not ESCALATE); the prior coherence verdict was PASS; the consecutive-lean count is 1 of a
cadence-6 threshold (not due); and this is a continuation of existing J-07 work with no brand-new
full-stack journey, no UI change, and (in the base case) no code change at all — the phase-by-phase join
can be done entirely test-side against telemetry that already exists, and any `config.yaml` tune (only if
the margin proves thin) is an infrastructure value change, not a new/changed Data-Contract producer or
endpoint.

## IN SCOPE

### Backend
- [ ] Build a live drill (extending the existing `test_start_backend_forward_aggregate_warm_under_realistic_pool_pressure` or a new sibling in `apps/backend/tests/test_start_backend_script.py`) that runs the SAME full deep-basis forward-aggregate warm under the current pool (`pool_size=24`, `max_overflow=44`) at realistic concurrency, launched only via `scripts/start-backend.sh` (never `dev.sh` — iter-71's binding lesson), reusing the existing `_MemSampler` and `_HealthPoller` — no new instrument.
- [ ] Join `_MemSampler`'s timestamped VmPeak samples against `_refresh_ingest_aggregates`'s existing "J-05 finalize-tail phase timing" log lines in `logs/backend.log` to produce a peak-VmPeak-at-completion figure for EACH finalize-tail phase, durable even if the drill is interrupted/times out before every phase completes (`_write_run_evidence`'s existing finally-block persistence already makes the sample side durable; confirm both timestamp sources share one clock before joining, per iter-66's lesson).
- [ ] Record the per-phase breakdown and the assembled overall peak-memory figure, plus its percentage margin against `server.memory_cap_mb` (8192 MB), in a new dated addendum in `reports/perf-budgets.md` (following the Addendum 13/32-38 convention).
- [ ] If the margin is <20% headroom (peak VmPeak > 6,553.6 MB — iter-73's own binding threshold), lower `config.yaml`'s `database.pragmas.cache_size` and/or `pool_size`/`max_overflow` until a recomputed worst-case retained-connection footprint restores ≥20%, while keeping `pool_size + max_overflow >= server.limit_concurrency` (`config.py:2778`'s boot-time invariant — binding "Do not redo," never weaken or remove).
- [ ] If the margin is ≥20%, state that explicitly in the addendum ("margin comfortable, no config change") and leave `config.yaml` byte-unchanged.
- [ ] **Binding stop rule:** if the phase-by-phase join also fails to produce a usable number (e.g. no phase completes before every attempt is defeated by host contention), do not attempt a further/fourth method this round — record the failure plainly in the dev handoff and state the two-way choice for the owner (accept the recorded 2,334.8 MB / 71.5% quiet-run figure as final, or relax step 3's bar) exactly as the stop rule requires.
- [ ] Correct `reports/perf-budgets.md` Addendum 38's "72 tests in this module's non-heavy-ingest scope … all still pass" claim to the true counts (18 collected / 12 passed / 1 skipped), confirmed by a fresh `pytest --collect-only` count.
- [ ] Correct `docs/goal.md`'s "Ground truth (measured 2026-07-18)" block: replace the stale ~811 MiB DB-size figure with a freshly measured size, and add the fact that `rebuild` runs the full committed 2005-02-25 → 2026-08-03 range regardless of the requested dates — each fact cited to its measurement/source.
- [ ] Any process stopped during this round's drills is stopped by exact PID, never a broad-pattern `pkill -f` against a live drill's own backend — closing iter-73/d's disclosed process-hygiene defect (an over-broad `pkill -f` killed iter-73's own in-progress 18+ minute drill).

### Frontend (if applicable)
- None. No UI change this iteration.

### New user-facing capability
None — this iteration changes no user-visible behavior. It closes an internal safety-margin measurement gap; the app's observable behavior (badge, pages, job flows) is unchanged whether or not a config value moves.

### New information displayed
None.

### New user actions
None.

### UI surface changes
None.

### Product surface delta
None visible to a user. Internally, J-07 (a cross-cutting availability guarantee with no dedicated page — global readiness badge + `/backtest`, per the blueprint's Information Architecture) either moves from `partial` to `passing` (if the phase-by-phase margin is comfortable, or was made comfortable by a config tune) or stays `partial` with the true, freshly phase-attributed number on record — either way it is no longer resting on the stale 2,334.8 MB partial-run figure alone.

### Blueprint conformance
No new page or nav entry. J-07 keeps its existing homes per `blueprint.md`'s Information Architecture table: the global readiness badge (top bar, every page) and `/backtest` (Backtest nav section). The measurement artifact is `reports/perf-budgets.md`, already registered in the Data Contract as "N/A — a measurement artifact, not a served runtime value." `docs/goal.md`'s Ground Truth correction is a factual documentation fix, not a Data-Contract or Information-Architecture change.

### Data-contract additions
None. No new displayed value, no new computing module, no new endpoint. Any `config.yaml` pool/cache-size adjustment (only if TC-2/TC-3 below fires) is infrastructure configuration, not a Data-Contract row — it changes an input to the ALREADY-registered `reports/perf-budgets.md` measurement artifact, not a value's producer or serving endpoint. `blueprint.md` is updated with a narrative note only (already applied — see NOTES).

## OUT OF SCOPE

- Repairing the QA frontend that intermittently serves unstyled, asset-less pages (iter-72/c, iter-73's carried defect, the evaluator's own next-step item (2)) — a separate risky change in a different domain (frontend/harness serving), deliberately not bundled with this round's memory-measurement action per rule 5. It stays queued as the very next round's target once this round lands.
- Regenerating the J-05..J-09 goldens as a fix for the replay FAILs — binding "Do not redo": the cause is the asset-less QA frontend, not selector drift; regenerating a script cannot fix a broken frontend.
- Rendering `stale_for_s` on the badge/preflight banner (iter-72/f) — binding "Do not redo": queued for its own FULL-depth round since it is this cycle's first user-visible UI change; not this round.
- Diagnosing or fixing the separately-disclosed uvicorn `--limit-concurrency` admission-control 503 streak (`reports/perf-budgets.md` Addendum 37/38) — a different, already-flagged issue (GIL/event-loop scheduling under sustained CPU-bound work), not this round's memory/pool question. If this round's own drill reproduces it, name it as that known, distinct issue rather than folding a fix into this iteration's scope.
- B-1107 (bounding how many heavy computations may run at once) — owner decision, not yet sanctioned.
- The 2-second health-ceiling policy question (long jobs vs. short jobs only) — owner decision.
- The `scripts/automation/browser-qa-phase.sh` one-line ordering-bug fix — awaiting owner permission.
- Any cost-budget decision — 13 consecutive over-budget rounds is an owner-facing question, not something this spec resolves by cutting the measurement short.
- J-05's/J-07's `[NEW]` walkthrough steps and the demo recorder repair (5 of 8 steps fail their own actions) — carried, not this round's goal.
- J-06's page timings into `reports/perf-budgets.md` (4th round owed) — carried, not this round's goal.
- iter-33/g, the Regime Lab — deferred a 40th time; do not schedule without owner direction (binding "Do not redo").
- Any code-level touch to `compute_readiness`/`compute_preflight`/`_tick_and_cache` or the readiness serve-stale + post-lock-recheck mechanism — DONE per the binding "Do not redo" list; not this round's concern.
- Any change to `compute_forward_aggregates` or any other canonical aggregate producer — this iteration reads/joins existing telemetry only; it does not touch the warm computation itself.

## DEFINITION OF DONE

- [ ] J-07 step 3 has a phase-by-phase-assembled VmPeak profile — obtained by joining `_MemSampler`'s samples against `_refresh_ingest_aggregates`'s existing phase-timer log lines, durable even through an interrupted drill — recorded in a new dated `reports/perf-budgets.md` addendum, with the margin against `memory_cap_mb=8192` stated.
- [ ] If the margin was <20%, `config.yaml`'s pool/cache-size values are adjusted and the boot-time `pool_size + max_overflow >= server.limit_concurrency` invariant still holds, verified by `test_config.py`'s existing boot-invariant tests passing.
- [ ] If the phase-by-phase method also fails (binding stop rule), the failure and the owner's two-way choice are recorded plainly — never silently re-carried, never a fourth method attempted this round.
- [ ] `reports/perf-budgets.md` Addendum 38's test-count claim is corrected to 18 collected / 12 passed / 1 skipped.
- [ ] `docs/goal.md`'s "Ground truth (measured 2026-07-18)" block is corrected (DB size, `rebuild` full-range behavior).
- [ ] Target journey J-07 passes via browser-qa-agent, OR — per the binding stop rule — its gap is re-recorded with the fresh phase-level evidence and the owner's two-way choice, never silently re-carried as before.
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-06, J-08, J-09 remain green (deterministic replay + LLM fallback); any replay FAIL is reconciled by opening its own frame/log (never accepted as "transient/selector drift" without evidence, per iter-72's and iter-73's own lessons).
- [ ] No anti-goal violation introduced — AG-10's caps stay declared and enforced (never removed/weakened), AG-9 ingest stays seed-only, no unbounded whole-table load is introduced (AG-8).
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-74-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-07 (re-verification of step 3 specifically; steps 1/2/4 carried on iter-73's durable evidence unless this round's own drill contradicts them). J-01, J-03, J-04, J-05, J-06, J-08, J-09 via deterministic replay with LLM fallback on any FAIL.
- Unit/integration: `apps/backend/tests/test_start_backend_script.py` (the phase-by-phase VmPeak join), `apps/backend/tests/test_config.py` (pool-invariant tests, only re-asserted if TC-3 fires).
- Error cases: a config edit that would drop `pool_size + max_overflow` below `server.limit_concurrency` must raise `ConfigError` at boot (already-covered invariant — must stay covered, never weakened).

Test-first contract:

- TC-1: given the backend launched via `scripts/start-backend.sh` with host-guard caps applied (`memory_cap_mb=8192`, `malloc_arena_max=2`, confirmed by the boot header in `logs/backend.log`) and the current pool (`pool_size=24`, `max_overflow=44`), when a full deep-basis forward-aggregate warm runs with `_MemSampler` polling `/proc/<pid>/status` throughout, then EACH of `_refresh_ingest_aggregates`'s ~9 finalize-tail phases (`coverage_membership_timeline_refresh`, `per_date_coverage_warm`, `market_phase_warm`, `forward_aggregates_warm` per horizon, `research_hot_keys_warm`, `index_series_warm`, `availability_heatmap_warm`, `factor_lab_all_warm`, `drawdown_expectations_warm`) has its own recorded VmPeak-at-completion figure, obtained by joining `_MemSampler`'s CSV samples against that phase's "J-05 finalize-tail phase timing" log line in `logs/backend.log` — no new/second sampling instrument.
- TC-2: given TC-1's per-phase figures, when the maximum across all completed phases is taken as the assembled peak VmPeak for the whole warm, then that figure and its percentage margin against `server.memory_cap_mb` (8192 MB) are recorded in a new dated `reports/perf-budgets.md` addendum, alongside the per-phase breakdown table.
- TC-3: given TC-2's margin is <20% headroom (peak VmPeak > 6,553.6 MB), when the round applies a fix, then `config.yaml`'s `pragmas.cache_size` and/or `pool_size`/`max_overflow` are lowered until a recomputed worst-case retained-connection footprint restores ≥20% margin, AND `pool_size + max_overflow` stays ≥ `server.limit_concurrency` (64), verified by `test_config.py`'s boot-time-invariant tests passing.
- TC-4: given TC-2's margin is ≥20%, when the addendum is written, then `config.yaml` is left byte-unchanged and the addendum states "margin comfortable, no config change."
- TC-5 (binding stop rule): given the phase-by-phase join ALSO fails to produce a usable per-phase VmPeak profile this round (e.g. every attempt is defeated by host contention before even one phase's log line and sample window can be joined), when that outcome is reached, then NO further/fourth measurement method is attempted this round — the dev handoff records the failure plainly and states the two-way choice for the owner (accept the recorded 2,334.8 MB / 71.5% quiet-run figure as the final record for J-07 step 3, or relax step 3's bar), and J-07's gap field names that choice first.
- TC-6: given `reports/perf-budgets.md` Addendum 38's "72 tests in this module's non-heavy-ingest scope … all still pass" claim, when the developer corrects it, then the addendum states the true collected/passed/skipped counts (18 collected / 12 passed / 1 skipped), confirmed by a fresh `pytest --collect-only` count cited in the correction.
- TC-7: given `docs/goal.md`'s "Ground truth (measured 2026-07-18)" block states "DB ~811 MiB" and is silent about `rebuild`'s range behavior, when the developer corrects it, then the block states a freshly measured DB file size and the fact that `rebuild` runs the full committed range (2005-02-25 → 2026-08-03) regardless of the requested dates, each fact cited to its measurement/source.
- TC-8: given the six Required-still-passing journeys touched by this iteration's shared surfaces (J-01, J-03, J-04, J-05, J-06, J-08, J-09), when deterministic replay/browser-qa runs this iteration, then each either passes on fresh evidence or (for J-08/J-09, if the replay lane is still serving unstyled asset-less pages per the carried, unrepaired defect) is held at `passing` on evidence durability exactly as iter-73 documented — none moves from `passing`/`already_passing` to `failing`, and any replay FAIL is reconciled by opening its own frame/log before being attributed to "transient load" or "selector drift."
- TC-9: given AG-10's declared host-guard caps and the `pool_size + max_overflow >= limit_concurrency` boot invariant, when this iteration's diff is inspected (`git status --porcelain -- config.yaml project-extensions/ scripts/`), then only the intended pool/cache-size lines (if TC-3 fired) appear, and every declared cap value is present and byte-unchanged.
- TC-10: given any process started for this round's drills, when a process needs to be stopped, then it is stopped by its exact PID — never a broad-pattern `pkill -f` capable of matching the drill's own live backend — closing iter-73/d's disclosed process-hygiene defect.

## NOTES

- **Assumption logged:** whether `docs/goal.md`'s "Ground truth" engineering-appendix block (distinct from its owner-gated journeys/anti-goals) is ordinary developer-correctable documentation — see `runs/goal-session-ops-hardening/state/assumptions.md`, entry `## iter-74 — goal-decomposer`.
- **Lessons applied:** iter-68's lesson ("before commissioning a new instrument, join the instruments you already have") is this iteration's whole method. iter-66's lesson (host-local vs. UTC timestamp mismatches can silently corrupt a phase-attribution join) — verify `_MemSampler`'s epoch timestamps and `logs/backend.log`'s log-line timestamps share one clock/timezone before joining. iter-71's lesson (score J-04/J-06/J-07 only from a `scripts/start-backend.sh` drill, never `dev.sh`). iter-72's second lesson and iter-73's own lesson (never accept "transient/concurrent load" or "selector drift" for a replay FAIL without opening the frame/log first — a contiguous block of identical broken frames means the environment moved, not the product).
- **Process-hygiene caution (iter-73/d):** an over-broad `pkill -f` cleanup command killed iter-73's own 18+ minute in-progress drill backend last round. Stop any process by exact PID this round, not by pattern.
- **Owner items still open, not this round's job to resolve:** the 2-second health-ceiling policy (long vs. short jobs), B-1107 (limiting concurrent heavy computes), the `browser-qa-phase.sh` ordering-bug fix permission, and the now-13-consecutive-round cost overrun. Do not silently ignore them — the evaluator should keep asking in writing.
- **Blueprint kept current:** `runs/goal-session-ops-hardening/state/blueprint.md` already received a short additive narrative note (top-of-file "iter-74 update" paragraph, plus one sentence appended to the "Page performance budgets" row's Notes) — no Data Contract row's computing module/endpoint changes, no Information Architecture change, so no re-approval file is needed.
- If TC-1's join still cannot produce even a single phase's usable reading (e.g. the drill is defeated before the first phase's log line is even written), record that honestly as this round's own finding per TC-5's stop rule rather than forcing a number — the goal is a trustworthy measurement, not a clean-looking one.
