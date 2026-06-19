# Goal Iteration 36 — Make GET /api/data responsive (cache the J-96 membership timeline; no served-value change)

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 36
- **Mode:** next
- **Depth:** full
- **Frontend Present:** no
- **Target journeys:** J-94, J-96
- **Required-still-passing journeys:** J-93, J-06, J-07, J-18, J-87, J-88, J-36, J-37, J-39, J-85, J-15
- **Anti-goal reminders:**
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. The relocated as-of-scoped evidence aggregate is likewise derived once per resolved as-of date over the snapshots dated ≤ D, persisted/cached, and read from storage — never recomputed per request and never including a snapshot dated > D. *(extends Single source of truth)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. *(critical)*
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D. *(critical)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **Honest limitations surfaced.** Breadth/new-high-new-low metrics MUST be labelled "universe-relative" and walk-forward evidence MUST be labelled as carrying survivorship bias.
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - Exactly one global date selector — the frontend MUST NOT introduce a second/page-local date state. *(critical)*

## GOAL

The `/data` page hydrates again within a normal page load: `GET /api/data` returns promptly (no >300 s hang), so the J-94 per-date coverage diagnostic and the J-96 membership-timeline step function render with their honesty labels — and every served value is byte-identical to the slow computation it replaces.

## BACKGROUND

iter-35 halted **REGRESSION**: the out-of-band J-85 rebuild (job `eb48cbf1`, 1369/1369 dates) correctly fixed J-93 (the dynamic universe now slides `0 → 494 → 504 → 544` on `/stocks`), but the SAME data growth made `GET /api/data` hang >300 s, so the `/data` page that fully rendered J-94 in iter-34 now serves only un-hydrated skeletons (J-94 regressed; J-96 stayed partial — data correct, page never renders). Root cause is source-confirmed: `compute_coverage` (`apps/backend/app/engine/data_manager.py:531`) always calls `_membership_timeline` (`:469-528`, invoked at `:603`), whose per-date loop calls `universe_resolver.resolve_with_reasons(session, d, cfg)` for ALL ~1369 snapshot dates (`:514`) with NO result cache (only an in-block `bar_cache`). That was cheap at iter-34's static-122 set and is intractable at the post-rebuild sliding `0→544` set. This is a **read-path performance defect exposed by correct data growth** — the served VALUES are correct (J-96 data is DB-direct-correct), only delivery is too slow. The evaluator's recommended fix (and the open_item `iter35-api-data-timeline-uncached`) is to make `GET /api/data` responsive WITHOUT changing any served value, then LIVE re-verify J-94 + J-96 and re-smoke the co-located `/data` journeys. Depth is **full**: this adds backend code + a new cache table + tests, so the full backend pytest suite is the GOAL_ACHIEVED gate (iter-23/iter-35 precedent). Coherence at iter-35 was COHERENCE-PASS, so no consolidation pass is owed — this iteration may add the perf fix directly.

## IN SCOPE

### Backend
- [ ] Eliminate the O(dates × pool) cost of `_membership_timeline` (`apps/backend/app/engine/data_manager.py:469-528`) so `GET /api/data` responds promptly post-rebuild. Use the **established J-72/J-87 cache precedent**: add a STANDALONE `create_all`-managed cache table (mirroring `EventStudyCache` / `MarketPhaseCache` in `apps/backend/app/models.py:385-472`) keyed by a single `dataset_version` stamp — reuse the SAME `app.engine.research._dataset_version(session)` stamp (single-sourced; it already changes on any dataset change), storing the SERIALIZED `_membership_timeline(...)` payload. A read computes the current stamp, returns the stored payload on hit, and computes-once-then-upserts on miss; a stale row keyed to an older stamp is never hit (and is pruned on write). The cached payload MUST be byte-identical to a fresh `_membership_timeline` compute.
- [ ] Precompute / warm the membership-timeline cache during the background warm-up daemon (`apps/backend/app/engine/warmup.py::_run_warmup`, after `backfill_forward_returns`, inside or after the existing `bar_cache` usage) so the FIRST `/data` request after a boot/rebuild serves the cached payload rather than paying the cold compute synchronously (the J-40/J-41 serve-fast lifespan precedent). Warm-up failure stays NON-FATAL (caught + logged), exactly as the existing warm-up worker already guarantees.
- [ ] If a cold miss can still occur on a request (e.g. before warm-up completes), bound the synchronous cost so `GET /api/data` never hangs: the per-date excluded-by-reason resolver loop must read each pool symbol's series ONCE (the existing in-block `bar_cache` already does this for bars — extend the same load-once discipline to `resolve_with_reasons` so it is not re-screening from scratch per date), OR fall back to serving the timeline's already-cheap parts (size/entries/exits read from the single `ScannerRun`/`ScannerResult` join at `:492-498`, which is already one query) with the per-date `excluded` counts filled from cache when present. The served block's shape and values must stay identical to today's `compute_coverage` output.
- [ ] Any new tunable (e.g. a cache-staleness or batch knob) MUST be sourced from `config.yaml` (e.g. under `config.data_manager`), never an inline literal — `data_manager.py` is not in `test_no_magic_numbers` CALC_FILES, but config-sourcing is the project rule.
- [ ] Register the new standalone cache table in `apps/backend/tests/test_db.py::test_create_all_produces_expected_tables` (add a new `MEMBERSHIP_TIMELINE_CACHE_TABLES = {"<name>"}` group to the expected-tables union at line 70, the iter-20/21/29 standalone-cache-table precedent). It is legitimately mutable derived/cache state — NOT a scanner snapshot — so the `_ADDITIVE_COLUMNS` trap (iter-12) does not apply, exactly like `event_study_cache` / `market_phase_cache`.

### Frontend (if applicable)
- None. This is a backend read-path performance fix only — `/data` page components are unchanged; they simply hydrate again once the endpoint responds. No frontend diff expected.

### New user-facing capability
The `/data` Data Manager page loads and stays interactive again: the J-94 per-date coverage diagnostic and the J-96 membership-timeline step function render instead of perpetual skeleton panels. No NEW capability — this restores a previously-passing surface.

### New information displayed
None new. The same coverage block (`universe_count`, `universe_diagnostic` (J-94), `membership_timeline` (J-96) — size step function + entries/exits + per-date excluded-by-reason counts, plus the three honesty labels) is served — now promptly, and byte-identical to the iter-35 (slow) values.

### New user actions
None. (Do NOT add any control. Do NOT add any second date state — the single global as-of is the only date control, J-18 critical.)

### UI surface changes
None. `/data` Data Manager home renders as before — the regression was hydration failure, not a layout change.

### Product surface delta
The `/data` page returns from "permanently loading skeletons" to a working coverage view. `/stocks` (J-93, the fast `/api/stocks` snapshot path) is unaffected and stays green.

### Blueprint conformance
No new surfaces. J-94 and J-96 already live on the EXISTING **Data Manager** node (`/data` coverage home) in the blueprint Information Architecture; J-93 lives on the **Stocks** node. The canonical computing module for the J-96 timeline (`data_manager._membership_timeline` → `compute_coverage`) and its serving endpoint (`membership_timeline` field on `GET /api/data`) are unchanged — the cache sits behind the SAME module/endpoint, so no IA edit and no nav-skeleton change. No `blueprint.reapproval-requested` file.

### Data-contract additions
None. No new displayed value is introduced. The membership timeline, the per-date coverage diagnostic, and `universe_count` are already registered in the Data Contract with their single canonical module + endpoint. The new cache table is internal performance state, not a displayed value, and serves the SAME registered value through the SAME endpoint — read it from the registered canonical source, never via a second path.

## OUT OF SCOPE

- **Do NOT re-trigger the J-85 `kind:"rebuild"` job** (~11 h, destructive — clears ~1369 daily snapshots). The data is already correct post-iter-35; this iteration only fixes delivery speed. (See MEMORY: "J-85 rebuild is ~11h and clears the snapshot layer".)
- No change to `universe_resolver` resolution math, `score_stocks`, `forward_testing`, or any canonical scoring formula. The resolver's admitted/excluded results must be identical — only their delivery is cached/precomputed.
- No change to the served coverage block's shape or values (byte-identity is a hard DoD).
- No new frontend component, no new date control, no new endpoint.
- No new Data Contract value; no nav-skeleton change.
- Not addressing J-22/J-23/J-24 (data-walled per goal.md, non-vetoing) — out of scope.

## DEFINITION OF DONE

- [ ] `GET /api/data` returns within a normal request budget on the post-rebuild DB (verify with a timed live request; no >300 s hang).
- [ ] **Byte-identity asserted:** the served `coverage` block (especially `membership_timeline`, `universe_diagnostic`, `universe_count`) is identical before/after the perf fix — a test proves the cached payload == a fresh `_membership_timeline` / `compute_coverage` compute (deep-equal, not "looks similar").
- [ ] Target journeys J-94 and J-96 pass via browser-qa-agent on LIVE, md5-distinct, non-skeleton evidence: J-94 = the per-date universe-resolution diagnostic renders (admitted + excluded-by-reason counts at the resolved as-of); J-96 = the rising membership-timeline step function from ~2021-10-18 with populated Entries/Exits and the three honesty labels, scrolled into the viewport and the pixels viewed.
- [ ] Required-still-passing journeys remain green: J-93 still slides `0→544` on `/stocks` (fast `/api/stocks` path, unaffected); J-06 single-source (NVDA list == detail); the CRITICAL J-07 (Risk-Off → 0 Actionable) and J-18 (exactly one date selector, 0 `input[type=date]`); J-87/J-88 dashboard market-phase unchanged; co-located `/data` journeys J-36/J-37/J-39/J-85 re-smoked; J-15 leaderboard speed.
- [ ] No anti-goal violation introduced (no recompute in the read path — a cache of a deterministic read-only derivation is permitted by the "derived once… persisted/cached, read from storage" clause; single source of truth held; snapshots untouched; no fabrication; honesty labels intact).
- [ ] New standalone cache table registered in `test_db.py` expected-tables; unit tests pass.
- [ ] Full backend pytest suite flushes `0 failed, EXIT 0` — handed to the pump nohup-async; the evaluator is gated on the FLUSHED terminal summary line, NEVER blocked on the in-flight suite (iter-11/29/30 lesson).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-36-dev.md`.

## TESTING REQUIREMENTS

- **Browser:** J-94 (per-date coverage diagnostic renders on `/data`), J-96 (membership-timeline rising step function + Entries/Exits + the three honesty labels, scrolled into viewport). Re-smoke J-36, J-37, J-39, J-85 on `/data`; re-confirm J-93 on `/stocks` (fast path) and the CRITICAL J-18 (0 `input[type=date]`) and J-07 (Risk-Off → 0 Actionable). md5sum the evidence dir FIRST; reject any un-hydrated skeleton frame (iter-18/iter-33 precedent — a loading skeleton is NOT evidence).
- **Unit/integration:**
  - A timing/responsiveness test: `compute_coverage` / the timeline read returns quickly when the cache is warm (and does not hang when cold — bounded), on a DB with the dense sliding membership.
  - A **byte-identity** test: the cached/served `membership_timeline` payload deep-equals a fresh `_membership_timeline(...)` compute over the same DB; `universe_diagnostic` and `universe_count` unchanged.
  - A cache-invalidation test: after a dataset change (the `_dataset_version` stamp changes), a stale cache row is not served (the read recomputes against the new stamp). Mirror the `event_study_cache` / `market_phase_cache` cache-key tests.
  - `test_db.py::test_create_all_produces_expected_tables` updated for the new standalone table and still green.
  - Strict no-lookahead / causality of the timeline is unchanged (each date observed from its own ≤ D snapshot + bars ≤ D) — re-assert the existing `_membership_timeline` causality property holds through the cache.
- **Error cases:** empty DB / no snapshots → an empty-but-valid timeline (no fabricated dates/members), exactly as today; an invalid/absent `?as_of` on `GET /api/data` still falls back gracefully to the latest stored run date (no 4xx — descriptive metadata).

## NOTES

- **Precedent to copy (do not invent a new abstraction):** the standalone derived-aggregate cache keyed by `(key…, dataset_version)` is already implemented twice — `EventStudyCache` (J-72, `models.py:385-433`) and `MarketPhaseCache` (J-87/J-88, `models.py:436-472`), both registered in `test_db.py` (`RESEARCH_CACHE_TABLES`, `MARKET_PHASE_CACHE_TABLES`) and both using `research._dataset_version(session)` as the single-sourced stamp. Reuse that exact pattern for the membership timeline. The warm-up precompute mirrors how `_run_warmup` already produces the cadence snapshots + forward returns off the boot path.
- **Lesson — read-path data-volume cost (iter-35, this regression's own lesson):** a correct data-volume increase exposed a latent O(dates × pool) read-path cost; a data-regeneration must smoke `GET /api/data` for RESPONSE TIME, not just verify the DB-direct values. This iteration's QA MUST include a timed live `GET /api/data`.
- **Lesson — standalone cache table guards (iter-20/21/29):** a new `table=True` model trips `test_db.py::test_create_all_produces_expected_tables` (exact-set) — add it to the expected union in the SAME iteration. A standalone table correctly avoids the iter-12 `_ADDITIVE_COLUMNS` trap.
- **Lesson — `GET /api/data` shape guard (iter-32):** `test_api_data.py::test_get_data_overview_shape` uses `<= set(payload)` (subset) at line 79, so it will NOT trip on this fix (no NEW top-level key is added — `membership_timeline` already exists). Do not add a new top-level `/api/data` key; if you ever must, update that guard in the same iter.
- **Lesson — never block the evaluator on the in-flight suite (iter-11/29/30):** on this 1369-run host the full suite runs ~60 min and `loaded_engine`-fixture tests cannot finish under a subagent Bash cap. Launch the full suite via `nohup` to the pump and gate GOAL_ACHIEVED candidacy on the FLUSHED `0 failed, EXIT 0` line; an `exit=137` on the nohup wrapper is the known harness-kill, not a test failure. Re-run any single `test_data_manager_jobs_pipeline.py` / `test_warmup.py` `F` in isolation before attributing it to this iteration (the documented scanner_runs-race / slow-boot / warm-up-contention flake on a byte-unchanged path).
- **Lesson — skeleton frames are not evidence (iter-18/iter-33):** the iter-35 `/data` frames were all un-hydrated skeletons; the below-the-fold timeline grid/step-function must be scrolled into the viewport and the rendered pixels viewed. md5sum the dir first; reject duplicate/blank frames.
- **Env health (iter-17/30):** confirm backend `:8835` + frontend `:3835` + Chrome `:9222` reachable BEFORE scoring; if Chrome MCP is down the browser-qa-agent should fall back to Playwright (iter-34 precedent) so the differential J-94/J-96 evidence is genuinely live.
- After J-94 re-renders and J-96 flips to passing with COHERENCE-PASS and a GREEN full suite (and J-93/J-06/J-07/J-18/J-87/J-88 still green), the next evaluation is a GOAL_ACHIEVED candidate — J-22/J-23/J-24 stay honestly blocked-NA (non-vetoing per goal.md). Closes open_item `iter35-api-data-timeline-uncached`.
