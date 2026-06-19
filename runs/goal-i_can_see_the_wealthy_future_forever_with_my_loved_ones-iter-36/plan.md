# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-36 Execution Plan

## What to Build
Make `GET /api/data` responsive again on the post-rebuild DB (~1369 sliding snapshot dates) by caching the J-96 membership-timeline derivation — with ZERO change to any served value (byte-identity is a hard DoD). This is a backend read-path performance fix only; no frontend diff, no new endpoint, no new displayed value.

- Add a STANDALONE `create_all`-managed cache table for the serialized `_membership_timeline(...)` payload, keyed by a single `dataset_version` stamp (mirror `EventStudyCache` / `MarketPhaseCache` in `apps/backend/app/models.py:385-472`). Reuse the SAME `app.engine.research._dataset_version(session)` stamp (single-sourced — already changes on any dataset change). Read = compute current stamp → return stored payload on hit; compute-once + upsert on miss; prune rows keyed to older stamps on write. Cached payload MUST be deep-equal to a fresh `_membership_timeline` compute.
- Route `compute_coverage`'s `membership_timeline` field (`data_manager.py:603`) through the cache so a warm cache serves it without the O(dates × pool) `resolve_with_reasons` loop (`:514`).
- Warm the cache during the background warm-up daemon (`apps/backend/app/engine/warmup.py::_run_warmup`, after `backfill_forward_returns`, within/after the existing `bar_cache(session)` usage) so the FIRST `/data` request after boot/rebuild serves the cached payload (J-40/J-41 serve-fast precedent). Warm-up failure stays NON-FATAL (caught + logged), exactly as the existing worker guarantees.
- Bound the cold-miss cost so a request before warm-up completes still never hangs >300 s: either extend the load-once discipline so `resolve_with_reasons` reads each pool symbol's series once across the per-date loop, or serve the already-cheap timeline parts (size/entries/exits from the single `ScannerRun`/`ScannerResult` join at `:492-498`) with `excluded` counts filled from cache when present. The served block's shape and values stay identical to today.
- Source any new tunable (cache-staleness / batch knob) from the config object (the `DataManagerConfig` in `apps/backend/app/config.py`, e.g. `config.data_manager.*`) — never an inline literal. NOTE: the spec says "`config.yaml`" but this project's config lives in `config.py` (Pydantic). Add the field there. (Likely no new tunable is needed; document the assumption if so.)
- Register the new standalone cache table in `apps/backend/tests/test_db.py::test_create_all_produces_expected_tables` — add a new `MEMBERSHIP_TIMELINE_CACHE_TABLES = {"<name>"}` group to the expected-tables union at line 70 (iter-20/21/29 standalone-cache precedent). The `_ADDITIVE_COLUMNS` trap (iter-12) does NOT apply — it is a standalone mutable cache table, like `event_study_cache` / `market_phase_cache`.

## Agents Required
- developer: yes -- implement the membership-timeline cache table + cache read/upsert + warm-up precompute + cold-miss bound; add the byte-identity, timing, cache-invalidation, causality, and `test_db` registration tests; write the dev handoff. Backend-only (`apps/backend/`). No frontend work.

## Frontend Present
no

(Justification for QA: this is a pure backend read-path performance fix. `/data` page components are unchanged — they simply re-hydrate once the endpoint responds. No frontend code diff. HOWEVER, the DoD and TESTING REQUIREMENTS explicitly require LIVE browser re-verification of J-94 + J-96 and a re-smoke of co-located `/data` journeys plus the critical J-18/J-07 and J-93. The `Frontend Present: no` line reflects "no new frontend surface / no new component," but the QA step MUST still run the browser-qa-agent against the restored `/data` page per the spec's TESTING REQUIREMENTS — the user-visible regression being fixed is hydration of an existing page. See "Key Test Scenarios" below; do NOT skip browser QA on the basis of this line.)

## Files to Create/Modify
- `apps/backend/app/models.py` -- add the standalone `MembershipTimelineCache` (`table=True`) model mirroring `EventStudyCache`/`MarketPhaseCache`; key on `(dataset_version)` (+ a UniqueConstraint), `payload_json`, `created_at`.
- `apps/backend/app/engine/data_manager.py` -- add a cache read/upsert wrapper around `_membership_timeline`; call it from `compute_coverage` at the `membership_timeline` field (`:603`); apply the cold-miss bound. NO change to resolver math or to the served block's shape/values.
- `apps/backend/app/engine/warmup.py` -- after `backfill_forward_returns` in `_run_warmup`, precompute + upsert the membership-timeline cache (non-fatal on failure).
- `apps/backend/app/config.py` -- (only if a tunable is genuinely needed) add a typed `data_manager` field for the cache knob; otherwise no change.
- `apps/backend/tests/test_db.py` -- add `MEMBERSHIP_TIMELINE_CACHE_TABLES` group + include in the expected-tables union (line 70).
- `apps/backend/tests/test_data_manager_membership_cache.py` (new) -- byte-identity (cached payload deep-equals fresh `_membership_timeline`), cache-hit timing/responsiveness, cache-invalidation on `_dataset_version` change (stale row not served), causality (each date observed from its own ≤ D snapshot/bars) preserved through the cache, empty-DB → empty-but-valid timeline.
- `apps/backend/tests/test_warmup.py` -- assert the warm-up precomputes the membership-timeline cache (and stays non-fatal on a forced failure). (Extend existing file.)
- `docs/handoffs/goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-36-dev.md` -- dev handoff.

## Key Test Scenarios
- **Timed live `GET /api/data`** on the post-rebuild DB returns within a normal request budget — no >300 s hang (cache warm). Cold miss is bounded (never hangs). (iter-35 regression's own lesson: smoke `/api/data` for RESPONSE TIME, not just DB values.)
- **Byte-identity (hard DoD):** the served `coverage` block — especially `membership_timeline`, `universe_diagnostic`, `universe_count` — is deep-equal to a fresh `_membership_timeline` / `compute_coverage` compute over the same DB (deep-equal, not "looks similar").
- **Cache invalidation:** after `_dataset_version(session)` changes, a stale cache row is NOT served — the read recomputes against the new stamp (mirror the `event_study_cache` / `market_phase_cache` cache-key tests).
- **`test_db.py::test_create_all_produces_expected_tables`** green with the new standalone table in the expected union.
- **Causality preserved through the cache:** each timeline date observed from its own ≤ D snapshot + bars ≤ D (no future leakage) — re-assert the existing `_membership_timeline` causality property holds through the cache.
- **Error cases:** empty DB / no snapshots → empty-but-valid timeline (no fabricated dates/members); invalid/absent `?as_of` on `GET /api/data` still falls back gracefully to the latest stored run date (no 4xx, descriptive metadata).
- **Browser (per spec TESTING REQUIREMENTS — run despite Frontend Present: no):** md5sum the evidence dir FIRST; reject any un-hydrated skeleton frame (iter-18/33). J-94 = per-date coverage diagnostic (admitted + excluded-by-reason counts) renders on `/data` at the resolved as-of. J-96 = the rising membership-timeline step function from ~2021-10-18 with populated Entries/Exits + the three honesty labels, scrolled INTO the viewport with the pixels viewed. Re-smoke J-36/J-37/J-39/J-85 on `/data`. Re-confirm J-93 (`/stocks` still slides `0→544`, fast path, unaffected), and the CRITICAL J-18 (0 `input[type=date]`) and J-07 (Risk-Off → 0 Actionable). Env: backend :8835 + frontend :3835 + Chrome :9222 reachable before scoring; Playwright fallback if Chrome MCP is down (iter-34).
- **Full backend pytest suite** flushes `0 failed, EXIT 0` — handed to the pump nohup-async; the evaluator gates GOAL_ACHIEVED candidacy on the FLUSHED terminal summary line, NEVER blocked on the in-flight suite (iter-11/29/30). Re-run any single `test_warmup.py` / `test_data_manager_jobs_pipeline.py` / `scanner_runs`-touching `F` in isolation before attributing a regression.

## Out of Scope / Scope Flags
- **Do NOT re-trigger the J-85 `kind:"rebuild"` job** (~11 h, destructive — clears ~1369 daily snapshots). The data is already correct post-iter-35; this iteration only fixes delivery speed. (MEMORY: "J-85 rebuild is ~11h and clears the snapshot layer.")
- No change to `universe_resolver` resolution math, `score_stocks`, `forward_testing`, or any canonical scoring formula — the resolver's admitted/excluded results must be identical; only delivery is cached/precomputed.
- No change to the served coverage block's shape or values (byte-identity is a hard DoD). Do NOT add a new top-level `/api/data` key (`membership_timeline` already exists; the iter-32 subset guard `test_get_data_overview_shape` stays green only if no new top-level key is added).
- No new frontend component, no new date control (J-18 critical — exactly one global as-of), no new endpoint, no new Data Contract value, no nav/blueprint change.
- Not addressing J-22/J-23/J-24 (data-walled per goal.md, non-vetoing) — out of scope.

## Goal Alignment Note
This iteration directly serves the stated GOAL: the `/data` page hydrates again within a normal page load so J-94 + J-96 render with their honesty labels, and every served value stays byte-identical. It closes open_item `iter35-api-data-timeline-uncached` and resolves the iter-35 REGRESSION (correct data growth exposed a latent O(dates × pool) read-path cost). The plan reuses the established J-72/J-87 cache precedent rather than inventing a new abstraction, holds every critical anti-goal (no recompute in the read path beyond a permitted cache of a deterministic read-only derivation; single source of truth; snapshots immutable; no fabrication; honesty labels intact; Risk-Off gate untouched; single date selector). No drift from the project goal detected.
```
