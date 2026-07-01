/**
 * Per-horizon factor-lab evidence badges (goal-mcp-loop iter-11, J-07).
 *
 * PURE + dependency-free (no React, no fetch) so it is unit-testable under the repo's TS type-strip
 * convention (`npx tsx lib/factor-lab-evidence.test.ts`) — the `/research/factor-lab` FactorsTable maps over
 * it to render ONE evidence chip PER horizon.
 *
 * This is the read-side successor to iter-8's single-horizon badge: the Factor Lab evolves from a single
 * evidence marker at the default horizon to an HONEST per-horizon view (J-07). Each horizon resolves its own
 * status via the EXISTING `resolveCohortEvidence` matcher reading the SAME `GET /api/evidence` payload — no
 * new fetch path, no recompute. A horizon reads "Proven" ONLY when a PASS-backed certified-claim matches its
 * exact cohort (factor + top decile + horizon + direction); every unbacked horizon reads "Not yet proven"
 * (anti-goal #1 — the UI never fabricates proven-ness).
 */
import {
  resolveCohortEvidence,
  type CertifiedClaim,
  type FactorCohort,
} from "./evidence";

/** One per-horizon evidence-badge descriptor for a factor's top-decile cohort — the resolved status a
 *  factor-lab chip renders. `horizon` is threaded onto the chip's `data-horizon` (the browser-qa selector);
 *  `proven` / `label` / `href` / `claim` are read VERBATIM from `resolveCohortEvidence` (no recompute). */
export interface FactorHorizonBadge {
  /** The factor key this badge speaks for (the chip's `data-factor`). */
  factor: string;
  /** The highest-factor-value decile the cohort covers (D`topDecile`) — for the chip's title copy. */
  topDecile: number;
  /** The forward-return horizon (trading days) this badge resolves — the chip's `data-horizon`. */
  horizon: number;
  /** True iff a PASS-backed certified-claim matches this exact cohort (the chip's `data-proven`). */
  proven: boolean;
  /** "Proven" | "Not yet proven" — the exact status text the chip renders. */
  label: string;
  /** The `/evidence#…` deep-link when proven; null when not yet proven (no link). */
  href: string | null;
  /** The backing certified-claim row when proven (for the chip's registered-date title); null otherwise. */
  claim: CertifiedClaim | null;
}

/**
 * Resolve the per-horizon evidence badges for ONE factor's top-decile cohort (PURE, read-only). For each
 * horizon in the served vocabulary (`data.horizons`, e.g. [1,5,10,20,60]) it queries the SAME
 * `resolveCohortEvidence` matcher against the SAME served `claims[]` — returning ONE descriptor per horizon,
 * IN THE GIVEN ORDER. FAIL-SAFE: an empty / null / undefined claim list (fetch failed, or the ledger is
 * empty) yields every horizon "Not yet proven" with no link. Recomputes nothing — it re-displays the
 * referee's verdict per horizon, so a horizon lights "Proven" ONLY with a PASS-backed certified-claim.
 */
export function factorHorizonBadges(
  factor: string,
  topDecile: number,
  horizons: number[],
  claims: CertifiedClaim[] | null | undefined,
): FactorHorizonBadge[] {
  return horizons.map((horizon) => {
    const cohort: FactorCohort = {
      factor,
      slice_kind: "decile",
      decile: topDecile,
      horizon,
      direction: "positive",
    };
    const status = resolveCohortEvidence(cohort, claims);
    return {
      factor,
      topDecile,
      horizon,
      proven: status.proven,
      label: status.label,
      href: status.href,
      claim: status.claim,
    };
  });
}
