**Verdict:** COHERENCE-PASS

## Iteration audited

Session: mcp-loop / Iteration: 2 / Name: goal-mcp-loop-iter-2

Snapshot SHA: 36d48720c4055f57cc5861e8f4cc1d83a92c92ab

Files changed (tracked + untracked):
- `apps/backend/app/engine/evidence.py` — added `_resolve_signal()` helper
- `apps/backend/tests/test_evidence.py` — test additions
- `apps/frontend/app/stocks/[ticker]/page.tsx` — imports `ScoreProofPanel` + `SCORE_SIGNALS`
- `apps/frontend/app/stocks/page.tsx` — imports `SCORE_SIGNALS` (replaces local duplicate)
- `apps/frontend/lib/evidence.ts` — added `SCORE_SIGNALS`, `proofFieldsFor`, `ProofFields`, `formatEvidencePct`, `formatPValue`
- `apps/frontend/lib/evidence.test.ts` — tests for above additions
- `apps/frontend/components/score-proof-panel.tsx` — new component (untracked, created this iteration)
- `runs/goal-session-mcp-loop/state/blueprint.md` — iter-2 clarification note added (additive)
- `runs/goal-session-mcp-loop/state/certified-claims.jsonl` — first certified entry written by gate

---

## Step 1 — Data Contract

Blueprint contract row 1: **Evidence status + certified-claim** computed by `app.engine.evidence:build_evidence_payload` / `app.engine.referee:certify_edge`, served by `GET /api/evidence` exclusively.

**Findings — no violations.**

1. `apps/backend/app/engine/evidence.py:69` — new `_resolve_signal(claim)` function. This is a module-private display-routing helper: it derives the UI signal key for a score-column factor cohort that omits an explicit `signal` field on the written claim. Proven-ness is unchanged — it flows 100% from `verdict.status == "PASS"` in the ledger. The blueprint's Data Contract row-1 iter-2 clarification explicitly documents this as "display-routing, not a second computation." Not a duplicate computation of evidence status.

2. `apps/frontend/lib/evidence.ts:148` — new `proofFieldsFor(signal, provenSignals)` function. It calls `resolveEvidenceStatus`, which reads `claim.proven` from the `provenSignals` map passed in. The `provenSignals` map originates from a fetch of `GET /api/evidence` (the canonical endpoint) in the parent page component. No new fetch, no recomputation of proven-ness. Values are read verbatim from the served map.

3. `apps/frontend/lib/evidence.ts:175–200` — `formatEvidencePct` and `formatPValue`. Display-only formatters. Re-format served numeric fields for presentation; they do not compute any registered value.

4. `apps/frontend/components/score-proof-panel.tsx:42` — `ScoreProofPanel` calls `proofFieldsFor(signal, provenSignals)` where `provenSignals` is passed in from the stock-detail page (already fetched from `GET /api/evidence`). The component comment explicitly states "It FETCHES NOTHING and RECOMPUTES NOTHING." Confirmed by code inspection.

5. `SCORE_SIGNALS` constant — previously duplicated identically in `apps/frontend/app/stocks/page.tsx` and `apps/frontend/app/stocks/[ticker]/page.tsx`; consolidated into `apps/frontend/lib/evidence.ts` and both pages now import from there. This is a coherence improvement (eliminates a latent duplicate-definition risk), not a new computation.

---

## Step 2 — Information Architecture

Blueprint IA: `/stocks/{ticker}` is the canonical home for J-02 (badge → proof panel). `/evidence` is the canonical home for J-05. Sidebar nav has `{ href: "/stocks" }` (1 click) and `{ href: "/evidence" }` (1 click).

**Findings — no violations.**

1. `ScoreProofPanel` lives on `/stocks/{ticker}` — the blueprint's explicit J-02 canonical home. Reachable via `Stocks` sidebar link (1 click) → click any stock row (2 clicks). Within the ≤2-click budget.

2. No new top-level routes or pages were introduced. The J-02 proof panel is an in-place expandable element on an existing page.

3. No duplicate home: there is no pre-existing proof-drill component for the same entity.

4. No parallel shell: `ScoreProofPanel` renders inside the existing `ScoreCard` layout on the stock-detail page.

5. `/evidence` (J-05) — existing page with sidebar link. State-only change (populated claim row now that the ledger has its first certified entry). No structural change.

6. Sidebar inspection: `apps/frontend/components/sidebar.tsx` line 33 confirms `/stocks` link; line 41 confirms `/evidence` link. Both are reachable in 1 click from any page.

---

## Step 3 — Advisory observations (WARN only)

None. No label inconsistencies, formatting drift, or reachability concerns observed.

---

## Summary

Both the Data Contract (no duplicate computation, no non-canonical source for any registered value) and the Information Architecture (no hidden features, no duplicate homes, no parallel shells) are clean. The `SCORE_SIGNALS` deduplication and the `_resolve_signal()` defense-in-depth are coherence improvements documented in the blueprint.
