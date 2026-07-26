import type { BackgroundComputeOutcome } from "./api";

/**
 * goal-ops-hardening iter-26 (J-09 confirm-gap 2) — the single, pure authority for HOW
 * `LastOutcomeSummary` (`app/data/page.tsx`) renders a completed/failed background-compute outcome. No
 * React, no DOM types, so it is unit-testable under `node` (the existing frontend convention — see
 * `lib/background-compute-panel-branch.ts`).
 *
 * Pure extraction of the decision that was previously inline in `LastOutcomeSummary` — refactor only,
 * no behavior change. The `completed` case renders byte-identically (badge `"ok"`, no reason line); the
 * `failed` case (never exercised by a captured panel state before this iteration) now has direct,
 * citable test coverage of exactly what it produces.
 */
export interface LastOutcomeSummary {
  /** The failure reason to render, or `null` when there is none (the `completed` case). */
  reasonText: string | null;
  /** The badge variant `LastOutcomeSummary` passes straight to `<Badge variant=...>`. */
  badgeVariant: "ok" | "danger";
}

/** Resolve how a single `background_compute.recent_outcomes[0]` entry should render. */
export function resolveLastOutcomeSummary(outcome: BackgroundComputeOutcome): LastOutcomeSummary {
  const failed = outcome.outcome === "failed";
  return {
    reasonText: failed ? outcome.reason : null,
    badgeVariant: failed ? "danger" : "ok",
  };
}
