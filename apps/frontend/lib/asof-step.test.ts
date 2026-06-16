/**
 * Unit tests for the J-79 pure as-of stepping + field-guard authority (lib/asof-step.ts).
 *
 * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
 *   node lib/asof-step.test.ts
 * They assert EXACT values (bounded no-ops, snapshot-only landings, Latest normalisation, and the
 * field-guard predicate across input/textarea/select/contenteditable vs steppable targets).
 */
import assert from "node:assert";

import { resolveStep, canStepPrev, canStepNext, isFieldEditingTarget } from "./asof-step.ts";

// Descending (newest-first) snapshot list, as the asof-provider serves it. Note the deliberate gap
// (no 2026-05-03) so "snapshot-only" stepping is proven to skip the non-snapshot calendar day.
const DATES = ["2026-05-06", "2026-05-05", "2026-05-04", "2026-05-02", "2026-05-01"];

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

// --- resolveStep: snapshot-only, bounded, Latest-normalised --------------------------------------

check("step older from the newest (Latest, asOf=null) lands on the 2nd-newest", () => {
  assert.deepStrictEqual(resolveStep(DATES, null, -1), { changed: true, next: "2026-05-05" });
});

check("step older skips a non-snapshot calendar day (05-04 -> 05-02, not 05-03)", () => {
  assert.deepStrictEqual(resolveStep(DATES, "2026-05-04", -1), { changed: true, next: "2026-05-02" });
});

check("step older at the OLDEST date is a bounded no-op", () => {
  assert.deepStrictEqual(resolveStep(DATES, "2026-05-01", -1), { changed: false, next: "2026-05-01" });
});

check("step newer from a historical date lands on the next snapshot up", () => {
  assert.deepStrictEqual(resolveStep(DATES, "2026-05-02", 1), { changed: true, next: "2026-05-04" });
});

check("step newer onto the newest snapshot normalises to Latest (null)", () => {
  assert.deepStrictEqual(resolveStep(DATES, "2026-05-05", 1), { changed: true, next: null });
});

check("step newer at Latest (asOf=null) is a bounded no-op", () => {
  assert.deepStrictEqual(resolveStep(DATES, null, 1), { changed: false, next: null });
});

check("an unknown asOf is treated as the newest index (older step lands on 2nd-newest)", () => {
  assert.deepStrictEqual(resolveStep(DATES, "1999-01-01", -1), { changed: true, next: "2026-05-05" });
});

check("empty date list never steps", () => {
  assert.deepStrictEqual(resolveStep([], "2026-05-01", -1), { changed: false, next: "2026-05-01" });
  assert.deepStrictEqual(resolveStep([], null, 1), { changed: false, next: null });
});

check("a single-date list is bounded both ways", () => {
  assert.deepStrictEqual(resolveStep(["2026-05-01"], null, -1), { changed: false, next: null });
  assert.deepStrictEqual(resolveStep(["2026-05-01"], "2026-05-01", 1), { changed: false, next: "2026-05-01" });
});

// --- canStepPrev / canStepNext bounds ------------------------------------------------------------

check("canStepPrev is false at the oldest, true elsewhere", () => {
  assert.strictEqual(canStepPrev(DATES, "2026-05-01"), false);
  assert.strictEqual(canStepPrev(DATES, "2026-05-02"), true);
  assert.strictEqual(canStepPrev(DATES, null), true); // from Latest there is older history
});

check("canStepNext is false at Latest/newest, true elsewhere", () => {
  assert.strictEqual(canStepNext(DATES, null), false);
  assert.strictEqual(canStepNext(DATES, "2026-05-06"), false); // newest == Latest
  assert.strictEqual(canStepNext(DATES, "2026-05-01"), true);
});

// --- field-guard predicate -----------------------------------------------------------------------

check("field-guard catches input/textarea/select (any case) + contenteditable", () => {
  assert.strictEqual(isFieldEditingTarget({ tagName: "INPUT" }), true);
  assert.strictEqual(isFieldEditingTarget({ tagName: "input" }), true);
  assert.strictEqual(isFieldEditingTarget({ tagName: "TEXTAREA" }), true);
  assert.strictEqual(isFieldEditingTarget({ tagName: "SELECT" }), true);
  assert.strictEqual(isFieldEditingTarget({ tagName: "DIV", isContentEditable: true }), true);
});

check("field-guard allows steppable targets (body, button, link, null)", () => {
  assert.strictEqual(isFieldEditingTarget({ tagName: "BODY" }), false);
  assert.strictEqual(isFieldEditingTarget({ tagName: "BUTTON" }), false);
  assert.strictEqual(isFieldEditingTarget({ tagName: "A" }), false);
  assert.strictEqual(isFieldEditingTarget(null), false);
  assert.strictEqual(isFieldEditingTarget(undefined), false);
});

console.log(`\nasof-step: ${passed} checks passed`);
