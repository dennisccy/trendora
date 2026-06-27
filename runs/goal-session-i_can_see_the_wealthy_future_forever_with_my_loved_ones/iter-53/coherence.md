**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-53 (J-110: Research Regime Lab)

**Session:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
**Iteration:** 53
**Snapshot SHA:** b7adbce48cd4833e71f54f57e44466b8df78952b
**Audited:** 2026-06-27

---

## Files changed this iteration

```
apps/backend/app/api/research.py
apps/backend/app/engine/research.py
apps/backend/app/engine/samples.py
apps/backend/tests/test_api_research.py
apps/backend/tests/test_samples.py
apps/frontend/app/research/_labs.tsx
apps/frontend/app/research/page.tsx
apps/frontend/lib/api.ts
apps/frontend/lib/samples-link.ts
runs/…/state/blueprint.md  (additive: J-110 IA line + Data Contract row)
```

---

## Part A — Data Contract (duplicate computation / non-canonical source)

### New aggregate: Regime Lab cross-sectional study (J-110)

**Blueprint registration (blueprint.md line 434 / line 478 — added this iteration):**
- Canonical computing module: `research:compute_regime_lab` (`apps/backend/app/engine/research.py`)
- Serving endpoint: `GET /api/research/regime-lab` (`apps/backend/app/api/research.py`)

**Duplicate computation check:**
`compute_regime_lab` and `regime_lab_cached` group ALREADY-STORED values only — they read `ForwardReturn.realized_return`, `ForwardReturn.max_drawdown`, and `ScannerRun.regime_score`/`ScannerRun.regime_label` verbatim from storage over the bounded streamed read path. No new function computes regime scores or forward returns independently. No violation found.

**Non-canonical source check:**
The frontend `fetchRegimeLab` in `apps/frontend/lib/api.ts` constructs a call to `/api/research/regime-lab` — the registered canonical endpoint. The page component in `apps/frontend/app/research/_labs.tsx` uses only `fetchRegimeLab` for its data; no client-side recomputation of return, regime, or drawdown values occurs.

**Unregistered-value check:**
The per-label and per-decile mean return, mean max-drawdown, rank-IC, and n values are all part of the single new Regime Lab aggregate registered in the blueprint this iteration. No displayed value remains unregistered.

**Part A result: PASS — no data contract violations.**

---

## Part B — Information Architecture (nav path / duplicate home / parallel shell)

### New page: `/research/regime-lab`

**Blueprint IA registration (blueprint.md line 434 — added this iteration):**
```
│   ├── Regime Lab          /research/regime-lab          (J-110 [TARGET iter-53] …)  — hub-linked, deep-linkable
```

**Navigation path check:**
`apps/frontend/app/research/page.tsx` adds a tile `{ href: "/research/regime-lab", title: "Regime Lab", icon: Gauge }` to the `LABS` array rendered on the Research hub. The Research hub is reachable from the persistent top-level nav in one click. The Regime Lab page is then one tile-click away from the hub.
Reachability: **≤2 clicks** (nav → Research hub → Regime Lab tile). PASS.

**Route existence check:**
`apps/frontend/app/research/regime-lab/page.tsx` exists (confirmed via directory listing). The Next.js app-router route is properly in place.

**Duplicate home check:**
The blueprint and iter spec both explicitly state J-110 is DISTINCT from J-77 (`/research/regime-setup-pattern` — regime × setup × pattern) and J-103 (`/research/severity-velocity` — severity-velocity sign vs SPY). Different routes, different subjects (regime score/label alone vs cross-sectional stock returns). No duplicate home.

**Parallel shell check:**
The new page lives under the existing `/research` hub as a lazy sub-route — no new top-level nav section, no new layout shell. The Research nav section is unchanged.

**Part B result: PASS — no IA violations.**

---

## Part C — Advisory observations

None. The new tile and sub-route follow the established hub-tile → lazy-sub-route pattern identically to all prior lab additions (Factor Lab, Severity-velocity, Downtrend Opportunity, etc.).

---

## Summary

| Check | Result |
|---|---|
| A1: Duplicate computation of Regime Lab aggregate | PASS — no second computation path |
| A2: Non-canonical source for Regime Lab | PASS — frontend reads from `GET /api/research/regime-lab` only |
| A3: Unregistered new value | PASS — aggregate registered in blueprint this iteration |
| B1: Navigation path for `/research/regime-lab` | PASS — Research hub tile, ≤2 clicks |
| B2: Route file exists | PASS — `apps/frontend/app/research/regime-lab/page.tsx` |
| B3: Duplicate home | PASS — distinct from J-77 and J-103 |
| B4: Parallel shell | PASS — sub-route under existing Research hub |
