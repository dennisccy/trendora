**Verdict:** COHERENCE-PASS

## Coherence Audit — goal-mcp-loop-iter-15

**Session:** mcp-loop  
**Iteration:** 15 (goal-mcp-loop-iter-15)  
**Snapshot SHA:** 80511e2d961398ae55ef19bbc3abab928410d07c  
**Audited:** 2026-07-01

---

## Step 1 — Data Contract Check

**Registered contract value under audit:** Evidence status + certified-claim (the single new value this session introduces), served by `GET /api/evidence`, computed by `app.engine.referee:certify_edge` / `app.engine.evidence:build_evidence_payload` over `app.engine.ledger:read_entries(certified-claims.jsonl)`.

### Files changed this iteration (tracked diff)

| File | Nature |
|---|---|
| `runs/goal-session-mcp-loop/state/certified-claims.jsonl` | Data row 7 appended (rs_spy_3m D10 h60, PASS, Bonferroni divisor 7) by the post-decompose gate |
| `apps/backend/tests/test_evidence.py` | Test-only: golden-fixture refreshed from 6 to 7 entries; no `app/**` source change |
| `apps/backend/tests/test_staging_ledger_routing.py` | Test-only: live-canonical count assertions updated 6 → 7; no `app/**` source change |
| `apps/frontend/lib/evidence.test.ts` | Test-only: new J-09 unit cases (ee, ff) + negative-case (o) reconciled; no `lib/**` source change |
| `runs/goal-session-mcp-loop/state/blueprint.md` | J-09 row added to IA table; iter-15 clarification paragraph added to Data Contract — both additive, not contract-altering |

No source files under `app/` or `apps/frontend/lib/` (excluding tests) were modified. The UI surface map confirms: "Modified components: 0 (no source code edited; behavior changed via new data in the ledger)."

### Duplicate computation check

No new function computing proven-ness was introduced. The existing `resolveCohortEvidence` in `apps/frontend/lib/evidence.ts` (unmodified) now matches the rs_spy_3m h60 entry purely because the canonical ledger gained a row — general matcher, no factor-specific branch (the spec explicitly forbids one; iter-8 lesson). `proven_signals` stays `{leadership_score}` as verified by the updated `test_canonical_ledger_frozen_golden` assertion at `apps/backend/tests/test_evidence.py:641` and the frontend `(ff)` check that `resolveEvidenceStatus("leadership_score", {}).proven` is false against the 7-entry fixture.

**No duplicate computation violation.**

### Non-canonical source check

The new UI behavior — the 7th row on `/evidence` and the rs_spy_3m h60 "Proven" badge on `/research/factor-lab` — flows from the existing `GET /api/evidence` endpoint, the existing `lib/api.ts:fetchEvidence` client, and the unchanged per-horizon `resolveCohortEvidence` reader. No new endpoint was introduced. No client-side recomputation of proven-ness occurs.

**No non-canonical source violation.**

### New displayed values

The 7th certified-claim row displayed on `/evidence` and the "Proven" chip on the factor-lab `rs_spy_3m` h60 cell are new DATA INSTANCES under the existing "Evidence status + certified-claim" contract value — not a new value type. The iter-15 clarification in the blueprint correctly registers this as "one more reader position of the same contract value." The new value is not a synonym or re-derivation of any other registered contract row.

**No unregistered-value issue.**

---

## Step 2 — Information Architecture Check

**New pages/routes introduced:** 0 (confirmed by UI surface map).

The two changed UI surfaces are:

| Surface | IA canonical home | Reachable in ≤2 clicks |
|---|---|---|
| `/evidence` — 7th `ClaimRow` (rs_spy_3m D10 h60) | `Evidence [NEW]` — registered in sidebar nav skeleton | Yes: sidebar link (1 click) |
| `/research/factor-lab` — rs_spy_3m h60 chip | `Research` (lab, link-reached) | Yes: sidebar `Research` (1 click) → `factor-lab` (inline tab/link, 2 clicks) |

Both homes are established IA entries — no new section, no parallel shell, no duplicate home. The J-09 row is explicitly registered in the blueprint's feature/journey homes table.

**No navigation path violation. No duplicate home. No parallel shell.**

---

## Step 3 — Subjective observations (advisory)

One data-quality observation that falls outside the coherence-auditor's hard rules, noted for the phase auditor who also scrutinizes this iteration:

- **Yellow-flag holdout edge:** the new ledger row carries `holdout_edge = control_excess = 0.21344270202534893` (+21.34%), and both fields are equal. The spec, the blueprint's iter-15 clarification, and the iteration notes all flag this as "implausibly large" and direct the phase auditor + closure gate to scrutinize it. The coherence-auditor's scope is limited to whether the value is served from the canonical source and displayed verbatim — it is (anti-goal #3). The statistical reasonableness of the edge is the domain of the post-decompose gate (which already returned PASS at divisor 7, p=0.0004998) and the phase/closure auditors. No coherence WARN issued.

---

## Summary

| Check | Result | Evidence |
|---|---|---|
| Duplicate computation of evidence status | None found | No new `certify`, `resolve`, or `proven` functions in diff |
| Non-canonical source for evidence status | None found | All reads go through existing `GET /api/evidence` / `fetchEvidence` |
| New unregistered value type | None | 7th row is a data instance under the existing contract value |
| `proven_signals` still `{leadership_score}` | Confirmed | `test_evidence.py:641`; frontend check `(ff)` |
| New pages/routes | 0 | UI surface map; git diff |
| All new surfaces in IA-canonical homes | Yes | `/evidence` + `/research/factor-lab` both in nav skeleton |
| Nav reachability ≤2 clicks | Yes | Both in existing sidebar links |
| Duplicate home for any entity | None | No second page for any existing entity |
| Parallel shell | None | No new layout/nav introduced |
