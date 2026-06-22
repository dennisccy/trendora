**Verdict:** COHERENCE-PASS

---

## Coherence Audit — Iteration 45

**Session:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
**Iteration index:** 45
**Snapshot SHA:** 6b636f39ebbf905be7afc6d6fe264810db25e8a2
**Changed files:** `apps/backend/app/api/research.py`, `apps/backend/app/config.py`, `apps/backend/app/engine/market_phase.py`, `apps/backend/app/engine/research.py`, `apps/backend/app/engine/samples.py`, `apps/backend/tests/test_api_research.py`, `apps/frontend/app/research/page.tsx`, `apps/frontend/app/research/samples/page.tsx`, `apps/frontend/lib/api.ts`, `apps/frontend/lib/samples-link.ts`, `config.yaml`, `runs/.../state/blueprint.md`

---

## Part A — Data Contract

### Registered values checked

**severity_velocity (J-102 / J-103):**
- Canonical computing module: `research:compute_severity_velocity_study` (new; registered in blueprint Data Contract this iteration).
- Serving endpoint: `GET /api/research/severity-velocity` (new; registered in blueprint).
- The study reads `severity_velocity` from `market_phase.severity_velocity_by_date` — the registered canonical source for J-102. Confirmed in `apps/backend/app/engine/research.py` (new function `_severity_velocity_observation_set` lazy-imports `severity_velocity_by_date` from `market_phase`; no slope recomputed here).
- The study reads `forward_returns` (SPY) verbatim from the stored `ForwardReturn` table — the registered canonical source. No new forward-return computation.
- No duplicate computation found. No non-canonical source.

**factor_combination (J-26):**
- J-104(a) wraps `compute_factor_combination` in a new caching layer `factor_combination_cached` (`apps/backend/app/engine/research.py:2482`). The API endpoint `GET /api/research/factor-combination` now calls `factor_combination_cached` instead of `compute_factor_combination` directly (`apps/backend/app/api/research.py:199`). This is a pure performance layer — the serving endpoint is unchanged, figures are byte-identical, no new computation path introduced. Not a violation.

**regime_setup_pattern (J-77):**
- J-104(a) wraps `compute_regime_setup_pattern_study` in `regime_setup_pattern_cached` (`apps/backend/app/engine/research.py:2538`). The API endpoint `GET /api/research/regime-setup-pattern` now calls `regime_setup_pattern_cached` (`apps/backend/app/api/research.py:311`). Same caching-layer pattern — serving endpoint unchanged, figures byte-identical. Not a violation.

**downtrend_opportunity (J-91):**
- J-104(b) bounds the `select(ScannerRun)` query in `_downtrend_opportunity_observation_set` with `where(ScannerRun.asof_date <= as_of)` (`apps/backend/app/engine/research.py` diff, replacing `session.exec(select(ScannerRun)).all()`). This is a query-optimization (no full-table scan), not a recomputation. Serving endpoint `GET /api/research/downtrend-opportunity` unchanged. Not a violation.

**Research samples drill-down (J-51):**
- A new `KIND_SEVERITY_VELOCITY = "severity-velocity"` cohort is added to `samples.py` (`apps/backend/app/engine/samples.py`). The `_severity_velocity_samples` builder uses the SAME `_severity_velocity_observation_set` + `_severity_velocity_member_key` that `compute_severity_velocity_study` uses — one membership rule. Served via the EXISTING `GET /api/research/samples`. Not a new endpoint, not a recompute. Not a violation.

**New displayed values introduced:**
- The severity-velocity × regime matrix (mean forward return / win-rate / N per cell per horizon). This is registered in the blueprint Data Contract as a new J-103 row. The inputs (`severity_velocity`, `forward_returns`) are ALREADY registered values read from their canonical sources — no new canonical value, no duplicate concept. Compliant.

### No Data Contract violations found.

---

## Part B — Information Architecture

### New routes introduced

| Route | Home in IA | Hub link present | Sidebar reachability |
|-------|-----------|-----------------|----------------------|
| `/research/severity-velocity` | Registered in blueprint IA (line 340 of blueprint.md) | Yes — entry `href: "/research/severity-velocity"` in `LABS` array in `apps/frontend/app/research/page.tsx:74` | Research sidebar → `/research` hub (1 click) → lab card (2nd click) |
| `/research/factor-combination` | Registered in blueprint IA (line 341) | Yes — entry `href: "/research/factor-combination"` in `LABS` array at `page.tsx:38` | Same 2-click path |
| `/research/event-study` | Registered in blueprint IA (line 342) | Yes — entry `href: "/research/event-study"` in `LABS` array at `page.tsx:43` | Same 2-click path |
| `/research/regime-setup-pattern` | Registered in blueprint IA (line 343) | Yes — entry `href: "/research/regime-setup-pattern"` in `LABS` array at `page.tsx:47` | Same 2-click path |
| `/research/downtrend-opportunity` | Registered in blueprint IA (line 344) | Yes — entry `href: "/research/downtrend-opportunity"` in `LABS` array at `page.tsx:62` | Same 2-click path |
| `/research/factor-lab` | Present in the hub `LABS` array at `page.tsx:32` (pre-existing feature, now its own route) | Yes | Same 2-click path |
| `/research/recovery-turn-edge` | Pre-existing feature (J-90), now its own route — linked from hub `LABS` at `page.tsx:60` | Yes | Same 2-click path |

**Sidebar verification:** `apps/frontend/components/sidebar.tsx` has a single `{ href: "/research", label: "Research" }` entry (line 37). `isActive` uses `pathname.startsWith(href)` (line 51), so every `/research/*` sub-route inherits the sidebar highlight. All new routes are reachable in exactly 2 clicks from the persistent nav (sidebar Research → hub → lab card). No route requires typing a URL.

**No navigation-path violations. No undiscoverable routes. No duplicate home. No parallel shell.**

The `/research` monolith→hub restructure is a nav-skeleton change explicitly noted as `blueprint.reapproval-requested` in the iteration spec and registered in the blueprint IA this iteration. The run-goal.sh framework auto-approves this and continues.

---

## Part C — Advisory

No advisory issues noted. Label consistency, value formatting, and layout all follow the established shell patterns. The honest verdict caveat (`SEVERITY_VELOCITY_VERDICT_CAVEAT` constant in `apps/backend/app/engine/research.py`) is carried verbatim on every payload response, matching the `Honest limitations surfaced` anti-goal invariant.

---

## Summary

- **Part A violations (Data Contract):** 0
- **Part B violations (Information Architecture):** 0
- **Advisory notes:** 0

All new routes are registered in the blueprint IA, reachable in ≤2 clicks from the sidebar via the `/research` hub, and serve values through their single registered canonical endpoints. The caching wrappers (J-104a) and the query bound (J-104b) are pure performance properties with byte-identical figures and no new computation paths.
