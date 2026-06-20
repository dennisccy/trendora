# goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39 Dev Handoff

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-39
**Date:** 2026-06-20
**Agent:** developer
**Status:** complete

## What Was Built

Backend-only cache-correctness fix for J-97 (the Dashboard two-pane cross-view bottom pane that
rendered EMPTY at the live current as-of). No new feature, no new value, no new endpoint — a surgical
cache-key fix so the already-registered `timeline_full` series is served on a cache HIT, not only on a
fresh-compute MISS.

- **Payload-schema version token in the `MarketPhaseCache` key.** Added a module-level
  `SCHEMA_VERSION = "s1"` constant and a `_cache_version(session)` helper in
  `apps/backend/app/engine/market_phase.py`. `_cache_version` returns `f"{_dataset_version(session)}|{SCHEMA_VERSION}"`
  — the existing J-72 data stamp PLUS the new payload-schema token, folded into the existing
  `dataset_version` STRING composite that is stored in the cache row. **No new DB column** (the
  spec-preferred, lower-risk route — avoids the `db.py` `_ADDITIVE_COLUMNS` + `test_db.py` guard
  registration on the live persistent DB).
- **Both cache paths now key on `_cache_version`.** `market_phase_cached` (the causal payload, ~788)
  and `retrospective_cached` (the fenced J-89 retrospective, ~1110) both compose their cache version via
  `_cache_version`. Because every pre-iter-38 row is keyed to the BARE data stamp (`r1370-f3078889`), it
  is now a guaranteed MISS under the composite key and is recomputed ONCE — WITH the additive
  `timeline_full` field — and the stale-schema row is pruned by the existing `dataset_version != version`
  cleanup.
- **Payloads are byte-identical.** Only the cache KEY string changed. The persisted/served payload, the
  `market_phase_default_payload` strip behavior (`?full=false` card), and the fenced retrospective payload
  are untouched. The served `timeline_full` is read VERBATIM from the engine's `_timeline_series` /
  `compute_market_phase` output — no second computation, no client-side math.

The API layer (`apps/backend/app/api/market_phase.py`) is UNCHANGED — it already routes
`?full=true` → `market_phase_full_cached` → `market_phase_cached`, so the endpoint contract is identical;
only the cache key inside the engine changed. Frontend is UNCHANGED (the J-97 chart + J-98 restructure
already shipped in iter-38; the empty pane was purely the stale-cache payload).

## Files Changed

- `apps/backend/app/engine/market_phase.py` — added `SCHEMA_VERSION` constant + `_cache_version()` helper;
  `market_phase_cached` and `retrospective_cached` now key the `MarketPhaseCache` row on `_cache_version`
  (data stamp `|` schema token) instead of the bare `_dataset_version`. Payloads unchanged.
- `apps/backend/tests/test_market_phase.py` — new cache-HIT correctness tests (probe an ALREADY-POPULATED
  OLD-schema row, not a fresh compute); updated `test_cache_refreshes_on_dataset_version_change` to query
  the stored COMPOSITE `_cache_version` (the stored `dataset_version` column now holds the composite). See
  "Tests Run".

## Tests Run

Command: `cd apps/backend && .venv/bin/python -m pytest tests/test_market_phase.py -k "cache or full or schema or retrospective or byte_identical" -q`

New / updated tests:
- `test_cache_hit_on_old_schema_row_now_serves_timeline_full` — THE CRUX. Seeds an OLD-schema cache row
  (bare-stamp key, payload WITHOUT `timeline_full`) as the only row for the as-of, then asserts
  `market_phase_full_cached` MISSES it, recomputes once, serves `timeline_full` byte-identical to a fresh
  `compute_market_phase(...)["timeline_full"]`, and the served row is now keyed to the composite stamp.
- `test_old_schema_row_is_pruned_and_recomputed_under_composite_key` — the stale bare-stamp row is pruned;
  exactly one composite-keyed row remains.
- `test_card_payload_byte_identical_after_schema_fix` — `?full=false` (card) stays byte-identical
  (no `timeline_full`, equals a fresh strip of `compute_market_phase`). J-87/J-88 unchanged.
- `test_retrospective_payload_byte_identical_after_schema_fix` — the fenced retrospective payload is
  byte-identical post-fix (smoothed/true-bear fence unchanged). J-89 unchanged.
- `test_schema_version_token_present_in_composite_key` — the composite key carries both the data stamp
  and the `SCHEMA_VERSION` token (so a future additive field can invalidate stale rows by bumping the token).
- `test_cache_refreshes_on_dataset_version_change` (UPDATED) — now queries `_cache_version` (the composite
  the column stores) rather than the bare `_dataset_version`. Intent unchanged: a data-version change
  prunes the stale row and writes a fresh one.

Result: targeted module run — see status.json `tests_run`. The FULL backend pytest suite (~34 min) is
handed to the pump to run `nohup`-async; gate on the flushed `0 failed, EXIT 0` line (suite-gate lesson —
never block the goal-evaluator on the in-flight stream).

## Known Issues

- **Full suite runtime / contention flakes:** the full backend suite is ~34 min on this machine. Re-run any
  single `test_warmup.py` / `test_data_manager_jobs_pipeline.py` failure in isolation before attributing it
  to this iteration (known slow-boot/contention flakes per MEMORY, not regressions from this diff).
- **Live browser verification is the QA agent's job (this iteration's other half):** the iter-38 evidence
  dir was EMPTY (Chrome MCP CDP timeout). The cache fix here is the necessary precondition; the live J-97
  (bottom pane populated at the live current as-of, two byte-DISTINCT synced-zoom frames, early-as-of
  honest-empty) + J-98 (compact at-a-glance + More-detail expand + as-of updates both figures) evidence is
  captured downstream by browser-qa. Bring up backend `:8835` (WAIT for `/api/health` "ready"), frontend
  `:3835`, Chrome `:9222`; fall back to Playwright if Chrome MCP is unreachable (iter-34 precedent).
  Scroll the below-the-fold bottom pane into the viewport before capture; `md5sum` evidence FIRST and
  REJECT any blank/skeleton/byte-identical frame.
- **One-time recompute on first HIT-miss:** after the fix, the first `market_phase_full_cached` at each
  previously-cached as-of pays a single market-phase compute (a guaranteed MISS) before re-caching under
  the composite key. Bounded (one market-phase compute, not a scan). Does NOT touch `/api/data` (the known
  pool-exhaustion hazard is untouched).

## Fix Notes

N/A — initial build for this iteration. (One in-loop correction during dev: the first targeted run failed
on test isolation — a UNIQUE-key collision on the shared session-scoped `loaded_engine` DB. Fixed by making
the seed helper idempotent and clearing the as-of's rows before seeding the OLD-schema row, so the
cache-HIT tests deterministically MISS the seeded old-schema row regardless of prior test order. No change
to the fix itself; the crux test `test_cache_hit_on_old_schema_row_now_serves_timeline_full` had already
passed.)
