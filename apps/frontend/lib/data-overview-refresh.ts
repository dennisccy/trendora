/**
 * goal-ops-hardening iter-62 (J-07 / auditor F3 fix) — the single, pure authority for how `/data`'s
 * ambient idle-cadence coverage/availability refresh (iter-60/61) should handle a fetch REJECTION. No
 * React, no DOM types, so it is unit-testable under `node` (the existing frontend convention — see
 * `lib/api-base.ts`, `lib/background-compute-panel-branch.ts`).
 *
 * WHY THIS EXISTS — before this fix, `app/data/page.tsx`'s `loadOverview`/`loadAvailability` `.catch`
 * handlers unconditionally set `{kind:"error"}` on ANY fetch failure, INCLUDING the periodic 30-second
 * ambient poll (iter-60/61). A single transient hiccup on that poll silently wiped already-rendered good
 * coverage/availability numbers and replaced them with the "Backend unavailable" card, one poll cycle
 * away from clearing again -- exactly the "silently discard good data" failure mode AG-8 exists to catch.
 *
 * The fix: once a page has SOMETHING real to show (`kind === "ok"`), a fetch failure never erases it --
 * the stale-but-real data keeps rendering until a fetch actually succeeds again. The INITIAL-mount
 * failure case (no data yet -- `kind === "loading"`) is unchanged: it still becomes the honest
 * "Backend unavailable" card, exactly as today.
 */

export type FetchState<T> =
  | { kind: "loading" }
  | { kind: "ok"; data: T }
  | { kind: "error" };

/**
 * Resolve the next state after a fetch REJECTS, given the state immediately before that fetch started.
 *
 * @param prev the state before this fetch's `.catch` fired.
 * @returns `prev` UNCHANGED when it already carries real data (`kind === "ok"`) -- a periodic refresh's
 *          transient failure must never erase already-displayed data; `{kind:"error"}` otherwise
 *          (preserves today's initial-mount-failure "Backend unavailable" behavior byte-for-byte).
 */
export function nextStateAfterFetchError<T>(prev: FetchState<T>): FetchState<T> {
  if (prev.kind === "ok") return prev;
  return { kind: "error" };
}
