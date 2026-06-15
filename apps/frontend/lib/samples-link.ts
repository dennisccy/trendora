/**
 * Build the `/research/samples` query string for ONE published `N=` cohort (J-51). The ONE place the
 * chip→drill-down param shape is defined, so the chip link and the samples page agree on the contract.
 *
 * This carries ONLY the cohort selectors (kind + slice + the cohort's identifying params + horizon). It
 * does NOT add `?asof` — that is the single global as-of's serialization, merged separately by the J-50
 * `useAsOfHref` helper at the link site, so the URL has exactly one author for the date (no second date
 * state). The drill-down's as-of SCOPE (the Research analysis-mode "as of date" toggle) IS a cohort param
 * (`scope=asof`) because it changes WHICH observations the cohort pools — distinct from the global as-of
 * date itself (which `useAsOfHref` adds). At all-history mode `scope` is omitted.
 */

export type SampleScope = "all" | "asof";

/** A factor-lab cohort chip: n_total / rank-IC n (slice "total"), a per-decile n (slice "decile"), or a
 *  by-regime n (slice "regime"). */
export interface FactorCohortParams {
  kind: "factor";
  factor: string;
  horizon: number;
  slice: "total" | "decile" | "regime";
  decile?: number;
  regime?: string;
}

/** A combination-lab cohort chip: baseline / a single condition / composite / strict-overlap n. The
 *  `conditions` are the resolved `"<factor>:<side>:<quantile>"` triples (config-driven). */
export interface CombinationCohortParams {
  kind: "combination";
  conditions: string[]; // "<factor_key>:<side>:<quantile_key>"
  horizon: number;
  cohort: "baseline" | "single" | "composite" | "strict_overlap";
  singleIndex?: number;
}

/** An event-study cohort chip: pooled n / per-horizon n (slice "pooled"), a by-regime n, or a by-sector n.
 *  `view` (J-63) is the overlap-honesty MODE the chip was clicked under — `episodes` (first-trigger,
 *  default) or `pooled` (per-signal-day) — so the drill-down reproduces the same mode + cohort. It is a
 *  cohort/mode selector ONLY: it does NOT touch `?asof` or the analysis-mode `scope`. */
export interface EventStudyCohortParams {
  kind: "event-study";
  subject: string;
  horizon: number;
  slice: "pooled" | "regime" | "sector";
  view: "episodes" | "pooled";
  regime?: string;
  sector?: string;
}

/** A Regime × Setup × Pattern combination cohort chip (J-77): one (regime, setup, pattern) row's `N=`.
 *  `view` (J-63) is the overlap-honesty MODE the chip was clicked under — `episodes` (first-trigger,
 *  default) or `pooled` (per-signal-day) — so the drill-down reproduces the same mode + cohort. The
 *  `pattern` is a config pattern key OR the `"none"` sentinel (an observation with no flagged pattern). */
export interface RegimeSetupPatternCohortParams {
  kind: "regime-setup-pattern";
  horizon: number;
  regime: string;
  setup: string;
  pattern: string; // a config pattern key, or "none"
  view: "episodes" | "pooled";
}

export type CohortParams =
  | FactorCohortParams
  | CombinationCohortParams
  | EventStudyCohortParams
  | RegimeSetupPatternCohortParams;

/** Serialize a cohort + the analysis-mode scope into the `/research/samples` path (no `?asof` — that is
 *  merged by `useAsOfHref` at the link site). Repeated `condition` params are preserved. */
export function buildSamplesHref(cohort: CohortParams, scope: SampleScope): string {
  const params = new URLSearchParams();
  params.set("kind", cohort.kind);
  params.set("horizon", String(cohort.horizon));

  if (cohort.kind === "factor") {
    params.set("factor", cohort.factor);
    params.set("slice", cohort.slice);
    if (cohort.slice === "decile" && cohort.decile !== undefined) {
      params.set("decile", String(cohort.decile));
    }
    if (cohort.slice === "regime" && cohort.regime !== undefined) {
      params.set("regime", cohort.regime);
    }
  } else if (cohort.kind === "combination") {
    for (const c of cohort.conditions) params.append("condition", c);
    params.set("cohort", cohort.cohort);
    if (cohort.cohort === "single" && cohort.singleIndex !== undefined) {
      params.set("single_index", String(cohort.singleIndex));
    }
  } else if (cohort.kind === "regime-setup-pattern") {
    // J-77: the (regime, setup, pattern) combination cohort selectors + the overlap-honesty view.
    params.set("regime", cohort.regime);
    params.set("setup", cohort.setup);
    params.set("pattern", cohort.pattern);
    params.set("view", cohort.view);
  } else {
    params.set("subject", cohort.subject);
    params.set("slice", cohort.slice);
    // J-63: carry the overlap-honesty view so the drill-down reproduces the same mode (a cohort selector,
    // never the date — `?asof` is still merged separately by `useAsOfHref`).
    params.set("view", cohort.view);
    if (cohort.slice === "regime" && cohort.regime !== undefined) {
      params.set("regime", cohort.regime);
    }
    if (cohort.slice === "sector" && cohort.sector !== undefined) {
      params.set("sector", cohort.sector);
    }
  }

  // the analysis-mode scope is a cohort param (it changes WHICH observations pool). All-history omits it.
  if (scope === "asof") params.set("scope", "asof");

  return `/research/samples?${params.toString()}`;
}

/** The reverse mapping used by the samples PAGE: turn the page's own search params into the flat
 *  [key, value][] list `fetchSamples` sends to the backend, dropping the frontend-only `scope` + `asof`
 *  (the backend learns the as-of cutoff via `withAsOf`'s `as_of` param, added by the caller). Repeated
 *  `condition` params are preserved in order. */
export function samplesFetchParams(search: URLSearchParams): [string, string][] {
  const out: [string, string][] = [];
  for (const [key, value] of search.entries()) {
    if (key === "scope" || key === "asof" || key === "as_of") continue;
    out.push([key, value]);
  }
  return out;
}
