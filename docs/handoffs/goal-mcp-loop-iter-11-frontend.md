# goal-mcp-loop-iter-11 Frontend Handoff

**Phase:** goal-mcp-loop-iter-11
**Date:** 2026-07-01
**Agent:** developer
**Status:** complete

## What Was Built (UI)

The Research **Factor Lab** (`/research/factor-lab`) evidence marker became **per-horizon**, and the
**Evidence** ledger (`/evidence`) gained its first non-20-horizon certified-claim row — both reading the same
canonical `GET /api/evidence` payload (single source, no recompute).

### `/research/factor-lab` — per-horizon evidence chips
- The "Evidence" column (header now **"Evidence (D10 · per horizon)"**) renders a compact **chip strip** —
  one chip per served horizon `[1, 5, 10, 20, 60]` — instead of a single chip at the default horizon.
- Each chip reads `{h}d {status}`:
  - **Proven** — calm accent pill with a shield-check icon; a `<Link>` deep-linking to the backing
    `/evidence#…` row. Hover/focus states preserved; `stopPropagation()` stops the click/Enter from also
    toggling the row's decile-grid expander (iter-5 nested-interactive hazard).
  - **Not yet proven** — muted, non-interactive pill with a shield icon (no link) — the fail-safe honest
    default for every unbacked horizon.
- On the `vcp_contraction` row: **h60 → "Proven"** → `/evidence#factor-vcp_contraction-d10-h60`;
  **h20 → "Proven"** → `/evidence#factor-vcp_contraction-d10-h20` (unchanged, J-06); **h1/h5/h10 → "Not yet
  proven"**. `leadership_score` honestly reads "Proven" at h20 → `/evidence#signal-leadership_score` (a real
  PASS entry — deliberately NOT special-cased).
- Every chip carries `data-testid="factor-evidence-badge"`, `data-factor`, `data-proven`, and the new
  **`data-horizon`** so each is independently selectable by browser-qa. The chip cell also carries
  `data-testid="factor-evidence-{factorKey}"`.

### `/evidence` — new h60 claim row
- One additional certified-claim row auto-renders via the existing `ClaimRow` (no new component): title
  `vcp_contraction — top decile (D10)`, subtitle **"Out-of-sample edge — factor top decile · 60-day hold"**
  (horizon-disambiguated), hypothesis chip showing `horizon=60`, PASS, holdout **+8.91%**, SPY control
  **+8.91%**, a registration date, forward-walk "Pending", and a "Backs: Research factor lab →" linkback.
- The h20 vcp_contraction row's wording is **byte-identical** to iter-8 (J-06 non-regression).

## States Handled
- **Empty / failed `fetchEvidence`** → every chip reads "Not yet proven" with no link (fail-safe honesty; the
  claim list starts empty and stays empty on any fetch error).
- **Uncertified horizon** (h1/h5/h10) → "Not yet proven".
- **Matched-but-non-PASS** ledger entry (ma_stack FAIL) → never "Proven" at any horizon.
- **Hover / focus / active** → preserved on the "Proven" link (accent ring, surface hover).

## Design-System Conformance
- Reuses the existing `Badge` component (`accent` for proven, `default` for not-proven), `lucide-react`
  `ShieldCheck` / `Shield` icons, the `num` mono class for the horizon token, and Next.js `<Link>` — no raw
  HTML, no new visual effects, no arbitrary colors. Matches Trendora's minimal, data-dense, evidence-first,
  calm "proven / not yet proven" chip style (goal.md Design Direction).
- Layout: extends the existing data-dense factor-lab table (chip strip in the existing Evidence cell); no
  layout rewrite, no new page, no nav change.

## Files Changed (frontend)
- `apps/frontend/lib/factor-lab-evidence.ts` — NEW pure per-horizon badge resolver.
- `apps/frontend/lib/factor-lab-evidence.test.ts` — NEW (5 checks).
- `apps/frontend/app/research/_labs.tsx` — per-horizon chip strip + presentational `FactorEvidenceBadge` +
  `data-horizon` + header copy.
- `apps/frontend/lib/evidence.ts` — `claimSurface` h60 subtitle disambiguation only.
- `apps/frontend/lib/evidence.test.ts` — h60 unit coverage (27 checks).

## Tests
- `npx tsx lib/factor-lab-evidence.test.ts` → 5 passed; `npx tsx lib/evidence.test.ts` → 27 passed; full
  `lib/*.test.ts` sweep green; `npx tsc --noEmit` clean.

## Browser-QA Handoff Notes (required — Frontend Present: yes)
- Assert on `/research/factor-lab`: `[data-factor="vcp_contraction"][data-horizon="60"]` → `data-proven="true"`,
  text "Proven", href `/evidence#factor-vcp_contraction-d10-h60`; `[data-horizon="1"|"5"|"10"]` →
  `data-proven="false"`, text "Not yet proven"; `[data-horizon="20"]` → "Proven" → `…-h20` (J-06).
- **Scroll each asserted chip into the viewport before capture** — the factor-lab table is wide (17 columns);
  the evidence chip strip is in column 2 (right after Factor), so it is near the left, but confirm the target
  `vcp_contraction` row is scrolled into frame (iter-3 lesson).
- Corroborate with the `/evidence` h60 row render (same values) + the confirmed in-component deep-link.
- Regression: `/stocks` Leadership "Proven" / Entry Quality + Risk "Not yet proven" unchanged (no new inline
  badge from the signal-less h60 claim); `/evidence` still lists the prior 4 rows plus the new h60 row.
- Free port **:3255** and ensure the frontend reaches the backend (:8255) before binding.
