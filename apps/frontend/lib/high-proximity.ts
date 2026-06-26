/**
 * Shared "Proximity to 52-week high" helpers (J-106) — the SINGLE source for reading + formatting the
 * stored `high_proximity` leadership component value, so the `/stocks` leaderboard column and the Stock
 * Detail Leadership breakdown render the IDENTICAL value (single source of truth → J-06). These read the
 * already-served `ScoreComponent.raw` (the canonical `dist_from_high`, a percent <= 0; 0 at a fresh high;
 * null/NA on short history) — they NEVER recompute it and never add a field to the `/api/stocks` payload.
 */
import type { ScoreComponent } from "@/lib/api";

/** The canonical leadership component key carrying the stored distance-below-52-week-high. */
export const HIGH_PROXIMITY_KEY = "high_proximity";

/**
 * The stored proximity-to-52w-high value for a leadership component list: the `high_proximity`
 * component's raw value when available, else null (NA). The SAME served datum the Leadership breakdown
 * reads — a pure lookup, no recompute. A percent <= 0 (0 at a fresh high); null on short history.
 */
export function highProximityValue(components: ScoreComponent[]): number | null {
  const c = components.find((x) => x.name === HIGH_PROXIMITY_KEY);
  if (!c || !c.available || c.raw == null) return null;
  return c.raw;
}

/**
 * Format the proximity value identically wherever it is shown (leaderboard column + Leadership
 * breakdown): a percent printed with two decimals (its natural sign — <= 0, e.g. "-5.20%"; "0.00%" at a
 * fresh high). NA (null/undefined) renders the muted "NA" label — never a fabricated number.
 */
export function fmtHighProximity(value: number | null | undefined): string {
  if (value === null || value === undefined) return "NA";
  return `${value.toFixed(2)}%`;
}
