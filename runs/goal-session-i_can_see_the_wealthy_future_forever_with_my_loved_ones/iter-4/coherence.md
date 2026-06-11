**Verdict:** COHERENCE-PASS

## Coherence Audit — Iteration 4 (J-47 Glossary + Inline Tooltips)

**Session:** i_can_see_the_wealthy_future_forever_with_my_loved_ones
**Iteration index:** 4
**Snapshot SHA:** a03b4460d56a87745c1166405d218c28b814df85
**Audited files:** 14 changed (12 modified + 2 untracked key files)

---

### Step 1 — Data Contract check

The registered Data Contract row for J-47 is:
> Setup & pattern catalog → `methodology:build_catalog(config)` → `GET /api/methodology`

**Audit findings (no violations):**

1. **No new endpoint.** The glossary is assembled by a new private helper `_glossary()` in
   `apps/backend/app/engine/methodology.py` (line 80) called exclusively from `build_catalog` — the
   same function that already populates the `GET /api/methodology` payload. No new router, no new
   endpoint, no second serving path.

2. **Frontend reads the single canonical endpoint.** `apps/frontend/lib/glossary.tsx` (`GlossaryProvider`)
   calls `fetchMethodology()` from `apps/frontend/lib/api.ts:797` which is the existing
   `GET /api/methodology` fetch. The `GlossaryProvider` is mounted once in the app shell
   (`apps/frontend/app/layout.tsx:22`) and distributes the result via React Context. Every surface that
   renders `<TermInfo>` reads the shared context — no independent fetch, no second endpoint call, no
   client-side recomputation of any value.

3. **Methodology page does not re-fetch.** `apps/frontend/app/methodology/page.tsx` already fetches
   `fetchMethodology()` for the existing setup/pattern catalog; the new `GlossarySection` consumes
   `state.data.glossary` from the SAME response object — not a second fetch.

4. **Setups & Patterns are derived, not re-described.** `_glossary()` in `methodology.py` projects the
   existing `methodology.entries` into the Setups & Patterns glossary category (setting `entry_key`,
   `kind`, and copying `entry.meaning` verbatim) — no second copy, no independent re-description.
   Boot validation in `config.py:_glossary_terms_well_formed` rejects any authored term colliding with
   an entry key or name.

5. **No new canonical numeric value introduced.** 109 authored terms in `config.yaml` are plain-language
   definitions. Where a threshold is cited it uses the existing `ref` mechanism (`Config._methodology_refs_resolve`)
   — never a re-typed literal. No scoring/regime/forward-testing values are computed client-side or
   duplicated.

6. **No magic numbers.** Every threshold referenced in a glossary entry (`config.yaml`) uses a `ref`
   path; `config.py:resolve_ref` resolves them live at boot from the canonical Config tree.

**KEY CHECK (J-47 special requirement):** Glossary and tooltips both read `GET /api/methodology`
exclusively — `glossary.tsx` shares a single `fetchMethodology()` call with the methodology page via
the app-shell `GlossaryProvider`. No second catalog, no hardcoded definition anywhere in the diff or
the new untracked files.

---

### Step 2 — Information Architecture check

**New pages/routes in this iteration:** NONE.

The diff touches only **existing** pages and components:
- `/methodology` — glossary section added below the existing setup/pattern catalog
- `/backtest`, `/research`, `/stocks`, `/` (dashboard), `/data` — `<TermInfo>` markers added to
  existing headers and stat labels

**Navigation check:** `/methodology` is linked from the sidebar at
`apps/frontend/components/sidebar.tsx:38` (`{ href: "/methodology", label: "Methodology", icon: BookOpen }`).
Reachable in 1 click from every page — no change to the nav was made or needed.

**No new home, no duplicate home, no parallel shell.** The blueprint's IA entry for `/methodology`
already annotates "J-47 full Glossary [TARGET — iter-4 in flight]"; the implementation places the
Glossary section in exactly that home.

---

### Step 3 — Subjective observations (advisory only)

No advisory issues identified. The implementation is consistent with the established patterns
(`InfoTooltip` wrapper, dark analytical workstation style, catalog-driven labels).

---

### Summary

| Rule | Finding |
|------|---------|
| Data Contract: duplicate computation | NONE |
| Data Contract: non-canonical source | NONE |
| Data Contract: unregistered value | NONE (glossary entries are presentation copy, not new computed values) |
| IA: no navigation path | NONE |
| IA: undiscoverable (>2 clicks) | NONE |
| IA: duplicate home | NONE |
| IA: parallel shell | NONE |

All checked against the blueprint contract and the iteration diff. No objective violations found.
