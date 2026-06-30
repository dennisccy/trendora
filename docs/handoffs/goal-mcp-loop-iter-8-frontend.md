# goal-mcp-loop-iter-8 Frontend Handoff

**Phase:** goal-mcp-loop-iter-8
**Date:** 2026-06-30
**Agent:** developer
**Status:** complete

## What Was Built (UI)

- **Research factor lab — new "Evidence (D10 · 20d)" column.** Every factor's summary row now shows a calm
  evidence chip for its top-decile cohort at the certified horizon. **vcp_contraction → "Proven"** (accent
  chip with a ShieldCheck icon, deep-links to its `/evidence` ledger row); every unbacked factor — including
  the FAIL'd **ma_stack** — reads **"Not yet proven"** (muted chip with an outline Shield, no link). The chip
  re-displays the served evidence status via the pure `resolveCohortEvidence` matcher; it computes nothing.
  Score-column factors that are also lab rows (e.g. **Leadership score**) honestly read "Proven" too and link
  to their real `signal-…` ledger row.
- **`/evidence` — new vcp_contraction claim row.** Renders the same five fields as existing rows
  (Hypothesis chips, Out-of-sample verdict with "holdout edge +3.33%", Control vs SPY, Registration date,
  Forward-walk score-to-date), an honest title `vcp_contraction — top decile (D10)`, an honest subtitle
  `Out-of-sample edge — factor top decile`, and a **"Backs: Research factor lab →"** linkback. The
  ma_stack FAIL cohort is also audit-listed (PASS badge → FAIL badge) with the same factor framing.
- **Round-trip navigation.** Factor-lab "Proven" badge → `/evidence#factor-vcp_contraction-d10-h20`
  (the matching row id); the `/evidence` row's "Backs: Research factor lab →" → `/research/factor-lab`.

## Visual / Design

- Reused the existing `Badge` token (accent for "Proven", `default` + faint text for "Not yet proven") with
  the `ShieldCheck`/`Shield` lucide icons — mirrors `components/evidence-status-badge.tsx`. No new
  design-system component; `FactorEvidenceBadge` is a local component in `_labs.tsx`.
- Existing `Card`/table layout, existing `Link` style (`text-accent hover:underline focus-visible:ring-1`).
  No new pages, no nav change, no new visual effects. Framing is historical out-of-sample *evidence*, never a
  buy/sell or return promise (anti-goal #2). Calm and unmissable, never hype.
- Interactive states: the "Proven" `<Link>` has hover (`hover:bg-surface`), active (`active:bg-bg`), and
  focus (`focus-visible:ring-1 focus-visible:ring-accent`) states. The "Not yet proven" chip is
  non-interactive by design (no certified backing → no link).

## States Handled

- **Loading / error / empty evidence:** the evidence fetch is fail-safe — the claim list starts empty and
  stays empty on any fetch error, so every top-decile badge reads "Not yet proven" with no link (never a
  fabricated "Proven", never a 500). The factor table itself keeps its existing loading skeleton / "Backend
  unavailable" / empty states.
- **Matched-but-non-PASS cohort:** ma_stack's FAIL ledger row resolves to "Not yet proven", no href.
- **Below-the-fold:** the vcp_contraction row on `/evidence` and the factor-lab "Proven" badge sit below the
  fold inside wide content — browser QA MUST scroll each target into the viewport before capture (iter-3
  lesson). Verified during dev via `scrollIntoView`.

## Files Changed (frontend)

- `apps/frontend/lib/evidence.ts`
- `apps/frontend/lib/evidence.test.ts`
- `apps/frontend/app/evidence/page.tsx`
- `apps/frontend/app/research/_labs.tsx`

## Tests Run

- `cd apps/frontend && npx tsx lib/evidence.test.ts` → **25 passed**.
- `cd apps/frontend && npx tsc --noEmit` → clean.
- `npx next build` → `/research/factor-lab` + `/evidence` routes compiled.
- Live browser verification (Chrome) on :3255 against backend :8255 — see dev handoff.

## Known Issues

- None specific to the UI. The badge cohort is config-driven (top decile = `deciles_count`, horizon =
  `default_horizon`); see the dev handoff for the config-drift fail-safe note.
