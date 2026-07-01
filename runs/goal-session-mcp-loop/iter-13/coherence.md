**Verdict:** COHERENCE-PASS

---

## Coherence Audit — goal-mcp-loop iter-13

**Iteration:** 13 (goal-mcp-loop-iter-13)
**Auditor:** coherence-auditor
**Date:** 2026-07-01
**Snapshot SHA:** fd4ae6d0b977b6c6379d58d96314c6bbac68acd8

---

## Step 1 — Data Contract Check

### Registered contract value audited

**Evidence status + certified-claim** (the single new value this session introduced):
- Canonical computing source: `app.engine.referee:certify_edge` via `app.mcp.tools:verify_edge`
- Canonical read-side resolver: `app.engine.evidence:build_evidence_payload` over `runs/goal-session-mcp-loop/state/certified-claims.jsonl`
- Canonical serving endpoint: `GET /api/evidence`

### Findings

**New `certified-claims.jsonl` entry (6th row):** The combination claim was appended to the EXISTING canonical
`certified-claims.jsonl` by the post-decompose gate via `verify_edge(ledger="canonical")`. The developer did
NOT hand-write the entry. This is the canonical write path. No violation.

**`resolveCombinationEvidence` in `apps/frontend/lib/evidence.ts`:** This is a new pure read-side matcher
(the multi-factor sibling of the previously accepted `resolveCohortEvidence`). It scans the served
`claims[]` from `GET /api/evidence` and re-displays `entry.proven` verbatim — it does NOT recompute
proven-ness from raw cohort data. The guard `entry.proven !== true` reads the served field; the
`combinationCohortFromClaim` + leg-key comparisons are display-routing (which row to highlight), not a
second computation of whether a claim passed the referee. This is the same display-routing pattern accepted
at iter-8 for factor cohorts. No duplicate computation.

**`fetchEvidence` call added to `CombinationLab` in `apps/frontend/app/research/_labs.tsx` (line ~1116):**
The call is `fetchEvidence(controller.signal)` imported from `lib/api.ts`, which calls
`GET /api/evidence` (canonical endpoint, `lib/api.ts:345`). This is the SAME endpoint the `/evidence` page
and the factor-lab badges use. No non-canonical source.

**`apps/frontend/app/evidence/page.tsx`:** Only a scroll `useEffect` was added (re-applies the URL hash
scroll after the async fetch resolves); no new data fetching, no new endpoint call.

**New displayed value check:** The 6th `/evidence` claim row and the `/research/factor-combination`
composite-cohort badge both display the EXISTING "Evidence status + certified-claim" contract value from
the EXISTING canonical endpoint. No new concept was introduced. No unregistered value.

**Result: No Part A violations.**

---

## Step 2 — Information Architecture Check

### New surfaces from this iteration

The iteration introduces no new pages or routes. Both affected surfaces are already in the blueprint IA:

| Route | Blueprint canonical home | Nav path | Click count |
|---|---|---|---|
| `/evidence` | J-05 canonical home (Evidence [NEW] section) | sidebar link (`components/sidebar.tsx:41`) | 1 click |
| `/research/factor-combination` | J-08 canonical home (Research section, link-reached) | sidebar → `/research` hub → `factor-combination` lab card (`lib/research-labs.ts:83`) | 2 clicks |

**`/evidence`:** listed directly in the sidebar at `components/sidebar.tsx:41` (`{ href: "/evidence", label: "Evidence", icon: ShieldCheck }`). 1 click from any page.

**`/research/factor-combination`:** reachable via the sidebar "Research" link (1st click, `sidebar.tsx:38`) → the `/research` hub grid → the "factor-combination" lab card link (`lib/research-labs.ts:83`, `href: "/research/factor-combination"`). 2 clicks total — within the ≤2 click rule.

No duplicate home: neither surface duplicates an existing home for any entity.
No parallel shell: no new layout or nav was introduced; both surfaces live inside the existing sidebar shell.
No hidden feature: the combination badge is inline on the existing composite cohort row; the 6th `/evidence`
row is additive to the existing claim list.

**Result: No Part B violations.**

---

## Step 3 — Subjective Observations (advisory only)

None. The `CombinationEvidenceBadge` component (`_labs.tsx`) mirrors the established `FactorEvidenceBadge`
pattern (same `ShieldCheck`/`Shield` icons, same "Proven"/"Not yet proven" labels, same `data-testid`
conventions, same deep-link-on-proven behavior). Visually and semantically consistent with the established
evidence badge language.

---

## Summary

| Check | Result | Notes |
|---|---|---|
| A1 — duplicate computation | PASS | `resolveCombinationEvidence` is pure read-side display routing; proven-ness flows solely from `entry.proven` (served field) |
| A2 — non-canonical source | PASS | `CombinationLab` calls `fetchEvidence` → `GET /api/evidence` (canonical endpoint, `lib/api.ts:345`) |
| A3 — new unregistered value | PASS | 6th claim row + combination badge display the existing "Evidence status + certified-claim" value; no new concept |
| B1 — no navigation path | PASS | `/evidence` (sidebar direct) + `/research/factor-combination` (Research hub → lab card) both navigable |
| B2 — reachability ≤2 clicks | PASS | `/evidence` = 1 click; `/research/factor-combination` = 2 clicks |
| B3 — duplicate home | PASS | No existing entity gets a second home |
| B4 — parallel shell | PASS | No new layout or nav introduced |
| C — advisory | PASS | No subjective issues noted |
