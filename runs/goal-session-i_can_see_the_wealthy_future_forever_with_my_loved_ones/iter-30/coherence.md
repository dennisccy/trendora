**Verdict:** COHERENCE-PASS

## Coherence Audit — iter-30 (J-89 + J-90)

**Session:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
**Iteration:** 30
**Snapshot SHA:** dbd92e79ecf37ddb24a7076cd739f80f147b702f
**Audited:** 2026-06-18

---

## Part A — Data Contract check

### Registered values checked

**J-89 market-phase history timeline** (`{date, phase, p_bear}` per snapshot date):
- Blueprint registers this as an additive field on `GET /api/market-phase` computed by `market_phase` engine.
- `_timeline_series` in `apps/backend/app/engine/market_phase.py` reads the SAME `_filtered_bear_path` the panel's served P(bear) is the last element of — one derived series, no second computation.
- Served via the existing `GET /api/market-phase` cached payload as an additive field. No duplicate source found.
- **No violation.**

**J-89 causal downtrend episodes** (`{first_trigger_date, severity_at_trigger, open|closed}`):
- Blueprint registers under `market_phase` engine, served by `GET /api/market-phase`.
- `_downtrend_episodes` groups the causal timeline series — a deterministic grouping of the same `_timeline_series` output. One computation source. No second episode dater found elsewhere.
- **No violation.**

**J-89 retrospective (fenced)** — smoothed P(bear) + true-bear dating:
- Blueprint registers under `market_phase` engine, served ONLY on a separate explicitly-named `retrospective` field, NEVER feeding any as-of value.
- `_smoothed_bear_path` and `compute_retrospective` exist only in `market_phase.py`; they are called ONLY from `retrospective_cached` in `apps/backend/app/engine/market_phase.py`, which is called ONLY from the API endpoint `apps/backend/app/api/market_phase.py` when `retrospective=True`. The causal `compute_market_phase` path does not import or call `_smoothed_bear_path` or `compute_retrospective`.
- On the frontend, `fetchMarketPhase(asof, signal, retrospective)` in `apps/frontend/lib/api.ts` sends `?retrospective=true` ONLY when `showRetrospective=true` (a UI-toggle bool state in `MarketPhaseCard`, not a date state). The `MarketPhaseBody` reads ONLY `data.retrospective` for the fenced sub-view.
- Fence is structural (two separate code paths, two separate cached namespaces). **No violation.**

**J-90 causal recovery/turn signal** (`{is_recovery_turn, reason}`):
- Blueprint registers under `market_phase` engine, served by `GET /api/market-phase`.
- `_recovery_turn_signal` in `market_phase.py` is called from `compute_market_phase` and reads from the same timeline series (data ≤ D). Served as an additive `recovery_turn` field on the same cached payload. No second implementation found.
- **No violation.**

**J-90 Recovery-Turn Edge study** (per-horizon forward-return distribution):
- Blueprint registers canonical source as `research:compute_recovery_turn_edge`, served by NEW `GET /api/research/recovery-turn-edge`.
- `compute_recovery_turn_edge` is the sole implementation in `apps/backend/app/engine/research.py`. The API endpoint at `apps/backend/app/api/research.py:312` calls `recovery_turn_edge_cached` which calls `compute_recovery_turn_edge`. No other module computes this study.
- `fetchRecoveryTurnEdge` in `apps/frontend/lib/api.ts` fetches exclusively from `GET /api/research/recovery-turn-edge`. The `RecoveryTurnEdgeLab` component in `apps/frontend/app/research/page.tsx` reads only from this function.
- **No violation.**

**J-90 samples drill-down** (recovery-turn cohort via existing `GET /api/research/samples`):
- Blueprint registers the drill-down via the EXISTING `GET /api/research/samples` with a new `kind`. `KIND_RECOVERY_TURN = "recovery-turn"` is added to `apps/backend/app/engine/samples.py`. No new endpoint introduced. `samples-link.ts` serializes the cohort params into the existing `/research/samples` href.
- **No violation.**

### Existing registered values — no new duplicate computation found

The diff was checked for any new function computing phase/severity/P(bear) (J-87/J-88) or realized forward returns (J-21/J-75/J-81/J-86) independently of the registered canonical sources. None found. The `_recovery_turn_observation_set` reads `forward_returns` VERBATIM (SELECT-only), matching the blueprint registration.

---

## Part B — Information Architecture check

### New surfaces and routes

| Surface | Canonical IA home | Nav path | Verdict |
|---------|------------------|----------|---------|
| J-89 timeline overlay + episode list + fenced retrospective sub-view | Dashboard `/` | Sidebar link `{ href: "/", label: "Dashboard" }` — 1 click | PASS |
| J-90 recovery/turn signal on Market-Phase panel | Dashboard `/` | same sidebar link | PASS |
| J-90 Recovery-Turn Edge lab | Research `/research` | Sidebar `{ href: "/research", label: "Research", icon: Microscope }` at `apps/frontend/components/sidebar.tsx:37` — 1 click | PASS |
| J-90 samples drill-down via N= chip | `/research/samples` | link-reached from Recovery-Turn Edge lab chip — 2 clicks (Research → N= chip) | PASS |

No new top-level nav section. No new page/route. No duplicate home (the Recovery-Turn Edge lab is a section within the existing `/research` page, consistent with all prior lab additions J-25/J-26/J-27/J-29/J-72/J-77). No parallel shell.

### Date-state invariant (J-18) check

The diff was searched for `useState` calls in new frontend components. Only these state variables are introduced:
- `MarketPhaseCard`: `showRetrospective` (boolean toggle, not a date)
- `RecoveryTurnEdgeLab`: `view` (Episodes/Pooled cohort mode, not a date), `data`, `status`
- `RecoveryTurnPhaseTable`: `sortKey`, `sortDir` (view-transform sort state, not a date)

No `new Date()` or date `useState` found in the diff. No `window.addEventListener` or `document.addEventListener` in the new components. The single global as-of is consumed via `useAsOf()` in `MarketPhaseCard` — unchanged. **J-18 intact.**

---

## Part C — Advisory observations

None. All new values are registered in the Data Contract. All new surfaces land on existing IA homes. The fenced retrospective discipline matches the J-49 precedent. No formatting inconsistencies observed across surfaces for the same value.

---

## Summary

No objective violations from Part A (Data Contract) or Part B (Information Architecture). The iteration is fully coherent with the blueprint: two new registered values (Recovery-Turn Edge study + samples kind) each have a single canonical computing module and a single serving endpoint; the timeline + episodes + recovery signal are additive fields on the existing `GET /api/market-phase` canonical path; the fenced retrospective is structurally isolated from every causal path; and all new surfaces land on existing IA homes reachable in ≤ 2 clicks.
