/**
 * Unit tests for the "Not priority" disclosure summary string (lib/why-not-summary.ts) — TC-14 of
 * goal-market-compass iter-39, the AG-8 regression repair.
 *
 * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
 *   node lib/why-not-summary.test.ts
 *
 * Covers the two manifest shapes that motivated this iteration:
 *  - a pre-iter-38-shaped fixture (missing `why_not_totals`, matching 34/36 stored rows as of
 *    iter-38) -> the degraded "held-back counts unavailable" string, no exception.
 *  - a post-iter-38 fixture (all fields present) -> the existing fully-counted string, unchanged.
 */
import assert from "node:assert";

import { whyNotSummary } from "./why-not-summary.ts";

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

// --- pre-iter-38 fixture: why_not_totals absent (undefined) -> degraded string, no throw --------

check("undefined why_not_totals produces the degraded held-back-unavailable string", () => {
  const summary = whyNotSummary({ why_not_count: 5, why_not_totals: undefined });
  assert.strictEqual(summary, "Not priority (5 shown — held-back counts unavailable for this manifest version)");
});

check("undefined why_not_totals with zero shown entries still degrades cleanly (no throw)", () => {
  const summary = whyNotSummary({ why_not_count: 0, why_not_totals: undefined });
  assert.strictEqual(summary, "Not priority (0 shown — held-back counts unavailable for this manifest version)");
});

check("omitting why_not_totals entirely (optional field) behaves identically to passing undefined", () => {
  const summary = whyNotSummary({ why_not_count: 3 });
  assert.strictEqual(summary, "Not priority (3 shown — held-back counts unavailable for this manifest version)");
});

// --- post-iter-38 fixture: why_not_totals present -> existing fully-counted string, unchanged ----

check("populated why_not_totals produces the existing fully-counted string", () => {
  const summary = whyNotSummary({
    why_not_count: 5,
    why_not_totals: { excluded_by_cap_uncapped: 4, below_floor_in_band_uncapped: 9 },
  });
  assert.strictEqual(summary, "Not priority (5 shown of 13 held back — 4 cap-excluded, 9 below-floor near-miss)");
});

check("populated why_not_totals with an explicit zero in one reason class renders that zero honestly", () => {
  const summary = whyNotSummary({
    why_not_count: 2,
    why_not_totals: { excluded_by_cap_uncapped: 0, below_floor_in_band_uncapped: 2 },
  });
  assert.strictEqual(summary, "Not priority (2 shown of 2 held back — 0 cap-excluded, 2 below-floor near-miss)");
});

check("both reason classes explicitly zero renders '0 held back', never a fabricated count", () => {
  const summary = whyNotSummary({
    why_not_count: 0,
    why_not_totals: { excluded_by_cap_uncapped: 0, below_floor_in_band_uncapped: 0 },
  });
  assert.strictEqual(summary, "Not priority (0 shown of 0 held back — 0 cap-excluded, 0 below-floor near-miss)");
});

console.log(`\n${passed} passed`);
