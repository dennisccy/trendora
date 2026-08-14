/**
 * Unit tests for the shared date authority (lib/dates.ts).
 *
 * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
 *   node lib/dates.test.ts
 * (Per the project's documented dev-box limitation, `node lib/*.test.ts` may not execute on every Node
 * build locally — see docs/handoffs/*iter-25-dev.md; `npx tsx lib/dates.test.ts` is the local fallback.)
 *
 * `todayIsoDate` seeds the `/data` job form's End date. It is LOCAL-timezone by design — the field is an
 * editable default, and a UTC-derived value would read as "yesterday" for anyone east of Greenwich in
 * their evening. Every other helper here stays UTC-anchored because those render STORED dates.
 */
import assert from "node:assert";

import { formatIsoDate, isValidIsoDate, todayIsoDate } from "./dates.ts";

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

// --- todayIsoDate ------------------------------------------------------------------------------------

check("renders the injected date as yyyy-MM-dd", () => {
  // constructed with LOCAL components, since the helper reads local ones
  assert.strictEqual(todayIsoDate(new Date(2026, 7, 14)), "2026-08-14"); // month is 0-based: 7 = August
});

check("zero-pads single-digit months and days", () => {
  assert.strictEqual(todayIsoDate(new Date(2026, 0, 5)), "2026-01-05");
  assert.strictEqual(todayIsoDate(new Date(2026, 11, 31)), "2026-12-31");
});

check("uses the LOCAL calendar day, not the UTC one", () => {
  // 2026-08-15 00:30 local. In any timezone ahead of UTC this instant is still the 14th in UTC, so a
  // UTC-derived implementation would return the wrong day for the user staring at the field.
  const localMidnightish = new Date(2026, 7, 15, 0, 30);
  assert.strictEqual(todayIsoDate(localMidnightish), "2026-08-15");
});

check("its output is always a valid ISO date the job form will accept", () => {
  // the form blocks submission on anything `isValidIsoDate` rejects, so the seeded default must pass
  for (const d of [new Date(2026, 1, 28), new Date(2024, 1, 29), new Date(2026, 7, 14)]) {
    assert.strictEqual(isValidIsoDate(todayIsoDate(d)), true, `${todayIsoDate(d)} must be accepted`);
  }
});

check("a real `new Date()` round-trips through the validator", () => {
  assert.strictEqual(isValidIsoDate(todayIsoDate()), true);
});

// --- the existing helpers stay unchanged --------------------------------------------------------------

check("isValidIsoDate still rejects the shapes the /data inputs must reject", () => {
  assert.strictEqual(isValidIsoDate("2026-13-40"), false);
  assert.strictEqual(isValidIsoDate("10/06/2026"), false);
  assert.strictEqual(isValidIsoDate("2026-02-30"), false);
  assert.strictEqual(isValidIsoDate("2026-08-14"), true);
});

check("formatIsoDate still renders the em dash rather than a fabricated date", () => {
  assert.strictEqual(formatIsoDate(null), "—");
  assert.strictEqual(formatIsoDate(""), "—");
  assert.strictEqual(formatIsoDate("2026-08-14T13:30:00"), "2026-08-14");
});

console.log(`${passed} passed`);
