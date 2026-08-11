import type { RegimeLabHorizonCell } from "./api";

/**
 * ops-hardening iter-60 (J-05/J-07 closeout) — the single, pure authority for whether `RegimeReturnCell`
 * (`app/research/_labs.tsx`) suppresses its `SampleLink` drill-down in favor of a visible,
 * non-tooltip-only "Unavailable" indicator. No React, no DOM types, so it is unit-testable under `node`
 * (the existing frontend convention — see `lib/availability-empty-state.ts`).
 *
 * `status === "unavailable"` means THIS horizon's aggregation degraded under memory pressure
 * (`compute_regime_lab`'s per-horizon isolate-and-continue bound, ops-hardening iter-59/60) — its `n=0`
 * is an honest placeholder for a cohort that does not really exist for this response, not a genuinely
 * empty one, so a LIVE drill-down link into it would be misleading (previously distinguishable from a
 * real n=0 only by hovering the `title`). A genuine low-sample cell (`low_sample: true`, `status` absent)
 * is unaffected — its chip and link stay exactly as before.
 */
export function isRegimeCellUnavailable(cell: RegimeLabHorizonCell): boolean {
  return cell.status === "unavailable";
}
