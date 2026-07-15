/**
 * Shared risk-budget formatting helpers (iter-40, J-24 / B-201) — the SINGLE source for rendering a
 * `RiskBudgetComponent` (value + cross-sectional percentile), used by BOTH the Stock Detail risk-budget
 * card and the `/stocks` leaderboard risk-budget columns, so the same stock's number reads identically
 * in both places (single source of truth — never recomputed client-side, never a second formatter).
 *
 * Every `RiskBudgetComponent.value` served by the backend is ALREADY a percent number (e.g. `5.23` means
 * "5.23%") — these helpers only round + append "%"; they never multiply by 100 (unlike
 * `components/forward-return.tsx`'s `fmtPct`/`fmtMdd`, which format raw FRACTION returns).
 */
import type { RiskBudgetComponent } from "@/lib/api";

/** Format an already-percent risk-budget value — "5.23%" (natural sign, never a forced "+"); null/
 *  undefined (NA — insufficient history) renders "NA". */
export function fmtRiskValue(value: number | null | undefined): string {
  if (value === null || value === undefined) return "NA";
  return `${value.toFixed(2)}%`;
}

/** Format a risk-budget percentile (a fraction in [0,1], oriented so HIGHER always means MORE risk) as
 *  the card's "pXX of universe" label; null/undefined renders null so the caller omits the chip
 *  entirely (never a fabricated "p0"). */
export function fmtRiskPercentile(percentile: number | null | undefined): string | null {
  if (percentile === null || percentile === undefined) return null;
  return `p${Math.round(percentile * 100)} of universe`;
}

/** True when a risk-budget component carries no value (short-history / insufficient-data NA) — the
 *  card/leaderboard render an honest "NA", never a fabricated 0. Mirrors the `naInvalidation`
 *  short-history convention already used on this page. */
export function isRiskBudgetNa(component: RiskBudgetComponent | null | undefined): boolean {
  return !component || component.value === null || component.value === undefined;
}
