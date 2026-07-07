/**
 * Unit tests for the iter-19 "Unassigned" sector bucket (lib/sector-label.ts).
 *
 * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
 *   node lib/sector-label.test.ts
 *
 * The crux (iter-19 regression fix): a stock with no mapped GICS sector serves `sector: null`. This must
 * read as the honest "Unassigned" bucket everywhere (display / filter vocabulary / sort), and the sort
 * comparator must never throw on a null sector (the exact `.localeCompare` crash this iteration fixes).
 */
import assert from "node:assert";

import { UNASSIGNED_SECTOR, compareSectors, sectorLabel } from "./sector-label.ts";

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

// --- sectorLabel: the display/filter mapping ------------------------------------------------------

check('null maps to the honest "Unassigned" bucket', () => {
  assert.strictEqual(sectorLabel(null), UNASSIGNED_SECTOR);
});

check("a real sector name passes through verbatim (never renamed)", () => {
  assert.strictEqual(sectorLabel("Technology"), "Technology");
});

check('UNASSIGNED_SECTOR is never a literal "null" string', () => {
  assert.notStrictEqual(UNASSIGNED_SECTOR, "null");
  assert.strictEqual(typeof UNASSIGNED_SECTOR, "string");
});

// --- compareSectors: the null-safe sort comparator (the exact crash this iteration fixes) ----------

check("comparing two nulls never throws and reports equal", () => {
  assert.strictEqual(compareSectors(null, null), 0);
});

check("comparing null against a real sector never throws", () => {
  assert.doesNotThrow(() => compareSectors(null, "Technology"));
  assert.doesNotThrow(() => compareSectors("Technology", null));
});

check("null sorts consistently with its own label (matches Unassigned vs the real sector)", () => {
  const direct = "Unassigned".localeCompare("Technology");
  assert.strictEqual(Math.sign(compareSectors(null, "Technology")), Math.sign(direct));
  assert.strictEqual(compareSectors(null, "Technology"), -compareSectors("Technology", null));
});

check("two equal real sectors compare equal", () => {
  assert.strictEqual(compareSectors("Technology", "Technology"), 0);
});

check("comparator ordering is stable (sorting a null-mixed array never throws)", () => {
  const sectors: (string | null)[] = ["Utilities", null, "Energy", null, "Consumer Discretionary"];
  assert.doesNotThrow(() => [...sectors].sort(compareSectors));
  const sorted = [...sectors].sort(compareSectors);
  const labels = sorted.map(sectorLabel);
  const expected = [...labels].sort((a, b) => a.localeCompare(b));
  assert.deepStrictEqual(labels, expected);
});

console.log(`\n${passed} passed`);
