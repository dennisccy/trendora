/**
 * Unit tests for the J-86 magnitude-graded max-drawdown colour scale (lib/mdd-color.ts).
 *
 * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
 *   node lib/mdd-color.test.ts
 * They assert EXACT class strings: NA / undefined / exactly-0 are the muted token (never a graded red),
 * and a more-negative drawdown maps to a strictly more-severe (less-muted) band of the `--neg` token.
 * The scale uses ONLY existing design tokens (color-mix over --neg toward --text-muted) — no new hex.
 */
import assert from "node:assert";

import { MUTED_CLASS, MDD_BANDS, mddColorClass } from "./mdd-color.ts";

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

// --- NA / non-real-drawdown cases: always muted, never a graded red ------------------------------

check("null is the muted token (NA — not a real drawdown)", () => {
  assert.strictEqual(mddColorClass(null), MUTED_CLASS);
});

check("undefined is the muted token (NA — not a real drawdown)", () => {
  assert.strictEqual(mddColorClass(undefined), MUTED_CLASS);
});

check("exactly 0 is the muted token (flat — not a real drawdown)", () => {
  assert.strictEqual(mddColorClass(0), MUTED_CLASS);
});

// --- magnitude grading: deeper drawdown => strictly more-severe band -----------------------------

check("a tiny drawdown lands in the shallowest (least-severe) band", () => {
  assert.strictEqual(mddColorClass(-0.005), MDD_BANDS[0].className);
});

check("a -8% drawdown is more severe than a -1% drawdown (different, later band)", () => {
  const shallow = MDD_BANDS.findIndex((b) => b.className === mddColorClass(-0.01));
  const deep = MDD_BANDS.findIndex((b) => b.className === mddColorClass(-0.08));
  assert.ok(deep > shallow, `expected -8% band (${deep}) to be later than -1% band (${shallow})`);
});

check("a catastrophic -50% drawdown lands in the deepest (most-severe) band", () => {
  assert.strictEqual(mddColorClass(-0.5), MDD_BANDS[MDD_BANDS.length - 1].className);
});

check("the scale is monotonic — magnitude never maps to an earlier band as it deepens", () => {
  const samples = [-0.001, -0.02, -0.05, -0.1, -0.2, -0.4];
  let lastBand = -1;
  for (const v of samples) {
    const band = MDD_BANDS.findIndex((b) => b.className === mddColorClass(v));
    assert.ok(band >= lastBand, `band regressed at ${v}: ${band} < ${lastBand}`);
    lastBand = band;
  }
});

// --- token discipline: every band is a design-token color-mix, never a hardcoded hex -------------

check("no band class contains a hardcoded hex literal (design tokens only)", () => {
  for (const band of MDD_BANDS) {
    assert.ok(!/#[0-9a-fA-F]{3,8}/.test(band.className), `band has hex: ${band.className}`);
    assert.ok(band.className.includes("var(--neg)"), `band must mix --neg: ${band.className}`);
  }
  assert.ok(!/#[0-9a-fA-F]{3,8}/.test(MUTED_CLASS), `muted has hex: ${MUTED_CLASS}`);
});

check("there are at least four severity bands (visible magnitude grading)", () => {
  assert.ok(MDD_BANDS.length >= 4, `expected >= 4 bands, got ${MDD_BANDS.length}`);
});

console.log(`\n${passed} passed`);
