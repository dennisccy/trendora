# Goal Iteration 73 — Measure real peak memory under the resized DB pool, close J-07 step 3

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 73
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
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills, full-universe rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched only via the project launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those scripts MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env` whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`, `malloc_arena_max`). Never remove, weaken, or bypass these caps: stripping a HOST-GUARD marked block from a launch script is a REGRESSION regardless of test outcomes. *(critical)*

## GOAL

Measure the process's real peak memory (VmPeak) under the iter-72-resized 68-connection DB pool at realistic concurrency during a full deep-basis forward-aggregate warm, record the margin against `server.memory_cap_mb` in `reports/perf-budgets.md`, and — only if that margin is thin — tune `pragmas.cache_size`/`pool_size`/`max_overflow` to restore it, closing J-07's last open acceptance step.

## BACKGROUND

The iter-72 evaluator re-derived the round's own numbers and confirmed J-07's availability step (step 2) and its background-refresh honesty (readiness cache) are genuinely fixed, but stopped short of `passing` on one narrow gap: iter-72 doubled the DB connection pool (`pool_size`+`max_overflow` 30 → 68) to fix pool exhaustion, and each pooled sqlite connection carries a 256 MB `pragmas.cache_size` page cache under an unchanged 8192 MB `ulimit -v` — a retained-connection worst case that moved from 2.5 GB to 6 GB against a warm whose last recorded VmPeak was 3.69 GB (iter-38). The drill that proved step 2 clean "only ever opened a handful of connections, so the new ceiling was never exercised" (iter-72 eval.md item (5)) — this is the evaluator's binding next-step item (1) and, per the iteration-state digest, "the only thing between J-07 and `passing`." Per the priority rubric: no journey regressed (rule 1); the last coherence verdict was PASS, so no consolidation is mandated (rule 2); J-07 is this session's sole non-passing journey and closing it is a pure unblock (rule 3); this is also the smallest available spec that moves a journey's status (rule 4). The evaluator's next-step also names two OTHER items — rendering `stale_for_s` on the badge (item 2, explicitly scoped to its own future FULL-depth round since it is this cycle's first user-visible UI change) and restoring a trustworthy replay baseline by fixing why the QA frontend served unstyled pages (item 3) — both deliberately EXCLUDED here per rule 5 (never bundle two risky changes): this round's one risky action is the pool/memory measurement-and-possible-tuning; a second, unrelated risky change to the QA harness stays a separate round's action.

Two lessons apply directly. **iter-72's lesson:** "a connection-pool resize is a MEMORY change, not just a concurrency change... whenever a diff changes pool size, worker count, or a per-connection/per-thread cache, re-measure peak memory before carrying any prior memory evidence forward" — this iteration IS that re-measurement. **iter-71's lesson:** any drill scoring J-04/J-06/J-07 must run on `scripts/start-backend.sh`, never `scripts/dev.sh` — `logs/backend.log` must show the `start-backend.sh` boot header with `memory_cap_mb`/`malloc_arena_max`/host-guard values, or the drill is invalid evidence. A third, more recent finding must also be respected: `reports/perf-budgets.md` Addendum 37 ("New finding") discloses that sufficiently high COMBINED request pressure (beyond the already-clean 1 Hz health-poll + backtest-check load) can trigger a *separate*, already-disclosed uvicorn `--limit-concurrency` admission-control 503 streak, unrelated to the DB pool/memory question this round targets. Since this round deliberately drives concurrent load higher (to actually exercise the 68-connection ceiling), the drill design must generate DB-pool pressure without conflating it with that separate, out-of-scope failure mode — see TESTING REQUIREMENTS TC-8.

Depth is LEAN, matching the evaluator's binding recommendation: this is backend/config-only work (no UI change), touches one measurement instrument plus at most one config file, and none of the four full triggers hold — the prior verdict was CONTINUE (not ESCALATE), the prior coherence verdict was PASS, consecutive-lean count is 0 of a cadence-6 threshold, and no brand-new full-stack journey is in play.

## IN SCOPE

### Backend
- [ ] Design and run a live drill, launched only via `scripts/start-backend.sh`, that runs a full deep-basis forward-aggregate warm (the same warm J-07 step 1 names) while concurrently holding a realistic number of pooled DB connections open (materially closer to the 68-connection ceiling than "a handful") — reuse the existing `_MemSampler`/`_HealthPoller` instrumentation in `apps/backend/tests/test_start_backend_script.py` (the same `/proc/<pid>/status` VmPeak sampler already used for the iter-32/iter-38 measurements) rather than building a second instrument.
- [ ] Record the drill's peak VmPeak and its margin against `server.memory_cap_mb` (8192 MB) in a new dated addendum in `reports/perf-budgets.md`, following the existing addendum convention (Addendum 13, 32-37).
- [ ] If the measured margin is thin (<20% headroom — see assumptions.md iter-73 for the threshold's grounding), lower `config.yaml`'s `database.pragmas.cache_size` and/or `database.pool_size`/`max_overflow` until a recomputed worst-case retained-connection footprint restores ≥20% margin, while keeping `pool_size + max_overflow >= server.limit_concurrency` (the existing `config.py:2778` boot-time invariant — binding "Do not redo," never weaken or remove it).
- [ ] If no config change is needed, state that explicitly in the addendum ("margin comfortable, no config change") rather than leaving the question open.
- [ ] Confirm on the SAME drill that `GET /api/health` stays fully responsive (every poll HTTP 200 within the existing ≤2 s Bounded Compute Window ceiling, `reports/perf-budgets.md` "Bounded background-compute window (BCW)" entry) and that `logs/backend.log` shows zero `QueuePool ... timeout` lines and zero `MemoryError`/`Traceback` lines — this re-confirms J-07 step 2 and J-05 step 4 are not regressed by any config change made here.

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
None visible to a user. Internally, J-07 (a cross-cutting availability guarantee with no dedicated page — global readiness badge + `/backtest`, per the blueprint's Information Architecture) moves from `partial` to `passing` if the measured margin is comfortable (or stays `partial` with the true, freshly-measured number on record if not — either way it is no longer carried on a durability assumption iter-72 itself broke).

### Blueprint conformance
No new page or nav entry. J-07 keeps its existing homes per `blueprint.md`'s Information Architecture table: the global readiness badge (top bar, every page) and `/backtest` (Backtest nav section). The measurement artifact itself is `reports/perf-budgets.md`, already registered in the Data Contract as "N/A — a measurement artifact, not a served runtime value."

### Data-contract additions
None. No new displayed value, no new computing module, no new endpoint. Any `config.yaml` pool/cache-size adjustment is infrastructure configuration, not a Data Contract row — it changes an input to the ALREADY-registered `reports/perf-budgets.md` measurement artifact, not a value's producer or serving endpoint. `blueprint.md` is updated with a narrative note only (see NOTES).

## OUT OF SCOPE

- Rendering `stale_for_s` on the badge/preflight banner (iter-72/f, audit B4) — explicitly deferred to its own FULL-depth round per the evaluator's next-step item (2); this cycle's first user-visible UI change needs full review capacity this lean round is not scoped for.
- Restoring a trustworthy deterministic-replay baseline (iter-72/c: fixing why the QA frontend served unstyled pages, re-running the goldens on a quiet host, disclosing J-01's undisclosed golden edits) — a separate risky change to the QA harness, deliberately not bundled with this round's DB-pool/memory action per rule 5.
- Diagnosing or fixing the separately-disclosed uvicorn `--limit-concurrency` admission-control 503 streak (`reports/perf-budgets.md` Addendum 37 "New finding") — a different, already-flagged root cause (GIL/event-loop scheduling under sustained CPU-bound work), not this round's memory/pool question. If this round's own concurrency drill reproduces it, name it as that known, distinct issue (TC-8) rather than folding a fix into this iteration's scope.
- B-1107 (bounding how many heavy computations may run at once) — owner decision, not yet sanctioned.
- The 2-second health-ceiling policy question (long jobs vs. short jobs only) — owner decision.
- The `scripts/automation/browser-qa-phase.sh` one-line ordering-bug fix — awaiting owner permission.
- Any cost-budget decision — 12 consecutive over-budget rounds is an owner-facing question, not something this spec resolves by cutting the measurement short.
- TC-10's `/data` honest-fallback screenshot and the unused unguarded fault hook at `apps/backend/app/api/data.py:119` (iter-72/b) — small, "ride along, never the goal" per the evaluator; may be captured opportunistically during this round's own drill session if convenient, but is not a Definition-of-Done item and must not expand this round's one risky action.
- J-05/J-07 walkthrough recording and any demo-recorder repair (iter-72's own finding: 5 of 8 recorder steps fail their own actions) — carried, not this round's goal.
- iter-33/g, the Regime Lab — deferred a 39th time; do not schedule without owner direction (binding "Do not redo").
- Any code-level touch to `compute_readiness`/`compute_preflight`/`_tick_and_cache` or the readiness serve-stale + post-lock-recheck mechanism — DONE per the binding "Do not redo" list; this iteration only re-exercises it under load, never modifies it.

## DEFINITION OF DONE

- [ ] J-07 step 3 has a fresh, real (not durability-carried) VmPeak measurement taken under the current 68-connection pool at realistic concurrency, with its margin against `memory_cap_mb=8192` recorded in a new dated `reports/perf-budgets.md` addendum.
- [ ] If the margin was thin (<20%), `config.yaml`'s pool/cache-size values are adjusted and the boot-time `pool_size + max_overflow >= server.limit_concurrency` invariant still holds, verified by the existing `test_config.py` tests passing (`test_real_config_db_pool_covers_server_concurrency`, `test_db_pool_below_server_concurrency_raises`, `test_db_pool_exactly_covering_server_concurrency_is_valid`).
- [ ] The SAME drill shows zero `GET /api/health` non-answers and zero non-200s within the ≤2 s BCW ceiling, and zero `QueuePool`/`MemoryError`/`Traceback` lines in `logs/backend.log` — J-07 step 2 and J-05 step 4 are not regressed by anything this round changes.
- [ ] Target journey J-07 passes via browser-qa-agent, OR — if the memory margin turns out thin enough that a config change alone cannot restore it within this round's one risky action — J-07's gap is re-recorded with the fresh, real number and a clearly named remaining action for the next round (never silently re-carried as before).
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-05, J-06, J-08, J-09 remain green (deterministic replay + LLM fallback).
- [ ] No anti-goal violation introduced — AG-10's caps stay declared and enforced (never removed/weakened), AG-9 ingest stays seed-only, no unbounded whole-table load is introduced (AG-8).
- [ ] Unit tests pass; no regressions.
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-73-dev.md`.

## TESTING REQUIREMENTS

- Browser: J-07 (full re-verification of steps 1-4); J-01, J-03, J-04, J-05, J-06, J-08, J-09 via deterministic replay with LLM fallback on any FAIL.
- Unit/integration: `apps/backend/tests/test_start_backend_script.py` (VmPeak/health-drill assertions), `apps/backend/tests/test_config.py` (pool-invariant tests), any new/extended concurrency-drill test.
- Error cases: a config edit that would drop `pool_size + max_overflow` below `server.limit_concurrency` must raise `ConfigError` at boot (already-covered invariant — must stay covered, never weakened).

Test-first contract:

- TC-1: given the backend launched via `scripts/start-backend.sh` with host-guard caps applied (`memory_cap_mb=8192`, `malloc_arena_max=2`, confirmed by the boot header in `logs/backend.log`) and the current pool (`pool_size=24`, `max_overflow=44`), when a full deep-basis forward-aggregate warm runs concurrently with a realistic number of simultaneous DB-connection-holding requests materially closer to the 68-connection ceiling than a handful, then `/proc/<pid>/status`'s VmPeak is sampled at ≥1 Hz throughout the drill and its maximum value plus the percentage margin against 8192 MB is recorded in a new dated addendum in `reports/perf-budgets.md`.
- TC-2: given TC-1's recorded margin, when the margin is ≥20% (peak VmPeak ≤ 6,553.6 MB), then `config.yaml`'s `database.pool_size`, `database.max_overflow`, and `database.pragmas.cache_size` are left unchanged and the new addendum states "margin comfortable, no config change."
- TC-3: given TC-1's recorded margin is <20% (peak VmPeak > 6,553.6 MB), when the round applies a fix, then `config.yaml`'s `pragmas.cache_size` and/or `pool_size`/`max_overflow` are lowered until a recomputed worst-case retained-connection footprint restores ≥20% margin, AND `pool_size + max_overflow` stays ≥ `server.limit_concurrency` (64), verified by `test_config.py`'s boot-time-invariant tests passing.
- TC-4: given the SAME drill as TC-1, when `GET /api/health` is polled once per second throughout, then every poll answers HTTP 200 within the committed ≤2 s BCW ceiling (`reports/perf-budgets.md`'s existing "Bounded background-compute window (BCW)" entry) — zero non-answers, zero non-200s, matching iter-72's clean 1,315/1,315 result.
- TC-5: given the SAME drill window, when `logs/backend.log` is inspected for that window, then it contains zero `QueuePool ... timeout`/overflow lines and zero `MemoryError`/`Traceback` lines.
- TC-6: given this round's config state (unchanged or adjusted per TC-2/TC-3), when the deterministic regression replay runs for J-01, J-03, J-04, J-05, J-06, J-08, J-09, then all seven goldens PASS; any golden that FAILs is reconciled by opening its own verify frame/log (never accepted as "transient/concurrent load" without evidence, per the iter-72 lesson) before recording an overturn.
- TC-7: given this iteration's diff, when `git status --porcelain -- config.yaml project-extensions/ scripts/` and `git diff HEAD -- config.yaml` are inspected, then only the intended `database.pool_size`/`max_overflow`/`pragmas.cache_size` lines (if TC-3 fired) appear in the diff, and AG-10's declared caps (`memory_cap_mb`, `malloc_arena_max`, host-guard CPU/BLAS mask) are present and byte-unchanged.
- TC-8: given the drill's own concurrency-generating load, when any HTTP 503 appears during the drill, then each one is attributed by its exact `logs/backend.log` line to either a `QueuePool ... timeout` (this round's own pool/memory question, in scope) or an `Exceeded concurrency limit` line (the separately-disclosed, out-of-scope GIL/admission-control finding, Addendum 37) — never left unattributed or folded into a fix this round did not scope.
- TC-9: given the addendum recorded in TC-1, when the goal-evaluator re-scores J-07 step 3, then the acceptance criterion ("assert it stays under the declared `server.memory_cap_mb`, with the margin recorded in `reports/perf-budgets.md`") is satisfiable on this round's own fresh evidence, not a carried-forward durability claim.

## NOTES

- **Assumption logged:** the "thin margin" threshold (<20% headroom) used in TC-2/TC-3 is this iteration's own interpretation of J-07 step 3's unspecified acceptance bar — see `runs/goal-session-ops-hardening/state/assumptions.md`, entry `## iter-73 — goal-decomposer`.
- **Lessons applied:** iter-72's lesson (pool/worker/per-connection-cache resizes void memory-evidence durability — re-measure before carrying forward); iter-71's lesson (score J-04/J-06/J-07 only from a `scripts/start-backend.sh` drill — confirm the boot header in `logs/backend.log`, never `dev.sh`); iter-72's second lesson (never accept "transient/concurrent load" for a replay FAIL without opening the frame/log first).
- **Owner items still open, not this round's job to resolve:** the 2-second health-ceiling policy (long vs. short jobs), B-1107 (limiting concurrent heavy computes), the `browser-qa-phase.sh` ordering-bug fix permission, and the now-12-consecutive-round cost overrun. Do not silently ignore them — the evaluator should keep asking in writing.
- **Blueprint kept current:** `runs/goal-session-ops-hardening/state/blueprint.md` gets a short additive narrative note (top-of-file "iter-73 update" paragraph, plus a one-sentence addition to the "Page performance budgets" row's Notes) — no Data Contract row's computing module/endpoint changes, no Information Architecture change, so no re-approval file is needed.
- If TC-1's drill instead reveals that the concurrency-generating load itself cannot cleanly reach a realistic fraction of the 68-connection ceiling without confounding results (e.g., the admission-control 503 issue fires before the pool does), record that honestly as the round's own finding rather than forcing a number — the goal is a trustworthy measurement, not a clean-looking one.
