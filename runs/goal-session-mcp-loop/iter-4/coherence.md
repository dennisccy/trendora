**Verdict:** COHERENCE-PASS

## Coherence Audit — goal-mcp-loop iter-4

**Session:** mcp-loop | **Iteration:** 4 | **Iter name:** goal-mcp-loop-iter-4
**Audited diff:** `git diff 9b770ce6b3ce5c81f3366d58adab3433662a1c46` (+ uncommitted working-tree changes)

---

## Files changed this iteration

| File | Nature |
|---|---|
| `apps/frontend/lib/evidence.ts` | Added `regimeLabel` + `claimSurface` display helpers |
| `apps/frontend/app/evidence/page.tsx` | `ClaimRow` updated to use new helpers; local `surfaceForSignal` removed |
| `apps/frontend/app/page.tsx` | `RegimeGlanceCard` gains a Dashboard → `/evidence` affordance link |
| `apps/frontend/lib/evidence.test.ts` | Unit tests for new helpers |
| `apps/backend/tests/test_evidence.py` | Backend regression test for 2-entry ledger; no app source changed |
| `runs/goal-session-mcp-loop/state/certified-claims.jsonl` | 2nd ledger entry appended (Breakout-watch × Risk-on PASS) |
| `runs/goal-session-mcp-loop/state/blueprint.md` | J-04 row text tightened; iter-4 clarification appended |

No backend application source (`apps/backend/app/**`) was changed.

---

## Step 1 — Data Contract check

**Registered canonical value at issue:** Data Contract row 1 — "Evidence status + certified-claim",
computed by `app.engine.referee:certify_edge`, served by `GET /api/evidence`.

### 1a — No duplicate computation

`apps/frontend/lib/evidence.ts` introduces two new exported functions:

- `regimeLabel(claim)` — reads `claim.claim.regime` verbatim from the `CertifiedClaim` object (i.e.,
  from what `GET /api/evidence` already serves). Returns a trimmed string or `null`. No arithmetic,
  no scoring, no proven-ness decision.

- `claimSurface(claim)` — maps claim attributes (signal, kind, subject, regime) to display strings
  (title, subtitle, linkback href/label). Replaces the local `surfaceForSignal` that was previously
  inlined in `apps/frontend/app/evidence/page.tsx`. Both old and new functions are pure display
  routing; neither computes proven-ness. The refactor moves the logic to a shared module and extends
  it to handle signal-less event-study cohorts honestly.

Neither function independently computes proven-ness. `resolveEvidenceStatus` (the pre-existing
canonical status resolver in `evidence.ts`) is unchanged and still the only code that decides
"Proven" / "Not yet proven". No second computation of any registered value.

### 1b — No non-canonical source

`apps/frontend/app/evidence/page.tsx` `ClaimRow` now calls `claimSurface(claim)` and `regimeLabel(claim)`.
Both receive the `CertifiedClaim` object fetched from `GET /api/evidence` (via `fetchEvidence` / `useEffect`
already in the component — unchanged call site). No new endpoint called, no client-side re-derivation of
proven-ness, no data fetched from a second source.

`apps/frontend/app/page.tsx` `RegimeGlanceCard` gains a `<Link href="/evidence">` — a navigation
affordance only. It reads no data from any endpoint; it does not display any registered value.

### 1c — New ledger entry (same Data Contract row 1, not a new value)

The second certified-claims entry (Breakout-watch × Risk-on event-study, appended by the post-decompose
gate) is an additional record of the same "Evidence status + certified-claim" concept already registered
in row 1. The blueprint's iter-4 clarification (added in this diff) explicitly records this and confirms:
signal-less regime cohorts appear only in `claims[]`, never in `proven_signals`. The backend unit test
`test_build_payload_regime_event_study_claim_adds_no_signal` in `apps/backend/tests/test_evidence.py`
asserts `list(payload["proven_signals"].keys()) == ["leadership_score"]` over the 2-entry ledger — no
second proven signal introduced. This is read-verbatim re-display, not a new computing module.

**Data Contract: no violations.**

---

## Step 2 — Information Architecture check

New UI surfaces this iteration (per the surface map):
- `/evidence` — `ClaimRow` component updated (existing page, existing nav entry)
- `/` — `RegimeGlanceCard` component updated (existing page, existing nav entry)

### 2a — Navigation path

`apps/frontend/components/sidebar.tsx` line 41:
```
{ href: "/evidence", label: "Evidence", icon: ShieldCheck },
```
`/evidence` is a first-level sidebar entry (1 click from anywhere in the app). Already established in
iter-1. No new route was added; no nav change was made.

`/` (Dashboard) is the root path — always reachable.

Both modified surfaces are established nav destinations. No missing nav path.

### 2b — Reachability

`/evidence` — 1 click (sidebar). `/` — 1 click (sidebar). Both within the 1-click bound. The new
Dashboard → `/evidence` link is a within-page affordance that creates a 2-click path (Dashboard → link
→ Evidence) explicitly sanctioned by J-04's blueprint home row.

### 2c — No duplicate home / no parallel shell

No new pages or routes introduced. `ClaimRow` on `/evidence` and the affordance link in `RegimeGlanceCard`
are additive modifications to existing pages inside the established sidebar shell. No second `/evidence`
page. J-04's canonical home (`/` + `/evidence`) matches exactly where the changes land.

**Information Architecture: no violations.**

---

## Step 3 — Advisory observations

No advisory (WARN) items warranting note. The `claimSurface` fallback path for unrecognized signal-less
cohorts preserves the pre-iter-4 "Unmapped signal" + Stocks leaderboard behavior — defensive, consistent
with prior behavior, and no such cohort exists in the current ledger. The linkback to `/research/event-study`
targets an existing Research lab route within the established IA (blueprint: "Research → /research → labs
(factor, event-study, regime, …)").

---

## Summary

| Check | Result |
|---|---|
| Data Contract row 1 — no duplicate computation | PASS |
| Data Contract row 1 — no non-canonical source | PASS |
| New ledger entry — same value, same endpoint | PASS |
| `/evidence` nav path | PASS (sidebar, 1 click) |
| `/` (Dashboard) nav path | PASS (sidebar, 1 click) |
| J-04 canonical home followed | PASS |
| No new pages without nav | PASS |
| No parallel shell | PASS |
| No duplicate home | PASS |
