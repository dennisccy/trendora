# Iteration 38 — Coherence Audit

**Iteration:** goal-mcp-loop-iter-38
**Date:** 2026-07-15
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Watchlist concentration X-ray (correlation matrix, clusters, ENB, sector/theme/setup concentration) | OK | Computed once: `apps/backend/app/engine/watchlist_xray.py:167` (`build_xray_payload`), which imports the ONE canonical helper `apps/backend/app/engine/concentration.py:51` (`correlation_matrix`) and `:60` (`effective_number_of_bets`). Served: additive `xray` field on the existing `GET /api/watchlist`, `apps/backend/app/api/watchlist.py:114`. Single reader: `apps/frontend/app/watchlist/page.tsx:326` (`WatchlistXraySection`) + `apps/frontend/components/correlation-heatmap.tsx:42`, both fed from the one `state.data.xray` populated by the single `fetchWatchlist()` call at `page.tsx:78-84` — no second fetch, no browser-side recompute. |
| ENB / pairwise-correlation math (codebase-wide duplicate check) | OK | `grep -rn "def effective_number_of_bets\|def correlation_matrix\|eigvalsh"` across `apps/backend` returns hits ONLY in `concentration.py:51,60,74` — no second implementation anywhere, including no reuse conflict with the pre-existing, unrelated single-pair Pearson helper in `apps/backend/app/engine/research.py:130` (a different statistic — factor-vs-forward-return Rank-IC, not a multi-asset portfolio correlation matrix; pre-existed this iteration, untouched by the diff). |
| Sector / theme / setup-status concentration (reuse of existing canonical sources) | OK | `_sector_concentration`/`_theme_concentration`/`_setup_concentration` in `watchlist_xray.py:95-145` read the SAME canonical rows `GET /api/stocks` serves via `filtered_stock_rows` (`apps/backend/app/engine/snapshot_serving.py:214`, confirmed the only definition) and reuse `summarize_candidates` (`apps/backend/app/engine/setups.py`, the dashboard's own tally) rather than a second setup count. Price history reads the existing bounded `bars_asof_window` (`apps/backend/app/engine/prices.py:419`, the same accessor `scoring.py`/`regime.py` use) — no whole-table load, no parallel price reader. |
| Null-sector → "Unassigned" bucketing (iter-18/19 nullable-field lesson) | OK | Backend groups the raw `sector` value (including `None`) without inventing its own label (`watchlist_xray.py:20-24`, explicit in the module docstring); display mapping is deferred to the SAME existing frontend helper `apps/frontend/lib/sector-label.ts:17` (`sectorLabel`), invoked at `page.tsx` in the new `ConcentrationBars` sector entries — confirmed via grep this is the only `"Unassigned"` mapping definition in the frontend. No second null-handling rule introduced. |
| Setup-status color mapping | OK | Reuses the pre-existing page-local `setupVariant()` (`apps/frontend/app/watchlist/page.tsx:47`, unmodified by this diff) — no new color scale. |
| Any new value outside the Data Contract | N/A | None found — the X-ray payload is exactly the one value pre-registered in `blueprint.md`'s Data Contract table (the J-23/B-204 row), and nothing else new is displayed. |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/watchlist` Concentration X-ray section | OK | `apps/frontend/components/sidebar.tsx:42` still carries the single, unmodified `/watchlist` nav entry (confirmed `git diff <snapshot> --stat -- sidebar.tsx app/layout.tsx` returns no changes — neither file touched by this iteration). The X-ray is appended inside the SAME `WatchlistPage` component (`page.tsx:236`, `<WatchlistXraySection .../>` directly under the existing entries table), wrapped in the identical `Card` primitive already used on the page — no parallel shell, no new route (`git diff --stat -- 'apps/frontend/app/*'` shows only `watchlist/page.tsx` modified, 0 new page files). Reachable in 1 click from the persistent nav (same as before), and the blueprint's IA table (current `blueprint.md`, J-23 row) already names this exact home: "`/watchlist` (an additive concentration X-ray section on the EXISTING page) ... Watchlist (existing top-level nav; additive section, no new page/route)" — matches what was built verbatim. No duplicate home: no other page in the app shows watchlist-level pairwise correlation/ENB/concentration. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None of substance. Two candidate nitpicks were checked and dismissed as non-issues: (1) sector-null bucketing is split across backend (raw grouping) and frontend (`sectorLabel()` display mapping) — this is the deliberate, explicitly documented single-mapping-point pattern already established in iter-19, not new drift; (2) the X-ray config defaults are stated in both `config.py` (Pydantic `Field` defaults) and `config.yaml` (explicit restatement) — this is the codebase's standing convention for every other `*Cfg` block (mirrors `ChartBarsCfg`/`ServerOpsCfg`), not something introduced or done inconsistently by this iteration.
- The blueprint's Data Contract and IA rows for J-23/B-204 were already present in the current `blueprint.md` (state file, outside this diff's tracked scope under `runs/`) and match the shipped code exactly — no drift between contract and implementation to flag.
