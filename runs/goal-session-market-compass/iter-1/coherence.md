# Iteration 1 — Coherence Audit

**Iteration:** goal-market-compass-iter-1
**Date:** 2026-08-20
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Stock sector label (`ScannerResult.sector`) | OK | Extended in place inside the SAME registered module `scoring.score_stocks` — `apps/backend/app/engine/scoring.py:456` now reads `cfg.stock_sectors.get(ticker) or pool_sectors.get(ticker)` (curated map still wins). The pool fallback (`pool_sector_map` / `resolve_pool_sector`) is defined once in `apps/backend/app/engine/universe_screen.py:110-145` and called only from `scoring.py:119` — no second, independent computation site. Still served exclusively by the two registered endpoints `GET /api/stocks`, `GET /api/stocks/{ticker}` (`apps/backend/app/api/stocks.py:58,63`, untouched this iteration). This is precisely the extension the blueprint's Data Contract row pre-anticipated ("J-01 [TARGET] adds a pool-CSV fallback via `universe.pool_sector_aliases`"). `/stocks/page.tsx` and `/stocks/[ticker]/page.tsx` have zero diff (confirmed via `git status` and the ui-surface-map) — no new UI surface fetches this value from anywhere else. `ScannerResult` rows already stored before this iteration are proved unchanged by `test_historical_row_sector_not_rewritten_by_pool_fallback` (TC-8). |
| Sector-basis disclosure prose (new, `methodology.universe_selection.sector_basis`) | OK (not a duplicate; not independently tracked, and rightly so) | Single producer `_sector_basis()` in `apps/backend/app/engine/methodology.py:79-91`, reading one config field (`config.methodology.universe_selection.sector_basis`, `apps/backend/app/config.py:1807`) — the same config-prose pattern already used for `membership_rule` (which likewise has no dedicated Data Contract row). Single endpoint `GET /api/methodology` (`apps/backend/app/api/methodology.py`). Single frontend consumer `SectorBasisCard` (`apps/frontend/app/methodology/page.tsx:303-315`), single type (`apps/frontend/lib/api.ts:1342`). Grep confirms no second producer/consumer anywhere in `apps/`. This prose documents the already-registered "Stock sector label" row rather than introducing a second tracked value — not a duplicate-of-existing-concept, and not the kind of divergence-risk value the Data Contract exists to pin down. |
| `Stock.sector_id` / `stock_sector_etf` / `rs_sector` (scoring inputs, unchanged) | OK | Diff shows no edit to that block in `scoring.py` (lines ~124-131, immediately after the new fallback-map insertion, are untouched). `TC-4` (`test_pool_sector_fallback_never_changes_any_score_bucket_or_setup`, `apps/backend/tests/test_scoring.py:349-376`) is a byte-identity regression proof over leadership/entry_quality/risk/bucket/setup_status with the fallback monkeypatched off vs. on. |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/methodology` — new "Stock sector labels" disclosure card (`SectorBasisCard`) | OK | No new route; renders inside the existing `/methodology` page (`apps/frontend/app/methodology/page.tsx:64-66`), which is already a top-level, persistent sidebar entry — `apps/frontend/components/sidebar.tsx:43` (`{ href: "/methodology", label: "Methodology", ... }`), 1 click from anywhere. Matches the blueprint's own J-01 row verbatim: canonical home "`/methodology` (two-source disclosure)" under the Methodology nav section. Reuses the page's existing `Card`/`Badge` components (no parallel shell). Not a duplicate home — this IS the registered home, and it is a new subsection of an existing card family, not a second methodology page. `sidebar.tsx` itself is untouched this iteration (confirmed via `git status` — no navigation changes), consistent with the ui-surface-map's own "Navigation changes: no." |
| `/stocks`, `/stocks/{ticker}` (Sector cell / filter, more often populated) | OK | Zero code diff on both pages (confirmed via `git status`) — same existing canonical home per the blueprint's J-01 row, same rendering helper (`sectorLabel()`), only the underlying stored data becomes more complete. No new surface introduced. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `apps/backend/app/engine/methodology.py:73` — `payload["sector_basis"] = _sector_basis(config)` is syntactically nested inside `if catalog.universe_selection is not None:` (line 67), and the inline comment above it (lines 69-72) asserts it is "a SIBLING top-level section, deliberately NOT nested inside `universe_selection`." That claim is about the *served JSON shape*, not the Python control flow, and it is true only because (a) `catalog.universe_selection` here is a config-presence check (`config.methodology.universe_selection`, always non-None in this repo's committed `config.yaml`) rather than the actual screen-record gate, and (b) the real J-22 gate lives one layer up, in `apps/backend/app/api/methodology.py:40-41`, which pops only the `universe_selection` key and leaves the sibling `sector_basis` key untouched. Traced end-to-end this is correct today, and it is locked in by two regression tests (`test_sector_basis_survives_the_honest_universe_gate` in `test_api_methodology.py:227-237`, `test_sector_basis_is_a_sibling_of_universe_selection_not_nested_in_it` in `test_methodology.py:264-271`). Flagging only because the local comment reads as if the sibling-ness were guaranteed at this line, when it actually depends on the API layer's `pop()` — worth a clarifying comment update if this file is touched again, not a coherence violation and not blocking.
- No unregistered net-new tracked value this iteration: the only new displayed content (`sector_basis` prose) is documentation of the already-registered "Stock sector label" Data Contract row, not a new entity requiring its own row.
