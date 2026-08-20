/**
 * apps/frontend/lib/format-fact.ts — TC-36 (goal-market-compass iter-3): a type-aware DISPLAY formatter
 * for a compass narrative sentence's cited `fact.value` (`GET /api/compass`'s `narrative.sentences[].
 * facts[].value`). A number renders as a rounded, human-readable 2-decimal string (e.g. "-0.20" instead
 * of a raw floating-point artifact like "-0.20000000000000284"); any other type renders via `String(...)`
 * unchanged (unchanged behavior for strings/booleans/null — no regression there).
 *
 * Display-only: the served/stored fact value itself is NEVER altered by this function or its caller —
 * only how it is RENDERED on screen.
 */

export function formatFactValue(value: string | number | boolean | null): string {
  if (typeof value === "number") {
    return value.toFixed(2);
  }
  return String(value);
}
