# Iteration 8 — Coherence Audit

**Iteration:** goal-mcp-loop-iter-8
**Date:** 2026-06-30
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Data Contract check

The blueprint's Data Contract registers one canonical evidence value for this session:

- **Evidence status + certified-claim**: written by `app.engine.referee:certify_edge` via `app.mcp.tools:verify_edge`; read by `app.engine.evidence:build_evidence_payload`; served exclusively via `GET /api/evidence`.

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Evidence status + certified-claim (vcp_contraction D10 h20 PASS entry) | OK | `runs/goal-session-mcp-loop/state/certified-claims.jsonl` line 4 — appended by the post-decompose gate (the canonical writer), no new compute path |
| `resolveCohortEvidence` — factor-lab badge display helper | OK | `apps/frontend/lib/evidence.ts` — pure read of served `entry.proven`; reads `GET /api/evidence` via the existing `fetchEvidence()` client (`apps/frontend/lib/api.ts:344`); never recomputes proven-ness |
| `FactorEvidenceBadge` on `/research/factor-lab` | OK | `apps/frontend/app/research/_labs.tsx` — fetches via `fetchEvidence()` (same canonical endpoint, no new fetch path); resolves status via `resolveCohortEvidence` which is a pure matcher over the served `claims[]` |
| `ClaimRow` anchor update on `/evidence` | OK | `apps/frontend/app/evidence/page.tsx` — replaces inline `signal ? signal-${signal} : undefined` with `claimAnchorId(claim)` (same logic, shared helper); display-routing only, no value recomputed |
| `claimAnchorId`, `cohortClaimId`, `cohortEvidenceAnchor`, `factorCohortFromClaim` helpers | OK | `apps/frontend/lib/evidence.ts` — display-routing helpers; read `claim.claim` selectors verbatim, never derive proven-ness independently |

No duplicate computation. No non-canonical source. The vcp_contraction claim carries no `signal` key, consistent with the blueprint's iter-8 clarification and the Data Contract requirement that it must not enter `proven_signals` nor light a per-stock score badge.

The new value displayed on the factor lab (a "Proven"/"Not yet proven" badge per factor's top-decile cohort) is an additional reader of the already-registered `GET /api/evidence` payload; it is not a new conceptual value — it is the same evidence status re-displayed on a new surface, which the blueprint explicitly anticipates and permits.

## Information Architecture check

No new pages or routes were introduced this iteration. Both affected surfaces are existing canonical homes registered in the blueprint's IA.

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/research/factor-lab` — new Evidence column + `FactorEvidenceBadge` | OK | `apps/frontend/components/sidebar.tsx` (unchanged by this diff); Research is a top-level nav link; factor-lab is row/link-reached within Research — 2 clicks. No nav change. |
| `/evidence` — new 4th claim row (vcp_contraction) + updated `ClaimRow` anchor | OK | Evidence is a top-level sidebar link — 1 click. No nav change. |

No new pages. No parallel shell. No duplicate home. No nav-skeleton change. The blueprint's J-06 row explicitly assigns `/research/factor-lab` and `/evidence` as J-06's canonical homes — both already existed and remained unchanged.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

None. The `FactorEvidenceBadge` component follows the same visual pattern as the existing `EvidenceStatusBadge` (ShieldCheck/Shield icon, accent/default variant, identical text labels), so there is no formatting drift across surfaces.
