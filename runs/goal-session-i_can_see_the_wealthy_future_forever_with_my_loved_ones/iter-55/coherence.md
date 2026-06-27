**Verdict:** COHERENCE-PASS

---

## Coherence Audit — iter-55 (J-112: Regime × Phase × Factor 3-way decile lab)

**Session:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
**Iteration:** 55
**Snapshot SHA:** d11e4c99cb6d585c4c28ba1a407e063e8ac0ae2f
**Files changed:** 14 (+1394 / -4); all changes are additive to backend engine, API, frontend, and tests.

---

### Part A — Data Contract (no violations)

Blueprint registers J-112 with:
- Canonical computing module: `research:compute_regime_phase_factor_study`
- Serving endpoint: `GET /api/research/regime-phase-factor`
- Reads (VERBATIM) from already-registered sources: `ScannerRun.regime_score` (J-80), served `market_phase` 0-100 severity (J-87/J-111, joined by snapshot date), stored factor values (Factor Lab source), `forward_returns.realized_return` + `forward_returns.max_drawdown` (J-86)

**A1 — Duplicate computation check:** No second function outside the registered module computes regime score, severity, forward return, max drawdown, or factor values. The diff introduces `compute_regime_phase_factor_study` in `apps/backend/app/engine/research.py` — this IS the registered canonical module. The helper functions `_regime_phase_factor_members_by_horizon`, `_assign_triple_deciles`, `_regime_phase_factor_observation_set` are internal to the same module. No duplicate computation found.

**A2 — Non-canonical source check:** `fetchRegimePhaseFactor` in `apps/frontend/lib/api.ts:1365` calls `/api/research/regime-phase-factor` — the registered canonical endpoint. The `RegimePhaseFactorPage` component in `apps/frontend/app/research/_labs.tsx:4502` invokes only `fetchRegimePhaseFactor`. No client-side recomputation of any registered value.

**A3 — New aggregate registration:** The 3-way `(regime-score-decile × severity-score-decile × factor-decile)` aggregate is a genuinely new combination study, not a synonym or re-derivation of any existing registered value (distinct from J-77 regime×setup×pattern, J-103 severity-velocity-sign, J-110 regime-alone, J-111 phase/severity-alone). It IS registered in the blueprint's Data Contract this iteration with the correct canonical module and endpoint. No "unregistered value" warning needed.

**A4 — No magic number violation:** `regime_phase_factor_page_size: 30` sourced from `config.yaml`/`config.py`; page size passed to the frontend via the API payload. No inline literal in `research.py` or `samples.py` for min-sample, page size, horizons, or decile count.

No Part A violations.

---

### Part B — Information Architecture (no violations)

Blueprint IA registers `/research/regime-phase-factor` as a hub-linked lazy sub-route under the existing Research section (≤2 clicks from nav).

**B1 — Navigation path:** `apps/frontend/components/sidebar.tsx:37` has `href: "/research"` (1 click). `apps/frontend/app/research/page.tsx` (Research hub) now includes a tile with `href: "/research/regime-phase-factor"` (2nd click). Route file exists at `apps/frontend/app/research/regime-phase-factor/page.tsx`. Navigation path confirmed: reachable in exactly 2 clicks.

**B2 — Reachability:** 2 clicks (sidebar → Research hub → Regime × Phase × Factor tile). Within the ≤2-click rule.

**B3 — Duplicate home:** No existing entity has `/research/regime-phase-factor` as a home. The new page is explicitly distinct from all sibling labs. No duplicate home.

**B4 — Parallel shell:** The new page (`page.tsx`) is a thin wrapper importing `RegimePhaseFactorPage` from `_labs.tsx`. It inherits the Next.js App Router layout from the parent tree (no standalone layout.tsx in the new directory). Uses `useResearchControls()` (the shared research control hook) — no second date state, no parallel nav shell.

No Part B violations.

---

### Part C — Advisory observations

None. The new page follows the established Research hub pattern (tile → lazy sub-route, same layout, same `useResearchControls` hook, same `CombinationLab` design language). No inconsistent entity labelling, no formatting drift, no layout divergence from the established shell.

---

### Summary

| Check | Result |
|-------|--------|
| Data Contract — duplicate computation | PASS — no duplicate; `compute_regime_phase_factor_study` is the sole registered module |
| Data Contract — non-canonical source | PASS — frontend reads only `GET /api/research/regime-phase-factor` |
| Data Contract — new aggregate registered | PASS — J-112 row present in blueprint Data Contract |
| IA — navigation path exists | PASS — sidebar → Research hub → tile (2 clicks) |
| IA — reachability ≤2 clicks | PASS |
| IA — duplicate home | PASS — distinct from all sibling labs |
| IA — parallel shell | PASS — inherits app layout |
