/**
 * Unit tests for the J-04/J-07 readiness-badge/preflight-banner staleness annotation formatter
 * (lib/staleness-annotation.ts). No test framework is installed in this frontend; these run under
 * Node's native TS type-stripping:
 *   node lib/staleness-annotation.test.ts
 * (per the project's documented dev-box limitation, `node lib/*.test.ts` may not execute on every Node
 * build locally -- see docs/handoffs/*iter-49-dev.md; these run in the CI/QA Node environment either
 * way, same as every other `lib/*.test.ts` file here.)
 *
 * TC-3/TC-4 (ops-hardening iter-77): `stale_for_s > 0` renders the annotation, `stale_for_s === 0`
 * (fresh/synchronous) renders none, and a failed-poll `null` renders none -- never a stale or
 * fabricated number.
 */
import assert from "node:assert";

import { formatStaleAnnotation } from "./staleness-annotation.ts";

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

check("stale_for_s > 0 renders 'as of Ns ago', rounded to the nearest second", () => {
  assert.strictEqual(formatStaleAnnotation(12.4), "as of 12s ago");
  assert.strictEqual(formatStaleAnnotation(0.6), "as of 1s ago");
});

check("sub-second staleness reads 'as of <1s ago', never the self-contradictory 'as of 0s ago'", () => {
  // The steady state with `readiness.refresh_interval_seconds: 0.5` -- most live samples land here
  // (audit finding F1). The annotation must stay visible (the payload IS stale) and stay truthful.
  assert.strictEqual(formatStaleAnnotation(0.053), "as of <1s ago");
  assert.strictEqual(formatStaleAnnotation(0.128), "as of <1s ago");
  assert.strictEqual(formatStaleAnnotation(0.499), "as of <1s ago");
  // The rounding boundary: >= 0.5 rounds up to a real second, so it keeps the numeric form.
  assert.strictEqual(formatStaleAnnotation(0.505), "as of 1s ago");
});

check("stale_for_s === 0 (fresh/synchronous compute) renders no annotation", () => {
  assert.strictEqual(formatStaleAnnotation(0), null);
});

check("stale_for_s === null (before first poll / failed poll) renders no annotation", () => {
  assert.strictEqual(formatStaleAnnotation(null), null);
});

check("a negative value never renders a fabricated annotation (defensive, unexpected payload shape)", () => {
  assert.strictEqual(formatStaleAnnotation(-3), null);
});

check("a non-finite value (NaN/Infinity) never renders a fabricated annotation", () => {
  assert.strictEqual(formatStaleAnnotation(Number.NaN), null);
  assert.strictEqual(formatStaleAnnotation(Number.POSITIVE_INFINITY), null);
});

check("a large staleness value still renders honestly (no cap/clamp hiding real age)", () => {
  assert.strictEqual(formatStaleAnnotation(482.9), "as of 483s ago");
});

console.log(`${passed} passed`);
