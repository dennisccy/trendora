**Verdict:** COHERENCE-PASS

# Coherence Audit — iter-54 (J-111: Market Phase & Severity Lab)

**Session:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
**Iteration:** 54
**Snapshot SHA:** e45a81596067958b33ce349cef4bcb57ff4568d7
**Audited diff files:** 12 changed (1116 insertions, 7 deletions)

---

## Part A — Data Contract (duplicate computation / non-canonical source)

### Registered values touched by this iteration

**New aggregate — Phase & Severity Lab (J-111):**
- Blueprint Data Contract row added this iteration (blueprint.md +1 row at the Data Contract section, confirmed in the diff)
- Canonical computing module registered: `research:compute_phase_severity_lab` in `apps/backend/app/engine/research.py` (lines 3490+)
- Canonical serving endpoint registered: `GET /api/research/phase-severity-lab` in `apps/backend/app/api/research.py` (lines 419–459)

**Source values consumed (already-registered):**
- `forward_returns.realized_return` + `forward_returns.max_drawdown` — read from the stored `forward_returns` table verbatim (canonical source unchanged)
- Market-phase label + 0–100 severity score — read VERBATIM from `market_phase._timeline_series`/`timeline_full` joined by snapshot date (the J-87/J-88/J-97 registered canonical source; no second phase/severity computation introduced)

**Duplicate computation check:**
- `compute_phase_severity_lab` appears exclusively in `apps/backend/app/engine/research.py`. No second implementation of the same grouping logic was introduced anywhere in the diff.
- Phase label and severity score are joined from the existing `market_phase` causal timeline series — the same path the Dashboard panel and J-103 already use. The diff introduces no independent phase/severity derivation.

**Non-canonical source check:**
- `apps/frontend/lib/api.ts` `fetchPhaseSeverityLab` calls `GET /api/research/phase-severity-lab` (the registered canonical endpoint) via `getJSON` + `withAsOf`. No client-side recomputation and no alternative backend path.

**Result: no Part A violations.**

---

## Part B — Information Architecture (navigation path / duplicate home / parallel shell)

### New route: `/research/phase-severity-lab`

**Blueprint IA registration:**
The blueprint IA tree was updated this iteration to add:
```
│   ├── Phase & Severity Lab /research/phase-severity-lab  (J-111 [TARGET iter-54] … hub-linked, deep-linkable
```
(blueprint.md diff, +1 line after the Regime Lab entry)

**Route existence:** `apps/frontend/app/research/phase-severity-lab/page.tsx` — confirmed present.

**Navigation path (static analysis):**

1. `apps/frontend/components/sidebar.tsx:37` — `{ href: "/research", label: "Research", icon: Microscope }` — direct sidebar link to the Research hub (1 click from the persistent nav).
2. `apps/frontend/app/research/page.tsx` — new `LABS` entry `{ href: "/research/phase-severity-lab", title: "Market Phase & Severity Lab", … }` (diff confirmed) — one click from the Research hub to the new page.

Total: **2 clicks** from the persistent sidebar. Compliant with the ≤2 click rule.

**Duplicate home check:** No existing blueprint entity has `/research/phase-severity-lab` as its home. The new page is explicitly distinguished from J-103 (severity-velocity SIGN vs SPY) and J-110 (regime score/label) — different grouping subject (severity LEVEL + phase label vs cross-sectional stock returns). No duplicate home.

**Parallel shell check:** The new page is nested under the existing `/research` hub and uses the same app shell. No new layout wrapper or separate nav was introduced.

**Result: no Part B violations.**

---

## Part C — Advisory observations

None. The iteration is a structural twin of the iter-53 Regime Lab: same caching idiom, same bounded-read path, same hub-tile + lazy sub-route pattern. No labelling inconsistency, formatting drift, or layout deviation detected.

---

## Summary

| Check | Result |
|-------|--------|
| A1 — Duplicate computation of registered value | PASS — `compute_phase_severity_lab` is the sole implementation; phase/severity read from canonical `market_phase` series |
| A2 — Non-canonical source in new UI surface | PASS — frontend calls only `GET /api/research/phase-severity-lab` |
| A4 — New displayed value duplicates an existing registered concept | PASS — distinct subject (severity LEVEL + phase label vs cross-sectional returns); not J-103 or J-110 |
| A5 — New value unregistered in Data Contract | PASS — Data Contract row added to blueprint.md this iteration |
| B1 — No navigation path to new route | PASS — sidebar → Research → hub tile (2 clicks) |
| B2 — Reachability > 2 clicks | PASS — exactly 2 clicks |
| B3 — Duplicate home for existing entity | PASS — no prior home for this entity |
| B4 — Parallel shell | PASS — placed under existing `/research` hub shell |
