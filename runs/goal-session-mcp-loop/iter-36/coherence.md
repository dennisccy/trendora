# Iteration 36 — Coherence Audit

**Iteration:** goal-mcp-loop-iter-36
**Date:** 2026-07-15
**Written by:** coherence-auditor

---

**Verdict:** COHERENCE-PASS

<!-- COHERENCE-PASS: no objective violations; at most minor advisory notes -->

---

## Data Contract check

Iter-36 registers exactly ONE new Data Contract value (blueprint.md, `## Data Contract` table + the
iter-36 clarification note appended at the bottom) — the **referee-audit report**. Verified against the
diff (snapshot `1a46053`..working tree) and the code:

| Value / entity | Result | Evidence (file:line) |
|---|---|---|
| Referee-audit report (null-trial count; empirical false-pass rate + binomial CI; α; contaminated-factor verdict; run date + params) | OK | Computed once by `build_referee_audit_report()` / orchestrated by `run_referee_audit()` in `apps/backend/app/engine/referee_audit.py:234-371`; persisted/read by the sole pair `write_referee_audit_report()` / `read_referee_audit_report()` (`referee_audit.py:141-170`); served by the ONE new endpoint `GET /api/research/referee-audit` (`apps/backend/app/api/referee_audit.py:26-31`, which calls only `read_referee_audit_report()`); the ONE reader is `apps/frontend/app/research/referee-audit/page.tsx:38` (`fetchRefereeAudit()` → `lib/api.ts:425-217` → that one endpoint, no client recompute). Grepped for a second binomial-CI / Wilson-interval implementation anywhere else in `apps/backend/app/` — none found (`binomial_ci` is unique to this module). |
| Evidence status / certified-claim (existing contract row) | OK — untouched | `certified-claims.jsonl` / `staging-ledger.jsonl` / `pre-registrations.jsonl` show **zero diff** vs the snapshot SHA (`git diff 1a46053 --stat` on all three paths returns empty). `referee_audit.py` never imports or calls `evidence.resolve_ledger_path()`, `graveyard.resolve_staging_ledger_path()`, or `app.mcp.tools.verify_edge` (grepped — only doc-comment mentions of those names, no call sites); every null/contaminated trial runs `referee.certify_edge()` directly against a fresh `RefereeState` and an explicit **throwaway** `ledger_path` (`referee_audit.py:130-138, 292-360`). The isolation claim in the blueprint's iter-36 clarification is verified true, not just asserted. |
| Other existing rows (scores, regime, sectors, themes, forward-return, research cohorts, registry, graveyard, budget, preflight, drift) | OK — untouched | None of their computing modules (`scoring.py`, `regime.py`, `sectors.py`, `themes.py`, `forward_testing.py`, `research.py`, `registry.py`, `graveyard.py`, `budget_accounting.py`, `readiness.py`, `drift.py`) or endpoints appear in the diff at all. |

No duplicate computation, no non-canonical source, no unregistered value.

## Information Architecture check

| Feature / route | Result | Evidence (nav file inspected) |
|---|---|---|
| `/research/referee-audit` (new page) | OK | Blueprint IA row (`blueprint.md:90`, added this iteration) already names this exact route as J-22's canonical home, "hub-reached in ≤2 clicks under the Research 'Governance & process' grouping" — matching the pre-approved iter-30 governance-grouping precedent (registry/graveyard/budget). Verified statically: `apps/frontend/components/sidebar.tsx:38` has the persistent top-level `{ href: "/research", label: "Research" }` link (click 1) → `apps/frontend/app/research/page.tsx:156-175` adds a new `<Link href={asofHref("/research/referee-audit")} data-testid="research-governance-link-referee-audit">` card inside the existing "Governance & process" grid (click 2). No nav-skeleton change: the sidebar array is untouched by this diff (only `research/page.tsx`, `lib/api.ts`, `config.py`, `main.py`, `config.yaml`, `README.md` changed — no `sidebar.tsx` hunk). |
| `/research` "Governance & process" grouping | OK — no duplicate/parallel shell | The new card is appended inside the SAME existing grid div (`research/page.tsx:145-147`) alongside registry/graveyard/budget, not a new section; the new page itself (`referee-audit/page.tsx`) uses the standard site chrome (`PageHeading`, `Card`, `useAsOfHref`, the ordinary `<div className="space-y-4">` body) — same shell every sibling governance page uses, no independent layout/nav invented. |

No hidden feature, no >2-click surface, no duplicate home, no parallel shell.

## Blocking violations (FAIL only)

None.

## Advisory notes (non-blocking)

- `README.md`'s `<!-- AUTO:capabilities -->` block was touched this iteration (two bullets — Data Manager,
  Daily preflight banner — picked up drift/J-21 wording) but no new bullet was added for the "Referee
  audit" governance card built in this same iteration, unlike every prior governance-cluster iteration
  (registry/graveyard/budget each got a README bullet the iteration they shipped). Cosmetic/documentation
  gap only — outside this gate's IA/Data-Contract scope (the README is not part of the blueprint's nav
  skeleton or Data Contract) and does not affect app coherence; flagging for the readme-maintainer pass to
  pick up.
- `referee-audit/page.tsx:149-153` defines a local `contaminatedStatusVariant()` badge-color mapper whose
  doc-comment says it "mirrors `research/graveyard/page.tsx`'s `verdictKindVariant` mapping." The two
  functions are intentionally NOT shared (graveyard's `verdictKindVariant` is a private, unexported
  function at `graveyard/page.tsx:152`, and the semantics genuinely differ — PASS maps to `danger` here
  because a PASS on the contaminated factor is the alarming tripwire case, whereas graveyard never sees a
  PASS at all). Not a Data Contract violation (no canonical value is computed here — it's a local
  display-color helper, not a registered value), just a minor missed-reuse opportunity if a third governance
  page ever needs the same status-badge pattern.
