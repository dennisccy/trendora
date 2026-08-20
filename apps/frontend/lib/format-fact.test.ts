/**
 * Unit tests for lib/format-fact.ts (TC-36, goal-market-compass iter-3) — a raw floating-point cited-fact
 * value (e.g. "-0.20000000000000284") must render as a rounded, human-readable string ("-0.20"); every
 * other value type renders unchanged via `String(...)`.
 *
 * No test framework is installed in this frontend; run under the repo's TS type-strip convention:
 *   npx tsx lib/format-fact.test.ts
 */
import assert from "node:assert";

import { formatFactValue } from "./format-fact.ts";

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

check("a raw floating-point artifact rounds to a clean 2-decimal string", () => {
  assert.strictEqual(formatFactValue(-0.20000000000000284), "-0.20");
});

check("a positive float rounds the same way", () => {
  assert.strictEqual(formatFactValue(58.043219999), "58.04");
});

check("a clean integer-valued number still renders with 2 decimal places", () => {
  assert.strictEqual(formatFactValue(58), "58.00");
});

check("zero renders as 0.00, not -0.00 or bare 0", () => {
  assert.strictEqual(formatFactValue(0), "0.00");
});

check("a string value passes through via String(...) unchanged (no regression)", () => {
  assert.strictEqual(formatFactValue("improving"), "improving");
});

check("a boolean value passes through via String(...) unchanged (no regression)", () => {
  assert.strictEqual(formatFactValue(true), "true");
  assert.strictEqual(formatFactValue(false), "false");
});

check("null passes through via String(...) unchanged (no regression)", () => {
  assert.strictEqual(formatFactValue(null), "null");
});

console.log(`\nformat-fact: ${passed} checks passed`);
