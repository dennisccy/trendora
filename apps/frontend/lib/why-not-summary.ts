/**
 * goal-market-compass iter-39 — the "Not priority" disclosure summary string for the Next-session
 * focus section (`compass-focus-section.tsx`), extracted to a pure function so the degraded-vs-full
 * variants are unit-testable under this project's plain-node convention
 * (`node lib/why-not-summary.test.ts`, no test framework installed).
 *
 * This is a mechanical extraction of the previously-inline template-literal ternary, not a new
 * behavior: the fully-counted string is byte-identical to iter-38's, and the new degraded string is
 * the one this iteration's fix introduces (AG-8 regression repair — see docs/goal.md J-14 /
 * `docs/phases/goal-market-compass-iter-39.md`).
 *
 * `why_not_totals` mirrors `CompassSelection.why_not_totals` (lib/api.ts) as its OWN local type
 * (rather than importing from api.ts) — kept dependency-free so this module runs under plain
 * `node lib/why-not-summary.test.ts` without pulling in api.ts's fetch machinery, matching the
 * `basis-disclosure-label.ts` convention.
 */
export interface WhyNotSummaryTotals {
  excluded_by_cap_uncapped: number;
  below_floor_in_band_uncapped: number;
}

export interface WhyNotSummaryInput {
  /** `selection.why_not.length` — the number of why-not entries actually rendered (already capped). */
  why_not_count: number;
  /**
   * `selection.why_not_totals` — `undefined` on any stored manifest minted before the iter-38
   * `rule_version` bump (34 of 36 stored rows as of iter-38). MUST be treated as "unavailable for
   * this manifest version", never dereferenced, and never defaulted to a fabricated `0`.
   */
  why_not_totals?: WhyNotSummaryTotals;
}

/**
 * Resolve the "Not priority" `Disclosure` summary string.
 *  - `why_not_totals` present (post-iter-38 manifest) -> the existing fully-counted string, unchanged.
 *  - `why_not_totals` undefined (pre-iter-38 manifest) -> an honest degraded string naming the shown
 *    count only — never a crash, never an invented held-back total.
 */
export function whyNotSummary({ why_not_count, why_not_totals }: WhyNotSummaryInput): string {
  if (why_not_totals === undefined) {
    return `Not priority (${why_not_count} shown — held-back counts unavailable for this manifest version)`;
  }
  const heldBack = why_not_totals.excluded_by_cap_uncapped + why_not_totals.below_floor_in_band_uncapped;
  return (
    `Not priority (${why_not_count} shown of ${heldBack} held back — ` +
    `${why_not_totals.excluded_by_cap_uncapped} cap-excluded, ` +
    `${why_not_totals.below_floor_in_band_uncapped} below-floor near-miss)`
  );
}
