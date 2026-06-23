# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-48 — User-Visible Changes

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-48
**Date:** 2026-06-22
**Written by:** ui-impact-analyst

---

## What Users Can Now Do

- Users can now open the Factor Lab page (`/research/factor-lab`), select a factor and a horizon, and read a real decile table (D1–D10 mean return, risk-adjusted return, and sample count) together with a numeric rank-IC value — the page previously returned an HTTP 500 / "Backend unavailable" error on every request against the live full dataset.
- Users can now select a component-based factor (one whose values come from nested JSON, such as RS 3m) in the Factor Lab and receive real decile figures — the component factor path is now safe against the same memory fault.
- Users can now trust that the `N=` sample-count chips on the Factor Lab results are populated with real observation counts, enabling the existing drill-down flow: clicking an `N=` chip opens `/research/samples` in a new tab and the total matches the published cell N.
- The Factor-Combination lab (`/research/factor-combination`) cold-miss path (cache miss on first request) is now memory-safe, so users visiting it immediately after a backend restart will also receive real figures instead of an error.

---

## What Changed in the Visible UI

- The Factor Lab page (`/research/factor-lab`) now renders with a populated decile table and rank-IC statistic where it previously showed only the "Backend unavailable — No figures are shown rather than fabricated values" error banner on the full live dataset. The page structure, layout, and all labels are unchanged; only the error state is replaced by real content.
- All five heavy research labs (Event Study, Factor Lab, Factor Combination, Regime x Setup x Pattern, Downtrend Opportunity) are now consistently reachable under a single sequential probe session. Previously, Factor Lab alone would HTTP-500 after the iter-46 regression, breaking the "all labs load reliably" expectation.

---

## What Old Behavior Changed

- Factor Lab (`/research/factor-lab`): previously always returned HTTP 500 with a `MemoryError` on the live 3.47 GB database (iter-46 regression). Now returns HTTP 200 with real figures in approximately 50–120 seconds (uncached compute over ~598K observation rows). The loading time is unchanged relative to the pre-iter-46 baseline; the figures are byte-identical to that baseline.
- Factor Combination (`/research/factor-combination`) cold-miss path: previously would have OOM'd on a cache miss (masked in practice by the EventStudyCache hit). Now safe on both a cache hit and a cold miss, so users who encounter a genuine cache miss receive real figures rather than a 500.

---

## Not Visible Yet

- No new backend capabilities were introduced. This iteration is a memory-safety fix: the two backend read paths (`_factor_observations` and `_combination_observations` in `research.py`) are now streamed instead of materializing ~609K ORM rows at once. The fix is invisible to the user beyond the restoration of the previously-failing Factor Lab page.
- The Factor Lab remains intentionally uncached (no server-side cache was added). Users will continue to wait approximately 50–120 seconds for the cold compute on every request — this is a known characteristic, not a regression.
