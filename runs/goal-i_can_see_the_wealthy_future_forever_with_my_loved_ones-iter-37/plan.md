# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37 Execution Plan

## What to Build
- **PRIMARY — restore the J-46 load-once invariant** broken by the iter-36 cold-miss optimization.
  A K-date parallel backfill must load each symbol's bar series AT MOST ONCE for the whole job.
  Root cause (confirmed): `_BarCache.prefill` (`prices.py` L66-81) only records symbols that have
  rows in `daily_prices`; a candidate-pool symbol with ZERO bars is never in `_dates_by_symbol`,
  so `resolve_with_reasons`'s active-cache branch (`universe_resolver.py` L140-142) calls
  `trailing_count(sym, asof)` which falls into `bars_asof`'s lazy per-symbol load (`prices.py`
  L114-119 → L83-100) — re-issued once per worker session (not shared), breaking load-once.
  Fix it with the smallest correct change (developer's choice among the three sanctioned options
  below). Test `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` currently
  fails `assert 3 == 1`; it must pass with the assertion UNCHANGED.
- **Byte-identity (non-negotiable):** the served `membership_timeline` payload and the canonical
  `score_stocks(D)` output (rows/scores/buckets/setups/VCP) MUST be byte-identical before and after
  the fix. A zero-bar symbol's trailing count is `0` → `below_history` either way; admitted set,
  excluded-by-reason counts, and universe_count must not change.
- **(Recommended, scope as developer judges) Optimize the residual `compute_coverage` O(1369) cost**
  so `GET /api/data` is sub-second and robust under a concurrent reader, with EVERY served coverage
  value byte-identical. The residual ~10-12 s is the single-as-of `_resolved_universe` /
  `_coverage_diagnostic_absent` resolves in `compute_coverage` (`data_manager.py` L631/L691),
  NOT the now-cached J-96 timeline. Use the established pattern: precompute/cache in the warm-up
  daemon keyed by the EXISTING `research._dataset_version` stamp (the same stamp the iter-36
  `MembershipTimelineCache` uses — do NOT introduce a second version stamp or a second computation
  of any coverage value). If a new cache table is added, register it in `test_db.py`'s expected-tables
  guard (standalone table, NOT `_ADDITIVE_COLUMNS`). If descoped, the residual ~10 s MUST be
  documented as a Known Issue in the dev handoff AND `/data` must still hydrate within the live wait.
- **LIVE re-verify J-94 + J-96** on `/data` via browser-QA (single sequential page load, ~30 s
  hydration wait, md5sum the evidence dir first, scroll below-fold panels into the viewport). This
  is the ONLY path to flip J-94 back to passing and J-96 to passing (iter-36 auto-skip lesson —
  never upgrade a UI journey from API-layer evidence alone).

### Sanctioned fix approaches (developer picks the smallest correct one)
- (a) Have `prefill` record an empty/absent series for every requested/candidate symbol so a no-bar
  symbol resolves to count 0 from the shared cache with no re-load; OR
- (b) Make `trailing_count` memoize the "this symbol has no bars" result after the first load so it
  is never re-loaded on later dates / other worker sessions reading the shared cache; OR
- (c) Prefill the candidate-pool symbol set explicitly up front.
- Whatever the approach: a no-bar candidate-pool symbol must be loaded AT MOST ONCE for the whole job,
  and the served values stay byte-identical. The default (no-cache) per-request resolve path must
  stay unchanged.

## Agents Required
- developer: yes -- restore the load-once invariant in `prices.py`/`universe_resolver.py` (and the
  shared-cache worker plumbing as needed); add/repair the no-bar-symbol fast unit test; assert
  membership_timeline + `score_stocks(D)` byte-identity; optionally precompute the residual coverage
  cost in `warmup._run_warmup` keyed by `_dataset_version`; write the dev handoff. No frontend code
  change expected (see below).

## Frontend Present
yes

## Files to Create/Modify
- `apps/backend/app/engine/prices.py` -- fix `_BarCache.prefill`/`trailing_count` so no-bar
  candidate-pool symbols are sourced once from the shared cache, never per-date/per-worker re-loaded.
- `apps/backend/app/engine/universe_resolver.py` -- adjust the active-cache branch (L133-142) only if
  needed; keep the no-context default path byte-identical.
- `apps/backend/app/engine/data_manager.py` -- (only if the coverage optimization lands) route the
  residual single-as-of coverage resolve through a `_dataset_version`-keyed cache; no second value
  computation, no second version stamp.
- `apps/backend/app/engine/warmup.py` -- (only if the coverage optimization lands) precompute the new
  coverage cache off the boot path, non-fatal (own guard), mirroring `_warm_membership_timeline`.
- `apps/backend/app/models.py` -- (only if a new coverage cache table is required) add a standalone
  `create_all`-managed cache model keyed by `dataset_version`.
- `apps/backend/tests/test_bar_cache.py` -- add a FAST unit test: a candidate-pool symbol with zero
  bars counts as 0 trailing bars from the prefilled cache with at most one load. Keep
  `test_kdate_backfill_loads_each_symbol_at_most_once` assertion unchanged.
- `apps/backend/tests/test_db.py` -- (only if a new cache table is added) extend the expected-tables guard.
- `apps/backend/tests/test_data_manager_membership_cache.py` (or sibling) -- (if coverage opt lands)
  assert the served coverage block is byte-identical to the pre-optimization `compute_coverage` output
  and the warm read does not recompute (mirror `test_warm_read_does_not_recompute_timeline`).
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-37-dev.md` -- rewrite
  the handoff to record the real fix (the existing one is the aborted verify-only stub).

## UI Evolution
- New user-facing capability: none new. This restores reliability/promptness of the EXISTING `/data`
  Data Manager surface (J-94 per-date universe-resolution diagnostic + J-96 membership timeline).
- New information displayed: none — the SAME `membership_timeline` and coverage-diagnostic values,
  now delivered fast enough to hydrate under a single concurrent reader.
- New user actions: none.
- UI surface changes: none — `/data` is unchanged; it simply hydrates promptly because `GET /api/data`
  responds quickly (the iter-35 regression closed at the user-visible layer).
- Navigation changes: none.

> `Frontend Present: yes` is set ONLY to FORCE the browser-QA step so the live `/data` render is
> captured this iteration (the iter-36 auto-skip lesson). If the live re-verify surfaces a genuine
> render defect on `/data` (a skeleton that never hydrates for a reason OTHER than endpoint latency),
> fix it minimally; otherwise the frontend diff stays empty.

## Visual Requirements
- Component patterns: no new components. Re-use the existing `/data` panels — the membership-timeline
  step-function chart and the colored per-date universe-resolution diagnostic cards (admitted +
  excluded-by-reason). No redesign.
- Layout: existing `/data` Data Manager page layout, unchanged.
- Key visual effects: none new; match the established `/data` styling.
- States to handle: the verification must capture the HYDRATED state (not a mid-warm-up skeleton).
  WAIT for `readiness:"ready"` before driving the page. A 404 dead-shell (missing `main-app.js`,
  "Checking backend…") = a `.next` clobbered by a prod build → record SKIPPED, not FAIL. An
  un-hydrated skeleton frame is rejected as evidence, never accepted (iter-18/33 precedent).

## Key Test Scenarios
- `test_bar_cache.py::test_kdate_backfill_loads_each_symbol_at_most_once` PASSES with the assertion
  unchanged (max load count per symbol == 1).
- A candidate-pool symbol with ZERO bars resolves to 0 trailing bars from the prefilled cache with at
  most one load (new fast unit test).
- `membership_timeline` payload + `score_stocks(D)` output are byte-identical before/after the fix
  (asserted): excluded-by-reason counts, admitted set, universe_count unchanged.
- If the coverage optimization lands: served coverage block byte-identical to the pre-optimization
  `compute_coverage`; warm read does not recompute; new table registered in `test_db.py`.
- Error cases: empty DB → empty-but-valid timeline + coverage (no fabricated dates/members); a zero-bar
  candidate-pool symbol is `below_history` (count 0), never fabricated as present; `GET /api/data` under
  a SECOND concurrent reader does NOT return `db_ok:false` / a skeleton (pool not exhausted).
- LIVE browser-QA (single sequential `/data` load, ~30 s wait, md5-distinct non-skeleton evidence,
  NEVER concurrent `/api/data` probing):
  - **J-94** — per-date universe-resolution diagnostic renders (admitted count + excluded-by-reason:
    below-history / below-price / below-ADV at the resolved as-of).
  - **J-96** — membership-timeline rising step function from ~2021-10-18, populated Entries/Exits,
    all three honesty labels (survivorship / warm-up / universe-relative) scrolled into view and the
    pixels viewed.
  - Re-smoke: J-93 (`/stocks` still slides 0/495/504/544 — fast path), J-06 (NVDA `/stocks` ==
    Stock-Detail; J-94 diagnostic count reconciles with served `/stocks` membership), J-07 (Risk-Off →
    0 Actionable), J-18 (0 `input[type=date]`), J-87/J-88 (Dashboard market phase / P(bear) unchanged),
    J-36/J-37/J-39/J-85 (co-located `/data`), J-15 (fast snapshot reads).
- Full backend pytest suite flushes `0 failed, EXIT 0` — handed to the pump nohup-async; gate
  GOAL_ACHIEVED candidacy on the FLUSHED line, NEVER on the in-flight suite. `test_warmup.py` /
  `test_data_manager_jobs_pipeline.py` `F` = known concurrent-QA / slow-boot contention flake — re-run
  ISOLATED before attributing a regression.

## Scope Guards (out of scope — do NOT do)
- Do NOT re-trigger the J-85 `kind:"rebuild"` job — ~11 h, destructive (clears ~1370 snapshots), and
  the data is already correct. This is a read-path fix, not a data regeneration (iter-34/35 lesson).
- No resolver-math change, no scoring-formula change, no membership change — only the cache sourcing
  and (optionally) the coverage delivery.
- No new snapshot column, no in-place snapshot update (Snapshots are immutable, anti-goal).
- No second `dataset_version` stamp, no second coverage/timeline computation path, no new public endpoint.
- No `/stocks` work (J-93 fast path unaffected — only re-smoke), no frontend redesign, no new date state.

## Goal Alignment & Coherence Notes
- Fully aligned with `docs/goal.md` anti-goals: byte-identity preserves Single-source-of-truth and
  No-recompute-in-the-read-path; the fix touches only HOW the trailing-bar count is sourced (cache vs
  per-date re-load), never WHAT is computed/served. No lookahead, no fabricated data, snapshots
  immutable, no magic numbers (thresholds stay config-sourced), Risk-Off gate and the single date
  selector untouched.
- No new surfaces — both target journeys live on the EXISTING `/data` coverage home (blueprint IA
  line 293) and the EXISTING `data_manager:compute_coverage` → `GET /api/data` rows (Data Contract
  lines 336-337). No nav-skeleton change, no re-approval required.
- No scope creep detected. The spec offers the developer an explicit choice among three correct
  fix approaches — pick the smallest that restores load-once with byte-identical served values.
