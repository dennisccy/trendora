# Iteration 22 — Coherence Audit

**Iteration:** goal-mcp-loop-iter-22
**Date:** 2026-07-08
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-WARN

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Index/benchmark/macro series vendor label + honest first-bar window (NEW this iteration, registered additively in `blueprint.md`'s Data Contract + the iter-22 spec's "Data-contract additions") | OK | **Sole computation:** `apps/backend/app/engine/indexes.py:47-52` (`_vendor_label`, the one raw-key→display-label map) assembled into each series entry at `indexes.py:135` (`seed_meta = load_seed_meta(seed_dir)`) and `:156-163` (`vendor`/`first` attached in `compute_index_series`). **Sole source read:** `apps/backend/app/engine/data_manager.py:991-1009` (`load_seed_meta`), which shares ONE parse point, `data_manager.py:959-969` (`_read_seed_meta_rows`), with the pre-existing `load_seed_windows` — refactored (`data_manager.py:974-989`) to reuse it, so there is no second `json.loads(meta.json)` anywhere in the diff. **Sole endpoint:** additive fields on the existing `GET /api/indexes` — no new route file, no second endpoint. **Two readers, neither recomputes:** both go through the existing typed client `apps/frontend/lib/api.ts:499` (`fetchIndexes`) — `apps/frontend/components/index-vendor-panel.tsx:43` (new `/data` panel) and `apps/frontend/components/phase-cross-view-card.tsx:51` → `phase-cross-view-chart.tsx:305,369,450` (the live Dashboard chart's tooltip/legend, `v.vendor`/`s.vendor` rendered verbatim from the server payload). Confirmed real backing data, not just test fixtures: `apps/backend/data/seed/meta.json` carries `^SPX/^NDX/^DJI → "stooq"`, `^VIX → "yahoo"`, `^TNX/^DXY/^VXN → "fred-macro-proxy"`, matching the new unit tests' assertions byte-for-byte. The panel's fetch omits the global `asof` param that the chart passes (`index-vendor-panel.tsx:43` vs `phase-cross-view-card.tsx:51`), but both pass `full=true`, and `indexes.py:140-144` shows `full=True` selects `bars_through_latest` unconditionally (independent of `resolved`/as-of) — so the set of series and their `vendor`/`first` values (sourced from the static manifest, never from `points`) cannot diverge between the two readers. Not a violation. |
| Existing Leadership/Entry/Risk scores, regime, sector, theme, forward-return, research-cohort values, evidence ledger | OK — untouched | No hunk in this diff touches `scoring.py`, `regime.py`, `sectors.py`, `themes.py`, `forward_testing.py`, `research.py`, `referee.py`, or `ledger.py`. `config.yaml`'s only change is 5 additive `index_chart.symbols` entries (`config.yaml:604-620`), explicitly NOT added to `etfs.index` — confirmed no other `config.yaml` hunk touches `etfs.*`/scoring/universe keys, consistent with the spec's anti-leak constraint. |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Deep `^SPX`/`^NDX`/`^DJI`/`^VIX`/`^TNX` benchmark lines + vendor labels on the Dashboard chart | OK — no new route | `apps/frontend/components/sidebar.tsx:32` lists `/` (Dashboard) as an existing top-level link (1 click). The change is additive content inside the already-live chart — `apps/frontend/app/page.tsx:161` renders `<PhaseCrossViewCard />` (confirmed the sole market chart on `/`) — not a new page or a parallel shell. |
| `/data` index/benchmark vendor-disclosure panel (`IndexVendorPanel`, new component) | OK — no new route | `apps/frontend/components/sidebar.tsx:44` lists `/data` (Data Manager) as an existing top-level link (1 click). `apps/frontend/app/data/page.tsx:474` mounts `<IndexVendorPanel />` inline in the existing page immediately after the existing `<MacroFeedPanel />` (`:469`) — same route, same shell, same `Card` primitive; not a second page for index/benchmark data. |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Perpetuated dead-code duplicate (tidy next iteration).** `apps/frontend/components/index-regime-chart.tsx` and its wrapper `major-indexes-card.tsx` are imported by nothing under `apps/frontend/app/` (`grep -rn "MajorIndexesCard" apps/frontend/app` → zero hits), confirmed independently and matching the ui-impact-analyst's own finding in `reports/phase-goal-mcp-loop-iter-22-ui-surface-map.md`. `apps/frontend/app/page.tsx:157-160`'s own comment records this card was superseded by `PhaseCrossViewChart` in a prior iteration (J-101a) for being a duplicate. This iteration applied the identical vendor-label + 10-slot-palette fix to BOTH the live `phase-cross-view-chart.tsx` and the dead `index-regime-chart.tsx`, spending effort keeping an unreachable duplicate byte-for-byte in sync with the live implementation instead of deleting it. Not a FAIL: the duplicate predates this iteration (not a new "duplicate home" introduced now) and is unreachable by any user, so it cannot itself produce a displayed "numbers don't match" symptom today. But it is exactly the scattered-duplicate pattern this gate exists to catch before it bites — if a future edit updates one copy's chart logic and misses the other, or `MajorIndexesCard` is ever accidentally re-wired into a route, the two will have silently diverged. Recommend a follow-up iteration delete `index-regime-chart.tsx` + `major-indexes-card.tsx` (and any now-pointless dedicated tests for them) now that two iterations in a row have confirmed `phase-cross-view-chart.tsx` is the sole live implementation.
- **Stale blueprint IA label.** `runs/goal-session-mcp-loop/state/blueprint.md`'s Feature/journey homes table still names J-14's Dashboard home "major-indexes & regime card" — that named component was removed and consolidated into the "Regime × phase cross-view" card by the same prior iteration (J-101a) noted above. The registered route (`/`) is still correct, so this is documentation drift, not a coherence violation; worth a one-line rename the next time the blueprint file is touched.
