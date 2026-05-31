**Verdict:** COHERENCE-PASS

# Coherence Audit — goal-i_can_see_the_wealthy_future-iter-8

- **Session:** i_can_see_the_wealthy_future
- **Iteration:** 8 — Snapshot-served reads + global as-of date switcher (J-15, J-13)
- **Snapshot SHA audited:** `74c8cd4d6e4f81c19973c9e36c0d2c63cb6f5632` (+ uncommitted working tree)
- **Auditor:** coherence-auditor

## Summary

This iteration re-points the five live read endpoints (`/api/dashboard`, `/api/stocks`,
`/api/stocks/{ticker}`, `/api/sectors`, `/api/themes`) from the iter-2/3 *on-request compute* model
to **serve canonical values from the persisted immutable snapshot for a resolved as-of date**, and
adds a global top-bar as-of switcher. This is exactly the consolidation the blueprint's iter-5/6
notes always anticipated. It is a low-coherence-risk iteration: it **removes** four live computation
call-sites and routes every value through the one canonical persister (`run_scan`). No objective
Data-Contract or Information-Architecture violation found.

## Part A — Data Contract check (single source / "numbers don't match")

**No violation.** Verified the re-pointed read path introduces no second computation and no
non-canonical serving path for any registered contract value.

- **Serving layer reads stored rows, computes nothing.** The new `apps/backend/app/engine/snapshot_serving.py`
  reshapes a resolved `ScannerRun` + its stored children into the existing payloads by reading
  columns/JSON only:
  - `dashboard_payload` reads `run.regime_score/regime_label`, `regime_components_json`, breadth
    columns, `new_high_low_json`, and **`candidate_counts_json`** — no re-derivation
    (`snapshot_serving.py:64-82`).
  - `stocks_payload`/`stock_detail_payload` both call `stored_stock_rows`, which rehydrates each
    `ScannerResult.record_json` (`snapshot_serving.py:55-101`).
  - `sectors_payload`/`themes_payload` read the stored `SectorScoreRow`/`ThemeScoreRow` children
    verbatim (`snapshot_serving.py:104-160`).
- **`run_scan` remains the ONE computing path and is idempotent.** `resolve_run` → `run_scan`
  returns the existing run for a stored date and **never recomputes/overwrites** it
  (`scanner.py:55-63`: `if existing is not None: return existing`); only on first creation does it
  call each canonical engine exactly once and store faithful copies (`scanner.py:65-146`). So for a
  persisted date the read path performs no recompute — satisfying the *No recompute in the read path*
  and *Snapshots-immutable* anti-goals at the structural level the coherence gate checks.
- **J-06 byte-identical preserved.** `/api/stocks` (list) and `/api/stocks/{ticker}` (detail) both
  read the *same* `stored_stock_rows` output (`stocks.py:24-37`) → the detail row is the identical
  rehydrated `record_json`, not a per-ticker recomputation.
- **Watchlist coherence improved, not drifted.** `app/api/watchlist.py:_canonical_rows` now reads
  `stocks_payload(resolved_run(None))["rows"]` — the SAME stored latest-snapshot rows `/api/stocks`
  serves — replacing the former parallel live `score_stocks` call (`watchlist.py:52-58`). This brings
  the watchlist's "current" values onto the identical source as `/api/stocks`, eliminating a
  potential divergence rather than creating one. Blessed by the blueprint iter-8 note.
- **No unregistered new value.** The only new displayed concept — the resolved as-of date + the
  available-date list — is registered in the blueprint Data Contract (the J-13 row,
  `blueprint.md:83`); the available dates come from the **existing** canonical `GET /api/runs`
  (frontend `AsOfProvider` calls `fetchRuns()` → `/api/runs`, `asof-provider.tsx:41`), not a new
  source. `/api/stocks/{ticker}/bars` gains `?as_of=` but still serves raw `bars_asof` + canonical
  `sma_series` (no score) — explicitly exempt from snapshot storage by the blueprint.
- **Endpoint identity unchanged.** Each value's canonical *serving endpoint* is the same as before;
  only the internal data source moved from live-compute to stored-read — and the blueprint Data
  Contract + iter-8 serving note (`blueprint.md:70-71,98`) record this re-sourcing explicitly.

## Part B — Information Architecture check (discoverability / duplicate home / parallel shell)

**No violation.**

- **No new page/route.** Zero new routes (confirmed by the ui-surface-map and the diff). The switcher
  is a global top-bar control only.
- **No parallel shell.** `AsOfSwitcher` + `AsOfProvider` mount inside the **existing** app shell
  header next to `HealthBadge`, with the unchanged `Sidebar` (`app/layout.tsx`: switcher added to the
  same `<header>`, `<Sidebar />` untouched). No competing layout/nav introduced.
- **Reachability.** A global top-bar control is present on every as-of-aware page → 0 clicks to
  reach; trivially within the ≤2-click rule.
- **No duplicate home.** No second page is created for any entity; all five target pages keep their
  established homes under the blueprint IA.
- **Blueprint conformance.** The IA section was updated this iteration to register the switcher as an
  additive top-bar control with **no sidebar section added and no feature home moved** — nav skeleton
  unchanged, no `blueprint.reapproval-requested` (`blueprint.md:27-29`). Consistent with the diff.

## Part C — Advisory observations (non-blocking)

- None material. The historical indicator label ("Viewing as-of {date} (historical)",
  `asof-switcher.tsx:24-27`) matches the blueprint IA wording, and the per-page "Data as-of {date}" /
  "as of {date}" labels remain consistent across pages. The blueprint and Data Contract were updated
  in-diff to reflect the re-sourcing, so no drift between contract and code.

## Conclusion

No objective Step-1 (Data Contract) or Step-2 (Information Architecture) violation. The iteration
consolidates the read path onto the single canonical persisted snapshot, preserves J-06 byte-identity
across list/detail, and keeps the watchlist on the same source as `/api/stocks`. **COHERENCE-PASS.**
