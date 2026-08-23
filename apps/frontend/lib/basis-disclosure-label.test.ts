/**
 * Unit tests for the goal-market-compass iter-11 basis-disclosure status -> {variant, label} mapping
 * (lib/basis-disclosure-label.ts), extracted from compass-manifest-strip.tsx's BasisLine.
 *
 * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
 *   node lib/basis-disclosure-label.test.ts
 * They assert EXACT variant + label strings for all four statuses, and specifically that the NEW
 * "unverifiable" status (TC-14) reads visibly distinct from both "available" (ok) and "unavailable"
 * (danger) -- never collapsed into either neighbor's variant or wording.
 */
import assert from "node:assert";

import { basisDisclosureLabel } from "./basis-disclosure-label.ts";

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

// --- the three pre-existing statuses -- unchanged behavior after the mechanical refactor -----------

check('"available" is the ok variant with the unchanged label', () => {
  assert.deepStrictEqual(basisDisclosureLabel("available"), { variant: "ok", label: "Basis: available" });
});

check('"rebuilt" is the warn variant with the unchanged label', () => {
  assert.deepStrictEqual(basisDisclosureLabel("rebuilt"), { variant: "warn", label: "Basis: rebuilt" });
});

check('"unavailable" is the danger variant with the unchanged label', () => {
  assert.deepStrictEqual(basisDisclosureLabel("unavailable"), { variant: "danger", label: "Basis: unavailable" });
});

// --- TC-14: the new "unverifiable" status is visibly distinct from BOTH neighbors -------------------

check('"unverifiable" is its OWN distinct variant, not "ok" (never a confident claim -- AG-1)', () => {
  const result = basisDisclosureLabel("unverifiable");
  assert.notStrictEqual(result.variant, "ok");
});

check('"unverifiable" is its OWN distinct variant, not "danger" (a different fact than "run is gone")', () => {
  const result = basisDisclosureLabel("unverifiable");
  assert.notStrictEqual(result.variant, "danger");
});

check('"unverifiable" resolves to the neutral default variant with its own distinct label', () => {
  assert.deepStrictEqual(basisDisclosureLabel("unverifiable"), {
    variant: "default",
    label: "Basis: unverifiable",
  });
});

check('every one of the four statuses maps to a UNIQUE (variant, label) pair -- none collapse together', () => {
  const statuses = ["available", "unavailable", "rebuilt", "unverifiable"] as const;
  const seen = new Set(statuses.map((s) => JSON.stringify(basisDisclosureLabel(s))));
  assert.strictEqual(seen.size, statuses.length);
});

console.log(`\n${passed} passed`);
