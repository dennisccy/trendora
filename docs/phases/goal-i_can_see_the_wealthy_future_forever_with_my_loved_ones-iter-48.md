# Goal Iteration 48 — Finish J-105: stream the remaining unstreamed ScannerResult reads so Factor Lab (J-25) loads on the full live dataset

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 48
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-25, J-104, J-105
- **Required-still-passing journeys:** J-29, J-26, J-77, J-91, J-103, J-51, J-63, J-65, J-72, J-32, J-06, J-18, J-07
- **Anti-goal reminders (verbatim from docs/goal.md):**
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request. The scan is computed once per date (bootstrap, scheduled, or first view) and then read from storage. …
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. … *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation … *(critical)*
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **Honest forward-test for partial windows.** … MUST show NA/partial for horizons or cohorts lacking enough samples and MUST show sample size — never fabricate or extrapolate a return to fill a gap. *(extends No fabricated data)*

## GOAL

A user can open the **Factor Lab** (`/research/factor-lab`) on the full live dataset and read the decile table + rank-IC with real figures — the lab serves HTTP 200 without the `MemoryError` that iter-47 left, because the last two unstreamed full-table `select(ScannerResult)…all()` ORM reads are now `yield_per`-streamed, with every served figure byte-identical.

## BACKGROUND

iter-46 was an acknowledged REGRESSION: the J-85 rebuild grew `forward_returns` to ~3.08M rows and the heavy research labs began `MemoryError`-ing on the live 3.3 GB DB. iter-47 (full, `--acknowledge-regression`) streamed the seven unbounded `select(ForwardReturn)…all()` reads and **net-restored J-29 (event-study) + J-26 (factor-combination)** — but the fix was **incomplete**: it left the sibling `select(ScannerResult)…all()` reads in the same two builders unstreamed (`_factor_observations` research.py:216, `_combination_observations` research.py:421), each materializing ~609K ORM rows. Because **Factor Lab is UNCACHED** (it recomputes the observation set every request, unlike factor-combination / regime-setup-pattern which serve from the J-104 `EventStudyCache` and never rebuild the set), **J-25 still HTTP-500s with a `MemoryError` at research.py:216** (confirmed in the live backend log) and J-104's "labs load reliably" acceptance stays unmet. `_combination_observations` (line 421) is a **latent cold-miss OOM** currently masked only by the cache hit. The iter-47 evaluator prescribed exactly this iter-48: stream both reads (factor-lab first), keep figures byte-identical, then live re-verify on a quiet backend + a flushed-green suite. Coherence was COHERENCE-PASS for iter-47, so this is not a forced consolidation pass — it is the completion of the same J-105 contract.

**Lessons applied (from lessons.md / MEMORY):**
- **iter-47 lesson (directly applies):** a "stream the heavy read path" fix can be HALF-DONE — grep EVERY unbounded `.all()` in the function (ForwardReturn AND ScannerResult AND ScannerRun) and probe the UNCACHED lab COLD; a cache hit masks the defect on its cached siblings. (Audit already done in this spec — see IN SCOPE.)
- **iter-46 lesson:** verify scale-bounded read paths against the LIVE 3.3 GB data volume, not just small fixtures; a freshly-warmed-idle-backend MemoryError at the FIRST fetch is a real defect, "Backend unavailable" under a concurrent full-suite is contention.
- **iter-45 lesson:** heavy-research browser-QA MUST run on a freshly-restarted, warmed, single-fetch-at-a-time backend; if a lab shows "Backend unavailable"/500/timeout, check whether the live backend is hung (CPU still pegged) and re-run the touched modules in isolation before calling REGRESSION. Verify the EXACT `?as_of=` (underscore) param spelling before trusting a curl-based "ignores param" FAIL.
- **iter-43/42/36 lesson:** a backend-only iteration whose acceptance is a RENDERED surface auto-skips browser-QA on `Frontend Present: no` — so this iter sets **`Frontend Present: yes`** to force the live render-capture in the SAME iteration; PLAN the Playwright fallback UP FRONT (Chrome MCP CDP has emptied the evidence dir on iters 38/39/40/42); md5sum the dir FIRST and reject "Loading…"/"Backend unavailable"/skeleton frames.
- **iter-37 lesson:** justify the optimization with BOTH a byte-identity assertion AND the load/compute behaviour it claims; gate GOAL_ACHIEVED candidacy on the FLUSHED full suite (`0 failed, EXIT 0`), not targeted modules — re-run any isolated `test_warmup.py` / `test_watchlist_persistence.py` / `test_data_manager_jobs_pipeline.py` E/F before attributing a suite failure (slow-boot/contention flake).
- **iter-20 lesson:** the `read_batch_size` config key already exists from iter-47 (boot-validated ≥1) — reuse it; do NOT introduce a new float/int literal in a CALC_FILE (`test_no_magic_numbers` blanket-forbids them). No new `table=True` model is added, so `test_db.py`'s expected-tables guard is unchanged.

## IN SCOPE

### Backend
- [ ] **`_factor_observations` (apps/backend/app/engine/research.py:216)** — replace the unstreamed `session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()` with a `yield_per(batch)`-streamed read over the same `runs_with_fr` filter (batch = `cfg.research.read_batch_size`, exactly as the FR read at line 211 already does), so the ~609K ScannerResult rows are not all materialized as ORM objects at once. Iterate the streamed rows in the same id order the prior implicit `.all()` produced (add `.order_by(ScannerResult.id)` if needed to lock byte-identical ordering of the resulting observations). **The factor value is read via `_extract_factor_value(res, parsed)`, which for a `column` factor reads a typed attribute and for a `component` factor reads `res.record_json` (a JSON blob) — so this read MUST keep `record_json` (and any typed factor column the catalog can reference) available on each streamed row.** The simplest byte-identical approach is to stream the full `ScannerResult` ORM rows via `yield_per` (no `.all()` materialization) rather than a narrow column projection that would drop `record_json`; if a column projection is used instead it MUST project `run_id`, `ticker`, `record_json`, and every typed factor column `_extract_factor_value`/`parse_factor_source` can name. Keep the `run_rows`/`regime_by_run` map (line 220) read VERBATIM — it is already run-id-bounded; stream it too if it is large enough to matter, otherwise leave it (bounded to `runs_with_fr`, not the full table). Every observation dict, decile, rank-IC, and `by_regime` figure stays **byte-identical**.
- [ ] **`_combination_observations` (apps/backend/app/engine/research.py:421)** — apply the same `yield_per(batch)` streaming to the identical `select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr)).all()`, locking the same id order (`.order_by(ScannerResult.id)`), keeping `record_json` available for `_extract_factor_value`, so the factor-combination cold-miss path can never reintroduce the OOM even on a cache MISS. Every composite/strict-overlap cohort figure stays **byte-identical**.
- [ ] **Audit confirmation (no code change expected):** the other ScannerResult/ScannerRun reads in research.py are already bounded/streamed — `_regime_setup_pattern_observations` (research.py:1533) is already column-projected + `yield_per`-streamed; `_recovery_turn_observation_set` (research.py:1771) is run-id-bounded to signal dates with `.order_by(ScannerResult.id)` and is cache-served (`recovery_turn_edge_cached`); line 220 (`select(ScannerRun)…all()`) and line 2378 are bounded to `runs_with_fr` (not the full table); lines 833/986/2044 are column-projected. Record this audit in the dev handoff; if any of these is found to also OOM on the live DB under the streamed standard, stream it the same way (still no figure change).
- [ ] **Tests:** add a deep-equality test that asserts the streamed `_factor_observations` and `_combination_observations` produce the **byte-identical** observation list (and the resulting `compute_factor_lab` / `compute_factor_combination` payloads) as the prior `.all()` reference, across as-of / all-history, a column factor AND a component (`record_json`) factor, and a zero-N cohort. Mirror the existing `test_research_streaming.py` shape from iter-47.

### Frontend (if applicable)
- [ ] No frontend source change is expected (`apps/frontend` diff empty). `Frontend Present: yes` is set ONLY to force the browser-QA live render-capture step (the iter-42/43 lesson — the acceptance is a RENDERED lab loading); the developer makes no frontend edit.

### New user-facing capability
The Factor Lab decile/rank-IC view (`/research/factor-lab`) loads with real figures on the full live dataset instead of returning an HTTP 500 / "Backend unavailable" banner — restoring J-25 and closing the iter-46 regression for the last affected lab.

### New information displayed
None. Every figure is byte-identical to the pre-iter-46 aggregation — this is a memory-safety property, not a new value.

### New user actions
None.

### UI surface changes
None — the Factor Lab page (`/research/factor-lab`) and `/research/factor-combination` are unchanged in structure; they merely render successfully (no skeleton/error) on the live DB.

### Product surface delta
The research-labs hub becomes fully reliable: all five heavy labs (event-study, factor-lab, factor-combination, regime×setup×pattern, downtrend-opportunity) now serve HTTP 200 on the full live dataset, completing J-104's "labs load reliably" acceptance.

### Blueprint conformance
No new surfaces and no nav-skeleton change. The work lives under the existing **Research** Information-Architecture home — specifically the `/research/factor-lab` (J-25/J-26) and `/research/factor-combination` sub-routes registered under the Research hub (blueprint.md lines 339–344). No `blueprint.reapproval-requested` is filed.

### Data-contract additions
None. `forward_returns` and all research aggregates (Factor-Lab decile/rank-IC, multi-factor composite, event-study/RSP/downtrend cells, every `N=` cohort) are already-registered Data-Contract values read from their canonical sources via the existing `GET /api/research/{factor-lab,factor-combination,event-study,regime-setup-pattern,downtrend-opportunity}` + `GET /api/research/samples` endpoints. No new endpoint, no new computation, no new `table=True` model. The existing **J-105** Data-Contract row (blueprint.md line 388) is updated with an additive annotation noting that the **ScannerResult-side** reads in `_factor_observations` (research.py:216) and `_combination_observations` (research.py:421) are now `yield_per`-streamed too (completing the iter-47 ForwardReturn-side streaming); the streaming batch size remains the existing `config.research.read_batch_size` (no new config key).

## OUT OF SCOPE

- Any change to a canonical score / return / membership / aggregate VALUE — figures must stay byte-identical (assert it).
- Adding any new table, endpoint, config key (beyond reusing `research.read_batch_size`), or magic-number literal in a CALC_FILE.
- Re-triggering the J-85 `kind:rebuild` (~11h, destructive; the data is correct — MEMORY).
- The data-walled J-22/J-23/J-24 (provider-gated; stay honestly blocked-NA, non-vetoing per goal.md:105–108).
- Any caching of Factor Lab itself — the fix is to make the UNCACHED recompute memory-safe (streamed), not to introduce a new cache (caching is the J-104 path already done for the other labs; adding one here is out of scope and unnecessary once the read streams).

## DEFINITION OF DONE

- [ ] J-25 (Factor Lab decile/rank-IC) passes via browser-qa-agent on the live full dataset — the lab renders real figures (no "Loading…"/"Backend unavailable"/skeleton), HTTP 200, no `MemoryError` in the backend log.
- [ ] J-104 flips partial → passing (all five heavy labs load reliably) and J-105 flips partial → passing (the read path never materializes an unbounded full table) on live evidence.
- [ ] Required-still-passing journeys remain green (re-rendered/replayed): J-29, J-26, J-77, J-91, J-103 (must STAY passing — re-render on a quiet, warmed, single-fetch backend), J-51/J-63/J-65 (factor-lab `N=` drill-down now testable once J-25 serves; total == published N), J-06/J-18 (CRITICAL)/J-07 (CRITICAL), J-72/J-32 (streamed-builder byte-identity).
- [ ] No anti-goal violation introduced (figures byte-identical → Single source of truth / No recompute; no magic number; no fabricated data; honest error only on a genuine fault).
- [ ] Unit/integration tests pass; the deep-equality byte-identity tests for the streamed `_factor_observations`/`_combination_observations` are green; no regressions.
- [ ] The FLUSHED full backend suite shows `0 failed, EXIT 0` (pump nohup-async; never block the evaluator on the in-flight suite). This is the GOAL_ACHIEVED-candidacy gate.
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-48-dev.md`, including the ScannerResult/ScannerRun `.all()` audit.

## TESTING REQUIREMENTS

- **Browser (live, quiet/warmed/single-fetch backend; Playwright fallback PLANNED UP FRONT; md5sum the evidence dir FIRST):**
  - **J-25** — open `/research/factor-lab`, pick a **column** factor (e.g. RS 3m) AND a **component** factor (one that reads `record_json`), pick a horizon; the decile table (D1…D10 mean return + risk-adjusted + n) and a numeric rank-IC render with real figures; no skeleton/error banner; backend log shows no `MemoryError` at research.py:216.
  - **J-26 / factor-combination** — `/research/factor-combination` renders the Combined cohort figures (cold-miss safe).
  - **J-104** — all five heavy labs serve HTTP 200 (event-study, factor-lab, factor-combination, regime×setup×pattern, downtrend-opportunity), one heavy fetch at a time.
  - **J-51/J-63/J-65** — a Factor Lab `N=` chip opens `/research/samples` in a new tab; drill-down total == the published cell N (count coherence).
  - **J-29/J-77/J-91/J-103** — re-render with real figures (must STAY passing).
  - **CRITICAL** J-18 (0 native `input[type=date]` on the research surfaces; single global as-of), J-07 (Risk-Off → 0 Actionable on the snapshot-served fast path), J-06 (single source — diagnostic/served reconcile).
- **Unit/integration:**
  - Deep-equality byte-identity: streamed `_factor_observations` vs the prior `.all()` reference observation list, and the full `compute_factor_lab` payload (deciles, rank_ic, by_regime, n_total) — across as-of / all-history, a column factor, a component (`record_json`) factor, and a zero-N cohort.
  - Deep-equality byte-identity: streamed `_combination_observations` vs reference, and `compute_factor_combination` (composite + strict_overlap cohorts) — as-of / all-history, multi-factor, zero-N.
  - The streamed reads honor the `as_of` cutoff identically (`ScannerRun.asof_date <= as_of` membership filter unchanged; the EXACT param is `?as_of=` with an underscore — verify spelling before trusting any curl-based "ignores param" FAIL, iter-45 lesson).
  - Existing `test_research.py` / `test_samples.py` / `test_research_streaming.py` stay green (event-study J-29/J-63, downtrend J-91, samples count-coherence J-51/J-65).
- **Error cases:** an unknown factor key still raises ValueError → 422 (unchanged); a genuine fault still surfaces an honest "Backend unavailable — No figures are shown rather than fabricated values" banner (never fabricated data); a zero-N cohort still shows honest NA, never a fabricated row.

## NOTES

- **Root-cause grounding (verified in this spec against the live source):** both `_factor_observations` (research.py:216) and `_combination_observations` (research.py:421) still contain `session.exec(select(ScannerResult).where(ScannerResult.run_id.in_(runs_with_fr))).all()` — the exact unstreamed reads the iter-47 evaluator flagged. The ForwardReturn side at lines 211/411 is already `yield_per`-streamed (iter-47). `_regime_setup_pattern_observations` (1533) is already streamed; `_recovery_turn_observation_set` (1771) is run-id-bounded + cached. Factor Lab is **uncached** (`compute_factor_lab` calls `_factor_observations` directly every request) → it is the genuine OOM site; factor-combination is cached so its line-421 OOM is latent (cold-miss only).
- **Byte-identity caveat:** `_extract_factor_value` reads `record_json` for component factors — a naive column projection that drops `record_json` would silently change component-factor figures. Prefer streaming the full ORM row via `yield_per` (which already avoids the all-at-once materialization that causes the OOM), or, if projecting, include `record_json` + every typable factor column. Lock the row order (`.order_by(ScannerResult.id)`) so the resulting observation list is byte-identical to the prior implicit `.all()` order.
- **Evidence hygiene / operational (iter-45/46/47 + pump lessons):** bring up a FRESH `:8835` (wait health "ready" so warm-up finishes), `:3835`, `:9222`; **NEVER run the full backend suite concurrently with the heavy-lab browser probes** (its RAM pressure exacerbated the factor-lab OOM in iter-47 — run the suite nohup-async AFTER the live probes, or on a separate window); fetch **one** heavy lab at a time; allow ~50–60s for the factor-lab cold compute over ~598K rows before the first response. If a lab shows "Backend unavailable", check whether the live uvicorn is hung (CPU still pegged) and re-run the touched modules in isolation before calling REGRESSION.
- **GOAL_ACHIEVED candidacy:** after J-25 flips passing with byte-identical figures + J-104/J-105 flip passing + a flushed-GREEN suite (`0 failed, EXIT 0`) + COHERENCE-PASS + zero regression, the next evaluation is a sound GOAL_ACHIEVED candidate (every buildable Must-have J-01..J-21, J-25..J-105 positive-evidenced; J-22/J-23/J-24 stay honestly blocked-NA, non-vetoing per goal.md:105–108). Do NOT block the evaluator on the in-flight suite (iter-11/29/37 lesson).
