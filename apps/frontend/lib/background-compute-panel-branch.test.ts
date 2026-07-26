/**
 * Unit tests for the J-09 / audit-F1 `BackgroundComputePanel` branch resolver
 * (lib/background-compute-panel-branch.ts).
 *
 * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
 *   node lib/background-compute-panel-branch.test.ts
 * (Per the project's documented dev-box limitation, `node lib/*.test.ts` may not execute on every Node
 * build locally — see docs/handoffs/*iter-49-dev.md; these run in the CI/QA Node environment either
 * way, same as every other `lib/*.test.ts` file here.)
 *
 * TC-3 (poll-failure -> "unknown", never the idle sentence) and TC-4 (poll succeeds, zero active ->
 * idle, unchanged) are both covered below, plus the active-window and outcome-visibility branches.
 */
import assert from "node:assert";

import { resolveBackgroundComputePanelBranch } from "./background-compute-panel-branch.ts";
import type { BackgroundComputeStatus } from "./api.ts";

const EMPTY: BackgroundComputeStatus = { active: [], recent_outcomes: [] };

const ONE_ACTIVE: BackgroundComputeStatus = {
  active: [{
    asof_key: "2026-07-17", dataset_version: "r1-f2", started_at: "2026-07-17T00:00:00+00:00",
    elapsed_ms: 41800, horizons_done: 2, horizons_total: 5,
  }],
  recent_outcomes: [],
};

const ONE_OUTCOME: BackgroundComputeStatus = {
  active: [],
  recent_outcomes: [{
    asof_key: "2026-07-17", dataset_version: "r1-f2", outcome: "completed",
    started_at: "2026-07-17T00:00:00+00:00", finished_at: "2026-07-17T00:01:15+00:00",
    duration_ms: 75000, reason: null,
  }],
};

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

// --- TC-3: poll failure / backend unreachable -> "unknown", regardless of the stale backgroundCompute
//     value the provider may still be holding -------------------------------------------------------

check("state 'unavailable' resolves to 'unknown' even when backgroundCompute is null (the provider's own catch-branch pairing)", () => {
  assert.deepStrictEqual(resolveBackgroundComputePanelBranch("unavailable", null), { kind: "unknown" });
});

check("state 'unavailable' resolves to 'unknown' even with a (stale) non-empty backgroundCompute value", () => {
  assert.deepStrictEqual(resolveBackgroundComputePanelBranch("unavailable", ONE_ACTIVE), { kind: "unknown" });
});

// --- TC-4: poll succeeds, zero active windows -> idle, unchanged from before this fix ----------------

check("state 'ready' with the empty shape resolves to idle with no last outcome (TC-4, the existing idle case)", () => {
  assert.deepStrictEqual(resolveBackgroundComputePanelBranch("ready", EMPTY), { kind: "idle", showLastOutcome: false });
});

check("state 'initializing' with the empty shape also resolves to idle (readiness state doesn't gate this)", () => {
  assert.deepStrictEqual(resolveBackgroundComputePanelBranch("initializing", EMPTY), { kind: "idle", showLastOutcome: false });
});

// --- pre-first-poll (state === null, backgroundCompute === null): unchanged prior behavior -----------

check("state null (before the first poll resolves) falls through to idle, never 'unknown' (no regression)", () => {
  assert.deepStrictEqual(resolveBackgroundComputePanelBranch(null, null), { kind: "idle", showLastOutcome: false });
});

// --- idle with a last outcome present -----------------------------------------------------------------

check("zero active windows but a recorded outcome resolves to idle WITH a last outcome to show", () => {
  assert.deepStrictEqual(resolveBackgroundComputePanelBranch("ready", ONE_OUTCOME), { kind: "idle", showLastOutcome: true });
});

// --- active window, with and without a prior outcome ---------------------------------------------------

check("an active window with no prior outcome resolves to active, no last outcome", () => {
  assert.deepStrictEqual(resolveBackgroundComputePanelBranch("ready", ONE_ACTIVE), { kind: "active", showLastOutcome: false });
});

check("an active window alongside a prior outcome resolves to active WITH a last outcome to show", () => {
  const both: BackgroundComputeStatus = { active: ONE_ACTIVE.active, recent_outcomes: ONE_OUTCOME.recent_outcomes };
  assert.deepStrictEqual(resolveBackgroundComputePanelBranch("ready", both), { kind: "active", showLastOutcome: true });
});

console.log(`${passed} passed`);
