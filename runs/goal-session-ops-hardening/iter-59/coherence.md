# Iteration 59 — Coherence Audit

**Iteration:** goal-ops-hardening-iter-59
**Date:** 2026-08-11
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Regime Lab `by_horizon[].status` / whole-response `regime_lab_status` (row: "Membership timeline / research hot-key caches") | OK | `apps/backend/app/engine/research.py:4358-4267` (`_degrade_regime_lab_horizon`, `compute_regime_lab`) — same canonical module `app.engine.research.compute_regime_lab`, same endpoint `GET /api/research/regime-lab` (`research.py:4622-4627` `regime_lab_cached` unchanged endpoint binding); no second producer, no new table. Mirrors the already-registered Factor Lab `by_horizon[].status`/`factors_status` sibling fields on the SAME row per blueprint.md:430. |
| Same value, frontend read | OK | `apps/frontend/lib/api.ts:737-754` — `RegimeLabHorizonCell.status?` / `RegimeLabResponse.regime_lab_status?` are additive optional TS fields on the existing `GET /api/research/regime-lab` response shape (`fetchRegimeLab`, unchanged call site) — no second endpoint, no client-side recomputation. `apps/frontend/app/research/_labs.tsx:663-721` (`regimeCellIsNa`, `regimeNaTitle`, `RegimeReturnCell`, `RegimeMddCell`) only branches display/tooltip text off the fetched field — a re-format, not a computation. |
| `regime_lab_cached`'s never-cache-a-degraded-payload guard | OK | `research.py:4619-4625` — a caching-policy change to the existing cache write path, not a second producer or a second serving endpoint. |
| Test-only `TRENDORA_FAULT_INJECT_MEMORY_ERROR` site registration | OK (not a displayed value) | `apps/backend/app/engine/data_manager.py:9-16` — adds `"regime_lab"` to the existing `_FAULT_INJECT_SITES` frozenset, the same env-gated test seam already used for `forward_aggregates`/`factor_lab_all`/etc. No product code path. |
| `rank_ic_by_horizon[].status` (a third accumulator carrying the same degrade marker, alongside `by_label`/`by_decile`'s `by_horizon[].status`) | OK — same concept, not a new value | `research.py:49` (`_degrade_regime_lab_horizon`) — same computing module/endpoint as the registered row; this is the identical "honest per-horizon unavailable marker" concept applied to a third accumulator on the SAME payload, not a new displayed value requiring separate registration. |

No new function recomputes regime score, market phase, or realized forward-returns outside their registered modules. No new UI surface fetches this value from a non-canonical endpoint.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/research/regime-lab` (degrade-state rendering only) | OK | No new route/page/nav entry. Confirmed via `reports/phase-goal-ops-hardening-iter-59-ui-surface-map.md` ("New pages/routes: 0", "Navigation changes: no") and the diff itself — only `_labs.tsx` (existing component tree under the existing `/research/regime-lab` page) and `lib/api.ts` (types) changed on the frontend. Route already has its canonical home per blueprint.md's IA tree (`Research /research — index of 15 labs (…, regime-lab, …)`) and the "Feature / journey homes" table's J-07 row (global badge + `/research/*`/`/backtest`, unchanged). No parallel shell introduced — the changed components render inside the existing `RegimeLabPage`/`ResearchControls` shell (per the ui-surface-map's "Whole page, non-degraded path... Unchanged" row). |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- **Inconsistent degrade signaling within one page.** Per `reports/phase-goal-ops-hardening-iter-59-ui-surface-map.md` row 3 ("Known gap (unchanged)"): the backend now emits `rank_ic_by_horizon[].status: "unavailable"` on a degraded horizon (`research.py:49`), but the Rank-IC header row's frontend rendering does not read that field — a degraded horizon in the Rank-IC row still falls back to the pre-existing generic "Not enough independent observations..." tooltip instead of the new "Temporarily unavailable — degraded under memory pressure" wording the by-label/by-decile cells now show for the identical underlying cause. This is disclosed and intentional this round (explicit scope boundary in the ui-surface-map, not a hidden defect), and it does not produce a wrong number — the Rank-IC cell still correctly shows NA. Same entity (a memory-pressure degrade), two different tooltip wordings on the same page — a Part-C labeling-consistency item for a future iteration to close (wire `regimeNaTitle`'s degrade branch into the Rank-IC row's own NA rendering), not a gate-blocking issue.
