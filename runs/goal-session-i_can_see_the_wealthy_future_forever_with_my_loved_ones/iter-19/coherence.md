# Iteration 19 — Coherence Audit

**Iteration:** goal-i_can_see_the_wealthy_future_forever_with_my_loved_ones-iter-19
**Date:** 2026-06-15
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Resolved as-of date + available dates (ONE global state) | OK | `apps/frontend/components/asof-provider.tsx:83` — lazy initializer `readAsofFromUrl` on the EXISTING `asOf` useState (no second date state); sole `?asof` owner unchanged; `searchKey` dep fix (line 222) and `restored` guard (line 177) preserved |
| Normalized index display series (J-44/J-49/J-78) | OK | `config.yaml:305` — `default_range` changed from `"6M"` to `"all"` (a valid preset key); canonical computation `indexes:compute_index_series` and canonical endpoint `GET /api/indexes` are unchanged; no new code path |

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| Dashboard `/` — indexes card default range | OK | No new page/route; amends existing Dashboard surface registered in IA |
| Cross-cutting as-of switcher (`asof-provider.tsx`) | OK | No new page/route; amends the existing cross-cutting top-bar control registered in IA |

## Blocking violations (FAIL only)

None

## Advisory notes (non-blocking)

None. This is a minimal two-target iteration: one config value edit (J-78) and one timing-only refactor of the existing single global as-of state (J-73). No new displayed value, no new endpoint, no new navigation surface, no second date state introduced. The J-18/J-43/J-50 single-global-as-of invariant is structurally intact — `asof-provider.tsx` remains the sole `?asof` reader/writer, the lazy initializer changes only when the one state is seeded (not what computes it), and the run-list validation/degrade pass is preserved.
