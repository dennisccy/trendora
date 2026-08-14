/**
 * Unit tests for the `/data` job card's finalize-tail rendering rules (lib/job-finalize-phase.ts).
 *
 * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
 *   node lib/job-finalize-phase.test.ts
 * (Per the project's documented dev-box limitation, `node lib/*.test.ts` may not execute on every Node
 * build locally — see docs/handoffs/*iter-25-dev.md; `npx tsx lib/job-finalize-phase.test.ts` is the
 * local fallback. These run in the CI/QA Node environment either way.)
 *
 * The regression these pin (live, run 530 on 2026-08-14): a healthy backfill rendered a FULL 8/8 bar, a
 * completed-sounding message, a false "scanning 2026-08-12 (8/8)" activity line and an amber
 * "· possibly stalled" — simultaneously — for 15m22s, because the finalize tail published nothing and
 * its longest phase (511s, a single call) starved the heartbeat.
 */
import assert from "node:assert";

import {
  backfillCountsLabel,
  finalizeView,
  formatElapsed,
  shouldShowStallWarning,
} from "./job-finalize-phase.ts";

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

const T0 = Date.parse("2026-08-14T20:49:28.000Z");
const RUNNING_IN_PHASE = {
  status: "running",
  finalize_phase: "factor lab",
  finalize_phase_started_at: "2026-08-14T20:49:28.000Z",
};
const RUNNING_NO_PHASE = { status: "running", finalize_phase: "", finalize_phase_started_at: null };

// --- formatElapsed -----------------------------------------------------------------------------------

check("formatElapsed renders seconds, minutes and hours compactly", () => {
  assert.strictEqual(formatElapsed(12), "12s");
  assert.strictEqual(formatElapsed(398), "6m38s"); // the live factor-lab phase, mid-run
  assert.strictEqual(formatElapsed(511), "8m31s"); // its measured total
  assert.strictEqual(formatElapsed(3725), "1h02m");
});

check("formatElapsed refuses to invent a duration from a bad input", () => {
  assert.strictEqual(formatElapsed(Number.NaN), "");
  assert.strictEqual(formatElapsed(-5), "");
});

// --- finalizeView ------------------------------------------------------------------------------------

check("a named phase renders with its own elapsed time", () => {
  const view = finalizeView(RUNNING_IN_PHASE, T0 + 398_000);
  assert.deepStrictEqual(view, { phase: "factor lab", elapsed: "6m38s" });
});

check("elapsed is time-in-THIS-phase, not time since the tail began", () => {
  // the backend re-stamps `finalize_phase_started_at` on every phase, so a later phase reads small
  const later = { ...RUNNING_IN_PHASE, finalize_phase: "drawdown expectations (factor:ma_stack:h20)",
                  finalize_phase_started_at: "2026-08-14T20:58:00.000Z" };
  const view = finalizeView(later, Date.parse("2026-08-14T20:58:53.000Z"));
  assert.strictEqual(view?.elapsed, "53s");
});

check("no finalize phase -> no finalize line (the honest idle case)", () => {
  assert.strictEqual(finalizeView(RUNNING_NO_PHASE, T0), null);
  assert.strictEqual(finalizeView({ status: "ok" }, T0), null);
});

check("a phase with an unparseable start still renders the phase, never a fabricated elapsed", () => {
  const view = finalizeView({ ...RUNNING_IN_PHASE, finalize_phase_started_at: "not-a-date" }, T0);
  assert.deepStrictEqual(view, { phase: "factor lab", elapsed: "" });
});

// --- shouldShowStallWarning --------------------------------------------------------------------------

check("THE REGRESSION: a stale heartbeat inside a named finalize phase is NOT a stall", () => {
  // live: 141s stale inside `factor_lab_all_warm`, which ticks once before a single 511s call
  assert.strictEqual(shouldShowStallWarning(RUNNING_IN_PHASE, true), false);
});

check("the scan loop keeps its stall detection unchanged", () => {
  assert.strictEqual(shouldShowStallWarning(RUNNING_NO_PHASE, true), true);
});

check("a fresh heartbeat is never a stall, phase or not", () => {
  assert.strictEqual(shouldShowStallWarning(RUNNING_NO_PHASE, false), false);
  assert.strictEqual(shouldShowStallWarning(RUNNING_IN_PHASE, false), false);
});

// --- backfillCountsLabel -----------------------------------------------------------------------------

check("a full bar during the tail is labelled 'finalizing', not left reading as complete", () => {
  assert.strictEqual(backfillCountsLabel(RUNNING_IN_PHASE, 8, 8), "8/8 dates · finalizing");
});

check("mid-scan and finished jobs keep the plain counts label", () => {
  assert.strictEqual(backfillCountsLabel(RUNNING_NO_PHASE, 3, 8), "3/8 dates");
  assert.strictEqual(backfillCountsLabel({ status: "ok" }, 8, 8), "8/8 dates");
  // a completed job whose deferred hot-key warms are still running must NOT say "finalizing" on a bar
  // it has already finished — the status is the gate, and it is `ok` here.
  assert.strictEqual(
    backfillCountsLabel({ ...RUNNING_IN_PHASE, status: "ok" }, 8, 8), "8/8 dates",
  );
});

console.log(`${passed} passed`);
