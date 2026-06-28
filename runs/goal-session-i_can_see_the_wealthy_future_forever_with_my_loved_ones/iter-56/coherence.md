**Verdict:** COHERENCE-PASS

---

## Coherence Audit — iter-56 (J-113: Research hub reorder + J-114: de-interleave all-horizon lab columns)

**Session:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
**Iteration:** 56
**Snapshot SHA:** 0eef52cf34ab2cec8746c148850841e1aa27e181
**Files changed (committed):** 2 frontend files (`apps/frontend/app/research/page.tsx`, `apps/frontend/app/research/_labs.tsx`); plus `runs/` and blueprint annotation (additive docs only).
**Untracked new files (to be committed):** `apps/frontend/lib/research-labs.ts`, `apps/frontend/lib/research-lab-columns.ts`, `apps/frontend/lib/research-labs.test.ts`, `apps/frontend/lib/research-lab-columns.test.ts`.

---

### Part A — Data Contract (no violations)

Blueprint registers J-113/J-114 as "NO new Data Contract value, NO new endpoint, NO recompute — pure frontend presentation / view-transform changes over already-served values."

**A1 — Duplicate computation check:**

`apps/frontend/lib/research-lab-columns.ts` introduces `groupedHorizonColumns(horizons)`. This function takes the config-driven `horizons` array (reported verbatim by the lab API payload as `data.horizons`) and returns grouped column descriptors — it determines column ordering only. It computes no financial value, calls no API, and reads no canonical data. It is not a synonym or re-derivation of any Data Contract entry. No duplicate computation found.

`apps/frontend/lib/research-labs.ts` introduces `RESEARCH_LABS` — a static ordered array of hrefs/titles/icons. No computation, no API call. Not a new displayed value; it is a refactored source of the same 10 lab navigation entries previously defined inline in `page.tsx`.

**A2 — Non-canonical source check:**

All four lab tables (`FactorsTable`, `RegimeLabByLabelTable`, `PhaseSeverityLabByLabelTable`, `RegimePhaseFactorTable`) and their sub-tables in `_labs.tsx` now iterate via `groupedHorizonColumns(horizons)` instead of paired `Fragment` loops. Every cell renderer (`TopDecileCell`, `DecileReturnCell`, `DecileMddCell`, `RegimeReturnCell`, `RegimeMddCell`) is unchanged and reads values from the same component props it always did — which are derived from the lab API fetch (`fetchFactorLab`, `fetchRegimeLab`, etc.). No new fetch path, no client-side recomputation of any registered value.

**A3 — New values check:**

No new displayed value. The spec confirms "figures are byte-identical." No unregistered-value warning is warranted.

No Part A violations.

---

### Part B — Information Architecture (no violations)

Blueprint IA registers all ten lab sub-routes under the existing Research section (≤2 clicks from nav). J-113/J-114 change only the reading ORDER of those ten entries; no route is added, removed, or renamed.

**B1 — Navigation path:**

`apps/frontend/components/sidebar.tsx:37` — `{ href: "/research", label: "Research", icon: Microscope }` (1 click).

`apps/frontend/lib/research-labs.ts` (new, imported by `page.tsx`) lists the same 10 hrefs as the previous inline `LABS` array, in the J-113 order. All 10 are valid existing routes. The hub page renders each as a `Link` card (2nd click). Navigation path confirmed for all ten labs: ≤2 clicks.

**B2 — Reachability:**

2 clicks for every lab (sidebar → Research hub → card). Within the ≤2-click rule.

**B3 — Duplicate home:**

No new lab page or route introduced. No entity gains a second home. No duplicate home.

**B4 — Parallel shell:**

No new layout file. The hub page inherits the existing app shell. No parallel shell.

No Part B violations.

---

### Part C — Advisory observations

None. The refactor to `lib/research-labs.ts` and `lib/research-lab-columns.ts` follows the established node TS-strip test convention and is consistent with the project's lib-module pattern. No inconsistent labelling, no formatting drift, no layout divergence.

---

### Summary

| Check | Result |
|-------|--------|
| Data Contract — duplicate computation | PASS — `groupedHorizonColumns` orders columns only; computes no financial value |
| Data Contract — non-canonical source | PASS — all lab tables still read from their existing canonical API fetch functions |
| Data Contract — new/unregistered value | PASS — no new displayed value; figures byte-identical |
| IA — navigation path exists (all 10 labs) | PASS — sidebar → Research hub → tile card (2 clicks each) |
| IA — reachability ≤2 clicks | PASS |
| IA — duplicate home | PASS — no new route; no second home for any entity |
| IA — parallel shell | PASS — inherits existing app layout |
