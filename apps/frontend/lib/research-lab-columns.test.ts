/**
 * Unit tests for the J-114 grouped per-horizon column order (lib/research-lab-columns.ts).
 *
 * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
 *   node lib/research-lab-columns.test.ts
 *
 * The J-114 crux (de-interleave to match the J-86 leaderboard grouping): the four all-horizon lab tables
 * must render ALL forward-return columns first, then ALL max-drawdown columns — never interleaved. These
 * tests assert that:
 *   (a) every forward-return descriptor precedes every max-drawdown descriptor (no Fwd → MDD → Fwd);
 *   (b) within each metric block the horizons keep the supplied (ascending 1/5/10/20/60d) order;
 *   (c) the column count is exactly 2 × |horizons| (one fwd + one mdd per horizon — none added/dropped);
 *   (d) the horizon set is whatever config supplies (no hardcoded [1,5,10,20,60]) — a 3-horizon and a
 *       single-horizon config both group correctly;
 *   (e) the key strings (`fwd:${h}` / `mdd:${h}` equivalents) the sort-column mapping uses are stable.
 */
import assert from "node:assert";

import {
  groupedHorizonColumns,
  horizonColumnKey,
  type HorizonColumn,
} from "./research-lab-columns.ts";

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

const HORIZONS = [1, 5, 10, 20, 60];

// --- (a) all forward-return columns precede all max-drawdown columns (the J-114 invariant) -------

check("all forward-return columns come before all max-drawdown columns (no interleave)", () => {
  const cols = groupedHorizonColumns(HORIZONS);
  const firstMdd = cols.findIndex((c) => c.metric === "mdd");
  const lastFwd = cols.map((c) => c.metric).lastIndexOf("fwd");
  assert.ok(firstMdd > lastFwd, "every fwd descriptor must precede every mdd descriptor");
  // and explicitly: no fwd appears after the first mdd
  cols.slice(firstMdd).forEach((c) => assert.strictEqual(c.metric, "mdd", "no fwd after the first mdd"));
});

check("the exact grouped sequence for [1,5,10,20,60] is all-fwd-then-all-mdd", () => {
  const cols = groupedHorizonColumns(HORIZONS);
  assert.deepStrictEqual(cols, [
    { metric: "fwd", horizon: 1 },
    { metric: "fwd", horizon: 5 },
    { metric: "fwd", horizon: 10 },
    { metric: "fwd", horizon: 20 },
    { metric: "fwd", horizon: 60 },
    { metric: "mdd", horizon: 1 },
    { metric: "mdd", horizon: 5 },
    { metric: "mdd", horizon: 10 },
    { metric: "mdd", horizon: 20 },
    { metric: "mdd", horizon: 60 },
  ]);
});

// --- (b) within each metric block, the supplied horizon order is preserved (ascending) -----------

check("each metric block preserves the supplied horizon order", () => {
  const cols = groupedHorizonColumns(HORIZONS);
  const fwdHorizons = cols.filter((c) => c.metric === "fwd").map((c) => c.horizon);
  const mddHorizons = cols.filter((c) => c.metric === "mdd").map((c) => c.horizon);
  assert.deepStrictEqual(fwdHorizons, HORIZONS);
  assert.deepStrictEqual(mddHorizons, HORIZONS);
});

// --- (c) exactly one fwd + one mdd per horizon — none added or dropped ---------------------------

check("column count is exactly 2 × |horizons| (paired, nothing added or dropped)", () => {
  const cols = groupedHorizonColumns(HORIZONS);
  assert.strictEqual(cols.length, HORIZONS.length * 2);
  // each horizon appears exactly once as fwd and once as mdd
  HORIZONS.forEach((h) => {
    assert.strictEqual(cols.filter((c) => c.metric === "fwd" && c.horizon === h).length, 1);
    assert.strictEqual(cols.filter((c) => c.metric === "mdd" && c.horizon === h).length, 1);
  });
});

// --- (d) config-driven horizon set: no hardcoded [1,5,10,20,60] ----------------------------------

check("a 3-horizon config groups all-fwd-then-all-mdd", () => {
  const cols = groupedHorizonColumns([5, 10, 20]);
  assert.deepStrictEqual(cols, [
    { metric: "fwd", horizon: 5 },
    { metric: "fwd", horizon: 10 },
    { metric: "fwd", horizon: 20 },
    { metric: "mdd", horizon: 5 },
    { metric: "mdd", horizon: 10 },
    { metric: "mdd", horizon: 20 },
  ]);
});

check("a single-horizon config yields exactly one fwd then one mdd", () => {
  assert.deepStrictEqual(groupedHorizonColumns([20]), [
    { metric: "fwd", horizon: 20 },
    { metric: "mdd", horizon: 20 },
  ]);
});

check("an empty horizon set yields no columns (honest empty, never fabricated)", () => {
  assert.deepStrictEqual(groupedHorizonColumns([]), []);
});

// --- (e) the key strings the sort-column mapping uses are stable ----------------------------------

check("horizonColumnKey is stable and distinct per (metric, horizon)", () => {
  const cols = groupedHorizonColumns(HORIZONS);
  const keys = cols.map((c: HorizonColumn) => horizonColumnKey(c));
  assert.strictEqual(new Set(keys).size, keys.length, "all keys distinct");
  assert.strictEqual(horizonColumnKey({ metric: "fwd", horizon: 5 }), "fwd-5");
  assert.strictEqual(horizonColumnKey({ metric: "mdd", horizon: 20 }), "mdd-20");
});

console.log(`\nresearch-lab-columns: ${passed} checks passed`);
