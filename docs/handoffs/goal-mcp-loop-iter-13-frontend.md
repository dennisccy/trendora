# goal-mcp-loop-iter-13 Frontend Handoff

**Phase:** goal-mcp-loop-iter-13
**Date:** 2026-07-01
**Agent:** developer
**Status:** complete

## What Was Built (UI)

The evidence layer now proves a **composite (multi-factor)** edge, not just single-factor / single-horizon
ones. Two additive, calm evidence markers — both reading the SAME `GET /api/evidence` payload:

- **`/research/factor-combination` — composite-cohort evidence badge.** The Combined (composite rank-blend)
  cohort row gains an inline "Proven" / "Not yet proven" chip. It reads "Proven" (accent, `ShieldCheck`,
  deep-links to the `/evidence` combination row) ONLY when the currently-selected legs match the certified
  cohort — `rs_spy_3m:top:quintile` + `high_proximity:top:tertile` @ horizon **20**. Every other combination
  (including the FAILED config default `rs_spy_3m × atr_pct`, or any other horizon) reads "Not yet proven"
  (muted, `Shield`, no link). Reactive to the leg/horizon selection.
- **`/evidence` — a 6th certified-claim row (auto-rendered).** The combination claim renders through the
  existing `ClaimRow`: hypothesis chips (both `condition` legs + `kind=combination` + `horizon=20` +
  `direction=positive` + `cohort=composite` + `ledger=canonical`), PASS verdict + holdout edge **+4.69%**,
  control vs SPY **+4.69%**, registration date 2026-07-01, forward-walk "Pending", and a
  **"Backs: Multi-factor combination lab →"** linkback (an honest title, never "Unmapped signal").

## Files Changed

- `apps/frontend/lib/evidence.ts` -- the pure read-side matcher (`resolveCombinationEvidence`), the
  `CombinationCohort` type, the extractor, the combination anchor, and the `claimSurface`/`claimAnchorId`
  combination branch. No React, no fetch — unit-tested.
- `apps/frontend/lib/evidence.test.ts` -- +10 combination unit checks.
- `apps/frontend/app/research/_labs.tsx` -- `CombinationLab` fetches `fetchEvidence` claims; `CombinationTable`
  builds + resolves the composite cohort and renders the new `CombinationEvidenceBadge` on the composite row.

## Design System Conformance

- Reuses the existing quiet evidence chip pattern — `Badge` (`accent` for Proven, `default` for Not-yet-proven),
  `lucide-react` `ShieldCheck` / `Shield`, Next.js `<Link>` for the deep-link — mirroring `FactorEvidenceBadge`.
  No new component beyond the small badge, no new colors/effects, no layout rewrite. Matches Trendora's
  minimal, data-dense, evidence-first style (a calm "proven / not yet proven" chip, never hype).
- **States handled:** empty/failed `fetchEvidence` → "Not yet proven", no link (fail-safe honesty); the
  default and every non-certified selection → "Not yet proven"; a matched-but-non-PASS entry → never "Proven";
  the composite row keeps its existing NA/low-sample cells unchanged. Interactive "Proven" badge has hover /
  focus-visible / active states.

## Interaction Notes for Browser QA

- **To see "Proven":** on `/research/factor-combination` at horizon **20**, keep leg 1 as
  `rs_spy_3m` / top / quintile and change leg 2 to `high_proximity` / **top** / **tertile**. The composite-row
  badge flips to "Proven" and deep-links to the `/evidence` combination row.
- **To see "Not yet proven":** the first-load default (`rs_spy_3m × atr_pct:bottom:tertile`), or the certified
  legs at any horizon other than 20. This is correct/honest — do NOT special-case the default.
- Badge selectors: `[data-testid="combination-evidence-badge"]`, `[data-proven="true|false"]`,
  `[data-horizon]`, `[data-legs]`; the composite row is `[data-testid="combination-row-composite"]`; the
  `/evidence` combination row carries `id="combination-high_proximity-rs_spy_3m-h20"`.

## Known Limitations

- No new page/route/nav — both routes were already registered. The combination badge is the only new
  interactive element; the `/evidence` row is pure additive rendering.
- Direction is fixed `positive` (the composite is the top-quantile blend — positive by construction), matching
  the certified claim.
