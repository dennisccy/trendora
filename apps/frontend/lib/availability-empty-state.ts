import type { AvailabilityResponse } from "./api";

/**
 * ops-hardening iter-58 (audit B5 fix) — the single, pure authority for whether
 * `AvailabilityHeatmap` (`components/availability-heatmap.tsx`) renders the "No availability yet"
 * empty state. No React, no DOM types, so it is unit-testable under `node` (the existing frontend
 * convention — see `lib/background-compute-panel-branch.ts`).
 *
 * Before this fix the gate was `cells.length === 0` alone, which is honest for the ONE case it was
 * designed for (a DB where no `AvailabilityCache` row has ever been persisted) but also — a narrow,
 * real precondition — true for a persisted row whose stamp mismatches AND whose stored `cells` array
 * happens to be empty (e.g. a warm that ran before any trading day existed). That row is real, honestly
 * stale/updating data, not "nothing has ever been ingested" — showing the empty state there is the same
 * false claim iter-57 already fixed for the non-empty case. The fix: empty state renders ONLY when the
 * cells are empty AND the payload is not stale (`!stale`) — a stale-but-empty row falls through to the
 * normal `stale: true` banner path instead.
 */
export function shouldShowAvailabilityEmptyState(data: AvailabilityResponse): boolean {
  return data.cells.length === 0 && !data.stale;
}
