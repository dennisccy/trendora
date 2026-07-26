import type { BackgroundComputeStatus, ReadinessState } from "./api";

/**
 * ops-hardening iter-25 (J-09, audit F1 fix) — the single, pure authority for WHICH copy branch
 * `BackgroundComputePanel` (`app/data/page.tsx`) renders. No React, no DOM types, so it is
 * unit-testable under `node` (the existing frontend convention — see `lib/asof-step.ts`).
 *
 * Before this fix, the panel read only `backgroundCompute` (from `useReadiness()`) and fell through to
 * the idle "No background compute running…" copy whenever that value was `null` — which is EXACTLY what
 * the provider also sets on a poll failure (`readiness-provider.tsx`'s catch branch), so a genuinely
 * unreachable backend was misreported as an honestly-idle one. This resolver reads the SAME shared
 * `state` the provider already exposes (the poll-failure signal `HealthBadge` uses for its own
 * "Backend unavailable" pill) to distinguish the two cases -- no second fetch, no new signal.
 */
export type BackgroundComputePanelBranch =
  | { kind: "unknown" }
  | { kind: "idle"; showLastOutcome: boolean }
  | { kind: "active"; showLastOutcome: boolean };

/**
 * Resolve which branch the panel should render.
 *
 * @param state             the shared readiness state from `useReadiness()` (`null` before the first
 *                          poll resolves, `"unavailable"` when the most recent poll failed).
 * @param backgroundCompute the shared `background_compute` value from `useReadiness()` (`null` before
 *                          the first poll resolves, or when the poll failed).
 */
export function resolveBackgroundComputePanelBranch(
  state: ReadinessState | null,
  backgroundCompute: BackgroundComputeStatus | null,
): BackgroundComputePanelBranch {
  // The poll-failure signal: `state === "unavailable"` — the SAME condition `HealthBadge` already
  // renders "Backend unavailable" for. Never confused with the pre-first-poll `state === null` moment
  // (that one still falls through to the idle branch below, unchanged from before this fix).
  if (state === "unavailable") return { kind: "unknown" };

  const active = backgroundCompute?.active ?? [];
  const recentOutcomes = backgroundCompute?.recent_outcomes ?? [];
  const showLastOutcome = recentOutcomes.length > 0;
  return active.length === 0 ? { kind: "idle", showLastOutcome } : { kind: "active", showLastOutcome };
}
