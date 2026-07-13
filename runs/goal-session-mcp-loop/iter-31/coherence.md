# Iteration 31 — Coherence Audit

**Iteration:** goal-mcp-loop-iter-31
**Date:** 2026-07-13
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

---

## Summary

Iter-31 ships J-19 (backlog B-902): a read-only negative-results graveyard at `/research/graveyard`
composing both certified-claims ledgers' NON-PASS verdicts. It is a textbook additive iteration —
one new composition endpoint over already-canonical reads, one new page under an already-approved
nav grouping. No Data Contract or Information Architecture violation found.

## Data Contract check

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Negative-results graveyard composition (NEW this iteration) | OK | `apps/backend/app/engine/graveyard.py:119-137` `build_graveyard_payload()` reads canonical via the EXISTING `evidence_mod.resolve_ledger_path()` (line 131, imported `app.engine.evidence as evidence_mod` at line 39) and staging via `resolve_staging_ledger_path()` (line 132) — both through the EXISTING `app.engine.ledger.read_entries` (line 40 import, called at `graveyard.py:109`). Zero new verdict/proven-ness computation: `_graveyard_row` (`graveyard.py:86-101`) re-displays `claim`/`verdict` verbatim. Registered in `runs/goal-session-mcp-loop/state/blueprint.md`'s Data Contract table (row "Negative-results graveyard composition") and the iter-31 clarification paragraph (blueprint.md:250) in the SAME commit that builds it — not an unregistered value. |
| Registration lineage matching | OK | `graveyard.py:42` imports `match_registration` from the EXISTING `app.engine.registry` and calls it verbatim at `graveyard.py:100` — no second selector-matcher. Confirmed `app.engine.registry.py` still owns `_CLAIM_SELECTOR_KEYS`/`match_registration`/`claim_selectors` (grep confirmed, unmodified this iteration). A new drift-insurance test (`apps/backend/tests/test_registry.py:66-67`) asserts `registry_mod._CLAIM_SELECTOR_KEYS == mcp_tools._CLAIM_SELECTOR_KEYS` — hardens the single-matcher invariant, does not weaken it. |
| Evidence status / certified-claim ("Proven"/"Not yet proven", `proven_signals`) | OK — untouched | Not read or written anywhere in the new code. `graveyard.py` never imports `build_evidence_payload` or touches `proven_signals`; the frontend graveyard page (`apps/frontend/app/research/graveyard/page.tsx`) never calls `fetchEvidence`. Verdict badges on the new page render only `FAIL`/`INSUFFICIENT` via `verdictKindVariant` (`page.tsx:152-156`), which maps to the SAME `danger`/`warn` variants `apps/frontend/app/evidence/page.tsx:29-32`'s `verdictVariant` uses for these two statuses (grep-confirmed) — consistent styling, and `accent` (the "Proven" color) is structurally unreachable since the backend already filters PASS out (`graveyard.py:112-114`). |
| Ledger origin tag / deflation context | OK | Re-displayed verbatim: `_graveyard_row` tags `ledger` (canonical/staging, `graveyard.py:93`) and passes `verdict` through unmodified (`graveyard.py:99`); the frontend's `DeflationLabel` (`page.tsx:205-216`) reads `verdict.deflation`/`verdict.deflation_divisor` directly with no recomputation. |
| "Permanent" marking (closed registrations) | OK | `page.tsx:159` `entry.lineage?.status === "closed"` — reads the already-canonical registry row's `status` field verbatim; not a new computation. |
| Staging ledger "internal-only" invariant | OK — documented, honest narrowing | Blueprint iter-31 clarification (blueprint.md:250) explicitly narrows the iter-9/10/12 "staging never served" rule and states the preserved honesty fence (staging carries 0 PASS; `/evidence`/`proven_signals` stay byte-identical). Code matches: `graveyard.py` never writes either ledger (no `append_entry` import), and the graveyard filters to non-PASS only (`graveyard.py:112-114`), so no staging edge can ever render as proven. |

No new function/endpoint computes any existing registered value (scores, regime, sectors, themes,
forward-return evidence, index/vendor data, DB capacity, or the registry) independently of its
canonical source. No new UI surface fetches a registered value from a non-canonical endpoint.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/research/graveyard` (new page) | OK | Blueprint IA table row "J-19 ... `/research/graveyard` (graveyard table — hub-reached in ≤2 clicks under the Research governance grouping)" (`blueprint.md:86`) names this exact canonical home. `apps/frontend/components/sidebar.tsx:38` still lists `{ href: "/research", label: "Research", icon: Microscope }` unchanged (not in this iteration's diff). `apps/frontend/app/research/page.tsx` diff adds ONE new `<Link data-testid="research-governance-link-graveyard">` (lines 102-120 of the diff) inside the SAME EXISTING `data-testid="research-governance"` grid that already held the iter-30 registry card — no new grid, no new section. Path: Dashboard → sidebar "Research" (click 1) → `/research` hub → governance card (click 2) → `/research/graveyard`. 2 clicks, matches the spec's own "≤2 clicks" requirement and the same pattern `/research/registry` already uses. |
| Page shell (no parallel layout) | OK | `apps/frontend/app/research/graveyard/` contains only `page.tsx` (verified via `ls`) — no local `layout.tsx`. The only layout file under `apps/frontend/app` is the single root `app/layout.tsx` (verified via `find`); no `app/research/layout.tsx` exists either, so every Research sub-page — including the new one — inherits the one shared shell. `GraveyardPage` composes existing shared components only (`PageHeading`, `Card`, `CardContent`, `Badge`), mirroring `research/registry/page.tsx`'s shape exactly per the spec's own instruction. |
| Duplicate-home check | OK — no duplication | The graveyard shows only NON-PASS verdicts (FAIL/INSUFFICIENT); `/evidence` shows only the PASS-derived proven-ness value; `/research/registry` shows registration rows regardless of verdict. Three distinct entities, three distinct canonical homes — no second page for an entity that already has one. |
| `apps/backend/main.py` router wiring | OK | Additive two-line change (`graveyard` import + `include_router(graveyard.router, prefix="/api")`, diff lines 17-30) — no existing route touched, no path collision (`GET /api/research/graveyard` is a new, unique path). |
| `/research/registry` anchor addition | OK — presentation-only, not a new route | The `id={`registration-${row.id}`}` + `scroll-mt-20` addition (diff lines 153-163) and the deep-link `useEffect` (diff lines 128-148) let the graveyard's Lineage link land on the exact registry row. This is a same-page enhancement of the EXISTING registry route, not a new page and not a nav change; plain (non-anchor) browsing is unaffected per the diff (only a `key`/`id`/`className` addition to the existing `<tr>`). |

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- None rising to WARN. (For context, not a coherence matter: the ux-regression-reviewer flagged the
  Lineage link's client-side-navigation scroll behavior as broken in its initial pass; the fix — the
  `useEffect` in `apps/frontend/app/research/registry/page.tsx:43-58` — is already present in the
  diff under audit here (applied by the auditor per `docs/handoffs/goal-mcp-loop-iter-31-audit.md`
  finding F1), so the code state this gate is auditing already reflects the fix. This was always a
  functional/UX concern, not a Data Contract or Information Architecture one, and does not affect
  this verdict.)
