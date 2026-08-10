# Goal Iteration 56 — Close J-06's last gap: profile-then-fix the DB-growth-driven `/api/runs` and `/api/data/availability` latency

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** ops-hardening
- **Iteration:** 56
- **Mode:** next
- **Depth:** full
- **Full trigger:** 1 — the fix spans ≥3 modules whose interaction is uncovered by any one journey's own tests: `app/api/runs.py` (N+1 query removal), `app/engine/data_manager.py` (a new ingest-time-warmed availability cache + finalize-hook wiring, sharing the SAME MemoryError-isolation convention six prior iterations have hardened there), and `app/models.py` (a new standalone cache table) — and the DB-growth root cause was explicitly UNCONFIRMED at the code level by both iter-54's and iter-55's own text (`reports/perf-budgets.md` Addendum 18: "unverified at the code level this dispatch"), so this is a genuine profile-then-fix effort spanning the API and engine layers, not a contained one-function change.
- **Frontend Present:** no
- **Target journeys:** J-06
- **Required-still-passing journeys:** J-01, J-03, J-04, J-08, J-09
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
  - **AG-10 — Host resource ceiling (hardware protection):** heavy compute — backfills, full-universe rebuilds, measurement passes, load drills, test-suite bursts — MUST be launched only via the project launch scripts (`scripts/dev.sh` / `scripts/start-backend.sh`), and those scripts MUST apply the host caps declared in `project-extensions/host-guard/host-guard.env` whenever that file is present (CPU-affinity mask, BLAS/OMP thread caps, `memory_cap_mb`, `malloc_arena_max`). Never remove, weaken, or bypass these caps: stripping a HOST-GUARD marked block from a launch script is a REGRESSION regardless of test outcomes. The ceilings are a physical constraint of the current host (two instant hardware resets under all-core vectorized ingest bursts: 2026-07-20 19:17, 2026-07-21 10:33), not a performance budget to optimize away. *(Owner amendment 2026-07-31, two corrections of record — nothing above is relaxed: `memory_cap_mb` / `malloc_arena_max` live in `config.yaml`, not in `host-guard.env`; and the 2026-07-20/21 resets were subsequently attributed to an uncorrected hardware data-fabric fault (`host-guard.env`, 2026-07-30), so the ceiling VALUES are an owner-set envelope — re-set by the dated entry in "Additional binding notes" below — while this paragraph's prohibition on agents removing, weakening, or bypassing caps is unchanged.) *(critical)*

## GOAL

Bring `GET /api/runs` and `GET /api/data/availability` back under their committed ≤1.5s budget on the live, 8.37 GB dev database, closing J-06's one remaining gap.

## BACKGROUND

`reports/perf-budgets.md`'s Addendum 18 (iter-54, re-confirmed unchanged at iter-55) records both endpoints WARN — `/api/runs` 3.2-7.5s, `/api/data/availability` 15.1-21.2s, against a committed ≤1.5s generic budget — root-caused to the shared dev DB's growth to 8.37 GB / 2,937 `scanner_runs` rows (~15x the session's original baseline), but explicitly states the actual code-level cause is "unverified... no time budget left this pass for a profile." The iter-55 evaluator's own next-step item (4) names this the single thing keeping J-06 `partial` and instructs: "measure first, then fix." A direct read of the current code (this decomposer, not yet confirmed live) finds two strong, independent candidates: (1) `app/api/runs.py`'s `runs()` issues one `ScannerResult` COUNT query PER stored run inside a Python loop (2,937 queries on the live DB) — the exact N+1 shape `blueprint.md`'s iter-5 entry already flagged as a candidate years before it was ever measured live; (2) `compute_availability` (`app.engine.data_manager`) runs an unbounded, uncached `GROUP BY DailyPrice.date` scan across the FULL benchmark trading calendar (1996-01-02 to today) on every request — the exact "compute at ingest, serve from storage" gap goal.md's own Improvement-direction table names as aggregation candidate #7 ("per-date bars-present rollup for the availability heatmap... optional"), now justified by measured evidence instead of being merely optional. Both fixes require live profiling FIRST, per this session's binding iter-48/50/53 discipline (never force-fit a diagnosis ahead of measurement) — this spec names the candidates, it does not mandate them ahead of the developer's own profile.

Target selection: no journey is `regressed` (rule 1 does not apply); the last `coherence.md` was COHERENCE-PASS, not FAIL (rule 2 does not apply); J-06 is the clearest unblocker available (rule 3) — it is this session's LAST failing/partial journey with no open human-owned blocker, unlike J-05 (blocked on the owner's availability-ceiling decision) and J-07 (its evaluator-confirmed-exhausted per-compute-yield lever, item (5): "five rounds have tried the same lever...this round's data shows it is finished" — rule 6 bars re-planning it). This is ONE risky action (rule 5): a genuinely unprofiled, cross-module fix, so J-05's golden-date rotation (a cheap, mechanical fixture edit, not a second risky journey) rides alongside it without violating the one-risky-action rule.

Depth is **full**, matching the evaluator's binding recommendation for this iteration and independently justified by trigger 1 (see metadata) — the fix's actual shape is not yet confirmed at the code level and spans the API layer (two separate endpoint handlers), the engine layer (a new ingest-finalize warm step sharing the session's hard-won MemoryError-isolation convention), and a new DB table, none of which is exercised end-to-end by any single existing golden.

This iteration deliberately excludes the framework-level replay-lane result-overwrite bug and the QA-agent verdict-line-reading defect the iter-55 evaluator flagged as items (2)/(3) (the latter now 5 consecutive rounds unfixed) — a direct search confirms both live in the vendored `incredible_auto_dev/scripts/automation/` tree, not this product's own `apps/backend`/`apps/frontend`/`scripts/automation/`, outside a product-development iteration's remit. Logged with full grounds at `runs/goal-session-ops-hardening/state/assumptions.md` (iter-56) rather than silently re-carried as if agent-actionable.

Per the binding TC-9/TC-13 lane-ordering rule (carried forward verbatim, proven at iter-53): if the audit finds a defect requiring a product-code change after this iteration's lane has already run, it is filed as a note for iter-57 rather than applied as a code-changing audit-fix.

## IN SCOPE

### Backend
- [ ] Profile `GET /api/runs` and `GET /api/data/availability` live against the current DB (idle host, warm `scripts/start-backend.sh`, no concurrent job) with query-level instrumentation (SQL echo / query counting) BEFORE committing to a fix — confirm or correct the two candidates named in BACKGROUND (binding iter-48/50/53 profile-first discipline).
- [ ] If profiling confirms the N+1 pattern: replace `app/api/runs.py`'s `runs()` per-run `ScannerResult` COUNT query (issued once per `ScannerRun` row) with a single grouped aggregate query. Same endpoint (`GET /api/runs`), same response shape, byte-identical `n_stocks` per run — no second producer.
- [ ] If profiling confirms the unbounded full-history `GROUP BY`: move `compute_availability`'s (`app.engine.data_manager`) heatmap derivation from the request path to the existing ingest finalize hook (`_refresh_ingest_aggregates`) — persist to a new standalone `dataset_version`-keyed cache table (`app/models.py`, mirrors the already-proven `IndexSeriesCache`/`CoverageSnapshot` convention). `GET /api/data/availability` reads the persisted row; same computing module, same endpoint, no second producer.
- [ ] Wire the new availability-heatmap warm into the SAME MemoryError-isolation convention (`_release_process_memory()`, isolate-and-continue, per-item honest-omission) every other finalize-tail item in `_refresh_ingest_aggregates` already uses — a failed warm never wedges the run and never fabricates a refresh claim.
- [ ] Add `"availability_heatmap"` as a further legal member of the existing `aggregates_refreshed` enumerated list (mirrors the iter-13 `"index_series"` precedent) — no new field, no second record.
- [ ] Honest not-yet-computed fallback when no cache row exists for the current `dataset_version` (not-yet-ingested DB, or a warm the isolation convention skipped) — never a live full-table compute on the default request path; mirrors `coverage_snapshot`'s missing-row convention.
- [ ] If profiling finds a DIFFERENT bottleneck than either named candidate, apply whichever bounded/indexed/cached fix the profile actually supports, and document the real diagnosis in the dev handoff (the same license iter-53/54's specs used).

### Frontend
None — Frontend Present: no. Both endpoints' response shapes stay byte-identical to today; zero `apps/frontend/` changes.

### Verification & test infrastructure
- [ ] Rotate `runs/goal-session-ops-hardening/journey-scripts/J-05.json`'s single-use target date off the now-consumed 2010-11-08 (`scanner_runs.id=2940`) to 2010-11-10 (steps 2, 3, 13, 14, plus the `_notes` rotation log) — reverify the new date's zero-snapshot state live via `GET /api/runs` immediately before use, per the file's own existing instruction. Test-fixture fix only; no re-open of J-05's already-confirmed-built product code (binding "Do not redo" — the honest-status fix and the GIL-holding treatment are untouched).
- [ ] **Lane-ordering rule (carried forward verbatim, binding this iteration):** if the audit subsequently finds a defect needing a product-code change, it is filed as a note for iter-57 rather than applied as a code-changing audit-fix, so this iteration's own lane evidence stays valid for the tree it measured.

### New user-facing capability
None — this iteration is a latency fix to two already-shipped, already-displayed endpoints; no new feature.

### New information displayed
None. `/api/runs`'s `n_stocks` and `/api/data/availability`'s heatmap cells are unchanged values in an unchanged shape — only their computation path changes.

### New user actions
None.

### UI surface changes
None (Frontend Present: no).

### Product surface delta
`/scanner-runs`, `/data`, and every page whose job-history table calls `GET /api/runs` load their run list within the committed ≤1.5s budget again; `/data`'s availability heatmap loads within budget instead of 15-21s. No visible change to values, layout, or interaction — the page shell and primary content already paint fast (per Addendum 18's own `content_visible_ms` reading); only these two calls' own latency changes.

### Blueprint conformance
Both touched values keep their EXISTING Information-Architecture homes per `blueprint.md`: Data Manager (`/data`) and Scanner Runs (`/scanner-runs`), both already-registered nav homes — J-06's own canonical home stays "cross-cutting measurement; canonical artifact `reports/perf-budgets.md`" (no change). `blueprint.md` was additively updated this iteration: a new top-level `iter-56 update` changelog paragraph, a new "Availability heatmap" Data Contract row (mirrors the iter-13 Index-series precedent, `[TARGET, iter-56 building]`), and an additive sentence on the already-registered "Backfill run-summary contract" row's `aggregates_refreshed` Notes.

### Data-contract additions
- **Availability heatmap** (per-trading-date bars-present + snapshot-exists cells, J-61) — NOT a new displayed value (pre-existing `/data` heatmap widget), but gains its first dedicated Data Contract row this iteration because it gains a new computing/serving PATH: computing module `app.engine.data_manager.compute_availability` (unchanged function/signature), now warmed inside the existing `_refresh_ingest_aggregates` finalize hook into a new standalone cache table; serving endpoint `GET /api/data/availability` (unchanged). Field shape (unchanged from today): `total_symbols: int >= 0`, `trading_day_count: int >= 0`, `cells: list[{date: str (ISO yyyy-MM-dd), symbols_with_bars: int >= 0, total_symbols: int >= 0, snapshot_exists: bool}]`.
- **`aggregates_refreshed`** (Backfill run-summary contract row, ALREADY REGISTERED) gains one further legal enumerated string member, `"availability_heatmap"` — no new field, no second record.
- `/api/runs`'s `n_stocks` is NOT a new or changed value — same field, same endpoint, same computing module (`app.api.runs.runs`); only its query plan changes. No Data Contract row addition needed.

## OUT OF SCOPE

- J-07 step 2's per-compute-yield lever — five consecutive rounds have applied the same scheduling treatment; the iter-55 evaluator's own item (5) states the lever is exhausted. Not retried this iteration.
- The framework-level replay-lane result-overwrite bug and the QA-agent verdict-line-reading defect (iter-55 evaluator items (2)/(3), the latter now 5 consecutive rounds unfixed) — both live in the vendored `incredible_auto_dev/scripts/automation/` tree, not `apps/backend`/`apps/frontend`/this product's own `scripts/automation/`; outside a product-development iteration's remit (`assumptions.md` iter-56). Flagged again, not silently dropped.
- The demo-recorder script bug ("step[6] fill requires text") — costs J-04/J-05/J-07 their `[NEW]` walkthrough captures per iteration-state.md's active blockers; this is showcase-pipeline tooling, the same framework-boundary reasoning as the two items above, not product dev scope.
- All previously-carried, untouched ledger items from iteration-state.md's carried list (iter-29/b through iter-48/bj) — not re-itemized here, still deferred.
- The two standing OWNER decisions, unanswered since iter-50/51, repeated every round through iter-55: (a) may heavy compute move to a separate process/worker boundary; (b) does the finalize-tail wall-clock budget bind while the app serves traffic, or only when idle. Human-owned per rule 6; not re-planned as agent work.
- The Regime Lab's data-call MemoryError and its heading-only golden (iter-33/g) — 21st deferral, unless the owner promotes it.
- Any new frontend surface, page, route, or nav entry.
- Rebuilding or re-verifying J-05/J-07's already-confirmed-built product code (honest-status accounting fix, GIL-holding treatment) — proven and binding "Do not redo"; this iteration touches only J-05's golden fixture's target date, never its product fix.

## DEFINITION OF DONE

- [ ] Target journey J-06 scored by goal-evaluator using real behavioral evidence (fresh dated `reports/perf-budgets.md` measurements taken THIS iteration + code-level confirmation that neither endpoint performs an unbounded scan/recompute on the request path) — never a stale or cached reading
- [ ] Required-still-passing journeys J-01, J-03, J-04, J-08, J-09 remain green via deterministic replay, with LLM-lane fallback for any journey whose golden is missing that iteration
- [ ] `GET /api/runs` reads ≤1.5s on the live (8.37 GB+) DB, measured 3x back-to-back on an idle host (no concurrent ingest/page contention), recorded in a new dated `reports/perf-budgets.md` section
- [ ] `GET /api/data/availability` reads ≤1.5s on the SAME DB under the SAME conditions, recorded in the SAME section
- [ ] `/api/runs`'s `n_stocks` values are byte-identical per run to the pre-fix per-run computation, proven by a unit test comparing every stored run's count
- [ ] `/api/data/availability`'s cached payload is byte-identical to the pre-existing unbounded live computation for the same DB state, proven against a pinned pre-fix reference oracle
- [ ] A missing/stale availability-cache row serves an honest not-yet-computed empty payload (HTTP 200, no fabricated cells) — never a live full-table compute on the default request path
- [ ] `journey-scripts/J-05.json` is rotated off its consumed date and the new date's zero-snapshot state is reverified live before use
- [ ] If the audit finds a defect needing a product-code change, it is filed as a note for iter-57, not applied as a code-changing fix — no `apps/backend/**`/`apps/frontend/**` file's mtime postdates the lane's own artifacts
- [ ] AG-3 (byte-identity for both fixed values), AG-8 (no new unbounded load introduced; isolate-and-continue intact on the new cache warm), AG-9 (`provider='seed'` on every run created this iteration), AG-10 (5 frozen host-guard paths untouched) all independently re-verified this iteration
- [ ] Unit tests pass; no regressions
- [ ] Dev handoff written at `docs/handoffs/goal-ops-hardening-iter-56-dev.md`

## TESTING REQUIREMENTS

- Browser: J-06 (target); J-01, J-03, J-04, J-08, J-09 (required-still-passing) — dispatched LAST per the binding lane-ordering rule.
- Unit/integration: `app/api/runs.py`'s `runs()` (query-count assertion + byte-identity for `n_stocks`); `app.engine.data_manager.compute_availability`'s new cache-backed path (byte-identity for cache-hit vs. cache-miss vs. stale/missing-row honest fallback); the finalize-hook wiring's MemoryError-isolation behavior for the new warm step.
- Error cases: a `MemoryError` fault-injected during the availability-heatmap warm leaves `"availability_heatmap"` OUT of `aggregates_refreshed` for that run (never fabricated) and the request path still serves the honest not-yet-computed/stale-but-prior payload, never a 500; an empty/bars-less DB still returns `cells: []`, `total_symbols: 0` (unchanged existing behavior).

Test-first contract:

- TC-1: given the live DB (2,937+ `ScannerRun` rows), when `GET /api/runs` is profiled with SQL query-count instrumentation before any fix, then the number of `ScannerResult` COUNT queries issued is recorded (confirming or correcting the N+1 hypothesis) in the dev handoff.
- TC-2: given the confirmed root cause, when `app/api/runs.py`'s `runs()` is fixed, then the number of `ScannerResult` queries issued for one `GET /api/runs` request drops to a small constant that does not scale with the number of stored runs, proven by a unit test.
- TC-3: given the fix applied, when every stored run's `n_stocks` is compared against the pre-fix per-run COUNT computation, then every value is byte-identical.
- TC-4: given the fix applied, when `GET /api/runs` is requested 3x back-to-back on an idle host with no page/ingest contention, then all 3 readings are ≤1.5s, recorded in a new dated `reports/perf-budgets.md` section.
- TC-5: given an ingest job (fetch/backfill/rebuild) finalizes after the availability-heatmap fix lands, when the finalize hook runs, then a new cache row is persisted keyed by the current `dataset_version`, and `data_provider_runs.aggregates_refreshed` for that run lists `"availability_heatmap"` ONLY if the row was actually persisted this run (never on a cache HIT / no-op run).
- TC-6: given the persisted cache row exists for the current `dataset_version`, when `GET /api/data/availability` is requested, then the response is served from the cache without executing the full-history `GROUP BY` scan, and every field (`total_symbols`, `trading_day_count`, every cell's `date`/`symbols_with_bars`/`snapshot_exists`) is byte-identical to `compute_availability`'s live (pre-fix) computation for the same DB state.
- TC-7: given the fix applied, when `GET /api/data/availability` is requested 3x back-to-back on an idle host with no page/ingest contention, then all 3 readings are ≤1.5s, recorded in the SAME dated `reports/perf-budgets.md` section as TC-4.
- TC-8: given no cache row exists yet for the current `dataset_version` (fresh DB, or a warm the isolation convention skipped under memory pressure), when `GET /api/data/availability` is requested, then it returns HTTP 200 with the honest not-yet-computed/empty payload — never a 500, never a fabricated cell.
- TC-9: given a `MemoryError` fault-injected during the availability-heatmap warm step, when the ingest job finalizes, then `"availability_heatmap"` is absent from that run's `aggregates_refreshed`, the run's overall `status` is unaffected (isolate-and-continue), and no other finalize-tail item's own completeness flag is altered by this fault.
- TC-10: given `journey-scripts/J-05.json`'s target date is rotated to 2010-11-10 and its zero-snapshot state is reverified live via `GET /api/runs`, when the golden replays steps 1-15, then step 10's "0 already snapshotted" assertion does not fail for a fixture reason.
- TC-11: given the audit step runs after the lane, when it finds a defect requiring a product-code change, then it is filed as a note for iter-57 and no file under `apps/backend/**`/`apps/frontend/**` has a modification time later than the lane's own earliest artifact.
- TC-12: given this iteration's fixes and drills run, when `data_provider_runs` rows created this iteration are queried, then every row's `provider` field reads `'seed'` (AG-9), AND `git diff --stat` / `git status --porcelain` over the 5 frozen host-guard paths (`config.yaml`, `host-guard.env`, `start-backend.sh`, `dev.sh`, `start-frontend.sh`) are both empty (AG-10).
- TC-13: given this iteration's work is complete, when the developer writes the dev handoff, then `docs/handoffs/goal-ops-hardening-iter-56-dev.md` exists and names the profiling result (confirmed or corrected root cause) and the before/after measured latency for both endpoints.

## NOTES

- **Lessons applied:** iter-48/50/53's profile-first discipline ("never force-fit a fix ahead of measurement") governs TC-1/TC-2 and the IN SCOPE conditional fix bullets — this spec names two strong, code-confirmed candidates but does not mandate them ahead of live profiling. The iter-50 lesson ("bounding memory cannot close a responsiveness requirement... a *scheduling* problem wearing a memory problem's clothes") is why this iteration bounds/caches the QUERY shape rather than reaching for a memory-side fix. The iter-53 lesson on unit mismatches (bound vs. consumer must speak the same unit) applies if the developer's profile points at a windowing/pagination fix rather than a full ingest-time cache — verify the bound's unit against what the frontend actually consumes before shipping it.
- **OWNER decisions still open, unanswered since iter-50/51, repeated every round through iter-55 (not this iteration's scope, per rule 6):** (a) may heavy compute move to a separate process/worker boundary; (b) does the finalize-tail wall-clock budget bind while the app serves traffic, or only when idle.
- **Assumption logged:** `assumptions.md` iter-56 records why the replay-lane/QA-verdict-reading defects (iter-55 evaluator items (2)/(3)) and the demo-recorder script bug are excluded from this iteration's IN SCOPE — both live in framework/pipeline tooling outside a product-development iteration's remit, not a scoping shortcut, and the cost (a 6th unfixed round for item (3)) is recorded honestly.
- **J-05 is NOT a Target journey this iteration** — its product fix (honest-status accounting, GIL-holding treatment) is already built and evaluator-confirmed (iter-55); the golden-date rotation in this iteration's scope is enabling/fixture work only, so J-05 stays `partial` (blocked on the human-owned availability-ceiling decision, per iteration-state.md).
- If profiling finds the true bottleneck differs from either candidate named above, apply whichever bounded/indexed/cached fix the profile actually supports and document the real diagnosis in the dev handoff — the same license iter-53/54's specs used, which is what let those iterations find the real cause instead of guessing.
