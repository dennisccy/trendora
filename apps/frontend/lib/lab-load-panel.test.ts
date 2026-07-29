/**
 * Unit tests for the research-lab load-panel resolver (lib/lab-load-panel.ts) — ops-hardening iter-33,
 * the UT-11 fix.
 *
 * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
 *   node lib/lab-load-panel.test.ts
 *
 * The UT-11 defect this pins: `/research/regime-lab` rendered an UNLABELLED grey skeleton indefinitely
 * (observed 40+ s, backing endpoint 60-90 s on a cold cache) with zero user feedback — no explanation, no
 * elapsed time, no retry affordance, and one backend trial returned a raw error body instead of data. The
 * resolver below is the single pure decision the page renders from, so the honest-feedback rule is
 * asserted here rather than in un-runnable component code:
 *   (a) a brief ordinary load stays a plain skeleton (no alarming copy for a sub-threshold fetch);
 *   (b) once the wait crosses the threshold the panel becomes an explicit, LABELLED "computing" state
 *       carrying the elapsed seconds — never an indefinite unlabelled skeleton;
 *   (c) a failed fetch resolves to an error panel that is explicitly retryable;
 *   (d) a completed fetch resolves to the data panel regardless of how long it took;
 *   (e) the elapsed label is human-readable (seconds under a minute, m+s above it).
 */
import assert from "node:assert";

import {
  formatElapsedSeconds,
  resolveLabLoadPanel,
  SLOW_COMPUTE_NOTICE_AFTER_SECONDS,
} from "./lab-load-panel.ts";

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

// --- (a) a brief ordinary load stays a plain skeleton --------------------------------------------

check("a fresh loading fetch (0s) resolves to the plain skeleton", () => {
  assert.deepStrictEqual(resolveLabLoadPanel("loading", 0), { kind: "skeleton" });
});

check("a loading fetch one second under the threshold is still the plain skeleton", () => {
  assert.deepStrictEqual(resolveLabLoadPanel("loading", SLOW_COMPUTE_NOTICE_AFTER_SECONDS - 1), {
    kind: "skeleton",
  });
});

// --- (b) crossing the threshold produces a LABELLED computing state with the elapsed seconds -----

check("at the threshold the panel becomes an explicit computing state carrying the elapsed seconds", () => {
  assert.deepStrictEqual(resolveLabLoadPanel("loading", SLOW_COMPUTE_NOTICE_AFTER_SECONDS), {
    kind: "computing",
    elapsedSeconds: SLOW_COMPUTE_NOTICE_AFTER_SECONDS,
  });
});

check("the UT-11 wait (40s) is a computing state, never an unlabelled skeleton", () => {
  assert.deepStrictEqual(resolveLabLoadPanel("loading", 40), { kind: "computing", elapsedSeconds: 40 });
});

check("the UT-11 worst observed backend wait (90s) is still a computing state", () => {
  assert.deepStrictEqual(resolveLabLoadPanel("loading", 90), { kind: "computing", elapsedSeconds: 90 });
});

// --- (c) a failed fetch is an explicitly retryable error panel ------------------------------------

check("an errored fetch resolves to a retryable error panel", () => {
  assert.deepStrictEqual(resolveLabLoadPanel("error", 0), { kind: "error", retryable: true });
});

check("an errored fetch after a long wait is still a retryable error panel (never a stuck skeleton)", () => {
  assert.deepStrictEqual(resolveLabLoadPanel("error", 95), { kind: "error", retryable: true });
});

// --- (d) a completed fetch is the data panel ------------------------------------------------------

check("a completed fetch resolves to the data panel", () => {
  assert.deepStrictEqual(resolveLabLoadPanel("ok", 0), { kind: "data" });
});

check("a completed fetch that took 68s still resolves to the data panel", () => {
  assert.deepStrictEqual(resolveLabLoadPanel("ok", 68), { kind: "data" });
});

// --- (e) the elapsed label is human-readable ------------------------------------------------------

check("elapsed under a minute renders as whole seconds", () => {
  assert.strictEqual(formatElapsedSeconds(0), "0s");
  assert.strictEqual(formatElapsedSeconds(3), "3s");
  assert.strictEqual(formatElapsedSeconds(59), "59s");
});

check("elapsed at or over a minute renders as minutes + seconds", () => {
  assert.strictEqual(formatElapsedSeconds(60), "1m 00s");
  assert.strictEqual(formatElapsedSeconds(72), "1m 12s");
  assert.strictEqual(formatElapsedSeconds(90), "1m 30s");
  assert.strictEqual(formatElapsedSeconds(605), "10m 05s");
});

check("a negative or fractional elapsed never renders a nonsense label", () => {
  assert.strictEqual(formatElapsedSeconds(-4), "0s");
  assert.strictEqual(formatElapsedSeconds(4.7), "4s");
});

// --- the threshold itself is a short, honest grace window ------------------------------------------

check("the notice threshold is a short grace window (1-10s), not a second silent wait", () => {
  assert.ok(
    SLOW_COMPUTE_NOTICE_AFTER_SECONDS >= 1 && SLOW_COMPUTE_NOTICE_AFTER_SECONDS <= 10,
    `threshold ${SLOW_COMPUTE_NOTICE_AFTER_SECONDS}s is outside the 1-10s honest grace window`,
  );
});

console.log(`\n${passed} passed`);
