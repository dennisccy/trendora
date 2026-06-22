# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-47
**Date:** 2026-06-22
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/research/event-study` | Per-horizon mean/win-rate/N matrix | Restored behavior | Backend read path no longer OOMs on 3M-row live DB; previously returned HTTP 500 | Load the page, wait for the matrix to populate, confirm at least one horizon row shows a numeric mean_return and a non-zero N value (not a skeleton or "Backend unavailable" message) |
| `/research/event-study` | `N=` chip drill-down link | Restored behavior | Same OOM fix restores count-coherent drill-down | Click an `N=` chip on any populated matrix cell; confirm the `/research/samples` page loads and shows a `total` row-count equal to the N value on the chip |
| `/research` | Factor Lab decile table + rank-IC figure | Restored behavior | Backend read path no longer OOMs; previously returned HTTP 500 on full live dataset | Select a factor (e.g. leadership_score) and a horizon, wait up to 60 seconds for the cold-cache compute, confirm 10 decile rows appear with numeric mean_return values and a rank_ic figure is shown |
| `/research` | Factor Lab `N=` drill-down link | Restored behavior | Same OOM fix restores the drill-down that feeds Factor Lab cohorts | Click an `N=` chip in the Factor Lab result; confirm `/research/samples` loads and its displayed total matches the N on the chip |
| `/research` | Factor-combination composite result | Restored behavior | Backend read path no longer OOMs; previously returned HTTP 500 | Select a factor combination and a horizon; confirm the result card shows a numeric pool_n and at least one composite cohort row |
| `/research/regime-setup-pattern` | Regime x Setup x Pattern ranked table | Restored behavior | Backend read path no longer OOMs; previously returned HTTP 500 | Load the page with a horizon selected; confirm the table contains rows with numeric mean_return and a non-zero n_total — reject a "Loading..." or empty-table state |
| `/research/downtrend-opportunity` | Downtrend Opportunity lab figures | Restored behavior | Backend read path no longer OOMs; previously returned HTTP 500 | Load the page with a horizon selected; confirm at least one row with a numeric mean_return appears in the result table within 30 seconds |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/research.py` — replaced 7 unbounded full-table ORM reads (`select(ForwardReturn).all()`) with column-projected, `yield_per`-streamed, cohort-bounded reads; every served figure byte-identical — no UI surface affected beyond the restored load described above
- `apps/backend/app/engine/forward_testing.py` — replaced the warm-up idempotency-set full-table scan with a streamed key-projected scan (`_streamed_existing_keys`); no change to stored data or any served value — no UI surface affected
- `apps/backend/app/config.py` — added required `read_batch_size: int` field to `ResearchCfg` with boot validation (`>= 1`); this is a memory-safety tuning parameter, not a displayed value — no UI surface affected
- `config.yaml` — added `read_batch_size: 2000` under the `research:` block; pure runtime memory-safety setting — no UI surface affected
- `apps/backend/tests/test_config.py`, `test_config_engine.py`, `test_sectors.py`, `test_themes.py`, `test_indexes.py` — added `read_batch_size` to inline `ResearchCfg` fixtures so they construct under the now-required key — no UI surface affected
- `apps/backend/tests/test_research_streaming.py` (new) — deep-equality and chunk-independence tests of the streamed builders — no UI surface affected
- `apps/backend/tests/test_forward_testing_streaming.py` (new) — idempotency and key-type tests of the streamed warm-up scan — no UI surface affected

---

## Summary

- **Frontend surfaces changed:** 0 (no frontend source files modified)
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 7 files (research.py, forward_testing.py, config.py, config.yaml, 3 test fixture files + 2 new test files)
- **UI surface impact:** 7 existing surfaces restored from HTTP 500 / OOM failure to successfully rendering real figures on the full live dataset — no new surfaces, no layout or value changes
