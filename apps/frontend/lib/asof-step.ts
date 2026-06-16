/**
 * J-79 — the single, pure authority for STEPPING the one global as-of date one available snapshot at a
 * time, and for the keyboard FIELD-GUARD. No React, no DOM types beyond a structural target shape, so it
 * is unit-testable under `node`. Every J-79 affordance (the top-bar ◀ ▶ buttons, the opt-in ← → keys,
 * and the calendar's ArrowLeft/Right scrub from J-71) computes its landing date through THIS module, so
 * stepping is identical everywhere and there is no second/page-local date state — the result is fed to
 * the EXISTING `setAsOf` the calendar already calls (the asof-provider stays the sole owner of the date
 * and its `?asof` serialization).
 *
 * "Snapshot-only" stepping: movement is among the dates that actually have snapshots (the run list),
 * NEVER an arbitrary calendar ±1 onto a non-trading / no-snapshot day. Stepping is BOUNDED — at the
 * oldest, a backward step is a no-op; at the newest, a forward step rests at the newest (which the
 * provider normalises to "Latest"). The newest available date == the latest view, so landing there is
 * surfaced as `null` (clear the as-of), matching the calendar day buttons' Latest semantics.
 */

/** Step direction: -1 = older (◀ / ArrowLeft), +1 = newer (▶ / ArrowRight). */
export type StepDir = -1 | 1;

/**
 * Resolve the as-of date one available snapshot in `dir`, bounded.
 *
 * @param dates  ALL available snapshot dates, DESCENDING (newest first) — the asof-provider's `dates`.
 * @param asOf   the current selection (null == viewing the latest/newest).
 * @returns      a `{ changed, next }` result. `changed` is false when the step is bounded out (no-op at
 *               the oldest going older / at the newest going newer). `next` is the landing date, or null
 *               when landing on the newest available date (== Latest). When `changed` is false, `next`
 *               echoes the current selection so callers may apply it harmlessly.
 */
export function resolveStep(
  dates: string[],
  asOf: string | null,
  dir: StepDir,
): { changed: boolean; next: string | null } {
  if (dates.length === 0) return { changed: false, next: asOf };
  // Ascending order makes "older = lower index, newer = higher index" hold for the bounds math.
  const asc = [...dates].sort();
  const lastIdx = asc.length - 1; // newest == Latest
  const newest = asc[lastIdx];
  // Current index: the selected date's index, or the newest (last) when at Latest / an unknown value.
  const curIdx = asOf ? asc.indexOf(asOf) : lastIdx;
  const fromIdx = curIdx < 0 ? lastIdx : curIdx;
  const nextIdx = fromIdx + dir;
  if (nextIdx < 0 || nextIdx > lastIdx) return { changed: false, next: asOf }; // bounded: no-op
  const landing = asc[nextIdx];
  // The newest available date is the latest view — surface it as null (clear the as-of) so the historical
  // indicator and the `?asof` serialization match the calendar's "Latest" affordance exactly.
  return { changed: true, next: landing === newest ? null : landing };
}

/** True iff a backward (older) step would move — i.e. the current selection is not already the oldest. */
export function canStepPrev(dates: string[], asOf: string | null): boolean {
  return resolveStep(dates, asOf, -1).changed;
}

/** True iff a forward (newer) step would move — i.e. the current selection is not already the newest. */
export function canStepNext(dates: string[], asOf: string | null): boolean {
  return resolveStep(dates, asOf, 1).changed;
}

/** The structural shape of a focused element we field-guard against (an `EventTarget` at call sites). */
export interface FieldGuardTarget {
  tagName?: string;
  isContentEditable?: boolean;
}

/**
 * J-79 field-guard: true when keyboard stepping MUST be ignored because focus is inside a text-entry
 * surface — an `<input>`, `<textarea>`, `<select>`, or any `contenteditable` element — so ← / → move the
 * caret / change the field, never the as-of date (goal.md J-79 step 5: caret in the `/stocks` search box).
 * Anything else (body, a button, a link) is steppable. A null/odd target is treated as NOT a field
 * (safe default: a global handler with no element shouldn't be silently swallowed).
 */
export function isFieldEditingTarget(target: FieldGuardTarget | null | undefined): boolean {
  if (!target) return false;
  if (target.isContentEditable) return true;
  const tag = target.tagName ? target.tagName.toUpperCase() : "";
  return tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT";
}
