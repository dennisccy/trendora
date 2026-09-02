/**
 * Unit tests for the What-changed card's stock-accounting disclosure helpers
 * (lib/stock-accounting-summary.ts) — goal-market-compass iter-40, J-15.
 *
 * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
 *   node lib/stock-accounting-summary.test.ts
 *
 * Covers the two manifest shapes named in the TESTING REQUIREMENTS: an OLD (absent-field) fixture and a
 * NEW (present-field) fixture, plus the residual-zero and residual-positive branches.
 */
import assert from "node:assert";

import { stockResidualDisclosureText, stockShownCapDisclosureText } from "./stock-accounting-summary.ts";

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

// --- old fixture: stock_accounting absent (pre-iter-40 manifest) -> render nothing new, no throw -----

check("undefined stock_accounting yields no residual disclosure (old manifest, AG-8)", () => {
  assert.strictEqual(stockResidualDisclosureText(undefined), null);
});

check("undefined stock_accounting yields no shown-cap disclosure (old manifest, AG-8)", () => {
  assert.strictEqual(stockShownCapDisclosureText(undefined), null);
});

check("omitting stock_accounting entirely (optional field) behaves identically to passing undefined", () => {
  assert.strictEqual(stockResidualDisclosureText(), null);
  assert.strictEqual(stockShownCapDisclosureText(), null);
});

// --- new fixture, residual_count > 0 (the frontier-pair shape: 10 shown, 43 suppressed, 4 residual) ---

check("present stock_accounting with residual > 0 discloses the held-back count", () => {
  const summary = stockResidualDisclosureText({
    evaluated_count: 57, shown_count: 10, suppressed_count: 43, residual_count: 4,
  });
  assert.strictEqual(summary, "4 more stock moves held back by the display cap");
});

check("present stock_accounting with residual > 0 discloses the shown-top-N cap", () => {
  const summary = stockShownCapDisclosureText({
    evaluated_count: 57, shown_count: 10, suppressed_count: 43, residual_count: 4,
  });
  assert.strictEqual(summary, "Showing the top 10 stock moves");
});

check("residual_count === 1 is singular ('move', not 'moves')", () => {
  const summary = stockResidualDisclosureText({
    evaluated_count: 11, shown_count: 10, suppressed_count: 0, residual_count: 1,
  });
  assert.strictEqual(summary, "1 more stock move held back by the display cap");
});

// --- new fixture, residual_count === 0 (nothing held back this session) ------------------------------

check("present stock_accounting with residual === 0 still discloses an explicit zero (never blank)", () => {
  const summary = stockResidualDisclosureText({
    evaluated_count: 3, shown_count: 3, suppressed_count: 0, residual_count: 0,
  });
  assert.strictEqual(summary, "0 more stock moves held back by the display cap");
});

check("present stock_accounting with residual === 0 omits the shown-top-N cap entirely", () => {
  const summary = stockShownCapDisclosureText({
    evaluated_count: 3, shown_count: 3, suppressed_count: 0, residual_count: 0,
  });
  assert.strictEqual(summary, null);
});

console.log(`\n${passed} passed`);
