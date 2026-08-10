/**
 * Unit tests for the iter-58 (audit B5 fix) availability empty-state gate
 * (lib/availability-empty-state.ts).
 *
 * No test framework is installed in this frontend; these run under Node's native TS type-stripping:
 *   node lib/availability-empty-state.test.ts
 * (Per the project's documented dev-box limitation, `node lib/*.test.ts` may not execute on every Node
 * build locally — see docs/handoffs/*iter-25-dev.md; `npx tsx lib/availability-empty-state.test.ts` is
 * the local fallback. These run in the CI/QA Node environment either way, same as every other
 * `lib/*.test.ts` file here.)
 *
 * TC-4 (goal-ops-hardening-iter-58.md): a stale-but-empty persisted row must NOT trigger the empty
 * state — only a genuinely non-stale empty payload (no `AvailabilityCache` row has ever been persisted)
 * may.
 */
import assert from "node:assert";

import { shouldShowAvailabilityEmptyState } from "./availability-empty-state.ts";
import type { AvailabilityResponse } from "./api.ts";

let passed = 0;
function check(name: string, fn: () => void) {
  fn();
  passed += 1;
  console.log(`  ok - ${name}`);
}

const NEVER_WARMED: AvailabilityResponse = {
  total_symbols: 0,
  trading_day_count: 0,
  cells: [],
  stale: false,
  served_dataset_version: null,
};

// TC-4's own precondition: a persisted row whose stamp mismatches AND whose cells array is empty
// (constructed via a direct-write test fixture at the backend layer — this is the frontend-side gate
// that same payload shape must satisfy).
const STALE_BUT_EMPTY: AvailabilityResponse = {
  total_symbols: 0,
  trading_day_count: 0,
  cells: [],
  stale: true,
  served_dataset_version: "r1-f1",
};

const NON_EMPTY_NOT_STALE: AvailabilityResponse = {
  total_symbols: 5,
  trading_day_count: 1,
  cells: [{ date: "2024-01-02", symbols_with_bars: 5, total_symbols: 5, snapshot_exists: false }],
  stale: false,
  served_dataset_version: "r1-f1",
};

const NON_EMPTY_STALE: AvailabilityResponse = {
  total_symbols: 5,
  trading_day_count: 1,
  cells: [{ date: "2024-01-02", symbols_with_bars: 5, total_symbols: 5, snapshot_exists: false }],
  stale: true,
  served_dataset_version: "r1-f1",
};

// --- the never-warmed case (unchanged): empty cells + not stale -> the empty state IS honest here -----

check("never-warmed (empty cells, not stale) shows the empty state — unchanged from before this fix", () => {
  assert.strictEqual(shouldShowAvailabilityEmptyState(NEVER_WARMED), true);
});

// --- TC-4: the narrow B5 precondition — empty cells but STALE -> never the empty state -----------------

check("TC-4: a stale-but-empty persisted row does NOT show 'No availability yet'", () => {
  assert.strictEqual(shouldShowAvailabilityEmptyState(STALE_BUT_EMPTY), false);
});

// --- non-empty cases: never the empty state, stale or not -----------------------------------------------

check("non-empty, not stale -> never the empty state", () => {
  assert.strictEqual(shouldShowAvailabilityEmptyState(NON_EMPTY_NOT_STALE), false);
});

check("non-empty, stale -> never the empty state (the stale banner path handles this instead)", () => {
  assert.strictEqual(shouldShowAvailabilityEmptyState(NON_EMPTY_STALE), false);
});

console.log(`${passed} passed`);
