**Verdict:** COHERENCE-PASS

**Iteration:** goal-mcp-loop-iter-11
**Audited by:** coherence-auditor
**Date:** 2026-07-01
**Snapshot SHA:** 8dd8512ec7a84f242992e0ca938d754d075cdcb2

---

## Step 1 — Data Contract Check

**Registered contract value audited:** "Evidence status + certified-claim" — computed by `app.engine.referee:certify_edge` via `verify_edge`; read-side resolved by `app.engine.evidence:build_evidence_payload`; served by `GET /api/evidence`.

**Changed files touching evidence display:**
- `apps/frontend/lib/evidence.ts` (modified — committed)
- `apps/frontend/app/research/_labs.tsx` (modified — committed)
- `apps/frontend/lib/factor-lab-evidence.ts` (new untracked file)
- `runs/goal-session-mcp-loop/state/certified-claims.jsonl` (5th entry added)

**Findings:**

1. **`factor-lab-evidence.ts` — not a duplicate computation.** The new module exports one pure function `factorHorizonBadges` that calls `resolveCohortEvidence` (from `evidence.ts`) for each horizon. `resolveCohortEvidence` is the canonical read-side cohort matcher already registered in the blueprint (iter-8 clarification). `factorHorizonBadges` maps over horizons and re-displays the returned `proven`/`label`/`href`/`claim` verbatim — it decides nothing about proven-ness. No new computation introduced. (`apps/frontend/lib/factor-lab-evidence.ts:49–73`)

2. **`_labs.tsx` — still reads the canonical endpoint.** `evidenceClaims` is obtained via `fetchEvidence(controller.signal)` (`apps/frontend/app/research/_labs.tsx:215`) which calls `GET /api/evidence` (`apps/frontend/lib/api.ts:344–345`). The refactored per-horizon chip strip passes that same `evidenceClaims` slice to `factorHorizonBadges` — no new fetch path, no second endpoint. (`apps/frontend/app/research/_labs.tsx:840`)

3. **`evidence.ts` `claimSurface` subtitle — display formatting only.** The change appends `· ${factorCohort.horizon}-day hold` for non-default horizons. (`apps/frontend/lib/evidence.ts:293–304`). This is a re-format of the existing `claimSurface` helper; no new computing module and no change to how proven-ness is determined.

4. **5th `certified-claims.jsonl` entry — additive, canonical, no new endpoint.** The new entry (`vcp_contraction` D10 h60, `status=PASS`, `deflation_divisor=5`, `p_value=0.0004997501249375312 < required_p=0.010`) was written by the post-decompose gate via the existing `verify_edge` path. It carries no `signal` key and will not enter `proven_signals`. It is served verbatim by the existing `GET /api/evidence`. (`runs/goal-session-mcp-loop/state/certified-claims.jsonl` line 5)

**Result: no Data Contract violations.**

---

## Step 2 — Information Architecture Check

**New routes/pages introduced this iteration:** none.

The iteration touches two existing surfaces:
- `/research/factor-lab` — already in the blueprint IA under Research; per-horizon chip strip is an inline addition to the existing Evidence column.
- `/evidence` — already in the blueprint IA as the Evidence [NEW] nav section; the h60 claim row is an auto-rendered additive entry.

No new top-level or sub-level nav entries were added. No new pages or routes. Both surfaces are reachable in 1 click from the persistent sidebar nav (`components/sidebar.tsx` unchanged). No parallel shell introduced.

**Result: no IA violations.**

---

## Step 3 — Advisory Notes

None. No subjective coherence concerns observed. The extraction of `factorHorizonBadges` into a standalone `factor-lab-evidence.ts` module is a reasonable separation; it references only `resolveCohortEvidence` from `evidence.ts` and introduces no display drift.

---

## Summary

All Data Contract and Information Architecture checks pass. The h60 `vcp_contraction` canonical claim, the per-horizon factor-lab chip strip, and the `claimSurface` subtitle are all additive readers of the same contract value and the same serving endpoint. No objective violations.
