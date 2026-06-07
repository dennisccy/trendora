# Phase goal-i_can_see_the_wealthy_future_forever-iter-23 — UI Surface Map

**Phase:** goal-i_can_see_the_wealthy_future_forever-iter-23
**Date:** 2026-06-07
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|------------|-------------|
| `/data` | `JobForm` — job-kind `<Select>` | New option added | J-35: Expand-universe job kind introduced | Open the job-kind dropdown; confirm a fourth option "Expand universe" is present and selectable alongside the existing three options. |
| `/data` | `JobForm` — Import source `<Select>` | Changed behavior | Source picker must now also appear when job kind is "expand" | Select "Expand universe" from the job-kind dropdown; confirm the Import source picker becomes visible (previously hidden for non-fetch kinds). |
| `/data` | `JobForm` — Import source `<option>` items | Changed behavior | Ineligible sources (alpha_vantage, stooq) must be disabled when expand is selected | Select "Expand universe", then open the source dropdown; confirm Alpha Vantage and Stooq options are disabled and show "cannot supply market cap — not selectable for expand" in their label text. |
| `/data` | `JobForm` — ineligible-reason alert (`data-testid="expand-ineligible-reason"`) | New component | User must see a plain-language explanation when they select an ineligible source for expand | With "Expand universe" selected, choose Alpha Vantage from the source picker; confirm an amber alert block appears below the source picker reading "Alpha Vantage cannot supply market cap — not selectable for an expand job." |
| `/data` | `JobForm` — Start button | Changed behavior | Start must be blocked when an ineligible source is selected with expand | With "Expand universe" selected and Alpha Vantage chosen as the source, confirm the Start button is disabled (cursor-not-allowed state, opacity-50). |
| `/data` | `JobForm` — panel title hint text | Changed behavior | Hint copy now mentions "expand" as a job type that requires a source | Inspect the subtitle under "Start a fetch / backfill / expand job"; confirm it reads "…and — for a fetch or expand — an import source…". |
| `/data` | `JobProgressPanel` — `ExpandScreenResult` block (`data-testid="expand-screen-result"`) | New component | J-35: expand job outcome (passers + omitted-with-reason) must appear on the job card | After an expand job completes (or via injected provider in test), confirm the "Universe screen" section appears on the job card with a green passers badge and an amber omitted badge. |
| `/data` | `ExpandScreenResult` — passers badge (`data-testid="expand-passers"`) | New component | User must see how many candidates passed the screen | On a completed expand job card, confirm the green badge reads "{N} passed" where N matches the actual passer count. |
| `/data` | `ExpandScreenResult` — omitted badge (`data-testid="expand-omitted-count"`) | New component | User must see the total omitted count distinct from the passers | On a completed expand job card, confirm the amber badge reads "{M} omitted" and that passers + omitted equals the total candidate count shown ("of N candidates"). |
| `/data` | `ExpandScreenResult` — omitted list (`data-testid="expand-omitted-list"`) | New component | User must see each omitted candidate with its reason | On a completed expand job card with omissions, confirm the scrollable omitted list shows each symbol and a reason string; confirm the list is scrollable when it exceeds its max-height (scroll the container). |
| `/data` | `ExpandScreenResult` — empty omissions state | New component | User must see a confirmation message when all candidates pass | Drive an expand with an injected provider that passes all candidates; confirm the message "All screened candidates passed — no omissions." appears instead of the omitted list. |
| `/data` | `CoveragePanel` — Universe count (`data-testid="universe-count"`) | Changed behavior | After a completed expand, universe count must reflect the grown universe from universe.json | After a successful expand that produces passing members (requires a reachable feed or injected provider), reload the page and confirm `data-testid="universe-count"` shows a value larger than the pre-expand count. |
| `/data` | `RunHistoryPanel` — run-history table | Changed behavior | Expand runs must appear in history with their kind and screen outcome | After an expand job finishes, scroll to the run history table; confirm a row appears with the "expand" kind badge and the Summary column contains a message describing passers and omitted counts. |
| `/data` | `JobProgressPanel` — chunk progress badge (`data-testid="chunk-progress"`) | Unchanged (reused) | Expand reuses the J-34 chunked-fetch progress display | During a running expand, confirm the "chunk X/N" badge appears alongside the symbols-fetched progress bar, just as it does for a chunked fetch job. |
| `/data` | `JobProgressPanel` — resumable state block (`data-testid="resumable-state"`) | Unchanged (reused) | Expand must land in the amber resumable state on a rate limit | Trigger an expand over a provider that returns a rate-limit error; confirm the amber "rate-limited — resumable" block appears with a Resume button, identical to the J-34 resumable state for a fetch job. |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/app/engine/data_manager.py` — expand job orchestration (`_run_expand_screen`, `_screen_one_candidate`, `_write_expand_artifacts`, `_write_universe_csv`) and `JobProgress.passers`/`omitted_total`/`omitted` fields — UI consumes all of these via `GET /api/data/jobs/{id}`, so they are NOT backend-only; all impact is visible.
- `apps/backend/app/engine/universe_screen.py` — new module consolidating the single `screen_reasons` definition; this is an internal code-organization change with no user-visible difference (the screen predicate outcome is the same, only its source location changed).
- `apps/backend/scripts/screen_universe.py` — now re-exports `screen_reasons` from the new module instead of defining it; no user-visible change.
- `apps/backend/app/data_providers/base.py` — `PriceProvider.get_market_cap` abstract hook — backend abstraction, not directly exposed in UI.
- `apps/backend/app/data_providers/yahoo_provider.py`, `tiingo_provider.py`, `finnhub_provider.py` — real `get_market_cap` implementations — no direct UI surface; they supply data to the expand job backend logic.
- `apps/backend/app/config.py` — `_merge_committed_universe` (wires `universe.json` into `config.universe.symbols` on load); optional `UniverseFilters.adv_window_days` — no UI element; the effect is visible indirectly via the Coverage `universe-count` after a successful expand.
- `apps/backend/tests/test_db.py`, `test_data_manager.py`, `test_api_data.py`, `test_provider_clients.py` — test files, no UI impact.

---

## Summary

- **Frontend surfaces changed:** 1 page (`/data`) — all changes are additive within the existing page
- **New pages/routes:** 0
- **Modified components:** `JobForm` (new option, new eligibility gating), `JobProgressPanel` (new `ExpandScreenResult` sub-component), `RunHistoryPanel` (now surfaces expand run rows), `CoveragePanel` (now sources universe count from the grown universe post-expand)
- **Navigation changes:** no
- **Backend-only changes:** 6 (universe_screen module re-home, provider capability hooks, config merge, test files)
