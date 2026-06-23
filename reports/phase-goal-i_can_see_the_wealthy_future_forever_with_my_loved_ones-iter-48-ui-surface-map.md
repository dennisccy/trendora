# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-48 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-48
**Date:** 2026-06-22
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/research/factor-lab` | Decile table (D1–D10 rows showing mean return, risk-adjusted return, and n) | Changed behavior (error → success) | Backend `_factor_observations` read path now streams ~609K rows instead of materializing them all at once, eliminating the MemoryError that caused HTTP 500 | Navigate to `/research/factor-lab`, select factor "RS 3m" and horizon "20d", wait up to 120 s; verify the decile table renders 10 rows (D1–D10) with non-null mean return and n values, and the rank-IC stat shows a numeric value — not the "Backend unavailable" error banner |
| `/research/factor-lab` | Rank-IC statistic display | Changed behavior (error → success) | Same backend fix restores the full `compute_factor_lab` payload including the rank_ic field | On the same Factor Lab request above, confirm the rank-IC value displayed is numeric (e.g. 0.006 or −0.012) and not blank, "NaN", or hidden by an error overlay |
| `/research/factor-lab` | N= sample-count chips | Changed behavior (now populated) | With the lab now serving HTTP 200, the N= observation counts per decile are present and the drill-down link is reachable | Click the `N=` chip on any decile row; confirm a new tab opens at `/research/samples` and the total count shown in that tab equals the n value displayed in the chip |
| `/research/factor-lab` | Component-factor path (factors reading nested record_json, e.g. RS SPY 3m) | Changed behavior (error → success) | The streamed read preserves the full ORM row including `record_json`, so component factors that extract nested JSON values are byte-identical to the pre-regression baseline | Select a component factor (e.g. "RS SPY 3m") in the Factor Lab dropdown, pick a horizon, wait up to 120 s; verify the decile table is populated with non-null figures and no "Backend unavailable" banner appears |
| `/research/factor-combination` | Combined cohort figures (composite + strict-overlap cohorts) | Changed behavior (cold-miss path hardened) | Backend `_combination_observations` read path is now streamed, eliminating the latent cold-miss OOM | After a backend restart (to clear EventStudyCache), navigate to `/research/factor-combination` and request a combination with at least two factors; confirm the Combined cohort row renders with a non-null mean return and pool_n, and no HTTP 500 or "Backend unavailable" banner appears |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/research.py` — `_factor_observations` (line ~216): replaced `session.exec(select(ScannerResult)…).all()` with `.yield_per(cfg.research.read_batch_size)` streaming over the full ORM row, with `.order_by(ScannerResult.run_id, ScannerResult.id)` to preserve byte-identical row order. No API response shape change; no new config key; no frontend source change.
- `apps/backend/app/engine/research.py` — `_combination_observations` (line ~421): same `yield_per` streaming applied to the factor-combination builder's ScannerResult read. Figures are byte-identical; no API shape change.
- `apps/backend/tests/test_research_streaming.py` — added byte-identity and chunk-independence tests for both ScannerResult-side builders (column factor, component factor, zero-N cohort, as-of/all-history). Test-only file; no UI impact.

---

## Summary

- **Frontend surfaces changed:** 0 (no frontend source files were modified)
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 3 (research.py _factor_observations stream, research.py _combination_observations stream, test_research_streaming.py additions)
- **Behavior-restored surfaces:** 2 (/research/factor-lab restored from HTTP 500 to HTTP 200; /research/factor-combination cold-miss path hardened)
