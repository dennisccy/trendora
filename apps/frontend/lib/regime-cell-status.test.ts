/**
 * Unit tests for the J-05/J-07 closeout Regime-Lab degraded-cell predicate (lib/regime-cell-status.ts).
 *
 * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
 *   node lib/regime-cell-status.test.ts
 *
 * TC-5/TC-6 (ops-hardening iter-60): a DEGRADED horizon (`status: "unavailable"`, `n: 0`) must be
 * reported unavailable — `RegimeReturnCell` uses this to suppress the active `SampleLink` drill-down in
 * favor of a visible "Unavailable" indicator. A genuinely low-sample-but-not-degraded cell (`status`
 * absent, a real `n` below `min`) must NOT be reported unavailable — its existing chip and link render
 * exactly as before.
 */
import assert from "node:assert";

import { isRegimeCellUnavailable } from "./regime-cell-status.ts";
import type { RegimeLabHorizonCell } from "./api.ts";

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

// --- TC-5: a degraded horizon (status: "unavailable", n: 0) is reported unavailable ----------------

check("a degraded cell (status: unavailable, n=0) is reported unavailable", () => {
  const cell: RegimeLabHorizonCell = {
    horizon: 20, n: 0, low_sample: true, mean_return: null, mean_max_drawdown: null, status: "unavailable",
  };
  assert.strictEqual(isRegimeCellUnavailable(cell), true);
});

// --- TC-6: a genuine low-sample cell (status absent, real n below min) is NOT reported unavailable ---

check("a genuine low-sample cell (status absent, n=3 below min) is NOT reported unavailable", () => {
  const cell: RegimeLabHorizonCell = {
    horizon: 20, n: 3, low_sample: true, mean_return: -0.012, mean_max_drawdown: -0.041,
  };
  assert.strictEqual(isRegimeCellUnavailable(cell), false);
});

// --- a clean, well-sampled cell is NOT reported unavailable (the ordinary case) ----------------------

check("a clean, well-sampled cell (status absent, low_sample false) is NOT reported unavailable", () => {
  const cell: RegimeLabHorizonCell = {
    horizon: 20, n: 512, low_sample: false, mean_return: 0.031, mean_max_drawdown: -0.058,
  };
  assert.strictEqual(isRegimeCellUnavailable(cell), false);
});

console.log(`\nregime-cell-status: ${passed} checks passed`);
