# Phase goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-26 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-26
**Date:** 2026-06-17
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | Unfinished-imports panel / resumable job row | Changed behavior | Backend now classifies a whole-batch Yahoo auth/rate-limit failure as a resumable pause instead of completing silently with 0 members | Trigger an Expand-universe job that hits a systemic Yahoo auth rejection; verify the Unfinished-imports panel shows the paused job with a Resume button and a non-empty honest message (NOT "0 passers, 548 omitted" or a blank completion) |
| `/data` | Job card — job status message | Changed behavior | Backend now plumbs the verbatim auth-failure reason to the job `message` field, which the job card renders | On a paused Expand-universe job, open the job card and confirm the displayed message reads something like "market-cap provider auth failed" (not a silent success) and does NOT contain the Yahoo crumb token or a raw URL with query parameters |
| `/data` | Unfinished-imports panel — Resume affordance | Changed behavior | A systemic auth failure now surfaces as a resumable state (previously the job completed, so Resume was never offered for this failure mode) | After an auth-paused Expand job appears in Unfinished-imports, click **Resume**; verify the job re-starts the screen step without re-fetching OHLCV bars (progress counter should advance from the screen step, not restart from fetch) |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/data_providers/base.py` — added optional `get_market_caps(symbols)` batch method with default returning `None`; no served field added, no API response shape changed.
- `apps/backend/app/data_providers/yahoo_provider.py` — cookie+crumb acquisition, batched `/v7/finance/quote` with `QUOTE_BATCH = 40`, single-symbol `get_market_cap` delegating to batch, systemic 401/429 → `RateLimitError` with redacted URLs; no new endpoint or response field.
- `apps/backend/app/engine/data_manager.py` — `_run_expand_screen` batched cap pre-fetch + systemic-pause classification + resume-at-screen live/pool binding fix; no new endpoint, table, column, or served field.
- `apps/backend/tests/test_provider_clients.py` — extended offline tests for cookie→crumb→quote flow; test-only, no UI impact.
- `apps/backend/tests/test_data_manager.py` — J-84 expand integration tests (offline); test-only, no UI impact.
- `apps/backend/data/seed/meta.json` — rebuilt to correct price-seed manifest (159 symbols, accurate first/last/bars); restores the J-39 seed-window protection internally; no visible UI field changed.
- `apps/backend/data/seed/universe.json` — removed (was a corrupt 0-member bug residue); restores the honest "screen not built yet" state; the `/data` Stocks universe section reflects absence of a built universe (same as before the corruption).

---

## Summary

- **Frontend surfaces changed:** 0 (no frontend code was modified)
- **New pages/routes:** 0
- **Modified components:** 0
- **Navigation changes:** no
- **Backend-only changes:** 7
- **Behavior changes visible via existing UI surfaces:** 3 (all on `/data` — the job card message, the Unfinished-imports resumable row, and the Resume affordance availability for the Yahoo-auth-failure case)
