# Phase goal-mcp-loop-iter-18 — UI Surface Map

**Phase:** goal-mcp-loop-iter-18
**Date:** 2026-07-06
**Written by:** ui-impact-analyst

---

## Affected UI Surfaces

| Route / Page | Component / Element | Change Type | Why Changed | What to Test |
|-------------|--------------------|-----------:|-------------|-------------|
| `/stocks/{ticker}` | `ChartRangeControl` — new "Recent / Full history" segmented toggle in the chart header (`stocks/[ticker]/page.tsx`) | New component | J-10: the 30-year basis must not ship every bar by default; needs an explicit bounded-default + full-history opt-in | Navigate to `/stocks/AAPL`; confirm a "Recent"/"Full history" toggle sits next to the existing Regime toggle in the chart header; click "Full history" and confirm the chart shows a brief loading skeleton (no stale chart left on screen) then renders a deeper span; click "Recent" and confirm it returns to the bounded window |
| `/stocks/{ticker}` | Chart header depth caption (`data-testid="chart-window-caption"`) | Changed behavior | J-10 honest depth disclosure — the caption now discloses the real first-available date and downsampling | On `/stocks/AAPL`, read the caption; confirm it reads "... history since 1996-01-02"; switch to "Full history" and confirm the caption appends "· older bars weekly-sampled"; repeat on `/stocks/NVDA` and confirm "history since 1999-01-22" |
| `/stocks/{ticker}` | Chart header caption for a post-IPO ticker | Changed behavior | J-10 honest short-history disclosure for recently-listed names | Navigate to `/stocks/ARM` (or `/stocks/COIN`, `/stocks/HOOD`); confirm the caption's "history since" date matches the real IPO date (ARM 2023-09-14 / COIN 2021-04-14 / HOOD 2021-07-29) and the chart shows only that short span even with "Full history" selected |
| `/stocks/{ticker}` | Leadership / Entry Quality / Risk `ScoreCard` evidence chips | Changed behavior (content only — component untouched) | J-11 sanctioned ledger reset — zero of the 7 canonical claims re-certified | Open any stock detail page; confirm all three ScoreCards show a "Not yet proven" chip (none show "Proven") |
| `/stocks/{ticker}` | Sector text on the detail header | Changed behavior (new empty-value case) | Broadened candidate pool includes names with no sector mapping (confirmed: 422/541 rows had `sector=None` in the backend's own re-verification) | Open the detail page for a broadened-pool ticker outside the legacy ~122 that has no sector assigned; confirm the Sector text renders blank/absent rather than a fabricated sector, and the rest of the page (scores, chart) still renders normally |
| `/stocks` (leaderboard) | Row count / candidate pool size | Changed behavior (content only — page untouched) | J-12 broadened point-in-time universe (`resolve_members` now screens the ~548-name pool instead of the static ~122) | Load `/stocks`; confirm the row count is far larger than the legacy ~122 (should approach the ~548-name pool, filtered by point-in-time membership at the current as-of); spot-check that at least one name outside the legacy ~122 set appears in the list |
| `/stocks` | Leadership / Entry Quality / Risk evidence chips on every row | Changed behavior (content only) | J-11 sanctioned ledger reset | Load `/stocks`; confirm every row's three score chips read "Not yet proven" |
| `/stocks` | "Sector" column header (sort) + "Filter by sector" dropdown | Changed behavior (new empty-value case) | Broadened pool introduces rows with `sector: null` for the first time | On `/stocks`, click the "Sector" column header to sort by sector, then open the "Filter by sector" select; confirm no runtime error occurs and any row with no sector shows an honest blank cell rather than crashing the page or displaying the literal text "null" |
| `/data` | Universe Diagnostic panel — reason-card grid (`UniverseDiagnosticPanel`) | Updated layout | J-12 staleness gate adds a 5th exclusion reason | Load `/data`; confirm the reason-card grid shows 5 cards (previously 4), including a new "Stale series" card, and that its definition text names the 10-day (`max_staleness_days`) threshold |
| `/data` | Universe Diagnostic panel — hint text under the panel title | Changed behavior (copy) | J-12 | On `/data`, read the Universe Diagnostic panel's hint sentence (below the title); confirm it now mentions "a FRESH series (last bar within N calendar days...)" alongside the existing history/price/liquidity criteria |
| `/data` | Coverage panel — "Admitted" metric definition (`DefinedMetric`) | Changed behavior (copy) | J-12 | On `/data`, open/hover the "Admitted" metric's info definition in the top Coverage summary; confirm the text now includes "a fresh series (last bar within N days)" |
| `/data` | Membership Timeline table — rightmost column header + cell (`MembershipTimelinePanel`) | Changed behavior | J-12 | On `/data`, scroll to the Membership Timeline table; confirm the rightmost column header reads "Excl. hist / stale / price / liq" (was "Excl. hist / price / liq") and each row shows four slash-separated numbers instead of three |
| `/methodology` | Universe Selection card — per-date rule paragraph | Changed behavior (copy) | J-12 | Load `/methodology`; find the Universe Selection card; confirm its per-date-rule paragraph now mentions data recency / a stale-series exclusion and cites the 10-day threshold |
| `/backtest` | Survivorship-bias caveat banner | Changed behavior (copy, content only — page untouched) | Depth actually used (30-year `walk_forward.history_years`); `SURVIVORSHIP_BIAS_LABEL` text rewritten | Load `/backtest`; read the survivorship disclosure banner; confirm it now mentions "up to ~30 years of history (1996 to present)" |
| `/research/*` lab pages (factor lab, combination lab, regime lab, phase-severity lab, samples, severity-velocity) | `CaveatBanner` / `ResearchCaveat` survivorship text | Changed behavior (copy, content only — pages untouched) | Same `SURVIVORSHIP_BIAS_LABEL` change, shared across every lab route | Open any Research lab page (e.g. `/research/samples`); confirm the caveat banner text matches the updated 30-year wording; confirm any cohort badges on that page now read "Not yet proven" rather than "Proven" (J-11) |
| `/evidence` | Claim rows (`ClaimRow`) | Changed behavior (content only — component untouched) | J-11 sanctioned ledger reset | Load `/evidence`; count exactly 7 rows; confirm every row's register date reads 2026-07-03 and every verdict shows an honest FAIL / "Not yet proven" state (zero "Proven" text anywhere on the page); spot-check row 1's p-value (0.5352) and holdout edge (-0.03%) against `runs/goal-session-mcp-loop/state/certified-claims.jsonl` line 1 |
| `/watchlist` | Add-ticker free-text field | Changed behavior | Ticker validation broadened, shared with the chart endpoint's `resolve_servable_symbol` | On `/watchlist`, type a broadened-pool ticker that is NOT among the legacy ~122 names (and has real stored bars) into the ticker field and submit; confirm it is accepted and appears in the list (no "unknown ticker" error); then submit a genuinely invalid ticker (e.g. "ZZZZZ") and confirm the honest not-found error still appears |

---

## Backend-Only Changes (No UI Impact)

- `apps/backend/data/seed/prices/` — the 590-file atomic 30-year seed swap (filesystem move, not a code change) — the raw fuel behind the chart/backtest depth above, but not itself a UI element
- `apps/backend/data/seed/meta.json` — regenerated provenance/vendor metadata; per-series vendor labels stay explicitly UNDISPLAYED this iteration (deferred to J-14)
- `apps/backend/data/seed-stooq-30y/` (591 files removed) — retired staging tree — no UI impact
- `apps/backend/app/seed_loader.py` — `price_load_symbols` (pool ∪ context loader used at boot and by `resolve_servable_symbol`) — no UI surface of its own; its effect is visible only through the already-listed `/stocks`, `/stocks/{ticker}`, and `/watchlist` rows above
- `apps/backend/app/engine/universe_resolver.py` — the staleness-gate engine (`resolve_candidate`, `REASON_STALE`, 4-gate order) — no UI surface of its own; its output is what the `/data` and `/methodology` rows above display
- `apps/backend/app/engine/data_manager.py` — `_cadence_allowed_dates` (bounded snapshot-backfill cadence filter) — governs which historical trading days get a scanner snapshot; no dedicated UI control or indicator of the cadence policy itself
- `apps/backend/app/config.py`, `config.yaml` — new config schema/values (`universe.filters.max_staleness_days`, `SnapshotCadenceCfg`, `ChartBarsCfg`, `walk_forward.history_years: 30`, `scanner.bootstrap_dates`) — pure configuration; consumed entirely through the surfaces already listed above
- `runs/goal-session-mcp-loop/state/certified-claims.jsonl`, `staging-ledger.jsonl` — regenerated ledger DATA (not code) — this is what flips every evidence badge; effect already captured in the `/evidence`, `/stocks`, `/stocks/{ticker}`, and Research-lab rows above
- `apps/backend/scripts/regenerate_ledgers.py`, `apps/backend/scripts/finish_iter18_fullsuite.sh`, `apps/backend/scripts/verify_iter18_fixes.sh` — one-off operational/test-runner scripts — no UI surface
- `apps/backend/tests/*.py` (all modified suites plus new `test_bars_windowing.py`, `test_seed_loader_pool.py`) — test-only — no UI surface
- `apps/frontend/lib/evidence.test.ts`, `apps/frontend/lib/factor-lab-evidence.test.ts` — docstring/comment-only changes relabeling fixture values as synthetic post-reset mirrors; zero behavioral edit — no UI surface
- `apps/frontend/lib/membership-timeline-view.test.ts` — test fixture gains a `stale_series` key — test-only, no UI surface
- `docs/handoffs/goal-mcp-loop-iter-18-dev.md`, `docs/handoffs/goal-mcp-loop-iter-18-frontend.md`, `docs/phases/goal-mcp-loop-iter-18.md`, `docs/improvement-backlog.md`, `reports/**`, `runs/**` — documentation and pipeline/governance artifacts — no UI surface

---

## Summary

- **Frontend surfaces changed:** 8 routes — 2 with modified frontend code (`/stocks/{ticker}` chart header, `/data` diagnostics/timeline); 6 content-only via already-consumed endpoints (`/stocks` leaderboard, `/methodology`, `/backtest`, `/research/*` labs, `/evidence`, `/watchlist`)
- **New pages/routes:** 0 (no new pages this iteration — confirmed by plan.md's "No new pages")
- **Modified components:** 4 — `ChartRangeControl` (new) + chart header caption in `stocks/[ticker]/page.tsx`; `UniverseDiagnosticPanel` + `MembershipTimelinePanel`/`CoveragePanel` copy in `data/page.tsx`
- **Navigation changes:** no
- **Backend-only changes:** 11 — seed price data move, `meta.json`, retired staging tree, `seed_loader.py`, `universe_resolver.py` engine, `data_manager.py` cadence filter, `config.py`/`config.yaml` schema, regenerated ledger JSONL data files, 3 ops scripts, ~30 backend test files, frontend test-fixture files, and process/documentation artifacts
