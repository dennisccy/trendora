/**
 * Unit tests for the J-09 goal-ops-hardening iter-26 `LastOutcomeSummary` render-decision extraction
 * (lib/background-compute-last-outcome.ts).
 *
 * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
 *   node lib/background-compute-last-outcome.test.ts
 * (Per the project's documented dev-box limitation, `node lib/*.test.ts` may not execute on every Node
 * build locally — see docs/handoffs/*iter-49-dev.md; these run in the CI/QA Node environment either
 * way, same as every other `lib/*.test.ts` file here.)
 *
 * TC-5: `completed` (reason: null) -> { reasonText: null, badgeVariant: "ok" }; `failed` (reason: <str>)
 * -> { reasonText: <that exact string>, badgeVariant: "danger" }.
 */
import assert from "node:assert";

import { resolveLastOutcomeSummary } from "./background-compute-last-outcome.ts";
import type { BackgroundComputeOutcome } from "./api.ts";

const COMPLETED: BackgroundComputeOutcome = {
  asof_key: "2026-07-17",
  dataset_version: "r1-f2",
  outcome: "completed",
  started_at: "2026-07-17T00:00:00+00:00",
  finished_at: "2026-07-17T00:01:15+00:00",
  duration_ms: 75000,
  reason: null,
};

const FAILED: BackgroundComputeOutcome = {
  asof_key: "2026-01-04",
  dataset_version: "r1-f2",
  outcome: "failed",
  started_at: "2026-01-04T00:00:00+00:00",
  finished_at: "2026-01-04T00:00:05+00:00",
  duration_ms: 5000,
  reason: "forced test failure — simulated dispatch error",
};

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

check("a completed outcome resolves to reasonText null and badgeVariant ok (TC-5, existing case)", () => {
  assert.deepStrictEqual(resolveLastOutcomeSummary(COMPLETED), { reasonText: null, badgeVariant: "ok" });
});

check("a failed outcome resolves to reasonText equal to the exact reason string and badgeVariant danger (TC-5)", () => {
  assert.deepStrictEqual(resolveLastOutcomeSummary(FAILED), {
    reasonText: "forced test failure — simulated dispatch error",
    badgeVariant: "danger",
  });
});

console.log(`${passed} passed`);
