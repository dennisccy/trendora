# Goal Iteration 37 — Restore the load-once bar-cache invariant, optimize the /api/data read path, and live-verify the /data membership timeline + universe diagnostic

<!-- machine-readable goal-mode metadata -->
## Goal Mode Metadata

- **Session ID:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
- **Iteration:** 37
- **Mode:** next
- **Depth:** full
- **Frontend Present:** yes
- **Target journeys:** J-94, J-96
- **Required-still-passing journeys:** J-93, J-06, J-07, J-18, J-87, J-88, J-36, J-37, J-39, J-85, J-15
- **Anti-goal reminders (verbatim from `docs/goal.md`):**
  - **No lookahead.** Scoring for a snapshot dated D MUST use only price bars with date ≤ D; forward returns MUST use only bars with date > D. The walk-forward MUST be unit-tested to prove no future bar influences an as-of score. *(critical)*
  - **Snapshots are immutable.** A persisted `scanner_run` and its result rows MUST never be updated or overwritten after creation; forward returns live in a separate append-only table keyed to the snapshot. A wholesale regenerate-from-scratch of the entire snapshot set IS permitted as a deterministic, operator-triggered, confirm-gated create-once rebuild … but an existing snapshot MUST never be UPDATED or overwritten in place. *(critical)*
  - **Single source of truth.** Each of the six canonical scores (and the A–E bucket and setup status) MUST be computed exactly once by the scoring/regime engine and read identically by every page; the API and frontend MUST NOT recompute them. The same symbol's score MUST NOT differ between two views. *(critical)*
  - **No recompute in the read path.** Read endpoints MUST serve canonical values from the persisted immutable snapshot for the resolved as-of date; they MUST NOT recompute scores/returns/buckets per request … The relocated as-of-scoped evidence aggregate … is likewise derived once per resolved as-of date over the snapshots dated ≤ D, persisted/cached, and read from storage — never recomputed per request. *(extends Single source of truth)*
  - **Coverage & missing-data are descriptive & honest.** The coverage figures, the per-symbol/per-universe-member table, and the insufficient-for-analysis diagnostic MUST be read-only metadata derived from the stored bars + config — they MUST NOT recompute or restate any canonical score, return, bucket, or setup … the history threshold … MUST come from config (`indicators.min_history_bars` …) — no magic number in coverage/diagnostic code. *(extends No fabricated data + No recompute in the read path)*
  - **No fabricated data.** On a data-provider failure the system MUST surface an explicit stale/unavailable state and MUST NOT synthesize prices or scores to force a green journey.
  - **No magic numbers.** Every scoring weight, threshold, decision-rule cutoff, bucket edge, universe entry, and theme definition MUST come from the config file — no such literal in calculation code.
  - **Risk-Off must gate Actionable.** When the regime is Risk-Off, the scanner MUST mark zero stocks "Actionable" (watchlist-only). *(critical)*
  - **Exactly one date selector.** (J-18) — no page-local or second date state anywhere in this iteration.

## GOAL

Restore the J-46 "each symbol loaded at most once per parallel backfill job" invariant that the iter-36 resolver `trailing_count` cold-miss optimization silently broke, make `GET /api/data` fast and concurrency-robust without changing any served value, and capture the live `/data` render evidence that flips J-94 back to passing and J-96 to passing.

## BACKGROUND

The prior iter-37 attempt was a lean live-verify that got ABORTED on a pump-heartbeat technicality — but before it aborted, the live re-verify exposed TWO real problems the artifacts had not recorded, so this iteration is re-planned as a **full** fix-and-verify pass rather than a lean verify.

1. **A genuine iter-36 REGRESSION (primary fix — blocks a green suite / GOAL_ACHIEVED).** `apps/backend/tests/test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` FAILS — reproduced in isolation just now: `assert 3 == 1` (e.g. `ABBV` loaded 3×, `A` 2×). iter-36 added `active_bar_cache()` / `_BarCache.trailing_count()` to `apps/backend/app/engine/prices.py` and routed `universe_resolver.resolve_with_reasons` through `trailing_count` when a cache context is active (the J-96 cold-miss bound). Root cause: `prefilled_bar_cache.prefill()` only records symbols that actually have rows in `daily_prices`; a candidate-pool symbol with **zero** bars is never in `_dates_by_symbol`, so the resolver's per-date `trailing_count(sym, asof)` falls into `bars_asof`'s lazy-load path and re-issues a per-symbol load **every snapshot date** of the parallel K-date backfill — breaking the load-once-per-job invariant. The iter-36 targeted-only QA missed it; the full suite caught it. The fix must restore load-once WITHOUT changing any served value (a zero-bar symbol's trailing count is 0 regardless of path; membership-timeline + scoring byte-identity must hold).

2. **`GET /api/data` is still ~10–12 s even cache-WARM.** The J-96 membership_timeline cache HIT is confirmed; the residual ~10 s is OTHER uncached O(1369) work inside `compute_coverage`. `/data` fetches `/api/data` once on load (no polling), so one user sees /data render in ~10 s, but that request holds a DB connection — any concurrency (browser-qa probing, a user refresh) exhausts the pool (size 5 + overflow 10) → `db_ok:false` → /data goes skeleton. This iteration SHOULD cache/optimize the remaining `compute_coverage` O(1369) work to make `/api/data` sub-second and robust, with the served coverage block byte-identical. At minimum it MUST make /data live-verifiable; if the residual ~10 s is left, it stays a documented limitation.

3. **Live re-verify technique.** J-94/J-96 live re-verification MUST use a SINGLE sequential `/data` page load with a generous (~30 s) wait for hydration, and md5sum the evidence dir first. NEVER do concurrent `/api/data` probing — that exhausted the pool last attempt and produced only skeleton frames plus a 2.5 h browser-qa run. Skeleton frames are rejected, not evidence (iter-18/33 precedent).

This is `full` depth because: the prior evaluator's lean recommendation was written before the regression was known; the iteration now touches engine read-path code (`prices.py` / `universe_resolver.py` / `data_manager.py`), must add/repair backend tests, and is gated on the full ~3.5 h pytest suite flushing `0 failed` for any GOAL_ACHIEVED candidacy.

**Applicable lessons (from `lessons.md`):**
- **iter-34** — a backend feature can be built + unit-correct + coherence-clean yet still fail its user-facing acceptance until the persisted/served layer it feeds is regenerated; verify the SERVED/RENDERED end state, never just the DB-direct values. Here: do not re-trigger the J-85 rebuild (data is correct); verify the rendered /data surface.
- **iter-35** — a correct data-volume increase exposed a latent O(dates×pool) read-path cost; the served VALUES are correct, only delivery is too slow. The fix is read-path caching/precompute/optimization with the served block byte-identical — never a resolver-math change or another rebuild.
- **iter-36** — a backend-only read-path fix whose purpose is to restore a PAGE RENDER gets auto-skipped by browser-QA on "Frontend Present: no"; the decomposer should set `Frontend Present: yes` (done above) so the live evidence is captured in the SAME iteration. Never flip a UI journey to passing from API-layer evidence alone — "expected to render" is not "verified-rendered".
- **iter-29** — on this 1369-run host, any `loaded_engine`-seed `test_*.py` boots the heavy backend and cannot finish under a subagent Bash cap; split fast (no-boot) vs slow (seed-boot) tests, verify anti-goal legs via the fast set, and require a flushed `0 failed, EXIT 0` from a `nohup`-launched full suite via the pump for a GOAL_ACHIEVED candidate.
- **iter-11 / iter-30** — never block the evaluator on the in-flight full suite; hand it to the pump nohup-async and gate on the flushed terminal summary; re-run any single `test_warmup.py` / `test_data_manager_jobs_pipeline.py` `F` isolated before attributing it (known slow-boot / scanner_runs-race / concurrent-QA-warm-up flake).
- **iter-18 / iter-33** — md5sum the evidence dir FIRST; reject any un-hydrated skeleton or wrong-surface frame; scroll the below-the-fold /data panels into the viewport and VIEW the pixels; a differential leg needs byte-distinct frames.

## IN SCOPE

### Backend
- [ ] **Restore the load-once invariant (PRIMARY).** Fix the iter-36 regression so a K-date parallel backfill loads each symbol's bar series AT MOST ONCE for the whole job. The defect is that `universe_resolver.resolve_with_reasons`'s active-cache branch calls `_BarCache.trailing_count(session, sym, asof)` for every candidate-pool symbol, and `trailing_count` triggers a fresh per-symbol `bars_asof` lazy-load for any symbol not in `_dates_by_symbol` — which includes every candidate-pool symbol that has zero rows in `daily_prices` (never recorded by `prefill`), repeated once per snapshot date. Restore load-once by ensuring the trailing-bar count for ALL candidate-pool symbols (including no-bar names) is sourced from the once-loaded prefilled cache rather than a per-date re-load. Acceptable approaches (developer's choice, smallest correct change): (a) have `prefill` record an empty/absent series for every requested/candidate symbol so a no-bar symbol resolves to a count of 0 from the cache with no re-load; or (b) make `_BarCache.trailing_count` memoize the "this symbol has no bars" result after the first load so it is never re-loaded on later dates; or (c) prefill the candidate-pool symbol set explicitly up front. Whatever the approach, a no-bar candidate-pool symbol must be loaded AT MOST ONCE for the whole job.
- [ ] **Byte-identity is non-negotiable.** The served `membership_timeline` payload and the canonical `score_stocks(D)` output (rows/scores/buckets/setups/VCP) MUST be byte-identical before and after this fix. A zero-bar symbol's `trailing_count` is `0` and yields `below_history` exactly as the grouped-count path does; the excluded-by-reason counts and the admitted set must not change.
- [ ] **(Recommended, scope as judged) Optimize the residual `compute_coverage` O(1369) cost** so `GET /api/data` is sub-second and robust under concurrency, with EVERY served value in the coverage block byte-identical. Prefer the established pattern: cache/precompute the remaining per-date O(1369) work during the background warm-up daemon (`warmup._run_warmup`, the J-40/J-41 serve-fast lifespan precedent) keyed by `research._dataset_version` (the same stamp the iter-36 `MembershipTimelineCache` uses — do NOT introduce a second version stamp or a second computation of any coverage value). If a NEW cache table is required, register it in `test_db.py`'s expected-tables guard (the iter-20/21 lesson) — do NOT use `_ADDITIVE_COLUMNS` for a standalone table. If this optimization is descoped, the ~10 s residual MUST be documented as a known limitation in the dev handoff and the /data page must still render within the live-verify wait.
- [ ] **Tests.** Confirm `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` passes after the fix (do NOT weaken the assertion — the invariant is the contract). Keep / extend the existing `test_cached_snapshot_equals_uncached_row_level`, `test_cached_bars_asof_slices_le_d_identically`, and the membership-cache byte-identity tests green. If the no-bar-symbol case is the root cause, add a fast unit test that a candidate-pool symbol with zero bars is counted as 0 trailing bars from the prefilled cache with no additional per-date load. If the coverage optimization is done, assert the served coverage block is byte-identical to the pre-optimization `compute_coverage` output and that the warm read does not recompute (mirror `test_warm_read_does_not_recompute_timeline`).

### Frontend (if applicable)
- [ ] No frontend code change is expected. `Frontend Present: yes` is set ONLY to FORCE the browser-QA step so the /data render is captured live this iteration (the iter-36 auto-skip lesson). If the live re-verify surfaces a genuine rendering defect on `/data` (e.g. a skeleton that never hydrates for a reason other than the endpoint latency), fix it minimally; otherwise the frontend diff stays empty.

### New user-facing capability
None new. This iteration restores correctness/performance so the existing `/data` membership-timeline (J-96) and per-date universe-resolution diagnostic (J-94) render reliably and promptly for a single user and under light concurrency.

### New information displayed
None new — same `membership_timeline` and coverage-diagnostic values, now delivered fast enough to hydrate.

### New user actions
None.

### UI surface changes
None — the `/data` Data Manager page is unchanged; it simply hydrates promptly because `GET /api/data` responds quickly.

### Product surface delta
The `/data` page reliably shows the rising membership-timeline step function (0 → 544 from ~2021-10-18 with populated entries/exits and the three honesty labels) and the per-date universe-resolution diagnostic (admitted + excluded-by-reason counts), even under a second concurrent reader — closing the iter-35 regression at the user-visible layer.

### Blueprint conformance
No new surfaces. Both target journeys live on the EXISTING Data Manager `/data` coverage home (Information Architecture, blueprint line 293) and on the EXISTING `data_manager:compute_coverage` → `GET /api/data` coverage rows in the Data Contract (blueprint lines 336–337). The J-96 Data-Contract row's iter-37 annotation was updated additively to record this fix-and-verify scope (same module/endpoint/values — no nav-skeleton change, no re-approval required).

### Data-contract additions
None. The fix changes HOW the trailing-bar count is sourced (cache vs per-date re-load) and optionally HOW the coverage block is delivered (cached/precomputed), never WHAT is computed or served. No new displayed value, no new endpoint, no second computation of any value already in the Data Contract. If a coverage cache table is introduced it is internal performance state (not a displayed value), keyed by the existing `dataset_version` stamp.

## OUT OF SCOPE

- **Do NOT re-trigger the J-85 `kind:"rebuild"` job.** It is ~11 h, destructive (clears ~1370 daily snapshots), and the data is already correct (the iter-35 rebuild fixed J-93; J-96 data is DB-direct-correct). This iteration is a read-path fix, not a data regeneration.
- No resolver-math change, no scoring-formula change, no membership change — only the cache sourcing and (optionally) the coverage delivery.
- No new snapshot column, no in-place snapshot update (Snapshots are immutable).
- No second `dataset_version` stamp, no second coverage/timeline computation path, no new public endpoint.
- No `/stocks` work — J-93 uses the fast `/api/stocks` snapshot path and is unaffected; only re-smoke it.
- No frontend redesign; no new date state or control.

## DEFINITION OF DONE

- [ ] `apps/backend/tests/test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` PASSES (load-once restored), with the assertion unchanged.
- [ ] The served `membership_timeline` payload and `score_stocks(D)` output are byte-identical before/after the fix (asserted).
- [ ] `GET /api/data` renders the `/data` page within the live-verify hydration wait (sub-second target if the coverage optimization lands; the residual ~10 s documented as a known limitation otherwise) and does NOT go skeleton under a single concurrent reader.
- [ ] Target journeys verified via browser-qa-agent on LIVE, md5-distinct, non-skeleton evidence: **J-94** (per-date universe-resolution diagnostic renders — admitted + excluded-by-reason counts at the resolved as-of) and **J-96** (rising membership-timeline step function from ~2021-10-18 with populated Entries/Exits + the three honesty labels scrolled into the viewport and the pixels viewed).
- [ ] Required-still-passing journeys remain green: J-93 (`/stocks` still slides — fast path), J-06 (single source; the J-94 diagnostic count reconciles with the served `/stocks` membership), J-07 (CRITICAL Risk-Off → 0 Actionable), J-18 (CRITICAL exactly one date selector — 0 `input[type=date]`), J-87/J-88 (Dashboard market phase / P(bear) unchanged), J-36/J-37/J-39/J-85 (co-located `/data` journeys re-smoked), J-15 (fast snapshot reads).
- [ ] No anti-goal violation introduced (byte-identity of served values; no lookahead; no recompute in the read path; no fabricated data; snapshots immutable; no magic numbers; Risk-Off gate intact; exactly one date selector).
- [ ] Full backend pytest suite flushes `0 failed, EXIT 0` (handed to the pump nohup-async; the evaluator gates GOAL_ACHIEVED candidacy on the FLUSHED line, never on the in-flight suite; `test_warmup.py` / `test_data_manager_jobs_pipeline.py` timeouts are known contention flakes — re-run isolated before attributing).
- [ ] Dev handoff written at `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37-dev.md` (including, if the coverage optimization is descoped, the residual `/api/data` latency documented as a Known Issue).
- [ ] `ui-test-results.md` is WRITTEN with live evidence (not SKIPPED) — the closure artifact iter-33/36 lacked.

## TESTING REQUIREMENTS

- **Browser (live, single sequential page load, ~30 s hydration wait — NEVER concurrent `/api/data` probing; md5sum the dir first; reject skeleton frames):**
  - J-94 — `/data` per-date universe-resolution diagnostic renders (admitted count + excluded-by-reason: below-history / below-price / below-ADV at the resolved as-of).
  - J-96 — `/data` membership-timeline rising step function from ~2021-10-18, populated Entries/Exits, three honesty labels (survivorship / warm-up / universe-relative) scrolled into view and the pixels viewed.
  - Re-smoke J-36, J-37, J-39, J-85 (co-located `/data`), J-93 (`/stocks` still slides 0/495/504/544 — fast path), J-18 (0 `input[type=date]`), J-07 (Risk-Off → 0 Actionable), J-06 (NVDA `/stocks` list value == Stock-Detail value; reconcile the J-94 diagnostic count vs the served `/stocks` membership).
- **Unit/integration:**
  - `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` passes (load-once restored; assertion unchanged).
  - The no-bar candidate-pool symbol resolves to 0 trailing bars from the prefilled cache with at most one load (new fast test if the no-bar case is the root cause).
  - Membership-timeline + `score_stocks(D)` byte-identity before/after the fix.
  - If the coverage optimization lands: served coverage block byte-identical to the pre-optimization output; warm read does not recompute.
  - Run the FAST (no-boot) subset under the subagent cap; hand the FULL suite to the pump (nohup-async) for the flushed `0 failed, EXIT 0` gate.
- **Error cases:**
  - Empty DB → empty-but-valid timeline + coverage (no fabricated dates/members).
  - A candidate-pool symbol with zero bars is `below_history` (count 0), never fabricated as present.
  - `GET /api/data` under a second concurrent reader does NOT return `db_ok:false` / a skeleton (pool not exhausted).

## NOTES

- The regression was confirmed by reproducing the failing test in isolation (`assert 3 == 1`; over-loaded symbols are candidate-pool names like `ABBV`/`A`). Encode the load-once fix as the primary deliverable.
- This is a read-path-performance-and-correctness iteration: served values byte-identical, coverage block byte-identical, NO resolver math change, NO snapshot rebuild (the destructive J-85 rebuild stays out of scope — the data is already correct).
- The live re-verify is the ONLY path to flip J-94 back to passing and J-96 to passing (iter-36 auto-skip lesson) — hence `Frontend Present: yes` to force browser-QA. Do not upgrade either journey from API-layer evidence alone.
- After J-94 re-renders and J-96 flips to passing on live evidence, with COHERENCE-PASS, zero regression, and a flushed GREEN full suite, this iteration is a sound GOAL_ACHIEVED candidate — every buildable Must-have green; J-22/J-23/J-24 stay honestly blocked-NA (non-vetoing per goal.md lines 105–108).
- Closes open_item `iter35-api-data-timeline-uncached` and the iter-36 carried J-94/J-96 live-evidence gap; additionally records and closes the newly-discovered `test_bar_cache` load-once regression.
